# kioku

**kioku** (記憶, memory) is a memory model of the person an agent works with:
the **learner**. It records what they have shown they know, as the probability
they recall each idea now, so that any agent (writing, teaching, or
pair-programming with them) can pitch its work one step from what they hold,
ask a short question when it cannot tell, and never re-teach what they have.

It is for anyone who works with coding or writing agents and wants them to know
where they stand. The tool and its skills are general; who you are lives in a
profile in your own model folder. Why it works the way it does is in
[PHILOSOPHY.md](PHILOSOPHY.md), and the words it uses in
[GLOSSARY.md](GLOSSARY.md).

## Install

    uv tool install git+https://github.com/MarkKon/kioku
    kioku init                          # creates ~/.local/share/kioku
    $EDITOR ~/.local/share/kioku/profile.md
    kioku skills --to ~/.claude/skills  # or wherever your agent reads skills

To try it without installing: `uvx --from git+https://github.com/MarkKon/kioku
kioku -h`.

The profile is free text the agents read once per session: your background,
how you like to answer (typing, paper, voice), your notation, where your notes
are, how long your sessions usually are. Nothing about you goes anywhere else.

## The skills

`kioku skills` links three skills into your agent's skills folder:

- **kioku**, loaded by almost every session: the check (look up, decide, ask,
  pitch), the question block, and recording. Short on purpose; the formats are
  in `kioku ask -h`, `kioku add -h` and `kioku observed -h`.
- **learn** teaches a goal in one session, one step per turn: each turn gives
  feedback on your last reply, takes one new idea, and asks.
- **pair** pair-programs: you type, the agent navigates. Each step is one
  turn; library calls come as materials and shrink to a bare name as you hold
  them, and you learn the idea a step implements by building it.

Skills made for one person (your essay or paper workflow, your notes) belong
in your own skills folder; they load the kioku skill and follow its check.

## The loop

1. **Look up.** `kioku context girsanov` shows an idea, what it needs and
   uses, and what needs and uses it, each with R, the probability the learner
   recalls it now; `kioku context stochastic-calculus` lists an area with its
   coverage, and a miss says where it looked.
2. **Ask.** When R and the task leave it unsettled, the agent asks a short
   question block (`kioku ask`): multiple choice with a confidence digit, a
   formula written by hand, or one free line.
3. **Record.** The learner's one-line reply goes to `kioku answer`, which
   records at once what happened: right, partly, wrong or never met, with
   their confidence.

Ideas are added with `kioku add` (blocks on stdin), changed or moved with
`kioku edit`, and removed with `kioku rm`, which moves any answers to
`archive.md` rather than dropping them. An answer that should not count is set
aside the same way with `kioku answer --retract`. A step of pairing work that
a test verified is recorded with `kioku observed`, and the names the learner
marks as never met in a triage with `kioku unmet`. `kioku log` lists what was
asked and answered in the last hours, and `kioku context <idea> --near` the
ideas around one, lowest R first.

Evidence comes only from questions asked and answered and from verified work,
never from conversation or self-report. A memory model (FSRS-6 for now, on
elapsed time to the minute) turns each idea's answers into R: it reads a
pick's confidence against your own record at that digit, and takes a right
answer to a probe (a question asked to find out what you already hold) as
knowledge you had before, lasting longer the surer it was. The model is
plain files in a git repo: one markdown file per area, holding its ideas
(name, kind, statement, and edges marked needs or uses), and one line per
answer.

## See it

`kioku graph` serves the whole model on localhost and opens it in the browser
as a force-directed graph; `kioku graph girsanov` shows just that
neighbourhood, and `kioku graph maths/analysis` an area. The ↻ button (or `r`)
rebuilds the page from the model, keeping the layout, so answers recorded
meanwhile show up. `--out page.html` writes a static page instead.

Nodes are coloured by R (grey: never asked) and never overlap. An edge is solid
when it needs and dashed when it only uses, and its arrow points to the idea
that rests on it, which sits below. The areas read like a map: each top
area is one blob, split into a face for each subarea (and those into theirs,
with dashed borders), its ideas kept inside it. Areas never overlap, and where
two meet a straight border runs between them. Hovering lights an idea's edges, with particles
flowing toward what rests on it; clicking a node shows its statement and every
answer. Search matches names, statements and aliases; `area:maths/analysis`
lights an area.

The settings menu (the sliders icon) sets node size, labels, spacing, shading,
arrows, the theme and the key, and the page remembers them. The stats view
(the bars icon, or `s`) shows the model in numbers: coverage, mean R, R across
ideas, answers over time, each area and kind, and the ideas with the lowest R.
Click an area or an idea there to see it in the graph.

## Configure

Settings come from the environment, or from `config.toml` in the model folder:

| env                 | config.toml   | what                                          |
| ------------------- | ------------- | --------------------------------------------- |
| `KIOKU_HOME`        |               | the model folder (default `~/.local/share/kioku`) |
| `KIOKU_VAULT`       | `vault`       | a folder of your markdown notes, shown as hints |
| `KIOKU_NOTEBOOK`    | `notebook`    | a folder the agent writes notes into, for you to look things up in |
| `KIOKU_SCOUT_MODEL` | `scout_model` | a [pi](https://github.com/badlogic/pi-mono) model that drafts ideas from notes |

The notes folder, the notebook and the scout are optional. The notebook holds
one note per idea the agent has taught you (`kioku note <idea>`), with an
index note per area; it uses the same format as a notes folder, so the same
editor reads both, and you may keep it open while you answer. Run `kioku upkeep` daily to
check and back up the model (it commits to the model folder's git repo, and
pushes when it has a remote) and to list duplicates and areas worth splitting.

## Code

| module         | what it owns                                              |
| -------------- | --------------------------------------------------------- |
| `records.py`   | the records: ideas (with their edges) and answers         |
| `store.py`     | the model folder, its area files and its line formats     |
| `memory.py`    | the memory model: answers → R (swap this for a better one) |
| `model.py`     | the model in memory: names, edges, areas and coverage, search, recall per idea |
| `questions.py` | question blocks: parse, render, read replies              |
| `vault.py`     | the optional notes folder, read only                      |
| `notebook.py`  | the optional notebook: note skeletons and area indexes    |
| `upkeep.py`    | checks, duplicates, areas to split, calibration, backup, drafting |
| `view.py`      | the graph page (`kioku graph`) and its local server; template and vendored [force-graph](https://github.com/vasturiano/force-graph) (MIT) in `assets/` |
| `cli.py`       | arguments and printing                                    |

The skills are in `skills/`, shipped inside the package so `kioku skills` can link them.

## Test

    uv run pytest
