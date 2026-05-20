from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from finalized_paper_order_request import (
    PAPER_ORDER_REQUEST_FINALIZED,
    FinalizedPaperOrderRequest,
    finalize_paper_order_request,
)
from finalized_paper_order_request import _default_candidate_and_review


REPORT_ROOT = Path("reports/manual_execution_confirmation")
REPORT_NAME = "MANUAL_EXECUTION_CONFIRMATION.md"
JOURNAL_NAME = "MANUAL_EXECUTION_CONFIRMATION_JOURNAL.json"

MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT = (
    "MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT"
)
MANUAL_EXECUTION_REJECTED = "MANUAL_EXECUTION_REJECTED"
MANUAL_EXECUTION_NEEDS_MORE_INFORMATION = "MANUAL_EXECUTION_NEEDS_MORE_INFORMATION"
MANUAL_EXECUTION_EXPIRED = "MANUAL_EXECUTION_EXPIRED"
MANUAL_EXECUTION_INVALID = "MANUAL_EXECUTION_INVALID"
ALLOWED_CONFIRMATION_STATUSES = {
    MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT,
    MANUAL_EXECUTION_REJECTED,
    MANUAL_EXECUTION_NEEDS_MORE_INFORMATION,
    MANUAL_EXECUTION_EXPIRED,
    MANUAL_EXECUTION_INVALID,
}


@dataclass(frozen=True)
class ManualExecutionConfirmation:
    manual_confirmation_id: str
    paper_order_request_id: str
    candidate_id: str
    review_id: str
    confirmed_at: str
    confirmer: str
    confirmation_status: str
    confirmation_notes: str
    paper_only_confirmation: bool
    no_live_trading_confirmation: bool
    finalized_request_reviewed: bool
    risk_reviewed: bool
    order_details_reviewed: bool
    notional_limit_confirmation: bool
    limit_order_confirmation: bool
    day_time_in_force_confirmation: bool
    no_short_confirmation: bool
    no_crypto_confirmation: bool
    no_options_confirmation: bool
    no_margin_confirmation: bool
    no_extended_hours_confirmation: bool
    broker_execution_allowed: bool
    live_trading_allowed: bool
    paper_send_preflight_required: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "manual_confirmation_id": self.manual_confirmation_id,
            "paper_order_request_id": self.paper_order_request_id,
            "candidate_id": self.candidate_id,
            "review_id": self.review_id,
            "confirmed_at": self.confirmed_at,
            "confirmer": self.confirmer,
            "confirmation_status": self.confirmation_status,
            "confirmation_notes": self.confirmation_notes,
            "paper_only_confirmation": self.paper_only_confirmation,
            "no_live_trading_confirmation": self.no_live_trading_confirmation,
            "finalized_request_reviewed": self.finalized_request_reviewed,
            "risk_reviewed": self.risk_reviewed,
            "order_details_reviewed": self.order_details_reviewed,
            "notional_limit_confirmation": self.notional_limit_confirmation,
            "limit_order_confirmation": self.limit_order_confirmation,
            "day_time_in_force_confirmation": self.day_time_in_force_confirmation,
            "no_short_confirmation": self.no_short_confirmation,
            "no_crypto_confirmation": self.no_crypto_confirmation,
            "no_options_confirmation": self.no_options_confirmation,
            "no_margin_confirmation": self.no_margin_confirmation,
            "no_extended_hours_confirmation": self.no_extended_hours_confirmation,
            "broker_execution_allowed": self.broker_execution_allowed,
            "live_trading_allowed": self.live_trading_allowed,
            "paper_send_preflight_required": self.paper_send_preflight_required,
        }


@dataclass(frozen=True)
class ManualConfirmationValidation:
    status: str
    violations: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def as_dict(self) -> dict[str, object]:
        return {"status": self.status, "violations": list(self.violations)}


@dataclass(frozen=True)
class ManualConfirmationResult:
    confirmation: ManualExecutionConfirmation | None
    validation: ManualConfirmationValidation
    paper_order_request_id: str | None
    candidate_id: str | None
    review_id: str | None
    confirmation_status: str
    final_status: str
    reason: str
    report_path: str | None
    journal_path: str | None
    paper_send_preflight_created: bool = False
    order_sent: bool = False
    broker_execution_readiness: bool = False
    alpaca_order_api_called: bool = False
    live_trading_assumption: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "confirmation": self.confirmation.as_dict() if self.confirmation else None,
            "validation": self.validation.as_dict(),
            "paper_order_request_id": self.paper_order_request_id,
            "candidate_id": self.candidate_id,
            "review_id": self.review_id,
            "confirmation_status": self.confirmation_status,
            "final_status": self.final_status,
            "reason": self.reason,
            "report_path": self.report_path,
            "journal_path": self.journal_path,
            "paper_send_preflight_created": self.paper_send_preflight_created,
            "order_sent": self.order_sent,
            "broker_execution_readiness": self.broker_execution_readiness,
            "alpaca_order_api_called": self.alpaca_order_api_called,
            "live_trading_assumption": self.live_trading_assumption,
        }


def create_manual_execution_confirmation(
    *,
    request: FinalizedPaperOrderRequest | None,
    confirmer: str,
    confirmation_status: str = MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT,
    confirmation_notes: str = "",
    paper_only_confirmation: bool = True,
    no_live_trading_confirmation: bool = True,
    finalized_request_reviewed: bool = True,
    risk_reviewed: bool = True,
    order_details_reviewed: bool = True,
    notional_limit_confirmation: bool = True,
    limit_order_confirmation: bool = True,
    day_time_in_force_confirmation: bool = True,
    no_short_confirmation: bool = True,
    no_crypto_confirmation: bool = True,
    no_options_confirmation: bool = True,
    no_margin_confirmation: bool = True,
    no_extended_hours_confirmation: bool = True,
    request_expired: bool = False,
    output_root: Path = REPORT_ROOT,
    write_artifacts: bool = True,
) -> ManualConfirmationResult:
    validation = validate_manual_confirmation_inputs(
        request=request,
        confirmer=confirmer,
        confirmation_status=confirmation_status,
        paper_only_confirmation=paper_only_confirmation,
        no_live_trading_confirmation=no_live_trading_confirmation,
        finalized_request_reviewed=finalized_request_reviewed,
        risk_reviewed=risk_reviewed,
        order_details_reviewed=order_details_reviewed,
        notional_limit_confirmation=notional_limit_confirmation,
        limit_order_confirmation=limit_order_confirmation,
        day_time_in_force_confirmation=day_time_in_force_confirmation,
        no_short_confirmation=no_short_confirmation,
        no_crypto_confirmation=no_crypto_confirmation,
        no_options_confirmation=no_options_confirmation,
        no_margin_confirmation=no_margin_confirmation,
        no_extended_hours_confirmation=no_extended_hours_confirmation,
        request_expired=request_expired,
    )
    if not validation.passed:
        status = MANUAL_EXECUTION_EXPIRED if request_expired else MANUAL_EXECUTION_INVALID
        return _confirmation_result(
            confirmation=None,
            validation=validation,
            request=request,
            confirmation_status=status,
            reason="; ".join(validation.violations),
            output_root=output_root,
            write_artifacts=write_artifacts,
        )

    assert request is not None
    confirmation = _build_manual_confirmation(
        request=request,
        confirmer=confirmer,
        confirmation_status=confirmation_status,
        confirmation_notes=confirmation_notes,
        paper_only_confirmation=paper_only_confirmation,
        no_live_trading_confirmation=no_live_trading_confirmation,
        finalized_request_reviewed=finalized_request_reviewed,
        risk_reviewed=risk_reviewed,
        order_details_reviewed=order_details_reviewed,
        notional_limit_confirmation=notional_limit_confirmation,
        limit_order_confirmation=limit_order_confirmation,
        day_time_in_force_confirmation=day_time_in_force_confirmation,
        no_short_confirmation=no_short_confirmation,
        no_crypto_confirmation=no_crypto_confirmation,
        no_options_confirmation=no_options_confirmation,
        no_margin_confirmation=no_margin_confirmation,
        no_extended_hours_confirmation=no_extended_hours_confirmation,
    )
    confirmation_validation = validate_manual_confirmation(confirmation)
    if not confirmation_validation.passed:
        return _confirmation_result(
            confirmation=confirmation,
            validation=confirmation_validation,
            request=request,
            confirmation_status=MANUAL_EXECUTION_INVALID,
            reason="; ".join(confirmation_validation.violations),
            output_root=output_root,
            write_artifacts=write_artifacts,
        )

    reason = (
        "Manual Execution Confirmation created for future Paper Send Preflight only."
        if confirmation_status == MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT
        else "Manual Execution Confirmation blocks progression."
    )
    return _confirmation_result(
        confirmation=confirmation,
        validation=confirmation_validation,
        request=request,
        confirmation_status=confirmation_status,
        reason=reason,
        output_root=output_root,
        write_artifacts=write_artifacts,
    )


def validate_manual_confirmation_inputs(
    *,
    request: FinalizedPaperOrderRequest | None,
    confirmer: str,
    confirmation_status: str = MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT,
    paper_only_confirmation: bool = True,
    no_live_trading_confirmation: bool = True,
    finalized_request_reviewed: bool = True,
    risk_reviewed: bool = True,
    order_details_reviewed: bool = True,
    notional_limit_confirmation: bool = True,
    limit_order_confirmation: bool = True,
    day_time_in_force_confirmation: bool = True,
    no_short_confirmation: bool = True,
    no_crypto_confirmation: bool = True,
    no_options_confirmation: bool = True,
    no_margin_confirmation: bool = True,
    no_extended_hours_confirmation: bool = True,
    request_expired: bool = False,
) -> ManualConfirmationValidation:
    violations: list[str] = []
    if request is None:
        violations.append("finalized request missing")
    else:
        if request.request_status != PAPER_ORDER_REQUEST_FINALIZED:
            violations.append("request status is not PAPER_ORDER_REQUEST_FINALIZED")
        if request.paper_trading_only is not True:
            violations.append("paper_trading_only=true is required")
        if request.live_trading_allowed is not False:
            violations.append("live_trading_allowed=false is required")
        if request.broker_execution_allowed is not False:
            violations.append("broker_execution_allowed=false is required")
        if request.manual_execution_confirmation_required is not True:
            violations.append("manual_execution_confirmation_required=true is required")
        for field_name, value in _required_request_references(request).items():
            if value in (None, ""):
                violations.append(f"missing {field_name}")
    if request_expired:
        violations.append("request expired")
    if not confirmer:
        violations.append("confirmer is required")
    if confirmation_status not in ALLOWED_CONFIRMATION_STATUSES:
        violations.append("confirmation status is not allowed")
    required_confirmations = {
        "paper_only_confirmation": paper_only_confirmation,
        "no_live_trading_confirmation": no_live_trading_confirmation,
        "finalized_request_reviewed": finalized_request_reviewed,
        "risk_reviewed": risk_reviewed,
        "order_details_reviewed": order_details_reviewed,
        "notional_limit_confirmation": notional_limit_confirmation,
        "limit_order_confirmation": limit_order_confirmation,
        "day_time_in_force_confirmation": day_time_in_force_confirmation,
        "no_short_confirmation": no_short_confirmation,
        "no_crypto_confirmation": no_crypto_confirmation,
        "no_options_confirmation": no_options_confirmation,
        "no_margin_confirmation": no_margin_confirmation,
        "no_extended_hours_confirmation": no_extended_hours_confirmation,
    }
    for field_name, value in required_confirmations.items():
        if value is not True:
            violations.append(f"{field_name} is required")
    if os.environ.get("PAPER_ORDER_EXECUTION_ENABLED", "").lower() == "true":
        violations.append("PAPER_ORDER_EXECUTION_ENABLED=true is blocked")
    return ManualConfirmationValidation("FAIL" if violations else "PASS", tuple(violations))


def validate_manual_confirmation(
    confirmation: ManualExecutionConfirmation | None,
) -> ManualConfirmationValidation:
    if confirmation is None:
        return ManualConfirmationValidation("FAIL", ("manual confirmation missing",))
    violations: list[str] = []
    required_values = {
        "manual_confirmation_id": confirmation.manual_confirmation_id,
        "paper_order_request_id": confirmation.paper_order_request_id,
        "candidate_id": confirmation.candidate_id,
        "review_id": confirmation.review_id,
        "confirmed_at": confirmation.confirmed_at,
        "confirmer": confirmation.confirmer,
        "confirmation_status": confirmation.confirmation_status,
    }
    for field_name, value in required_values.items():
        if value in (None, ""):
            violations.append(f"missing {field_name}")
    if confirmation.confirmation_status not in ALLOWED_CONFIRMATION_STATUSES:
        violations.append("confirmation status is not allowed")
    for field_name, value in _confirmation_checks(confirmation).items():
        if value is not True:
            violations.append(f"{field_name} must be true")
    if confirmation.broker_execution_allowed is not False:
        violations.append("broker_execution_allowed must be false")
    if confirmation.live_trading_allowed is not False:
        violations.append("live_trading_allowed must be false")
    if confirmation.paper_send_preflight_required is not True:
        violations.append("paper_send_preflight_required must be true")
    return ManualConfirmationValidation("FAIL" if violations else "PASS", tuple(violations))


def _build_manual_confirmation(
    *,
    request: FinalizedPaperOrderRequest,
    confirmer: str,
    confirmation_status: str,
    confirmation_notes: str,
    paper_only_confirmation: bool,
    no_live_trading_confirmation: bool,
    finalized_request_reviewed: bool,
    risk_reviewed: bool,
    order_details_reviewed: bool,
    notional_limit_confirmation: bool,
    limit_order_confirmation: bool,
    day_time_in_force_confirmation: bool,
    no_short_confirmation: bool,
    no_crypto_confirmation: bool,
    no_options_confirmation: bool,
    no_margin_confirmation: bool,
    no_extended_hours_confirmation: bool,
) -> ManualExecutionConfirmation:
    return ManualExecutionConfirmation(
        manual_confirmation_id=f"manual-confirmation-{request.paper_order_request_id}",
        paper_order_request_id=request.paper_order_request_id,
        candidate_id=request.candidate_id,
        review_id=request.review_id,
        confirmed_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        confirmer=confirmer,
        confirmation_status=confirmation_status,
        confirmation_notes=confirmation_notes,
        paper_only_confirmation=paper_only_confirmation,
        no_live_trading_confirmation=no_live_trading_confirmation,
        finalized_request_reviewed=finalized_request_reviewed,
        risk_reviewed=risk_reviewed,
        order_details_reviewed=order_details_reviewed,
        notional_limit_confirmation=notional_limit_confirmation,
        limit_order_confirmation=limit_order_confirmation,
        day_time_in_force_confirmation=day_time_in_force_confirmation,
        no_short_confirmation=no_short_confirmation,
        no_crypto_confirmation=no_crypto_confirmation,
        no_options_confirmation=no_options_confirmation,
        no_margin_confirmation=no_margin_confirmation,
        no_extended_hours_confirmation=no_extended_hours_confirmation,
        broker_execution_allowed=False,
        live_trading_allowed=False,
        paper_send_preflight_required=True,
    )


def _confirmation_result(
    *,
    confirmation: ManualExecutionConfirmation | None,
    validation: ManualConfirmationValidation,
    request: FinalizedPaperOrderRequest | None,
    confirmation_status: str,
    reason: str,
    output_root: Path,
    write_artifacts: bool,
) -> ManualConfirmationResult:
    report_path: Path | None = None
    journal_path: Path | None = None
    if write_artifacts:
        report_dir = _timestamped_report_dir(output_root)
        report_path = report_dir / REPORT_NAME
        journal_path = report_dir / JOURNAL_NAME
    result = ManualConfirmationResult(
        confirmation=confirmation,
        validation=validation,
        paper_order_request_id=request.paper_order_request_id if request else None,
        candidate_id=request.candidate_id if request else None,
        review_id=request.review_id if request else None,
        confirmation_status=confirmation_status,
        final_status=confirmation_status,
        reason=reason,
        report_path=report_path.as_posix() if report_path else None,
        journal_path=journal_path.as_posix() if journal_path else None,
    )
    if write_artifacts and report_path and journal_path:
        journal_path.write_text(json.dumps(_journal_payload(result), indent=2), encoding="utf-8")
        report_path.write_text(_render_manual_confirmation_report(result), encoding="utf-8")
    return result


def _required_request_references(request: FinalizedPaperOrderRequest) -> dict[str, str]:
    return {
        "human_review_reference": request.human_review_reference,
        "journal_reference": request.journal_reference,
        "strategy_evaluation_reference": request.strategy_evaluation_reference,
        "evaluation_gate_reference": request.evaluation_gate_reference,
        "negative_case_regression_reference": request.negative_case_regression_reference,
        "risk_reference": request.risk_reference,
    }


def _confirmation_checks(confirmation: ManualExecutionConfirmation) -> dict[str, bool]:
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


def _journal_payload(result: ManualConfirmationResult) -> dict[str, object]:
    confirmation = result.confirmation
    return {
        "manual_confirmation_id": (
            confirmation.manual_confirmation_id if confirmation else None
        ),
        "paper_order_request_id": result.paper_order_request_id,
        "candidate_id": result.candidate_id,
        "review_id": result.review_id,
        "confirmer": confirmation.confirmer if confirmation else None,
        "confirmation_status": result.confirmation_status,
        "confirmation_notes": confirmation.confirmation_notes if confirmation else None,
        "confirmations": _confirmation_checks(confirmation) if confirmation else {},
        "broker_execution_allowed": (
            confirmation.broker_execution_allowed if confirmation else False
        ),
        "live_trading_allowed": confirmation.live_trading_allowed if confirmation else False,
        "paper_send_preflight_required": (
            confirmation.paper_send_preflight_required if confirmation else False
        ),
        "final_status": result.final_status,
        "reason": result.reason,
        "paper_send_preflight_created": False,
        "order_sent": False,
        "broker_execution_readiness": False,
        "alpaca_order_api_called": False,
        "live_trading_assumption": False,
    }


def _render_manual_confirmation_report(result: ManualConfirmationResult) -> str:
    confirmation = result.confirmation
    return f"""# Manual Execution Confirmation

## Summary

- Manual confirmation id: {confirmation.manual_confirmation_id if confirmation else None}
- Paper order request id: {result.paper_order_request_id}
- Candidate id: {result.candidate_id}
- Review id: {result.review_id}
- Confirmer: {confirmation.confirmer if confirmation else None}
- Confirmation status: {result.confirmation_status}
- Confirmation notes: {confirmation.confirmation_notes if confirmation else None}
- Required confirmations: {json.dumps(_confirmation_checks(confirmation) if confirmation else {}, sort_keys=True)}
- broker_execution_allowed: {str(confirmation.broker_execution_allowed if confirmation else False).lower()}
- live_trading_allowed: {str(confirmation.live_trading_allowed if confirmation else False).lower()}
- paper_send_preflight_required: {str(confirmation.paper_send_preflight_required if confirmation else False).lower()}
- Final status: {result.final_status}
- Reason: {result.reason}

## Confirmation

```json
{json.dumps(confirmation.as_dict() if confirmation else None, indent=2)}
```

## Safety

Manual Execution Confirmation does not send orders.
Paper Send Preflight is still required later.
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


def _default_finalized_request() -> FinalizedPaperOrderRequest:
    candidate, review = _default_candidate_and_review()
    result = finalize_paper_order_request(candidate=candidate, review=review, write_artifacts=False)
    if result.request is None:
        raise RuntimeError("default finalized Paper Order Request could not be created")
    return result.request


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create an inert Manual Execution Confirmation artifact."
    )
    parser.add_argument("--confirmer", required=True)
    parser.add_argument(
        "--status",
        default=MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT,
        choices=sorted(ALLOWED_CONFIRMATION_STATUSES),
    )
    parser.add_argument("--notes", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = create_manual_execution_confirmation(
        request=_default_finalized_request(),
        confirmer=args.confirmer,
        confirmation_status=args.status,
        confirmation_notes=args.notes,
    )
    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(result.final_status)
        print(result.report_path)
    return 0 if result.validation.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
