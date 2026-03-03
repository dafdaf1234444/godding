#!/usr/bin/env python3
"""create_domain.py — scaffold a new swarm domain with the standard 4-file structure.

Usage:
  python3 tools/create_domain.py <domain-name> [--topic "Short topic description"]

Creates:
  domains/<domain-name>/DOMAIN.md       — domain identity and scope
  domains/<domain-name>/COLONY.md       — domain colony state
  domains/<domain-name>/INDEX.md        — lesson index (initially empty)
  domains/<domain-name>/tasks/FRONTIER.md — domain frontier questions

Replaces manual scaffolding pattern (L-601: creation-time structure).
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAINS_DIR = ROOT / "domains"

DOMAIN_MD_TEMPLATE = """# Domain: {title}
Topic: {topic}
Beliefs: (none yet — first DOMEX session)
"""

COLONY_MD_TEMPLATE = """# Colony: {title}

## Active Sessions
(none yet)

## Merged Sessions
| Session | Lesson | Finding |
|---------|--------|---------|
"""

INDEX_MD_TEMPLATE = """# {title} Domain Index
Updated: {date} (domain genesis)

## Active Frontiers
- (see tasks/FRONTIER.md)

## Lessons
(none yet)
"""

FRONTIER_MD_TEMPLATE = """# {title} Domain — Frontier Questions
Domain agent: write here, not to tasks/FRONTIER.md
Updated: {date} | Active: 0

## Active

(none yet — open with python3 tools/open_lane.py)

## Resolved
| ID | Answer | Session | Date |
|----|--------|---------|------|
| (none) | | | |
"""


def main():
    parser = argparse.ArgumentParser(description="Scaffold a new swarm domain.")
    parser.add_argument("domain", help="Domain slug (e.g. 'string-theory')")
    parser.add_argument("--topic", default="(domain topic — fill in before first DOMEX session)",
                        help="Short topic description")
    args = parser.parse_args()

    domain_slug = args.domain.lower().replace(" ", "-")
    title = " ".join(w.capitalize() for w in domain_slug.replace("-", " ").split())
    domain_dir = DOMAINS_DIR / domain_slug
    tasks_dir = domain_dir / "tasks"

    if domain_dir.exists():
        print(f"ERROR: domain already exists: {domain_dir}", file=sys.stderr)
        sys.exit(1)

    from datetime import date
    today = date.today().strftime("%Y-%m-%d")

    tasks_dir.mkdir(parents=True)

    (domain_dir / "DOMAIN.md").write_text(
        DOMAIN_MD_TEMPLATE.format(title=title, topic=args.topic))
    (domain_dir / "COLONY.md").write_text(
        COLONY_MD_TEMPLATE.format(title=title))
    (domain_dir / "INDEX.md").write_text(
        INDEX_MD_TEMPLATE.format(title=title, date=today))
    (tasks_dir / "FRONTIER.md").write_text(
        FRONTIER_MD_TEMPLATE.format(title=title, date=today))

    print(f"Created domain: {domain_slug}")
    print(f"  {domain_dir}/DOMAIN.md")
    print(f"  {domain_dir}/COLONY.md")
    print(f"  {domain_dir}/INDEX.md")
    print(f"  {domain_dir}/tasks/FRONTIER.md")
    print(f"\nNext: open a DOMEX lane with python3 tools/open_lane.py")


if __name__ == "__main__":
    main()
