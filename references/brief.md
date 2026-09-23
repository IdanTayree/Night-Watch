# The morning brief — measured, not recalled

**The brief is the product of the night.** The commits are the work; the brief is the only part the
owner actually consumes, and it is the part most likely to be quietly wrong — because by morning the
shift is recalling rather than measuring.

---

## Measure first

```bash
python3 scripts/verify_shift.py path/to/brief.md
```

It parses every `### … · \`sha\`` heading in the Log, checks each sha with
`git merge-base --is-ancestor`, counts what the shift claims against what git confirms, and prints
`UNMEASURED:` for anything it could not establish.

**Two rules about its output, and they are the whole point of running it:**

1. **A sha that is not an ancestor goes at the top of the brief, loudly.** It means the log records
   work that is not in history — an amended commit, a lost rebase, or a sha that was never real.
2. **`UNMEASURED` is reported as unmeasured.** Never substitute a remembered number. *Loading*, *not
   running*, *empty* and *not knowing* are four different states, and a brief that prints a
   plausible figure for any of them has failed at the one thing it exists to do.

---

## The shape

**Short, and in this order.** The reader is deciding what to do with their morning, not reading a
report.

### 1 · Two lines: did the night deliver, and is anything on fire

Phases completed of how many, commits, gates green or not, anything blocked. If a sha failed
verification, it goes here.

### 2 · A small table of numbers

Whatever this project measures — test counts, gate results, board state. **Numbers only**, no prose.
Each one either measured this morning or labelled with when it was taken.

### 3 · What landed

One line per phase, each with its verified sha. **Not a list of everything done** — a list of what
changed for the reader. If a phase was pure hygiene, it belongs in one clause, not a paragraph.

### 4 · What was refused, and why

**Often the most useful section.** Each refusal: what was measured, what it says, and in one clause
what would change the answer. A refusal without a measurement is a deferral wearing better clothes —
say which one it is.

### 5 · Found and not chased

**This is where the value usually is, and it is the section that vanishes if nobody asks for it.**
Things the shift noticed that were on nobody's list: a defect next door to the work, a number that
disagrees with a document, a capability with no consumer.

On one real shift the single most valuable finding — a health check that reported a dead service as
healthy — was not on the queue at all. It surfaced because the shift was told to write down what it
noticed. Keep this section even when it is empty, and say it is empty.

### 6 · What needs them

**Capped at five.** Each one sentence, each with the default that will be taken if they say nothing.
A question with no default is a question that blocks; a question with a default is one they can
ignore safely.

---

## What a brief must never do

- **Never list every task.** Twelve rows of *done* is the thing people stop reading. The log exists
  for that; the brief is for what they would not otherwise notice.
- **Never soften a refusal into a deferral**, or a block into "in progress".
- **Never report an estimate as a measurement.** If it was not measured this morning, say when it
  was.
- **Never compute a percentage over a denominator the reader will guess wrong.** Say both numbers.
- **Never bury a failed sha.** It is the one thing that invalidates everything above it.

---

## When there was no shift

If nothing ran — no commits since the brief was armed, no log entries — **say that in one line** and
offer the queue instead. A brief invented for a night that did not happen is the worst possible
output of a tool whose entire purpose is trustworthy reporting.
