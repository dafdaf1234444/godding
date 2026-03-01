#!/usr/bin/env python3

import hashlib
import re
import sys
from pathlib import Path

# Consolidated validation functions (merged from validate_beliefs_extras.py S359)

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def parse_beliefs(path: str) -> list[dict]:
    text = _read_text(Path(path))
    beliefs = []
    pat = re.compile(r"^###\s+(?P<id>B\d+):\s*(?P<statement>.+?)$", re.MULTILINE)
    matches = list(pat.finditer(text))
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end]
        evidence = re.search(r"\*\*Evidence\*\*:\s*(\S+)", block, re.IGNORECASE)
        falsified = re.search(r"\*\*Falsified if\*\*:\s*(.+?)$", block, re.MULTILINE | re.IGNORECASE)
        depends = re.search(r"\*\*Depends on\*\*:\s*(.+?)$", block, re.MULTILINE | re.IGNORECASE)
        tested = re.search(r"\*\*Last tested\*\*:\s*(.+?)$", block, re.MULTILINE | re.IGNORECASE)
        depended = re.search(r"\*\*Depended on by\*\*:\s*(.+?)$", block, re.MULTILINE | re.IGNORECASE)
        dep_ids = []
        if depends:
            s = depends.group(1).strip().lower()
            if s not in ("none", "n/a", "-", ""):
                dep_ids = re.findall(r"B\d+", depends.group(1))
        rev_ids = []
        if depended:
            s = depended.group(1).strip().lower()
            if s not in ("none", "n/a", "-", ""):
                rev_ids = re.findall(r"B\d+", depended.group(1))
        beliefs.append({
            "id": m.group("id"),
            "statement": m.group("statement").strip(),
            "evidence": evidence.group(1).strip().lower() if evidence else "",
            "falsification": falsified.group(1).strip() if falsified else "",
            "depends_on": dep_ids,
            "depended_on_by": rev_ids,
            "last_tested": tested.group(1).strip() if tested else "",
        })
    return beliefs


def check_format(beliefs: list[dict]) -> list[str]:
    out = []
    for b in beliefs:
        bid = b["id"]
        if b["evidence"] not in ("observed", "theorized"):
            out.append(
                f"FAIL FORMAT: {bid} missing or invalid evidence type "
                f"(got '{b['evidence']}', need 'observed' or 'theorized')"
            )
        if not b["falsification"] or b["falsification"].lower() in ("", "none", "n/a"):
            out.append(f"WARN FORMAT: {bid} missing falsification condition")
        if not b["last_tested"]:
            out.append(f"FAIL FORMAT: {bid} missing 'Last tested' field")
    return out


def check_existence(beliefs: list[dict]) -> list[str]:
    known = {b["id"] for b in beliefs}
    out = []
    for b in beliefs:
        for dep in b["depends_on"]:
            if dep not in known:
                out.append(f"FAIL EXISTENCE: {b['id']} depends on {dep}, which is not defined")
    return out


def check_cycles(beliefs: list[dict]) -> list[str]:
    adj = {b["id"]: b["depends_on"] for b in beliefs}
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {bid: WHITE for bid in adj}
    out = []

    def dfs(node: str, path: list[str]) -> None:
        color[node] = GRAY
        for dep in adj.get(node, []):
            if dep not in color:
                continue
            if color[dep] == GRAY:
                start = path.index(dep)
                out.append(f"FAIL CYCLE: circular dependency: {' -> '.join(path[start:] + [dep])}")
            elif color[dep] == WHITE:
                dfs(dep, path + [dep])
        color[node] = BLACK

    for bid in adj:
        if color[bid] == WHITE:
            dfs(bid, [bid])
    return out


def check_dep_consistency(beliefs: list[dict]) -> list[str]:
    out = []
    known = {b["id"] for b in beliefs}
    forward = {b["id"]: set(b["depends_on"]) for b in beliefs}
    reverse = {b["id"]: set(b.get("depended_on_by", [])) for b in beliefs}
    for bid, deps in forward.items():
        for dep in deps:
            if dep in known and bid not in reverse.get(dep, set()):
                out.append(f"WARN DEP_SYNC: {dep} should list {bid} in 'Depended on by'")
    for bid, rev_deps in reverse.items():
        for rdep in rev_deps:
            if rdep in known and bid not in forward.get(rdep, set()):
                out.append(f"WARN DEP_SYNC: {rdep} should list {bid} in 'Depends on'")
    return out


def check_orphans(beliefs: list[dict]) -> list[str]:
    depended_on = set()
    for b in beliefs:
        depended_on.update(b["depends_on"])
    out = []
    for b in beliefs:
        if b["id"] not in depended_on and not b["falsification"]:
            out.append(f"WARN ORPHAN: {b['id']} has no dependents and no falsification condition")
    return out


def cascade_check(beliefs: list[dict], changed_id: str) -> list[str]:
    by_id = {b["id"]: b for b in beliefs}
    if changed_id not in by_id:
        return [f"FAIL CASCADE: unknown belief ID '{changed_id}'"]
    forward: dict[str, list[str]] = {}
    for b in beliefs:
        for dep in b.get("depends_on", []):
            forward.setdefault(dep, []).append(b["id"])
    visited, queue, downstream = set(), [changed_id], []
    while queue:
        for child in forward.get(queue.pop(0), []):
            if child not in visited:
                visited.add(child)
                downstream.append(child)
                queue.append(child)
    if not downstream:
        return [f"INFO CASCADE: {changed_id} has no downstream beliefs"]
    changed_date = by_id[changed_id].get("last_tested", "")[:10]
    out = []
    for did in downstream:
        dep_date = by_id[did].get("last_tested", "")[:10]
        preview = by_id[did]["statement"][:55].rstrip()
        if not dep_date or (changed_date and dep_date < changed_date):
            out.append(f"WARN STALE: {did} ('{preview}') — last {dep_date or 'never'} vs {changed_id} {changed_date}")
        else:
            out.append(f"INFO CASCADE: {did} last {dep_date} >= {changed_id} {changed_date}")
    return out


def parse_phil_claims() -> list[dict]:
    """Parse PHILOSOPHY.md claims table (PHIL-N entries). Added S348 (CORE P14)."""
    phil_path = REPO_ROOT / "beliefs" / "PHILOSOPHY.md"
    text = _read_text(phil_path)
    if not text:
        return []
    claims = []
    in_claims = False
    for line in text.splitlines():
        # Detect the claims table header: | ID | Claim ...
        if "| ID |" in line and "Claim" in line:
            in_claims = True
            continue
        if in_claims and re.match(r"^\s*\|[-| ]+\|\s*$", line):
            continue  # skip separator row
        # Stop at blank line, section marker, or horizontal rule after table
        if in_claims and (
            not line.strip() or line.startswith("##") or line.strip() == "---"
        ):
            break
        if not in_claims:
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 5:
            continue
        pid = cells[1]
        if not re.match(r"PHIL-\d+$", pid):
            continue
        # S356 added Grounding column: | ID | Claim | Type | Grounding | Status |
        # Handle both 4-column (pre-S356) and 5-column (post-S356) formats (L-599)
        if len(cells) >= 7:  # 5 data columns + 2 empty borders
            claims.append({
                "id": pid,
                "claim": cells[2],
                "type": cells[3].strip().lower(),
                "grounding": cells[4].strip().lower(),
                "status": cells[5],
            })
        else:
            claims.append({
                "id": pid,
                "claim": cells[2],
                "type": cells[3].strip().lower(),
                "grounding": "",
                "status": cells[4],
            })
    return claims


def check_phil_format(claims: list[dict]) -> list[str]:
    """Validate PHIL claims have required fields and grounding labels (L-599)."""
    VALID_GROUNDING = {"grounded", "partial", "axiom", "aspirational", "unverified", "metaphor"}
    out = []
    for c in claims:
        if c["type"] not in ("observed", "axiom"):
            out.append(
                f"FAIL PHIL: {c['id']} invalid type '{c['type']}' "
                f"(need 'observed' or 'axiom')"
            )
        if not c["status"].startswith("active"):
            out.append(f"WARN PHIL: {c['id']} status not active: '{c['status'][:50]}'")
        # L-599 grounding enforcement: every PHIL claim must have a grounding label
        grounding = c.get("grounding", "")
        if grounding and grounding not in VALID_GROUNDING:
            out.append(f"WARN PHIL: {c['id']} invalid grounding '{grounding}' "
                       f"(valid: {', '.join(sorted(VALID_GROUNDING))})")
        if not grounding:
            out.append(f"WARN PHIL: {c['id']} missing grounding label (L-599)")
    return out


def check_stale_challenges(current_session: int, threshold: int = 50) -> list[str]:
    """Flag OPEN/PERSISTENT challenges older than threshold sessions."""
    phil_path = REPO_ROOT / "beliefs" / "PHILOSOPHY.md"
    text = _read_text(phil_path)
    if not text:
        return []
    out = []
    in_challenges = False
    for line in text.splitlines():
        if "| Claim |" in line and "Session" in line and "Challenge" in line:
            in_challenges = True
            continue
        if in_challenges and re.match(r"^\s*\|[-| ]+\|\s*$", line):
            continue
        if not in_challenges:
            continue
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) < 5:
            continue
        claim = cells[1]
        status = cells[4]
        if "OPEN" not in status and "PERSISTENT" not in status:
            continue
        sess_m = re.search(r"S(\d+)", cells[2])
        if not sess_m:
            continue
        challenge_session = int(sess_m.group(1))
        drift = current_session - challenge_session
        if drift > threshold:
            out.append(
                f"WARN CHALLENGE: {claim} OPEN since S{challenge_session} "
                f"({drift}s stale)"
            )
    return out


def check_identity() -> list[str]:
    index_md = REPO_ROOT / "memory" / "INDEX.md"
    core_md = REPO_ROOT / "beliefs" / "CORE.md"
    if not index_md.exists() or not core_md.exists():
        return []
    m = re.search(r"<!--\s*core_md_hash:\s*([a-f0-9]{64})\s*-->", _read_text(index_md))
    if not m:
        return []
    stored = m.group(1)
    current = hashlib.sha256(core_md.read_bytes()).hexdigest()
    if stored != current:
        return [f"FAIL IDENTITY: CORE.md changed without renewal (stored={stored[:12]}..., current={current[:12]}...)"]
    return []


# === CONSOLIDATED FUNCTIONS (from validate_beliefs_extras.py) ===

import subprocess

def _git(*args: str) -> str:
    try:
        r = subprocess.run(
            ["git", "-C", str(REPO_ROOT)] + list(args),
            capture_output=True,
            text=True,
            timeout=10,
        )
        return r.stdout.strip()
    except Exception:
        return ""


def _line_count(path: Path) -> int:
    try:
        return len(_read_text(path).splitlines())
    except Exception:
        return 9999


def _sc(pts, cond, msg):
    return (pts, pts if cond else 0, f"  {msg}: +{pts if cond else 0}")


def print_swarmability(beliefs: list[dict], has_errors: bool, existence_ok: bool):
    print("\n=== SWARMABILITY SCORE ===\n")
    frontier_path = REPO_ROOT / "tasks" / "FRONTIER.md"
    frontier_text = _read_text(frontier_path) if frontier_path.exists() else ""
    open_qs = re.findall(r"^\- \*\*F\d+\*\*:(.+)", frontier_text, re.MULTILINE)
    theorized_pct = sum(1 for b in beliefs if b["evidence"] == "theorized") / max(len(beliefs), 1)
    has_tested = any(b["last_tested"] and b["last_tested"].lower() != "never" for b in beliefs)

    dep_log = _git("log", "--oneline", "-5", "--", "beliefs/DEPS.md")
    belief_modified = False
    for sha in (l.split()[0] for l in dep_log.splitlines() if l.strip()):
        stat = _git("show", "--stat", sha, "--", "beliefs/DEPS.md")
        if "insertions" in stat and "deletions" in stat:
            belief_modified = True
            break
    ev_log = _git("log", "-20", "-p", "--", "beliefs/DEPS.md")
    ev_changed = bool(re.search(r"^[-+].*\*\*Evidence\*\*:", ev_log, re.MULTILINE)) if ev_log else False

    mandatory = sum(_line_count(REPO_ROOT / p) for p in ["CLAUDE.md", "beliefs/CORE.md", "memory/INDEX.md"])
    lessons_dir = REPO_ROOT / "memory" / "lessons"
    over_20 = sum(1 for f in lessons_dir.glob("L-*.md") if _line_count(f) > 20) if lessons_dir.exists() else 0

    ext_kw = ["RFC", "websocket", "library", "API", "code", "test", "external", "build", "tool", "implement", "research"]
    has_external = any(any(k.lower() in q.lower() for k in ext_kw) for q in open_qs)
    git_log = _git("log", "--oneline", "-3", "--name-only")
    recent = {l.strip() for l in git_log.splitlines() if "/" in l or "." in l} if git_log else set()
    non_meta = any(
        f.startswith(("workspace/", "experiments/", "tools/"))
        or (not f.startswith(("beliefs/", "memory/", "tasks/", "CLAUDE")) and "." in f)
        for f in recent
    )

    categories = [
        ("Onboarding Clarity", [
            _sc(5, (REPO_ROOT / "CLAUDE.md").exists() and _line_count(REPO_ROOT / "CLAUDE.md") < 300, "CLAUDE.md exists and <300 lines"),
            _sc(5, bool(_git("log", "--oneline", "-3", "--", "memory/INDEX.md")), "INDEX.md updated within last 3 commits"),
            _sc(5, bool(open_qs), f"FRONTIER.md has {len(open_qs)} open question(s)"),
            _sc(5, existence_ok, "No broken B-ID references"),
        ]),
        ("Belief Health", [
            _sc(10, not has_errors, "Validator PASS (0 errors)"),
            _sc(5, theorized_pct < 0.6, f"Theorized {theorized_pct:.0%} < 60%"),
            _sc(5, has_tested, "At least 1 belief has a Last tested date"),
        ]),
        ("Adaptation Rate", [
            _sc(10, belief_modified, "Belief modified in last 5 DEPS.md commits"),
            _sc(10, ev_changed, "Evidence type changed in history"),
        ]),
        ("Context Efficiency", [
            _sc(10, mandatory < 450, f"Mandatory files {mandatory} lines (<450)"),
            _sc(10, over_20 == 0, "No lessons over 20 lines"),
        ]),
        ("Forward Momentum", [
            _sc(5, len(open_qs) >= 3, f"{len(open_qs)} open frontier questions (>=3)"),
            _sc(5, has_external, "At least 1 external-facing frontier question"),
            _sc(10, non_meta, "Recent commits touch non-meta files"),
        ]),
    ]

    total = 0
    for i, (name, checks) in enumerate(categories, 1):
        earned = sum(c[1] for c in checks)
        max_pts = sum(c[0] for c in checks)
        print(f"{i}. {name}: {earned}/{max_pts}")
        for _, _, note in checks:
            print(note)
        total += earned
    print(f"\nSWARMABILITY: {total}/100")


def detect_entropy(beliefs: list[dict]) -> list[str]:
    findings = []
    for b in beliefs:
        if b["evidence"] == "theorized" and (not b["last_tested"] or b["last_tested"].lower() == "never"):
            findings.append(f"  {b['id']}: theorized and never tested")

    deps_path = REPO_ROOT / "beliefs" / "DEPS.md"
    superseded = set(re.findall(r"~~(B\d+)~~", _read_text(deps_path))) if deps_path.exists() else set()
    lessons_dir = REPO_ROOT / "memory" / "lessons"
    if lessons_dir.exists() and superseded:
        for f in sorted(lessons_dir.glob("L-*.md")):
            text = _read_text(f) if f.exists() else ""
            m = re.search(r"## Affected beliefs:\s*(.+)", text)
            if m:
                stale = [bid for bid in re.findall(r"B\d+", m.group(1)) if bid in superseded]
                if stale:
                    findings.append(f"  {f.name}: references superseded {', '.join(stale)}")

    refs = "".join(_read_text(p) for p in [REPO_ROOT / "CLAUDE.md", REPO_ROOT / "memory" / "INDEX.md"] if p.exists())
    skip = {"INDEX.md", "PRINCIPLES.md", "SESSION-LOG.md", "PULSE.md", "HEALTH.md"}
    memory_dir = REPO_ROOT / "memory"
    if memory_dir.exists():
        for f in sorted(memory_dir.glob("*.md")):
            if f.name not in skip and f.name not in refs:
                findings.append(f"  {f.relative_to(REPO_ROOT)}: not referenced by CLAUDE.md or INDEX.md")
    return findings


def print_entropy(beliefs: list[dict]):
    findings = detect_entropy(beliefs)
    print("\n=== ENTROPY DETECTOR ===\n")
    if findings:
        for f in findings:
            print(f)
        print(f"\nEntropy items: {len(findings)}")
    else:
        print("  No entropy detected.")
        print("\nEntropy items: 0")


def main() -> int:
    quick = "--quick" in sys.argv
    raw = [a for a in sys.argv[1:] if a != "--quick"]
    changed_id, args = None, []
    i = 0
    while i < len(raw):
        if raw[i].startswith("--changed="):
            changed_id = raw[i].split("=", 1)[1]
        elif raw[i] == "--changed" and i + 1 < len(raw):
            changed_id = raw[i + 1]
            i += 1
        else:
            args.append(raw[i])
        i += 1

    path = args[0] if args else "beliefs/DEPS.md"
    if not Path(path).exists():
        print(f"ERROR: {path} not found")
        return 1
    beliefs = parse_beliefs(path)
    if not beliefs:
        print(f"ERROR: No beliefs found in {path}")
        return 1

    issues: list[str] = []
    existence = check_existence(beliefs)
    issues.extend(existence)
    issues.extend(check_cycles(beliefs))
    issues.extend(check_orphans(beliefs))
    issues.extend(check_dep_consistency(beliefs))
    issues.extend(check_format(beliefs))
    issues.extend(check_identity())

    # PHIL-N claims validation (CORE P14: self-application, S348)
    phil_claims = parse_phil_claims()
    if phil_claims:
        issues.extend(check_phil_format(phil_claims))

    # Confidence tag coverage check (WARN if <90%, from L-651)
    if not quick:
        lessons_dir = REPO_ROOT / "memory" / "lessons"
        if lessons_dir.exists():
            all_lessons = list(lessons_dir.glob("L-*.md"))
            untagged = [f for f in all_lessons if "Confidence:" not in _read_text(f)]
            coverage_pct = (len(all_lessons) - len(untagged)) / len(all_lessons) if all_lessons else 1.0
            if coverage_pct < 0.90:
                issues.append(
                    f"WARN: confidence tag coverage {coverage_pct:.1%} (<90%) — "
                    f"{len(untagged)}/{len(all_lessons)} lessons missing Confidence: label. "
                    f"Run tools/confidence_tagger.py or add manually. (L-651)"
                )

    # Stale challenge detection (non-quick only — informational)
    if not quick and phil_claims:
        index_text = _read_text(REPO_ROOT / "memory" / "INDEX.md")
        sess_m = re.search(r"Sessions:\s*(\d+)", index_text[:300])
        if sess_m:
            current_session = int(sess_m.group(1))
            issues.extend(check_stale_challenges(current_session))

    n_obs = sum(1 for b in beliefs if b["evidence"] == "observed")
    n_the = sum(1 for b in beliefs if b["evidence"] == "theorized")
    n_phil_obs = sum(1 for c in phil_claims if c["type"] == "observed")
    n_phil_ax = sum(1 for c in phil_claims if c["type"] == "axiom")
    for issue in issues:
        print(issue)
    fails = [i for i in issues if i.startswith("FAIL")]
    warns = [i for i in issues if i.startswith("WARN")]
    print()
    summary = (
        f"Summary: {len(beliefs)} beliefs, {n_obs} observed, {n_the} theorized"
    )
    if phil_claims:
        summary += f" | {len(phil_claims)} PHIL claims, {n_phil_obs} observed, {n_phil_ax} axiom"
    summary += f" | {len(fails)} errors, {len(warns)} warnings"
    print(summary)
    exit_code = 1 if fails else 0
    print("RESULT: FAIL" if fails else "RESULT: PASS")

    if not quick:
        print_swarmability(beliefs, bool(fails), not existence)
        print_entropy(beliefs)
    if changed_id:
        print(f"\n=== CASCADE CHECK ({changed_id} changed) ===")
        for issue in cascade_check(beliefs, changed_id):
            print(issue)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
