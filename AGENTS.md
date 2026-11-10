# kioku

kioku is for anyone: a memory model of the person an agent works with (the
learner), and the general skills that use it. Keep it that way.

- **Nothing in the code or in `skills/` names a person, a path or a personal
  tool.** Who the learner is lives in their `profile.md`, their setup in
  `config.toml`, both in the model folder. A skill made for one person lives
  outside this repo and calls the general ones.
- **Keep to the core loop:** ideas and the edges between them (marked needs
  and uses), evidence about them, a memory model that turns evidence into
  recall probabilities, and agents that decide from those numbers and the task
  whether to ask.
- Evidence is only an answer to a question that was asked, or verified
  pairing work: never conversation, teaching, self-report or notes.
- Output raw recall probabilities, not labels or verdicts, and keep the skills
  that way too: they decide from R and answers, they do not sort ideas into
  states laid over the model.
- An answer updates only the idea it is about. Propagation along edges, review
  scheduling and better memory models are later, swappable work.
- States stay few and simple, and every answer is written the moment it is
  given.
- An answer records what happened (the outcome, the confidence, the help it
  took), never a grade. What it is worth is the memory model's business.
- The notebook is reference the agent writes for the learner to look things up
  in. It is never evidence, and the model does not read it.

`PHILOSOPHY.md` gives the reason for each rule, and `GLOSSARY.md` the words.
A change that bends a principle updates it there first and adds a dated line
to its decision log.

The README's module table says what each module owns; keep it true. The memory
model is the seam for later work: only `memory.recall` knows how R is computed.

The CLI and the skills in `skills/` (`kioku`, always loaded; `learn`, which
runs lessons; `pair`, which pair-programs) change together: a command change
updates every skill that uses it in the same commit. Formats live in the CLI's
help (`kioku ask -h`, `add -h`, `observed -h`, `unmet -h`, `note -h`); skills
point there rather than repeat them. How a turn teaches is written once, in
`skills/kioku/turn.md`; `learn` and `pair` point there too. Run `uv run
pytest` before committing.
