# Night shift — 2026-09-15

> **Note for anyone running `precheck.py` against this file:** it will refuse it, and it is right
> to. This is a **finished** shift — its tasks are closed now, and a closed task in a queue is
> exactly what the check exists to catch. That refusal is the tool working, not a bug in the
> example.

**Armed at 04:02 after the precondition check passed.** Four phases. This is a real brief from the
project Night Watch was extracted from, trimmed to what a reader needs.

**Profile:** gates are `python -m pytest -q` (in `core-brain/`) and `pnpm test` + `pnpm exec tsc
--noEmit` (in `app/`). Both watched passing before arming.

## Never decide

- Restarting or killing anything the owner is running — the brain, his dev server, his model server.
- Writing his settings store, his conversations, or his presets.
- Anything outward-facing: a PR, an issue, a message, a publish.
- Adding an entry to the bridge allowlist. Widening a security boundary is a day decision.
- Any scope call the phases below did not already settle.

## Phase 1 — T-533 the microphone reported nothing when it failed

He pressed both microphone controls and nothing happened. Diagnose it.

**What must be true afterwards:** either the cause is named with a measurement, or — if it does not
reproduce — every layer on that path can report its own failure, and a broken voice link puts a
sentence on the screen.

**Gate:** `python -m pytest -q` (in `core-brain/`), `pnpm test` (in `app/`)

**Must not touch:** the running brain, the dev server, the model server.

## Phase 2 — T-532 attachments

A file dropped on the composer reaches the model. He ruled the design: the window sends a **path**,
never bytes.

**What must be true afterwards:** the original path is in the audit log; content reaches the model
inside the existing sanitizer and fence; the transcript stores his sentence and not the file body.

**Gate:** `python -m pytest -q` (in `core-brain/`)

**Must not touch:** the bridge allowlist without its written argument in the same commit.

## Phase 3 — T-531b read an answer aloud

The brain can speak and nothing can ask it to.

**What must be true afterwards:** it goes through the speech queue, not the engine, so the existing
stop can silence it; it is capped; nothing about how he sounds changes.

**Gate:** `python -m pytest -q` (in `core-brain/`)

## Phase 4 — T-530 smart-turn, which may end as a refusal

Confirm the licence **in writing from the model's own repository**, then measure it or refuse it
with the table.

**What must be true afterwards:** either it ships with a comparison against the current detector, or
it is refused with one. The existing timer survives as the fallback either way.

**Gate:** `python -m pytest -q` (in `core-brain/`)

---

## Log

### Phase 1 — T-533, not reproduced; the silence was the defect · `33401e1`

Every layer measured working afterwards. The finding: nothing on that path could report a failure —
the window swallowed its own rejection, the bridge command returned `Ok(())` whether or not it ever
connected, and the frame that says the link dropped had no listener anywhere.

**Gate:** `python -m pytest -q` → `2865 passed, 1 skipped` · `pnpm test` → `52 pass, 0 fail`

**Mutation:** put `.catch(() => undefined)` back on the subscription → **SURVIVED twice.** The first
guard asserted a symbol was present and the link listener still used it; the second sliced the whole
statement and `setVoiceFault(null)` on the success path satisfied it. Third version asserts on the
rejection handler alone → red.

**Found and not chased:** `subscribe_orion_broadcasts` kept only the *first* caller's broadcast
types and silently discarded every later one. Fixed in the same phase; benign today.

### Phase 2 — T-532 attachments, path not bytes · `a8f7153`

**Gate:** `python -m pytest -q` → `2879 passed, 1 skipped`

**Mutation:** removed the fence from the attachment body → red. Removed the fail-closed branch → red.
Made the store keep the fenced body → red on the third test. **Two earlier mutations of mine proved
nothing** and are recorded as such: one evaluated to the original expression, one truncated the file
before reading it.

### Phase 3 — T-531b read-aloud through the queue · `9951486`

**Gate:** `python -m pytest -q` → `2886 passed, 1 skipped`

**Not done:** the talking-speed slider. The brain supports it; there is no settings screen to put it
on. Recorded rather than bolted somewhere it does not belong.

### Phase 4 — T-530 REFUSED, and the reason is a language · `2355016`

The licence gate passed — BSD-2, confirmed from the model's own repository. Then its README settled
it: **23 supported languages, and the owner's is not one of them.** The per-language workaround is
closed by his own stack, which advertises mixed-language transcription because he mixes both inside
single utterances.

**What would change the answer:** his language in the list. Nothing else.

**Gate:** `python -m pytest -q` → `2886 passed, 1 skipped`
