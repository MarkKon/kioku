# reader v1: files and commands

A spec to agree on before code. The model itself (ideas, areas, edges, depth)
is in `PHILOSOPHY.md` ("The model, and why") and `GLOSSARY.md`; this page is
only how it is stored and how agents reach it.

Three aims, each from a v0 failure:

- **One format everywhere.** An idea looks the same in its file, in `add`, in
  `edit` and in what `context` prints. Statements go in through stdin, so
  `$`, apostrophes and `=>` never meet the shell (v0 broke on all three).
- **Lookups that stay small.** `context` shows a region, not the whole model,
  and a miss says how sure it is.
- **One call per act.** Asking, answering, grading, retracting and recording
  observed work were 3 to 5 calls each in pairing, with four slips in one
  session.

## The model folder

```
profile.md                  who the reader is (unchanged)
config.toml                 settings (unchanged)
areas/                      the area tree, as folders and files
  maths/
    analysis.md             ideas whose home is maths/analysis
    analysis/
      metric-spaces.md      ideas whose home is maths/analysis/metric-spaces
  tools/
    pytorch.md
evidence.md                 one answer per line, append-only (format below)
asks/                       every question block, as JSON (unchanged)
archive.md                  evidence set aside (unchanged)
```

An area is a path; its ideas live in `<path>.md`. The tree opens as-is in
Obsidian. Each area file is a list of ideas:

```markdown
## banach-fixed-point · result · p_nuv7
A contraction $g$ (constant $q<1$) on a complete metric space $X$ has exactly
one fixed point $x^*$, and the iteration $x_{k+1}=g(x_k)$ converges to it from
every $x_0$.
- needs: contraction, complete-metric-space
- aliases: Banach fixed point theorem, contraction mapping theorem
- vault: 0ezzzp

## banach-fixed-point-proof · proof · c_ktug
The iterates are Cauchy by the geometric tail bound, so they converge by
completeness; continuity of $g$ makes the limit fixed; $q<1$ forces two fixed
points to coincide.
- needs: banach-fixed-point
- uses: geometric-tail-bound, cauchy-sequence
```

- The header is `name · kind · id`. The **name** is unique across the whole
  model and is what agents type everywhere. The **id** never changes and is what
  evidence lines refer to, so a rename touches one header and the edges that
  name it, never the evidence. v0 ids are kept; new ideas get `i_…`.
- The statement is the paragraph under the header.
- `needs:` and `uses:` list the names this idea has edges to. An edge with both
  marks appears in both lists. Reverse edges are computed, never stored.
- `aliases:` and `vault:` are optional. Nothing else is stored on an idea.

Evidence keeps its line, with two changes: the depth the question demanded,
and `observed` as a kind of its own (v0 recorded observed work as `say`).

```
- 2026-11-08T18:02 p_nuv7 pick good 8 use q_yvuh/1 — picked …
- 2026-11-07T19:19 p_344t observed hard use q_rjvc/2 — needed the device demo for register_buffer
```

Depth is `state`, `use` or `transfer`; old lines have none, which reads as
unknown.

## Commands

Nine verbs, plus `init` and `profile`. Everywhere an idea is named, its name,
an alias or its id works; several are comma-separated.

| v1 | does | replaces (v0) |
| -- | ---- | ------------- |
| `context <what>` | look up an area, ideas or terms | `check`, `find`, `show`, `status` |
| `add` | add ideas (stdin) | `new prop`, `new chain` |
| `edit <name>` | change an idea or its edges | `amend` |
| `rm <name> --why` | remove an idea; answers to the archive | `delete` |
| `ask` | store a question block (stdin), print it | `ask` |
| `answer <q> "<reply>"` | grade, regrade, retract, redo | `answer`, `grade`, `retract` |
| `observed` | record a step of verified work in one call | say-block workaround |
| `graph [what]` | the graph page | `graph` |
| `upkeep` | lint, backup, duplicates, calibration, scout | `upkeep`, `lint`, `dupes`, `calib`, `scout` |

### `reader context`

The main call, and the one an agent makes whenever the conversation moves to a
new subject. (The outputs below are mock-ups; the numbers are not real data.) It takes an area, idea names or free terms, and tries them in that
order: exact idea name or id, area path or last segment, alias, statement text.

An area shows its ideas and its sub-areas folded:

```
$ reader context maths/analysis/metric-spaces
maths/analysis/metric-spaces · 7 ideas · 5 asked · last 11-03 · R = recall now, – = never asked
  contraction               definition  R .91  n2  11-03 good   use
  banach-fixed-point        result      R .62  n3  11-03 hard   use
  banach-fixed-point-proof  proof       R –    n0
  a-priori-estimate         result      R .40  n1  11-02 hard   state
  …
  fixed-points/             4 ideas · 1 asked · last 11-02
```

Columns: name, kind, R, number of answers, date and grade of the last one, and
the deepest depth answered right. No statements, so a 40-idea area still fits
in a screen.

An idea shows its statement and its neighbours, one step each way:

```
$ reader context banach-fixed-point
banach-fixed-point · result · maths/analysis/metric-spaces · R .62 n3 · last 11-03 hard (use)
  A contraction $g$ (constant $q<1$) on a complete metric space …
  needs   contraction               R .91  n2  11-03 good
          complete-metric-space     R –    n0
  needed by  banach-fixed-point-proof   R –   n0
  used by    picard-lindelof            R .30 n1  11-02 again
  last answer: picked the right bound but not the iteration's start · q_w81k/2
```

`--answers` adds every answer with the question it answered (v0 `show`).

A miss says where it looked and how full that region is:

```
$ reader context novikov
no idea, alias or statement matches "novikov" (412 ideas searched)
  nearest name: girsanov · maths/probability/stochastic-calculus · R .70
  maths/probability/stochastic-calculus · 31 ideas · 24 asked · last 11-07
```

With no argument, `context` prints the top of the tree with coverage per area
(v0 `status`).

### `reader add` and `reader edit`

`add` reads one or more ideas from stdin, in the file format plus the area:

```
reader add <<'EOF'
## banach-fixed-point · result · maths/analysis/metric-spaces
A contraction $g$ …
- needs: contraction, complete-metric-space
EOF
```

It prints each new id, and refuses, printing what it found, when:

- a name, an alias or a close statement already exists (`--anyway` adds it
  regardless);
- a `needs` or `uses` name does not exist (add that idea first, or drop the
  edge);
- the area does not exist (`--new-area` makes it: a new area is a choice, not a
  typo);
- an edge would close a cycle.

`edit <name>` takes flags for small changes and stdin for a new statement:

```
reader edit banach-fixed-point --uses +geometric-tail-bound --needs -metric-space
reader edit banach-fixed-point --name banach-fixed-point-theorem --area maths/analysis
reader edit banach-fixed-point <<'EOF'
A contraction on a complete metric space has exactly one fixed point …
EOF
```

`edit` takes several names, comma-separated, for moves. `--needs` and
`--uses` take `+name` and `-name` entries; `--aliases` replaces the list. A rename rewrites every edge that names the idea. There is no
`--force`: rewording is allowed as long as a past right answer would still be
right (PHILOSOPHY), and a different claim is a new idea. Splitting an idea, when
answers show its parts coming apart, is an `add` of the part and an `edit` of
the whole (`--needs +part`); the whole keeps its answers.

### Growing and folding areas

An area is nothing but where its ideas live, so changing the tree moves ideas
and nothing else: evidence points at ids, edges at names, and coverage is
recomputed.

- **Unfold** a sub-theme that has grown: `reader edit a,b,c --area
  maths/topology --new-area`. The ideas are found by `context topology`, which
  searches statements, even with no area of that name.
- **When**: an agent adding the fifth or so idea on a sub-theme makes the area
  (`add` prints the target area's size), and `upkeep` lists areas over about 40
  ideas and clusters of about 5 ideas in one area that are linked mostly to
  each other.
- **Fold** an area back by moving its ideas to the parent; an empty area's file
  is removed.

### `reader ask` and `reader answer`

`ask` is v0's block format, with each item tagged by idea name and,
optionally, depth (default `use`):

```
1 pick banach-fixed-point use: Let $g(x)=x/2+1$ on $\mathbb R$. The iteration from $x_0=0$ …
  * converges to 2
  - diverges :: thinks a contraction needs a bounded domain
```

`answer` takes the reply and grades it in one call. What v0 needed `grade` and
`retract` for are flags on it:

```
reader answer q_x "1b8 2= 3: because the drift cancels"
reader answer q_x "…" --say 3=good           # grade a say item in the same call
reader answer q_x --regrade 2=hard --mis "believed X → Y"
reader answer q_x --retract 1 --why "misread the question"
reader answer q_x "1a7" --redo
```

A say item left ungraded is listed in the output as waiting, so it is not
lost.

### `reader observed`

One call per step of verified pairing work, no block:

```
reader observed --step "3 · causal head" register-buffer=hard tensor-broadcasting=good \
  --note "register-buffer: needed the device demo"
```

It writes a record in `asks/` (so every answer still traces to something) and
one evidence line per idea, kind `observed`, depth `use`.

## Migration

A script, run on a copy of the model folder, then checked before the switch.

1. **Propositions become ideas one to one**, keeping name, id, statement,
   aliases and vault. No splitting during migration: an idea is split later,
   when answers show its parts coming apart.
2. **Chains:**
   - one that has answers becomes a proof idea under its own id, so its answers
     stay attached;
   - one without answers becomes a proof idea if its step is a derivation;
   - edges only, if it assembles a method or definition from parts;
   - dropped, if it only recorded teaching order.
3. **Kind, area and edge marks need judgement.** An agent proposes them per
   v0 area into a table, `migration.md` (old id → name, kind, area, needs,
   uses, chain verdict). You review it, at least for one area, and the script
   applies it. The script checks that every v0 id is covered, every edge
   resolves, and nothing forms a cycle.
4. **Areas:** the starting tree below, approved 2026-11-08. A v0 topic too
   small for an area folds into its neighbour; projects get an area only for
   facts about the project itself (`projects/<project>`), and a topic like
   `llm-pair` sends its ideas to their subjects.
5. **Evidence:** ids stay valid (propositions and answered chains keep theirs).
   Lines whose note starts with `observed:` become kind `observed`. No depth is
   invented for old lines.
6. **The switch:** the old folder is kept as `reader-v0/` beside the new one.
   Code and skills merge in one commit, which the editable install and the
   skill symlinks pick up at once.

## Starting tree

```
maths/analysis                         analysis, differentiation, topology
maths/differential-equations           differential-equations, flow maps
maths/probability                      probability
maths/probability/stochastic-calculus  stochastic-calculus, sde
maths/geometry                         sphere, geometry, convex-geometry
maths/optimisation                     linear-programming, optimisation
maths/discrepancy-theory               discrepancy-theory
maths/discrepancy-theory/ordering-types
maths/discrepancy-theory/inverse-discrepancy
maths/discrepancy-theory/spherical     discrepancy with sphere
ml/transformers
ml/language-modeling                   language-modeling, tokenization
ml/training
ml/generative-models                   generative-models, denoising, flow matching
learning-science
learning-science/spaced-repetition     spaced-repetition, fsrs
tools/pytorch
tools/python
science/nmr
projects/<project>
```

## Left out on purpose

- Graph inference of any kind (principle 12): the memory model still reads one
  idea's answers.
- Learning versus retention, and the skill redesign: after the switch.
- A redesign of `ask` and `answer` (the question-block format, how replies are
  given and graded). v1 keeps v0's, with the flags above, until then.
- A database: plain files still fit (principle 11).
