from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


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


automated_dry_run = load_module("automated_proposal_dry_run")


class AutomatedProposalDryRunTests(unittest.TestCase):
    def test_runner_works_in_dry_run_only(self) -> None:
        report = run(scenario="proposal")

        self.assertEqual(report.mode, automated_dry_run.DRY_RUN_ONLY)
        self.assertEqual(
            report.final_status,
            automated_dry_run.AUTOMATED_DRY_RUN_PROPOSAL_CREATED,
        )

    def test_runner_rejects_if_execution_flag_true(self) -> None:
        with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": "true"}):
            report = automated_dry_run.run_automated_proposal_dry_run(
                symbols=["SIM"],
                scenario="proposal",
                write_artifacts=False,
            )

        self.assertEqual(report.final_status, automated_dry_run.AUTOMATED_DRY_RUN_BLOCKED)
        self.assertIn("PAPER_ORDER_EXECUTION_ENABLED=true", report.reason)

    def test_runner_rejects_more_than_one_symbol(self) -> None:
        report = automated_dry_run.run_automated_proposal_dry_run(
            symbols=["SIM", "SPY"],
            write_artifacts=False,
        )

        self.assertEqual(report.final_status, automated_dry_run.AUTOMATED_DRY_RUN_BLOCKED)
        self.assertIn("Exactly one symbol", report.reason)

    def test_runner_can_produce_no_trade(self) -> None:
        report = run(scenario="no_trade")

        self.assertEqual(report.decision, automated_dry_run.NO_TRADE)
        self.assertEqual(report.final_status, automated_dry_run.AUTOMATED_DRY_RUN_NO_TRADE)

    def test_runner_can_produce_reject(self) -> None:
        report = run(scenario="reject")

        self.assertEqual(report.decision, automated_dry_run.REJECT)
        self.assertEqual(report.final_status, automated_dry_run.AUTOMATED_DRY_RUN_REJECTED)

    def test_runner_can_produce_trade_proposal(self) -> None:
        report = run(scenario="proposal")

        self.assertEqual(report.decision, automated_dry_run.TRADE_PROPOSAL)
        self.assertEqual(
            report.final_status,
            automated_dry_run.AUTOMATED_DRY_RUN_PROPOSAL_CREATED,
        )

    def test_data_integrity_failure_blocks_flow(self) -> None:
        report = run(scenario="data_fail")

        self.assertEqual(report.final_status, automated_dry_run.AUTOMATED_DRY_RUN_BLOCKED)
        self.assertEqual(report.data_integrity_status, "FAIL")

    def test_evaluation_gate_failure_blocks_flow(self) -> None:
        report = run(scenario="gate_fail")

        self.assertEqual(report.final_status, automated_dry_run.AUTOMATED_DRY_RUN_BLOCKED)
        self.assertEqual(report.evaluation_gate_status, "EVALUATION_GATE_BLOCKED")

    def test_negative_case_failure_blocks_flow(self) -> None:
        report = run(scenario="negative_fail")

        self.assertEqual(report.final_status, automated_dry_run.AUTOMATED_DRY_RUN_BLOCKED)
        self.assertEqual(report.negative_case_regression_status, "FAIL")

    def test_risk_dry_run_failure_blocks_flow(self) -> None:
        report = run(scenario="risk_fail")

        self.assertEqual(report.final_status, automated_dry_run.AUTOMATED_DRY_RUN_BLOCKED)
        self.assertEqual(report.risk_dry_run_status, "RISK_REJECTED")

    def test_runner_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = automated_dry_run.run_automated_proposal_dry_run(
                symbols=["SIM"],
                output_root=Path(tmp),
            )

            self.assertIsNotNone(report.report_path)
            self.assertTrue(Path(report.report_path or "").exists())
            rendered = Path(report.report_path or "").read_text(encoding="utf-8")
            self.assertIn("No order was sent.", rendered)
            self.assertIn("No Paper Order Request was created.", rendered)
            self.assertIn("Live trading remains unsupported.", rendered)

    def test_runner_writes_journal_dry_run_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = automated_dry_run.run_automated_proposal_dry_run(
                symbols=["SIM"],
                output_root=Path(tmp),
            )

            self.assertIsNotNone(report.journal_path)
            self.assertTrue(Path(report.journal_path or "").exists())

    def test_runner_never_creates_paper_order_request(self) -> None:
        report = run()

        self.assertFalse(report.paper_order_request_created)
        self.assertNotIn("paper_order_request", source_imports())

    def test_runner_never_requests_human_approval(self) -> None:
        report = run()

        self.assertFalse(report.human_approval_requested)
        self.assertNotIn("human_approval", source_imports())

    def test_runner_never_requests_manual_execution_confirmation(self) -> None:
        report = run()

        self.assertFalse(report.manual_execution_confirmation_requested)
        self.assertNotIn("manual_execution_confirmation", source_imports())

    def test_runner_never_sends_orders(self) -> None:
        report = run()

        self.assertFalse(report.paper_send_readiness)
        self.assertNotIn("submit_order", source_text())
        self.assertNotIn("place_order", source_text())
        self.assertNotIn("send_paper_order_request", source_text())

    def test_runner_never_creates_paper_send_readiness(self) -> None:
        report = run()

        self.assertFalse(report.paper_send_readiness)

    def test_runner_never_creates_broker_execution_readiness(self) -> None:
        report = run()

        self.assertFalse(report.broker_execution_readiness)

    def test_no_alpaca_order_api_calls_exist(self) -> None:
        source = source_text()

        self.assertNotIn("alpaca_paper_order_adapter", source)
        self.assertNotIn("UrlLibAlpacaPaperOrderClient", source)
        self.assertNotIn("urlopen", source)
        self.assertNotIn("/v2/orders", source)

    def test_no_live_trading_exists(self) -> None:
        source = source_text()
        report = run()

        self.assertFalse(report.live_trading_assumption)
        self.assertNotIn("LIVE_ALPACA", source)
        self.assertNotIn("api.alpaca.markets", source)

    def test_no_batch_behavior_exists(self) -> None:
        report = run()

        self.assertFalse(report.batch_behavior)
        self.assertNotIn("batch_order", source_text().lower())

    def test_no_cancel_replace_exists(self) -> None:
        source = source_text()
        report = run()

        self.assertFalse(report.cancel_replace_behavior)
        self.assertNotIn("cancel_order", source)
        self.assertNotIn("replace_order", source)

    def test_no_credentials_env_files_or_llm_calls(self) -> None:
        before = env_files()
        run()

        self.assertEqual(before, env_files())
        self.assertNotIn("chat.completions", source_text())
        self.assertNotIn("responses.create", source_text())
        self.assertNotIn("OpenAI", source_text())


def run(*, scenario: str = "proposal"):
    with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": ""}):
        return automated_dry_run.run_automated_proposal_dry_run(
            symbols=["SIM"],
            scenario=scenario,
            write_artifacts=False,
        )


def source_text() -> str:
    return (RUNTIME_PATH / "automated_proposal_dry_run.py").read_text(encoding="utf-8")


def source_imports() -> str:
    return "\n".join(
        line
        for line in source_text().splitlines()
        if line.startswith("from ") or line.startswith("import ")
    )


def env_files() -> set[str]:
    return {path.as_posix() for path in ROOT.glob(".env*")}


if __name__ == "__main__":
    unittest.main()
