from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from paper_order_request_candidate import (
    PAPER_ORDER_CANDIDATE_CREATED,
    PaperOrderRequestCandidate,
    create_paper_order_request_candidate,
)


REPORT_ROOT = Path("reports/human_review_queue")
REPORT_NAME = "HUMAN_REVIEW_RECORD.md"
JOURNAL_NAME = "HUMAN_REVIEW_JOURNAL.json"

HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST = "HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST"
HUMAN_REVIEW_REJECTED = "HUMAN_REVIEW_REJECTED"
HUMAN_REVIEW_NEEDS_MORE_INFORMATION = "HUMAN_REVIEW_NEEDS_MORE_INFORMATION"
HUMAN_REVIEW_EXPIRED = "HUMAN_REVIEW_EXPIRED"
HUMAN_REVIEW_INVALID = "HUMAN_REVIEW_INVALID"
HUMAN_REVIEW_BLOCKED = "HUMAN_REVIEW_BLOCKED"

ALLOWED_REVIEW_STATUSES = {
    HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST,
    HUMAN_REVIEW_REJECTED,
    HUMAN_REVIEW_NEEDS_MORE_INFORMATION,
    HUMAN_REVIEW_EXPIRED,
    HUMAN_REVIEW_INVALID,
}


@dataclass(frozen=True)
class HumanReviewQueue:
    queue_name: str = "human_review_queue"
    accepts: str = "Paper Order Request Candidates"
    finalized_paper_order_request_created: bool = False
    manual_execution_confirmation_created: bool = False
    order_sent: bool = False
    broker_execution_readiness: bool = False


@dataclass(frozen=True)
class HumanReviewRecord:
    review_id: str
    candidate_id: str
    reviewed_at: str
    reviewer: str
    review_status: str
    review_notes: str
    paper_only_confirmation: bool
    no_live_trading_confirmation: bool
    risk_review_confirmation: bool
    evaluation_review_confirmation: bool
    negative_case_review_confirmation: bool
    journal_review_confirmation: bool
    requested_changes: str | None = None
    expiration_at: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "review_id": self.review_id,
            "candidate_id": self.candidate_id,
            "reviewed_at": self.reviewed_at,
            "reviewer": self.reviewer,
            "review_status": self.review_status,
            "review_notes": self.review_notes,
            "paper_only_confirmation": self.paper_only_confirmation,
            "no_live_trading_confirmation": self.no_live_trading_confirmation,
            "risk_review_confirmation": self.risk_review_confirmation,
            "evaluation_review_confirmation": self.evaluation_review_confirmation,
            "negative_case_review_confirmation": self.negative_case_review_confirmation,
            "journal_review_confirmation": self.journal_review_confirmation,
            "requested_changes": self.requested_changes,
            "expiration_at": self.expiration_at,
        }


@dataclass(frozen=True)
class HumanReviewValidation:
    status: str
    violations: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def as_dict(self) -> dict[str, object]:
        return {"status": self.status, "violations": list(self.violations)}


@dataclass(frozen=True)
class HumanReviewResult:
    queue: HumanReviewQueue
    record: HumanReviewRecord | None
    validation: HumanReviewValidation
    candidate_id: str | None
    reviewer: str | None
    review_status: str
    review_notes: str
    gate_references: dict[str, str]
    risk_review_confirmation: bool
    evaluation_review_confirmation: bool
    negative_case_review_confirmation: bool
    journal_review_confirmation: bool
    paper_only_confirmation: bool
    no_live_trading_confirmation: bool
    final_status: str
    reason: str
    report_path: str | None
    journal_path: str | None
    finalized_paper_order_request_created: bool = False
    manual_execution_confirmation_created: bool = False
    order_sent: bool = False
    broker_execution_readiness: bool = False
    live_trading_assumption: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "queue": self.queue.__dict__,
            "record": self.record.as_dict() if self.record else None,
            "validation": self.validation.as_dict(),
            "candidate_id": self.candidate_id,
            "reviewer": self.reviewer,
            "review_status": self.review_status,
            "review_notes": self.review_notes,
            "gate_references": self.gate_references,
            "risk_review_confirmation": self.risk_review_confirmation,
            "evaluation_review_confirmation": self.evaluation_review_confirmation,
            "negative_case_review_confirmation": self.negative_case_review_confirmation,
            "journal_review_confirmation": self.journal_review_confirmation,
            "paper_only_confirmation": self.paper_only_confirmation,
            "no_live_trading_confirmation": self.no_live_trading_confirmation,
            "final_status": self.final_status,
            "reason": self.reason,
            "report_path": self.report_path,
            "journal_path": self.journal_path,
            "finalized_paper_order_request_created": self.finalized_paper_order_request_created,
            "manual_execution_confirmation_created": self.manual_execution_confirmation_created,
            "order_sent": self.order_sent,
            "broker_execution_readiness": self.broker_execution_readiness,
            "live_trading_assumption": self.live_trading_assumption,
        }


def create_human_review_record(
    *,
    candidate: PaperOrderRequestCandidate | None,
    reviewer: str | None,
    review_status: str,
    review_notes: str,
    paper_only_confirmation: bool = True,
    no_live_trading_confirmation: bool = True,
    risk_review_confirmation: bool = True,
    evaluation_review_confirmation: bool = True,
    negative_case_review_confirmation: bool = True,
    journal_review_confirmation: bool = True,
    requested_changes: str | None = None,
    expiration_at: str | None = None,
    candidate_expired: bool = False,
    output_root: Path = REPORT_ROOT,
    write_artifacts: bool = True,
) -> HumanReviewResult:
    validation = validate_review(
        candidate=candidate,
        reviewer=reviewer,
        review_status=review_status,
        paper_only_confirmation=paper_only_confirmation,
        no_live_trading_confirmation=no_live_trading_confirmation,
        risk_review_confirmation=risk_review_confirmation,
        evaluation_review_confirmation=evaluation_review_confirmation,
        negative_case_review_confirmation=negative_case_review_confirmation,
        journal_review_confirmation=journal_review_confirmation,
        candidate_expired=candidate_expired,
    )
    if not validation.passed:
        return _finalize_result(
            candidate=candidate,
            record=None,
            validation=validation,
            reviewer=reviewer,
            review_status=HUMAN_REVIEW_BLOCKED,
            review_notes=review_notes,
            paper_only_confirmation=paper_only_confirmation,
            no_live_trading_confirmation=no_live_trading_confirmation,
            risk_review_confirmation=risk_review_confirmation,
            evaluation_review_confirmation=evaluation_review_confirmation,
            negative_case_review_confirmation=negative_case_review_confirmation,
            journal_review_confirmation=journal_review_confirmation,
            final_status=HUMAN_REVIEW_BLOCKED,
            reason="; ".join(validation.violations),
            output_root=output_root,
            write_artifacts=write_artifacts,
        )

    assert candidate is not None
    assert reviewer is not None
    record = HumanReviewRecord(
        review_id=f"review-{candidate.candidate_id}",
        candidate_id=candidate.candidate_id,
        reviewed_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        reviewer=reviewer,
        review_status=review_status,
        review_notes=review_notes,
        paper_only_confirmation=paper_only_confirmation,
        no_live_trading_confirmation=no_live_trading_confirmation,
        risk_review_confirmation=risk_review_confirmation,
        evaluation_review_confirmation=evaluation_review_confirmation,
        negative_case_review_confirmation=negative_case_review_confirmation,
        journal_review_confirmation=journal_review_confirmation,
        requested_changes=requested_changes,
        expiration_at=expiration_at,
    )
    return _finalize_result(
        candidate=candidate,
        record=record,
        validation=validation,
        reviewer=reviewer,
        review_status=review_status,
        review_notes=review_notes,
        paper_only_confirmation=paper_only_confirmation,
        no_live_trading_confirmation=no_live_trading_confirmation,
        risk_review_confirmation=risk_review_confirmation,
        evaluation_review_confirmation=evaluation_review_confirmation,
        negative_case_review_confirmation=negative_case_review_confirmation,
        journal_review_confirmation=journal_review_confirmation,
        final_status=review_status,
        reason=_status_reason(review_status),
        output_root=output_root,
        write_artifacts=write_artifacts,
    )


def validate_review(
    *,
    candidate: PaperOrderRequestCandidate | None,
    reviewer: str | None,
    review_status: str,
    paper_only_confirmation: bool,
    no_live_trading_confirmation: bool,
    risk_review_confirmation: bool,
    evaluation_review_confirmation: bool,
    negative_case_review_confirmation: bool,
    journal_review_confirmation: bool,
    candidate_expired: bool = False,
) -> HumanReviewValidation:
    violations: list[str] = []
    if candidate is None:
        violations.append("candidate missing")
    else:
        if candidate.candidate_status != PAPER_ORDER_CANDIDATE_CREATED:
            violations.append("candidate status is not PAPER_ORDER_CANDIDATE_CREATED")
        if candidate.broker_execution_allowed is not False:
            violations.append("broker_execution_allowed=true is blocked")
        if candidate.live_trading_allowed is not False:
            violations.append("live_trading_allowed=true is blocked")
        if candidate.human_approval_required is not True:
            violations.append("human_approval_required=true is required")
        if candidate.manual_execution_confirmation_required is not True:
            violations.append("manual_execution_confirmation_required=true is required")
    if candidate_expired:
        violations.append("candidate expired")
    if not reviewer:
        violations.append("reviewer is required")
    if review_status not in ALLOWED_REVIEW_STATUSES:
        violations.append("review status is not allowed")
    if paper_only_confirmation is not True:
        violations.append("paper_only_confirmation is required")
    if no_live_trading_confirmation is not True:
        violations.append("no_live_trading_confirmation is required")
    if risk_review_confirmation is not True:
        violations.append("risk_review_confirmation is required")
    if evaluation_review_confirmation is not True:
        violations.append("evaluation_review_confirmation is required")
    if negative_case_review_confirmation is not True:
        violations.append("negative_case_review_confirmation is required")
    if journal_review_confirmation is not True:
        violations.append("journal_review_confirmation is required")
    if os.environ.get("PAPER_ORDER_EXECUTION_ENABLED", "").lower() == "true":
        violations.append("PAPER_ORDER_EXECUTION_ENABLED=true is blocked")
    return HumanReviewValidation("FAIL" if violations else "PASS", tuple(violations))


def _finalize_result(
    *,
    candidate: PaperOrderRequestCandidate | None,
    record: HumanReviewRecord | None,
    validation: HumanReviewValidation,
    reviewer: str | None,
    review_status: str,
    review_notes: str,
    paper_only_confirmation: bool,
    no_live_trading_confirmation: bool,
    risk_review_confirmation: bool,
    evaluation_review_confirmation: bool,
    negative_case_review_confirmation: bool,
    journal_review_confirmation: bool,
    final_status: str,
    reason: str,
    output_root: Path,
    write_artifacts: bool,
) -> HumanReviewResult:
    report_path: Path | None = None
    journal_path: Path | None = None
    if write_artifacts:
        report_dir = _timestamped_report_dir(output_root)
        report_path = report_dir / REPORT_NAME
        journal_path = report_dir / JOURNAL_NAME
    result = HumanReviewResult(
        queue=HumanReviewQueue(),
        record=record,
        validation=validation,
        candidate_id=candidate.candidate_id if candidate else None,
        reviewer=reviewer,
        review_status=review_status,
        review_notes=review_notes,
        gate_references=_gate_references(candidate),
        risk_review_confirmation=risk_review_confirmation,
        evaluation_review_confirmation=evaluation_review_confirmation,
        negative_case_review_confirmation=negative_case_review_confirmation,
        journal_review_confirmation=journal_review_confirmation,
        paper_only_confirmation=paper_only_confirmation,
        no_live_trading_confirmation=no_live_trading_confirmation,
        final_status=final_status,
        reason=reason,
        report_path=report_path.as_posix() if report_path else None,
        journal_path=journal_path.as_posix() if journal_path else None,
    )
    if write_artifacts and report_path and journal_path:
        journal_path.write_text(json.dumps(_journal_payload(result), indent=2), encoding="utf-8")
        report_path.write_text(_render_review_report(result), encoding="utf-8")
    return result


def _gate_references(candidate: PaperOrderRequestCandidate | None) -> dict[str, str]:
    if candidate is None:
        return {}
    return {
        "strategy_evaluation_reference": candidate.strategy_evaluation_reference,
        "evaluation_gate_reference": candidate.evaluation_gate_reference,
        "negative_case_regression_reference": candidate.negative_case_regression_reference,
        "risk_dry_run_reference": candidate.risk_dry_run_reference,
        "journal_reference": candidate.journal_reference,
    }


def _status_reason(review_status: str) -> str:
    if review_status == HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST:
        return "Human reviewed candidate for future Paper Order Request finalization only."
    if review_status == HUMAN_REVIEW_REJECTED:
        return "Human rejected candidate."
    if review_status == HUMAN_REVIEW_NEEDS_MORE_INFORMATION:
        return "Human requested more information."
    if review_status == HUMAN_REVIEW_EXPIRED:
        return "Human review expired."
    if review_status == HUMAN_REVIEW_INVALID:
        return "Human review marked invalid."
    return "Human review blocked."


def _journal_payload(result: HumanReviewResult) -> dict[str, object]:
    return {
        "candidate_id": result.candidate_id,
        "review_id": result.record.review_id if result.record else None,
        "reviewer": result.reviewer,
        "review_status": result.review_status,
        "review_notes": result.review_notes,
        "paper_only_confirmation": result.paper_only_confirmation,
        "no_live_trading_confirmation": result.no_live_trading_confirmation,
        "risk_review_confirmation": result.risk_review_confirmation,
        "evaluation_review_confirmation": result.evaluation_review_confirmation,
        "negative_case_review_confirmation": result.negative_case_review_confirmation,
        "journal_review_confirmation": result.journal_review_confirmation,
        "final_status": result.final_status,
        "reason": result.reason,
        "finalized_paper_order_request_created": False,
        "manual_execution_confirmation_created": False,
        "order_sent": False,
        "broker_execution_readiness": False,
    }


def _render_review_report(result: HumanReviewResult) -> str:
    return f"""# Human Review Record

## Summary

- Candidate id: {result.candidate_id}
- Reviewer: {result.reviewer}
- Review status: {result.review_status}
- Review notes: {result.review_notes}
- Gate references: {json.dumps(result.gate_references, sort_keys=True)}
- Risk review confirmation: {str(result.risk_review_confirmation).lower()}
- Evaluation review confirmation: {str(result.evaluation_review_confirmation).lower()}
- Negative-case review confirmation: {str(result.negative_case_review_confirmation).lower()}
- Journal review confirmation: {str(result.journal_review_confirmation).lower()}
- Paper-only confirmation: {str(result.paper_only_confirmation).lower()}
- No-live-trading confirmation: {str(result.no_live_trading_confirmation).lower()}
- Final status: {result.final_status}
- Reason: {result.reason}

## Review Record

```json
{json.dumps(result.record.as_dict() if result.record else None, indent=2)}
```

## Safety

Human review does not authorize order sending.
Manual Execution Confirmation is still required later.
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


def _default_candidate() -> PaperOrderRequestCandidate:
    result = create_paper_order_request_candidate(symbols=["SIM"], write_artifacts=False)
    if result.candidate is None:
        raise RuntimeError("default candidate could not be created")
    return result.candidate


def main() -> int:
    parser = argparse.ArgumentParser(description="Record a Human Review Queue decision.")
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--status", choices=sorted(ALLOWED_REVIEW_STATUSES), required=True)
    parser.add_argument("--notes", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = create_human_review_record(
        candidate=_default_candidate(),
        reviewer=args.reviewer,
        review_status=args.status,
        review_notes=args.notes,
    )
    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(result.final_status)
        print(result.report_path)
    return 0 if result.validation.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
