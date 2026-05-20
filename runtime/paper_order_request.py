from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Iterable

from alpaca_paper_account import default_mock_snapshot
from evaluation_first_gate import (
    EVALUATION_GATE_PASSED,
    EvaluationGateResult,
    evaluate_gate,
    evaluation_gate_journal_entry,
    evaluation_gate_passed,
)
from human_approval import (
    HUMAN_APPROVED_FOR_PAPER_ONLY,
    ApprovalRecord,
    JournalEntry,
    commit_journal_entry,
    deterministic_human_approval,
    validate_approval,
)
from paper_trade import (
    RISK_APPROVED,
    PaperTradeProposal,
    RiskEvaluation,
    deterministic_valid_proposal,
    evaluate_risk,
    validate_proposal,
)
from strategy_evaluation_harness import StrategyEvaluationInput, evaluate_strategy


PAPER_ORDER_REQUEST_CREATED = "PAPER_ORDER_REQUEST_CREATED"
PAPER_ORDER_REQUEST_BLOCKED = "PAPER_ORDER_REQUEST_BLOCKED"
PAPER_ORDER_REQUEST_INVALID = "PAPER_ORDER_REQUEST_INVALID"
PAPER_ORDER_REQUEST_EXPIRED = "PAPER_ORDER_REQUEST_EXPIRED"

READY_FOR_PAPER_ORDER_REQUEST = "READY_FOR_PAPER_ORDER_REQUEST"
EXECUTION_BLOCKED = "EXECUTION_BLOCKED"

FORBIDDEN_GATEKEEPER_OUTPUTS = {
    "ORDER_PLACED",
    "BUY",
    "SELL",
    "EXECUTED",
    "SENT_TO_BROKER",
    "LIVE_APPROVED",
}


@dataclass(frozen=True)
class PaperOrderRequest:
    paper_order_request_id: str | None
    proposal_id: str | None
    approval_id: str | None
    journal_entry_id: str | None
    created_at: str | None
    expires_at: str | None
    symbol: str | None
    side: str | None
    order_intent: str | None
    quantity: str | None
    notional: str | None
    order_type: str | None
    time_in_force: str | None
    proposed_entry: str | None
    stop_loss: str | None
    target_1: str | None
    target_2: str | None
    max_loss_amount: str | None
    max_loss_pct_equity: str | None
    paper_trading_only: bool
    broker_execution_allowed: bool
    live_trading_allowed: bool
    risk_approval_reference: str | None
    human_approval_reference: str | None
    journal_commit_reference: str | None
    adlc_compliance_reference: str | None
    evaluation_gate_reference: str | None
    gatekeeper_status: str
    final_status: str

    def as_dict(self) -> dict[str, object]:
        return {
            "paper_order_request_id": self.paper_order_request_id,
            "proposal_id": self.proposal_id,
            "approval_id": self.approval_id,
            "journal_entry_id": self.journal_entry_id,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "symbol": self.symbol,
            "side": self.side,
            "order_intent": self.order_intent,
            "quantity": self.quantity,
            "notional": self.notional,
            "order_type": self.order_type,
            "time_in_force": self.time_in_force,
            "proposed_entry": self.proposed_entry,
            "stop_loss": self.stop_loss,
            "target_1": self.target_1,
            "target_2": self.target_2,
            "max_loss_amount": self.max_loss_amount,
            "max_loss_pct_equity": self.max_loss_pct_equity,
            "paper_trading_only": self.paper_trading_only,
            "broker_execution_allowed": self.broker_execution_allowed,
            "live_trading_allowed": self.live_trading_allowed,
            "risk_approval_reference": self.risk_approval_reference,
            "human_approval_reference": self.human_approval_reference,
            "journal_commit_reference": self.journal_commit_reference,
            "adlc_compliance_reference": self.adlc_compliance_reference,
            "evaluation_gate_reference": self.evaluation_gate_reference,
            "gatekeeper_status": self.gatekeeper_status,
            "final_status": self.final_status,
        }


@dataclass(frozen=True)
class PaperOrderRequestValidation:
    status: str
    violations: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def as_dict(self) -> dict[str, object]:
        return {"status": self.status, "violations": list(self.violations)}


def gatekeeper_request_status(
    *,
    proposal: PaperTradeProposal | None,
    risk_evaluation: RiskEvaluation | None,
    approval: ApprovalRecord | None,
    journal_commit: JournalEntry | None,
    evaluation_gate: EvaluationGateResult | None = None,
) -> str:
    if (
        proposal is not None
        and risk_evaluation is not None
        and approval is not None
        and journal_commit is not None
        and evaluation_gate_passed(evaluation_gate)
        and validate_proposal(proposal).passed
        and risk_evaluation.decision == RISK_APPROVED
        and approval.approval_state == HUMAN_APPROVED_FOR_PAPER_ONLY
        and proposal.journal_ready
        and proposal.adlc_compliance_status == "PASS"
        and proposal.paper_trading_only
    ):
        return READY_FOR_PAPER_ORDER_REQUEST
    return EXECUTION_BLOCKED


def create_paper_order_request(
    *,
    proposal: PaperTradeProposal,
    risk_evaluation: RiskEvaluation,
    approval: ApprovalRecord,
    journal_commit: JournalEntry,
    gatekeeper_status: str,
    evaluation_gate: EvaluationGateResult | None = None,
) -> PaperOrderRequest:
    final_status = (
        PAPER_ORDER_REQUEST_CREATED
        if gatekeeper_status == READY_FOR_PAPER_ORDER_REQUEST
        and evaluation_gate_passed(evaluation_gate)
        else PAPER_ORDER_REQUEST_BLOCKED
    )
    return PaperOrderRequest(
        paper_order_request_id=f"paper-order-request-{proposal.proposal_id}",
        proposal_id=proposal.proposal_id,
        approval_id=approval.approval_id,
        journal_entry_id=_journal_entry_id(journal_commit),
        created_at="2026-05-19T13:35:00+00:00",
        expires_at=None,
        symbol=proposal.symbol,
        side=proposal.direction,
        order_intent="paper_order_request_only",
        quantity=proposal.proposed_position_size,
        notional=None,
        order_type="limit",
        time_in_force="day",
        proposed_entry=proposal.proposed_entry,
        stop_loss=proposal.stop_loss,
        target_1=proposal.target_1,
        target_2=proposal.target_2,
        max_loss_amount=proposal.max_loss_amount,
        max_loss_pct_equity=proposal.max_loss_pct_equity,
        paper_trading_only=True,
        broker_execution_allowed=False,
        live_trading_allowed=False,
        risk_approval_reference=risk_evaluation.decision,
        human_approval_reference=approval.approval_state,
        journal_commit_reference=_journal_entry_id(journal_commit),
        adlc_compliance_reference=proposal.adlc_compliance_status,
        evaluation_gate_reference=(
            evaluation_gate.status if evaluation_gate else None
        ),
        gatekeeper_status=gatekeeper_status,
        final_status=final_status,
    )


def validate_paper_order_request(
    request: PaperOrderRequest | None,
    *,
    proposal: PaperTradeProposal | None,
    risk_evaluation: RiskEvaluation | None,
    approval: ApprovalRecord | None,
    journal_commit: JournalEntry | None,
    evaluation_gate: EvaluationGateResult | None = None,
) -> PaperOrderRequestValidation:
    violations: list[str] = []
    if request is None:
        return PaperOrderRequestValidation("FAIL", ("request missing",))

    if request.broker_execution_allowed:
        violations.append("broker_execution_allowed is true")
    if request.live_trading_allowed:
        violations.append("live_trading_allowed is true")
    if request.paper_trading_only is not True:
        violations.append("paper_trading_only is not true")
    if risk_evaluation is None or risk_evaluation.decision != RISK_APPROVED:
        violations.append("proposal is not risk-approved")
    if approval is None or approval.approval_state != HUMAN_APPROVED_FOR_PAPER_ONLY:
        violations.append("human approval is missing or not HUMAN_APPROVED_FOR_PAPER_ONLY")
    if journal_commit is None:
        violations.append("journal commit is missing")
    if request.adlc_compliance_reference != "PASS":
        violations.append("ADLC compliance is not PASS")
    if request.evaluation_gate_reference != EVALUATION_GATE_PASSED:
        violations.append("evaluation gate did not pass")
    if (
        not evaluation_gate_passed(evaluation_gate)
        and request.evaluation_gate_reference != EVALUATION_GATE_PASSED
    ):
        violations.append("evaluation gate is missing or blocked")
    if request.gatekeeper_status != READY_FOR_PAPER_ORDER_REQUEST:
        violations.append("gatekeeper status is not READY_FOR_PAPER_ORDER_REQUEST")
    if request.gatekeeper_status in FORBIDDEN_GATEKEEPER_OUTPUTS:
        violations.append("gatekeeper status is forbidden")
    if proposal is None or not validate_proposal(proposal).passed:
        violations.append("proposal validation did not pass")

    required_fields = {
        "paper_order_request_id": request.paper_order_request_id,
        "proposal_id": request.proposal_id,
        "approval_id": request.approval_id,
        "journal_entry_id": request.journal_entry_id,
        "created_at": request.created_at,
        "symbol": request.symbol,
        "side": request.side,
        "order_intent": request.order_intent,
        "order_type": request.order_type,
        "time_in_force": request.time_in_force,
        "proposed_entry": request.proposed_entry,
        "stop_loss": request.stop_loss,
        "target_1": request.target_1,
        "max_loss_amount": request.max_loss_amount,
        "max_loss_pct_equity": request.max_loss_pct_equity,
        "risk_approval_reference": request.risk_approval_reference,
        "human_approval_reference": request.human_approval_reference,
        "journal_commit_reference": request.journal_commit_reference,
        "adlc_compliance_reference": request.adlc_compliance_reference,
        "evaluation_gate_reference": request.evaluation_gate_reference,
        "final_status": request.final_status,
    }
    missing = _missing_fields(required_fields)
    if missing:
        violations.append(f"required trade fields are missing: {', '.join(missing)}")
    if not request.quantity and not request.notional:
        violations.append("quantity and notional are both missing")
    if not request.order_type:
        violations.append("order_type is missing")
    if not request.time_in_force:
        violations.append("time_in_force is missing")

    return PaperOrderRequestValidation("FAIL" if violations else "PASS", tuple(violations))


def request_journal_entry(
    *,
    request: PaperOrderRequest | None,
    proposal: PaperTradeProposal | None,
    risk_status: str,
    human_approval_status: str,
    validation: PaperOrderRequestValidation,
) -> JournalEntry:
    if request is None:
        event_type = "paper_order_request_blocked"
        reason = "Paper order request was not created."
        gatekeeper_status = EXECUTION_BLOCKED
    elif validation.passed:
        event_type = "paper_order_request_created"
        reason = PAPER_ORDER_REQUEST_CREATED
        gatekeeper_status = request.gatekeeper_status
    else:
        event_type = "paper_order_request_invalid"
        reason = "; ".join(validation.violations)
        gatekeeper_status = request.gatekeeper_status
    return commit_journal_entry(
        proposal=proposal,
        risk_status=risk_status,
        human_approval_status=human_approval_status,
        gatekeeper_status=gatekeeper_status,
        event_type=event_type,
        reason_for_final_decision=reason,
        lessons_or_notes="Internal request only; no broker order or execution exists.",
    )


def deterministic_valid_request() -> tuple[
    PaperTradeProposal,
    RiskEvaluation,
    ApprovalRecord,
    JournalEntry,
    PaperOrderRequest,
    PaperOrderRequestValidation,
]:
    proposal = deterministic_valid_proposal()
    risk = evaluate_risk(proposal, default_mock_snapshot())
    evaluation_report = evaluate_strategy(
        StrategyEvaluationInput(
            proposal=proposal,
            risk_evaluation=risk,
            journal_entry=_evaluation_journal_fixture(proposal),
        )
    )
    evaluation_gate = evaluate_gate(evaluation_report, journal_reference="journal-evaluation-gate")
    evaluation_gate_journal_entry(evaluation_gate)
    approval = deterministic_human_approval(proposal)
    journal = commit_journal_entry(
        proposal=proposal,
        risk_status=risk.decision,
        human_approval_status=approval.approval_state,
        gatekeeper_status=EXECUTION_BLOCKED,
        event_type="human_approved_for_paper_only",
        reason_for_final_decision="Human paper-only approval recorded.",
        lessons_or_notes="Journal commit precedes any paper order request.",
    )
    gatekeeper_status = gatekeeper_request_status(
        proposal=proposal,
        risk_evaluation=risk,
        approval=approval,
        journal_commit=journal,
        evaluation_gate=evaluation_gate,
    )
    request = create_paper_order_request(
        proposal=proposal,
        risk_evaluation=risk,
        approval=approval,
        journal_commit=journal,
        gatekeeper_status=gatekeeper_status,
        evaluation_gate=evaluation_gate,
    )
    validation = validate_paper_order_request(
        request,
        proposal=proposal,
        risk_evaluation=risk,
        approval=approval,
        journal_commit=journal,
        evaluation_gate=evaluation_gate,
    )
    return proposal, risk, approval, journal, request, validation


def _journal_entry_id(journal: JournalEntry) -> str:
    return f"journal-{journal.proposal_id}-{journal.event_type}"


def _missing_fields(fields: dict[str, object]) -> tuple[str, ...]:
    return tuple(name for name, value in fields.items() if value in (None, ""))


class _EvaluationJournalFixture:
    reason_for_final_decision = "Valid paper-only proposal with clear context and fixed risk."
    lessons_or_notes = "Evaluation-first gate fixture with strong journal readiness."


def _evaluation_journal_fixture(proposal: PaperTradeProposal) -> _EvaluationJournalFixture:
    return _EvaluationJournalFixture()


def assert_gatekeeper_output_allowed(status: str) -> None:
    if status not in {READY_FOR_PAPER_ORDER_REQUEST, EXECUTION_BLOCKED}:
        raise ValueError(f"Forbidden gatekeeper output: {status}")


def forbidden_gatekeeper_outputs() -> Iterable[str]:
    return tuple(FORBIDDEN_GATEKEEPER_OUTPUTS)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate deterministic paper order request fixture.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    _, _, _, journal, request, validation = deterministic_valid_request()
    request_journal = request_journal_entry(
        request=request,
        proposal=deterministic_valid_proposal(),
        risk_status=request.risk_approval_reference or "NOT_RUN",
        human_approval_status=request.human_approval_reference or "NOT_REQUESTED",
        validation=validation,
    )
    payload = {
        "request": request.as_dict(),
        "validation": validation.as_dict(),
        "approval_journal_commit": journal.as_dict(),
        "request_journal_commit": request_journal.as_dict(),
    }
    print(json.dumps(payload, indent=2))
    return 0 if validation.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
