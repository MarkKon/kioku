"""The model on disk: one folder of plain files, readable and diffable.

  profile.md   who the reader is, free text for agents
  config.toml  optional settings (see config.py)
  props.md     one proposition per line
  chains.md    one chain per line
  evidence.md  one answer per line, the only learner data
  asks/        every question block asked, as JSON, with their replies
  archive.md   evidence set aside, e.g. of deleted ids; nothing reads it

Only this module knows the line formats.
"""

from __future__ import annotations

import datetime as dt
import json
import random
import re
import string
from dataclasses import dataclass, field
from pathlib import Path

from .records import Answer, Chain, Prop

SEP = " · "
ID = r"[pc]_[0-9a-z]{3,8}"
QID = r"q_[0-9a-z]{4,16}"

HEADERS = {
    "props.md": "# Propositions\n\n"
    "<!-- - p_id · name · statement · topics: a, b · vault: <note> · aliases: x, y -->\n\n",
    "chains.md": "# Chains\n\n"
    "<!-- - c_id · p_a ∧ p_b ⟹ p_c · step: <the reasoning step> -->\n\n",
    "evidence.md": "# Evidence\n\n"
    "<!-- One line per answered item, written by `reader answer` and `reader grade`:\n"
    "     - YYYY-MM-DDTHH:MM <id> pick|write|say <grade> [confidence] [mis|unseen] q_<ask>/<n>"
    " — <what they answered> -->\n\n",
    "profile.md": "# Reader profile\n\n"
    "<!-- Who the reader is, for agents pitching explanations at their level. -->\n\n"
    "Name:\n\nBackground:\n\nHow they answer:\n",
}

ARCHIVE_HEADER = ("# Archive\n\nNot evidence: lines set aside, e.g. the answers of deleted ids. "
                  "Nothing reads this file.\n")

ANSWER_RE = re.compile(
    r"^- (?P<day>\d{4}-\d{2}-\d{2})(?:T(?P<time>\d{2}:\d{2}))? (?P<id>" + ID + r") (?P<kind>pick|write|say)"
    r" (?P<grade>again|hard|good|easy|guess)"
    r"(?: (?P<conf>[0-9]))?"
    r"(?: (?P<flag>mis|unseen))?"
    r" (?P<ask>" + QID + r")/(?P<n>\d+)"
    r"(?:\s+—\s*(?P<note>.*))?\s*$")


@dataclass
class Snapshot:
    props: dict[str, Prop]
    chains: dict[str, Chain]
    answers: list[Answer]
    problems: list[str] = field(default_factory=list)  # lines that did not parse


class Store:
    def __init__(self, home: Path):
        self.home = home

    # -- reading

    def load(self) -> Snapshot:
        problems: list[str] = []
        return Snapshot(self._props(problems), self._chains(problems),
                        self._answers(problems), problems)

    def profile(self) -> str | None:
        p = self.home / "profile.md"
        return p.read_text() if p.exists() else None

    def ask(self, qid: str) -> dict | None:
        p = self.home / "asks" / f"{qid}.json"
        return json.loads(p.read_text()) if p.exists() else None

    def ask_ids(self) -> set[str]:
        return {p.stem for p in (self.home / "asks").glob("q_*.json")}

    # -- writing

    def init(self) -> None:
        (self.home / "asks").mkdir(parents=True, exist_ok=True)
        for name, header in HEADERS.items():
            if not (self.home / name).exists():
                (self.home / name).write_text(header)

    def add_prop(self, p: Prop) -> None:
        self._append("props.md", format_prop(p))

    def add_chain(self, c: Chain) -> None:
        self._append("chains.md", format_chain(c))

    def replace(self, r: Prop | Chain) -> None:
        """Rewrite the line of an existing proposition or chain in place."""
        name, line = (("props.md", format_prop(r)) if isinstance(r, Prop)
                      else ("chains.md", format_chain(r)))
        if not self._rewrite(name, lambda x: line if _line_id(x) == r.id else x):
            raise KeyError(r.id)

    def remove(self, iid: str, day: dt.date, why: str) -> list[str]:
        """Delete a proposition or chain; move its evidence to archive.md.

        Returns the evidence lines moved. Evidence is set aside, never rewritten,
        so a deleted id's history stays auditable.
        """
        name = "props.md" if iid.startswith("p_") else "chains.md"
        if not self._rewrite(name, lambda x: None if _line_id(x) == iid else x):
            raise KeyError(iid)
        moved: list[str] = []

        def take(x: str) -> str | None:
            m = ANSWER_RE.match(x)
            if m and m["id"] == iid:
                moved.append(x)
                return None
            return x

        self._rewrite("evidence.md", take)
        if moved:
            self._archive(f"{day} · deleted {iid}", why, moved)
        return moved

    def record(self, a: Answer) -> None:
        """Write an answer now. An earlier answer to the same item (a redo or a
        regrade) moves to archive.md."""
        self.take_answer(a.ask, a.n, a.day, "replaced by a new answer to the same item")
        self._append("evidence.md", format_answer(a))

    def take_answer(self, ask: str, n: int, day: dt.date, why: str) -> list[str]:
        """Move the evidence of one question item to archive.md; returns the lines
        moved. Evidence is set aside, never rewritten."""
        moved: list[str] = []

        def take(x: str) -> str | None:
            m = ANSWER_RE.match(x)
            if m and (m["ask"], int(m["n"])) == (ask, n):
                moved.append(x)
                return None
            return x

        self._rewrite("evidence.md", take)
        if moved:
            self._archive(f"{day} · {ask}/{n}", why, moved)
        return moved

    def save_ask(self, ask: dict) -> None:
        self.init()
        (self.home / "asks" / f"{ask['id']}.json").write_text(
            json.dumps(ask, indent=1, ensure_ascii=False))

    # -- internals

    def _archive(self, head: str, why: str, lines: list[str]) -> None:
        if not (self.home / "archive.md").exists():
            (self.home / "archive.md").write_text(ARCHIVE_HEADER)
        note = " ".join(why.split())
        self._append("archive.md", f"\n## {head}" + (f" · {note}" if note else "") +
                     "\n" + "\n".join(lines))

    def _lines(self, name: str) -> list[str]:
        p = self.home / name
        return p.read_text().splitlines() if p.exists() else []

    def _rewrite(self, name: str, f) -> bool:
        """Map every line of a file through f (None drops it); True if any changed."""
        p = self.home / name
        if not p.exists():
            return False
        lines = p.read_text().splitlines()
        new = [y for x in lines if (y := f(x)) is not None]
        if new == lines:
            return False
        p.write_text("\n".join(new) + "\n")
        return True

    def _append(self, name: str, line: str) -> None:
        self.init()
        p = self.home / name
        text = p.read_text()
        with p.open("a") as f:
            f.write(("" if not text or text.endswith("\n") else "\n") + line + "\n")

    def _props(self, problems: list[str]) -> dict[str, Prop]:
        props: dict[str, Prop] = {}
        for n, line in enumerate(self._lines("props.md"), 1):
            if not line.startswith("- p_"):
                continue
            f = line[2:].split(SEP)
            if len(f) < 3 or not re.fullmatch(ID, f[0]):
                problems.append(f"props.md:{n}: want `- p_id · name · statement · key: value`")
                continue
            extra: dict = {}
            for kv in f[3:]:
                k, _, v = (x.strip() for x in kv.partition(":"))
                if k in ("topics", "aliases"):
                    extra[k] = tuple(x.strip() for x in v.split(",") if x.strip())
                elif k == "vault":
                    extra[k] = v or None
                else:
                    problems.append(f"props.md:{n}: unknown field `{k}`")
            if f[0] in props:
                problems.append(f"props.md:{n}: duplicate id {f[0]}")
            props[f[0]] = Prop(f[0], f[1].strip(), f[2].strip(), **extra)
        return props

    def _chains(self, problems: list[str]) -> dict[str, Chain]:
        chains: dict[str, Chain] = {}
        for n, line in enumerate(self._lines("chains.md"), 1):
            if not line.startswith("- c_"):
                continue
            f = line[2:].split(SEP)
            parsed = parse_chain(f[1]) if len(f) >= 2 else None
            if not parsed or not re.fullmatch(ID, f[0]):
                problems.append(f"chains.md:{n}: want `- c_id · p_a ∧ p_b ⟹ p_c · step: …`")
                continue
            step = next((v.strip() for k, _, v in (kv.partition(":") for kv in f[2:])
                         if k.strip() == "step"), "")
            chains[f[0]] = Chain(f[0], tuple(parsed[0]), parsed[1], step)
        return chains

    def _answers(self, problems: list[str]) -> list[Answer]:
        answers = []
        for n, line in enumerate(self._lines("evidence.md"), 1):
            if not line.startswith("- "):
                continue
            a = parse_answer(line)
            if a is None:
                problems.append(f"evidence.md:{n}: want `- YYYY-MM-DDTHH:MM <id> <kind> <grade> "
                                f"[conf] [mis|unseen] q_<ask>/<n> — note`")
            elif a.grade == "guess" and a.kind != "pick":
                problems.append(f"evidence.md:{n}: only a pick can be a guess")
            else:
                answers.append(a)
        return answers


def _line_id(line: str) -> str | None:
    m = re.match(r"- (" + ID + r")" + re.escape(SEP), line)
    return m.group(1) if m else None


def format_prop(p: Prop) -> str:
    line = f"- {p.id}{SEP}{p.name}{SEP}{p.statement}"
    if p.topics:
        line += f"{SEP}topics: {', '.join(p.topics)}"
    if p.vault:
        line += f"{SEP}vault: {p.vault}"
    if p.aliases:
        line += f"{SEP}aliases: {', '.join(p.aliases)}"
    return line


def format_chain(c: Chain) -> str:
    return f"- {c.id}{SEP}{' ∧ '.join(c.premises)} ⟹ {c.conclusion}{SEP}step: {c.step}"


def parse_chain(body: str, names: bool = False) -> tuple[list[str], str] | None:
    """`p_a ∧ p_b ⟹ p_c`; with names=True the parts may be proposition names."""
    part = r"\S+" if names else ID
    m = re.fullmatch(r"(.+?)\s*(?:⟹|=>)\s*(" + part + r")", body.strip())
    if not m:
        return None
    premises = [x for x in re.split(r"\s*(?:∧|\+|,|\s)\s*", m.group(1).strip()) if x]
    if not premises or not all(re.fullmatch(part, x) for x in premises):
        return None
    return premises, m.group(2)


def parse_answer(line: str) -> Answer | None:
    m = ANSWER_RE.match(line)
    if not m:
        return None
    at = dt.datetime.fromisoformat(f"{m['day']}T{m['time'] or '12:00'}")
    return Answer(at=at, id=m["id"], kind=m["kind"],
                  grade=m["grade"], ask=m["ask"], n=int(m["n"]),
                  conf=int(m["conf"]) if m["conf"] else None, flag=m["flag"],
                  note=m["note"] or "")


def format_answer(a: Answer) -> str:
    parts = [f"{a.at:%Y-%m-%dT%H:%M}", a.id, a.kind, a.grade]
    if a.conf is not None:
        parts.append(str(a.conf))
    if a.flag:
        parts.append(a.flag)
    parts.append(f"{a.ask}/{a.n}")
    note = " ".join(a.note.split())
    return "- " + " ".join(parts) + (f" — {note}" if note else "")


def new_id(prefix: str, taken: set[str], k: int = 4) -> str:
    alphabet = string.digits + string.ascii_lowercase
    while True:
        iid = prefix + "".join(random.choices(alphabet, k=k))
        if iid not in taken:
            return iid
