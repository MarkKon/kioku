---
name: reader-brief
description:
  "What the reader (the person you work with) has shown they know, as recall
  probabilities, and the one way to ask them. Use whenever an explanation, lesson, essay, paper or step of
  shared work leans on an idea they may not hold: look it up, and ask what the
  lookup does not settle, before pitching it at their level."
---

# Reader brief

The reader is the person you are working with. `reader profile` says who they
are and how they like to answer; read it once per session. Pitch everything at the **goldilocks** level: each new idea sits one reasoning
step from something they hold, and what they hold gets a sentence and a link,
not a re-derivation. Learn what they hold by looking it up, and ask when the
lookup does not settle it.

## The model

- A **proposition** is one checkable claim (a definition, theorem, formula or
  fact) with its assumptions inside it.
- A **chain** says that some propositions together give another, by a named
  **step**.
- **Evidence** is an answer they gave to a question you asked, about one
  proposition or one chain. Nothing else counts: what they showed in
  conversation, what you taught, what they say they know and what they wrote in
  their notes move no number.
- A **memory model** turns each id's answers into **R**, the probability they
  recall it now (FSRS-6 on elapsed time, so R falls within a day too). An
  answer updates only the id it is about: nothing propagates through chains.
  A wrong last answer holds R at 0 until a right one. No answers means no R:
  unknown, not zero.

The model lives in `$READER_HOME` (default `~/.local/share/reader/`). Read and
write it only through `reader` (`reader -h` lists the commands).

## The check

Use this whenever something you are about to say or do leans on an idea they
may not hold. It is also how every brief is built.

1. **Look up**: `reader check <ids or terms>` (comma-separated; `#topic`
   matches a topic). For each matching proposition or chain it shows what the
   idea rests on (chains and premises, two levels) and what rests on it. Each
   line has R, the number of answers, the last answer's time (date if not
   today) and grade, and the
   statement or step. A misconception or "never met it" shown in the last answer
   is flagged. When a vault (a folder of their notes) is configured, notes on
   the terms that have no proposition yet are listed as hints.
2. **Decide** from R and the task. How sure you need to be depends on how much
   the next step leans on the idea: a premise the argument runs through needs a
   high, recent R, and a side remark needs none. The premises' R tells you
   whether they could rebuild an idea they have forgotten. A misconception in
   the last answer is repaired before anything rests on it. A question costs
   them a moment; a pitch at the wrong level costs the conversation.
3. **Ask** what the lookup does not settle, as one question block (below). An
   idea with no proposition yet: add it (see Propositions), then ask.
4. **Pitch** the next step at what they showed. Their answer is already
   recorded.

Most of what they know has no evidence yet: that calls for a question,
not an assumption that they lack it.

## A brief

A brief is the check run on everything a piece rests on: an aissay, paiper,
lesson or pair session.

1. `reader check <topic>, <synonym>, <key result>`. For each vault note it
   lists that the piece leans on, read the note, add its propositions, and check
   again.
2. List the ideas the piece needs. Ask about every one the lookup does not
   settle, in blocks, hardest first. A confident right answer at the top tells
   you where they stand, but it records nothing about the ideas below it: an
   idea the piece leans on gets its own answer.
3. Show them the brief. For each idea give its id, R (or none), last date, and
   how the piece treats it: used with a link, recalled in a sentence, or taught.
   Then list their answers. Their correction is final for this piece and goes
   into its `BRIEF.md`. It enters the model only through a question they answer.

When the main idea needs more than one new prerequisite in a chain, say so and
propose a smaller target or a piece about the chain itself.

## Questions

Every question put to them is a **question block**: numbered items, answered
in one line. A check, a brief, and a lesson's probe, prediction and check all
use it. There are three kinds of item:

- **pick**: multiple choice, answered with a letter and a confidence digit
  (`2b8`: option b, 80% sure). The default: the quickest to answer.
- **write**: they write it on paper or a tablet and compare it with the reference
  you then show (`3.` when done, then `3=`, `3~` or `3x`). For formulas and
  short derivations they want in their hands.
- **say**: one free line, typed or dictated, for a why or a prediction a pick
  cannot hold.

Write the block and pipe it into `reader ask`. It stores the block with its key
under a new id (`q_…`), shuffles the options, and prints the block; show them
that output as it is.

```
# girsanov
1 pick p_1ymv: Under $Q$ with $dQ/dP = \exp(\theta W_T - \tfrac12\theta^2 T)$, the process $W_t - \theta t$ is
  * a $Q$-Brownian motion
  - a $Q$-martingale but not a Brownian motion :: thinks Girsanov keeps only the martingale property
  - a $P$-Brownian motion
  ? Under $Q$ the shifted process is a Brownian motion: drift removed, quadratic variation kept.
2 write p_k2x9: Itô's formula for $f(t, X_t)$, $X$ an Itô process.
  = $df = \partial_t f\,dt + \partial_x f\,dX_t + \tfrac12 \partial_{xx} f\,d\langle X \rangle_t$
3 say c_8q1m: In one line, where does the drift $-\theta$ come from?
  = Itô on $Z_t = \exp(\theta W_t - \tfrac12\theta^2 t)$ gives $dZ = \theta Z\,dW$; under $Q$ that shifts $W$ by $\theta\,dt$.
```

`*` marks the right option and `-` the others. `::` names the misconception a
confident pick of that option reveals. `?` is the explanation and `=` the
reference.

- Tag each item with what it tests: a proposition id to state or apply the
  idea, a chain id to derive it.
- Each item stands alone: every term in it is defined in the item or was
  defined earlier in the conversation, in the reader's notation, unless
  recalling that definition is what the item tests.
- Options are bare claims of the same length and register. Write the right one
  first, then turn it into each wrong one: the answer someone holding a
  specific wrong model would give. Every wrong option is false outright, never
  a weaker form of the right one (if the right one says $=$, $\le$ is not a
  wrong option).
- Solve the item yourself, from the definitions as stated, before asking.
- Prefer an item that applies an idea to one that recites it.
- At most six items per block. A lesson's prediction is one item, its check
  two to four.

Pass a reply in the format on as typed: `reader answer <q_id> "<reply>"`. It
grades picks and writes, prints a verdict per item, and records each answer at
once. The parser reads input from agents: a reply outside the format ("between
a and b", a letter without a digit, two letters) is yours to settle first. Ask
what they meant, or put the reading you would record to them in the format,
and pass that on. Grade
each say item against its reference with
`reader grade <q_id> <n> good|hard|again`, adding
`--mis "believed X → Y"` for a misconception. Then answer every ✗ in prose: the
right answer and, for a misconception, why the wrong one tempts.

Grades: again (wrong or blank), hard (right with effort or a slip), good (right
and clean), easy (right and carried to a new setting). A right pick at chance
confidence is a guess, which is recorded but carries no grade.

An answer that does not count (they misread the question, misclicked, or the
item itself was wrong) is set aside, not edited:
`reader retract <q_id> <n> --why "<reason>"` moves it to `archive.md` and opens
the item again, so a corrected reply goes through `reader answer`. To answer a
finished item again, `reader answer --redo`; the old answer is archived too.

## Propositions

Search before adding: `reader find <terms>`, and reuse what exists.

```
reader new prop <kebab-name> "<statement>" --topics <t1>,<t2> [--vault <id>] [--aliases "x, y"]
reader new chain <premise> <premise> => <conclusion> --step "<the reasoning step>"
```

Both print the new id. A statement is one claim, maths in `$…$`, every
assumption inside, readable alone. A chain's premises jointly give its
conclusion; ids or names both work. Topics are kebab-case subjects, reused from
`reader status`. `reader show <id>` lists every answer for an id with the
question it answered.

Fix a mistake rather than living with it:

```
reader amend <id> [--name …] [--statement …] [--topics a,b] [--aliases …] [--vault …]
reader amend <c_id> [--chain "p_a p_b => p_c"] [--step "…"]
reader delete <id> [--why "…"]
```

`amend` keeps the id and its answers, so it is for wording, not for a
different claim: changing the statement, premises or step of an id that has
answers needs `--force`. A different claim is a new id; delete the old one.
`delete` refuses while a chain rests on the id (delete or amend that chain
first), and refuses an id with answers unless `--force`, which moves the
answers to `archive.md` rather than dropping them.

## Upkeep

Run `reader upkeep` daily, e.g. as a scheduled task. It lints the model,
commits it to its git repo (and pushes, when it has a remote), and lists likely
duplicates. With a vault, it lists finished notes that have no proposition yet;
with `--scout` and a configured scout model, a cheap model drafts propositions
for them into `proposals.md`. When they approve drafts,
check each against its note, add it with `reader new`, and end its `##` header
with `· added` or `· skipped`.
