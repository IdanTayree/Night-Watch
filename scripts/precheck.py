#!/usr/bin/env python3
"""Validate a structured shift brief before arming. Exit 0 valid, 1 refused.

This checks declarations, not command safety, test quality or filesystem permissions.
See references/contracts.md. No command from the brief is executed.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
from contracts import load_queue, board_state


def check(brief, board, repo):
    try:
        policy, phases, _ = load_queue(brief.read_text(), repo)
        state = board_state(board)
        errors = [f"Phase {p['id']}: {p['task']} is missing or closed on the board"
                  for p in phases if not state.get(p['task'], False)]
        result = subprocess.run(['git', 'merge-base', '--is-ancestor', policy['base_commit'], 'HEAD'],
                                cwd=repo, capture_output=True, timeout=20)
        if result.returncode:
            errors.append('base_commit must be an ancestor of this repository HEAD')
        return errors, (['More than eight phases; confirm a measured time budget.'] if len(phases) > 8 else [])
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        return [str(exc)], []


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('brief', type=Path)
    ap.add_argument('--board', type=Path)
    ap.add_argument('--repo', type=Path, default=Path('.'))
    args = ap.parse_args()
    board = args.board
    if board is None:
        board = next((args.repo / n for n in ('async-inbox.md', 'TODO.md', 'TASKS.md', 'BACKLOG.md')
                      if (args.repo / n).is_file()), None)
    errors, warnings = check(args.brief, board, args.repo)
    for message in warnings:
        print('WARN   ' + message)
    for message in errors:
        print('REFUSE ' + message)
    if not errors:
        print('OK declared tasks, contracts, base commit and path boundaries validated.')
        print('Before arming: run the gates and review permissions; this is not a sandbox.')
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
