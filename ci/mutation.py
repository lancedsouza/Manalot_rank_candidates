#!/usr/bin/env python3
"""Mutation ratchet on the Python files a change touches (ISS-15).

  ci/mutation.py [BASE]            mutate files changed since BASE (default origin/main)
  ci/mutation.py [BASE] --update   also raise baselines in ci/baselines/mutation.json

Score per file = (killed + timeout) / mutants, skipped mutants excluded. A file
already in the baseline may not score lower; a new file is reported only.
mutmut reads setup.cfg, so this script writes one for the run and removes it.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "ci" / "baselines" / "mutation.json"
MUTMUT = ROOT / ".venv" / "bin" / "mutmut"
SOURCES = ["app", "backend.py", "worker.py"]
# Files the tests read or import from the repo root, copied into mutmut's sandbox
ALSO_COPY = ["pytest.ini", "streamlit_app.py", "ci", "start.sh", "docker-compose.yml"]
KILLED = {"killed", "timeout"}


def changed_files(base: str) -> list:
    out = subprocess.run(["git", "diff", "--name-only", "--diff-filter=AMR", f"{base}...HEAD", "--", *SOURCES],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return sorted(f for f in out.split() if f.endswith(".py") and "/test_" not in f
                  and not Path(f).name.startswith("test_") and (ROOT / f).exists())


def write_setup_cfg(files: list) -> None:
    def block(key, items):
        return f"{key} =\n" + "".join(f"    {i}\n" for i in items)
    (ROOT / "setup.cfg").write_text(
        "[mutmut]\n" + block("source_paths", SOURCES) + block("only_mutate", files)
        + block("also_copy", ALSO_COPY) + block("pytest_add_cli_args", ["-m", "not pg", "-p", "no:cacheprovider"]))


def module_of(path: str) -> str:
    return path[:-3].replace("/", ".")


def scores(files: list) -> dict:
    out = subprocess.run([str(MUTMUT), "results", "--all", "true"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    tally = {f: [0, 0] for f in files}  # killed, counted
    for name, status in re.findall(r"^\s*(\S+): (.+)$", out, re.M):
        if status.strip() == "skipped":
            continue
        owner = max((f for f in files if name.startswith(module_of(f) + ".")), key=len, default=None)
        if owner:
            tally[owner][1] += 1
            tally[owner][0] += status.strip() in KILLED
    return {f: round(100 * k / n, 1) for f, (k, n) in tally.items() if n}


def main(args: list) -> int:
    update = "--update" in args
    args = [a for a in args if a != "--update"]
    files = changed_files(args[0] if args else "origin/main")
    if not files:
        print("Mutation ratchet: no changed source files, skipped")
        return 0
    print("Mutating:", ", ".join(files))
    shutil.rmtree(ROOT / "mutants", ignore_errors=True)
    write_setup_cfg(files)
    try:
        subprocess.run([str(MUTMUT), "run"], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        now = scores(files)
    finally:
        (ROOT / "setup.cfg").unlink(missing_ok=True)
    base = json.loads(BASELINE.read_text()) if BASELINE.exists() else {}
    errors, raised = [], dict(base)
    for f, s in sorted(now.items()):
        b = base.get(f)
        print(f"  {f}: {s}%" + (f" (baseline {b}%)" if b is not None else " (new)"))
        if b is not None and s + 0.05 < b:
            errors.append(f"{f}: {s}% < baseline {b}%")
        elif b is None or s > b:
            raised[f] = s
    if errors:
        print("Mutation ratchet FAILED (see `.venv/bin/mutmut results`):\n  " + "\n  ".join(errors))
        return 1
    if raised != base:
        if update:
            BASELINE.write_text(json.dumps(raised, indent=2, sort_keys=True) + "\n")
            print("Mutation baseline raised; commit ci/baselines/mutation.json")
        else:
            print("Mutation score above baseline; run `ci/mutation.py --update` and commit it")
    print("Mutation ratchet OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
