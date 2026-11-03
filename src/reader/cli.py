"""reader: what a reader has shown they know, as recall probabilities.

The loop: look an idea up (`check`), ask what the lookup does not settle
(`ask`), and pass the reply on (`answer`, `grade`), which records it at once.
Evidence comes only from questions asked and answered. A memory model turns
each id's answers into R, the chance they recall it now.

This module parses arguments and prints; the work lives in the modules below.
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import NoReturn

from . import config, questions, upkeep, view
from .memory import Recall
from .model import Model
from .records import GRADES, Chain, Prop
from .store import ID, QID, SEP, Store, format_answer, new_id, parse_chain
from .text import norm, short
from .vault import Vault


class Context:
    """What every command works on, opened once per run."""

    def __init__(self):
        self.cfg = config.load()
        self.store = Store(self.cfg.home)
        self.vault = Vault(self.cfg.vault, self.cfg.cache) if self.cfg.vault else None
        self._model: Model | None = None

    @property
    def model(self) -> Model:
        if self._model is None:
            self._model = Model(self.store.load(), self.cfg.now)
        return self._model


def die(msg: str) -> NoReturn:
    print(f"reader: {msg}", file=sys.stderr)
    sys.exit(1)


def terms_of(args: list[str]) -> list[str]:
    return [t.strip() for t in " ".join(args).split(",") if t.strip()]


# -- output

def fmt_r(r: float | None) -> str:
    """Rounded down, so only a fresh right answer reads 1."""
    return "–" if r is None else "1" if r >= 1 else f"{int(r * 100) / 100:.2f}".lstrip("0")


def when(m: Model, t: dt.datetime) -> str:
    """The time of an answer: hours and minutes today, the date before."""
    return f"{t:%H:%M}" if t.date() == m.today else f"{t:%m-%d}"


def row(m: Model, iid: str, width: int = 28) -> str:
    """id, name, R, answers, last answer, and what else an agent needs to judge."""
    rc: Recall = m.recall(iid)
    p = m.props.get(iid)
    last = rc.last
    last_s = f"{when(m, last.at)} {last.grade}" if last else "no evidence"
    notes = []
    if last and last.flag == "mis":
        notes.append(f"! last answer: {short(last.note or 'misconception', 80)}")
    if last and last.flag == "unseen":
        notes.append("last answer: never met it")
    if p and p.vault:
        notes.append(f"vault {p.vault}")
    notes.append(short(p.statement, 70) if p else "step: " + short(m.chains[iid].step, 70))
    return (f"  {iid:<8}{short(m.name(iid), width):<{width + 1}}R {fmt_r(rc.r):>3}  "
            f"n{rc.n:<2} {last_s:<12}  " + " · ".join(notes))


def warn(m: Model):
    if m.problems:
        print(f"({len(m.problems)} parse problem(s); `reader lint`)", file=sys.stderr)


# -- commands: looking up

def cmd_init(ctx: Context, a):
    ctx.store.init()
    if shutil.which("git") and not (ctx.cfg.home / ".git").exists():
        subprocess.run(["git", "init", "-q", str(ctx.cfg.home)], check=False)
    print(f"reader: model in {ctx.cfg.home}; describe the reader in profile.md")


def cmd_profile(ctx: Context, a):
    text = ctx.store.profile()
    if text is None:
        die(f"no profile yet; `reader init`, then describe the reader in {ctx.cfg.home}/profile.md")
    print(text.strip())


def cmd_check(ctx: Context, a):
    m, terms = ctx.model, terms_of(a.terms)
    if not terms:
        die("check needs ids or terms, e.g. `reader check p_k2x9, girsanov, #sde`")
    found = m.lookup(terms, a.depth, None if a.all else 30)
    print(f"reader check · {', '.join(terms)} · {ctx.cfg.now:%Y-%m-%d %H:%M}"
          f" · R = recall probability now, – = no evidence")
    for title, ids in (("matched", found.matched), ("rests on (chains, then premises)",
                       found.rests_on), ("rests on it", found.rests_on_it)):
        if ids:
            print(title)
            print("\n".join(row(m, i) for i in ids))
    notes = ctx.vault.matching([t for t in terms if not t.startswith("#") and not m.exists(t)],
                               {p.vault for p in m.props.values() if p.vault}) if ctx.vault else []
    if notes:
        print("vault notes with no proposition (hints, not evidence)")
        for n in notes:
            print(f"  {n.id}  {short(n.title, 50)}  ({n.status or n.type})")
    if not found.matched and not notes:
        print("nothing recorded; add the idea with `reader new prop`, then ask")
    warn(m)


def graph_page(ctx: Context, terms: list[str], depth: int, live: bool) -> str:
    m = ctx.model
    if terms:
        found = m.lookup(terms, depth, None)
        if not found.matched:
            die(f"nothing matches {', '.join(terms)}")
        data = view.graph(m, found.matched + found.rests_on + found.rests_on_it, found.matched)
    else:
        data = view.graph(m)
    return view.html(data, "reader · " + (", ".join(terms) or "everything"), live)


def cmd_graph(ctx: Context, a):
    terms = terms_of(a.terms)
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


def cmd_find(ctx: Context, a):
    m, terms = ctx.model, terms_of(a.terms)
    hits = m.find(terms, a.limit)
    for pid in hits:
        p = m.props[pid]
        print(f"{pid:<8}{short(p.name, 28):<29}{short(p.statement, 100)}")
    for c in m.chains.values():
        if any(pid in (c.conclusion, *c.premises) for pid in hits[:3]):
            print(f"{c.id:<8}{short(m.name(c.id), 120)}")
    notes = ctx.vault.matching(terms, {p.vault for p in m.props.values() if p.vault},
                               a.limit) if ctx.vault else []
    for n in notes:
        print(f"vault {n.id}  {short(n.title, 50)}  ({n.status or n.type})")
    if not hits and not notes:
        print("no match")


def cmd_show(ctx: Context, a):
    m = ctx.model
    if a.id in m.props:
        p = m.props[a.id]
        print(f"{p.id} · {p.name} · {p.statement}" + (f" · topics: {', '.join(p.topics)}"
                                                      if p.topics else ""))
    elif a.id in m.chains:
        c = m.chains[a.id]
        print(f"{c.id} · {m.name(c.id)} · step: {c.step}")
    else:
        die(f"no proposition or chain {a.id}")
    for ans in m.answers_for(a.id):
        print(f"  {format_answer(ans)[2:]}")
        ask = ctx.store.ask(ans.ask)
        if ask and ans.n <= len(ask["items"]):
            print(f"      asked: {short(ask['items'][ans.n - 1]['q'], 110)}")
    rc = m.recall(a.id)
    if rc.r is None:
        print(f"  no graded answer yet ({rc.n} answer(s))")
    else:
        print(f"  R now {rc.r:.3f}, stability {rc.stability:.1f} days, {rc.n} answer(s)")


def cmd_status(ctx: Context, a):
    m = ctx.model
    answered = [i for i in m.ids() if m.recall(i).n]
    print(f"reader · {ctx.cfg.today} · {len(m.props)} propositions, {len(m.chains)} chains, "
          f"{len(m.answers)} answers on {len(answered)} ids")
    topics: dict[str, list[str]] = {}
    for p in m.props.values():
        for t in p.topics or ("(none)",):
            topics.setdefault(t, []).append(p.id)
    for t, ids in sorted(topics.items(), key=lambda kv: -len(kv[1]))[:15]:
        rs = [r for i in ids if (r := m.recall(i).r) is not None]
        mean = f"  mean R {sum(rs) / len(rs):.2f}" if rs else ""
        print(f"  #{t:<24}{len(ids):>3} props, {len(rs):>2} with evidence{mean}")
    mis = [i for i in m.ids() if (last := m.recall(i).last) and last.flag == "mis"]
    if mis:
        print("misconceptions shown in the last answer:")
        for i in mis:
            print(f"  {i}  {short(m.name(i), 30)}  {short(m.recall(i).last.note, 80)}")
    if m.answers:
        last = max(m.answers, key=lambda x: x.at)
        print(f"last answer: {last.at:%Y-%m-%d %H:%M} ({last.ask})")
    warn(m)


# -- commands: adding, amending and deleting propositions and chains

def split_list(s: str | None) -> tuple[str, ...]:
    return tuple(x.strip() for x in (s or "").split(",") if x.strip())


def check_prop(ctx: Context, p: Prop, force: bool):
    """Die unless p is a well-formed proposition whose name no other one has."""
    for text in (p.name, p.statement, *p.topics, *p.aliases, p.vault or ""):
        if SEP.strip() in text or "\n" in text:
            die("fields may not contain ` · ` or newlines")
    if not p.name.strip() or not p.statement.strip():
        die("a proposition needs a name and a statement")
    clash = [q for q in ctx.model.props.values() if norm(q.name) == norm(p.name) and q.id != p.id]
    if clash and not force:
        die(f"{clash[0].id} already has this name: {clash[0].statement} (--force to add anyway)")
    if p.vault and ctx.vault and p.vault not in ctx.vault:
        die(f"no vault note {p.vault}")


def check_chain(ctx: Context, text: str, step: str, iid: str = "") -> tuple[tuple[str, ...], str]:
    """Resolve `p_a p_b => p_c` (ids or names) to premises and conclusion, or die."""
    m = ctx.model
    parsed = parse_chain(text, names=True)
    if not parsed:
        die("want: p_a p_b => p_c (ids or names)")

    def resolve(x):
        if re.fullmatch(ID, x):
            return x
        hits = [p.id for p in m.props.values() if norm(p.name) == norm(x)]
        if len(hits) != 1:
            die(f"`{x}` names {len(hits)} propositions; use an id")
        return hits[0]

    premises, conclusion = tuple(map(resolve, parsed[0])), resolve(parsed[1])
    for pid in (*premises, conclusion):
        if pid not in m.props:
            die(f"no proposition {pid}")
    if conclusion in premises:
        die("a conclusion cannot be its own premise")
    for c in m.chains.values():
        if c.id != iid and (sorted(c.premises), c.conclusion) == (sorted(premises), conclusion):
            die(f"{c.id} is already this chain")
    if not step.strip() or SEP.strip() in step or "\n" in step:
        die("a step is required and may not contain ` · ` or newlines")
    return premises, conclusion


def cmd_new_prop(ctx: Context, a):
    p = Prop(new_id("p_", set(ctx.model.ids())), a.name, a.statement, split_list(a.topics),
             split_list(a.aliases), a.vault)
    check_prop(ctx, p, a.force)
    ctx.store.add_prop(p)
    print(p.id)


def cmd_new_chain(ctx: Context, a):
    premises, conclusion = check_chain(ctx, " ".join(a.chain), a.step)
    c = Chain(new_id("c_", set(ctx.model.ids())), premises, conclusion, a.step)
    ctx.store.add_chain(c)
    print(c.id)


def cmd_amend(ctx: Context, a):
    m = ctx.model
    if a.id in m.props:
        if a.chain is not None or a.step is not None:
            die(f"{a.id} is a proposition: amend --name, --statement, --topics, --aliases, --vault")
        old = m.props[a.id]
        new = Prop(old.id, old.name if a.name is None else a.name,
                   old.statement if a.statement is None else a.statement,
                   old.topics if a.topics is None else split_list(a.topics),
                   old.aliases if a.aliases is None else split_list(a.aliases),
                   old.vault if a.vault is None else (a.vault or None))
        check_prop(ctx, new, a.force)
        claim_changed = new.statement != old.statement
    elif a.id in m.chains:
        if any(x is not None for x in (a.name, a.statement, a.topics, a.aliases, a.vault)):
            die(f"{a.id} is a chain: amend --chain 'p_a p_b => p_c' or --step")
        old = m.chains[a.id]
        step = old.step if a.step is None else a.step
        text = a.chain if a.chain is not None else f"{' '.join(old.premises)} => {old.conclusion}"
        premises, conclusion = check_chain(ctx, text, step, old.id)
        new = Chain(old.id, premises, conclusion, step)
        claim_changed = (set(new.premises), new.conclusion, new.step) != \
                        (set(old.premises), old.conclusion, old.step)
    else:
        die(f"no proposition or chain {a.id}")
    if new == old:
        die("nothing to change")
    n = len(m.answers_for(a.id))
    if claim_changed and n and not a.force:
        die(f"{a.id} has {n} answer(s), given to the claim as it reads now. Fix its wording "
            f"with --force; if the claim itself is different, add a new id and delete this one")
    ctx.store.replace(new)
    print(f"{a.id} amended")


def cmd_delete(ctx: Context, a):
    m = ctx.model
    if not m.exists(a.id):
        die(f"no proposition or chain {a.id}")
    used = [c.id for c in m.chains.values() if a.id in (*c.premises, c.conclusion)]
    if used:
        die(f"chains rest on {a.id}: {', '.join(used)}; delete or amend them first")
    n = len(m.answers_for(a.id))
    if n and not a.force:
        die(f"{a.id} has {n} answer(s); --force deletes it and moves them to archive.md")
    moved = ctx.store.remove(a.id, ctx.cfg.today, a.why or "")
    print(f"{a.id} deleted" + (f"; {len(moved)} answer(s) moved to archive.md" if moved else ""))


# -- commands: asking and recording

def cmd_ask(ctx: Context, a):
    m = ctx.model
    text = open(a.file).read() if a.file else sys.stdin.read()
    title, items, problems = questions.parse_block(text)
    if not items:
        problems.append("no items")
    problems += [f"item {it['n']}: unknown id {it['id']} (add it with `reader new`)"
                 for it in items if not m.exists(it["id"])]
    if problems:
        die("question block not stored:\n  " + "\n  ".join(problems))
    ask = questions.new_block(new_id("q_", ctx.store.ask_ids()), title, items, ctx.cfg.now)
    ctx.store.save_ask(ask)
    print(questions.render(ask))


def open_ask(ctx: Context, qid: str) -> dict:
    if not re.fullmatch(QID, qid):
        die(f"`{qid}` is not a block id; `reader ask` prints one (q_…)")
    ask = ctx.store.ask(qid)
    if ask is None:
        die(f"no question block {qid}")
    return ask


def cmd_answer(ctx: Context, a):
    ask = open_ask(ctx, a.ask)
    g = questions.grade_reply(ask, " ".join(a.reply), ctx.cfg.now, a.redo)
    if not g.shown:
        die("could not read the reply; entries look like `1b8 2. 3- 4?` or `5: …`")
    for answer in g.answers:
        ctx.store.record(answer)
    ctx.store.save_ask(ask)
    print("\n".join(g.shown))
    notes = [f"grade {n}: reader grade {ask['id']} {n} good|hard|again [--mis 'believed X → Y']"
             for n in g.to_grade]
    if g.answers:
        notes.append(f"{len(g.answers)} answer(s) recorded")
    if notes:
        print("\n<!-- for the agent: " + "; ".join(notes) + " -->")


def cmd_grade(ctx: Context, a):
    ask = open_ask(ctx, a.ask)
    if not 0 < a.n <= len(ask["items"]):
        die(f"no item {a.n}")
    if a.grade not in GRADES:
        die("grade is again, hard, good or easy")
    if ask["items"][a.n - 1]["state"] == "open":
        die(f"item {a.n} has no answer yet; pass their reply to `reader answer {ask['id']}`")
    if a.mis and a.grade != "again":
        die("a misconception is graded again")
    ctx.store.record(questions.grade_say(ask, a.n, a.grade, ctx.cfg.now, a.mis, a.note))
    ctx.store.save_ask(ask)
    print(f"{a.n} graded {a.grade}, recorded")


def cmd_retract(ctx: Context, a):
    ask = open_ask(ctx, a.ask)
    if not 0 < a.n <= len(ask["items"]):
        die(f"no item {a.n}")
    if not (a.why or "").strip():
        die("say why with --why, e.g. 'misread the question' or 'misclick: meant 1a7'")
    moved = ctx.store.take_answer(ask["id"], a.n, ctx.cfg.today, "retracted: " + a.why)
    if not moved:
        die(f"item {a.n} of {ask['id']} has no recorded answer")
    it = ask["items"][a.n - 1]
    it["state"] = "open"
    it.setdefault("replies", []).append(
        {"at": ctx.cfg.now.isoformat(timespec="seconds"), "token": "retracted", "thoughts": a.why})
    ctx.store.save_ask(ask)
    print(f"{ask['id']}/{a.n} retracted; its answer moved to archive.md. The item is open "
          f"again: pass a new reply with `reader answer {ask['id']} \"{a.n}…\"`, or ask a new item")


# -- commands: upkeep

def cmd_lint(ctx: Context, a):
    problems = upkeep.lint(ctx.store, ctx.model, ctx.vault)
    print("\n".join(problems) if problems else
          f"ok · {len(ctx.model.props)} propositions, {len(ctx.model.chains)} chains, "
          f"{len(ctx.model.answers)} answers")
    if problems:
        sys.exit(1)


def cmd_dupes(ctx: Context, a):
    print("\n".join(upkeep.dupes(ctx.model, a.threshold)) or "no likely duplicates")


def cmd_calib(ctx: Context, a):
    bins = upkeep.calibration(ctx.model)
    if not bins:
        print("no picks with confidence yet")
        return
    print("conf  n   right  (said)")
    for c, (n, right) in bins.items():
        print(f"  {c}  {n:>3}  {right:>5.0%}  ({c}0%)")


def cmd_upkeep(ctx: Context, a):
    print(upkeep.run(ctx.cfg, ctx.store, ctx.model, ctx.vault, a.scout, a.limit, a.timeout))


def cmd_scout(ctx: Context, a):
    try:
        print(upkeep.scout(ctx.cfg, " ".join(a.task), a.timeout))
    except RuntimeError as e:
        die(str(e))


# --------------------------------------------------------------------------

def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="reader", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, help_):
        sp = sub.add_parser(name, help=help_, description=help_)
        sp.set_defaults(fn=fn)
        return sp

    add("init", cmd_init, "create the model folder, its profile and its git repo")
    add("profile", cmd_profile, "who the reader is")
    sp = add("check", cmd_check, "look ideas up: each with what it rests on, what rests on it, "
             "and R per id (ids or terms, comma-separated; #topic)")
    sp.add_argument("terms", nargs="+")
    sp.add_argument("--depth", type=int, default=2, help="levels of premises (default 2)")
    sp.add_argument("--all", action="store_true", help="no limit on matches")
    sp = add("graph", cmd_graph, "draw the model (or the neighbourhood of some terms) as an "
             "interactive graph in the browser")
    sp.add_argument("terms", nargs="*")
    sp.add_argument("--depth", type=int, default=2, help="levels of premises (default 2)")
    sp.add_argument("--out", help="write a static page here instead of serving it (no refresh)")
    sp.add_argument("--port", type=int, default=0, help="port to serve on (default: any free)")
    sp.add_argument("--no-open", action="store_true", help="do not open a browser")
    sp = add("find", cmd_find, "existing propositions and vault notes for some terms")
    sp.add_argument("terms", nargs="+")
    sp.add_argument("--limit", type=int, default=8)
    sp = add("show", cmd_show, "one proposition or chain with every answer and its question")
    sp.add_argument("id")
    add("status", cmd_status, "the whole model in a few lines")

    sp = add("new", None, "add a proposition or a chain")
    nsub = sp.add_subparsers(dest="what", required=True)
    np_ = nsub.add_parser("prop", help="add a proposition; prints its id")
    np_.add_argument("name")
    np_.add_argument("statement")
    np_.add_argument("--topics")
    np_.add_argument("--vault")
    np_.add_argument("--aliases")
    np_.add_argument("--force", action="store_true")
    np_.set_defaults(fn=cmd_new_prop)
    nc = nsub.add_parser("chain", help="add a chain: p_a p_b => p_c --step '…'; prints its id")
    nc.add_argument("chain", nargs="+")
    nc.add_argument("--step", required=True)
    nc.set_defaults(fn=cmd_new_chain)
    sp = add("amend", cmd_amend, "fix a proposition or chain in place; its id and answers stay "
             "(a different claim is a new id)")
    sp.add_argument("id")
    sp.add_argument("--name")
    sp.add_argument("--statement")
    sp.add_argument("--topics", help="replaces the topics; '' clears them")
    sp.add_argument("--aliases", help="replaces the aliases; '' clears them")
    sp.add_argument("--vault", help="'' clears it")
    sp.add_argument("--chain", help="a chain's new premises and conclusion: 'p_a p_b => p_c'")
    sp.add_argument("--step")
    sp.add_argument("--force", action="store_true",
                    help="change the claim of an id with answers, or reuse a name")
    sp = add("delete", cmd_delete, "delete a proposition or chain nothing rests on; its answers "
             "move to archive.md")
    sp.add_argument("id")
    sp.add_argument("--why", help="a note kept with the archived answers")
    sp.add_argument("--force", action="store_true", help="delete it even though it has answers")

    sp = add("ask", cmd_ask, "store a question block (file or stdin), print it shuffled with its id")
    sp.add_argument("file", nargs="?")
    sp = add("answer", cmd_answer, "grade the reader's one-line reply to a block and record it now")
    sp.add_argument("ask", help="the block id, q_…")
    sp.add_argument("reply", nargs="+")
    sp.add_argument("--redo", action="store_true",
                    help="answer an item again; the old answer moves to archive.md")
    sp = add("grade", cmd_grade, "grade a say item (or regrade any answered item) and record it now")
    sp.add_argument("ask", help="the block id, q_…")
    sp.add_argument("n", type=int)
    sp.add_argument("grade")
    sp.add_argument("--mis", help="the misconception the answer shows: 'believed X → Y'")
    sp.add_argument("--note")
    sp = add("retract", cmd_retract, "set an answer aside (misread question, misclick): it moves "
             "to archive.md and the item opens again")
    sp.add_argument("ask", help="the block id, q_…")
    sp.add_argument("n", type=int)
    sp.add_argument("--why", required=True, help="why the answer does not count")

    add("calib", cmd_calib, "how often the reader's confidence digits are right")
    sp = add("dupes", cmd_dupes, "likely duplicate propositions")
    sp.add_argument("--threshold", type=float, default=0.85)
    add("lint", cmd_lint, "check that every file parses and every id and answer resolves")
    sp = add("upkeep", cmd_upkeep, "daily: lint, back up, duplicates, notes without propositions")
    sp.add_argument("--scout", action="store_true", help="draft propositions with the scout")
    sp.add_argument("--limit", type=int, default=5)
    sp.add_argument("--timeout", type=int, default=600)
    sp = add("scout", cmd_scout, "ask a cheap read-only model to search the vault")
    sp.add_argument("task", nargs="+")
    sp.add_argument("--timeout", type=int, default=900)
    return ap


def main(argv: list[str] | None = None):
    ap = parser()
    a = ap.parse_args(argv)
    if a.fn is None:
        ap.parse_args([a.cmd, "-h"])
    a.fn(Context(), a)


if __name__ == "__main__":
    main()
