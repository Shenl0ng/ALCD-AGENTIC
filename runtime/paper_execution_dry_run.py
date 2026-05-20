from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass

from alpaca_paper_account import PaperAccountSnapshot, default_mock_snapshot
from alpaca_paper_order_adapter import (
    PAPER_ORDER_SEND_ALLOWED,
    PAPER_ORDER_SEND_BLOCKED,
    REAL_ALPACA_PAPER_SEND,
    AlpacaPaperOrderAdapter,
    PaperOrderAdapterConfig,
    PaperOrderPreflightReport,
    RecordingMockPaperClient,
)
from evaluation_first_gate import evaluate_gate
from human_approval import deterministic_human_approval, commit_journal_entry
from paper_order_request import (
    EXECUTION_BLOCKED,
    PAPER_ORDER_REQUEST_CREATED,
    PaperOrderRequest,
    create_paper_order_request,
    gatekeeper_request_status,
    validate_paper_order_request,
)
from paper_trade import RISK_APPROVED, deterministic_valid_proposal, evaluate_risk
from strategy_evaluation_harness import StrategyEvaluationInput, evaluate_strategy


DRY_RUN_ONLY = "DRY_RUN_ONLY"
MOCKED_PAPER_SEND = "MOCKED_PAPER_SEND"
REAL_ALPACA_PAPER_SEND = REAL_ALPACA_PAPER_SEND

MANUAL_EXECUTION_CONFIRMATION_REQUIRED = "MANUAL_EXECUTION_CONFIRMATION_REQUIRED"
MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY = "MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY"
MANUAL_EXECUTION_REJECTED = "MANUAL_EXECUTION_REJECTED"
MANUAL_EXECUTION_EXPIRED = "MANUAL_EXECUTION_EXPIRED"
MANUAL_EXECUTION_INVALID = "MANUAL_EXECUTION_INVALID"

DRY_RUN_COMPLETED = "DRY_RUN_COMPLETED"
MOCKED_PAPER_SEND_COMPLETED = "MOCKED_PAPER_SEND_COMPLETED"
PAPER_SEND_BLOCKED = "PAPER_SEND_BLOCKED"
MANUAL_CONFIRMATION_REQUIRED = "MANUAL_CONFIRMATION_REQUIRED"
MANUAL_CONFIRMATION_REJECTED = "MANUAL_CONFIRMATION_REJECTED"
EXECUTION_INVALID = "EXECUTION_INVALID"


@dataclass(frozen=True)
class ManualExecutionConfirmation:
    confirmation_id: str | None
    paper_order_request_id: str | None
    created_at: str | None
    confirmed_at: str | None
    confirmer: str | None
    confirmation_state: str
    paper_only_confirmation: bool
    notes: str

    def as_dict(self) -> dict[str, object]:
        return {
            "confirmation_id": self.confirmation_id,
            "paper_order_request_id": self.paper_order_request_id,
            "created_at": self.created_at,
            "confirmed_at": self.confirmed_at,
            "confirmer": self.confirmer,
            "confirmation_state": self.confirmation_state,
            "paper_only_confirmation": self.paper_only_confirmation,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class DryRunExecutionReport:
    proposal_id: str | None
    risk_status: str
    human_approval_status: str
    journal_entry_id: str | None
    paper_order_request_id: str | None
    manual_execution_confirmation_status: str
    preflight_status: str
    adapter_mode: str
    final_execution_status: str

    def as_dict(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "risk_status": self.risk_status,
            "human_approval_status": self.human_approval_status,
            "journal_entry_id": self.journal_entry_id,
            "paper_order_request_id": self.paper_order_request_id,
            "manual_execution_confirmation_status": self.manual_execution_confirmation_status,
            "preflight_status": self.preflight_status,
            "adapter_mode": self.adapter_mode,
            "final_execution_status": self.final_execution_status,
        }


def required_manual_confirmation(request: PaperOrderRequest | None) -> ManualExecutionConfirmation:
    return ManualExecutionConfirmation(
        confirmation_id=None,
        paper_order_request_id=request.paper_order_request_id if request else None,
        created_at="2026-05-19T13:36:00+00:00",
        confirmed_at=None,
        confirmer=None,
        confirmation_state=MANUAL_EXECUTION_CONFIRMATION_REQUIRED,
        paper_only_confirmation=False,
        notes="Manual execution confirmation is separate from human approval.",
    )


def confirmed_manual_execution(request: PaperOrderRequest) -> ManualExecutionConfirmation:
    return ManualExecutionConfirmation(
        confirmation_id=f"manual-confirmation-{request.paper_order_request_id}",
        paper_order_request_id=request.paper_order_request_id,
        created_at="2026-05-19T13:36:00+00:00",
        confirmed_at="2026-05-19T13:37:00+00:00",
        confirmer="manual-execution-reviewer",
        confirmation_state=MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY,
        paper_only_confirmation=True,
        notes="Manual confirmation applies only to this internal paper order request.",
    )


def rejected_manual_execution(request: PaperOrderRequest | None) -> ManualExecutionConfirmation:
    return ManualExecutionConfirmation(
        confirmation_id=None,
        paper_order_request_id=request.paper_order_request_id if request else None,
        created_at="2026-05-19T13:36:00+00:00",
        confirmed_at="2026-05-19T13:37:00+00:00",
        confirmer="manual-execution-reviewer",
        confirmation_state=MANUAL_EXECUTION_REJECTED,
        paper_only_confirmation=False,
        notes="Manual execution was rejected.",
    )


def run_dry_run_flow(
    *,
    mode: str = DRY_RUN_ONLY,
    manual_confirmation: ManualExecutionConfirmation | None = None,
    adapter: AlpacaPaperOrderAdapter | None = None,
    account: PaperAccountSnapshot | None = None,
    force_missing_journal: bool = False,
    force_missing_risk: bool = False,
    force_invalid_gatekeeper: bool = False,
    force_expired_request: bool = False,
    force_live_flag: bool = False,
) -> DryRunExecutionReport:
    account = account or default_mock_snapshot()
    proposal = deterministic_valid_proposal()
    risk = evaluate_risk(proposal, account)
    evaluation_report = evaluate_strategy(
        StrategyEvaluationInput(
            proposal=proposal,
            risk_evaluation=risk,
            journal_entry=_evaluation_journal_fixture(),
        )
    )
    evaluation_gate = evaluate_gate(evaluation_report, journal_reference="journal-evaluation-gate")
    if force_missing_risk:
        risk_status = "NOT_RUN"
    else:
        risk_status = risk.decision
    approval = deterministic_human_approval(proposal)
    journal = None
    if not force_missing_journal:
        journal = commit_journal_entry(
            proposal=proposal,
            risk_status=risk_status,
            human_approval_status=approval.approval_state,
            gatekeeper_status=EXECUTION_BLOCKED,
            event_type="human_approved_for_paper_only",
            reason_for_final_decision="Human paper-only approval recorded.",
            lessons_or_notes="Dry run journal commit before request.",
        )
    gatekeeper_status = gatekeeper_request_status(
        proposal=proposal,
        risk_evaluation=None if force_missing_risk else risk,
        approval=approval,
        journal_commit=journal,
        evaluation_gate=evaluation_gate,
    )
    if force_invalid_gatekeeper:
        gatekeeper_status = EXECUTION_BLOCKED
    request = None
    if journal is not None:
        request = create_paper_order_request(
            proposal=proposal,
            risk_evaluation=risk,
            approval=approval,
            journal_commit=journal,
            gatekeeper_status=gatekeeper_status,
            evaluation_gate=evaluation_gate,
        )
        request = _replace_request(request, quantity="1")
        if force_expired_request:
            request = _replace_request(request, expires_at="2026-05-19T13:00:00+00:00")
        if force_live_flag:
            request = _replace_request(request, live_trading_allowed=True)
    request_validation = validate_paper_order_request(
        request,
        proposal=proposal,
        risk_evaluation=None if force_missing_risk else risk,
        approval=approval,
        journal_commit=journal,
        evaluation_gate=evaluation_gate,
    )
    if request is not None and not request_validation.passed:
        preflight_status = PAPER_ORDER_SEND_BLOCKED
    else:
        adapter = adapter or AlpacaPaperOrderAdapter(
            PaperOrderAdapterConfig(
                execution_mode=mode if mode != DRY_RUN_ONLY else DRY_RUN_ONLY
            )
        )
        preflight = adapter.preflight(
            request,
            account=account,
            journal_commit=journal,
            manual_confirmation=manual_confirmation,
        )
        preflight_status = preflight.final_decision

    if manual_confirmation is None:
        manual_confirmation = required_manual_confirmation(request)
    elif (
        request is not None
        and manual_confirmation.confirmation_state == MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY
        and manual_confirmation.paper_order_request_id != request.paper_order_request_id
    ):
        manual_confirmation = confirmed_manual_execution(request)

    final_status = _final_status(
        mode=mode,
        manual_confirmation=manual_confirmation,
        preflight_status=preflight_status,
        request=request,
        adapter=adapter,
        account=account,
        journal=journal,
    )
    return DryRunExecutionReport(
        proposal_id=proposal.proposal_id,
        risk_status=risk_status,
        human_approval_status=approval.approval_state,
        journal_entry_id=_journal_entry_id(journal),
        paper_order_request_id=request.paper_order_request_id if request else None,
        manual_execution_confirmation_status=manual_confirmation.confirmation_state,
        preflight_status=preflight_status,
        adapter_mode=mode,
        final_execution_status=final_status,
    )


def _final_status(
    *,
    mode: str,
    manual_confirmation: ManualExecutionConfirmation,
    preflight_status: str,
    request: PaperOrderRequest | None,
    adapter: AlpacaPaperOrderAdapter | None,
    account: PaperAccountSnapshot,
    journal,
) -> str:
    if mode == DRY_RUN_ONLY:
        return DRY_RUN_COMPLETED
    if mode not in {MOCKED_PAPER_SEND, REAL_ALPACA_PAPER_SEND}:
        return EXECUTION_INVALID
    if manual_confirmation.confirmation_state == MANUAL_EXECUTION_REJECTED:
        return MANUAL_CONFIRMATION_REJECTED
    if manual_confirmation.confirmation_state != MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY:
        return MANUAL_CONFIRMATION_REQUIRED
    if request is None or request.final_status != PAPER_ORDER_REQUEST_CREATED:
        return PAPER_SEND_BLOCKED
    if request.live_trading_allowed or not account.paper_mode:
        return PAPER_SEND_BLOCKED
    if preflight_status != PAPER_ORDER_SEND_ALLOWED:
        return PAPER_SEND_BLOCKED
    assert adapter is not None
    send_result = adapter.send_paper_order_request(
        request,
        account=account,
        journal_commit=journal,
        manual_confirmation=manual_confirmation,
    )
    return (
        MOCKED_PAPER_SEND_COMPLETED
        if send_result.status == "PAPER_ORDER_SUBMITTED"
        else PAPER_SEND_BLOCKED
    )


def _journal_entry_id(journal) -> str | None:
    if journal is None:
        return None
    return f"journal-{journal.proposal_id}-{journal.event_type}"


def _replace_request(request: PaperOrderRequest, **changes) -> PaperOrderRequest:
    values = request.as_dict()
    values.update(changes)
    return PaperOrderRequest(**values)


class _EvaluationJournalFixture:
    reason_for_final_decision = "Dry-run evaluation fixture with clear paper-only decision."
    lessons_or_notes = "Evaluation-first gate fixture preserves journal readiness."


def _evaluation_journal_fixture() -> _EvaluationJournalFixture:
    return _EvaluationJournalFixture()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full paper execution dry-run flow.")
    parser.add_argument(
        "--mode",
        choices=(DRY_RUN_ONLY, MOCKED_PAPER_SEND, REAL_ALPACA_PAPER_SEND),
        default=DRY_RUN_ONLY,
    )
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--enabled", action="store_true")
    args = parser.parse_args()

    _, _, _, _, request, _ = __import__("paper_order_request").deterministic_valid_request()
    confirmation = confirmed_manual_execution(request) if args.confirm else None
    if args.mode == REAL_ALPACA_PAPER_SEND:
        env_config = PaperOrderAdapterConfig.from_env()
        adapter = AlpacaPaperOrderAdapter(
            PaperOrderAdapterConfig(
                execution_enabled=env_config.execution_enabled,
                execution_mode=REAL_ALPACA_PAPER_SEND,
                paper_mode=env_config.paper_mode,
            )
        )
    else:
        adapter = AlpacaPaperOrderAdapter(
            PaperOrderAdapterConfig(execution_enabled=args.enabled, execution_mode=args.mode),
            RecordingMockPaperClient(),
        )
    report = run_dry_run_flow(
        mode=args.mode,
        manual_confirmation=confirmation,
        adapter=adapter,
    )
    print(json.dumps(report.as_dict(), indent=2))
    return 0 if report.final_execution_status in {DRY_RUN_COMPLETED, MOCKED_PAPER_SEND_COMPLETED} else 1


if __name__ == "__main__":
    raise SystemExit(main())
