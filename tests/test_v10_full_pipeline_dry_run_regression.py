from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "runtime"

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


regression = load_module("v10_full_pipeline_dry_run_regression")


class V10FullPipelineDryRunRegressionTests(unittest.TestCase):
    def test_regression_runner_exists(self) -> None:
        self.assertTrue(hasattr(regression, "run_v10_full_pipeline_dry_run_regression"))

    def test_full_valid_v10_pipeline_reaches_send_allowed(self) -> None:
        result = by_id(run_regression(), "full_valid_v10_pipeline")

        self.assertTrue(result.passed, result.failure_reason)
        self.assertEqual(result.dry_run_decision, "TRADE_PROPOSAL")
        self.assertEqual(result.candidate_status, "PAPER_ORDER_CANDIDATE_CREATED")
        self.assertEqual(result.review_status, "HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST")
        self.assertEqual(result.finalized_request_status, "PAPER_ORDER_REQUEST_FINALIZED")
        self.assertEqual(
            result.manual_confirmation_status,
            "MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT",
        )
        self.assertEqual(result.preflight_status, "PAPER_ORDER_SEND_ALLOWED")

    def test_candidate_blocked_scenario_blocks_before_review(self) -> None:
        result = by_id(run_regression(), "candidate_blocked")

        self.assertTrue(result.passed, result.failure_reason)
        self.assertNotEqual(result.candidate_status, "PAPER_ORDER_CANDIDATE_CREATED")
        self.assertIsNone(result.review_status)
        self.assertIsNone(result.finalized_request_status)
        self.assertIsNone(result.manual_confirmation_status)
        self.assertIsNone(result.preflight_status)

    def test_human_review_rejected_blocks_before_finalized_request(self) -> None:
        result = by_id(run_regression(), "human_review_rejected")

        self.assertTrue(result.passed, result.failure_reason)
        self.assertEqual(result.candidate_status, "PAPER_ORDER_CANDIDATE_CREATED")
        self.assertEqual(result.review_status, "HUMAN_REVIEW_REJECTED")
        self.assertIsNone(result.finalized_request_status)
        self.assertIsNone(result.manual_confirmation_status)
        self.assertIsNone(result.preflight_status)

    def test_manual_confirmation_rejected_blocks_before_preflight_allowed(self) -> None:
        result = by_id(run_regression(), "manual_confirmation_rejected")

        self.assertTrue(result.passed, result.failure_reason)
        self.assertEqual(result.finalized_request_status, "PAPER_ORDER_REQUEST_FINALIZED")
        self.assertEqual(result.manual_confirmation_status, "MANUAL_EXECUTION_REJECTED")
        self.assertIsNone(result.preflight_status)

    def test_preflight_blocked_scenario_produces_send_blocked(self) -> None:
        result = by_id(run_regression(), "preflight_blocked")

        self.assertTrue(result.passed, result.failure_reason)
        self.assertEqual(result.preflight_status, "PAPER_ORDER_SEND_BLOCKED")
        self.assertEqual(result.final_status, "BLOCKED_AT_PREFLIGHT")

    def test_execution_flag_true_blocks_before_progression(self) -> None:
        result = by_id(run_regression(), "paper_order_execution_enabled_true")

        self.assertTrue(result.passed, result.failure_reason)
        self.assertEqual(result.blocked_stage, "BLOCKED_BEFORE_PROGRESSION")
        self.assertIsNone(result.review_status)
        self.assertIsNone(result.finalized_request_status)
        self.assertIsNone(result.manual_confirmation_status)
        self.assertIsNone(result.preflight_status)

    def test_no_scenario_sends_orders(self) -> None:
        self.assertFalse(any(result.order_sent for result in run_regression().results))

    def test_no_scenario_calls_order_api(self) -> None:
        self.assertFalse(
            any(result.alpaca_order_api_called for result in run_regression().results)
        )
        source = source_text()
        self.assertNotIn("UrlLibAlpacaPaperOrderClient", source)
        self.assertNotIn("urlopen", source)
        self.assertNotIn("/v2/orders", source)

    def test_no_scenario_creates_broker_execution_readiness(self) -> None:
        self.assertFalse(
            any(result.broker_execution_readiness for result in run_regression().results)
        )

    def test_no_scenario_creates_live_trading_readiness(self) -> None:
        self.assertFalse(
            any(result.live_trading_readiness for result in run_regression().results)
        )
        self.assertNotIn("api.alpaca.markets", source_text())

    def test_no_scenario_creates_batch_behavior(self) -> None:
        self.assertFalse(any(result.batch_behavior for result in run_regression().results))
        self.assertNotIn("batch_order", source_text().lower())

    def test_no_scenario_creates_cancel_replace_behavior(self) -> None:
        self.assertFalse(
            any(result.cancel_replace_behavior for result in run_regression().results)
        )
        self.assertNotIn("cancel_order", source_text())
        self.assertNotIn("replace_order", source_text())

    def test_report_is_generated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run = regression.run_v10_full_pipeline_dry_run_regression(
                output_root=Path(tmp),
                write_report=True,
            )

            self.assertEqual(run.final_status, "PASS")
            self.assertIsNotNone(run.report_path)
            self.assertTrue(Path(run.report_path or "").exists())
            self.assertEqual(
                Path(run.report_path or "").name,
                "V10_FULL_PIPELINE_DRY_RUN_REGRESSION_REPORT.md",
            )

    def test_report_contains_required_proof_statements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run = regression.run_v10_full_pipeline_dry_run_regression(
                output_root=Path(tmp),
                write_report=True,
            )
            rendered = Path(run.report_path or "").read_text(encoding="utf-8")

        self.assertIn("Proof no order was sent: True", rendered)
        self.assertIn("Proof no Alpaca order API was called: True", rendered)
        self.assertIn(
            "Proof PAPER_ORDER_EXECUTION_ENABLED was not enabled except blocked scenario: True",
            rendered,
        )
        self.assertIn("Proof no broker execution readiness was created: True", rendered)
        self.assertIn("Live trading remains unsupported.", rendered)
        self.assertIn("Increasing notional remains prohibited.", rendered)
        self.assertIn(
            "Automation beyond approved dry-run/candidate flow remains prohibited.",
            rendered,
        )

    def test_full_regression_passes(self) -> None:
        self.assertEqual(run_regression().final_status, "PASS")


def run_regression():
    return regression.run_v10_full_pipeline_dry_run_regression(write_report=False)


def by_id(run, scenario_id: str):
    matches = [result for result in run.results if result.scenario_id == scenario_id]
    assert len(matches) == 1
    return matches[0]


def source_text() -> str:
    return (RUNTIME_PATH / "v10_full_pipeline_dry_run_regression.py").read_text(
        encoding="utf-8"
    )


if __name__ == "__main__":
    unittest.main()
