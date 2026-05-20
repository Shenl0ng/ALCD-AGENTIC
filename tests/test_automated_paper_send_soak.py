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


soak = load_module("automated_paper_send_soak")


class AutomatedPaperSendSoakTests(unittest.TestCase):
    def test_soak_run_registry_exists(self) -> None:
        record = sample_record()

        self.assertEqual(record.run_id, "run-1")

    def test_daily_order_counter_exists(self) -> None:
        state = soak.SoakRunState(daily_order_count=1)

        self.assertEqual(state.daily_order_count, 1)

    def test_daily_notional_tracker_exists(self) -> None:
        state = soak.SoakRunState(daily_notional_used="50")

        self.assertEqual(state.daily_notional_used, "50")

    def test_cooldown_tracker_exists(self) -> None:
        state = soak.SoakRunState(cooldown_satisfied=False)

        self.assertFalse(state.cooldown_satisfied)

    def test_kill_switch_integration_exists(self) -> None:
        result = run_with(state=soak.SoakRunState(kill_switch_active=True))

        self.assert_blocked_with(result, "automation kill switch is active")

    def test_previous_reconciliation_dependency_check_exists(self) -> None:
        result = run_with(state=soak.SoakRunState(previous_reconciliation_exists=False))

        self.assert_blocked_with(result, "previous reconciliation missing")

    def test_previous_post_mortem_dependency_check_exists(self) -> None:
        result = run_with(state=soak.SoakRunState(previous_post_mortem_exists=False))

        self.assert_blocked_with(result, "previous post-mortem missing")

    def test_unresolved_issue_blocker_exists(self) -> None:
        result = run_with(state=soak.SoakRunState(unresolved_issue_exists=True))

        self.assert_blocked_with(result, "unresolved issue exists")

    def test_consecutive_failure_counter_exists(self) -> None:
        result = run_with(state=soak.SoakRunState(consecutive_failures=2, kill_switch_active=True))

        self.assertEqual(result.consecutive_failures, 3)

    def test_consecutive_success_counter_exists(self) -> None:
        result = run_with(state=soak.SoakRunState(consecutive_successes=2))

        self.assertEqual(result.consecutive_successes, 3)

    def test_reconciliation_mismatch_blocks_soak_continuation(self) -> None:
        result = run_with(state=soak.SoakRunState(reconciliation_mismatch_exists=True))

        self.assert_blocked_with(result, "reconciliation mismatch blocks soak continuation")
        self.assertEqual(result.recommendation, soak.SOAK_RECOMMENDATION_HOLD)

    def test_missing_reconciliation_blocks_soak_continuation(self) -> None:
        result = run_with(state=soak.SoakRunState(missing_reconciliation=True))

        self.assert_blocked_with(result, "missing reconciliation blocks soak continuation")

    def test_missing_post_mortem_blocks_soak_continuation(self) -> None:
        result = run_with(state=soak.SoakRunState(missing_post_mortem=True))

        self.assert_blocked_with(result, "missing post-mortem blocks soak continuation")

    def test_unresolved_post_mortem_blocker_blocks_soak_continuation(self) -> None:
        result = run_with(state=soak.SoakRunState(unresolved_post_mortem_blocker=True))

        self.assert_blocked_with(result, "unresolved post-mortem blocker blocks soak continuation")
        self.assertEqual(result.recommendation, soak.SOAK_RECOMMENDATION_HOLD)

    def test_kill_switch_active_blocks_soak_continuation(self) -> None:
        result = run_with(state=soak.SoakRunState(kill_switch_active=True))

        self.assert_blocked_with(result, "automation kill switch is active")

    def test_live_endpoint_detected_blocks_soak_continuation(self) -> None:
        result = run_with(live_endpoint_configured=True)

        self.assert_blocked_with(result, "live endpoint detected")

    def test_more_than_one_order_in_a_day_blocks_soak_continuation(self) -> None:
        result = run_with(state=soak.SoakRunState(daily_order_count=1))

        self.assert_blocked_with(result, "daily order limit exceeded")

    def test_daily_notional_exceeded_blocks_soak_continuation(self) -> None:
        result = run_with(state=soak.SoakRunState(daily_notional_used="50"), notional="51")

        self.assert_blocked_with(result, "daily notional limit exceeded")

    def test_cooldown_violation_blocks_soak_continuation(self) -> None:
        result = run_with(state=soak.SoakRunState(cooldown_satisfied=False))

        self.assert_blocked_with(result, "cooldown violation")

    def test_batch_cancel_replace_attempt_blocks_soak_continuation(self) -> None:
        result = run_with(batch_orders=True, cancel_replace=True)

        self.assert_blocked_with(result, "batch orders are blocked")
        self.assertIn("cancel/replace is blocked", result.block_reasons)

    def test_failed_v13_gate_blocks_soak_continuation(self) -> None:
        result = run_with(evaluation_gate_status="EVALUATION_GATE_BLOCKED")

        self.assert_blocked_with(result, "Evaluation-First Gate status is not EVALUATION_GATE_PASSED")

    def test_repeated_approval_red_flag_blocks_or_warns(self) -> None:
        quality = soak.SoakQualityMetrics(attempted_runs=5, approved_runs=5, no_trade_or_rejection_count=0)
        result = run_with(quality=quality)

        self.assertIn("approval-rate red flag", result.block_reasons)
        self.assertIn(result.recommendation, {soak.SOAK_RECOMMENDATION_HOLD, soak.SOAK_RECOMMENDATION_CONTINUE})

    def test_evaluation_score_inflation_blocks_or_warns(self) -> None:
        result = run_with(quality=soak.SoakQualityMetrics(evaluation_score_inflation=True))

        self.assert_blocked_with(result, "evaluation score inflation")

    def test_rubber_stamping_blocks_or_warns(self) -> None:
        result = run_with(quality=soak.SoakQualityMetrics(rubber_stamping_detected=True))

        self.assert_blocked_with(result, "rubber-stamping detected")

    def test_journal_quality_degradation_blocks_or_warns(self) -> None:
        result = run_with(quality=soak.SoakQualityMetrics(journal_quality_degraded=True))

        self.assert_blocked_with(result, "journal quality degradation")

    def test_soak_report_generator_writes_all_required_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = soak.generate_soak_reports(records=(sample_record(),), output_root=Path(tmp))

            self.assertTrue(Path(paths.soak_test_plan_path or "").exists())
            self.assertTrue(Path(paths.soak_run_registry_path or "").exists())
            self.assertTrue(Path(paths.soak_daily_limits_path or "").exists())
            self.assertTrue(Path(paths.soak_quality_review_path or "").exists())
            self.assertTrue(Path(paths.soak_final_report_path or "").exists())

    def test_soak_report_generator_reads_existing_one_real_artifacts(self) -> None:
        artifact_dir = ROOT / "reports" / "one_real_automated_paper_send" / "20260520T134219Z"
        if not artifact_dir.exists():
            self.skipTest("V13 one-real artifact directory is not available")
        with tempfile.TemporaryDirectory() as tmp:
            paths = soak.generate_soak_reports_from_existing_artifacts(
                artifact_dirs=(artifact_dir,),
                output_root=Path(tmp),
            )

            report = Path(paths.soak_final_report_path or "").read_text(encoding="utf-8")
            self.assertIn("Number of attempted runs: 1", report)
            self.assertIn("RECONCILIATION_MATCHED", report)

    def test_soak_final_report_includes_recommendation(self) -> None:
        report = generated_final_report_text()

        self.assertIn("Recommendation:", report)

    def test_soak_final_report_includes_required_prohibition_statements(self) -> None:
        report = generated_final_report_text()

        for statement in (
            "Live trading remains unsupported.",
            "Increasing notional remains prohibited.",
            "Multi-symbol automation remains prohibited.",
            "Batch orders remain prohibited.",
            "Cancel/replace remains prohibited.",
        ):
            self.assertIn(statement, report)

    def test_no_real_alpaca_api_is_called(self) -> None:
        result = run_with()

        self.assertFalse(result.real_alpaca_api_called)

    def test_no_real_order_is_sent(self) -> None:
        result = run_with()

        self.assertFalse(result.real_order_sent)
        self.assertEqual(result.submitted_paper_order_count, 0)

    def test_no_live_trading_exists(self) -> None:
        result = run_with(live_endpoint_configured=True)

        self.assertFalse(result.live_trading_readiness)

    def test_no_live_endpoints_exist(self) -> None:
        source = (RUNTIME_PATH / "automated_paper_send_soak.py").read_text(encoding="utf-8")

        self.assertNotIn("/v2/orders", source)
        self.assertNotIn("urlopen", source)

    def test_no_secrets_are_printed(self) -> None:
        secret = "phase51-secret-not-in-output"
        with patch.dict(os.environ, {"ALPACA_API_SECRET_KEY": secret}):
            result = run_with()

        self.assertNotIn(secret, str(result.as_dict()))
        self.assertFalse(result.secrets_printed)

    def test_default_state_keeps_automation_disabled(self) -> None:
        result = soak.evaluate_soak_run()

        self.assert_blocked_with(result, "PAPER_ORDER_EXECUTION_ENABLED is not true")
        self.assertIn("PAPER_AUTOMATED_SEND_ENABLED is not true", result.block_reasons)

    def test_flags_are_disabled_unset_after_evaluation(self) -> None:
        with patch.dict(
            os.environ,
            {
                "PAPER_ORDER_EXECUTION_ENABLED": "true",
                "PAPER_AUTOMATED_SEND_ENABLED": "true",
            },
        ):
            result = run_with()
            self.assertIsNone(os.environ.get("PAPER_ORDER_EXECUTION_ENABLED"))
            self.assertIsNone(os.environ.get("PAPER_AUTOMATED_SEND_ENABLED"))

        self.assertTrue(result.flags_disabled_unset_after_run)

    def test_accelerated_cooldown_config_exists(self) -> None:
        config = soak.AcceleratedSoakCooldownConfig()

        self.assertFalse(config.accelerated_mode_enabled)
        self.assertEqual(config.production_default_cooldown_seconds, 86400)

    def test_accelerated_cooldown_validator_exists(self) -> None:
        self.assertTrue(callable(soak.validate_accelerated_cooldown))

    def test_production_default_cooldown_remains_24_hours_when_accelerated_false(self) -> None:
        config = soak.AcceleratedSoakCooldownConfig()

        self.assertEqual(config.production_default_cooldown_seconds, 24 * 60 * 60)

    def test_accelerated_cooldown_is_disabled_by_default(self) -> None:
        config = soak.SoakRunConfig()

        self.assertFalse(config.accelerated_cooldown.accelerated_mode_enabled)

    def test_paper_soak_test_accelerated_false_by_default(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            config = soak.accelerated_cooldown_config_from_env()

        self.assertFalse(config.accelerated_mode_enabled)

    def test_accelerated_mode_requires_cooldown_seconds(self) -> None:
        result = run_accelerated(configured_cooldown_seconds=None)

        self.assert_blocked_with(result, "PAPER_SOAK_TEST_COOLDOWN_SECONDS is required")

    def test_accelerated_cooldown_60_seconds_passes(self) -> None:
        result = run_accelerated(configured_cooldown_seconds=60, state=soak.SoakRunState(cooldown_satisfied=False))

        self.assertEqual(result.final_status, soak.SOAK_RUN_ALLOWED)
        self.assertNotIn("cooldown violation", result.block_reasons)

    def test_accelerated_cooldown_59_seconds_blocks(self) -> None:
        result = run_accelerated(configured_cooldown_seconds=59)

        self.assert_blocked_with(result, "PAPER_SOAK_TEST_COOLDOWN_SECONDS < 60 is blocked")

    def test_accelerated_cooldown_86400_seconds_blocks(self) -> None:
        result = run_accelerated(configured_cooldown_seconds=86400)

        self.assert_blocked_with(result, "PAPER_SOAK_TEST_COOLDOWN_SECONDS >= 86400 is blocked")

    def test_accelerated_cooldown_86399_seconds_passes(self) -> None:
        result = run_accelerated(configured_cooldown_seconds=86399, state=soak.SoakRunState(cooldown_satisfied=False))

        self.assertEqual(result.final_status, soak.SOAK_RUN_ALLOWED)

    def test_accelerated_mode_requires_alpaca_paper_true(self) -> None:
        result = run_accelerated(alpaca_paper=False)

        self.assert_blocked_with(result, "PAPER_SOAK_TEST_ACCELERATED=true requires ALPACA_PAPER=true")

    def test_accelerated_mode_blocks_live_endpoint(self) -> None:
        result = run_accelerated(live_endpoint_configured=True)

        self.assert_blocked_with(result, "accelerated cooldown blocks live endpoint")

    def test_accelerated_mode_blocks_live_trading_assumption(self) -> None:
        result = run_accelerated(live_trading_assumption=True)

        self.assert_blocked_with(result, "accelerated cooldown blocks live trading assumption")

    def test_accelerated_mode_blocks_notional_over_100(self) -> None:
        result = run_accelerated(notional="101")

        self.assert_blocked_with(result, "accelerated cooldown blocks notional > 100 USD")

    def test_accelerated_mode_blocks_more_than_one_symbol(self) -> None:
        result = run_accelerated(symbols=("SIM", "ALT"))

        self.assert_blocked_with(result, "accelerated cooldown blocks more than one symbol")

    def test_accelerated_mode_blocks_more_than_one_order_per_run(self) -> None:
        result = run_accelerated(order_count=2)

        self.assert_blocked_with(result, "accelerated cooldown blocks more than one order per run")

    def test_accelerated_mode_blocks_batch_cancel_replace(self) -> None:
        result = run_accelerated(batch_orders=True, cancel_replace=True)

        self.assert_blocked_with(result, "accelerated cooldown blocks batch/cancel/replace")

    def test_accelerated_mode_blocks_failed_v13_gate(self) -> None:
        result = run_accelerated(evaluation_gate_status="EVALUATION_GATE_BLOCKED")

        self.assert_blocked_with(result, "accelerated cooldown blocks failed V13 gate")

    def test_accelerated_mode_blocks_missing_previous_reconciliation(self) -> None:
        result = run_accelerated(state=soak.SoakRunState(previous_reconciliation_exists=False))

        self.assert_blocked_with(result, "accelerated cooldown blocks missing previous reconciliation")

    def test_accelerated_mode_blocks_unresolved_reconciliation_mismatch(self) -> None:
        result = run_accelerated(state=soak.SoakRunState(previous_reconciliation_matched=False))

        self.assert_blocked_with(result, "accelerated cooldown blocks unresolved reconciliation mismatch")

    def test_accelerated_mode_blocks_missing_previous_post_mortem(self) -> None:
        result = run_accelerated(state=soak.SoakRunState(previous_post_mortem_exists=False))

        self.assert_blocked_with(result, "accelerated cooldown blocks missing previous post-mortem")

    def test_accelerated_mode_blocks_unresolved_post_mortem_blocker(self) -> None:
        result = run_accelerated(state=soak.SoakRunState(previous_post_mortem_has_blockers=True))

        self.assert_blocked_with(result, "accelerated cooldown blocks unresolved post-mortem blocker")

    def test_accelerated_mode_blocks_unresolved_issue(self) -> None:
        result = run_accelerated(state=soak.SoakRunState(unresolved_issue_exists=True))

        self.assert_blocked_with(result, "accelerated cooldown blocks unresolved issue")

    def test_accelerated_mode_blocks_kill_switch_active(self) -> None:
        result = run_accelerated(state=soak.SoakRunState(kill_switch_active=True))

        self.assert_blocked_with(result, "accelerated cooldown blocks kill switch active")

    def test_soak_reports_include_accelerated_cooldown_fields(self) -> None:
        report = generated_final_report_text(accelerated_cooldown=accelerated_config())

        for field in (
            "accelerated_mode_enabled",
            "configured_cooldown_seconds",
            "production_default_cooldown_seconds",
            "accelerated_mode_reason",
            "alpaca_paper_confirmed",
            "live_endpoint_rejected",
            "live_trading_unsupported",
            "production_cooldown_remains_default",
            "does_not_authorize_frequency_increase",
            "does_not_authorize_live_trading",
        ):
            self.assertIn(field, report)

    def test_soak_reports_include_required_accelerated_mode_statements(self) -> None:
        report = generated_final_report_text(accelerated_cooldown=accelerated_config())

        for statement in (
            "Accelerated cooldown was used for paper soak framework validation only.",
            "Production/default cooldown remains 24 hours.",
            "Live trading remains unsupported.",
            "Increasing notional remains prohibited.",
            "Multi-symbol automation remains prohibited.",
            "Batch orders remain prohibited.",
            "Cancel/replace remains prohibited.",
        ):
            self.assertIn(statement, report)

    def assert_blocked_with(self, result, reason: str) -> None:
        self.assertEqual(result.final_status, soak.SOAK_RUN_BLOCKED)
        self.assertIn(reason, result.block_reasons)
        self.assertFalse(result.real_order_sent)
        self.assertFalse(result.real_alpaca_api_called)


def run_with(**overrides):
    config = soak.valid_soak_config(**overrides)
    return soak.evaluate_soak_run(config)


def run_accelerated(
    *,
    configured_cooldown_seconds=60,
    live_trading_assumption=False,
    used_for_soak_testing=True,
    **overrides,
):
    overrides["accelerated_cooldown"] = accelerated_config(
        configured_cooldown_seconds=configured_cooldown_seconds,
        live_trading_assumption=live_trading_assumption,
        used_for_soak_testing=used_for_soak_testing,
    )
    config = soak.valid_soak_config(**overrides)
    return soak.evaluate_soak_run(config)


def accelerated_config(
    *,
    configured_cooldown_seconds=60,
    live_trading_assumption=False,
    used_for_soak_testing=True,
):
    return soak.AcceleratedSoakCooldownConfig(
        accelerated_mode_enabled=True,
        configured_cooldown_seconds=configured_cooldown_seconds,
        accelerated_mode_reason="phase54-test",
        live_trading_assumption=live_trading_assumption,
        used_for_soak_testing=used_for_soak_testing,
    )


def sample_record(**overrides):
    values = {
        "run_id": "run-1",
        "timestamp": "2026-05-20T00:00:00Z",
        "send_decision": soak.SOAK_RUN_ALLOWED,
        "submitted_paper_order_id": "mock-soak-paper-order-001",
        "reconciliation_status": soak.RECONCILIATION_MATCHED,
        "post_mortem_status": "PASS",
    }
    values.update(overrides)
    return soak.SoakRunRecord(**values)


def generated_final_report_text(
    accelerated_cooldown=None,
) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        paths = soak.generate_soak_reports(
            records=(sample_record(),),
            accelerated_cooldown=accelerated_cooldown,
            output_root=Path(tmp),
        )
        return Path(paths.soak_final_report_path or "").read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
