# Checked brief format (version 1)

Keep the human explanation. Add these JSON fences for facts the helpers can check. JSON must have
unique keys. Do not put real secrets in a brief, gate output or receipt. Commands are **recorded, never
executed by precheck or verify_shift**. Paths in arguments are relative to the caller's working directory;
paths inside the contract are relative to `--repo`. Use absolute CLI paths to avoid ambiguity.

## Before the shift

Create a task board with real open rows, for example `- [ ] **T-1:** Add the parser`. Capture the
current full SHA with `git rev-parse HEAD`. In the brief, before the numbered phases:

```night-watch-policy
{"version": 1, "base_commit": "0000000000000000000000000000000000000000", "protected_paths": ["data", "config/production.json"]}
```

Replace the example SHA with the actual current commit. `.git` and `.github/workflows` are always
protected by these helpers. Other literal paths come from the project's Never decide list. Use an
explicit empty list when there are no additional protected paths. A path denotes itself and everything
under it; wildcards, absolute paths, parent traversal and symlink escapes are rejected. Runtime paths
outside the repository, running services, network calls and secrets require the host's permission
controls and the human-readable Never decide list; these helpers cannot enforce those boundaries.

Each queued heading is `## Phase 1 — T-1 Add parser`, followed by exactly one contract:

```night-watch-phase
{"task": "T-1", "gate": "python -m unittest discover -s tests -v", "cwd": ".", "done": "Malformed input is rejected and valid input is preserved", "paths": ["src/parser.py", "tests/test_parser.py", "docs/parser.md"]}
```

Task IDs and phase IDs must be unique. A board is required, and every task must be open before arming.
Gate, cwd and done must be nonempty; this does not prove the command or assertion is appropriate.
Declared write paths cannot overlap protected paths. Broad parent paths also count as overlaps.
All files changed by the implementation commit must fit the declared paths, including its task docs.
Keep administrative receipt commits separate; the verifier checks claimed implementation commits,
not every unrelated commit in the branch. An integrator must review the complete branch diff too.

```bash
python3 /path/to/night-watch/scripts/precheck.py /path/to/brief.md --repo /path/to/project --board /path/to/project/TASKS.md
```

Exit 0 validates declarations; exit 1 refuses. **Also run the actual gate and review scope/permissions.**
The brief should be approved/pinned outside the worker's editable scope. Do not let the worker weaken
its own contract or accept its own changes. No parser substitutes for semantic review of the plan.

## During and after the shift

Use one implementation commit per phase, whose subject starts with the task ID, e.g. `T-1: Add parser`.
Run its gate against that exact commit (or its identical code tree, before adding only the receipt).
Record real output and the full SHA; do not synthesize passing output. The `## Log` section contains:

```markdown
### Phase 1 — T-1 Add parser · `abcdef0`
```

Then a receipt (replace the example SHA and output with actual evidence):

```night-watch-receipt
{"task": "T-1", "status": "completed", "gate": {"command": "python -m unittest discover -s tests -v", "cwd": ".", "commit": "0000000000000000000000000000000000000000", "exit_code": 0, "output": "Exact output from the gate goes here"}}
```

The commit must be a distinct single-parent commit with a nonempty diff, after the base, in phase
order, and an ancestor of HEAD. The short SHA in the heading must resolve to the full gate commit.
No duplicate task receipts or skipped phase IDs. Changed paths are checked with rename detection off
so both ends of a move count. A clean working tree, including committed receipts, is required.

A measured refusal is a finished outcome: use `status: "refused"`, `reason` and `would_change`, plus
a commit of its written evidence and gate. A blocked phase is unfinished: use `status: "blocked"`
and a nonempty `reason`; no fake SHA or passing gate is required. Stop the sequential queue instead
of running dependents. Add `### STOPPED AFTER PHASE 1 — <reason>` (last attempted phase, or `0` if none).
Additional Markdown headings in the Log are rejected; use bold labels inside phase entries instead.

```bash
python3 /path/to/night-watch/scripts/verify_shift.py /path/to/brief.md --repo /path/to/project --json
```

- **0 — complete:** every phase has a valid completed/refused receipt and all structural checks pass.
- **1 — invalid:** missing/malformed/duplicate evidence, dirty checkout, mismatched gate, out-of-scope
  diff, missing ancestor or unmarked unfinished work. Never promote this to success.
- **2 — incomplete:** a valid explicit interruption/blocked outcome. Report what remains; it is not
  completion and must not trigger dependent work.

To check delivery to a remote branch, fetch it first (under existing authorization), then pass
`--require-ref origin/main`. Without this option, ancestry establishes local HEAD inclusion only.
The verifier never fetches and cannot establish remote freshness. A receipt's output remains a claim;
independent review/rerunning trusted gates establishes test truth and design acceptance.

## Migration

Historical briefs remain historical. Copy their intended scope into a new current template, resolve
open decisions, and add actual board IDs/base SHA/path declarations. Re-run gates for new work. Do not
backfill invented outputs into old logs to get a green exit. [Template](../examples/brief-template.md).
