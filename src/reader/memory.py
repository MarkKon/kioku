"""The memory model: one id's answers → the chance the reader recalls it today.

FSRS-6 with the py-fsrs 6.x default parameters. This module is the seam for a
better model: nothing else knows how R is computed.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass

from .records import Answer

W = (0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334, 3.0194, 0.001, 1.8722,
     0.1666, 0.796, 1.4835, 0.0614, 0.2629, 1.6483, 0.6014, 1.8729, 0.5425,
     0.0912, 0.0658, 0.1542)
DECAY = -W[20]
FACTOR = 0.9 ** (1 / DECAY) - 1
GRADE = {"again": 1, "hard": 2, "good": 3, "easy": 4}


@dataclass(frozen=True)
class Recall:
    r: float | None  # chance of recall today; None: no graded answer yet
    stability: float | None  # days until R falls to 0.9
    n: int  # answers recorded, graded or not
    last: Answer | None  # the latest answer


def recall(answers: list[Answer], today: dt.date) -> Recall:
    """Replay the graded answers through FSRS.

    FSRS assumes the item was relearned after a miss. Seeing the right answer
    is not evidence, so a wrong last answer holds R at 0 until a right one.
    """
    answers = sorted(answers, key=lambda a: a.day)  # stable: file order within a day
    last = answers[-1] if answers else None
    graded = [(a.day.toordinal(), GRADE[a.grade]) for a in answers if a.grade in GRADE]
    if not graded:
        return Recall(None, None, len(answers), last)
    s, last_day = _replay(graded)
    r = 0.0 if graded[-1][1] == 1 else _retrievability(s, today.toordinal() - last_day)
    return Recall(r, s, len(answers), last)


def _retrievability(s: float, t: float) -> float:
    return (1 + FACTOR * max(t, 0.0) / s) ** DECAY


def _replay(graded: list[tuple[int, int]]) -> tuple[float, int]:
    """(day, grade) pairs in order → (stability, day of the last review)."""
    (day, g), rest = graded[0], graded[1:]
    s, d, last = W[g - 1], _clamp(_initial_difficulty(g)), day
    for day, g in rest:
        s, d, last = _next_stability(s, d, g, day - last), _next_difficulty(d, g), day
    return s, last


def _clamp(d: float) -> float:
    return min(10.0, max(1.0, d))


def _initial_difficulty(g: int) -> float:
    return W[4] - math.exp(W[5] * (g - 1)) + 1


def _next_difficulty(d: float, g: int) -> float:
    d2 = d + (10 - d) * (-W[6] * (g - 3)) / 9
    return _clamp(W[7] * _initial_difficulty(4) + (1 - W[7]) * d2)


def _next_stability(s: float, d: float, g: int, t: float) -> float:
    if t < 1:  # same day
        inc = math.exp(W[17] * (g - 3 + W[18])) * s ** -W[19]
        return max(s * (max(inc, 1.0) if g >= 2 else inc), 0.001)
    r = _retrievability(s, t)
    if g == 1:
        lapse = W[11] * d ** -W[12] * ((s + 1) ** W[13] - 1) * math.exp((1 - r) * W[14])
        return max(min(lapse, s / math.exp(W[17] * W[18])), 0.001)
    hard = W[15] if g == 2 else 1
    easy = W[16] if g == 4 else 1
    return s * (1 + math.exp(W[8]) * (11 - d) * s ** -W[9]
                * (math.exp((1 - r) * W[10]) - 1) * hard * easy)
