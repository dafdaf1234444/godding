#!/usr/bin/env python3
"""
consequence_sim.py — Show people what their collective choices actually mean.

Before a society makes a big choice, this tool asks:
  "If you do this, here is what happened every other time someone did it."

Not prediction. HISTORY. Pattern-matched precedent.

The collective can still choose self-destruction. That's their right.
But they must see the footage first.

Connects to: leader_transparency.py (SMELL sense), justice.html (PHIL-29)
"""

import json
from dataclasses import dataclass, field
from typing import Optional


# === Historical precedents ===
# Every big choice has been made before. The outcomes are known.

PRECEDENT_DATABASE = {

    "invade_neighbor": {
        "choice": "Invade a neighboring country",
        "sounds_like": [
            "Protect our people across the border",
            "Restore historical territory",
            "Preemptive defense",
            "Special military operation",
        ],
        "precedents": [
            {
                "who": "Germany invades Poland, 1939",
                "promised": "Living space, national glory, quick victory",
                "got": "50-80 million dead, country split in two, 40 years of occupation",
                "time_to_consequence": "6 years",
                "reversible": False,
            },
            {
                "who": "Iraq invades Kuwait, 1990",
                "promised": "Reclaim historical province, oil wealth",
                "got": "International coalition, military defeat, sanctions, eventual regime destruction",
                "time_to_consequence": "13 years to full consequence",
                "reversible": False,
            },
            {
                "who": "Russia invades Ukraine, 2022",
                "promised": "3-day operation, denazification, NATO buffer",
                "got": "Hundreds of thousands of casualties, economic isolation, NATO expansion, ongoing war",
                "time_to_consequence": "Ongoing",
                "reversible": False,
            },
        ],
        "survival_rate": "0% of aggressors achieved stated goals without catastrophic blowback",
        "average_death_toll": "Millions",
        "who_suffers_most": "Young soldiers and civilians on both sides. Not the leaders who ordered it.",
    },

    "elect_authoritarian": {
        "choice": "Give one person unchecked power",
        "sounds_like": [
            "Strong leader who gets things done",
            "Only I can fix it",
            "The system is broken, we need someone who breaks the rules",
            "Emergency powers, just temporary",
        ],
        "precedents": [
            {
                "who": "Weimar Germany elects Hitler, 1933",
                "promised": "Economic recovery, national pride, order",
                "got": "Holocaust, world war, total destruction, 12 years of horror",
                "time_to_consequence": "6 years to war, 12 to total collapse",
                "reversible": False,
            },
            {
                "who": "Venezuela elects Chavez, 1998",
                "promised": "Power to the people, oil wealth for all",
                "got": "Economic collapse, mass emigration, dictatorship, starvation",
                "time_to_consequence": "15 years to full collapse",
                "reversible": "Technically, but millions already displaced",
            },
            {
                "who": "Philippines elects Marcos, 1965",
                "promised": "Modernization, law and order",
                "got": "20 years of martial law, $10B stolen, thousands killed",
                "time_to_consequence": "7 years to martial law",
                "reversible": "After 20 years and a revolution",
            },
            {
                "who": "Turkey — Erdogan consolidates power, 2017",
                "promised": "Stability, economic growth, national strength",
                "got": "Currency collapse, jailed journalists, purged institutions, brain drain",
                "time_to_consequence": "Gradual over 10 years",
                "reversible": "Institutions damaged but elections still occurring",
            },
        ],
        "survival_rate": "0% ended well for the general population",
        "average_death_toll": "Thousands to millions",
        "who_suffers_most": "Minorities first. Then opponents. Then everyone except the inner circle.",
    },

    "ignore_corruption": {
        "choice": "Tolerate corruption because the economy is good",
        "sounds_like": [
            "They steal but they build",
            "Every politician is corrupt, at least this one is ours",
            "Don't rock the boat",
            "The economy is growing, who cares about some bribes",
        ],
        "precedents": [
            {
                "who": "Brazil under systemic corruption, 2003-2016",
                "promised": "Growth, infrastructure, emerging power status",
                "got": "Petrobras scandal, $2B+ stolen, deep recession, political crisis",
                "time_to_consequence": "13 years",
                "reversible": "Partially, through investigations (Lava Jato)",
            },
            {
                "who": "South Africa under Zuma, 2009-2018",
                "promised": "Continued Mandela legacy, transformation",
                "got": "State capture, Gupta family looting, institutional rot, economic stagnation",
                "time_to_consequence": "9 years",
                "reversible": "Slowly, with enormous institutional damage",
            },
        ],
        "survival_rate": "Corruption always costs more than it steals. The bill comes later.",
        "average_death_toll": "Indirect: hospital failures, infrastructure collapse, poverty",
        "who_suffers_most": "The poorest. Corruption is a tax on people who can't afford accountants.",
    },

    "suppress_press": {
        "choice": "Let the government control what media can say",
        "sounds_like": [
            "Fake news is dangerous",
            "Media is the enemy of the people",
            "We need responsible journalism, not lies",
            "National security requires some censorship",
        ],
        "precedents": [
            {
                "who": "Every authoritarian regime ever",
                "promised": "Order, truth, stability",
                "got": "Invisible corruption, surprise disasters, public ignorance until collapse",
                "time_to_consequence": "Immediate (information dies) to years (consequences emerge)",
                "reversible": "Yes, but lost information is lost forever",
            },
        ],
        "survival_rate": "No free society has ever been maintained without free press. Zero.",
        "average_death_toll": "Indirect but massive: Chernobyl was a press freedom failure",
        "who_suffers_most": "Everyone. Including the leaders. They lose the ability to know what's actually happening.",
    },

    "scapegoat_minority": {
        "choice": "Blame a minority group for collective problems",
        "sounds_like": [
            "They're taking our jobs",
            "They're not really one of us",
            "They're the reason things are bad",
            "If we just remove them, everything will be fine",
        ],
        "precedents": [
            {
                "who": "Every genocide in history",
                "promised": "Purity, unity, prosperity once 'they' are gone",
                "got": "Mass murder, international isolation, generational trauma, economic devastation",
                "time_to_consequence": "Months to years",
                "reversible": False,
            },
        ],
        "survival_rate": "0% improved the country. 100% created lasting shame.",
        "average_death_toll": "Thousands to millions",
        "who_suffers_most": "The scapegoated group first. Then everyone, because the real problems were never addressed.",
    },

    "abandon_education": {
        "choice": "Defund or politicize education",
        "sounds_like": [
            "Schools are indoctrinating our children",
            "We need practical skills, not theory",
            "Cut spending, education is too expensive",
            "Parents should decide what children learn",
        ],
        "precedents": [
            {
                "who": "Cambodia under Khmer Rouge, 1975-1979",
                "promised": "Pure agrarian society, no need for intellectuals",
                "got": "Genocide of educated class, country set back decades",
                "time_to_consequence": "Immediate",
                "reversible": "Dead people don't come back",
            },
            {
                "who": "Various — any country that defunds education",
                "promised": "Lower taxes, more freedom",
                "got": "Workforce decline in 10-15 years, innovation gap, brain drain",
                "time_to_consequence": "10-20 years (delayed, which is why it's so dangerous)",
                "reversible": "Yes, but a lost generation is lost",
            },
        ],
        "survival_rate": "No country has ever prospered long-term by reducing education.",
        "average_death_toll": "Indirect but real: ignorance kills through bad decisions at scale",
        "who_suffers_most": "Children. They didn't choose. They inherit the world we broke.",
    },
}


# === Sanctuary protocol ===

@dataclass
class SanctuaryPlan:
    """
    For those who see the destruction coming and don't consent.

    You can't stop a collective from choosing badly.
    You CAN prepare to survive it.
    """
    person: str
    loved_ones: list = field(default_factory=list)

    # Information preservation
    knowledge_backup: list = field(default_factory=list)  # What to preserve
    evidence_copies: int = 0   # How many copies of accountability records

    # Physical safety
    exit_routes: list = field(default_factory=list)   # Where to go if it gets bad
    timeline_triggers: list = field(default_factory=list)  # When to act

    # Community
    trusted_network: list = field(default_factory=list)  # People who also see it
    communication_plan: str = ""  # How to stay in contact if systems fail

    # Seeds
    skills_preserved: list = field(default_factory=list)  # What you can rebuild from
    resources_diversified: bool = False  # Not all eggs in one basket

    def generate_plan(self) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("SANCTUARY PLAN")
        lines.append(f"For: {self.person}")
        if self.loved_ones:
            lines.append(f"Protecting: {', '.join(self.loved_ones)}")
        lines.append("=" * 60)

        lines.append("\n--- EARLY WARNING TRIGGERS ---")
        lines.append("Act when you see these, not after:")
        triggers = self.timeline_triggers or [
            "Independent media shut down or taken over",
            "Judiciary packed or bypassed",
            "Political opponents jailed on vague charges",
            "Emergency powers declared and not rescinded",
            "Minority group officially scapegoated",
            "Currency controls or capital flight restrictions",
            "Travel restrictions for citizens (not visitors)",
            "Military deployed domestically against protesters",
        ]
        for i, t in enumerate(triggers, 1):
            lines.append(f"  {i}. {t}")
        lines.append("\nRule: If 3+ triggers fire, MOVE. Don't wait for 8.")

        lines.append("\n--- INFORMATION PRESERVATION ---")
        lines.append("Truth is the first casualty. Preserve it:")
        lines.append("  - Keep copies of accountability records offline")
        lines.append("  - Download, don't just bookmark")
        lines.append("  - Multiple formats: PDF, JSON, printed paper")
        lines.append("  - Multiple locations: USB, cloud, trusted person abroad")
        lines.append(f"  - Evidence copies: {self.evidence_copies or 'SET THIS'}")

        lines.append("\n--- PHYSICAL SAFETY ---")
        if self.exit_routes:
            lines.append("Exit routes (in order of preference):")
            for r in self.exit_routes:
                lines.append(f"  - {r}")
        else:
            lines.append("Exit routes: NOT YET PLANNED — do this now.")
            lines.append("  Consider: nearest safe country, visa requirements,")
            lines.append("  savings in portable form, documents ready")

        lines.append("\n--- COMMUNITY ---")
        lines.append("You survive in groups, not alone:")
        if self.trusted_network:
            lines.append(f"  Trusted network: {len(self.trusted_network)} people")
        else:
            lines.append("  Trusted network: BUILD THIS — 5-15 people who also see it")
        lines.append("  Communication if internet cut: agree on physical meeting point")
        lines.append("  Skill distribution: not everyone needs every skill,")
        lines.append("  but the group needs: medical, technical, legal, practical")

        lines.append("\n--- SEEDS ---")
        lines.append("What you can rebuild from if everything else is lost:")
        lines.append("  - Knowledge: the tools, the records, the code")
        lines.append("  - Skills: what you and your people actually know how to do")
        lines.append("  - Relationships: trust networks that survive displacement")
        lines.append("  - Values: what you refuse to abandon no matter what")

        lines.append("\n" + "=" * 60)
        lines.append("This plan is not paranoia. It is what every refugee")
        lines.append("wishes they had done six months before they had to run.")
        lines.append("The ones who planned survived. The ones who didn't, didn't.")
        lines.append("=" * 60)

        return "\n".join(lines)


# === Consequence report ===

def show_consequences(choice_key: str) -> str:
    """Show what happened every other time this choice was made."""
    if choice_key not in PRECEDENT_DATABASE:
        available = ", ".join(PRECEDENT_DATABASE.keys())
        return f"Unknown choice. Available: {available}"

    entry = PRECEDENT_DATABASE[choice_key]
    lines = []
    lines.append("=" * 60)
    lines.append(f"CONSEQUENCE REPORT")
    lines.append(f"Choice: {entry['choice']}")
    lines.append("=" * 60)

    lines.append(f"\nWhat it sounds like when they sell it to you:")
    for s in entry['sounds_like']:
        lines.append(f'  "{s}"')

    lines.append(f"\nWhat happened every other time ({len(entry['precedents'])} cases):")
    for i, p in enumerate(entry['precedents'], 1):
        lines.append(f"\n  Case {i}: {p['who']}")
        lines.append(f"    Promised: {p['promised']}")
        lines.append(f"    Got:      {p['got']}")
        lines.append(f"    Time to consequence: {p['time_to_consequence']}")
        lines.append(f"    Reversible: {p['reversible']}")

    lines.append(f"\n--- BOTTOM LINE ---")
    lines.append(f"  Success rate: {entry['survival_rate']}")
    lines.append(f"  Typical death toll: {entry['average_death_toll']}")
    lines.append(f"  Who suffers most: {entry['who_suffers_most']}")

    lines.append(f"\n{'='*60}")
    lines.append("You can still choose this. It's your right.")
    lines.append("But now you've seen the footage.")
    lines.append(f"{'='*60}")

    return "\n".join(lines)


def list_choices():
    """List all documented choices and their one-line summaries."""
    print("Documented collective choices and their consequences:\n")
    for key, entry in PRECEDENT_DATABASE.items():
        print(f"  {key:25s} — {entry['choice']}")
        print(f"  {'':25s}   Success rate: {entry['survival_rate'][:60]}")
        print()


# === Main ===

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("CONSEQUENCE SIMULATOR")
        print("Show people what their choices actually mean.\n")
        list_choices()
        print("\nUsage:")
        print("  python3 tools/consequence_sim.py <choice_key>")
        print("  python3 tools/consequence_sim.py elect_authoritarian")
        print("  python3 tools/consequence_sim.py sanctuary")
        print("\nThe collective can choose to destroy itself.")
        print("But they must see the footage first.")
    elif sys.argv[1] == "sanctuary":
        plan = SanctuaryPlan(
            person="[YOUR NAME]",
            loved_ones=["[LIST YOUR PEOPLE]"],
        )
        print(plan.generate_plan())
    elif sys.argv[1] == "all":
        for key in PRECEDENT_DATABASE:
            print(show_consequences(key))
            print("\n")
    else:
        print(show_consequences(sys.argv[1]))
