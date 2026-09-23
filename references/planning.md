# The day shift — building a queue that can run without you

**The day's job is one question: *what would stop the night?*** Everything here serves that.

An unattended shift fails in one of three ways, and all three are decided during the day: it works
on something that does not exist, it stalls on a question nobody answered, or it produces changes
nobody can check. This document is how to close all three before anyone goes to bed.

---

## 1 · Profile the project — generated, never asked

```bash
python3 scripts/profile.py            # writes .night-watch/profile.json
```

It reads the repo for the things a shift needs to know: which gates appear to exist and candidate commands to
run them, the package manager and where it lives, where tests live, whether there is a board or an
issue tracker, the commit message convention in recent history, and which processes and ports look
like they belong to a running dev environment.

**Then show it and take corrections.** The generated profile will get something wrong — a gate that
needs a different working directory, a port that belongs to something else. **This is the cheapest
question in the whole cycle**, because every correction here is a question the night cannot ask.

### The gate check is a hard gate

The profile reports the gates it found. **Run at least one and watch it pass**, in this session,
before anything else happens. A gate that has never been seen to pass is not known to work, and a
shift that discovers at 2am that the test command is wrong has lost the night.

**If there are no gates, stop and say so.** See the precondition in `SKILL.md`. Offer to build the
first one — that is a fine day's work and it makes every night after it possible.

---

## 2 · Sort the work by who is needed

Take the candidate work — a backlog, a blueprint, a list they just said out loud — and put every
item in one of two columns. **The test is not difficulty. It is whether an answer only they have
would change what gets built.**

| needs them (day work) | needs nobody (night work) |
|---|---|
| a decision between two designs | a decision already made, not yet done |
| anything about taste or how it should feel | a defect with a known correct behaviour |
| scope: is this in or out | a test for behaviour that is already specified |
| anything touching money, credentials, or people outside the project | a refactor with a green gate on both sides |
| a preference nobody can infer | a measurement, and writing down what it says |
| "should we even do this" | "do this, it was agreed" |

**Retire the left column now, while they are here.** That is the day shift. Every item moved from
left to right is an hour of night that will not be wasted.

**An item that cannot be moved does not go in the queue.** Put it in the brief's *what needs them*
section instead. A phase that depends on an unanswered question is the most common way a night is
lost, and the precondition check refuses it for that reason.

---

## 3 · Write the phases

One phase is **one task, one commit, one gate.** If a phase cannot be committed on its own, it is
two phases.

Each phase states, in this order:

1. **What to do**, concretely enough that no scope decision is left in it.
2. **Why now** — one clause. A phase whose reason cannot be written is usually not ready.
3. **What must be true afterwards** — the definition of done, as observable facts rather than
   intentions.
4. **Which gate proves it**, by exact command.
5. **What it must NOT touch.** Often the most load-bearing line: the files, services or data that
   are out of scope even if they look related.

### Order by reversibility, cheapest first

**Not by interest, not by importance.** The shift may die at any phase — a crash, a rate limit, a
three-strike stop — and the question that matters is: *if it stops here, was what already happened
safe to have done?*

So: pure additions and tests first. Refactors behind a green gate next. Anything touching shared
state, live services, generated files or another agent's lane **last, or not at all.**

A second reason, less obvious: the early phases teach the shift about the project. A phase that
fails cheaply at position one is worth more than the same failure at position six, because the
remaining five now have that information.

### Estimate against something measured

If this project has run shifts before, use its own history: phases completed per hour, from the
logs. If not, **say the estimate is unmeasured** and keep the first queue short. A queue longer than
the night is not ambition — it guarantees a `STOPPED AFTER PHASE N` and an unfinished phase to
unpick in the morning.

---

## 4 · Write the never-decide list

**The most expensive unattended failure is a scope call at 3am**, made reasonably, in good faith,
and wrong. "A refusal is a deliverable" is not enough on its own — it relies on the agent noticing
that a decision is being made. Name the categories in advance so noticing is not required.

Defaults, which every project should keep:

- **Anything destructive and irreversible.** Deleting data, force-pushing, rewriting history,
  dropping a table, revoking a key.
- **Anything outward-facing.** Opening a PR, posting an issue or comment, sending a message,
  publishing a package, touching production.
- **Anything about money, secrets or people.**
- **Widening a permission or security boundary** — a new capability, a new scope, a new allowlist
  entry, a loosened check.
- **A scope decision the brief did not already settle.** If two readings of a phase lead to
  materially different work, that is a question, not a coin toss.
- **Anything the owner has said is theirs.** Their settings, their data, their running processes.

Then add the project's own. A project that has been burned once knows what belongs here.

---

## 5 · Check the structured contract

Use [contracts.md](contracts.md) to record the base commit, protected paths, per-phase task/gate/done
conditions and write scopes. Run precheck with the explicit project and board paths. It validates
those declarations; it never executes gate commands or interprets all natural-language restrictions.
A nonexistent/empty board is a failure. A passing precheck still needs a real green gate and an
independent permissions/scope review before arming. Use the host sandbox for runtime restrictions.


## Coming from a Blindspot blueprint

[Blindspot](https://github.com/IdanTayree/Blindspot) ends with a blueprint: decisions in the user's
own words, stated assumptions, and a list of open questions — plus a verified component list.

**The open questions are the day's work.** They are, by construction, exactly the things a night
cannot resolve. Work through them first; the blueprint's own convergence table tells you which
quadrant each came from and therefore how expensive it is to settle.

**The decisions become phases**, and the decomposition is the step neither skill does alone:

1. Take each decision that implies work.
2. Split until each piece is independently committable and has a gate that can prove it.
3. Attach the component the harvest verified for that piece, with its licence — **a night shift
   should never be choosing a dependency**, that is a day decision with a licence attached.
4. Order the pieces by reversibility, per above.
5. Anything that will not split into something a gate can prove is **day work** — a design, a
   measurement, or a conversation.

The blueprint's stated assumptions deserve one pass too: an assumption the user has not corrected is
not a decision, and a phase resting on one belongs in the day column until they confirm it.
