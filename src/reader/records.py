"""The three records a model is made of: propositions, chains and answers."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

KINDS = ("pick", "write", "say")
GRADES = ("again", "hard", "good", "easy")  # `guess` is recorded but carries no grade


@dataclass(frozen=True)
class Prop:
    """One checkable claim, with its assumptions inside it."""

    id: str
    name: str
    statement: str
    topics: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    vault: str | None = None  # the vault note that states it


@dataclass(frozen=True)
class Chain:
    """Premises that together give a conclusion, by a named step."""

    id: str
    premises: tuple[str, ...]
    conclusion: str
    step: str


@dataclass(frozen=True)
class Answer:
    """One answered question item: the only evidence of what the reader holds."""

    at: dt.datetime  # when it was answered (a line with only a date reads as noon)
    id: str  # the proposition or chain the item tests
    kind: str  # pick, write or say
    grade: str  # again, hard, good, easy, or guess
    ask: str  # the question block, q_…
    n: int  # the item's number in its block
    conf: int | None = None  # their confidence digit, for a pick
    flag: str | None = None  # mis: shows a misconception; unseen: never met it
    note: str = ""

    @property
    def day(self) -> dt.date:
        return self.at.date()
