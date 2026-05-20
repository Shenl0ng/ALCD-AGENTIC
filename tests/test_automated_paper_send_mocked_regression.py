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


regression = load_module("automated_paper_send_mocked_regression")


class AutomatedPaperSendMockedRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.regression_run = regression.run_automated_paper_send_mocked_regression(output_root=Path(cls._tmp.name))
        cls.results = {result.scenario_id: result for result in cls.regression_run.results}

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmp.cleanup()

    def test_mocked_regression_runner_exists(self) -> None:
        self.assertTrue(hasattr(regression, "run_automated_paper_send_mocked_regression"))

    def test_full_valid_mocked_scenario_submits_exactly_one_mocked_paper_limit_day_order(self) -> None:
        result = self.results["full_valid_mocked_automated_paper_send"]

        self.assertTrue(result.passed)
        self.assertEqual(result.final_status, regression.AUTOMATED_PAPER_SEND_SUBMITTED)
        self.assertEqual(result.mocked_order_count, 1)
        payload = result.mocked_payloads[0]
        self.assertEqual(payload["type"], "limit")
        self.assertEqual(payload["time_in_force"], "day")

    def test_default_disabled_scenario_sends_zero_mocked_orders(self) -> None:
        self.assert_blocked_zero_orders("default_disabled", regression.AUTOMATED_PAPER_SEND_BLOCKED)

    def test_execution_flag_disabled_scenario_sends_zero_mocked_orders(self) -> None:
        self.assert_blocked_zero_orders("execution_flag_disabled", regression.AUTOMATED_PAPER_SEND_BLOCKED)

    def test_kill_switch_scenario_blocks_and_sends_zero_mocked_orders(self) -> None:
        self.assert_blocked_zero_orders("kill_switch", regression.AUTOMATED_PAPER_SEND_REJECTED_BY_KILL_SWITCH)

    def test_daily_order_limit_scenario_blocks_and_sends_zero_mocked_orders(self) -> None:
        self.assert_blocked_zero_orders("daily_order_limit", regression.AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS)

    def test_daily_notional_limit_scenario_blocks_and_sends_zero_mocked_orders(self) -> None:
        self.assert_blocked_zero_orders("daily_notional_limit", regression.AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS)

    def test_cooldown_scenario_blocks_and_sends_zero_mocked_orders(self) -> None:
        self.assert_blocked_zero_orders("cooldown", regression.AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS)

    def test_missing_previous_reconciliation_scenario_blocks_and_sends_zero_mocked_orders(self) -> None:
        self.assert_blocked_zero_orders(
            "missing_previous_reconciliation",
            regression.AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION,
        )

    def test_unresolved_reconciliation_mismatch_scenario_blocks_and_sends_zero_mocked_orders(self) -> None:
        self.assert_blocked_zero_orders(
            "unresolved_reconciliation_mismatch",
            regression.AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION,
        )

    def test_missing_post_mortem_scenario_blocks_and_sends_zero_mocked_orders(self) -> None:
        self.assert_blocked_zero_orders("missing_post_mortem", regression.AUTOMATED_PAPER_SEND_REJECTED_BY_POST_MORTEM)

    def test_unresolved_issue_scenario_blocks_and_sends_zero_mocked_orders(self) -> None:
        self.assert_blocked_zero_orders("unresolved_issue", regression.AUTOMATED_PAPER_SEND_BLOCKED)

    def test_live_endpoint_scenario_blocks_and_sends_zero_mocked_orders(self) -> None:
        self.assert_blocked_zero_orders("live_endpoint", regression.AUTOMATED_PAPER_SEND_REJECTED_BY_PREFLIGHT)

    def test_notional_over_100_scenario_blocks_and_sends_zero_mocked_orders(self) -> None:
        self.assert_blocked_zero_orders("notional_over_100", regression.AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS)

    def test_batch_cancel_replace_scenario_blocks_and_sends_zero_mocked_orders(self) -> None:
        self.assert_blocked_zero_orders("batch_cancel_replace", regression.AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS)

    def test_report_is_generated(self) -> None:
        self.assertEqual(self.regression_run.final_status, regression.REGRESSION_PASSED)
        self.assertTrue(Path(self.regression_run.report_path or "").exists())

    def test_report_proves_no_real_alpaca_api_was_called(self) -> None:
        report = self.report_text()

        self.assertIn("Proof no real Alpaca API was called: true", report)

    def test_report_proves_no_real_order_was_sent(self) -> None:
        report = self.report_text()

        self.assertIn("Proof no real order was sent: true", report)

    def test_report_proves_system_returned_to_dry_run_only(self) -> None:
        report = self.report_text()

        self.assertIn("Proof system returned to DRY_RUN_ONLY: True", report)

    def test_report_proves_flags_disabled_unset_after_test_context(self) -> None:
        report = self.report_text()

        self.assertIn("Proof flags were disabled/unset after test context: True", report)

    def test_report_contains_required_safety_statements(self) -> None:
        report = self.report_text()

        for statement in (
            "Automated paper send remains paper-only.",
            "Live trading remains unsupported.",
            "Increasing notional remains prohibited.",
            "Batch orders remain prohibited.",
            "Cancel/replace remains prohibited.",
        ):
            self.assertIn(statement, report)

    def assert_blocked_zero_orders(self, scenario_id: str, expected_status: str) -> None:
        result = self.results[scenario_id]
        self.assertTrue(result.passed, result.failure_reason)
        self.assertEqual(result.final_status, expected_status)
        self.assertEqual(result.mocked_order_count, 0)
        self.assertFalse(result.real_alpaca_api_called)
        self.assertFalse(result.real_order_sent)

    def report_text(self) -> str:
        return Path(self.regression_run.report_path or "").read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
