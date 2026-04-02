#!/usr/bin/env python3
"""
classify.py — Classify any public figure against the six universal sins.

Input: a name and a list of known facts (from public record).
Output: a simple card. SAID vs DID. Evidence grade. Sin classification.

This is the simplest possible version:
  python3 tools/classify.py

It walks you through it. Name. Facts. Sources. Done. Card out.

For bulk/automated use, feed it JSON:
  python3 tools/classify.py --from records/leaders.json
"""

import json
import sys
from datetime import datetime


# The six sins — what every civilization agrees on
SINS = {
    "HARM_CHILDREN": {
        "name": "Harming children",
        "tier": 3,
        "keywords": [
            "child abuse", "minor", "underage", "trafficking children",
            "child labor", "child soldiers", "child marriage",
            "pedophil", "sexual abuse of minors", "exploitation of children",
        ],
    },
    "MURDER": {
        "name": "Murder of innocents",
        "tier": 2,
        "keywords": [
            "war crime", "civilian casualties", "massacre", "assassination",
            "extrajudicial", "torture", "bombing civilian", "genocide",
            "ethnic cleansing", "crimes against humanity",
        ],
    },
    "THEFT": {
        "name": "Theft from the powerless",
        "tier": 1,
        "keywords": [
            "embezzlement", "corruption", "bribery", "stolen", "looted",
            "offshore accounts", "shell companies", "money laundering",
            "tax evasion", "fraud", "kleptocracy", "misappropriation",
            "enrichment", "unexplained wealth",
        ],
    },
    "SLAVERY": {
        "name": "Slavery / forced labor",
        "tier": 2,
        "keywords": [
            "forced labor", "slavery", "trafficking", "debt bondage",
            "forced marriage", "human trafficking", "sweatshop",
            "modern slavery", "indentured",
        ],
    },
    "DESTROY_TRUTH": {
        "name": "Destruction of truth",
        "tier": 2,
        "keywords": [
            "censorship", "jailed journalist", "killed journalist",
            "destroyed evidence", "cover-up", "classified", "sealed records",
            "threatened witness", "NDA", "silenced", "propaganda",
            "disinformation campaign", "media control",
        ],
    },
    "BETRAYAL": {
        "name": "Betrayal of trust",
        "tier": 1,
        "keywords": [
            "abuse of power", "oath of office", "conflict of interest",
            "nepotism", "cronyism", "breach of duty", "violated oath",
            "self-dealing", "insider", "position of trust",
        ],
    },
}

EVIDENCE_GRADES = {
    "A":  "Court records, convictions, official legal findings",
    "A-": "Financial disclosures, government records, FOIA documents",
    "B":  "Major investigative journalism (3+ independent outlets)",
    "B-": "Multiple independent witnesses or documents agree",
    "C":  "One credible source, not yet corroborated",
    "C-": "Formal allegation (lawsuit filed, complaint made)",
    "D":  "Unverified claim",
    "S":  "Self-reported (they admitted it themselves)",
}


def classify_facts(facts: list) -> dict:
    """
    Given a list of fact strings, classify which sins they match.
    Returns {sin_code: [matching_facts]}.
    """
    matches = {}
    for fact in facts:
        fact_lower = fact.lower()
        for code, sin in SINS.items():
            for keyword in sin["keywords"]:
                if keyword in fact_lower:
                    if code not in matches:
                        matches[code] = []
                    if fact not in matches[code]:
                        matches[code].append(fact)
                    break
    return matches


def highest_tier(matches: dict) -> int:
    """Return the highest (worst) tier from matched sins."""
    if not matches:
        return 0
    return max(SINS[code]["tier"] for code in matches)


def generate_card(record: dict) -> str:
    """Generate a text card from a record."""
    name = record["name"]
    role = record.get("role", "")
    country = record.get("country", "")
    said = record.get("said", [])
    did = record.get("did", [])
    facts = record.get("facts", [])
    sources = record.get("sources", [])
    grade = record.get("grade", "C")

    matches = classify_facts(facts + did)
    tier = highest_tier(matches)

    lines = []
    lines.append("=" * 56)
    lines.append(f"  {name}")
    if role:
        lines.append(f"  {role}" + (f" — {country}" if country else ""))
    lines.append("=" * 56)

    # SAID
    if said:
        lines.append("")
        lines.append("  SAID:")
        for s in said:
            lines.append(f'    "{s}"')

    # DID
    if did:
        lines.append("")
        lines.append("  DID:")
        for d in did:
            lines.append(f"    {d}")

    # SINS MATCHED
    if matches:
        lines.append("")
        tier_word = {1: "TIER 1", 2: "TIER 2", 3: "TIER 3 — WORST"}
        lines.append(f"  CLASSIFICATION: {tier_word.get(tier, '?')}")
        for code, matched_facts in matches.items():
            sin = SINS[code]
            lines.append(f"    [{sin['name']}]")
            for f in matched_facts[:2]:  # Show max 2 per sin
                lines.append(f"      - {f}")
    else:
        lines.append("")
        lines.append("  CLASSIFICATION: No universal sins matched from provided facts.")
        lines.append("  (This could mean clean, or could mean insufficient data.)")

    # EVIDENCE
    lines.append("")
    lines.append(f"  EVIDENCE GRADE: {grade}")
    lines.append(f"    = {EVIDENCE_GRADES.get(grade, '?')}")
    if sources:
        lines.append("  SOURCES:")
        for src in sources:
            lines.append(f"    - {src}")

    lines.append("")
    lines.append("-" * 56)
    lines.append("  This card DESCRIBES. It does not SENTENCE.")
    lines.append("  You read it. You decide what it means.")
    lines.append("-" * 56)

    return "\n".join(lines)


def generate_html_card(record: dict) -> str:
    """Generate an HTML card snippet for embedding."""
    name = record["name"]
    role = record.get("role", "")
    said = record.get("said", [])
    did = record.get("did", [])
    facts = record.get("facts", [])
    grade = record.get("grade", "C")
    sources = record.get("sources", [])

    matches = classify_facts(facts + did)
    tier = highest_tier(matches)

    sin_tags = ""
    for code in matches:
        sin = SINS[code]
        t = sin["tier"]
        color = {1: "#d4a574", 2: "#c47474", 3: "#8a4a4a"}.get(t, "#999")
        sin_tags += f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:4px;font-size:11px;margin-right:4px;">{sin["name"]}</span>'

    said_html = "<br>".join(f'"{s}"' for s in said) if said else ""
    did_html = "<br>".join(did) if did else ""
    src_html = " &middot; ".join(sources[:3]) if sources else ""

    return f"""<div class="card">
<div class="card-half card-said">
<div class="label label-said">THEY SAID</div>
<div class="card-text">{said_html}</div>
</div>
<div class="card-half card-did">
<div class="label label-did">THEY DID</div>
<div class="card-text">{did_html}</div>
</div>
<div class="proof">
<span class="grade-badge">Grade {grade}</span>
<span class="proof-text">{src_html}</span>
</div>
<div style="padding:10px 28px;background:#111;">
{sin_tags}
<span style="color:#555;font-size:12px;margin-left:8px;">{name} — {role}</span>
</div>
</div>"""


def interactive():
    """Walk someone through creating a card. No knowledge needed."""
    print()
    print("=" * 50)
    print("  CLASSIFY A PUBLIC FIGURE")
    print("  Answer the questions. Get the card.")
    print("=" * 50)
    print()

    name = input("  Name: ").strip()
    if not name:
        print("  Need a name. Try again.")
        return

    role = input("  Role (president, CEO, etc): ").strip()
    country = input("  Country: ").strip()

    print()
    print("  What did they SAY? (public promises, quotes)")
    print("  Enter one per line. Empty line when done.")
    said = []
    while True:
        s = input("    > ").strip()
        if not s:
            break
        said.append(s)

    print()
    print("  What did they actually DO? (facts, outcomes)")
    print("  Enter one per line. Empty line when done.")
    did = []
    while True:
        d = input("    > ").strip()
        if not d:
            break
        did.append(d)

    print()
    print("  Any other known facts? (allegations, investigations, etc)")
    print("  Enter one per line. Empty line when done.")
    facts = []
    while True:
        f = input("    > ").strip()
        if not f:
            break
        facts.append(f)

    print()
    print("  Evidence sources? (court records, news outlets, etc)")
    print("  Enter one per line. Empty line when done.")
    sources = []
    while True:
        src = input("    > ").strip()
        if not src:
            break
        sources.append(src)

    print()
    print("  Evidence grade?")
    for g, desc in EVIDENCE_GRADES.items():
        print(f"    {g:3s} = {desc}")
    grade = input("  Grade [B]: ").strip() or "B"

    record = {
        "name": name,
        "role": role,
        "country": country,
        "said": said,
        "did": did,
        "facts": facts,
        "sources": sources,
        "grade": grade,
        "classified_at": datetime.now().isoformat(),
    }

    print()
    print(generate_card(record))

    # Save
    save = input("\n  Save this record? (y/n) [y]: ").strip().lower()
    if save != "n":
        slug = name.lower().replace(" ", "_").replace(".", "")
        path = f"records/{slug}.json"
        import os
        os.makedirs("records", exist_ok=True)
        with open(path, "w") as f:
            json.dump(record, f, indent=2)
        print(f"  Saved to {path}")

    return record


def from_json(path: str):
    """Load records from JSON file and generate cards."""
    with open(path) as f:
        data = json.load(f)

    records = data if isinstance(data, list) else [data]

    for record in records:
        print(generate_card(record))
        print()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--from":
        from_json(sys.argv[2])
    elif len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage:")
        print("  python3 tools/classify.py              Interactive mode")
        print("  python3 tools/classify.py --from X.json Load from file")
        print()
        print("Evidence grades:")
        for g, desc in EVIDENCE_GRADES.items():
            print(f"  {g:3s} = {desc}")
        print()
        print("Six universal sins:")
        for code, sin in SINS.items():
            print(f"  Tier {sin['tier']}: {sin['name']}")
    else:
        interactive()
