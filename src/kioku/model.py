"""The model in memory: ideas, their edges, the area tree, and each idea's recall now."""

from __future__ import annotations

import datetime as dt
import difflib
from dataclasses import dataclass

from . import memory
from .records import DEPTHS, Answer, Idea
from .store import Snapshot
from .text import matches, norm

RIGHT = ("hard", "good", "easy")


@dataclass(frozen=True)
class Coverage:
    ideas: int
    asked: int  # ideas with at least one answer
    last: dt.datetime | None  # the latest answer in the area


class Model:
    def __init__(self, snap: Snapshot, now: dt.datetime):
        self.ideas: dict[str, Idea] = snap.ideas
        self.answers: list[Answer] = snap.answers
        self.problems: list[str] = snap.problems
        self.now = now
        self.today = now.date()
        self.by_name: dict[str, str] = {}
        for i in self.ideas.values():
            self.by_name.setdefault(i.name, i.id)
        self._alias: dict[str, list[str]] = {}
        for i in self.ideas.values():
            for a in i.aliases:
                self._alias.setdefault(norm(a), []).append(i.id)
        self.areas: set[str] = set(snap.areas)
        for i in self.ideas.values():
            self.areas.add(i.area)
        for a in list(self.areas):
            parts = a.split("/")
            self.areas.update("/".join(parts[:k]) for k in range(1, len(parts)))
        self._by_id: dict[str, list[Answer]] = {}
        for a in self.answers:
            self._by_id.setdefault(a.id, []).append(a)
        self._recall: dict[str, memory.Recall] = {}
        # edges by id; an edge to a name that does not resolve is kept out (lint reports it)
        self.needs = {i.id: [x for n in i.needs if (x := self.by_name.get(n))]
                      for i in self.ideas.values()}
        self.uses = {i.id: [x for n in i.uses if (x := self.by_name.get(n))]
                     for i in self.ideas.values()}
        self.needed_by: dict[str, list[str]] = {}
        self.used_by: dict[str, list[str]] = {}
        for src, dsts in self.needs.items():
            for d in dsts:
                self.needed_by.setdefault(d, []).append(src)
        for src, dsts in self.uses.items():
            for d in dsts:
                self.used_by.setdefault(d, []).append(src)

    # -- ids and names

    def resolve(self, term: str) -> str | None:
        """An id, a name, or an alias that names exactly one idea."""
        t = term.strip()
        if t in self.ideas:
            return t
        if t in self.by_name:
            return self.by_name[t]
        hits = self._alias.get(norm(t), [])
        return hits[0] if len(hits) == 1 else None

    def name(self, iid: str) -> str:
        return self.ideas[iid].name if iid in self.ideas else iid

    def answers_for(self, iid: str) -> list[Answer]:
        return self._by_id.get(iid, [])

    def recall(self, iid: str) -> memory.Recall:
        if iid not in self._recall:
            self._recall[iid] = memory.recall(self.answers_for(iid), self.now)
        return self._recall[iid]

    def deepest(self, iid: str) -> str | None:
        """The deepest depth the idea was answered right at."""
        shown = {a.depth for a in self.answers_for(iid) if a.grade in RIGHT and a.depth}
        return next((d for d in reversed(DEPTHS) if d in shown), None)

    # -- areas

    def area_of(self, term: str) -> str | None:
        """An area path, or the last segment of exactly one area's path."""
        t = term.strip().strip("/")
        if t in self.areas:
            return t
        hits = [a for a in self.areas if a.rsplit("/", 1)[-1] == t]
        return hits[0] if len(hits) == 1 else None

    def in_area(self, area: str, deep: bool = False) -> list[str]:
        return [i.id for i in self.ideas.values()
                if i.area == area or (deep and i.area.startswith(area + "/"))]

    def children(self, area: str) -> list[str]:
        """The areas directly below `area` ('' for the top of the tree)."""
        depth = 0 if not area else area.count("/") + 1
        return sorted(a for a in self.areas if a.count("/") == depth
                      and (not area or a.startswith(area + "/")))

    def coverage(self, ids: list[str]) -> Coverage:
        asked = [i for i in ids if any(a.flag != "pre" for a in self.answers_for(i))]
        last = max((a.at for i in asked for a in self.answers_for(i)), default=None)
        return Coverage(len(ids), len(asked), last)

    # -- search

    def hay(self, i: Idea) -> str:
        return norm(" ".join([i.id, i.name, i.statement, *i.aliases]))

    def search(self, term: str, limit: int = 12) -> list[str]:
        """Ideas whose text contains every word of the term, names and aliases first."""
        words = norm(term).split()
        if not words:
            return []
        scored = []
        for i in self.ideas.values():
            if matches(term, self.hay(i)):
                label = norm(" ".join([i.name, *i.aliases]))
                scored.append((-sum(w in label for w in words), i.name, i.id))
        return [iid for *_, iid in sorted(scored)[:limit]]

    def nearest(self, term: str, n: int = 3) -> list[str]:
        """The names closest in spelling to a term that matched nothing."""
        names = {norm(i.name): i.id for i in self.ideas.values()}
        for a, ids in self._alias.items():
            names.setdefault(a, ids[0])
        close = difflib.get_close_matches(norm(term), list(names), n=n, cutoff=0.5)
        return list(dict.fromkeys(names[c] for c in close))

    def similar(self, name: str, statement: str, skip: str = "",
                threshold: float = 0.85) -> list[tuple[float, str]]:
        """Ideas whose name or statement is close to these: likely duplicates."""
        kn, ks = norm(name), norm(statement)
        out = []
        for i in self.ideas.values():
            if i.id == skip:
                continue
            r = max(difflib.SequenceMatcher(None, kn, norm(i.name)).ratio(),
                    difflib.SequenceMatcher(None, ks, norm(i.statement)).ratio() if ks else 0,
                    1.0 if kn in self._alias else 0)
            if r >= threshold:
                out.append((r, i.id))
        return sorted(out, reverse=True)

    # -- the graph

    def cycle_through(self, src: str, dsts: list[str]) -> list[str] | None:
        """If edges src → dsts would close a cycle, one such cycle as a list of ids."""
        for d in dsts:
            path = self._path(d, src)
            if path:
                return [src, *path]
        return None

    def _path(self, start: str, goal: str) -> list[str] | None:
        stack, seen = [(start, [start])], {start}
        while stack:
            node, path = stack.pop()
            if node == goal:
                return path
            for nxt in (*self.needs.get(node, ()), *self.uses.get(node, ())):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append((nxt, [*path, nxt]))
        return None

    def cycles(self) -> list[list[str]]:
        """Every edge that closes a cycle, as the cycle it closes."""
        out = []
        for src in self.ideas:
            for d in (*self.needs.get(src, ()), *self.uses.get(src, ())):
                p = self._path(d, src)
                if p:
                    out.append([src, *p])
        return out
