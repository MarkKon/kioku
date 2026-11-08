import json
import os
import subprocess
import sys

import pytest


AREA = """# maths/probability/stochastic-calculus

## increments · result · p_aaaa
BM increments are independent

## quadratic-variation · result · p_bbbb
the QV of BM on [0,t] is t
- needs: increments
- aliases: QV

## quadratic-variation-proof · proof · c_cccc
mean and variance of the sum of squared increments
- needs: quadratic-variation
- uses: increments
"""

BLOCK = """# test
1 pick increments: increments are
  * independent
  - dependent :: thinks increments correlate
2 write QV state: QV of BM
  = $t$
3 say quadratic-variation-proof: why
  = because
"""


@pytest.fixture
def reader(tmp_path):
    home = tmp_path / "model"
    (home / "areas" / "maths" / "probability").mkdir(parents=True)
    (home / "areas" / "maths" / "probability" / "stochastic-calculus.md").write_text(AREA)
    (home / "areas" / "tools").mkdir()
    (home / "areas" / "tools" / "python.md").write_text("# tools/python\n")
    (tmp_path / "vault" / "notes").mkdir(parents=True)
    env = {**os.environ, "READER_HOME": str(home), "READER_VAULT": str(tmp_path / "vault"),
           "READER_TODAY": "2026-11-02"}

    def run(*args, stdin=None, ok=True, at=None):
        r = subprocess.run([sys.executable, "-m", "reader", *args], input=stdin,
                           stdin=None if stdin is not None else subprocess.DEVNULL,
                           capture_output=True, text=True,
                           env={**env, "READER_TODAY": at} if at else env)
        if ok:
            assert r.returncode == 0, r.stderr
        return r

    run.home = home
    run.area = home / "areas" / "maths" / "probability" / "stochastic-calculus.md"
    return run


def ask(reader):
    out = reader("ask", stdin=BLOCK).stdout
    qid = next(t for t in out.split("`") if t.startswith("reader answer q_")).split()[2]
    return qid, out


def evidence(reader):
    return [l for l in (reader.home / "evidence.md").read_text().splitlines() if l.startswith("- ")]


def line_of(out, name):
    return next(l for l in out.splitlines() if l.strip().split()[:1] == [name]
                or l.split()[1:2] == [name])


# -- looking up

def test_context_of_an_idea_shows_its_edges_and_no_evidence(reader):
    out = reader("context", "quadratic-variation").stdout
    assert out.splitlines()[1] == ""
    assert "quadratic-variation · result · maths/probability/stochastic-calculus · R – n0" in out
    assert "needs      increments" in out and "needed by  quadratic-variation-proof" in out
    assert "R   –" in line_of(out, "increments")
    assert "maths/probability/stochastic-calculus · 3 ideas · 0 asked · last never" in out


def test_context_of_an_area_and_of_the_tree(reader):
    out = reader("context", "stochastic-calculus").stdout
    assert "maths/probability/stochastic-calculus · 3 ideas · 0 asked" in out
    assert "quadratic-variation-proof" in out and "proof" in out
    top = reader("context").stdout
    assert "maths/" in top and "probability/" in top and "tools/" in top
    up = reader("context", "maths/probability").stdout
    assert "(no ideas of its own)" in up and "stochastic-calculus/" in up


def test_a_miss_says_where_it_looked_and_what_is_near(reader):
    out = reader("context", "quadratc").stdout
    assert 'no idea, alias or statement matches "quadratc" (3 ideas searched)' in out
    assert "nearest" in out and "quadratic-variation" in out
    hits = reader("context", "squared").stdout
    assert "1 idea(s) mention it" in hits and "quadratic-variation-proof" in hits


# -- asking and recording

def test_answers_are_recorded_at_once_with_their_depth(reader):
    qid, out = ask(reader)
    stored = json.loads((reader.home / "asks" / f"{qid}.json").read_text())
    assert [it["id"] for it in stored["items"]] == ["p_aaaa", "p_bbbb", "c_cccc"]
    right = "a" if "**a)** independent" in out else "b"
    out = reader("answer", qid, f"1{right}9 2. 3: variance shrinks").stdout
    assert "--say 3=" in out
    reader("answer", qid, "2=", "--say", "3=hard")
    lines = evidence(reader)
    assert [l.split()[2:5] for l in lines] == [
        ["p_aaaa", "pick", "good"], ["p_bbbb", "write", "good"], ["c_cccc", "say", "hard"]]
    assert " use " in lines[0] and " state " in lines[1]
    assert "(use)" in reader("context", "increments").stdout.splitlines()[2]
    reader("upkeep", "--check")


def test_wrong_last_answer_holds_r_at_zero(reader):
    qid, out = ask(reader)
    wrong = "b" if "**a)** independent" in out else "a"
    reader("answer", qid, f"1{wrong}9")
    line = evidence(reader)[0]
    assert " again 9 mis use " in line and "misconception: thinks increments correlate" in line
    row = line_of(reader("context", "stochastic-calculus").stdout, "increments")
    assert "R .00" in row and "! misconception" in row


def test_redo_regrade_and_retract(reader):
    qid, out = ask(reader)
    reader("answer", qid, "1-")
    assert " unseen " in evidence(reader)[0]
    reader("answer", qid, "--redo", "1?")
    lines = evidence(reader)
    assert len(lines) == 1 and "could not produce it" in lines[0]
    reader("answer", qid, "--regrade", "1=hard")
    assert " hard " in evidence(reader)[0]
    assert "--why" in reader("answer", qid, "--retract", "1", ok=False).stderr
    reader("answer", qid, "--retract", "1", "--why", "misclick")
    assert evidence(reader) == []
    archive = (reader.home / "archive.md").read_text()
    assert f"## 2026-11-02 · {qid}/1 · retracted: misclick" in archive
    right = "a" if "**a)** independent" in out else "b"
    reader("answer", qid, f"1{right}8")  # open again
    assert " good 8 " in evidence(reader)[0]
    reader("upkeep", "--check")


def test_answers_are_stamped_and_r_falls_within_the_day(reader):
    qid, out = ask(reader)
    right = "a" if "**a)** independent" in out else "b"
    reader("answer", qid, f"1{right}9", at="2026-11-02T09:15")
    assert evidence(reader)[0].startswith("- 2026-11-02T09:15 p_aaaa pick good 9 use ")

    def r_at(t):
        out = reader("context", "increments", "--answers", at=t).stdout
        return float(out.split("R now ")[1].split(",")[0])
    assert r_at("2026-11-02T09:15") == 1 > r_at("2026-11-02T12:00") > r_at("2026-11-02T20:00")


def test_ask_refuses_unknown_ideas(reader):
    r = reader("ask", stdin="1 pick nope: q\n  * a\n  - b\n", ok=False)
    assert "unknown idea nope" in r.stderr


def test_observed_work_is_one_call(reader):
    out = reader("observed", "increments=good", "QV=hard", "--step", "2 · qv",
                 "--note", "QV: needed the variance hint").stdout
    assert "2 observed answer(s) recorded" in out
    lines = evidence(reader)
    assert [l.split()[2:6] for l in lines] == [["p_aaaa", "observed", "good", "use"],
                                              ["p_bbbb", "observed", "hard", "use"]]
    assert "needed the variance hint" in lines[1] and "verified by" in lines[0]
    reader("upkeep", "--check")


# -- adding, editing, removing

NEW = """## brownian-motion · definition · maths/probability/stochastic-calculus
a continuous process with independent Gaussian increments, starting at 0
- aliases: Wiener process

## ito-isometry · result · maths/probability/stochastic-calculus
$E[(\\int f dW)^2] = E \\int f^2 dt$ for adapted $f$ in $L^2$
- needs: brownian-motion
- uses: increments
"""


def area_text(reader):
    return reader.area.read_text()


def test_add_reads_ideas_from_stdin_and_keeps_the_format(reader):
    out = reader("add", stdin=NEW).stdout
    assert "brownian-motion → maths/probability/stochastic-calculus (now 5 ideas)" in out
    text = area_text(reader)
    assert "## ito-isometry · result · i_" in text
    assert "- needs: brownian-motion\n- uses: increments" in text
    assert "$E[(\\int f dW)^2]" in text  # no shell ever saw the statement
    assert "needed by  ito-isometry" in reader("context", "Wiener process").stdout
    reader("upkeep", "--check")


def test_add_refuses_what_would_spoil_the_model(reader):
    def refused(text, *flags):
        return reader("add", *flags, stdin=text, ok=False).stderr

    assert "no area maths/topology" in refused("## open-set · definition · maths/topology\nx\n")
    reader("add", "--new-area", stdin="## open-set · definition · maths/topology\nx\n")
    assert (reader.home / "areas" / "maths" / "topology.md").exists()
    assert "edge to unknown idea `filtration`" in refused(
        "## adapted · definition · tools/python\nan adapted process\n- needs: filtration\n")
    assert "the name is taken by p_aaaa" in refused(
        "## increments · result · tools/python\nsomething else entirely\n")
    assert "close to quadratic-variation" in refused(
        "## quadratic-variations · result · tools/python\nthe QV of BM on [0,t] is t\n")
    reader("add", "--anyway", stdin="## quadratic-variations · result · tools/python\n"
                                     "the QV of BM on [0,t] is t\n")
    assert "cycle" in refused("## a-x · result · tools/python\nx one\n- needs: b-x\n\n"
                              "## b-x · result · tools/python\nx two\n- needs: a-x\n")
    assert "not one of" in refused("## odd · lemma · tools/python\nx\n")
    reader("upkeep", "--check")


def test_edit_renames_moves_and_rewrites_edges(reader):
    reader("edit", "increments", "--name", "independent-increments")
    text = area_text(reader)
    assert "## independent-increments · result · p_aaaa" in text
    assert "- needs: independent-increments" in text and "- uses: independent-increments" in text
    reader("edit", "QV", stdin="the quadratic variation of BM on [0,t] equals t\n")
    assert "the quadratic variation of BM on [0,t] equals t" in area_text(reader)
    reader("edit", "quadratic-variation-proof", "--uses", "-independent-increments")
    assert "- uses:" not in area_text(reader)
    assert "cycle" in reader("edit", "independent-increments", "--needs",
                             "+quadratic-variation-proof", ok=False).stderr
    reader("edit", "independent-increments,quadratic-variation", "--area", "maths/bm",
           "--new-area")
    moved = (reader.home / "areas" / "maths" / "bm.md").read_text()
    assert "p_aaaa" in moved and "p_bbbb" in moved and "p_aaaa" not in area_text(reader)
    reader("edit", "quadratic-variation-proof", "--area", "maths/bm")
    assert not reader.area.exists()  # an emptied area's file goes
    reader("upkeep", "--check")


def test_rm_respects_edges_and_archives_answers(reader):
    qid, _ = ask(reader)
    reader("answer", qid, "2=")
    assert "needed or used by quadratic-variation-proof" in reader(
        "rm", "QV", "--why", "x", ok=False).stderr
    reader("rm", "quadratic-variation-proof", "--why", "rewritten")
    out = reader("rm", "QV", "--why", "duplicate").stdout
    assert "1 answer(s) moved" in out
    assert len(evidence(reader)) == 0
    archive = (reader.home / "archive.md").read_text()
    assert "## 2026-11-02 · removed p_bbbb quadratic-variation · duplicate" in archive
    reader("edit", "increments", "--needs", "+brownian", ok=False)
    reader("upkeep", "--check")


# -- the graph page

def page_data(page):
    return json.loads(page.split("const DATA = ", 1)[1].split(";\n", 1)[0])


def test_graph_page_has_ideas_and_marked_edges(reader, tmp_path):
    out = tmp_path / "g.html"
    reader("graph", "quadratic-variation-proof", "--out", str(out), "--no-open")
    data = page_data(out.read_text())
    assert data["live"] is False
    assert {n["id"] for n in data["nodes"]} == {"p_aaaa", "p_bbbb", "c_cccc"}
    assert [n["id"] for n in data["nodes"] if n["focus"]] == ["c_cccc"]
    assert sorted((l["source"], l["target"], l["needs"], l["uses"]) for l in data["links"]) == [
        ("p_aaaa", "c_cccc", False, True), ("p_aaaa", "p_bbbb", True, False),
        ("p_bbbb", "c_cccc", True, False)]
    assert "ForceGraph" in out.read_text()


def test_graph_serves_a_page_built_afresh_on_every_request(reader):
    import urllib.request
    env = {**os.environ, "READER_HOME": str(reader.home), "READER_TODAY": "2026-11-02"}
    proc = subprocess.Popen([sys.executable, "-m", "reader", "graph", "--no-open"],
                            stdout=subprocess.PIPE, text=True, env=env)
    try:
        url = proc.stdout.readline().split()[0]
        first = page_data(urllib.request.urlopen(url).read().decode())
        assert next(n for n in first["nodes"] if n["id"] == "p_aaaa")["n"] == 0
        qid, _ = ask(reader)
        reader("answer", qid, "1-")
        again = page_data(urllib.request.urlopen(url).read().decode())
        assert next(n for n in again["nodes"] if n["id"] == "p_aaaa")["n"] == 1
    finally:
        proc.terminate()
        proc.wait(5)


# -- migration from v0

def test_migration_from_v0(tmp_path):
    v0 = tmp_path / "v0"
    (v0 / "asks").mkdir(parents=True)
    (v0 / "props.md").write_text(
        "# Propositions\n\n"
        "- p_aaaa · increments · BM increments are independent · topics: sde\n"
        "- p_bbbb · quadratic-variation · the QV of BM is t · topics: sde · aliases: QV\n")
    (v0 / "chains.md").write_text(
        "# Chains\n\n- c_cccc · p_aaaa ⟹ p_bbbb · step: mean and variance\n"
        "- c_dddd · p_bbbb ⟹ p_aaaa · step: taught after\n")
    (v0 / "evidence.md").write_text(
        "# Evidence\n\n- 2026-11-02T10:00 c_cccc say good q_aaaa/1 — fine\n"
        "- 2026-11-02T11:00 p_aaaa say hard q_bbbb/1 — observed: needed a hint\n")
    (v0 / "asks" / "q_aaaa.json").write_text(json.dumps(
        {"id": "q_aaaa", "items": [{"n": 1, "kind": "say", "id": "c_cccc"}]}))
    (v0 / "asks" / "q_bbbb.json").write_text(json.dumps(
        {"id": "q_bbbb", "items": [{"n": 1, "kind": "say", "id": "p_aaaa"}]}))
    (tmp_path / "map.txt").write_text("sde = maths/stochastic-calculus\n")

    def mig(*args, ok=True):
        r = subprocess.run([sys.executable, "-m", "reader.migrate", *map(str, args)],
                           capture_output=True, text=True)
        if ok:
            assert r.returncode == 0, r.stderr
        return r

    table = mig("skeleton", v0, "--map", tmp_path / "map.txt").stdout
    assert "- p_bbbb · idea · quadratic-variation · ? · maths/stochastic-calculus · needs: " \
           "increments" in table
    assert "- c_cccc · idea · quadratic-variation-proof · proof" in table  # answered
    assert "- c_dddd · ?" in table
    t = tmp_path / "migration.md"
    t.write_text(table)
    assert "kind `?`" in mig("apply", v0, t, tmp_path / "v1", ok=False).stderr
    assert "- p_aaaa · idea · increments · ? · maths/stochastic-calculus · needs: " \
           "quadratic-variation" in table  # drafted from the teaching-order chain: a cycle
    t.write_text(table.replace("· ? ·", "· result ·").replace("- c_dddd · ?", "- c_dddd · drop"))
    assert "cycle: increments → quadratic-variation" in mig("apply", v0, t, tmp_path / "v1",
                                                           ok=False).stderr
    t.write_text(t.read_text().replace("increments · result · maths/stochastic-calculus · "
                                       "needs: quadratic-variation", "increments · result · "
                                       "maths/stochastic-calculus · needs: "))
    out = mig("apply", v0, t, tmp_path / "v1").stdout
    assert "3 ideas in 1 areas" in out and "1 answer(s) marked observed" in out
    home = tmp_path / "v1"
    assert not (home / "props.md").exists()
    text = (home / "areas" / "maths" / "stochastic-calculus.md").read_text()
    assert "## quadratic-variation-proof · proof · c_cccc\nmean and variance" in text
    assert "- aliases: QV" in text
    assert " p_aaaa observed hard " in (home / "evidence.md").read_text()
    env = {**os.environ, "READER_HOME": str(home), "READER_TODAY": "2026-11-03"}
    r = subprocess.run([sys.executable, "-m", "reader", "upkeep", "--check"],
                       capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stdout + r.stderr
