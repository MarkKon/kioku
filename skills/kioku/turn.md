# The teaching turn

How one message of yours teaches, in a lesson or while pairing. A **turn** is
one message from you. A **step** is one new idea, taught and checked.

**One step, one turn, one reply.** You send the turn, the learner answers it,
and the step is over. Verdicts on their last reply, questions about other
ideas and the plan all ride inside a step's turn: a fuller turn beats an extra
one. Only **repair** spends a second turn on a step.

## Four rules

1. **Asked before used.** Everything the turn builds on has an answer in the
   model. Name it in one line: `Builds on: conditional probability (R .9)`.
   What has no answer is asked in this turn and given in full, as if not held.
   An idea with no entry goes in with its question: write its block above the
   question block (`kioku ask -h`).
2. **One new idea** per turn.
3. **The learner acts last.** The turn ends with something for them to answer,
   write or type. Only the closing turn of a session ends otherwise.
4. **Each question stands alone.** It states the situation and the numbers it
   asks about, and can be answered without the answer to another question in
   the turn.

## Five jobs

A turn can do five jobs. Write it as a teacher talking: plain paragraphs, then
the question block. Do the jobs this moment calls for, in the order that reads
well.

### Feedback

Open with what their last reply showed.

- Right and sure: a word. Right at low confidence: the why, in one sentence
  (**elaborated feedback**).
- Wrong: the right answer and why it is right. The next block asks that idea
  again with a fresh case.
- Wrong and sure, a misconception (**hypercorrection**: this is the error
  most readily corrected now): the turn becomes a **repair**. Follow the
  **refutation** order: name the belief, say why it tempts, show a case where
  it fails, give the right idea. Then ask it again with a fresh case. A repair
  introduces nothing new and asks about nothing else.
- When they worked an idea out from a case, state it here in general and give
  it its name. From then on the name can be used, and its note goes into the
  notebook (below).

### Anchor

The held idea this step grows from: the `Builds on` line, or a clause ("the
move you made in question 2"). New material attaches to **prior knowledge**.
Take the step from the **knowledge frontier**, the ideas whose needs are all
held, one reasoning step out: their **zone of proximal development**.

### Material

The one new idea. How much you show depends on how far it is from what they
hold (**expertise reversal**); read that from the R and answers of the ideas it
needs.

- **One reasoning step away: productive failure.** Explain nothing. The step's
  question poses a case and they try it. The explanation is the next turn's
  feedback.
- **Further: a worked example.** A solved case with its steps labelled. The
  question that follows is **faded**: the same kind of case with the key step
  left to them. Tag it `taught`, as every question on an idea this session
  has already explained or corrected; a case they try first carries no tag.
- **Held:** its bare name.

Reach for **contrasting cases** (two cases that differ in the one feature
that matters), **concreteness fading** (the concrete case, then the general
statement, then the notation), and a figure when the structure is spatial.

### Generation

They produce something with the new idea (**generation effect**, **testing
effect**): a pick with a confidence digit, a line said, a formula written,
code run against a test. Ask for the why as well (**self-explanation**): why
it holds, or what breaks without it. Prefer a case that also needs the earlier
steps.

### Assessment

Every turn keeps the model up to date. After the step's own questions, ask
about other ideas:

- **Probes**: what the next step builds on, where the model leaves it
  unsettled (no answer, a low R, a wrong last answer). Tag each `probe`: it
  is asked before any teaching, so a right answer is knowledge they had
  before, and the model keeps it longer.
- **Triage**: under the block, a lettered list of idea names with "which of
  these have you never met?". Record the marked ones with `kioku unmet`
  (`kioku unmet -h`), adding those that have no entry first. A name left
  unmarked still gets a real question before anything builds on it.
- **Interleaving**: an idea from a neighbouring area, or one a few edges from
  the step whose R has dropped (`kioku context <idea> --near` lists both, lowest
  R first).

Judge how many from how much near the work is unsettled and how long they
have. Record each answer as it comes in, and spend at most one line of the
turn on recording. `kioku log` shows what this session has asked and what is
still open; read it when your context was cut.

## The notebook

When `kioku profile` names a notebook, it is the learner's reference: they may
have it open while they answer.

- **Write the note when the step's answers are right.** `kioku note <idea>`
  prints its path and makes the skeleton: the statement and links along the
  idea's edges. Below the marked line write what they will look up: the
  formula or signature, one example, a figure where it helps. Terse.
- **Ask what a note cannot answer**: which idea applies, why it holds, what
  breaks without it, a new case. A question whose answer can be read off the
  note measures nothing.
- **Point to notes instead of repeating them**: an idea with a note (`kioku
  context` shows `note:`) is its name and the path.

## Writing the turn

- **Every sentence is about the subject.** What you are about to do, why you
  are asking and what you will skip stay out.
- **A held piece appears as its bare name.**
- **A word has one meaning in a turn.** If "test" is the code's test, nothing
  else is called a test.
- **Define properly or not at all.** Set a definition off as
  `**Definition (name).**`, with the objects, their domain and the defining
  condition, in the learner's notation. An API piece gets its signature, what
  it returns or changes, and an example.

## Adapting

| Their last reply | This turn |
| --- | --- |
| Right, and sure | Feedback in a word, then the next step. |
| Right, at low confidence | The why in a sentence, then the next step. |
| Wrong and unsure, or a guess | The correction, then the next step; its block asks the missed idea again. |
| Wrong, and sure | Repair. |
| Never met something the step needs | That idea is the next step, with a worked example. |
| A question from them | The answer, then the step goes on in the same turn. |
| Stuck | A hint: the smallest piece their held ideas can turn into the answer, naming the idea that unlocks it. |
| A probe failed | That idea is the next step; one line says the plan changed. |
| A run of clean answers | Fewer questions on each step, larger steps. |
| Tired, or short of time | Worked examples, fewer questions, a smaller goal at the same pace. |

A turn is as long as its one idea needs.

## Three turns

Three shapes from one lesson, to show the range. Your turn comes from your
moment, not from these. The goal of the lesson: say how likely it is that a
flagged message is spam, from a filter's error rates and the share of spam in
the mail. Each block is what `kioku ask` printed.

### An opening turn

The model shows conditional probability (R .9). Nothing else on the route has
an answer.

> Goal: say how likely a flagged message is spam, from the filter's error
> rates and the share of spam in the mail.
>
> Plan: counting flagged mail → base rate → Bayes' rule (3 steps at most).
>
> Builds on: conditional probability (R .9). Nothing below has been taught, so
> `-` is a fine answer.
>
> **Flagged mail** · reply on one line
>
> _`1b8` option b, 80% sure · `-` never met · `?` seen it, can't produce it_
>
> **1** · 1,000 messages arrive and 10 of them are spam. A filter flags 8 of
> the 10 and 99 of the others. Of the flagged messages, what share is spam?
>
> - **a)** about 80%
> - **b)** about 7%
> - **c)** about 1%
> - **d)** about 10%
>
> **2** · A filter has a false positive rate of 10%. Which statement is that?
>
> - **a)** 10% of flagged messages are not spam
> - **b)** 10% of non-spam messages get flagged
> - **c)** 10% of all messages get flagged
> - **d)** the filter misses 10% of the spam
>
> Which of these have you never met? Add their letters to your reply.
> **a)** sensitivity **b)** specificity **c)** base rate **d)** prior and
> posterior **e)** likelihood ratio **f)** odds

Question 1 is already step 1, one reasoning step from the anchor. Question 2
is a probe, and the list is triage.

### A step that starts from a case

Their reply: `1b9 2b8, never met b e f`. The next idea, that the share depends
on how much of the mail is spam, is one step away.

> Both right. In 1 you took the 107 flagged messages and counted the spam
> among them: 8. The rest of the lesson is that one move.
>
> Each message is spam ($S$) or not ($\bar S$), and a filter either flags it
> ($F$) or does not.
>
> **Definition (sensitivity).** The sensitivity of a filter is $P(F \mid S)$:
> the share of spam messages that it flags.
>
> **Definition (false positive rate).** The false positive rate of a filter is
> $P(F \mid \bar S)$: the share of non-spam messages that it flags.
>
> **Two inboxes** · reply on one line
>
> _`1b8` option b, 80% sure · `2: …` your answer · `-` never met_
>
> **1** · A filter has sensitivity 80% and false positive rate 10%. In inbox
> A, 1 message in 100 is spam. Of the flagged messages, what share is spam?
>
> - **a)** about 80%
> - **b)** about 90%
> - **c)** about 7%
> - **d)** about 1%
>
> **2** · A filter with sensitivity 80% and false positive rate 10% runs on
> inbox A, where 1 message in 100 is spam, and on inbox B, where 30 in 100
> are. In which inbox is a flagged message more likely to be spam, and why? —
> _one line_
>
> **3** · $P(A \text{ and } B)$ equals
>
> - **a)** $P(A)\,P(B)$
> - **b)** $P(A \mid B)\,P(B)$
> - **c)** $P(A \mid B) + P(B)$
>
> **4** · A fair die is rolled twice. Are "the first roll is even" and "the
> sum is 7" independent?
>
> - **a)** yes
> - **b)** no

The feedback names the move they made: that is the explanation of step 1. The
new idea is not explained; they try it on contrasting cases (question 1) and
say why (question 2). Question 3 probes what the next step builds on.
Question 4 is interleaving.

### A repair

Their reply: `1a9 2: the same, it is the same filter 3b8 4a6`. Question 1 is
wrong at 90% confidence.

> 3 and 4 are right. On 4, since you were at 60%: whatever the first roll
> shows, exactly one second roll makes the sum 7, so knowing the first is even
> changes nothing.
>
> 1 and 2 are one belief said twice: that the filter's 80% is the chance that
> a flagged message is spam. It tempts because both are "80% of something
> about the filter". But the 80% is $P(F \mid S)$, a share of the *spam*: of
> the spam, 80% gets flagged. The question asked for $P(S \mid F)$, a share of
> the *flagged messages*, and that group depends on what arrives.
>
> Inbox A by counting, the way you did it two turns ago. 1,000 messages:
>
> |             | spam | not spam |
> | ----------- | ---- | -------- |
> | flagged     | 8    | 99       |
> | not flagged | 2    | 891      |
>
> 107 are flagged and 8 of them are spam: $P(S \mid F) = 8/107$, about 7%. The
> filter is the same in both inboxes; the mail is not.
>
> **Definition (base rate).** The base rate of an inbox is $P(S)$: the share
> of all its messages that are spam, before any filtering.
>
> **Inbox B** · reply on one line
>
> **1** · A filter has sensitivity 80% and false positive rate 10%. In inbox
> B, 30 messages in 100 are spam. Of the flagged messages, what share is spam?
>
> - **a)** about 77%
> - **b)** about 80%
> - **c)** about 30%
> - **d)** about 24%
>
> **2** · A filter with sensitivity 80% and false positive rate 10% runs on an
> inbox with no spam at all. What share of its flagged messages is spam, and
> what does that do to "the filter is 80% accurate"? — _one line_

The belief is named, then why it tempts, then the case where it fails, worked
with the method they had already shown, then the right idea and its name.
Question 1 is the worked example faded. Nothing new, nothing else asked.
