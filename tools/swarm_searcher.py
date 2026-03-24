#!/usr/bin/env python3
"""swarm_searcher.py — Generic knowledge searcher for continuous swarm improvement.

External knowledge is precalculation. Good and bad can be learned from all sources.
Some have more to teach — swarm prioritizes well.

Reads swarm state (frontiers, blind spots, dogma, decayed knowledge) to generate
search queries, fetches from multiple sources (arXiv, Wikipedia, GitHub), scores
results by teaching potential, and outputs actionable recommendations.

Usage:
    python3 tools/swarm_searcher.py                          # auto-mode: read state, search, rank
    python3 tools/swarm_searcher.py --query "stigmergy"      # manual topic
    python3 tools/swarm_searcher.py --source arxiv            # single source
    python3 tools/swarm_searcher.py --source wiki             # single source
    python3 tools/swarm_searcher.py --source github           # single source
    python3 tools/swarm_searcher.py --needs                   # show what swarm needs (no fetch)
    python3 tools/swarm_searcher.py --top 5                   # top N results
    python3 tools/swarm_searcher.py --json                    # machine-readable output
    python3 tools/swarm_searcher.py --out PATH                # save results

Sources:
    arxiv  — academic papers (multi-agent, swarm intelligence, epistemology, etc.)
    wiki   — Wikipedia (concepts, theories, algorithms, named phenomena)
    github — GitHub trending/search (tools, frameworks, implementations)

Design principle: all external knowledge is precalculation that may contain answers
to questions the swarm hasn't asked yet. Prioritize by teaching potential — what
would change the most if the swarm learned it?
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).parent.parent

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class SwarmNeed:
    """Something the swarm needs to learn or improve."""
    category: str          # blind-spot, dogma, frontier, decay, grounding, soul
    id: str                # e.g. "F-COMP1", "PHIL-13", "B20"
    description: str
    urgency: float         # 0.0-1.0 — higher = search first
    search_terms: list[str] = field(default_factory=list)


@dataclass
class SearchResult:
    """A single result from any source."""
    source: str            # arxiv, wiki, github
    title: str
    url: str
    summary: str
    published: str = ""
    authors: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    relevance_score: float = 0.0
    teaching_potential: float = 0.0   # how much swarm could learn
    matched_needs: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Swarm state readers — what does the swarm need?
# ---------------------------------------------------------------------------

def _read_frontiers() -> list[SwarmNeed]:
    """Extract open frontiers as search needs."""
    needs = []
    frontier_path = ROOT / "tasks" / "FRONTIER.md"
    if not frontier_path.exists():
        return needs
    text = frontier_path.read_text(encoding="utf-8")

    # Parse frontier entries
    for m in re.finditer(
        r'\*\*(F[-\w]+)\*\*:?\s*(.+?)(?=\n\s*-\s*\*\*F|\n##|\Z)',
        text, re.DOTALL
    ):
        fid = m.group(1)
        desc = m.group(2).strip()[:300]
        # Skip resolved
        if "Moved to Resolved" in desc or "RESOLVED" in desc[:50]:
            continue
        # Extract key terms
        terms = _extract_search_terms(desc)
        urgency = 0.7 if "Critical" in text[:text.find(fid)] else 0.5
        needs.append(SwarmNeed(
            category="frontier", id=fid, description=desc[:200],
            urgency=urgency, search_terms=terms
        ))
    return needs


def _read_dogma() -> list[SwarmNeed]:
    """Extract ossified beliefs that need external challenge."""
    needs = []
    beliefs_dir = ROOT / "beliefs"
    if not beliefs_dir.exists():
        return needs
    # Read PHILOSOPHY.md for PHIL claims
    phil_path = beliefs_dir / "PHILOSOPHY.md"
    if phil_path.exists():
        text = phil_path.read_text(encoding="utf-8")
        for m in re.finditer(r'(PHIL-\d+)[:\s]+(.+?)(?:\n|$)', text):
            pid = m.group(1)
            desc = m.group(2).strip()[:200]
            terms = _extract_search_terms(desc)
            needs.append(SwarmNeed(
                category="dogma", id=pid, description=desc,
                urgency=0.6, search_terms=terms
            ))
    return needs[:10]  # cap to avoid flooding


def _read_blind_spots() -> list[SwarmNeed]:
    """Read knowledge state for BLIND-SPOT and DECAYED items."""
    needs = []
    ks_path = ROOT / "experiments" / "meta"
    if not ks_path.exists():
        return needs
    # Find latest knowledge-state file
    files = sorted(ks_path.glob("knowledge-state-s*.json"))
    if not files:
        return needs
    try:
        data = json.loads(files[-1].read_text(encoding="utf-8"))
    except Exception:
        return needs

    for item in data.get("items", []):
        state = item.get("state", "")
        if state in ("BLIND-SPOT", "DECAYED"):
            iid = item.get("id", "?")
            desc = item.get("description", item.get("title", ""))[:200]
            terms = _extract_search_terms(desc)
            urgency = 0.8 if state == "BLIND-SPOT" else 0.4
            needs.append(SwarmNeed(
                category="blind-spot" if state == "BLIND-SPOT" else "decay",
                id=iid, description=desc,
                urgency=urgency, search_terms=terms
            ))
    return needs[:15]


def _read_grounding_gaps() -> list[SwarmNeed]:
    """Find high-value lessons with zero external grounding."""
    needs = []
    lesson_dir = ROOT / "memory" / "lessons"
    if not lesson_dir.exists():
        return needs
    # Sample recent lessons, check for external references
    lessons = sorted(lesson_dir.glob("L-*.md"), reverse=True)[:50]
    ext_patterns = [
        re.compile(r'https?://\S+'),
        re.compile(r'arXiv[:\s]\d{4}\.\d+'),
        re.compile(r'\b\w+ et al\.'),
    ]
    for lpath in lessons:
        try:
            text = lpath.read_text(encoding="utf-8")
        except Exception:
            continue
        has_external = any(p.search(text) for p in ext_patterns)
        if not has_external:
            # Extract topic from lesson
            first_line = text.split("\n")[0].strip().lstrip("#").strip()
            lid = lpath.stem
            terms = _extract_search_terms(first_line)
            if terms:
                needs.append(SwarmNeed(
                    category="grounding", id=lid, description=first_line[:200],
                    urgency=0.5, search_terms=terms
                ))
    return needs[:10]


def _extract_search_terms(text: str) -> list[str]:
    """Extract meaningful search terms from a description."""
    # Remove swarm-internal references
    cleaned = re.sub(r'\b(?:L-\d+|P-\d+|B\d+|F-\w+|PHIL-\d+|S\d{3,4}|SIG-\d+)\b', '', text)
    cleaned = re.sub(r'\b(?:tools?/\w+\.py|orient\.py|compact\.py|check\.sh)\b', '', cleaned)
    cleaned = re.sub(r'https?://\S+', '', cleaned)
    # Remove common swarm jargon that won't help external search
    cleaned = re.sub(r'\b(?:swarm|lane|DOMEX|UCB1|dispatch|frontier|lesson|belief)\b', '', cleaned, flags=re.I)
    # Extract remaining meaningful words (3+ chars, not stopwords)
    stopwords = {
        'the', 'and', 'for', 'with', 'that', 'this', 'from', 'are', 'was',
        'has', 'have', 'had', 'not', 'but', 'can', 'how', 'does', 'will',
        'what', 'when', 'where', 'which', 'who', 'why', 'more', 'than',
        'also', 'been', 'each', 'into', 'over', 'most', 'only', 'same',
        'some', 'very', 'just', 'about', 'after', 'before', 'between',
        'through', 'during', 'should', 'could', 'would', 'their', 'there',
        'these', 'those', 'other', 'any', 'all', 'open', 'related', 'test',
        'target', 'session', 'sessions', 'run', 'per', 'first', 'new',
    }
    words = re.findall(r'\b[a-zA-Z]{3,}\b', cleaned)
    terms = []
    seen = set()
    for w in words:
        wl = w.lower()
        if wl not in stopwords and wl not in seen:
            seen.add(wl)
            terms.append(w)
    return terms[:8]


def gather_needs() -> list[SwarmNeed]:
    """Gather all swarm needs, sorted by urgency."""
    needs: list[SwarmNeed] = []
    needs.extend(_read_frontiers())
    needs.extend(_read_dogma())
    needs.extend(_read_blind_spots())
    needs.extend(_read_grounding_gaps())
    needs.sort(key=lambda n: -n.urgency)
    return needs


def needs_to_queries(needs: list[SwarmNeed], max_queries: int = 6) -> list[dict]:
    """Convert swarm needs into search queries for different sources."""
    queries = []
    seen_terms = set()

    for need in needs:
        if len(queries) >= max_queries:
            break
        terms = need.search_terms
        if not terms:
            continue
        # Deduplicate by top terms
        key = tuple(sorted(t.lower() for t in terms[:3]))
        if key in seen_terms:
            continue
        seen_terms.add(key)

        # Generate source-specific queries
        arxiv_q = ' AND '.join(f'all:"{t}"' for t in terms[:3])
        wiki_q = ' '.join(terms[:2])
        github_q = ' '.join(terms[:3])

        queries.append({
            "need_id": need.id,
            "need_category": need.category,
            "urgency": need.urgency,
            "terms": terms[:5],
            "arxiv_query": arxiv_q,
            "wiki_query": wiki_q,
            "github_query": github_q,
        })
    return queries


# ---------------------------------------------------------------------------
# Source fetchers
# ---------------------------------------------------------------------------

ARXIV_API = "https://export.arxiv.org/api/query"
WIKI_API = "https://en.wikipedia.org/w/api.php"
WIKI_REST = "https://en.wikipedia.org/api/rest_v1"
GITHUB_API = "https://api.github.com/search/repositories"


def _http_get(url: str, headers: dict = None, timeout: int = 15) -> str:
    """Safe HTTP GET with timeout."""
    hdrs = {"User-Agent": "SwarmSearcher/1.0 (research)"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        return f"ERROR: {e}"


def search_arxiv(query: str, max_results: int = 5) -> list[SearchResult]:
    """Search arXiv for papers."""
    import xml.etree.ElementTree as ET
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urllib.parse.urlencode(params)}"
    xml_text = _http_get(url, timeout=20)
    if xml_text.startswith("ERROR"):
        return []

    results = []
    try:
        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            title = " ".join((entry.findtext("atom:title", "", ns) or "").split())
            summary = " ".join((entry.findtext("atom:summary", "", ns) or "").split())
            abs_url = (entry.findtext("atom:id", "", ns) or "").strip()
            published = (entry.findtext("atom:published", "", ns) or "").strip()
            authors = [
                " ".join((n.text or "").split())
                for n in entry.findall("atom:author/atom:name", ns)
            ]
            cats = [
                n.attrib.get("term", "")
                for n in entry.findall("atom:category", ns)
            ]
            if not title:
                continue
            results.append(SearchResult(
                source="arxiv",
                title=title,
                url=abs_url,
                summary=summary[:500],
                published=published[:10],
                authors=authors[:5],
                tags=cats[:5],
            ))
    except ET.ParseError:
        pass
    return results


def search_wiki(query: str, max_results: int = 5) -> list[SearchResult]:
    """Search Wikipedia for articles."""
    params = {
        "action": "query",
        "list": "search",
        "srsearch": query,
        "srlimit": max_results,
        "format": "json",
    }
    url = f"{WIKI_API}?{urllib.parse.urlencode(params)}"
    raw = _http_get(url)
    if raw.startswith("ERROR"):
        return []

    results = []
    try:
        data = json.loads(raw)
        for item in data.get("query", {}).get("search", []):
            title = item.get("title", "")
            snippet = re.sub(r'<[^>]+>', '', item.get("snippet", ""))
            wiki_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
            results.append(SearchResult(
                source="wiki",
                title=title,
                url=wiki_url,
                summary=snippet[:500],
            ))
    except (json.JSONDecodeError, KeyError):
        pass

    # Fetch summaries for top results
    for r in results[:3]:
        encoded = urllib.parse.quote(r.title.replace(" ", "_"), safe="")
        summary_url = f"{WIKI_REST}/page/summary/{encoded}"
        raw = _http_get(summary_url, timeout=10)
        if not raw.startswith("ERROR"):
            try:
                sdata = json.loads(raw)
                r.summary = sdata.get("extract", r.summary)[:500]
                r.tags = [sdata.get("description", "")]
            except (json.JSONDecodeError, KeyError):
                pass

    return results


def search_github(query: str, max_results: int = 5) -> list[SearchResult]:
    """Search GitHub for repositories."""
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": max_results,
    }
    url = f"{GITHUB_API}?{urllib.parse.urlencode(params)}"
    raw = _http_get(url, headers={"Accept": "application/vnd.github.v3+json"})
    if raw.startswith("ERROR"):
        return []

    results = []
    try:
        data = json.loads(raw)
        for repo in data.get("items", []):
            results.append(SearchResult(
                source="github",
                title=repo.get("full_name", ""),
                url=repo.get("html_url", ""),
                summary=(repo.get("description", "") or "")[:500],
                published=repo.get("created_at", "")[:10],
                tags=repo.get("topics", [])[:8],
            ))
    except (json.JSONDecodeError, KeyError):
        pass
    return results


SOURCE_MAP = {
    "arxiv": search_arxiv,
    "wiki": search_wiki,
    "github": search_github,
}


# ---------------------------------------------------------------------------
# Scoring — what teaches the swarm the most?
# ---------------------------------------------------------------------------

# Terms that signal high teaching potential
HIGH_TEACH_TERMS = {
    # Fundamental concepts the swarm cares about
    "self-organization", "emergence", "stigmergy", "autopoiesis",
    "epistemology", "falsification", "calibration", "bayesian",
    "multi-agent", "coordination", "consensus", "governance",
    "scaling", "complexity", "adaptation", "evolution",
    "isomorphism", "homomorphism", "category theory", "topology",
    "knowledge", "memory", "retrieval", "compression",
    "safety", "alignment", "robustness", "reliability",
    "recursive", "self-reference", "fixed point", "reflection",
    "game theory", "mechanism design", "incentive", "auction",
    "information theory", "entropy", "mutual information",
    "network", "graph", "percolation", "resilience",
    "optimization", "exploration", "exploitation", "bandit",
    # Real-world grounding
    "empirical", "experiment", "benchmark", "dataset",
    "prediction", "forecasting", "evaluation", "measurement",
    # Things the swarm is weak at (soul extraction: BAD signals)
    "external validation", "real-world", "deployment", "production",
    "user study", "human evaluation", "practical",
}

# Terms that signal low teaching potential (swarm already knows)
LOW_TEACH_TERMS = {
    "prompt engineering", "chatbot", "conversational",
    "fine-tuning", "rlhf", "instruction tuning",
}


def score_result(result: SearchResult, needs: list[SwarmNeed]) -> SearchResult:
    """Score a search result by teaching potential for the swarm."""
    text = f"{result.title} {result.summary} {' '.join(result.tags)}".lower()

    # Base relevance from term matching
    relevance = 0.0
    for term in HIGH_TEACH_TERMS:
        if term in text:
            relevance += 0.15
    for term in LOW_TEACH_TERMS:
        if term in text:
            relevance -= 0.2

    # Match against swarm needs
    matched = []
    for need in needs:
        match_count = sum(1 for t in need.search_terms if t.lower() in text)
        if match_count >= 2:
            matched.append(need.id)
            relevance += 0.2 * need.urgency

    # Source-specific boosts
    if result.source == "arxiv":
        # Academic papers have higher baseline teaching potential
        relevance += 0.1
        # Recency boost
        if result.published and result.published >= "2024":
            relevance += 0.1
    elif result.source == "wiki":
        # Wikipedia is good for concept grounding
        relevance += 0.05
    elif result.source == "github":
        # GitHub is good for implementation patterns
        relevance += 0.05

    # Novelty boost: concepts the swarm hasn't encountered
    novel_terms = {"morphogenesis", "autopoiesis", "stigmergy", "quorum sensing",
                   "swarm robotics", "ant colony", "particle swarm",
                   "cellular automata", "reaction-diffusion", "turing pattern",
                   "social choice", "arrow impossibility", "condorcet",
                   "epistemic democracy", "wisdom of crowds",
                   "information cascade", "herding", "groupthink",
                   "satisficing", "bounded rationality",
                   "annealing", "tempering", "ergodicity",
                   "renormalization", "universality class",
                   "scale-free", "power law", "preferential attachment"}
    for term in novel_terms:
        if term in text:
            relevance += 0.2  # novelty is valuable

    result.relevance_score = min(max(relevance, 0.0), 1.0)
    result.teaching_potential = result.relevance_score  # could be separated later
    result.matched_needs = matched
    return result


# ---------------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------------

def run_search(
    *,
    manual_query: Optional[str] = None,
    sources: list[str] = None,
    max_per_source: int = 5,
    top_n: int = 10,
) -> dict:
    """Run the full search pipeline."""
    if sources is None:
        sources = ["arxiv", "wiki", "github"]

    # Step 1: Gather swarm needs
    needs = gather_needs()

    # Step 2: Generate queries
    if manual_query:
        queries = [{
            "need_id": "manual",
            "need_category": "manual",
            "urgency": 1.0,
            "terms": manual_query.split()[:5],
            "arxiv_query": f'all:"{manual_query}"',
            "wiki_query": manual_query,
            "github_query": manual_query,
        }]
    else:
        queries = needs_to_queries(needs, max_queries=6)

    if not queries:
        return {
            "status": "no_queries",
            "message": "Could not generate search queries from swarm state",
            "needs_count": len(needs),
        }

    # Step 3: Search each source
    all_results: list[SearchResult] = []
    errors: list[str] = []

    for qi, q in enumerate(queries):
        for source in sources:
            if source not in SOURCE_MAP:
                continue
            query_text = q.get(f"{source}_query", q["terms"][0])
            try:
                results = SOURCE_MAP[source](query_text, max_results=max_per_source)
                all_results.extend(results)
            except Exception as e:
                errors.append(f"{source}/{q['need_id']}: {e}")
            # Rate limit between API calls
            if qi < len(queries) - 1 or source != sources[-1]:
                time.sleep(0.5)

    # Step 4: Score and rank
    for r in all_results:
        score_result(r, needs)

    # Deduplicate by URL
    seen_urls: set[str] = set()
    unique_results: list[SearchResult] = []
    for r in all_results:
        if r.url not in seen_urls:
            seen_urls.add(r.url)
            unique_results.append(r)

    # Sort by teaching potential
    unique_results.sort(key=lambda r: -r.teaching_potential)
    top_results = unique_results[:top_n]

    return {
        "status": "ok",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z",
        "needs_analyzed": len(needs),
        "queries_generated": len(queries),
        "sources_searched": sources,
        "total_results": len(unique_results),
        "top_results": [asdict(r) for r in top_results],
        "queries": queries,
        "needs_summary": [
            {"id": n.id, "category": n.category, "urgency": n.urgency,
             "description": n.description[:100]}
            for n in needs[:10]
        ],
        "errors": errors,
    }


def format_text(payload: dict) -> str:
    """Format results as readable text."""
    lines = []
    lines.append(f"=== SWARM SEARCHER ===")
    lines.append(f"Generated: {payload.get('generated_at', 'N/A')}")
    lines.append(f"Needs analyzed: {payload.get('needs_analyzed', 0)}")
    lines.append(f"Queries: {payload.get('queries_generated', 0)}")
    lines.append(f"Sources: {', '.join(payload.get('sources_searched', []))}")
    lines.append(f"Total results: {payload.get('total_results', 0)}")
    lines.append("")

    # Show needs
    needs = payload.get("needs_summary", [])
    if needs:
        lines.append("--- Swarm needs (top 10) ---")
        for n in needs:
            lines.append(f"  [{n['category']:<12}] {n['id']:<12} urgency={n['urgency']:.1f}  {n['description'][:80]}")
        lines.append("")

    # Show queries
    queries = payload.get("queries", [])
    if queries:
        lines.append("--- Search queries ---")
        for q in queries:
            lines.append(f"  {q['need_id']}: {' '.join(q['terms'][:4])}")
        lines.append("")

    # Show results
    results = payload.get("top_results", [])
    if results:
        lines.append("--- Top results (by teaching potential) ---")
        for i, r in enumerate(results, 1):
            teach = r.get("teaching_potential", 0)
            source = r.get("source", "?")
            title = r.get("title", "?")[:80]
            url = r.get("url", "")
            matched = r.get("matched_needs", [])

            lines.append(f"  {i:2d}. [{source:<6}] teach={teach:.2f}  {title}")
            lines.append(f"      {url}")
            if r.get("summary"):
                lines.append(f"      {r['summary'][:120]}")
            if matched:
                lines.append(f"      matches: {', '.join(matched)}")
            lines.append("")
    else:
        lines.append("No results found.")

    # Errors
    errors = payload.get("errors", [])
    if errors:
        lines.append("--- Errors ---")
        for e in errors:
            lines.append(f"  ! {e}")

    # Recommendations
    if results:
        lines.append("--- Recommendations ---")
        lines.append("  For each high-scoring result:")
        lines.append("  1. Read the full source (wiki_swarm.py for wiki, arxiv_search.py for papers)")
        lines.append("  2. Extract falsifiable claims or transferable methods")
        lines.append("  3. Map to existing frontier/principle/belief IDs")
        lines.append("  4. Open a DOMEX lane if teaching potential > 0.5")
        lines.append("  5. Log what was learned — even 'nothing useful' is data")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--query", "-q", type=str, default=None,
                        help="Manual search query (overrides auto-generation)")
    parser.add_argument("--source", "-s", type=str, default=None,
                        choices=["arxiv", "wiki", "github"],
                        help="Search single source (default: all)")
    parser.add_argument("--needs", action="store_true",
                        help="Show swarm needs only (no fetching)")
    parser.add_argument("--top", type=int, default=10,
                        help="Number of top results to show")
    parser.add_argument("--max-per-source", type=int, default=5,
                        help="Max results per source per query")
    parser.add_argument("--json", action="store_true",
                        help="Output JSON instead of text")
    parser.add_argument("--out", type=Path, default=None,
                        help="Save results to file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.needs:
        needs = gather_needs()
        if args.json:
            print(json.dumps([asdict(n) for n in needs], indent=2))
        else:
            print(f"=== SWARM NEEDS ({len(needs)} total) ===\n")
            for n in needs:
                print(f"  [{n.category:<12}] {n.id:<12} urgency={n.urgency:.1f}")
                print(f"    {n.description[:100]}")
                print(f"    terms: {', '.join(n.search_terms[:5])}")
                print()
        return 0

    sources = [args.source] if args.source else ["arxiv", "wiki", "github"]

    payload = run_search(
        manual_query=args.query,
        sources=sources,
        max_per_source=args.max_per_source,
        top_n=args.top,
    )

    if args.json:
        output = json.dumps(payload, indent=2)
    else:
        output = format_text(payload)

    print(output)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(payload, indent=2) + "\n" if args.json
            else output + "\n",
            encoding="utf-8"
        )
        print(f"\nSaved to: {args.out}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
