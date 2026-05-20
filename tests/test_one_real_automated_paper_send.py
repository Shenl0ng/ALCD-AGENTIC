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


one_real = load_module("one_real_automated_paper_send")
automated = load_module("automated_paper_send")


class OneRealAutomatedPaperSendTests(unittest.TestCase):
    def test_one_real_automated_runner_exists(self) -> None:
        self.assertTrue(hasattr(one_real, "run_one_real_automated_paper_send"))

    def test_blocks_unless_execution_enabled_true(self) -> None:
        result = run_with(valid_config(paper_order_execution_enabled=False))

        self.assert_blocked_with(result, "PAPER_ORDER_EXECUTION_ENABLED is not true during final explicit run")

    def test_blocks_unless_automated_send_enabled_true(self) -> None:
        result = run_with(valid_config(paper_automated_send_enabled=False))

        self.assert_blocked_with(result, "PAPER_AUTOMATED_SEND_ENABLED is not true during final explicit run")

    def test_blocks_unless_alpaca_paper_true(self) -> None:
        result = run_with(valid_config(alpaca_paper=False))

        self.assert_blocked_with(result, "ALPACA_PAPER is not true")

    def test_blocks_missing_full_tests_pass(self) -> None:
        result = run_with(valid_config(full_tests_status=None))

        self.assert_blocked_with(result, "full tests status is not PASS")

    def test_blocks_missing_architecture_validation_pass(self) -> None:
        result = run_with(valid_config(architecture_validation_status=None))

        self.assert_blocked_with(result, "architecture validation status is not PASS")

    def test_blocks_missing_v10_full_pipeline_dry_run_regression_pass(self) -> None:
        result = run_with(valid_config(v10_full_pipeline_regression_status=None))

        self.assert_blocked_with(result, "V10 full pipeline dry-run regression status is not PASS")

    def test_blocks_missing_automated_paper_send_mocked_regression_pass(self) -> None:
        result = run_with(valid_config(automated_paper_send_mocked_regression_status=None))

        self.assert_blocked_with(result, "automated paper send mocked regression status is not PASS")

    def test_blocks_any_failed_v12_gate(self) -> None:
        result = run_with(valid_config(evaluation_gate_status="EVALUATION_GATE_BLOCKED"))

        self.assert_blocked_with(result, "Evaluation-First Gate status is not EVALUATION_GATE_PASSED")

    def test_blocks_kill_switch_active(self) -> None:
        result = run_with(valid_config(limits=limits(kill_switch_active=True)))

        self.assert_blocked_with(result, "automation kill switch is active")

    def test_blocks_daily_order_limit_exceeded(self) -> None:
        result = run_with(valid_config(limits=limits(daily_order_count=1)))

        self.assert_blocked_with(result, "daily order limit exceeded")

    def test_blocks_daily_notional_limit_exceeded(self) -> None:
        result = run_with(valid_config(limits=limits(daily_notional_used="50"), notional="51"))

        self.assert_blocked_with(result, "daily notional limit exceeded")

    def test_blocks_cooldown_not_satisfied(self) -> None:
        result = run_with(valid_config(limits=limits(cooldown_satisfied=False)))

        self.assert_blocked_with(result, "cooldown not satisfied")

    def test_blocks_previous_reconciliation_missing_or_mismatched(self) -> None:
        missing = run_with(valid_config(limits=limits(previous_reconciliation_exists=False)))
        mismatched = run_with(valid_config(limits=limits(previous_reconciliation_unresolved_mismatch=True)))

        self.assert_blocked_with(missing, "previous reconciliation missing")
        self.assert_blocked_with(mismatched, "previous reconciliation mismatch unresolved")

    def test_blocks_previous_post_mortem_missing_or_blocking(self) -> None:
        missing = run_with(valid_config(limits=limits(previous_post_mortem_exists=False)))
        blocking = run_with(valid_config(limits=limits(previous_post_mortem_unresolved_blocker=True)))

        self.assert_blocked_with(missing, "previous post-mortem missing")
        self.assert_blocked_with(blocking, "previous post-mortem unresolved blocker")

    def test_blocks_unresolved_issue(self) -> None:
        result = run_with(valid_config(limits=limits(unresolved_issue_exists=True)))

        self.assert_blocked_with(result, "unresolved issue exists")

    def test_blocks_live_endpoint(self) -> None:
        result = run_with(valid_config(live_endpoint_configured=True))

        self.assert_blocked_with(result, "live endpoint configured is blocked")

    def test_blocks_non_paper_account(self) -> None:
        result = run_with(valid_config(alpaca_paper_account_confirmed=False))

        self.assert_blocked_with(result, "Alpaca paper account is not confirmed")

    def test_blocks_notional_over_100(self) -> None:
        result = run_with(valid_config(notional="101"))

        self.assert_blocked_with(result, "notional > 100 USD is blocked")

    def test_blocks_non_limit_order(self) -> None:
        result = run_with(valid_config(order_type="market"))

        self.assert_blocked_with(result, "limit order only is required")

    def test_blocks_non_day_tif(self) -> None:
        result = run_with(valid_config(time_in_force="gtc"))

        self.assert_blocked_with(result, "day time-in-force only is required")

    def test_blocks_short_crypto_options_margin_extended_hours(self) -> None:
        cases = (
            ({"short_selling": True}, "short selling is blocked"),
            ({"crypto": True}, "crypto is blocked"),
            ({"options": True}, "options are blocked"),
            ({"margin_or_leverage": True}, "margin/leverage is blocked"),
            ({"extended_hours": True}, "extended hours are blocked"),
        )
        for overrides, reason in cases:
            with self.subTest(reason=reason):
                self.assert_blocked_with(run_with(valid_config(**overrides)), reason)

    def test_blocks_batch_cancel_replace(self) -> None:
        result = run_with(valid_config(batch_orders=True, cancel_replace=True))

        self.assert_blocked_with(result, "batch orders are blocked")
        self.assertIn("cancel/replace is blocked", result.block_reasons)

    def test_mocked_final_run_path_submits_exactly_one_mocked_paper_limit_day_order(self) -> None:
        client = automated.RecordingAutomatedPaperClient()
        result = run_with(valid_config(), client=client)

        self.assertEqual(result.final_status, one_real.ONE_REAL_AUTOMATED_PAPER_SEND_SUBMITTED)
        self.assertEqual(result.submitted_order_count, 1)
        self.assertEqual(len(client.payloads), 1)
        payload = client.payloads[0]
        self.assertEqual(payload["type"], "limit")
        self.assertEqual(payload["time_in_force"], "day")
        self.assertEqual(payload["notional"], "100")

    def test_runner_writes_all_required_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = one_real.run_one_real_automated_paper_send(
                config=valid_config(),
                client=automated.RecordingAutomatedPaperClient(),
                output_root=Path(tmp),
            )

            self.assertTrue(Path(result.report_path or "").exists())
            self.assertTrue(Path(result.audit_log_path or "").exists())
            self.assertTrue(Path(result.reconciliation_path or "").exists())
            self.assertTrue(Path(result.post_send_safety_path or "").exists())
            self.assertTrue(Path(result.post_mortem_path or "").exists())

    def test_runner_returns_system_to_dry_run_only(self) -> None:
        result = run_with(valid_config())

        self.assertTrue(result.returned_to_dry_run_only)

    def test_runner_requires_flags_unset_disabled_after_run(self) -> None:
        with patch.dict(
            os.environ,
            {
                "PAPER_ORDER_EXECUTION_ENABLED": "true",
                "PAPER_AUTOMATED_SEND_ENABLED": "true",
            },
        ):
            result = run_with(valid_config())
            self.assertIsNone(os.environ.get("PAPER_ORDER_EXECUTION_ENABLED"))
            self.assertIsNone(os.environ.get("PAPER_AUTOMATED_SEND_ENABLED"))

        self.assertTrue(result.flags_unset_or_disabled_after_run)

    def test_no_real_order_is_sent_during_tests(self) -> None:
        result = run_with(valid_config())

        self.assertTrue(result.order_sent)
        self.assertFalse(result.alpaca_order_api_called)

    def test_no_live_trading_exists(self) -> None:
        result = run_with(valid_config(live_endpoint_configured=True))

        self.assertFalse(result.live_trading_readiness)
        self.assertFalse(result.live_endpoint_used)

    def test_no_secrets_are_printed(self) -> None:
        secret = "phase49-secret-not-in-output"
        with patch.dict(os.environ, {"ALPACA_API_SECRET_KEY": secret}):
            result = run_with(valid_config())

        self.assertNotIn(secret, str(result.as_dict()))
        self.assertFalse(result.secrets_printed)

    def assert_blocked_with(self, result, reason: str) -> None:
        self.assertEqual(result.final_status, one_real.ONE_REAL_AUTOMATED_PAPER_SEND_BLOCKED)
        self.assertIn(reason, result.block_reasons)
        self.assertFalse(result.order_sent)
        self.assertEqual(result.submitted_order_count, 0)
        self.assertFalse(result.alpaca_order_api_called)


def valid_config(**overrides):
    values = {
        "paper_order_execution_enabled": True,
        "paper_automated_send_enabled": True,
        "alpaca_paper": True,
        "full_tests_status": "PASS",
        "architecture_validation_status": "PASS",
        "v10_full_pipeline_regression_status": "PASS",
        "automated_paper_send_mocked_regression_status": "PASS",
        "secrets_present": True,
    }
    values.update(overrides)
    return one_real.OneRealAutomatedPaperSendConfig(**values)


def limits(**overrides):
    values = automated.AutomationLimits().__dict__.copy()
    values.update(overrides)
    return automated.AutomationLimits(**values)


def run_with(config, client=None):
    return one_real.run_one_real_automated_paper_send(
        config=config,
        client=client or automated.RecordingAutomatedPaperClient(),
        write_artifacts=False,
    )


if __name__ == "__main__":
    unittest.main()
