from __future__ import annotations

from datetime import UTC, datetime, timedelta
import tempfile
import unittest
from pathlib import Path

from runtime.market_data import (
    MOCK_MARKET_DATA_FIXTURES,
    MarketDataSnapshot,
    MockMarketDataAdapter,
    RealMarketDataAdapter,
    RealMarketDataConfig,
    RealMarketDataMissingCredentialsError,
    RealMarketDataSafetyError,
    RealMarketDataValidationError,
    load_real_market_data_config,
    validate_market_data,
)


class FakeReadOnlyHttpClient:
    def __init__(self, payload: dict[str, object] | None = None, error: Exception | None = None):
        self.payload = payload or valid_payload()
        self.error = error
        self.urls: list[str] = []
        self.headers: list[dict[str, str]] = []

    def get_json(self, url: str, headers: dict[str, str]) -> dict[str, object]:
        self.urls.append(url)
        self.headers.append(headers)
        if self.error:
            raise self.error
        return self.payload


class RealMarketDataAdapterTests(unittest.TestCase):
    def test_deterministic_mock_market_data_still_validates(self) -> None:
        snapshot = MockMarketDataAdapter("fresh").load_snapshot("market_open")
        validation = validate_market_data(snapshot)

        self.assertTrue(validation.passed)
        self.assertEqual(validation.data_source, "deterministic_mock")
        self.assertIn("fresh", MOCK_MARKET_DATA_FIXTURES)

    def test_real_market_data_adapter_exists(self) -> None:
        self.assertTrue(RealMarketDataAdapter)
        self.assertTrue(MockMarketDataAdapter)

    def test_loads_config_from_environment_without_creating_env_file(self) -> None:
        with adapter_context() as ctx:
            config = load_real_market_data_config(
                environ={
                    "MARKET_DATA_PROVIDER": "alpaca",
                    "MARKET_DATA_SYMBOL": "AAPL",
                    "MARKET_DATA_TIMEFRAME": "1m",
                    "MARKET_DATA_MAX_AGE_SECONDS": "60",
                    "MARKET_DATA_REQUIRE_SPREAD": "true",
                    "MARKET_DATA_REQUIRE_VOLUME": "true",
                    "ALPACA_PAPER": "true",
                    "ALPACA_API_KEY_ID": "key-id",
                    "ALPACA_API_SECRET_KEY": "secret-key",
                },
                watchlist_path=ctx.watchlist_path,
                report_root=ctx.report_root,
            )

            self.assertEqual(config.provider, "alpaca")
            self.assertEqual(config.symbols, ("AAPL",))
            self.assertEqual(config.timeframe, "1m")
            self.assertEqual(config.max_age, timedelta(seconds=60))
            self.assertTrue(config.require_spread)
            self.assertTrue(config.require_volume)

    def test_accepts_exactly_one_approved_symbol(self) -> None:
        with adapter_context() as ctx:
            client = FakeReadOnlyHttpClient()
            adapter = RealMarketDataAdapter(ctx.config(), http_client=client)

            snapshot = adapter.load_snapshot("market_open")

            self.assertEqual(snapshot.symbol, "AAPL")
            self.assertEqual(snapshot.source, "alpaca_market_data_read_only")
            self.assertTrue(snapshot.spread_available)
            self.assertTrue(snapshot.volume_available)
            self.assertFalse(snapshot.broker_execution_readiness)
            self.assertEqual(len(client.urls), 1)
            self.assertNotIn("/v2/orders", client.urls[0])

    def test_rejects_more_than_one_symbol(self) -> None:
        with adapter_context() as ctx:
            adapter = RealMarketDataAdapter(ctx.config(symbols=("AAPL", "MSFT")))

            with self.assertRaises(RealMarketDataSafetyError):
                adapter.load_snapshot("market_open")

    def test_rejects_missing_symbol(self) -> None:
        with adapter_context() as ctx:
            adapter = RealMarketDataAdapter(ctx.config(symbols=()))

            with self.assertRaisesRegex(RealMarketDataValidationError, "missing_configured_symbol"):
                adapter.load_snapshot("market_open")

    def test_rejects_missing_provider(self) -> None:
        with adapter_context() as ctx:
            adapter = RealMarketDataAdapter(ctx.config(provider=""))

            with self.assertRaisesRegex(RealMarketDataValidationError, "missing_provider"):
                adapter.load_snapshot("market_open")

    def test_rejects_unsupported_provider(self) -> None:
        with adapter_context() as ctx:
            adapter = RealMarketDataAdapter(ctx.config(provider="unsupported"))

            with self.assertRaisesRegex(RealMarketDataSafetyError, "unsupported_provider"):
                adapter.load_snapshot("market_open")

    def test_rejects_missing_watchlist_approval(self) -> None:
        with adapter_context(watchlist_symbol="MSFT") as ctx:
            adapter = RealMarketDataAdapter(ctx.config())

            with self.assertRaisesRegex(
                RealMarketDataValidationError,
                "missing_watchlist_approval",
            ):
                adapter.load_snapshot("market_open")

    def test_rejects_stale_data(self) -> None:
        with adapter_context() as ctx:
            payload = valid_payload(timestamp="2026-05-20T13:00:00+00:00")
            adapter = RealMarketDataAdapter(ctx.config(), http_client=FakeReadOnlyHttpClient(payload))

            with self.assertRaisesRegex(RealMarketDataValidationError, "stale_data"):
                adapter.load_snapshot("market_open")

    def test_rejects_missing_timestamp(self) -> None:
        with adapter_context() as ctx:
            payload = valid_payload(timestamp=None)
            adapter = RealMarketDataAdapter(ctx.config(), http_client=FakeReadOnlyHttpClient(payload))

            with self.assertRaisesRegex(RealMarketDataValidationError, "missing_timestamp"):
                adapter.load_snapshot("market_open")

    def test_rejects_missing_timeframe(self) -> None:
        with adapter_context() as ctx:
            adapter = RealMarketDataAdapter(ctx.config(timeframe=""))

            with self.assertRaisesRegex(RealMarketDataValidationError, "missing_timeframe"):
                adapter.load_snapshot("market_open")

    def test_rejects_missing_session(self) -> None:
        with adapter_context() as ctx:
            adapter = RealMarketDataAdapter(ctx.config(session=""))

            with self.assertRaisesRegex(RealMarketDataValidationError, "missing_session"):
                adapter.load_snapshot("market_open")

    def test_rejects_missing_source(self) -> None:
        with adapter_context() as ctx:
            adapter = RealMarketDataAdapter(
                ctx.config(source=""),
                http_client=FakeReadOnlyHttpClient(),
            )

            with self.assertRaisesRegex(RealMarketDataValidationError, "missing_source"):
                adapter.load_snapshot("market_open")

    def test_rejects_missing_spread_when_required(self) -> None:
        with adapter_context() as ctx:
            payload = valid_payload(include_quote=False)
            adapter = RealMarketDataAdapter(ctx.config(), http_client=FakeReadOnlyHttpClient(payload))

            with self.assertRaisesRegex(RealMarketDataValidationError, "missing_required_spread"):
                adapter.load_snapshot("market_open")

    def test_rejects_missing_volume_when_required(self) -> None:
        with adapter_context() as ctx:
            payload = valid_payload(include_bar=False)
            adapter = RealMarketDataAdapter(ctx.config(), http_client=FakeReadOnlyHttpClient(payload))

            with self.assertRaisesRegex(RealMarketDataValidationError, "missing_required_volume"):
                adapter.load_snapshot("market_open")

    def test_rejects_live_endpoint(self) -> None:
        with adapter_context() as ctx:
            adapter = RealMarketDataAdapter(ctx.config(base_url="https://api.alpaca.markets"))

            with self.assertRaisesRegex(RealMarketDataSafetyError, "live_or_trading_endpoint"):
                adapter.load_snapshot("market_open")

    def test_rejects_alpaca_order_endpoint(self) -> None:
        with adapter_context() as ctx:
            adapter = RealMarketDataAdapter(
                ctx.config(base_url="https://data.alpaca.markets/v2/orders")
            )

            with self.assertRaisesRegex(RealMarketDataSafetyError, "alpaca_order_endpoint"):
                adapter.load_snapshot("market_open")

    def test_rejects_execution_enabled_for_data_only_run(self) -> None:
        self.assert_execution_flag_blocks("PAPER_ORDER_EXECUTION_ENABLED")

    def test_rejects_automated_send_enabled_for_data_only_run(self) -> None:
        self.assert_execution_flag_blocks("PAPER_AUTOMATED_SEND_ENABLED")

    def test_rejects_accelerated_soak_enabled_for_data_only_run(self) -> None:
        self.assert_execution_flag_blocks("PAPER_SOAK_TEST_ACCELERATED")

    def test_rejects_missing_api_keys_for_real_provider(self) -> None:
        with adapter_context() as ctx:
            adapter = RealMarketDataAdapter(ctx.config(api_key_id=None, api_secret_key=None))

            with self.assertRaises(RealMarketDataMissingCredentialsError):
                adapter.load_snapshot("market_open")

    def test_redacts_secrets_from_report_and_exceptions(self) -> None:
        secret = "secret-value-that-must-not-appear"
        with adapter_context(api_secret_key=secret) as ctx:
            adapter = RealMarketDataAdapter(
                ctx.config(api_secret_key=secret),
                http_client=FakeReadOnlyHttpClient(
                    error=RealMarketDataValidationError(f"provider leaked {secret}")
                ),
            )

            with self.assertRaises(RealMarketDataValidationError) as raised:
                adapter.load_snapshot("market_open")

            self.assertNotIn(secret, str(raised.exception))
            self.assertNotIn(secret, repr(adapter.config))
            report = latest_report_text(ctx.report_root)
            self.assertNotIn(secret, report)
            self.assertIn("[REDACTED]", report)

    def test_report_contains_required_statements(self) -> None:
        with adapter_context() as ctx:
            adapter = RealMarketDataAdapter(ctx.config(), http_client=FakeReadOnlyHttpClient())

            adapter.load_snapshot("market_open")

            report = latest_report_text(ctx.report_root)
            self.assertIn("provider: alpaca", report)
            self.assertIn("spread availability: true", report)
            self.assertIn("volume availability: true", report)
            self.assertIn("REAL_MARKET_DATA_LOADED", report)
            self.assertIn("No order was sent.", report)
            self.assertIn("Live trading remains unsupported.", report)
            self.assertIn("This adapter is read-only.", report)
            self.assertIn("Mock fixtures remain available for tests.", report)
            self.assertIn("broker execution readiness not created: true", report)

    def test_no_order_api_method_exists_or_is_called(self) -> None:
        with adapter_context() as ctx:
            client = FakeReadOnlyHttpClient()
            adapter = RealMarketDataAdapter(ctx.config(), http_client=client)

            adapter.load_snapshot("market_open")

            self.assertFalse(hasattr(client, "post"))
            self.assertFalse(hasattr(client, "patch"))
            self.assertFalse(hasattr(client, "put"))
            self.assertFalse(hasattr(client, "delete"))
            self.assertEqual(len(client.urls), 1)
            self.assertNotIn("orders", client.urls[0].lower())

    def test_no_broker_execution_readiness_is_created(self) -> None:
        with adapter_context() as ctx:
            snapshot = RealMarketDataAdapter(
                ctx.config(),
                http_client=FakeReadOnlyHttpClient(),
            ).load_snapshot("market_open")

            validation = validate_market_data(snapshot)
            self.assertIsInstance(snapshot, MarketDataSnapshot)
            self.assertFalse(snapshot.broker_execution_readiness)
            self.assertNotIn("broker_execution_readiness_not_allowed", validation.violations)

    def assert_execution_flag_blocks(self, flag_name: str) -> None:
        with adapter_context() as ctx:
            adapter = RealMarketDataAdapter(
                ctx.config(environ={flag_name: "true"}),
                http_client=FakeReadOnlyHttpClient(),
            )

            with self.assertRaisesRegex(RealMarketDataSafetyError, flag_name):
                adapter.load_snapshot("market_open")


class adapter_context:
    def __init__(
        self,
        *,
        watchlist_symbol: str = "AAPL",
        api_key_id: str = "key-id",
        api_secret_key: str = "secret-key",
    ) -> None:
        self.watchlist_symbol = watchlist_symbol
        self.api_key_id = api_key_id
        self.api_secret_key = api_secret_key
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None
        self.root: Path
        self.watchlist_path: Path
        self.report_root: Path

    def __enter__(self) -> adapter_context:
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
                    "- Reason: adapter unit test",
                    "- Required context condition: paper-only data validation",
                    "- Required liquidity condition: spread and volume available",
                    "- Expiration or review date: 2026-06-01",
                    "",
                    "Watchlist inclusion is not a trade proposal.",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.report_root = self.root / "reports" / "real_market_data_adapter"
        return self

    def __exit__(self, *args: object) -> None:
        assert self._temp_dir is not None
        self._temp_dir.cleanup()

    def config(self, **overrides: object) -> RealMarketDataConfig:
        values = {
            "symbols": ("AAPL",),
            "base_url": "https://data.alpaca.markets",
            "timeframe": "1m",
            "session": "market_open",
            "provider": "alpaca",
            "watchlist_path": self.watchlist_path,
            "report_root": self.report_root,
            "api_key_id": self.api_key_id,
            "api_secret_key": self.api_secret_key,
            "as_of": datetime(2026, 5, 20, 13, 31, tzinfo=UTC),
            "max_age": timedelta(minutes=15),
        }
        values.update(overrides)
        return RealMarketDataConfig(**values)


def valid_payload(
    *,
    timestamp: str | None = "2026-05-20T13:30:00+00:00",
    include_quote: bool = True,
    include_bar: bool = True,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "latestTrade": {"t": timestamp, "p": 189.12},
    }
    if include_quote:
        payload["latestQuote"] = {"t": timestamp, "bp": 189.1, "ap": 189.13}
    if include_bar:
        payload["minuteBar"] = {"t": timestamp, "c": 189.12, "v": 12345}
    return payload


def latest_report_text(report_root: Path) -> str:
    reports = sorted(report_root.glob("*/REAL_MARKET_DATA_ADAPTER_REPORT.md"))
    if not reports:
        raise AssertionError("expected real market data adapter report")
    return reports[-1].read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
