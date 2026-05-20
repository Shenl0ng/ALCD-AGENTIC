from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from finalized_paper_order_request import (
    PAPER_ORDER_REQUEST_FINALIZED,
    FinalizedPaperOrderRequest,
)
from manual_execution_confirmation import (
    MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT,
    ManualExecutionConfirmation,
    _default_finalized_request,
    create_manual_execution_confirmation,
)


REPORT_ROOT = Path("reports/paper_send_preflight")
REPORT_NAME = "PAPER_SEND_PREFLIGHT.md"
JOURNAL_NAME = "PAPER_SEND_PREFLIGHT_JOURNAL.json"

PAPER_ORDER_SEND_ALLOWED = "PAPER_ORDER_SEND_ALLOWED"
PAPER_ORDER_SEND_BLOCKED = "PAPER_ORDER_SEND_BLOCKED"
PAPER_ORDER_SEND_INVALID = "PAPER_ORDER_SEND_INVALID"
PAPER_ORDER_SEND_EXPIRED = "PAPER_ORDER_SEND_EXPIRED"
ALLOWED_PREFLIGHT_STATUSES = {
    PAPER_ORDER_SEND_ALLOWED,
    PAPER_ORDER_SEND_BLOCKED,
    PAPER_ORDER_SEND_INVALID,
    PAPER_ORDER_SEND_EXPIRED,
}
MAX_NOTIONAL_USD = Decimal("100")


@dataclass(frozen=True)
class PaperSendPreflight:
    preflight_id: str
    paper_order_request_id: str
    manual_confirmation_id: str
    checked_at: str
    preflight_status: str
    paper_trading_only: bool
    account_mode_checked: bool
    live_endpoint_rejected: bool
    max_notional_check: bool
    order_type_check: bool
    time_in_force_check: bool
    no_short_check: bool
    no_crypto_check: bool
    no_options_check: bool
    no_margin_check: bool
    no_extended_hours_check: bool
    one_order_only_check: bool
    no_batch_check: bool
    no_cancel_replace_check: bool
    broker_execution_allowed: bool
    live_trading_allowed: bool
    failure_reasons: tuple[str, ...]
    final_status: str

    def as_dict(self) -> dict[str, object]:
        return {
            "preflight_id": self.preflight_id,
            "paper_order_request_id": self.paper_order_request_id,
            "manual_confirmation_id": self.manual_confirmation_id,
            "checked_at": self.checked_at,
            "preflight_status": self.preflight_status,
            "paper_trading_only": self.paper_trading_only,
            "account_mode_checked": self.account_mode_checked,
            "live_endpoint_rejected": self.live_endpoint_rejected,
            "max_notional_check": self.max_notional_check,
            "order_type_check": self.order_type_check,
            "time_in_force_check": self.time_in_force_check,
            "no_short_check": self.no_short_check,
            "no_crypto_check": self.no_crypto_check,
            "no_options_check": self.no_options_check,
            "no_margin_check": self.no_margin_check,
            "no_extended_hours_check": self.no_extended_hours_check,
            "one_order_only_check": self.one_order_only_check,
            "no_batch_check": self.no_batch_check,
            "no_cancel_replace_check": self.no_cancel_replace_check,
            "broker_execution_allowed": self.broker_execution_allowed,
            "live_trading_allowed": self.live_trading_allowed,
            "failure_reasons": list(self.failure_reasons),
            "final_status": self.final_status,
        }


@dataclass(frozen=True)
class PreflightValidation:
    status: str
    violations: tuple[str, ...]
    checks: dict[str, bool]

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "violations": list(self.violations),
            "checks": self.checks,
        }


@dataclass(frozen=True)
class PreflightResult:
    preflight: PaperSendPreflight | None
    validation: PreflightValidation
    paper_order_request_id: str | None
    manual_confirmation_id: str | None
    preflight_status: str
    final_status: str
    reason: str
    report_path: str | None
    journal_path: str | None
    order_sent: bool = False
    alpaca_order_api_called: bool = False
    broker_execution_readiness: bool = False
    live_trading_assumption: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "preflight": self.preflight.as_dict() if self.preflight else None,
            "validation": self.validation.as_dict(),
            "paper_order_request_id": self.paper_order_request_id,
            "manual_confirmation_id": self.manual_confirmation_id,
            "preflight_status": self.preflight_status,
            "final_status": self.final_status,
            "reason": self.reason,
            "report_path": self.report_path,
            "journal_path": self.journal_path,
            "order_sent": self.order_sent,
            "alpaca_order_api_called": self.alpaca_order_api_called,
            "broker_execution_readiness": self.broker_execution_readiness,
            "live_trading_assumption": self.live_trading_assumption,
        }


def run_paper_send_preflight(
    *,
    request: FinalizedPaperOrderRequest | None,
    confirmation: ManualExecutionConfirmation | None,
    request_expired: bool = False,
    confirmation_expired: bool = False,
    account_mode_checked: bool = True,
    live_endpoint_configured: bool = False,
    order_count: int = 1,
    short_selling: bool = False,
    crypto: bool = False,
    options: bool = False,
    margin_or_leverage: bool = False,
    extended_hours: bool = False,
    batch_behavior: bool = False,
    cancel_replace_behavior: bool = False,
    output_root: Path = REPORT_ROOT,
    write_artifacts: bool = True,
) -> PreflightResult:
    validation = validate_paper_send_preflight(
        request=request,
        confirmation=confirmation,
        request_expired=request_expired,
        confirmation_expired=confirmation_expired,
        account_mode_checked=account_mode_checked,
        live_endpoint_configured=live_endpoint_configured,
        order_count=order_count,
        short_selling=short_selling,
        crypto=crypto,
        options=options,
        margin_or_leverage=margin_or_leverage,
        extended_hours=extended_hours,
        batch_behavior=batch_behavior,
        cancel_replace_behavior=cancel_replace_behavior,
    )
    if validation.passed:
        status = PAPER_ORDER_SEND_ALLOWED
        reason = (
            "Paper Send Preflight passed for later controlled paper send consideration only."
        )
    elif request_expired or confirmation_expired:
        status = PAPER_ORDER_SEND_EXPIRED
        reason = "; ".join(validation.violations)
    elif request is None or confirmation is None:
        status = PAPER_ORDER_SEND_BLOCKED
        reason = "; ".join(validation.violations)
    else:
        status = PAPER_ORDER_SEND_INVALID
        reason = "; ".join(validation.violations)

    preflight = _build_preflight(
        request=request,
        confirmation=confirmation,
        status=status,
        validation=validation,
    )
    return _preflight_result(
        preflight=preflight,
        validation=validation,
        request=request,
        confirmation=confirmation,
        preflight_status=status,
        reason=reason,
        output_root=output_root,
        write_artifacts=write_artifacts,
    )


def validate_paper_send_preflight(
    *,
    request: FinalizedPaperOrderRequest | None,
    confirmation: ManualExecutionConfirmation | None,
    request_expired: bool = False,
    confirmation_expired: bool = False,
    account_mode_checked: bool = True,
    live_endpoint_configured: bool = False,
    order_count: int = 1,
    short_selling: bool = False,
    crypto: bool = False,
    options: bool = False,
    margin_or_leverage: bool = False,
    extended_hours: bool = False,
    batch_behavior: bool = False,
    cancel_replace_behavior: bool = False,
) -> PreflightValidation:
    violations: list[str] = []
    checks = _base_checks(
        request=request,
        confirmation=confirmation,
        account_mode_checked=account_mode_checked,
        live_endpoint_configured=live_endpoint_configured,
        order_count=order_count,
        short_selling=short_selling,
        crypto=crypto,
        options=options,
        margin_or_leverage=margin_or_leverage,
        extended_hours=extended_hours,
        batch_behavior=batch_behavior,
        cancel_replace_behavior=cancel_replace_behavior,
    )

    if request is None:
        violations.append("finalized request missing")
    else:
        if request.request_status != PAPER_ORDER_REQUEST_FINALIZED:
            violations.append("request status is not PAPER_ORDER_REQUEST_FINALIZED")
        if request.paper_trading_only is not True:
            violations.append("paper_trading_only=true is required")
        if request.live_trading_allowed is not False:
            violations.append("request live_trading_allowed=false is required")
        if request.broker_execution_allowed is not False:
            violations.append("request broker_execution_allowed=false is required")
        if not _notional_within_limit(request.notional):
            violations.append("notional > 100 USD is blocked")
        if request.order_type.lower() != "limit":
            violations.append("order type must be limit")
        if request.time_in_force.lower() != "day":
            violations.append("time in force must be day")

    if confirmation is None:
        violations.append("manual confirmation missing")
    else:
        if (
            confirmation.confirmation_status
            != MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT
        ):
            violations.append(
                "confirmation status is not MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT"
            )
        if confirmation.broker_execution_allowed is not False:
            violations.append("confirmation broker_execution_allowed=false is required")
        if confirmation.live_trading_allowed is not False:
            violations.append("confirmation live_trading_allowed=false is required")
        if confirmation.paper_send_preflight_required is not True:
            violations.append("paper_send_preflight_required=true is required")
        for field_name, value in _required_confirmation_checks(confirmation).items():
            if value is not True:
                violations.append(f"{field_name} is required")

    if request_expired or confirmation_expired:
        violations.append("request or confirmation expired")
    if not account_mode_checked:
        violations.append("paper account mode read-only check is required")
    if live_endpoint_configured:
        violations.append("live endpoint configured is blocked")
    if short_selling:
        violations.append("short selling is blocked")
    if crypto:
        violations.append("crypto is blocked")
    if options:
        violations.append("options are blocked")
    if margin_or_leverage:
        violations.append("margin/leverage is blocked")
    if extended_hours:
        violations.append("extended hours are blocked")
    if order_count != 1:
        violations.append("one order only is required")
    if batch_behavior:
        violations.append("batch behavior is blocked")
    if cancel_replace_behavior:
        violations.append("cancel/replace behavior is blocked")
    if os.environ.get("PAPER_ORDER_EXECUTION_ENABLED", "").lower() == "true":
        violations.append("PAPER_ORDER_EXECUTION_ENABLED=true is blocked")
    return PreflightValidation("FAIL" if violations else "PASS", tuple(violations), checks)


def _base_checks(
    *,
    request: FinalizedPaperOrderRequest | None,
    confirmation: ManualExecutionConfirmation | None,
    account_mode_checked: bool,
    live_endpoint_configured: bool,
    order_count: int,
    short_selling: bool,
    crypto: bool,
    options: bool,
    margin_or_leverage: bool,
    extended_hours: bool,
    batch_behavior: bool,
    cancel_replace_behavior: bool,
) -> dict[str, bool]:
    return {
        "paper_trading_only": bool(request and request.paper_trading_only is True),
        "account_mode_checked": account_mode_checked,
        "live_endpoint_rejected": not live_endpoint_configured,
        "max_notional_check": bool(request and _notional_within_limit(request.notional)),
        "order_type_check": bool(request and request.order_type.lower() == "limit"),
        "time_in_force_check": bool(request and request.time_in_force.lower() == "day"),
        "no_short_check": not short_selling,
        "no_crypto_check": not crypto,
        "no_options_check": not options,
        "no_margin_check": not margin_or_leverage,
        "no_extended_hours_check": not extended_hours,
        "one_order_only_check": order_count == 1,
        "no_batch_check": not batch_behavior,
        "no_cancel_replace_check": not cancel_replace_behavior,
        "confirmation_broker_execution_allowed_false": bool(
            confirmation and confirmation.broker_execution_allowed is False
        ),
        "confirmation_live_trading_allowed_false": bool(
            confirmation and confirmation.live_trading_allowed is False
        ),
        "paper_send_preflight_required": bool(
            confirmation and confirmation.paper_send_preflight_required is True
        ),
    }


def _notional_within_limit(value: str) -> bool:
    try:
        return Decimal(str(value)) <= MAX_NOTIONAL_USD
    except (InvalidOperation, ValueError):
        return False


def _required_confirmation_checks(
    confirmation: ManualExecutionConfirmation,
) -> dict[str, bool]:
    return {
        "paper_only_confirmation": confirmation.paper_only_confirmation,
        "no_live_trading_confirmation": confirmation.no_live_trading_confirmation,
        "finalized_request_reviewed": confirmation.finalized_request_reviewed,
        "risk_reviewed": confirmation.risk_reviewed,
        "order_details_reviewed": confirmation.order_details_reviewed,
        "notional_limit_confirmation": confirmation.notional_limit_confirmation,
        "limit_order_confirmation": confirmation.limit_order_confirmation,
        "day_time_in_force_confirmation": confirmation.day_time_in_force_confirmation,
        "no_short_confirmation": confirmation.no_short_confirmation,
        "no_crypto_confirmation": confirmation.no_crypto_confirmation,
        "no_options_confirmation": confirmation.no_options_confirmation,
        "no_margin_confirmation": confirmation.no_margin_confirmation,
        "no_extended_hours_confirmation": confirmation.no_extended_hours_confirmation,
    }


def _build_preflight(
    *,
    request: FinalizedPaperOrderRequest | None,
    confirmation: ManualExecutionConfirmation | None,
    status: str,
    validation: PreflightValidation,
) -> PaperSendPreflight:
    checks = validation.checks
    return PaperSendPreflight(
        preflight_id=f"preflight-{request.paper_order_request_id if request else 'missing-request'}",
        paper_order_request_id=request.paper_order_request_id if request else "",
        manual_confirmation_id=confirmation.manual_confirmation_id if confirmation else "",
        checked_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        preflight_status=status,
        paper_trading_only=checks["paper_trading_only"],
        account_mode_checked=checks["account_mode_checked"],
        live_endpoint_rejected=checks["live_endpoint_rejected"],
        max_notional_check=checks["max_notional_check"],
        order_type_check=checks["order_type_check"],
        time_in_force_check=checks["time_in_force_check"],
        no_short_check=checks["no_short_check"],
        no_crypto_check=checks["no_crypto_check"],
        no_options_check=checks["no_options_check"],
        no_margin_check=checks["no_margin_check"],
        no_extended_hours_check=checks["no_extended_hours_check"],
        one_order_only_check=checks["one_order_only_check"],
        no_batch_check=checks["no_batch_check"],
        no_cancel_replace_check=checks["no_cancel_replace_check"],
        broker_execution_allowed=False,
        live_trading_allowed=False,
        failure_reasons=validation.violations,
        final_status=status,
    )


def _preflight_result(
    *,
    preflight: PaperSendPreflight,
    validation: PreflightValidation,
    request: FinalizedPaperOrderRequest | None,
    confirmation: ManualExecutionConfirmation | None,
    preflight_status: str,
    reason: str,
    output_root: Path,
    write_artifacts: bool,
) -> PreflightResult:
    report_path: Path | None = None
    journal_path: Path | None = None
    if write_artifacts:
        report_dir = _timestamped_report_dir(output_root)
        report_path = report_dir / REPORT_NAME
        journal_path = report_dir / JOURNAL_NAME
    result = PreflightResult(
        preflight=preflight,
        validation=validation,
        paper_order_request_id=request.paper_order_request_id if request else None,
        manual_confirmation_id=(
            confirmation.manual_confirmation_id if confirmation else None
        ),
        preflight_status=preflight_status,
        final_status=preflight_status,
        reason=reason,
        report_path=report_path.as_posix() if report_path else None,
        journal_path=journal_path.as_posix() if journal_path else None,
    )
    if write_artifacts and report_path and journal_path:
        journal_path.write_text(json.dumps(_journal_payload(result), indent=2), encoding="utf-8")
        report_path.write_text(_render_preflight_report(result), encoding="utf-8")
    return result


def _journal_payload(result: PreflightResult) -> dict[str, object]:
    preflight = result.preflight
    return {
        "preflight_id": preflight.preflight_id if preflight else None,
        "paper_order_request_id": result.paper_order_request_id,
        "manual_confirmation_id": result.manual_confirmation_id,
        "preflight_status": result.preflight_status,
        "checks": result.validation.checks,
        "failure_reasons": list(result.validation.violations),
        "broker_execution_allowed": (
            preflight.broker_execution_allowed if preflight else False
        ),
        "live_trading_allowed": preflight.live_trading_allowed if preflight else False,
        "final_status": result.final_status,
        "reason": result.reason,
        "order_sent": False,
        "alpaca_order_api_called": False,
        "broker_execution_readiness": False,
        "live_trading_assumption": False,
    }


def _render_preflight_report(result: PreflightResult) -> str:
    preflight = result.preflight
    return f"""# Paper Send Preflight

## Summary

- Preflight id: {preflight.preflight_id if preflight else None}
- Paper order request id: {result.paper_order_request_id}
- Manual confirmation id: {result.manual_confirmation_id}
- Preflight status: {result.preflight_status}
- Checks: {json.dumps(result.validation.checks, sort_keys=True)}
- Failure reasons: {json.dumps(list(result.validation.violations))}
- broker_execution_allowed: {str(preflight.broker_execution_allowed if preflight else False).lower()}
- live_trading_allowed: {str(preflight.live_trading_allowed if preflight else False).lower()}
- Final status: {result.final_status}
- Reason: {result.reason}

## Preflight

```json
{json.dumps(preflight.as_dict() if preflight else None, indent=2)}
```

## Safety

Paper Send Preflight does not send orders.
PAPER_ORDER_SEND_ALLOWED is not broker execution.
PAPER_ORDER_SEND_ALLOWED does not call Alpaca.
PAPER_ORDER_EXECUTION_ENABLED was not enabled.
No order was sent.
No broker execution readiness was created.
Live trading remains unsupported.
"""


def _timestamped_report_dir(output_root: Path) -> Path:
    report_dir = output_root / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = 1
    while report_dir.exists():
        report_dir = output_root / f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{suffix}"
        suffix += 1
    report_dir.mkdir(parents=True, exist_ok=False)
    return report_dir


def _default_request_and_confirmation() -> tuple[
    FinalizedPaperOrderRequest,
    ManualExecutionConfirmation,
]:
    request = _default_finalized_request()
    result = create_manual_execution_confirmation(
        request=request,
        confirmer="manual-confirmer",
        write_artifacts=False,
    )
    if result.confirmation is None:
        raise RuntimeError("default manual confirmation could not be created")
    return request, result.confirmation


def main() -> int:
    parser = argparse.ArgumentParser(description="Run inert Paper Send Preflight.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    request, confirmation = _default_request_and_confirmation()
    result = run_paper_send_preflight(request=request, confirmation=confirmation)
    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(result.final_status)
        print(result.report_path)
    return 0 if result.preflight_status == PAPER_ORDER_SEND_ALLOWED else 1


if __name__ == "__main__":
    raise SystemExit(main())
