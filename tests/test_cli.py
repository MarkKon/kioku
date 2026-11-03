import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


BLOCK = """# test
1 pick p_aaaa: increments are
  * independent
  - dependent :: thinks increments correlate
2 write p_bbbb: QV of BM
  = $t$
3 say c_cccc: why
  = because
"""


@pytest.fixture
def reader(tmp_path):
    home = tmp_path / "model"
    home.mkdir()
    (tmp_path / "vault" / "notes").mkdir(parents=True)
    (home / "props.md").write_text(
        "# Propositions\n\n"
        "- p_aaaa · increments · BM increments are independent · topics: sde\n"
        "- p_bbbb · quadratic-variation · the QV of BM on [0,t] is t · topics: sde\n")
    (home / "chains.md").write_text(
        "# Chains\n\n- c_cccc · p_aaaa ⟹ p_bbbb · step: mean and variance of the sum\n")
    env = {**os.environ, "READER_HOME": str(home), "READER_VAULT": str(tmp_path / "vault"),
           "READER_TODAY": "2026-11-02"}

    def run(*args, stdin=None, ok=True, at=None):
        r = subprocess.run([sys.executable, "-m", "reader", *args], input=stdin,
                           capture_output=True, text=True,
                           env={**env, "READER_TODAY": at} if at else env)
        if ok:
            assert r.returncode == 0, r.stderr
        return r

    run.home = home
    return run


def ask(reader):
    out = reader("ask", stdin=BLOCK).stdout
    qid = next(t for t in out.split("`") if t.startswith("reader answer q_")).split()[2]
    return qid, out


def evidence(reader):
    return [l for l in (reader.home / "evidence.md").read_text().splitlines() if l.startswith("- ")]


def test_no_evidence_without_answers(reader):
    out = reader("check", "increments").stdout
    assert "no evidence" in out and "R   –" in out


def test_answers_are_recorded_at_once(reader):
    qid, out = ask(reader)
    assert (reader.home / "asks" / f"{qid}.json").exists()
    right = "a" if "**a)** independent" in out else "b"
    reader("answer", qid, f"1{right}9 2. 3: variance shrinks")
    assert [l.split()[2] for l in evidence(reader)] == ["p_aaaa"]
    reader("answer", qid, "2=")
    reader("grade", qid, "3", "hard")
    lines = evidence(reader)
    assert [l.split()[2:5] for l in lines] == [
        ["p_aaaa", "pick", "good"], ["p_bbbb", "write", "good"], ["c_cccc", "say", "hard"]]
    assert all(f"{qid}/" in l for l in lines)
    reader("lint")


def test_wrong_last_answer_holds_r_at_zero(reader):
    qid, out = ask(reader)
    wrong = "b" if "**a)** independent" in out else "a"
    reader("answer", qid, f"1{wrong}9")
    line = evidence(reader)[0]
    assert " again 9 mis " in line and "misconception: thinks increments correlate" in line
    row = next(l for l in reader("check", "p_aaaa").stdout.splitlines() if l.startswith("  p_aaaa"))
    assert "R .00" in row and "! last answer" in row


def test_redo_replaces_the_items_evidence_and_archives_the_old(reader):
    qid, _ = ask(reader)
    reader("answer", qid, "1-")
    assert " unseen " in evidence(reader)[0]
    reader("answer", qid, "--redo", "1?")
    lines = evidence(reader)
    assert len(lines) == 1 and "could not produce it" in lines[0]
    archive = (reader.home / "archive.md").read_text()
    assert f"## 2026-11-02 · {qid}/1 · replaced" in archive and " unseen " in archive


def test_answers_are_stamped_with_the_time_and_r_falls_within_the_day(reader):
    qid, out = ask(reader)
    right = "a" if "**a)** independent" in out else "b"
    reader("answer", qid, f"1{right}9", at="2026-11-02T09:15")
    assert evidence(reader)[0].startswith("- 2026-11-02T09:15 p_aaaa pick good 9 ")

    def r_at(t):
        out = reader("show", "p_aaaa", at=t).stdout
        return float(out.split("R now ")[1].split(",")[0])
    assert r_at("2026-11-02T09:15") == 1 > r_at("2026-11-02T12:00") > r_at("2026-11-02T20:00")
    row = next(l for l in reader("check", "p_aaaa", at="2026-11-02T20:00").stdout.splitlines()
               if l.startswith("  p_aaaa"))
    assert "09:15 good" in row


def test_retract_archives_the_answer_and_reopens_the_item(reader):
    qid, out = ask(reader)
    wrong = "b" if "**a)** independent" in out else "a"
    right = "a" if wrong == "b" else "b"
    reader("answer", qid, f"1{wrong}8")
    assert "--why" in reader("retract", qid, "1", ok=False).stderr
    reader("retract", qid, "1", "--why", "misclick: meant the other option")
    assert evidence(reader) == []
    archive = (reader.home / "archive.md").read_text()
    assert f"{qid}/1 · retracted: misclick" in archive
    reader("answer", qid, f"1{right}8")  # open again, no --redo needed
    assert " good 8 " in evidence(reader)[0]
    assert "no recorded answer" in reader("retract", qid, "2", "--why", "x", ok=False).stderr
    reader("lint")


def test_check_shows_premises_and_dependents(reader):
    out = reader("check", "c_cccc").stdout
    rests_on, rests_on_it = out.split("rests on it")
    assert "p_aaaa" in rests_on and "p_bbbb" in rests_on_it


def test_answer_needs_a_block_id(reader):
    r = reader("answer", "1a9", ok=False)
    assert r.returncode != 0


def page_data(page):
    return json.loads(page.split("const DATA = ", 1)[1].split(";\n", 1)[0])


def test_graph_writes_a_page_with_the_neighbourhood(reader, tmp_path):
    out = tmp_path / "g.html"
    reader("graph", "quadratic", "--out", str(out), "--no-open")
    page = out.read_text()
    data = page_data(page)
    assert data["live"] is False
    assert {n["id"] for n in data["nodes"]} == {"p_aaaa", "p_bbbb"}
    assert [n["id"] for n in data["nodes"] if n["focus"]] == ["p_bbbb"]
    assert data["links"] == [{"source": "p_aaaa", "target": "p_bbbb", "chain": "c_cccc",
                              "arrow": True}]
    assert "ForceGraph" in page


def chains(reader):
    return [l for l in (reader.home / "chains.md").read_text().splitlines() if l.startswith("- ")]


def test_amend_rewrites_in_place(reader):
    reader("amend", "p_bbbb", "--name", "qv-of-bm", "--topics", "sde, bm")
    props = (reader.home / "props.md").read_text().splitlines()
    assert props[-1] == "- p_bbbb · qv-of-bm · the QV of BM on [0,t] is t · topics: sde, bm"
    reader("amend", "c_cccc", "--step", "sum of independent increments")
    assert chains(reader) == ["- c_cccc · p_aaaa ⟹ p_bbbb · step: sum of independent increments"]
    reader("amend", "c_cccc", "--chain", "qv-of-bm => p_aaaa")
    assert chains(reader)[0].startswith("- c_cccc · p_bbbb ⟹ p_aaaa · ")
    assert "is a chain" in reader("amend", "c_cccc", "--name", "x", ok=False).stderr
    assert "nothing to change" in reader("amend", "p_aaaa", ok=False).stderr
    assert "already has this name" in reader("amend", "p_bbbb", "--name", "increments",
                                             ok=False).stderr
    reader("lint")


def test_amending_the_claim_of_an_answered_id_needs_force(reader):
    qid, _ = ask(reader)
    reader("answer", qid, "2=")
    r = reader("amend", "p_bbbb", "--statement", "QV is 2t", ok=False)
    assert "1 answer(s)" in r.stderr
    reader("amend", "p_bbbb", "--name", "qv")  # wording around the claim is free
    reader("amend", "p_bbbb", "--statement", "the QV of BM on [0,t] equals t", "--force")
    assert "equals t" in reader("show", "p_bbbb").stdout
    assert len(evidence(reader)) == 1


def test_delete_archives_evidence_and_respects_chains(reader):
    qid, _ = ask(reader)
    reader("answer", qid, "2=")
    assert "c_cccc" in reader("delete", "p_bbbb", ok=False).stderr  # a chain rests on it
    reader("delete", "c_cccc")
    assert chains(reader) == []
    assert "--force" in reader("delete", "p_bbbb", ok=False).stderr  # it has an answer
    out = reader("delete", "p_bbbb", "--force", "--why", "duplicate").stdout
    assert "1 answer(s) moved" in out
    assert evidence(reader) == []
    archive = (reader.home / "archive.md").read_text()
    assert "## 2026-11-02 · deleted p_bbbb · duplicate" in archive and f"{qid}/2" in archive
    assert "p_bbbb" not in (reader.home / "props.md").read_text()
    reader("lint")


def test_graph_serves_a_page_built_afresh_on_every_request(reader):
    import urllib.request
    env = {**os.environ, "READER_HOME": str(reader.home), "READER_TODAY": "2026-11-02"}
    proc = subprocess.Popen([sys.executable, "-m", "reader", "graph", "--no-open"],
                            stdout=subprocess.PIPE, text=True, env=env)
    try:
        url = proc.stdout.readline().split()[0]
        first = page_data(urllib.request.urlopen(url).read().decode())
        assert first["live"] is True
        assert next(n for n in first["nodes"] if n["id"] == "p_aaaa")["n"] == 0
        qid, _ = ask(reader)
        reader("answer", qid, "1-")
        again = page_data(urllib.request.urlopen(url).read().decode())
        assert next(n for n in again["nodes"] if n["id"] == "p_aaaa")["n"] == 1
    finally:
        proc.terminate()
        proc.wait(5)
