#!/usr/bin/env python3
"""Ratchet: findings per file and coverage may only get better (ISS-02).

  ci/ratchet.py lint             check ruff counts against ci/baselines/ruff.json
  ci/ratchet.py coverage FILE    check coverage.json total against ci/baselines/coverage.json
  add --update to lower a baseline after an improvement (never raises it)
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "ci" / "baselines"
TARGETS = ["app", "backend.py", "worker.py", "streamlit_app.py", "tests", "ci"]


def ruff_counts() -> dict:
    ruff = ROOT / ".venv" / "bin" / "ruff"
    cmd = [str(ruff) if ruff.exists() else "ruff", "check", "--output-format", "json", "--exit-zero", *TARGETS]
    out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True).stdout
    counts: dict = {}
    for f in json.loads(out):
        rel = str(Path(f["filename"]).resolve().relative_to(ROOT))
        counts[rel] = counts.get(rel, 0) + 1
    return counts


def tracked_py() -> set:
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.py"],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return set(out.split())


def lint(update: bool) -> int:
    path = BASE / "ruff.json"
    base = json.loads(path.read_text()) if path.exists() else {}
    now = ruff_counts()
    errors, lowered = [], dict(base)
    for f in sorted(tracked_py() | set(now)):
        n, b = now.get(f, 0), base.get(f)
        if b is None and n:
            errors.append(f"{f}: new file has {n} findings (must be 0)")
        elif b is not None and n > b:
            errors.append(f"{f}: {n} findings, baseline {b}")
        elif b is not None and n < b:
            lowered[f] = n
    for f in list(lowered):
        if lowered[f] == 0 or f not in tracked_py():
            lowered.pop(f)
    if errors:
        print("Lint ratchet FAILED (run `.venv/bin/ruff check <file>` to see them):\n  " + "\n  ".join(errors))
        return 1
    if lowered != base:
        if update:
            path.write_text(json.dumps(lowered, indent=2, sort_keys=True) + "\n")
            print("Lint baseline lowered; commit ci/baselines/ruff.json")
        else:
            print("Lint improved below baseline; run `ci/ratchet.py lint --update` and commit it")
    print(f"Lint ratchet OK ({sum(now.values())} findings, baseline {sum(base.values())})")
    return 0


def coverage(report: str, update: bool) -> int:
    path = BASE / "coverage.json"
    base = json.loads(path.read_text())["total_percent"] if path.exists() else 0.0
    now = round(json.loads(Path(report).read_text())["totals"]["percent_covered"], 2)
    if now + 0.01 < base:
        print(f"Coverage ratchet FAILED: {now}% < baseline {base}%")
        return 1
    if update and now > base:
        path.write_text(json.dumps({"total_percent": now}, indent=2) + "\n")
        print("Coverage baseline raised; commit ci/baselines/coverage.json")
    print(f"Coverage ratchet OK ({now}%, baseline {base}%)")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    update = "--update" in args
    args = [a for a in args if a != "--update"]
    if args[:1] == ["lint"]:
        sys.exit(lint(update))
    if args[:1] == ["coverage"]:
        sys.exit(coverage(args[1], update))
    sys.exit(__doc__)
