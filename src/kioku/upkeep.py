"""Keeping the model sound: lint, duplicates, areas to split, calibration, backup
and drafting.

None of this writes evidence. Drafting asks a cheap read-only model (through
`pi`) to propose ideas for finished vault notes; a person or agent approves
them before they are added.
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
learner knows. You work in their vault, a folder of markdown notes:
notes/<id>.md, with YAML frontmatter (`aliases:` holds the title, `status:`
stub/wip/developed) and links [[id|label]]. Never create, edit or move any
file. Search with grep and find, read what you need, and answer tersely. When
asked for ideas, give each as a block for `kioku add`:

  ## <kebab-case-name> · definition|result|proof|method · <area, e.g. maths/analysis>
  <the statement, LaTeX in $…$, readable alone>
  - needs: <names of ideas you cannot follow it without>
  - uses: <names of ideas that doing it carries out>
  - vault: <note id>

one idea per block, taken from a note's own definition or theorem block; a
proof is its own idea. Leave out a line that would be empty. Cite note ids. No
preamble."""

AREA_LIMIT = 40  # an area listing stops fitting a screen
CLUSTER = 5  # ideas linked mostly to each other: a sub-area


def lint(store: Store, m: Model, vault: Vault | None) -> list[str]:
    """Every file parses, every name and edge resolves, nothing forms a cycle, and every
    answer matches its question."""
    problems = list(m.problems)
    names: dict[str, str] = {}
    for i in m.ideas.values():
        if i.name in names:
            problems.append(f"{i.id}: name {i.name} is also {names[i.name]}'s")
        names.setdefault(i.name, i.id)
        problems += [f"{i.name}: edge to unknown idea {n}" for n in (*i.needs, *i.uses)
                     if n not in m.by_name]
    problems += [f"cycle: {' → '.join(m.name(x) for x in c)}" for c in m.cycles()]
    seen = set()
    for a in m.answers:
        where = f"{a.ask}/{a.n}"
        if a.id not in m.ideas:
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
        problems += [f"{i.name}: no vault note {i.vault}"
                     for i in m.ideas.values() if i.vault and i.vault not in vault]
    return problems


def dupes(m: Model, threshold: float = 0.85) -> list[str]:
    ideas = list(m.ideas.values())
    keys = [(norm(i.name), norm(i.statement)) for i in ideas]
    out = []
    for a in range(len(ideas)):
        for b in range(a + 1, len(ideas)):
            r = max(difflib.SequenceMatcher(None, keys[a][0], keys[b][0]).ratio(),
                    difflib.SequenceMatcher(None, keys[a][1], keys[b][1]).ratio())
            if r >= threshold:
                out.append(f"{r:.2f}  {ideas[a].name}  ~  {ideas[b].name}")
    return out


def to_split(m: Model) -> list[str]:
    """Areas too big for one listing, and clusters of ideas inside an area that are
    linked mostly to each other: candidates for a sub-area."""
    out = []
    for area in sorted(m.areas):
        own = m.in_area(area)
        if len(own) > AREA_LIMIT:
            out.append(f"{area}: {len(own)} ideas, more than one listing holds")
        inside = set(own)
        comp: dict[str, int] = {}
        for start in own:
            if start in comp:
                continue
            stack, comp[start] = [start], len(comp)
            k = comp[start]
            while stack:
                x = stack.pop()
                for y in (*m.needs.get(x, ()), *m.uses.get(x, ()),
                          *m.needed_by.get(x, ()), *m.used_by.get(x, ())):
                    if y in inside and y not in comp:
                        comp[y] = k
                        stack.append(y)
        groups: dict[int, list[str]] = {}
        for x, k in comp.items():
            groups.setdefault(k, []).append(x)
        if len(groups) > 1:
            for g in groups.values():
                if len(g) >= CLUSTER:
                    out.append(f"{area}: {len(g)} ideas linked only to each other: "
                               + ", ".join(sorted(m.name(x) for x in g)[:6])
                               + (" …" if len(g) > 6 else ""))
    return out


def calibration(m: Model) -> dict[int, tuple[int, float]]:
    """Confidence digit → (picks, share right)."""
    bins: dict[int, list[bool]] = {}
    for a in m.answers:
        if a.kind == "pick" and a.conf is not None and a.flag not in ("unseen", "pre"):
            bins.setdefault(a.conf, []).append(a.grade != "again")
    return {c: (len(xs), sum(xs) / len(xs)) for c, xs in sorted(bins.items())}


def scout(cfg: Config, task: str, timeout: int) -> str:
    if not cfg.vault:
        raise RuntimeError("no vault configured (KIOKU_VAULT or vault in config.toml)")
    if not cfg.scout_model:
        raise RuntimeError("no scout model configured (KIOKU_SCOUT_MODEL or scout_model)")
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
    """The daily pass: check, back up, duplicates, areas to split, calibration, and vault
    notes still without ideas."""
    store.init()
    report = [f"# kioku upkeep · {cfg.today}"]
    problems = lint(store, m, vault)
    report.append("problems:\n" + "\n".join(problems) if problems
                  else f"check: ok · {len(m.ideas)} ideas, {len(m.areas)} areas, "
                       f"{len(m.answers)} answers")
    report += _backup(cfg.home, cfg.today)
    d = dupes(m)
    if d:
        report.append("likely duplicates (merge by hand):\n" + "\n".join(d))
    s = to_split(m)
    if s:
        report.append("areas to consider splitting (`kioku edit a,b,c --area <new> "
                      "--new-area`):\n" + "\n".join(s))
    bins = calibration(m)
    if bins:
        report.append("confidence digits (conf · picks · right):\n" + "\n".join(
            f"  {c}  {n:>3}  {right:>4.0%}" for c, (n, right) in bins.items()))
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
    pointed = {i.vault for i in m.ideas.values() if i.vault}
    todo = sorted(((vault.developed_date(n.id) or dt.date.min, n) for n in vault.notes().values()
                   if n.status == "developed" and n.type in ("", "note")
                   and n.id not in pointed | handled),
                  key=lambda x: x[0], reverse=True)
    batch = todo[:limit]
    if not batch:
        return "vault: no developed notes without ideas"
    if not draft:
        return (f"vault: {len(todo)} developed notes without ideas; newest:\n"
                + "\n".join(f"  {n.id}  {n.title}  ({day})" for day, n in batch))
    out = []
    for day, n in batch:
        try:
            body = scout(cfg, f"Read notes/{n.id}.md and the notes it links to. Propose the "
                              f"ideas that note {n.id} states, at most 6.", timeout)
        except RuntimeError as e:
            body = f"(scout failed: {e})"
        out += ["", f"## {n.id} · {n.title} · developed {day} · proposed {cfg.today}", body]
    with proposals.open("a") as f:
        f.write("\n".join(out) + "\n")
    return (f"vault: drafted ideas for {len(batch)} of {len(todo)} notes into "
            f"proposals.md: " + ", ".join(n.id for _, n in batch))
