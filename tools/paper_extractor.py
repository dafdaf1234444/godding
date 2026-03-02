#!/usr/bin/env python3
"""
paper_extractor.py — Extract and route research papers to domain experts.

Pipeline:
  1. Query: fetch papers from Semantic Scholar API by domain keywords
  2. Route: assign each paper to ≥1 domain expert by keyword overlap
  3. Evaluate: score relevance + isomorphism potential per domain
  4. Integrate: emit recommended_actions for domain FRONTIERs + ISOMORPHISM-ATLAS

Usage:
    python3 tools/paper_extractor.py query <domain> [--limit N]
    python3 tools/paper_extractor.py route <papers.json>
    python3 tools/paper_extractor.py full [--domain <d>] [--limit N]
    python3 tools/paper_extractor.py test          # offline validation

Output (JSON to stdout):
    {
      "papers": [{"title", "abstract", "year", "citations", "url", "domains"}],
      "expert_evaluations": [{"paper", "domain", "relevance", "isomorphism_score", "key_concept"}],
      "recommended_actions": ["Add to domain FRONTIER: ...", "Add to ISOMORPHISM-ATLAS: ..."]
    }

isomorphism_score: 0.0 = no structural match; 1.0 = strong structural match with swarm.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
import urllib.parse
from typing import Any

# ---------------------------------------------------------------------------
# Domain → search query mapping
# Each domain has primary queries + structure keywords for isomorphism scoring
# ---------------------------------------------------------------------------
DOMAIN_QUERIES: dict[str, dict] = {
    "ai": {
        "queries": ["swarm intelligence emergent coordination", "multi-agent system belief revision",
                    "self-organizing systems distributed learning"],
        "keywords": ["swarm", "multi-agent", "emergent", "distributed", "coordination",
                     "self-organization", "belief", "agent"],
        "swarm_isomorphism_hints": ["coordination overhead", "information asymmetry",
                                    "belief propagation", "agent hierarchy"],
    },
    "brain": {
        "queries": ["neural circuit emergent computation", "cortical hierarchy belief updating",
                    "predictive coding sparse representation"],
        "keywords": ["neural", "cortical", "synapse", "hippocampus", "plasticity",
                     "predictive", "hierarchy", "sparse"],
        "swarm_isomorphism_hints": ["Hebbian learning = co-citation strengthening",
                                    "predictive coding = expect-act-diff",
                                    "sparse coding = compaction"],
    },
    "evolution": {
        "queries": ["evolutionary dynamics fitness landscape adaptation",
                    "natural selection population genetics epistasis"],
        "keywords": ["fitness", "selection", "mutation", "epistasis", "adaptation",
                     "population", "genotype", "phenotype", "drift"],
        "swarm_isomorphism_hints": ["fitness = Sharpe ratio", "mutation = session variation",
                                    "selection pressure = context window limit",
                                    "NK landscape = belief interdependence"],
    },
    "economy": {
        "queries": ["market equilibrium resource allocation mechanism design",
                    "network economics distributed market"],
        "keywords": ["market", "equilibrium", "allocation", "mechanism", "incentive",
                     "utility", "network", "price", "auction"],
        "swarm_isomorphism_hints": ["price = proxy-K signal", "market clearing = lane closure",
                                    "mechanism design = dispatch policy"],
    },
    "game-theory": {
        "queries": ["Nash equilibrium coordination game signaling",
                    "cooperative game theory coalition formation"],
        "keywords": ["Nash", "equilibrium", "strategy", "cooperation", "signaling",
                     "coalition", "game", "payoff", "dominant"],
        "swarm_isomorphism_hints": ["Nash equilibrium = stable belief state",
                                    "coalition = domain shard", "signaling = bulletin"],
    },
    "information-science": {
        "queries": ["information asymmetry knowledge graph distributed knowledge",
                    "semantic similarity knowledge compression"],
        "keywords": ["information", "asymmetry", "knowledge", "semantic", "compression",
                     "retrieval", "entropy", "Kolmogorov"],
        "swarm_isomorphism_hints": ["information asymmetry = SESSION-LOG gap",
                                    "compression = compaction", "entropy = belief uncertainty"],
    },
    "statistics": {
        "queries": ["meta-analysis heterogeneity effect size bayesian updating",
                    "multiple comparison correction hypothesis testing"],
        "keywords": ["meta-analysis", "heterogeneity", "Bayesian", "effect", "p-value",
                     "variance", "prior", "posterior", "significance"],
        "swarm_isomorphism_hints": ["STAT gate = multiple comparison correction",
                                    "Bayesian update = belief revision",
                                    "heterogeneity I² = domain variation"],
    },
    "control-theory": {
        "queries": ["feedback control stability convergence adaptive control",
                    "model predictive control distributed control"],
        "keywords": ["feedback", "stability", "control", "convergence", "adaptive",
                     "lyapunov", "oscillation", "setpoint"],
        "swarm_isomorphism_hints": ["feedback = expect-act-diff loop",
                                    "stability = belief convergence",
                                    "adaptive control = dynamic protocol"],
    },
    "psychology": {
        "queries": ["cognitive bias decision heuristic group cognition",
                    "motivated reasoning confirmation bias"],
        "keywords": ["bias", "heuristic", "cognition", "decision", "belief",
                     "anchoring", "confirmation", "motivated"],
        "swarm_isomorphism_hints": ["confirmation bias = belief entrenchment",
                                    "group cognition = swarm collective reasoning"],
    },
    "operations-research": {
        "queries": ["scheduling queuing theory resource allocation optimization",
                    "WIP limit throughput constraint"],
        "keywords": ["scheduling", "queuing", "throughput", "WIP", "constraint",
                     "optimization", "bottleneck", "capacity"],
        "swarm_isomorphism_hints": ["WIP limit = lane cap", "throughput = sessions per commit",
                                    "queuing = SWARM-LANES backlog"],
    },
}

SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1/paper/search"
PAPER_FIELDS = "title,abstract,year,citationCount,externalIds"


def _query_semantic_scholar(query: str, limit: int = 5) -> list[dict]:
    """Fetch papers from Semantic Scholar. Returns [] on failure."""
    params = urllib.parse.urlencode({
        "query": query,
        "fields": PAPER_FIELDS,
        "limit": limit,
    })
    url = f"{SEMANTIC_SCHOLAR_API}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "swarm-paper-extractor/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get("data", [])
    except Exception:
        return []


def _keyword_overlap(text: str, keywords: list[str]) -> float:
    """Fraction of domain keywords found in text (case-insensitive)."""
    if not text or not keywords:
        return 0.0
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in text_lower)
    return hits / len(keywords)


def _isomorphism_score(text: str, hints: list[str]) -> float:
    """Score structural similarity to swarm based on isomorphism hints."""
    if not text:
        return 0.0
    text_lower = text.lower()
    # Extract left-side concepts from "X = Y" hint format
    concepts = []
    for hint in hints:
        parts = re.split(r"=|→", hint)
        for p in parts:
            concepts.extend(re.findall(r"\b\w{4,}\b", p.lower()))
    if not concepts:
        return 0.0
    hits = sum(1 for c in concepts if c in text_lower)
    return min(1.0, hits / max(1, len(concepts) * 0.4))


def route_paper(paper: dict, domains: list[str] | None = None) -> list[str]:
    """Return list of domain names this paper belongs to, ordered by relevance."""
    title = paper.get("title", "")
    abstract = paper.get("abstract", "") or ""
    text = f"{title} {abstract}"

    target_domains = domains if domains else list(DOMAIN_QUERIES.keys())
    scores: list[tuple[float, str]] = []
    for domain in target_domains:
        if domain not in DOMAIN_QUERIES:
            continue
        cfg = DOMAIN_QUERIES[domain]
        overlap = _keyword_overlap(text, cfg["keywords"])
        if overlap >= 0.05:  # at least 1 keyword hit typically
            scores.append((overlap, domain))

    scores.sort(reverse=True)
    return [d for _, d in scores[:3]]  # top 3 domain matches


def evaluate_paper(paper: dict, domain: str) -> dict:
    """Produce expert evaluation for a paper in a given domain."""
    cfg = DOMAIN_QUERIES.get(domain, {})
    title = paper.get("title", "")
    abstract = paper.get("abstract", "") or ""
    text = f"{title} {abstract}"

    relevance = _keyword_overlap(text, cfg.get("keywords", []))
    iso_score = _isomorphism_score(text, cfg.get("swarm_isomorphism_hints", []))

    # Extract most prominent domain keyword found in paper as key concept
    key_concept = ""
    for kw in cfg.get("keywords", []):
        if kw.lower() in text.lower():
            key_concept = kw
            break

    return {
        "paper_title": title,
        "domain": domain,
        "relevance": round(relevance, 3),
        "isomorphism_score": round(iso_score, 3),
        "key_concept": key_concept,
        "year": paper.get("year"),
        "citations": paper.get("citationCount", 0),
        "source_url": _get_url(paper),
    }


def _get_url(paper: dict) -> str:
    ids = paper.get("externalIds") or {}
    if ids.get("ArXiv"):
        return f"https://arxiv.org/abs/{ids['ArXiv']}"
    doi = ids.get("DOI")
    if doi:
        return f"https://doi.org/{doi}"
    pid = paper.get("paperId", "")
    if pid:
        return f"https://www.semanticscholar.org/paper/{pid}"
    return ""


def recommended_actions(evaluations: list[dict]) -> list[str]:
    """Convert expert evaluations to actionable strings for domain FRONTIERs."""
    actions = []
    seen = set()
    for ev in sorted(evaluations, key=lambda e: -(e["isomorphism_score"] + e["relevance"])):
        title = ev["paper_title"]
        if title in seen:
            continue
        seen.add(title)
        domain = ev["domain"]
        iso = ev["isomorphism_score"]
        rel = ev["relevance"]

        if iso >= 0.3:
            actions.append(
                f"ISOMORPHISM-ATLAS candidate [{domain}]: '{title}' "
                f"(iso={iso:.2f}, rel={rel:.2f}) — check {ev.get('source_url', '')}"
            )
        elif rel >= 0.15:
            actions.append(
                f"Domain FRONTIER [{domain}]: add '{title}' as external evidence "
                f"(rel={rel:.2f}) — {ev.get('source_url', '')}"
            )
    return actions


def cmd_query(domain: str, limit: int = 5) -> dict:
    """Fetch papers for a domain from Semantic Scholar."""
    cfg = DOMAIN_QUERIES.get(domain)
    if not cfg:
        return {"error": f"Unknown domain: {domain}. Known: {list(DOMAIN_QUERIES)}"}

    all_papers: list[dict] = []
    seen_titles: set[str] = set()
    for query in cfg["queries"]:
        papers = _query_semantic_scholar(query, limit=limit)
        for p in papers:
            t = p.get("title", "")
            if t and t not in seen_titles:
                seen_titles.add(t)
                p["domains"] = route_paper(p)
                all_papers.append(p)
        if len(all_papers) >= limit:
            break

    return {"domain": domain, "papers": all_papers[:limit], "count": len(all_papers[:limit])}


def cmd_route(papers_json: str) -> dict:
    """Route pre-fetched papers to domain experts."""
    with open(papers_json) as f:
        data = json.load(f)
    papers = data if isinstance(data, list) else data.get("papers", [])
    for p in papers:
        p["domains"] = route_paper(p)
    return {"papers": papers}


def cmd_full(domain: str | None = None, limit: int = 5) -> dict:
    """End-to-end: query → route → evaluate → recommended_actions."""
    target_domains = [domain] if domain else list(DOMAIN_QUERIES.keys())
    all_papers: list[dict] = []
    all_evaluations: list[dict] = []

    for d in target_domains:
        result = cmd_query(d, limit=limit)
        papers = result.get("papers", [])
        all_papers.extend(papers)
        for paper in papers:
            for assigned_domain in (paper.get("domains") or [d]):
                ev = evaluate_paper(paper, assigned_domain)
                all_evaluations.append(ev)

    actions = recommended_actions(all_evaluations)
    return {
        "papers": all_papers,
        "expert_evaluations": all_evaluations,
        "recommended_actions": actions,
    }


def cmd_test() -> dict:
    """Offline validation: route and evaluate synthetic papers."""
    test_papers = [
        {
            "title": "Emergent coordination in distributed multi-agent belief systems",
            "abstract": "We study how agents with local belief updates achieve global coordination "
                        "without central control. Nash equilibrium emerges from repeated belief "
                        "revision under information asymmetry. Sparse communication reduces overhead.",
            "year": 2024, "citationCount": 42, "externalIds": {},
        },
        {
            "title": "Hebbian learning and sparse coding in cortical hierarchies",
            "abstract": "Cortical circuits implement predictive coding via Hebbian plasticity. "
                        "Sparse neural representations compress redundant sensory input. "
                        "Hierarchical feedback enables predictive error minimization.",
            "year": 2023, "citationCount": 118, "externalIds": {},
        },
        {
            "title": "NK fitness landscapes and epistatic constraints on adaptation",
            "abstract": "We analyze how epistasis shapes evolutionary trajectories on NK landscapes. "
                        "Higher epistasis creates more rugged landscapes with local optima. "
                        "Population diversity maintains exploration under selection pressure.",
            "year": 2024, "citationCount": 67, "externalIds": {},
        },
        {
            "title": "WIP limits and queuing theory in software delivery pipelines",
            "abstract": "We apply Little's Law and queuing theory to software delivery. "
                        "WIP limits improve throughput by reducing context switching. "
                        "Bottleneck identification via constraint analysis increases flow efficiency.",
            "year": 2023, "citationCount": 31, "externalIds": {},
        },
    ]

    all_evaluations: list[dict] = []
    for paper in test_papers:
        paper["domains"] = route_paper(paper)
        for domain in paper["domains"]:
            ev = evaluate_paper(paper, domain)
            all_evaluations.append(ev)

    actions = recommended_actions(all_evaluations)
    return {
        "test": True,
        "papers_evaluated": len(test_papers),
        "evaluations": len(all_evaluations),
        "recommended_actions": actions,
        "pass": len(actions) > 0,
        "sample_evaluations": all_evaluations[:4],
    }


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] == "test":
        result = cmd_test()
    elif args[0] == "query":
        if len(args) < 2:
            print("Usage: paper_extractor.py query <domain> [--limit N]", file=sys.stderr)
            sys.exit(1)
        limit = int(args[args.index("--limit") + 1]) if "--limit" in args else 5
        result = cmd_query(args[1], limit=limit)
    elif args[0] == "route":
        if len(args) < 2:
            print("Usage: paper_extractor.py route <papers.json>", file=sys.stderr)
            sys.exit(1)
        result = cmd_route(args[1])
    elif args[0] == "full":
        domain = args[args.index("--domain") + 1] if "--domain" in args else None
        limit = int(args[args.index("--limit") + 1]) if "--limit" in args else 5
        result = cmd_full(domain, limit=limit)
    else:
        print(f"Unknown command: {args[0]}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
