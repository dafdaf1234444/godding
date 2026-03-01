"""
domain_map.py — shared module for lane-abbreviation → domain-name resolution.

Extracted from dispatch_optimizer.py (L-909: spec-as-module pattern, L-905).
Any tool that needs to map DOMEX-XXX lane IDs to domain directory names
should import from here rather than maintaining its own copy.

Usage:
    from tools.domain_map import LANE_ABBREV_TO_DOMAIN, COUNCIL_TOPIC_TO_DOMAIN, resolve_lane_domain

    dom = resolve_lane_domain("DOMEX-BRN-S411")  # → "brain"
"""

from __future__ import annotations
import re

# L-909: extracted from dispatch_optimizer.py S411. Add new entries here when
# a new domain or lane abbreviation is introduced.
LANE_ABBREV_TO_DOMAIN: dict[str, str] = {
    # Legacy abbreviations (S302-S340 era)
    "NK": "nk-complexity", "LNG": "linguistics", "EXP": "expert-swarm",
    "STAT": "statistics", "PHI": "philosophy", "CTX": "meta", "MECH": "meta",
    "FLD": "fluid-dynamics", "BRN": "brain", "HLP": "helper-swarm",
    "ECO": "economy", "PHY": "physics", "SCI": "evaluation", "EVO": "evolution",
    "DNA": "meta", "IS": "information-science", "HS": "human-systems",
    "COMP": "competitions", "INFO": "information-science",
    # Full-name and common abbreviations (L-676: 33 were missing — 65% data loss)
    "META": "meta", "SP": "stochastic-processes", "EMP": "empathy",
    "AI": "ai", "CON": "conflict", "CONFLICT": "conflict",
    "CAT": "catastrophic-risks", "DS": "distributed-systems",
    "FIN": "finance", "GOV": "governance", "EVAL": "evaluation",
    "FRA": "fractals", "FRACTALS": "fractals", "GT": "graph-theory",
    "GTH": "graph-theory", "GAME": "gaming", "GAMING": "gaming",
    "SEC": "security", "SECURITY": "security",
    "GUE": "guesstimates", "GAM": "game-theory", "PSY": "psychology",
    "SOC": "social-media", "STR": "strategy", "QC": "quality",
    "QUALITY": "quality", "OR": "operations-research", "OPS": "operations-research",
    "FARMING": "farming", "FAR": "farming", "COORD": "meta", "HUMAN": "human-systems",
    "INFOFLOW": "information-science", "INFRA": "meta", "GEN": "meta",
    "DREAM": "dream", "BRAIN": "brain", "ECON": "economy", "ECONOMY": "economy",
    "EMPATHY": "empathy", "EVOLUTION": "evolution", "EXPERT": "expert-swarm",
    "AGENT": "meta", "CT": "meta", "CTL": "control-theory",
    "CC": "cryptocurrency", "CRY": "cryptography", "CRYPTO": "cryptocurrency",
    "CRYPTOGRAPHY": "cryptography",
    "PRO": "protocol-engineering", "README": "meta",
    "SCHED": "meta", "PRIORITY": "meta", "UNIVERSALITY": "meta",
    "PERSONALITY": "psychology",
}

COUNCIL_TOPIC_TO_DOMAIN: dict[str, str] = {
    "AGENT-AWARE": "meta", "SCIENCE": "evaluation", "DNA": "meta",
    "EXPERT-SWARM": "expert-swarm", "USE-CASES": "meta",
}


def resolve_lane_domain(lane_id: str) -> str | None:
    """Return the domain name for a DOMEX-XXX or COUNCIL-XXX lane ID.

    Returns None if the lane cannot be mapped to a known domain.

    Examples:
        resolve_lane_domain("DOMEX-BRN-S411") -> "brain"
        resolve_lane_domain("DOMEX-META-S411") -> "meta"
        resolve_lane_domain("COUNCIL-EXPERT-SWARM-S390") -> "expert-swarm"
    """
    m = re.match(r"DOMEX-([A-Z]+)", lane_id)
    if m:
        dom = LANE_ABBREV_TO_DOMAIN.get(m.group(1))
        if dom:
            return dom
    m = re.match(r"COUNCIL-([A-Z-]+)-S\d+", lane_id)
    if m:
        return COUNCIL_TOPIC_TO_DOMAIN.get(m.group(1))
    return None


if __name__ == "__main__":
    # Quick audit: show all known abbreviation→domain mappings
    print(f"LANE_ABBREV_TO_DOMAIN: {len(LANE_ABBREV_TO_DOMAIN)} entries")
    domains = sorted(set(LANE_ABBREV_TO_DOMAIN.values()))
    print(f"Unique domains covered: {len(domains)}")
    for d in domains:
        abbrevs = [k for k, v in LANE_ABBREV_TO_DOMAIN.items() if v == d]
        print(f"  {d}: {', '.join(abbrevs)}")
