"""One-off: a v0 model folder (props.md, chains.md) → a v1 one (areas/).

  python -m kioku.migrate skeleton <v0-home> [--map topics.txt] > migration.md
  python -m kioku.migrate apply <v0-home> <migration.md> <new-home> [--check]

The skeleton lists every v0 id once, as a line of the table to fill in:

  - p_nuv7 · idea · banach-fixed-point · result · maths/analysis · needs: a, b · uses: c
  - c_ktug · idea · banach-fixed-point-proof · proof · maths/analysis · needs: … · uses: …
  - c_q4yv · edges
  - c_wmkr · drop · <why>

A proposition is always an idea; a chain becomes a proof idea (its step is the
statement, its id and answers stay), only edges (written on the ideas it
joined), or is dropped. A chain with answers must become an idea, so no answer
loses its idea. Edge names may also be v0 ids. `apply` checks the table, then
writes the new folder: area files, evidence with observed work marked as such,
and everything else copied as it is (asks, archive, profile, config, .git).
With --check it only reports.

The topic map (`--map`) belongs to the learner's data, not to this code: lines
`topic = area`, or `topic+topic = area` for a combination, most specific first.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import re
import shutil
import sys
from pathlib import Path

from .model import Model
from .records import IDEA_KINDS, Idea
from .store import AREA, NAME, SEP, Snapshot, format_answer, format_area, parse_answer

V0_ID = r"[pc]_[0-9a-z]{3,8}"


# -- reading v0

def read_v0(home: Path) -> tuple[dict, dict]:
    props, chains = {}, {}
    for line in (home / "props.md").read_text().splitlines():
        if not line.startswith("- p_"):
            continue
        f = line[2:].split(SEP)
        extra = {"topics": (), "aliases": (), "vault": None}
        for kv in f[3:]:
            k, _, v = (x.strip() for x in kv.partition(":"))
            if k in ("topics", "aliases"):
                extra[k] = tuple(x.strip() for x in v.split(",") if x.strip())
            elif k == "vault":
                extra[k] = v or None
        props[f[0]] = {"id": f[0], "name": f[1].strip(), "statement": f[2].strip(), **extra}
    for line in (home / "chains.md").read_text().splitlines():
        if not line.startswith("- c_"):
            continue
        f = line[2:].split(SEP)
        m = re.fullmatch(r"(.+?)\s*⟹\s*(" + V0_ID + r")", f[1].strip())
        if not m:
            continue
        step = next((v.strip() for k, _, v in (kv.partition(":") for kv in f[2:])
                     if k.strip() == "step"), "")
        chains[f[0]] = {"id": f[0], "premises": re.findall(V0_ID, m[1]), "conclusion": m[2],
                        "step": step}
    return props, chains


def answered(home: Path) -> dict[str, int]:
    n: dict[str, int] = {}
    for line in (home / "evidence.md").read_text().splitlines():
        a = parse_answer(line)
        if a:
            n[a.id] = n.get(a.id, 0) + 1
    return n


# -- the skeleton

def read_map(path: Path | None) -> list[tuple[set[str], str]]:
    rules = []
    if path:
        for line in path.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if "=" in line:
                left, area = (x.strip() for x in line.split("=", 1))
                rules.append(({t.strip() for t in left.split("+")}, area))
    return rules


def skeleton(home: Path, map_path: Path | None) -> str:
    props, chains = read_v0(home)
    n = answered(home)
    rules = read_map(map_path)

    def area_of(topics) -> str:
        return next((a for need, a in rules if need <= set(topics)), "?")

    out = ["# migration table", "",
           "<!-- one line per v0 id; see `python -m kioku.migrate -h` -->", ""]
    for p in props.values():
        into = [c for c in chains.values() if c["conclusion"] == p["id"]]
        needs = sorted({props[x]["name"] if x in props else x for c in into for x in c["premises"]})
        out.append(f"- {p['id']} · idea · {p['name']} · ? · {area_of(p['topics'])} · "
                   f"needs: {', '.join(needs)} · uses: ")
    for c in chains.values():
        concl = props.get(c["conclusion"], {"name": c["conclusion"], "topics": ()})
        verdict = (f"idea · {concl['name']}-proof · proof · {area_of(concl['topics'])} · "
                   f"needs: {concl['name']} · uses: "
                   + ", ".join(props[x]["name"] if x in props else x for x in c["premises"])) \
            if n.get(c["id"]) else "?"
        out.append(f"- {c['id']} · {verdict}" + (f"   <!-- {n[c['id']]} answer(s) -->"
                                                  if n.get(c["id"]) else ""))
    return "\n".join(out) + "\n"


# -- applying a table

def read_table(path: Path) -> tuple[dict[str, dict], list[str]]:
    rows, problems = {}, []
    for k, raw in enumerate(path.read_text().splitlines(), 1):
        line = re.sub(r"<!--.*?-->", "", raw).strip()
        if not line.startswith("- "):
            continue
        f = [x.strip() for x in line[2:].split(SEP)]
        if not re.fullmatch(V0_ID, f[0]):
            problems.append(f"table:{k}: `{f[0]}` is not a v0 id")
            continue
        row = {"id": f[0], "verdict": f[1] if len(f) > 1 else "?", "line": k}
        if row["verdict"] == "idea":
            if len(f) < 5:
                problems.append(f"table:{k}: want `id · idea · name · kind · area · needs: … · uses: …`")
                continue
            row.update(name=f[2], kind=f[3], area=f[4], needs=[], uses=[])
            for kv in f[5:]:
                key, _, v = kv.partition(":")
                if key.strip() in ("needs", "uses"):
                    row[key.strip()] = [x.strip() for x in v.split(",") if x.strip()]
                else:
                    problems.append(f"table:{k}: unknown field `{key.strip()}`")
        elif row["verdict"] == "drop":
            row["why"] = f[2] if len(f) > 2 else ""
        elif row["verdict"] != "edges":
            problems.append(f"table:{k}: verdict is idea, edges or drop, not `{row['verdict']}`")
        if f[0] in rows:
            problems.append(f"table:{k}: {f[0]} is listed twice")
        rows[f[0]] = row
    return rows, problems


def build(home: Path, table: Path) -> tuple[list[Idea], list[str], list[str]]:
    """The v1 ideas the table describes, problems that stop it, and notes."""
    props, chains = read_v0(home)
    n = answered(home)
    rows, problems = read_table(table)
    notes: list[str] = []
    for vid in [*props, *chains]:
        if vid not in rows:
            problems.append(f"{vid}: missing from the table")
    for vid, row in rows.items():
        if vid not in props and vid not in chains:
            problems.append(f"{vid}: not in the v0 model")
        elif vid in props and row["verdict"] != "idea":
            problems.append(f"{vid}: a proposition must become an idea")
        elif n.get(vid) and row["verdict"] != "idea":
            problems.append(f"{vid}: has {n[vid]} answer(s), so it must become an idea")
    ideas_rows = [r for r in rows.values() if r["verdict"] == "idea"]
    id_name = {r["id"]: r["name"] for r in ideas_rows}
    seen: dict[str, str] = {}
    for r in ideas_rows:
        where = f"{r['id']} {r['name']}"
        if not re.fullmatch(NAME, r["name"]):
            problems.append(f"{where}: name is not kebab-case")
        if r["name"] in seen:
            problems.append(f"{where}: name also used by {seen[r['name']]}")
        seen[r["name"]] = r["id"]
        if r["kind"] not in IDEA_KINDS:
            problems.append(f"{where}: kind `{r['kind']}` is not one of {', '.join(IDEA_KINDS)}")
        if not re.fullmatch(AREA, r["area"]):
            problems.append(f"{where}: area `{r['area']}` is not a path")
        for f in ("needs", "uses"):
            r[f] = [id_name.get(x, x) for x in r[f]]
            for x in r[f]:
                if x not in seen and x not in id_name.values():
                    problems.append(f"{where}: {f} unknown idea `{x}`")
            if r["name"] in r[f]:
                problems.append(f"{where}: {f} itself")
    ideas = []
    for r in ideas_rows:
        if r["id"] in props:
            p = props[r["id"]]
            ideas.append(Idea(r["id"], r["name"], r["kind"], r["area"], p["statement"],
                              tuple(r["needs"]), tuple(r["uses"]), p["aliases"], p["vault"]))
        elif r["id"] in chains:
            ideas.append(Idea(r["id"], r["name"], r["kind"], r["area"], chains[r["id"]]["step"],
                              tuple(r["needs"]), tuple(r["uses"])))
    if not problems:
        m = Model(Snapshot({i.id: i for i in ideas}, set(), []), dt.datetime.now())
        problems += [f"cycle: {' → '.join(m.name(x) for x in c)}" for c in m.cycles()]
        for vid, row in rows.items():
            if row["verdict"] == "edges" and vid in chains:
                c = chains[vid]
                concl = m.by_name.get(id_name.get(c["conclusion"], ""))
                linked = {*m.needs.get(concl, ()), *m.uses.get(concl, ())} if concl else set()
                if not any(m.by_name.get(id_name.get(p, "")) in linked for p in c["premises"]):
                    notes.append(f"{vid}: marked edges, but its conclusion has no edge to any "
                                 f"of its premises")
        areas = sorted({i.area for i in ideas})
        notes.append(f"{len(ideas)} ideas in {len(areas)} areas: " + ", ".join(areas))
        dropped = [v for v, r in rows.items() if r["verdict"] == "drop"]
        edges = [v for v, r in rows.items() if r["verdict"] == "edges"]
        notes.append(f"chains: {len(chains) - len(dropped) - len(edges)} became ideas, "
                     f"{len(edges)} edges only, {len(dropped)} dropped")
    return ideas, problems, notes


def apply(home: Path, table: Path, out: Path, check: bool) -> int:
    ideas, problems, notes = build(home, table)
    print("\n".join(notes))
    if problems:
        print(f"{len(problems)} problem(s):\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    if check:
        print("table ok (--check: nothing written)")
        return 0
    if out.exists():
        print(f"{out} exists; migrate into a new folder", file=sys.stderr)
        return 1
    shutil.copytree(home, out, ignore=shutil.ignore_patterns("props.md", "chains.md",
                                                             "evidence.md"))
    by_area: dict[str, list[Idea]] = {}
    for i in ideas:
        by_area.setdefault(i.area, []).append(i)
    for area, lst in by_area.items():
        p = out / "areas" / f"{area}.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(format_area(area, lst))
    lines, observed = [], 0
    for line in (home / "evidence.md").read_text().splitlines():
        a = parse_answer(line)
        if a and a.kind == "say" and a.note.startswith("observed:"):
            help_ = {"wrong": "shown", "partly": "hint"}.get(a.outcome)
            line = format_answer(dataclasses.replace(a, kind="observed", outcome="right",
                                                     help=help_))
            observed += 1
        lines.append(line)
    (out / "evidence.md").write_text("\n".join(lines) + "\n")
    print(f"written to {out}: {len(ideas)} ideas, {observed} answer(s) marked observed")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m kioku.migrate", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sk = sub.add_parser("skeleton")
    sk.add_argument("home", type=Path)
    sk.add_argument("--map", type=Path)
    ap_ = sub.add_parser("apply")
    ap_.add_argument("home", type=Path)
    ap_.add_argument("table", type=Path)
    ap_.add_argument("out", type=Path)
    ap_.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "skeleton":
        print(skeleton(a.home.expanduser(), a.map), end="")
        return 0
    return apply(a.home.expanduser(), a.table, a.out.expanduser(), a.check)


if __name__ == "__main__":
    sys.exit(main())
