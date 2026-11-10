"""Question blocks: the one way to ask, and the only source of evidence.

A block is written in a small text format (`kioku ask -h`), stored
as a dict (JSON in the store), shown as markdown, and answered in one line.
Grading a reply turns each answered item into an Answer. Nothing here touches
files.
"""

from __future__ import annotations

import datetime as dt
import random
import re
import string
from dataclasses import dataclass, field

from .records import DEPTHS, Answer
from .text import short

# `1 pick banach-fixed-point use: …`: the item's idea (name, alias or id), optionally
# the depth it demands (default use), and optionally `pre` (asked before the idea is
# taught, so its answer is kept as data but is not evidence of memory), `taught` (the
# session explained the idea before this question) or `probe` (asked to find out what
# they already held); the last two are recorded with the answer
ITEM_RE = re.compile(r"^(\d+)\s+(pick|write|say)\s+([^\s:]+)(?:\s+(" + "|".join(DEPTHS)
                     + r"))?(?:\s+(pre|taught|probe))?:\s*(.*)$")


def split_ideas(text: str) -> tuple[str, str]:
    """Idea blocks (`## name · kind · area`, as for `kioku add`) written above a question
    block → (the idea blocks, the question block)."""
    lines = text.splitlines()
    if not any(l.startswith("## ") for l in lines):
        return "", text
    cut = next((k for k, l in enumerate(lines) if l.startswith("# ") or ITEM_RE.match(l)),
               len(lines))
    return "\n".join(lines[:cut]), "\n".join(lines[cut:])
REPLY_RE = re.compile(r"(?:(?<=[\s,;])|^)(\d{1,2})([a-h][0-9]?|[.=~x?\-])(?=[\s,;:]|$)")


def parse_block(text: str) -> tuple[str, list[dict], list[str]]:
    """Block text → (title, items, problems). Each item is a dict:
    n, kind, id (as written: the caller resolves it), depth, q, options
    [{text, correct, mis}], why, ref."""
    title, items, problems = "", [], []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("# ") and not items:
            title = line[2:].strip()
            continue
        m = ITEM_RE.match(line)
        if m:
            items.append({"n": int(m[1]), "kind": m[2], "id": m[3], "depth": m[4] or "use",
                          "pre": m[5] == "pre", "taught": m[5] == "taught",
                          "probe": m[5] == "probe", "q": m[6],
                          "options": [], "why": "", "ref": ""})
            continue
        if not items:
            problems.append(f"before the first item: {line}")
            continue
        it, body = items[-1], line.strip()
        if body[:2] in ("* ", "- "):
            text_, _, mis = body[2:].partition(" :: ")
            it["options"].append({"text": text_.strip(), "correct": body[0] == "*",
                                  "mis": mis.strip()})
        elif body.startswith("? "):
            it["why"] = (it["why"] + " " + body[2:]).strip()
        elif body.startswith("= "):
            it["ref"] = (it["ref"] + " " + body[2:]).strip()
        else:
            it["q"] = (it["q"] + " " + body).strip()
    for k, it in enumerate(items, 1):
        if it["n"] != k:
            problems.append(f"items must be numbered 1, 2, 3, …; got {it['n']} at position {k}")
        if it["kind"] == "pick":
            if len(it["options"]) < 2 or sum(o["correct"] for o in it["options"]) != 1:
                problems.append(f"item {it['n']}: a pick needs ≥ 2 options, exactly one `* `")
        elif not it["ref"]:
            problems.append(f"item {it['n']}: a {it['kind']} needs a `= ` reference answer")
    return title, items, problems


def new_block(qid: str, title: str, items: list[dict], now: dt.datetime) -> dict:
    """A stored block: options shuffled, every item open."""
    for it in items:
        random.shuffle(it["options"])
        it["state"] = "open"
    return {"id": qid, "title": title, "asked": now.isoformat(timespec="seconds"),
            "items": items}


def render(ask: dict) -> str:
    """The block as markdown, to show as it is."""
    items = ask["items"]
    out = [f"**{ask['title'] or 'Questions'}** · reply on one line", "", f"_{_legend(items)}_"]
    for it in items:
        hint = {"pick": "", "write": f" — _on paper or a tablet; reply `{it['n']}.` when done_",
                "say": " — _one line_"}[it["kind"]]
        out += ["", f"**{it['n']}** · {it['q']}{hint}"]
        if it["options"]:
            out.append("")
        out += [f"- **{string.ascii_lowercase[k]})** {o['text']}"
                for k, o in enumerate(it["options"])]
    return "\n".join(out)


@dataclass
class Graded:
    shown: list[str] = field(default_factory=list)  # one verdict line per item, for the learner
    answers: list[Answer] = field(default_factory=list)  # to record
    to_grade: list[int] = field(default_factory=list)  # say items the agent must grade


def grade_reply(ask: dict, reply: str, now: dt.datetime, redo: bool = False) -> Graded:
    """Grade a one-line reply. Updates each item's state and replies in `ask`."""
    g = Graded()
    entries = parse_reply(reply, len(ask["items"]))
    for n, tok, thoughts in entries:
        it = ask["items"][n - 1]
        if it["state"] == "done" and not redo:
            g.shown.append(f"- **{n}** already answered (--redo to answer again)")
            continue
        it.setdefault("replies", []).append(
            {"at": now.isoformat(timespec="seconds"), "token": tok, "thoughts": thoughts})
        shown, answer, done = _grade_item(ask["id"], it, tok, thoughts, now)
        g.shown.append(f"- **{n}** {shown}")
        if answer:
            g.answers.append(answer)
        if done:
            it["state"] = "done"
        elif it["kind"] == "say" and (tok == ":" or thoughts):
            it["state"], it["answer"] = "to-grade", thoughts
            g.to_grade.append(n)
    return g


def grade_say(ask: dict, n: int, outcome: str, now: dt.datetime, mis: str | None = None,
              note: str | None = None) -> Answer:
    """The agent's judgement of an answered item (a say item, or a regrade): right,
    partly or wrong."""
    it = ask["items"][n - 1]
    it["state"] = "done"
    text = f"misconception: {mis}" if mis else note or short(it.get("answer", ""), 80) \
        or "graded by the agent"
    flag = "pre" if it.get("pre") else "mis" if mis else None
    return Answer(now, it["id"], it["kind"], outcome, ask["id"], n,
                  flag=flag, depth=it.get("depth"), note=text, taught=bool(it.get("taught")),
                  probe=bool(it.get("probe")))


def parse_reply(reply: str, n_items: int) -> list[tuple[int, str, str]]:
    """`1b8 2. 3- 4? 5: free text` → [(item, token, thoughts)], in item order."""
    found, last = [], 0
    for m in REPLY_RE.finditer(reply):
        n = int(m.group(1))
        if last < n <= n_items:
            found.append((n, m.group(2), m.start(), m.end()))
            last = n
    entries = []
    for k, (n, tok, _start, end) in enumerate(found):
        stop = found[k + 1][2] if k + 1 < len(found) else len(reply)
        rest = reply[end:stop].strip().strip(",;").strip()
        entries.append((n, tok, rest[1:].strip() if rest.startswith(":") else rest))
    for m in re.finditer(r"(?:(?<=\s)|^)(\d{1,2}):\s*", reply):  # `3: …` for a say item
        n = int(m.group(1))
        if 0 < n <= n_items and all(e[0] != n for e in entries):
            stop = min([s for (_n, _t, s, _e) in found if s > m.end()] + [len(reply)])
            entries.append((n, ":", reply[m.end():stop].strip()))
    return sorted(entries)


def _grade_item(qid: str, it: dict, tok: str, thoughts: str,
                now: dt.datetime) -> tuple[str, Answer | None, bool]:
    """One reply token → (verdict to show, answer to record, item done)."""
    n, kind = it["n"], it["kind"]
    said = f" · “{short(thoughts, 80)}”" if thoughts else ""
    right = next((o for o in it["options"] if o["correct"]), {"text": "", "mis": ""})

    def answer(outcome, note, conf=None, flag=None):
        if it.get("pre"):  # before teaching: kept as data, skipped by the memory model
            flag = "pre"
        return Answer(now, it["id"], kind, outcome, qid, n, conf, flag, it.get("depth"),
                      note + said, bool(it.get("taught")), probe=bool(it.get("probe")))

    if tok == "-":
        return "never met", answer("unmet", "never met it"), True
    if tok == "?":
        return ("seen, not producible — it is: " + (it["ref"] or right["text"]),
                answer("wrong", "seen it, could not produce it"), True)
    if kind == "pick":
        if not re.fullmatch(r"[a-h][0-9]?", tok):
            return f"wants a letter and a confidence digit, e.g. `{n}b8`", None, False
        k = ord(tok[0]) - ord("a")
        if k >= len(it["options"]):
            return f"has no option {tok[0]}", None, False
        conf = int(tok[1]) if len(tok) > 1 else 5
        unsure = "" if len(tok) > 1 else " (no confidence given, read as 5)"
        chosen = it["options"][k]
        if chosen["correct"]:
            guess = conf / 10 <= 1 / len(it["options"])  # no surer than chance
            why = f". {it['why']}" if it["why"] and conf < 8 else ""
            return (f"{'✓ but a guess' if guess else '✓'} — {tok[0]} at {conf}0%{unsure}{why}",
                    answer("guess" if guess else "right", f"picked {short(chosen['text'], 50)}",
                           conf), True)
        mis = conf >= 8
        letter = string.ascii_lowercase[it["options"].index(right)]
        if mis:
            note = (f"misconception: {chosen['mis'] or short(chosen['text'], 50)}; "
                    f"right: {short(right['text'], 50)}")
        else:
            note = f"picked {short(chosen['text'], 50)}, right: {short(right['text'], 50)}"
        shown = (f"✗ {'misconception' if mis else 'gap'} — {tok[0]} at {conf}0%{unsure}. "
                 f"Right: **{letter})** {right['text']}"
                 + (f". _{chosen['mis']}_" if chosen["mis"] and mis else "")
                 + (f". {it['why']}" if it["why"] else ""))
        return shown, answer("wrong", note, conf, "mis" if mis else None), True
    if kind == "write":
        if tok == ".":
            it["state"] = "shown"
            return (f"compare with: {it['ref']}  \n"
                    f"  reply `{n}=` matches · `{n}~` small slip · `{n}x` wrong"), None, False
        if tok in ("=", "~", "x"):
            outcome = {"=": "right", "~": "partly", "x": "wrong"}[tok]
            note = {"=": "wrote it correctly", "~": "wrote it with a small slip",
                    "x": "could not write it"}[tok]
            return f"{'✗' if tok == 'x' else '✓'} {note}", answer(outcome, note), True
        return f"wants `{n}.` then `{n}=`, `{n}~` or `{n}x`", None, False
    if tok != ":" and not thoughts:  # say
        return f"wants `{n}: <answer>`", None, False
    return f"you said: “{short(thoughts, 100)}”  \n  reference: {it['ref']}", None, False


def _legend(items: list[dict]) -> str:
    """The reply forms this block uses, with its own item numbers."""
    first: dict[str, int] = {}
    for it in items:
        first.setdefault(it["kind"], it["n"])
    parts = []
    if "pick" in first:
        parts.append(f"`{first['pick']}b8` option b, 80% sure")
    if "write" in first:
        parts.append(f"`{first['write']}.` done writing")
    if "say" in first:
        parts.append(f"`{first['say']}: …` your answer")
    if "pick" in first or "write" in first:
        parts += ["`-` never met", "`?` seen it, can't produce it",
                  "`: …` after any answer for your thoughts"]
    return " · ".join(parts)
