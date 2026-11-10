# The teaching turn: why, and what is left

Written 2026-11-10 and put into the skills the same day. The turn itself (its
rules, its jobs, how it adapts, example turns) is in `skills/kioku/turn.md`,
and nowhere else. This page keeps the reasons and the parts not built yet.

## What was wrong

- **Sessions took too many messages.** In pairing, a step ran as a lesson, a
  check, a verdict and then the brief. In a lesson, a round of questions came
  before any teaching.
- **Agents assumed.** Much of the model has no answers, and agents built on
  ideas nobody had asked about, in spite of the rule to check.
- **Teaching methods did not land.** The skills paraphrased them ("at the size
  of what they hold"). A paraphrase brings none of what an agent already knows
  about a worked example or about hypercorrection.

## What was decided

- **One step is one turn and one reply.** Only the repair of a confident
  error spends a second turn. Verdicts, questions about other ideas and the
  plan ride inside a step's turn.
- **Assessment is a job of every turn.** Each turn's questions also probe what
  the next step builds on, triage names, and bring back a nearby idea whose R
  has dropped. This replaces the lesson's sweep; its reason stands (nothing
  rests on an unasked idea).
- **An idea one reasoning step away is tried before it is explained**; one
  further away gets a worked example. The explanation of a tried idea is the
  feedback of the next turn.
- **The jobs are named by the terms of the literature**, listed below.
- **A turn is not a format.** It has four fixed rules and is otherwise
  judgement; the skill carries example turns of different shapes.
- **A term is defined properly or not at all**, a question states what it
  asks about, and a turn carries no commentary on what the agent is doing.
- **Learn and pair share the turn.** In pairing the learner's production is
  code. A passing test is evidence for the method and the API pieces it
  carried out; why the method works gets a question in the next turn.

## Outside maths and code

The jobs stay; the forms change. In a language, contrasting cases are two
sentences that differ in one ending, and the learner produces a sentence of
their own. In history, the case is a source, and the learner says what it does
and does not show. For a lab method, the learner carries out the procedure,
and a result that can be checked is its key.

The four kinds of idea cover this when read as four questions: what it means
(definition), that it holds (result), why it holds (proof), how to do it
(method).

## The leading terms

| Term | In one line | Source |
| --- | --- | --- |
| Elaborated feedback | Feedback that says why, not only whether | Shute, "Focus on formative feedback" (2008) |
| Hypercorrection | Confident errors are corrected most readily | Butterfield & Metcalfe (2001) |
| Refutation | Name the belief, show where it fails, then correct | Kendeou & O'Brien (2014) |
| Prior knowledge | New material attaches to what is held | Ausubel (1968) |
| Zone of proximal development | What they can do with help, not yet alone | Vygotsky (1978) |
| Knowledge frontier | Ideas whose needs are all held | Doignon & Falmagne (1985) |
| Mastery learning | A step is done when it is shown, not when it is explained | Bloom (1968) |
| Productive failure | Trying before being told | Kapur (2008) |
| Worked example, fading | A solved case, then one with the key step left out | Renkl & Atkinson (2003) |
| Expertise reversal | Help for novices slows the experienced | Kalyuga et al. (2003) |
| Contrasting cases | Two cases that differ in what matters | Schwartz & Bransford (1998) |
| Concreteness fading | Concrete first, then general, then notation | Goldstone & Son (2005) |
| Generation effect | Produced is kept better than read | Slamecka & Graf (1978) |
| Testing effect | Retrieval strengthens more than re-reading | Roediger & Karpicke (2006) |
| Self-explanation | Saying why a step holds | Chi et al. (1994) |
| Interleaving | Mixed topics, harder and longer-lasting retrieval | Rohrer & Taylor (2007) |

## Not built yet

Built with the turn, on 2026-11-10:

- `kioku unmet` records the names marked never met in a triage; an idea last
  answered that way reads `unmet`, apart from a wrong answer.
- A question block has no size limit.
- `kioku ask` adds the ideas written above its block.
- `kioku log --since 3h` lists what was asked and answered lately.
- `kioku context <idea> --near` lists the ideas around one, lowest R first.
- An item tagged `taught` marks its answer as given after teaching in the
  same session.
- The notebook: `kioku note <idea>` makes a note's skeleton and the area
  indexes; the agent writes the body and a map of each lesson.

- An answer records what happened (right, partly, wrong, never met; the
  confidence digit; the help a step took) in place of the grades again, hard,
  good and easy. The memory model reads confidence against the learner's own
  record. A question tagged `probe` is asked to find out what they already
  held; a right first answer to one starts at up to thirty days of stability,
  by how sure it was.

Still to build:

- **Fitting the memory model on the learner's own answers.** The thirty days
  for old knowledge, and how much a hint or a slip counts, are placeholders
  until there are enough later-day answers to fit them (principle 12).

## Not decided

- **How this works with a weaker agent.** The turn asks for judgement, and a
  weaker model may copy one example's shape every time. The plan is to try the
  skill with a small model as the learner on an invented subject, where it
  knows only what the lesson tells it.
