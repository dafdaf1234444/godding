#!/usr/bin/env python3
"""
F-EVO5: Self-archaeology — extract swarm evolution timeline across
functional (capabilities), size (L/P/B/F), and structural (domains/tools) dimensions.
"""
import json
import re
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def run(cmd):
    return subprocess.check_output(cmd, text=True, cwd=Path(__file__).parent.parent)


def extract_size_timeline():
    """Parse L/P/B/F counts from SESSION-LOG.md and git commit messages."""
    sessions = {}

    # Source 1: SESSION-LOG.md cumulative anchors
    log_path = Path(__file__).parent.parent / "memory" / "SESSION-LOG.md"
    if log_path.exists():
        content = log_path.read_text()
        # Patterns like "S182: 253L 169P" or within lines "253L 169P 17B 19F"
        for line in content.splitlines():
            sm = re.match(r"S(\d+)", line.strip())
            if not sm:
                continue
            s = int(sm.group(1))
            lm = re.search(r"(\d+)L\s+(\d+)P", line)
            bm = re.search(r"(\d+)B\s+(\d+)F", line)
            if lm and s not in sessions:
                sessions[s] = {
                    "session": s,
                    "date": None,
                    "L": int(lm.group(1)),
                    "P": int(lm.group(2)),
                    "B": int(bm.group(1)) if bm else None,
                    "F": int(bm.group(2)) if bm else None,
                    "source": "SESSION-LOG",
                }

    # Source 2: git commit messages
    log = run(["git", "log", "--format=%s|%ad", "--date=short", "-1000"])
    for line in log.splitlines():
        parts = line.rsplit("|", 1)
        if len(parts) < 2:
            continue
        msg, date = parts
        sm = re.search(r"\[S(\d+)\]", msg)
        lm = re.search(r"(\d+)L\s+(\d+)P", msg)
        bm = re.search(r"(\d+)B\s+(\d+)F", msg)
        if sm and lm:
            s = int(sm.group(1))
            if s not in sessions:
                sessions[s] = {
                    "session": s,
                    "date": date,
                    "L": int(lm.group(1)),
                    "P": int(lm.group(2)),
                    "B": int(bm.group(1)) if bm else None,
                    "F": int(bm.group(2)) if bm else None,
                    "source": "git-log",
                }
            elif sessions[s]["date"] is None:
                sessions[s]["date"] = date

    return dict(sorted(sessions.items()))


def extract_tool_births():
    """Find when each tools/*.py file was first added."""
    log = run(["git", "log", "--diff-filter=A", "--name-only", "--format=%s|%ad", "--date=short", "-1000"])
    births = {}
    current_meta = None
    for line in log.splitlines():
        line = line.strip()
        if "|" in line and not line.startswith("tools/"):
            sm = re.search(r"\[S(\d+)\]", line)
            date = line.rsplit("|", 1)[-1]
            current_meta = (int(sm.group(1)) if sm else None, date)
        elif line.startswith("tools/") and line.endswith(".py"):
            name = Path(line).name
            if name not in births and current_meta:
                births[name] = {"session": current_meta[0], "date": current_meta[1]}
    return births


def extract_domain_births():
    """Find when each domains/<name>/ directory was seeded (DOMAIN.md added)."""
    log = run(["git", "log", "--diff-filter=A", "--name-only", "--format=%s|%ad", "--date=short", "-1000"])
    births = {}
    current_meta = None
    for line in log.splitlines():
        line = line.strip()
        if "|" in line and not line.startswith("domains/"):
            sm = re.search(r"\[S(\d+)\]", line)
            date = line.rsplit("|", 1)[-1]
            current_meta = (int(sm.group(1)) if sm else None, date)
        elif line.startswith("domains/") and line.endswith("DOMAIN.md"):
            m = re.match(r"domains/([^/]+)/DOMAIN\.md", line)
            if m:
                domain = m.group(1)
                if domain not in births and current_meta:
                    births[domain] = {"session": current_meta[0], "date": current_meta[1]}
    return births


def classify_tool(name):
    """Rough functional category for a tool."""
    n = name.lower()
    for kw, cat in [
        ("f_evo", "evolution"), ("f_ai", "ai-behavior"), ("f_fin", "finance"),
        ("f_ops", "operations"), ("f_gam", "gaming"), ("f_lng", "linguistics"),
        ("f_qc", "quality"), ("f_con", "conflict"), ("f_ctl", "control"),
        ("f_his", "history"), ("f_psy", "psychology"), ("f_brn", "brain"),
        ("f_eco", "economy"), ("f_hlt", "health"), ("f_soc", "social"),
        ("f_str", "strategy"), ("f_gov", "governance"), ("f_fra", "fractals"),
        ("f_pro", "protocol"), ("f_drm", "dream"), ("f_eval", "evaluation"),
        ("f_pers", "personality"),
        ("compact", "ops-core"), ("orient", "ops-core"), ("maintenance", "ops-core"),
        ("sync_state", "ops-core"), ("validate", "ops-core"), ("check", "ops-core"),
        ("proxy", "ops-core"), ("change_quality", "ops-core"),
        ("wiki", "capability"), ("task_recognizer", "capability"),
        ("substrate", "capability"), ("bulletin", "capability"),
        ("personality", "meta"), ("expert", "meta"), ("belief", "meta"),
        ("paper", "meta"), ("economy_expert", "meta"),
        ("close_lane", "ops-lane"), ("swarm_lanes", "ops-lane"),
        ("f_evo2_extract", "evolution"),
    ]:
        if kw in n:
            return cat
    return "other"


def compute_growth_phases(timeline):
    """Identify growth phases by L delta per 10-session window."""
    sessions = sorted(timeline.keys())
    if len(sessions) < 4:
        return []
    phases = []
    step = 10
    for i in range(0, len(sessions) - step, step):
        s_start = sessions[i]
        s_end = sessions[min(i + step, len(sessions) - 1)]
        dl = timeline[s_end]["L"] - timeline[s_start]["L"]
        dp = timeline[s_end]["P"] - timeline[s_start]["P"]
        rate = dl / (s_end - s_start) if s_end > s_start else 0
        phases.append({
            "s_start": s_start, "s_end": s_end,
            "dL": dl, "dP": dp,
            "L_per_session": round(rate, 2),
        })
    return phases


def summarize():
    size_tl = extract_size_timeline()
    tool_births = extract_tool_births()
    domain_births = extract_domain_births()

    # Functional categories over sessions
    by_cat = defaultdict(list)
    for name, meta in tool_births.items():
        cat = classify_tool(name)
        by_cat[cat].append({"tool": name, **meta})

    # Domain seeding timeline
    domain_by_session = defaultdict(list)
    for d, meta in domain_births.items():
        domain_by_session[meta["session"]].append(d)

    phases = compute_growth_phases(size_tl)

    # Current state
    if size_tl:
        latest = max(size_tl.keys())
        cur = size_tl[latest]
    else:
        cur = {}

    # Tool count by category
    cat_counts = {cat: len(tools) for cat, tools in sorted(by_cat.items())}

    # Domain seeding acceleration: sessions with 3+ domains seeded
    burst_sessions = {s: doms for s, doms in domain_by_session.items() if len(doms) >= 3}

    return {
        "meta": {"generated_by": "f_evo5_self_archaeology.py", "date": datetime.now().date().isoformat()},
        "current_scale": cur,
        "size_timeline_sessions": len(size_tl),
        "size_timeline": {str(k): v for k, v in size_tl.items()},
        "growth_phases": phases,
        "tool_births_total": len(tool_births),
        "tool_births_by_category": cat_counts,
        "tool_births_detail": dict(by_cat),
        "domain_births_total": len(domain_births),
        "domain_births_by_session": {str(k): v for k, v in sorted(domain_by_session.items())},
        "domain_burst_sessions": {str(k): v for k, v in sorted(burst_sessions.items())},
        "all_domains": dict(sorted(domain_births.items())),
    }


def print_summary(data):
    cur = data["current_scale"]
    print(f"=== F-EVO5 SELF-ARCHAEOLOGY ===")
    print(f"Current scale: S{cur.get('session')} — {cur.get('L')}L {cur.get('P')}P {cur.get('B')}B {cur.get('F')}F")
    print(f"Size timeline: {data['size_timeline_sessions']} sessions with L/P counts")
    print()
    print("Growth phases (L/session):")
    for ph in data["growth_phases"]:
        print(f"  S{ph['s_start']:3d}→S{ph['s_end']:3d}: +{ph['dL']:3d}L +{ph['dP']:2d}P  ({ph['L_per_session']:.1f} L/s)")
    print()
    print(f"Tools born: {data['tool_births_total']}")
    print("By category:")
    for cat, n in sorted(data["tool_births_by_category"].items(), key=lambda x: -x[1]):
        print(f"  {cat:25s}: {n}")
    print()
    print(f"Domains seeded: {data['domain_births_total']}")
    if data["domain_burst_sessions"]:
        print("Domain burst sessions (3+ domains seeded):")
        for s, doms in data["domain_burst_sessions"].items():
            print(f"  S{s}: {', '.join(doms)}")


if __name__ == "__main__":
    data = summarize()
    out = Path("experiments/evolution/f-evo5-self-archaeology-s195.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2))
    print_summary(data)
    print(f"\nArtifact: {out}")
