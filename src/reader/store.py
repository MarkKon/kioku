"""The model on disk: one folder of plain files, readable and diffable.

  profile.md   who the reader is, free text for agents
  config.toml  optional settings (see config.py)
  areas/       the area tree: the ideas whose home is maths/analysis live in
               areas/maths/analysis.md, one `## name · kind · id` block each
  evidence.md  one answer per line, the only learner data
  asks/        every question block asked (and every observed step), as JSON
  archive.md   evidence set aside, e.g. of removed ideas; nothing reads it

Only this module knows the file formats.
"""

from __future__ import annotations

import datetime as dt
import json
import random
import re
import string
from dataclasses import dataclass, field
from pathlib import Path

from .records import DEPTHS, IDEA_KINDS, Answer, Idea

SEP = " · "
ID = r"[pci]_[0-9a-z]{3,8}"
QID = r"q_[0-9a-z]{4,16}"
NAME = r"[a-z0-9][a-z0-9-]*"  # kebab-case
AREA = r"[a-z0-9][a-z0-9-]*(?:/[a-z0-9][a-z0-9-]*)*"
FIELDS = ("needs", "uses", "aliases", "vault")

HEADERS = {
    "evidence.md": "# Evidence\n\n"
    "<!-- One line per answer, written by `reader answer` and `reader observed`:\n"
    "     - YYYY-MM-DDTHH:MM <id> pick|write|say|observed <grade> [confidence] [mis|unseen]"
    " [state|use|transfer] q_<ask>/<n> — <what they answered> -->\n\n",
    "profile.md": "# Reader profile\n\n"
    "<!-- Who the reader is, for agents pitching explanations at their level. -->\n\n"
    "Name:\n\nBackground:\n\nHow they answer:\n",
}

ARCHIVE_HEADER = ("# Archive\n\nNot evidence: lines set aside, e.g. the answers of removed ideas. "
                  "Nothing reads this file.\n")

ANSWER_RE = re.compile(
    r"^- (?P<day>\d{4}-\d{2}-\d{2})(?:T(?P<time>\d{2}:\d{2}))? (?P<id>" + ID + r")"
    r" (?P<kind>pick|write|say|observed)"
    r" (?P<grade>again|hard|good|easy|guess)"
    r"(?: (?P<conf>[0-9]))?"
    r"(?: (?P<flag>mis|unseen))?"
    r"(?: (?P<depth>" + "|".join(DEPTHS) + r"))?"
    r" (?P<ask>" + QID + r")/(?P<n>\d+)"
    r"(?:\s+—\s*(?P<note>.*))?\s*$")
HEAD_RE = re.compile(r"^## (?P<name>\S+) · (?P<kind>\S+) · (?P<third>\S+)\s*$")


@dataclass
class Snapshot:
    ideas: dict[str, Idea]  # by id, in file order
    areas: set[str]  # every area with a file or a folder
    answers: list[Answer]
    problems: list[str] = field(default_factory=list)  # what did not parse


class Store:
    def __init__(self, home: Path):
        self.home = home

    @property
    def tree(self) -> Path:
        return self.home / "areas"

    # -- reading

    def load(self) -> Snapshot:
        problems: list[str] = []
        ideas: dict[str, Idea] = {}
        areas: set[str] = set()
        if self.tree.exists():
            for d in sorted(self.tree.rglob("*")):
                rel = d.relative_to(self.tree).as_posix()
                if d.is_dir():
                    areas.add(rel)
                elif d.suffix == ".md":
                    area = rel[:-3]
                    areas.add(area)
                    for idea in parse_area(d.read_text(), area, f"areas/{rel}", problems):
                        if idea.id in ideas:
                            problems.append(f"areas/{rel}: duplicate id {idea.id}")
                        ideas[idea.id] = idea
        return Snapshot(ideas, areas, self._answers(problems), problems)

    def profile(self) -> str | None:
        p = self.home / "profile.md"
        return p.read_text() if p.exists() else None

    def ask(self, qid: str) -> dict | None:
        p = self.home / "asks" / f"{qid}.json"
        return json.loads(p.read_text()) if p.exists() else None

    def ask_ids(self) -> set[str]:
        return {p.stem for p in (self.home / "asks").glob("q_*.json")}

    # -- writing ideas

    def init(self) -> None:
        (self.home / "asks").mkdir(parents=True, exist_ok=True)
        self.tree.mkdir(parents=True, exist_ok=True)
        for name, header in HEADERS.items():
            if not (self.home / name).exists():
                (self.home / name).write_text(header)

    def write_ideas(self, ideas: list[Idea], before: dict[str, Idea]) -> None:
        """Write the given ideas (new or changed) into their area files.

        `before` is the whole model as loaded; an idea that moved area leaves its
        old file, and an area file left empty is removed."""
        self.init()
        files: dict[str, list[Idea]] = {}

        def area_ideas(area: str) -> list[Idea]:
            if area not in files:
                files[area] = [i for i in before.values() if i.area == area]
            return files[area]

        for new in ideas:
            old = before.get(new.id)
            if old and old.area != new.area:
                area_ideas(old.area)[:] = [i for i in area_ideas(old.area) if i.id != new.id]
            lst = area_ideas(new.area)
            k = next((j for j, i in enumerate(lst) if i.id == new.id), None)
            if k is None:
                lst.append(new)
            else:
                lst[k] = new
        for area, lst in files.items():
            self._write_area(area, lst)

    def make_area(self, area: str) -> None:
        (self.tree / area).parent.mkdir(parents=True, exist_ok=True)
        p = self.tree / f"{area}.md"
        if not p.exists():
            p.write_text(format_area(area, []))

    def remove_idea(self, idea: Idea, before: dict[str, Idea], day: dt.date, why: str) -> list[str]:
        """Take an idea out of its area file and move its evidence to archive.md.

        Returns the evidence lines moved: set aside, never rewritten."""
        self._write_area(idea.area, [i for i in before.values()
                                     if i.area == idea.area and i.id != idea.id])
        moved: list[str] = []

        def take(x: str) -> str | None:
            m = ANSWER_RE.match(x)
            if m and m["id"] == idea.id:
                moved.append(x)
                return None
            return x

        self._rewrite("evidence.md", take)
        self._archive(f"{day} · removed {idea.id} {idea.name}", why, moved or ["(no answers)"])
        return moved

    def _write_area(self, area: str, ideas: list[Idea]) -> None:
        p = self.tree / f"{area}.md"
        if not ideas:
            if p.exists():
                p.unlink()
            d = p.parent
            while d != self.tree and d.exists() and not any(d.iterdir()):
                d.rmdir()
                d = d.parent
            return
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(format_area(area, ideas))

    # -- writing evidence

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
        text = p.read_text() if p.exists() else ""
        with p.open("a") as f:
            f.write(("" if not text or text.endswith("\n") else "\n") + line + "\n")

    def _answers(self, problems: list[str]) -> list[Answer]:
        answers = []
        for n, line in enumerate(self._lines("evidence.md"), 1):
            if not line.startswith("- "):
                continue
            a = parse_answer(line)
            if a is None:
                problems.append(f"evidence.md:{n}: want `- YYYY-MM-DDTHH:MM <id> <kind> <grade> "
                                f"[conf] [mis|unseen] [depth] q_<ask>/<n> — note`")
            elif a.grade == "guess" and a.kind != "pick":
                problems.append(f"evidence.md:{n}: only a pick can be a guess")
            else:
                answers.append(a)
        return answers


# -- the idea block: the one format of area files, `reader add` and `reader context`

def parse_blocks(text: str, where: str, problems: list[str], need_id: bool = True) -> list[dict]:
    """`## name · kind · id-or-area` blocks → dicts with name, kind, third, statement,
    and the fields. Lines before the first block (a title, comments) are skipped."""
    blocks: list[dict] = []
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if line.startswith("## "):
            m = HEAD_RE.match(line)
            if not m:
                problems.append(f"{where}:{n}: want `## name · kind · "
                                f"{'id' if need_id else 'area'}`")
                blocks.append({"bad": True})
                continue
            blocks.append({"name": m["name"], "kind": m["kind"], "third": m["third"],
                           "statement": [], "line": n, **{f: [] for f in FIELDS}})
            continue
        if not blocks or blocks[-1].get("bad"):
            continue
        b = blocks[-1]
        fm = re.match(r"^- (needs|uses|aliases|vault):\s*(.*)$", line)
        if fm:
            b[fm[1]] += [x.strip() for x in fm[2].split(",") if x.strip()]
        elif line.startswith("- ") and re.match(r"^- [a-z]+:", line):
            problems.append(f"{where}:{n}: unknown field `{line.split(':')[0][2:]}`")
        elif line.strip() and not line.startswith("<!--"):
            if any(b[f] for f in FIELDS):
                problems.append(f"{where}:{n}: statement text after the fields")
            b["statement"].append(line.strip())
    out = []
    for b in blocks:
        if b.get("bad"):
            continue
        b["statement"] = " ".join(b["statement"])
        out.append(b)
    return out


def parse_area(text: str, area: str, where: str, problems: list[str]) -> list[Idea]:
    ideas = []
    for b in parse_blocks(text, where, problems):
        if not re.fullmatch(ID, b["third"]):
            problems.append(f"{where}:{b['line']}: `{b['third']}` is not an id")
            continue
        problems += [f"{where}:{b['line']}: {p}" for p in check_block(b)]
        ideas.append(block_idea(b, b["third"], area))
    return ideas


def check_block(b: dict) -> list[str]:
    problems = []
    if not re.fullmatch(NAME, b["name"]):
        problems.append(f"name `{b['name']}` is not kebab-case")
    if b["kind"] not in IDEA_KINDS:
        problems.append(f"kind `{b['kind']}` is not one of {', '.join(IDEA_KINDS)}")
    if not b["statement"]:
        problems.append(f"{b['name']} has no statement")
    if len(b["vault"]) > 1:
        problems.append(f"{b['name']} has more than one vault note")
    return problems


def block_idea(b: dict, iid: str, area: str) -> Idea:
    return Idea(iid, b["name"], b["kind"], area, b["statement"], tuple(b["needs"]),
                tuple(b["uses"]), tuple(b["aliases"]), b["vault"][0] if b["vault"] else None)


def format_idea(i: Idea, third: str | None = None) -> str:
    out = [f"## {i.name}{SEP}{i.kind}{SEP}{third or i.id}", i.statement]
    for f, v in (("needs", i.needs), ("uses", i.uses), ("aliases", i.aliases)):
        if v:
            out.append(f"- {f}: {', '.join(v)}")
    if i.vault:
        out.append(f"- vault: {i.vault}")
    return "\n".join(out)


def format_area(area: str, ideas: list[Idea]) -> str:
    return f"# {area}\n\n" + "\n\n".join(format_idea(i) for i in ideas) + ("\n" if ideas else "")


# -- evidence lines

def parse_answer(line: str) -> Answer | None:
    m = ANSWER_RE.match(line)
    if not m:
        return None
    at = dt.datetime.fromisoformat(f"{m['day']}T{m['time'] or '12:00'}")
    return Answer(at=at, id=m["id"], kind=m["kind"], grade=m["grade"], ask=m["ask"],
                  n=int(m["n"]), conf=int(m["conf"]) if m["conf"] else None, flag=m["flag"],
                  depth=m["depth"], note=m["note"] or "")


def format_answer(a: Answer) -> str:
    parts = [f"{a.at:%Y-%m-%dT%H:%M}", a.id, a.kind, a.grade]
    if a.conf is not None:
        parts.append(str(a.conf))
    if a.flag:
        parts.append(a.flag)
    if a.depth:
        parts.append(a.depth)
    parts.append(f"{a.ask}/{a.n}")
    note = " ".join(a.note.split())
    return "- " + " ".join(parts) + (f" — {note}" if note else "")


def new_id(prefix: str, taken: set[str], k: int = 4) -> str:
    alphabet = string.digits + string.ascii_lowercase
    while True:
        iid = prefix + "".join(random.choices(alphabet, k=k))
        if iid not in taken:
            return iid
