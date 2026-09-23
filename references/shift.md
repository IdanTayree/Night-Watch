# The night shift — working the queue and leaving evidence

**Nobody is awake to catch you.** Everything here follows from that one fact.

The failure this document is written against is not the shift that crashes. A crash is obvious in the
morning. **It is the shift that finishes every phase, reports success, and produced nothing real** —
because the tests it wrote could not fail, the guard it added was satisfied by the comment explaining
it, or the number it reported came from memory. That failure looks identical to success from the
inside, which is why the rules below are about evidence rather than effort.

---

## The loop

For each phase, in the order the brief gives them:

1. **Re-read the phase.** Its *must not touch* line especially.
2. **Do the work.**
3. **Falsify it** — see below. This is not optional and it is not the same as testing.
4. **Run the phase's gate.** The exact command from the brief.
5. **Read the gate's output.** All of it.
6. **Commit** — one phase, one commit, the project's own message convention.
7. **Log the phase into the brief**, with the sha in the heading.

Then the next phase. **No reordering.** If a phase turns out to depend on a later one, that is a
finding for the brief, not a licence to shuffle.

---

## Falsify, don't just test

**Writing a test proves you wrote a test.** The question is whether it can fail for the right
reason, and the only way to know is to make it fail.

After adding any guard or test:

1. **Break the thing it guards, on purpose.** Not the test — the code under it.
2. **Confirm the guard goes red.**
3. **Confirm the break actually produced the defect.** This is the step people skip, and it is where
   the value is. A mutation that makes the file fail to parse, or that changes nothing at all, tells
   you nothing about the guard — it went red for the wrong reason, or stayed green for the right one.
4. **Restore, confirm green, and record both** in the phase's log: what was mutated, and what
   happened.

**Mutations that prove nothing, all of which are real:**

| mutation | why it proved nothing |
|---|---|
| `if (false) return …` | the file stopped loading; red came from the parser, not the guard |
| `x if False else x` | evaluates to the original; nothing changed |
| a one-liner that truncated the file before reading it | the guard passed over an empty file |
| deleting a check that nothing downstream reached anyway | the defect never occurred |

**Assert against structure, not text.** A guard that greps source for a forbidden word will match the
comment explaining the ban — including, eventually, its own. Parse it, or strip comments first. And
when a guard survives a mutation that should have killed it, the guard is wrong: re-aim it at the
mechanism rather than at a word that happens to be nearby.

---

## Evidence rules

- **Paste the gate's real output**, including the exit status. A sentence saying it passed is not
  the thing passing.
- **Numbers are measured in the moment or labelled stale.** A count from earlier in the shift is a
  count from earlier in the shift; say when it was taken.
- **A claim about another file is the claim that nothing checks.** *"X is called by Y"* has been
  wrong far more often than any measured number. Open Y.
- **When an instrument and the code disagree, suspect the instrument first.** A metric that
  aggregates should print its parts. An absence found by a search is a fact about the search.

---

## Logging, and why the sha goes in the heading

Each phase gets an explicit status and structured receipt in the brief's **Log** section. Use the
[contract format](contracts.md), including the full implementation SHA in gate evidence and the SHA
in the phase heading. The verifier checks one-to-one ordered mapping, actual changed paths and
ancestry. A heading alone never declares completion. Keep implementation and receipt commits separate
when project policy requires it; commit the final brief before verifying a clean checkout.

---

## Stopping

**Three strikes.** Three consecutive failed attempts at the same problem, and the phase is `BLOCKED`.
Write what was tried, what each attempt did, and what would unblock it. Stop the sequential queue and add a STOPPED marker.
A separately approved independent queue can proceed; do not guess which later phases are independent.

**Refusal is completion.** A phase that should not be done is finished when the refusal is written:
what was measured, why it says no, and in one clause what would change the answer. A refusal with a
measurement behind it is worth more than the work would have been.

**Ending early.** Write, at the top of the Log:

```markdown
### STOPPED AFTER PHASE N — <one line on why>
```

Without it the morning cannot tell finished from interrupted, and a half-done phase gets built on.

---

## The never-decide list

The brief carries it. When a phase turns out to require one of those decisions:

1. **Stop that phase.** Do not pick the reasonable option.
2. **Write the question** into the brief's *what needs them* section, with the options and what each
   costs.
3. **Stop the sequential queue and record the interruption.**

A question asked in the morning costs minutes. A decision made at 3am and discovered a week later
costs the work built on top of it.

---

## Leave the machine as you found it

Note anything started, and stop it before the shift ends — or say plainly in the brief that it is
still running and why. A process left behind is a defect discovered by someone who did not start it.

**And anything the owner is running is theirs.** Their editor, their servers, their sessions. If a
phase needs a port or a process they own, that is a question for the morning, not a restart at 3am
— unless the brief says otherwise in writing.
