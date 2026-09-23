#!/usr/bin/env python3
"""Read the project and write what a night shift needs to know about it.

**Generated rather than asked.** Every answer in here is already in the repo, and asking for it
spends the one thing the day shift exists to protect. What the profile gets wrong is cheap to
correct in one message; what it never asked is a question the night discovers at 2am.

No dependencies beyond the standard library, by design: a tool that needs installing before it can
tell you whether a project is ready is one more thing to go wrong at the worst time.

    python3 scripts/profile.py [path] [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

#: A gate is anything that can go red on its own. The value is what to run and where.
#: Ordered by how much a red result actually tells you — a type error is narrower than a test suite,
#: but it is also unambiguous, and a shift that cannot run the suite can still run this.
GATE_PROBES = [
    # (label, file that implies it, command, how to confirm it is really configured)
    ("pytest", "pytest.ini", "python -m pytest -q", None),
    ("pytest", "pyproject.toml", "python -m pytest -q", "pytest"),
    ("pytest", "setup.cfg", "python -m pytest -q", "[tool:pytest]"),
    ("mypy", "mypy.ini", "mypy .", None),
    ("ruff", "ruff.toml", "ruff check .", None),
    ("cargo test", "Cargo.toml", "cargo test", None),
    ("cargo clippy", "Cargo.toml", "cargo clippy -- -D warnings", None),
    ("go test", "go.mod", "go test ./...", None),
    ("rspec", ".rspec", "bundle exec rspec", None),
]

#: Script names in package.json that are gates rather than chores. `dev` and `start` are not gates:
#: they do not terminate, and a shift that runs one waits forever.
JS_GATE_SCRIPTS = ("test", "typecheck", "type-check", "tsc", "lint", "check", "build", "e2e")


def run(cmd: list[str], cwd: Path) -> str:
    try:
        out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=20)
        return out.stdout.strip()
    except Exception:
        return ""


def package_manager(root: Path) -> str | None:
    for lock, name in (("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"),
                       ("bun.lockb", "bun"), ("package-lock.json", "npm")):
        if (root / lock).exists():
            return name
    return "npm" if (root / "package.json").exists() else None


def js_gates(root: Path) -> list[dict]:
    """Gates from package.json, read from the file rather than guessed from convention."""
    pkg = root / "package.json"
    if not pkg.exists():
        return []
    try:
        scripts = json.loads(pkg.read_text(encoding="utf-8")).get("scripts", {}) or {}
    except Exception:
        return []
    pm = package_manager(root) or "npm"
    runner = f"{pm} run" if pm != "npm" else "npm run"
    return [{"label": name, "command": f"{runner} {name}", "cwd": ".", "source": "package.json"}
            for name in scripts if name in JS_GATE_SCRIPTS]


def native_gates(root: Path) -> list[dict]:
    found, seen = [], set()
    for label, marker, command, needle in GATE_PROBES:
        path = root / marker
        if not path.exists():
            continue
        if needle:
            try:
                if needle not in path.read_text(encoding="utf-8", errors="replace"):
                    continue
            except OSError:
                continue
        if (label, command) in seen:
            continue
        seen.add((label, command))
        found.append({"label": label, "command": command, "cwd": ".", "source": marker})
    return found


def nested_gates(root: Path, depth: int = 2) -> list[dict]:
    """Sub-projects. A monorepo's real gate often lives one directory down, and a shift that only
    looks at the root concludes there are none."""
    out = []
    for pkg in root.glob("*/package.json"):
        if "node_modules" in pkg.parts:
            continue
        for gate in js_gates(pkg.parent):
            gate["cwd"] = pkg.parent.name
            out.append(gate)
    for cargo in root.glob("*/Cargo.toml"):
        out.append({"label": "cargo test", "command": "cargo test",
                    "cwd": cargo.parent.name, "source": f"{cargo.parent.name}/Cargo.toml"})
    # Nested Python, which the first version of this script missed on the project it was written
    # for: the root had no pytest config and the suite lived one directory down, so the profile
    # reported two gates where there were three — and the biggest one was the one it could not see.
    # `conftest.py` and `test_*.py` are the honest signals; a config file is not required to have a
    # suite, and plenty of real projects do not have one.
    for sub in sorted(root.glob("*/")):
        if sub.name.startswith(".") or sub.name in {"node_modules", "target", "dist", "build"}:
            continue
        has_tests = any(sub.glob("test_*.py")) or (sub / "conftest.py").exists() \
            or any(sub.glob("tests/test_*.py"))
        if has_tests and not any(g["cwd"] == sub.name and "pytest" in g["label"] for g in out):
            out.append({"label": "pytest", "command": "python -m pytest -q",
                        "cwd": sub.name, "source": f"{sub.name}/ (test files found)"})
    return out[:14]


def commit_convention(root: Path) -> dict:
    """What recent commits look like, so the shift writes messages that match rather than inventing
    a style. Read from history, which is the only honest source for a convention."""
    log = run(["git", "log", "-40", "--format=%s"], root)
    subjects = [s for s in log.splitlines() if s.strip()]
    if not subjects:
        return {"sample": [], "pattern": None}
    conventional = sum(bool(re.match(r"^(feat|fix|chore|docs|test|refactor|perf|build|ci)(\(.+\))?!?: ", s))
                       for s in subjects)
    ticketed = sum(bool(re.match(r"^[A-Z]+-\d+", s)) for s in subjects)
    pattern = None
    if conventional > len(subjects) * 0.5:
        pattern = "conventional commits (feat:/fix:/chore:)"
    elif ticketed > len(subjects) * 0.5:
        pattern = "ticket id first (ABC-123: …)"
    return {"sample": subjects[:5], "pattern": pattern,
            "counted": {"conventional": conventional, "ticketed": ticketed, "of": len(subjects)}}


def boards(root: Path) -> list[str]:
    names = ("TODO.md", "TASKS.md", "async-inbox.md", "BACKLOG.md", "ROADMAP.md", "roadmap.md")
    found = [n for n in names if (root / n).exists()]
    found += [str(p.relative_to(root)) for p in root.glob("docs/*.md")
              if p.name.lower() in {"todo.md", "tasks.md", "backlog.md", "next.md"}]
    return found


def listening_ports(root: Path) -> list[str]:
    """What is already running. Not to manage it — to keep the shift's hands off it."""
    out = run(["lsof", "-nP", "-iTCP", "-sTCP:LISTEN"], root)
    seen = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 9 and ":" in parts[8]:
            entry = f"{parts[0]} {parts[8].rsplit(':', 1)[-1]}"
            if entry not in seen:
                seen.append(entry)
    return seen[:20]


def build(root: Path) -> dict:
    gates = native_gates(root) + js_gates(root) + nested_gates(root)
    return {
        "root": str(root),
        "is_git": (root / ".git").exists(),
        "branch": run(["git", "rev-parse", "--abbrev-ref", "HEAD"], root) or None,
        "head": run(["git", "rev-parse", "--short", "HEAD"], root) or None,
        "dirty": bool(run(["git", "status", "--porcelain"], root)),
        "package_manager": package_manager(root),
        "gates": gates,
        "gate_count": len(gates),
        "boards": boards(root),
        "commit_convention": commit_convention(root),
        "listening": listening_ports(root),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--json", action="store_true", help="machine-readable only")
    args = ap.parse_args()

    root = Path(args.path).resolve()
    profile = build(root)

    out_dir = root / ".night-watch"
    out_dir.mkdir(exist_ok=True)
    (out_dir / "profile.json").write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(profile, indent=2))
        return 0

    print(f"project   {root}")
    print(f"git       {profile['branch'] or '—'} @ {profile['head'] or '—'}"
          f"{'  (dirty)' if profile['dirty'] else ''}")
    print(f"packages  {profile['package_manager'] or '—'}")
    print()
    if profile["gates"]:
        print(f"gates     {profile['gate_count']} found — RUN ONE AND WATCH IT PASS before arming")
        for g in profile["gates"]:
            where = "" if g["cwd"] == "." else f"   (in {g['cwd']}/)"
            print(f"          · {g['command']}{where}")
    else:
        print("gates     NONE FOUND")
        print()
        print("          A night shift on a project with no gate produces changes nobody can")
        print("          check. Do not arm one. Build the first gate instead — that is a good")
        print("          day's work, and it makes every night after it possible.")
    print()
    print(f"boards    {', '.join(profile['boards']) or '—'}")
    conv = profile["commit_convention"]
    print(f"commits   {conv['pattern'] or 'no dominant pattern'}")
    for s in conv["sample"][:3]:
        print(f"          · {s[:78]}")
    if profile["listening"]:
        print()
        print("running   leave these alone unless the brief says otherwise")
        for p in profile["listening"][:8]:
            print(f"          · {p}")
    print()
    print(f"written   {out_dir / 'profile.json'}")
    print()
    print("Now correct whatever this got wrong — that is the cheapest question of the whole cycle.")
    return 0 if profile["gates"] else 1


if __name__ == "__main__":
    sys.exit(main())
