# Changes

## 2026-09-23 — Verification hardening and ChatGPT compatibility

Added versioned task/path contracts, required board validation, actual implementation-diff checks, ordered commit/gate receipts, incomplete exit status, and regression tests. Old prose-only briefs require explicit migration; see references/contracts.md.

Both the README and skill entry point now cover Claude, ChatGPT and Codex. Added host-capability
fallbacks and OpenAI skill metadata. Fixed invalid original YAML descriptions. Existing Claude
installation remains supported. Documentation explains what the checks establish and what still
requires independent review; no live ChatGPT/Claude overnight run was claimed.

Validation used disposable repositories and mocked API responses, without owner data or credentials.
Exact gate output:

```text
$ /Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m unittest discover -s tests -v
test_base_commit_cannot_be_reused_as_delivery (test_checks.ShiftChecks) ... ok
test_cli_json_returns_nonzero_incomplete (test_checks.ShiftChecks) ... ok
test_complete_receipt (test_checks.ShiftChecks) ... ok
test_duplicate_json_keys_refused (test_checks.ShiftChecks) ... ok
test_empty_log_never_passes (test_checks.ShiftChecks) ... ok
test_explicit_interruption_has_distinct_nonzero_exit (test_checks.ShiftChecks) ... ok
test_fenced_phase_example_not_counted (test_checks.ShiftChecks) ... ok
test_gate_must_match (test_checks.ShiftChecks) ... ok
test_missing_empty_closed_and_duplicate_boards (test_checks.ShiftChecks) ... ok
test_missing_remaining_phase_is_not_success (test_checks.ShiftChecks) ... ok
test_missing_sha_or_gate_evidence_rejected (test_checks.ShiftChecks) ... ok
test_missing_task_gate_done_and_paths (test_checks.ShiftChecks) ... ok
test_negated_prose_does_not_trigger_false_refusal (test_checks.ShiftChecks) ... ok
test_out_of_scope_actual_change_rejected (test_checks.ShiftChecks) ... ok
test_profile_unavailable_git_status_is_unknown (test_checks.ShiftChecks) ... ok
test_refusal_and_blocked_are_distinct (test_checks.ShiftChecks) ... ok
test_remote_ref_required_when_requested (test_checks.ShiftChecks) ... ok
test_renamed_protected_source_rejected (test_checks.ShiftChecks) ... ok
test_scopes (test_checks.ShiftChecks) ... ok
test_two_phases_with_separate_receipt_commit (test_checks.ShiftChecks) ... ok
test_unmerged_commit_rejected (test_checks.ShiftChecks) ... ok
test_valid_precheck (test_checks.ShiftChecks) ... ok
test_wrong_task_duplicate_and_dirty_rejected (test_checks.ShiftChecks) ... ok

----------------------------------------------------------------------
Ran 23 tests in 3.724s

OK
exit 0

$ /Users/idan/Orion/core-brain/.venv/bin/python3 /Users/idan/.codex/skills/.system/skill-creator/scripts/quick_validate.py /private/tmp/maestro-night-watch-review.Vp750R
Skill is valid!
exit 0

$ git diff --check
exit 0
```
