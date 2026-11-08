---
name: learn
description:
  "Teach the reader (the person you work with) a topic in this session, one checked step at a time, from
  what they hold to a goal. Use when they ask to learn, understand or be taught
  something here and now."
---

# Learn

A lesson moves the reader from what they hold to a **goal**, one reasoning
**step** at a time, each step checked before anything rests on it. The goal is
reached when it feels obviously true to them: it follows from what they hold
rather than sitting beside it as a memorised fact.

Load the reader-brief skill first: it holds their model, the check, and the
question block. Every probe, prediction and check below is a question block, so
the lesson records what they show as it goes.

What they hold is what their answers show, and nothing else. A result in their
vault, their notes or a paper they wrote is a place to read the statement from;
it is held once a question shows it. Speak of it in numbers ("R .6, one answer,
fragile"), never as "you hold this".

**State and derive are two ideas.** A result's answers say whether they can
state and apply it; its proof idea says whether they can derive it. A lesson
aimed at proofs needs both: a remembered theorem with an unasked proof is known
but not understood, and the record should say exactly that.

## 1. Goal

Get the goal in their words and make it concrete. "Understand Girsanov" might
mean the statement, the proof, or using it to remove a drift. Ask in prose until
the goal names something a final question can check.

## 2. Route

Draft the **route**: every idea from the goal down to ideas they surely hold,
reusing what `reader context` finds and adding the rest with `reader add`, with
their needs and uses edges.

- Each step teaches one new idea from ideas they hold or earlier steps gave;
  a result taught with its proof brings its proof idea as well.
- Every term the goal uses is a **definition** idea on the route. In a
  mathematical topic it is a proper mathematical definition: the objects, their
  domain and the defining condition, in the notation their notes use.
- Every theorem on the route is either **proved** in the lesson, from what they
  hold and what earlier steps teach, or declared a **dependency**: stated
  exactly, marked as unproved here, with a reference when one exists. A theorem
  enters the lesson only as one of the two.

## 3. Sweep

Ask about the whole route before teaching any of it. Nothing propagates in
their model: a right answer high up says nothing recorded about what lies
below, so every idea the lesson will lean on gets its own answer.

1. `reader context` every idea on the route (its area first, for the overview).
   An idea with a recent, high R needs no question; every other one is **open**.
2. Ask the open ideas in blocks of up to six, bottom up: definitions first, each
   applied to a tiny concrete example; then the results and methods; then the
   proof ideas, as "derive" or "why" items. Mostly picks, so a block takes a
   minute.
3. Read each answer with its confidence. Right and sure: held. Right and
   unsure: fragile, revisit it in the teaching. Wrong and sure: a
   misconception; repair it before anything rests on it. `-` or `?`: a gap,
   which becomes a step.

Done when every idea on the route has an answer or a recent, high R. Then state
the **floor** (what they hold), the gaps and the misconceptions in a few lines.

## 4. Plan

The plan is the route minus what the sweep showed they hold, in teaching order.

1. Number the steps and show them as a table: `step · name · kind · R`, with
   dependencies marked and the count of steps.
2. Wait for their go. From then on the route is fixed: open every turn with
   "Step k of N". When a step turns out to need a prerequisite they lack, insert
   it as a new step before the current one, show the changed rows, and teach
   it. The statement of the goal stays as agreed.

## 5. Teach

Each step, in order:

1. **Predict**: a one-item block about the step not yet taught. Point at the
   problem ("this works, but breaks when …; what has to give?") and let them
   attempt it. Skip it for a repair or a wrap-up.
2. **The step**: open by resolving their prediction, then give the one new fact
   in its clearest form: a definition as a proper definition, a theorem with
   all its hypotheses and then its full proof, written so they can copy both
   into their vault. A dependency is stated and named as unproved. Motivate a
   proof so it reads as discovered. Go Socratic when they can reason their way there, expository
   when it is beyond cold reach or they are tired.
3. **Check**: one block of two to four items:
   - the proof idea: derive the step, as a write or say item;
   - the new idea: apply it to a fresh case, as a pick;
   - one item on an earlier step or what it rests on, so earlier steps
     keep earning evidence.
4. **Repair** on ✗: name the wrong model, re-teach the step smaller, and check
   again with a fresh item. Build only on steps they have shown.

A block ends your turn.

## 6. Close

1. A final block on the goal itself, composing the steps.
2. Coverage: `reader context` the route and report "route: N ideas, k asked,
   mean R …". Ask one more block on any idea still without an answer.
3. List the results worth a vault note, for them to write.
