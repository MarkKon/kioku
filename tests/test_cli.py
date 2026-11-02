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

    def run(*args, stdin=None, ok=True):
        r = subprocess.run([sys.executable, "-m", "reader", *args], input=stdin,
                           capture_output=True, text=True, env=env)
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


def test_redo_replaces_the_items_evidence(reader):
    qid, _ = ask(reader)
    reader("answer", qid, "1-")
    assert " unseen " in evidence(reader)[0]
    reader("answer", qid, "--redo", "1?")
    lines = evidence(reader)
    assert len(lines) == 1 and "could not produce it" in lines[0]


def test_check_shows_premises_and_dependents(reader):
    out = reader("check", "c_cccc").stdout
    rests_on, rests_on_it = out.split("rests on it")
    assert "p_aaaa" in rests_on and "p_bbbb" in rests_on_it


def test_answer_needs_a_block_id(reader):
    r = reader("answer", "1a9", ok=False)
    assert r.returncode != 0
