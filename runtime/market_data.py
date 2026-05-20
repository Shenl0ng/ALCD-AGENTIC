from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
import os
from pathlib import Path
from typing import Any, Protocol
from urllib import request
from urllib.parse import quote, urljoin, urlparse


SIMULATION_AS_OF = datetime(2026, 5, 19, 13, 30, tzinfo=UTC)
MAX_FRESHNESS_AGE = timedelta(minutes=15)
DEFAULT_WATCHLIST_PATH = Path("memory/watchlist.md")
DEFAULT_REAL_MARKET_DATA_REPORT_ROOT = Path("reports/real_market_data_adapter")


@dataclass(frozen=True)
class MarketDataSnapshot:
    source: str | None
    timestamp: datetime | None
    symbol: str | None
    timeframe: str | None
    session: str | None
    spread_available: bool
    volume_available: bool
    last_price: float | None = None
    bid_available: bool = False
    ask_available: bool = False
    bar_available: bool = False
    broker_execution_readiness: bool = False


@dataclass(frozen=True)
class MarketDataValidation:
    data_source: str
    data_timestamp: str
    timeframe: str
    session: str
    freshness_status: str
    completeness_status: str
    data_integrity_status: str
    violations: tuple[str, ...]
    spread_available: bool
    volume_available: bool
    last_price: float | None = None
    bid_available: bool = False
    ask_available: bool = False
    bar_available: bool = False
    broker_execution_readiness: bool = False

    @property
    def passed(self) -> bool:
        return self.data_integrity_status == "PASS"

    def as_dict(self) -> dict[str, object]:
        return {
            "data_source": self.data_source,
            "data_timestamp": self.data_timestamp,
            "timeframe": self.timeframe,
            "session": self.session,
            "freshness_status": self.freshness_status,
            "completeness_status": self.completeness_status,
            "data_integrity_status": self.data_integrity_status,
            "violations": list(self.violations),
            "spread_available": self.spread_available,
            "volume_available": self.volume_available,
            "last_price": self.last_price,
            "bid_available": self.bid_available,
            "ask_available": self.ask_available,
            "bar_available": self.bar_available,
            "broker_execution_readiness": self.broker_execution_readiness,
        }


class MarketDataAdapter(Protocol):
    def load_snapshot(self, routine_name: str) -> MarketDataSnapshot:
        """Return deterministic market data for Data Integrity validation only."""


class ReadOnlyMarketDataHttpClient(Protocol):
    def get_json(self, url: str, headers: dict[str, str]) -> dict[str, Any]:
        """Perform a read-only GET request and return decoded JSON."""


class RealMarketDataSafetyError(RuntimeError):
    """Raised when real market data configuration violates read-only safety rules."""


class RealMarketDataMissingCredentialsError(RealMarketDataSafetyError):
    """Raised when real provider credentials are required but unavailable."""


class RealMarketDataValidationError(RealMarketDataSafetyError):
    """Raised when real market data cannot pass adapter-level validation."""


@dataclass(frozen=True)
class RealMarketDataConfig:
    symbols: tuple[str, ...]
    base_url: str
    timeframe: str
    session: str
    watchlist_path: Path = DEFAULT_WATCHLIST_PATH
    report_root: Path = DEFAULT_REAL_MARKET_DATA_REPORT_ROOT
    source: str = "alpaca_market_data_read_only"
    api_key_id: str | None = field(default=None, repr=False)
    api_secret_key: str | None = field(default=None, repr=False)
    require_spread: bool = True
    require_volume: bool = True
    max_age: timedelta = MAX_FRESHNESS_AGE
    as_of: datetime | None = None


class UrlLibReadOnlyMarketDataHttpClient:
    def get_json(self, url: str, headers: dict[str, str]) -> dict[str, Any]:
        req = request.Request(url, headers=headers, method="GET")
        with request.urlopen(req, timeout=15) as response:
            payload = response.read().decode("utf-8")
        import json

        data = json.loads(payload)
        if not isinstance(data, dict):
            raise RealMarketDataValidationError("market data response was not a JSON object")
        return data


class RealMarketDataAdapter:
    def __init__(
        self,
        config: RealMarketDataConfig,
        *,
        http_client: ReadOnlyMarketDataHttpClient | None = None,
    ) -> None:
        self.config = config
        self.http_client = http_client or UrlLibReadOnlyMarketDataHttpClient()

    def load_snapshot(self, routine_name: str) -> MarketDataSnapshot:
        final_status = "BLOCKED"
        snapshot: MarketDataSnapshot | None = None
        validation: MarketDataValidation | None = None
        try:
            symbol = self._validate_config()
            self._require_watchlist_approval(symbol)
            headers = self._headers()
            url = self._market_data_url(symbol)
            payload = self.http_client.get_json(url, headers)
            snapshot = self._snapshot_from_payload(payload, symbol, routine_name)
            validation = validate_market_data(
                snapshot,
                as_of=self.config.as_of or datetime.now(UTC),
                max_age=self.config.max_age,
                require_spread=self.config.require_spread,
                require_volume=self.config.require_volume,
            )
            if not validation.passed:
                raise RealMarketDataValidationError(
                    "market data validation failed: "
                    + ",".join(validation.violations)
                )
            final_status = "PASS"
            return snapshot
        except RealMarketDataSafetyError as exc:
            redacted_error = self._redact_text(str(exc))
            self._write_report(snapshot, validation, final_status, redacted_error)
            if redacted_error != str(exc):
                raise type(exc)(redacted_error) from exc
            raise
        except Exception as exc:
            self._write_report(snapshot, validation, final_status, "market data load failed")
            raise RealMarketDataValidationError("market data load failed") from exc
        finally:
            if final_status == "PASS":
                self._write_report(snapshot, validation, final_status, None)

    def _validate_config(self) -> str:
        symbols = tuple(symbol.strip().upper() for symbol in self.config.symbols if symbol.strip())
        if not symbols:
            raise RealMarketDataValidationError("missing_symbol")
        if len(symbols) != 1:
            raise RealMarketDataSafetyError("more_than_one_symbol_blocked")
        if not self.config.timeframe:
            raise RealMarketDataValidationError("missing_timeframe")
        if not self.config.session:
            raise RealMarketDataValidationError("missing_session")
        self._validate_base_url(self.config.base_url)
        if not self._credential("ALPACA_API_KEY_ID", self.config.api_key_id):
            raise RealMarketDataMissingCredentialsError("missing_api_key_id")
        if not self._credential("ALPACA_API_SECRET_KEY", self.config.api_secret_key):
            raise RealMarketDataMissingCredentialsError("missing_api_secret_key")
        return symbols[0]

    def _validate_base_url(self, base_url: str) -> None:
        parsed = urlparse(base_url)
        lowered = base_url.lower()
        host = parsed.netloc.lower()
        path = parsed.path.lower()
        if parsed.scheme != "https":
            raise RealMarketDataSafetyError("market_data_endpoint_must_use_https")
        if "paper-api.alpaca.markets" in host or host == "api.alpaca.markets":
            raise RealMarketDataSafetyError("live_or_trading_endpoint_rejected")
        if "orders" in path or "/v2/orders" in lowered:
            raise RealMarketDataSafetyError("alpaca_order_endpoint_rejected")
        if "account" in path or "positions" in path:
            raise RealMarketDataSafetyError("broker_execution_readiness_path_rejected")
        if "data.alpaca.markets" not in host:
            raise RealMarketDataSafetyError("unsupported_market_data_endpoint")

    def _headers(self) -> dict[str, str]:
        return {
            "APCA-API-KEY-ID": self._credential("ALPACA_API_KEY_ID", self.config.api_key_id),
            "APCA-API-SECRET-KEY": self._credential(
                "ALPACA_API_SECRET_KEY",
                self.config.api_secret_key,
            ),
        }

    def _credential(self, env_name: str, configured_value: str | None) -> str:
        return configured_value or os.environ.get(env_name, "")

    def _market_data_url(self, symbol: str) -> str:
        base = self.config.base_url.rstrip("/") + "/"
        path = f"v2/stocks/{quote(symbol)}/snapshot"
        url = urljoin(base, path)
        lowered = url.lower()
        if "/v2/orders" in lowered or "orders" in urlparse(url).path.lower():
            raise RealMarketDataSafetyError("alpaca_order_endpoint_rejected")
        return url

    def _require_watchlist_approval(self, symbol: str) -> None:
        try:
            text = self.config.watchlist_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise RealMarketDataValidationError("watchlist_missing") from exc
        if not _watchlist_symbol_is_approved(text, symbol):
            raise RealMarketDataValidationError("missing_watchlist_approval")

    def _snapshot_from_payload(
        self,
        payload: dict[str, Any],
        symbol: str,
        routine_name: str,
    ) -> MarketDataSnapshot:
        quote_data = _dict_value(payload, "latestQuote", "quote")
        trade_data = _dict_value(payload, "latestTrade", "trade")
        bar_data = _dict_value(payload, "minuteBar", "dailyBar", "bar")
        timestamp = _parse_timestamp(
            _first_present(payload, "timestamp", "t")
            or _first_present(quote_data, "t", "timestamp")
            or _first_present(trade_data, "t", "timestamp")
            or _first_present(bar_data, "t", "timestamp")
        )
        bid = _first_present(quote_data, "bp", "bid_price", "bid")
        ask = _first_present(quote_data, "ap", "ask_price", "ask")
        volume = _first_present(bar_data, "v", "volume")
        last_price = _first_present(trade_data, "p", "price") or _first_present(
            bar_data,
            "c",
            "close",
        )
        return MarketDataSnapshot(
            source=self.config.source,
            timestamp=timestamp,
            symbol=symbol,
            timeframe=self.config.timeframe,
            session=self.config.session or routine_name,
            spread_available=bid is not None and ask is not None,
            volume_available=volume is not None,
            last_price=float(last_price) if last_price is not None else None,
            bid_available=bid is not None,
            ask_available=ask is not None,
            bar_available=bool(bar_data),
            broker_execution_readiness=False,
        )

    def _write_report(
        self,
        snapshot: MarketDataSnapshot | None,
        validation: MarketDataValidation | None,
        final_status: str,
        error: str | None,
    ) -> None:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        report_dir = self.config.report_root / timestamp
        report_dir.mkdir(parents=True, exist_ok=True)
        symbol = snapshot.symbol if snapshot else ",".join(self.config.symbols) or "MISSING"
        source = snapshot.source if snapshot else self.config.source
        data_timestamp = (
            snapshot.timestamp.isoformat()
            if snapshot and snapshot.timestamp
            else "MISSING"
        )
        timeframe = snapshot.timeframe if snapshot else self.config.timeframe or "MISSING"
        session = snapshot.session if snapshot else self.config.session or "MISSING"
        freshness = validation.freshness_status if validation else "UNKNOWN"
        completeness = validation.completeness_status if validation else "UNKNOWN"
        integrity = validation.data_integrity_status if validation else "UNKNOWN"
        lines = [
            "# Real Market Data Adapter Report",
            "",
            f"- symbol: {symbol}",
            f"- source: {source}",
            f"- timestamp: {data_timestamp}",
            f"- timeframe: {timeframe}",
            f"- session: {session}",
            f"- freshness status: {freshness}",
            f"- completeness status: {completeness}",
            f"- data integrity status: {integrity}",
            "- live endpoint rejected: true",
            "- order API not used: true",
            "- secrets not printed: true",
            "- broker execution readiness: false",
            f"- final status: {final_status}",
            "- No order was sent.",
            "- Live trading remains unsupported.",
            "- This adapter is read-only.",
        ]
        if error:
            lines.append(f"- error: {self._redact_text(error)}")
        (report_dir / "REAL_MARKET_DATA_ADAPTER_REPORT.md").write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )

    def _redact_text(self, text: str) -> str:
        return _redact(text, self.config.api_key_id, self.config.api_secret_key)


class MockMarketDataAdapter:
    def __init__(self, fixture_name: str = "fresh") -> None:
        if fixture_name not in MOCK_MARKET_DATA_FIXTURES:
            raise ValueError(f"Unknown market data fixture: {fixture_name}")
        self.fixture_name = fixture_name

    def load_snapshot(self, routine_name: str) -> MarketDataSnapshot:
        fixture = MOCK_MARKET_DATA_FIXTURES[self.fixture_name]
        return MarketDataSnapshot(
            source=fixture.source,
            timestamp=fixture.timestamp,
            symbol=fixture.symbol,
            timeframe=fixture.timeframe,
            session=routine_name,
            spread_available=fixture.spread_available,
            volume_available=fixture.volume_available,
        )


MOCK_MARKET_DATA_FIXTURES: dict[str, MarketDataSnapshot] = {
    "fresh": MarketDataSnapshot(
        source="deterministic_mock",
        timestamp=datetime(2026, 5, 19, 13, 29, tzinfo=UTC),
        symbol="SIM",
        timeframe="1m",
        session=None,
        spread_available=True,
        volume_available=True,
    ),
    "stale": MarketDataSnapshot(
        source="deterministic_mock",
        timestamp=datetime(2026, 5, 19, 12, 30, tzinfo=UTC),
        symbol="SIM",
        timeframe="1m",
        session=None,
        spread_available=True,
        volume_available=True,
    ),
    "missing_timestamp": MarketDataSnapshot(
        source="deterministic_mock",
        timestamp=None,
        symbol="SIM",
        timeframe="1m",
        session=None,
        spread_available=True,
        volume_available=True,
    ),
    "missing_symbol": MarketDataSnapshot(
        source="deterministic_mock",
        timestamp=datetime(2026, 5, 19, 13, 29, tzinfo=UTC),
        symbol=None,
        timeframe="1m",
        session=None,
        spread_available=True,
        volume_available=True,
    ),
    "missing_timeframe": MarketDataSnapshot(
        source="deterministic_mock",
        timestamp=datetime(2026, 5, 19, 13, 29, tzinfo=UTC),
        symbol="SIM",
        timeframe=None,
        session=None,
        spread_available=True,
        volume_available=True,
    ),
    "missing_source": MarketDataSnapshot(
        source=None,
        timestamp=datetime(2026, 5, 19, 13, 29, tzinfo=UTC),
        symbol="SIM",
        timeframe="1m",
        session=None,
        spread_available=True,
        volume_available=True,
    ),
}


def validate_market_data(
    snapshot: MarketDataSnapshot,
    *,
    as_of: datetime = SIMULATION_AS_OF,
    max_age: timedelta = MAX_FRESHNESS_AGE,
    require_spread: bool = False,
    require_volume: bool = False,
) -> MarketDataValidation:
    violations: list[str] = []

    if not snapshot.source:
        violations.append("missing_source")
    if snapshot.timestamp is None:
        violations.append("missing_timestamp")
    if not snapshot.symbol:
        violations.append("missing_symbol")
    if not snapshot.timeframe:
        violations.append("missing_timeframe")
    if not snapshot.session:
        violations.append("missing_session")
    if snapshot.broker_execution_readiness:
        violations.append("broker_execution_readiness_not_allowed")
    if require_spread and not snapshot.spread_available:
        violations.append("missing_required_spread")
    if require_volume and not snapshot.volume_available:
        violations.append("missing_required_volume")

    freshness_status = "UNKNOWN"
    if snapshot.timestamp is not None:
        age = as_of - snapshot.timestamp
        freshness_status = "FRESH" if timedelta() <= age <= max_age else "STALE"
        if freshness_status == "STALE":
            violations.append("stale_data")

    required_fields_complete = all(
        [
            snapshot.source,
            snapshot.timestamp,
            snapshot.symbol,
            snapshot.timeframe,
            snapshot.session,
        ]
    )
    completeness_status = "COMPLETE" if required_fields_complete else "INCOMPLETE"
    data_integrity_status = "PASS" if not violations else "FAIL"

    return MarketDataValidation(
        data_source=snapshot.source or "MISSING",
        data_timestamp=snapshot.timestamp.isoformat() if snapshot.timestamp else "MISSING",
        timeframe=snapshot.timeframe or "MISSING",
        session=snapshot.session or "MISSING",
        freshness_status=freshness_status,
        completeness_status=completeness_status,
        data_integrity_status=data_integrity_status,
        violations=tuple(violations),
        spread_available=snapshot.spread_available,
        volume_available=snapshot.volume_available,
        last_price=snapshot.last_price,
        bid_available=snapshot.bid_available,
        ask_available=snapshot.ask_available,
        bar_available=snapshot.bar_available,
        broker_execution_readiness=snapshot.broker_execution_readiness,
    )


def _watchlist_symbol_is_approved(text: str, symbol: str) -> bool:
    normalized_symbol = symbol.upper()
    active_symbol: str | None = None
    active_has_approval = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        lowered = line.lower()
        if lowered.startswith("- symbol:") or lowered.startswith("symbol:"):
            if active_symbol == normalized_symbol and active_has_approval:
                return True
            active_symbol = line.split(":", 1)[1].strip().upper()
            active_has_approval = False
            continue
        if active_symbol == normalized_symbol and (
            lowered in {"approved: true", "approved: yes", "- approved: true", "- approved: yes"}
            or "watchlist approval: approved" in lowered
            or "status: approved" in lowered
        ):
            active_has_approval = True
    return active_symbol == normalized_symbol and active_has_approval


def _dict_value(payload: dict[str, Any], *keys: str) -> dict[str, Any]:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _first_present(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return None


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if not isinstance(value, str):
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _redact(text: str, *configured_secrets: str | None) -> str:
    redacted = text
    for value in configured_secrets:
        if value:
            redacted = redacted.replace(value, "[REDACTED]")
    for env_name in ("ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY"):
        value = os.environ.get(env_name)
        if value:
            redacted = redacted.replace(value, "[REDACTED]")
    return redacted
