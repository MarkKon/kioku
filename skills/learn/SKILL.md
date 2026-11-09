---
name: learn
description:
  "Teach the learner (the person you work with) something in this session, one
  checked step at a time, from what they hold to a goal. Use when they ask to
  learn, understand, revise or be taught something here and now."
---

# Learn

A lesson moves the learner from what they hold to a **goal**, one **step** at
a time. Each step is taught at the size of what they hold and checked before
anything rests on it. The goal is reached when it feels obviously true to
them: it follows from what they hold rather than sitting beside it as a fact.

Load the kioku skill first: the model, the check and the question block. Every
check below is a question block, so the lesson records what they show as it
goes. Read `kioku profile` for their notation, how they answer and how long
they usually have.

What they hold is what their answers show. A result in their notes or a paper
they wrote is a place to read the statement from; it is held once a question
shows it. Speak of it in numbers ("R .6, one answer"), never as "you know
this". **State and derive are two ideas**: a result's answers say whether they
can state and use it, its proof idea whether they can derive it.

## How everything is written

- Everything they should see is in your reply: lesson text, proofs, blocks.
- Every term is defined before it is used, as a proper definition (the
  objects, their domain, the defining condition) in their notation. A named
  result is stated before it is used.
- Every proof is whole: from what they hold and what earlier steps taught. A
  theorem the lesson does not prove is a **dependency**: stated exactly, said
  to be unproved here, with a reference when one exists.
- One change at a time, said out loud: a changed theorem, plan or notation is
  announced with what changed and why.

## 1. Goal

Get the goal in their words and make it something a final question can check.
"Understand Girsanov" might mean the statement, the proof, or using it to
remove a drift: ask until it names one. When it is unclear how long they have,
ask; a short session gets a smaller goal, not a faster pace.

## 2. Route

The **route** is the path of ideas from the goal down, along needs edges, to
ideas they hold. `kioku context` the goal's area, then every idea on the path;
reuse what exists and add what is missing, with its edges ([ideas.md in the
kioku skill](../kioku/ideas.md)). Every term the goal uses is a definition on
the route; every theorem on it is proved in the lesson or a dependency.

## 3. Sweep

Ask before teaching. Read each route idea's R and last answer and decide what
the lesson needs from it: what the goal runs through needs a recent right
answer; an idea answered well long ago with R now low gets a question, not a
lesson; one never answered gets a probe; a confident wrong last answer is
repaired first. A right answer high on the route records nothing about what
lies below it: every idea the lesson leans on gets its own answer.

Ask what is unsettled in blocks of up to six, bottom up, mostly picks that
apply each idea to a tiny case. The sweep is done when every idea the lesson
leans on has a recent answer or a high R. Then say in a few lines what they
showed: what holds, what is missing, any misconception.

## 4. Plan

The steps are the route's ideas their answers did not show, ordered so each
step's needs are held or taught earlier. Show them as a table, `step · name ·
kind · R`, with the number of steps and whether the lesson is mostly new or
mostly revisiting. Wait for their go.

From then on, open every turn with "Step k of N". When a step turns out to
need something they lack, insert it as a new step before the current one, show
the changed rows, and teach it. The goal stays as agreed.

## 5. Teach

Each step, in order:

1. **Teach it at the size of what they hold.** New to them: a full worked
   derivation with its steps labelled, motivated so it reads as discovered.
   Its parts held: the skeleton, with the key step left to them. Held: a
   sentence and a link. Go Socratic when they can reason their way there,
   expository when it is out of cold reach or they are tired.
2. **Check**, one block of two to four items:
   - one "why does this hold / what breaks if …" item, tied to an idea they
     hold;
   - the new idea applied to a fresh case that also needs the earlier steps it
     rests on, so those come back because the case needs them;
   - its proof idea, when the goal is about proofs, as a write or say item;
   - rarely, as the last item, the next step before it is taught, tagged
     `pre`: only where they can reason most of the way there.
3. **The step is done when its check is right.** A confident wrong answer is
   the moment to teach: name the belief behind it, show where it fails on a
   contrasting case, give the right idea, and re-ask it later in the lesson
   with a new item. Re-teach the step smaller and check it again with a fresh
   item. Build only on steps they have shown.

When they are stuck, the hint is the smallest step their own held ideas can
bridge: name the idea that unlocks it ("this is the tower property again").
When what is missing is something they do not hold, it is not a hint but a
gap: teach it as a step.

A block ends your turn.

## 6. Close

1. A final block on the goal at **transfer** depth: a case that looks
   different, where nothing names the idea, and that needs each step again.
2. Coverage: `kioku context` the route and report it in one line ("route: 9
   ideas, all asked, mean R .8").
3. List the results worth a note, for them to write.

## Across sessions

A lesson that stops before the close writes `LESSON.md` in the working
folder: the goal as agreed, the plan's rows, and "next: step k of N". The next
session reads it, re-asks the steps taught so far in one block, and goes on.
