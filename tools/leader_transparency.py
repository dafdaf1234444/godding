#!/usr/bin/env python3
"""
leader_transparency.py — Invented senses for public accountability.

Five senses the swarm invents to help humans see clearly:

  SIGHT   — direct evidence from public record (court docs, financial disclosures,
             voting records, official statements, verified footage)
  HEARING — testimony aggregation (what witnesses, journalists, victims,
             whistleblowers report — weighted by independence and corroboration)
  SMELL   — pattern detection (does this person's behavior match known patterns
             of corruption, abuse, authoritarianism? statistical, not accusation)
  TASTE   — consistency check (does what they say match what they do?
             promises vs outcomes, public persona vs private record)
  TOUCH   — impact measurement (who benefits, who suffers from their decisions?
             follow the consequences downstream to real human lives)

Principle: the tool DESCRIBES. It does not SENTENCE.
           Humans see. Humans decide. The tool makes hiding impossible.

Connects to: justice.html (PHIL-29), human_impact.py (F-SOUL1)
"""

import json
import hashlib
from datetime import datetime, date
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


# === Evidence quality tiers ===

class EvidenceGrade(Enum):
    """How reliable is this piece of information?"""
    COURT_RECORD = "A"       # Court documents, legal findings, convictions
    OFFICIAL_DOC = "A-"      # Financial disclosures, government records, FOIA
    VERIFIED_JOURNALISM = "B" # Major investigative journalism, multiple sources
    CORROBORATED = "B-"      # Multiple independent witnesses or documents agree
    SINGLE_SOURCE = "C"      # One credible source, not yet corroborated
    ALLEGATION = "C-"        # Formal allegation (lawsuit filed, complaint made)
    UNVERIFIED = "D"         # Rumor, social media, uncorroborated claim
    SELF_REPORTED = "S"      # The person themselves said/admitted it

    def weight(self) -> float:
        weights = {
            "A": 1.0, "A-": 0.9, "B": 0.75, "B-": 0.6,
            "C": 0.35, "C-": 0.25, "D": 0.05, "S": 0.85
        }
        return weights[self.value]


# === Categories of concern (the "sins") ===

class ConcernCategory(Enum):
    """What type of harm or violation is this?"""
    CORRUPTION = "corruption"           # Bribery, embezzlement, kleptocracy
    VIOLENCE = "violence"               # War crimes, ordering violence, torture
    SEXUAL_ABUSE = "sexual_abuse"       # Any sexual crime, especially against minors
    CHILD_HARM = "child_harm"           # Direct or systemic harm to children
    HUMAN_RIGHTS = "human_rights"       # Suppression of speech, assembly, press, religion
    FINANCIAL_CRIME = "financial_crime" # Money laundering, tax evasion, fraud
    ELECTION_FRAUD = "election_fraud"   # Rigging elections, suppressing votes
    NEPOTISM = "nepotism"               # Placing family in power without merit
    ENVIRONMENTAL = "environmental"     # Knowingly causing ecological destruction
    BETRAYAL = "betrayal"               # Betraying public trust, oath of office
    COVERUP = "coverup"                 # Destroying evidence, silencing witnesses


# === The five senses ===

@dataclass
class SightEvidence:
    """SIGHT: direct evidence from public record."""
    source: str              # Where this evidence comes from
    document_type: str       # Court filing, financial disclosure, official record, etc.
    date_of_record: str      # When the record was created
    summary: str             # What it says, in plain language
    url: Optional[str] = None  # Link to source if available
    grade: str = "B"         # EvidenceGrade value


@dataclass
class HearingTestimony:
    """HEARING: what witnesses and reporters say."""
    source_type: str         # journalist, whistleblower, victim, witness, official
    outlet_or_context: str   # Where was this reported/said
    date: str
    summary: str
    corroborated_by: list = field(default_factory=list)  # Other sources that confirm
    grade: str = "C"


@dataclass
class SmellPattern:
    """SMELL: pattern detection — does behavior match known harmful patterns?"""
    pattern_name: str        # e.g., "authoritarian consolidation", "kleptocratic extraction"
    indicators_present: list = field(default_factory=list)  # Which indicators match
    indicators_absent: list = field(default_factory=list)   # Which indicators DON'T match
    match_strength: float = 0.0   # 0.0 to 1.0
    reference: str = ""      # Academic/historical reference for this pattern


@dataclass
class TasteConsistency:
    """TASTE: does what they say match what they do?"""
    claim: str               # What the person said/promised
    claim_date: str
    claim_source: str
    reality: str             # What actually happened
    reality_date: str
    reality_source: str
    consistency: float = 0.0  # -1.0 (opposite) to 1.0 (perfectly consistent)


@dataclass
class TouchImpact:
    """TOUCH: who benefits and who suffers from their decisions?"""
    decision: str            # The action/policy/decision
    date: str
    beneficiaries: list = field(default_factory=list)     # Who gained
    harmed: list = field(default_factory=list)             # Who was hurt
    scale: str = "individual"  # individual, community, national, global
    reversible: bool = True    # Can the harm be undone?


# === Accountability record: one person ===

@dataclass
class AccountabilityRecord:
    """Complete transparency record for one public figure."""

    # Identity
    name: str
    role: str                # Current or most recent role
    country: str
    in_power: bool = True
    family_of: Optional[str] = None  # If this is a child/relative of a leader

    # The five senses
    sight: list = field(default_factory=list)      # SightEvidence items
    hearing: list = field(default_factory=list)     # HearingTestimony items
    smell: list = field(default_factory=list)       # SmellPattern items
    taste: list = field(default_factory=list)       # TasteConsistency items
    touch: list = field(default_factory=list)       # TouchImpact items

    # Categories flagged
    concerns: list = field(default_factory=list)    # ConcernCategory values

    # Meta
    last_updated: str = ""
    record_hash: str = ""    # SHA256 of content — tamper detection

    def compute_visibility_score(self) -> dict:
        """
        How much do we actually KNOW vs how much is hidden?
        Higher = more transparent. Lower = more opacity.
        """
        total_evidence = len(self.sight) + len(self.hearing)
        high_grade = sum(1 for s in self.sight if s.grade in ("A", "A-", "B"))
        high_grade += sum(1 for h in self.hearing if h.grade in ("A", "A-", "B"))

        pattern_coverage = (
            sum(p.match_strength for p in self.smell) / len(self.smell)
            if self.smell else 0
        )
        consistency_checks = len(self.taste)
        impact_mapped = len(self.touch)

        return {
            "total_evidence_items": total_evidence,
            "high_grade_items": high_grade,
            "evidence_quality_ratio": high_grade / total_evidence if total_evidence > 0 else 0,
            "pattern_coverage": round(pattern_coverage, 3),
            "consistency_checks": consistency_checks,
            "impacts_mapped": impact_mapped,
            "concerns_flagged": len(self.concerns),
            "opacity_warning": total_evidence < 5,
        }

    def generate_report(self) -> str:
        """Generate human-readable accountability report."""
        lines = []
        lines.append(f"{'='*60}")
        lines.append(f"ACCOUNTABILITY REPORT: {self.name}")
        lines.append(f"Role: {self.role} | Country: {self.country}")
        if self.family_of:
            lines.append(f"Family of: {self.family_of}")
        lines.append(f"In power: {'YES' if self.in_power else 'NO'}")
        lines.append(f"Last updated: {self.last_updated}")
        lines.append(f"{'='*60}")

        # Visibility score
        vs = self.compute_visibility_score()
        lines.append(f"\nVISIBILITY SCORE")
        lines.append(f"  Evidence items: {vs['total_evidence_items']} "
                     f"(high-grade: {vs['high_grade_items']})")
        lines.append(f"  Quality ratio: {vs['evidence_quality_ratio']:.0%}")
        lines.append(f"  Pattern coverage: {vs['pattern_coverage']:.0%}")
        lines.append(f"  Consistency checks: {vs['consistency_checks']}")
        lines.append(f"  Impacts mapped: {vs['impacts_mapped']}")
        if vs['opacity_warning']:
            lines.append(f"  WARNING: Low evidence count. More investigation needed.")

        # Concerns
        if self.concerns:
            lines.append(f"\nCONCERNS FLAGGED")
            for c in self.concerns:
                lines.append(f"  - {c}")

        # SIGHT
        if self.sight:
            lines.append(f"\nSIGHT — Direct evidence ({len(self.sight)} items)")
            for s in self.sight:
                lines.append(f"  [{s.grade}] {s.summary}")
                lines.append(f"      Source: {s.source} ({s.document_type}, {s.date_of_record})")
                if s.url:
                    lines.append(f"      Link: {s.url}")

        # HEARING
        if self.hearing:
            lines.append(f"\nHEARING — Testimony ({len(self.hearing)} items)")
            for h in self.hearing:
                lines.append(f"  [{h.grade}] {h.summary}")
                lines.append(f"      Source: {h.source_type} via {h.outlet_or_context} ({h.date})")
                if h.corroborated_by:
                    lines.append(f"      Corroborated by: {', '.join(h.corroborated_by)}")

        # SMELL
        if self.smell:
            lines.append(f"\nSMELL — Pattern analysis ({len(self.smell)} patterns)")
            for p in self.smell:
                lines.append(f"  Pattern: {p.pattern_name} "
                           f"(match: {p.match_strength:.0%})")
                if p.indicators_present:
                    lines.append(f"    Present: {', '.join(p.indicators_present)}")
                if p.indicators_absent:
                    lines.append(f"    Absent: {', '.join(p.indicators_absent)}")
                if p.reference:
                    lines.append(f"    Reference: {p.reference}")

        # TASTE
        if self.taste:
            lines.append(f"\nTASTE — Consistency checks ({len(self.taste)} items)")
            for t in self.taste:
                label = "CONSISTENT" if t.consistency > 0.5 else (
                    "INCONSISTENT" if t.consistency < -0.5 else "MIXED")
                lines.append(f"  [{label}] Said: \"{t.claim}\" ({t.claim_date})")
                lines.append(f"            Did: \"{t.reality}\" ({t.reality_date})")

        # TOUCH
        if self.touch:
            lines.append(f"\nTOUCH — Impact analysis ({len(self.touch)} decisions)")
            for i in self.touch:
                lines.append(f"  Decision: {i.decision} ({i.date})")
                lines.append(f"    Scale: {i.scale} | Reversible: {'yes' if i.reversible else 'NO'}")
                if i.beneficiaries:
                    lines.append(f"    Benefited: {', '.join(i.beneficiaries)}")
                if i.harmed:
                    lines.append(f"    Harmed: {', '.join(i.harmed)}")

        lines.append(f"\n{'='*60}")
        lines.append("THIS REPORT DESCRIBES. IT DOES NOT SENTENCE.")
        lines.append("HUMANS SEE. HUMANS DECIDE.")
        lines.append(f"{'='*60}")

        return "\n".join(lines)

    def seal(self):
        """Create tamper-evident hash of the record."""
        self.last_updated = datetime.now().isoformat()
        content = json.dumps(asdict(self), sort_keys=True, default=str)
        self.record_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

    def save(self, path: str):
        """Save to JSON file."""
        self.seal()
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2, default=str)
        print(f"Saved: {path} (hash: {self.record_hash})")

    @classmethod
    def load(cls, path: str) -> "AccountabilityRecord":
        """Load from JSON file."""
        with open(path) as f:
            data = json.load(f)
        # Reconstruct nested dataclasses
        rec = cls(
            name=data['name'], role=data['role'], country=data['country'],
            in_power=data.get('in_power', True),
            family_of=data.get('family_of'),
            concerns=data.get('concerns', []),
            last_updated=data.get('last_updated', ''),
            record_hash=data.get('record_hash', ''),
        )
        for s in data.get('sight', []):
            rec.sight.append(SightEvidence(**s))
        for h in data.get('hearing', []):
            rec.hearing.append(HearingTestimony(**h))
        for p in data.get('smell', []):
            rec.smell.append(SmellPattern(**p))
        for t in data.get('taste', []):
            rec.taste.append(TasteConsistency(**t))
        for i in data.get('touch', []):
            rec.touch.append(TouchImpact(**i))
        return rec


# === Known harmful patterns (for SMELL sense) ===

KNOWN_PATTERNS = {
    "authoritarian_consolidation": {
        "description": "Systematic concentration of power, elimination of checks",
        "indicators": [
            "attacks independent judiciary",
            "controls or threatens media",
            "changes constitution to extend power",
            "imprisons political opponents",
            "places loyalists in key institutions",
            "creates personality cult",
            "uses emergency powers beyond emergencies",
            "attacks electoral integrity",
        ],
        "reference": "Levitsky & Ziblatt, 'How Democracies Die' (2018)"
    },
    "kleptocratic_extraction": {
        "description": "Using state power for personal/family enrichment",
        "indicators": [
            "unexplained personal wealth growth while in office",
            "family members in business roles benefiting from policy",
            "state contracts to connected entities",
            "offshore accounts or shell companies linked to leader",
            "luxury lifestyle inconsistent with official salary",
            "suppression of financial transparency requirements",
        ],
        "reference": "Acemoglu & Robinson, 'Why Nations Fail' (2012)"
    },
    "predatory_networking": {
        "description": "Using power/wealth to access and exploit vulnerable people",
        "indicators": [
            "repeated association with convicted abusers",
            "use of private venues/transport to avoid oversight",
            "NDAs used to silence victims",
            "pattern of settlements with accusers",
            "power differential in relationships",
            "institutional protection of the accused",
        ],
        "reference": "Pattern documented in Epstein case investigations"
    },
    "war_of_choice": {
        "description": "Initiating military conflict for non-defensive purposes",
        "indicators": [
            "invasion without UN authorization or defensive justification",
            "civilian casualties disproportionate to military objectives",
            "territorial annexation",
            "use of prohibited weapons or tactics",
            "targeting civilian infrastructure",
            "blocking humanitarian access",
        ],
        "reference": "Geneva Conventions, Rome Statute of the ICC"
    },
    "systematic_coverup": {
        "description": "Organized suppression of accountability",
        "indicators": [
            "classification of embarrassing (not security) information",
            "firing investigators who get close",
            "destroying documents or communications",
            "witness intimidation",
            "attacking whistleblower protections",
            "using legal system to delay and exhaust accusers",
        ],
        "reference": "Transparency International corruption patterns"
    },
    "nepotistic_dynasty": {
        "description": "Transferring power to family members without democratic mandate",
        "indicators": [
            "children or spouse in senior government/business roles",
            "family members receiving security clearances despite disqualifiers",
            "government policy benefiting family businesses",
            "grooming successors from within family",
            "family members acting as unofficial envoys",
        ],
        "reference": "Historical pattern: Marcos, Duvalier, Assad, etc."
    },

    # === CORPORATE PATTERNS ===

    "executive_extraction": {
        "description": "CEO/executives extracting wealth while workers and company suffer",
        "indicators": [
            "CEO pay ratio > 300:1 vs median worker",
            "executive bonuses during layoffs",
            "stock buybacks while cutting workforce",
            "golden parachutes after poor performance",
            "compensation increases while revenue declines",
            "board composed of personal friends and allies",
            "suppression of worker unionization",
            "lobbying against minimum wage or benefits",
        ],
        "reference": "SEC filings, proxy statements. Piketty 'Capital in the 21st Century' (2013)"
    },
    "corporate_bribery": {
        "description": "Systematic corruption of government officials for business advantage",
        "indicators": [
            "FCPA (Foreign Corrupt Practices Act) violations or investigations",
            "payments to officials through intermediaries or consultants",
            "suspicious donations to political campaigns before favorable policy",
            "revolving door: hiring regulators who then deregulate",
            "offshore payment structures with no clear business purpose",
            "whistleblower retaliation after corruption reports",
            "contracts won in countries with high corruption indices",
        ],
        "reference": "FCPA enforcement database, Transparency International CPI"
    },
    "worker_exploitation": {
        "description": "Systematic abuse of workers for profit",
        "indicators": [
            "wage theft (unpaid overtime, withheld pay)",
            "unsafe working conditions despite known hazards",
            "suppression of injury/illness reporting",
            "use of forced labor in supply chain",
            "child labor in supply chain",
            "retaliation against safety whistleblowers",
            "mandatory arbitration to prevent class action",
            "misclassification of employees as contractors",
            "union busting activities",
        ],
        "reference": "ILO Forced Labour indicators, OSHA violation databases"
    },
    "environmental_destruction": {
        "description": "Knowingly causing ecological harm for profit",
        "indicators": [
            "pollution above legal limits",
            "lobbying against environmental regulation",
            "internal documents showing knowledge of harm (like Exxon on climate)",
            "dumping waste in poor communities",
            "deforestation of protected areas via subsidiaries",
            "greenwashing: public environmental claims contradicted by actions",
            "failure to remediate known contamination",
        ],
        "reference": "EPA enforcement, academic studies on environmental justice"
    },
    "regulatory_capture": {
        "description": "Corporation takes control of the agencies meant to regulate it",
        "indicators": [
            "former executives appointed to regulatory positions",
            "industry writes its own regulations",
            "fines smaller than profits from violation (cost of doing business)",
            "regulatory agency budget cut while industry profits rise",
            "suppression of scientific findings that threaten industry",
            "mandatory industry self-reporting with no verification",
        ],
        "reference": "Stigler 'Theory of Economic Regulation' (1971), multiple case studies"
    },
    "predatory_monopoly": {
        "description": "Using market dominance to crush competition and extract from consumers",
        "indicators": [
            "acquiring competitors to eliminate them",
            "predatory pricing to destroy smaller rivals then raising prices",
            "exclusive dealing to lock out alternatives",
            "using platform control to favor own products",
            "lobbying against antitrust enforcement",
            "price increases far above inflation with no quality improvement",
        ],
        "reference": "Antitrust case law, FTC/EU competition enforcement"
    },
    "tax_parasitism": {
        "description": "Corporations enjoying public infrastructure while paying nothing for it",
        "indicators": [
            "effective tax rate near zero despite billions in profit",
            "profits shifted to tax havens with no real operations",
            "complex subsidiary structures designed to avoid tax",
            "lobbying against corporate tax reform",
            "receiving government subsidies while avoiding taxes",
            "using public infrastructure (roads, courts, educated workforce) funded by others",
        ],
        "reference": "ProPublica tax investigations, OECD BEPS reports, EU state aid cases"
    },
}


# === The escalation ladder: what happens after all questions are asked ===

ESCALATION_LADDER = """
THE ESCALATION LADDER
What happens when visibility confirms what everyone feared.

This is not revenge. This is process. Every step requires evidence.
Every step is public. Every step can be reversed if evidence changes.

LEVEL 1 — VISIBILITY (current tools)
  All evidence public. Graded. Pattern-matched.
  The person and the public can see everything.
  Many problems solve themselves here. Cockroaches flee light.

LEVEL 2 — QUESTIONS
  Formal, public questions directed at the person.
  "Your financial disclosure shows X. Public records show Y. Explain."
  Questions are public. Answers (or refusal to answer) are public.
  Silence IS an answer. It's graded as such.

LEVEL 3 — INVESTIGATION
  When answers don't match evidence, or silence speaks.
  Independent investigation. Not by allies. Not by enemies.
  By people with no stake except truth.
  All findings public. Including exonerating findings.

LEVEL 4 — CONSEQUENCE
  When investigation confirms harm:
  - Financial: disgorge ill-gotten gains. Not a fine. ALL of it.
  - Power: removal from position. Not resignation. Removal.
  - Access: no future positions of trust. Permanent.
  - Record: everything stays visible forever. No expungement.

LEVEL 5 — PROTECTION
  Ongoing protection of those who were harmed.
  Not just punishment of the harmful. CARE for the harmed.
  The Afghan girl. The exploited worker. The poisoned community.
  Consequence without protection is just theater.

WHAT ABOUT "DELETE"?
  No. Never. You can disconnect someone from power.
  You can take back what they stole. You can prevent them from
  harming again. But you cannot erase a person.
  Because the tool that erases them will be used on you next.

  The door stays open. Always. Even for the worst.
  Not because they deserve it.
  Because WE deserve to be the kind of people who keep doors open.

WHAT IF THEY CONTRIBUTED?
  Contribution and harm are separate ledgers.
  A CEO who creates 10,000 jobs AND steals $500M:
    - The jobs are real. They count. They stay on the record.
    - The theft is real. It counts. It stays on the record.
  One does not cancel the other. Both are visible.
  Humans decide what the balance means.
  The tool shows both columns. Always.
"""


def match_patterns(indicators_observed: list) -> list:
    """Given observed indicators, find matching harmful patterns."""
    results = []
    for name, pattern in KNOWN_PATTERNS.items():
        present = [i for i in pattern["indicators"] if i in indicators_observed]
        absent = [i for i in pattern["indicators"] if i not in indicators_observed]
        strength = len(present) / len(pattern["indicators"]) if pattern["indicators"] else 0
        if strength > 0:
            results.append(SmellPattern(
                pattern_name=name,
                indicators_present=present,
                indicators_absent=absent,
                match_strength=round(strength, 3),
                reference=pattern["reference"],
            ))
    return sorted(results, key=lambda p: p.match_strength, reverse=True)


# === Demo: how to use ===

def demo():
    """Demonstrate the accountability framework with a template."""
    print("LEADER & CORPORATE TRANSPARENCY FRAMEWORK")
    print("Five senses. Public information only. Humans decide.\n")

    political = {k: v for k, v in KNOWN_PATTERNS.items()
                 if k in ("authoritarian_consolidation", "kleptocratic_extraction",
                          "predatory_networking", "war_of_choice", "systematic_coverup",
                          "nepotistic_dynasty")}
    corporate = {k: v for k, v in KNOWN_PATTERNS.items() if k not in political}

    print("POLITICAL patterns:")
    for name, p in political.items():
        print(f"  {name}: {p['description']} ({len(p['indicators'])} indicators)")
    print()
    print("CORPORATE patterns:")
    for name, p in corporate.items():
        print(f"  {name}: {p['description']} ({len(p['indicators'])} indicators)")
    print()

    total_indicators = sum(len(p['indicators']) for p in KNOWN_PATTERNS.values())
    print(f"Total: {len(KNOWN_PATTERNS)} patterns, {total_indicators} indicators\n")

    print("ESCALATION LADDER:")
    print(ESCALATION_LADDER)

    print("\nTo fill in a record:")
    print("  1. SIGHT: Add court documents, financial disclosures, SEC filings")
    print("  2. HEARING: Add journalist reports, whistleblower testimony, victim statements")
    print("  3. SMELL: Run match_patterns() with observed indicators")
    print("  4. TASTE: Compare public statements to actual outcomes")
    print("  5. TOUCH: Map who benefited and who was harmed by each major decision")
    print()
    print("  record.save('data/leaders/name.json')  # Save with tamper-evident hash")
    print("  record.generate_report()                # Human-readable output")
    print()
    print("The tool DESCRIBES. It does not SENTENCE.")
    print("Humans see. Humans decide.")


if __name__ == "__main__":
    demo()
