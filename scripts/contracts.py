"""Machine-readable boundaries and receipts; never execute commands supplied by a brief."""
from __future__ import annotations
import json
import re
from pathlib import Path, PurePosixPath

PHASE = re.compile(r'^#{2,4}\s+Phase\s+(\S+)\s+[—:-]\s+(.+)$', re.M)
TASK = re.compile(r'[A-Z][A-Z0-9]{0,9}-\d+[a-z]?')


def prose(text):
    """Blank fenced examples so their headings cannot become task/log claims."""
    return re.sub(r'^(`{3,}|~{3,}).*?\n.*?^\1\s*$', lambda m: '\n' * m[0].count('\n'), text,
                  flags=re.M | re.S)


def block(text, tag):
    matches = re.findall(r'^```' + re.escape(tag) + r'\s*\n(.*?)^```\s*$', text, re.M | re.S)
    if len(matches) != 1:
        raise ValueError(f'exactly one {tag} JSON block is required')
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f'duplicate JSON key: {key}')
            result[key] = value
        return result
    value = json.loads(matches[0], object_pairs_hook=unique)
    if not isinstance(value, dict):
        raise ValueError(f'{tag} must be an object')
    return value


def split_log(text):
    # Preserve positions while masking fences.
    masked = re.sub(r'^(`{3,}|~{3,}).*?\n.*?^\1\s*$',
                    lambda m: ''.join('\n' if c == '\n' else ' ' for c in m[0]), text, flags=re.M | re.S)
    logs = list(re.finditer(r'^#{1,3}\s+Log\s*$', masked, re.M | re.I))
    if len(logs) != 1:
        raise ValueError('exactly one Log heading is required')
    m = logs[0]
    return text[:m.start()], text[m.end():]


def sections(text):
    masked = re.sub(r'^(`{3,}|~{3,}).*?\n.*?^\1\s*$',
                    lambda m: ''.join('\n' if c == '\n' else ' ' for c in m[0]), text, flags=re.M | re.S)
    marks = list(PHASE.finditer(masked))
    return [(m[1], m[2], text[m.end():marks[i+1].start() if i+1 < len(marks) else len(text)])
            for i, m in enumerate(marks)]


def path_name(value, repo, allow_root=False):
    if not isinstance(value, str) or not value.strip() or '\\' in value or '\x00' in value:
        raise ValueError('paths must be nonempty repository-relative POSIX paths')
    p = PurePosixPath(value)
    if p.is_absolute() or '..' in p.parts or any(c in value for c in '*?['):
        raise ValueError(f'not a literal repository path: {value}')
    normalized = str(p)
    if normalized == '.' and not allow_root:
        raise ValueError('a whole-repository path is not a bounded write scope')
    try:
        (repo / normalized).resolve().relative_to(repo.resolve())
    except ValueError:
        raise ValueError(f'path escapes repository through a symlink: {value}')
    return normalized


def overlaps(a, b):
    return a == '.' or b == '.' or a == b or a.startswith(b + '/') or b.startswith(a + '/')


def contains(parent, child):
    return parent == '.' or child == parent or child.startswith(parent + '/')


def load_queue(text, repo):
    queue, log = split_log(text)
    policy = block(queue, 'night-watch-policy')
    if type(policy.get('version')) is not int or policy.get('version') != 1 or not re.fullmatch(r'[0-9a-f]{40}', str(policy.get('base_commit', ''))):
        raise ValueError('policy needs version 1 and a full base_commit SHA')
    protected = policy.get('protected_paths')
    if not isinstance(protected, list) or any(not isinstance(p, str) for p in protected):
        raise ValueError('protected_paths must be a list (use [] explicitly if none)')
    policy['protected_paths'] = [path_name(p, repo) for p in ['.git', '.github/workflows', *protected]]
    phases = []
    for pid, title, body in sections(queue):
        phase = block(body, 'night-watch-phase')
        if not TASK.fullmatch(str(phase.get('task', ''))):
            raise ValueError(f'Phase {pid} needs one explicit task id')
        if not re.match(re.escape(phase['task']) + r'(?=[:\s])', title):
            raise ValueError(f'Phase {pid} heading must start with its task id')
        for key in ('gate', 'done', 'cwd'):
            if not isinstance(phase.get(key), str) or not phase[key].strip():
                raise ValueError(f'Phase {pid} needs nonempty {key}')
        phase['cwd'] = path_name(phase['cwd'], repo, allow_root=True)
        paths = phase.get('paths')
        if not isinstance(paths, list) or not paths:
            raise ValueError(f'Phase {pid} needs a nonempty paths list')
        phase['paths'] = [path_name(p, repo) for p in paths]
        if any(overlaps(p, banned) for p in phase['paths'] for banned in policy['protected_paths']):
            raise ValueError(f'Phase {pid} write scope overlaps a protected path')
        if re.search(r'\b(TBD|TBC|unanswered|decide later|to be decided)\b|\?\?\?',
                     phase['done'] + '\n' + phase['gate'], re.I):
            raise ValueError(f'Phase {pid} has an unresolved contract')
        phase.update(id=pid, title=title)
        phases.append(phase)
    if not phases:
        raise ValueError('no queued phases')
    for key in ('id', 'task'):
        if len({p[key] for p in phases}) != len(phases):
            raise ValueError(f'duplicate phase {key}')
    return policy, phases, log


def board_state(board):
    if board is None or not board.is_file():
        raise ValueError('a readable task board is required; pass --board')
    state = {}
    pattern = re.compile(r'^\s*[-*]\s+\[([ xX])\]\s+(?:\*\*)?(' + TASK.pattern + r')(?=[:\s*])')
    for line in prose(board.read_text()).splitlines():
        m = pattern.match(line)
        if m:
            if m[2] in state:
                raise ValueError(f'duplicate task on board: {m[2]}')
            state[m[2]] = m[1] == ' '
    if not state:
        raise ValueError('board contains no parseable task rows')
    return state
