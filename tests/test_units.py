import datetime as dt

from reader import memory, questions
from reader.records import Answer

NOW = dt.datetime(2026, 11, 2, 12, 0)
DAY = dt.timedelta(days=1)
HOUR = dt.timedelta(hours=1)


def answer(grade, at=NOW, n=1):
    return Answer(at, "p_aaaa", "pick", grade, "q_test", n)


def test_no_answers_is_unknown_not_zero():
    rc = memory.recall([], NOW)
    assert rc.r is None and rc.n == 0


def test_recall_decays_with_time():
    a = [answer("good")]
    assert memory.recall(a, NOW).r == 1
    later = memory.recall(a, NOW + 10 * DAY).r
    assert 0 < later < memory.recall(a, NOW + DAY).r < 1


def test_recall_decays_within_the_day():
    a = [answer("good")]
    r = [memory.recall(a, NOW + h * HOUR).r for h in (0, 1, 4, 11)]
    assert r[0] == 1 and r == sorted(r, reverse=True) and len(set(r)) == 4
    # a hard first answer fades faster than a good one
    assert memory.recall([answer("hard")], NOW + 4 * HOUR).r < r[2]


def test_two_answers_hours_apart_are_a_short_term_review():
    # FSRS-6's same-day update: a second right answer resets R but barely moves
    # stability; a miss within the day lowers it
    once = memory.recall([answer("good")], NOW + 3 * HOUR)
    twice = memory.recall([answer("good"), answer("good", NOW + 3 * HOUR)], NOW + 3 * HOUR)
    assert twice.r == 1 > once.r and twice.stability >= once.stability
    lapse = memory.recall([answer("good"), answer("again", NOW + 3 * HOUR),
                           answer("good", NOW + 4 * HOUR)], NOW + 4 * HOUR)
    assert lapse.stability < once.stability


def test_a_miss_holds_r_at_zero_until_a_right_answer():
    a = [answer("good"), answer("again", NOW + 3 * DAY)]
    assert memory.recall(a, NOW + 3 * DAY).r == 0
    a.append(answer("good", NOW + 4 * DAY))
    assert memory.recall(a, NOW + 4 * DAY).r == 1


def test_a_guess_is_recorded_but_not_graded():
    rc = memory.recall([answer("guess")], NOW)
    assert rc.r is None and rc.n == 1


def test_evidence_lines_carry_the_time_and_old_ones_read_as_noon():
    from reader.store import format_answer, parse_answer
    a = answer("good", dt.datetime(2026, 11, 3, 9, 41))
    line = format_answer(a)
    assert line.startswith("- 2026-11-03T09:41 p_aaaa pick good ")
    assert parse_answer(line) == a
    old = parse_answer("- 2026-11-02 p_aaaa pick good 8 q_test/1 — picked x")
    assert old.at == dt.datetime(2026, 11, 2, 12, 0)


BLOCK = """# t
1 pick p_aaaa: q
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


def test_parse_block_reports_problems():
    _, _, problems = questions.parse_block("1 pick p_aaaa: q\n  - only wrong\n")
    assert any("exactly one" in p for p in problems)


def test_confident_wrong_pick_is_a_misconception():
    g = questions.grade_reply(block(), "1b9", NOW)
    (a,) = g.answers
    assert (a.grade, a.conf, a.flag) == ("again", 9, "mis") and "a wrong model" in a.note


def test_say_items_wait_for_the_agent():
    ask = block()
    g = questions.grade_reply(ask, "1a8 2: since it must", NOW)
    assert [a.grade for a in g.answers] == ["good"] and g.to_grade == [2]
    a = questions.grade_say(ask, 2, "hard", NOW)
    assert (a.kind, a.grade, a.note) == ("say", "hard", "since it must")


def test_parse_reply_reads_thoughts():
    assert questions.parse_reply("1b8: hmm 2?", 2) == [(1, "b8", "hmm"), (2, "?", "")]


def test_a_chain_with_two_premises_forks_through_a_knot():
    from reader import view
    from reader.model import Model
    from reader.records import Chain, Prop
    from reader.store import Snapshot
    props = {i: Prop(i, i, "s") for i in ("p_a", "p_b", "p_c", "p_d")}
    chains = {"c_x": Chain("c_x", ("p_a", "p_b"), "p_c", "step")}
    g = view.graph(Model(Snapshot(props, chains, [], []), NOW))
    assert {n["id"] for n in g["nodes"] if n.get("knot")} == {"c_x"}
    assert sorted((l["source"], l["target"], l["arrow"]) for l in g["links"]) == [
        ("c_x", "p_c", True), ("p_a", "c_x", False), ("p_b", "c_x", False)]
