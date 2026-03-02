#!/usr/bin/env python3
"""
colony_interact.py — Swarm-to-swarm interaction tooling.

Measures inter-colony signal rate, maps colony capability edges,
and suggests cross-colony pairings by frontier compatibility.

Part of F-EXP6: How do swarm colonies signal each other?

Usage:
  python3 tools/colony_interact.py map            -- capability graph + signal rate
  python3 tools/colony_interact.py suggest        -- suggest top colony pairings
  python3 tools/colony_interact.py signal <src> <dst> <msg>  -- write colony signal
  python3 tools/colony_interact.py signals [domain]          -- read colony signals
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
DOMAINS = ROOT / "domains"


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _current_session() -> str:
    try:
        import subprocess
        r = subprocess.run(["git", "log", "--oneline", "-30"],
                           capture_output=True, text=True, cwd=ROOT)
        for line in r.stdout.splitlines():
            m = re.search(r'\[S(\d+)\]', line)
            if m:
                return f"S{m.group(1)}"
    except Exception:
        pass
    return "S?"


ALL_DOMAIN_NAMES = [d.name for d in DOMAINS.iterdir() if d.is_dir() and (d / "COLONY.md").exists()]


# ── Capability extraction ────────────────────────────────────────────────────

def extract_colony_capabilities(domain: str) -> dict:
    """Extract what a colony knows and can offer."""
    result = {
        "domain": domain,
        "open_frontiers": [],
        "cross_links": [],
        "instruments": [],
        "iso_links": [],
    }
    # Open frontiers
    fp = DOMAINS / domain / "tasks" / "FRONTIER.md"
    if fp.exists():
        text = fp.read_text(errors="ignore")
        result["open_frontiers"] = re.findall(r"\*\*(F-[A-Z0-9]+)\*\*", text)
        result["cross_links_raw"] = re.findall(r"[Cc]ross-?link:\s*([^\n]+)", text)

    # INDEX.md cross-domain links
    idx = DOMAINS / domain / "INDEX.md"
    if idx.exists():
        text = idx.read_text(errors="ignore")
        for d in ALL_DOMAIN_NAMES:
            if d != domain and re.search(r'\b' + re.escape(d) + r'\b', text):
                result["cross_links"].append(d)
        # Instruments
        result["instruments"] = re.findall(r"tools/(\S+\.py)", text)
        # ISO links
        result["iso_links"] = re.findall(r"\b(ISO-\d+)\b", text)

    return result


# ── Signal rate measurement ──────────────────────────────────────────────────

def measure_signal_rate() -> dict:
    """
    Measure current inter-colony interaction rate.
    Signal = a colony explicitly referencing another colony in FRONTIER.md or INDEX.md.
    """
    colonies = ALL_DOMAIN_NAMES
    total = len(colonies)
    linked = 0
    edges = []

    for domain in colonies:
        caps = extract_colony_capabilities(domain)
        if caps["cross_links"]:
            linked += 1
            for target in caps["cross_links"]:
                edges.append((domain, target))

    # Also check colony signals file
    signal_edges = []
    for domain in colonies:
        sf = DOMAINS / domain / "tasks" / "SIGNALS.md"
        if sf.exists():
            text = sf.read_text(errors="ignore")
            sigs = re.findall(r"^\|[^|]+\|([^|]+)\|", text, re.MULTILINE)
            signal_edges.extend([(domain, s.strip()) for s in sigs if s.strip()])

    return {
        "total_colonies": total,
        "linked_colonies": linked,
        "signal_rate": round(linked / total, 4) if total else 0,
        "edges": edges,
        "signal_file_edges": signal_edges,
        "active_signal_files": len([d for d in colonies
                                    if (DOMAINS / d / "tasks" / "SIGNALS.md").exists()]),
    }


# ── Pairing suggestions ──────────────────────────────────────────────────────

def suggest_pairings() -> list[dict]:
    """
    Suggest colony pairings based on frontier keyword overlap.
    High overlap = colony A could benefit from colony B's expertise.
    """
    caps = {d: extract_colony_capabilities(d) for d in ALL_DOMAIN_NAMES}
    suggestions = []

    for src in ALL_DOMAIN_NAMES:
        src_frontiers = caps[src]["open_frontiers"]
        src_text = ""
        fp = DOMAINS / src / "tasks" / "FRONTIER.md"
        if fp.exists():
            src_text = fp.read_text(errors="ignore").lower()

        for dst in ALL_DOMAIN_NAMES:
            if dst == src:
                continue
            if dst in caps[src]["cross_links"]:
                continue  # already linked

            # Keyword overlap: does dst's instruments/ISO appear in src's frontiers?
            dst_instruments = caps[dst]["instruments"]
            dst_iso = caps[dst]["iso_links"]
            dst_idx = DOMAINS / dst / "INDEX.md"
            dst_keywords = set()
            if dst_idx.exists():
                dst_text = dst_idx.read_text(errors="ignore").lower()
                # Extract nouns/concepts from dst
                words = re.findall(r'\b[a-z]{5,}\b', dst_text)
                dst_keywords = set(words[:200])  # sample

            overlap = 0
            for kw in dst_keywords:
                if kw in src_text:
                    overlap += 1

            if overlap > 15:  # threshold: meaningful overlap
                suggestions.append({
                    "src": src,
                    "dst": dst,
                    "overlap_score": overlap,
                    "reason": f"{dst} keywords appear {overlap}x in {src} frontier",
                })

    suggestions.sort(key=lambda x: x["overlap_score"], reverse=True)
    return suggestions[:20]


# ── Colony signaling ─────────────────────────────────────────────────────────

def write_signal(src: str, dst: str, message: str) -> None:
    """
    Write a peer-to-peer colony signal.
    Stored in dst's tasks/SIGNALS.md — readable by the destination colony.
    """
    dst_tasks = DOMAINS / dst / "tasks"
    if not dst_tasks.exists():
        print(f"Error: destination colony {dst} has no tasks/ directory")
        sys.exit(1)

    sf = dst_tasks / "SIGNALS.md"
    session = _current_session()
    today = _today()

    header = "# Colony Signals\n<!-- Peer-to-peer inter-colony messages. Format: | From | Message | Session | Date | -->\n"
    row = f"| {src} | {message} | {session} | {today} |\n"

    if not sf.exists():
        sf.write_text(header + "\n| From | Message | Session | Date |\n|------|---------|---------|------|\n" + row)
        print(f"Created {sf.relative_to(ROOT)} with signal from {src}")
    else:
        text = sf.read_text()
        sf.write_text(text + row)
        print(f"Appended signal to {sf.relative_to(ROOT)}")


def read_signals(domain: str) -> None:
    """Read colony signals for a domain."""
    sf = DOMAINS / domain / "tasks" / "SIGNALS.md"
    if not sf.exists():
        print(f"No signals for {domain}")
        return
    print(sf.read_text())


# ── CLI ──────────────────────────────────────────────────────────────────────

def cmd_map() -> None:
    stats = measure_signal_rate()
    print("=== COLONY INTERACTION MAP ===")
    print(f"Total colonies: {stats['total_colonies']}")
    print(f"Linked colonies: {stats['linked_colonies']}")
    print(f"Signal rate (INDEX.md cross-links): {stats['signal_rate']*100:.1f}%")
    print(f"Active SIGNALS.md files: {stats['active_signal_files']}")
    print(f"Peer signal edges: {len(stats['signal_file_edges'])}")
    print()
    if stats["edges"]:
        print("Detected inter-colony edges (INDEX.md):")
        for src, dst in stats["edges"]:
            print(f"  {src} → {dst}")
    else:
        print("No inter-colony edges detected via INDEX.md.")
    print()
    passive_pct = round(stats['linked_colonies'] / stats['total_colonies'] * 100, 1) if stats['total_colonies'] else 0
    active_pct = round(stats['active_signal_files'] / stats['total_colonies'] * 100, 1) if stats['total_colonies'] else 0
    print(f"Diagnosis: {passive_pct}% passive linkage (INDEX.md), {active_pct}% active signaling (SIGNALS.md).")
    if active_pct == 0:
        print("Colonies know about each other but cannot actively message each other.")
        print("F-EXP6: Active peer-to-peer inter-colony signal protocol needed.")
    else:
        print(f"Active signaling started ({stats['active_signal_files']}/{stats['total_colonies']} colonies).")
        print("F-EXP6: Compare artifact rate vs passive-only baseline at next measurement point.")


def cmd_suggest() -> None:
    print("=== COLONY PAIRING SUGGESTIONS ===")
    print("(colonies with high frontier keyword overlap — potential benefit from interaction)")
    print()
    suggestions = suggest_pairings()
    if not suggestions:
        print("No strong pairings found.")
        return
    for s in suggestions[:10]:
        print(f"  {s['src']} ← {s['dst']}: overlap_score={s['overlap_score']}")
    print()
    print(f"Top pair: {suggestions[0]['src']} ← {suggestions[0]['dst']}")


def cmd_signal(args: list[str]) -> None:
    if len(args) < 3:
        print("Usage: colony_interact.py signal <src> <dst> <message>")
        sys.exit(1)
    src, dst, msg = args[0], args[1], " ".join(args[2:])
    write_signal(src, dst, msg)


def cmd_signals(args: list[str]) -> None:
    if not args:
        # Show all domains with signals
        for d in ALL_DOMAIN_NAMES:
            sf = DOMAINS / d / "tasks" / "SIGNALS.md"
            if sf.exists():
                print(f"\n=== {d} ===")
                print(sf.read_text())
        return
    read_signals(args[0])


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "map":
        cmd_map()
    elif cmd == "suggest":
        cmd_suggest()
    elif cmd == "signal":
        cmd_signal(args)
    elif cmd == "signals":
        cmd_signals(args)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
