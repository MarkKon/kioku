# v1 skills: the memory skill, learn, pair

Proposal, 2026-11-09, revised after the first read. The knowledge model is
settled (`PHILOSOPHY.md`, "The model, and why"). This is the shape of the
three skills built on it, the evidence behind each rule, and how the repo
becomes usable by anyone.

Sources: the learning-science and programming-education literature (each rule
names its source), and the past lesson and pairing sessions (quoted as
_sessions_).

## The name

`reader` was named for the essay and paper skills, whose audience is a
reader. The tool is no longer about a reader: it is a memory model of the
person an agent works with, a backend any skill can ask "do they hold this?".
The name should say that. Candidates (the command can differ from the PyPI
name, where all of these are taken):

- **`ken`**: one's range of knowledge ("beyond my ken"). `ken context
  girsanov`, `ken ask`. Short, unclaimed as a command here.
- **`engram`**: a memory trace. Precise, but heavier.
- **`grasp`**: what someone has grasped. Plain, slightly generic.

The person is **the learner** in the docs (the driver, in pairing). The
always-loaded skill takes the tool's name.

## What all three share

These come from what went wrong in past sessions, and hold in every skill:

- **Everything the learner should see is in the reply text.** Question
  blocks, lesson text, proofs. Tool output is invisible to them. (_sessions_:
  "i cant see a question", "where did you send the text?")
- **Every term is defined and every proof is whole.** A named result is
  stated before it is used; a proof does not lean on "another proof" unless
  that dependency is stated and marked unproved. (_sessions_: "don't reference
  other proofs", "you did not define the open-cone theorem")
- **One change at a time, said out loud.** A changed theorem, plan or
  notation is announced with what changed and why. (_sessions_: "why change
  the theorems all of a sudden?")
- **Time is theirs.** Ask how long they have when it is unclear, and size the
  work to it; a short session is a smaller goal, not a faster pace.
  (_sessions_: "maybe we can make a shorter session")
- **Bookkeeping stays out of the way.** Recording costs at most one line in
  the reply ("Recorded: register-buffer hard, module-list good").
- **The skills read the model's numbers, not labels.** What an agent gets is
  the idea, its answers, its R now, and the path of ideas to a goal. It decides
  from those and the task, every time; no skill sorts ideas into states or
  modes on top of the model (principle: output raw R, not verdicts).
- **Who the learner is lives in their profile**, never in a skill:
  background, how they answer (paper, tablet, voice), notation, where their
  notes are, usual session length. Every skill reads it once per session.

## The memory skill: small, loaded by every session

Renamed from `reader-brief` to the tool's name. Its job: let any agent, in any
task, find out whether the learner holds what the next step leans on, and ask
when it is not settled. It is read by almost every session, so the main file
stays under about 700 words; what is needed only sometimes is one link away.

**`SKILL.md`** (always read):

1. The model in six lines: idea (name, kind, area), edges (needs, uses),
   evidence (answers and observed work only), R, depth.
2. **The check**: `context <terms>` → decide from R and how much the step
   leans on the idea → ask what is unsettled → pitch at what they showed.
   A step the argument runs through needs a high recent R; a misconception is
   repaired first; no R means unknown, not absent; a tool idea (`tools/…`) is
   cheap to name, a concept is not.
3. **Asking**: one question block, piped to `ask`, copied verbatim into the
   reply; the reply passed to `answer`. The format lives in `ask -h`.
4. **Recording** observed work in pairing: one `observed` call.
5. **Adding**: when the task leans on an idea with no entry, add it (the four
   tests and the edge rules in `ideas.md`).

**Loaded only when needed:** `questions.md` (writing good items, grading,
retract, redo, regrade), `ideas.md` (the four tests, needs and uses, closest
edge, areas, add, edit, rm), `upkeep.md` (daily upkeep, the notes folder, the
scout).

**The CLI's help carries the formats** (`ask -h` prints the block format with
an example, `add -h` the idea block), so the skill and the code cannot drift.

## `learn`

A lesson moves the learner from what they hold to a goal, one checked step at
a time. The skeleton stays (goal, route, sweep, plan, teach, close). v1 sharpens
three things: how much each step teaches, how earlier steps come back, and how
the goal is checked.

### The route

- The route is the path of ideas from the goal down, along needs edges, to
  ideas they hold, reusing what `context` finds and adding what is missing.
  The agent reads each idea's R and last answer and decides from those and the
  goal what to teach, what to re-ask and what to build on: an idea answered
  well long ago with R now low gets a question, not a lesson; one never
  answered gets a probe; a confident wrong last answer is repaired first.
- The next step is one whose needs they hold or were just taught: the edge of
  what they know (Doignon & Falmagne's knowledge spaces; Skycak's "knowledge
  frontier"). No step rests on something unshown.
- Every term the goal uses is a definition on the route; every theorem is
  proved in the lesson or declared a dependency (stated, marked unproved).
- **A step is done when its check is right**, not when it has been explained
  (mastery learning: Bloom 1984; Kulik et al. 1990).

### The step

1. **Teach, sized to what they hold.** This is the goldilocks rule made
   concrete. A new idea gets a full worked derivation with its steps labelled.
   An idea whose parts they hold gets a completion: the skeleton, with the key
   step left to them. What they hold gets a sentence and a link. Help a
   beginner needs costs someone who already knows the area (worked examples and
   fading: Renkl & Atkinson 2003; expertise reversal: Kalyuga et al. 2003).
2. **Explain back.** One "why does this hold / what breaks if…" item tied to
   a named idea they hold (self-explanation: Chi et al. 1994).
3. **Check.** Two to four items: the new idea applied to a fresh case, its
   proof idea when the goal is about proofs, and one earlier idea (below).
4. **Repair.** A confident wrong answer is the best moment to teach (the
   hypercorrection effect: Butterfield & Metcalfe 2001): name the belief
   behind it, show why it fails on a contrasting case, give the right idea,
   and re-ask it later in the lesson with a new item (refutation: Kendeou &
   O'Brien 2014).

**When they are stuck**, the hint is the smallest step that their own held
ideas can bridge: name the idea they hold that unlocks it ("this is the
tower property again"). If what is missing is not something they hold, it is
not a hint but a gap, and it gets taught. No chain of tiny hops (the
assistance dilemma: Koedinger & Aleven 2007).

### Earlier steps come back (open)

Retrieving an idea again after other material came between is what makes it
stick, and a quick right answer straight after teaching is weak evidence
(interleaving and spacing within a session: Rohrer & Taylor 2007; Karpicke &
Roediger 2007; fluency illusions: Bjork, Dunlosky & Kornell 2013).

The model cannot pick which idea comes back within a lesson: one good answer
gives a stability of about 2.3 days, so R is .997 an hour later and .99 after
three hours. Any rule built on R inside a session is noise. The proposal is to
let the graph do it instead:

- **Checks compose.** A check item on step k is a case where the new idea has
  to be used together with earlier steps it rests on (its needs and uses
  edges), so earlier ideas are retrieved because the case requires them, not
  because a rule says so. The item is tagged with the new idea.
- **The goal block composes everything**, at the end, after the whole lesson
  came between: each step is retrieved by the case, and items on the steps
  whose only answer was given straight after teaching record that later
  evidence.

### Attempting first

Not a separate turn: a prediction at the start of a step stops the flow for a
question they cannot answer yet (pretesting helps: Richland, Kornell & Kao
2009; Kapur 2008; but it costs a full turn here). When it fits, the last item
of a step's check block asks about the next step before it is taught: rare,
only where they can reason most of the way there. Its answer is recorded with
a `before teaching` marker: the memory model skips it, and it stays as data,
for instance to fit an idea's starting difficulty later (principle 12).

### Depth

Route ideas are checked at **use**. The goal is checked at **transfer**: a
case that looks different but has the same structure, where nothing names the
idea (comparing two cases is what produces transfer: Gentner, Loewenstein &
Thompson 2003).

### Across sessions

A lesson that does not finish writes `LESSON.md` in the working folder: the
goal, the route, and "step k of N". The next session opens with the route's
lowest-R ideas, then continues. The route can always be rebuilt from the
model; the file only keeps the agreed goal and order.

### Close

A final block on the goal at transfer depth that also re-asks each step;
the route's coverage in one line ("route: 9 ideas, all asked, mean R .8"); the
results worth a note, for them to write.

## `pair`: learning while building

Moves into the repo from the personal skills. What works stays: strong style
(every idea reaches the code through the driver's hands), altitude and fading,
briefs with verified materials, ping-pong tests, the confidence zone, the
parking lot, the driver's call.

### API pieces are handed over, and stick by use

The API calls a step needs are part of its **materials**: here are the five
pieces (`register_buffer`, `masked_fill`, …) with signatures and a one-line
example; build the step out of them. Using them is what teaches them. Nobody
quizzes a signature, and looking something up is a skill, not a gap
(API learning is blocked mostly by missing examples: Robillard 2009;
Duala-Ekoko & Robillard 2012).

Each step that lands records the pieces it used as observed work. As a piece
gets used again and again its R climbs, and once the model says it is well
held, it drops out of the materials: the driver reaches for it alone. If they
stall on it, it comes back. Fading is the model's job, not a schedule's.

### Concepts get the learn structure, at the depth the code needs

When a step implements an idea (an architecture, an algorithm, a loss), the
driver needs to understand why it works: intuitively, enough to write the
code and know what breaks it. When that idea's R does not settle it, the
step opens with a short lesson from `learn`: taught at the size of what they
hold, explained back, checked. Then the brief.

That understanding is not mental execution: no prediction that means running
fifty steps of an algorithm in one's head. A quick prediction (a shape, a
sign, which way a loss moves) is fine when it is cheap and the answer teaches
something; it is not the centre of the session.

### What else the session does

- **After a step done with real help, one "why does it work" question.** In a
  2026 randomised trial, people learning a new library with AI help learned
  less, except those who asked conceptual questions as they went (Anthropic,
  arXiv 2601.20245).
- **Never the finished line for an untried step**, and never a useless hop
  either: the hint is the smallest piece their held ideas can turn into the
  line; a real gap gets taught (guarded hints: Bastani et al., PNAS 2025;
  CodeAid: Kazemitabaar et al. 2024).
- **Tests are a contract.** Fixed inputs or seeds, green against a throwaway
  reference implementation before handing over, and every test expected to be
  red named as such. (_sessions_: a colliding random test; "one test failing,
  did you forget that?")
- **Close** with a short block on the concepts the session leaned on, and a
  commit point.

The skill can be invoked from plain language ("let's pair on…"), since
`/pair` "didn't trigger from plain language" (_sessions_).

## The repo is for anyone

- **AGENTS.md** gets the rule, since that is what agents editing the repo
  follow: nothing in the code or in `skills/` names a person, a path or a
  personal tool. Personal setup lives in the model folder (`profile.md`,
  `config.toml`); personal skills live outside the repo and call these.
- **README** gets who it is for, installing the CLI, linking the skills into
  the agent's skills folder, and writing a profile.
- **PHILOSOPHY.md** keeps the reason in one line.
- **`init`** writes a profile template with the sections the skills read:
  background, how they answer, notation, notes folder, session length.
- The skills drop every personal reference (aissay and paiper in the brief,
  `~/labvault` in pair). The notes folder stays a generic, optional feature.

## Testing before use

Each skill is run against a simulated learner (an agent with a written
profile and a hidden list of what it knows and its misconceptions) on a
throwaway model folder. A run passes when the skill was followed: blocks in
the reply, terms defined, steps checked before building on them, answers
recorded with the right ideas and depths, turns within budget. Only skills
that pass reach the live install.

## Open

1. The name (`ken`, `engram`, `grasp`, or another).
2. How earlier steps come back (checks compose, above).
3. `LESSON.md` in the working folder for lessons that span sessions.
4. Publishing: public repo and licence (only changes the README).
