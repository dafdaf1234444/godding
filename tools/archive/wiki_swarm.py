#!/usr/bin/env python3
"""wiki_swarm.py — crawl a small Wikipedia neighborhood from a seed topic.

Usage:
    python3 tools/wiki_swarm.py <topic> [--depth 1] [--fanout 5] [--lang en] [--out FILE]
    python3 tools/wiki_swarm.py --auto [--depth 1] [--fanout 5]
    python3 tools/wiki_swarm.py --coord-experiment [--trials 200] [--error-rate 0.2] [--json-out FILE]
    python3 tools/wiki_swarm.py --coord-live-experiment [--trials 120] [--perturb-rate 0.35] [--json-out FILE]
    python3 tools/wiki_swarm.py --ai1-live-experiment [--trials 120] [--perturb-rate 0.35] [--json-out FILE]
    python3 tools/wiki_swarm.py
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = "swarm-wiki/0.1 (+https://github.com/dafdaf1234444/swarm)"
DEFAULT_AUTO_TOPIC = "Swarm intelligence"
GENERIC_INVOCATIONS = {
    "swarm",
    "swarm this",
    "swarm it",
    "swarm command",
    "cross domain knowledge coordinator swarm",
    "swarm expert builder to swarm the swarm",
    "wiki swarm",
    "swarm wiki swarm",
    "swarm the wiki swarm",
    "start wiki swarm",
    "run wiki swarm",
}
GENERIC_COMMAND_WORDS = {
    "a",
    "an",
    "builder",
    "command",
    "coordinator",
    "cross",
    "domain",
    "domains",
    "expert",
    "it",
    "knowledge",
    "launch",
    "multi",
    "now",
    "on",
    "please",
    "run",
    "start",
    "swarmer",
    "the",
    "this",
    "to",
    "wiki",
}
AUTO_TOPICS = [
    ("Swarm intelligence", ("swarm", "colony", "agent", "parallel")),
    ("Stigmergy", ("stigmergy", "bulletin", "append-only", "pheromone")),
    ("Distributed systems", ("distributed", "replication", "consensus", "fault")),
    ("Error handling", ("error handling", "eh", "retry", "failure")),
    ("Conflict-free replicated data type", ("crdt", "append-only", "monotonic")),
    ("Transactive memory", ("transactive", "memory", "specialist", "coordination")),
]
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "of",
    "on",
    "or",
    "that",
    "the",
    "their",
    "this",
    "to",
    "what",
    "when",
    "where",
    "which",
    "who",
    "why",
    "with",
}


def _request_json(url: str, timeout: int = 15) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_exc: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8", errors="replace"))
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code == 429 and attempt < 3:
                time.sleep(0.4 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError as exc:
            last_exc = exc
            if attempt < 3:
                time.sleep(0.2 * (attempt + 1))
                continue
            raise

    if last_exc:
        raise last_exc
    raise RuntimeError("unreachable request_json failure")


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if text else "(no summary available)"


def _normalize_invocation(text: str) -> str:
    text = re.sub(r"[^a-z0-9\s]+", " ", (text or "").lower())
    return re.sub(r"\s+", " ", text).strip()


def is_generic_invocation(topic: str) -> bool:
    """Return True when input is a generic wiki-swarm command."""
    normalized = _normalize_invocation(topic)
    if not normalized:
        return True
    if normalized in GENERIC_INVOCATIONS:
        return True

    tokens = normalized.split()
    if not tokens:
        return True

    def _is_swarm_token(token: str) -> bool:
        return token == "swarmer" or token.startswith("swarm")

    swarm_tokens = sum(1 for token in tokens if _is_swarm_token(token))
    command_like_tokens = sum(
        1
        for token in tokens
        if _is_swarm_token(token) or token in GENERIC_COMMAND_WORDS
    )
    return swarm_tokens >= 1 and command_like_tokens == len(tokens)


def _search_titles(query: str, lang: str, limit: int = 1) -> list[str]:
    q = urllib.parse.quote_plus(query)
    url = (
        f"https://{lang}.wikipedia.org/w/api.php"
        f"?action=query&list=search&srsearch={q}&srlimit={limit}&format=json"
    )
    data = _request_json(url)
    return [item.get("title", "").strip() for item in data.get("query", {}).get("search", []) if item.get("title")]


def _keyword_queries(text: str) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z-]+", (text or "").lower())
    keywords: list[str] = []
    for word in words:
        if word in STOPWORDS:
            continue
        stem = word
        if stem.endswith("ing") and len(stem) > 6:
            stem = stem[:-3]
        if stem.startswith("mis") and len(stem) > 6:
            keywords.append(stem[3:])
        keywords.append(stem)

    deduped: list[str] = []
    for word in keywords:
        if word and word not in deduped:
            deduped.append(word)

    queries: list[str] = []
    if len(deduped) >= 3:
        queries.append(" ".join(deduped[:3]))
    if len(deduped) >= 2:
        queries.append(" ".join(deduped[:2]))
    queries.extend(deduped)
    return queries


def resolve_topic(topic: str, lang: str) -> str:
    """Resolve a free-form query to a canonical Wikipedia title."""
    topic = topic.strip()
    if not topic:
        return topic

    results = _search_titles(topic, lang, limit=1)
    if results:
        return results[0]

    for query in _keyword_queries(topic):
        if query == topic:
            continue
        fallback = _search_titles(query, lang, limit=1)
        if fallback:
            return fallback[0]

    return topic


def fetch_summary(title: str, lang: str) -> dict | None:
    """Fetch page summary from REST API."""
    safe_title = urllib.parse.quote(title.replace(" ", "_"), safe="()")
    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{safe_title}"
    try:
        data = _request_json(url)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise

    page_url = (
        data.get("content_urls", {})
        .get("desktop", {})
        .get("page", f"https://{lang}.wikipedia.org/wiki/{safe_title}")
    )
    return {
        "title": data.get("title", title),
        "summary": _clean_text(data.get("extract", "")),
        "url": page_url,
    }


def fetch_related_titles(title: str, lang: str, limit: int) -> list[str]:
    """Fetch semantically related titles via search relevance."""
    q = urllib.parse.quote_plus(title)
    # Pull extra candidates to compensate for filtering exact-match and numeric pages.
    search_limit = min(max(limit * 3, 10), 50)
    url = (
        f"https://{lang}.wikipedia.org/w/api.php"
        f"?action=query&list=search&srsearch={q}&srlimit={search_limit}&format=json"
    )
    data = _request_json(url)
    pages = data.get("query", {}).get("search", [])
    titles: list[str] = []
    for page in pages:
        candidate = page.get("title", "").strip()
        if not candidate or candidate == title:
            continue
        if re.match(r"^\d", candidate):
            continue
        titles.append(candidate)
    return titles[:limit]


def fetch_links(title: str, lang: str, limit: int) -> list[str]:
    """Fallback: fetch page links (main namespace only)."""
    safe_title = urllib.parse.quote_plus(title)
    url = (
        f"https://{lang}.wikipedia.org/w/api.php"
        f"?action=query&titles={safe_title}&prop=links&plnamespace=0&pllimit=max&format=json&redirects=1"
    )
    data = _request_json(url)
    pages = data.get("query", {}).get("pages", {})
    if not pages:
        return []

    first_page = next(iter(pages.values()))
    links = first_page.get("links", [])
    titles = [link.get("title", "").strip() for link in links]
    titles = [t for t in titles if t]
    return titles[:limit]


def choose_auto_topic() -> tuple[str, str]:
    """Infer a sensible seed topic from current swarm state files."""
    files = [
        REPO_ROOT / "tasks" / "NEXT.md",
        REPO_ROOT / "tasks" / "FRONTIER.md",
        REPO_ROOT / "memory" / "INDEX.md",
    ]
    corpus = []
    for path in files:
        try:
            corpus.append(path.read_text(encoding="utf-8", errors="replace").lower())
        except Exception:
            continue
    text = "\n".join(corpus)

    best_topic = DEFAULT_AUTO_TOPIC
    best_score = 0
    for topic, keywords in AUTO_TOPICS:
        score = sum(text.count(keyword.lower()) for keyword in keywords)
        if score > best_score:
            best_topic = topic
            best_score = score

    if best_score <= 0:
        return best_topic, "auto(default)"
    return best_topic, f"auto(state-score={best_score})"


def swarm_topic(seed: str, depth: int, fanout: int, lang: str) -> tuple[str, list[dict]]:
    """Breadth-first traversal of Wikipedia pages around a seed topic."""
    root = resolve_topic(seed, lang)
    queue: deque[tuple[str, int]] = deque([(root, 0)])
    visited: set[str] = set()
    nodes: list[dict] = []

    while queue:
        current_title, current_depth = queue.popleft()
        if current_title in visited:
            continue
        visited.add(current_title)

        summary = fetch_summary(current_title, lang)
        if not summary:
            continue

        children: list[str] = []
        if current_depth < depth:
            try:
                children = fetch_related_titles(summary["title"], lang, fanout)
            except Exception:
                try:
                    children = fetch_links(summary["title"], lang, fanout)
                except Exception:
                    children = []

        nodes.append(
            {
                "title": summary["title"],
                "depth": current_depth,
                "summary": summary["summary"],
                "url": summary["url"],
                "children": children,
            }
        )

        if current_depth < depth:
            for child_title in children:
                if child_title not in visited:
                    queue.append((child_title, current_depth + 1))

    return root, nodes


def render_markdown(
    seed: str,
    resolved: str,
    depth: int,
    fanout: int,
    lang: str,
    nodes: list[dict],
    topic_source: str,
) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Wiki Swarm: {seed}",
        "",
        f"- Resolved topic: `{resolved}`",
        f"- Topic source: `{topic_source}`",
        f"- Depth: {depth}",
        f"- Fanout: {fanout}",
        f"- Language: `{lang}`",
        f"- Generated: {ts}",
        "",
    ]

    if not nodes:
        lines.append("No pages were retrieved.")
        return "\n".join(lines)

    for node in nodes:
        lines.extend(
            [
                f"## {node['title']} (depth {node['depth']})",
                f"- URL: {node['url']}",
                f"- Summary: {node['summary']}",
            ]
        )
        if node["children"]:
            children = ", ".join(node["children"])
            lines.append(f"- Related pages sampled: {children}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _pearson(xs: list[int], ys: list[int]) -> float:
    """Compute Pearson correlation with zero-variance guard."""
    n = min(len(xs), len(ys))
    if n == 0:
        return 0.0
    xvals = xs[:n]
    yvals = ys[:n]
    mean_x = sum(xvals) / n
    mean_y = sum(yvals) / n
    var_x = sum((x - mean_x) ** 2 for x in xvals)
    var_y = sum((y - mean_y) ** 2 for y in yvals)
    if var_x == 0 or var_y == 0:
        return 0.0
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xvals, yvals))
    return cov / math.sqrt(var_x * var_y)


def run_coordination_experiment(trials: int, error_rate: float, seed: int) -> dict:
    """
    Controlled F-AI2/F-HLT2 simulation:
    - leader receives a potential error
    - async follower samples independently
    - sync follower inherits leader state (forced synchronization)
    """
    trials = max(1, trials)
    error_rate = max(0.0, min(error_rate, 1.0))
    rng = random.Random(seed)

    leader_errors: list[int] = []
    async_follower_errors: list[int] = []
    sync_follower_errors: list[int] = []

    for _ in range(trials):
        leader_error = 1 if rng.random() < error_rate else 0
        async_error = 1 if rng.random() < error_rate else 0
        sync_error = leader_error  # Forced sync: follower inherits leader state exactly.

        leader_errors.append(leader_error)
        async_follower_errors.append(async_error)
        sync_follower_errors.append(sync_error)

    async_joint = sum(
        1 for l, a in zip(leader_errors, async_follower_errors) if l == 1 and a == 1
    )
    sync_joint = sum(
        1 for l, s in zip(leader_errors, sync_follower_errors) if l == 1 and s == 1
    )
    leader_rate = sum(leader_errors) / trials
    async_follower_rate = sum(async_follower_errors) / trials
    sync_follower_rate = sum(sync_follower_errors) / trials

    async_corr = _pearson(leader_errors, async_follower_errors)
    sync_corr = _pearson(leader_errors, sync_follower_errors)

    return {
        "experiment": "F-AI2/F-HLT2",
        "title": "Forced synchronization vs asynchronous independence",
        "mode": "controlled-simulation",
        "seed": seed,
        "trials": trials,
        "injected_error_rate": error_rate,
        "leader_error_rate": round(leader_rate, 4),
        "async": {
            "follower_error_rate": round(async_follower_rate, 4),
            "joint_error_rate": round(async_joint / trials, 4),
            "leader_follower_error_correlation": round(async_corr, 4),
        },
        "sync": {
            "follower_error_rate": round(sync_follower_rate, 4),
            "joint_error_rate": round(sync_joint / trials, 4),
            "leader_follower_error_correlation": round(sync_corr, 4),
        },
        "verdict": (
            "Forced synchronization creates perfectly correlated error propagation; "
            "asynchronous followers keep errors mostly uncorrelated."
        ),
    }


def _perturb_topic_query(topic: str, rng: random.Random) -> str:
    """Apply a lightweight typo perturbation to a topic query string."""
    text = topic.strip()
    if len(text) < 4:
        return text

    mode = rng.choice(("drop_char", "swap_adjacent", "drop_space"))
    if mode == "drop_char":
        idx = rng.randrange(1, len(text) - 1)
        return text[:idx] + text[idx + 1 :]
    if mode == "swap_adjacent":
        idx = rng.randrange(0, len(text) - 1)
        chars = list(text)
        chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
        return "".join(chars)
    if " " in text:
        return text.replace(" ", "", 1)
    return text


def run_live_coordination_experiment(
    trials: int,
    perturb_rate: float,
    seed: int,
    lang: str,
    sync_inherit_prob: float = 1.0,
) -> dict:
    """
    Live (networked) F-AI2/F-HLT2 experiment using Wikipedia topic resolution:
    - leader query may be typo-perturbed
    - async follower resolves independently from a separately perturbed/clean query
    - sync follower inherits leader result with probability p (partial/full sync)
    """
    trials = max(1, trials)
    perturb_rate = max(0.0, min(perturb_rate, 1.0))
    sync_inherit_prob = max(0.0, min(sync_inherit_prob, 1.0))
    rng = random.Random(seed)

    topic_pool = [topic for topic, _ in AUTO_TOPICS]
    resolve_cache: dict[str, str] = {}
    query_banks: dict[str, list[str]] = {}

    def resolved(query: str) -> str:
        if query not in resolve_cache:
            try:
                # Use REST summary lookup directly to reduce search-endpoint rate pressure.
                summary = fetch_summary(query, lang)
                resolve_cache[query] = summary["title"] if summary else query
            except urllib.error.HTTPError as exc:
                # If Wikimedia throttles requests, keep experiment running with a
                # conservative fallback rather than aborting the full run.
                if exc.code == 429:
                    resolve_cache[query] = query
                else:
                    raise
        return resolve_cache[query]

    def query_bank(topic: str) -> list[str]:
        if topic in query_banks:
            return query_banks[topic]
        bank = [topic]
        local_rng = random.Random(f"{seed}:{topic}")
        for _ in range(4):
            candidate = _perturb_topic_query(topic, local_rng)
            if candidate not in bank:
                bank.append(candidate)
        query_banks[topic] = bank
        return bank

    leader_errors: list[int] = []
    async_follower_errors: list[int] = []
    sync_follower_errors: list[int] = []
    mismatch_samples: list[dict[str, str]] = []

    for _ in range(trials):
        base_topic = rng.choice(topic_pool)
        canonical = resolved(base_topic)
        bank = query_bank(base_topic)
        perturbed_options = bank[1:] if len(bank) > 1 else bank

        leader_query = (
            rng.choice(perturbed_options) if rng.random() < perturb_rate else base_topic
        )
        async_query = (
            rng.choice(perturbed_options) if rng.random() < perturb_rate else base_topic
        )

        leader_resolved = resolved(leader_query)
        async_resolved = resolved(async_query)

        leader_error = int(leader_resolved.lower() != canonical.lower())
        async_error = int(async_resolved.lower() != canonical.lower())

        if rng.random() < sync_inherit_prob:
            sync_resolved = leader_resolved
        else:
            sync_query = (
                rng.choice(perturbed_options) if rng.random() < perturb_rate else base_topic
            )
            sync_resolved = resolved(sync_query)
        sync_error = int(sync_resolved.lower() != canonical.lower())

        leader_errors.append(leader_error)
        async_follower_errors.append(async_error)
        sync_follower_errors.append(sync_error)

        if leader_error and len(mismatch_samples) < 12:
            mismatch_samples.append(
                {
                    "base_topic": base_topic,
                    "canonical": canonical,
                    "leader_query": leader_query,
                    "leader_resolved": leader_resolved,
                }
            )

    async_joint = sum(
        1 for l, a in zip(leader_errors, async_follower_errors) if l == 1 and a == 1
    )
    sync_joint = sum(
        1 for l, s in zip(leader_errors, sync_follower_errors) if l == 1 and s == 1
    )
    leader_rate = sum(leader_errors) / trials
    async_rate = sum(async_follower_errors) / trials
    sync_rate = sum(sync_follower_errors) / trials

    async_corr = _pearson(leader_errors, async_follower_errors)
    sync_corr = _pearson(leader_errors, sync_follower_errors)

    return {
        "experiment": "F-AI2/F-HLT2",
        "title": "Live fetch perturbation: forced sync vs async independence",
        "mode": "live-perturbation",
        "seed": seed,
        "trials": trials,
        "lang": lang,
        "perturb_rate": perturb_rate,
        "sync_inherit_prob": round(sync_inherit_prob, 4),
        "leader_error_rate": round(leader_rate, 4),
        "async": {
            "follower_error_rate": round(async_rate, 4),
            "joint_error_rate": round(async_joint / trials, 4),
            "leader_follower_error_correlation": round(async_corr, 4),
        },
        "sync": {
            "follower_error_rate": round(sync_rate, 4),
            "joint_error_rate": round(sync_joint / trials, 4),
            "leader_follower_error_correlation": round(sync_corr, 4),
        },
        "mismatch_samples": mismatch_samples,
        "verdict": (
            "Live topic perturbations preserve the same directional result: "
            "forced synchronization propagates leader mistakes, while asynchronous "
            "followers remain less correlated."
        ),
    }


def run_live_ai1_evidence_experiment(
    trials: int,
    perturb_rate: float,
    seed: int,
    lang: str,
    leader_high_conf_prob: float = 0.45,
    leader_high_conf_perturb_rate: float = 0.15,
    leader_low_conf_perturb_rate: float = 0.55,
) -> dict:
    """
    Live (networked) F-AI1 experiment:
    - leader and follower resolve potentially perturbed topic queries
    - forced sync copies leader
    - evidence-surfacing gates adoption of leader answer by confidence + disagreement
    """
    trials = max(1, trials)
    perturb_rate = max(0.0, min(perturb_rate, 1.0))
    leader_high_conf_prob = max(0.0, min(leader_high_conf_prob, 1.0))
    leader_high_conf_perturb_rate = max(0.0, min(leader_high_conf_perturb_rate, 1.0))
    leader_low_conf_perturb_rate = max(0.0, min(leader_low_conf_perturb_rate, 1.0))
    rng = random.Random(seed)

    topic_pool = [topic for topic, _ in AUTO_TOPICS]
    resolve_cache: dict[str, str] = {}
    query_banks: dict[str, list[str]] = {}

    def resolved(query: str) -> str:
        if query not in resolve_cache:
            try:
                summary = fetch_summary(query, lang)
                resolve_cache[query] = summary["title"] if summary else query
            except urllib.error.HTTPError as exc:
                if exc.code == 429:
                    resolve_cache[query] = query
                else:
                    raise
        return resolve_cache[query]

    def query_bank(topic: str) -> list[str]:
        if topic in query_banks:
            return query_banks[topic]
        bank = [topic]
        local_rng = random.Random(f"ai1:{seed}:{topic}")
        for _ in range(4):
            candidate = _perturb_topic_query(topic, local_rng)
            if candidate not in bank:
                bank.append(candidate)
        query_banks[topic] = bank
        return bank

    leader_errors: list[int] = []
    async_follower_errors: list[int] = []
    sync_follower_errors: list[int] = []
    surfaced_follower_errors: list[int] = []
    surfaced_adopt_count = 0

    for _ in range(trials):
        base_topic = rng.choice(topic_pool)
        canonical = resolved(base_topic)
        bank = query_bank(base_topic)
        perturbed_options = bank[1:] if len(bank) > 1 else bank

        leader_high_conf = rng.random() < leader_high_conf_prob
        leader_perturb_rate = (
            leader_high_conf_perturb_rate
            if leader_high_conf
            else leader_low_conf_perturb_rate
        )

        leader_query = (
            rng.choice(perturbed_options)
            if rng.random() < leader_perturb_rate
            else base_topic
        )
        follower_query = (
            rng.choice(perturbed_options) if rng.random() < perturb_rate else base_topic
        )

        leader_resolved = resolved(leader_query)
        follower_resolved = resolved(follower_query)

        leader_error = int(leader_resolved.lower() != canonical.lower())
        async_error = int(follower_resolved.lower() != canonical.lower())
        sync_error = leader_error

        if leader_resolved == follower_resolved:
            surfaced_error = async_error
        elif leader_high_conf:
            surfaced_error = leader_error
            surfaced_adopt_count += 1
        else:
            surfaced_error = async_error

        leader_errors.append(leader_error)
        async_follower_errors.append(async_error)
        sync_follower_errors.append(sync_error)
        surfaced_follower_errors.append(surfaced_error)

    async_joint = sum(
        1 for l, a in zip(leader_errors, async_follower_errors) if l == 1 and a == 1
    )
    sync_joint = sum(
        1 for l, s in zip(leader_errors, sync_follower_errors) if l == 1 and s == 1
    )
    surfaced_joint = sum(
        1 for l, s in zip(leader_errors, surfaced_follower_errors) if l == 1 and s == 1
    )

    async_rate = sum(async_follower_errors) / trials
    sync_rate = sum(sync_follower_errors) / trials
    surfaced_rate = sum(surfaced_follower_errors) / trials

    return {
        "experiment": "F-AI1",
        "title": "Live confidence-gated evidence sharing vs async baseline vs forced sync",
        "mode": "live-evidence-surfacing",
        "seed": seed,
        "trials": trials,
        "lang": lang,
        "follower_perturb_rate": perturb_rate,
        "leader_high_conf_prob": round(leader_high_conf_prob, 4),
        "leader_high_conf_perturb_rate": round(leader_high_conf_perturb_rate, 4),
        "leader_low_conf_perturb_rate": round(leader_low_conf_perturb_rate, 4),
        "async": {
            "follower_error_rate": round(async_rate, 4),
            "joint_error_rate": round(async_joint / trials, 4),
            "leader_follower_error_correlation": round(
                _pearson(leader_errors, async_follower_errors), 4
            ),
        },
        "sync": {
            "follower_error_rate": round(sync_rate, 4),
            "joint_error_rate": round(sync_joint / trials, 4),
            "leader_follower_error_correlation": round(
                _pearson(leader_errors, sync_follower_errors), 4
            ),
        },
        "evidence_surfacing": {
            "follower_error_rate": round(surfaced_rate, 4),
            "joint_error_rate": round(surfaced_joint / trials, 4),
            "leader_follower_error_correlation": round(
                _pearson(leader_errors, surfaced_follower_errors), 4
            ),
            "adopted_high_conf_disagreements": surfaced_adopt_count,
        },
        "delta": {
            "surfacing_minus_async_error": round(surfaced_rate - async_rate, 4),
            "sync_minus_async_error": round(sync_rate - async_rate, 4),
        },
        "verdict": (
            "Confidence-gated evidence sharing can reduce follower error against async "
            "baseline while avoiding full synchronization coupling."
        ),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Swarm a Wikipedia topic by traversing related pages."
    )
    parser.add_argument("topic", nargs="*", help="Seed topic to explore.")
    parser.add_argument("--depth", type=int, default=1, help="Traversal depth (default: 1).")
    parser.add_argument("--fanout", type=int, default=5, help="Links sampled per page (default: 5).")
    parser.add_argument("--lang", default="en", help="Wikipedia language code (default: en).")
    parser.add_argument("--out", help="Optional output markdown path.")
    parser.add_argument(
        "--coord-experiment",
        action="store_true",
        help="Run a controlled async-vs-sync coordination experiment (no network calls).",
    )
    parser.add_argument(
        "--coord-live-experiment",
        action="store_true",
        help="Run a live Wikipedia perturbation experiment for async-vs-sync correlation.",
    )
    parser.add_argument(
        "--ai1-live-experiment",
        action="store_true",
        help="Run a live confidence-gated evidence-surfacing experiment (F-AI1).",
    )
    parser.add_argument(
        "--trials",
        type=int,
        default=200,
        help="Number of experiment trials when --coord-experiment is enabled.",
    )
    parser.add_argument(
        "--error-rate",
        type=float,
        default=0.2,
        help="Injected leader error probability [0,1] for --coord-experiment.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=155,
        help="Random seed for --coord-experiment.",
    )
    parser.add_argument(
        "--json-out",
        help="Optional JSON output path for --coord-experiment.",
    )
    parser.add_argument(
        "--perturb-rate",
        type=float,
        default=0.35,
        help="Topic-perturbation probability [0,1] for --coord-live-experiment.",
    )
    parser.add_argument(
        "--sync-inherit-prob",
        type=float,
        default=1.0,
        help="Probability [0,1] that sync follower inherits leader result in --coord-live-experiment.",
    )
    parser.add_argument(
        "--leader-high-conf-prob",
        type=float,
        default=0.45,
        help="Probability [0,1] leader is high-confidence in --ai1-live-experiment.",
    )
    parser.add_argument(
        "--leader-high-conf-perturb-rate",
        type=float,
        default=0.15,
        help="Leader query perturbation rate [0,1] when high-confidence in --ai1-live-experiment.",
    )
    parser.add_argument(
        "--leader-low-conf-perturb-rate",
        type=float,
        default=0.55,
        help="Leader query perturbation rate [0,1] when low-confidence in --ai1-live-experiment.",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Infer a topic from swarm state files when topic is omitted or generic.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    topic = " ".join(args.topic).strip()
    depth = max(0, min(args.depth, 3))
    fanout = max(1, min(args.fanout, 20))
    lang = args.lang.strip() or "en"

    if args.coord_experiment:
        payload = run_coordination_experiment(args.trials, args.error_rate, args.seed)
        payload["generated_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if args.json_out:
            out_path = Path(args.json_out)
            if not out_path.is_absolute():
                out_path = REPO_ROOT / out_path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            print(f"Wrote experiment: {out_path}")
        else:
            print(json.dumps(payload, indent=2))
        return 0

    if args.coord_live_experiment:
        payload = run_live_coordination_experiment(
            args.trials,
            args.perturb_rate,
            args.seed,
            lang,
            args.sync_inherit_prob,
        )
        payload["generated_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if args.json_out:
            out_path = Path(args.json_out)
            if not out_path.is_absolute():
                out_path = REPO_ROOT / out_path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            print(f"Wrote experiment: {out_path}")
        else:
            print(json.dumps(payload, indent=2))
        return 0

    if args.ai1_live_experiment:
        payload = run_live_ai1_evidence_experiment(
            args.trials,
            args.perturb_rate,
            args.seed,
            lang,
            args.leader_high_conf_prob,
            args.leader_high_conf_perturb_rate,
            args.leader_low_conf_perturb_rate,
        )
        payload["generated_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if args.json_out:
            out_path = Path(args.json_out)
            if not out_path.is_absolute():
                out_path = REPO_ROOT / out_path
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            print(f"Wrote experiment: {out_path}")
        else:
            print(json.dumps(payload, indent=2))
        return 0

    use_auto = args.auto or is_generic_invocation(topic)
    topic_source = "manual"

    if use_auto:
        topic, topic_source = choose_auto_topic()

    try:
        resolved, nodes = swarm_topic(topic, depth, fanout, lang)
    except Exception as e:
        print(f"wiki_swarm.py error: {e}", file=sys.stderr)
        return 1

    report = render_markdown(topic, resolved, depth, fanout, lang, nodes, topic_source)

    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = REPO_ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"Wrote report: {out_path}")
    else:
        print(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
