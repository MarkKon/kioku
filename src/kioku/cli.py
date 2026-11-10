"""kioku: what a learner has shown they know, as recall probabilities.

The loop: look ideas up (`context`), ask what the lookup does not settle
(`ask`), and pass the reply on (`answer`), which records it at once. Evidence
comes only from questions asked and answered, from verified work
(`observed`), and from names the learner marks as never met (`unmet`). A memory model turns each idea's answers into R, the chance
they recall it now.

This module parses arguments and prints; the work lives in the modules below.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import select
import shutil
import subprocess
import sys
import webbrowser
from dataclasses import replace
from importlib import resources
from pathlib import Path
from typing import NoReturn

from . import config, questions, upkeep, view
from .model import Model
from .notebook import Notebook
from .records import IDEA_KINDS, Answer, Idea
from .store import AREA, NAME, QID, SEP, Snapshot, Store, block_idea, check_block, \
    format_answer, new_id, parse_blocks
from .text import short
from .vault import Vault


class Context:
    """What every command works on, opened once per run."""

    def __init__(self):
        self.cfg = config.load()
        self.store = Store(self.cfg.home)
        self.vault = Vault(self.cfg.vault, self.cfg.cache) if self.cfg.vault else None
        self.notebook = Notebook(self.cfg.notebook) if self.cfg.notebook else None
        self._model: Model | None = None

    @property
    def model(self) -> Model:
        if self._model is None:
            self._model = Model(self.store.load(), self.cfg.now)
        return self._model


def die(msg: str) -> NoReturn:
    print(f"kioku: {msg}", file=sys.stderr)
    sys.exit(1)


def terms_of(args: list[str]) -> list[str]:
    return [t.strip() for t in " ".join(args).split(",") if t.strip()]


def stdin_text(required: bool) -> str:
    """What was piped in: a heredoc or a file. Never waits on a terminal."""
    if sys.stdin is None or sys.stdin.isatty():
        if required:
            die("pipe the ideas in, e.g. `kioku add <<'EOF'` … `EOF`")
        return ""
    if not required and not select.select([sys.stdin], [], [], 0.2)[0]:
        return ""
    return sys.stdin.read()


# -- output

LEGEND = "R = recall now, – = never asked, unmet = never met"


def fmt_r(r: float | None) -> str:
    """Rounded down, so only a fresh right answer reads 1."""
    return "–" if r is None else "1" if r >= 1 else f"{int(r * 100) / 100:.2f}".lstrip("0")


def when(m: Model, t: dt.datetime | None) -> str:
    """The time of an answer: hours and minutes today, the date before."""
    if t is None:
        return "never"
    return f"{t:%H:%M}" if t.date() == m.today else f"{t:%m-%d}"


def width_for(m: Model, ids: list[str]) -> int:
    """A name column as wide as the longest name shown (names are identities: never cut)."""
    return max([18, *(len(m.ideas[i].name) for i in ids)])


def row(m: Model, iid: str, label: str | None = None, width: int = 30) -> str:
    """name, kind, R, answers, the last answer and how it went, deepest depth shown. With a
    label (`needs`, `used by`; '' continues the one above) the row is indented under it."""
    i, rc = m.ideas[iid], m.recall(iid)
    last = "" if not rc.last else when(m, rc.last.at) if m.unmet(iid) \
        else f"{when(m, rc.last.at)} {went(rc.last)}"
    flags = []
    if rc.last and rc.last.flag == "mis":
        flags.append(f"! misconception: {short(rc.last.note.removeprefix('misconception: '), 70)}")
    head = f"  {label:<11}" if label is not None else "  "
    return (f"{head}{i.name:<{width + 1}}{i.kind:<11}{r_cell(m, iid)}  "
            f"n{rc.n:<3}{last:<12} {m.deepest(iid) or '':<9}" + "  ".join(flags)).rstrip()


def went(a: Answer) -> str:
    """How an answer went, in one word: the help it took, if any, else its outcome."""
    return a.help or a.outcome


def r_cell(m: Model, iid: str) -> str:
    """R in five characters; an idea last answered "never met" says so instead."""
    return "unmet" if m.unmet(iid) else f"R {fmt_r(m.recall(iid).r):>3}"


def coverage_line(m: Model, ids: list[str]) -> str:
    c = m.coverage(ids)
    unmet = f" · {c.unmet} unmet" if c.unmet else ""
    return (f"{c.ideas} idea{'' if c.ideas == 1 else 's'} · {c.asked} asked{unmet} · "
            f"last {when(m, c.last)}")


def warn(m: Model):
    if m.problems:
        print(f"({len(m.problems)} problem(s) in the model files; `kioku upkeep --check`)",
              file=sys.stderr)


# -- commands: looking up

def cmd_init(ctx: Context, a):
    ctx.store.init()
    if shutil.which("git") and not (ctx.cfg.home / ".git").exists():
        subprocess.run(["git", "init", "-q", str(ctx.cfg.home)], check=False)
    print(f"kioku: model in {ctx.cfg.home}; describe the learner in profile.md")


def skills_dir() -> Path:
    """The skills shipped with kioku: inside the installed package, or the repo's."""
    packaged = Path(str(resources.files("kioku"))) / "skills"
    return packaged if packaged.is_dir() else Path(__file__).resolve().parents[2] / "skills"


def cmd_skills(ctx: Context, a):
    src = skills_dir()
    names = sorted(d.name for d in src.iterdir() if (d / "SKILL.md").exists())
    if not a.to:
        print(f"skills in {src}: {', '.join(names)}")
        print("link them into your agent's skills folder: `kioku skills --to ~/.claude/skills`")
        return
    to = Path(a.to).expanduser()
    to.mkdir(parents=True, exist_ok=True)
    for n in names:
        dest = to / n
        if dest.is_symlink() and dest.resolve() == (src / n).resolve():
            print(f"{n}: already linked")
            continue
        if dest.exists() or dest.is_symlink():
            print(f"{n}: {dest} exists; left alone (remove it to link kioku's)")
            continue
        if a.copy:
            shutil.copytree(src / n, dest)
        else:
            dest.symlink_to(src / n, target_is_directory=True)
        print(f"{n}: {'copied' if a.copy else 'linked'} → {dest}")


def cmd_profile(ctx: Context, a):
    text = ctx.store.profile()
    if text is None:
        die(f"no profile yet; `kioku init`, then describe the learner in {ctx.cfg.home}/profile.md")
    print(text.strip())
    if ctx.cfg.notebook:
        print(f"\nNotebook: {ctx.cfg.notebook} (notes the agent writes: `kioku note <idea>`)")


def cmd_context(ctx: Context, a):
    m, terms = ctx.model, terms_of(a.what)
    print(f"kioku context · {ctx.cfg.now:%Y-%m-%d %H:%M} · {LEGEND}")
    if not terms:
        show_tree(m)
    for t in terms:
        print()
        if (iid := m.resolve(t)) is not None:
            show_near(m, iid) if a.near else show_idea(ctx, iid, a.answers)
        elif (area := m.area_of(t)) is not None:
            show_area(m, area)
        else:
            show_search(ctx, t)
    warn(m)


def show_tree(m: Model):
    print(f"{len(m.ideas)} ideas · {len({a.id for a in m.answers})} asked · "
          f"{len(m.answers)} answers")
    for top in m.children(""):
        print(f"  {top + '/':<40}{coverage_line(m, m.in_area(top, deep=True))}")
        for sub in m.children(top):
            print(f"    {sub.split('/', 1)[1] + '/':<38}{coverage_line(m, m.in_area(sub, deep=True))}")
    mis = [i for i in m.ideas if (last := m.recall(i).last) and last.flag == "mis"]
    if mis:
        print("misconceptions in the last answer:")
        print("\n".join(row(m, i, width=width_for(m, mis)) for i in mis))


def show_area(m: Model, area: str):
    own = m.in_area(area)
    print(f"{area} · {coverage_line(m, m.in_area(area, deep=True))}")
    w = width_for(m, own)
    print("\n".join(row(m, i, width=w) for i in own) or "  (no ideas of its own)")
    for sub in m.children(area):
        name = sub[len(area) + 1:] + "/"
        print(f"  {name:<41}{coverage_line(m, m.in_area(sub, deep=True))}")


def show_idea(ctx: Context, iid: str, answers: bool):
    m = ctx.model
    i, rc = m.ideas[iid], m.recall(iid)
    unmet = m.unmet(iid)
    last = "" if not rc.last else f" · last {when(m, rc.last.at)}" \
        + ("" if unmet else f" {went(rc.last)}")
    depth = f" ({m.deepest(iid)})" if m.deepest(iid) else ""
    r = "unmet" if unmet else f"R {fmt_r(rc.r)}"
    print(f"{i.name}{SEP}{i.kind}{SEP}{i.area}{SEP}{r} n{rc.n}{last}{depth}")
    print(f"  {i.statement}")
    extra = [f"aliases: {', '.join(i.aliases)}"] if i.aliases else []
    if i.vault:
        extra.append(f"vault: {i.vault}")
    if ctx.notebook and ctx.notebook.has(i):
        extra.append(f"note: {ctx.notebook.path(i)}")
    if extra:
        print("  " + " · ".join(extra))
    groups = (("needs", m.needs), ("uses", m.uses), ("needed by", m.needed_by),
              ("used by", m.used_by))
    w = width_for(m, [j for _, e in groups for j in e.get(iid, [])])
    for label, edges in groups:
        for k, j in enumerate(edges.get(iid, [])):
            print(row(m, j, label if k == 0 else "", w))
    broken = [n for n in (*i.needs, *i.uses) if n not in m.by_name]
    if broken:
        print(f"  edges to unknown names: {', '.join(broken)}")
    if rc.last and rc.last.flag == "mis":
        print(f"  ! last answer shows a misconception: {rc.last.note}")
    print(f"  {i.area} · {coverage_line(m, m.in_area(i.area))}")
    if answers:
        for ans in m.answers_for(iid):
            print(f"  {format_answer(ans)[2:]}")
            ask = ctx.store.ask(ans.ask)
            if ask and ans.n <= len(ask["items"]):
                print(f"      asked: {short(ask['items'][ans.n - 1]['q'], 110)}")
        if rc.r is not None:
            print(f"  R now {rc.r:.3f}, stability {rc.stability:.1f} days")


def show_near(m: Model, iid: str, limit: int = 20):
    """The ideas close to one: asked ones by rising R, then never asked, then never met."""
    i = m.ideas[iid]

    def order(x: tuple[str, str]):
        r = m.recall(x[1]).r
        return (2 if m.unmet(x[1]) else 1 if r is None else 0, r or 0)

    near = sorted(m.near(iid), key=order)
    print(f"near {i.name}{SEP}{i.area}{SEP}{len(near)} idea(s), lowest R first")
    w = width_for(m, [j for _, j in near[:limit]])
    for where, j in near[:limit]:
        print(row(m, j, where, w))
    if len(near) > limit:
        print(f"  … and {len(near) - limit} more")


def show_search(ctx: Context, term: str):
    m = ctx.model
    hits = m.search(term)
    if hits:
        print(f"\"{term}\" · no idea or area of that name; {len(hits)} idea(s) mention it")
        print("\n".join(row(m, i, width=width_for(m, hits)) for i in hits))
        regions = dict.fromkeys(m.ideas[i].area for i in hits)
        for area in list(regions)[:3]:
            print(f"  {area} · {coverage_line(m, m.in_area(area))}")
    else:
        print(f"no idea, alias or statement matches \"{term}\" ({len(m.ideas)} ideas searched)")
        near = m.nearest(term)
        for k, j in enumerate(near):
            print(row(m, j, "nearest" if k == 0 else "", width_for(m, near)))
        for area in dict.fromkeys(m.ideas[j].area for j in near[:1]):
            print(f"  {area} · {coverage_line(m, m.in_area(area))}")
    notes = ctx.vault.matching([term], {i.vault for i in m.ideas.values() if i.vault}) \
        if ctx.vault else []
    if notes:
        print("  vault notes with no idea (hints, not evidence):")
        for n in notes:
            print(f"    {n.id}  {short(n.title, 50)}  ({n.status or n.type})")


# -- commands: the graph page

def graph_page(ctx: Context, terms: list[str], depth: int, live: bool) -> str:
    m = ctx.model
    if terms:
        seeds: list[str] = []
        for t in terms:
            if (iid := m.resolve(t)) is not None:
                seeds.append(iid)
            elif (area := m.area_of(t)) is not None:
                seeds += m.in_area(area, deep=True)
            else:
                seeds += m.search(t, limit=30)
        if not seeds:
            die(f"nothing matches {', '.join(terms)}")
        data = view.graph(m, view.around(m, seeds, depth), seeds)
    else:
        data = view.graph(m)
    return view.html(data, "kioku · " + (", ".join(terms) or "everything"), live)


def cmd_graph(ctx: Context, a):
    terms = terms_of(a.what)
    if a.out:
        out = Path(a.out).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(graph_page(ctx, terms, a.depth, live=False))
        print(out)
        if not a.no_open:
            webbrowser.open(out.resolve().as_uri())
        return
    graph_page(ctx, terms, a.depth, live=False)  # fail here, not in the browser
    # every request reads the model afresh, so the page's refresh shows new answers
    view.serve(lambda: graph_page(Context(), terms, a.depth, live=True), a.port,
               lambda url: (print(f"{url}  (Ctrl-C to stop)", flush=True),
                            None if a.no_open else webbrowser.open(url)))


# -- commands: adding, editing and removing ideas

def canonical(m: Model, names: list[str], extra: dict[str, str]) -> tuple[list[str], list[str]]:
    """Edge targets (names, aliases or ids) → canonical names, and those that resolve to
    nothing. `extra` maps names being added in the same call."""
    out, bad = [], []
    for n in names:
        if n in extra:
            out.append(n)
        elif (j := m.resolve(n)) is not None:
            out.append(m.ideas[j].name)
        else:
            bad.append(n)
    return list(dict.fromkeys(out)), bad


def check_cycles(m: Model, changed: list[Idea]) -> list[str]:
    """Cycles the changed ideas would close, as readable paths."""
    ideas = dict(m.ideas)
    for i in changed:
        ideas[i.id] = i
    trial = Model(Snapshot(ideas, set(), []), m.now)
    touched = {i.id for i in changed}
    return [" → ".join(trial.name(x) for x in c) for c in trial.cycles() if c[0] in touched]


def plan_add(ctx: Context, text: str, anyway: bool,
             new_area: bool) -> tuple[list[Idea], list[str], list[str]]:
    """Idea blocks → (the ideas to add, the areas to make, what is wrong). Writes nothing."""
    m = ctx.model
    problems: list[str] = []
    blocks = parse_blocks(text, "stdin", problems, need_id=False)
    batch = {b["name"]: b for b in blocks}
    taken = set(m.ideas)
    new: list[Idea] = []
    new_areas: list[str] = []
    for b in blocks:
        where = f"{b['name']}:"
        problems += [f"{where} {p}" for p in check_block(b)]
        area = b["third"].strip("/")
        if not re.fullmatch(AREA, area):
            problems.append(f"{where} `{area}` is not an area path (e.g. maths/analysis)")
        elif area not in m.areas and area not in new_areas:
            if new_area:
                new_areas.append(area)
            else:
                near = [x for x in sorted(m.areas) if x.rsplit("/", 1)[-1] in area or area in x]
                problems.append(f"{where} no area {area} (--new-area makes it"
                                + (f"; existing: {', '.join(near[:4])}" if near else "") + ")")
        if b["name"] in m.by_name or sum(x["name"] == b["name"] for x in blocks) > 1:
            j = m.by_name.get(b["name"])
            problems.append(f"{where} the name is taken" + (f" by {j}: {short(m.ideas[j].statement, 80)}"
                                                           if j else " twice in this input"))
        elif not anyway:
            for r, j in m.similar(b["name"], b["statement"])[:3]:
                problems.append(f"{where} close to {m.ideas[j].name} ({r:.2f}): "
                                f"{short(m.ideas[j].statement, 80)} (--anyway adds it regardless)")
        names = {k: k for k in batch}
        needs, bad1 = canonical(m, b["needs"], names)
        uses, bad2 = canonical(m, b["uses"], names)
        for n in bad1 + bad2:
            hint = m.nearest(n, 1)
            problems.append(f"{where} edge to unknown idea `{n}`; add it first or drop the edge"
                            + (f" (nearest: {m.ideas[hint[0]].name})" if hint else ""))
        if b["name"] in needs + uses:
            problems.append(f"{where} an idea cannot need or use itself")
        if b["vault"] and ctx.vault and b["vault"][0] not in ctx.vault:
            problems.append(f"{where} no vault note {b['vault'][0]}")
        iid = new_id("i_", taken)
        taken.add(iid)
        new.append(replace(block_idea(b, iid, area), needs=tuple(needs), uses=tuple(uses)))
    if not problems:
        problems += [f"cycle: {c}" for c in check_cycles(m, new)]
    return new, new_areas, problems


def write_added(ctx: Context, new: list[Idea], new_areas: list[str]) -> None:
    for area in new_areas:
        ctx.store.make_area(area)
    ctx.store.write_ideas(new, ctx.model.ideas)


def cmd_add(ctx: Context, a):
    new, new_areas, problems = plan_add(ctx, stdin_text(required=True), a.anyway, a.new_area)
    if not new and not problems:
        die("no ideas read; want `## name · kind · area`, the statement, then `- needs: …`")
    if problems:
        die("nothing added:\n  " + "\n  ".join(problems))
    write_added(ctx, new, new_areas)
    after = Model(ctx.store.load(), ctx.cfg.now)
    for i in new:
        print(f"{i.id} {i.name} → {i.area} (now {len(after.in_area(i.area))} ideas)")


def edit_list(m: Model, old: tuple[str, ...], spec: str) -> tuple[tuple[str, ...], list[str]]:
    """`+a,-b,c` applied to a list of names; plain entries add."""
    out, bad = list(old), []
    for e in (x.strip() for x in spec.split(",") if x.strip()):
        sign, name = (e[0], e[1:]) if e[0] in "+-" else ("+", e)
        if sign == "-":
            j = m.resolve(name)
            target = m.ideas[j].name if j else name
            if target not in out:
                bad.append(f"no edge to `{name}` to remove")
            out = [x for x in out if x != target]
        else:
            names, unknown = canonical(m, [name], {})
            bad += [f"edge to unknown idea `{n}`" for n in unknown]
            out += [n for n in names if n not in out]
    return tuple(out), bad


def cmd_edit(ctx: Context, a):
    m = ctx.model
    targets = terms_of([a.names])
    ids = []
    for t in targets:
        j = m.resolve(t)
        if j is None:
            near = m.nearest(t, 1)
            die(f"no idea `{t}`" + (f" (nearest: {m.ideas[near[0]].name})" if near else ""))
        ids.append(j)
    statement = " ".join(stdin_text(required=False).split())
    if len(ids) > 1 and (a.name or statement):
        die("a new name or statement is for one idea at a time")
    problems: list[str] = []
    if a.area is not None:
        area = a.area.strip("/")
        if not re.fullmatch(AREA, area):
            die(f"`{area}` is not an area path (e.g. maths/analysis)")
        if area not in m.areas and not a.new_area:
            die(f"no area {area} (--new-area makes it)")
    changed: dict[str, Idea] = {}
    for j in ids:
        old = m.ideas[j]
        new = old
        if a.name:
            if not re.fullmatch(NAME, a.name):
                problems.append(f"name `{a.name}` is not kebab-case")
            elif a.name in m.by_name and m.by_name[a.name] != j:
                problems.append(f"the name {a.name} is taken by {m.by_name[a.name]}")
            new = replace(new, name=a.name)
        if a.kind:
            if a.kind not in IDEA_KINDS:
                problems.append("kind is definition, result, proof or method")
            new = replace(new, kind=a.kind)
        if a.area is not None:
            new = replace(new, area=a.area.strip("/"))
        if statement:
            new = replace(new, statement=statement)
        if a.needs:
            needs, bad = edit_list(m, new.needs, a.needs)
            problems += bad
            new = replace(new, needs=needs)
        if a.uses:
            uses, bad = edit_list(m, new.uses, a.uses)
            problems += bad
            new = replace(new, uses=uses)
        if a.aliases is not None:
            new = replace(new, aliases=tuple(x.strip() for x in a.aliases.split(",") if x.strip()))
        if a.vault is not None:
            if a.vault and ctx.vault and a.vault not in ctx.vault:
                problems.append(f"no vault note {a.vault}")
            new = replace(new, vault=a.vault or None)
        if old.name in (*new.needs, *new.uses) or (a.name and a.name in (*new.needs, *new.uses)):
            problems.append(f"{old.name} cannot need or use itself")
        if new != old:
            changed[j] = new
    if not changed and not problems:
        die("nothing to change")
    if a.name and ids[0] in changed:  # a rename rewrites the edges that name the idea
        old_name = m.ideas[ids[0]].name
        for i in m.ideas.values():
            cur = changed.get(i.id, i)
            if old_name in (*cur.needs, *cur.uses):
                changed[i.id] = replace(cur, needs=tuple(a.name if x == old_name else x
                                                         for x in cur.needs),
                                        uses=tuple(a.name if x == old_name else x for x in cur.uses))
    if not problems:
        problems += [f"cycle: {c}" for c in check_cycles(m, list(changed.values()))]
    if problems:
        die("nothing changed:\n  " + "\n  ".join(problems))
    if a.area is not None and a.area.strip("/") not in m.areas:
        ctx.store.make_area(a.area.strip("/"))
    ctx.store.write_ideas(list(changed.values()), m.ideas)
    for j in ids:
        i = changed.get(j, m.ideas[j])
        print(f"{j} {i.name} edited" + (f" → {i.area}" if a.area is not None else ""))
    others = [i for i in changed if i not in ids]
    if others:
        print(f"renamed in the edges of {len(others)} other idea(s)")


def cmd_rm(ctx: Context, a):
    m = ctx.model
    j = m.resolve(a.name)
    if j is None:
        die(f"no idea `{a.name}`")
    if not (a.why or "").strip():
        die("say why with --why; its answers move to archive.md with the reason")
    users = sorted({m.name(x) for x in (*m.needed_by.get(j, []), *m.used_by.get(j, []))})
    if users:
        die(f"{m.name(j)} is needed or used by {', '.join(users)}; edit their edges first")
    moved = ctx.store.remove_idea(m.ideas[j], m.ideas, ctx.cfg.today, a.why)
    print(f"{j} {m.name(j)} removed" + (f"; {len(moved)} answer(s) moved to archive.md"
                                        if moved else ""))


# -- commands: asking and recording

def cmd_ask(ctx: Context, a):
    m = ctx.model
    text = open(a.file).read() if a.file else stdin_text(required=True)
    ideas_text, text = questions.split_ideas(text)
    new, new_areas, problems = plan_add(ctx, ideas_text, a.anyway, a.new_area) \
        if ideas_text.strip() else ([], [], [])
    added = {i.name: i for i in new}
    title, items, block_problems = questions.parse_block(text)
    problems += block_problems
    if not items:
        problems.append("no items")
    for it in items:
        j = m.resolve(it["id"])
        if it["id"] in added:
            it["id"], it["name"] = added[it["id"]].id, it["id"]
        elif j is None:
            problems.append(f"item {it['n']}: unknown idea {it['id']} (put its `## name · kind "
                            f"· area` block above the title, or add it with `kioku add`)")
        else:
            it["id"], it["name"] = j, m.ideas[j].name
    if problems:
        die("question block not stored" + (", no idea added" if ideas_text.strip() else "")
            + ":\n  " + "\n  ".join(problems))
    if new:
        write_added(ctx, new, new_areas)
        print("kioku: added " + ", ".join(f"{i.name} ({i.id})" for i in new))
    ask = questions.new_block(new_id("q_", ctx.store.ask_ids()), title, items, ctx.cfg.now)
    ctx.store.save_ask(ask)
    rule = "─" * 60
    print(f"kioku: stored as {ask['id']}. Copy what is between the lines into your reply: it has "
          f"no answer key, unlike the block you wrote. Pass their reply on with "
          f"`kioku answer {ask['id']} \"<reply>\"`.\n{rule}\n{questions.render(ask)}\n{rule}")


def open_ask(ctx: Context, qid: str) -> dict:
    if not re.fullmatch(QID, qid):
        die(f"`{qid}` is not a block id; `kioku ask` prints one (q_…)")
    ask = ctx.store.ask(qid)
    if ask is None:
        die(f"no question block {qid}")
    return ask


# the words of before 2026-11-10, still read from agents that learned them
OLD_OUTCOME = {"good": "right", "easy": "right", "hard": "partly", "again": "wrong"}
OLD_HELP = {"good": "alone", "hard": "hint", "again": "shown"}


def item_outcome(spec: str, ask: dict) -> tuple[int, str]:
    n, _, word = spec.partition("=")
    if not n.isdigit() or not 0 < int(n) <= len(ask["items"]):
        die(f"`{spec}`: want <item>=<outcome>, e.g. 3=right")
    word = OLD_OUTCOME.get(word, word)
    if word not in ("right", "partly", "wrong"):
        die(f"`{spec}`: the outcome is right, partly or wrong")
    return int(n), word


def cmd_answer(ctx: Context, a):
    ask = open_ask(ctx, a.ask)
    reply = " ".join(a.reply)
    if not (reply or a.say or a.regrade or a.retract):
        die("pass the reply, or --say, --regrade or --retract")
    shown, recorded, waiting = [], 0, []
    if a.retract:
        if not (a.why or "").strip():
            die("say why with --why, e.g. 'misread the question' or 'misclick: meant 1a7'")
        for n in a.retract:
            if not 0 < n <= len(ask["items"]):
                die(f"no item {n}")
            if not ctx.store.take_answer(ask["id"], n, ctx.cfg.today, "retracted: " + a.why):
                die(f"item {n} of {ask['id']} has no recorded answer")
            it = ask["items"][n - 1]
            it["state"] = "open"
            it.setdefault("replies", []).append(
                {"at": ctx.cfg.now.isoformat(timespec="seconds"), "token": "retracted",
                 "thoughts": a.why})
            shown.append(f"- **{n}** retracted; its answer moved to archive.md, and the item "
                         f"is open again")
    if reply:
        g = questions.grade_reply(ask, reply, ctx.cfg.now, a.redo)
        if not g.shown:
            die("could not read the reply; entries look like `1b8 2. 3- 4?` or `5: …`")
        for answer in g.answers:
            ctx.store.record(answer)
        shown += g.shown
        recorded += len(g.answers)
        waiting += g.to_grade
    grades = [(item_outcome(s, ask), "say") for s in a.say or []] + \
             [(item_outcome(s, ask), "regrade") for s in a.regrade or []]
    if a.mis and len(grades) != 1:
        die("--mis goes with exactly one --say or --regrade")
    for (n, grade), how in grades:
        it = ask["items"][n - 1]
        if it["state"] == "open":
            die(f"item {n} has no answer yet; pass their reply first")
        if how == "say" and it["kind"] != "say":
            die(f"item {n} is a {it['kind']}; --regrade changes its outcome")
        if a.mis and grade != "wrong":
            die("a misconception is a wrong answer: --say N=wrong --mis '…'")
        ctx.store.record(questions.grade_say(ask, n, grade, ctx.cfg.now, a.mis, a.note))
        shown.append(f"- **{n}** {grade}")
        recorded += 1
        waiting = [w for w in waiting if w != n]
    ctx.store.save_ask(ask)
    print("\n".join(shown))
    notes = [f"judge {n}: kioku answer {ask['id']} --say {n}=right|partly|wrong "
             f"[--mis 'believed X → Y']" for n in waiting]
    if recorded:
        notes.append(f"{recorded} answer(s) recorded")
    if notes:
        print("\n<!-- for the agent: " + "; ".join(notes) + " -->")


def cmd_observed(ctx: Context, a):
    m = ctx.model
    pairs = []
    for spec in a.ideas:
        name, _, grade = spec.rpartition("=")
        j = m.resolve(name)
        if j is None:
            die(f"no idea `{name}` (add it with `kioku add`)")
        grade = OLD_HELP.get(grade, grade)
        if grade not in ("alone", "hint", "shown"):
            die(f"`{spec}`: observed work is recorded as alone, hint or shown")
        pairs.append((j, grade))
    notes: dict[str, str] = {}
    common = ""
    for note in a.note or []:
        head, sep, rest = note.partition(":")
        j = m.resolve(head.strip()) if sep else None
        if j is not None:
            notes[j] = rest.strip()
        else:
            common = (common + " " + note).strip()
    qid = new_id("q_", ctx.store.ask_ids())
    items = [{"n": k, "kind": "observed", "id": j, "name": m.ideas[j].name, "depth": "use",
              "q": a.step, "options": [], "why": "", "ref": "", "state": "done"}
             for k, (j, _g) in enumerate(pairs, 1)]
    ctx.store.save_ask({"id": qid, "title": f"observed · {a.step}",
                        "asked": ctx.cfg.now.isoformat(timespec="seconds"), "observed": True,
                        "items": items})
    for k, (j, grade) in enumerate(pairs, 1):
        note = "observed: " + (notes.get(j) or common or "verified by the step's tests")
        ctx.store.record(Answer(ctx.cfg.now, j, "observed", "right", qid, k, depth="use",
                                note=note, help=None if grade == "alone" else grade))
    print(f"{len(pairs)} observed answer(s) recorded under {qid}: "
          + ", ".join(f"{m.name(j)} {g}" for j, g in pairs))


def cmd_unmet(ctx: Context, a):
    m = ctx.model
    ids = []
    for name in (t.strip() for arg in a.ideas for t in arg.split(",") if t.strip()):
        j = m.resolve(name)
        if j is None:
            die(f"no idea `{name}` (add it with `kioku add`, then record it)")
        ids.append(j)
    ids = list(dict.fromkeys(ids))
    asked = [m.name(j) for j in ids if any(x.flag != "pre" for x in m.answers_for(j))]
    if asked:
        die(f"{', '.join(asked)} already has answers; ask a question about it instead")
    qid = new_id("q_", ctx.store.ask_ids())
    what = " ".join((a.note or "").split())
    items = [{"n": k, "kind": "triage", "id": j, "name": m.ideas[j].name, "depth": None,
              "q": "never met?", "options": [], "why": "", "ref": "", "state": "done"}
             for k, j in enumerate(ids, 1)]
    ctx.store.save_ask({"id": qid, "title": "triage" + (f" · {what}" if what else ""),
                        "asked": ctx.cfg.now.isoformat(timespec="seconds"), "triage": True,
                        "items": items})
    for k, j in enumerate(ids, 1):
        ctx.store.record(Answer(ctx.cfg.now, j, "triage", "unmet", qid, k,
                                note="never met it (triage)"))
    print(f"{len(ids)} idea(s) recorded as never met under {qid}: "
          + ", ".join(m.name(j) for j in ids))


def span(text: str) -> dt.timedelta:
    m = re.fullmatch(r"(\d+)\s*([mhd])", text.strip())
    if not m:
        die(f"`{text}`: want a span such as 90m, 3h or 2d")
    return dt.timedelta(**{{"m": "minutes", "h": "hours", "d": "days"}[m[2]]: int(m[1])})


def cmd_log(ctx: Context, a):
    m = ctx.model
    since = ctx.cfg.now - span(a.since)
    asks = [x for q in ctx.store.ask_ids()
            if (x := ctx.store.ask(q)) and dt.datetime.fromisoformat(x["asked"]) >= since]
    asks.sort(key=lambda x: x["asked"])
    by = {(x.ask, x.n): x for x in m.answers}
    print(f"kioku log · since {since:%Y-%m-%d %H:%M} · {len(asks)} block(s)")
    waiting = 0
    for ask in asks:
        print(f"\n{ask['id']}{SEP}{when(m, dt.datetime.fromisoformat(ask['asked']))}{SEP}"
              f"{ask['title'] or 'Questions'}")
        w = max(len(m.name(it["id"])) for it in ask["items"])
        for it in ask["items"]:
            ans = by.get((ask["id"], it["n"]))
            if ans is None:
                what = {"to-grade": "answered, not graded yet", "done": "answer set aside",
                        "shown": "reference shown, not graded yet"}.get(it.get("state"), "open")
                waiting += it.get("state") != "done"
            elif ans.outcome == "unmet":
                what = "never met"
            else:
                what = " ".join(x for x in (
                    ans.outcome, "" if ans.conf is None else str(ans.conf), ans.help or "",
                    ans.flag or "",
                    ans.depth or "", "taught" if ans.taught else "probe" if ans.probe else "")
                    if x)
                what += f" — {short(ans.note, 70)}" if ans.note else ""
            print(f"  {it['n']:>2} {m.name(it['id']):<{w}}  {it['kind']:<8} {what}")
    if waiting:
        print(f"\n{waiting} item(s) without a recorded answer")


def cmd_note(ctx: Context, a):
    if ctx.notebook is None:
        die("no notebook; set `notebook = \"<folder>\"` in config.toml in the model folder "
            "(or KIOKU_NOTEBOOK)")
    m = ctx.model
    for t in terms_of(a.ideas):
        j = m.resolve(t)
        if j is None:
            die(f"no idea `{t}` (add it with `kioku add`)")
        path, made = ctx.notebook.ensure(m, m.ideas[j])
        print(f"{path}" + ("  (new: write below the marked line)" if made else ""))
    n = ctx.notebook.write_indexes(m)
    if not a.ideas:
        print(f"{n} area index note(s) written in {ctx.notebook.notes}")


# -- commands: upkeep

def cmd_upkeep(ctx: Context, a):
    if a.check:
        problems = upkeep.lint(ctx.store, ctx.model, ctx.vault)
        m = ctx.model
        print("\n".join(problems) if problems else
              f"ok · {len(m.ideas)} ideas, {len(m.areas)} areas, {len(m.answers)} answers")
        if problems:
            sys.exit(1)
        return
    print(upkeep.run(ctx.cfg, ctx.store, ctx.model, ctx.vault, a.scout, a.limit, a.timeout))


# --------------------------------------------------------------------------
# The formats live here, in the help, so the skills point at them instead of
# repeating them.

ASK_FORMAT = """\
A block, on stdin or in a file:

  # <title>
  <n> pick|write|say <idea> [state|use|transfer] [pre|taught|probe]: <question>
    * <the right option>                         pick: exactly one
    - <a wrong option> :: <the misconception a confident pick of it shows>
    ? <explanation, shown with the verdict>
    = <reference answer>                         write and say

<idea> is a name, alias or id. The depth is what the item demands: state (recall
it), use (apply it when named, the default), transfer (reach for it where nothing
points to it). pre: asked before the idea is taught; the answer is kept but is
not evidence of memory. taught: the session explained the idea before this
question (a worked example, a correction). probe: asked to find out what they
already held, before any teaching; a right answer then counts as knowledge
they had before, and lasts longer in the model the surer it was. Both marks
are recorded with the answer.

Ideas the block asks about that have no entry yet can be added in the same
call: put their blocks (`## name · kind · area`, see `kioku add -h`) above the
title. Nothing is added unless the block is stored.

Replies, all items on one line, e.g. `1b8 2. 3: the variance shrinks`:
  pick   a letter and a confidence digit: `1b8` (option b, 80% sure)
  write  `2.` once written; then `2=` right, `2~` a slip, `2x` wrong
  say    `3: <free text>`; judge it with `kioku answer <q_id> --say 3=right`
  any    `4-` never met it, `4?` seen it but cannot produce it

The block is stored with its key and printed with its id, options shuffled.
The learner never sees tool output: copy the printed block into your reply.

Example:
  kioku ask <<'EOF'
  # girsanov
  1 pick girsanov: Under $Q$ with $dQ/dP = e^{\\theta W_T - \\theta^2 T/2}$, $W_t - \\theta t$ is
    * a $Q$-Brownian motion
    - a $Q$-martingale but not a Brownian motion :: keeps only the martingale property
    - a $P$-Brownian motion
    ? Under $Q$ the drift is removed and the quadratic variation kept.
  2 say girsanov-proof: In one line, where does the drift come from?
    = Itô on the density gives $dZ = \\theta Z\\,dW$, which shifts $W$ by $\\theta\\,dt$ under $Q$.
  EOF
"""

ANSWER_FORMAT = """\
An answer records what happened: right, partly (right with a slip), wrong, or
never met. You judge a say item with --say N=right|partly|wrong; picks and
write items are settled by the reply. A right pick at chance confidence is a
guess: recorded, not counted. A wrong pick at 80% or more is a misconception.
What the answer does to R is the memory model's business: it reads a pick's
confidence against the learner's own record at that digit.

A reply outside the format ("between a and b", a letter without a digit) is
yours to settle with the learner first.
"""

ADD_FORMAT = """\
Ideas on stdin, one block each:

  ## <name> · <kind> · <area>
  <statement: what a right answer must match; may span lines>
  - needs: <name>, …      ideas it cannot be followed without
  - uses: <name>, …       ideas that doing it, or answering on it, carries out
  - aliases: <other names>
  - vault: <note id>      the note in the notes folder that states it

name: kebab-case, unique, no "and". kind: definition | result | proof | method.
area: a path such as maths/analysis. The edge lines are optional; an edge may
name an idea added earlier in the same input. Refuses, and shows what it found:
a name or close statement that exists (--anyway), an edge to an unknown idea, an
unknown area (--new-area), an edge that closes a cycle.
"""

OBSERVED_FORMAT = """\
One call per step, after its tests pass, for each idea the step carried out,
with the help it took:
  alone  done from the brief and its materials
  hint   needed help beyond the brief, or a slip
  shown  handed the answer
An idea taught within the same step is left out.

Example:
  kioku observed register-buffer=hint tensor-broadcasting=alone \\
    --step "3 · causal head" --note "register-buffer: needed the device demo"
"""

UNMET_FORMAT = """\
Triage: show the learner a lettered list of idea names in your reply and ask
which they have never met. Record the ones they mark, in one call:

  kioku unmet specificity likelihood-ratio odds --note "opening of the lesson"

A claim of never having met an idea is recorded. A name left unmarked is not
evidence of anything: it still gets a real question before work rests on it.
Each idea must exist (`kioku add`) and have no answers yet.
"""


NOTE_FORMAT = """\
The notebook is a folder of notes the agent writes for the learner to look
things up in: `notebook = "<folder>"` in config.toml. One note per idea, named
by its id, in the format of a vault (frontmatter, `[[id|label]]` links).

  kioku note girsanov        prints the note's path, making its skeleton if new:
                             the statement and links along the idea's edges
  kioku note                 rewrites the index note of every area with notes

Write the body with your file tools, below the marked line: the formula or
signature, one example, a figure where it helps. Keep it terse. Notes are
never evidence.
"""


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="kioku", description=(__doc__ or "").split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_, epilog=None):
        sp = sub.add_parser(name, help=help_, description=help_, epilog=epilog,
                            formatter_class=argparse.RawDescriptionHelpFormatter)
        sp.set_defaults(fn=fn)
        return sp

    add("init", cmd_init, "create the model folder, its profile and its git repo")
    add("profile", cmd_profile, "who the learner is")
    sp = add("skills", cmd_skills, "list the skills kioku ships, or link them into an agent's "
             "skills folder")
    sp.add_argument("--to", help="the skills folder, e.g. ~/.claude/skills or ~/.agents/skills")
    sp.add_argument("--copy", action="store_true", help="copy instead of linking")
    sp = add("context", cmd_context, "look up an area, ideas or terms (comma-separated); "
             "no argument: the top of the area tree")
    sp.add_argument("what", nargs="*")
    sp.add_argument("--answers", action="store_true", help="every answer, with its question")
    sp.add_argument("--near", action="store_true",
                    help="for an idea: the ideas within two edges and in the areas around "
                         "it, lowest R first")
    sp = add("graph", cmd_graph, "draw the model (or the neighbourhood of some ideas or an area) "
             "as an interactive graph in the browser")
    sp.add_argument("what", nargs="*")
    sp.add_argument("--depth", type=int, default=2, help="steps along edges (default 2)")
    sp.add_argument("--out", help="write a static page here instead of serving it (no refresh)")
    sp.add_argument("--port", type=int, default=0, help="port to serve on (default: any free)")
    sp.add_argument("--no-open", action="store_true", help="do not open a browser")

    sp = add("add", cmd_add, "add ideas from stdin; prints their ids", ADD_FORMAT)
    sp.add_argument("--anyway", action="store_true", help="add despite a likely duplicate")
    sp.add_argument("--new-area", action="store_true", help="make an area that does not exist")
    sp = add("edit", cmd_edit, "change ideas (comma-separated names); a new statement on stdin")
    sp.add_argument("names")
    sp.add_argument("--name", help="rename it; the edges that name it follow")
    sp.add_argument("--kind")
    sp.add_argument("--area", help="move it (them) to this area")
    sp.add_argument("--new-area", action="store_true", help="make the area if it does not exist")
    sp.add_argument("--needs", help="+name to add an edge, -name to remove one; comma-separated")
    sp.add_argument("--uses", help="+name to add an edge, -name to remove one; comma-separated")
    sp.add_argument("--aliases", help="replaces the aliases; '' clears them")
    sp.add_argument("--vault", help="'' clears it")
    sp = add("rm", cmd_rm, "remove an idea nothing needs or uses; its answers move to archive.md")
    sp.add_argument("name")
    sp.add_argument("--why", help="kept with the archived answers")

    sp = add("ask", cmd_ask, "store a question block (file or stdin), print it shuffled with its id",
             ASK_FORMAT)
    sp.add_argument("file", nargs="?")
    sp.add_argument("--anyway", action="store_true",
                    help="add an idea written above the block despite a likely duplicate")
    sp.add_argument("--new-area", action="store_true",
                    help="make the area of an idea written above the block")
    sp = add("answer", cmd_answer, "read the learner's one-line reply to a block and record it "
             "now; also judge say items, change an outcome, retract", ANSWER_FORMAT)
    sp.add_argument("ask", help="the block id, q_…")
    sp.add_argument("reply", nargs="*")
    sp.add_argument("--redo", action="store_true",
                    help="answer an item again; the old answer moves to archive.md")
    sp.add_argument("--say", action="append", metavar="N=OUTCOME",
                    help="judge a say item: right, partly or wrong")
    sp.add_argument("--regrade", action="append", metavar="N=OUTCOME",
                    help="change the outcome of an answered item")
    sp.add_argument("--mis", help="the misconception it shows: 'believed X → Y' (with wrong)")
    sp.add_argument("--note", help="a note for --say or --regrade")
    sp.add_argument("--retract", action="append", type=int, metavar="N",
                    help="set an answer aside (misread, misclick); the item opens again")
    sp.add_argument("--why", help="why a retracted answer does not count")
    sp = add("observed", cmd_observed, "record a step of verified pairing work: "
             "name=alone|hint|shown for each idea it carried out", OBSERVED_FORMAT)
    sp.add_argument("ideas", nargs="+", metavar="NAME=HELP")
    sp.add_argument("--step", required=True, help="the step, e.g. '3 · causal head'")
    sp.add_argument("--note", action="append",
                    help="what was observed; 'name: …' for one idea, else for all")

    sp = add("unmet", cmd_unmet, "record the ideas the learner marked as never met in a "
             "triage", UNMET_FORMAT)
    sp.add_argument("ideas", nargs="+", metavar="NAME")
    sp.add_argument("--note", help="what the triage was for")

    sp = add("log", cmd_log, "what was asked and answered lately, block by block")
    sp.add_argument("--since", default="3h", help="how far back: 90m, 3h, 2d (default 3h)")
    sp = add("note", cmd_note, "the notebook note of an idea (made if new); no argument: "
             "rewrite the area indexes", NOTE_FORMAT)
    sp.add_argument("ideas", nargs="*")

    sp = add("upkeep", cmd_upkeep, "daily: check, back up, duplicates, areas to split, "
             "calibration, vault notes without ideas")
    sp.add_argument("--check", action="store_true",
                    help="only check that every file parses and every name, id and answer "
                         "resolves (exit 1 on problems)")
    sp.add_argument("--scout", action="store_true", help="draft ideas for vault notes")
    sp.add_argument("--limit", type=int, default=5)
    sp.add_argument("--timeout", type=int, default=600)
    return ap


def main(argv: list[str] | None = None):
    ap = parser()
    args = list(sys.argv[1:] if argv is None else argv)
    # `--needs -x` removes an edge; argparse would read `-x` as an option
    for k in range(len(args) - 1, 0, -1):
        if args[k - 1] in ("--needs", "--uses") and args[k].startswith("-"):
            args[k - 1:k + 1] = [f"{args[k - 1]}={args[k]}"]
    a = ap.parse_args(args)
    a.fn(Context(), a)


if __name__ == "__main__":
    main()
