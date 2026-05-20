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


controlled = load_module("v10_controlled_paper_send")


class ControlledV10PaperSendTests(unittest.TestCase):
    def test_controlled_v10_paper_send_runner_exists(self) -> None:
        self.assertTrue(hasattr(controlled, "run_controlled_v10_paper_send"))

    def test_blocks_if_full_tests_status_missing(self) -> None:
        result = run_with(controlled.ControlledV10PaperSendConfig(full_tests_status=None))

        self.assert_blocked_with(result, "full tests status is not PASS")

    def test_blocks_if_architecture_validation_missing(self) -> None:
        result = run_with(valid_config(architecture_validation_status=None))

        self.assert_blocked_with(result, "architecture validation status is not PASS")

    def test_blocks_if_v10_full_pipeline_regression_missing(self) -> None:
        result = run_with(valid_config(v10_full_pipeline_regression_status=None))

        self.assert_blocked_with(result, "V10 full pipeline dry-run regression status is not PASS")

    def test_blocks_if_strategy_evaluation_fails(self) -> None:
        result = run_with(valid_config(strategy_evaluation_status="FAIL"))

        self.assert_blocked_with(result, "Strategy Evaluation status is not PASS")

    def test_blocks_if_evaluation_first_gate_fails(self) -> None:
        result = run_with(valid_config(evaluation_gate_status="EVALUATION_GATE_BLOCKED"))

        self.assert_blocked_with(result, "Evaluation-First Gate status is not PASS")

    def test_blocks_if_negative_case_regression_fails(self) -> None:
        result = run_with(valid_config(negative_case_regression_status="FAIL"))

        self.assert_blocked_with(result, "Negative Case Regression status is not PASS")

    def test_blocks_if_candidate_missing(self) -> None:
        result = run_with(valid_config(candidate_scenario="no_trade"))

        self.assert_blocked_with(result, "Paper Order Request Candidate is missing")

    def test_blocks_if_human_review_not_approved(self) -> None:
        result = run_with(valid_config(human_review_status="HUMAN_REVIEW_REJECTED"))

        self.assert_blocked_with(result, "Human Review is not approved")

    def test_blocks_if_finalized_request_missing(self) -> None:
        result = run_with(valid_config(human_review_status="HUMAN_REVIEW_REJECTED"))

        self.assert_blocked_with(result, "Finalized Paper Order Request is missing or not finalized")

    def test_blocks_if_manual_confirmation_missing(self) -> None:
        result = run_with(valid_config(manual_confirmation_status="MANUAL_EXECUTION_REJECTED"))

        self.assert_blocked_with(result, "Manual Execution Confirmation is missing or not confirmed")

    def test_blocks_if_preflight_not_allowed(self) -> None:
        result = run_with(valid_config(live_endpoint_configured=True))

        self.assert_blocked_with(result, "Paper Send Preflight is not PAPER_ORDER_SEND_ALLOWED")

    def test_blocks_if_alpaca_paper_account_not_confirmed(self) -> None:
        result = run_with(valid_config(alpaca_paper_account_confirmed=False))

        self.assert_blocked_with(result, "Alpaca paper account is not confirmed")

    def test_blocks_if_live_endpoint_configured(self) -> None:
        result = run_with(valid_config(live_endpoint_configured=True))

        self.assert_blocked_with(result, "live endpoint configured is blocked")

    def test_blocks_if_execution_flag_not_true_for_final_run(self) -> None:
        result = run_with(valid_config(execution_enabled=False))

        self.assert_blocked_with(result, "PAPER_ORDER_EXECUTION_ENABLED is not true for manual run")

    def test_blocks_notional_over_100(self) -> None:
        result = run_with(valid_config(notional="101"))

        self.assert_blocked_with(result, "notional > 100 USD is blocked")

    def test_blocks_market_order(self) -> None:
        result = run_with(valid_config(order_type="market"))

        self.assert_blocked_with(result, "limit order only is required")

    def test_blocks_non_day_time_in_force(self) -> None:
        result = run_with(valid_config(time_in_force="gtc"))

        self.assert_blocked_with(result, "day time-in-force only is required")

    def test_blocks_short_selling(self) -> None:
        result = run_with(valid_config(short_selling=True))

        self.assert_blocked_with(result, "short selling is blocked")

    def test_blocks_crypto(self) -> None:
        result = run_with(valid_config(crypto=True))

        self.assert_blocked_with(result, "crypto is blocked")

    def test_blocks_options(self) -> None:
        result = run_with(valid_config(options=True))

        self.assert_blocked_with(result, "options are blocked")

    def test_blocks_margin_leverage(self) -> None:
        result = run_with(valid_config(margin_or_leverage=True))

        self.assert_blocked_with(result, "margin/leverage is blocked")

    def test_blocks_extended_hours(self) -> None:
        result = run_with(valid_config(extended_hours=True))

        self.assert_blocked_with(result, "extended hours are blocked")

    def test_blocks_batch_orders(self) -> None:
        result = run_with(valid_config(batch_orders=True))

        self.assert_blocked_with(result, "batch orders are blocked")

    def test_blocks_cancel_replace(self) -> None:
        result = run_with(valid_config(cancel_replace=True))

        self.assert_blocked_with(result, "cancel/replace is blocked")

    def test_sends_exactly_one_mocked_paper_limit_day_order_when_all_gates_pass(self) -> None:
        client = controlled.RecordingControlledPaperClient()
        result = run_with(valid_config(), client=client)

        self.assertEqual(result.final_status, controlled.PAPER_ORDER_SUBMITTED)
        self.assertEqual(result.submitted_order_count, 1)
        self.assertEqual(len(client.payloads), 1)
        payload = client.payloads[0]
        self.assertEqual(payload["type"], "limit")
        self.assertEqual(payload["time_in_force"], "day")
        self.assertEqual(payload["notional"], "100")

    def test_runner_writes_controlled_send_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = controlled.run_controlled_v10_paper_send(
                config=valid_config(execution_enabled=False),
                client=controlled.RecordingControlledPaperClient(),
                output_root=Path(tmp),
            )

            self.assertTrue(Path(result.report_path or "").exists())

    def test_runner_writes_reconciliation_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = controlled.run_controlled_v10_paper_send(
                config=valid_config(execution_enabled=False),
                client=controlled.RecordingControlledPaperClient(),
                output_root=Path(tmp),
            )

            self.assertTrue(Path(result.reconciliation_path or "").exists())

    def test_runner_writes_post_send_safety_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = controlled.run_controlled_v10_paper_send(
                config=valid_config(execution_enabled=False),
                client=controlled.RecordingControlledPaperClient(),
                output_root=Path(tmp),
            )

            self.assertTrue(Path(result.post_send_safety_path or "").exists())

    def test_runner_writes_post_mortem(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = controlled.run_controlled_v10_paper_send(
                config=valid_config(execution_enabled=False),
                client=controlled.RecordingControlledPaperClient(),
                output_root=Path(tmp),
            )

            self.assertTrue(Path(result.post_mortem_path or "").exists())

    def test_runner_does_not_support_live_trading(self) -> None:
        result = run_with(valid_config(live_endpoint_configured=True))

        self.assertFalse(result.live_trading_readiness)
        self.assertIn("live endpoint configured is blocked", result.block_reasons)

    def test_runner_does_not_support_live_endpoints(self) -> None:
        result = run_with(valid_config(live_endpoint_configured=True))

        self.assertEqual(result.final_status, controlled.CONTROLLED_SEND_BLOCKED)
        self.assertFalse(result.order_sent)

    def test_runner_does_not_print_secrets(self) -> None:
        secret = "phase43-secret-not-in-output"
        with patch.dict(os.environ, {"ALPACA_API_SECRET_KEY": secret}):
            result = run_with(valid_config(execution_enabled=False))

        self.assertNotIn(secret, str(result.as_dict()))

    def test_runner_returns_to_dry_run_and_unsets_execution_flag(self) -> None:
        with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": "true"}):
            result = run_with(valid_config())
            self.assertIsNone(os.environ.get("PAPER_ORDER_EXECUTION_ENABLED"))

        self.assertTrue(result.returned_to_dry_run_only)
        self.assertTrue(result.operator_unset_instruction)

    def test_no_real_alpaca_call_in_mocked_mode(self) -> None:
        result = run_with(valid_config())

        self.assertTrue(result.order_sent)
        self.assertFalse(result.alpaca_order_api_called)

    def assert_blocked_with(self, result, reason: str) -> None:
        self.assertEqual(result.final_status, controlled.CONTROLLED_SEND_BLOCKED)
        self.assertIn(reason, result.block_reasons)
        self.assertFalse(result.order_sent)
        self.assertEqual(result.submitted_order_count, 0)


def valid_config(**overrides):
    values = {
        "full_tests_status": "PASS",
        "architecture_validation_status": "PASS",
        "v10_full_pipeline_regression_status": "PASS",
        "execution_enabled": True,
    }
    values.update(overrides)
    return controlled.ControlledV10PaperSendConfig(**values)


def run_with(config, client=None):
    return controlled.run_controlled_v10_paper_send(
        config=config,
        client=client or controlled.RecordingControlledPaperClient(),
        write_artifacts=False,
    )


if __name__ == "__main__":
    unittest.main()
