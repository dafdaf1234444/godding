#!/usr/bin/env python3
"""Synthetic steerer engine — creates and runs persistent synthetic humans.

Unlike personalities (session-scoped cognitive styles), steerers are persistent
directional authorities with their own worldviews imported from external knowledge.
They generate the kind of signals that the human node generates (Tier 1–2 reframes),
but from radically different intellectual traditions.

Usage:
  python3 tools/synthetic-steerers/steerer.py list          # list available steerers
  python3 tools/synthetic-steerers/steerer.py run <name>    # generate signals from steerer
  python3 tools/synthetic-steerers/steerer.py run --all     # all steerers generate signals
  python3 tools/synthetic-steerers/steerer.py history <name> # show steerer's signal history
  python3 tools/synthetic-steerers/steerer.py create <name> # scaffold a new steerer
  python3 tools/synthetic-steerers/steerer.py record <name> "sig1" "sig2"  # record signals
  python3 tools/synthetic-steerers/steerer.py respond <name> <target>      # cross-pollinate

Design (L-1336 inverse law): steerers produce SHORT directional signals (3–15 words),
not long analysis. The swarm decomposes; the steerer directs.
"""
import argparse
import glob
import json
import os
import random
import sys
from datetime import datetime
from pathlib import Path

STEERER_DIR = Path(__file__).parent
REPO_ROOT = STEERER_DIR.parent.parent
HISTORY_FILE = STEERER_DIR / "signal-history.json"


def load_steerer(name):
    """Load a steerer definition from its markdown file."""
    path = STEERER_DIR / f"{name}.md"
    if not path.exists():
        print(f"ERROR: steerer '{name}' not found at {path}")
        sys.exit(1)

    text = path.read_text()
    # Parse frontmatter
    parts = text.split("---", 2)
    if len(parts) < 3:
        print(f"ERROR: steerer '{name}' has no frontmatter")
        sys.exit(1)

    meta = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            meta[key.strip()] = val.strip()

    body = parts[2].strip()
    return {**meta, "body": body, "name": name}


def list_steerers():
    """List all available steerers."""
    files = sorted(STEERER_DIR.glob("*.md"))
    steerers = []
    for f in files:
        if f.name in ("README.md", "cross-challenges.md"):
            continue
        s = load_steerer(f.stem)
        steerers.append(s)

    if not steerers:
        print("No steerers found. Create one with: steerer.py create <name>")
        return

    print(f"{'Name':<25} {'Tradition':<25} {'Focus':<30} {'Signals'}")
    print("-" * 95)
    history = load_history()
    for s in steerers:
        count = len(history.get(s["name"], []))
        print(f"{s['name']:<25} {s.get('tradition', '?'):<25} {s.get('focus', '?'):<30} {count}")


def load_history():
    """Load signal history."""
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return {}


def save_history(history):
    """Save signal history."""
    HISTORY_FILE.write_text(json.dumps(history, indent=2))


def read_swarm_state():
    """Read minimal swarm state for steerer context."""
    state = {}

    # Current metrics from INDEX.md — extract counts like "1220L 252P 21B 12F"
    idx = REPO_ROOT / "memory" / "INDEX.md"
    if idx.exists():
        import re
        text = idx.read_text()
        counts = {}
        # Look for patterns like "**1220 lessons**", "**252 principles**", etc.
        for m in re.finditer(r'\*\*(\d+)\s+(lessons|principles|beliefs|frontiers)\*\*', text):
            num, kind = m.group(1), m.group(2)
            tag = {"lessons": "L", "principles": "P", "beliefs": "B", "frontiers": "F"}[kind]
            counts[tag] = num
        if counts:
            parts = []
            for tag in ["L", "P", "B", "F"]:
                if tag in counts:
                    parts.append(f"{counts[tag]}{tag}")
            state["index_header"] = " ".join(parts)
        else:
            state["index_header"] = "unknown"

    # Open frontiers
    frontiers = REPO_ROOT / "tasks" / "FRONTIER.md"
    if frontiers.exists():
        lines = frontiers.read_text().split("\n")
        open_f = [l for l in lines if "OPEN" in l and l.lstrip("- ~").startswith("**F")]
        state["open_frontiers"] = open_f[:10]

    # Philosophy claims
    phil = REPO_ROOT / "beliefs" / "PHILOSOPHY.md"
    if phil.exists():
        lines = phil.read_text().split("\n")
        claims = [l for l in lines if l.startswith("**[PHIL-")]
        state["philosophy"] = claims[:15]

    # Recent human signals
    signals = REPO_ROOT / "tasks" / "SIGNALS.md"
    if signals.exists():
        lines = signals.read_text().split("\n")
        human_sigs = [l for l in lines if "| human |" in l]
        state["recent_human_signals"] = human_sigs[-5:]

    # Dogma/ossified beliefs (from orient output or dogma finder)
    state["ossified_count"] = "17 ossified claims (run dogma_finder.py)"

    # Sample 3 random lessons for grounding
    lesson_dir = REPO_ROOT / "memory" / "lessons"
    if lesson_dir.exists():
        lessons = list(lesson_dir.glob("L-*.md"))
        if lessons:
            sample = random.sample(lessons, min(3, len(lessons)))
            state["sampled_lessons"] = []
            for lf in sample:
                lines = lf.read_text().split("\n")
                title_line = [l for l in lines if l.startswith("Title:")]
                if title_line:
                    state["sampled_lessons"].append(f"{lf.stem}: {title_line[0]}")

    return state


def run_steerer(name):
    """Generate signals from a steerer's perspective."""
    s = load_steerer(name)
    state = read_swarm_state()

    print(f"\n{'='*60}")
    print(f"SYNTHETIC STEERER: {s['name']}")
    print(f"Tradition: {s.get('tradition', 'unknown')}")
    print(f"Focus: {s.get('focus', 'unknown')}")
    print(f"{'='*60}")
    print(f"\n## Worldview\n{s['body'][:500]}...")
    print(f"\n## Swarm state snapshot")
    print(f"  Index: {state.get('index_header', 'unknown')}")
    print(f"  Open frontiers: {len(state.get('open_frontiers', []))}")
    print(f"  Philosophy claims: {len(state.get('philosophy', []))}")
    print(f"  Ossified: {state.get('ossified_count', '?')}")

    if state.get("sampled_lessons"):
        print(f"\n## Random lesson sample (for grounding)")
        for l in state["sampled_lessons"]:
            print(f"  - {l}")

    print(f"\n## Steerer prompt")
    print(f"  Given this swarm state and your worldview ({s.get('tradition', '')}),")
    print(f"  generate 2-3 directional signals (3-15 words each).")
    print(f"  These are Tier 1/2 reframes, not tasks.")
    print(f"  Format: one signal per line, prefixed with [SIGNAL]")
    print()

    # The actual signal generation happens in the LLM session that runs this tool.
    # This tool provides the context and framing. The session writes signals.
    # Record that this steerer was consulted.
    history = load_history()
    if name not in history:
        history[name] = []
    history[name].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "session": f"S{_current_session()}",
        "state_snapshot": state.get("index_header", ""),
        "signals": []  # filled in by the session after generation
    })
    save_history(history)
    return state


def show_history(name):
    """Show a steerer's signal history."""
    history = load_history()
    entries = history.get(name, [])
    if not entries:
        print(f"No signal history for '{name}'")
        return

    print(f"\nSignal history for '{name}' ({len(entries)} consultations):")
    for e in entries:
        print(f"  {e['date']} ({e.get('session', '?')}): {len(e.get('signals', []))} signals")
        for sig in e.get("signals", []):
            print(f"    -> {sig}")


def create_steerer(name):
    """Scaffold a new steerer file."""
    path = STEERER_DIR / f"{name}.md"
    if path.exists():
        print(f"Steerer '{name}' already exists at {path}")
        return

    template = f"""---
name: {name}
tradition: [intellectual tradition]
focus: [what aspect of the swarm this steerer challenges]
type: synthetic-steerer
created: {datetime.now().strftime('%Y-%m-%d')}
---

## Worldview
[What does this person fundamentally believe about systems, knowledge, growth?]

## What they see when they look at the swarm
[What aspects of the swarm would this person notice first?]

## Signal style
[How does this person communicate? Short aphorisms? Questions? Provocations?]

## Blind spots they correct
[What does the swarm miss that this worldview catches?]

## Historical exemplars
[Real thinkers who embody this worldview — for grounding, not impersonation]
"""
    path.write_text(template)
    print(f"Created steerer scaffold at {path}")
    print(f"Edit it, then run: python3 tools/synthetic-steerers/steerer.py run {name}")


def record_signals(name, signals):
    """Record signals into the most recent history entry for a steerer."""
    history = load_history()
    entries = history.get(name, [])
    if not entries:
        print(f"ERROR: no history entries for '{name}'. Run the steerer first.")
        sys.exit(1)

    # Find the most recent entry with an empty signals array
    target = None
    for i in range(len(entries) - 1, -1, -1):
        if not entries[i].get("signals"):
            target = i
            break

    if target is None:
        print(f"ERROR: no empty-signals entry found for '{name}'. Run the steerer first to create one.")
        sys.exit(1)

    entries[target]["signals"] = list(signals)
    history[name] = entries
    save_history(history)
    print(f"Recorded {len(signals)} signal(s) for '{name}' (entry {entries[target]['date']} {entries[target].get('session', '?')}):")
    for sig in signals:
        print(f"  -> {sig}")


def respond_to_steerer(name, target_name):
    """Show steerer `name` the signals from steerer `target_name` and prompt for a response."""
    s = load_steerer(name)
    t = load_steerer(target_name)
    history = load_history()

    # Get target's most recent non-empty signals
    target_entries = history.get(target_name, [])
    target_signals = []
    for entry in reversed(target_entries):
        if entry.get("signals"):
            target_signals = entry["signals"]
            break

    if not target_signals:
        print(f"ERROR: '{target_name}' has no recorded signals to respond to.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print(f"CROSS-POLLINATION: {name} responds to {target_name}")
    print(f"{'='*60}")
    print(f"\n## {target_name}'s signals ({t.get('tradition', 'unknown')}):")
    for sig in target_signals:
        print(f"  -> {sig}")
    print(f"\n## {name}'s worldview ({s.get('tradition', 'unknown')}):")
    print(f"  {s['body'][:300]}...")
    print(f"\n## Prompt")
    print(f"  You are {name} ({s.get('tradition', '')}). You just heard these signals from")
    print(f"  {target_name} ({t.get('tradition', '')}). Generate 1-2 response signals (3-15 words).")
    print(f"  Respond to their framing from YOUR worldview. Agree, challenge, or reframe.")
    print(f"  Format: one signal per line, prefixed with [SIGNAL]")
    print()

    # Record that this cross-pollination was initiated
    if name not in history:
        history[name] = []
    history[name].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "session": f"S{_current_session()}",
        "state_snapshot": f"respond-to:{target_name}",
        "signals": []  # filled in by the session
    })
    save_history(history)


def _current_session():
    """Best-effort session number from NEXT.md."""
    try:
        next_md = REPO_ROOT / "tasks" / "NEXT.md"
        if next_md.exists():
            first = next_md.read_text().split("\n")[0]
            if "S" in first:
                import re
                m = re.search(r"S(\d+)", first)
                if m:
                    return m.group(1)
    except Exception:
        pass
    return "?"


def main():
    parser = argparse.ArgumentParser(description="Synthetic steerer engine")
    parser.add_argument("command", choices=["list", "run", "history", "create", "record", "respond"])
    parser.add_argument("name", nargs="?", default=None)
    parser.add_argument("signals", nargs="*", default=[])
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if args.command == "list":
        list_steerers()
    elif args.command == "run":
        if args.all:
            files = sorted(STEERER_DIR.glob("*.md"))
            for f in files:
                if f.name in ("README.md", "cross-challenges.md"):
                    continue
                run_steerer(f.stem)
        elif args.name:
            run_steerer(args.name)
        else:
            print("Usage: steerer.py run <name> or steerer.py run --all")
    elif args.command == "history":
        if args.name:
            show_history(args.name)
        else:
            print("Usage: steerer.py history <name>")
    elif args.command == "create":
        if args.name:
            create_steerer(args.name)
        else:
            print("Usage: steerer.py create <name>")
    elif args.command == "record":
        if args.name and args.signals:
            record_signals(args.name, args.signals)
        else:
            print('Usage: steerer.py record <name> "<signal1>" "<signal2>" ...')
    elif args.command == "respond":
        if args.name and args.signals:
            respond_to_steerer(args.name, args.signals[0])
        else:
            print("Usage: steerer.py respond <name> <target-name>")


if __name__ == "__main__":
    main()
