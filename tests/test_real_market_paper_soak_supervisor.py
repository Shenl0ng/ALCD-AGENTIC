from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "runtime"
MODULE_PATH = RUNTIME_PATH / "real_market_paper_soak_supervisor.py"

if str(RUNTIME_PATH) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PATH))

spec = importlib.util.spec_from_file_location("real_market_paper_soak_supervisor", MODULE_PATH)
soak = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["real_market_paper_soak_supervisor"] = soak
spec.loader.exec_module(soak)


@dataclass(frozen=True)
class FakePhase57Result:
    strategy_decision: str = "TRADE_PROPOSAL"
    strategy_reason: str = "fake strategy reason"
    symbol: str = "AAPL"
    data_integrity_status: str = "PASS"
    report_path: str = "phase57-report.md"
    live_order_sent: bool = False
    live_trading_assumption: bool = False
    live_endpoint_detected: bool = False
    secrets_printed: bool = False
    runner_message: str = ""


@dataclass(frozen=True)
class FakePhase58Result:
    final_status: str = "PAPER_ORDER_SENT"
    reason: str = "fake paper send"
    symbol: str = "AAPL"
    paper_order_sent: bool = True
    report_path: str = "phase58-report.md"
    live_order_sent: bool = False
    live_trading_assumption: bool = False
    live_endpoint_detected: bool = False
    secrets_printed: bool = False


@dataclass(frozen=True)
class FakePhase59Result:
    reconciliation_status: str = "RECONCILED"
    final_status: str = "RECONCILED"
    report_path: str = "phase59-report.md"
    evidence_manifest_path: str = "phase59-manifest.md"
    live_order_sent: bool = False
    live_trading_assumption: bool = False
    live_endpoint_detected: bool = False
    secrets_printed: bool = False


class FakePhase57Runner:
    def __init__(self, results: list[FakePhase57Result] | None = None) -> None:
        self.results = results or [FakePhase57Result()]
        self.calls = 0

    def run(self):
        result = self.results[min(self.calls, len(self.results) - 1)]
        self.calls += 1
        return result


class FakePhase58Runner:
    def __init__(self, result: FakePhase58Result | None = None) -> None:
        self.result = result or FakePhase58Result()
        self.calls = 0
        self.inputs = []

    def run(self, phase57_result):
        self.calls += 1
        self.inputs.append(phase57_result)
        return self.result


class FakePhase59Runner:
    def __init__(self, result: FakePhase59Result | None = None) -> None:
        self.result = result or FakePhase59Result()
        self.calls = 0
        self.inputs = []

    def run(self, phase58_result):
        self.calls += 1
        self.inputs.append(phase58_result)
        return self.result


class RealMarketPaperSoakSupervisorTests(unittest.TestCase):
    def test_default_allow_paper_send_false_runs_phase57_only_and_sends_no_order(self) -> None:
        with run_context() as ctx:
            p57 = FakePhase57Runner()
            p58 = FakePhase58Runner()
            p59 = FakePhase59Runner()

            result = soak.run_real_market_paper_soak(
                ctx.config(max_cycles=2),
                phase57_runner=p57,
                phase58_runner=p58,
                phase59_runner=p59,
            )

            self.assertEqual(result.final_status, "PASS")
            self.assertEqual(p57.calls, 2)
            self.assertEqual(p58.calls, 0)
            self.assertEqual(p59.calls, 0)
            self.assertEqual(result.counters.paper_order_attempts, 0)
            self.assertEqual(result.counters.paper_orders_sent, 0)

    def test_allow_paper_send_true_happy_path_calls_phase57_phase58_phase59(self) -> None:
        with run_context() as ctx:
            p57 = FakePhase57Runner()
            p58 = FakePhase58Runner()
            p59 = FakePhase59Runner()

            result = soak.run_real_market_paper_soak(
                ctx.config(allow_paper_send=True),
                phase57_runner=p57,
                phase58_runner=p58,
                phase59_runner=p59,
            )

            self.assertEqual(result.final_status, "PASS")
            self.assertEqual(p57.calls, 1)
            self.assertEqual(p58.calls, 1)
            self.assertEqual(p59.calls, 1)
            self.assertEqual(result.counters.paper_order_attempts, 1)
            self.assertEqual(result.counters.paper_orders_sent, 1)
            self.assertEqual(result.counters.reconciliations_run, 1)

    def test_no_trade_does_not_call_phase58(self) -> None:
        self.assert_no_phase58_for_decision("NO_TRADE")

    def test_reject_does_not_call_phase58(self) -> None:
        self.assert_no_phase58_for_decision("REJECT")

    def test_trade_proposal_may_call_phase58_only_if_allow_paper_send_true(self) -> None:
        with run_context() as ctx:
            p58 = FakePhase58Runner()
            soak.run_real_market_paper_soak(
                ctx.config(allow_paper_send=False),
                phase57_runner=FakePhase57Runner([FakePhase57Result(strategy_decision="TRADE_PROPOSAL")]),
                phase58_runner=p58,
                phase59_runner=FakePhase59Runner(),
            )
            self.assertEqual(p58.calls, 0)

            p58 = FakePhase58Runner()
            soak.run_real_market_paper_soak(
                ctx.config(allow_paper_send=True),
                phase57_runner=FakePhase57Runner([FakePhase57Result(strategy_decision="TRADE_PROPOSAL")]),
                phase58_runner=p58,
                phase59_runner=FakePhase59Runner(),
            )
            self.assertEqual(p58.calls, 1)

    def test_phase59_reconciliation_runs_after_fake_phase58_send(self) -> None:
        with run_context() as ctx:
            p58 = FakePhase58Runner(FakePhase58Result(paper_order_sent=True))
            p59 = FakePhase59Runner()

            soak.run_real_market_paper_soak(
                ctx.config(allow_paper_send=True),
                phase57_runner=FakePhase57Runner(),
                phase58_runner=p58,
                phase59_runner=p59,
            )

            self.assertEqual(p59.calls, 1)
            self.assertIs(p59.inputs[0], p58.result)

    def test_failed_phase59_reconciliation_stops_soak(self) -> None:
        with run_context() as ctx:
            result = soak.run_real_market_paper_soak(
                ctx.config(allow_paper_send=True, max_cycles=3),
                phase57_runner=FakePhase57Runner(),
                phase58_runner=FakePhase58Runner(),
                phase59_runner=FakePhase59Runner(FakePhase59Result(reconciliation_status="FAILED")),
            )

            self.assertEqual(result.final_status, "BLOCKED")
            self.assertEqual(result.counters.reconciliations_failed, 1)
            self.assertEqual(result.counters.stopped_reason, "phase59_reconciliation_failed")
            self.assertEqual(result.counters.cycles_started, 1)

    def test_kill_switch_enabled_true_blocks_before_any_cycle(self) -> None:
        self.assert_blocked_config({"kill_switch_enabled": True}, "kill_switch_enabled")

    def test_zero_symbols_block(self) -> None:
        self.assert_blocked_config({"symbols": ()}, "missing_symbol")

    def test_more_than_one_symbol_blocks(self) -> None:
        self.assert_blocked_config({"symbols": ("AAPL", "MSFT")}, "more_than_one_symbol_blocked")

    def test_multi_symbol_input_blocks(self) -> None:
        self.assert_blocked_config({"symbols": ("AAPL,MSFT",)}, "more_than_one_symbol_blocked")

    def test_missing_watchlist_approval_blocks(self) -> None:
        with run_context(watchlist_symbol="MSFT") as ctx:
            result = soak.run_real_market_paper_soak(
                ctx.config(),
                phase57_runner=FakePhase57Runner(),
            )
            self.assertEqual(result.counters.stopped_reason, "missing_watchlist_approval")

    def test_max_notional_over_100_blocks(self) -> None:
        self.assert_blocked_config({"max_notional_usd": 101.0}, "max_notional_over_100")

    def test_paper_only_false_blocks(self) -> None:
        self.assert_blocked_config({"paper_only": False}, "paper_only_required")

    def test_require_human_review_false_blocks(self) -> None:
        self.assert_blocked_config({"require_human_review": False}, "human_review_required")

    def test_require_manual_confirmation_false_blocks(self) -> None:
        self.assert_blocked_config(
            {"require_manual_confirmation": False},
            "manual_execution_confirmation_required",
        )

    def test_require_preflight_false_blocks(self) -> None:
        self.assert_blocked_config({"require_preflight": False}, "preflight_required")

    def test_max_paper_orders_total_is_enforced(self) -> None:
        with run_context() as ctx:
            p58 = FakePhase58Runner()
            result = soak.run_real_market_paper_soak(
                ctx.config(allow_paper_send=True, max_paper_orders_total=0),
                phase57_runner=FakePhase57Runner(),
                phase58_runner=p58,
                phase59_runner=FakePhase59Runner(),
            )

            self.assertEqual(result.final_status, "BLOCKED")
            self.assertEqual(result.counters.stopped_reason, "max_paper_orders_total_reached")
            self.assertEqual(p58.calls, 0)

    def test_max_paper_orders_per_symbol_is_enforced(self) -> None:
        with run_context() as ctx:
            p58 = FakePhase58Runner()
            result = soak.run_real_market_paper_soak(
                ctx.config(allow_paper_send=True, max_paper_orders_per_symbol=0),
                phase57_runner=FakePhase57Runner(),
                phase58_runner=p58,
                phase59_runner=FakePhase59Runner(),
            )

            self.assertEqual(result.final_status, "BLOCKED")
            self.assertEqual(result.counters.stopped_reason, "max_paper_orders_per_symbol_reached")
            self.assertEqual(p58.calls, 0)

    def test_no_automatic_retry_after_failure(self) -> None:
        with run_context() as ctx:
            p58 = FakePhase58Runner(FakePhase58Result(final_status="BLOCKED", paper_order_sent=False))
            result = soak.run_real_market_paper_soak(
                ctx.config(allow_paper_send=True, max_cycles=3),
                phase57_runner=FakePhase57Runner(),
                phase58_runner=p58,
                phase59_runner=FakePhase59Runner(),
            )

            self.assertEqual(result.final_status, "BLOCKED")
            self.assertEqual(p58.calls, 1)
            self.assertEqual(result.counters.paper_order_attempts, 1)
            self.assertEqual(result.counters.paper_orders_sent, 0)

    def test_live_trading_assumption_true_blocks(self) -> None:
        self.assert_blocked_config(
            {"live_trading_assumption": True},
            "live_trading_assumption_blocked",
        )

    def test_live_endpoint_detection_blocks(self) -> None:
        self.assert_blocked_config({"live_endpoint_detected": True}, "live_endpoint_detected")

    def test_secret_in_runner_message_is_redacted_and_stops(self) -> None:
        secret = "PHASE60SECRET123456789"
        with run_context() as ctx:
            result = soak.run_real_market_paper_soak(
                ctx.config(injected_secrets=(secret,)),
                phase57_runner=FakePhase57Runner(
                    [FakePhase57Result(runner_message=f"token={secret}")]
                ),
            )

            report = result.artifacts.report_path.read_text(encoding="utf-8")
            self.assertEqual(result.final_status, "BLOCKED")
            self.assertNotIn(secret, report)
            self.assertIn("[REDACTED]", report)

    def test_exact_injected_secret_is_absent_from_soak_report(self) -> None:
        secret = "EXACT_PHASE60_SECRET"
        with run_context() as ctx:
            result = soak.run_real_market_paper_soak(
                ctx.config(injected_secrets=(secret,), symbols=(secret,)),
                phase57_runner=FakePhase57Runner(),
            )

            report = result.artifacts.report_path.read_text(encoding="utf-8")
            self.assertNotIn(secret, report)
            self.assertIn("[REDACTED]", report)

    def test_report_contains_all_required_safety_statements(self) -> None:
        with run_context() as ctx:
            result = soak.run_real_market_paper_soak(
                ctx.config(),
                phase57_runner=FakePhase57Runner(),
            )

            report = result.artifacts.report_path.read_text(encoding="utf-8")
            self.assertIn("No live order was sent.", report)
            self.assertIn("Paper-only execution path remains required.", report)
            self.assertIn("Human review remained required.", report)
            self.assertIn("Manual execution confirmation remained required.", report)
            self.assertIn("Preflight remained required.", report)
            self.assertIn("Live trading remains unsupported.", report)

    def test_evidence_manifest_is_created_and_contains_required_evidence(self) -> None:
        with run_context() as ctx:
            result = soak.run_real_market_paper_soak(
                ctx.config(),
                phase57_runner=FakePhase57Runner(),
            )

            manifest_path = result.artifacts.evidence_manifest_path
            self.assertTrue(manifest_path.exists())
            manifest = manifest_path.read_text(encoding="utf-8")
            self.assertIn("Order Limit Evidence", manifest)
            self.assertIn("Kill-Switch Evidence", manifest)
            self.assertIn("No-Live-Order Evidence", manifest)
            self.assertIn("No-Secret Evidence", manifest)
            self.assertIn("Test Command Evidence", manifest)

    def test_no_alpaca_order_adapter_import(self) -> None:
        self.assert_no_forbidden_import("alpaca_paper_order_adapter")

    def test_no_automated_paper_send_import(self) -> None:
        self.assert_no_forbidden_import("automated_paper_send")
        self.assert_no_forbidden_import("one_real_automated_paper_send")

    def test_no_order_endpoint_usage(self) -> None:
        module_text = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("/v2/orders", module_text)

    def test_no_env_file_creation(self) -> None:
        module_text = MODULE_PATH.read_text(encoding="utf-8")
        self.assertNotIn(".env", module_text)

    def test_no_secrets_printed(self) -> None:
        with run_context() as ctx:
            result = soak.run_real_market_paper_soak(
                ctx.config(),
                phase57_runner=FakePhase57Runner(),
            )
            self.assertFalse(result.secrets_printed)
            report = result.artifacts.report_path.read_text(encoding="utf-8")
            self.assertIn("secrets_printed: false", report)

    def assert_no_phase58_for_decision(self, decision: str) -> None:
        with run_context() as ctx:
            p58 = FakePhase58Runner()
            result = soak.run_real_market_paper_soak(
                ctx.config(allow_paper_send=True),
                phase57_runner=FakePhase57Runner([FakePhase57Result(strategy_decision=decision)]),
                phase58_runner=p58,
                phase59_runner=FakePhase59Runner(),
            )

            self.assertEqual(p58.calls, 0)
            self.assertEqual(result.counters.paper_orders_sent, 0)

    def assert_blocked_config(self, overrides: dict[str, object], reason: str) -> None:
        with run_context() as ctx:
            result = soak.run_real_market_paper_soak(
                ctx.config(**overrides),
                phase57_runner=FakePhase57Runner(),
                phase58_runner=FakePhase58Runner(),
                phase59_runner=FakePhase59Runner(),
            )

            self.assertEqual(result.final_status, "BLOCKED")
            self.assertEqual(result.counters.stopped_reason, reason)
            self.assertEqual(result.counters.cycles_started, 0)

    def assert_no_forbidden_import(self, name: str) -> None:
        module_text = MODULE_PATH.read_text(encoding="utf-8")
        import_lines = [
            line
            for line in module_text.splitlines()
            if line.startswith("import ") or line.startswith("from ")
        ]
        self.assertFalse(any(name in line for line in import_lines))


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
                    "- Reason: Phase 60 soak supervisor test",
                    "- Required context condition: one symbol only",
                    "- Required liquidity condition: fake runner only",
                    "- Expiration or review date: 2026-06-01",
                    "",
                    "Watchlist inclusion is not a trade proposal.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.report_root = self.root / "reports" / "real_market_paper_soak"
        return self

    def __exit__(self, *args: object) -> None:
        assert self._temp_dir is not None
        self._temp_dir.cleanup()

    def config(self, **overrides: object):
        values = {
            "symbols": ("AAPL",),
            "paper_only": True,
            "max_notional_usd": 100.0,
            "max_cycles": 1,
            "max_paper_orders_total": 1,
            "max_paper_orders_per_symbol": 1,
            "require_human_review": True,
            "require_manual_confirmation": True,
            "require_preflight": True,
            "kill_switch_enabled": False,
            "output_dir": self.report_root,
            "watchlist_path": self.watchlist_path,
        }
        values.update(overrides)
        return soak.RealMarketPaperSoakConfig(**values)


if __name__ == "__main__":
    unittest.main()
