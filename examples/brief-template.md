# Night shift — fill and validate before arming

## Never decide

- No access to owner data or running services beyond the granted task scope.
- No publishing, messages, purchases or permission changes without existing owner authorization.
- Stop on unsettled scope; do not reinterpret it overnight.

```night-watch-policy
{"version": 1, "base_commit": "REPLACE_WITH_FULL_CURRENT_SHA", "protected_paths": ["data"]}
```

## Phase 1 — T-1 Add parser validation

Why now: a settled contract needs executable coverage. Replace these illustrative paths, task and
command with the actual open task and project gate. The unfilled base above intentionally fails.

```night-watch-phase
{"task": "T-1", "gate": "python -m unittest discover -s tests -v", "cwd": ".", "done": "Valid data round-trips and malformed data is rejected", "paths": ["src/parser.py", "tests/test_parser.py", "docs/parser.md"]}
```

## Log
