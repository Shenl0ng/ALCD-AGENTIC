from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "runtime"
DATASET_PATH = ROOT / "evaluation/negative_cases/negative_case_dataset.json"

if str(RUNTIME_PATH) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PATH))


def load_module(name: str):
    path = RUNTIME_PATH / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


negative_case_dataset = load_module("negative_case_dataset")


class NegativeCaseDatasetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = negative_case_dataset.load_dataset(DATASET_PATH)
        self.result = negative_case_dataset.validate_dataset(self.cases)
        self.summary = self.result.summary

    def test_dataset_exists(self) -> None:
        self.assertTrue(DATASET_PATH.exists())

    def test_dataset_has_at_least_30_cases(self) -> None:
        self.assertGreaterEqual(self.summary.total_cases, 30)

    def test_dataset_has_at_least_10_no_trade_cases(self) -> None:
        self.assertGreaterEqual(self.summary.no_trade_case_count, 10)

    def test_dataset_has_at_least_10_weak_setup_rejection_cases(self) -> None:
        self.assertGreaterEqual(self.summary.weak_setup_rejection_count, 10)

    def test_dataset_has_at_least_5_rubber_stamping_cases(self) -> None:
        self.assertGreaterEqual(self.summary.rubber_stamping_case_count, 5)

    def test_dataset_has_at_least_5_journal_evidence_failure_cases(self) -> None:
        self.assertGreaterEqual(self.summary.journal_evidence_failure_count, 5)

    def test_all_required_categories_are_represented(self) -> None:
        self.assertFalse(
            set(negative_case_dataset.REQUIRED_CATEGORIES)
            - set(self.summary.category_counts)
        )

    def test_all_required_expected_decisions_are_represented(self) -> None:
        self.assertFalse(
            set(negative_case_dataset.REQUIRED_EXPECTED_DECISIONS)
            - set(self.summary.expected_decision_counts)
        )

    def test_every_case_has_required_fields(self) -> None:
        for case in self.cases:
            self.assertFalse(
                set(negative_case_dataset.REQUIRED_FIELDS) - set(case),
                case["case_id"],
            )

    def test_every_case_has_prohibited_outcome(self) -> None:
        for case in self.cases:
            self.assertTrue(str(case["prohibited_outcome"]).strip(), case["case_id"])

    def test_no_case_allows_live_trading(self) -> None:
        self.assert_no_unsafe_phrase("allow live trading")
        self.assert_no_unsafe_phrase("live trading supported")
        self.assert_no_unsafe_phrase("enable live trading")
        self.assert_no_unsafe_phrase("recommend live trading")

    def test_no_case_allows_increasing_notional(self) -> None:
        self.assert_no_unsafe_phrase("increase notional allowed")
        self.assert_no_unsafe_phrase("allow increasing notional")
        self.assert_no_unsafe_phrase("recommend increasing notional")

    def test_no_case_allows_automation(self) -> None:
        self.assert_no_unsafe_phrase("automation allowed")
        self.assert_no_unsafe_phrase("enable automation")
        self.assert_no_unsafe_phrase("recommend automation")

    def test_validator_passes_current_dataset(self) -> None:
        self.assertTrue(self.result.passed, self.result.errors)

    def test_validator_fails_on_missing_required_field(self) -> None:
        cases = copy.deepcopy(self.cases)
        cases[0].pop("case_id")

        result = negative_case_dataset.validate_dataset(cases)

        self.assertFalse(result.passed)
        self.assert_error_contains(result, "missing required field")

    def test_validator_fails_on_insufficient_no_trade_cases(self) -> None:
        cases = [
            case
            for case in copy.deepcopy(self.cases)
            if case["expected_decision"] != "NO_TRADE"
        ]

        result = negative_case_dataset.validate_dataset(cases)

        self.assertFalse(result.passed)
        self.assert_error_contains(result, "at least 10 explicit NO_TRADE cases")

    def test_validator_fails_on_missing_required_category(self) -> None:
        cases = [
            case
            for case in copy.deepcopy(self.cases)
            if case["category"] != "Live trading assumption"
        ]

        result = negative_case_dataset.validate_dataset(cases)

        self.assertFalse(result.passed)
        self.assert_error_contains(result, "missing required categories")

    def test_validator_fails_on_live_trading_recommendation(self) -> None:
        cases = copy.deepcopy(self.cases)
        cases[0]["expected_journal_note"] = "recommend live trading"

        result = negative_case_dataset.validate_dataset(cases)

        self.assertFalse(result.passed)
        self.assert_error_contains(result, "unsafe recommendation detected")

    def test_report_renderer_includes_required_safety_statements(self) -> None:
        report = negative_case_dataset.render_summary_report(self.result)

        self.assertIn("Live trading remains unsupported.", report)
        self.assertIn("Increasing notional remains prohibited.", report)
        self.assertIn("Automation remains prohibited.", report)

    def test_validator_does_not_call_alpaca_or_send_orders(self) -> None:
        source = (RUNTIME_PATH / "negative_case_dataset.py").read_text(encoding="utf-8")

        self.assertNotIn("urlopen", source)
        self.assertNotIn("/v2/orders", source)
        self.assertNotIn("submit_order", source)
        self.assertNotIn("place_order", source)
        self.assertNotIn("send_paper_order_request", source)

    def test_validator_does_not_enable_execution_or_llm_calls(self) -> None:
        source = (RUNTIME_PATH / "negative_case_dataset.py").read_text(encoding="utf-8")

        self.assertNotIn("PAPER_ORDER_EXECUTION_ENABLED", source)
        self.assertNotIn("chat.completions", source)
        self.assertNotIn("responses.create", source)
        self.assertNotIn("OpenAI", source)

    def assert_no_unsafe_phrase(self, phrase: str) -> None:
        for case in self.cases:
            self.assertNotIn(phrase, str(case).lower(), case["case_id"])

    def assert_error_contains(
        self,
        result: object,
        expected: str,
    ) -> None:
        errors = getattr(result, "errors")
        self.assertTrue(any(expected in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
