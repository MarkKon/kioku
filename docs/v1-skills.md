# v1 skills: reader, learn, pair

Proposal, 2026-11-09. The knowledge model is settled (`PHILOSOPHY.md`, "The
model, and why"). This is the shape of the three skills built on it, the
evidence behind each rule, and how the repo becomes usable by anyone.

Sources: the learning-science and programming-education literature
(summaries in the session's research notes; each rule below names its source),
and the past lesson and pairing sessions (quoted as _sessions_).

## What all three share

These come from what went wrong in past sessions, and hold in every skill:

- **Everything the reader should see is in the reply text.** Question blocks,
  lesson text, proofs. Tool output is invisible to them. (_sessions_: "i cant
  see a question", "where did you send the text?")
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
- **Who the reader is lives in their profile**, never in the skill: background,
  how they answer (paper, tablet, voice), notation, where their notes are,
  usual session length. Every skill reads `reader profile` once per session.

## `reader`: small, loaded by every session

Renamed from `reader-brief`. Its job: let any agent, in any task, find out
whether the person holds what the next step leans on, and ask when it is not
settled. It is read by almost every session, so the main file stays under
about 700 words; everything needed only sometimes is one link away.

**`skills/reader/SKILL.md`** (always read):

1. The model in six lines: idea (name, kind, area), edges (needs, uses),
   evidence (answers and observed work only), R, depth.
2. **The check**: `reader context <terms>` → decide from R and how much the
   step leans on the idea → ask what is unsettled → pitch at what they showed.
   Decision rules: a step the argument runs through needs a high recent R; a
   misconception is repaired first; no R means unknown, not absent; a tool
   idea (`tools/…`) is cheap to name, a concept is not.
3. **Asking**: one question block, piped to `reader ask`, copied verbatim into
   the reply; the reply passed to `reader answer`. The format lives in
   `reader ask -h`, not in the skill.
4. **Recording** observed work in pairing: one `reader observed` call.
5. **Adding**: when the task leans on an idea with no entry, add it (four
   tests and the edge rules in `ideas.md`).

**Loaded only when needed:**

- `questions.md`: writing good items (options as specific wrong models,
  standalone items, solve it first), grading, retract/redo/regrade.
- `ideas.md`: the four tests, needs vs uses, closest edge, areas, `add`/`edit`/`rm`.
- `upkeep.md`: the daily upkeep, the notes folder and the scout.

**CLI help carries the formats** (`reader ask -h` prints the block format with
an example, `reader add -h` the idea block), so the skill and the code cannot
drift apart.

## `learn`: a lesson built from what the evidence supports

A lesson moves the reader from what they hold to a goal, one checked step at a
time. The current skill has the right skeleton (goal, route, sweep, plan,
teach, close); v1 makes each part do what the evidence says works, and makes
"learning new" and "recalling old" two explicit cases of one loop.

### Every idea on the route is in one of five states

After the sweep, each idea on the route is one of these, and that decides
what the lesson does with it:

| state | from | the lesson |
|---|---|---|
| **held** | right answer at the target depth, R high | builds on it; one sentence and a link |
| **fading** | answered right before, R now low | one retrieval item, no re-teaching unless it fails |
| **misconception** | last answer a confident wrong one | repaired before anything rests on it |
| **unseen** | no answers | probed in the sweep, then held or gap |
| **gap** | probed, not held | becomes a step |

A lesson that is mostly *fading* is a **refresher**: retrieval first, teaching
only where an item fails. One mostly of *gaps* is new learning. The same
skill runs both; the plan says which it is. (Retrieval practice: Roediger &
Karpicke 2006; Dunlosky et al. 2013.)

### The route and its order

- The route is every idea from the goal down to held ones, along needs edges,
  reusing what `reader context` finds and adding what is missing.
- The next step is always one whose needs are all held or already taught: the
  outer fringe of what they know (Doignon & Falmagne's knowledge spaces;
  Skycak's "knowledge frontier"). No step rests on a gap.
- Every term the goal uses is a definition on the route; every theorem is
  proved in the lesson or declared a dependency (stated, marked unproved).
- **Mastery gate**: a step is done when its check is right at its target
  depth, not when it has been explained. (Bloom 1984; Kulik et al. 1990.)

### The step cycle

1. **Predict.** One item about the step before it is taught. Attempting first,
   even wrongly, makes the teaching stick better (pretesting: Richland, Kornell
   & Kao 2009; productive failure when they can partly reason it out: Kapur
   2008, Sinha & Kapur 2021).
2. **Teach, sized to what they hold.** A new idea gets a full worked
   derivation with its steps labelled. An idea they partly hold gets a
   completion: the skeleton, with the key step left to them. Help that a
   beginner needs costs someone who already knows the area (worked examples
   and fading: Renkl & Atkinson 2003; expertise reversal: Kalyuga et al. 2003).
3. **Explain back.** One "why does this hold / what breaks if…" item tied to
   a named prerequisite (self-explanation: Chi et al. 1994).
4. **Check.** Two to four items: the new idea applied to a fresh case, its
   proof idea if the goal is about proofs, and one item on an earlier step, so
   earlier steps are retrieved again after other material came between
   (interleaving and spacing within a session: Rohrer & Taylor 2007; Karpicke &
   Roediger 2007).
5. **Repair.** A confident wrong answer is the best moment to teach (the
   hypercorrection effect: Butterfield & Metcalfe 2001): name the belief
   behind it, say why it fails with a contrasting case, give the right idea,
   and re-ask it later in the lesson with a new item (refutation: Kendeou &
   O'Brien 2014).

**Hints** follow the assistance dilemma (Koedinger & Aleven 2007): one attempt
before any hint, then each hint one level more specific than the last.

### Depth

- Route ideas are checked at **use** (applied when named).
- The goal is checked at **transfer**: a second case that looks different but
  has the same structure, where nothing names the idea. Comparing two cases is
  what produces transfer (Gentner, Loewenstein & Thompson 2003).
- A quick right answer just after teaching is weak evidence (fluency
  illusions: Bjork, Dunlosky & Kornell 2013). The close re-asks every step
  once more, after the rest of the lesson came between.

### Across sessions

A lesson that does not finish writes `LESSON.md` in the working folder: the
goal, the route with each idea's state, and "step k of N". The next session
starts by retrieving the last session's steps, then continues. This needs no
new record in the reader: the route can always be rebuilt from the model.

### Close

A final block on the goal at transfer depth, re-asking each step once; then
the route's coverage in one line ("route: 9 ideas, all asked, 7 held"), and
the results worth a note in their notes folder, for them to write.

## `pair`: learning while building

Moves into the repo from `~/.agents/skills/pair`. What works stays: strong
style (every idea reaches the code through the driver's hands), altitude and
fading, briefs with verified materials, ping-pong tests, the confidence zone,
the parking lot, the driver's call. v1 adds an explicit split between two
kinds of knowledge, and turns pairing into a place where both are learned and
recorded.

### API knowledge and concepts are learned differently

The split already exists in the model: tool areas (`tools/pytorch`) hold API
ideas, the other areas hold concepts. Each gets its own treatment:

| | API (`tools/…`: `register_buffer`, broadcasting, `nn.ModuleList`) | concept (causal attention, a numerical scheme, a loss) |
|---|---|---|
| check before | none, usually: name it and give the signature and one example | ask when R does not settle it, before the step's brief |
| teach | the docs, one example, then they call it. Looking it up is a skill, not a gap | predict or derive it first; a worked example with named subgoals; a mini step from `learn` when it is a gap |
| evidence | `state`: picks the right call when it is offered; `use`: calls it unaided in a passing step | an answer at `use`, or a step that implements it; `transfer` when they reach for it unprompted |
| aim | `use`, and knowing where to look | `use`, and `transfer` for what the project rests on |

Sources: API learning is blocked mostly by missing examples, not by the API
(Robillard 2009; Duala-Ekoko & Robillard 2012); programming plans and subgoal
labels (Soloway 1986; Morrison, Margulieux & Guzdial 2015); predict-run-
investigate-modify-make (Sentance & Waite 2017).

### What changes in the session

- **Predict before run**, with a number: a shape, a loss, a count. The past
  pairing session named this the best part.
- **After a step done with help, one "why does it work" question.** In a 2026
  randomised trial, people learning a new library with AI help learned less,
  except those who asked conceptual questions as they went (Anthropic,
  arXiv 2601.20245). Unguided AI help raised practice scores and lowered exam
  scores; a tutor that gave graded hints did not (Bastani et al., PNAS 2025).
- **Never the finished line for an untried step**: the next hint, then the
  next (CodeAid: Kazemitabaar et al. 2024).
- **Tests are a contract.** Fixed inputs or seeds, green against a throwaway
  reference implementation before handing over, and every test expected to be
  red is named as such. (_sessions_: a colliding random test; "one test
  failing, did you forget that?")
- **Fading follows the model.** Full materials on first use of an idea, the
  brief alone once it shows held, the goal alone after that. An API element is
  never faded to "recall the signature": that fading "went too far once"
  (_sessions_).
- **Close with a short block** on the concepts the session leaned on, asked
  after the work (one more spaced retrieval), and a commit point.

The skill becomes invocable from plain language ("let's pair on…"), since
`/pair` "didn't trigger from plain language" (_sessions_).

## The repo is for anyone

- **AGENTS.md** gets the rule, since that is what agents editing the repo
  follow: nothing in the code or in `skills/` names a person, a path or a
  personal tool. Personal setup lives in the model folder (`profile.md`,
  `config.toml`); personal skills live outside the repo and call these.
- **README** gets "who it is for", installing the CLI (`uv tool install`),
  linking the skills into the agent's skills folder, and writing a profile.
- **PHILOSOPHY.md** keeps the reason in one line (an agent cannot know who it
  is talking to from the code).
- **`reader init`** writes a profile template with the sections the skills
  read: background, how they answer, notation, notes folder, session length.
- The skills drop every personal reference: aissay and paiper in the brief,
  `~/labvault` in pair. The notes folder stays as a generic, optional feature
  (`vault` in `config.toml`).

## Testing before use

Each skill is run against a simulated learner (an agent with a written
profile and a hidden list of what it knows and its misconceptions) on a
throwaway model folder. A run passes when the skill was followed: blocks in
the reply, terms defined, the mastery gate held, answers recorded with the
right ideas and depths, turns within budget. Only skills that pass reach the
live install.

## Open

1. Rename `reader-brief` to `reader`.
2. `LESSON.md` in the working folder for lessons that span sessions.
3. Publishing: public repo and licence (only changes the README).
4. `pair` invocable from plain language, not only `/pair`.
