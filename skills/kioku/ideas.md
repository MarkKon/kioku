# Ideas

The block format is in `kioku add -h`. This file is how to decide what one idea
is, which edges it gets, and where it lives.

## What one idea is

Four tests:

1. **It has a name** a colleague would use, in a few words, with no "and".
2. **It can be known alone.** If they could plausibly hold one part and lack
   the other, the parts are two ideas. A named theorem keeps its name for its
   main claim; other parts get names of their own. When it is unclear, keep it
   whole: when answers show them getting one part and missing the other, add
   the part as its own idea and give the whole a needs edge to it.
3. **One short question can check it**, and a right answer is good evidence
   for all of it.
4. **It does not contain other ideas.** A result does not restate the
   definitions it uses; it has an edge to them. Why a result holds is a
   separate proof idea.

Its kind says what a good question about it looks like: a **definition** (what
a term means), a **result** (that something holds: a theorem, a property, how
an API behaves), a **proof** (why a result holds: a proof, a derivation, an
argument), a **method** (how to do something: an algorithm, a technique, a
code pattern).

## Edges

For each edge ask both questions, separately, and write the edge with every
mark that passes:

- can they follow X's statement without Y? If not: **needs**;
- does answering or doing X make them carry Y out? If so: **uses**.

Definitions and results mostly only need; proofs and methods use what they
carry out, and often need it too. A result that seems to use something usually
means its proof is missing. Write only the closest edge: if X needs Y and Y
needs Z, X gets no edge to Z for that reason. Teaching order is not an edge.

## Areas

The home area is the most specific existing area where a colleague would look
first. Make a new one (`--new-area`) only when several ideas will live there.
API knowledge lives under `tools/` (`tools/pytorch`), concepts in their
subject's area. Areas are for finding and coverage, never prerequisites.

## Adding

Pipe blocks into `kioku add <<'EOF' … EOF`, so no shell sees the statement.
Several blocks may go in at once; an edge may name an idea added earlier in
the same input. It prints each new id and the area's size, and refuses (with
what it found) a duplicate, an edge to an unknown idea, an unknown area, or a
cycle. Link the learner's note in `- vault:` when one states the idea.

## Changing

```
kioku edit <name> --needs +a,-b --uses +c       # add and remove edges
kioku edit <name> --name new-name               # its edges follow the rename
kioku edit a,b,c --area maths/topology --new-area   # move ideas; unfold a sub-area
kioku edit <name> <<'EOF'                       # reword the statement
…
EOF
kioku rm <name> --why "<reason>"                # its answers move to archive.md
```

Reword freely as long as a past right answer would still be right; a different
claim is a new idea. `rm` refuses while another idea needs or uses it.
