from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from human_review_queue import (
    HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST,
    HumanReviewRecord,
    create_human_review_record,
)
from paper_order_request_candidate import (
    PAPER_ORDER_CANDIDATE_CREATED,
    PaperOrderRequestCandidate,
    create_paper_order_request_candidate,
)


REPORT_ROOT = Path("reports/finalized_paper_order_request")
REPORT_NAME = "FINALIZED_PAPER_ORDER_REQUEST.md"
JOURNAL_NAME = "FINALIZED_PAPER_ORDER_REQUEST_JOURNAL.json"

PAPER_ORDER_REQUEST_FINALIZED = "PAPER_ORDER_REQUEST_FINALIZED"
PAPER_ORDER_REQUEST_BLOCKED = "PAPER_ORDER_REQUEST_BLOCKED"
PAPER_ORDER_REQUEST_INVALID = "PAPER_ORDER_REQUEST_INVALID"
PAPER_ORDER_REQUEST_EXPIRED = "PAPER_ORDER_REQUEST_EXPIRED"
ALLOWED_REQUEST_STATUSES = {
    PAPER_ORDER_REQUEST_FINALIZED,
    PAPER_ORDER_REQUEST_BLOCKED,
    PAPER_ORDER_REQUEST_INVALID,
    PAPER_ORDER_REQUEST_EXPIRED,
}


@dataclass(frozen=True)
class FinalizedPaperOrderRequest:
    paper_order_request_id: str
    candidate_id: str
    review_id: str
    created_at: str
    symbol: str
    side: str
    order_type: str
    time_in_force: str
    notional: str
    quantity: str | None
    limit_price: str
    stop_loss: str
    target_1: str
    target_2: str | None
    thesis: str
    invalidation: str
    proposal_reference: str
    strategy_evaluation_reference: str
    evaluation_gate_reference: str
    negative_case_regression_reference: str
    risk_reference: str
    journal_reference: str
    human_review_reference: str
    paper_trading_only: bool
    manual_execution_confirmation_required: bool
    broker_execution_allowed: bool
    live_trading_allowed: bool
    request_status: str

    def as_dict(self) -> dict[str, object]:
        return {
            "paper_order_request_id": self.paper_order_request_id,
            "candidate_id": self.candidate_id,
            "review_id": self.review_id,
            "created_at": self.created_at,
            "symbol": self.symbol,
            "side": self.side,
            "order_type": self.order_type,
            "time_in_force": self.time_in_force,
            "notional": self.notional,
            "quantity": self.quantity,
            "limit_price": self.limit_price,
            "stop_loss": self.stop_loss,
            "target_1": self.target_1,
            "target_2": self.target_2,
            "thesis": self.thesis,
            "invalidation": self.invalidation,
            "proposal_reference": self.proposal_reference,
            "strategy_evaluation_reference": self.strategy_evaluation_reference,
            "evaluation_gate_reference": self.evaluation_gate_reference,
            "negative_case_regression_reference": self.negative_case_regression_reference,
            "risk_reference": self.risk_reference,
            "journal_reference": self.journal_reference,
            "human_review_reference": self.human_review_reference,
            "paper_trading_only": self.paper_trading_only,
            "manual_execution_confirmation_required": self.manual_execution_confirmation_required,
            "broker_execution_allowed": self.broker_execution_allowed,
            "live_trading_allowed": self.live_trading_allowed,
            "request_status": self.request_status,
        }


@dataclass(frozen=True)
class FinalizedRequestValidation:
    status: str
    violations: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def as_dict(self) -> dict[str, object]:
        return {"status": self.status, "violations": list(self.violations)}


@dataclass(frozen=True)
class FinalizationResult:
    request: FinalizedPaperOrderRequest | None
    validation: FinalizedRequestValidation
    candidate_id: str | None
    review_id: str | None
    request_status: str
    final_status: str
    reason: str
    report_path: str | None
    journal_path: str | None
    manual_execution_confirmation_created: bool = False
    order_sent: bool = False
    broker_execution_readiness: bool = False
    live_trading_assumption: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "request": self.request.as_dict() if self.request else None,
            "validation": self.validation.as_dict(),
            "candidate_id": self.candidate_id,
            "review_id": self.review_id,
            "request_status": self.request_status,
            "final_status": self.final_status,
            "reason": self.reason,
            "report_path": self.report_path,
            "journal_path": self.journal_path,
            "manual_execution_confirmation_created": self.manual_execution_confirmation_created,
            "order_sent": self.order_sent,
            "broker_execution_readiness": self.broker_execution_readiness,
            "live_trading_assumption": self.live_trading_assumption,
        }


def finalize_paper_order_request(
    *,
    candidate: PaperOrderRequestCandidate | None,
    review: HumanReviewRecord | None,
    candidate_expired: bool = False,
    review_expired: bool = False,
    output_root: Path = REPORT_ROOT,
    write_artifacts: bool = True,
) -> FinalizationResult:
    validation = validate_finalized_request_inputs(
        candidate=candidate,
        review=review,
        candidate_expired=candidate_expired,
        review_expired=review_expired,
    )
    if not validation.passed:
        status = (
            PAPER_ORDER_REQUEST_EXPIRED
            if candidate_expired or review_expired
            else PAPER_ORDER_REQUEST_BLOCKED
        )
        return _finalize_result(
            request=None,
            validation=validation,
            candidate=candidate,
            review=review,
            request_status=status,
            reason="; ".join(validation.violations),
            output_root=output_root,
            write_artifacts=write_artifacts,
        )

    assert candidate is not None
    assert review is not None
    request = _build_finalized_request(candidate, review)
    request_validation = validate_finalized_request(request)
    if not request_validation.passed:
        return _finalize_result(
            request=request,
            validation=request_validation,
            candidate=candidate,
            review=review,
            request_status=PAPER_ORDER_REQUEST_INVALID,
            reason="; ".join(request_validation.violations),
            output_root=output_root,
            write_artifacts=write_artifacts,
        )
    return _finalize_result(
        request=request,
        validation=request_validation,
        candidate=candidate,
        review=review,
        request_status=PAPER_ORDER_REQUEST_FINALIZED,
        reason="Finalized Paper Order Request created as an inert artifact only.",
        output_root=output_root,
        write_artifacts=write_artifacts,
    )


def validate_finalized_request_inputs(
    *,
    candidate: PaperOrderRequestCandidate | None,
    review: HumanReviewRecord | None,
    candidate_expired: bool = False,
    review_expired: bool = False,
) -> FinalizedRequestValidation:
    violations: list[str] = []
    if candidate is None:
        violations.append("candidate missing")
    else:
        if candidate.candidate_status != PAPER_ORDER_CANDIDATE_CREATED:
            violations.append("candidate status is not PAPER_ORDER_CANDIDATE_CREATED")
        if candidate.paper_trading_only is not True:
            violations.append("paper_trading_only=true is required")
        if candidate.human_approval_required is not True:
            violations.append("human_approval_required=true is required")
        if candidate.manual_execution_confirmation_required is not True:
            violations.append("manual_execution_confirmation_required=true is required")
        if candidate.broker_execution_allowed is not False:
            violations.append("broker_execution_allowed=true is blocked")
        if candidate.live_trading_allowed is not False:
            violations.append("live_trading_allowed=true is blocked")
    if review is None:
        violations.append("review missing")
    else:
        if review.review_status != HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST:
            violations.append("human review is not approved for paper request")
        if not review.reviewer:
            violations.append("reviewer is required")
        if review.paper_only_confirmation is not True:
            violations.append("paper_only_confirmation is required")
        if review.no_live_trading_confirmation is not True:
            violations.append("no_live_trading_confirmation is required")
        if review.risk_review_confirmation is not True:
            violations.append("risk_review_confirmation is required")
        if review.evaluation_review_confirmation is not True:
            violations.append("evaluation_review_confirmation is required")
        if review.negative_case_review_confirmation is not True:
            violations.append("negative_case_review_confirmation is required")
        if review.journal_review_confirmation is not True:
            violations.append("journal_review_confirmation is required")
    if candidate_expired:
        violations.append("candidate expired")
    if review_expired:
        violations.append("review expired")
    if os.environ.get("PAPER_ORDER_EXECUTION_ENABLED", "").lower() == "true":
        violations.append("PAPER_ORDER_EXECUTION_ENABLED=true is blocked")
    return FinalizedRequestValidation("FAIL" if violations else "PASS", tuple(violations))


def validate_finalized_request(
    request: FinalizedPaperOrderRequest | None,
) -> FinalizedRequestValidation:
    if request is None:
        return FinalizedRequestValidation("FAIL", ("request missing",))
    violations: list[str] = []
    required_values = {
        "paper_order_request_id": request.paper_order_request_id,
        "candidate_id": request.candidate_id,
        "review_id": request.review_id,
        "created_at": request.created_at,
        "symbol": request.symbol,
        "side": request.side,
        "order_type": request.order_type,
        "time_in_force": request.time_in_force,
        "notional": request.notional,
        "limit_price": request.limit_price,
        "stop_loss": request.stop_loss,
        "target_1": request.target_1,
        "thesis": request.thesis,
        "invalidation": request.invalidation,
        "proposal_reference": request.proposal_reference,
        "strategy_evaluation_reference": request.strategy_evaluation_reference,
        "evaluation_gate_reference": request.evaluation_gate_reference,
        "negative_case_regression_reference": request.negative_case_regression_reference,
        "risk_reference": request.risk_reference,
        "journal_reference": request.journal_reference,
        "human_review_reference": request.human_review_reference,
        "request_status": request.request_status,
    }
    for field_name, value in required_values.items():
        if value in (None, ""):
            violations.append(f"missing {field_name}")
    if request.request_status not in ALLOWED_REQUEST_STATUSES:
        violations.append("request status is not allowed")
    if request.paper_trading_only is not True:
        violations.append("paper_trading_only must be true")
    if request.manual_execution_confirmation_required is not True:
        violations.append("manual_execution_confirmation_required must be true")
    if request.broker_execution_allowed is not False:
        violations.append("broker_execution_allowed must be false")
    if request.live_trading_allowed is not False:
        violations.append("live_trading_allowed must be false")
    return FinalizedRequestValidation("FAIL" if violations else "PASS", tuple(violations))


def _build_finalized_request(
    candidate: PaperOrderRequestCandidate,
    review: HumanReviewRecord,
) -> FinalizedPaperOrderRequest:
    return FinalizedPaperOrderRequest(
        paper_order_request_id=f"finalized-{candidate.candidate_id}",
        candidate_id=candidate.candidate_id,
        review_id=review.review_id,
        created_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        symbol=candidate.symbol,
        side=candidate.proposed_side,
        order_type=candidate.proposed_order_type,
        time_in_force=candidate.proposed_time_in_force,
        notional=candidate.proposed_notional,
        quantity=candidate.proposed_quantity,
        limit_price=candidate.proposed_limit_price,
        stop_loss=candidate.stop_loss,
        target_1=candidate.target_1,
        target_2=candidate.target_2,
        thesis=candidate.thesis,
        invalidation=candidate.invalidation,
        proposal_reference=candidate.proposal_id,
        strategy_evaluation_reference=candidate.strategy_evaluation_reference,
        evaluation_gate_reference=candidate.evaluation_gate_reference,
        negative_case_regression_reference=candidate.negative_case_regression_reference,
        risk_reference=candidate.risk_dry_run_reference,
        journal_reference=candidate.journal_reference,
        human_review_reference=review.review_id,
        paper_trading_only=True,
        manual_execution_confirmation_required=True,
        broker_execution_allowed=False,
        live_trading_allowed=False,
        request_status=PAPER_ORDER_REQUEST_FINALIZED,
    )


def _finalize_result(
    *,
    request: FinalizedPaperOrderRequest | None,
    validation: FinalizedRequestValidation,
    candidate: PaperOrderRequestCandidate | None,
    review: HumanReviewRecord | None,
    request_status: str,
    reason: str,
    output_root: Path,
    write_artifacts: bool,
) -> FinalizationResult:
    report_path: Path | None = None
    journal_path: Path | None = None
    if write_artifacts:
        report_dir = _timestamped_report_dir(output_root)
        report_path = report_dir / REPORT_NAME
        journal_path = report_dir / JOURNAL_NAME
    result = FinalizationResult(
        request=request,
        validation=validation,
        candidate_id=candidate.candidate_id if candidate else None,
        review_id=review.review_id if review else None,
        request_status=request_status,
        final_status=request_status,
        reason=reason,
        report_path=report_path.as_posix() if report_path else None,
        journal_path=journal_path.as_posix() if journal_path else None,
    )
    if write_artifacts and report_path and journal_path:
        journal_path.write_text(json.dumps(_journal_payload(result), indent=2), encoding="utf-8")
        report_path.write_text(_render_finalized_request_report(result), encoding="utf-8")
    return result


def _journal_payload(result: FinalizationResult) -> dict[str, object]:
    request = result.request
    return {
        "paper_order_request_id": request.paper_order_request_id if request else None,
        "candidate_id": result.candidate_id,
        "review_id": result.review_id,
        "request_status": result.request_status,
        "human_review_status": HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST if request else None,
        "gate_references": _gate_references(request),
        "paper_trading_only": request.paper_trading_only if request else False,
        "manual_execution_confirmation_required": (
            request.manual_execution_confirmation_required if request else False
        ),
        "broker_execution_allowed": request.broker_execution_allowed if request else False,
        "live_trading_allowed": request.live_trading_allowed if request else False,
        "final_status": result.final_status,
        "reason": result.reason,
        "manual_execution_confirmation_created": False,
        "order_sent": False,
        "broker_execution_readiness": False,
    }


def _gate_references(request: FinalizedPaperOrderRequest | None) -> dict[str, str]:
    if request is None:
        return {}
    return {
        "strategy_evaluation_reference": request.strategy_evaluation_reference,
        "evaluation_gate_reference": request.evaluation_gate_reference,
        "negative_case_regression_reference": request.negative_case_regression_reference,
        "risk_reference": request.risk_reference,
        "journal_reference": request.journal_reference,
        "human_review_reference": request.human_review_reference,
    }


def _render_finalized_request_report(result: FinalizationResult) -> str:
    request = result.request
    return f"""# Finalized Paper Order Request

## Summary

- Paper order request id: {request.paper_order_request_id if request else None}
- Candidate id: {result.candidate_id}
- Review id: {result.review_id}
- Symbol: {request.symbol if request else None}
- Side: {request.side if request else None}
- Order type: {request.order_type if request else None}
- Time in force: {request.time_in_force if request else None}
- Notional: {request.notional if request else None}
- Limit price: {request.limit_price if request else None}
- Request status: {result.request_status}
- Gate references: {json.dumps(_gate_references(request), sort_keys=True)}
- Human review reference: {request.human_review_reference if request else None}
- paper_trading_only: {str(request.paper_trading_only if request else False).lower()}
- manual_execution_confirmation_required: {str(request.manual_execution_confirmation_required if request else False).lower()}
- broker_execution_allowed: {str(request.broker_execution_allowed if request else False).lower()}
- live_trading_allowed: {str(request.live_trading_allowed if request else False).lower()}
- Final status: {result.final_status}
- Reason: {result.reason}

## Request

```json
{json.dumps(request.as_dict() if request else None, indent=2)}
```

## Safety

Finalized Paper Order Request is not broker execution.
Manual Execution Confirmation is still required later.
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


def _default_candidate_and_review() -> tuple[PaperOrderRequestCandidate, HumanReviewRecord]:
    candidate_result = create_paper_order_request_candidate(symbols=["SIM"], write_artifacts=False)
    if candidate_result.candidate is None:
        raise RuntimeError("default candidate could not be created")
    review_result = create_human_review_record(
        candidate=candidate_result.candidate,
        reviewer="human-reviewer",
        review_status=HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST,
        review_notes="Reviewed candidate for future request finalization only.",
        write_artifacts=False,
    )
    if review_result.record is None:
        raise RuntimeError("default review could not be created")
    return candidate_result.candidate, review_result.record


def main() -> int:
    parser = argparse.ArgumentParser(description="Finalize an inert Paper Order Request artifact.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    candidate, review = _default_candidate_and_review()
    result = finalize_paper_order_request(candidate=candidate, review=review)
    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(result.final_status)
        print(result.report_path)
    return 0 if result.final_status == PAPER_ORDER_REQUEST_FINALIZED else 1


if __name__ == "__main__":
    raise SystemExit(main())
