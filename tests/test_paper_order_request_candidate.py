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


candidate_module = load_module("paper_order_request_candidate")


class PaperOrderRequestCandidateTests(unittest.TestCase):
    def test_candidate_model_exists(self) -> None:
        self.assertTrue(hasattr(candidate_module, "PaperOrderRequestCandidate"))

    def test_candidate_validator_exists(self) -> None:
        self.assertTrue(hasattr(candidate_module, "validate_candidate"))

    def test_valid_trade_proposal_creates_candidate(self) -> None:
        result = create_candidate()

        self.assertEqual(result.final_status, candidate_module.PAPER_ORDER_CANDIDATE_CREATED)
        self.assertIsNotNone(result.candidate)

    def test_no_trade_does_not_create_candidate(self) -> None:
        result = create_candidate(scenario="no_trade")

        self.assertEqual(result.final_status, candidate_module.PAPER_ORDER_CANDIDATE_BLOCKED)
        self.assertIsNone(result.candidate)
        self.assertIn("TRADE_PROPOSAL", result.reason)

    def test_reject_does_not_create_candidate(self) -> None:
        result = create_candidate(scenario="reject")

        self.assertEqual(result.final_status, candidate_module.PAPER_ORDER_CANDIDATE_BLOCKED)
        self.assertIsNone(result.candidate)
        self.assertIn("TRADE_PROPOSAL", result.reason)

    def test_data_integrity_failure_blocks_candidate(self) -> None:
        result = create_candidate(scenario="data_fail")

        self.assertEqual(result.final_status, candidate_module.PAPER_ORDER_CANDIDATE_BLOCKED)
        self.assertIn("Data Integrity PASS", result.reason)

    def test_strategy_evaluation_failure_blocks_candidate(self) -> None:
        result = create_candidate(scenario="gate_fail")

        self.assertEqual(result.final_status, candidate_module.PAPER_ORDER_CANDIDATE_BLOCKED)
        self.assertIn("Strategy Evaluation PASS", result.reason)

    def test_evaluation_gate_blocked_blocks_candidate(self) -> None:
        result = create_candidate(scenario="gate_fail")

        self.assertEqual(result.final_status, candidate_module.PAPER_ORDER_CANDIDATE_BLOCKED)
        self.assertIn("Evaluation-First Gate PASS", result.reason)

    def test_negative_case_regression_failure_blocks_candidate(self) -> None:
        result = create_candidate(scenario="negative_fail")

        self.assertEqual(result.final_status, candidate_module.PAPER_ORDER_CANDIDATE_BLOCKED)
        self.assertIn("Negative Case Regression PASS", result.reason)

    def test_known_negative_case_failure_pattern_blocks_candidate(self) -> None:
        result = create_candidate(known_negative_case_failure_pattern=True)

        self.assertEqual(result.final_status, candidate_module.PAPER_ORDER_CANDIDATE_BLOCKED)
        self.assertIn("known negative-case failure pattern", result.reason)

    def test_risk_dry_run_failure_blocks_candidate(self) -> None:
        result = create_candidate(scenario="risk_fail")

        self.assertEqual(result.final_status, candidate_module.PAPER_ORDER_CANDIDATE_BLOCKED)
        self.assertIn("Risk Manager dry-run/read-only PASS", result.reason)

    def test_execution_flag_true_blocks_candidate(self) -> None:
        with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": "true"}):
            result = candidate_module.create_paper_order_request_candidate(
                symbols=["SIM"],
                write_artifacts=False,
            )

        self.assertEqual(result.final_status, candidate_module.PAPER_ORDER_CANDIDATE_BLOCKED)
        self.assertIn("PAPER_ORDER_EXECUTION_ENABLED=true", result.reason)

    def test_multiple_symbols_block_candidate(self) -> None:
        result = candidate_module.create_paper_order_request_candidate(
            symbols=["SIM", "SPY"],
            write_artifacts=False,
        )

        self.assertEqual(result.final_status, candidate_module.PAPER_ORDER_CANDIDATE_BLOCKED)
        self.assertIn("one symbol only", result.reason)

    def test_paper_send_readiness_blocks_candidate(self) -> None:
        result = create_candidate(paper_send_readiness=True)

        self.assertEqual(result.final_status, candidate_module.PAPER_ORDER_CANDIDATE_BLOCKED)
        self.assertIn("paper send readiness", result.reason)

    def test_broker_execution_readiness_blocks_candidate(self) -> None:
        result = create_candidate(broker_execution_readiness=True)

        self.assertEqual(result.final_status, candidate_module.PAPER_ORDER_CANDIDATE_BLOCKED)
        self.assertIn("broker execution readiness", result.reason)

    def test_candidate_has_paper_trading_only_true(self) -> None:
        self.assertTrue(create_candidate().candidate.paper_trading_only)

    def test_candidate_has_human_approval_required_true(self) -> None:
        self.assertTrue(create_candidate().candidate.human_approval_required)

    def test_candidate_has_manual_execution_confirmation_required_true(self) -> None:
        self.assertTrue(create_candidate().candidate.manual_execution_confirmation_required)

    def test_candidate_has_broker_execution_allowed_false(self) -> None:
        self.assertFalse(create_candidate().candidate.broker_execution_allowed)

    def test_candidate_has_live_trading_allowed_false(self) -> None:
        self.assertFalse(create_candidate().candidate.live_trading_allowed)

    def test_candidate_artifact_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = candidate_module.create_paper_order_request_candidate(
                symbols=["SIM"],
                output_root=Path(tmp),
            )

            self.assertTrue(Path(result.report_path or "").exists())
            rendered = Path(result.report_path or "").read_text(encoding="utf-8")
            self.assertIn("No order was sent.", rendered)
            self.assertIn("No finalized Paper Order Request was created.", rendered)
            self.assertIn("No broker execution readiness was created.", rendered)
            self.assertIn("Live trading remains unsupported.", rendered)

    def test_candidate_journal_entry_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = candidate_module.create_paper_order_request_candidate(
                symbols=["SIM"],
                output_root=Path(tmp),
            )

            self.assertTrue(Path(result.journal_path or "").exists())

    def test_no_finalized_paper_order_request_is_created(self) -> None:
        self.assertFalse(create_candidate().finalized_paper_order_request_created)

    def test_no_human_approval_is_requested_automatically(self) -> None:
        result = create_candidate()

        self.assertFalse(result.human_approval_requested)
        self.assertNotIn("human_approval", source_imports())

    def test_no_manual_execution_confirmation_is_requested(self) -> None:
        result = create_candidate()

        self.assertFalse(result.manual_execution_confirmation_requested)
        self.assertNotIn("manual_execution_confirmation", source_imports())

    def test_no_order_is_sent(self) -> None:
        result = create_candidate()

        self.assertFalse(result.order_sent)
        self.assertNotIn("submit_order", source_text())
        self.assertNotIn("place_order", source_text())
        self.assertNotIn("send_paper_order_request", source_text())

    def test_no_broker_execution_readiness_is_created(self) -> None:
        self.assertFalse(create_candidate().broker_execution_readiness)

    def test_no_alpaca_order_api_calls_exist(self) -> None:
        source = source_text()

        self.assertNotIn("alpaca_paper_order_adapter", source)
        self.assertNotIn("UrlLibAlpacaPaperOrderClient", source)
        self.assertNotIn("urlopen", source)
        self.assertNotIn("/v2/orders", source)

    def test_no_live_trading_exists(self) -> None:
        source = source_text()

        self.assertFalse(create_candidate().live_trading_assumption)
        self.assertNotIn("LIVE_ALPACA", source)
        self.assertNotIn("api.alpaca.markets", source)

    def test_no_batch_behavior_exists(self) -> None:
        self.assertNotIn("batch_order", source_text().lower())

    def test_no_cancel_replace_exists(self) -> None:
        source = source_text()

        self.assertNotIn("cancel_order", source)
        self.assertNotIn("replace_order", source)

    def test_no_credentials_env_files_or_llm_calls(self) -> None:
        before = env_files()
        create_candidate()

        self.assertEqual(before, env_files())
        self.assertNotIn("chat.completions", source_text())
        self.assertNotIn("responses.create", source_text())
        self.assertNotIn("OpenAI", source_text())


def create_candidate(**overrides):
    with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": ""}):
        return candidate_module.create_paper_order_request_candidate(
            symbols=["SIM"],
            write_artifacts=False,
            **overrides,
        )


def source_text() -> str:
    return (RUNTIME_PATH / "paper_order_request_candidate.py").read_text(encoding="utf-8")


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
