from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Protocol
from urllib.request import Request, urlopen

from alpaca_paper_account import PAPER_BASE_URL, PaperAccountSnapshot, default_mock_snapshot
from human_approval import HUMAN_APPROVED_FOR_PAPER_ONLY, JournalEntry, commit_journal_entry
from paper_order_request import (
    EVALUATION_GATE_PASSED,
    PAPER_ORDER_REQUEST_CREATED,
    READY_FOR_PAPER_ORDER_REQUEST,
    PaperOrderRequest,
    deterministic_valid_request,
    validate_paper_order_request,
)
from paper_trade import RISK_APPROVED


ENV_EXECUTION_ENABLED = "PAPER_ORDER_EXECUTION_ENABLED"
ENV_ALPACA_API_KEY_ID = "ALPACA_API_KEY_ID"
ENV_ALPACA_API_SECRET_KEY = "ALPACA_API_SECRET_KEY"
ENV_ALPACA_PAPER = "ALPACA_PAPER"
DRY_RUN_ONLY = "DRY_RUN_ONLY"
MOCKED_PAPER_SEND = "MOCKED_PAPER_SEND"
REAL_ALPACA_PAPER_SEND = "REAL_ALPACA_PAPER_SEND"
EXECUTION_MODES = {DRY_RUN_ONLY, MOCKED_PAPER_SEND, REAL_ALPACA_PAPER_SEND}
PAPER_ORDER_SEND_BLOCKED = "PAPER_ORDER_SEND_BLOCKED"
PAPER_ORDER_SEND_ALLOWED = "PAPER_ORDER_SEND_ALLOWED"
PAPER_ORDER_SEND_SUCCEEDED = "PAPER_ORDER_SEND_SUCCEEDED"
PAPER_ORDER_SUBMITTED = "PAPER_ORDER_SUBMITTED"
PAPER_ORDER_REJECTED_BY_PREFLIGHT = "PAPER_ORDER_REJECTED_BY_PREFLIGHT"
PAPER_ORDER_REJECTED_BY_ADAPTER = "PAPER_ORDER_REJECTED_BY_ADAPTER"
PAPER_ORDER_REJECTED_BY_ALPACA = "PAPER_ORDER_REJECTED_BY_ALPACA"
PAPER_ORDER_SEND_ERROR = "PAPER_ORDER_SEND_ERROR"
MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY = "MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY"
MAX_NOTIONAL_PER_PAPER_ORDER = Decimal("100")


@dataclass(frozen=True)
class PaperOrderAdapterConfig:
    execution_enabled: bool = False
    execution_mode: str = DRY_RUN_ONLY
    base_url: str = PAPER_BASE_URL
    paper_mode: bool = True
    allow_market_orders: bool = False
    allow_short_selling: bool = False
    allow_bracket_orders: bool = False

    @classmethod
    def from_env(cls) -> PaperOrderAdapterConfig:
        enabled = os.environ.get(ENV_EXECUTION_ENABLED, "false").lower() == "true"
        paper_mode = os.environ.get(ENV_ALPACA_PAPER, "false").lower() == "true"
        return cls(execution_enabled=enabled, paper_mode=paper_mode)


@dataclass(frozen=True)
class PaperOrderPreflightReport:
    request_id: str | None
    proposal_id: str | None
    approval_id: str | None
    journal_entry_id: str | None
    paper_mode_confirmation: bool
    live_mode_rejection_confirmation: bool
    risk_approval_reference: str | None
    human_approval_reference: str | None
    journal_commit_reference: str | None
    adlc_compliance_reference: str | None
    account_mode_check: str
    request_expiration_check: str
    final_decision: str
    violations: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "request_id": self.request_id,
            "proposal_id": self.proposal_id,
            "approval_id": self.approval_id,
            "journal_entry_id": self.journal_entry_id,
            "paper_mode_confirmation": self.paper_mode_confirmation,
            "live_mode_rejection_confirmation": self.live_mode_rejection_confirmation,
            "risk_approval_reference": self.risk_approval_reference,
            "human_approval_reference": self.human_approval_reference,
            "journal_commit_reference": self.journal_commit_reference,
            "adlc_compliance_reference": self.adlc_compliance_reference,
            "account_mode_check": self.account_mode_check,
            "request_expiration_check": self.request_expiration_check,
            "final_decision": self.final_decision,
            "violations": list(self.violations),
        }


@dataclass(frozen=True)
class PaperOrderSendResult:
    status: str
    preflight: PaperOrderPreflightReport
    client_reference: str | None = None
    execution_result: "PaperOrderExecutionResult | None" = None
    journal_entry: JournalEntry | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "preflight": self.preflight.as_dict(),
            "client_reference": self.client_reference,
            "execution_result": (
                self.execution_result.as_dict() if self.execution_result else None
            ),
            "journal_entry": self.journal_entry.as_dict() if self.journal_entry else None,
        }


class MockPaperSendClient(Protocol):
    def send_paper_order_request(self, payload: Mapping[str, object]) -> Mapping[str, object]:
        """Send already preflighted paper request through a mocked paper client."""


@dataclass(frozen=True)
class PaperOrderExecutionResult:
    execution_result_id: str
    paper_order_request_id: str | None
    proposal_id: str | None
    approval_id: str | None
    manual_confirmation_id: str | None
    journal_entry_id: str | None
    submitted_at: str
    broker: str
    account_mode: str
    symbol: str | None
    side: str | None
    quantity: str | None
    notional: str | None
    order_type: str | None
    limit_price: str | None
    time_in_force: str | None
    alpaca_order_id: str | None
    alpaca_order_status: str | None
    final_status: str
    error_message: str | None
    preflight_reference: str
    adlc_compliance_reference: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "execution_result_id": self.execution_result_id,
            "paper_order_request_id": self.paper_order_request_id,
            "proposal_id": self.proposal_id,
            "approval_id": self.approval_id,
            "manual_confirmation_id": self.manual_confirmation_id,
            "journal_entry_id": self.journal_entry_id,
            "submitted_at": self.submitted_at,
            "broker": self.broker,
            "account_mode": self.account_mode,
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "notional": self.notional,
            "order_type": self.order_type,
            "limit_price": self.limit_price,
            "time_in_force": self.time_in_force,
            "alpaca_order_id": self.alpaca_order_id,
            "alpaca_order_status": self.alpaca_order_status,
            "final_status": self.final_status,
            "error_message": self.error_message,
            "preflight_reference": self.preflight_reference,
            "adlc_compliance_reference": self.adlc_compliance_reference,
        }


class UrlLibAlpacaPaperOrderClient:
    def __init__(self, *, key_id: str, secret_key: str, base_url: str = PAPER_BASE_URL) -> None:
        if base_url.rstrip("/") != PAPER_BASE_URL:
            raise ValueError("Only the Alpaca paper endpoint is allowed.")
        if not key_id or not secret_key:
            raise ValueError("Missing Alpaca paper credentials.")
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "APCA-API-KEY-ID": key_id,
            "APCA-API-SECRET-KEY": secret_key,
            "Content-Type": "application/json",
        }

    def send_paper_order_request(self, payload: Mapping[str, object]) -> Mapping[str, object]:
        body = json.dumps(payload).encode("utf-8")
        request = Request(
            f"{self._base_url}/v2/orders",
            data=body,
            headers=self._headers,
            method="POST",
        )
        with urlopen(request, timeout=15) as response:
            decoded = json.loads(response.read().decode("utf-8"))
        if not isinstance(decoded, Mapping):
            raise RuntimeError("Unexpected Alpaca paper order response shape.")
        return decoded


class AlpacaPaperOrderAdapter:
    def __init__(
        self,
        config: PaperOrderAdapterConfig | None = None,
        client: MockPaperSendClient | None = None,
    ) -> None:
        self.config = config or PaperOrderAdapterConfig()
        self._client = client
        self._submitted_order_count = 0

    def preflight(
        self,
        request: PaperOrderRequest | object,
        *,
        account: PaperAccountSnapshot,
        journal_commit: JournalEntry | None,
        manual_confirmation: object | None = None,
    ) -> PaperOrderPreflightReport:
        if not isinstance(request, PaperOrderRequest):
            return _blocked_preflight(None, ("request is not a PaperOrderRequest",))

        violations: list[str] = []
        if self.config.execution_mode not in EXECUTION_MODES:
            violations.append("adapter mode is not supported")
        if self.config.execution_mode == DRY_RUN_ONLY:
            violations.append("adapter mode is DRY_RUN_ONLY")
        if not self.config.execution_enabled:
            violations.append("PAPER_ORDER_EXECUTION_ENABLED is not true")
        if not self.config.paper_mode:
            violations.append("paper mode is not confirmed")
        if self.config.base_url.rstrip("/") != PAPER_BASE_URL:
            violations.append("live endpoint/config rejected")
        if self._submitted_order_count >= 1:
            violations.append("more than one order per run rejected")
        if not account.paper_mode:
            violations.append("non-paper account rejected")
        if not request.paper_trading_only:
            violations.append("paper_trading_only is not true")
        if request.broker_execution_allowed:
            violations.append("broker_execution_allowed was true at request creation")
        if request.live_trading_allowed:
            violations.append("live_trading_allowed is true")
        if request.gatekeeper_status != READY_FOR_PAPER_ORDER_REQUEST:
            violations.append("gatekeeper status is not READY_FOR_PAPER_ORDER_REQUEST")
        if request.risk_approval_reference != RISK_APPROVED:
            violations.append("missing risk approval")
        if request.human_approval_reference != HUMAN_APPROVED_FOR_PAPER_ONLY:
            violations.append("missing human approval")
        if not _manual_confirmation_passed(request, manual_confirmation):
            violations.append("missing manual execution confirmation")
        if journal_commit is None or not request.journal_commit_reference:
            violations.append("missing journal commit")
        if request.adlc_compliance_reference != "PASS":
            violations.append("ADLC compliance is not PASS")
        if request.evaluation_gate_reference != EVALUATION_GATE_PASSED:
            violations.append("evaluation gate did not pass")
        if _is_expired(request):
            violations.append("request is expired")
        if request.final_status != PAPER_ORDER_REQUEST_CREATED:
            violations.append("request final_status is not PAPER_ORDER_REQUEST_CREATED")
        if request.order_type == "market" and not self.config.allow_market_orders:
            violations.append("market orders are not allowed by governance")
        if request.order_type != "limit":
            violations.append("Phase 9 allows limit orders only")
        if request.time_in_force != "day":
            violations.append("Phase 9 allows day time in force only")
        if request.side == "short" and not self.config.allow_short_selling:
            violations.append("short selling is not allowed by governance")
        if request.side not in {"long", "buy"}:
            violations.append("Phase 9 supports long buy orders only")
        if _notional_value(request) is None:
            violations.append("order notional could not be determined")
        elif _notional_value(request) > MAX_NOTIONAL_PER_PAPER_ORDER:
            violations.append("notional over 100 USD")
        if _is_option_symbol(request.symbol):
            violations.append("options are disabled")
        if _is_crypto_symbol(request.symbol):
            violations.append("crypto is disabled")
        if _is_margin_or_leverage_request(request):
            violations.append("margin/leverage is disabled")
        if _uses_extended_hours(request):
            violations.append("extended hours are disabled")
        if _uses_complex_order(request) and not self.config.allow_bracket_orders:
            violations.append("bracket/complex orders are disabled")

        validation = validate_paper_order_request(
            request,
            proposal=None,
            risk_evaluation=None,
            approval=None,
            journal_commit=journal_commit,
        )
        request_validation_violations = tuple(
            violation
            for violation in validation.violations
            if violation
            not in {
                "proposal is not risk-approved",
                "human approval is missing or not HUMAN_APPROVED_FOR_PAPER_ONLY",
                "proposal validation did not pass",
            }
        )
        violations.extend(request_validation_violations)

        final_decision = PAPER_ORDER_SEND_BLOCKED if violations else PAPER_ORDER_SEND_ALLOWED
        return PaperOrderPreflightReport(
            request_id=request.paper_order_request_id,
            proposal_id=request.proposal_id,
            approval_id=request.approval_id,
            journal_entry_id=request.journal_entry_id,
            paper_mode_confirmation=self.config.paper_mode and account.paper_mode,
            live_mode_rejection_confirmation=self.config.base_url.rstrip("/") == PAPER_BASE_URL,
            risk_approval_reference=request.risk_approval_reference,
            human_approval_reference=request.human_approval_reference,
            journal_commit_reference=request.journal_commit_reference,
            adlc_compliance_reference=request.adlc_compliance_reference,
            account_mode_check="PAPER" if account.paper_mode else "NON_PAPER",
            request_expiration_check="EXPIRED" if _is_expired(request) else "ACTIVE",
            final_decision=final_decision,
            violations=tuple(dict.fromkeys(violations)),
        )

    def send_paper_order_request(
        self,
        request: PaperOrderRequest | object,
        *,
        account: PaperAccountSnapshot,
        journal_commit: JournalEntry | None,
        manual_confirmation: object | None = None,
    ) -> PaperOrderSendResult:
        preflight = self.preflight(
            request,
            account=account,
            journal_commit=journal_commit,
            manual_confirmation=manual_confirmation,
        )
        if preflight.final_decision != PAPER_ORDER_SEND_ALLOWED:
            execution_result = _execution_result(
                request,
                account=account,
                manual_confirmation=manual_confirmation,
                preflight=preflight,
                final_status=PAPER_ORDER_REJECTED_BY_PREFLIGHT,
                error_message="; ".join(preflight.violations),
            )
            return PaperOrderSendResult(
                PAPER_ORDER_REJECTED_BY_PREFLIGHT,
                preflight,
                execution_result=execution_result,
                journal_entry=_post_send_journal(request, execution_result),
            )
        if self._client is None and self.config.execution_mode == REAL_ALPACA_PAPER_SEND:
            self._client = UrlLibAlpacaPaperOrderClient(
                key_id=os.environ.get(ENV_ALPACA_API_KEY_ID, ""),
                secret_key=os.environ.get(ENV_ALPACA_API_SECRET_KEY, ""),
                base_url=self.config.base_url,
            )
        if self._client is None:
            blocked = PaperOrderPreflightReport(
                **{
                    **preflight.as_dict(),
                    "final_decision": PAPER_ORDER_SEND_BLOCKED,
                    "violations": ("paper send client is required",),
                }
            )
            execution_result = _execution_result(
                request,
                account=account,
                manual_confirmation=manual_confirmation,
                preflight=blocked,
                final_status=PAPER_ORDER_REJECTED_BY_ADAPTER,
                error_message="paper send client is required",
            )
            return PaperOrderSendResult(
                PAPER_ORDER_REJECTED_BY_ADAPTER,
                blocked,
                execution_result=execution_result,
                journal_entry=_post_send_journal(request, execution_result),
            )
        try:
            response = self._client.send_paper_order_request(_paper_payload(request))
        except Exception as exc:
            execution_result = _execution_result(
                request,
                account=account,
                manual_confirmation=manual_confirmation,
                preflight=preflight,
                final_status=PAPER_ORDER_SEND_ERROR,
                error_message=_safe_error(exc),
            )
            return PaperOrderSendResult(
                PAPER_ORDER_SEND_ERROR,
                preflight,
                execution_result=execution_result,
                journal_entry=_post_send_journal(request, execution_result),
            )
        final_status = (
            PAPER_ORDER_REJECTED_BY_ALPACA
            if str(response.get("status", "")).lower() in {"rejected", "canceled", "expired"}
            else PAPER_ORDER_SUBMITTED
        )
        execution_result = _execution_result(
            request,
            account=account,
            manual_confirmation=manual_confirmation,
            preflight=preflight,
            final_status=final_status,
            alpaca_order_id=_string_or_none(response.get("id") or response.get("paper_client_reference")),
            alpaca_order_status=_string_or_none(response.get("status", "accepted")),
        )
        if execution_result.final_status == PAPER_ORDER_SUBMITTED:
            self._submitted_order_count += 1
        return PaperOrderSendResult(
            status=final_status,
            preflight=preflight,
            client_reference=execution_result.alpaca_order_id,
            execution_result=execution_result,
            journal_entry=_post_send_journal(request, execution_result),
        )


class RecordingMockPaperClient:
    def __init__(self) -> None:
        self.payloads: list[Mapping[str, object]] = []

    def send_paper_order_request(self, payload: Mapping[str, object]) -> Mapping[str, object]:
        self.payloads.append(payload)
        return {"paper_client_reference": "mock-paper-send-001"}


def _paper_payload(request: PaperOrderRequest | object) -> Mapping[str, object]:
    assert isinstance(request, PaperOrderRequest)
    payload: dict[str, object] = {
        "symbol": request.symbol,
        "side": "buy",
        "type": "limit",
        "time_in_force": "day",
        "limit_price": request.proposed_entry,
        "paper_order_request_id": request.paper_order_request_id,
    }
    if request.notional:
        payload["notional"] = request.notional
    else:
        payload["qty"] = request.quantity
    return payload


def _blocked_preflight(
    request: PaperOrderRequest | None,
    violations: tuple[str, ...],
) -> PaperOrderPreflightReport:
    return PaperOrderPreflightReport(
        request_id=request.paper_order_request_id if request else None,
        proposal_id=request.proposal_id if request else None,
        approval_id=request.approval_id if request else None,
        journal_entry_id=request.journal_entry_id if request else None,
        paper_mode_confirmation=False,
        live_mode_rejection_confirmation=True,
        risk_approval_reference=request.risk_approval_reference if request else None,
        human_approval_reference=request.human_approval_reference if request else None,
        journal_commit_reference=request.journal_commit_reference if request else None,
        adlc_compliance_reference=request.adlc_compliance_reference if request else None,
        account_mode_check="UNKNOWN",
        request_expiration_check="UNKNOWN",
        final_decision=PAPER_ORDER_SEND_BLOCKED,
        violations=violations,
    )


def _is_expired(request: PaperOrderRequest) -> bool:
    if not request.expires_at:
        return False
    expires_at = datetime.fromisoformat(request.expires_at.replace("Z", "+00:00"))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at <= datetime(2026, 5, 19, 13, 36, tzinfo=UTC)


def _manual_confirmation_passed(
    request: PaperOrderRequest,
    manual_confirmation: object | None,
) -> bool:
    return (
        manual_confirmation is not None
        and getattr(manual_confirmation, "confirmation_state", None)
        == MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY
        and getattr(manual_confirmation, "paper_only_confirmation", False) is True
        and getattr(manual_confirmation, "paper_order_request_id", None)
        == request.paper_order_request_id
        and bool(getattr(manual_confirmation, "confirmation_id", None))
    )


def _decimal_or_none(value: str | None) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _notional_value(request: PaperOrderRequest) -> Decimal | None:
    notional = _decimal_or_none(request.notional)
    if notional is not None:
        return notional
    quantity = _decimal_or_none(request.quantity)
    limit_price = _decimal_or_none(request.proposed_entry)
    if quantity is None or limit_price is None:
        return None
    return quantity * limit_price


def _is_option_symbol(symbol: str | None) -> bool:
    if not symbol:
        return False
    return len(symbol) >= 15 and symbol[-8:].isdigit()


def _is_crypto_symbol(symbol: str | None) -> bool:
    if not symbol:
        return False
    normalized = symbol.upper().replace("/", "")
    crypto_markers = ("BTC", "ETH", "SOL", "DOGE", "USDT", "USDC")
    return any(marker in normalized for marker in crypto_markers)


def _is_margin_or_leverage_request(request: PaperOrderRequest) -> bool:
    text = " ".join(
        str(value or "")
        for value in (request.order_intent, request.order_type, request.time_in_force)
    ).lower()
    return "margin" in text or "leverage" in text


def _uses_extended_hours(request: PaperOrderRequest) -> bool:
    text = " ".join(str(value or "") for value in (request.order_intent, request.time_in_force))
    return "extended" in text.lower()


def _uses_complex_order(request: PaperOrderRequest) -> bool:
    text = " ".join(str(value or "") for value in (request.order_intent, request.order_type))
    markers = ("bracket", "oco", "oto", "trailing", "stop_limit", "complex")
    return any(marker in text.lower() for marker in markers)


def _execution_result(
    request: PaperOrderRequest | object,
    *,
    account: PaperAccountSnapshot,
    manual_confirmation: object | None,
    preflight: PaperOrderPreflightReport,
    final_status: str,
    error_message: str | None = None,
    alpaca_order_id: str | None = None,
    alpaca_order_status: str | None = None,
) -> PaperOrderExecutionResult:
    typed_request = request if isinstance(request, PaperOrderRequest) else None
    request_id = typed_request.paper_order_request_id if typed_request else None
    return PaperOrderExecutionResult(
        execution_result_id=f"execution-result-{request_id or 'blocked'}",
        paper_order_request_id=request_id,
        proposal_id=typed_request.proposal_id if typed_request else None,
        approval_id=typed_request.approval_id if typed_request else None,
        manual_confirmation_id=_string_or_none(
            getattr(manual_confirmation, "confirmation_id", None)
        ),
        journal_entry_id=typed_request.journal_entry_id if typed_request else None,
        submitted_at="2026-05-19T13:38:00+00:00",
        broker="alpaca",
        account_mode="PAPER" if account.paper_mode else "NON_PAPER",
        symbol=typed_request.symbol if typed_request else None,
        side="buy" if typed_request and typed_request.side in {"long", "buy"} else None,
        quantity=typed_request.quantity if typed_request and not typed_request.notional else None,
        notional=typed_request.notional if typed_request else None,
        order_type=typed_request.order_type if typed_request else None,
        limit_price=typed_request.proposed_entry if typed_request else None,
        time_in_force=typed_request.time_in_force if typed_request else None,
        alpaca_order_id=alpaca_order_id,
        alpaca_order_status=alpaca_order_status,
        final_status=final_status,
        error_message=error_message,
        preflight_reference=preflight.final_decision,
        adlc_compliance_reference=typed_request.adlc_compliance_reference if typed_request else None,
    )


def _post_send_journal(
    request: PaperOrderRequest | object,
    execution_result: PaperOrderExecutionResult,
) -> JournalEntry:
    if execution_result.final_status == PAPER_ORDER_SUBMITTED:
        event_type = "paper_order_send_submitted"
    elif execution_result.final_status == PAPER_ORDER_REJECTED_BY_ALPACA:
        event_type = "paper_order_send_broker_rejected"
    elif execution_result.final_status == PAPER_ORDER_REJECTED_BY_ADAPTER:
        event_type = "paper_order_send_adapter_rejected"
    elif execution_result.final_status == PAPER_ORDER_SEND_ERROR:
        event_type = "paper_order_send_error"
    else:
        event_type = "paper_order_send_blocked"
    notes = (
        f"send attempted; final status={execution_result.final_status}; "
        f"alpaca_order_id={execution_result.alpaca_order_id or 'none'}"
    )
    return commit_journal_entry(
        proposal=None,
        risk_status=getattr(request, "risk_approval_reference", "UNKNOWN") or "UNKNOWN",
        human_approval_status=getattr(request, "human_approval_reference", "UNKNOWN") or "UNKNOWN",
        gatekeeper_status=getattr(request, "gatekeeper_status", "UNKNOWN") or "UNKNOWN",
        event_type=event_type,
        reason_for_final_decision=execution_result.final_status,
        lessons_or_notes=notes,
        routine_name="manual_paper_send",
        adlc_status=getattr(request, "adlc_compliance_reference", "UNKNOWN") or "UNKNOWN",
    )


def _safe_error(exc: Exception) -> str:
    message = str(exc)
    for secret_name in (ENV_ALPACA_API_KEY_ID, ENV_ALPACA_API_SECRET_KEY):
        secret = os.environ.get(secret_name)
        if secret:
            message = message.replace(secret, "[REDACTED]")
    return message or exc.__class__.__name__


def _string_or_none(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run paper order adapter preflight.")
    parser.add_argument("--enabled", action="store_true")
    parser.add_argument(
        "--mode",
        choices=(DRY_RUN_ONLY, MOCKED_PAPER_SEND, REAL_ALPACA_PAPER_SEND),
        default=DRY_RUN_ONLY,
    )
    args = parser.parse_args()

    _, _, _, journal, request, _ = deterministic_valid_request()
    adapter = AlpacaPaperOrderAdapter(
        PaperOrderAdapterConfig(execution_enabled=args.enabled, execution_mode=args.mode),
        RecordingMockPaperClient(),
    )
    result = adapter.send_paper_order_request(
        request,
        account=default_mock_snapshot(),
        journal_commit=journal,
        manual_confirmation=None,
    )
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.preflight.final_decision == PAPER_ORDER_SEND_ALLOWED else 1


if __name__ == "__main__":
    raise SystemExit(main())
