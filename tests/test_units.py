import datetime as dt

from kioku import memory, questions
from kioku.records import Answer

NOW = dt.datetime(2026, 11, 2, 12, 0)
DAY = dt.timedelta(days=1)
HOUR = dt.timedelta(hours=1)


def answer(outcome, at=NOW, n=1, conf=9, taught=True, **more):
    """A pick, by default one on an idea the session taught (FSRS's own start)."""
    return Answer(at, "p_aaaa", "pick", outcome, "q_test", n, conf=conf, taught=taught, **more)


def test_no_answers_is_unknown_not_zero():
    rc = memory.recall([], NOW)
    assert rc.r is None and rc.n == 0


def test_recall_decays_with_time():
    a = [answer("right")]
    assert memory.recall(a, NOW).r == 1
    later = memory.recall(a, NOW + 10 * DAY).r
    assert 0 < later < memory.recall(a, NOW + DAY).r < 1


def test_recall_decays_within_the_day():
    a = [answer("right")]
    r = [memory.recall(a, NOW + h * HOUR).r for h in (0, 1, 4, 11)]
    assert r[0] == 1 and r == sorted(r, reverse=True) and len(set(r)) == 4
    # a slip fades faster than a clean answer
    assert memory.recall([answer("partly")], NOW + 4 * HOUR).r < r[2]


def test_two_answers_hours_apart_are_a_short_term_review():
    # FSRS-6's same-day update: a second right answer resets R but barely moves
    # stability; a miss within the day lowers it
    once = memory.recall([answer("right")], NOW + 3 * HOUR)
    twice = memory.recall([answer("right"), answer("right", NOW + 3 * HOUR)], NOW + 3 * HOUR)
    assert twice.r == 1 > once.r and twice.stability >= once.stability
    lapse = memory.recall([answer("right"), answer("wrong", NOW + 3 * HOUR),
                           answer("right", NOW + 4 * HOUR)], NOW + 4 * HOUR)
    assert lapse.stability < once.stability


def test_a_miss_holds_r_at_zero_until_a_right_answer():
    a = [answer("right"), answer("wrong", NOW + 3 * DAY)]
    assert memory.recall(a, NOW + 3 * DAY).r == 0
    a.append(answer("right", NOW + 4 * DAY))
    assert memory.recall(a, NOW + 4 * DAY).r == 1
    # never met, and handed the answer, hold it at zero too
    assert memory.recall([answer("unmet")], NOW).r == 0
    assert memory.recall([answer("right", help="shown")], NOW).r == 0


def test_a_guess_is_recorded_but_not_counted():
    rc = memory.recall([answer("guess", conf=2)], NOW)
    assert rc.r is None and rc.n == 1


def test_a_pick_counts_by_the_learners_own_record_at_its_digit():
    week = NOW + 7 * DAY
    sure, unsure = [answer("right", conf=9)], [answer("right", conf=4)]
    assert memory.recall(sure, week).r > memory.recall(unsure, week).r
    # a learner who is nearly always right at 4 has their 4 read as nearly sure
    record = [answer("right", NOW - DAY, n, conf=4) for n in range(40)]
    calib = memory.calibration(record)
    assert calib[4] > 0.85
    assert memory.recall(unsure, week, calib).r > memory.recall(unsure, week).r
    # between FSRS's "hard" and "good", never outside
    assert memory.quality(unsure[0], calib) < memory.quality(sure[0], {}) <= memory.GOOD
    assert memory.quality(answer("right", help="hint"), {}) == memory.HARD


def test_a_right_answer_to_an_idea_never_taught_is_old_knowledge():
    month = NOW + 30 * DAY
    cold = memory.recall([answer("right", taught=False)], month)
    fresh = memory.recall([answer("right", taught=True)], month)
    assert cold.stability == memory.OLD and abs(cold.r - 0.9) < 1e-6
    assert fresh.stability < 3 and fresh.r < cold.r
    # only a first answer starts there: one that follows a miss was learned here
    relearned = memory.recall([answer("unmet", NOW - HOUR), answer("right", taught=False)], month)
    assert relearned.stability < 3


def test_evidence_lines_say_what_happened_and_old_ones_still_read():
    from kioku.store import format_answer, parse_answer
    a = answer("right", dt.datetime(2026, 11, 3, 9, 41))
    line = format_answer(a)
    assert line == "- 2026-11-03T09:41 p_aaaa pick right 9 taught q_test/1"
    assert parse_answer(line) == a
    deep = Answer(a.at, "i_x1y2", "observed", "right", "q_test", 2, depth="use", note="n",
                  help="hint")
    assert format_answer(deep) == "- 2026-11-03T09:41 i_x1y2 observed right hint use q_test/2 — n"
    assert parse_answer(format_answer(deep)) == deep
    # lines from before 2026-11-10 carry a grade, and a date without a time reads as noon
    old = parse_answer("- 2026-11-02 p_aaaa pick good 8 q_test/1 — picked x")
    assert old.at == dt.datetime(2026, 11, 2, 12, 0) and (old.outcome, old.conf) == ("right", 8)
    read = lambda line: (lambda x: (x.outcome, x.help, x.flag))(parse_answer(line))
    assert read("- 2026-11-02T10:00 p_aaaa pick hard 6 use q_test/1") == ("right", None, None)
    assert read("- 2026-11-02T10:00 p_aaaa pick again 9 mis use q_test/1") == ("wrong", None, "mis")
    assert read("- 2026-11-02T10:00 p_aaaa pick again unseen q_test/1") == ("unmet", None, None)
    assert read("- 2026-11-02T10:00 p_aaaa write hard state q_test/1") == ("partly", None, None)
    assert read("- 2026-11-02T10:00 p_aaaa observed hard use q_test/1") == ("right", "hint", None)
    assert read("- 2026-11-02T10:00 p_aaaa observed again use q_test/1") == ("right", "shown", None)
    assert read("- 2026-11-02T10:00 p_aaaa pick guess 2 q_test/1") == ("guess", None, None)


BLOCK = """# t
1 pick p_aaaa transfer: q
  * right
  - wrong :: a wrong model
2 say c_cccc: why
  = because
"""


def block():
    title, items, problems = questions.parse_block(BLOCK)
    assert not problems
    for it in items:
        it["options"].sort(key=lambda o: not o["correct"])  # a) is right
        it["state"] = "open"
    return {"id": "q_test", "title": title, "asked": "", "items": items}


def test_items_name_their_idea_and_depth():
    _, items, _ = questions.parse_block(BLOCK)
    assert [(it["id"], it["depth"]) for it in items] == [("p_aaaa", "transfer"), ("c_cccc", "use")]


def test_parse_block_reports_problems():
    _, _, problems = questions.parse_block("1 pick p_aaaa: q\n  - only wrong\n")
    assert any("exactly one" in p for p in problems)


def test_confident_wrong_pick_is_a_misconception():
    g = questions.grade_reply(block(), "1b9", NOW)
    (a,) = g.answers
    assert (a.outcome, a.conf, a.flag, a.depth) == ("wrong", 9, "mis", "transfer")
    assert "a wrong model" in a.note


def test_say_items_wait_for_the_agent():
    ask = block()
    g = questions.grade_reply(ask, "1a8 2: since it must", NOW)
    assert [a.outcome for a in g.answers] == ["right"] and g.to_grade == [2]
    a = questions.grade_say(ask, 2, "partly", NOW)
    assert (a.kind, a.outcome, a.note) == ("say", "partly", "since it must")


def test_parse_reply_reads_thoughts():
    assert questions.parse_reply("1b8: hmm 2?", 2) == [(1, "b8", "hmm"), (2, "?", "")]


def test_idea_blocks_round_trip():
    from kioku.store import format_area, parse_area
    from kioku.records import Idea
    ideas = [Idea("p_a1b2", "banach", "result", "maths/analysis", "a contraction has one fixed "
                  "point", ("contraction",), (), ("Banach fixed point",), "0ezz"),
             Idea("i_c3d4", "banach-proof", "proof", "maths/analysis", "iterate; Cauchy",
                  ("banach",), ("geometric-series",))]
    problems: list[str] = []
    assert parse_area(format_area("maths/analysis", ideas), "maths/analysis", "f",
                      problems) == ideas
    assert problems == []


def test_edges_and_cycles():
    from kioku.model import Model
    from kioku.records import Idea
    from kioku.store import Snapshot
    ideas = {i.id: i for i in (
        Idea("i_a", "a", "definition", "x", "s"),
        Idea("i_b", "b", "result", "x", "s", needs=("a",)),
        Idea("i_c", "c", "proof", "x/y", "s", needs=("b",), uses=("a",)))}
    m = Model(Snapshot(ideas, set(), []), NOW)
    assert m.needed_by["i_a"] == ["i_b"] and m.used_by["i_a"] == ["i_c"]
    assert m.cycles() == [] and m.cycle_through("i_a", ["i_c"]) == ["i_a", "i_c", "i_a"]
    assert m.areas == {"x", "x/y"} and m.children("x") == ["x/y"]
    assert m.resolve("b") == "i_b" and m.in_area("x", deep=True) == ["i_a", "i_b", "i_c"]
