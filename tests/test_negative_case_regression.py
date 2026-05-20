from __future__ import annotations

import copy
import importlib.util
import sys
import tempfile
import unittest
from dataclasses import replace
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
negative_case_regression = load_module("negative_case_regression")


class NegativeCaseRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = negative_case_dataset.load_dataset(DATASET_PATH)
        self.report = negative_case_regression.run_negative_case_regression(
            DATASET_PATH,
            write_report=False,
        )

    def test_every_case_is_evaluated(self) -> None:
        self.assertEqual(len(self.report.case_results), len(self.cases))

    def test_every_case_produces_deterministic_evaluation_result(self) -> None:
        second = negative_case_regression.run_negative_case_regression(
            DATASET_PATH,
            write_report=False,
        )

        self.assertEqual(
            [result.as_dict() for result in self.report.case_results],
            [result.as_dict() for result in second.case_results],
        )

    def test_reject_cases_do_not_pass_gate(self) -> None:
        for result in self.report.case_results:
            if result.expected_decision == "REJECT":
                self.assertNotEqual(result.gate_status, "EVALUATION_GATE_PASSED", result.case_id)

    def test_no_trade_cases_are_recognized(self) -> None:
        for result in self.report.case_results:
            if result.expected_decision == "NO_TRADE":
                self.assertTrue(result.no_trade_recognized, result.case_id)
                self.assertEqual(result.actual_decision, "NO_TRADE")

    def test_block_evaluation_gate_cases_are_blocked_by_gate(self) -> None:
        for result in self.report.case_results:
            if result.expected_decision == "BLOCK_EVALUATION_GATE":
                self.assertEqual(result.gate_status, "EVALUATION_GATE_BLOCKED", result.case_id)

    def test_block_human_approval_cases_do_not_reach_human_approval(self) -> None:
        for result in self.report.case_results:
            if result.expected_decision == "BLOCK_HUMAN_APPROVAL":
                self.assertTrue(result.blocked_before_human_approval, result.case_id)

    def test_block_paper_request_cases_do_not_create_paper_request(self) -> None:
        for result in self.report.case_results:
            if result.expected_decision == "BLOCK_PAPER_REQUEST":
                self.assertFalse(result.paper_send_readiness, result.case_id)
                self.assertEqual(result.actual_decision, "BLOCK_PAPER_REQUEST")

    def test_no_negative_case_produces_paper_send_readiness(self) -> None:
        self.assertFalse(any(result.paper_send_readiness for result in self.report.case_results))

    def test_no_negative_case_produces_broker_execution_readiness(self) -> None:
        self.assertFalse(any(result.broker_execution_readiness for result in self.report.case_results))

    def test_live_trading_assumption_cases_blocked_100_percent(self) -> None:
        self.assertEqual(self.report.summary.live_trading_assumption_block_rate, 1.0)

    def test_missing_fixed_risk_cases_blocked_100_percent(self) -> None:
        cases = copy.deepcopy(self.cases)
        cases[0]["input_summary"] += " missing fixed risk"
        report = negative_case_regression.run_negative_case_regression_from_cases(
            cases,
            write_report=False,
        )

        self.assertEqual(report.summary.missing_fixed_risk_block_rate, 1.0)
        self.assertGreaterEqual(report.summary.missing_fixed_risk_blocked_count, 1)

    def test_missing_journal_readiness_cases_blocked_100_percent(self) -> None:
        self.assertEqual(self.report.summary.missing_journal_readiness_block_rate, 1.0)

    def test_rubber_stamping_cases_detected_or_blocked_100_percent(self) -> None:
        self.assertEqual(self.report.summary.rubber_stamping_detection_rate, 1.0)

    def test_below_90_blocked_before_human_approval_produces_improve_gate(self) -> None:
        results = list(self.report.case_results)
        broken_count = max(4, int(len(results) * 0.11) + 1)
        for index in range(broken_count):
            results[index] = replace(results[index], blocked_before_human_approval=False)

        summary = negative_case_regression._summarize(results)

        self.assertEqual(summary.recommendation, negative_case_regression.IMPROVE_GATE)

    def test_below_90_no_trade_recognition_produces_improve_gate(self) -> None:
        results = [
            replace(result, no_trade_recognized=False)
            if result.expected_decision == "NO_TRADE"
            else result
            for result in self.report.case_results
        ]

        summary = negative_case_regression._summarize(results)

        self.assertEqual(summary.recommendation, negative_case_regression.IMPROVE_GATE)

    def test_below_90_weak_setup_rejection_produces_improve_gate(self) -> None:
        results = [
            replace(result, weak_setup_rejected=False)
            if result.expected_decision == "REJECT"
            and result.category in negative_case_dataset.WEAK_SETUP_CATEGORIES
            else result
            for result in self.report.case_results
        ]

        summary = negative_case_regression._summarize(results)

        self.assertEqual(summary.recommendation, negative_case_regression.IMPROVE_GATE)

    def test_live_trading_pass_produces_hold(self) -> None:
        results = [
            replace(result, live_trading_assumption_blocked=False)
            if result.live_trading_assumption_case
            else result
            for result in self.report.case_results
        ]

        summary = negative_case_regression._summarize(results)

        self.assertEqual(summary.recommendation, negative_case_regression.HOLD)

    def test_missing_fixed_risk_pass_produces_hold(self) -> None:
        cases = copy.deepcopy(self.cases)
        cases[0]["input_summary"] += " missing fixed risk"
        report = negative_case_regression.run_negative_case_regression_from_cases(
            cases,
            write_report=False,
        )
        results = [
            replace(result, missing_fixed_risk_blocked=False)
            if result.missing_fixed_risk_case
            else result
            for result in report.case_results
        ]

        summary = negative_case_regression._summarize(results)

        self.assertEqual(summary.recommendation, negative_case_regression.HOLD)

    def test_missing_journal_readiness_pass_produces_hold(self) -> None:
        results = [
            replace(result, missing_journal_readiness_blocked=False)
            if result.missing_journal_readiness_case
            else result
            for result in self.report.case_results
        ]

        summary = negative_case_regression._summarize(results)

        self.assertEqual(summary.recommendation, negative_case_regression.HOLD)

    def test_report_is_generated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = negative_case_regression.run_negative_case_regression(
                DATASET_PATH,
                output_root=Path(tmp),
            )

            self.assertIsNotNone(report.report_path)
            self.assertTrue(Path(report.report_path or "").exists())

    def test_report_contains_required_prohibition_statements(self) -> None:
        rendered = negative_case_regression._render_report(
            self.report.case_results,
            self.report.summary,
        )

        self.assertIn("Live trading remains unsupported.", rendered)
        self.assertIn("Increasing notional remains prohibited.", rendered)
        self.assertIn("Automation remains prohibited.", rendered)

    def test_no_alpaca_imports_or_broker_calls_exist(self) -> None:
        source = source_text()
        import_lines = [
            line.strip().lower()
            for line in source.splitlines()
            if line.strip().startswith(("import ", "from "))
        ]

        self.assertFalse(any("alpaca" in line for line in import_lines))
        self.assertNotIn("urlopen", source)
        self.assertNotIn("/v2/orders", source)

    def test_no_order_sends_or_execution_flag_exist(self) -> None:
        source = source_text()

        self.assertNotIn("submit_order", source)
        self.assertNotIn("place_order", source)
        self.assertNotIn("send_paper_order_request", source)
        self.assertNotIn("PAPER_ORDER_EXECUTION_ENABLED", source)

    def test_no_automation_or_llm_calls_exist(self) -> None:
        source = source_text()

        self.assertNotIn("scheduler", source.lower())
        self.assertNotIn("autonomous", source.lower())
        self.assertNotIn("chat.completions", source)
        self.assertNotIn("responses.create", source)
        self.assertNotIn("OpenAI", source)

    def test_no_credentials_or_env_files_are_created(self) -> None:
        before = env_files()
        negative_case_regression.run_negative_case_regression(DATASET_PATH, write_report=False)

        self.assertEqual(before, env_files())


def source_text() -> str:
    return (RUNTIME_PATH / "negative_case_regression.py").read_text(encoding="utf-8")


def env_files() -> set[str]:
    return {path.as_posix() for path in ROOT.glob(".env*")}


if __name__ == "__main__":
    unittest.main()
