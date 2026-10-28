#!/usr/bin/env python3
"""Flag known ZenUML pitfalls in flow files. Exit 1 if any are found."""
import re
import sys

# unquoted text with spaces or punctuation is parsed as code and renders as stray Loop boxes
UNSAFE_RETURN = re.compile(r'^\s*return\s+(?!")\S.*[\s,()+*]')
UNSAFE_COND = re.compile(r'^\s*(?:\}\s*else\s+)?(?:if|loop|while)\s*\((?!")(.*)\)\s*\{')
SIMPLE_COND = re.compile(r'\w+(\s*(>=|<=|==|!=|<|>)\s*\w+)?')


def lint(path):
    problems = []
    lines = open(path, encoding="utf-8").read().splitlines()
    if not lines or lines[0].strip() != "```mermaid" or len(lines) < 3 or lines[1].strip() != "zenuml":
        problems.append((1, "file must start with ```mermaid then zenuml"))
    elif not lines[2].startswith("title "):
        problems.append((3, "third line must be 'title <FLOW-ID> <name>'"))
    for n, line in enumerate(lines, 1):
        if UNSAFE_RETURN.match(line):
            problems.append((n, "unquoted multi-word return renders as Loop boxes; quote it"))
        m = UNSAFE_COND.match(line)
        if m and not SIMPLE_COND.fullmatch(m.group(1).strip()):
            problems.append((n, "unquoted condition renders as Loop boxes; quote it"))
        if re.match(r"^\s*opt\s*\{", line) and n > 1 and lines[n - 2].strip().startswith("//"):
            problems.append((n, "commented opt: prefer if(condition) so the label sits inside the box"))
    return problems


if __name__ == "__main__":
    bad = 0
    for p in sys.argv[1:]:
        for n, msg in lint(p):
            print(f"{p}:{n}: {msg}")
            bad += 1
    sys.exit(1 if bad else 0)
