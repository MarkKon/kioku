---
name: reader-brief
description:
  "What Konstantin has shown they know, as recall probabilities, and the one
  way to ask them. Use whenever an explanation, lesson, essay, paper or step of
  shared work leans on an idea they may not hold: look it up, and ask what the
  lookup does not settle, before pitching it at their level."
---

# Reader brief

The reader is Konstantin: maths PhD student, MSc in Technical Mathematics.
Pitch everything at the **goldilocks** level: each new idea sits one reasoning
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
  the labvault move no number.
- A **memory model** turns each id's answers into **R**, the probability they
  recall it today (FSRS-6 for now). An answer updates only the id it is about.
  A wrong last answer holds R at 0 until a right one. No answers means no R:
  unknown, not zero.

The model lives in `~/.local/share/reader/`. Read and write it only through
`reader` (`reader -h` lists the commands).

## The check

Use this whenever something you are about to say or do leans on an idea they
may not hold. It is also how every brief is built.

1. **Look up**: `reader check <ids or terms>` (comma-separated; `#topic`
   matches a topic). For each matching proposition or chain it shows what the
   idea rests on (chains and premises, two levels) and what rests on it. Each
   line has R, the number of answers, the last answer's date and grade, and the
   statement or step. A misconception or "never met it" shown in the last answer
   is flagged. Vault notes on the terms that have no proposition yet are listed
   as hints.
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

Most of their MSc mathematics has no evidence yet: that calls for a question,
not an assumption that they lack it.

## A brief

A brief is the check run on everything a piece rests on: an aissay, paiper,
lesson or pair session.

1. `reader check <topic>, <synonym>, <key result>`. For each vault note it
   lists that the piece leans on, read the note, add its propositions, and check
   again.
2. List the ideas the piece needs. Ask about every one the lookup does not
   settle in one question block, hardest first: a confident right answer there
   spares its prerequisites.
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
  (`2b8`: option b, 80% sure). The default, since they usually type little.
- **write**: they write it on their tablet and compare it with the reference
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

- Tag each item with what it tests: a proposition id to recall it, a chain id
  to derive or apply it.
- Options are bare claims of the same length and register. Write the right one
  first, then turn it into each wrong one: the answer someone holding a
  specific wrong model would give.
- Prefer an item that applies an idea to one that recites it.
- At most six items, hardest first; in a lesson, one item per turn.

Pass their reply on as typed: `reader answer <q_id> "<reply>"`. It grades picks
and writes, prints a verdict per item, and records each answer at once. Grade
each say item against its reference with
`reader grade <q_id> <n> good|hard|again`, adding
`--mis "believed X → Y"` for a misconception. Then answer every ✗ in prose: the
right answer and, for a misconception, why the wrong one tempts.

Grades: again (wrong or blank), hard (right with effort or a slip), good (right
and clean), easy (right and carried to a new setting). A right pick at chance
confidence is a guess, which is recorded but carries no grade.

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

## Upkeep

A daily T3 task runs `reader upkeep --scout`. It lints the model, commits it to
its git repo, lists likely duplicates, and has a cheap model draft propositions
for newly developed vault notes into `proposals.md`. When they approve drafts,
check each against its note, add it with `reader new`, and end its `##` header
with `· added` or `· skipped`.
