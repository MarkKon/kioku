---
name: kioku
description:
  "What the learner (the person you work with) has shown they know, as recall
  probabilities, and how to ask them. Use before an explanation, lesson,
  document or step of shared work leans on an idea they may not hold."
---

# kioku

kioku is a memory model of the learner: what they have shown they know, as
numbers. Read `kioku profile` once per session: who they are, how they answer,
how they like to work.

Pitch at the **goldilocks** level: each new idea one reasoning step from
something they hold; what they hold gets a sentence and a link, never a
re-derivation.

## The model

- An **idea** is one named thing they could hold or lack on its own: a
  kebab-case name, a kind (definition, result, proof, method) and one home
  **area** in a tree (`maths/analysis`, `tools/pytorch`).
- **Edges**: X **needs** Y when they cannot follow X's statement without Y;
  X **uses** Y when doing X carries Y out.
- **Evidence** is an answer to a question asked here, or a pairing step they
  typed and a test verified. Nothing else moves a number: what they said in
  passing, what you taught, what they say they know, what their notes say.
- **R** is the probability they recall an idea now, from that idea's own
  evidence. No answers means no R: unknown, not absent. A wrong last answer
  holds R at 0 until a right one.
- Each answer records the **depth** its item demanded: state, use (the
  default) or transfer.

Read and write the model only through `kioku` (`kioku -h`).

## The check

Run it whenever what you are about to say or do leans on an idea they may not
hold.

1. **Look up**: `kioku context <terms>`, comma-separated: idea names, areas or
   plain text. An idea shows its statement, R, last answer, deepest depth
   shown, and its neighbours with their R. An area lists its ideas with R and
   its sub-areas with coverage; no argument shows the whole tree. A miss lists
   the ideas that mention the term, or the nearest names and how well that
   region is covered.
2. **Decide** from R and how much the step leans on the idea. What the
   argument runs through needs a high, recent R; a side remark needs none. A
   misconception (`!`) is repaired before anything rests on it. The R of what
   an idea needs says whether they could rebuild it. A tool idea is cheap to
   name in passing; a concept is not.
3. **Ask** what the lookup leaves unsettled, as one question block. An idea
   with no entry is added first.
4. **Pitch** the next step at what they showed.

A **brief** is the check run over everything a piece rests on (a lesson, a
document, a pairing session): look up its area and key ideas, ask the
unsettled ones in blocks, hardest first, and show the learner the list: each
idea's name, R, and how the piece treats it (used with a link, recalled in a
sentence, or taught). Their correction holds for the piece; it reaches the
model only through a question they answer.

## Asking

A **question block** is up to six numbered items, answered in one line. Write
it, pipe it into `kioku ask` (format and example: `kioku ask -h`), and copy the
block it prints between the lines into your reply, verbatim: they never see
tool output, and the block you wrote holds the answer key. Pass their
reply on as typed: `kioku answer <q_id> "<reply>"`, and grade say items with
`--say N=good|hard|again`. Answer every ✗ in prose: the right answer and, for
a misconception, why the wrong one tempts.

An item measures the learner only when it stands alone (every term defined in
it or earlier in the conversation, in their notation), you solved it yourself
first, and each wrong option is the answer a specific wrong model would give.
Prefer applying an idea to reciting it. [questions.md](questions.md) has the
full rules, the grades, and how to set aside an answer that should not count;
read it before your first block in a session.

## Observed work

In pairing, after a step's tests pass, record the ideas it exercised in one
call, graded by the help it took: `kioku observed name=good|hard|again …
--step "…"` (`kioku observed -h`). Report it in one line.

## Adding ideas

Look up before adding, and reuse what exists. Add an idea when the task leans
on one that has no entry, not in advance: `kioku add` (format: `kioku add
-h`). Before adding, editing or removing, read [ideas.md](ideas.md): what one
idea is, which edges to write, and where it lives.

Daily checks and backup: [upkeep.md](upkeep.md).
