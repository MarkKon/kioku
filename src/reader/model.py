"""The model in memory: propositions, chains, and each id's recall now."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from . import memory
from .records import Answer, Chain, Prop
from .store import Snapshot
from .text import matches, norm


@dataclass(frozen=True)
class Lookup:
    """An idea in context: what matched, what it rests on, what rests on it."""

    matched: list[str]
    rests_on: list[str]  # chains into the matches, then their premises, a few levels deep
    rests_on_it: list[str]  # chains out of the matches, then their conclusions


class Model:
    def __init__(self, snap: Snapshot, now: dt.datetime):
        self.props: dict[str, Prop] = snap.props
        self.chains: dict[str, Chain] = snap.chains
        self.answers: list[Answer] = snap.answers
        self.problems: list[str] = snap.problems
        self.now = now
        self.today = now.date()
        self._by_id: dict[str, list[Answer]] = {}
        for a in self.answers:
            self._by_id.setdefault(a.id, []).append(a)
        self._into: dict[str, list[str]] = {}
        for c in self.chains.values():
            self._into.setdefault(c.conclusion, []).append(c.id)
        self._recall: dict[str, memory.Recall] = {}

    def exists(self, iid: str) -> bool:
        return iid in self.props or iid in self.chains

    def ids(self) -> list[str]:
        return [*self.props, *self.chains]

    def name(self, iid: str) -> str:
        if iid in self.props:
            return self.props[iid].name
        c = self.chains.get(iid)
        if c:
            return " ∧ ".join(map(self.name, c.premises)) + " ⟹ " + self.name(c.conclusion)
        return iid

    def answers_for(self, iid: str) -> list[Answer]:
        return self._by_id.get(iid, [])

    def recall(self, iid: str) -> memory.Recall:
        if iid not in self._recall:
            self._recall[iid] = memory.recall(self.answers_for(iid), self.now)
        return self._recall[iid]

    # -- search

    def hay(self, p: Prop) -> str:
        return norm(" ".join([p.id, p.name, p.statement, *p.aliases, *p.topics]))

    def match(self, terms: list[str]) -> list[str]:
        """Ids named directly, propositions under a #topic, and propositions whose
        text contains every word of a term."""
        hits = []
        for t in terms:
            if self.exists(t):
                hits.append(t)
            elif t.startswith("#"):
                hits += [p.id for p in self.props.values() if t[1:] in p.topics]
            else:
                hits += [p.id for p in self.props.values() if matches(t, self.hay(p))]
        return list(dict.fromkeys(hits))

    def find(self, terms: list[str], limit: int) -> list[str]:
        """Propositions ranked by how many words of the terms they contain."""
        words = [w for t in terms for w in norm(t).split()]
        scored = []
        for p in self.props.values():
            hay, name = self.hay(p), norm(" ".join([p.name, *p.aliases]))
            score = sum(w in hay for w in words) + sum(w in name for w in words)
            if score:
                scored.append((-score, p.id))
        return [pid for _, pid in sorted(scored)[:limit]]

    def lookup(self, terms: list[str], depth: int = 2, limit: int | None = 30) -> Lookup:
        matched = self.match(terms)[:limit]
        return Lookup(matched, self._below(matched, depth), self._above(matched))

    # -- the graph around some ids

    def _below(self, seeds: list[str], depth: int) -> list[str]:
        chains: list[str] = []
        premises: list[str] = []
        seen = set(seeds)

        def take(pids):
            new = [p for p in pids if p not in seen]
            seen.update(new)
            premises.extend(new)
            return new

        frontier = [s for s in seeds if s in self.props]
        for cid in (s for s in seeds if s in self.chains):
            frontier += take(self.chains[cid].premises)
        for _ in range(depth):
            nxt = []
            for pid in frontier:
                for cid in self._into.get(pid, []):
                    if cid not in chains and cid not in seeds:
                        chains.append(cid)
                    nxt += take(self.chains[cid].premises)
            frontier = nxt
        return chains + premises

    def _above(self, seeds: list[str]) -> list[str]:
        chains: list[str] = []
        conclusions = [self.chains[s].conclusion for s in seeds if s in self.chains]
        for c in self.chains.values():
            if c.id not in seeds and any(p in seeds for p in c.premises):
                chains.append(c.id)
                conclusions.append(c.conclusion)
        return chains + [p for p in dict.fromkeys(conclusions) if p not in seeds]
