---
name: reader-brief
description:
  "What the reader (the person you work with) has shown they know, as recall
  probabilities, and the one way to ask them. Use whenever an explanation, lesson, essay, paper or step of
  shared work leans on an idea they may not hold: look it up, and ask what the
  lookup does not settle, before pitching it at their level."
---

# Reader brief

The reader is the person you are working with. `reader profile` says who they
are and how they like to answer; read it once per session. Pitch everything at
the **goldilocks** level: each new idea sits one reasoning step from something
they hold, and what they hold gets a sentence and a link, not a re-derivation.
Learn what they hold by looking it up, and ask when the lookup does not settle
it.

## The model

- An **idea** is one named unit of knowledge they could hold or lack on its
  own, and that one short question can check. Its **name** (kebab-case, unique)
  is what you type everywhere; its statement is a reference you check answers
  against. Each idea is one **kind**: a *definition*, a *result* (a theorem, a
  property, how an API behaves), a *proof* (why a result holds: a proof, a
  derivation, an argument), or a *method* (an algorithm, a technique, a code
  pattern).
- Every idea lives in one **area**, a path in a tree (`maths/analysis`,
  `tools/pytorch`). Areas are for finding ideas and for **coverage**: how many
  ideas an area has and how many were ever asked.
- An **edge** from X to Y carries **needs** (they cannot follow X's statement
  without Y), **uses** (answering or doing X makes them carry Y out), or both.
- **Evidence** is an answer to a question you asked, or a step of pairing work
  they typed and a test verified (see Observed work), about one idea. Nothing
  else counts: what they said in passing, what you taught, what they say they
  know and what they wrote in their notes move no number.
- A **memory model** turns each idea's answers into **R**, the probability they
  recall it now (FSRS-6 on elapsed time, so R falls within a day too). An
  answer updates only the idea it is about: nothing propagates along edges.
  A wrong last answer holds R at 0 until a right one. No answers means no R:
  unknown, not zero.
- Each answer records the **depth** its question demanded: *state* it, *use*
  it when it is named (the default), or *transfer* it where nothing points to
  it.

The model lives in `$READER_HOME` (default `~/.local/share/reader/`). Read and
write it only through `reader` (`reader -h` lists the commands).

## The check

Use this whenever something you are about to say or do leans on an idea they
may not hold. It is also how every brief is built.

1. **Look up**: `reader context <what>`, comma-separated. Each term is tried as
   an idea name (or alias, or id), then an area, then text.
   - An **idea** shows its statement, R, answers and last grade, the deepest
     depth answered right, and its neighbours one step each way (needs, uses,
     needed by, used by), each with its R.
   - An **area** lists its ideas with R, and its sub-areas folded with their
     coverage. When the conversation moves to a new subject, look up its area
     first.
   - A **term** with no idea of that name lists the ideas that mention it, or,
     when nothing does, the nearest names and how well covered that region is.
     When a vault (a folder of their notes) is configured, notes on the term
     are listed as hints.
   - No argument shows the top of the tree with coverage per area.
2. **Decide** from R and the task. How sure you need to be depends on how much
   the next step leans on the idea: something the argument runs through needs
   a high, recent R, and a side remark needs none. The R of what an idea needs
   tells you whether they could rebuild it if forgotten. A misconception in the
   last answer is repaired before anything rests on it. An idea in a tool area
   (`tools/…`) is cheap to name in passing; a concept is not. A question costs
   them a moment; a pitch at the wrong level costs the conversation.
3. **Ask** what the lookup does not settle, as one question block (below). An
   idea with no entry yet: add it (see Ideas), then ask.
4. **Pitch** the next step at what they showed. Their answer is already
   recorded.

Most of what they know has no evidence yet: that calls for a question, not an
assumption that they lack it.

## A brief

A brief is the check run on everything a piece rests on: an aissay, paiper,
lesson or pair session.

1. `reader context <area>, <topic>, <key result>`. For each vault note it
   lists that the piece leans on, read the note, add its ideas, and look up
   again.
2. List the ideas the piece needs. Ask about every one the lookup does not
   settle, in blocks, hardest first. A confident right answer at the top tells
   you where they stand, but it records nothing about the ideas below it: an
   idea the piece leans on gets its own answer.
3. Show them the brief. For each idea give its name, R (or none), last date,
   and how the piece treats it: used with a link, recalled in a sentence, or
   taught. Then list their answers. Their correction is final for this piece
   and goes into its `BRIEF.md`. It enters the model only through a question
   they answer.

When the main idea needs more than one new idea in a row beneath it, say so
and propose a smaller target or a piece about the missing step itself.

## Questions

Every question put to them is a **question block**: numbered items, answered
in one line. A check, a brief, and a lesson's probe, prediction and check all
use it. There are three kinds of item:

- **pick**: multiple choice, answered with a letter and a confidence digit
  (`2b8`: option b, 80% sure). The default: the quickest to answer.
- **write**: they write it on paper or a tablet and compare it with the reference
  you then show (`3.` when done, then `3=`, `3~` or `3x`). For formulas and
  short derivations they want in their hands.
- **say**: one free line, typed or dictated, for a why or a prediction a pick
  cannot hold.

Write the block and pipe it into `reader ask`. It stores the block with its key
under a new id (`q_…`), shuffles the options, and prints the block. They never
see tool output: copy the printed block into your reply verbatim.

```
reader ask <<'EOF'
# girsanov
1 pick girsanov: Under $Q$ with $dQ/dP = \exp(\theta W_T - \tfrac12\theta^2 T)$, the process $W_t - \theta t$ is
  * a $Q$-Brownian motion
  - a $Q$-martingale but not a Brownian motion :: thinks Girsanov keeps only the martingale property
  - a $P$-Brownian motion
  ? Under $Q$ the shifted process is a Brownian motion: drift removed, quadratic variation kept.
2 write ito-formula state: Itô's formula for $f(t, X_t)$, $X$ an Itô process.
  = $df = \partial_t f\,dt + \partial_x f\,dX_t + \tfrac12 \partial_{xx} f\,d\langle X \rangle_t$
3 say girsanov-proof: In one line, where does the drift $-\theta$ come from?
  = Itô on $Z_t = \exp(\theta W_t - \tfrac12\theta^2 t)$ gives $dZ = \theta Z\,dW$; under $Q$ that shifts $W$ by $\theta\,dt$.
EOF
```

`*` marks the right option and `-` the others. `::` names the misconception a
confident pick of that option reveals. `?` is the explanation and `=` the
reference.

- Tag each item with the idea it tests, by name, and with the depth it demands
  when that is not `use`: `state` to recall it, `transfer` to reach for it
  where nothing points to it. Ask why a result holds through its proof idea.
- Each item stands alone: every term in it is defined in the item or was
  defined earlier in the conversation, in the reader's notation, unless
  recalling that definition is what the item tests.
- Options are bare claims of the same length and register. Write the right one
  first, then turn it into each wrong one: the answer someone holding a
  specific wrong model would give. Every wrong option is false outright, never
  a weaker form of the right one (if the right one says $=$, $\le$ is not a
  wrong option).
- Solve the item yourself, from the definitions as stated, before asking.
- Prefer an item that applies an idea to one that recites it.
- At most six items per block. A lesson's prediction is one item, its check
  two to four.

Pass a reply in the format on as typed: `reader answer <q_id> "<reply>"`. It
grades picks and writes, prints a verdict per item, and records each answer at
once. The parser reads input from agents: a reply outside the format ("between
a and b", a letter without a digit, two letters) is yours to settle first. Ask
what they meant, or put the reading you would record to them in the format,
and pass that on. Grade each say item against its reference in the same call
or a later one: `reader answer <q_id> --say 3=good` (good, hard or again), with
`--mis "believed X → Y"` for a misconception. Then answer every ✗ in prose: the
right answer and, for a misconception, why the wrong one tempts.

Grades: again (wrong or blank), hard (right with effort or a slip), good (right
and clean), easy (right and carried to a new setting). A right pick at chance
confidence is a guess, which is recorded but carries no grade.

An answer that does not count (they misread the question, misclicked, or the
item itself was wrong) is set aside, not edited:
`reader answer <q_id> --retract 2 --why "<reason>"` moves it to `archive.md` and
opens the item again, so a corrected reply goes through `reader answer`. To
answer a finished item again, add `--redo`; to change a grade, `--regrade 2=hard`.
The old answer is archived either way.

## Observed work

In pairing, a step the driver typed and its tests turned green is evidence for
the ideas it exercised. Record it in one call, after the tests pass:

```
reader observed register-buffer=hard tensor-broadcasting=good --step "3 · causal head" \
  --note "register-buffer: needed the device demo"
```

Grade each idea by the help the step took:

- **good**: done clean from the brief. The brief's own materials are normal,
  not help.
- **hard**: needed help beyond the brief (a refresher, a pointer to a failure),
  or had a slip.
- **again**: handed the answer.

An idea you taught within the same step gets no grade: typing it straight
after the explanation is not recall.

## Ideas

Look up before adding: `reader context <name or terms>`, and reuse what exists.
Add an idea when the task leans on one that has no entry, not in advance.
Decide what one idea is with four tests:

1. **It has a name** a colleague would use, in a few words, with no "and".
2. **It can be known alone.** If they could plausibly hold one part and lack
   the other, the parts are two ideas. A named theorem keeps its name for its
   main claim; other parts get names of their own. When it is unclear, keep it
   whole: when answers show them getting one part and missing the other, add
   the part as its own idea and give the whole a needs edge to it.
3. **One short question can check it**, and a right answer is good evidence for
   all of it.
4. **It does not contain other ideas.** A result does not restate the
   definitions it uses; it has an edge to them. Why a result holds is a
   separate proof idea.

For each edge ask both questions, separately, and write the edge with every
mark that passes: can they follow X's statement without Y (if not: needs)?
does answering or doing X make them carry Y out (if so: uses)? Definitions and
results mostly only need; proofs and methods use what they carry out, and often
need it too. A result that seems to use something usually means its proof is
missing. Write only the closest edge: if X needs Y and Y needs Z, X gets no
edge to Z for that reason. Teaching order is not an edge.

Add ideas through stdin, so no shell ever sees the statement:

```
reader add <<'EOF'
## banach-fixed-point · result · maths/analysis
A contraction $g$ (constant $q<1$) on a complete metric space has exactly one
fixed point, and the iteration $x_{k+1}=g(x_k)$ converges to it from any start.
- needs: contraction, complete-metric-space
- aliases: Banach fixed point theorem, contraction mapping theorem
- vault: 0ezzzp

## banach-fixed-point-proof · proof · maths/analysis
The iterates are Cauchy by the geometric tail bound, so they converge by
completeness; continuity makes the limit fixed; $q<1$ forces uniqueness.
- needs: banach-fixed-point
- uses: geometric-tail-bound
EOF
```

Each block is `## name · kind · area`, the statement, then the optional lines
`- needs:`, `- uses:`, `- aliases:`, `- vault:` (link the vault note when one
exists). It prints each new id and the area's size. It refuses, and shows what
it found, when a name or a close statement already exists (`--anyway` adds it
regardless), an edge names an idea that does not exist (add that one first, in
the same input if you like), the area does not exist (`--new-area` makes it:
choose the most specific existing area where a colleague would look first, and
make a new one only when several ideas will live there), or an edge would
close a cycle.

Fix a mistake rather than living with it:

```
reader edit <name> --needs +a,-b --uses +c       # add and remove edges
reader edit <name> --name new-name               # its edges follow the rename
reader edit a,b,c --area maths/topology --new-area   # move ideas; unfold a sub-area
reader edit <name> <<'EOF'                       # reword the statement
…
EOF
reader rm <name> --why "<reason>"                # its answers move to archive.md
```

Reword freely as long as a past right answer would still be right; a different
claim is a new idea. `rm` refuses while another idea needs or uses it.

## Upkeep

Run `reader upkeep` daily, e.g. as a scheduled task. It checks the model,
commits it to its git repo (and pushes, when it has a remote), lists likely
duplicates and areas worth splitting (over about 40 ideas, or a cluster of
ideas linked only to each other), and shows how well their confidence digits
are calibrated. With a vault, it lists finished notes that have no idea yet;
with `--scout` and a configured scout model, a cheap model drafts ideas for
them into `proposals.md`. When they approve drafts, check each against its
note, add it with `reader add`, and end its `##` header in `proposals.md` with
`· added` or `· skipped`. `reader upkeep --check` only checks.
