"""Keeping the model sound: lint, duplicates, calibration, backup and drafting.

None of this writes evidence. Drafting asks a cheap read-only model (through
`pi`) to propose propositions for finished vault notes; a person or agent
approves them before they are added.
"""

from __future__ import annotations

import datetime as dt
import difflib
import re
import shutil
import subprocess
from pathlib import Path

from .config import Config
from .model import Model
from .store import Store
from .text import norm
from .vault import Vault

SCOUT_PROMPT = """You are a read-only scout for an agent that models what one
reader knows. You work in their vault, a folder of markdown notes:
notes/<id>.md, with YAML frontmatter (`aliases:` holds the title, `status:`
stub/wip/developed) and links [[id|label]]. Never create, edit or move any
file. Search with grep and find, read what you need, and answer tersely. When
asked for propositions, give one per line as

  reader new prop "<name>" "<statement, LaTeX in $…$, assumptions inside>" --topics <t> --vault <id>

with a kebab-case name, one checkable claim per line, taken from a note's own
definition or theorem block; then chains as

  reader new chain <name-a> <name-b> => <name-c> --step "<the reasoning step>"

using the names you proposed. Cite note ids. No preamble."""


def lint(store: Store, m: Model, vault: Vault | None) -> list[str]:
    """Every file parses, every id resolves, and every answer matches its question."""
    problems = list(m.problems)
    for c in m.chains.values():
        problems += [f"{c.id}: unknown proposition {p}"
                     for p in (*c.premises, c.conclusion) if p not in m.props]
    seen = set()
    for a in m.answers:
        where = f"{a.ask}/{a.n}"
        if not m.exists(a.id):
            problems.append(f"{where}: unknown id {a.id}")
        if (a.ask, a.n) in seen:
            problems.append(f"{where}: answered twice")
        seen.add((a.ask, a.n))
        ask = store.ask(a.ask)
        if ask is None:
            problems.append(f"{where}: no question block {a.ask}")
        elif a.n > len(ask["items"]) or ask["items"][a.n - 1]["id"] != a.id:
            problems.append(f"{where}: does not ask about {a.id}")
    if vault:
        problems += [f"{p.id}: no vault note {p.vault}"
                     for p in m.props.values() if p.vault and p.vault not in vault]
    return problems


def dupes(m: Model, threshold: float = 0.85) -> list[str]:
    ps = list(m.props.values())
    keys = [(norm(p.name), norm(p.statement)) for p in ps]
    out = []
    for i in range(len(ps)):
        for j in range(i + 1, len(ps)):
            r = max(difflib.SequenceMatcher(None, keys[i][0], keys[j][0]).ratio(),
                    difflib.SequenceMatcher(None, keys[i][1], keys[j][1]).ratio())
            if r >= threshold:
                out.append(f"{r:.2f}  {ps[i].id} {ps[i].name}  ~  {ps[j].id} {ps[j].name}")
    return out


def calibration(m: Model) -> dict[int, tuple[int, float]]:
    """Confidence digit → (picks, share right)."""
    bins: dict[int, list[bool]] = {}
    for a in m.answers:
        if a.kind == "pick" and a.conf is not None and a.flag != "unseen":
            bins.setdefault(a.conf, []).append(a.grade != "again")
    return {c: (len(xs), sum(xs) / len(xs)) for c, xs in sorted(bins.items())}


def scout(cfg: Config, task: str, timeout: int) -> str:
    if not cfg.vault:
        raise RuntimeError("no vault configured (READER_VAULT or vault in config.toml)")
    if not cfg.scout_model:
        raise RuntimeError("no scout model configured (READER_SCOUT_MODEL or scout_model)")
    if not shutil.which("pi"):
        raise RuntimeError("the scout needs pi, which is not installed")
    cmd = ["pi", "-p", "--no-session", "--no-skills", "--no-context-files",
           "--tools", "read,grep,find,ls", "--model", cfg.scout_model,
           "--append-system-prompt", SCOUT_PROMPT, task]
    try:
        r = subprocess.run(cmd, cwd=cfg.vault, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"scout timed out after {timeout}s ({cfg.scout_model})") from None
    if r.returncode:
        raise RuntimeError(f"scout failed ({cfg.scout_model}): {r.stderr.strip()[-500:]}")
    return r.stdout.strip()


def run(cfg: Config, store: Store, m: Model, vault: Vault | None,
        draft: bool, limit: int, timeout: int) -> str:
    """The daily pass: lint, back up, duplicates, and notes still without propositions."""
    store.init()
    report = [f"# reader upkeep · {cfg.today}"]
    problems = lint(store, m, vault)
    report.append("lint problems:\n" + "\n".join(problems) if problems
                  else f"lint: ok · {len(m.props)} propositions, {len(m.chains)} chains, "
                       f"{len(m.answers)} answers")
    report += _backup(cfg.home, cfg.today)
    d = dupes(m)
    if d:
        report.append("likely duplicates (merge by hand):\n" + "\n".join(d))
    if vault:
        report.append(_draft(cfg, store, m, vault, draft, limit, timeout))
    return "\n\n".join(report)


def _backup(home: Path, today: dt.date) -> list[str]:
    if not (home / ".git").exists():
        return []
    git = ["git", "-C", str(home)]
    subprocess.run([*git, "add", "-A"], check=False)
    c = subprocess.run([*git, "commit", "-qm", f"upkeep {today}"], capture_output=True, text=True)
    out = ["backup: committed" if c.returncode == 0 else "backup: nothing new"]
    if subprocess.run([*git, "remote"], capture_output=True, text=True).stdout.strip():
        p = subprocess.run([*git, "push", "-q"], capture_output=True, text=True)
        out.append("push: ok" if p.returncode == 0 else f"push failed: {p.stderr.strip()[-200:]}")
    return out


def _draft(cfg: Config, store: Store, m: Model, vault: Vault,
           draft: bool, limit: int, timeout: int) -> str:
    proposals = store.home / "proposals.md"
    handled = set(re.findall(r"^## (\S+) ", proposals.read_text() if proposals.exists() else "",
                             re.M))
    pointed = {p.vault for p in m.props.values() if p.vault}
    todo = sorted(((vault.developed_date(n.id) or dt.date.min, n) for n in vault.notes().values()
                   if n.status == "developed" and n.type in ("", "note")
                   and n.id not in pointed | handled),
                  key=lambda x: x[0], reverse=True)
    batch = todo[:limit]
    if not batch:
        return "vault: no new developed notes"
    if not draft:
        return (f"vault: {len(todo)} developed notes without propositions; newest:\n"
                + "\n".join(f"  {n.id}  {n.title}  ({day})" for day, n in batch))
    out = []
    for day, n in batch:
        try:
            body = scout(cfg, f"Read notes/{n.id}.md and the notes it links to. Propose the "
                              f"propositions (and chains between them) that note {n.id} states, "
                              f"at most 6.", timeout)
        except RuntimeError as e:
            body = f"(scout failed: {e})"
        out += ["", f"## {n.id} · {n.title} · developed {day} · proposed {cfg.today}", body]
    with proposals.open("a") as f:
        f.write("\n".join(out) + "\n")
    return (f"vault: drafted propositions for {len(batch)} of {len(todo)} notes into "
            f"proposals.md: " + ", ".join(n.id for _, n in batch))
