# reader

A learner model for agents. It records what a reader has shown they know, so
that coding and writing agents can pitch every explanation at their level:
one step from what they hold, never re-teaching what they have.

Why it works the way it does, and what it draws on, is in
[PHILOSOPHY.md](PHILOSOPHY.md).

## The loop

1. **Look up.** `reader context girsanov` shows an idea, what it needs and
   uses, and what needs and uses it, each with R, the probability the reader
   recalls it now; `reader context stochastic-calculus` lists an area with its
   coverage, and a miss says where it looked.
2. **Ask.** When R and the task leave it unsettled, the agent asks a short
   question block (`reader ask`): multiple choice with a confidence digit, a
   formula written by hand, or one free line.
3. **Record.** The reader's one-line reply goes to `reader answer`, which
   grades it and records the evidence at once.

Ideas are added with `reader add` (blocks on stdin), changed or moved with
`reader edit`, and removed with `reader rm`, which moves any answers to
`archive.md` rather than dropping them. An answer that should not count is set
aside the same way with `reader answer --retract`. A step of pairing work that
a test verified is recorded with `reader observed`.

Evidence comes only from questions asked and answered and from verified work,
never from conversation or self-report. A memory model (FSRS-6 for now, on
elapsed time to the minute) turns each idea's answers into R. The model is
plain files: one markdown file per area, holding its ideas (name, kind,
statement, and edges marked needs or uses), and one line per answer. The words
are defined in [GLOSSARY.md](GLOSSARY.md).

## See it

`reader graph` serves the whole model on localhost and opens it in the browser
as a force-directed graph; `reader graph girsanov` shows just that
neighbourhood, and `reader graph maths/analysis` an area. The ↻ button (or `r`) rebuilds the page from the model, keeping
the layout, so answers recorded meanwhile show up. `--out page.html` writes a
static page instead. Nodes are coloured by
R (grey: never asked), an edge is solid when it needs and dashed when it only
uses, its arrow points to the idea that rests on it (which sits below), each
area is a shaded region with its subareas shaded inside it (the `areas` box
turns this off), hovering lights an idea's edges with particles flowing toward
what rests on it, and clicking a node shows its statement and every answer. It follows the system's
light or dark mode, with a toggle.

## Install

    uv tool install git+https://github.com/MarkKon/reader
    reader init                      # creates ~/.local/share/reader
    $EDITOR ~/.local/share/reader/profile.md

Then link the skills into your agent's skills folder (for example
`~/.claude/skills/`): `skills/reader-brief` teaches agents the loop and the
question format, and `skills/learn` runs a lesson on it, sweeping the route
to a goal and checking each step before the next rests on it.

## Configure

Settings come from the environment, or from `config.toml` in the model folder:

| env                  | config.toml   | what                                          |
| -------------------- | ------------- | --------------------------------------------- |
| `READER_HOME`        |               | the model folder (default `~/.local/share/reader`) |
| `READER_VAULT`       | `vault`       | a folder of the reader's markdown notes, shown as hints |
| `READER_SCOUT_MODEL` | `scout_model` | a [pi](https://github.com/badlogic/pi-mono) model that drafts ideas from notes |

Both the vault and the scout are optional. Run `reader upkeep` daily to check
and back up the model (it commits to the model folder's git repo, and pushes
when it has a remote) and to list duplicates and areas worth splitting.

## Code

| module         | what it owns                                              |
| -------------- | --------------------------------------------------------- |
| `records.py`   | the records: ideas (with their edges) and answers         |
| `store.py`     | the model folder, its area files and its line formats     |
| `memory.py`    | the memory model: answers → R (swap this for a better one) |
| `model.py`     | the model in memory: names, edges, areas and coverage, search, recall per idea |
| `questions.py` | question blocks: parse, render, grade replies             |
| `vault.py`     | the optional notes folder, read only                      |
| `upkeep.py`    | checks, duplicates, areas to split, calibration, backup, drafting |
| `view.py`      | the graph page (`reader graph`) and its local server; template and vendored [force-graph](https://github.com/vasturiano/force-graph) (MIT) in `assets/` |
| `cli.py`       | arguments and printing                                    |
| `migrate.py`   | one-off: a v0 folder (propositions, chains) → v1 (areas)  |

## Test

    uv run pytest
