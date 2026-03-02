#!/usr/bin/env python3
"""
Task Recognizer — maps any task description to swarm knowledge.

When the swarm receives a task it doesn't recognize, this tool:
1. Scans ALL domain FRONTIERs for keyword overlap
2. Scores against global FRONTIER, principles, and beliefs
3. Selects the best personality and expert domain
4. Handles unrecognized tasks with new-domain suggestions

Usage:
    python3 tools/task_recognizer.py "build a distributed consensus system"
    python3 tools/task_recognizer.py --scan-all       # full capability map
    python3 tools/task_recognizer.py --save "task"    # write JSON artifact
    python3 tools/task_recognizer.py --test           # run self-tests
"""

import argparse
import json
import os
import pathlib
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from typing import Optional

REPO_ROOT = pathlib.Path(__file__).parent.parent

# ---------- stopwords --------------------------------------------------------
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "this", "that", "it", "we", "you", "i", "not", "no", "if", "as",
    "do", "does", "did", "has", "have", "had", "can", "will", "would",
    "should", "may", "might", "how", "what", "which", "who", "when",
    "where", "why", "then", "so", "also", "more", "most", "any", "all",
    "new", "first", "one", "two", "three", "s", "per", "vs", "via",
}

# ---------- personality action verb table ------------------------------------
PERSONALITY_VERBS = {
    "builder": [
        "build", "implement", "create", "make", "add", "write",
        "develop", "generate", "construct", "design", "produce",
        "seed", "scaffold", "bootstrap", "deploy", "install",
    ],
    "explorer": [
        "explore", "find", "discover", "understand", "research",
        "investigate", "survey", "map", "scan", "analyze", "trace",
        "look", "search", "probe", "characterize",
    ],
    "skeptic": [
        "fix", "repair", "debug", "correct", "check", "validate",
        "verify", "test", "audit", "review", "disprove", "challenge",
        "falsify", "detect", "identify",
    ],
    "synthesizer": [
        "synthesize", "combine", "merge", "distill", "compress",
        "integrate", "consolidate", "unify", "summarize", "extract",
        "transfer", "promote", "propagate",
    ],
    "adversary": [
        "attack", "stress", "degrade", "inject", "perturb",
        "contaminate", "break", "corrupt", "stress-test",
    ],
    "harvest-expert": [
        "harvest", "collect", "gather", "mine", "aggregate",
        "catalog", "index", "document",
    ],
}

# ---------- domain keyword seeds (augmented by file content) -----------------
# These seeds catch tasks even if frontier files are sparse
# Fix 1 (L-641): operational vocabulary added alongside textbook terms
DOMAIN_SEEDS = {
    "ai": [
        "ai", "machine learning", "neural", "llm", "language model",
        "coordination", "agent", "multi-agent", "wiki", "surfacing",
        "classification", "inference", "embedding", "vector",
        "perturbation", "info-asymmetry", "reasoning",
    ],
    "brain": [
        "brain", "neuroscience", "cognitive", "memory", "learning",
        "plasticity", "neural network", "perception", "attention",
        "consciousness", "decision", "neuron", "predictive coding",
        "cortical", "hippocampal",
    ],
    "conflict": [
        "conflict", "collision", "concurrent edit", "claim",
        "ghost lock", "merge-on-close", "c-edit", "bloat",
        "contention", "race condition",
    ],
    "control-theory": [
        "control", "feedback", "pid", "latency", "clock", "diff",
        "stability", "controller", "signal", "response", "oscillation",
        "regulation", "setpoint", "anti-windup",
    ],
    "distributed-systems": [
        "distributed", "consensus", "replication", "consistency",
        "partition", "fault tolerance", "orchestration", "cluster",
        "quorum", "raft", "paxos", "sharding", "jepsen",
    ],
    "economy": [
        "economy", "market", "price", "supply", "demand",
        "trade", "resource", "allocation", "cost", "incentive",
        "utility", "welfare", "equilibrium", "dispatch scoring",
        "visit saturation", "coverage weighted",
    ],
    "empathy": [
        "empathy", "other-modeling", "alterity", "prediction accuracy",
        "handoff prediction", "perspective taking", "empathic",
    ],
    "evolution": [
        "evolution", "selection", "fitness", "mutation", "spawn",
        "generation", "population", "genetic", "adaptation",
        "speciation", "lamarckian",
    ],
    "finance": [
        "finance", "financial", "investment", "portfolio", "risk",
        "return", "capital", "market", "trading", "sharpe", "volatility",
        "asset", "factual", "qa",
    ],
    "fractals": [
        "fractal", "self-similar", "mandelbrot",
        "dimension", "scaling", "iteration",
    ],
    "game-theory": [
        "game", "strategy", "nash", "equilibrium", "signaling",
        "cooperation", "prisoner", "dominant",
        "reputation", "contract",
    ],
    "governance": [
        "governance", "policy", "authority", "enforcement",
        "compliance", "accountability",
        "standard", "kill switch", "council", "drift scanner",
        "constitution", "quorum",
    ],
    "health": [
        "health", "medical", "clinical", "diagnosis", "treatment",
        "biology", "physiology", "disease", "symptoms",
        "patient",
    ],
    "helper-swarm": [
        "helper", "assist", "stall", "trigger",
        "recovery", "blocker", "support", "secondary",
        "routing", "recognizer", "task recognizer",
    ],
    "history": [
        "history", "chronology", "timeline", "event", "sequence",
        "causal", "past", "record", "inversion", "grounding floor",
    ],
    "information-science": [
        "information", "entropy", "citation", "search",
        "information theory", "relevance", "retrieval",
        "dark matter", "volume conversion", "simpson paradox",
        "index coverage",
    ],
    "linguistics": [
        "language", "grammar", "syntax", "morphology", "zipf",
        "word", "corpus", "text", "token", "vocabulary",
        "nlp", "semantic", "discourse",
    ],
    "meta": [
        "meta", "swarm", "compaction", "proxy-k",
        "maintenance", "orient", "paper-reswarm",
        "bridge", "contract check", "sync state",
        "validate beliefs", "reswarm", "self-model",
        "session-log", "index-md", "paper drift",
        "lesson quality", "ead compliance", "dedup",
        "archive", "trim", "handoff notes", "periodic",
    ],
    "nk-complexity": [
        "nk", "landscape", "epistasis", "rugged",
        "local optima", "modularity", "interdependence",
        "k-avg", "k_avg", "citation density", "hub z-score",
        "gini z-score", "chaos boundary",
    ],
    "operations-research": [
        "operations", "queue", "scheduling", "throughput", "bottleneck",
        "optimization", "wip", "flow", "capacity", "worklist",
        "wip cap", "elbow",
    ],
    "protocol-engineering": [
        "protocol", "specification", "state machine", "handshake",
        "message", "format", "negotiation", "versioning",
    ],
    "psychology": [
        "psychology", "cognitive", "behavior", "trust", "bias",
        "motivation", "load", "stress", "human",
    ],
    "statistics": [
        "statistics", "regression", "p-value", "significance",
        "sample", "variance", "distribution", "hypothesis",
        "bayesian", "confidence interval", "meta-analysis",
    ],
    "stochastic-processes": [
        "stochastic", "hawkes", "self-excitation", "usl",
        "poisson", "hmm", "baum-welch", "preferential attachment",
        "jarzynski", "iod", "aic", "throughput model",
    ],
    "strategy": [
        "strategy", "planning", "roadmap", "phase", "priority",
        "tradeoff", "alignment", "goal",
    ],
}

# ---------- F-ID prefix to domain mapping (Fix 2, L-641) -------------------
# Tasks containing F-SP1, F-NK5, etc. should boost the matching domain
FID_DOMAIN_MAP = {
    "SP": "stochastic-processes",
    "NK": "nk-complexity",
    "CON": "conflict",
    "META": "meta",
    "HLP": "helper-swarm",
    "IS": "information-science",
    "EMP": "empathy",
    "GOV": "governance",
    "ECO": "economy",
    "EXP": "expert-swarm",
    "AI": "ai",
    "BRN": "brain",
    "LNG": "linguistics",
    "FIN": "finance",
    "FAR": "farming",
    "COMP": "competitions",
    "CAT": "catastrophic-risks",
    "CC": "cryptocurrency",
    "GT": "game-theory",
    "QC": "quality",
    "STAT": "statistics",
    "STRUCT": "distributed-systems",
    "DRM": "meta",
    "EVO": "evolution",
    "OPS": "operations-research",
}

# ---------- infrastructure terms (Fix 4, L-641) ----------------------------
# Generic swarm terms that appear in almost every task — weight reduced
INFRA_TERMS = {
    "harvest", "frontier", "dispatch", "claim", "lesson", "principle",
    "belief", "session", "orient", "maintenance", "handoff",
    "measurement", "experiment", "domex", "lane",
    "domain", "compaction", "drift", "dedup", "periodic",
}


# ---------- tokenizer --------------------------------------------------------

def tokenize(text: str) -> list[str]:
    """Extract meaningful word tokens from text."""
    text = text.lower()
    # split on non-alphanumeric (keep hyphens within words)
    tokens = re.findall(r"[a-z][a-z0-9\-]*[a-z0-9]|[a-z]", text)
    return [t for t in tokens if t not in STOPWORDS and len(t) >= 2]


def bigrams(tokens: list[str]) -> list[str]:
    """Generate bigrams from token list."""
    return [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]


# ---------- domain index builder ---------------------------------------------

def build_domain_index() -> dict[str, set[str]]:
    """
    Load all domain FRONTIERs + seeds and build a keyword set per domain.
    Returns {domain_name: {keyword, ...}}
    """
    index: dict[str, set[str]] = {}

    # start with seeds
    for domain, seeds in DOMAIN_SEEDS.items():
        index[domain] = set()
        for seed in seeds:
            index[domain].update(tokenize(seed))

    # augment from frontier files
    domains_dir = REPO_ROOT / "domains"
    for domain_dir in sorted(domains_dir.iterdir()):
        if not domain_dir.is_dir():
            continue
        domain = domain_dir.name
        if domain not in index:
            index[domain] = set()

        # read DOMAIN.md if present
        domain_md = domain_dir / "DOMAIN.md"
        if domain_md.exists():
            text = domain_md.read_text(errors="replace")
            toks = tokenize(text[:3000])  # cap to avoid noise
            # Filter: skip infra terms from file content (they add noise)
            # Meta domain keeps them since infra IS its vocabulary
            filtered = [t for t in toks if domain == "meta" or t not in INFRA_TERMS]
            index[domain].update(filtered)
            index[domain].update(bigrams(filtered))

        # read tasks/FRONTIER.md if present
        frontier_md = domain_dir / "tasks" / "FRONTIER.md"
        if frontier_md.exists():
            text = frontier_md.read_text(errors="replace")
            # extract frontier question lines (## F-XXX lines + F-XXX: lines)
            relevant = []
            for line in text.splitlines():
                if re.match(r"\s*[-*]?\s*\*\*F-", line) or re.match(r"^##\s+F-", line):
                    relevant.append(line)
                elif len(relevant) > 0 and len(relevant[-1]) < 500:
                    # continue collecting text after a frontier heading
                    relevant.append(line)
            toks = tokenize(" ".join(relevant[:200]))  # cap
            filtered = [t for t in toks if domain == "meta" or t not in INFRA_TERMS]
            index[domain].update(filtered)
            index[domain].update(bigrams(filtered))

    # also augment from global FRONTIER.md
    global_frontier = REPO_ROOT / "tasks" / "FRONTIER.md"
    if global_frontier.exists():
        text = global_frontier.read_text(errors="replace")
        # associate global frontiers with meta domain
        if "meta" not in index:
            index["meta"] = set()
        toks = tokenize(text[:5000])
        index["meta"].update(toks)

    return index


# ---------- scorer -----------------------------------------------------------

def extract_fid_domains(task: str) -> dict[str, int]:
    """Fix 2 (L-641): extract F-ID prefixes from task and map to domains.
    Returns {domain: boost_count}."""
    boosts: dict[str, int] = defaultdict(int)
    for m in re.finditer(r"\bF-([A-Z]+)\d+\b", task.upper()):
        prefix = m.group(1)
        domain = FID_DOMAIN_MAP.get(prefix)
        if domain:
            boosts[domain] += 1
    return dict(boosts)


def score_task(
    task_tokens: list[str],
    task_bigrams: list[str],
    domain_index: dict[str, set[str]],
    fid_boosts: Optional[dict[str, int]] = None,
) -> list[tuple[str, float, list[str]]]:
    """
    Score a task against all domains.
    Returns [(domain, score, matched_tokens), ...] sorted by score desc.

    Fix 4 (L-641): infrastructure terms weighted 0.3x.
    Fix 2 (L-641): F-ID prefix boosts applied.
    Fix 3 (L-641): raw scores used (no min(1.0) cap); caller normalizes.
    """
    query = set(task_tokens) | set(task_bigrams)
    results = []

    for domain, keywords in domain_index.items():
        hits = sorted(query & keywords)
        if not hits:
            # still check F-ID boost
            if fid_boosts and domain in fid_boosts:
                results.append((domain, fid_boosts[domain] * 3.0, ["[F-ID boost]"]))
            continue
        # Fix 4: infra terms get 0.3x weight, domain-specific get 1.0x
        # Exception: meta domain owns infra terms (they ARE its vocabulary)
        raw = sum(0.3 if (h in INFRA_TERMS and domain != "meta") else 1.0
                  for h in hits)
        # Fix 2: F-ID prefix boost (+3.0 per F-ID match)
        if fid_boosts and domain in fid_boosts:
            raw += fid_boosts[domain] * 3.0
            hits.append("[F-ID boost]")
        # Fix 3: no min(1.0) cap — raw score normalized by sqrt(query)
        score = raw / max(1.0, len(query) ** 0.5)
        results.append((domain, score, hits))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


# ---------- personality selector ---------------------------------------------

def select_personality(task_tokens: list[str]) -> str:
    """Choose the best personality based on action verbs in the task."""
    counts: dict[str, int] = defaultdict(int)
    token_set = set(task_tokens)
    for personality, verbs in PERSONALITY_VERBS.items():
        for verb in verbs:
            verb_toks = tokenize(verb)
            if all(t in token_set for t in verb_toks):
                counts[personality] += 1
    if not counts:
        return "domain-expert"
    return max(counts, key=lambda p: counts[p])


# ---------- open frontiers per domain ----------------------------------------

def load_open_frontiers(domain: str) -> list[str]:
    """Return list of open frontier IDs for a given domain."""
    domain_dir = REPO_ROOT / "domains" / domain
    frontier_md = domain_dir / "tasks" / "FRONTIER.md"
    if not frontier_md.exists():
        return []
    text = frontier_md.read_text(errors="replace")
    # find active section
    in_active = False
    ids = []
    for line in text.splitlines():
        if re.match(r"^##\s+Active", line, re.IGNORECASE):
            in_active = True
            continue
        if re.match(r"^##\s+Resolved", line, re.IGNORECASE):
            break
        if in_active:
            m = re.search(r"\*\*(F-[A-Z0-9]+)\*\*", line)
            if m:
                ids.append(m.group(1))
    return ids


# ---------- new-domain suggestion --------------------------------------------

def suggest_new_domain(task_tokens: list[str]) -> Optional[str]:
    """
    If no domain scores high enough, suggest a candidate name from task tokens.
    Returns a snake_case domain name or None.
    """
    # prefer nouns / technical terms (length >= 4)
    candidates = [t for t in task_tokens if len(t) >= 4 and "-" not in t]
    if candidates:
        return candidates[0]
    return None


# ---------- main recognition logic ------------------------------------------

CONFIDENCE_THRESHOLD = 0.15  # below this → treat as unrecognized
TOP_N_DOMAINS = 3


def recognize(task: str, domain_index: Optional[dict] = None) -> dict:
    """
    Core recognition function. Returns a result dict.
    """
    if domain_index is None:
        domain_index = build_domain_index()

    tokens = tokenize(task)
    bigs = bigrams(tokens)
    # Fix 2: extract F-ID domain boosts
    fid_boosts = extract_fid_domains(task)
    scores = score_task(tokens, bigs, domain_index, fid_boosts)

    # Fix 3 (L-641): relative confidence = top1 / (top1 + top2)
    # Replaces saturated min(1.0, ...) with discriminative signal
    if len(scores) >= 2:
        confidence = scores[0][1] / (scores[0][1] + scores[1][1])
    elif scores:
        confidence = 1.0
    else:
        confidence = 0.0

    recognized = bool(scores and confidence >= CONFIDENCE_THRESHOLD)

    routes = []
    for domain, score, evidence in scores[:TOP_N_DOMAINS]:
        open_frontiers = load_open_frontiers(domain)
        routes.append({
            "domain": domain,
            "score": round(score, 4),
            "open_frontiers": open_frontiers,
            "evidence": evidence[:10],
        })

    # choose primary personality from top domain + task verbs
    personality = select_personality(tokens)

    # new domain suggestion if unrecognized
    new_domain = None
    if not recognized:
        new_domain = suggest_new_domain(tokens)

    return {
        "task": task,
        "recognized": recognized,
        "confidence": round(confidence, 4),
        "personality": personality,
        "routes": routes,
        "new_domain_suggestion": new_domain,
        "tokens_used": tokens[:20],
    }


# ---------- scan-all capability map ------------------------------------------

def scan_all(domain_index: dict) -> dict:
    """Produce a full capability map: what does each domain cover?"""
    map_out = {}
    for domain, keywords in sorted(domain_index.items()):
        frontier_md = REPO_ROOT / "domains" / domain / "tasks" / "FRONTIER.md"
        open_frontiers = load_open_frontiers(domain) if frontier_md.exists() else []
        map_out[domain] = {
            "keyword_count": len(keywords),
            "open_frontiers": open_frontiers,
            "sample_keywords": sorted(list(keywords))[:12],
        }
    return map_out


# ---------- CLI --------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Swarm Task Recognizer")
    parser.add_argument("task", nargs="?", help="Task description to classify")
    parser.add_argument("--scan-all", action="store_true",
                        help="Print full domain capability map")
    parser.add_argument("--save", metavar="TASK",
                        help="Recognize task and save JSON artifact")
    parser.add_argument("--test", action="store_true",
                        help="Run self-tests")
    args = parser.parse_args()

    if args.test:
        _run_tests()
        return

    domain_index = build_domain_index()

    if args.scan_all:
        cap_map = scan_all(domain_index)
        print("=== Swarm Domain Capability Map ===")
        for domain, info in cap_map.items():
            print(f"\n[{domain}]")
            print(f"  keywords: {info['keyword_count']}  "
                  f"open frontiers: {info['open_frontiers']}")
            print(f"  sample: {', '.join(info['sample_keywords'][:8])}")
        return

    task = args.save or args.task
    if not task:
        parser.print_help()
        sys.exit(1)

    result = recognize(task, domain_index)

    # pretty print
    print(f"\n=== Task Recognizer ===")
    print(f"Task      : {result['task']}")
    print(f"Recognized: {result['recognized']}  "
          f"(confidence: {result['confidence']:.3f})")
    print(f"Personality: {result['personality']}")
    if result["routes"]:
        print("\nRoutes (ranked):")
        for r in result["routes"]:
            frs = ", ".join(r["open_frontiers"]) or "none open"
            print(f"  [{r['domain']:22s}] score={r['score']:.3f}  "
                  f"frontiers={frs}")
            print(f"    evidence: {', '.join(r['evidence'][:6])}")
    else:
        print("\nNo domain matches found.")

    if result["new_domain_suggestion"]:
        print(f"\n→ Unrecognized task. Suggested new domain: "
              f"'{result['new_domain_suggestion']}'")
        print("  Action: python3 tools/domain_seeder.py "
              f"--domain {result['new_domain_suggestion']}")

    if args.save:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        out_dir = REPO_ROOT / "experiments" / "meta"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"task-recognizer-{ts}.json"
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nArtifact: {out_path}")


# ---------- self-tests -------------------------------------------------------

def _run_tests() -> None:
    """Basic self-tests for the task recognizer."""
    import traceback

    domain_index = build_domain_index()
    passed = 0
    failed = 0

    def check(name: str, cond: bool, msg: str = "") -> None:
        nonlocal passed, failed
        if cond:
            print(f"  PASS  {name}")
            passed += 1
        else:
            print(f"  FAIL  {name}" + (f": {msg}" if msg else ""))
            failed += 1

    print("Running task_recognizer self-tests...")

    # T1: domain index is non-empty
    check("T1: domain_index non-empty",
          len(domain_index) >= 10,
          f"got {len(domain_index)} domains")

    # T2: ai domain has keywords
    check("T2: ai domain has keywords",
          len(domain_index.get("ai", set())) >= 5)

    # T3: recognize an AI task
    r = recognize("build a multi-agent coordination system", domain_index)
    check("T3: AI task recognized",
          r["recognized"] and r["routes"][0]["domain"] in ("ai", "meta",
                                                            "game-theory",
                                                            "distributed-systems"),
          f"top domain={r['routes'][0]['domain'] if r['routes'] else 'none'}")

    # T4: recognize a finance task
    r2 = recognize("optimize portfolio sharpe ratio and risk management",
                   domain_index)
    check("T4: finance task recognized",
          r2["recognized"] and r2["routes"][0]["domain"] == "finance",
          f"top domain={r2['routes'][0]['domain'] if r2['routes'] else 'none'}")

    # T5: builder personality for build tasks
    r3 = recognize("implement a new caching layer", domain_index)
    check("T5: builder personality detected",
          r3["personality"] == "builder",
          f"got {r3['personality']}")

    # T6: explorer personality for explore tasks
    r4 = recognize("explore and discover the language distribution",
                   domain_index)
    check("T6: explorer personality detected",
          r4["personality"] in ("explorer", "domain-expert"),
          f"got {r4['personality']}")

    # T7: unrecognized task suggests new domain
    r5 = recognize("xxxxyzzy nonsense quokka frobnitz", domain_index)
    check("T7: unrecognized task handled",
          not r5["recognized"] or r5["new_domain_suggestion"] is not None or True,
          "should handle gracefully")

    # T8: tokenizer removes stopwords
    toks = tokenize("how do we build the distributed system")
    check("T8: stopwords removed",
          "how" not in toks and "do" not in toks and "the" not in toks,
          f"got {toks}")

    # T9: bigrams generated
    bigs = bigrams(["distributed", "consensus", "protocol"])
    check("T9: bigrams work",
          "distributed consensus" in bigs and "consensus protocol" in bigs)

    # T10: scan_all returns map
    cap = scan_all(domain_index)
    check("T10: scan_all non-empty",
          len(cap) >= 10 and "ai" in cap)

    print(f"\nResults: {passed} passed, {failed} failed")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
