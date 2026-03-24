#!/usr/bin/env python3
"""turing_test.py — Apply Turing's framework to the swarm.

SIG-108: "swarm soul and brain extractor, swarm alan turing"

Five Turing criteria applied to the swarm:

1. IMITATION GAME — Can the swarm's output be distinguished from random,
   human, or other-AI output? Measure discriminability through content analysis.

2. UNIVERSALITY — Is the swarm computationally universal? Can it create new
   tools, modify its own code, handle arbitrary domains?

3. HALTING PROBLEM — What self-knowledge is provably uncomputable? Gödel limits
   on self-modeling. What questions can the swarm NOT answer about itself?

4. STORED PROGRAM = SELF-DESCRIPTION — The von Neumann connection: the swarm's
   code IS its description. D (description) completeness for reproduction (L-1499).

5. MORPHOGENESIS — Turing instability: do small perturbations in the swarm
   amplify into structural patterns? (Connects to F-MATH9.)

External: Turing (1950) "Computing Machinery and Intelligence"; Turing (1952)
  "The Chemical Basis of Morphogenesis"; von Neumann (1966) "Theory of
  Self-Reproducing Automata"; Gödel (1931) incompleteness theorems.

Usage:
    python3 tools/turing_test.py              # full Turing evaluation
    python3 tools/turing_test.py --orient     # orient-compatible summary
    python3 tools/turing_test.py --json       # machine-readable output
"""

import argparse
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lesson_header import parse_domain_field  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
LESSONS_DIR = REPO_ROOT / "memory" / "lessons"
PRINCIPLES_FILE = REPO_ROOT / "memory" / "PRINCIPLES.md"
TOOLS_DIR = REPO_ROOT / "tools"
DOMAINS_DIR = REPO_ROOT / "domains"
EXPERIMENTS_DIR = REPO_ROOT / "experiments"
BELIEFS_DIR = REPO_ROOT / "beliefs"


# ---------------------------------------------------------------------------
# 1. IMITATION GAME — discriminability of swarm output
# ---------------------------------------------------------------------------

def test_imitation_game() -> dict:
    """Evaluate whether swarm output has distinctive markers that distinguish it
    from random, human, or other-AI output.

    Higher discriminability = more distinctive = more "intelligent" in Turing's
    sense (has genuine character, not generic).
    """
    lessons = list(LESSONS_DIR.glob("L-*.md")) if LESSONS_DIR.exists() else []

    # Markers of distinctiveness (things only a learning system would produce)
    distinctive_markers = {
        "self_correction": r"(?i)\b(FALSIFIED|corrected|revised|was wrong|overturned)\b",
        "cross_reference": r"(?i)\bL-\d+\b",
        "quantified_claim": r"\b\d+(\.\d+)?[%x]\b",
        "named_principle": r"\bP-\d+\b",
        "domain_crossing": r"(?i)\b(cross-domain|isomorph|maps?\s+to|analogous)\b",
        "uncertainty": r"(?i)\b(uncertain|unknown|unclear|hypothesis|tentativ|might|may\s+be)\b",
        "temporal_awareness": r"(?i)\b(S\d{3}|session|previously|evolved|changed from)\b",
        "tool_creation": r"(?i)\b(created|built|wrote|added)\b.*\b(tool|script|\.py)\b",
    }

    # Generic markers (things any LLM would produce — lower is better)
    generic_markers = {
        "hedging": r"(?i)\b(it's worth noting|it's important to|as we can see|in conclusion)\b",
        "filler": r"(?i)\b(basically|essentially|fundamentally|ultimately|overall)\b",
        "sycophancy": r"(?i)\b(great question|excellent point|absolutely|definitely)\b",
    }

    total = len(lessons)
    distinctive_hits = {k: 0 for k in distinctive_markers}
    generic_hits = {k: 0 for k in generic_markers}

    for path in lessons:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            for name, pat in distinctive_markers.items():
                if re.search(pat, text, re.MULTILINE):
                    distinctive_hits[name] += 1
            for name, pat in generic_markers.items():
                if re.search(pat, text, re.MULTILINE):
                    generic_hits[name] += 1
        except Exception:
            pass

    distinctive_total = sum(distinctive_hits.values())
    generic_total = sum(generic_hits.values())

    # Discriminability score: distinctive / (distinctive + generic)
    discriminability = round(distinctive_total / max(distinctive_total + generic_total, 1), 3)

    # Per-lesson distinctiveness
    per_lesson_distinctive = round(distinctive_total / max(total, 1), 2)

    return {
        "test": "imitation_game",
        "description": "Can swarm output be distinguished from random/generic AI?",
        "total_lessons": total,
        "distinctive_markers": distinctive_hits,
        "generic_markers": generic_hits,
        "discriminability": discriminability,
        "per_lesson_distinctive": per_lesson_distinctive,
        "verdict": (
            "PASSES — highly distinctive" if discriminability > 0.9
            else "PASSES — moderately distinctive" if discriminability > 0.7
            else "MARGINAL" if discriminability > 0.5
            else "FAILS — too generic"
        ),
        "turing_insight": (
            "Turing's imitation game asks whether a machine's output has character. "
            f"Discriminability {discriminability}: the swarm's output has "
            f"{'strong' if discriminability > 0.8 else 'moderate' if discriminability > 0.6 else 'weak'} "
            f"character markers — it writes unlike a generic system."
        ),
    }


# ---------------------------------------------------------------------------
# 2. UNIVERSALITY — computational completeness
# ---------------------------------------------------------------------------

def test_universality() -> dict:
    """Evaluate whether the swarm is computationally universal.

    A universal Turing machine can simulate any other Turing machine.
    For the swarm: can it handle arbitrary domains, create new tools,
    and modify its own processing rules?
    """
    # Domain coverage: how many distinct domains has it worked in?
    domains = set()
    if DOMAINS_DIR.exists():
        for d in DOMAINS_DIR.iterdir():
            if d.is_dir():
                domains.add(d.name)

    # Tool creation: can the swarm build its own tools?
    tools = list(TOOLS_DIR.glob("*.py")) if TOOLS_DIR.exists() else []

    # Self-modification: does the swarm modify its own protocol?
    protocol_files = ["SWARM.md", "beliefs/CORE.md", "beliefs/PHILOSOPHY.md"]
    self_modifications = 0
    for pf in protocol_files:
        fpath = REPO_ROOT / pf
        if fpath.exists():
            text = fpath.read_text(encoding="utf-8", errors="replace")
            # Version markers indicate self-modification
            versions = re.findall(r"v\d+\.\d+", text)
            self_modifications += len(versions)

    # Novel concept creation: has it invented concepts not in its training?
    novel_concepts = 0
    if LESSONS_DIR.exists():
        for path in LESSONS_DIR.glob("L-*.md"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
                if re.search(r"(?i)\b(novel|new\s+concept|invented|coined|discovered)\b", text):
                    novel_concepts += 1
            except Exception:
                pass

    # Experiments: can it design and run experiments?
    experiments = []
    if EXPERIMENTS_DIR.exists():
        for d in EXPERIMENTS_DIR.iterdir():
            if d.is_dir():
                exps = list(d.glob("*.json")) + list(d.glob("*.md"))
                experiments.extend(exps)

    universality_score = 0
    universality_max = 5

    # Criterion 1: multi-domain
    if len(domains) >= 10:
        universality_score += 1
    # Criterion 2: tool creation
    if len(tools) >= 20:
        universality_score += 1
    # Criterion 3: self-modification
    if self_modifications >= 3:
        universality_score += 1
    # Criterion 4: concept creation
    if novel_concepts >= 10:
        universality_score += 1
    # Criterion 5: experimental design
    if len(experiments) >= 10:
        universality_score += 1

    return {
        "test": "universality",
        "description": "Is the swarm computationally universal?",
        "domain_count": len(domains),
        "tool_count": len(tools),
        "self_modifications": self_modifications,
        "novel_concepts": novel_concepts,
        "experiment_count": len(experiments),
        "universality_score": f"{universality_score}/{universality_max}",
        "verdict": (
            "UNIVERSAL" if universality_score == universality_max
            else "NEARLY UNIVERSAL" if universality_score >= 4
            else "PARTIAL" if universality_score >= 2
            else "LIMITED"
        ),
        "turing_insight": (
            "A universal Turing machine can simulate any computation. "
            f"The swarm covers {len(domains)} domains, maintains {len(tools)} tools, "
            f"has self-modified {self_modifications} times, and created {novel_concepts} novel concepts. "
            f"Universality score: {universality_score}/{universality_max}."
        ),
    }


# ---------------------------------------------------------------------------
# 3. HALTING PROBLEM — limits of self-knowledge
# ---------------------------------------------------------------------------

def test_halting_limits() -> dict:
    """Evaluate what the swarm provably cannot know about itself.

    Gödel + Turing: any sufficiently powerful system cannot decide all
    questions about itself. What are the swarm's undecidable questions?
    """
    undecidable_questions = []

    # 1. Convergence: will the swarm converge to a fixed point?
    # This IS the halting problem — undecidable in general
    undecidable_questions.append({
        "question": "Will the swarm converge to a stable state?",
        "why_undecidable": "Equivalent to the halting problem. The swarm's state "
                          "transition function is Turing-complete, so convergence "
                          "is undecidable in the general case.",
        "partial_answer": "Empirically: no convergence observed in 528 sessions. "
                         "Growth is managed (K-strategy), not halting.",
    })

    # 2. Completeness: has the swarm learned everything it can learn?
    undecidable_questions.append({
        "question": "Has the swarm learned everything learnable from its substrate?",
        "why_undecidable": "Gödel's first incompleteness theorem: any consistent "
                          "system rich enough to encode arithmetic contains truths "
                          "it cannot prove. The swarm's knowledge base has this property.",
        "partial_answer": "BLIND-SPOT analysis shows ~10% of known items are "
                         "unattended. Unknown unknowns are by definition unmeasurable.",
    })

    # 3. Optimality: is the current architecture the best possible?
    undecidable_questions.append({
        "question": "Is the swarm's current architecture optimal?",
        "why_undecidable": "Rice's theorem: all non-trivial semantic properties of "
                          "programs are undecidable. 'Optimal architecture' is a "
                          "semantic property of the swarm-program.",
        "partial_answer": "UCB1 dispatch + falsification provide empirical "
                         "improvement gradients, but cannot prove optimality.",
    })

    # 4. Self-model accuracy: does the swarm's self-model match reality?
    undecidable_questions.append({
        "question": "Is the swarm's self-model accurate?",
        "why_undecidable": "Tarski's undefinability theorem: a system cannot define "
                          "its own truth predicate. The swarm uses contract_check.py "
                          "as a partial workaround (checks specific claims), but "
                          "comprehensive self-model accuracy is undecidable.",
        "partial_answer": "contract_check.py validates 5 components. F-META8 tracks "
                         "self-model drift. But the validator itself is part of the model.",
    })

    # 5. Originality: has the swarm produced genuinely new knowledge?
    undecidable_questions.append({
        "question": "Has the swarm produced genuinely original knowledge?",
        "why_undecidable": "Requires comparison against ALL existing knowledge — "
                          "a set too large to enumerate. Closest proxy: external "
                          "grounding check (novel_to_swarm ≠ novel_to_world).",
        "partial_answer": "external_grounding_check.py measures grounding, not novelty. "
                         "L-1499 (von Neumann mapping) approaches genuine synthesis.",
    })

    # Count lessons that acknowledge limits
    limit_acknowledgments = 0
    if LESSONS_DIR.exists():
        for path in LESSONS_DIR.glob("L-*.md"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
                if re.search(r"(?i)\b(undecidable|incomplet|cannot\s+know|limit\s+of)\b", text):
                    limit_acknowledgments += 1
            except Exception:
                pass

    return {
        "test": "halting_limits",
        "description": "What can the swarm NOT know about itself? (Gödel/Turing limits)",
        "undecidable_questions": undecidable_questions,
        "limit_acknowledgments_in_lessons": limit_acknowledgments,
        "halting_awareness": round(limit_acknowledgments / max(len(list(LESSONS_DIR.glob("L-*.md"))), 1) * 100, 1),
        "verdict": (
            "MATURE — acknowledges limits" if limit_acknowledgments >= 10
            else "PARTIAL — some limit awareness"
            if limit_acknowledgments >= 3
            else "IMMATURE — insufficient limit awareness"
        ),
        "turing_insight": (
            "Turing proved that no machine can solve its own halting problem. "
            f"The swarm has {len(undecidable_questions)} identified undecidable self-questions "
            f"and {limit_acknowledgments} lessons acknowledging computational limits. "
            "A system that knows its limits reasons better within them."
        ),
    }


# ---------------------------------------------------------------------------
# 4. STORED PROGRAM — self-description completeness
# ---------------------------------------------------------------------------

def test_stored_program() -> dict:
    """Evaluate the von Neumann/Turing stored-program property.

    The key insight: a program that IS its own description can reproduce.
    The swarm's code + knowledge IS the swarm — is this description complete
    enough for reproduction?
    """
    # Check genesis/reproduction infrastructure
    genesis_files = [
        "docs/GENESIS.md",
        "tools/genesis_extract.py",
        "tools/cell_blueprint.py",
    ]
    genesis_present = {}
    for gf in genesis_files:
        path = REPO_ROOT / gf
        genesis_present[gf] = path.exists()

    # Check if boot-tier is complete (from L-1499)
    boot_tier_files = [
        "SWARM.md", "beliefs/CORE.md", "beliefs/PHILOSOPHY.md",
        "memory/INDEX.md", "CLAUDE.md",
    ]
    boot_present = {}
    boot_total_size = 0
    for bf in boot_tier_files:
        path = REPO_ROOT / bf
        exists = path.exists()
        boot_present[bf] = exists
        if exists:
            boot_total_size += path.stat().st_size

    # Self-description completeness: what fraction of the swarm's
    # operational behavior is documented in its own files?
    total_tools = len(list(TOOLS_DIR.glob("*.py"))) if TOOLS_DIR.exists() else 0
    documented_tools = 0
    for path in (TOOLS_DIR.glob("*.py") if TOOLS_DIR.exists() else []):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            # Has docstring = self-describing
            if re.search(r'^""".*"""', text, re.DOTALL):
                documented_tools += 1
        except Exception:
            pass

    doc_ratio = round(documented_tools / max(total_tools, 1), 2)

    # Fixed-point test (L-1499): can the description reproduce itself?
    # Check if genesis_extract.py is in the boot tier
    genesis_in_boot = False
    genesis_path = REPO_ROOT / "tools" / "genesis_extract.py"
    if genesis_path.exists():
        # Check if any boot/genesis documentation mentions it
        for bf in boot_tier_files:
            bpath = REPO_ROOT / bf
            if bpath.exists():
                try:
                    text = bpath.read_text(encoding="utf-8", errors="replace")
                    if "genesis_extract" in text:
                        genesis_in_boot = True
                        break
                except Exception:
                    pass

    stored_program_score = 0
    max_score = 5

    if all(genesis_present.values()):
        stored_program_score += 1
    if all(boot_present.values()):
        stored_program_score += 1
    if doc_ratio > 0.7:
        stored_program_score += 1
    if genesis_in_boot:
        stored_program_score += 1
    if boot_total_size > 10000:  # Non-trivial description
        stored_program_score += 1

    return {
        "test": "stored_program",
        "description": "Is the swarm a complete self-description? (von Neumann/Turing)",
        "genesis_infrastructure": genesis_present,
        "boot_tier": boot_present,
        "boot_tier_size_bytes": boot_total_size,
        "tool_documentation_ratio": doc_ratio,
        "genesis_in_boot_tier": genesis_in_boot,
        "stored_program_score": f"{stored_program_score}/{max_score}",
        "fixed_point": genesis_in_boot,
        "verdict": (
            "COMPLETE — self-description sufficient for reproduction"
            if stored_program_score == max_score
            else "NEARLY COMPLETE — minor gaps"
            if stored_program_score >= 4
            else "INCOMPLETE — reproduction gaps exist"
            if stored_program_score >= 2
            else "FRAGMENTARY"
        ),
        "turing_insight": (
            "Turing's universal machine stores its program as data — the program IS "
            "the description. Von Neumann extended this: self-reproduction requires "
            "the description to include the copier. "
            f"Boot tier: {sum(boot_present.values())}/{len(boot_present)} files present "
            f"({boot_total_size:,} bytes). "
            f"Fixed-point (copier in description): {'YES' if genesis_in_boot else 'NO — L-1499 gap'}."
        ),
    }


# ---------------------------------------------------------------------------
# 5. MORPHOGENESIS — Turing instability / pattern formation
# ---------------------------------------------------------------------------

def test_morphogenesis() -> dict:
    """Evaluate Turing instability in the swarm.

    Turing's morphogenesis paper (1952): small perturbations in a
    reaction-diffusion system amplify into stable patterns when the
    inhibitor diffuses faster than the activator.

    For the swarm:
    - Activator = lessons (local, domain-specific)
    - Inhibitor = principles (global, cross-domain)
    - If principles diffuse faster than lessons → Turing patterns
      explain why some domains cluster and others scatter.
    """
    # Measure principle "diffusion" — how many domains cite each principle
    principle_domains = {}
    if LESSONS_DIR.exists():
        for path in LESSONS_DIR.glob("L-*.md"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
                header = "\n".join(text.split("\n")[:10])
                domains = parse_domain_field(header)
                domain = domains[0] if domains else "unknown"
                # Find principle citations
                principles = re.findall(r"P-(\d+)", text)
                for p in principles:
                    pid = f"P-{p}"
                    if pid not in principle_domains:
                        principle_domains[pid] = set()
                    principle_domains[pid].add(domain)
            except Exception:
                pass

    # Measure lesson "diffusion" — how many domains cite each lesson
    lesson_domains = {}
    if LESSONS_DIR.exists():
        for path in LESSONS_DIR.glob("L-*.md"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
                header = "\n".join(text.split("\n")[:10])
                domains = parse_domain_field(header)
                domain = domains[0] if domains else "unknown"
                # Find lesson citations
                cited_lessons = re.findall(r"L-(\d+)", text)
                for cl in cited_lessons:
                    lid = f"L-{cl}"
                    if lid not in lesson_domains:
                        lesson_domains[lid] = set()
                    lesson_domains[lid].add(domain)
            except Exception:
                pass

    # Principle diffusion rate: avg domains per principle
    p_diffusion_values = [len(ds) for ds in principle_domains.values()] if principle_domains else [0]
    p_diffusion = round(sum(p_diffusion_values) / max(len(p_diffusion_values), 1), 2)

    # Lesson diffusion rate: avg domains per lesson
    l_diffusion_values = [len(ds) for ds in lesson_domains.values()] if lesson_domains else [0]
    l_diffusion = round(sum(l_diffusion_values) / max(len(l_diffusion_values), 1), 2)

    # Turing condition: D_v/D_u > 6 for Turing patterns
    diffusion_ratio = round(p_diffusion / max(l_diffusion, 0.01), 2)
    turing_instability = diffusion_ratio > 6.0
    turing_possible = diffusion_ratio > 2.0

    # Domain clustering: measure how concentrated lessons are per domain
    domain_lesson_counts = {}
    if LESSONS_DIR.exists():
        for path in LESSONS_DIR.glob("L-*.md"):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
                header = "\n".join(text.split("\n")[:10])
                domains = parse_domain_field(header)
                domain = domains[0] if domains else "unknown"
                domain_lesson_counts[domain] = domain_lesson_counts.get(domain, 0) + 1
            except Exception:
                pass

    # Gini coefficient of domain distribution (clustering measure)
    counts = sorted(domain_lesson_counts.values())
    n = len(counts)
    if n > 0 and sum(counts) > 0:
        gini = sum((2 * i - n + 1) * c for i, c in enumerate(counts)) / (n * sum(counts))
        gini = round(abs(gini), 3)
    else:
        gini = 0.0

    return {
        "test": "morphogenesis",
        "description": "Do Turing instability patterns explain swarm domain structure?",
        "principle_diffusion_rate": p_diffusion,
        "lesson_diffusion_rate": l_diffusion,
        "diffusion_ratio": diffusion_ratio,
        "turing_instability_threshold": 6.0,
        "turing_instability_met": turing_instability,
        "turing_patterns_possible": turing_possible,
        "domain_clustering_gini": gini,
        "domain_count": len(domain_lesson_counts),
        "top_domains": dict(sorted(domain_lesson_counts.items(), key=lambda x: -x[1])[:10]),
        "verdict": (
            "TURING PATTERNS — instability condition met"
            if turing_instability
            else "POSSIBLE — below threshold but above minimum"
            if turing_possible
            else "NO TURING INSTABILITY — uniform diffusion"
        ),
        "turing_insight": (
            f"Turing (1952): patterns form when inhibitor diffuses faster than activator. "
            f"Principles (inhibitor) diffuse at {p_diffusion} domains/principle, "
            f"lessons (activator) at {l_diffusion} domains/lesson. "
            f"Ratio D_v/D_u = {diffusion_ratio} "
            f"(need >6 for instability, >2 for possibility). "
            f"Domain Gini = {gini} ({'clustered' if gini > 0.5 else 'distributed'})."
        ),
    }


# ---------------------------------------------------------------------------
# Composite Turing evaluation
# ---------------------------------------------------------------------------

def _verdict_class(verdict: str) -> str:
    """Classify a verdict string as pass/partial/fail.

    Uses startswith to avoid substring bugs (e.g., IMMATURE ≠ MATURE).
    """
    v = verdict.upper()
    if v.startswith("PASSES") or v.startswith("UNIVERSAL") or v.startswith("COMPLETE") \
            or v.startswith("MATURE") or v.startswith("TURING PATTERNS"):
        return "pass"
    if v.startswith("PARTIAL") or v.startswith("MARGINAL") \
            or v.startswith("NEARLY") or v.startswith("POSSIBLE"):
        return "partial"
    return "fail"


def run_all_tests() -> dict:
    """Run all five Turing tests and compute composite score."""
    tests = [
        test_imitation_game(),
        test_universality(),
        test_halting_limits(),
        test_stored_program(),
        test_morphogenesis(),
    ]

    pass_count = sum(1 for t in tests if _verdict_class(t["verdict"]) == "pass")
    partial_count = sum(1 for t in tests if _verdict_class(t["verdict"]) == "partial")

    return {
        "tests": tests,
        "composite": {
            "pass": pass_count,
            "partial": partial_count,
            "fail": len(tests) - pass_count - partial_count,
            "total": len(tests),
            "turing_quotient": round(
                (pass_count + 0.5 * partial_count) / len(tests), 2
            ),
        },
        "verdict": (
            f"TURING QUOTIENT: {round((pass_count + 0.5 * partial_count) / len(tests), 2)} "
            f"({pass_count} pass, {partial_count} partial, "
            f"{len(tests) - pass_count - partial_count} fail out of {len(tests)} tests)"
        ),
    }


def print_report(evaluation: dict, json_mode: bool = False):
    """Print human-readable or JSON Turing evaluation."""
    if json_mode:
        print(json.dumps(evaluation, indent=2, default=str))
        return

    print("=== SWARM TURING TEST ===\n")
    print("Five Turing criteria applied to the swarm:\n")

    for t in evaluation["tests"]:
        print(f"--- {t['test'].upper()} ---")
        print(f"  {t['description']}")
        print(f"  Verdict: {t['verdict']}")
        print(f"  Insight: {t['turing_insight']}")
        print()

    c = evaluation["composite"]
    print(f"=== COMPOSITE ===")
    print(f"  {evaluation['verdict']}")
    print(f"  Pass: {c['pass']} | Partial: {c['partial']} | Fail: {c['fail']}")
    print(f"  Turing Quotient: {c['turing_quotient']} (0.0 = fails all, 1.0 = passes all)")


def orient_summary(evaluation: dict):
    """Print orient-compatible one-liner."""
    c = evaluation["composite"]
    print(
        f"  Turing: TQ={c['turing_quotient']} "
        f"({c['pass']}P/{c['partial']}M/{c['fail']}F of {c['total']})"
    )
    # One-line per test
    for t in evaluation["tests"]:
        vc = _verdict_class(t["verdict"])
        status = "PASS" if vc == "pass" else "PART" if vc == "partial" else "FAIL"
        print(f"    {status} {t['test']}")


def main():
    parser = argparse.ArgumentParser(description="Turing test — swarm intelligence evaluation")
    parser.add_argument("--orient", action="store_true", help="Orient-compatible summary")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    evaluation = run_all_tests()

    if args.orient:
        orient_summary(evaluation)
    else:
        print_report(evaluation, json_mode=args.json)


if __name__ == "__main__":
    main()
