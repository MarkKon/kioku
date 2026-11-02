# reader

A learner model for one reader, Konstantin, used by coding and writing agents
to pitch explanations at their level.

The loop: an agent looks an idea up (`reader check`), asks what the lookup
does not settle (`reader ask`), and passes the reply on (`reader answer`,
`reader grade`), which records it at once. Evidence comes only from questions
asked and answered. A memory model (FSRS-6 for now) turns each id's answers
into R, the probability they recall it today.

- `src/reader/cli.py`: the CLI. `reader -h` lists the commands.
- `skills/reader-brief/`: the agent skill. Linked into `~/.agents/skills` by
  the dotfiles.
- The model itself lives in `$READER_HOME` (default `~/.local/share/reader`), a
  separate private git repo.

## Install

    uv tool install -e .

## Test

    uv run pytest
