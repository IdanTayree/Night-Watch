#!/usr/bin/env python3
"""Refuse a brief that cannot run unattended.

**The failure this exists to prevent has happened in real projects more than once:** a shift works
for hours on a task that was closed last week, or stalls on a phase whose answer nobody gave, and
the whole time it reads as productive. Nobody is awake to notice.

So every phase is checked for the four things that make a night recoverable — it names work that
exists and is open, it has a gate, it has a definition of done, and it does not depend on an open
question — plus the never-decide list, which is checked as paths rather than as good intentions.

    python3 scripts/precheck.py brief.md [--board async-inbox.md] [--repo .]

Exit 0 when the brief may be armed, 1 when it may not.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PHASE_RE = re.compile(r"^#{2,4}\s*Phase\s+(\S+?)\s*[—:-]\s*(.+?)\s*$", re.M | re.I)
#: A task id, and NOT a licence or a standard. `[A-Z]+-\d+` matched `BSD-2` on this project's own
#: example brief — which would have reported a licence name as an invented task. Two digits at
#: minimum, plus a denylist of the prefixes that actually collide.
TASK_RE = re.compile(r"\b([A-Z]{1,6}-\d{1,6})\b")
NOT_A_TASK = {"BSD", "MIT", "GPL", "LGPL", "AGPL", "EPL", "MPL", "CC", "UTF", "ISO", "RFC",
              "SHA", "MD", "AES", "RSA", "EC", "TLS", "SSL", "HTTP", "IPV", "CVE", "PEP",
              "ADR", "ES", "CSS", "HTML", "JS", "TS", "PY", "GB", "MB", "KB", "TB"}


def task_ids(text: str) -> list[str]:
    """Task ids in `text`, with licence and standard names excluded."""
    out = []
    for tid in TASK_RE.findall(text):
        prefix = tid.split("-")[0]
        if prefix in NOT_A_TASK:
            continue
        # A single-digit id is real on some boards (T-1) but `BSD-2` proved the shape is ambiguous,
        # so a one-digit id only counts when the board has actually seen that prefix.
        out.append(tid)
    return out
GATE_RE = re.compile(r"(?:^|\n)\s*(?:\*\*)?Gate(?:\*\*)?\s*[:：]|`(?:pytest|npm|pnpm|yarn|cargo|go|make|bundle|python)\b")
DONE_RE = re.compile(r"must be true|definition of done|\bDoD\b|done when", re.I)
OPEN_Q_RE = re.compile(r"\b(TBD|TBC|\?\?\?|decide later|to be decided|open question|needs? (?:his|her|their|the owner'?s) (?:answer|decision|call)|unanswered)\b", re.I)

#: Checked as paths, because "do not touch production" is a sentence and `.github/workflows/` is a
#: fact. A brief may add its own under a "Never decide" heading.
DEFAULT_FORBIDDEN = [
    (r"\.github/workflows/", "CI workflow files"),
    (r"\bforce[- ]push|push --force|-f\s+origin", "force pushing"),
    (r"\brm -rf\s+/", "recursive delete from root"),
    (r"\bDROP\s+(TABLE|DATABASE)\b", "dropping a table or database"),
    (r"\bgh (pr create|issue create)|git push.*--tags", "opening something outward-facing"),
    (r"\bnpm publish|cargo publish|twine upload", "publishing a package"),
]


def sections(text: str) -> list[tuple[str, str, str]]:
    """(id, title, body) per phase — the body is everything up to the next phase heading."""
    out, marks = [], list(PHASE_RE.finditer(text))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append((m.group(1), m.group(2), text[m.end():end]))
    return out


def board_state(board: Path | None) -> dict[str, bool]:
    """task id -> is_open. Reads the two marks a checklist actually has; a third invented state is
    invisible to every parser that matters, which is a real defect this refuses to inherit."""
    if not board or not board.exists():
        return {}
    state = {}
    for line in board.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"^\s*[-*]\s*\[([ xX])\]\s*(.+)$", line)
        if not m:
            continue
        ids = TASK_RE.findall(m.group(2)[:80])
        if ids:
            state[ids[0]] = m.group(1) == " "
    return state


def check(brief: Path, board: Path | None, repo: Path) -> tuple[list[str], list[str]]:
    full = brief.read_text(encoding="utf-8", errors="replace")
    # **Only the queue is checked, never the Log.** Found by running this on its own example: a log
    # entry is a RECORD and has no definition of done, so reading the log as a queue reported four
    # phantom failures and hid whether the real queue was sound. `verify_shift.py` makes the same
    # split for the mirror-image reason.
    log_at = re.search(r"^#{1,3}\s*Log\b", full, re.M | re.I)
    text = full[: log_at.start()] if log_at else full
    phases = sections(text)
    errors: list[str] = []
    warnings: list[str] = []

    if not phases:
        return (["no phases found — a brief is a numbered list of phases, each a heading like "
                 "`## Phase 1 — <what>`"], [])

    open_map = board_state(board)

    # Never-decide: the brief's own additions, plus the defaults.
    forbidden = list(DEFAULT_FORBIDDEN)
    never = re.search(r"#+\s*Never decide.*?\n(.*?)(?=\n#|\Z)", full, re.S | re.I)
    if not never:
        warnings.append("no `Never decide` section — the defaults apply, but a project that has "
                        "been burned once knows what else belongs there")

    for pid, title, body in phases:
        where = f"Phase {pid}"

        if not GATE_RE.search(body):
            errors.append(f"{where} has no gate. Name the exact command that proves it — a phase "
                          f"nothing can contradict is a phase nobody can check in the morning.")

        if not DONE_RE.search(body):
            errors.append(f"{where} has no definition of done. Write what must be TRUE afterwards, "
                          f"as observable facts.")

        q = OPEN_Q_RE.search(body)
        if q:
            errors.append(f"{where} depends on something unanswered ({q.group(0)!r}). That is day "
                          f"work — retire it while they are awake, or drop the phase.")

        for pattern, what in forbidden:
            if re.search(pattern, body, re.I):
                errors.append(f"{where} reaches {what}. That is on the never-decide list; it does "
                              f"not run unattended.")

        for tid in set(task_ids(title) + task_ids(body[:200])):
            if open_map and tid not in open_map:
                errors.append(f"{where} names {tid}, which is not on the board at all. A shift that "
                              f"works an invented task looks productive the whole time.")
            elif open_map.get(tid) is False:
                errors.append(f"{where} names {tid}, which is already CLOSED. This is the failure "
                              f"this check exists for.")

        if not body.strip():
            errors.append(f"{where} is empty.")

    if not log_at:
        errors.append("no `## Log` section — the shift has nowhere to record shas, and "
                      "`verify_shift.py` has nothing to verify.")

    if len(phases) > 8:
        warnings.append(f"{len(phases)} phases. A queue longer than the night guarantees an "
                        f"unfinished phase to unpick in the morning — unless this project has "
                        f"MEASURED that it gets through that many.")

    return errors, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("brief")
    ap.add_argument("--board", default=None, help="checklist to verify task ids against")
    ap.add_argument("--repo", default=".")
    args = ap.parse_args()

    brief = Path(args.brief)
    if not brief.exists():
        print(f"no brief at {brief}", file=sys.stderr)
        return 1

    board = Path(args.board) if args.board else None
    if board is None:
        for name in ("async-inbox.md", "TODO.md", "TASKS.md", "BACKLOG.md"):
            candidate = Path(args.repo) / name
            if candidate.exists():
                board = candidate
                break

    errors, warnings = check(brief, board, Path(args.repo))
    _full = brief.read_text(encoding="utf-8", errors="replace")
    _log = re.search(r"^#{1,3}\s*Log\b", _full, re.M | re.I)
    phases = len(sections(_full[: _log.start()] if _log else _full))

    print(f"brief   {brief}")
    print(f"board   {board or '— none found; task ids unchecked'}")
    print(f"phases  {phases}")
    print()

    for w in warnings:
        print(f"warn    {w}")
    if warnings:
        print()

    if errors:
        for e in errors:
            print(f"REFUSE  {e}")
        print()
        print(f"{len(errors)} reason(s) this brief cannot run unattended.")
        print("A failing check is a finding, not a formality — fix the brief, do not override it.")
        return 1

    print("OK      every phase names real open work, has a gate and a definition of done,")
    print("        depends on nothing unanswered, and stays off the never-decide list.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
