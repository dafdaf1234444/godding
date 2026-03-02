#!/usr/bin/env python3
"""Bridge file synchronization tool (fundamental-setup-reswarm S355).

Reduces friction from manual bridge file synchronization by detecting
protocol-critical changes and suggesting updates across all bridge files.

Usage:
  python3 tools/sync_bridges.py                    # check sync status
  python3 tools/sync_bridges.py --suggest          # suggest sync actions
  python3 tools/sync_bridges.py --check <file>     # check specific file
"""
import argparse
import hashlib
import os
import re
from typing import Dict, List, Set


def get_bridge_files() -> Dict[str, str]:
    """Get all bridge files and their paths."""
    return {
        "CLAUDE.md": "CLAUDE.md",
        "AGENTS.md": "AGENTS.md",
        "GEMINI.md": "GEMINI.md",
        ".cursorrules": ".cursorrules",
        ".cursor/rules/swarm.mdc": ".cursor/rules/swarm.mdc",
        ".windsurfrules": ".windsurfrules",
        ".github/copilot-instructions.md": ".github/copilot-instructions.md"
    }


def extract_protocol_sections(content: str) -> Dict[str, str]:
    """Extract protocol-critical sections from bridge file content."""
    sections = {}

    # Multi-tool compatibility section
    if "Multi-tool compatibility" in content:
        match = re.search(r"## Multi-tool compatibility.*?\n(?=##|$)", content, re.DOTALL)
        if match:
            sections["multi_tool"] = match.group(0).strip()

    # Minimum Swarmed Cycle
    if "Minimum Swarmed Cycle" in content:
        match = re.search(r"## Minimum Swarmed Cycle.*?\n(?=##|$)", content, re.DOTALL)
        if match:
            sections["min_cycle"] = match.group(0).strip()

    # Expert dispatch mentions
    expert_dispatch = re.findall(r".*[Ee]xpert dispatch.*", content)
    if expert_dispatch:
        sections["expert_dispatch"] = "\n".join(expert_dispatch)

    # Node interaction patterns
    if "Node interaction" in content:
        match = re.search(r".*[Nn]ode interaction.*?\n(?=  -|\n\n|$)", content, re.DOTALL)
        if match:
            sections["node_interaction"] = match.group(0).strip()

    return sections


def check_bridge_sync() -> Dict[str, Dict]:
    """Check synchronization status of all bridge files."""
    bridges = get_bridge_files()
    results = {}

    for name, path in bridges.items():
        if os.path.exists(path):
            with open(path, 'r') as f:
                content = f.read()

            results[name] = {
                "exists": True,
                "size": len(content),
                "sections": extract_protocol_sections(content),
                "hash": hashlib.md5(content.encode()).hexdigest()[:8]
            }
        else:
            results[name] = {"exists": False}

    return results


def find_sync_gaps(sync_status: Dict) -> List[str]:
    """Find potential synchronization gaps between bridge files."""
    gaps = []
    existing_bridges = {k: v for k, v in sync_status.items() if v.get("exists", False)}

    if len(existing_bridges) < 2:
        return gaps

    # Check for protocol sections that exist in some bridges but not others
    all_sections = set()
    for bridge_data in existing_bridges.values():
        all_sections.update(bridge_data.get("sections", {}).keys())

    for section in all_sections:
        bridges_with_section = []
        bridges_without_section = []

        for name, data in existing_bridges.items():
            if section in data.get("sections", {}):
                bridges_with_section.append(name)
            else:
                bridges_without_section.append(name)

        if bridges_without_section and len(bridges_with_section) > 0:
            gaps.append(f"Section '{section}' in {bridges_with_section} but missing from {bridges_without_section}")

    return gaps


def suggest_sync_actions(sync_status: Dict, gaps: List[str]) -> List[str]:
    """Suggest concrete actions to fix sync gaps."""
    suggestions = []

    if not gaps:
        suggestions.append("✅ No sync gaps detected between bridge files")
        return suggestions

    suggestions.append("📋 Bridge sync suggestions:")

    existing_bridges = [k for k, v in sync_status.items() if v.get("exists", False)]

    for gap in gaps:
        suggestions.append(f"  • {gap}")

    # Suggest checking the most recently modified bridge as the source of truth
    suggestions.append("\n🔧 Recommended action:")
    suggestions.append("  1. Identify which bridge file has the most recent protocol updates")
    suggestions.append("  2. Copy protocol-critical sections to other bridges")
    suggestions.append("  3. Adapt tool-specific syntax while preserving semantic content")
    suggestions.append("  4. Test each bridge with its respective tool if possible")

    return suggestions


def main():
    parser = argparse.ArgumentParser(description="Bridge file synchronization checker")
    parser.add_argument("--suggest", action="store_true", help="Show sync suggestions")
    parser.add_argument("--check", help="Check specific bridge file")
    args = parser.parse_args()

    print("=== BRIDGE SYNC STATUS ===")

    sync_status = check_bridge_sync()

    if args.check:
        if args.check in sync_status:
            data = sync_status[args.check]
            print(f"\n{args.check}:")
            if data.get("exists"):
                print(f"  Size: {data['size']} chars")
                print(f"  Hash: {data['hash']}")
                print(f"  Sections: {list(data.get('sections', {}).keys())}")
            else:
                print("  Status: FILE NOT FOUND")
        else:
            print(f"Unknown bridge file: {args.check}")
        return

    # Show status summary
    existing = sum(1 for v in sync_status.values() if v.get("exists", False))
    total = len(sync_status)
    print(f"Bridge files: {existing}/{total} exist")

    for name, data in sync_status.items():
        status = "✅" if data.get("exists") else "❌"
        print(f"  {status} {name}")

    # Check for sync gaps
    gaps = find_sync_gaps(sync_status)

    if args.suggest:
        suggestions = suggest_sync_actions(sync_status, gaps)
        print(f"\n{chr(10).join(suggestions)}")
    else:
        print(f"\nSync gaps: {len(gaps)} detected")
        if gaps:
            print("  Run with --suggest for recommendations")


if __name__ == "__main__":
    main()