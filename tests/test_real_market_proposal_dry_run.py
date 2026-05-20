from __future__ import annotations

from datetime import UTC, datetime, timedelta
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "runtime"
MODULE_PATH = RUNTIME_PATH / "real_market_proposal_dry_run.py"

if str(RUNTIME_PATH) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PATH))

spec = importlib.util.spec_from_file_location("real_market_proposal_dry_run", MODULE_PATH)
proposal_dry_run = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["real_market_proposal_dry_run"] = proposal_dry_run
spec.loader.exec_module(proposal_dry_run)

from market_data import MarketDataSnapshot


class FakeMarketDataAdapter:
    def __init__(self, snapshot: MarketDataSnapshot):
        self.snapshot = snapshot
        self.calls = 0

    def load_snapshot(self, routine_name: str) -> MarketDataSnapshot:
        self.calls += 1
        return self.snapshot


class RealMarketProposalDryRunTests(unittest.TestCase):
    def test_pass_path_returns_no_trade_dry_run_only(self) -> None:
        with dry_run_context() as ctx:
            adapter = FakeMarketDataAdapter(valid_snapshot())

            result = proposal_dry_run.run_real_market_proposal_dry_run(
                ctx.config(),
                market_data_adapter=adapter,
                environ={},
            )

            self.assertEqual(result.final_status, "NO_TRADE")
            self.assertEqual(result.strategy_decision, "NO_TRADE")
            self.assertIsNone(result.proposal)
            self.assertFalse(result.paper_order_request_created)
            self.assertFalse(result.human_review_requested)
            self.assertFalse(result.finalized_request_created)
            self.assertFalse(result.manual_confirmation_requested)
            self.assertFalse(result.paper_send_preflight_run)
            self.assertFalse(result.paper_order_sent)
            self.assertFalse(result.broker_execution_readiness)
            self.assertEqual(adapter.calls, 1)

    def test_valid_path_can_return_non_executable_trade_proposal(self) -> None:
        with dry_run_context() as ctx:
            result = proposal_dry_run.run_real_market_proposal_dry_run(
                ctx.config(allow_trade_proposal=True),
                market_data_adapter=FakeMarketDataAdapter(valid_snapshot()),
                environ={},
            )

            self.assertEqual(result.final_status, "TRADE_PROPOSAL")
            self.assertIsNotNone(result.proposal)
            assert result.proposal is not None
            self.assertFalse(result.proposal.executable)
            self.assertFalse(result.proposal.broker_execution_readiness)
            self.assertFalse(result.proposal.paper_order_request_created)
            self.assertFalse(result.proposal.human_review_requested)
            self.assertFalse(result.proposal.finalized_request_created)
            self.assertFalse(result.proposal.manual_confirmation_requested)
            self.assertFalse(result.proposal.paper_send_preflight_run)
            self.assertFalse(result.proposal.paper_order_sent)
            self.assertFalse(result.proposal.live_trading_assumption)

    def test_invalid_data_returns_reject_and_creates_no_proposal(self) -> None:
        result = self.run_with_snapshot(valid_snapshot(source=None))

        self.assertEqual(result.final_status, "REJECT")
        self.assertIsNone(result.proposal)
        self.assertFalse(result.paper_order_request_created)

    def test_stale_data_blocks(self) -> None:
        result = self.run_with_snapshot(
            valid_snapshot(timestamp=datetime(2026, 5, 20, 13, 0, tzinfo=UTC))
        )

        self.assertEqual(result.final_status, "REJECT")
        self.assertIn("stale_data", result.violations)

    def test_missing_timestamp_blocks(self) -> None:
        result = self.run_with_snapshot(valid_snapshot(timestamp=None))

        self.assertEqual(result.final_status, "REJECT")
        self.assertIn("missing_timestamp", result.violations)

    def test_missing_symbol_blocks(self) -> None:
        result = self.run_with_snapshot(valid_snapshot(symbol=None))

        self.assertEqual(result.final_status, "REJECT")
        self.assertIn("missing_symbol", result.violations)

    def test_missing_timeframe_blocks(self) -> None:
        result = self.run_with_snapshot(valid_snapshot(timeframe=None))

        self.assertEqual(result.final_status, "REJECT")
        self.assertIn("missing_timeframe", result.violations)

    def test_missing_session_blocks(self) -> None:
        result = self.run_with_snapshot(valid_snapshot(session=None))

        self.assertEqual(result.final_status, "REJECT")
        self.assertIn("missing_session", result.violations)

    def test_missing_spread_when_required_blocks(self) -> None:
        result = self.run_with_snapshot(valid_snapshot(spread_available=False))

        self.assertEqual(result.final_status, "REJECT")
        self.assertIn("missing_required_spread", result.violations)

    def test_missing_volume_when_required_blocks(self) -> None:
        result = self.run_with_snapshot(valid_snapshot(volume_available=False))

        self.assertEqual(result.final_status, "REJECT")
        self.assertIn("missing_required_volume", result.violations)

    def test_missing_watchlist_approval_blocks(self) -> None:
        with dry_run_context(watchlist_symbol="MSFT") as ctx:
            result = proposal_dry_run.run_real_market_proposal_dry_run(
                ctx.config(),
                market_data_adapter=FakeMarketDataAdapter(valid_snapshot()),
                environ={},
            )

            self.assertEqual(result.final_status, "REJECT")
            self.assertIn("missing_watchlist_approval", result.violations)

    def test_more_than_one_symbol_blocks(self) -> None:
        with dry_run_context() as ctx:
            result = proposal_dry_run.run_real_market_proposal_dry_run(
                ctx.config(symbols=("AAPL", "MSFT")),
                market_data_adapter=FakeMarketDataAdapter(valid_snapshot()),
                environ={},
            )

            self.assertEqual(result.final_status, "REJECT")
            self.assertIn("more_than_one_symbol_blocked", result.violations)

    def test_zero_symbols_blocks(self) -> None:
        with dry_run_context() as ctx:
            result = proposal_dry_run.run_real_market_proposal_dry_run(
                ctx.config(symbols=()),
                market_data_adapter=FakeMarketDataAdapter(valid_snapshot()),
                environ={},
            )

            self.assertEqual(result.final_status, "REJECT")
            self.assertIn("missing_symbol", result.violations)

    def test_execution_enabled_flag_blocks(self) -> None:
        result = self.run_with_env({"PAPER_ORDER_EXECUTION_ENABLED": "true"})

        self.assertEqual(result.final_status, "REJECT")
        self.assertIn("PAPER_ORDER_EXECUTION_ENABLED", result.strategy_reason)

    def test_automated_send_enabled_flag_blocks(self) -> None:
        result = self.run_with_env({"PAPER_AUTOMATED_SEND_ENABLED": "true"})

        self.assertEqual(result.final_status, "REJECT")
        self.assertIn("PAPER_AUTOMATED_SEND_ENABLED", result.strategy_reason)

    def test_accelerated_soak_flag_blocks(self) -> None:
        result = self.run_with_env({"PAPER_SOAK_TEST_ACCELERATED": "true"})

        self.assertEqual(result.final_status, "REJECT")
        self.assertIn("PAPER_SOAK_TEST_ACCELERATED", result.strategy_reason)

    def test_no_downstream_order_artifacts_are_created(self) -> None:
        with dry_run_context() as ctx:
            result = proposal_dry_run.run_real_market_proposal_dry_run(
                ctx.config(allow_trade_proposal=True),
                market_data_adapter=FakeMarketDataAdapter(valid_snapshot()),
                environ={},
            )

            self.assertFalse(result.paper_order_request_created)
            self.assertFalse(result.human_review_requested)
            self.assertFalse(result.finalized_request_created)
            self.assertFalse(result.manual_confirmation_requested)
            self.assertFalse(result.paper_send_preflight_run)
            self.assertFalse(result.paper_order_sent)
            self.assertFalse(result.order_api_used)
            reports = list(ctx.report_root.glob("*/REAL_MARKET_PROPOSAL_DRY_RUN_REPORT.md"))
            self.assertEqual(len(reports), 1)
            self.assertFalse((ctx.root / "paper_order_request_candidate").exists())
            self.assertFalse((ctx.root / "human_review_queue").exists())

    def test_order_api_endpoint_and_forbidden_modules_are_not_used(self) -> None:
        module_text = MODULE_PATH.read_text(encoding="utf-8")
        import_lines = [
            line
            for line in module_text.splitlines()
            if line.startswith("import ") or line.startswith("from ")
        ]

        self.assertFalse(any("alpaca_paper_order_adapter" in line for line in import_lines))
        self.assertFalse(any("automated_paper_send" in line for line in import_lines))
        self.assertFalse(any("paper_order_request_candidate" in line for line in import_lines))
        self.assertFalse(any("paper_send_preflight" in line for line in import_lines))
        self.assertNotIn("/v2/orders", module_text)
        self.assertNotIn("submit_order", module_text)

    def test_no_secrets_are_printed_or_written_to_report(self) -> None:
        secret = "phase57-secret-value"
        with dry_run_context() as ctx:
            result = proposal_dry_run.run_real_market_proposal_dry_run(
                ctx.config(),
                market_data_adapter=ExplodingAdapter(f"provider leaked {secret}"),
                environ={},
            )

            report = result.report_path.read_text(encoding="utf-8")
            self.assertEqual(result.final_status, "REJECT")
            self.assertNotIn(secret, report)

    def test_report_contains_required_statements(self) -> None:
        with dry_run_context() as ctx:
            result = proposal_dry_run.run_real_market_proposal_dry_run(
                ctx.config(),
                market_data_adapter=FakeMarketDataAdapter(valid_snapshot()),
                environ={},
            )

            report = result.report_path.read_text(encoding="utf-8")
            self.assertIn("No order was sent.", report)
            self.assertIn("No paper order candidate was created.", report)
            self.assertIn("No human review item was created.", report)
            self.assertIn("Live trading remains unsupported.", report)
            self.assertIn("This run is read-only and dry-run only.", report)

    def run_with_snapshot(self, snapshot: MarketDataSnapshot):
        with dry_run_context() as ctx:
            return proposal_dry_run.run_real_market_proposal_dry_run(
                ctx.config(),
                market_data_adapter=FakeMarketDataAdapter(snapshot),
                environ={},
            )

    def run_with_env(self, environ: dict[str, str]):
        with dry_run_context() as ctx:
            return proposal_dry_run.run_real_market_proposal_dry_run(
                ctx.config(),
                market_data_adapter=FakeMarketDataAdapter(valid_snapshot()),
                environ=environ,
            )


class ExplodingAdapter:
    def __init__(self, message: str):
        self.message = message

    def load_snapshot(self, routine_name: str) -> MarketDataSnapshot:
        raise RuntimeError(self.message)


class dry_run_context:
    def __init__(self, *, watchlist_symbol: str = "AAPL") -> None:
        self.watchlist_symbol = watchlist_symbol
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None
        self.root: Path
        self.watchlist_path: Path
        self.report_root: Path

    def __enter__(self) -> dry_run_context:
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
                    "- Reason: Phase 57 dry-run test",
                    "- Required context condition: read-only data validation",
                    "- Required liquidity condition: spread and volume available",
                    "- Expiration or review date: 2026-06-01",
                    "",
                    "Watchlist inclusion is not a trade proposal.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.report_root = self.root / "reports" / "real_market_proposal_dry_run"
        return self

    def __exit__(self, *args: object) -> None:
        assert self._temp_dir is not None
        self._temp_dir.cleanup()

    def config(self, **overrides: object):
        values = {
            "symbols": ("AAPL",),
            "timeframe": "1m",
            "session": "market_open",
            "watchlist_path": self.watchlist_path,
            "report_root": self.report_root,
            "as_of": datetime(2026, 5, 20, 13, 31, tzinfo=UTC),
            "max_age": timedelta(minutes=15),
            "api_key_id": None,
            "api_secret_key": None,
        }
        values.update(overrides)
        return proposal_dry_run.RealMarketProposalDryRunConfig(**values)


def valid_snapshot(**overrides: object) -> MarketDataSnapshot:
    values = {
        "source": "fake_read_only_market_data",
        "timestamp": datetime(2026, 5, 20, 13, 30, tzinfo=UTC),
        "symbol": "AAPL",
        "timeframe": "1m",
        "session": "market_open",
        "spread_available": True,
        "volume_available": True,
        "last_price": 189.12,
        "bid_available": True,
        "ask_available": True,
        "bar_available": True,
        "broker_execution_readiness": False,
    }
    values.update(overrides)
    return MarketDataSnapshot(**values)


if __name__ == "__main__":
    unittest.main()
