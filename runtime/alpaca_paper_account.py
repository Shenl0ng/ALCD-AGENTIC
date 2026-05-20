from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Mapping, Protocol
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PAPER_BASE_URL = "https://paper-api.alpaca.markets"
ENV_KEY_ID = "ALPACA_API_KEY_ID"
ENV_SECRET_KEY = "ALPACA_API_SECRET_KEY"
ENV_PAPER = "ALPACA_PAPER"


class AlpacaReadOnlyError(RuntimeError):
    pass


class AlpacaSafetyError(AlpacaReadOnlyError):
    pass


class AlpacaMissingCredentialsError(AlpacaReadOnlyError):
    pass


@dataclass(frozen=True)
class AlpacaPaperConfig:
    key_id: str = field(repr=False)
    secret_key: str = field(repr=False)
    base_url: str = PAPER_BASE_URL
    paper_mode: bool = True

    @classmethod
    def from_env(cls) -> AlpacaPaperConfig:
        key_id = os.environ.get(ENV_KEY_ID, "")
        secret_key = os.environ.get(ENV_SECRET_KEY, "")
        paper_mode = os.environ.get(ENV_PAPER, "false").lower() == "true"
        return cls(key_id=key_id, secret_key=secret_key, paper_mode=paper_mode)

    def validate(self) -> None:
        if not self.paper_mode:
            raise AlpacaSafetyError("Paper mode is required for read-only account access.")
        normalized = self.base_url.rstrip("/")
        if normalized != PAPER_BASE_URL:
            raise AlpacaSafetyError("Only the Alpaca paper endpoint is allowed.")
        if not self.key_id or not self.secret_key:
            raise AlpacaMissingCredentialsError(
                f"Missing read-only paper credentials in {ENV_KEY_ID}/{ENV_SECRET_KEY}."
            )


@dataclass(frozen=True)
class PaperAccountState:
    account_id: str | None
    cash: str | None
    equity: str | None
    buying_power: str | None
    portfolio_value: str | None
    day_trade_count: int | None
    trading_blocked: bool | None
    transfers_blocked: bool | None
    account_blocked: bool | None
    status: str | None
    read_status: str
    trading_allowed_in_principle: bool
    violations: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "account_id": self.account_id,
            "cash": self.cash,
            "equity": self.equity,
            "buying_power": self.buying_power,
            "portfolio_value": self.portfolio_value,
            "day_trade_count": self.day_trade_count,
            "trading_blocked": self.trading_blocked,
            "transfers_blocked": self.transfers_blocked,
            "account_blocked": self.account_blocked,
            "status": self.status,
            "read_status": self.read_status,
            "trading_allowed_in_principle": self.trading_allowed_in_principle,
            "violations": list(self.violations),
        }


@dataclass(frozen=True)
class PaperPositionRecord:
    symbol: str | None
    quantity: str | None
    market_value: str | None
    unrealized_pl: str | None
    average_entry_price: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "market_value": self.market_value,
            "unrealized_pl": self.unrealized_pl,
            "average_entry_price": self.average_entry_price,
        }


@dataclass(frozen=True)
class PaperOrderRecord:
    order_id: str | None
    symbol: str | None
    side: str | None
    order_type: str | None
    status: str | None
    submitted_time: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side,
            "type": self.order_type,
            "status": self.status,
            "submitted_time": self.submitted_time,
        }


@dataclass(frozen=True)
class PaperAccountSnapshot:
    account: PaperAccountState
    positions: tuple[PaperPositionRecord, ...]
    existing_orders: tuple[PaperOrderRecord, ...]
    paper_mode: bool = True

    def as_dict(self) -> dict[str, object]:
        return {
            "paper_mode": self.paper_mode,
            "account": self.account.as_dict(),
            "positions": [position.as_dict() for position in self.positions],
            "existing_orders": [order.as_dict() for order in self.existing_orders],
        }


class ReadOnlyHttpClient(Protocol):
    def get_json(
        self,
        path: str,
        params: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        """Perform a read-only GET request and return decoded JSON."""


class UrlLibReadOnlyHttpClient:
    def __init__(self, config: AlpacaPaperConfig) -> None:
        config.validate()
        self._base_url = config.base_url.rstrip("/")
        self._headers = {
            "APCA-API-KEY-ID": config.key_id,
            "APCA-API-SECRET-KEY": config.secret_key,
        }

    def get_json(
        self,
        path: str,
        params: Mapping[str, str] | None = None,
    ) -> Mapping[str, Any] | list[Mapping[str, Any]]:
        query = f"?{urlencode(params)}" if params else ""
        request = Request(f"{self._base_url}{path}{query}", headers=self._headers, method="GET")
        with urlopen(request, timeout=15) as response:
            payload = response.read().decode("utf-8")
        decoded = json.loads(payload)
        if not isinstance(decoded, (dict, list)):
            raise AlpacaReadOnlyError("Unexpected Alpaca paper response shape.")
        return decoded


class AlpacaPaperAccountReadOnlyAdapter:
    def __init__(self, config: AlpacaPaperConfig, client: ReadOnlyHttpClient | None = None) -> None:
        config.validate()
        self._client = client or UrlLibReadOnlyHttpClient(config)

    def read_account_state(self) -> PaperAccountState:
        payload = self._client.get_json("/v2/account")
        if not isinstance(payload, Mapping):
            raise AlpacaReadOnlyError("Account response must be an object.")
        return _account_state_from_payload(payload)

    def read_positions(self) -> tuple[PaperPositionRecord, ...]:
        payload = self._client.get_json("/v2/positions")
        if not isinstance(payload, list):
            raise AlpacaReadOnlyError("Positions response must be a list.")
        return tuple(_position_from_payload(position) for position in payload)

    def read_existing_paper_orders(self) -> tuple[PaperOrderRecord, ...]:
        payload = self._client.get_json("/v2/orders", {"status": "all", "limit": "50"})
        if not isinstance(payload, list):
            raise AlpacaReadOnlyError("Existing paper orders response must be a list.")
        return tuple(_order_from_payload(order) for order in payload)

    def read_paper_order_status(self, order_id: str) -> Mapping[str, Any]:
        payload = self._client.get_json(f"/v2/orders/{order_id}")
        if not isinstance(payload, Mapping):
            raise AlpacaReadOnlyError("Paper order status response must be an object.")
        return payload

    def read_account_and_positions_only(self) -> PaperAccountSnapshot:
        return PaperAccountSnapshot(
            account=self.read_account_state(),
            positions=self.read_positions(),
            existing_orders=(),
        )

    def read_snapshot(self) -> PaperAccountSnapshot:
        return PaperAccountSnapshot(
            account=self.read_account_state(),
            positions=self.read_positions(),
            existing_orders=self.read_existing_paper_orders(),
        )


class MockAlpacaPaperAccountReadOnlyAdapter:
    def __init__(self, snapshot: PaperAccountSnapshot | None = None) -> None:
        self._snapshot = snapshot or default_mock_snapshot()

    def read_snapshot(self) -> PaperAccountSnapshot:
        return self._snapshot

    def read_account_and_positions_only(self) -> PaperAccountSnapshot:
        return PaperAccountSnapshot(
            account=self._snapshot.account,
            positions=self._snapshot.positions,
            existing_orders=(),
            paper_mode=self._snapshot.paper_mode,
        )


def default_mock_snapshot() -> PaperAccountSnapshot:
    return PaperAccountSnapshot(
        account=PaperAccountState(
            account_id="paper-account-mock",
            cash="100000",
            equity="100000",
            buying_power="200000",
            portfolio_value="100000",
            day_trade_count=0,
            trading_blocked=False,
            transfers_blocked=False,
            account_blocked=False,
            status="ACTIVE",
            read_status="READ_OK",
            trading_allowed_in_principle=True,
        ),
        positions=(),
        existing_orders=(),
    )


def unavailable_snapshot(reason: str) -> PaperAccountSnapshot:
    return PaperAccountSnapshot(
        account=PaperAccountState(
            account_id=None,
            cash=None,
            equity=None,
            buying_power=None,
            portfolio_value=None,
            day_trade_count=None,
            trading_blocked=None,
            transfers_blocked=None,
            account_blocked=None,
            status=None,
            read_status="READ_UNAVAILABLE",
            trading_allowed_in_principle=False,
            violations=(reason,),
        ),
        positions=(),
        existing_orders=(),
    )


def _account_state_from_payload(payload: Mapping[str, Any]) -> PaperAccountState:
    violations: list[str] = []
    trading_blocked = _optional_bool(payload.get("trading_blocked"))
    account_blocked = _optional_bool(payload.get("account_blocked"))
    status = _optional_str(payload.get("status"))
    if trading_blocked:
        violations.append("trading_blocked")
    if account_blocked:
        violations.append("account_blocked")
    if status and status.upper() != "ACTIVE":
        violations.append("account_not_active")

    return PaperAccountState(
        account_id=_optional_str(payload.get("id") or payload.get("account_number")),
        cash=_optional_decimal_string(payload.get("cash")),
        equity=_optional_decimal_string(payload.get("equity")),
        buying_power=_optional_decimal_string(payload.get("buying_power")),
        portfolio_value=_optional_decimal_string(payload.get("portfolio_value")),
        day_trade_count=_optional_int(payload.get("daytrade_count")),
        trading_blocked=trading_blocked,
        transfers_blocked=_optional_bool(payload.get("transfers_blocked")),
        account_blocked=account_blocked,
        status=status,
        read_status="READ_OK",
        trading_allowed_in_principle=not violations,
        violations=tuple(violations),
    )


def _position_from_payload(payload: Mapping[str, Any]) -> PaperPositionRecord:
    return PaperPositionRecord(
        symbol=_optional_str(payload.get("symbol")),
        quantity=_optional_decimal_string(payload.get("qty")),
        market_value=_optional_decimal_string(payload.get("market_value")),
        unrealized_pl=_optional_decimal_string(payload.get("unrealized_pl")),
        average_entry_price=_optional_decimal_string(payload.get("avg_entry_price")),
    )


def _order_from_payload(payload: Mapping[str, Any]) -> PaperOrderRecord:
    return PaperOrderRecord(
        order_id=_optional_str(payload.get("id")),
        symbol=_optional_str(payload.get("symbol")),
        side=_optional_str(payload.get("side")),
        order_type=_optional_str(payload.get("type")),
        status=_optional_str(payload.get("status")),
        submitted_time=_optional_str(payload.get("submitted_at")),
    )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"


def _optional_decimal_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(Decimal(str(value)))


def main() -> int:
    try:
        adapter = AlpacaPaperAccountReadOnlyAdapter(AlpacaPaperConfig.from_env())
        snapshot = adapter.read_snapshot()
    except AlpacaReadOnlyError as error:
        safe_payload = unavailable_snapshot(type(error).__name__).as_dict()
        print(json.dumps(safe_payload, indent=2))
        return 1

    print(json.dumps(snapshot.as_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
