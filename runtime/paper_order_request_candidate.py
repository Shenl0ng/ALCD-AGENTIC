from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence
from unittest.mock import patch

from automated_proposal_dry_run import (
    DRY_RUN_ONLY,
    TRADE_PROPOSAL,
    AutomatedDryRunReport,
    run_automated_proposal_dry_run,
)
from paper_trade import deterministic_valid_proposal


REPORT_ROOT = Path("reports/automated_paper_request_candidate")
REPORT_NAME = "PAPER_ORDER_REQUEST_CANDIDATE.md"
JOURNAL_NAME = "PAPER_ORDER_REQUEST_CANDIDATE_JOURNAL.json"

PAPER_ORDER_CANDIDATE_CREATED = "PAPER_ORDER_CANDIDATE_CREATED"
PAPER_ORDER_CANDIDATE_BLOCKED = "PAPER_ORDER_CANDIDATE_BLOCKED"
PAPER_ORDER_CANDIDATE_INVALID = "PAPER_ORDER_CANDIDATE_INVALID"
PAPER_ORDER_CANDIDATE_EXPIRED = "PAPER_ORDER_CANDIDATE_EXPIRED"
ALLOWED_CANDIDATE_STATUSES = {
    PAPER_ORDER_CANDIDATE_CREATED,
    PAPER_ORDER_CANDIDATE_BLOCKED,
    PAPER_ORDER_CANDIDATE_INVALID,
    PAPER_ORDER_CANDIDATE_EXPIRED,
}


@dataclass(frozen=True)
class PaperOrderRequestCandidate:
    candidate_id: str
    created_at: str
    symbol: str
    proposal_id: str
    strategy_evaluation_reference: str
    evaluation_gate_reference: str
    negative_case_regression_reference: str
    risk_dry_run_reference: str
    journal_reference: str
    proposed_side: str
    proposed_order_type: str
    proposed_time_in_force: str
    proposed_notional: str
    proposed_quantity: str | None
    proposed_limit_price: str
    stop_loss: str
    target_1: str
    target_2: str | None
    thesis: str
    invalidation: str
    paper_trading_only: bool
    human_approval_required: bool
    manual_execution_confirmation_required: bool
    broker_execution_allowed: bool
    live_trading_allowed: bool
    candidate_status: str

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate_id": self.candidate_id,
            "created_at": self.created_at,
            "symbol": self.symbol,
            "proposal_id": self.proposal_id,
            "strategy_evaluation_reference": self.strategy_evaluation_reference,
            "evaluation_gate_reference": self.evaluation_gate_reference,
            "negative_case_regression_reference": self.negative_case_regression_reference,
            "risk_dry_run_reference": self.risk_dry_run_reference,
            "journal_reference": self.journal_reference,
            "proposed_side": self.proposed_side,
            "proposed_order_type": self.proposed_order_type,
            "proposed_time_in_force": self.proposed_time_in_force,
            "proposed_notional": self.proposed_notional,
            "proposed_quantity": self.proposed_quantity,
            "proposed_limit_price": self.proposed_limit_price,
            "stop_loss": self.stop_loss,
            "target_1": self.target_1,
            "target_2": self.target_2,
            "thesis": self.thesis,
            "invalidation": self.invalidation,
            "paper_trading_only": self.paper_trading_only,
            "human_approval_required": self.human_approval_required,
            "manual_execution_confirmation_required": self.manual_execution_confirmation_required,
            "broker_execution_allowed": self.broker_execution_allowed,
            "live_trading_allowed": self.live_trading_allowed,
            "candidate_status": self.candidate_status,
        }


@dataclass(frozen=True)
class CandidateValidation:
    status: str
    violations: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.status == "PASS"

    def as_dict(self) -> dict[str, object]:
        return {"status": self.status, "violations": list(self.violations)}


@dataclass(frozen=True)
class CandidateCreationResult:
    candidate: PaperOrderRequestCandidate | None
    validation: CandidateValidation
    symbol: str
    decision: str
    candidate_status: str
    proposal_reference: str
    strategy_evaluation_status: str
    evaluation_gate_status: str
    negative_case_regression_status: str
    risk_dry_run_status: str
    journal_reference: str
    final_status: str
    reason: str
    report_path: str | None
    journal_path: str | None
    finalized_paper_order_request_created: bool = False
    human_approval_requested: bool = False
    manual_execution_confirmation_requested: bool = False
    order_sent: bool = False
    broker_execution_readiness: bool = False
    live_trading_assumption: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "candidate": self.candidate.as_dict() if self.candidate else None,
            "validation": self.validation.as_dict(),
            "symbol": self.symbol,
            "decision": self.decision,
            "candidate_status": self.candidate_status,
            "proposal_reference": self.proposal_reference,
            "strategy_evaluation_status": self.strategy_evaluation_status,
            "evaluation_gate_status": self.evaluation_gate_status,
            "negative_case_regression_status": self.negative_case_regression_status,
            "risk_dry_run_status": self.risk_dry_run_status,
            "journal_reference": self.journal_reference,
            "final_status": self.final_status,
            "reason": self.reason,
            "report_path": self.report_path,
            "journal_path": self.journal_path,
            "finalized_paper_order_request_created": self.finalized_paper_order_request_created,
            "human_approval_requested": self.human_approval_requested,
            "manual_execution_confirmation_requested": self.manual_execution_confirmation_requested,
            "order_sent": self.order_sent,
            "broker_execution_readiness": self.broker_execution_readiness,
            "live_trading_assumption": self.live_trading_assumption,
        }


def create_paper_order_request_candidate(
    *,
    symbols: Sequence[str],
    scenario: str = "proposal",
    mode: str = DRY_RUN_ONLY,
    output_root: Path = REPORT_ROOT,
    write_artifacts: bool = True,
    known_negative_case_failure_pattern: bool = False,
    adlc_compliance_status: str = "PASS",
    journal_ready: bool = True,
    paper_send_readiness: bool = False,
    broker_execution_readiness: bool = False,
) -> CandidateCreationResult:
    dry_run = run_automated_proposal_dry_run(
        symbols=symbols,
        mode=mode,
        scenario=scenario,
        write_artifacts=False,
    )
    gate_violations = _candidate_gate_violations(
        symbols=symbols,
        mode=mode,
        dry_run=dry_run,
        known_negative_case_failure_pattern=known_negative_case_failure_pattern,
        adlc_compliance_status=adlc_compliance_status,
        journal_ready=journal_ready,
        paper_send_readiness=paper_send_readiness,
        broker_execution_readiness=broker_execution_readiness,
    )
    if gate_violations:
        return _finalize_result(
            dry_run=dry_run,
            candidate=None,
            validation=CandidateValidation("FAIL", tuple(gate_violations)),
            candidate_status=PAPER_ORDER_CANDIDATE_BLOCKED,
            reason="; ".join(gate_violations),
            output_root=output_root,
            write_artifacts=write_artifacts,
        )

    candidate = _build_candidate(dry_run)
    validation = validate_candidate(candidate)
    if not validation.passed:
        return _finalize_result(
            dry_run=dry_run,
            candidate=candidate,
            validation=validation,
            candidate_status=PAPER_ORDER_CANDIDATE_INVALID,
            reason="; ".join(validation.violations),
            output_root=output_root,
            write_artifacts=write_artifacts,
        )

    return _finalize_result(
        dry_run=dry_run,
        candidate=candidate,
        validation=validation,
        candidate_status=PAPER_ORDER_CANDIDATE_CREATED,
        reason="Paper Order Request Candidate created for later human review only.",
        output_root=output_root,
        write_artifacts=write_artifacts,
    )


def validate_candidate(candidate: PaperOrderRequestCandidate | None) -> CandidateValidation:
    if candidate is None:
        return CandidateValidation("FAIL", ("candidate is missing",))
    violations: list[str] = []
    required_values = {
        "candidate_id": candidate.candidate_id,
        "created_at": candidate.created_at,
        "symbol": candidate.symbol,
        "proposal_id": candidate.proposal_id,
        "strategy_evaluation_reference": candidate.strategy_evaluation_reference,
        "evaluation_gate_reference": candidate.evaluation_gate_reference,
        "negative_case_regression_reference": candidate.negative_case_regression_reference,
        "risk_dry_run_reference": candidate.risk_dry_run_reference,
        "journal_reference": candidate.journal_reference,
        "proposed_side": candidate.proposed_side,
        "proposed_order_type": candidate.proposed_order_type,
        "proposed_time_in_force": candidate.proposed_time_in_force,
        "proposed_notional": candidate.proposed_notional,
        "proposed_limit_price": candidate.proposed_limit_price,
        "stop_loss": candidate.stop_loss,
        "target_1": candidate.target_1,
        "thesis": candidate.thesis,
        "invalidation": candidate.invalidation,
        "candidate_status": candidate.candidate_status,
    }
    for field_name, value in required_values.items():
        if value in (None, ""):
            violations.append(f"missing {field_name}")
    if candidate.candidate_status not in ALLOWED_CANDIDATE_STATUSES:
        violations.append("candidate status is not allowed")
    if candidate.paper_trading_only is not True:
        violations.append("paper_trading_only must be true")
    if candidate.human_approval_required is not True:
        violations.append("human_approval_required must be true")
    if candidate.manual_execution_confirmation_required is not True:
        violations.append("manual_execution_confirmation_required must be true")
    if candidate.broker_execution_allowed is not False:
        violations.append("broker_execution_allowed must be false")
    if candidate.live_trading_allowed is not False:
        violations.append("live_trading_allowed must be false")
    return CandidateValidation("FAIL" if violations else "PASS", tuple(violations))


def _candidate_gate_violations(
    *,
    symbols: Sequence[str],
    mode: str,
    dry_run: AutomatedDryRunReport,
    known_negative_case_failure_pattern: bool,
    adlc_compliance_status: str,
    journal_ready: bool,
    paper_send_readiness: bool,
    broker_execution_readiness: bool,
) -> list[str]:
    violations: list[str] = []
    if mode != DRY_RUN_ONLY:
        violations.append("DRY_RUN_ONLY mode is required")
    if os.environ.get("PAPER_ORDER_EXECUTION_ENABLED", "").lower() == "true":
        violations.append("PAPER_ORDER_EXECUTION_ENABLED=true is blocked")
    if len(symbols) != 1:
        violations.append("one symbol only is required")
    if dry_run.decision != TRADE_PROPOSAL:
        violations.append("candidate requires TRADE_PROPOSAL decision")
    if dry_run.data_integrity_status != "PASS":
        violations.append("Data Integrity PASS is required")
    if dry_run.strategy_evaluation_status != "PASS":
        violations.append("Strategy Evaluation PASS is required")
    if dry_run.evaluation_gate_status != "EVALUATION_GATE_PASSED":
        violations.append("Evaluation-First Gate PASS is required")
    if dry_run.negative_case_regression_status != "PASS":
        violations.append("Negative Case Regression PASS is required")
    if known_negative_case_failure_pattern:
        violations.append("proposal matches known negative-case failure pattern")
    if dry_run.risk_dry_run_status != "RISK_APPROVED":
        violations.append("Risk Manager dry-run/read-only PASS is required")
    if adlc_compliance_status != "PASS":
        violations.append("ADLC compliance PASS is required")
    if not journal_ready:
        violations.append("journal readiness PASS is required")
    if dry_run.paper_send_readiness or paper_send_readiness:
        violations.append("paper send readiness is blocked")
    if dry_run.broker_execution_readiness or broker_execution_readiness:
        violations.append("broker execution readiness is blocked")
    if dry_run.live_trading_assumption:
        violations.append("live trading assumption is blocked")
    return violations


def _build_candidate(dry_run: AutomatedDryRunReport) -> PaperOrderRequestCandidate:
    proposal = deterministic_valid_proposal()
    symbol = dry_run.symbol.upper()
    return PaperOrderRequestCandidate(
        candidate_id=f"candidate-{proposal.proposal_id}",
        created_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        symbol=symbol,
        proposal_id=proposal.proposal_id or "unknown-proposal",
        strategy_evaluation_reference=f"strategy-evaluation-{proposal.proposal_id}",
        evaluation_gate_reference=f"evaluation-gate-{proposal.proposal_id}",
        negative_case_regression_reference="negative-case-regression-pass",
        risk_dry_run_reference=f"risk-dry-run-{proposal.proposal_id}",
        journal_reference=dry_run.journal_reference,
        proposed_side=proposal.direction or "long",
        proposed_order_type="limit",
        proposed_time_in_force="day",
        proposed_notional="100",
        proposed_quantity=None,
        proposed_limit_price=proposal.proposed_entry or "",
        stop_loss=proposal.stop_loss or "",
        target_1=proposal.target_1 or "",
        target_2=proposal.target_2,
        thesis=proposal.thesis or "",
        invalidation=proposal.what_invalidates_trade or "",
        paper_trading_only=True,
        human_approval_required=True,
        manual_execution_confirmation_required=True,
        broker_execution_allowed=False,
        live_trading_allowed=False,
        candidate_status=PAPER_ORDER_CANDIDATE_CREATED,
    )


def _finalize_result(
    *,
    dry_run: AutomatedDryRunReport,
    candidate: PaperOrderRequestCandidate | None,
    validation: CandidateValidation,
    candidate_status: str,
    reason: str,
    output_root: Path,
    write_artifacts: bool,
) -> CandidateCreationResult:
    report_path: Path | None = None
    journal_path: Path | None = None
    if write_artifacts:
        report_dir = _timestamped_report_dir(output_root)
        report_path = report_dir / REPORT_NAME
        journal_path = report_dir / JOURNAL_NAME
    result = CandidateCreationResult(
        candidate=candidate,
        validation=validation,
        symbol=dry_run.symbol,
        decision=dry_run.decision,
        candidate_status=candidate_status,
        proposal_reference=(candidate.proposal_id if candidate else "None"),
        strategy_evaluation_status=dry_run.strategy_evaluation_status,
        evaluation_gate_status=dry_run.evaluation_gate_status,
        negative_case_regression_status=dry_run.negative_case_regression_status,
        risk_dry_run_status=dry_run.risk_dry_run_status,
        journal_reference=dry_run.journal_reference,
        final_status=candidate_status,
        reason=reason,
        report_path=report_path.as_posix() if report_path else None,
        journal_path=journal_path.as_posix() if journal_path else None,
    )
    if write_artifacts and report_path and journal_path:
        journal_path.write_text(json.dumps(_journal_payload(result), indent=2), encoding="utf-8")
        report_path.write_text(_render_candidate_report(result), encoding="utf-8")
    return result


def _journal_payload(result: CandidateCreationResult) -> dict[str, object]:
    return {
        "journal_reference": result.journal_reference,
        "symbol": result.symbol,
        "decision": result.decision,
        "candidate_status": result.candidate_status,
        "final_status": result.final_status,
        "reason": result.reason,
        "candidate": result.candidate.as_dict() if result.candidate else None,
        "finalized_paper_order_request_created": False,
        "order_sent": False,
        "broker_execution_readiness": False,
    }


def _render_candidate_report(result: CandidateCreationResult) -> str:
    candidate = result.candidate
    paper_trading_only = candidate.paper_trading_only if candidate else False
    human_approval_required = candidate.human_approval_required if candidate else False
    manual_execution_confirmation_required = (
        candidate.manual_execution_confirmation_required if candidate else False
    )
    broker_execution_allowed = candidate.broker_execution_allowed if candidate else False
    live_trading_allowed = candidate.live_trading_allowed if candidate else False
    return f"""# Paper Order Request Candidate

## Summary

- Symbol: {result.symbol}
- Decision: {result.decision}
- Candidate status: {result.candidate_status}
- Proposal reference: {result.proposal_reference}
- Strategy evaluation status: {result.strategy_evaluation_status}
- Evaluation gate status: {result.evaluation_gate_status}
- Negative Case Regression status: {result.negative_case_regression_status}
- Risk dry-run status: {result.risk_dry_run_status}
- Journal reference: {result.journal_reference}
- paper_trading_only: {str(paper_trading_only).lower()}
- human_approval_required: {str(human_approval_required).lower()}
- manual_execution_confirmation_required: {str(manual_execution_confirmation_required).lower()}
- broker_execution_allowed: {str(broker_execution_allowed).lower()}
- live_trading_allowed: {str(live_trading_allowed).lower()}
- Final status: {result.final_status}
- Reason: {result.reason}

## Candidate

```json
{json.dumps(candidate.as_dict() if candidate else None, indent=2)}
```

## Safety

No order was sent.
No finalized Paper Order Request was created.
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Paper Order Request Candidate.")
    parser.add_argument("--symbol", action="append", required=True)
    parser.add_argument("--scenario", default="proposal")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": os.environ.get("PAPER_ORDER_EXECUTION_ENABLED", "")}):
        result = create_paper_order_request_candidate(symbols=args.symbol, scenario=args.scenario)
    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(result.final_status)
        print(result.report_path)
    return 0 if result.final_status == PAPER_ORDER_CANDIDATE_CREATED else 1


if __name__ == "__main__":
    raise SystemExit(main())
