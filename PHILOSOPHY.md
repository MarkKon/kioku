# Why reader exists

> The most important single factor influencing learning is what the learner
> already knows. Ascertain this and teach him accordingly.
> — David Ausubel, *Educational Psychology: A Cognitive View* (1968)

This file explains why reader exists, the principles it keeps and the reason
for each, the ideas it borrows from, and the questions it has not answered yet.
The README says what reader does. This file says why it does it that way. When
a change bends one of the principles, update this file first.

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
session starts blank. reader is that missing model, kept outside any single
agent so that every agent reads the same one. With it, any session can act as a
mentor tuned to what you know, whether you are coding, writing, or asking a
quick question, and not only when you ask to learn something.

## The core loop

```
propositions ──chains──▶ propositions
        │
   evidence: answers to questions that were asked
        │
   memory model (FSRS-6 for now, swappable)  →  R per id
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

## Principles, and why

### 1. Evidence is only an answer to a question that was asked

Conversation, things the agent taught, self-reports ("yes, I know Itô") and the
reader's own notes are never evidence.

- **Self-report is badly calibrated.** People feel they understand things they
  can't explain (the illusion of explanatory depth, Rozenblit & Keil 2002), and
  something that reads fluently feels known.
- **Being taught something isn't knowing it.** An explanation the agent gave
  says what the agent did, not what the reader can now do.
- **Conversation is ambiguous.** Using a term correctly in passing can come from
  real understanding or from pattern-matching. A question with a key can tell
  them apart, and a transcript can't.
- **Clean evidence keeps the model honest.** If every number traces back to a
  question and an answer, a strange R can be audited, and a better memory model
  can be run on the same history later.

The cost is that the model knows little at first, and it grows only as fast as
questions are asked. That is acceptable: a question costs a moment.

### 2. No evidence means unknown, not zero

Most of what any reader knows has never been recorded. An empty record calls for
a question. It is not grounds to assume a gap and re-teach from scratch. reader
keeps "no R" visibly different from "R = 0" everywhere, from the CLI output to
the colours in the graph.

### 3. Numbers, not verdicts

reader outputs R, the probability the reader recalls an idea now, along with
the evidence behind it. It does not output labels like "held" or "faded".

- **How much an idea needs to be known depends on the task.** A premise the
  argument runs through needs a high, recent R; a side remark needs none. Only
  the agent knows which one it's dealing with.
- **Labels hide their rules.** "Faded" means nothing until you read the five
  rules that define it. A probability carries its meaning with it.

The agent combines R, the R of the neighbouring ideas, and the task to decide
whether to ask. If a premise's R is high, the reader could probably rebuild a
conclusion they've forgotten.

### 4. An answer updates only the id it is about

A correct answer about a chain does not raise its premises. Each piece of
evidence stays attached to the thing that was actually asked. Spreading it
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

Unlike Anki, reader does not schedule reviews. R is information, not a
timetable. Review happens when a task needs an idea: the check finds it was
learned long ago and its R has dropped, so the agent asks, and that answer is
the review. Ideas come back when they matter, at the moment they are needed.
A session spent reviewing neglected ideas is still possible, but it is
something the reader chooses, not a queue that runs their day.

### 7. Being shown the answer is teaching, not evidence

Plain FSRS treats a failed item as relearned once the answer is shown, so it
reports high recall straight after a wrong answer. In reader, a wrong last
answer holds R at 0 until a later right answer. This is principle 1 applied to
the memory model.

### 8. Questions are built to diagnose

A question exists to separate states of knowledge, not just to collect a grade.

- **Pick items carry a confidence digit.** A right pick at chance confidence is
  a guess and carries no grade. A confident wrong pick is a misconception, which
  gets repaired before anything rests on it. Confident errors are also the ones
  people correct most readily once shown the answer (the hypercorrection effect).
- **Each wrong option is a specific wrong model**, named with `::`, so a pick
  reveals which misunderstanding the reader holds, not just that they are
  wrong. This is how concept inventories such as the Force Concept Inventory are
  built.
- **Applying beats reciting.** An item that uses an idea in a new case tests
  understanding; one that asks for the statement tests memory of the wording.
- **The answer format fits the reader**, as described in `profile.md`: a letter
  and a digit when they don't want to type, a formula written on paper or a
  tablet, a dictated line for a why.
- **A question block is short, hardest item first.** A confident right answer
  at the top shows where the reader stands. It records nothing about the ideas
  below it (principle 4), so an idea a task leans on still gets its own answer.
- **Each item stands alone.** Every term is defined in it or earlier, every
  wrong option is false outright, and the agent solves the item before asking.
  A badly built item measures the agent, not the reader.

### 9. A question costs a moment; a wrong pitch costs the conversation

This is the trade every check makes. Agents should ask rather than guess when
the next step depends on the answer, and skip the question when it doesn't. If
agents start asking about trivial things, tighten the threshold for asking. Don't
drop the check.

### 10. Nothing in the code is about one reader

Who the reader is lives in `profile.md`, and their setup in `config.toml`, both
in the private model folder. The code, the skill and this file are public and
work for anyone. The learner record stays private.

### 11. Infrastructure grows from use

Flat files read in full on each run are fine at fifty propositions. The schema
is the bigger risk: how fine-grained a proposition should be, what a chain
means, how evidence should spread. Those questions get answered by using the
loop in real sessions, not by designing a database up front. A database becomes
worth having when one of these happens: deduplication starts to hurt, the model
passes a few hundred propositions, or the graph view needs queries the CLI can't
answer.

## Ideas it draws on

The first group is where the idea came from. The rest are related work found
along the way, listed because each one supports or challenges a choice reader
makes.

| idea | source | in reader |
| ---- | ------ | --------- |
| Mastery learning | Bloom, "Learning for Mastery" (1968) | check before building; repair and re-check on a miss |
| The 2 sigma problem | Bloom, *Educational Researcher* 13(6) (1984); VanLehn, *Educational Psychologist* 46(4) (2011) | the reason it is worth doing: agents make one-to-one tutoring affordable |
| Zone of proximal development | Vygotsky, *Mind in Society* (1978) | the goldilocks rule: one reasoning step from what is held |
| Start from what the learner knows | Ausubel (1968) | the whole premise: look up before you pitch |
| Spaced repetition, forgetting curves | Ebbinghaus (1885); [FSRS](https://github.com/open-spaced-repetition) | R comes from FSRS-6, used as information rather than as a schedule |
| Learner models, knowledge tracing | Corbett & Anderson, "Knowledge tracing" (1994) | a learner model, but kept outside any one tutor and shared by every agent |
| Prerequisite structure | Doignon & Falmagne, knowledge space theory (1985) | chains: premises that together give a conclusion |
| The testing effect | Roediger & Karpicke, *Psychological Science* 17(3) (2006) | every check also strengthens what it measures |
| Confidence-based marking | Gardner-Medwin (1995) | the confidence digit on picks |
| Hypercorrection | Butterfield & Metcalfe (2001) | a confident miss is flagged and repaired first |
| Diagnostic distractors | Hestenes, Wells & Swackhamer, Force Concept Inventory (1992) | each wrong option names a wrong model |
| Illusion of explanatory depth | Rozenblit & Keil (2002) | why self-report is not evidence |
| Desirable difficulties, productive failure | Bjork (1994); Kapur (2008) | the predict step in lessons; the open question of how much struggle to leave |
| Memory woven into reading | Matuschak & Nielsen, [Quantum Country](https://quantum.country) and "How can we develop transformative tools for thought?" (2019) | the check sits inside the work, not in a separate review app |
| Graph view | Obsidian | `reader graph` |

## Tensions and open questions

These are the places where the philosophy is still unsettled. Using reader
should settle them, and each settled one moves into the principles above or the
log below.

- **Goldilocks is more than level.** Knowing what the reader holds says what to
  explain. It doesn't say how much to leave for them to work out themselves,
  which is where much of the learning happens (desirable difficulties). The
  learn skill's predict step is one answer, but there is no general rule yet.
  Getting this right matters a lot and is hard.
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
- **Propagation.** Should a right answer on a chain say something about its
  premises, or a held conclusion about what rests on it? Principle 4 says not in
  the evidence. Whether the memory model should infer it is open.
- **What is a proposition, and what is a chain?** Partly settled: a
  proposition's answers say whether the reader can state and apply a claim,
  and the chain into it whether they can derive it. How fine-grained a claim
  should be is still open, and affects every lookup and every question.
- **Competent use as evidence.** Code the reader writes correctly without being
  asked shows something. For now it doesn't count (principle 1). Revisit only if
  keeping evidence clean costs too many questions.
- **Question fatigue.** How many questions per session the reader will put up
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
