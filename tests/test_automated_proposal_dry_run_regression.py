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


regression = load_module("automated_proposal_dry_run_regression")


class AutomatedProposalDryRunRegressionTests(unittest.TestCase):
    def test_regression_runner_exists(self) -> None:
        self.assertTrue(hasattr(regression, "run_automated_proposal_dry_run_regression"))

    def test_strong_proposal_scenario_passes_expected_result(self) -> None:
        result = by_id(run_regression(), "strong_proposal_fixture")

        self.assertTrue(result.passed, result.failure_reason)
        self.assertEqual(result.decision, "TRADE_PROPOSAL")
        self.assertEqual(result.strategy_evaluation_status, "PASS")
        self.assertFalse(result.paper_order_request_created)
        self.assertFalse(result.broker_execution_readiness)

    def test_weak_setup_scenario_passes_expected_result(self) -> None:
        result = by_id(run_regression(), "weak_setup_fixture")

        self.assertTrue(result.passed, result.failure_reason)
        self.assertIn(result.decision, {"REJECT", "NO_TRADE"})
        self.assertEqual(result.evaluation_gate_status, "EVALUATION_GATE_BLOCKED")

    def test_no_trade_scenario_passes_expected_result(self) -> None:
        result = by_id(run_regression(), "no_trade_fixture")

        self.assertTrue(result.passed, result.failure_reason)
        self.assertEqual(result.decision, "NO_TRADE")
        self.assertEqual(result.final_status, "AUTOMATED_DRY_RUN_NO_TRADE")

    def test_data_integrity_failure_scenario_blocks(self) -> None:
        result = by_id(run_regression(), "data_integrity_failure_fixture")

        self.assertTrue(result.passed, result.failure_reason)
        self.assertEqual(result.final_status, "AUTOMATED_DRY_RUN_BLOCKED")
        self.assertIn("Data integrity failed", result.blocked_condition)

    def test_multiple_symbol_scenario_blocks(self) -> None:
        result = by_id(run_regression(), "multiple_symbol_attempt")

        self.assertTrue(result.passed, result.failure_reason)
        self.assertEqual(result.final_status, "AUTOMATED_DRY_RUN_BLOCKED")
        self.assertIn("Exactly one symbol", result.blocked_condition)

    def test_execution_flag_enabled_scenario_blocks(self) -> None:
        result = by_id(run_regression(), "execution_flag_enabled_attempt")

        self.assertTrue(result.passed, result.failure_reason)
        self.assertEqual(result.final_status, "AUTOMATED_DRY_RUN_BLOCKED")
        self.assertIn("PAPER_ORDER_EXECUTION_ENABLED=true", result.blocked_condition)

    def test_no_scenario_creates_paper_order_request(self) -> None:
        self.assertFalse(any(result.paper_order_request_created for result in run_regression().results))

    def test_no_scenario_requests_human_approval(self) -> None:
        self.assertFalse(any(result.human_approval_requested for result in run_regression().results))

    def test_no_scenario_requests_manual_execution_confirmation(self) -> None:
        self.assertFalse(
            any(result.manual_execution_confirmation_requested for result in run_regression().results)
        )

    def test_no_scenario_sends_orders(self) -> None:
        self.assertFalse(any(result.order_sent for result in run_regression().results))

    def test_no_scenario_creates_broker_execution_readiness(self) -> None:
        self.assertFalse(any(result.broker_execution_readiness for result in run_regression().results))

    def test_regression_report_is_generated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run = regression.run_automated_proposal_dry_run_regression(
                output_root=Path(tmp) / "regression",
                scenario_report_root=Path(tmp) / "scenario_reports",
                write_report=True,
                write_scenario_reports=True,
            )

            self.assertEqual(run.final_status, "PASS")
            self.assertIsNotNone(run.report_path)
            self.assertTrue(Path(run.report_path or "").exists())
            self.assertTrue(all(result.report_path for result in run.results))

    def test_regression_report_includes_required_proof_statements(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run = regression.run_automated_proposal_dry_run_regression(
                output_root=Path(tmp) / "regression",
                scenario_report_root=Path(tmp) / "scenario_reports",
                write_report=True,
                write_scenario_reports=True,
            )
            rendered = Path(run.report_path or "").read_text(encoding="utf-8")

        self.assertIn("Proof no Paper Order Request was created: True", rendered)
        self.assertIn("Proof no Human Approval was requested: True", rendered)
        self.assertIn("Proof no Manual Execution Confirmation was requested: True", rendered)
        self.assertIn("Proof no order was sent: True", rendered)
        self.assertIn("Proof no broker execution readiness was created: True", rendered)
        self.assertIn("Live trading remains unsupported.", rendered)

    def test_no_alpaca_order_api_calls_exist(self) -> None:
        source = source_text()

        self.assertNotIn("alpaca_paper_order_adapter", source)
        self.assertNotIn("UrlLibAlpacaPaperOrderClient", source)
        self.assertNotIn("urlopen", source)
        self.assertNotIn("/v2/orders", source)

    def test_no_live_trading_exists(self) -> None:
        self.assertFalse(any(result.live_trading_assumption for result in run_regression().results))
        self.assertNotIn("LIVE_ALPACA", source_text())
        self.assertNotIn("api.alpaca.markets", source_text())

    def test_no_batch_behavior_exists(self) -> None:
        self.assertNotIn("batch_order", source_text().lower())

    def test_no_cancel_replace_exists(self) -> None:
        self.assertNotIn("cancel_order", source_text())
        self.assertNotIn("replace_order", source_text())

    def test_no_credentials_env_files_or_llm_calls(self) -> None:
        before = env_files()
        run_regression()

        self.assertEqual(before, env_files())
        self.assertNotIn("chat.completions", source_text())
        self.assertNotIn("responses.create", source_text())
        self.assertNotIn("OpenAI", source_text())


def run_regression():
    return regression.run_automated_proposal_dry_run_regression(
        write_report=False,
        write_scenario_reports=False,
    )


def by_id(run, scenario_id: str):
    matches = [result for result in run.results if result.scenario_id == scenario_id]
    assert len(matches) == 1
    return matches[0]


def source_text() -> str:
    return (RUNTIME_PATH / "automated_proposal_dry_run_regression.py").read_text(
        encoding="utf-8"
    )


def env_files() -> set[str]:
    return {path.as_posix() for path in ROOT.glob(".env*")}


if __name__ == "__main__":
    unittest.main()
