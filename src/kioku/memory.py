"""The memory model: one idea's answers → the chance the learner recalls it now.

FSRS-6 with the py-fsrs 6.x default parameters, run on elapsed time in
fractional days rather than whole calendar days, so recall also falls within the
day of an answer. This module is the seam for a better model: nothing else
knows how R is computed.

An answer records what happened, not a grade. This module reads it as follows:

  a lapse        wrong, never met, or right only after being handed the answer
  not counted    a guess, or an answer given before teaching (`pre`)
  right          a number from 2 to 3 for how sure the evidence is, where FSRS
                 has its grades "hard" and "good": 2 for a slip or for help
                 beyond the brief; for a pick, 2 plus the learner's own share of
                 right picks at that confidence digit; 3 otherwise

A right first answer to an idea the session had not taught shows knowledge that
predates the record. It starts at OLD days of stability, where FSRS would start
a new card at about two.
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
LAPSE, HARD, GOOD = 1.0, 2.0, 3.0
OLD = 30.0  # days of stability for knowledge that predates the record
PRIOR = 10  # picks' worth of trust in a confidence digit before the record says otherwise


@dataclass(frozen=True)
class Recall:
    r: float | None  # chance of recall now; None: no counted answer yet
    stability: float | None  # days until R falls to 0.9
    n: int  # answers recorded, counted or not
    last: Answer | None  # the latest answer


def calibration(answers: list[Answer]) -> dict[int, float]:
    """Confidence digit → the learner's share of right picks at that digit, pulled
    toward the digit itself (digit 7 → 0.7) while their record at it is thin."""
    bins: dict[int, list[bool]] = {}
    for a in answers:
        if a.kind == "pick" and a.conf is not None and a.flag != "pre" and a.outcome != "unmet":
            bins.setdefault(a.conf, []).append(a.outcome in ("right", "guess"))
    return {c: (sum(x) + PRIOR * c / 10) / (len(x) + PRIOR) for c, x in sorted(bins.items())}


def quality(a: Answer, calib: dict[int, float]) -> float | None:
    """What an answer is worth to FSRS: None (not counted), LAPSE, or HARD to GOOD."""
    if a.flag == "pre" or a.outcome == "guess":
        return None
    if a.outcome in ("wrong", "unmet") or a.help == "shown":
        return LAPSE
    if a.outcome == "partly" or a.help == "hint":
        return HARD
    if a.kind == "pick":
        c = 5 if a.conf is None else a.conf
        return HARD + min(1.0, max(0.0, calib.get(c, c / 10)))
    return GOOD


def recall(answers: list[Answer], now: dt.datetime,
           calib: dict[int, float] | None = None) -> Recall:
    """Replay the counted answers through FSRS.

    FSRS assumes the item was relearned after a miss. Seeing the right answer
    is not evidence, so a lapse as the last answer holds R at 0 until a right
    one."""
    answers = sorted((a for a in answers if a.flag != "pre"), key=lambda a: a.at)  # stable: file order at equal times
    last = answers[-1] if answers else None
    counted = [(_days(a.at), q, a.taught) for a in answers
               if (q := quality(a, calib or {})) is not None]
    if not counted:
        return Recall(None, None, len(answers), last)
    s, last_t = _replay(counted)
    r = 0.0 if counted[-1][1] < HARD else _retrievability(s, _days(now) - last_t)
    return Recall(r, s, len(answers), last)


def _days(t: dt.datetime) -> float:
    """A moment as a count of days, with the time of day as the fraction."""
    return t.toordinal() + (t.hour * 3600 + t.minute * 60 + t.second) / 86400


def _retrievability(s: float, t: float) -> float:
    return (1 + FACTOR * max(t, 0.0) / s) ** DECAY


def _replay(counted: list[tuple[float, float, bool]]) -> tuple[float, float]:
    """(time in days, quality, taught) in order → (stability, time of the last answer)."""
    (t, q, taught), rest = counted[0], counted[1:]
    s, d, last = _initial_stability(q), _clamp(_initial_difficulty(q)), t
    if q >= HARD and not taught:
        s = max(s, OLD)
    for t, q, _ in rest:
        s, d, last = _next_stability(s, d, q, t - last), _next_difficulty(d, q), t
    return s, last


def _clamp(d: float) -> float:
    return min(10.0, max(1.0, d))


def _initial_stability(q: float) -> float:
    """FSRS's first stability, read between its grades on a log scale."""
    if q < HARD:
        return W[0]
    return math.exp((GOOD - q) * math.log(W[1]) + (q - HARD) * math.log(W[2]))


def _initial_difficulty(q: float) -> float:
    return W[4] - math.exp(W[5] * (q - 1)) + 1


def _next_difficulty(d: float, q: float) -> float:
    d2 = d + (10 - d) * (-W[6] * (q - 3)) / 9
    return _clamp(W[7] * _initial_difficulty(4) + (1 - W[7]) * d2)


def _next_stability(s: float, d: float, q: float, t: float) -> float:
    if t < 1:  # within a day: FSRS-6's short-term update
        inc = math.exp(W[17] * (q - 3 + W[18])) * s ** -W[19]
        return max(s * (max(inc, 1.0) if q >= HARD else inc), 0.001)
    r = _retrievability(s, t)
    if q < HARD:
        lapse = W[11] * d ** -W[12] * ((s + 1) ** W[13] - 1) * math.exp((1 - r) * W[14])
        return max(min(lapse, s / math.exp(W[17] * W[18])), 0.001)
    hard = W[15] + (1 - W[15]) * (q - HARD)  # FSRS's penalty for "hard", fading out toward "good"
    return s * (1 + math.exp(W[8]) * (11 - d) * s ** -W[9]
                * (math.exp((1 - r) * W[10]) - 1) * hard)
