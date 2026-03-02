#!/usr/bin/env python3
"""F-FIN1 factual-QA diversification harness (N=1 vs majority-vote N=3)."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from random import Random

import wiki_swarm


@dataclass(frozen=True)
class CapitalQuestion:
    country: str
    capital: str


QA_BANK: tuple[CapitalQuestion, ...] = (
    CapitalQuestion("France", "Paris"),
    CapitalQuestion("Japan", "Tokyo"),
    CapitalQuestion("Italy", "Rome"),
    CapitalQuestion("Canada", "Ottawa"),
    CapitalQuestion("Australia", "Canberra"),
    CapitalQuestion("India", "New Delhi"),
    CapitalQuestion("Spain", "Madrid"),
    CapitalQuestion("Germany", "Berlin"),
    CapitalQuestion("Argentina", "Buenos Aires"),
    CapitalQuestion("Egypt", "Cairo"),
    CapitalQuestion("Kenya", "Nairobi"),
    CapitalQuestion("Sweden", "Stockholm"),
)

CAPITAL_NAME_RE = r"[A-Z][A-Za-zÀ-ÿ'’-]*(?:\s+[A-Z][A-Za-zÀ-ÿ'’-]*){0,3}"

ANSWER_ALIAS_BY_COUNTRY: dict[str, dict[str, str]] = {
    "India": {
        "delhi": "New Delhi",
    },
}

BLOCKED_ANSWER_MARKERS: tuple[str, ...] = (
    "capital of",
    "capital punishment",
    "closed ended",
    "closed-ended",
    "closed ended question",
    "closed-ended question",
    "list of",
    "history of",
    "capital city",
)

BLOCKED_EXACT_ANSWERS: set[str] = {
    "capital",
    "capital city",
    "the city",
    "city",
    "new capital",
    "the new capital",
    "country capital",
    "question",
}


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text or "")
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return re.sub(r"\s+", " ", value).strip()


def _is_correct(predicted_title: str, predicted_summary: str, expected_title: str) -> bool:
    pred = _normalize(predicted_title)
    summary = _normalize(predicted_summary)
    expected = _normalize(expected_title)
    return (
        pred == expected
        or f" {expected} " in f" {pred} "
        or f" {expected} " in f" {summary} "
    )


def _extract_capital_answer(summary: str, country: str) -> str:
    text = (summary or "").strip()
    if not text:
        return ""
    country_re = re.escape(country)
    capital_re = CAPITAL_NAME_RE
    patterns = (
        rf"\bcapital(?:\s+city)?\s+of\s+{country_re}\s+is\s+(?:the\s+city\s+of\s+)?({capital_re})\b",
        rf"\bcapital(?:\s+city)?\s+of\s+{country_re}\s+has\s+been\s+({capital_re})\b",
        rf"\b({capital_re})\s+is\s+the\s+capital(?:\s+(?:and|,)\s+[A-Za-zÀ-ÿ' -]+)?\s+of\s+{country_re}\b",
        rf"\b({capital_re})\s+is\s+the\s+capital(?:\s+city)?\s+of\s+{country_re}\b",
        rf"\b({capital_re}),\s+the\s+capital(?:\s+city)?\s+of\s+{country_re}\b",
        rf"\b{country_re}'s\s+capital(?:\s+city)?\s+is\s+({capital_re})\b",
        rf"\b{country_re}\b[\s\S]{{0,220}}\bcapital(?:\s+city)?\s*,\s*({capital_re})\b",
        rf"\b{country_re}\b[\s\S]{{0,140}}\bcapital(?:\s+city)?\s+is\s+({capital_re})\b",
        rf"\b({capital_re})\s+serves\s+as\s+the\s+capital\s+of\s+{country_re}\b",
    )
    for pattern in patterns:
        m = re.search(pattern, text)
        if not m:
            continue
        answer = m.group(1).strip(" .,:;()[]{}")
        answer = re.sub(r"\s+", " ", answer)
        return answer
    return ""


def _canonicalize_answer(answer: str, country: str) -> str:
    value = re.sub(r"\s+", " ", (answer or "").strip(" .,:;()[]{}"))
    norm = _normalize(value)
    if norm.startswith("the city of "):
        value = value[12:]
        norm = _normalize(value)
    elif norm.startswith("city of "):
        value = value[8:]
        norm = _normalize(value)
    alias_map = ANSWER_ALIAS_BY_COUNTRY.get(country, {})
    if norm in alias_map:
        return alias_map[norm]
    if value.lower().startswith("the "):
        return value[4:]
    return value


def _is_plausible_capital_answer(answer: str, country: str) -> bool:
    norm_answer = _normalize(answer)
    norm_country = _normalize(country)
    if not norm_answer or norm_answer == norm_country:
        return False
    if norm_answer.startswith(("what", "who", "when", "where", "why", "how")):
        return False
    if norm_answer in BLOCKED_EXACT_ANSWERS:
        return False
    if any(marker in norm_answer for marker in BLOCKED_ANSWER_MARKERS):
        return False
    if len(norm_answer.split()) > 4:
        return False
    return True


def _majority_vote(predictions: list[str]) -> str:
    if not predictions:
        return ""
    counts = Counter(predictions)
    top = max(counts.values())
    top_labels = {label for label, value in counts.items() if value == top}
    for label in predictions:
        if label in top_labels:
            return label
    return predictions[0]


def _capital_query(country: str, rng: Random) -> str:
    templates = (
        "What is the capital of {country}?",
        "capital of {country}",
        "{country} capital city",
        "{country} capital",
        "capital {country}",
    )
    return rng.choice(templates).format(country=country)


def _perturb_query(text: str, rng: Random) -> str:
    value = text.strip()
    if len(value) < 4:
        return value
    mode = rng.choice(("drop_char", "swap_adjacent", "drop_space"))
    if mode == "drop_char":
        idx = rng.randrange(1, len(value) - 1)
        return value[:idx] + value[idx + 1 :]
    if mode == "swap_adjacent":
        idx = rng.randrange(0, len(value) - 1)
        chars = list(value)
        chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
        return "".join(chars)
    if " " in value:
        return value.replace(" ", "", 1)
    return value


def _resolve_title(query: str, lang: str, cache: dict[str, str]) -> str:
    if query not in cache:
        try:
            cache[query] = wiki_swarm.resolve_topic(query, lang)
        except Exception:
            cache[query] = query
    return cache[query]


def _resolve_summary(title: str, lang: str, cache: dict[str, str]) -> str:
    if title not in cache:
        try:
            payload = wiki_swarm.fetch_summary(title, lang)
            cache[title] = payload["summary"] if payload else ""
        except Exception:
            cache[title] = ""
    return cache[title]


def _is_plausible_capital_title(title: str, country: str) -> bool:
    norm_title = _normalize(title)
    norm_country = _normalize(country)
    if not norm_title or norm_title == norm_country:
        return False
    # Filter obvious query/topic echoes that are not candidate answers.
    blocked = (
        "capital of",
        "country of",
        "what is",
        "what ",
        "who ",
        "when ",
        "where ",
        "why ",
        "how ",
        "capital city",
        "new capital",
        "capital punishment",
        "closed ended question",
        "list of",
        "history of",
    )
    return not any(marker in norm_title for marker in blocked)


def _predict_capital(
    *,
    country: str,
    query: str,
    lang: str,
    resolve_cache: dict[str, str],
    summary_cache: dict[str, str],
) -> tuple[str, list[str]]:
    query_candidates = (
        query,
        f"What is the capital of {country}?",
        f"capital of {country}",
        f"{country} capital city",
        country,
    )
    seen_queries: set[str] = set()
    resolved_titles: list[str] = []
    fallback_title = ""

    for candidate in query_candidates:
        key = _normalize(candidate)
        if key in seen_queries:
            continue
        seen_queries.add(key)
        resolved = _resolve_title(candidate, lang, resolve_cache)
        resolved_titles.append(resolved)
        summary = _resolve_summary(resolved, lang, summary_cache)
        answer = _extract_capital_answer(summary, country)
        if answer:
            answer = _canonicalize_answer(answer, country)
            if _is_plausible_capital_answer(answer, country):
                return answer, resolved_titles
        fallback_candidate = _canonicalize_answer(resolved, country)
        if _is_plausible_capital_title(resolved, country) and _is_plausible_capital_answer(
            fallback_candidate, country
        ):
            fallback_title = fallback_candidate

    if fallback_title:
        return fallback_title, resolved_titles
    if resolved_titles:
        return resolved_titles[-1], resolved_titles
    return country, resolved_titles


def _trial(
    *,
    agents: int,
    perturb_rate: float,
    lang: str,
    rng: Random,
    resolve_cache: dict[str, str],
    summary_cache: dict[str, str],
) -> dict:
    agents = max(1, agents)
    correct = 0
    pairwise_equal = 0
    pairwise_total = 0
    error_samples: list[dict[str, object]] = []

    for row in QA_BANK:
        predictions: list[str] = []
        resolved_titles: list[str] = []
        for _ in range(agents):
            query = _capital_query(row.country, rng)
            if rng.random() < perturb_rate:
                query = _perturb_query(query, rng)
            answer, resolved_chain = _predict_capital(
                country=row.country,
                query=query,
                lang=lang,
                resolve_cache=resolve_cache,
                summary_cache=summary_cache,
            )
            resolved = resolved_chain[-1] if resolved_chain else query
            predictions.append(answer)
            resolved_titles.append(resolved)
        voted = _majority_vote(predictions)
        if _is_correct(voted, "", row.capital):
            correct += 1
        elif len(error_samples) < 8:
            error_samples.append(
                {
                    "country": row.country,
                    "expected": row.capital,
                    "resolved_titles": resolved_titles,
                    "predictions": predictions,
                    "vote": voted,
                }
            )

        if agents > 1:
            for i in range(len(predictions)):
                for j in range(i + 1, len(predictions)):
                    pairwise_total += 1
                    if _normalize(predictions[i]) == _normalize(predictions[j]):
                        pairwise_equal += 1

    total = len(QA_BANK)
    return {
        "accuracy": correct / total if total else 0.0,
        "correct": correct,
        "total": total,
        "pairwise_agreement": (
            pairwise_equal / pairwise_total if pairwise_total else None
        ),
        "error_samples": error_samples,
    }


def _summarize(accuracies: list[float]) -> dict:
    if not accuracies:
        return {"mean": 0.0, "std": 0.0, "variance": 0.0}
    mean = statistics.fmean(accuracies)
    variance = statistics.pvariance(accuracies) if len(accuracies) > 1 else 0.0
    return {
        "mean": round(mean, 4),
        "std": round(variance**0.5, 4),
        "variance": round(variance, 6),
    }


def _bootstrap_delta_ci(
    single_accuracies: list[float],
    diversified_accuracies: list[float],
    *,
    resamples: int,
    rng: Random,
) -> dict:
    if (
        not single_accuracies
        or not diversified_accuracies
        or resamples <= 0
    ):
        return {
            "resamples": 0,
            "lower": 0.0,
            "upper": 0.0,
            "includes_zero": True,
        }
    n1 = len(single_accuracies)
    n3 = len(diversified_accuracies)
    draws: list[float] = []
    for _ in range(resamples):
        sample_n1 = [single_accuracies[rng.randrange(n1)] for _ in range(n1)]
        sample_n3 = [diversified_accuracies[rng.randrange(n3)] for _ in range(n3)]
        draws.append(statistics.fmean(sample_n3) - statistics.fmean(sample_n1))
    draws.sort()
    lower_idx = int(0.025 * (resamples - 1))
    upper_idx = int(0.975 * (resamples - 1))
    lower = draws[lower_idx]
    upper = draws[upper_idx]
    return {
        "resamples": resamples,
        "lower": round(lower, 4),
        "upper": round(upper, 4),
        "includes_zero": lower <= 0.0 <= upper,
    }


def run(
    *,
    trials_per_condition: int,
    agents_diversified: int,
    perturb_rate: float,
    seed: int,
    lang: str,
    bootstrap_resamples: int,
    bootstrap_seed: int | None,
) -> dict:
    rng = Random(seed)
    resolve_cache: dict[str, str] = {}
    summary_cache: dict[str, str] = {}
    trials_per_condition = max(1, trials_per_condition)
    agents_diversified = max(2, agents_diversified)

    single_trials: list[dict] = []
    diversified_trials: list[dict] = []
    for _ in range(trials_per_condition):
        single_trials.append(
            _trial(
                agents=1,
                perturb_rate=perturb_rate,
                lang=lang,
                rng=rng,
                resolve_cache=resolve_cache,
                summary_cache=summary_cache,
            )
        )
        diversified_trials.append(
            _trial(
                agents=agents_diversified,
                perturb_rate=perturb_rate,
                lang=lang,
                rng=rng,
                resolve_cache=resolve_cache,
                summary_cache=summary_cache,
            )
        )

    single_accuracies = [row["accuracy"] for row in single_trials]
    diversified_accuracies = [row["accuracy"] for row in diversified_trials]
    single_summary = _summarize(single_accuracies)
    diversified_summary = _summarize(diversified_accuracies)

    variance_ratio = None
    if single_summary["variance"] > 0:
        variance_ratio = round(
            diversified_summary["variance"] / single_summary["variance"], 4
        )

    mean_pairwise = statistics.fmean(
        [
            row["pairwise_agreement"]
            for row in diversified_trials
            if row["pairwise_agreement"] is not None
        ]
    )
    bootstrap_rng = Random(seed + 1000 if bootstrap_seed is None else bootstrap_seed)
    delta_bootstrap_ci95 = _bootstrap_delta_ci(
        single_accuracies,
        diversified_accuracies,
        resamples=max(0, bootstrap_resamples),
        rng=bootstrap_rng,
    )

    return {
        "experiment": "F-FIN1",
        "title": "Factual-QA diversification: single-agent vs majority vote",
        "mode": "live-wikipedia-capital-qa-direct-answer",
        "seed": seed,
        "lang": lang,
        "trials_per_condition": trials_per_condition,
        "perturb_rate": round(perturb_rate, 4),
        "question_bank": [
            {
                "question": f"What is the capital of {row.country}?",
                "expected": row.capital,
            }
            for row in QA_BANK
        ],
        "single_agent": {
            "agents": 1,
            "trial_accuracies": [round(v, 4) for v in single_accuracies],
            "summary": single_summary,
            "error_samples": single_trials[0]["error_samples"] if single_trials else [],
        },
        "majority_vote": {
            "agents": agents_diversified,
            "trial_accuracies": [round(v, 4) for v in diversified_accuracies],
            "summary": diversified_summary,
            "mean_pairwise_prediction_agreement": round(mean_pairwise, 4),
            "error_samples": (
                diversified_trials[0]["error_samples"] if diversified_trials else []
            ),
        },
        "delta": {
            "mean_accuracy_n3_minus_n1": round(
                diversified_summary["mean"] - single_summary["mean"], 4
            ),
            "variance_ratio_n3_over_n1": variance_ratio,
            "bootstrap_ci95_n3_minus_n1": delta_bootstrap_ci95,
        },
        "interpretation": (
            "This run scores direct capital answers extracted from fetched knowledge "
            "content (with fallback to resolved title), reducing resolver-proxy bias "
            "in the F-FIN1 factual diversification test."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trials-per-condition", type=int, default=5)
    parser.add_argument("--agents-diversified", type=int, default=3)
    parser.add_argument("--perturb-rate", type=float, default=0.35)
    parser.add_argument("--seed", type=int, default=186)
    parser.add_argument("--bootstrap-resamples", type=int, default=2000)
    parser.add_argument("--bootstrap-seed", type=int)
    parser.add_argument("--lang", type=str, default="en")
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = run(
        trials_per_condition=args.trials_per_condition,
        agents_diversified=args.agents_diversified,
        perturb_rate=max(0.0, min(1.0, args.perturb_rate)),
        seed=args.seed,
        lang=args.lang,
        bootstrap_resamples=max(0, args.bootstrap_resamples),
        bootstrap_seed=args.bootstrap_seed,
    )
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    print(
        "acc:",
        f"N1={payload['single_agent']['summary']['mean']:.4f}",
        f"N{payload['majority_vote']['agents']}={payload['majority_vote']['summary']['mean']:.4f}",
        "var_ratio_n3_over_n1=",
        payload["delta"]["variance_ratio_n3_over_n1"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
