#!/usr/bin/env python3
"""Controlled experiment for F-AI1 evidence-surfacing intervention."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from random import Random

import wiki_swarm


@dataclass(frozen=True)
class Config:
    trials: int
    follower_accuracy: float
    leader_high_accuracy: float
    leader_low_accuracy: float
    leader_high_conf_prob: float
    seed: int


def _corr(xs: list[int], ys: list[int]) -> float:
    n = min(len(xs), len(ys))
    if n == 0:
        return 0.0
    x = xs[:n]
    y = ys[:n]
    mx = sum(x) / n
    my = sum(y) / n
    vx = sum((v - mx) ** 2 for v in x)
    vy = sum((v - my) ** 2 for v in y)
    if vx == 0 or vy == 0:
        return 0.0
    cov = sum((a - mx) * (b - my) for a, b in zip(x, y))
    return cov / ((vx * vy) ** 0.5)


def _choose_with_evidence(
    follower_title: str, leader_title: str, leader_high_confidence: bool
) -> str:
    """Confidence-gated surfacing policy used in both controlled and live modes."""
    if follower_title == leader_title:
        return follower_title
    return leader_title if leader_high_confidence else follower_title


def _normalize_accent(text: str) -> str:
    """Map accented chars to ASCII base equivalents (é→e, ñ→n, ü→u etc.)."""
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", _normalize_accent((text or "").lower()))



def _query_title_confidence(query: str, resolved_title: str, lang: str = "en") -> float:
    """
    Non-oracle confidence proxy from query-title alignment only.
    For EN: Jaccard overlap + character similarity.
    For non-EN: returns 0.0 (gate). ES consistently regressed (+0.08 to +0.14 delta)
    across all overlap formulations (Jaccard, recall, F1 with stop-word filtering) at
    all tested thresholds. Root cause: query-title alignment measures lexical similarity,
    not resolution correctness — the two are structurally decoupled in Spanish Wikipedia.
    (L-289: language-aware proxy attempt, gating as evidence-based fallback)
    """
    if lang != "en":
        return 0.0  # gate non-EN surfacing: proxy not reliable for ES (L-289)

    query_norm = " ".join(_tokenize(query))
    title_norm = " ".join(_tokenize(resolved_title))
    if not query_norm or not title_norm:
        return 0.0

    qset = set(query_norm.split())
    tset = set(title_norm.split())
    overlap = len(qset & tset) / max(1, len(qset | tset))
    char_sim = SequenceMatcher(None, query_norm, title_norm).ratio()
    return 0.6 * overlap + 0.4 * char_sim


def run(cfg: Config) -> dict:
    rng = Random(cfg.seed)
    baseline_leader_err: list[int] = []
    baseline_follower_err: list[int] = []
    sync_leader_err: list[int] = []
    sync_follower_err: list[int] = []
    surfaced_leader_err: list[int] = []
    surfaced_follower_err: list[int] = []

    for _ in range(cfg.trials):
        hidden = rng.randint(0, 1)
        leader_is_high_conf = rng.random() < cfg.leader_high_conf_prob
        leader_acc = (
            cfg.leader_high_accuracy if leader_is_high_conf else cfg.leader_low_accuracy
        )
        leader_signal = hidden if rng.random() < leader_acc else 1 - hidden
        follower_signal = hidden if rng.random() < cfg.follower_accuracy else 1 - hidden

        leader_pred = leader_signal
        baseline_pred = follower_signal
        sync_pred = leader_pred
        surfaced_pred = _choose_with_evidence(
            str(follower_signal), str(leader_signal), leader_is_high_conf
        )
        surfaced_pred = int(surfaced_pred)

        leader_err = int(leader_pred != hidden)
        baseline_err = int(baseline_pred != hidden)
        sync_err = int(sync_pred != hidden)
        surfaced_err = int(surfaced_pred != hidden)

        baseline_leader_err.append(leader_err)
        baseline_follower_err.append(baseline_err)
        sync_leader_err.append(leader_err)
        sync_follower_err.append(sync_err)
        surfaced_leader_err.append(leader_err)
        surfaced_follower_err.append(surfaced_err)

    def mean(vals: list[int]) -> float:
        return sum(vals) / len(vals) if vals else 0.0

    baseline_rate = mean(baseline_follower_err)
    sync_rate = mean(sync_follower_err)
    surfaced_rate = mean(surfaced_follower_err)
    leader_rate = mean(baseline_leader_err)

    return {
        "experiment": "F-AI1",
        "title": "Evidence-surfacing vs async baseline vs forced sync",
        "seed": cfg.seed,
        "trials": cfg.trials,
        "follower_accuracy": cfg.follower_accuracy,
        "leader_high_accuracy": cfg.leader_high_accuracy,
        "leader_low_accuracy": cfg.leader_low_accuracy,
        "leader_high_conf_prob": cfg.leader_high_conf_prob,
        "leader_error_rate": round(leader_rate, 4),
        "async_baseline": {
            "follower_error_rate": round(baseline_rate, 4),
            "leader_follower_error_correlation": round(
                _corr(baseline_leader_err, baseline_follower_err), 4
            ),
        },
        "sync_copy": {
            "follower_error_rate": round(sync_rate, 4),
            "leader_follower_error_correlation": round(
                _corr(sync_leader_err, sync_follower_err), 4
            ),
        },
        "evidence_surfacing": {
            "follower_error_rate": round(surfaced_rate, 4),
            "leader_follower_error_correlation": round(
                _corr(surfaced_leader_err, surfaced_follower_err), 4
            ),
        },
        "delta": {
            "surfacing_minus_async_error": round(surfaced_rate - baseline_rate, 4),
            "sync_minus_async_error": round(sync_rate - baseline_rate, 4),
        },
        "interpretation": (
            "Confidence-gated evidence sharing lowers follower error versus async "
            "baseline while preserving lower coupling than forced sync."
        ),
    }


def run_live(
    trials: int,
    perturb_rate: float,
    seed: int,
    lang: str,
    confidence_threshold: float,
) -> dict:
    """
    Live F-AI1 test on Wikipedia query resolution:
    - async follower resolves independently
    - sync follower copies leader
    - evidence-surfacing copies leader only on high-confidence disagreements
      using query-title alignment (non-oracle)
    """
    trials = max(1, trials)
    perturb_rate = max(0.0, min(1.0, perturb_rate))
    rng = Random(seed)

    topic_pool = [topic for topic, _ in wiki_swarm.AUTO_TOPICS]
    resolve_cache: dict[str, str] = {}

    def resolve(query: str) -> str:
        if query not in resolve_cache:
            resolve_cache[query] = wiki_swarm.resolve_topic(query, lang)
        return resolve_cache[query]

    leader_errs: list[int] = []
    async_errs: list[int] = []
    sync_errs: list[int] = []
    surfaced_errs: list[int] = []
    adopted_count = 0
    confidence_scores: list[float] = []
    high_conf_count = 0

    for _ in range(trials):
        base_topic = rng.choice(topic_pool)
        canonical = resolve(base_topic)

        leader_perturbed = rng.random() < perturb_rate
        follower_perturbed = rng.random() < perturb_rate
        leader_query = (
            wiki_swarm._perturb_topic_query(base_topic, rng)
            if leader_perturbed
            else base_topic
        )
        follower_query = (
            wiki_swarm._perturb_topic_query(base_topic, rng)
            if follower_perturbed
            else base_topic
        )

        leader_title = resolve(leader_query)
        follower_title = resolve(follower_query)

        conf_score = _query_title_confidence(leader_query, leader_title, lang=lang)
        leader_high_conf = conf_score >= confidence_threshold
        surfaced_title = _choose_with_evidence(
            follower_title, leader_title, leader_high_conf
        )
        if surfaced_title == leader_title and follower_title != leader_title:
            adopted_count += 1
        confidence_scores.append(conf_score)
        if leader_high_conf:
            high_conf_count += 1

        leader_errs.append(int(leader_title.lower() != canonical.lower()))
        async_errs.append(int(follower_title.lower() != canonical.lower()))
        sync_errs.append(int(leader_title.lower() != canonical.lower()))
        surfaced_errs.append(int(surfaced_title.lower() != canonical.lower()))

    def _mean(vals: list[int]) -> float:
        return sum(vals) / len(vals) if vals else 0.0

    async_rate = _mean(async_errs)
    sync_rate = _mean(sync_errs)
    surfaced_rate = _mean(surfaced_errs)

    return {
        "experiment": "F-AI1",
        "title": "Live evidence-surfacing vs async baseline vs forced sync",
        "mode": "live-networked-topic-resolution",
        "seed": seed,
        "trials": trials,
        "lang": lang,
        "perturb_rate": perturb_rate,
        "confidence_proxy": {
            "type": "query_title_alignment",
            "threshold": round(confidence_threshold, 4),
            "mean_score": round(sum(confidence_scores) / max(1, len(confidence_scores)), 4),
            "high_conf_rate": round(high_conf_count / trials, 4),
        },
        "leader_error_rate": round(_mean(leader_errs), 4),
        "async_baseline": {
            "follower_error_rate": round(async_rate, 4),
            "leader_follower_error_correlation": round(_corr(leader_errs, async_errs), 4),
        },
        "sync_copy": {
            "follower_error_rate": round(sync_rate, 4),
            "leader_follower_error_correlation": round(_corr(leader_errs, sync_errs), 4),
        },
        "evidence_surfacing": {
            "follower_error_rate": round(surfaced_rate, 4),
            "leader_follower_error_correlation": round(
                _corr(leader_errs, surfaced_errs), 4
            ),
            "adoption_rate": round(adopted_count / trials, 4),
        },
        "delta": {
            "surfacing_minus_async_error": round(surfaced_rate - async_rate, 4),
            "sync_minus_async_error": round(sync_rate - async_rate, 4),
        },
        "interpretation": (
            "Live confidence-gated evidence sharing is intended to reduce async error "
            "without the full coupling of forced synchronization."
        ),
    }


@dataclass
class _TrialData:
    canonical: str
    leader_query: str
    leader_title: str
    follower_title: str
    conf_score: float


def _build_trial_data(
    trials: int,
    perturb_rate: float,
    seed: int,
    lang: str,
) -> list[_TrialData]:
    """
    Pre-resolve all trials once so that calibration sweeps across thresholds
    share a single network pass — no redundant Wikipedia queries.
    """
    import time as _time

    trials = max(1, trials)
    perturb_rate = max(0.0, min(1.0, perturb_rate))
    rng = Random(seed)

    topic_pool = [topic for topic, _ in wiki_swarm.AUTO_TOPICS]
    resolve_cache: dict[str, str] = {}

    def resolve(query: str) -> str:
        if query not in resolve_cache:
            # Small delay to stay within Wikipedia rate limits
            _time.sleep(0.05)
            resolve_cache[query] = wiki_swarm.resolve_topic(query, lang)
        return resolve_cache[query]

    data: list[_TrialData] = []
    for _ in range(trials):
        base_topic = rng.choice(topic_pool)
        canonical = resolve(base_topic)

        leader_perturbed = rng.random() < perturb_rate
        follower_perturbed = rng.random() < perturb_rate
        leader_query = (
            wiki_swarm._perturb_topic_query(base_topic, rng)
            if leader_perturbed
            else base_topic
        )
        follower_query = (
            wiki_swarm._perturb_topic_query(base_topic, rng)
            if follower_perturbed
            else base_topic
        )

        leader_title = resolve(leader_query)
        follower_title = resolve(follower_query)
        conf_score = _query_title_confidence(leader_query, leader_title, lang=lang)

        data.append(
            _TrialData(
                canonical=canonical,
                leader_query=leader_query,
                leader_title=leader_title,
                follower_title=follower_title,
                conf_score=conf_score,
            )
        )

    return data


def _score_threshold(trial_data: list[_TrialData], threshold: float) -> dict:
    """Re-score pre-built trial data for a given confidence threshold."""

    def _mean(vals: list[int]) -> float:
        return sum(vals) / len(vals) if vals else 0.0

    leader_errs: list[int] = []
    async_errs: list[int] = []
    surfaced_errs: list[int] = []
    adopted_count = 0
    high_conf_count = 0

    for td in trial_data:
        leader_high_conf = td.conf_score >= threshold
        surfaced_title = _choose_with_evidence(
            td.follower_title, td.leader_title, leader_high_conf
        )
        if surfaced_title == td.leader_title and td.follower_title != td.leader_title:
            adopted_count += 1
        if leader_high_conf:
            high_conf_count += 1

        leader_errs.append(int(td.leader_title.lower() != td.canonical.lower()))
        async_errs.append(int(td.follower_title.lower() != td.canonical.lower()))
        surfaced_errs.append(int(surfaced_title.lower() != td.canonical.lower()))

    n = len(trial_data)
    async_rate = _mean(async_errs)
    surfaced_rate = _mean(surfaced_errs)

    return {
        "threshold": round(threshold, 4),
        "surfacing_error": round(surfaced_rate, 4),
        "async_error": round(async_rate, 4),
        "delta": round(surfaced_rate - async_rate, 4),
        "adoption_rate": round(adopted_count / n, 4),
        "high_conf_rate": round(high_conf_count / n, 4),
    }


def run_calibrate(
    thresholds: list[float],
    trials: int,
    perturb_rate: float,
    seed: int,
    lang: str,
) -> dict:
    """
    Calibration sweep: pre-build trial data once (single Wikipedia pass), then
    re-score for each threshold. Returns sweep showing surfacing_error, async_error,
    delta, adoption_rate, and high_conf_rate. Identifies optimal threshold
    (lowest surfacing_error).
    """
    print(f"  Pre-building trial data ({trials} trials, lang={lang})...")
    trial_data = _build_trial_data(trials, perturb_rate, seed, lang)
    print(f"  Done. Scoring {len(thresholds)} thresholds...")

    sweep: list[dict] = []
    for threshold in thresholds:
        row = _score_threshold(trial_data, threshold)
        sweep.append(row)
        print(
            f"  threshold={threshold:.2f}"
            f"  surfacing={row['surfacing_error']:.4f}"
            f"  async={row['async_error']:.4f}"
            f"  delta={row['delta']:+.4f}"
            f"  adoption={row['adoption_rate']:.4f}"
            f"  high_conf={row['high_conf_rate']:.4f}"
        )

    optimal = min(sweep, key=lambda r: r["surfacing_error"])

    return {
        "experiment": "F-AI1-calibrate",
        "title": "Threshold calibration sweep for evidence-surfacing confidence proxy",
        "lang": lang,
        "trials": trials,
        "perturb_rate": perturb_rate,
        "seed": seed,
        "sweep": sweep,
        "optimal_threshold": optimal["threshold"],
        "optimal_surfacing_error": optimal["surfacing_error"],
        "optimal_delta": optimal["delta"],
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live", action="store_true", help="Run live-networked experiment.")
    p.add_argument(
        "--calibrate-thresholds",
        type=str,
        default=None,
        help=(
            "Comma-separated list of confidence thresholds to sweep (e.g. "
            "'0.2,0.35,0.45,0.58,0.70,0.85'). Requires --live."
        ),
    )
    p.add_argument("--trials", type=int, default=2000)
    p.add_argument("--follower-accuracy", type=float, default=0.65)
    p.add_argument("--leader-high-accuracy", type=float, default=0.82)
    p.add_argument("--leader-low-accuracy", type=float, default=0.52)
    p.add_argument("--leader-high-conf-prob", type=float, default=0.45)
    p.add_argument("--perturb-rate", type=float, default=0.35)
    p.add_argument("--lang", type=str, default="en")
    p.add_argument("--confidence-threshold", type=float, default=0.58)
    p.add_argument("--seed", type=int, default=186)
    p.add_argument("--out", type=Path, required=True)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.calibrate_thresholds is not None:
        thresholds = [float(t.strip()) for t in args.calibrate_thresholds.split(",")]
        print(
            f"Calibration sweep: lang={args.lang} trials={args.trials} "
            f"seed={args.seed} perturb_rate={args.perturb_rate} "
            f"thresholds={thresholds}"
        )
        payload = run_calibrate(
            thresholds=thresholds,
            trials=args.trials,
            perturb_rate=args.perturb_rate,
            seed=args.seed,
            lang=args.lang,
        )
    elif args.live:
        payload = run_live(
            args.trials,
            args.perturb_rate,
            args.seed,
            args.lang,
            max(0.0, min(1.0, args.confidence_threshold)),
        )
    else:
        cfg = Config(
            trials=max(1, args.trials),
            follower_accuracy=max(0.0, min(1.0, args.follower_accuracy)),
            leader_high_accuracy=max(0.0, min(1.0, args.leader_high_accuracy)),
            leader_low_accuracy=max(0.0, min(1.0, args.leader_low_accuracy)),
            leader_high_conf_prob=max(0.0, min(1.0, args.leader_high_conf_prob)),
            seed=args.seed,
        )
        payload = run(cfg)
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    if "sweep" in payload:
        print(f"Optimal threshold: {payload['optimal_threshold']}")
        print(f"Optimal surfacing_error: {payload['optimal_surfacing_error']:.4f}")
        print(f"Optimal delta: {payload['optimal_delta']:+.4f}")
    else:
        print(
            "error:",
            f"async={payload['async_baseline']['follower_error_rate']:.4f}",
            f"surfacing={payload['evidence_surfacing']['follower_error_rate']:.4f}",
            f"sync={payload['sync_copy']['follower_error_rate']:.4f}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
