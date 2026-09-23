#!/usr/bin/env python3
"""Verify structured shift evidence. Exit 0 complete, 1 invalid, 2 explicitly incomplete.

Checks ancestry, task mapping, changed paths and recorded gate evidence, not test truth.
Does not run the brief's commands. See references/contracts.md.
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from pathlib import Path
from contracts import load_queue, sections, block, contains, overlaps, prose


def git(args, repo):
    p = subprocess.run(['git', *args], cwd=repo, capture_output=True, text=True, timeout=20)
    if p.returncode:
        raise ValueError('git ' + ' '.join(args) + ': ' + p.stderr.strip())
    return p.stdout.rstrip('\n')


def ancestor(commit, ref, repo):
    return subprocess.run(['git', 'merge-base', '--is-ancestor', commit, ref], cwd=repo,
                          capture_output=True, timeout=20).returncode == 0


def verify(brief, repo, require_ref=None):
    errors, claims = [], []
    result = {'status': 'invalid', 'errors': errors, 'claims': claims, 'queued_phases': 0}
    try:
        policy, phases, log = load_queue(brief.read_text(), repo)
        result['queued_phases'] = len(phases)
        if not ancestor(policy['base_commit'], 'HEAD', repo):
            raise ValueError('base_commit is not in HEAD history')
        if git(['status', '--porcelain', '--untracked-files=all'], repo):
            errors.append('working tree is dirty; commit the receipt or report unfinished work')
        stopped = list(re.finditer(r'^#{2,4}\s+STOPPED AFTER PHASE (\S+)\s+[—:-]\s+(.+)$', prose(log), re.M))
        logs = sections(log)
        if len(stopped) > 1:
            errors.append('multiple STOPPED markers')
        if len(logs) > len(phases):
            errors.append('extra or duplicate phase receipts')
        seen, previous = set(), policy['base_commit']
        incomplete = False
        for i, (pid, title, body) in enumerate(logs):
            if i >= len(phases):
                break
            phase = phases[i]
            if pid != phase['id']:
                errors.append(f'phase {pid} is duplicate, unknown or out of queue order')
            receipt = block(body, 'night-watch-receipt')
            status = receipt.get('status')
            if receipt.get('task') != phase['task']:
                errors.append(f'phase {pid} task does not match queue')
            if status == 'blocked':
                incomplete = True
                if not isinstance(receipt.get('reason'), str) or not receipt['reason'].strip():
                    errors.append(f'phase {pid} blocked without reason')
                if i != len(logs)-1:
                    errors.append('blocked phase must stop this sequential queue')
                continue
            if status not in ('completed', 'refused'):
                errors.append(f'phase {pid} has invalid status')
                continue
            if status == 'refused' and (not isinstance(receipt.get('reason'), str) or not receipt['reason'].strip() or
                                       not isinstance(receipt.get('would_change'), str) or not receipt['would_change'].strip()):
                errors.append(f'phase {pid} refusal needs reason and would_change')
            sha_match = re.search(r'\s[·|]\s*`([0-9a-f]{7,40})`\s*$', title)
            if not sha_match:
                errors.append(f'phase {pid} heading has no commit SHA')
                continue
            sha = git(['rev-parse', '--verify', sha_match[1] + '^{commit}'], repo)
            if sha in seen or sha == previous or not ancestor(previous, sha, repo) or not ancestor(sha, 'HEAD', repo):
                errors.append(f'phase {pid} commit is repeated, out of order or outside HEAD history')
            seen.add(sha)
            previous = sha
            if require_ref and not ancestor(sha, require_ref, repo):
                errors.append(f'phase {pid} commit not in required ref {require_ref}')
            subject = git(['log', '-1', '--format=%s', sha], repo)
            if not re.match(re.escape(phase['task']) + r'(?=[:\s])', subject):
                errors.append(f'phase {pid} commit subject does not name its task')
            parents = git(['rev-list', '--parents', '-n', '1', sha], repo).split()[1:]
            if len(parents) != 1:
                errors.append(f'phase {pid} must reference a single-parent implementation commit')
                continue
            # --no-renames exposes BOTH source and destination so moves cannot evade boundaries.
            changed = git(['diff', '--name-only', '-z', '--no-renames', parents[0], sha], repo).split('\0')
            changed = [p for p in changed if p]
            if not changed:
                errors.append(f'phase {pid} implementation commit has no changes')
            for path in changed:
                if (not any(contains(p, path) for p in phase['paths']) or
                        any(overlaps(p, path) for p in policy['protected_paths'])):
                    errors.append(f'phase {pid} changed undeclared/protected path: {path}')
            gate = receipt.get('gate', {})
            if not isinstance(gate, dict):
                errors.append(f'phase {pid} gate is not an object')
                gate = {}
            if (gate.get('command') != phase['gate'] or gate.get('cwd') != phase['cwd'] or
                    type(gate.get('exit_code')) is not int or gate.get('exit_code') != 0 or
                    gate.get('commit') != sha or not isinstance(gate.get('output'), str) or not gate['output'].strip()):
                errors.append(f'phase {pid} lacks matching command/cwd/commit, exit 0 and recorded output')
            claims.append({'phase': pid, 'task': phase['task'], 'sha': sha, 'status': status, 'paths': changed})
        # Any apparent completion heading must be parsed; arbitrary prose is not a receipt.
        headings = re.findall(r'^#{2,4}\s+(.+)$', prose(log), re.M)
        if any(not h.startswith('Phase ') and not h.startswith('STOPPED AFTER PHASE ') for h in headings):
            errors.append('unrecognized log heading; use Phase or STOPPED headings')
        if len(logs) < len(phases):
            incomplete = True
        if incomplete and not stopped:
            errors.append('unfinished queue has no explicit STOPPED marker')
        if stopped:
            expected = logs[-1][0] if logs else '0'
            if stopped[0][1] != expected:
                errors.append('STOPPED marker does not identify the last attempted phase (or 0)')
            incomplete = True
        result['status'] = 'invalid' if errors else ('incomplete' if incomplete else 'complete')
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        errors.append(str(exc))
    result['verified'] = len(claims) if not errors else 0
    result['exit_code'] = {'complete': 0, 'invalid': 1, 'incomplete': 2}[result['status']]
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('brief', type=Path)
    ap.add_argument('--repo', type=Path, default=Path('.'))
    ap.add_argument('--require-ref', help='also require ancestry in this already-fetched remote ref')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    result = verify(args.brief, args.repo.resolve(), args.require_ref)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{result['status'].upper()}: {result['verified']}/{result['queued_phases']} phase receipts verified")
        for error in result['errors']:
            print('FAIL ' + error)
        print('Recorded gate results require independent review; no gate was rerun by this verifier.')
    return result['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
