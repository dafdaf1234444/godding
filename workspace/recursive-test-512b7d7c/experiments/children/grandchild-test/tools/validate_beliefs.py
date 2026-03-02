#!/usr/bin/env python3
"""Validate structural integrity of the swarm belief graph."""
import re, sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def parse_beliefs(path):
    text = Path(path).read_text()
    beliefs = []
    for m in re.finditer(r"^###\s+(?P<id>B\d+):\s*(?P<stmt>.+?)$", text, re.MULTILINE):
        i = m.end()
        matches = list(re.finditer(r"^###\s+B\d+:", text[i:], re.MULTILINE))
        end = i + matches[0].start() if matches else len(text)
        block = text[i:end]
        ev = re.search(r"\*\*Evidence\*\*:\s*(\S+)", block, re.I)
        fa = re.search(r"\*\*Falsified if\*\*:\s*(.+?)$", block, re.M | re.I)
        dp = re.search(r"\*\*Depends on\*\*:\s*(.+?)$", block, re.M | re.I)
        lt = re.search(r"\*\*Last tested\*\*:\s*(.+?)$", block, re.M | re.I)
        dep_ids = []
        if dp:
            dt = dp.group(1).strip()
            if dt.lower() not in ("none", "n/a", "-", ""):
                dep_ids = re.findall(r"B\d+", dt)
        beliefs.append({
            "id": m.group("id"), "statement": m.group("stmt").strip(),
            "evidence": ev.group(1).strip().lower() if ev else "",
            "falsification": fa.group(1).strip() if fa else "",
            "depends_on": dep_ids,
            "last_tested": lt.group(1).strip() if lt else "",
        })
    return beliefs

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "beliefs/DEPS.md"
    if not Path(path).exists():
        print(f"ERROR: {path} not found"); return 1
    beliefs = parse_beliefs(path)
    if not beliefs:
        print(f"ERROR: No beliefs found in {path}"); return 1
    fails = []
    known = {b["id"] for b in beliefs}
    for b in beliefs:
        if b["evidence"] not in ("observed", "theorized"):
            fails.append(f"FAIL: {b['id']} invalid evidence type '{b['evidence']}'")
        if not b["falsification"]:
            fails.append(f"FAIL: {b['id']} missing falsification condition")
        if not b["last_tested"]:
            fails.append(f"FAIL: {b['id']} missing Last tested field")
        for d in b["depends_on"]:
            if d not in known:
                fails.append(f"FAIL: {b['id']} depends on {d} which doesn't exist")
    n_obs = sum(1 for b in beliefs if b["evidence"] == "observed")
    n_the = sum(1 for b in beliefs if b["evidence"] == "theorized")
    for f in fails: print(f)
    print(f"\nSummary: {len(beliefs)} beliefs, {n_obs} observed, {n_the} theorized, {len(fails)} errors")
    print("RESULT:", "FAIL" if fails else "PASS")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
