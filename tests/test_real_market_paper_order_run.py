from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "runtime"
MODULE_PATH = RUNTIME_PATH / "real_market_paper_order_run.py"

if str(RUNTIME_PATH) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PATH))

spec = importlib.util.spec_from_file_location("real_market_paper_order_run", MODULE_PATH)
paper_run = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["real_market_paper_order_run"] = paper_run
spec.loader.exec_module(paper_run)


class FakePaperOrderAdapter:
    def __init__(self) -> None:
        self.orders = []

    def send_paper_order(self, order):
        self.orders.append(order)
        return paper_run.PaperOrderResult(
            accepted=True,
            paper_order_id="fake-paper-order-1",
            reconciliation_status="RECONCILIATION_MATCHED",
            paper_only=True,
            live_order_sent=False,
        )


class RealMarketPaperOrderRunTests(unittest.TestCase):
    def test_happy_path_sends_one_fake_paper_order_only_after_all_gates_pass(self) -> None:
        with run_context() as ctx:
            adapter = FakePaperOrderAdapter()

            result = paper_run.run_real_market_paper_order(
                ctx.config(),
                phase57_signal=valid_signal(),
                paper_order_adapter=adapter,
            )

            self.assertEqual(result.final_status, "PAPER_ORDER_SENT")
            self.assertTrue(result.candidate_created)
            self.assertTrue(result.human_review_approved)
            self.assertTrue(result.finalized_request_created)
            self.assertTrue(result.manual_execution_confirmed)
            self.assertTrue(result.paper_order_sent)
            self.assertFalse(result.live_order_sent)
            self.assertEqual(result.reconciliation_status, "RECONCILIATION_MATCHED")
            self.assertEqual(len(adapter.orders), 1)
            self.assertTrue(adapter.orders[0].paper_only)
            self.assertFalse(adapter.orders[0].live_trading_assumption)
            self.assertLessEqual(adapter.orders[0].notional_usd, 100)

    def test_no_trade_blocks_and_sends_no_order(self) -> None:
        self.assert_blocked_signal(valid_signal(strategy_decision="NO_TRADE"))

    def test_reject_blocks_and_sends_no_order(self) -> None:
        self.assert_blocked_signal(valid_signal(strategy_decision="REJECT"))

    def test_missing_watchlist_approval_blocks(self) -> None:
        with run_context(watchlist_symbol="MSFT") as ctx:
            self.assert_blocked(ctx.config(), valid_signal(), "missing_watchlist_approval")

    def test_zero_symbols_blocks(self) -> None:
        with run_context() as ctx:
            self.assert_blocked(ctx.config(symbols=()), valid_signal(), "missing_symbol")

    def test_more_than_one_symbol_blocks(self) -> None:
        with run_context() as ctx:
            self.assert_blocked(
                ctx.config(symbols=("AAPL", "MSFT")),
                valid_signal(),
                "more_than_one_symbol_blocked",
            )

    def test_max_notional_over_100_blocks(self) -> None:
        self.assert_blocked_config({"max_notional_usd": 101.0}, "max_notional_over_100")

    def test_paper_only_false_blocks(self) -> None:
        self.assert_blocked_config({"paper_only": False}, "paper_only_required")

    def test_human_review_missing_blocks(self) -> None:
        self.assert_blocked_config(
            {"human_review_approved": False},
            "human_review_approval_required",
        )

    def test_manual_execution_confirmation_missing_blocks(self) -> None:
        self.assert_blocked_config(
            {"manual_execution_confirmed": False},
            "manual_execution_confirmation_required",
        )

    def test_allow_paper_send_false_blocks(self) -> None:
        self.assert_blocked_config({"allow_paper_send": False}, "allow_paper_send_required")

    def test_evaluation_gate_fail_blocks(self) -> None:
        self.assert_blocked_config({"evaluation_gate_status": "FAIL"}, "evaluation_gate_failed")

    def test_negative_regression_fail_blocks(self) -> None:
        self.assert_blocked_config(
            {"negative_regression_status": "FAIL"},
            "negative_regression_failed",
        )

    def test_preflight_fail_blocks(self) -> None:
        self.assert_blocked_config({"preflight_status": "BLOCKED"}, "preflight_failed")

    def test_stale_data_blocks(self) -> None:
        self.assert_blocked_signal(valid_signal(freshness_status="STALE"), "freshness_failed")

    def test_missing_timestamp_blocks(self) -> None:
        self.assert_blocked_signal(valid_signal(timestamp="MISSING"), "missing_timestamp")

    def test_missing_symbol_blocks(self) -> None:
        self.assert_blocked_signal(valid_signal(symbol="MISSING"), "phase57_symbol_mismatch")

    def test_missing_timeframe_blocks(self) -> None:
        self.assert_blocked_signal(valid_signal(timeframe="MISSING"), "missing_timeframe")

    def test_missing_session_blocks(self) -> None:
        self.assert_blocked_signal(valid_signal(session="MISSING"), "missing_session")

    def test_missing_spread_when_required_blocks(self) -> None:
        self.assert_blocked_signal(
            valid_signal(spread_available=False),
            "missing_required_spread",
        )

    def test_missing_volume_when_required_blocks(self) -> None:
        self.assert_blocked_signal(
            valid_signal(volume_available=False),
            "missing_required_volume",
        )

    def test_live_endpoint_detection_blocks(self) -> None:
        self.assert_blocked_signal(
            valid_signal(live_endpoint_detected=True),
            "live_endpoint_detected",
        )

    def test_live_trading_assumption_true_blocks(self) -> None:
        self.assert_blocked_config(
            {"live_trading_assumption": True},
            "live_trading_assumption_blocked",
        )

    def test_broker_execution_readiness_before_preflight_blocks(self) -> None:
        self.assert_blocked_config(
            {"broker_execution_readiness": True},
            "broker_execution_readiness_before_preflight",
        )

    def test_non_paper_account_assumption_blocks(self) -> None:
        self.assert_blocked_config(
            {"non_paper_account_assumption": True},
            "non_paper_account_assumption",
        )

    def test_live_order_endpoint_blocks(self) -> None:
        self.assert_blocked_config(
            {"order_endpoint_live": True},
            "live_order_endpoint_detected",
        )

    def test_data_integrity_fail_blocks(self) -> None:
        self.assert_blocked_signal(
            valid_signal(data_integrity_status="FAIL"),
            "data_integrity_failed",
        )

    def test_completeness_fail_blocks(self) -> None:
        self.assert_blocked_signal(
            valid_signal(completeness_status="INCOMPLETE"),
            "completeness_failed",
        )

    def test_fake_paper_adapter_receives_zero_orders_on_blocked_path(self) -> None:
        with run_context() as ctx:
            adapter = FakePaperOrderAdapter()
            result = paper_run.run_real_market_paper_order(
                ctx.config(max_notional_usd=101.0),
                phase57_signal=valid_signal(),
                paper_order_adapter=adapter,
            )

            self.assertEqual(result.final_status, "BLOCKED")
            self.assertEqual(len(adapter.orders), 0)

    def test_no_live_order_adapter_is_imported_and_no_live_endpoint_is_used(self) -> None:
        module_text = MODULE_PATH.read_text(encoding="utf-8")
        import_lines = [
            line
            for line in module_text.splitlines()
            if line.startswith("import ") or line.startswith("from ")
        ]

        self.assertFalse(any("alpaca_paper_order_adapter" in line for line in import_lines))
        self.assertFalse(any("automated_paper_send" in line for line in import_lines))
        self.assertFalse(any("one_real_automated_paper_send" in line for line in import_lines))
        self.assertNotIn("/v2/orders", module_text)
        self.assertNotIn("api.alpaca.markets", module_text)
        self.assertNotIn("submit_order", module_text)

    def test_no_env_file_is_created(self) -> None:
        with run_context() as ctx:
            adapter = FakePaperOrderAdapter()
            paper_run.run_real_market_paper_order(
                ctx.config(),
                phase57_signal=valid_signal(),
                paper_order_adapter=adapter,
            )

            self.assertFalse((ctx.root / ".env").exists())

    def test_no_secrets_are_printed_to_report(self) -> None:
        secret = "phase58-secret-value"
        with run_context() as ctx:
            result = paper_run.run_real_market_paper_order(
                ctx.config(),
                phase57_signal=valid_signal(strategy_reason=secret),
                paper_order_adapter=FakePaperOrderAdapter(),
            )

            report = result.report_path.read_text(encoding="utf-8")
            self.assertNotIn(secret, report)
            self.assertNotIn("ALPACA_API_SECRET_KEY", report)
            self.assertIn("[REDACTED]", report)
            self.assertIn("No live order was sent.", report)
            self.assertIn("Paper-only execution path was used.", report)
            self.assertIn("Human review remained required.", report)
            self.assertIn("Manual execution confirmation remained required.", report)
            self.assertIn("Live trading remains unsupported.", report)

    def test_secret_in_block_reason_is_redacted(self) -> None:
        secret = "secret=phase58-block-reason-token"
        with run_context() as ctx:
            result = paper_run.run_real_market_paper_order(
                ctx.config(symbols=("AAPL", "MSFT")),
                phase57_signal=valid_signal(strategy_reason=secret),
                paper_order_adapter=FakePaperOrderAdapter(),
            )

            report = result.report_path.read_text(encoding="utf-8")
            self.assertNotIn(secret, report)
            self.assertIn("[REDACTED]", report)

    def test_report_reason_field_redacts_secret(self) -> None:
        secret = "api_key=REASON_SECRET_TOKEN_123456789"
        with run_context() as ctx:
            result = paper_run.RealMarketPaperOrderRunResult(
                final_status="BLOCKED",
                reason=secret,
                symbol="AAPL",
                source="fake_read_only_market_data",
                timestamp="2026-05-20T13:30:00+00:00",
                timeframe="1m",
                session="market_open",
                watchlist_approval_status="APPROVED",
                freshness_status="FRESH",
                completeness_status="COMPLETE",
                data_integrity_status="PASS",
                strategy_decision="TRADE_PROPOSAL",
                strategy_reason="Validated dry-run proposal.",
                evaluation_gate_status="EVALUATION_GATE_PASSED",
                negative_regression_status="PASS",
                candidate_created=False,
                human_review_approved=True,
                finalized_request_created=False,
                manual_execution_confirmed=True,
                preflight_status="PAPER_ORDER_SEND_ALLOWED",
                max_notional_usd=100.0,
                paper_only=True,
                broker_execution_readiness=False,
                order_api_used=False,
                paper_order_sent=False,
                live_order_sent=False,
                live_trading_assumption=False,
                secrets_printed=False,
                reconciliation_status="NOT_RUN",
            )
            runner = paper_run.RealMarketPaperOrderRunner(
                ctx.config(),
                phase57_signal=valid_signal(),
                paper_order_adapter=FakePaperOrderAdapter(),
            )

            written = runner._write_report(result)
            report = written.report_path.read_text(encoding="utf-8")
            self.assertNotIn(secret, report)
            self.assertIn("[REDACTED]", report)
            self.assertIn("No live order was sent.", report)
            self.assertIn("Paper-only execution path was used.", report)
            self.assertIn("Human review remained required.", report)
            self.assertIn("Manual execution confirmation remained required.", report)
            self.assertIn("Live trading remains unsupported.", report)

    def test_secret_in_reconciliation_status_is_redacted(self) -> None:
        class SecretReconciliationAdapter(FakePaperOrderAdapter):
            def send_paper_order(self, order):
                self.orders.append(order)
                return paper_run.PaperOrderResult(
                    accepted=True,
                    paper_order_id="fake-paper-order-1",
                    reconciliation_status="token=phase58-reconciliation-token",
                    paper_only=True,
                    live_order_sent=False,
                )

        with run_context() as ctx:
            result = paper_run.run_real_market_paper_order(
                ctx.config(),
                phase57_signal=valid_signal(),
                paper_order_adapter=SecretReconciliationAdapter(),
            )

            report = result.report_path.read_text(encoding="utf-8")
            self.assertNotIn("phase58-reconciliation-token", report)
            self.assertIn("[REDACTED]", report)

    def test_safety_booleans_remain_readable_after_redaction(self) -> None:
        with run_context() as ctx:
            result = paper_run.run_real_market_paper_order(
                ctx.config(),
                phase57_signal=valid_signal(strategy_reason="api_key=phase58-key-value"),
                paper_order_adapter=FakePaperOrderAdapter(),
            )

            report = result.report_path.read_text(encoding="utf-8")
            self.assertIn("paper_only: true", report)
            self.assertIn("paper_order_sent: true", report)
            self.assertIn("live_order_sent: false", report)
            self.assertIn("live_trading_assumption: false", report)
            self.assertIn("broker_execution_readiness: true", report)
            self.assertIn("human_review_approved: true", report)
            self.assertIn("manual_execution_confirmed: true", report)
            self.assertIn("preflight_status: PAPER_ORDER_SEND_ALLOWED", report)
            self.assertIn("final status: PAPER_ORDER_SENT", report)

    def test_report_contains_required_statements(self) -> None:
        with run_context() as ctx:
            result = paper_run.run_real_market_paper_order(
                ctx.config(),
                phase57_signal=valid_signal(),
                paper_order_adapter=FakePaperOrderAdapter(),
            )

            report = result.report_path.read_text(encoding="utf-8")
            self.assertIn("No live order was sent.", report)
            self.assertIn("Paper-only execution path was used.", report)
            self.assertIn("Human review remained required.", report)
            self.assertIn("Manual execution confirmation remained required.", report)
            self.assertIn("Live trading remains unsupported.", report)

    def assert_blocked_signal(self, signal, reason: str | None = None) -> None:
        with run_context() as ctx:
            self.assert_blocked(ctx.config(), signal, reason)

    def assert_blocked_config(self, overrides: dict[str, object], reason: str) -> None:
        with run_context() as ctx:
            self.assert_blocked(ctx.config(**overrides), valid_signal(), reason)

    def assert_blocked(self, config, signal, reason: str | None = None) -> None:
        adapter = FakePaperOrderAdapter()
        result = paper_run.run_real_market_paper_order(
            config,
            phase57_signal=signal,
            paper_order_adapter=adapter,
        )

        self.assertEqual(result.final_status, "BLOCKED")
        self.assertFalse(result.paper_order_sent)
        self.assertFalse(result.live_order_sent)
        self.assertEqual(len(adapter.orders), 0)
        if reason:
            self.assertEqual(result.reason, reason)


class run_context:
    def __init__(self, *, watchlist_symbol: str = "AAPL") -> None:
        self.watchlist_symbol = watchlist_symbol
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None
        self.root: Path
        self.watchlist_path: Path
        self.report_root: Path

    def __enter__(self) -> run_context:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self._temp_dir.name)
        self.watchlist_path = self.root / "memory" / "watchlist.md"
        self.watchlist_path.parent.mkdir(parents=True)
        self.watchlist_path.write_text(
            "\n".join(
                [
                    "# Watchlist",
                    "",
                    f"- Symbol: {self.watchlist_symbol}",
                    "- Approved: true",
                    "- Reason: Phase 58 paper send test",
                    "- Required context condition: read-only market proposal",
                    "- Required liquidity condition: spread and volume available",
                    "- Expiration or review date: 2026-06-01",
                    "",
                    "Watchlist inclusion is not a trade proposal.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.report_root = self.root / "reports" / "real_market_paper_order_run"
        return self

    def __exit__(self, *args: object) -> None:
        assert self._temp_dir is not None
        self._temp_dir.cleanup()

    def config(self, **overrides: object):
        values = {
            "symbols": ("AAPL",),
            "max_notional_usd": 100.0,
            "paper_only": True,
            "human_review_approved": True,
            "manual_execution_confirmed": True,
            "allow_paper_send": True,
            "evaluation_gate_status": "EVALUATION_GATE_PASSED",
            "negative_regression_status": "PASS",
            "preflight_status": "PAPER_ORDER_SEND_ALLOWED",
            "watchlist_path": self.watchlist_path,
            "report_root": self.report_root,
        }
        values.update(overrides)
        return paper_run.RealMarketPaperOrderRunConfig(**values)


def valid_signal(**overrides: object):
    values = {
        "strategy_decision": "TRADE_PROPOSAL",
        "strategy_reason": "Validated dry-run proposal.",
        "symbol": "AAPL",
        "source": "fake_read_only_market_data",
        "timestamp": "2026-05-20T13:30:00+00:00",
        "timeframe": "1m",
        "session": "market_open",
        "watchlist_approval_status": "APPROVED",
        "freshness_status": "FRESH",
        "completeness_status": "COMPLETE",
        "data_integrity_status": "PASS",
        "spread_available": True,
        "volume_available": True,
    }
    values.update(overrides)
    return paper_run.Phase57Signal(**values)


if __name__ == "__main__":
    unittest.main()
