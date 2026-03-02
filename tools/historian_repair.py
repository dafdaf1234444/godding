#!/usr/bin/env python3
"""historian_repair.py — Automated historian-mode swarm repair scanner (F-META17).

Identifies unchanged/stale swarm artifacts using historian-check logic:
scans beliefs, frontiers, lanes, and domains for items not updated in N sessions,
diagnoses whether staleness is intentional (resolved) or neglected, and
proposes or auto-applies repairs.

Usage:
    python3 tools/historian_repair.py           # scan mode (default)
    python3 tools/historian_repair.py --repair  # auto-apply safe repairs
    python3 tools/historian_repair.py --json    # machine-readable output
    python3 tools/historian_repair.py --category beliefs|frontiers|lanes|domains|all

Thresholds (tunable via --belief-stale, --frontier-stale, --lane-stale):
    Beliefs:   >50 sessions without retest → STALE (orient.py default)
    Frontiers: >15 sessions without update → anxiety zone
    Lanes:     >2 sessions ACTIVE with no progress → stale
    Domains:   >30 sessions no DOMEX lane for active frontier → gap
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

try:
    from swarm_io import session_number as _session_number

    def current_session() -> int:
        return _session_number()
except ImportError:
    def current_session() -> int:
        try:
            log = (ROOT / "memory" / "SESSION-LOG.md").read_text()
            nums = re.findall(r"\bS(\d+)\b", log)
            return max(int(n) for n in nums) if nums else 0
        except Exception:
            return 0

# ── data model ────────────────────────────────────────────────────────────────

@dataclass
class StaleItem:
    category: str          # beliefs | frontiers | lanes | domains | maintenance
    item_id: str           # B6, F-META2, DOMEX-SP-S394, etc.
    description: str       # one-line human summary
    sessions_stale: int    # current_session - last_touched_session
    last_session: int      # last session that touched this item
    last_context: str      # brief historian note (what was last done)
    repair_type: str       # auto | suggest | none
    repair_action: str     # specific command or instruction
    severity: str = "WATCH"  # HIGH | WATCH | INFO

    def as_dict(self) -> dict:
        return {
            "category": self.category,
            "item_id": self.item_id,
            "description": self.description,
            "sessions_stale": self.sessions_stale,
            "last_session": self.last_session,
            "last_context": self.last_context,
            "repair_type": self.repair_type,
            "repair_action": self.repair_action,
            "severity": self.severity,
        }


# ── helpers ───────────────────────────────────────────────────────────────────

def max_session_in_text(text: str) -> int:
    nums = [int(n) for n in re.findall(r"\bS(\d+)\b", text)]
    return max(nums) if nums else 0


def last_line_with_session(text: str, target_session: int) -> str:
    """Return the first line mentioning the target session (for context)."""
    for line in text.splitlines():
        if f"S{target_session}" in line:
            return line.strip()[:120]
    return f"S{target_session} referenced"


def _stale_severity(sessions: int, threshold: int) -> str:
    ratio = sessions / threshold
    if ratio >= 2.0:
        return "HIGH"
    if ratio >= 1.0:
        return "WATCH"
    return "INFO"


# ── scanners ─────────────────────────────────────────────────────────────────

def scan_beliefs(cs: int, stale_threshold: int = 50) -> list[StaleItem]:
    """Find beliefs not retested in > stale_threshold sessions."""
    items: list[StaleItem] = []
    deps_path = ROOT / "beliefs" / "DEPS.md"
    if not deps_path.exists():
        return items

    text = deps_path.read_text()
    blocks = re.findall(r"### (B[-\w]+):(.*?)(?=###|\Z)", text, re.DOTALL)
    for raw_name, body in blocks:
        name = raw_name.strip()
        sessions = [int(n) for n in re.findall(r"S(\d+)", body)]
        if not sessions:
            last_s = 0
            stale = cs
        else:
            last_s = max(sessions)
            stale = cs - last_s

        if stale > stale_threshold:
            ctx = last_line_with_session(body, last_s) if last_s else "never retested"
            # Extract claim from first non-empty line (before bullet points)
            first_line = body.strip().split("\n")[0].strip()
            claim = first_line[:80] if first_line and not first_line.startswith("-") else name

            # Check if there's a DOMEX lane covering this belief
            repair = (
                f"Open DOMEX-META lane to retest {name}: "
                f"`python3 tools/open_lane.py --lane DOMEX-META --frontier F-META-retest "
                f"--intent 'retest {name}: {claim[:40]}...'`"
            )
            items.append(StaleItem(
                category="beliefs",
                item_id=name,
                description=f"{name}: {claim[:80]}",
                sessions_stale=stale,
                last_session=last_s,
                last_context=ctx,
                repair_type="suggest",
                repair_action=repair,
                severity=_stale_severity(stale, stale_threshold),
            ))
    return items


def scan_frontiers(cs: int, anxiety_threshold: int = 15) -> list[StaleItem]:
    """Find frontiers open > anxiety_threshold sessions without update."""
    items: list[StaleItem] = []
    frontier_path = ROOT / "tasks" / "FRONTIER.md"
    if not frontier_path.exists():
        return items

    text = frontier_path.read_text()
    current_fid: Optional[str] = None
    current_sessions: list[int] = []
    current_lines: list[str] = []

    def flush():
        if not current_fid:
            return
        if current_sessions:
            last_s = max(current_sessions)
            stale = cs - last_s
        else:
            last_s = 0
            stale = cs
        if stale > anxiety_threshold:
            # Get brief description
            desc_line = current_lines[0] if current_lines else current_fid
            desc = re.sub(r"\*\*", "", desc_line).strip()[:100]
            ctx = f"S{last_s}: {last_line_with_session(chr(10).join(current_lines), last_s)}"
            repair = (
                f"Run multi-expert synthesis for {current_fid}: "
                f"`python3 tools/dispatch_optimizer.py` then open DOMEX lane. "
                f"Or mark RESOLVED/ABANDONED if no longer relevant."
            )
            severity = _stale_severity(stale, anxiety_threshold)
            items.append(StaleItem(
                category="frontiers",
                item_id=current_fid,
                description=desc,
                sessions_stale=stale,
                last_session=last_s,
                last_context=ctx[:120],
                repair_type="suggest",
                repair_action=repair,
                severity=severity,
            ))

    for line in text.splitlines():
        fid_match = re.match(r"\s*[-*]\s*\*\*(F-\w+\d+)\*\*", line)
        if fid_match:
            flush()
            current_fid = fid_match.group(1)
            current_sessions = [int(n) for n in re.findall(r"\bS(\d+)\b", line)]
            current_lines = [line]
        elif current_fid and line.strip():
            current_sessions += [int(n) for n in re.findall(r"\bS(\d+)\b", line)]
            current_lines.append(line)
        elif not line.strip() and current_fid:
            current_lines.append(line)

    flush()
    return items


def scan_lanes(cs: int, stale_threshold: int = 2) -> list[StaleItem]:
    """Find ACTIVE/CLAIMED/BLOCKED lanes with no progress update for > stale_threshold sessions."""
    items: list[StaleItem] = []
    lanes_path = ROOT / "tasks" / "SWARM-LANES.md"
    if not lanes_path.exists():
        return items

    text = lanes_path.read_text()
    active_statuses = {"CLAIMED", "ACTIVE", "BLOCKED", "READY"}

    # Track latest row per lane_id
    lane_latest: dict[str, dict] = {}
    for row in text.splitlines():
        if not row.startswith("|"):
            continue
        parts = [p.strip() for p in row.split("|")]
        if len(parts) < 12:
            continue
        status = parts[11] if len(parts) > 11 else ""
        lane_id = parts[2]
        session_str = parts[3]
        if not lane_id or not session_str:
            continue
        # Extract session number
        s_match = re.search(r"S?(\d+)", session_str)
        if not s_match:
            continue
        sess = int(s_match.group(1))
        if lane_id not in lane_latest or sess > lane_latest[lane_id]["session"]:
            lane_latest[lane_id] = {"session": sess, "status": status, "row": row}

    for lane_id, info in lane_latest.items():
        if info["status"] not in active_statuses:
            continue
        last_s = info["session"]
        stale = cs - last_s
        if stale > stale_threshold:
            etc_match = re.search(r"\|\s*([^|]*?)\s*\|\s*" + re.escape(info["status"]), info["row"])
            etc_snippet = etc_match.group(1)[:80] if etc_match else ""
            repair = (
                f"Close stale lane {lane_id}: "
                f"`python3 tools/close_lane.py --lane {lane_id} --status ABANDONED "
                f"--note 'stale — no artifact produced in {stale} sessions'`"
            )
            items.append(StaleItem(
                category="lanes",
                item_id=lane_id,
                description=f"Active lane stale since S{last_s} ({info['status']})",
                sessions_stale=stale,
                last_session=last_s,
                last_context=etc_snippet[:100],
                repair_type="auto",
                repair_action=repair,
                severity=_stale_severity(stale, stale_threshold),
            ))
    return items


def scan_domains(cs: int, gap_threshold: int = 30) -> list[StaleItem]:
    """Find domains with active frontiers but no DOMEX lane in > gap_threshold sessions."""
    items: list[StaleItem] = []
    domains_root = ROOT / "domains"
    lanes_path = ROOT / "tasks" / "SWARM-LANES.md"
    if not domains_root.exists() or not lanes_path.exists():
        return items

    lanes_text = lanes_path.read_text()

    # Build: domain → latest DOMEX session
    domain_last_domex: dict[str, int] = {}
    for row in lanes_text.splitlines():
        if not row.startswith("|"):
            continue
        parts = [p.strip() for p in row.split("|")]
        if len(parts) < 12:
            continue
        lane_id = parts[2]
        session_str = parts[3]
        if not lane_id.startswith("DOMEX-"):
            continue
        # Infer domain from lane ID: DOMEX-META-S392 → meta, DOMEX-STR → strategy
        domain_abbr = lane_id.split("-")[1].lower() if len(lane_id.split("-")) > 1 else ""
        s_match = re.search(r"S?(\d+)", session_str)
        if not s_match:
            continue
        sess = int(s_match.group(1))
        domain_last_domex[domain_abbr] = max(domain_last_domex.get(domain_abbr, 0), sess)

    # Also check scope-key field for domain paths
    for row in lanes_text.splitlines():
        if not row.startswith("|"):
            continue
        parts = [p.strip() for p in row.split("|")]
        if len(parts) < 10:
            continue
        scope = parts[9] if len(parts) > 9 else ""
        session_str = parts[3]
        m = re.search(r"domains/([^/]+)", scope)
        if not m:
            continue
        domain = m.group(1)
        s_match = re.search(r"S?(\d+)", session_str)
        if not s_match:
            continue
        sess = int(s_match.group(1))
        domain_last_domex[domain] = max(domain_last_domex.get(domain, 0), sess)

    # Scan each domain for active frontiers
    for domain_dir in sorted(domains_root.iterdir()):
        if not domain_dir.is_dir():
            continue
        frontier_file = domain_dir / "tasks" / "FRONTIER.md"
        if not frontier_file.exists():
            continue
        frontier_text = frontier_file.read_text()
        # Check if there are open frontiers (not RESOLVED/ABANDONED)
        active_frontiers = re.findall(r"\*\*(F-\w+\d+)\*\*", frontier_text)
        resolved = set(re.findall(r"(?:RESOLVED|ABANDONED)[^\n]*\*\*(F-\w+\d+)\*\*|"
                                   r"\*\*(F-\w+\d+)\*\*[^\n]*(?:RESOLVED|ABANDONED)", frontier_text))
        open_fs = [f for f in active_frontiers if f not in resolved]
        if not open_fs:
            continue

        domain_name = domain_dir.name
        # Match domain to abbreviation used in lane IDs
        abbr_candidates = [
            domain_name[:3].upper(),  # MET, STR, etc
            domain_name.lower(),      # meta, strategy, etc
            domain_name[:2].upper(),  # NK
        ]
        last_domex = 0
        for abbr in abbr_candidates:
            last_domex = max(last_domex, domain_last_domex.get(abbr.lower(), 0))
        last_domex = max(last_domex, domain_last_domex.get(domain_name, 0))

        stale = cs - last_domex if last_domex > 0 else cs
        if stale > gap_threshold:
            top_frontier = open_fs[0]
            repair = (
                f"Open DOMEX lane for {domain_name}/{top_frontier}: "
                f"`python3 tools/dispatch_optimizer.py` → if top-3 → "
                f"`python3 tools/open_lane.py --lane DOMEX-{domain_name[:3].upper()}-S{cs} "
                f"--intent 'advance {top_frontier}'`"
            )
            items.append(StaleItem(
                category="domains",
                item_id=f"{domain_name}/{top_frontier}",
                description=f"{len(open_fs)} open frontier(s) in {domain_name}, last DOMEX: "
                            f"{'S'+str(last_domex) if last_domex else 'never'}",
                sessions_stale=stale,
                last_session=last_domex,
                last_context=f"Domain has {len(open_fs)} open frontier(s): {', '.join(open_fs[:3])}",
                repair_type="suggest",
                repair_action=repair,
                severity=_stale_severity(stale, gap_threshold),
            ))
    return items


def scan_maintenance(cs: int) -> list[StaleItem]:
    """Surface HIGH/DUE maintenance items that are blocking the swarm."""
    items: list[StaleItem] = []
    try:
        result = subprocess.run(
            ["python3", "tools/maintenance.py"],
            capture_output=True, text=True, cwd=ROOT, timeout=30
        )
        output = result.stdout
    except Exception:
        return items

    # Parse DUE items
    in_due = False
    for line in output.splitlines():
        if "[DUE]" in line:
            in_due = True
            continue
        if "[PERIODIC]" in line or "[NOTICE]" in line:
            in_due = False
            continue
        if in_due and line.strip().startswith("!"):
            # Extract item name and description
            m = re.search(r"\[([^\]]+)\]\s*(.*?)(?:\(every.*last:\s*S(\d+)\))?$", line)
            if m:
                name = m.group(1)
                desc = m.group(2).strip()[:100]
                last_s_str = m.group(3)
                last_s = int(last_s_str) if last_s_str else 0
                stale = cs - last_s if last_s else cs
                items.append(StaleItem(
                    category="maintenance",
                    item_id=f"DUE:{name}",
                    description=desc,
                    sessions_stale=stale,
                    last_session=last_s,
                    last_context=f"maintenance.py DUE item, overdue {stale} sessions",
                    repair_type="suggest",
                    repair_action=f"Run maintenance item '{name}' as described in maintenance.py output",
                    severity="HIGH" if stale > 10 else "WATCH",
                ))
    return items


# ── repair executor ───────────────────────────────────────────────────────────

def apply_auto_repairs(items: list[StaleItem]) -> list[str]:
    """Apply repairs marked repair_type='auto'. Returns list of actions taken."""
    actions: list[str] = []
    for item in items:
        if item.repair_type != "auto":
            continue
        # Currently: close stale lanes
        if "close_lane.py" in item.repair_action:
            # Extract the command
            m = re.search(r"(python3 tools/close_lane\.py[^`]+)", item.repair_action)
            if m:
                cmd = m.group(1).strip()
                result = subprocess.run(
                    cmd.split(), capture_output=True, text=True, cwd=ROOT
                )
                if result.returncode == 0:
                    actions.append(f"REPAIRED {item.item_id}: {cmd}")
                else:
                    actions.append(f"FAILED {item.item_id}: {result.stderr.strip()[:100]}")
    return actions


# ── reporter ──────────────────────────────────────────────────────────────────

def report_text(items: list[StaleItem], cs: int) -> str:
    if not items:
        return "=== HISTORIAN REPAIR — no stale items found ===\n"

    lines = [f"=== HISTORIAN REPAIR — S{cs} === ({len(items)} stale item(s))\n"]
    by_cat: dict[str, list[StaleItem]] = {}
    for item in items:
        by_cat.setdefault(item.category, []).append(item)

    severity_order = {"HIGH": 0, "WATCH": 1, "INFO": 2}
    cat_order = ["maintenance", "lanes", "beliefs", "frontiers", "domains"]

    for cat in cat_order:
        cat_items = sorted(by_cat.get(cat, []), key=lambda i: severity_order.get(i.severity, 9))
        if not cat_items:
            continue
        lines.append(f"--- {cat.upper()} ({len(cat_items)}) ---")
        for item in cat_items:
            prefix = "!!" if item.severity == "HIGH" else ("!" if item.severity == "WATCH" else ".")
            lines.append(f"  {prefix} [{item.item_id}] stale={item.sessions_stale}s — {item.description}")
            lines.append(f"       Last: S{item.last_session} | {item.last_context}")
            lines.append(f"       Repair ({item.repair_type}): {item.repair_action}")
        lines.append("")
    return "\n".join(lines)


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--repair", action="store_true", help="Auto-apply safe repairs")
    parser.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    parser.add_argument("--category", choices=["beliefs", "frontiers", "lanes", "domains", "maintenance", "all"],
                        default="all", help="Which category to scan")
    parser.add_argument("--belief-stale", type=int, default=50, metavar="N",
                        help="Belief stale threshold in sessions (default: 50)")
    parser.add_argument("--frontier-stale", type=int, default=15, metavar="N",
                        help="Frontier anxiety threshold in sessions (default: 15)")
    parser.add_argument("--lane-stale", type=int, default=2, metavar="N",
                        help="Active lane stale threshold in sessions (default: 2)")
    parser.add_argument("--domain-gap", type=int, default=30, metavar="N",
                        help="Domain DOMEX gap threshold in sessions (default: 30)")
    args = parser.parse_args()

    cs = current_session()
    cat = args.category

    items: list[StaleItem] = []
    if cat in ("beliefs", "all"):
        items += scan_beliefs(cs, args.belief_stale)
    if cat in ("frontiers", "all"):
        items += scan_frontiers(cs, args.frontier_stale)
    if cat in ("lanes", "all"):
        items += scan_lanes(cs, args.lane_stale)
    if cat in ("domains", "all"):
        items += scan_domains(cs, args.domain_gap)
    if cat in ("maintenance", "all"):
        items += scan_maintenance(cs)

    # Sort by severity then staleness
    sev_order = {"HIGH": 0, "WATCH": 1, "INFO": 2}
    items.sort(key=lambda i: (sev_order.get(i.severity, 9), -i.sessions_stale))

    if args.repair:
        actions = apply_auto_repairs(items)
        if actions:
            print("\n".join(actions))
        else:
            print("No auto-repairable items found (or all already clean).")

    if args.json:
        out = {
            "session": cs,
            "total": len(items),
            "items": [i.as_dict() for i in items],
        }
        print(json.dumps(out, indent=2))
    else:
        print(report_text(items, cs))


if __name__ == "__main__":
    main()
