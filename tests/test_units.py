import datetime as dt

from reader import memory, questions
from reader.records import Answer

DAY = dt.date(2026, 11, 2)
NOW = dt.datetime(2026, 11, 2, 12, 0)


def answer(grade, day=DAY, n=1):
    return Answer(day, "p_aaaa", "pick", grade, "q_test", n)


def test_no_answers_is_unknown_not_zero():
    rc = memory.recall([], DAY)
    assert rc.r is None and rc.n == 0


def test_recall_decays_with_time():
    a = [answer("good")]
    assert memory.recall(a, DAY).r == 1
    later = memory.recall(a, DAY + dt.timedelta(days=10)).r
    assert 0 < later < memory.recall(a, DAY + dt.timedelta(days=1)).r < 1


def test_a_miss_holds_r_at_zero_until_a_right_answer():
    a = [answer("good"), answer("again", DAY + dt.timedelta(days=3))]
    assert memory.recall(a, DAY + dt.timedelta(days=3)).r == 0
    a.append(answer("good", DAY + dt.timedelta(days=4)))
    assert memory.recall(a, DAY + dt.timedelta(days=4)).r == 1


def test_a_guess_is_recorded_but_not_graded():
    rc = memory.recall([answer("guess")], DAY)
    assert rc.r is None and rc.n == 1


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
    g = questions.grade_reply(block(), "1b9", DAY, NOW)
    (a,) = g.answers
    assert (a.grade, a.conf, a.flag) == ("again", 9, "mis") and "a wrong model" in a.note


def test_say_items_wait_for_the_agent():
    ask = block()
    g = questions.grade_reply(ask, "1a8 2: since it must", DAY, NOW)
    assert [a.grade for a in g.answers] == ["good"] and g.to_grade == [2]
    a = questions.grade_say(ask, 2, "hard", DAY)
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
    g = view.graph(Model(Snapshot(props, chains, [], []), DAY))
    assert {n["id"] for n in g["nodes"] if n.get("knot")} == {"c_x"}
    assert sorted((l["source"], l["target"], l["arrow"]) for l in g["links"]) == [
        ("c_x", "p_c", True), ("p_a", "c_x", False), ("p_b", "c_x", False)]
