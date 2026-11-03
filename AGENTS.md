# reader

Keep to the core loop: propositions and chains, evidence about them,
a memory model that turns evidence into recall probabilities, and agents that
decide from those numbers and the task whether to ask.

- Evidence is only an answer to a question that was asked: never conversation,
  teaching, self-report or vault notes.
- Output raw recall probabilities, not labels or verdicts; the agent judges
  what the task needs.
- An answer updates only the id it is about. Propagation through chains, review
  scheduling and better memory models are later, swappable work.
- States stay few and simple, and every answer is written the moment it is
  graded.

`PHILOSOPHY.md` gives the reason for each rule. A change that bends a principle
updates it there first and adds a dated line to its decision log.

Nothing in the code or the skills is about one reader: who they are lives in
their `profile.md`, and their setup in `config.toml`, both in the model folder.

The README's module table says what each module owns; keep it true. The memory
model is the seam for later work: only `memory.recall` knows how R is computed.

The CLI and the skills in `skills/` (`reader-brief`, and `learn`, which runs
lessons on the loop) change together: a command change updates every skill
that uses it in the same commit. Run `uv run pytest` before committing.
