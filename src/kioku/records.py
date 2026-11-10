"""The records a model is made of: ideas (with their edges) and answers."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

IDEA_KINDS = ("definition", "result", "proof", "method")
ASK_KINDS = ("pick", "write", "say")  # the item kinds of a question block
ANSWER_KINDS = (*ASK_KINDS, "observed", "triage")  # observed: a step of verified work;
# triage: a name the learner marked as never met
# what happened: `guess` is a right pick at chance confidence, `unmet` a "never met it"
OUTCOMES = ("right", "partly", "wrong", "unmet", "guess")
HELPS = ("hint", "shown")  # help beyond the brief; handed the answer. None: done alone
DEPTHS = ("state", "use", "transfer")


@dataclass(frozen=True)
class Idea:
    """One named unit of knowledge that can be held or lacked on its own.

    The name is what agents use and must be unique; the id never changes and is
    what evidence refers to. Edges are stored on the idea they leave, by the
    names they point to: `needs` (cannot follow this without it) and `uses`
    (doing this carries it out), independently."""

    id: str
    name: str
    kind: str
    area: str  # a path in the area tree, e.g. maths/analysis
    statement: str
    needs: tuple[str, ...] = ()
    uses: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    vault: str | None = None  # the vault note that states it


@dataclass(frozen=True)
class Answer:
    """One answered question item, one observed step, or one name marked never met in a
    triage: the only evidence."""

    at: dt.datetime  # when it was answered (a line with only a date reads as noon)
    id: str  # the idea it is about
    kind: str  # pick, write, say, observed or triage
    outcome: str  # right, partly, wrong, unmet or guess
    ask: str  # the question block (or observed record), q_…
    n: int  # the item's number in its block
    conf: int | None = None  # their confidence digit, for a pick
    flag: str | None = None  # mis: a misconception; pre: before teaching
    depth: str | None = None  # what the question demanded: state, use, transfer
    note: str = ""
    taught: bool = False  # the session explained the idea before this question
    help: str | None = None  # hint or shown; None: without help
    probe: bool = False  # asked to find out what they already held, before any teaching

    @property
    def right(self) -> bool:
        """Right or nearly, by their own doing."""
        return self.outcome in ("right", "partly") and self.help != "shown"

    @property
    def day(self) -> dt.date:
        return self.at.date()
