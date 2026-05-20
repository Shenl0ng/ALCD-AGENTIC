from __future__ import annotations

import importlib.util
import os
import sys
import unittest
import tempfile
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


automated = load_module("automated_paper_send")


class AutomatedPaperSendTests(unittest.TestCase):
    def test_automated_paper_send_runner_exists(self) -> None:
        self.assertTrue(hasattr(automated, "run_automated_paper_send"))

    def test_automated_send_disabled_by_default(self) -> None:
        result = run_with(automated.AutomatedPaperSendConfig())

        self.assert_blocked_with(result, "PAPER_AUTOMATED_SEND_ENABLED is not true")
        self.assertIn("PAPER_ORDER_EXECUTION_ENABLED is not true", result.block_reasons)

    def test_paper_automated_send_false_blocks_send(self) -> None:
        result = run_with(valid_config(paper_automated_send_enabled=False))

        self.assert_blocked_with(result, "PAPER_AUTOMATED_SEND_ENABLED is not true")

    def test_paper_order_execution_false_blocks_send(self) -> None:
        result = run_with(valid_config(paper_order_execution_enabled=False))

        self.assert_blocked_with(result, "PAPER_ORDER_EXECUTION_ENABLED is not true")

    def test_alpaca_paper_not_true_blocks_send(self) -> None:
        result = run_with(valid_config(alpaca_paper=False))

        self.assert_blocked_with(result, "ALPACA_PAPER is not true")

    def test_missing_full_tests_pass_blocks_send(self) -> None:
        result = run_with(valid_config(full_tests_status=None))

        self.assert_blocked_with(result, "full tests status is not PASS")

    def test_missing_architecture_validation_pass_blocks_send(self) -> None:
        result = run_with(valid_config(architecture_validation_status=None))

        self.assert_blocked_with(result, "architecture validation status is not PASS")

    def test_missing_v10_dry_run_regression_pass_blocks_send(self) -> None:
        result = run_with(valid_config(v10_full_pipeline_regression_status=None))

        self.assert_blocked_with(result, "V10 full pipeline dry-run regression status is not PASS")

    def test_strategy_evaluation_fail_blocks_send(self) -> None:
        result = run_with(valid_config(strategy_evaluation_status="FAIL"))

        self.assert_blocked_with(result, "Strategy Evaluation status is not PASS")

    def test_evaluation_first_gate_fail_blocks_send(self) -> None:
        result = run_with(valid_config(evaluation_gate_status="EVALUATION_GATE_BLOCKED"))

        self.assert_blocked_with(result, "Evaluation-First Gate status is not EVALUATION_GATE_PASSED")

    def test_negative_case_regression_fail_blocks_send(self) -> None:
        result = run_with(valid_config(negative_case_regression_status="FAIL"))

        self.assert_blocked_with(result, "Negative Case Regression status is not PASS")

    def test_missing_candidate_blocks_send(self) -> None:
        result = run_with(valid_config(candidate_scenario="no_trade"))

        self.assert_blocked_with(result, "Paper Order Request Candidate is missing")

    def test_human_review_not_approved_blocks_send(self) -> None:
        result = run_with(valid_config(human_review_status="HUMAN_REVIEW_REJECTED"))

        self.assert_blocked_with(result, "Human Review is not approved")

    def test_finalized_request_missing_blocks_send(self) -> None:
        result = run_with(valid_config(human_review_status="HUMAN_REVIEW_REJECTED"))

        self.assert_blocked_with(result, "Finalized Paper Order Request is missing or not finalized")

    def test_manual_execution_confirmation_missing_blocks_send(self) -> None:
        result = run_with(valid_config(manual_confirmation_status="MANUAL_EXECUTION_REJECTED"))

        self.assert_blocked_with(result, "Manual Execution Confirmation is missing or not confirmed")

    def test_paper_send_preflight_not_allowed_blocks_send(self) -> None:
        result = run_with(valid_config(live_endpoint_configured=True))

        self.assert_blocked_with(result, "Paper Send Preflight is not PAPER_ORDER_SEND_ALLOWED")

    def test_alpaca_paper_account_not_confirmed_blocks_send(self) -> None:
        result = run_with(valid_config(alpaca_paper_account_confirmed=False))

        self.assert_blocked_with(result, "Alpaca paper account is not confirmed")

    def test_live_endpoint_configured_blocks_send(self) -> None:
        result = run_with(valid_config(live_endpoint_configured=True))

        self.assert_blocked_with(result, "live endpoint configured is blocked")

    def test_kill_switch_active_blocks_send(self) -> None:
        result = run_with(valid_config(limits=limits(kill_switch_active=True)))

        self.assert_blocked_with(result, "automation kill switch is active")
        self.assertEqual(result.final_status, automated.AUTOMATED_PAPER_SEND_REJECTED_BY_KILL_SWITCH)

    def test_daily_order_limit_exceeded_blocks_send(self) -> None:
        result = run_with(valid_config(limits=limits(daily_order_count=1)))

        self.assert_blocked_with(result, "daily order limit exceeded")
        self.assertEqual(result.final_status, automated.AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS)

    def test_daily_notional_limit_exceeded_blocks_send(self) -> None:
        result = run_with(valid_config(limits=limits(daily_notional_used="50"), notional="51"))

        self.assert_blocked_with(result, "daily notional limit exceeded")

    def test_cooldown_not_satisfied_blocks_send(self) -> None:
        result = run_with(valid_config(limits=limits(cooldown_satisfied=False)))

        self.assert_blocked_with(result, "cooldown not satisfied")

    def test_missing_previous_reconciliation_blocks_send(self) -> None:
        result = run_with(valid_config(limits=limits(previous_reconciliation_exists=False)))

        self.assert_blocked_with(result, "previous reconciliation missing")
        self.assertEqual(result.final_status, automated.AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION)

    def test_unresolved_reconciliation_mismatch_blocks_send(self) -> None:
        result = run_with(valid_config(limits=limits(previous_reconciliation_unresolved_mismatch=True)))

        self.assert_blocked_with(result, "previous reconciliation mismatch unresolved")

    def test_missing_previous_post_mortem_blocks_send(self) -> None:
        result = run_with(valid_config(limits=limits(previous_post_mortem_exists=False)))

        self.assert_blocked_with(result, "previous post-mortem missing")
        self.assertEqual(result.final_status, automated.AUTOMATED_PAPER_SEND_REJECTED_BY_POST_MORTEM)

    def test_unresolved_post_mortem_blocker_blocks_send(self) -> None:
        result = run_with(valid_config(limits=limits(previous_post_mortem_unresolved_blocker=True)))

        self.assert_blocked_with(result, "previous post-mortem unresolved blocker")

    def test_unresolved_issue_blocks_send(self) -> None:
        result = run_with(valid_config(limits=limits(unresolved_issue_exists=True)))

        self.assert_blocked_with(result, "unresolved issue exists")

    def test_more_than_one_symbol_blocks_send(self) -> None:
        result = run_with(valid_config(symbols=("SIM", "ALT")))

        self.assert_blocked_with(result, "one symbol only is required")

    def test_more_than_one_order_blocks_send(self) -> None:
        result = run_with(valid_config(order_count=2))

        self.assert_blocked_with(result, "one order per automation run is required")

    def test_notional_over_100_blocks_send(self) -> None:
        result = run_with(valid_config(notional="101"))

        self.assert_blocked_with(result, "notional > 100 USD is blocked")

    def test_market_order_blocks_send(self) -> None:
        result = run_with(valid_config(order_type="market"))

        self.assert_blocked_with(result, "limit order only is required")

    def test_non_day_time_in_force_blocks_send(self) -> None:
        result = run_with(valid_config(time_in_force="gtc"))

        self.assert_blocked_with(result, "day time-in-force only is required")

    def test_short_selling_blocks_send(self) -> None:
        result = run_with(valid_config(short_selling=True))

        self.assert_blocked_with(result, "short selling is blocked")

    def test_crypto_blocks_send(self) -> None:
        result = run_with(valid_config(crypto=True))

        self.assert_blocked_with(result, "crypto is blocked")

    def test_options_blocks_send(self) -> None:
        result = run_with(valid_config(options=True))

        self.assert_blocked_with(result, "options are blocked")

    def test_margin_leverage_blocks_send(self) -> None:
        result = run_with(valid_config(margin_or_leverage=True))

        self.assert_blocked_with(result, "margin/leverage is blocked")

    def test_extended_hours_blocks_send(self) -> None:
        result = run_with(valid_config(extended_hours=True))

        self.assert_blocked_with(result, "extended hours are blocked")

    def test_batch_orders_block_send(self) -> None:
        result = run_with(valid_config(batch_orders=True))

        self.assert_blocked_with(result, "batch orders are blocked")

    def test_cancel_replace_blocks_send(self) -> None:
        result = run_with(valid_config(cancel_replace=True))

        self.assert_blocked_with(result, "cancel/replace is blocked")

    def test_mocked_alpaca_client_receives_exactly_one_paper_limit_day_order_when_all_gates_pass(self) -> None:
        client = automated.RecordingAutomatedPaperClient()
        result = run_with(valid_config(), client=client)

        self.assertEqual(result.final_status, automated.AUTOMATED_PAPER_SEND_SUBMITTED)
        self.assertEqual(result.submitted_order_count, 1)
        self.assertTrue(result.order_sent)
        self.assertEqual(len(client.payloads), 1)
        payload = client.payloads[0]
        self.assertEqual(payload["type"], "limit")
        self.assertEqual(payload["time_in_force"], "day")
        self.assertEqual(payload["notional"], "100")

    def test_runner_writes_automated_send_report(self) -> None:
        result = run_artifact_case()

        self.assertTrue(Path(result.report_path or "").exists())

    def test_runner_writes_automation_audit_log(self) -> None:
        result = run_artifact_case()

        self.assertTrue(Path(result.audit_log_path or "").exists())

    def test_runner_writes_reconciliation_artifact(self) -> None:
        result = run_artifact_case()

        self.assertTrue(Path(result.reconciliation_path or "").exists())

    def test_runner_writes_post_send_safety_artifact(self) -> None:
        result = run_artifact_case()

        self.assertTrue(Path(result.post_send_safety_path or "").exists())

    def test_runner_writes_post_mortem(self) -> None:
        result = run_artifact_case()

        self.assertTrue(Path(result.post_mortem_path or "").exists())

    def test_runner_returns_system_to_dry_run_only(self) -> None:
        result = run_with(valid_config())

        self.assertTrue(result.returned_to_dry_run_only)

    def test_runner_requires_flags_unset_or_disabled_after_run(self) -> None:
        with patch.dict(
            os.environ,
            {
                "PAPER_AUTOMATED_SEND_ENABLED": "true",
                "PAPER_ORDER_EXECUTION_ENABLED": "true",
            },
        ):
            result = run_with(valid_config())
            self.assertIsNone(os.environ.get("PAPER_AUTOMATED_SEND_ENABLED"))
            self.assertIsNone(os.environ.get("PAPER_ORDER_EXECUTION_ENABLED"))

        self.assertTrue(result.flags_unset_or_disabled_after_run)

    def test_no_live_trading_exists(self) -> None:
        result = run_with(valid_config(live_endpoint_configured=True))

        self.assertFalse(result.live_trading_readiness)
        self.assertFalse(result.order_sent)

    def test_no_live_endpoints_exist(self) -> None:
        source = (RUNTIME_PATH / "automated_paper_send.py").read_text(encoding="utf-8")
        result = run_with(valid_config(live_endpoint_configured=True))

        self.assertFalse(result.live_endpoint_used)
        self.assertNotIn("/v2/orders", source)
        self.assertNotIn("urlopen", source)

    def test_no_secrets_are_printed(self) -> None:
        secret = "phase45-secret-not-in-output"
        with patch.dict(os.environ, {"ALPACA_API_SECRET_KEY": secret}):
            result = run_with(valid_config())

        self.assertNotIn(secret, str(result.as_dict()))

    def test_report_contains_required_proof_statements(self) -> None:
        result = run_artifact_case()
        report = Path(result.report_path or "").read_text(encoding="utf-8")
        safety = Path(result.post_send_safety_path or "").read_text(encoding="utf-8")

        for statement in (
            "Automated paper send is paper-only.",
            "Live trading remains unsupported.",
            "Increasing notional remains prohibited.",
            "Batch orders remain prohibited.",
            "Cancel/replace remains prohibited.",
        ):
            self.assertIn(statement, report)
            if statement != "Automated paper send is paper-only.":
                self.assertIn(statement, safety)

    def assert_blocked_with(self, result, reason: str) -> None:
        self.assertIn(reason, result.block_reasons)
        self.assertFalse(result.order_sent)
        self.assertEqual(result.submitted_order_count, 0)
        self.assertFalse(result.alpaca_order_api_called)
        self.assertFalse(result.broker_execution_readiness)


def valid_config(**overrides):
    values = {
        "paper_automated_send_enabled": True,
        "paper_order_execution_enabled": True,
        "alpaca_paper": True,
        "full_tests_status": "PASS",
        "architecture_validation_status": "PASS",
        "v10_full_pipeline_regression_status": "PASS",
    }
    values.update(overrides)
    return automated.AutomatedPaperSendConfig(**values)


def limits(**overrides):
    values = automated.AutomationLimits().__dict__.copy()
    values.update(overrides)
    return automated.AutomationLimits(**values)


def run_with(config, client=None):
    return automated.run_automated_paper_send(
        config=config,
        client=client or automated.RecordingAutomatedPaperClient(),
        write_artifacts=False,
    )


def run_artifact_case():
    temp_root = tempfile.mkdtemp()
    result = automated.run_automated_paper_send(
        config=valid_config(),
        client=automated.RecordingAutomatedPaperClient(),
        output_root=Path(temp_root),
        write_artifacts=True,
    )
    return result


if __name__ == "__main__":
    unittest.main()
