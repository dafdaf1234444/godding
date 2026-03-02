#!/usr/bin/env python3
"""Regression tests for F-FIN1 factual-QA diversification harness."""

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import f_fin1_factual_qa as mod


class TestFFIN1FactualQA(unittest.TestCase):
    def test_normalize_strips_accents(self):
        self.assertEqual(mod._normalize("Brasilia"), mod._normalize("Brasília"))

    def test_majority_vote_uses_mode(self):
        self.assertEqual(mod._majority_vote(["Paris", "Paris", "Lyon"]), "Paris")

    def test_majority_vote_tie_breaks_first_seen(self):
        self.assertEqual(mod._majority_vote(["Rome", "Paris"]), "Rome")

    def test_correctness_match(self):
        self.assertTrue(mod._is_correct("Capital of India", "New Delhi is the capital of India.", "New Delhi"))
        self.assertFalse(mod._is_correct("Delhi Sultanate", "A medieval empire.", "New Delhi"))

    def test_extract_capital_answer_patterns(self):
        a = mod._extract_capital_answer("The capital of India is New Delhi.", "India")
        b = mod._extract_capital_answer("Tokyo is the capital city of Japan.", "Japan")
        self.assertEqual(mod._normalize(a), mod._normalize("New Delhi"))
        self.assertEqual(mod._normalize(b), mod._normalize("Tokyo"))

    def test_extract_capital_answer_handles_capital_and_largest_city(self):
        summary = "Paris is the capital and most populous city of France."
        answer = mod._extract_capital_answer(summary, "France")
        self.assertEqual(mod._normalize(answer), mod._normalize("Paris"))

    def test_extract_capital_answer_handles_city_of_form(self):
        summary = "The capital of Germany is the city of Berlin."
        answer = mod._extract_capital_answer(summary, "Germany")
        self.assertEqual(mod._normalize(answer), mod._normalize("Berlin"))

    def test_extract_capital_answer_handles_has_been_form(self):
        summary = "The capital of France has been Paris since 1944."
        answer = mod._extract_capital_answer(summary, "France")
        self.assertEqual(mod._normalize(answer), mod._normalize("Paris"))

    def test_extract_capital_answer_handles_appositive_form(self):
        summary = "Delhi contains New Delhi, the capital of India."
        answer = mod._extract_capital_answer(summary, "India")
        self.assertEqual(mod._normalize(answer), mod._normalize("New Delhi"))

    def test_extract_capital_answer_handles_country_then_capital_city_comma(self):
        summary = "Egypt. It is a satellite city of the nation's original capital city, Cairo."
        answer = mod._extract_capital_answer(summary, "Egypt")
        self.assertEqual(mod._normalize(answer), mod._normalize("Cairo"))

    def test_canonicalize_india_alias(self):
        self.assertEqual(mod._canonicalize_answer("Delhi", "India"), "New Delhi")

    def test_plausibility_filters_noise_answer(self):
        self.assertFalse(mod._is_plausible_capital_answer("Closed-ended question", "France"))
        self.assertFalse(mod._is_plausible_capital_answer("The New Capital", "Egypt"))
        self.assertFalse(mod._is_plausible_capital_answer("Whati", "France"))
        self.assertTrue(mod._is_plausible_capital_answer("Paris", "France"))

    @mock.patch.object(mod, "_resolve_summary")
    @mock.patch.object(mod, "_resolve_title")
    def test_predict_capital_uses_fallback_queries(self, mock_resolve_title, mock_resolve_summary):
        def fake_resolve(query: str, _lang: str, _cache: dict[str, str]) -> str:
            if query == "France capital city":
                return "Paris"
            return "France"

        def fake_summary(title: str, _lang: str, _cache: dict[str, str]) -> str:
            if title == "Paris":
                return "Paris is the capital and most populous city of France."
            return "France is a country in Europe."

        mock_resolve_title.side_effect = fake_resolve
        mock_resolve_summary.side_effect = fake_summary

        answer, resolved_chain = mod._predict_capital(
            country="France",
            query="Frnace capital",
            lang="en",
            resolve_cache={},
            summary_cache={},
        )
        self.assertEqual(mod._normalize(answer), mod._normalize("Paris"))
        self.assertIn("Paris", resolved_chain)

    @mock.patch.object(mod, "_resolve_summary")
    @mock.patch.object(mod, "_resolve_title")
    def test_predict_capital_skips_implausible_extracted_answer(
        self, mock_resolve_title, mock_resolve_summary
    ):
        def fake_resolve(query: str, _lang: str, _cache: dict[str, str]) -> str:
            if query == "What is the capital of France?":
                return "Paris"
            return "France"

        def fake_summary(title: str, _lang: str, _cache: dict[str, str]) -> str:
            if title == "France":
                return "The capital of France is Closed-ended question."
            if title == "Paris":
                return "Paris is the capital and most populous city of France."
            return ""

        mock_resolve_title.side_effect = fake_resolve
        mock_resolve_summary.side_effect = fake_summary

        answer, _ = mod._predict_capital(
            country="France",
            query="capital of France",
            lang="en",
            resolve_cache={},
            summary_cache={},
        )
        self.assertEqual(mod._normalize(answer), mod._normalize("Paris"))

    def test_bootstrap_delta_ci_covers_zero_for_identical_inputs(self):
        rng = mod.Random(5)
        ci = mod._bootstrap_delta_ci(
            [0.2, 0.4, 0.6, 0.8],
            [0.2, 0.4, 0.6, 0.8],
            resamples=500,
            rng=rng,
        )
        self.assertEqual(ci["resamples"], 500)
        self.assertTrue(ci["includes_zero"])
        self.assertLessEqual(ci["lower"], ci["upper"])


if __name__ == "__main__":
    unittest.main()
