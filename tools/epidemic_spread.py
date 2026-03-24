#!/usr/bin/env python3
"""epidemic_spread.py — Dual R₀ model for knowledge contagion.

Computes epidemic-style metrics on the lesson citation graph:
  R_bad:  effective reproduction number for falsified knowledge
  R_good: diffusion potential for high-value knowledge
  Immunity: correction rate acting as herd-immunity proxy
  Vaccination: proactive correction before spread (early containment)

Externalizable: same framework applies to rumor spread, policy diffusion,
misinformation containment, beneficial practice adoption.

Usage:
    python3 tools/epidemic_spread.py              # full report
    python3 tools/epidemic_spread.py --json       # machine-readable
    python3 tools/epidemic_spread.py --external   # show externalization template
"""

import argparse, glob, json, math, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LESSONS = ROOT / "memory" / "lessons"

# S537: integrate correction_propagation's bidirectional falsification detector
try:
    from tools.correction_propagation import (
        _parse_lessons as _cp_parse,
        _detect_falsified_lessons as _cp_detect,
    )
    _HAS_CP = True
except ImportError:
    try:
        sys.path.insert(0, str(ROOT))
        from tools.correction_propagation import (
            _parse_lessons as _cp_parse,
            _detect_falsified_lessons as _cp_detect,
        )
        _HAS_CP = True
    except ImportError:
        _HAS_CP = False


def load_graph():
    """Build citation graph, extract metadata."""
    files = sorted(LESSONS.glob("L-*.md"))
    graph = {}       # lid -> [cited lids]
    reverse = {}     # lid -> [citing lids]
    falsified = set()   # truly harmful (RETRACTED)
    obsolete = set()    # superseded/archived (not harmful, just outdated)
    sharpe = {}
    sessions = {}
    domains = {}

    for f in files:
        lid = f.stem
        text = f.read_text(errors="replace")[:2000]
        header = text[:800]

        # Citations
        cites = [f"L-{c}" for c in re.findall(r"L-(\d+)", text) if f"L-{c}" != lid]
        graph[lid] = list(set(cites))

        # Reverse edges
        for c in graph[lid]:
            reverse.setdefault(c, []).append(lid)

        # Three-tier classification (L-1550, S537 operational filter):
        # Tier 1: RETRACTED = truly harmful (R_bad applies)
        # Tier 2: Genuinely falsified = contextual evidence of falsification
        #         (claim proved wrong, but not formally retracted)
        # Tier 3: SUPERSEDED/ARCHIVED = obsolete (successor exists, maintenance debt)
        # L-1544: classification error dominates all downstream metrics.
        first_line = text.split("\n")[0] if text else ""
        is_retracted = "[RETRACTED]" in header
        is_superseded = (
            "<!-- SUPERSEDED" in text[:200]
            or bool(re.search(r"SUPERSEDED\s+(?:by|BY)\s+L-\d+", first_line))
            or "[SUPERSEDED" in first_line
        )
        is_archived = "<!-- ARCHIVED" in text[:200]
        # Tier 2 is handled post-loop by correction_propagation's bidirectional detector
        is_contextual_falsified = False
        if is_retracted:
            falsified.add(lid)  # Tier 1: truly harmful — R_bad applies
        elif is_contextual_falsified:
            falsified.add(lid)  # Tier 2: genuinely falsified — R_bad applies
        if is_superseded or is_archived:
            obsolete.add(lid)   # Tier 3: maintenance debt, not epidemic contamination

        m = re.search(r"Sharpe:\s*(\d+)", header)
        if m:
            sharpe[lid] = int(m.group(1))
        m = re.search(r"Session:\s*S(\d+)", header)
        if m:
            sessions[lid] = int(m.group(1))
        m = re.search(r"Domain:\s*(\S+)", header)
        if m:
            domains[lid] = m.group(1)

    # Tier 2 (S537): use correction_propagation's bidirectional detector for
    # genuinely falsified lessons. This catches lessons like L-025 that are
    # falsified by citation-context evidence (other lessons say "L-025 FALSIFIED").
    if _HAS_CP:
        try:
            cp_lessons = _cp_parse()
            cp_falsified = _cp_detect(cp_lessons)
            for fid in cp_falsified:
                if fid not in obsolete:  # don't promote obsolete to falsified
                    falsified.add(fid)
        except Exception:
            pass  # graceful degradation if CP fails

    return graph, reverse, falsified, obsolete, sharpe, sessions, domains


def _is_operational_citation(citer_text, falsified_lid):
    """Classify whether a citation is operational (builds on claim) vs historical (discusses it).

    S537 finding: operational/historical distinction is the binding classifier.
    Historical refs (discussing falsification) are not infections.
    Operational refs (using as premise) are genuine infections.
    """
    ref_positions = [m.start() for m in re.finditer(re.escape(falsified_lid), citer_text)]
    for pos in ref_positions:
        ctx = citer_text[max(0, pos - 200):min(len(citer_text), pos + 200)]
        # Operational: uses the claim as a premise
        if re.search(
            r"(?:as\s+shown|per|following|based\s+on|using|applies|confirms?|supports?)"
            r"\s+" + re.escape(falsified_lid),
            ctx, re.IGNORECASE
        ):
            # Check override: historical context nearby
            if not re.search(
                r"(?:see\s+also|cf\.|related|compare|history|background|era|legacy)"
                r"\s+.*?" + re.escape(falsified_lid),
                ctx, re.IGNORECASE
            ):
                return True
    return False


def compute_r_bad(reverse, falsified, graph=None):
    """Compute R_bad: effective reproduction of falsified knowledge.

    S537 three-tier model:
    - R_bad counts only OPERATIONAL citations (premise-building)
    - Historical citations (reference-only) are not infections
    - This prevents classification artifacts from inflating R_bad

    Epidemic analog: secondary infections from an infected individual.
    """
    # Load citer texts for operational/historical classification
    citer_texts = {}
    if graph:
        for lid in falsified:
            for citer in reverse.get(lid, []):
                if citer not in citer_texts:
                    citer_path = LESSONS / f"{citer}.md"
                    if citer_path.exists():
                        citer_texts[citer] = citer_path.read_text(errors="replace")[:2000]

    results = []
    total_operational = 0
    total_historical = 0
    for lid in falsified:
        citers = reverse.get(lid, [])
        live_citers = [c for c in citers if c not in falsified]
        total = len(citers)
        live = len(live_citers)

        # S537: split live citers into operational vs historical
        operational_citers = []
        historical_citers = []
        for c in live_citers:
            if c in citer_texts and _is_operational_citation(citer_texts[c], lid):
                operational_citers.append(c)
            else:
                historical_citers.append(c)

        operational = len(operational_citers)
        total_operational += operational
        total_historical += len(historical_citers)

        correction_rate = 1 - (live / total) if total > 0 else 1.0
        results.append({
            "lesson": lid,
            "total_citers": total,
            "live_citers": live,
            "operational_citers": operational,
            "historical_citers": len(historical_citers),
            "correction_rate": correction_rate,
            "r_effective": live,
            "r_operational": operational,
        })
    results.sort(key=lambda x: -x["r_effective"])

    # Population-level R_bad
    total_live = sum(r["live_citers"] for r in results)
    total_falsified = len(results) or 1
    r_bad_mean = total_live / total_falsified

    # S537: R_bad_operational counts only premise-building citations
    r_bad_operational = total_operational / total_falsified if total_falsified else 0

    # Herd immunity threshold: 1 - 1/R₀
    # If correction_rate > HIT, epidemic is controlled
    hit = 1 - 1 / r_bad_mean if r_bad_mean > 1 else 0
    actual_correction = (
        sum(r["correction_rate"] for r in results) / len(results) if results else 1.0
    )

    # Determine status using operational R_bad (more accurate)
    immune_status = "CONTROLLED" if r_bad_operational < 1.0 else (
        "CONTROLLED" if actual_correction > hit else "SUPERCRITICAL"
    )

    return {
        "r_bad_mean": round(r_bad_mean, 2),
        "r_bad_operational": round(r_bad_operational, 2),
        "total_operational_infections": total_operational,
        "total_historical_refs": total_historical,
        "herd_immunity_threshold": round(hit, 3),
        "actual_correction_rate": round(actual_correction, 3),
        "immune_status": immune_status,
        "falsified_count": len(falsified),
        "super_spreaders": results[:5],  # top 5 by live citers
        "all": results,
    }


def compute_r_good(graph, reverse, falsified, sharpe, sessions):
    """Compute R_good: diffusion potential of beneficial knowledge.

    R_good for a beneficial node = 2-hop reach / direct citations.
    High R_good = knowledge spreads through the network (viral diffusion).
    Low R_good = knowledge is trapped in a local cluster (diffusion failure).

    Epidemic analog: R₀ for a beneficial "infection" (practice adoption).
    """
    results = []
    for lid in graph:
        if lid in falsified:
            continue
        if sharpe.get(lid, 0) < 7:
            continue
        in_deg = len(reverse.get(lid, []))
        if in_deg < 3:
            continue

        # 2-hop reach
        hop1 = set(graph.get(lid, []))
        hop2 = set()
        for h in hop1:
            hop2.update(graph.get(h, []))
        reach = len(hop1 | hop2 - {lid})

        # Diffusion ratio: how much does reach amplify beyond direct citations?
        diffusion = reach / in_deg if in_deg > 0 else 0

        # Age (sessions since creation) — older lessons had more time to spread
        age = sessions.get(lid, 0)

        results.append({
            "lesson": lid,
            "in_degree": in_deg,
            "sharpe": sharpe.get(lid, 0),
            "two_hop_reach": reach,
            "diffusion_ratio": round(diffusion, 2),
            "session": age,
        })

    results.sort(key=lambda x: -x["in_degree"])

    # Population-level metrics
    if results:
        mean_diffusion = sum(r["diffusion_ratio"] for r in results) / len(results)
        # Trapped knowledge: high sharpe, high in-degree, but low diffusion
        trapped = [r for r in results if r["diffusion_ratio"] < 0.5 and r["in_degree"] >= 10]
        # Viral knowledge: high diffusion ratio
        viral = sorted(results, key=lambda x: -x["diffusion_ratio"])[:5]
    else:
        mean_diffusion = 0
        trapped = []
        viral = []

    return {
        "r_good_mean_diffusion": round(mean_diffusion, 2),
        "beneficial_count": len(results),
        "trapped_knowledge": trapped[:5],
        "viral_knowledge": viral,
        "critical_mass_threshold": 0.5,  # diffusion_ratio > 0.5 = self-sustaining
        "above_threshold": len([r for r in results if r["diffusion_ratio"] >= 0.5]),
        "below_threshold": len([r for r in results if r["diffusion_ratio"] < 0.5]),
    }


def compute_compartments(graph, reverse, falsified, sharpe):
    """SIR-style compartment model for knowledge health.

    S (Susceptible): lessons that cite no falsified source but could
    I (Infected):    lessons that cite a falsified source (uncorrected)
    R (Recovered):   falsified lessons that have been corrected/superseded
    V (Vaccinated):  high-sharpe lessons with no falsified citations

    Epidemic analog: classic SIR + vaccination compartment.
    """
    all_lessons = set(graph.keys())
    infected = set()
    for lid in falsified:
        for citer in reverse.get(lid, []):
            if citer not in falsified:
                infected.add(citer)

    vaccinated = {lid for lid in all_lessons
                  if sharpe.get(lid, 0) >= 8
                  and lid not in falsified
                  and lid not in infected}

    recovered = falsified  # falsified lessons are "resolved" — known bad
    susceptible = all_lessons - infected - recovered - vaccinated

    n = len(all_lessons) or 1
    return {
        "S": len(susceptible),
        "I": len(infected),
        "R": len(recovered),
        "V": len(vaccinated),
        "total": n,
        "infection_rate": round(len(infected) / n, 3),
        "vaccination_rate": round(len(vaccinated) / n, 3),
        "immunity": round((len(recovered) + len(vaccinated)) / n, 3),
    }


def externalization_template():
    """Generic dual-R₀ framework for any knowledge/information system."""
    return {
        "framework": "Dual-R₀ Epidemic Spread Model",
        "purpose": "Distinguish harmful contamination from beneficial diffusion in any knowledge system",
        "applications": [
            {
                "domain": "Social media / misinformation",
                "R_bad": "Uncorrected shares of debunked claims",
                "R_good": "Shares of corrections or beneficial content",
                "immunity": "Fact-check coverage rate",
                "vaccination": "Pre-bunking (inoculation before exposure)",
            },
            {
                "domain": "Software supply chain",
                "R_bad": "Downstream dependents of vulnerable package",
                "R_good": "Adoption rate of security patches",
                "immunity": "Automated dependency scanning coverage",
                "vaccination": "Pinned versions + automated update policies",
            },
            {
                "domain": "Organizational knowledge management",
                "R_bad": "Documents citing retracted/obsolete procedures",
                "R_good": "Cross-team adoption of best practices",
                "immunity": "Document review cycle compliance",
                "vaccination": "Mandatory sunset dates on procedural docs",
            },
            {
                "domain": "Scientific literature",
                "R_bad": "Citations of retracted papers by non-retracted papers",
                "R_good": "Citation cascade of replication-confirmed findings",
                "immunity": "Retraction-notice propagation to citing authors",
                "vaccination": "Pre-registration + registered reports",
            },
        ],
        "key_thresholds": {
            "herd_immunity": "correction_rate > 1 - 1/R_bad_mean",
            "critical_mass": "diffusion_ratio > 0.5 for beneficial content",
            "super_spreader": "single source with live_citers > 10x mean",
        },
        "insight": (
            "The same epidemic math (R₀, herd immunity, SIR compartments) "
            "applies to knowledge systems. The critical distinction: harmful spread "
            "requires suppression (lower R_bad via correction), while beneficial spread "
            "requires amplification (raise R_good via deliberate seeding). Most systems "
            "focus on one side; dual-R₀ addresses both simultaneously."
        ),
    }


def main():
    ap = argparse.ArgumentParser(description="Dual R₀ epidemic spread model")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--external", action="store_true", help="Show externalization template")
    args = ap.parse_args()

    if args.external:
        t = externalization_template()
        if args.json:
            print(json.dumps(t, indent=2))
        else:
            print(f"\n=== {t['framework']} ===")
            print(f"\n{t['insight']}\n")
            for app in t["applications"]:
                print(f"  [{app['domain']}]")
                print(f"    R_bad:        {app['R_bad']}")
                print(f"    R_good:       {app['R_good']}")
                print(f"    Immunity:     {app['immunity']}")
                print(f"    Vaccination:  {app['vaccination']}")
                print()
            print("  Key thresholds:")
            for k, v in t["key_thresholds"].items():
                print(f"    {k}: {v}")
        return

    graph, reverse, falsified, obsolete, sharpe, sessions, domains = load_graph()

    bad = compute_r_bad(reverse, falsified, graph=graph)
    good = compute_r_good(graph, reverse, falsified, sharpe, sessions)
    sir = compute_compartments(graph, reverse, falsified, sharpe)

    report = {
        "harmful_spread": {
            "R_bad_mean": bad["r_bad_mean"],
            "R_bad_operational": bad["r_bad_operational"],
            "operational_infections": bad["total_operational_infections"],
            "historical_refs": bad["total_historical_refs"],
            "herd_immunity_threshold": bad["herd_immunity_threshold"],
            "actual_correction_rate": bad["actual_correction_rate"],
            "immune_status": bad["immune_status"],
            "falsified_count": bad["falsified_count"],
            "super_spreaders": bad["super_spreaders"][:3],
        },
        "beneficial_spread": {
            "R_good_mean_diffusion": good["r_good_mean_diffusion"],
            "beneficial_count": good["beneficial_count"],
            "above_critical_mass": good["above_threshold"],
            "below_critical_mass": good["below_threshold"],
            "trapped_knowledge": good["trapped_knowledge"][:3],
            "viral_knowledge": good["viral_knowledge"][:3],
        },
        "compartments_SIR": sir,
        "obsolete_count": len(obsolete),
        "diagnosis": "",
    }

    # Generate diagnosis
    diag = []
    if bad["immune_status"] == "SUPERCRITICAL":
        diag.append(f"ALERT: harmful spread is supercritical (R_bad_op={bad['r_bad_operational']}, "
                     f"R_bad_total={bad['r_bad_mean']}, "
                     f"correction={bad['actual_correction_rate']}, need>{bad['herd_immunity_threshold']})")
    else:
        diag.append(f"Harmful spread CONTROLLED (R_bad_op={bad['r_bad_operational']}, "
                     f"R_bad_total={bad['r_bad_mean']})")

    if good["above_threshold"] > good["below_threshold"]:
        diag.append(f"Beneficial diffusion healthy ({good['above_threshold']}/{good['beneficial_count']} above critical mass)")
    else:
        diag.append(f"Beneficial diffusion weak ({good['below_threshold']}/{good['beneficial_count']} below critical mass)")

    if sir["infection_rate"] > 0.10:
        diag.append(f"HIGH infection rate: {sir['infection_rate']*100:.1f}% of lessons cite falsified sources")
    else:
        diag.append(f"Low infection rate: {sir['infection_rate']*100:.1f}%")

    report["diagnosis"] = " | ".join(diag)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("\n=== EPIDEMIC SPREAD MODEL (Dual R₀) ===\n")
        print(f"  {report['diagnosis']}\n")

        print("--- Harmful Spread (R_bad) ---")
        b = report["harmful_spread"]
        print(f"  R_bad (mean effective):     {b['R_bad_mean']}")
        print(f"  R_bad (operational only):   {b['R_bad_operational']}")
        print(f"    Operational infections:   {b['operational_infections']}")
        print(f"    Historical references:    {b['historical_refs']}")
        print(f"  Herd immunity threshold:    {b['herd_immunity_threshold']}")
        print(f"  Actual correction rate:     {b['actual_correction_rate']}")
        print(f"  Status:                     {b['immune_status']}")
        print(f"  Falsified lessons:          {b['falsified_count']}")
        if b["super_spreaders"]:
            print(f"  Super-spreaders (top 3):")
            for ss in b["super_spreaders"]:
                op = ss.get("operational_citers", "?")
                hist = ss.get("historical_citers", "?")
                print(f"    {ss['lesson']}: {ss['live_citers']} live ({op} operational, {hist} historical) "
                      f"/ {ss['total_citers']} total (correction={ss['correction_rate']:.2f})")

        if obsolete:
            print(f"\n--- Obsolete Lessons (maintenance debt, not epidemic) ---")
            print(f"  SUPERSEDED/ARCHIVED:        {len(obsolete)}")
            print(f"  NOTE: these are NOT harmful — successors exist. Citers may benefit")
            print(f"  from updating references but this is maintenance, not contamination.")

        print("\n--- Beneficial Spread (R_good) ---")
        g = report["beneficial_spread"]
        print(f"  Mean diffusion ratio:       {g['R_good_mean_diffusion']}")
        print(f"  Above critical mass:        {g['above_critical_mass']}/{g['beneficial_count']}")
        print(f"  Below critical mass:        {g['below_critical_mass']}/{g['beneficial_count']}")
        if g["trapped_knowledge"]:
            print(f"  Trapped knowledge (high value, low diffusion):")
            for tk in g["trapped_knowledge"]:
                print(f"    {tk['lesson']}: in-deg={tk['in_degree']}, sharpe={tk['sharpe']}, "
                      f"diffusion={tk['diffusion_ratio']}")
        if g["viral_knowledge"]:
            print(f"  Viral knowledge (highest diffusion):")
            for vk in g["viral_knowledge"]:
                print(f"    {vk['lesson']}: diffusion={vk['diffusion_ratio']}, in-deg={vk['in_degree']}")

        print("\n--- SIR Compartments ---")
        s = report["compartments_SIR"]
        print(f"  Susceptible (S): {s['S']:>5}  ({s['S']/s['total']*100:.1f}%)")
        print(f"  Infected (I):    {s['I']:>5}  ({s['infection_rate']*100:.1f}%)")
        print(f"  Recovered (R):   {s['R']:>5}  ({s['R']/s['total']*100:.1f}%)")
        print(f"  Vaccinated (V):  {s['V']:>5}  ({s['vaccination_rate']*100:.1f}%)")
        print(f"  Total immunity:  {s['immunity']*100:.1f}%")

        print(f"\n  Run with --external for the generic framework template")
        print(f"  Run with --json for machine-readable output\n")


if __name__ == "__main__":
    main()
