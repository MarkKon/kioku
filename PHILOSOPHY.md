# Why kioku exists

> The most important single factor influencing learning is what the learner
> already knows. Ascertain this and teach him accordingly.
> — David Ausubel, *Educational Psychology: A Cognitive View* (1968)

This file explains why kioku exists, the principles it keeps and the reason
for each, the ideas it borrows from, and the questions it has not answered yet.
The README says what kioku does. This file says why it does it that way. When
a change bends one of the principles, update this file first.

This file describes the v1 model (ideas, areas, edges marked needs and uses),
agreed on 2026-11-08; `GLOSSARY.md` defines its words and maps v0's
(propositions, chains, topics) to them.

## The problem

When you work with an agent, the agent gives you an explanation at whatever
level it guessed. Then you do the adapting: you skip what you already know, dig
out the step it skipped, and translate its frame into yours. The material may
already be distilled from source code or papers, but fitting it to what you know
is still your job. It should be the other way round: the agent should fit the
explanation to what you know.

This matters more as agents do more of the work. Work an agent does on your
behalf is only yours if you understand it. Agents have memory systems so they
can pick up where they left off, but the person using them needs one too: to
remember what was built, understand why, and keep up with the ideas the work
rests on. Otherwise the work gets done while your understanding of it falls
further behind. Keeping the person in the loop means keeping their
understanding in the loop.

## The opportunity

Every conversation with an agent can sit in the **goldilocks zone**: hard
enough that you have to work through it, and built exactly on what you already
know. That used to be expensive.

Benjamin Bloom's **mastery learning** (1968) says you don't build on a step
until the learner has shown they have it. When a check fails, you correct the
misunderstanding and check again. In 1984 Bloom reported that one-to-one
tutoring run this way beat ordinary classroom teaching by about two standard
deviations. He called it the "2 sigma problem" because nobody could afford a
tutor for every student. Later meta-analyses find a smaller effect (VanLehn
2011 puts human tutoring at about 0.8 SD), but it is still among the largest
effects in education research.

Agents remove the cost of the tutor. What they don't have is the thing a good
tutor carries from one session to the next: a model of what this learner has
shown, what they have forgotten, and what they misunderstand. Each agent
session starts blank. kioku is that missing model, kept outside any single
agent so that every agent reads the same one. With it, any session can act as a
mentor tuned to what you know, whether you are coding, writing, or asking a
quick question, and not only when you ask to learn something.

## The core loop

```
areas (a tree) ⊃ ideas ──needs / uses──▶ ideas
        │
   evidence: answers to questions that were asked, and verified work
        │
   memory model (FSRS-6 for now, swappable)  →  R per idea
        │
   agent: the idea + its neighbours + their R + the task  →  ask, or go on
        │
   answer  →  new evidence, written at once
```

The **check** is the smallest unit of this loop:

1. look up the ideas the next step leans on;
2. if R and the task leave it unsettled, ask;
3. record the answer the moment it is graded.

Everything else is built from checks. A brief for an essay or paper, the probe
and checks in a lesson, the pause in a pair-programming session, and the
one-line rule in an agent's global instructions are all checks run on different
sets of ideas.

## The model, and why

The model has to stay simple enough that any agent can add to it correctly in
passing, and still say something useful when it holds thousands of ideas.
Three records do that: ideas, the edges between them, and the areas they live
in. Evidence attaches to ideas.

### An idea is one thing that can be known alone

An idea is the unit evidence is about. An agent decides what one idea is with
four tests:

1. **It has a name**: the few words a colleague would use ("Itô isometry",
   "register_buffer", "Banach fixed point"), with no "and" in it. The name is
   the idea's identity. Its statement is a reference that can be reworded, as
   long as a past right answer would still be right.
2. **It can be known alone.** If someone could plausibly hold one part and lack
   the other, the parts are two ideas. If not, they are one. When a named
   theorem bundles parts that can be known apart (Banach: a unique fixed point,
   and the a priori estimate), the name goes to its main claim and each other
   part gets a name of its own. **When it is unclear, keep the idea whole**:
   answers show when parts come apart (the learner keeps getting one part and
   missing the other), and that is when a part gets its own idea. The whole
   keeps its answers and needs the new part.
3. **One short question can check it**, and a right answer is good evidence for
   the whole of it.
4. **It does not contain other ideas.** A result does not restate the
   definitions it uses; it has an edge to them. (A question still defines its
   terms inline: the question has to stand alone, the record does not.)

Each idea is one of four **kinds**: a *definition* (what a term means), a
*result* (that something holds: a theorem, a property, how an API behaves), a
*proof* (why a result holds: a proof, a derivation, or an argument for a
design choice), or a *method* (how to do something: an algorithm, a technique,
a code pattern). The kind says what a good question about it looks like.

Ideas are added when a task leans on them: when an agent is about to ask about
one, or to build on it, and finds nothing. A term a statement merely uses
("complete metric space") does not get an idea in advance. An agent looking
up the model before adding is what keeps it consistent: two agents asked to
cut the same material into ideas from scratch disagreed far more than two
agents choosing from areas that already existed.

Why:

- **v0 had no rule, and items grew.** Propositions had a median of 254
  characters. `causal-attention-head` held projections, scaling, mask, softmax
  and output; a lesson's theorem was rewritten three times before the learner
  cut it to "two facts". One grade then stood for several claims, and a right
  answer on the whole hid a wrong one on a part.
- **The size of a unit is set by what is learned and forgotten together.**
  This is the knowledge component of Koedinger, Corbett and Perfetti's KLI
  framework: a unit is inferred from performance on a family of tasks, and when
  those tasks stop moving together, the unit is split. Test 2 is that rule for
  an agent that has only one learner's answers.
- **Wording is not identity.** In v0 the statement was the identity, so an
  answered idea could not be reworded, and agents amended four ideas straight
  after creating them. A name is what an agent searches for and what a person
  says; it is the stable part.
- **A proof is its own idea** because stating a result and knowing why it
  holds are known apart ("remembering is not proving"). A result with two proofs
  has two proof ideas. This replaces v0's chains, which covered the same ground
  with hyperedges that also carried composition and teaching order.

### Edges are marked needs, uses, or both

An edge from X to Y carries one or both of two marks:

- **needs**: the learner cannot follow X's statement without holding Y. A
  result needs the definitions its statement uses; a proof needs the result it
  proves.
- **uses**: answering a question on X, or doing X, makes the learner carry Y
  out. A proof uses the lemmas it applies; training a model uses
  `optimizer.zero_grad()`.

The two marks are independent. Girsanov's theorem needs the definition of
Brownian motion but does not use it: applying the theorem does not make anyone
recall the definition. The proof of Girsanov's theorem needs and uses Itô's
formula. Training a model uses `zero_grad()`, but what a training loop is can be
followed without knowing that call, so it does not need it. Edges point one
way and never form a cycle.

For every edge the agent asks both questions, separately, and writes the edge
once with whichever marks pass. As a default, definitions and results only
need; proofs and methods use what they carry out, and often need it too (a
transformer block needs and uses layer normalisation). A result that seems to
use something usually means its proof is missing: the use belongs on the proof
idea. Only the closest edge is written: if X needs Y and Y needs Z, X gets no
edge to Z for that reason, which keeps notation such as $W$ from tying every
stochastic idea to Brownian motion.

Why:

- **An idea can be information or a tool.** Sometimes Y is needed only to
  understand what is going on, and sometimes it is used. Making the agent mark
  which, at the moment it adds the edge, makes the difference explicit for
  every agent that reads it.
- **The two behave differently in memory.** Math Academy keeps a prerequisite
  graph and a separate "encompassing" graph: doing an advanced topic counts as
  practice of what it encompasses, but not of every prerequisite, because
  "prerequisites are not necessarily activated" (Skycak 2023). He names mixing
  the two graphs as the way credit goes wrong.
- **v0's chains meant three things at once**: a step of a proof, the parts of
  a whole, and the order a lesson taught things in. 36 of 83 chains had a
  single premise and 52 were never asked. Needs and uses each have one test;
  teaching order is not a relation and lives in the lesson.
- **No OR.** Knowledge space theory can give an idea alternative sets of
  prerequisites (a surmise system), and v0 could, by several chains into one
  conclusion. In practice that only meant alternative proofs, which are now
  separate proof ideas.

### Areas are a tree for finding and for coverage

Every idea has exactly one home **area**, a path in a tree:
`maths/probability/stochastic-calculus`, `tools/pytorch`. The home is the most
specific existing area where a colleague would look for the idea first. A new
area is made only when several ideas will live in it, and the top levels are
few and change rarely. Areas hold no evidence and are not prerequisites. They
do three things:

- **They are the index.** At scale an agent does not search the whole model;
  it opens the area the conversation is in and sees its ideas with R, and its
  sub-areas folded with counts, the way it would list a directory.
- **They give coverage**: how many ideas an area has, how many have answers,
  and when it was last asked. Coverage is what makes "the learner knows this
  area" a statement with a denominator. In v0 a topic showed "mean R 0.88" when
  one of its eleven ideas had evidence.
- **They separate kinds of knowledge without a separate system.** Knowing
  `register_buffer` and knowing why attention is masked differ by where they
  live (`tools/pytorch` against `ml/transformers`). An idea in a tool area is
  cheap to name in passing; an idea in a concept area is not. A pairing skill
  reads that from the model rather than keeping its own.

### A lookup either finds the idea or says how sure it is that none exists

An agent looks ideas up by name first, then by alias, then by text. Adding an
idea refuses a near-duplicate and shows it, because a model with clean names
is the only kind in which a miss means something. A miss says where it looked
and how well covered that area is: "no idea named novikov; nearest is
girsanov; stochastic-calculus has 31 ideas, 24 with answers." In v0 a missed
search produced a duplicate of Picard–Lindelöf, and an empty result could not
tell "not recorded" from "not found".

### Depth belongs to the question, not to the idea

An idea can be known at different depths: the learner can state it, use it
when it is named, or transfer it to a setting where nothing points to it.
Each answer records the depth its question demanded. An idea does not get a
separate R per depth.

Why:

- **Four Rs per idea would need four times the questions**, and agents could
  not keep the levels apart. Most of the ladder already has a home: knowing a
  definition is the definition idea, deriving a result is its proof idea, and
  doing something fluently shows in the grade and in how stable the memory is.
- **Transfer is what is left, and it is rarely needed.** It is asked only when
  a task needs it, and the depth on the answer records that it was.
- **Recording depth costs one field** and keeps the data a later memory model
  will want.

## Principles, and why

### 1. Evidence is an answer to a question, or verified work

Evidence is an answer to a question that was asked, or a step of pairing work
the learner typed and a test verified, graded by how much help it took.
Conversation, things the agent taught, self-reports ("yes, I know Itô") and the
learner's own notes are never evidence.

One self-report is taken at its word: "never met it", said to a question or to
a name in a triage (a list of names the learner marks). A claim of not knowing
is rarely wrong, and when it is, the next question corrects it. A claim of
knowing is still tested. Confirmed "never met" matters even for ideas nobody
goes on to teach: it tells every agent which routes are closed.

Verified work passes the same tests as a question: a test with a key separates
real understanding from pattern-matching, and the grade traces back to a
recorded step. What it adds is volume: pairing exercises far more ideas than
any block of questions could ask about, and the learner is demonstrably building
the skill. Work that copies an explanation given in the same step is still
teaching, not evidence.

- **Self-report is badly calibrated.** People feel they understand things they
  can't explain (the illusion of explanatory depth, Rozenblit & Keil 2002), and
  something that reads fluently feels known.
- **Being taught something isn't knowing it.** An explanation the agent gave
  says what the agent did, not what the learner can now do.
- **Conversation is ambiguous.** Using a term correctly in passing can come from
  real understanding or from pattern-matching. A question with a key can tell
  them apart, and a transcript can't.
- **Clean evidence keeps the model honest.** If every number traces back to a
  question and an answer, a strange R can be audited, and a better memory model
  can be run on the same history later.

The cost is that the model knows little at first, and it grows only as fast as
questions are asked. That is acceptable: a question costs a moment.

### 2. No evidence means unknown, not zero

Most of what any learner knows has never been recorded. An empty record calls for
a question. It is not grounds to assume a gap and re-teach from scratch. kioku
keeps "no R" visibly different from "R = 0" everywhere, from the CLI output to
the colours in the graph.

### 3. Numbers, not verdicts

kioku outputs R, the probability the learner recalls an idea now, along with
the evidence behind it. It does not output labels like "held" or "faded".

- **How much an idea needs to be known depends on the task.** A premise the
  argument runs through needs a high, recent R; a side remark needs none. Only
  the agent knows which one it's dealing with.
- **Labels hide their rules.** "Faded" means nothing until you read the five
  rules that define it. A probability carries its meaning with it.

The agent combines R, the R of the neighbouring ideas, and the task to decide
whether to ask. If a premise's R is high, the learner could probably rebuild a
conclusion they've forgotten.

### 4. An answer updates only the idea it is about

A correct answer about a proof does not raise the lemmas it uses. Each piece of
evidence stays attached to the idea that was actually asked. Spreading it
through the graph would be inference. Inference belongs in the memory model,
where it can be swapped out and re-run, not baked into the evidence.

### 5. Write the moment it is graded; keep states few

Nothing waits in a pending area to be committed later. Each answer is stamped
with the minute it was given, so the memory model can see time pass within a
day. An answer that turns out not to count (a misread question, a misclick, a
broken item) is retracted: it moves to the archive with the reason, and is
never edited or silently dropped. The first version had a
pending step, and sessions sat uncommitted for days. Anything this basic and
this far in the background has to be simple: an id, a question, an answer, a
grade, a date. Each question block gets its own id, so parallel sessions never
grade against the wrong block.

### 6. Review comes from the work

Unlike Anki, kioku does not schedule reviews. R is information, not a
timetable. Review happens when a task needs an idea: the check finds it was
learned long ago and its R has dropped, so the agent asks, and that answer is
the review. Ideas come back when they matter, at the moment they are needed.
A session spent reviewing neglected ideas is still possible, but it is
something the learner chooses, not a queue that runs their day.

The model exists to estimate what the learner knows, not to make them keep it.
Forgetting is expected and fine: an idea that has not mattered for a year may
well be gone, and the model should say so, not push it back into memory. The
graph is built so that knowing and not knowing are easy to estimate, not so
that everything in it is retained.

### 7. Being shown the answer is teaching, not evidence

Plain FSRS treats a failed item as relearned once the answer is shown, so it
reports high recall straight after a wrong answer. In kioku, a wrong last
answer holds R at 0 until a later right answer. This is principle 1 applied to
the memory model.

### 8. Questions are built to diagnose

A question exists to separate states of knowledge, not just to collect a grade.

- **Pick items carry a confidence digit.** A right pick at chance confidence is
  a guess and carries no grade. A confident wrong pick is a misconception, which
  gets repaired before anything rests on it. Confident errors are also the ones
  people correct most readily once shown the answer (the hypercorrection effect).
- **Each wrong option is a specific wrong model**, named with `::`, so a pick
  reveals which misunderstanding the learner holds, not just that they are
  wrong. This is how concept inventories such as the Force Concept Inventory are
  built.
- **Applying beats reciting.** An item that uses an idea in a new case tests
  understanding; one that asks for the statement tests memory of the wording.
- **The answer format fits the learner**, as described in `profile.md`: a letter
  and a digit when they don't want to type, a formula written on paper or a
  tablet, a dictated line for a why.
- **A question block is as long as the moment needs.** A right answer records
  nothing about the ideas below it (principle 4), so an idea a task leans on
  still gets its own answer. While teaching, the questions on the step come
  first and questions that keep the model up to date follow: probes on what
  comes next, a triage, an idea from nearby whose R has dropped.
- **Each item stands alone.** Every term is defined in it or earlier, it can
  be answered without the other items, every wrong option is false outright,
  and the agent solves the item before asking. A badly built item measures the
  agent, not the learner.

### 9. A question costs a moment; a wrong pitch costs the conversation

This is the trade every check makes. Agents should ask rather than guess when
the next step depends on the answer, and skip the question when it doesn't. If
agents start asking about trivial things, tighten the threshold for asking. Don't
drop the check.

### 10. Nothing in the code or the skills is about one learner

Who the learner is lives in `profile.md`, and their setup in `config.toml`, both
in the private model folder. The code, the skills and this file are public and
work for anyone; skills made for one person live outside the repo and call
these. The learner record stays private.

Why: an agent cannot tell from the code who it is talking to, so anything
personal written into a skill is applied to everyone who installs it.

### 11. Infrastructure grows from use

Flat files read in full on each run were fine at fifty propositions. The schema
was the bigger risk: how fine-grained an idea should be, what an edge means,
how evidence should spread. v0 answered the first two by being used: about two
hundred answers over ten days showed items growing without a rule and chains
carrying three meanings, which is where the v1 model comes from. Storage still
grows from use. A database becomes worth having when one of these happens:
deduplication starts to hurt, the model passes a few thousand ideas, or the
graph view needs queries the CLI can't answer.

### 12. Record the structure now, model it later

The memory model today reads only an idea's own answers. It does not need the
edges, the areas or the depth of each answer. They are recorded anyway, because
they are cheap to write when an idea is added, while the agent has its
statement in front of it, and impossible to recover afterwards. Once there are
enough answers, a model can be fitted on everything at once: credit along uses
edges, what needs edges say about ideas never asked, how depth changes
forgetting. Such a model is judged by how well it predicts answers held out
from the log (as ALEKS validates its assessments), not by how plausible its
rules sound. Until one does better, R comes from the idea's own answers.

### 13. The notebook is open

A learner may keep a notebook: a folder of notes the agent writes, one per
idea, when a step's answers are right. A note holds what is looked up, not
what is understood: the statement, the formula or signature, one example, a
figure. The learner may have it open while they answer.

So R is the chance they can recall and use an idea with their notebook open.
That is the knowledge work needs. Nobody has to carry every formula and every
signature in their head, and a question that only asks for one measures
memory of the wording. Questions ask what a note cannot answer: which idea
applies, why it holds, what breaks without it.

The notebook is never evidence, and the model does not read it. It follows
the graph: a note is named by its idea's id, its links are the idea's edges,
and an index note per area lists what is there. The learner's own notes stay
their own, written by hand; the notebook is where they condense from.

## Ideas it draws on

The first group is where the idea came from. The rest are related work found
along the way, listed because each one supports or challenges a choice kioku
makes.

| idea | source | in kioku |
| ---- | ------ | --------- |
| Mastery learning | Bloom, "Learning for Mastery" (1968) | check before building; repair and re-check on a miss |
| The 2 sigma problem | Bloom, *Educational Researcher* 13(6) (1984); VanLehn, *Educational Psychologist* 46(4) (2011) | the reason it is worth doing: agents make one-to-one tutoring affordable |
| Zone of proximal development | Vygotsky, *Mind in Society* (1978) | the goldilocks rule: one reasoning step from what is held |
| Start from what the learner knows | Ausubel (1968) | the whole premise: look up before you pitch |
| Spaced repetition, forgetting curves | Ebbinghaus (1885); [FSRS](https://github.com/open-spaced-repetition) | R comes from FSRS-6, used as information rather than as a schedule |
| Learner models, knowledge tracing | Corbett & Anderson, "Knowledge tracing" (1994) | a learner model, but kept outside any one tutor and shared by every agent |
| Prerequisite structure | Doignon & Falmagne, knowledge space theory (1985); surmise systems in Falmagne & Doignon, *Learning Spaces* (2011) | needs edges; alternative prerequisite sets are left out, since in practice they were alternative proofs |
| Knowledge components | Koedinger, Corbett & Perfetti, "The Knowledge-Learning-Instruction framework", *Cognitive Science* 36(5) (2012) | an idea is sized by what is learned and forgotten together; split it when its parts move apart |
| Prerequisite vs encompassing graphs | Skycak, "Optimized, individualized spaced repetition in hierarchical knowledge structures" (2023), Math Academy | the needs and uses marks, kept apart because only use is practice |
| Validating an assessment by prediction | Cosyn et al., "Assessing mathematical knowledge in a learning space" (2013), ALEKS | a later memory model is judged by how well it predicts held-out answers |
| The testing effect | Roediger & Karpicke, *Psychological Science* 17(3) (2006) | every check also strengthens what it measures |
| Confidence-based marking | Gardner-Medwin (1995) | the confidence digit on picks |
| Hypercorrection | Butterfield & Metcalfe (2001) | a confident miss is flagged and repaired first |
| Diagnostic distractors | Hestenes, Wells & Swackhamer, Force Concept Inventory (1992) | each wrong option names a wrong model |
| Illusion of explanatory depth | Rozenblit & Keil (2002) | why self-report is not evidence |
| Desirable difficulties, productive failure | Bjork (1994); Kapur (2008) | an idea one step away is tried before it is explained; the open question of how much struggle to leave |
| Worked examples and fading; expertise reversal | Renkl & Atkinson (2003); Kalyuga et al. (2003) | an idea further away gets a solved case, then one with the key step left out; how much is read from R |
| Contrasting cases | Schwartz & Bransford, "A time for telling" (1998) | the explanation follows the learner's attempt on cases that differ in one feature |
| Generation effect, self-explanation | Slamecka & Graf (1978); Chi et al. (1994) | every teaching turn ends with the learner producing something, and saying why |
| Elaborated feedback, refutation | Shute (2008); Kendeou & O'Brien (2014) | feedback says why; a repair names the belief and shows where it fails |
| Interleaving | Rohrer & Taylor (2007) | a turn's questions include an idea from nearby whose R has dropped |
| Memory woven into reading | Matuschak & Nielsen, [Quantum Country](https://quantum.country) and "How can we develop transformative tools for thought?" (2019) | the check sits inside the work, not in a separate review app |
| Graph view | Obsidian | `kioku graph` |

## Tensions and open questions

These are the places where the philosophy is still unsettled. Using kioku
should settle them, and each settled one moves into the principles above or the
log below.

- **Goldilocks is more than level.** Knowing what the learner holds says what to
  explain. It doesn't say how much to leave for them to work out themselves,
  which is where much of the learning happens (desirable difficulties). The
  teaching turn's rule is one answer: an idea one reasoning step away is tried
  before it is explained, one further away gets a worked example. Whether that
  line is in the right place is for use to show.
- **Asking changes what it measures.** By the testing effect, every check is
  also practice. That fits the loop, since FSRS assumes reviews strengthen
  memory, but it means R partly reflects how often the agents happened to ask.
- **Stop and teach, or note it and go on?** When a check finds a gap in the
  middle of a task, the agent can teach it now or flag it and carry on. Neither
  is right for every task.
- **Knowledge that predates the record.** One right answer gives an FSRS
  stability of about 2.3 days, so material held for years looks faded within a
  week, and agents ask about it again too often. The memory model needs a prior
  for old knowledge that is being recorded for the first time.
- **Fresh answers say little.** R now falls within the day (FSRS-6 on elapsed
  time), but only slightly: a first answer graded good still reads about 0.98
  eight hours later. Whether early learning needs a separate short-term memory
  model, one in which an idea met this morning can be gone by the evening, is
  open.
- **What the graph should do to R.** Principle 12 records needs, uses, areas
  and depth for a later model. Which of them improve the prediction of answers,
  and by how much, is open until there is enough data to test.
- **Learning is not retention.** Only 14 of the 129 ideas answered in v0 were
  answered on more than one day, so R mostly reports how a lesson went that
  day, and a lesson's close reads .93 to .99 for ideas met that morning. An
  answer given on the day an idea was taught shows understanding, not memory.
  How the model should tell the two apart, and how a lesson should add new
  ideas rather than treat them like old ones, is the next question after v1.
  An answer now records whether the idea was taught earlier in the same
  session (`taught`), which is the data that question needs; the memory model
  does not read it yet.
- **Do agents mark edges consistently?** The needs and uses tests and the four
  tests for an idea are meant to give the same answer whichever agent applies
  them. If they do not, the rules need sharpening before the data is worth
  modelling.
- **Competent use outside pairing.** Test-verified pairing work counts
  (principle 1). Correct code written elsewhere, with no test and no recorded
  step, still does not; whether it should is open.
- **Observed work's grade.** good/hard/again by the help a step took is a first
  calibration; the memory model may need to weigh it differently from an
  answer.
- **Question fatigue.** How many questions per session the learner will put up
  with, and where "non-trivial" begins, can only be learned from use.

## Decision log

Newest last. Add an entry whenever a principle is added, changed or dropped.

- **2026-10-30.** reader-brief is a skill shared by the essay, paper and pair
  skills, backed by a single-file CLI.
- **2026-11-02.** Evidence is only answers to questions that were asked. The
  `demo`, `taught` and `recall` records move to an archive that nothing reads.
  Vault notes are hints, not credit.
- **2026-11-02.** `check` replaces `brief`. Labels are dropped in favour of raw
  R and the evidence behind it.
- **2026-11-02.** An answer updates only its own id. Propagation is later work
  for the memory model.
- **2026-11-02.** Answers are written the moment they are graded. The pending
  and commit steps are removed. Each question block gets its own id.
- **2026-11-02.** A wrong last answer holds R at 0 until a right one.
- **2026-11-02.** No review scheduler. R is information, and review happens when
  a task needs an idea.
- **2026-11-02.** A one-line reader-check rule goes into the global instructions
  of every agent, so ordinary sessions check too, not only the skills.
- **2026-11-02.** The project gets its own repo (public code, private data), is
  split into modules, and is made reader-agnostic through `profile.md` and
  `config.toml`.
- **2026-11-02.** `reader graph`: a read-only view of the model. Editing and
  timelines are left for the interface that use will shape.
- **2026-11-03.** `reader amend` and `reader delete`. An amend keeps the id
  and its answers, so changing the claim of an answered id needs `--force`; a
  different claim is a new id. A delete moves the id's answers to `archive.md`,
  so evidence is set aside, never rewritten or lost.
- **2026-11-03.** Answers carry the minute they were given, and the memory
  model runs on elapsed time, so R falls within a day. Older answers were
  timed from their question blocks; a line with only a date reads as noon.
- **2026-11-03.** `reader retract` sets an answer aside with a reason, and a
  redo or regrade archives the answer it replaces.
- **2026-11-03.** A right answer at the top of a block no longer stands in for
  its prerequisites: with no propagation, it recorded nothing about them, and
  lessons were built on floors nobody had checked. Lessons now sweep their
  whole route with questions before teaching.
- **2026-11-03.** A proposition records stating and applying, the chain into
  it records deriving.
- **2026-11-03.** The learn skill moves into the repo beside reader-brief: it
  runs on the CLI, so it changes with it. The essay, paper and pair skills stay
  out; they use the model only through reader-brief.
- **2026-11-07.** Test-verified pairing work becomes evidence, graded by the
  help it took (good: clean from the brief; hard: help beyond the brief or a
  slip; again: handed the answer). Pairing exercises more ideas than questions
  can cover, and work a test checks is not the ambiguous conversation principle
  1 excludes. Recorded as say-item blocks until the CLI gets a command for it.
- **2026-11-08.** v1 model. Propositions become **ideas**: named, sized by four
  tests (a name, can be known alone, one question checks it, contains no other
  idea), of four kinds (definition, result, proof, method); the name is the
  identity and the statement can be reworded. Chains are dropped: a proof is
  its own idea, and **edges** carry the marks **needs** (cannot follow it
  without) and **uses** (doing it carries it out), independently. Topics
  become **areas**, a tree with one home per idea, used for lookup and
  coverage and never as prerequisites. Answers record the **depth** their
  question demanded (state, use, transfer) instead of ideas getting levels. v0
  showed items growing without a rule (median 254 characters), chains carrying
  three meanings, and searches that missed into duplicates.
- **2026-11-08.** Principle 12: structure is recorded now for a model fitted
  later; the memory model keeps reading only an idea's own answers until a
  graph-aware one predicts held-out answers better. Principle 6 gains that the
  model is for assessment, not retention: forgetting is fine.
- **2026-11-08.** Dry run of the v1 rules: two agents each migrated three
  slices of the v0 model (93 propositions, 58 chains) on their own. They agreed
  on whether to split a proposition 80 times out of 93 and on its kind 50 out
  of 51, but on its area only 58 out of 93, and on an edge's marks 87 out of
  103 (27 of 40 for code and ML ideas, where they read needs and uses as
  exclusive). The rules gained: consequences and named bundles under test 2;
  arguments as proofs; terms as ideas before they are asked; both edge
  questions asked separately, with defaults by kind and closest edges only; and
  how to pick or make an area.
- **2026-11-08.** Second dry run with those rules and a starting area tree.
  Areas improved (67 of 93 the same) and chains too (53 of 58), but split
  decisions got worse (64 of 93): the rules that told agents to make more ideas
  (consequences, terms in advance) were applied differently by each. They are
  replaced by "when unclear, keep it whole; split when answers show the parts
  coming apart", which is the knowledge-component rule, and by adding ideas
  when a task leans on them. Edges: the two agents shared at least one mark on
  136 of 139 edges but disagreed on adding the second on 30, mostly in code
  and ML, so the second mark is noisy; it stays, as data for a later model.
- **2026-11-08.** The live model migrated to v1. One agent per group of areas
  filled the table: the 176 propositions became ideas as they were, and of the
  96 chains, 75 became proof or method ideas (all 32 with answers among them),
  18 became edges only and 3 were dropped as teaching order. 251 ideas in 19
  areas, 377 edges, no cycles; all 231 answers kept their idea, 23 now marked
  observed. The v0 folder stays beside it as `reader-v0`.
- **2026-11-09.** The tool becomes kioku (記憶, memory), and the person it
  models the learner: "reader" came from the essay and paper skills, and the
  tool is now a memory model any skill consults. The skills are rebuilt
  (`docs/v1-skills.md`): an always-loaded `kioku` skill kept short, with the
  formats in the CLI's help; `learn` teaching each step at the size of what the
  learner holds, with checks that compose earlier steps; `pair` moved into the
  repo, handing API calls over as materials that fade once R says they are
  held. Skills read R and answers, never labels laid over them: a first draft
  that sorted route ideas into states was dropped for going against principle
  3. An item can be asked before its idea is taught (`pre`): the answer is
  kept as data and skipped by the memory model.
- **2026-11-10.** The teaching turn (`skills/kioku/turn.md`, drafted in
  `docs/teaching-turn.md`). One step is one turn and one reply; only the
  repair of a confident error spends a second turn. A turn's jobs are named by
  the terms of the literature (feedback, anchor, material, generation,
  assessment), so the skills lead with words an agent already knows. This
  replaces the lesson's sweep of 2026-11-03: its reason stands (nothing rests
  on an unasked idea), but the asking now rides in every turn's questions
  instead of a round before the teaching, because rounds of questions and
  separate lesson, check and brief turns made sessions long. Learn and pair
  share the turn; in pairing the learner's production is code, a passing test
  is evidence for the method, and why it works gets its own question. A
  question block has no fixed size. "Never met it" can be said to a list of
  names (a triage, recorded with `kioku unmet`): a claim of not knowing is
  taken at its word, a claim of knowing is still tested.
- **2026-11-10.** Principle 13: the notebook. The agent writes one note per
  idea it has taught, the learner may keep it open while answering, and R is
  read as recall and use with the notebook open. It answers two things use
  showed: lessons ended with "what should go in my notes?", and questions
  that asked for a formula measured the wrong thing.
- **2026-11-10.** An answer records whether its idea was taught earlier in the
  same session (`taught`), as data for a later memory model (principle 12).
  "Never met" is shown as `unmet`, apart from a wrong answer, and counted in
  an area's coverage. `kioku ask` adds the ideas written above its block, so
  asking about an unrecorded idea is one call. `kioku log` and `kioku context
  --near` give an agent what a session asked and what lies around an idea.
