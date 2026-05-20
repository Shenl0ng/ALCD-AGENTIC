from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Mapping

from paper_trade import (
    RISK_APPROVED,
    RISK_REJECTED,
    PaperTradeProposal,
    RiskEvaluation,
    deterministic_valid_proposal,
    evaluate_risk,
    validate_proposal,
)
from alpaca_paper_account import default_mock_snapshot
from evaluation_first_gate import EvaluationGateResult, evaluation_gate_passed


HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
HUMAN_APPROVED_FOR_PAPER_ONLY = "HUMAN_APPROVED_FOR_PAPER_ONLY"
HUMAN_REJECTED = "HUMAN_REJECTED"
HUMAN_EXPIRED = "HUMAN_EXPIRED"
HUMAN_APPROVAL_INVALID = "HUMAN_APPROVAL_INVALID"

VALID_APPROVAL_STATES = {
    HUMAN_REVIEW_REQUIRED,
    HUMAN_APPROVED_FOR_PAPER_ONLY,
    HUMAN_REJECTED,
    HUMAN_EXPIRED,
    HUMAN_APPROVAL_INVALID,
}

JOURNAL_EVENTS = {
    "proposal_created",
    "proposal_rejected",
    "risk_approved",
    "risk_rejected",
    "human_review_required",
    "human_approved_for_paper_only",
    "human_rejected",
    "execution_blocked",
    "final_decision",
    "paper_order_request_created",
    "paper_order_request_blocked",
    "paper_order_request_invalid",
    "paper_order_send_attempted",
    "paper_order_send_blocked",
    "paper_order_send_submitted",
    "paper_order_send_broker_rejected",
    "paper_order_send_adapter_rejected",
    "paper_order_send_error",
    "paper_order_reconciliation",
    "evaluation_gate_passed",
    "evaluation_gate_blocked",
}


@dataclass(frozen=True)
class ApprovalRecord:
    approval_id: str | None
    proposal_id: str | None
    created_at: str | None
    reviewed_at: str | None
    reviewer: str | None
    approval_state: str
    approval_notes: str
    paper_only_confirmation: bool
    risk_approval_reference: str | None
    journal_ready_confirmation: bool
    adlc_compliance_reference: str | None
    live_trading_authorized: bool = False
    bypass_risk_manager: bool = False
    bypass_journal_agent: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "approval_id": self.approval_id,
            "proposal_id": self.proposal_id,
            "created_at": self.created_at,
            "reviewed_at": self.reviewed_at,
            "reviewer": self.reviewer,
            "approval_state": self.approval_state,
            "approval_notes": self.approval_notes,
            "paper_only_confirmation": self.paper_only_confirmation,
            "risk_approval_reference": self.risk_approval_reference,
            "journal_ready_confirmation": self.journal_ready_confirmation,
            "adlc_compliance_reference": self.adlc_compliance_reference,
            "live_trading_authorized": self.live_trading_authorized,
            "bypass_risk_manager": self.bypass_risk_manager,
            "bypass_journal_agent": self.bypass_journal_agent,
        }


@dataclass(frozen=True)
class ApprovalValidation:
    status: str
    violations: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def as_dict(self) -> dict[str, object]:
        return {"status": self.status, "violations": list(self.violations)}


@dataclass(frozen=True)
class JournalEntry:
    timestamp: str
    routine_name: str
    proposal_id: str | None
    event_type: str
    risk_status: str
    human_approval_status: str
    gatekeeper_status: str
    adlc_status: str
    paper_trading_confirmation: bool
    reason_for_final_decision: str
    lessons_or_notes: str

    def as_dict(self) -> dict[str, object]:
        return {
            "timestamp": self.timestamp,
            "routine_name": self.routine_name,
            "proposal_id": self.proposal_id,
            "event_type": self.event_type,
            "risk_status": self.risk_status,
            "human_approval_status": self.human_approval_status,
            "gatekeeper_status": self.gatekeeper_status,
            "adlc_status": self.adlc_status,
            "paper_trading_confirmation": self.paper_trading_confirmation,
            "reason_for_final_decision": self.reason_for_final_decision,
            "lessons_or_notes": self.lessons_or_notes,
        }


def enter_human_review(
    proposal: PaperTradeProposal,
    risk_evaluation: RiskEvaluation,
    evaluation_gate: EvaluationGateResult | None = None,
) -> ApprovalRecord:
    validation = validate_proposal(proposal)
    if (
        validation.passed
        and risk_evaluation.decision == RISK_APPROVED
        and evaluation_gate_passed(evaluation_gate)
        and proposal.paper_trading_only
        and proposal.human_approval_required is True
        and proposal.journal_ready
        and proposal.adlc_compliance_status == "PASS"
    ):
        return ApprovalRecord(
            approval_id=f"approval-{proposal.proposal_id}",
            proposal_id=proposal.proposal_id,
            created_at="2026-05-19T13:32:00+00:00",
            reviewed_at=None,
            reviewer=None,
            approval_state=HUMAN_REVIEW_REQUIRED,
            approval_notes="Human review required before any paper-only gate status.",
            paper_only_confirmation=True,
            risk_approval_reference=risk_evaluation.decision,
            journal_ready_confirmation=proposal.journal_ready,
            adlc_compliance_reference=proposal.adlc_compliance_status,
        )
    return ApprovalRecord(
        approval_id=None,
        proposal_id=proposal.proposal_id,
        created_at="2026-05-19T13:32:00+00:00",
        reviewed_at=None,
        reviewer=None,
        approval_state=HUMAN_APPROVAL_INVALID,
        approval_notes="Proposal cannot enter human review.",
        paper_only_confirmation=proposal.paper_trading_only,
        risk_approval_reference=risk_evaluation.decision,
        journal_ready_confirmation=proposal.journal_ready,
        adlc_compliance_reference=proposal.adlc_compliance_status,
    )


def deterministic_human_approval(
    proposal: PaperTradeProposal,
    state: str = HUMAN_APPROVED_FOR_PAPER_ONLY,
    reviewer: str | None = "human-reviewer",
) -> ApprovalRecord:
    return ApprovalRecord(
        approval_id=f"approval-{proposal.proposal_id}",
        proposal_id=proposal.proposal_id,
        created_at="2026-05-19T13:32:00+00:00",
        reviewed_at="2026-05-19T13:33:00+00:00",
        reviewer=reviewer,
        approval_state=state,
        approval_notes="Deterministic human approval fixture for paper-only review.",
        paper_only_confirmation=proposal.paper_trading_only,
        risk_approval_reference=RISK_APPROVED,
        journal_ready_confirmation=proposal.journal_ready,
        adlc_compliance_reference=proposal.adlc_compliance_status,
    )


def validate_approval(
    proposal: PaperTradeProposal,
    risk_evaluation: RiskEvaluation,
    approval: ApprovalRecord,
) -> ApprovalValidation:
    violations: list[str] = []
    proposal_validation = validate_proposal(proposal)

    if risk_evaluation.decision != RISK_APPROVED:
        violations.append("proposal is not risk-approved")
    if not proposal.paper_trading_only or not approval.paper_only_confirmation:
        violations.append("proposal is not paper-only")
    if not proposal.journal_ready or not approval.journal_ready_confirmation:
        violations.append("journal_ready is false")
    if proposal.adlc_compliance_status != "PASS" or approval.adlc_compliance_reference != "PASS":
        violations.append("ADLC compliance is not PASS")
    if not approval.paper_only_confirmation:
        violations.append("paper_only_confirmation is missing")
    if not approval.reviewer:
        violations.append("reviewer is missing")
    if approval.approval_state not in VALID_APPROVAL_STATES:
        violations.append("approval_state is not valid")
    if approval.live_trading_authorized:
        violations.append("approval attempts to authorize live trading")
    if approval.bypass_risk_manager:
        violations.append("approval attempts to bypass Risk Manager")
    if approval.bypass_journal_agent:
        violations.append("approval attempts to bypass Journal Agent")
    if not proposal_validation.passed:
        violations.extend(proposal_validation.violations)

    return ApprovalValidation("FAIL" if violations else "PASS", tuple(dict.fromkeys(violations)))


def commit_journal_entry(
    *,
    proposal: PaperTradeProposal | None,
    risk_status: str,
    human_approval_status: str,
    gatekeeper_status: str,
    event_type: str,
    reason_for_final_decision: str,
    lessons_or_notes: str,
    routine_name: str = "market_open",
    adlc_status: str = "PASS",
) -> JournalEntry:
    if event_type not in JOURNAL_EVENTS:
        raise ValueError(f"Unsupported journal event: {event_type}")
    return JournalEntry(
        timestamp="2026-05-19T13:34:00+00:00",
        routine_name=routine_name,
        proposal_id=proposal.proposal_id if proposal else None,
        event_type=event_type,
        risk_status=risk_status,
        human_approval_status=human_approval_status,
        gatekeeper_status=gatekeeper_status,
        adlc_status=adlc_status,
        paper_trading_confirmation=bool(proposal and proposal.paper_trading_only),
        reason_for_final_decision=reason_for_final_decision,
        lessons_or_notes=lessons_or_notes,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate deterministic human approval flow.")
    parser.add_argument("--reject", action="store_true")
    args = parser.parse_args()

    proposal = deterministic_valid_proposal()
    risk = evaluate_risk(proposal, default_mock_snapshot())
    approval = deterministic_human_approval(
        proposal,
        HUMAN_REJECTED if args.reject else HUMAN_APPROVED_FOR_PAPER_ONLY,
    )
    validation = validate_approval(proposal, risk, approval)
    journal = commit_journal_entry(
        proposal=proposal,
        risk_status=risk.decision,
        human_approval_status=approval.approval_state,
        gatekeeper_status="EXECUTION_BLOCKED",
        event_type="human_rejected" if args.reject else "human_approved_for_paper_only",
        reason_for_final_decision="Journal commit only; no order execution.",
        lessons_or_notes="Human approval does not execute or bypass gates.",
    )
    print(
        json.dumps(
            {
                "approval": approval.as_dict(),
                "validation": validation.as_dict(),
                "journal_entry": journal.as_dict(),
            },
            indent=2,
        )
    )
    return 0 if validation.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
