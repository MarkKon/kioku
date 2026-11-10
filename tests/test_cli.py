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
def kioku(tmp_path):
    home = tmp_path / "model"
    (home / "areas" / "maths" / "probability").mkdir(parents=True)
    (home / "areas" / "maths" / "probability" / "stochastic-calculus.md").write_text(AREA)
    (home / "areas" / "tools").mkdir()
    (home / "areas" / "tools" / "python.md").write_text("# tools/python\n")
    (tmp_path / "vault" / "notes").mkdir(parents=True)
    env = {**os.environ, "KIOKU_HOME": str(home), "KIOKU_VAULT": str(tmp_path / "vault"),
           "KIOKU_TODAY": "2026-11-02"}

    def run(*args, stdin=None, ok=True, at=None):
        r = subprocess.run([sys.executable, "-m", "kioku", *args], input=stdin,
                           stdin=None if stdin is not None else subprocess.DEVNULL,
                           capture_output=True, text=True,
                           env={**env, "KIOKU_TODAY": at} if at else env)
        if ok:
            assert r.returncode == 0, r.stderr
        return r

    run.home = home
    run.area = home / "areas" / "maths" / "probability" / "stochastic-calculus.md"
    return run


def ask(kioku):
    out = kioku("ask", stdin=BLOCK).stdout
    qid = next(t for t in out.split("`") if t.startswith("kioku answer q_")).split()[2]
    return qid, out


def evidence(kioku):
    return [l for l in (kioku.home / "evidence.md").read_text().splitlines() if l.startswith("- ")]


def line_of(out, name):
    return next(l for l in out.splitlines() if l.strip().split()[:1] == [name]
                or l.split()[1:2] == [name])


# -- looking up

def test_context_of_an_idea_shows_its_edges_and_no_evidence(kioku):
    out = kioku("context", "quadratic-variation").stdout
    assert out.splitlines()[1] == ""
    assert "quadratic-variation · result · maths/probability/stochastic-calculus · R – n0" in out
    assert "needs      increments" in out and "needed by  quadratic-variation-proof" in out
    assert "R   –" in line_of(out, "increments")
    assert "maths/probability/stochastic-calculus · 3 ideas · 0 asked · last never" in out


def test_context_of_an_area_and_of_the_tree(kioku):
    out = kioku("context", "stochastic-calculus").stdout
    assert "maths/probability/stochastic-calculus · 3 ideas · 0 asked" in out
    assert "quadratic-variation-proof" in out and "proof" in out
    top = kioku("context").stdout
    assert "maths/" in top and "probability/" in top and "tools/" in top
    up = kioku("context", "maths/probability").stdout
    assert "(no ideas of its own)" in up and "stochastic-calculus/" in up


def test_a_miss_says_where_it_looked_and_what_is_near(kioku):
    out = kioku("context", "quadratc").stdout
    assert 'no idea, alias or statement matches "quadratc" (3 ideas searched)' in out
    assert "nearest" in out and "quadratic-variation" in out
    hits = kioku("context", "squared").stdout
    assert "1 idea(s) mention it" in hits and "quadratic-variation-proof" in hits


# -- asking and recording

def test_answers_are_recorded_at_once_with_their_depth(kioku):
    qid, out = ask(kioku)
    stored = json.loads((kioku.home / "asks" / f"{qid}.json").read_text())
    assert [it["id"] for it in stored["items"]] == ["p_aaaa", "p_bbbb", "c_cccc"]
    right = "a" if "**a)** independent" in out else "b"
    out = kioku("answer", qid, f"1{right}9 2. 3: variance shrinks").stdout
    assert "--say 3=" in out
    kioku("answer", qid, "2=", "--say", "3=hard")
    lines = evidence(kioku)
    assert [l.split()[2:5] for l in lines] == [
        ["p_aaaa", "pick", "right"], ["p_bbbb", "write", "right"], ["c_cccc", "say", "partly"]]
    assert " use " in lines[0] and " state " in lines[1]
    assert "(use)" in kioku("context", "increments").stdout.splitlines()[2]
    kioku("upkeep", "--check")


def test_wrong_last_answer_holds_r_at_zero(kioku):
    qid, out = ask(kioku)
    wrong = "b" if "**a)** independent" in out else "a"
    kioku("answer", qid, f"1{wrong}9")
    line = evidence(kioku)[0]
    assert " wrong 9 mis use " in line and "misconception: thinks increments correlate" in line
    row = line_of(kioku("context", "stochastic-calculus").stdout, "increments")
    assert "R .00" in row and "! misconception" in row


def test_redo_regrade_and_retract(kioku):
    qid, out = ask(kioku)
    kioku("answer", qid, "1-")
    assert " pick unmet " in evidence(kioku)[0]
    kioku("answer", qid, "--redo", "1?")
    lines = evidence(kioku)
    assert len(lines) == 1 and "could not produce it" in lines[0]
    kioku("answer", qid, "--regrade", "1=partly")
    assert " partly " in evidence(kioku)[0]
    assert "--why" in kioku("answer", qid, "--retract", "1", ok=False).stderr
    kioku("answer", qid, "--retract", "1", "--why", "misclick")
    assert evidence(kioku) == []
    archive = (kioku.home / "archive.md").read_text()
    assert f"## 2026-11-02 · {qid}/1 · retracted: misclick" in archive
    right = "a" if "**a)** independent" in out else "b"
    kioku("answer", qid, f"1{right}8")  # open again
    assert " right 8 " in evidence(kioku)[0]
    kioku("upkeep", "--check")


def test_answers_are_stamped_and_r_falls_within_the_day(kioku):
    qid, out = ask(kioku)
    right = "a" if "**a)** independent" in out else "b"
    kioku("answer", qid, f"1{right}9", at="2026-11-02T09:15")
    assert evidence(kioku)[0].startswith("- 2026-11-02T09:15 p_aaaa pick right 9 use ")

    def r_at(t):
        out = kioku("context", "increments", "--answers", at=t).stdout
        return float(out.split("R now ")[1].split(",")[0])
    assert r_at("2026-11-02T09:15") == 1 > r_at("2026-11-02T12:00") > r_at("2026-11-02T20:00")


def test_ask_refuses_unknown_ideas(kioku):
    r = kioku("ask", stdin="1 pick nope: q\n  * a\n  - b\n", ok=False)
    assert "unknown idea nope" in r.stderr


def test_an_answer_before_teaching_is_kept_but_not_evidence(kioku):
    out = kioku("ask", stdin="# p\n1 pick increments pre: guess\n  * a\n  - b\n").stdout
    qid = next(t for t in out.split("`") if t.startswith("kioku answer q_")).split()[2]
    kioku("answer", qid, "1-")
    line = evidence(kioku)[0]
    assert " unmet pre " in line
    row = line_of(kioku("context", "stochastic-calculus").stdout, "increments")
    assert "R   –" in row and "n0" in row  # not evidence: no R, not counted
    assert "1 asked" not in kioku("context").stdout.split("probability")[1].splitlines()[0]
    kioku("upkeep", "--check")


def test_the_formats_are_in_the_help(kioku):
    assert "pick|write|say <idea> [state|use|transfer] [pre|taught]" in kioku("ask", "-h").stdout
    assert "## <name> · <kind> · <area>" in kioku("add", "-h").stdout
    assert "alone  done from the brief" in kioku("observed", "-h").stdout


def test_observed_work_is_one_call(kioku):
    out = kioku("observed", "increments=alone", "QV=hint", "--step", "2 · qv",
                 "--note", "QV: needed the variance hint").stdout
    assert "2 observed answer(s) recorded" in out
    lines = evidence(kioku)
    assert [l.split()[2:6] for l in lines] == [["p_aaaa", "observed", "right", "use"],
                                              ["p_bbbb", "observed", "right", "hint"]]
    assert "needed the variance hint" in lines[1] and "verified by" in lines[0]
    kioku("upkeep", "--check")


def test_triage_records_the_names_never_met(kioku):
    out = kioku("unmet", "increments", "QV", "--note", "opening").stdout
    assert "2 idea(s) recorded as never met" in out
    lines = evidence(kioku)
    assert [l.split()[2:4] for l in lines] == [["p_aaaa", "triage"], ["p_bbbb", "triage"]]
    assert all(" triage unmet q_" in l for l in lines)
    out = kioku("context", "increments").stdout
    assert "· unmet n1 · last" in out and "2 asked · 2 unmet" in out
    kioku("upkeep", "--check")
    r = kioku("unmet", "increments", ok=False)  # it has an answer now: ask, don't triage
    assert r.returncode == 1 and "already has answers" in r.stderr
    assert "no idea `nope`" in kioku("unmet", "nope", ok=False).stderr


# -- adding, editing, removing

NEW = """## brownian-motion · definition · maths/probability/stochastic-calculus
a continuous process with independent Gaussian increments, starting at 0
- aliases: Wiener process

## ito-isometry · result · maths/probability/stochastic-calculus
$E[(\\int f dW)^2] = E \\int f^2 dt$ for adapted $f$ in $L^2$
- needs: brownian-motion
- uses: increments
"""


def area_text(kioku):
    return kioku.area.read_text()


def test_add_reads_ideas_from_stdin_and_keeps_the_format(kioku):
    out = kioku("add", stdin=NEW).stdout
    assert "brownian-motion → maths/probability/stochastic-calculus (now 5 ideas)" in out
    text = area_text(kioku)
    assert "## ito-isometry · result · i_" in text
    assert "- needs: brownian-motion\n- uses: increments" in text
    assert "$E[(\\int f dW)^2]" in text  # no shell ever saw the statement
    assert "needed by  ito-isometry" in kioku("context", "Wiener process").stdout
    kioku("upkeep", "--check")


def test_add_refuses_what_would_spoil_the_model(kioku):
    def refused(text, *flags):
        return kioku("add", *flags, stdin=text, ok=False).stderr

    assert "no area maths/topology" in refused("## open-set · definition · maths/topology\nx\n")
    kioku("add", "--new-area", stdin="## open-set · definition · maths/topology\nx\n")
    assert (kioku.home / "areas" / "maths" / "topology.md").exists()
    assert "edge to unknown idea `filtration`" in refused(
        "## adapted · definition · tools/python\nan adapted process\n- needs: filtration\n")
    assert "the name is taken by p_aaaa" in refused(
        "## increments · result · tools/python\nsomething else entirely\n")
    assert "close to quadratic-variation" in refused(
        "## quadratic-variations · result · tools/python\nthe QV of BM on [0,t] is t\n")
    kioku("add", "--anyway", stdin="## quadratic-variations · result · tools/python\n"
                                     "the QV of BM on [0,t] is t\n")
    assert "cycle" in refused("## a-x · result · tools/python\nx one\n- needs: b-x\n\n"
                              "## b-x · result · tools/python\nx two\n- needs: a-x\n")
    assert "not one of" in refused("## odd · lemma · tools/python\nx\n")
    kioku("upkeep", "--check")


def test_edit_renames_moves_and_rewrites_edges(kioku):
    kioku("edit", "increments", "--name", "independent-increments")
    text = area_text(kioku)
    assert "## independent-increments · result · p_aaaa" in text
    assert "- needs: independent-increments" in text and "- uses: independent-increments" in text
    kioku("edit", "QV", stdin="the quadratic variation of BM on [0,t] equals t\n")
    assert "the quadratic variation of BM on [0,t] equals t" in area_text(kioku)
    kioku("edit", "quadratic-variation-proof", "--uses", "-independent-increments")
    assert "- uses:" not in area_text(kioku)
    assert "cycle" in kioku("edit", "independent-increments", "--needs",
                             "+quadratic-variation-proof", ok=False).stderr
    kioku("edit", "independent-increments,quadratic-variation", "--area", "maths/bm",
           "--new-area")
    moved = (kioku.home / "areas" / "maths" / "bm.md").read_text()
    assert "p_aaaa" in moved and "p_bbbb" in moved and "p_aaaa" not in area_text(kioku)
    kioku("edit", "quadratic-variation-proof", "--area", "maths/bm")
    assert not kioku.area.exists()  # an emptied area's file goes
    kioku("upkeep", "--check")


def test_rm_respects_edges_and_archives_answers(kioku):
    qid, _ = ask(kioku)
    kioku("answer", qid, "2=")
    assert "needed or used by quadratic-variation-proof" in kioku(
        "rm", "QV", "--why", "x", ok=False).stderr
    kioku("rm", "quadratic-variation-proof", "--why", "rewritten")
    out = kioku("rm", "QV", "--why", "duplicate").stdout
    assert "1 answer(s) moved" in out
    assert len(evidence(kioku)) == 0
    archive = (kioku.home / "archive.md").read_text()
    assert "## 2026-11-02 · removed p_bbbb quadratic-variation · duplicate" in archive
    kioku("edit", "increments", "--needs", "+brownian", ok=False)
    kioku("upkeep", "--check")


# -- the graph page

def page_data(page):
    return json.loads(page.split("const DATA = ", 1)[1].split(";\n", 1)[0])


def test_graph_page_has_ideas_and_marked_edges(kioku, tmp_path):
    out = tmp_path / "g.html"
    kioku("graph", "quadratic-variation-proof", "--out", str(out), "--no-open")
    data = page_data(out.read_text())
    assert data["live"] is False
    assert {n["id"] for n in data["nodes"]} == {"p_aaaa", "p_bbbb", "c_cccc"}
    assert [n["id"] for n in data["nodes"] if n["focus"]] == ["c_cccc"]
    assert sorted((l["source"], l["target"], l["needs"], l["uses"]) for l in data["links"]) == [
        ("p_aaaa", "c_cccc", False, True), ("p_aaaa", "p_bbbb", True, False),
        ("p_bbbb", "c_cccc", True, False)]
    assert "ForceGraph" in out.read_text()


def test_graph_serves_a_page_built_afresh_on_every_request(kioku):
    import urllib.request
    env = {**os.environ, "KIOKU_HOME": str(kioku.home), "KIOKU_TODAY": "2026-11-02"}
    proc = subprocess.Popen([sys.executable, "-m", "kioku", "graph", "--no-open"],
                            stdout=subprocess.PIPE, text=True, env=env)
    try:
        url = proc.stdout.readline().split()[0]
        first = page_data(urllib.request.urlopen(url).read().decode())
        assert next(n for n in first["nodes"] if n["id"] == "p_aaaa")["n"] == 0
        qid, _ = ask(kioku)
        kioku("answer", qid, "1-")
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
        r = subprocess.run([sys.executable, "-m", "kioku.migrate", *map(str, args)],
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
    assert " p_aaaa observed right hint " in (home / "evidence.md").read_text()
    env = {**os.environ, "KIOKU_HOME": str(home), "KIOKU_TODAY": "2026-11-03"}
    r = subprocess.run([sys.executable, "-m", "kioku", "upkeep", "--check"],
                       capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stdout + r.stderr


# -- the teaching turn's commands

def test_ask_adds_the_ideas_written_above_the_block(kioku):
    block = ("## ito-isometry · result · maths/probability/stochastic-calculus\n"
             "E[(∫H dW)²] = E[∫H² dt]\n- needs: quadratic-variation\n\n"
             "# isometry\n1 say ito-isometry taught: state it\n  = the identity\n")
    out = kioku("ask", stdin=block).stdout
    assert "kioku: added ito-isometry (i_" in out and "stored as q_" in out
    assert "ito-isometry" in kioku.area.read_text()
    qid = next(t for t in out.split("`") if t.startswith("kioku answer q_")).split()[2]
    kioku("answer", qid, "1: the identity", "--say", "1=right")
    assert " say right use taught q_" in evidence(kioku)[0]
    kioku("upkeep", "--check")
    # a broken block adds nothing
    bad = block.replace("ito-isometry", "ito-two").replace("  = the identity\n", "")
    r = kioku("ask", stdin=bad, ok=False)
    assert "no idea added" in r.stderr and "ito-two" not in kioku.area.read_text()


def test_log_shows_the_blocks_asked_lately(kioku):
    qid, out = ask(kioku)
    right = "a" if "**a)** independent" in out else "b"
    kioku("answer", qid, f"1{right}9")
    kioku("unmet", "QV")
    out = kioku("log", "--since", "1h").stdout
    assert "2 block(s)" in out and qid in out
    assert "right 9 use" in line_of(out, "increments")
    assert "2 item(s) without a recorded answer" in out and "never met" in out
    assert "0 block(s)" in kioku("log", at="2026-11-09").stdout
    assert "want a span" in kioku("log", "--since", "soon", ok=False).stderr


def test_near_lists_the_ideas_around_one(kioku):
    out = kioku("context", "increments", "--near").stdout
    assert "near increments" in out and "2 idea(s)" in out
    assert "  1 edge     quadratic-variation " in out


def test_the_notebook_gets_a_note_and_its_indexes(kioku, tmp_path):
    assert "no notebook" in kioku("note", "QV", ok=False).stderr
    (kioku.home / "config.toml").write_text(f'notebook = "{tmp_path / "nb"}"\n')
    out = kioku("note", "QV").stdout
    note = tmp_path / "nb" / "notes" / "p_bbbb.md"
    assert str(note) in out and "new" in out
    text = note.read_text()
    assert 'aliases: ["quadratic-variation"]' in text and "the QV of BM on [0,t] is t" in text
    assert "Needs: [[p_aaaa|increments]]" in text
    index = tmp_path / "nb" / "notes" / "area--maths--probability--stochastic-calculus.md"
    assert "[[p_bbbb|quadratic-variation]] (result)" in index.read_text()
    assert "[[area--maths|maths]]" in (tmp_path / "nb" / "notes" / "index.md").read_text()
    note.write_text(text + "\n$[W]_t = t$\n")  # the agent's body survives a second call
    assert "new" not in kioku("note", "QV").stdout and "$[W]_t = t$" in note.read_text()
    assert f"note: {note}" in kioku("context", "QV").stdout
    assert "Notebook:" in kioku("profile", ok=False).stdout + kioku("init").stdout + kioku("profile").stdout


def test_the_words_of_before_are_still_read_and_upkeep_rewrites_old_lines(kioku):
    qid, _ = ask(kioku)
    kioku("answer", qid, "2. 3: because")
    kioku("answer", qid, "2~", "--say", "3=good")  # an agent that learned the old words
    kioku("observed", "increments=hard", "--step", "1")
    assert [l.split()[4] for l in evidence(kioku)] == ["partly", "right", "right"]
    assert " observed right hint " in evidence(kioku)[2]
    with (kioku.home / "evidence.md").open("a") as f:
        f.write("- 2026-11-01T10:00 p_aaaa pick hard 6 use q_old1/1 — picked x\n"
                "- 2026-11-01T10:05 p_bbbb pick again unseen q_old1/2 — never met it\n")
    assert "2 line(s) rewritten" in kioku("upkeep").stdout
    lines = evidence(kioku)
    assert " pick right 6 use q_old1/1 — picked x" in lines[3] and " pick unmet q_old1/2" in lines[4]
    assert "rewritten" not in kioku("upkeep").stdout
