#!/usr/bin/env python3
"""F-IS5 arXiv intake harness: convert paper search results into swarm lanes."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import URLError
import xml.etree.ElementTree as ET
import time


ARXIV_API = "https://export.arxiv.org/api/query"
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

THEME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "protocol-orchestration": (
        "protocol",
        "orchestration",
        "coordination",
        "topology",
        "workflow",
        "planner",
        "routing",
    ),
    "memory-knowledge": (
        "memory",
        "context",
        "retrieval",
        "knowledge",
        "state",
        "blackboard",
        "trace",
    ),
    "safety-reliability": (
        "safety",
        "reliability",
        "alignment",
        "robust",
        "security",
        "trust",
        "deception",
        "byzantine",
    ),
    "evaluation-scaling": (
        "benchmark",
        "evaluation",
        "dataset",
        "metric",
        "analysis",
        "scaling",
        "survey",
        "ablation",
    ),
    "tool-use-execution": (
        "tool",
        "execution",
        "code",
        "agentic",
        "api",
        "planning",
        "automation",
    ),
}

THEME_RATIONALE: dict[str, str] = {
    "protocol-orchestration": "Coordination mechanics and topology design claims.",
    "memory-knowledge": "State persistence, context control, and memory abstractions.",
    "safety-reliability": "Failure modes, trust boundaries, and robustness checks.",
    "evaluation-scaling": "Quantitative tests, benchmarks, and scaling behavior.",
    "tool-use-execution": "Executable agent workflows and integration with tools.",
    "misc": "Relevant but not strongly classifiable by keyword signal.",
}


@dataclass(frozen=True)
class ArxivPaper:
    arxiv_id: str
    title: str
    summary: str
    published: str
    updated: str
    authors: tuple[str, ...]
    categories: tuple[str, ...]
    abs_url: str


def _collapse_ws(text: str | None) -> str:
    return " ".join((text or "").split())


def _paper_id(abs_url: str) -> str:
    return abs_url.rstrip("/").rsplit("/", 1)[-1]


def parse_feed(xml_text: str) -> list[ArxivPaper]:
    root = ET.fromstring(xml_text)
    papers: list[ArxivPaper] = []
    for entry in root.findall("atom:entry", ATOM_NS):
        abs_url = _collapse_ws(entry.findtext("atom:id", default="", namespaces=ATOM_NS))
        title = _collapse_ws(
            entry.findtext("atom:title", default="", namespaces=ATOM_NS)
        )
        summary = _collapse_ws(
            entry.findtext("atom:summary", default="", namespaces=ATOM_NS)
        )
        published = _collapse_ws(
            entry.findtext("atom:published", default="", namespaces=ATOM_NS)
        )
        updated = _collapse_ws(
            entry.findtext("atom:updated", default="", namespaces=ATOM_NS)
        )
        authors = tuple(
            _collapse_ws(node.text)
            for node in entry.findall("atom:author/atom:name", ATOM_NS)
            if _collapse_ws(node.text)
        )
        categories = tuple(
            node.attrib.get("term", "").strip()
            for node in entry.findall("atom:category", ATOM_NS)
            if node.attrib.get("term", "").strip()
        )
        if not abs_url or not title:
            continue
        papers.append(
            ArxivPaper(
                arxiv_id=_paper_id(abs_url),
                title=title,
                summary=summary,
                published=published,
                updated=updated,
                authors=authors,
                categories=categories,
                abs_url=abs_url,
            )
        )
    return papers


def fetch_arxiv(*, query: str, max_results: int, timeout_sec: int = 20) -> list[ArxivPaper]:
    params = {
        "search_query": query,
        "start": 0,
        "max_results": max(1, max_results),
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = f"{ARXIV_API}?{urlencode(params)}"
    request = Request(url, headers={"User-Agent": "swarm-f-is5-arxiv/1.0"})
    with urlopen(request, timeout=timeout_sec) as response:
        xml_text = response.read().decode("utf-8", errors="replace")
    return parse_feed(xml_text)


def fetch_arxiv_with_retry(
    *,
    query: str,
    max_results: int,
    timeout_sec: int = 20,
    attempts: int = 3,
) -> list[ArxivPaper]:
    attempts = max(1, attempts)
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fetch_arxiv(
                query=query,
                max_results=max_results,
                timeout_sec=timeout_sec,
            )
        except (URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt >= attempts:
                break
            time.sleep(min(3, attempt))
    assert last_error is not None
    raise RuntimeError(f"arXiv fetch failed after {attempts} attempt(s): {last_error}")


def score_theme(paper: ArxivPaper) -> tuple[str, int]:
    text = (
        f"{paper.title} {paper.summary} {' '.join(paper.categories)}"
    ).lower()
    best_theme = "misc"
    best_score = 0
    for theme, keywords in THEME_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text)
        if score > best_score:
            best_score = score
            best_theme = theme
    return best_theme, best_score


def build_lane_plan(
    papers: list[ArxivPaper], *, lane_size: int
) -> tuple[list[dict], dict[str, str]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    paper_theme: dict[str, str] = {}
    for paper in papers:
        theme, score = score_theme(paper)
        grouped[theme].append({"paper": paper, "score": score})
        paper_theme[paper.arxiv_id] = theme

    lanes: list[dict] = []
    lane_size = max(1, lane_size)
    ordered_groups = sorted(
        grouped.items(), key=lambda item: (-len(item[1]), item[0])
    )
    for index, (theme, rows) in enumerate(ordered_groups, start=1):
        rows.sort(key=lambda row: (-row["score"], row["paper"].published))
        selected = [row["paper"] for row in rows[:lane_size]]
        backlog = [row["paper"] for row in rows[lane_size:]]
        lanes.append(
            {
                "lane_id": f"ARX-{index:02d}",
                "theme": theme,
                "rationale": THEME_RATIONALE.get(theme, THEME_RATIONALE["misc"]),
                "paper_ids": [paper.arxiv_id for paper in selected],
                "backlog_paper_ids": [paper.arxiv_id for paper in backlog],
                "selected_count": len(selected),
                "backlog_count": len(backlog),
                "theme_total_count": len(rows),
                "task_template": [
                    "Extract 3 falsifiable claims with evidence location.",
                    "Map each claim to existing frontier/principle IDs.",
                    "Propose one experiment or challenge artifact for merge.",
                ],
            }
        )
    return lanes, paper_theme


def build_payload(
    *,
    query: str,
    max_results: int,
    lane_size: int,
    papers: list[ArxivPaper],
) -> dict:
    lane_plan, paper_theme = build_lane_plan(papers, lane_size=lane_size)
    if papers:
        published_values = sorted(paper.published for paper in papers if paper.published)
        oldest = published_values[0] if published_values else None
        newest = published_values[-1] if published_values else None
    else:
        newest = None
        oldest = None
    selected_count = sum(len(lane["paper_ids"]) for lane in lane_plan)
    backlog_count = sum(len(lane["backlog_paper_ids"]) for lane in lane_plan)

    return {
        "experiment": "F-IS5",
        "title": "arXiv swarmable intake pack",
        "query": query,
        "max_results": max_results,
        "retrieved_count": len(papers),
        "date_window": {"newest_published": newest, "oldest_published": oldest},
        "papers": [
            {
                "arxiv_id": paper.arxiv_id,
                "title": paper.title,
                "published": paper.published,
                "updated": paper.updated,
                "authors": list(paper.authors),
                "categories": list(paper.categories),
                "theme": paper_theme.get(paper.arxiv_id, "misc"),
                "summary_preview": (paper.summary[:300] + "...")
                if len(paper.summary) > 300
                else paper.summary,
                "abs_url": paper.abs_url,
            }
            for paper in papers
        ],
        "lane_plan": lane_plan,
        "lane_coverage": {
            "selected_count": selected_count,
            "backlog_count": backlog_count,
            "selected_ratio": (selected_count / len(papers)) if papers else 0.0,
        },
        "interpretation": (
            "This artifact turns ad-hoc paper drops into lane-ready swarm work: "
            "papers are grouped by theme with a fixed task template for parallel distill-and-merge."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--query",
        default='all:"multi-agent" AND all:"LLM" AND all:"coordination"',
        help="arXiv API search query.",
    )
    parser.add_argument("--max-results", type=int, default=24)
    parser.add_argument("--lane-size", type=int, default=5)
    parser.add_argument("--retry-attempts", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    papers = fetch_arxiv_with_retry(
        query=args.query,
        max_results=args.max_results,
        attempts=args.retry_attempts,
    )
    payload = build_payload(
        query=args.query,
        max_results=max(1, args.max_results),
        lane_size=args.lane_size,
        papers=papers,
    )
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote {args.out}")
    print(
        "retrieved=",
        payload["retrieved_count"],
        "lanes=",
        len(payload["lane_plan"]),
        "newest=",
        payload["date_window"]["newest_published"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
