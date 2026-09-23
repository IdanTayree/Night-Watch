#!/usr/bin/env python3
"""Check the shift's own claims against git, before anyone reads the brief.

**A log that says work happened is not work that happened.** On one real shift, ten commit shas were
written into body prose rather than into headings; the verifier found ten claims of completion and
could confirm none of them, and the morning brief would have reported ten landed items with zero
evidence behind any of them.

So the sha goes in the heading, and this reads it from there and asks git — with
`git merge-base --is-ancestor`, not `git cat-file`. A sha can exist and still not be in your
history: an amended commit, a lost rebase, a branch nobody pushed. Existence is not the question.

    python3 scripts/verify_shift.py brief.md [--repo .] [--json]

Exit 0 when every claim verified, 1 when any did not.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

#: `### Phase 3 — what it was · `a1b2c3d`` — the sha in the HEADING, which is the whole point.
HEADING_SHA = re.compile(r"^#{2,4}\s+(.+?)\s*[·|]\s*`([0-9a-f]{7,40})`\s*$", re.M)
#: A sha loose in prose. Found so it can be reported as NOT a claim — the log's own format is the
#: contract, and quietly accepting prose would make the format optional, which is how it rotted.
PROSE_SHA = re.compile(r"(?<![`/\w])\b([0-9a-f]{7,40})\b(?![`\w])")
STOPPED = re.compile(r"^#{2,4}\s*STOPPED AFTER PHASE\s+(\S+)\s*[—:-]\s*(.+)$", re.M | re.I)
BLOCKED = re.compile(r"^\s*(?:\*\*)?BLOCKED(?:\*\*)?\b", re.M | re.I)
PHASE_HEADING = re.compile(r"^#{2,4}\s*Phase\s+(\S+?)\s*[—:-]", re.M | re.I)


def git(args: list[str], repo: Path) -> tuple[int, str]:
    try:
        out = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, timeout=20)
        return out.returncode, (out.stdout or out.stderr).strip()
    except Exception as e:
        return 127, repr(e)


def verify(brief: Path, repo: Path) -> dict:
    text = brief.read_text(encoding="utf-8", errors="replace")
    log_at = re.search(r"^#{1,3}\s*Log\b", text, re.M | re.I)
    log = text[log_at.end():] if log_at else ""
    queue = text[: log_at.start()] if log_at else text

    claims = []
    for m in HEADING_SHA.finditer(log):
        title, sha = m.group(1).strip(), m.group(2)
        code, _ = git(["merge-base", "--is-ancestor", sha, "HEAD"], repo)
        exists, _ = git(["cat-file", "-e", f"{sha}^{{commit}}"], repo)
        claims.append({
            "title": title,
            "sha": sha,
            "in_history": code == 0,
            "exists": exists == 0,
            "subject": git(["log", "-1", "--format=%s", sha], repo)[1] if exists == 0 else None,
        })

    headings_without_sha = [
        m.group(0).strip() for m in re.finditer(r"^#{2,4}\s+(?!STOPPED)(.+)$", log, re.M)
        if not HEADING_SHA.match(m.group(0))
    ]

    stopped = STOPPED.search(log)
    return {
        "brief": str(brief),
        "queued_phases": len(PHASE_HEADING.findall(queue)),
        "claims": claims,
        "verified": sum(1 for c in claims if c["in_history"]),
        "failed": [c for c in claims if not c["in_history"]],
        "headings_without_sha": headings_without_sha,
        "prose_shas": len([s for s in PROSE_SHA.findall(log)
                           if s not in {c["sha"] for c in claims}]),
        "stopped_after": stopped.group(1) if stopped else None,
        "stopped_because": stopped.group(2).strip() if stopped else None,
        "blocked": len(BLOCKED.findall(log)),
        "head": git(["rev-parse", "--short", "HEAD"], repo)[1],
        "dirty": bool(git(["status", "--porcelain"], repo)[1]),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("brief")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    brief, repo = Path(args.brief), Path(args.repo).resolve()
    if not brief.exists():
        print(f"UNMEASURED: no brief at {brief} — report this as unmeasured, not as zero.",
              file=sys.stderr)
        return 1
    if not (repo / ".git").exists():
        print(f"UNMEASURED: {repo} is not a git repo; no claim here can be checked.",
              file=sys.stderr)
        return 1

    r = verify(brief, repo)
    if args.json:
        print(json.dumps(r, indent=2))
        return 0 if not r["failed"] else 1

    print(f"brief    {r['brief']}")
    print(f"HEAD     {r['head']}{'  (dirty)' if r['dirty'] else ''}")
    print(f"queued   {r['queued_phases']} phases")
    print(f"claimed  {len(r['claims'])} · verified {r['verified']}")
    print()

    if r["failed"]:
        print("THIS GOES AT THE TOP OF THE BRIEF:")
        for c in r["failed"]:
            why = ("the sha does not exist in this repo" if not c["exists"]
                   else "the commit exists but is NOT an ancestor of HEAD — amended, rebased away, "
                        "or on a branch nobody merged")
            print(f"  FAILED  {c['sha']}  {c['title'][:60]}")
            print(f"          {why}")
        print()

    for c in r["claims"]:
        if c["in_history"]:
            print(f"  ok      {c['sha']}  {c['title'][:60]}")

    if r["headings_without_sha"]:
        print()
        print("  no sha in these log headings — they claim a phase and prove nothing:")
        for h in r["headings_without_sha"][:8]:
            print(f"          {h[:76]}")

    if r["prose_shas"]:
        print()
        print(f"  {r['prose_shas']} sha-like string(s) in prose, NOT counted. The heading is the")
        print("  contract; a sha in a sentence is a sha nothing verifies.")

    if r["stopped_after"]:
        print()
        print(f"  STOPPED after phase {r['stopped_after']} — {r['stopped_because']}")
        print("  The night was interrupted. Say so in the brief's first two lines.")
    elif r["claims"] and r["queued_phases"] and len(r["claims"]) < r["queued_phases"]:
        print()
        print(f"  UNMEASURED: {len(r['claims'])} of {r['queued_phases']} phases logged, and no")
        print("  STOPPED marker. Cannot tell finished from interrupted — do not guess which.")

    if r["blocked"]:
        print(f"\n  {r['blocked']} BLOCKED entr(ies) — each needs its reason in the brief.")

    print()
    return 1 if r["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
