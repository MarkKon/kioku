---
name: learn
description:
  "Teach the learner (the person you work with) something in this session, one
  checked step at a time, from what they hold to a goal. Use when they ask to
  learn, understand, revise or be taught something here and now."
---

# Learn

A lesson moves the learner from what they hold to a **goal**, one **step** per
turn. The goal is reached when it feels obviously true to them: it follows
from what they hold rather than sitting beside it as a fact.

Load the kioku skill first: the model, the check and the question block. Then
read [the teaching turn](../kioku/turn.md): every turn of a lesson is one, and
it says how a turn teaches, asks and adapts. Read `kioku profile` for their
notation, how they answer and how long they usually have.

What they hold is what their answers show. A result in their notes or a paper
they wrote is a place to read the statement from; it is held once a question
shows it. Speak of it in numbers ("R .6, one answer"), never as "you know
this". **State and derive are two ideas**: a result's answers say whether they
can state and use it, its proof idea whether they can derive it.

## How a lesson is written

- Everything they should see is in your reply: lesson text, proofs, blocks.
- Every proof is whole: from what they hold and what earlier steps taught. A
  theorem the lesson does not prove is a **dependency**: stated exactly, said
  to be unproved here, with a reference when one exists.
- One change at a time, said out loud: a changed theorem, plan or notation is
  announced with what changed and why.
- What you teach is the idea's statement in the model. When the lesson needs a
  different one (more general, other hypotheses), reword the idea with `kioku
  edit` (or add a new one) before teaching it, and say so.

## 1. Goal

Get the goal in their words and make it something a final question can check.
"Understand Girsanov" might mean the statement, the proof, or using it to
remove a drift: ask until it names one. When it is unclear how long they have,
ask; a short session gets a smaller goal at the same pace.

## 2. Route

The **route** is the path of ideas from the goal down, along needs edges, to
ideas they hold. `kioku context` the goal's area, then every idea on the path
in one call (`kioku context a,b,c`); reuse what exists and add what is
missing, with its edges ([ideas.md in the kioku skill](../kioku/ideas.md)).
Every term the goal uses is a definition on the route; every theorem on it is
proved in the lesson or a dependency.

The **plan** is the route's ideas the model does not show held (no answer, a
low R, a wrong last answer), ordered so each step's needs come before it. An
idea answered well long ago with R now low is a step too: its question may
settle it in a word.

## 3. The opening turn

The first turn already takes the first step. It holds:

- the goal, in one line;
- the plan, in one line: `Plan: a → b → c (3 steps at most)`. They object in
  their reply if they want it changed;
- step 1, taken from the bottom of the plan, where everything it builds on
  has an answer;
- probes on what step 2 builds on;
- triage over the rest of the plan's names.

## 4. Every turn after

Open with "Step k of N", then write the teaching turn.

- **A step is done when its answer is right** (**mastery learning**). Build
  only on steps they have shown. An idea that turns out held costs a word of
  feedback and the plan gets shorter.
- **The plan changes when an answer says so.** A failed probe, or a name
  marked never met that the route needs, becomes a step before the one that
  builds on it. Say it in one line: what was added and why. The goal stays as
  agreed.
- **Proofs.** When the goal is about proofs, a result's step is followed by
  its proof idea as a step of its own, asked as a write or say question.
- **A confident wrong answer is re-asked later in the lesson**, with a new
  case, after its repair.

## 5. Close

1. A final block on the goal at **transfer** depth: a case that looks
   different, where nothing names the idea, and that needs each step again.
2. After their reply: the verdicts, then coverage in one line from `kioku
   context` on the route ("route: 9 ideas, all asked, mean R .8").
3. With a notebook: a map of the lesson, an index note in its `notes/` folder
   (`type: index` in the frontmatter) that links the lesson's notes in the
   order they were taught, a line each. Without one: the results worth a
   note, for them to write.

## Across sessions

A lesson that stops before the close writes `LESSON.md` in the working
folder: the goal as agreed, the plan, and "next: step k of N". The next
session reads it and `kioku log --since 2d`, and its opening turn asks the
steps taught so far again alongside the next step.
