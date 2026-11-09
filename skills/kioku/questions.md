# Questions

The format of a block, its replies and an example are in `kioku ask -h`. This
file is how to write items that measure the learner, and how answers are
graded and corrected.

## Items

There are three kinds:

- **pick**: multiple choice, answered with a letter and a confidence digit.
  The default: the quickest to answer.
- **write**: they write it on paper or a tablet and compare it with the
  reference you then show. For formulas and short derivations they want in
  their hands.
- **say**: one free line, typed or dictated, for a why or a prediction a pick
  cannot hold.

`kioku profile` says which kinds suit them.

- Tag each item with the idea it tests, by name, and with the depth it
  demands when that is not `use`: `state` to recall it, `transfer` to reach
  for it where nothing points to it. Ask why a result holds through its proof
  idea.
- Each item stands alone: every term in it is defined in the item or was
  defined earlier in the conversation, in their notation, unless recalling
  that definition is what the item tests.
- Options are bare claims of the same length and register. Write the right one
  first, then turn it into each wrong one: the answer someone holding a
  specific wrong model would give, named after `::`. Every wrong option is
  false outright, never a weaker form of the right one (if the right one says
  $=$, $\le$ is not a wrong option).
- Solve the item yourself, from the definitions as stated, before asking.
- Prefer an item that applies an idea to one that recites it.
- An item asked before its idea is taught is tagged `pre`: its answer is kept
  as data and does not count as evidence.

## Grades

again (wrong or blank), hard (right with effort or a slip), good (right and
clean), easy (right and carried to a new setting). A right pick at chance
confidence is a guess: recorded, with no grade. A confident wrong pick is a
**misconception**, the strongest signal there is: repair it before anything
rests on it.

Grade say items against their reference, in the same call or a later one:
`kioku answer <q_id> --say 3=good`, with `--mis "believed X → Y"` for a
misconception.

The parser reads input from agents: a reply outside the format ("between a
and b", a letter without a digit, two letters) is yours to settle first. Ask
what they meant, or put the reading you would record to them in the format,
and pass that on.

## Answers that should not count

An answer is set aside, never edited:

- they misread the question, misclicked, or the item itself was wrong:
  `kioku answer <q_id> --retract 2 --why "<reason>"` moves it to `archive.md`
  and opens the item again;
- to answer a finished item again: `--redo`;
- to change a grade: `--regrade 2=hard`.

The old answer is archived either way.
