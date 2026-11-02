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

The CLI and `skills/reader-brief/SKILL.md` change together: a command change
updates the skill in the same commit. Run `uv run pytest` before committing.
