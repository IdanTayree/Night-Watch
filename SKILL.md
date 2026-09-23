---
name: night-watch
description: "Plan, execute and report finite unattended project shifts with explicit task contracts and verifiable evidence. Use for overnight work, handing an approved queue to an agent, or reviewing what a shift delivered. Supports Claude, ChatGPT and Codex; without repository execution tools, provide planning or evidence review rather than claiming a shift ran."
---

# night-watch

## Host and capability check

Works with Claude, ChatGPT and Codex. Read [references/platforms.md](references/platforms.md) when
starting in a new host. Confirm available files, browsing, Python/Git and execution permissions before
promising outputs. Use its planning-only or conversation fallback when tools are missing. Resolve
bundled scripts relative to this SKILL.md, not the user's project. This check governs the file-saving
and execution steps below; never invent successful runs or persistence.


**Two shifts, split by who is needed — not by the clock.**

Some work needs the person: decisions, taste, anything only they know, anything whose answer changes
what gets built. Some work needs nobody: the thing was already decided and now has to be done, proved
and recorded. **Mixing them wastes the person's attention on the second kind and starves the first.**

This skill separates them. The **day shift** spends attention deliberately — answering the questions
that would otherwise stall the night, and turning the answers into a queue. The **night shift** works
that queue unattended, and comes back with something that can be checked rather than believed.

> *"Night gathers, and now my watch begins."*

## The one precondition, and it is not negotiable

**A project with nothing that can fail loudly gets no benefit from this.** Unattended work is only
worth having if somebody can tell afterwards whether it was real, and the person who cannot tell is
the agent that did it. Without tests, types, a build, a linter — something that goes red on its own —
a night shift produces eight hours of plausible diffs and no way to distinguish them from eight hours
of drift.

**So before arming anything, establish the project has at least one gate that can fail.** Run it and
watch it pass. If there is none, **say so and stop.** Offer the day-shift half — planning, deciding,
writing the queue — and offer to build the first gate. Do not arm a shift on a project that cannot
contradict it. That refusal is the most valuable output this skill has.

---

## Checked brief format

Use [references/contracts.md](references/contracts.md) for the required JSON policy, per-phase scope,
receipts and exit codes. The Markdown explanation remains useful to people; the structured fields
make task/path/evidence validation deterministic. Historical prose-only briefs require migration and
are not silently accepted. These checks are not a sandbox and do not prove self-reported tests ran.

## Phase 1 — the day shift: build a queue that can run without you

Read **`references/planning.md`** before starting this. The short version:

1. **Profile the project.** `python3 scripts/profile.py` reads the repo and writes
   `.night-watch/profile.json`: the gates it can find and how to run them, the package managers, the
   test layout, the commit conventions, whether a board or issue tracker exists. **Generated, not
   asked** — the answers are in the repo and asking for them wastes the attention this skill exists
   to protect.
2. **Confirm what it got wrong.** Show the profile and take corrections. This is the one place
   questions are cheap, because every one answered here is one the night cannot ask.
3. **Ask the question that defines the day: *what would stop the night?*** Go through the candidate
   work and sort it: **needs them** (a decision, a preference, a credential, a judgement about
   scope) versus **needs nobody**. The first list is the day's work. **Retire it now, while they are
   here.**
4. **Write the phases.** Each phase is one task, one commit, with its own gate and its own
   definition of done. Ordered by **reversibility, cheapest first** — see `planning.md` for why.
5. **Write the never-decide list.** Categories the night must refuse rather than resolve. Defaults
   in `planning.md`; the project adds its own.
6. **Run the precondition check.** `python3 scripts/precheck.py <brief>` and **read its output.**
   It refuses missing/closed tasks, incomplete structured contracts and protected-path overlaps.
   Review the surrounding prose for unresolved decisions; a parser cannot establish semantic clarity. **A failing check is not a formality to override** — it is
   the difference between a useful night and a wasted one.

**The day ends after the check passes, the gates run green and permissions are reviewed.** Nothing
is armed before that; precheck alone is insufficient.

---

## Phase 2 — the night shift: work the queue and leave evidence

Read **`references/shift.md`** before the first command. The rules that matter most:

- **Phases in order. One phase, one commit.** No bundling, no reordering because something looked
  easier.
- **Every claim carries its evidence.** Paste the gate's real output. A summary of a passing test is
  not a passing test.
- **Log each phase into the brief, with the commit sha in the heading.** Not in the prose — in the
  heading, where a script can find it and verify it with `git merge-base --is-ancestor`. A log that
  says work happened is not the same as work that happened.
- **Falsify, don't just test.** After writing a guard, **break the thing it guards on purpose and
  confirm the guard goes red.** Then confirm the break actually produced the defect — a mutation
  that fails to load, or that changes nothing, proves nothing about the guard. Record the mutation
  and its result. **This is the difference between a night shift and a night of typing.**
- **Three strikes and stop.** Three consecutive failed attempts at the same thing is a `BLOCKED`
  entry with a written reason, not a fourth attempt.
- **A refusal is a completed phase.** Say refused, say what was measured, and say in one clause what
  would change the answer. A task that should not be done is finished when that is written down.
- **Never decide what the list says not to decide.** Write the question and stop the sequential queue; do not run its dependents.
- **Stop cleanly.** If the shift ends early, write `STOPPED AFTER PHASE N — <one line on why>` so the
  morning knows the difference between finished and interrupted.

---

## Phase 3 — the morning: a brief that was measured

Read **`references/brief.md`**. Run `python3 scripts/verify_shift.py <brief>` **first** — it checks
queue/receipt mapping, ancestry, changed paths and recorded gate evidence. Exit 0 means complete,
1 means invalid evidence and 2 means explicitly incomplete; see the contract reference.

**Report `UNMEASURED` as unmeasured.** Never substitute a remembered number for one a script refused
to give: loading, not-running, empty and not-knowing are four different states, and a brief that
prints a plausible figure for any of them has lied about the one thing it exists to get right.

The brief has a fixed shape, and its most valuable section is the one nobody asked for:

1. **Did the night deliver, and is anything on fire** — two lines.
2. **A small table of numbers.** Gates, counts, whatever this project measures.
3. **What landed**, each with a verified sha.
4. **What was refused, and why** — often the most useful part.
5. **Found and not chased.** Things the shift noticed that were on nobody's list. This is where the
   value tends to be, and it is the section that disappears if nobody asks for it.
6. **What needs them**, capped at five, each one sentence.

---

## Pairs with Blindspot

**[Blindspot](https://github.com/IdanTayree/Blindspot)** interviews you until your unknowns run out
and produces a blueprint plus verified components. **Night Watch consumes a queue.**

They fit together exactly, and the seam is worth naming: **Blindspot's output is a list of decisions
and a list of open questions — and open questions are precisely what must never enter a night
queue.** So a blueprint is the right input, and its unresolved section is the day's work by
definition. Run Blindspot when the shape of the thing is still in question; run Night Watch once it
is not.

If a blueprint exists, `planning.md` describes how to decompose it into phases — the step that turns
a plan into a queue, which is the piece neither skill does on its own.

## Layout

```
night-watch/
├── SKILL.md                  this file — the three phases
├── references/
│   ├── planning.md           the day shift: profiling, sorting, writing phases, the check
│   ├── shift.md              the night shift: the loop, the evidence rules, stopping
│   └── brief.md              the morning brief: shape, and what may not be guessed
└── scripts/
    ├── profile.py            reads the repo, writes the project profile
    ├── precheck.py           refuses a brief that cannot run unattended
    └── verify_shift.py       checks the shift's own claims against git
```
