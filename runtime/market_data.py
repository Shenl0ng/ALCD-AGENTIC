from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol


SIMULATION_AS_OF = datetime(2026, 5, 19, 13, 30, tzinfo=UTC)
MAX_FRESHNESS_AGE = timedelta(minutes=15)


@dataclass(frozen=True)
class MarketDataSnapshot:
    source: str | None
    timestamp: datetime | None
    symbol: str | None
    timeframe: str | None
    session: str | None
    spread_available: bool
    volume_available: bool


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
        }


class MarketDataAdapter(Protocol):
    def load_snapshot(self, routine_name: str) -> MarketDataSnapshot:
        """Return deterministic market data for Data Integrity validation only."""


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
    )
