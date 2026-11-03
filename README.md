# reader

A learner model for agents. It records what a reader has shown they know, so
that coding and writing agents can pitch every explanation at their level:
one step from what they hold, never re-teaching what they have.

Why it works the way it does, and what it draws on, is in
[PHILOSOPHY.md](PHILOSOPHY.md).

## The loop

1. **Look up.** `reader check girsanov, #sde` shows the matching ideas, what
   they rest on, and what rests on them, each with R, the probability the
   reader recalls it today.
2. **Ask.** When R and the task leave it unsettled, the agent asks a short
   question block (`reader ask`): multiple choice with a confidence digit, a
   formula written by hand, or one free line.
3. **Record.** The reader's one-line reply goes to `reader answer`, which
   grades it and records the evidence at once.

Ideas are added with `reader new`, fixed with `reader amend`, and removed with
`reader delete`, which moves any answers to `archive.md` rather than dropping
them. An answer that should not count is set aside the same way with
`reader retract`.

Evidence comes only from questions asked and answered, never from
conversation or self-report. A memory model (FSRS-6 for now, on elapsed time
to the minute) turns each idea's answers into R. The model is plain files: propositions (checkable claims),
chains (premises that give a conclusion by a step), and one line per answer.

## See it

`reader graph` serves the whole model on localhost and opens it in the browser
as a force-directed graph; `reader graph girsanov` shows just that
neighbourhood. The ↻ button (or `r`) rebuilds the page from the model, keeping
the layout, so answers recorded meanwhile show up. `--out page.html` writes a
static page instead. Nodes are coloured by
R (grey: never asked), a chain is a fork from its premises to its conclusion,
implications flow down the page (premises above what rests on them), and
clicking a node shows its statement and every answer. It follows the system's
light or dark mode, with a toggle.

## Install

    uv tool install git+https://github.com/MarkKon/reader
    reader init                      # creates ~/.local/share/reader
    $EDITOR ~/.local/share/reader/profile.md

Then link `skills/reader-brief` into your agent's skills folder (for example
`~/.claude/skills/reader-brief`), so agents know the loop and the question
format.

## Configure

Settings come from the environment, or from `config.toml` in the model folder:

| env                  | config.toml   | what                                          |
| -------------------- | ------------- | --------------------------------------------- |
| `READER_HOME`        |               | the model folder (default `~/.local/share/reader`) |
| `READER_VAULT`       | `vault`       | a folder of the reader's markdown notes, shown as hints |
| `READER_SCOUT_MODEL` | `scout_model` | a [pi](https://github.com/badlogic/pi-mono) model that drafts propositions from notes |

Both the vault and the scout are optional. Run `reader upkeep` daily to lint
and back up the model (it commits to the model folder's git repo, and pushes
when it has a remote).

## Code

| module         | what it owns                                              |
| -------------- | --------------------------------------------------------- |
| `records.py`   | the records: propositions, chains, answers                |
| `store.py`     | the model folder and its line formats                     |
| `memory.py`    | the memory model: answers → R (swap this for a better one) |
| `model.py`     | the graph in memory: lookups, search, recall per id       |
| `questions.py` | question blocks: parse, render, grade replies             |
| `vault.py`     | the optional notes folder, read only                      |
| `upkeep.py`    | lint, duplicates, calibration, backup, drafting           |
| `view.py`      | the graph page (`reader graph`) and its local server; template and vendored [force-graph](https://github.com/vasturiano/force-graph) (MIT) in `assets/` |
| `cli.py`       | arguments and printing                                    |

## Test

    uv run pytest
