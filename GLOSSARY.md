# kioku

The language of kioku's model of what a learner knows, from v1 on. The v0
terms it retired are listed at the end.

## The learner and the model

**Learner**:
The person an agent works with, whose knowledge the model estimates; the
driver, in pairing.
_Avoid_: user, reader, student

**Model**:
Everything kioku records about one learner: areas, ideas, edges and evidence.
_Avoid_: knowledge base, memory base, graph

## What is known

**Idea**:
One named unit of knowledge that a learner could hold or lack on its own, and
that one short question can check.
_Avoid_: proposition, item, card, concept, knowledge component

**Name**:
The few words a colleague would use for an idea; it is the idea's identity.
_Avoid_: title, slug

**Statement**:
The idea's reference text, which questions are checked against; it can be
reworded without changing the idea.
_Avoid_: claim, definition (as a field)

**Kind**:
What sort of idea it is: a definition, a result, a proof or a method.
_Avoid_: type, category

**Definition**:
An idea that says what a term means.

**Result**:
An idea that says something holds: a theorem, a property, a fact, the behaviour
of an API.
_Avoid_: claim, theorem (as a kind), fact

**Proof**:
An idea that says why a result holds: a proof, a derivation, or an argument; it
is a separate idea from the result.
_Avoid_: chain, derivation

**Method**:
An idea that says how to do something: an algorithm, a technique, a code
pattern.
_Avoid_: skill, procedure

## How ideas relate

**Area**:
A named place in one tree where ideas live; every idea has exactly one home
area.
_Avoid_: topic, tag, folder, subject

**Edge**:
A link from one idea to another, carrying the mark needs, the mark uses, or
both.
_Avoid_: chain, link, dependency

**Needs**:
The mark on an edge from X to Y when the learner cannot follow X's statement
without holding Y.
_Avoid_: prerequisite, rests on, premise

**Uses**:
The mark on an edge from X to Y when answering a question on X, or doing X,
makes the learner carry out Y.
_Avoid_: encompasses, exercises, applies

## What was shown

**Question**:
One numbered item in a question block, about one idea.
_Avoid_: item (alone), card, probe

**Question block**:
The few questions put to the learner at once, answered in one line.
_Avoid_: quiz, ask

**Answer**:
The learner's reply to one question and how it went, recorded the moment it
is read.
_Avoid_: response, review

**Observed work**:
A step the learner did in pairing that a test verified, recorded with the help
it took.
_Avoid_: demo, usage

**Triage**:
A list of idea names the learner marks as never met; the marked ones are
recorded, the others still get a question.
_Avoid_: survey, self-assessment

**Evidence**:
Answers, observed work and names marked never met; nothing else moves a
number.
_Avoid_: data, history

**Depth**:
What a question demanded of the idea: state it, use it when it is named, or
transfer it to a setting where nothing points to it.
_Avoid_: level, mastery level

**Outcome**:
How an answer went: right, partly (right with a slip), wrong, or never met; a
guess is a right pick at chance confidence, recorded and not counted.
_Avoid_: grade, score, rating

**Help**:
What a step of observed work took: done alone, with a hint, or shown the
answer.

**Probe**:
A question marked as asked to find out what the learner already held, before
any teaching; a right answer to it is read as knowledge from before the
record.
_Avoid_: pretest, diagnostic (as a noun)

**Confidence**:
The digit a learner puts on a pick; the memory model reads it against their
own share of right picks at that digit.

## What the model says

**R**:
The probability that the learner can recall and use an idea now, with their
notebook open when they keep one, computed by the memory model from that
idea's evidence.
_Avoid_: mastery, score, retention, recall (as a depth)

**Memory model**:
The swappable function that turns evidence, and later the graph, into R.
_Avoid_: scheduler, FSRS (as the name of the role)

**Coverage**:
How much of an area has evidence: its ideas, how many have answers, and when
it was last asked.
_Avoid_: progress, completion

**Check**:
Looking up the ideas a next step leans on, and asking what the lookup does not
settle.
_Avoid_: brief (for a single lookup), quiz

**Notebook**:
A folder of notes the agent writes for the learner to look things up in, one
note per idea; never evidence.
_Avoid_: vault (the learner's own notes), lecture notes, wiki

## How it is taught

**Turn**:
One message from the agent.
_Avoid_: response, round

**Step**:
One new idea, taught and checked; it takes one turn and one reply.
_Avoid_: lesson (for a single idea), unit

**Teaching turn**:
A turn that teaches a step: feedback on the last reply, the idea the step
grows from, the new idea, something for the learner to produce, and questions
that keep the model up to date.

**Repair**:
A second turn on a step, after an answer that was wrong and confident.
_Avoid_: remediation, re-teach

**Plan**:
The ideas on the way to a goal that the model does not show held, in the order
they are taught.
_Avoid_: curriculum, syllabus

## Retired terms (v0)

**Grade** (again, hard, good, easy): now an outcome, with the confidence and
help recorded beside it; old evidence lines are still read.
**Proposition**: now an idea.
**Chain**: now a proof idea and its edges; a chain that only recorded teaching
order is dropped.
**Topic**: now an area.
**reader**: the tool is now kioku (記憶, memory); the person it models is the
learner.
