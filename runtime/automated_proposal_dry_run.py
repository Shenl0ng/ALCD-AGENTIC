from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping, Sequence

from alpaca_paper_account import default_mock_snapshot
from evaluation_first_gate import evaluate_gate
from negative_case_regression import run_negative_case_regression
from paper_trade import (
    RISK_APPROVED,
    RISK_REJECTED,
    PaperTradeProposal,
    RiskEvaluation,
    deterministic_valid_proposal,
    evaluate_risk,
)
from strategy_evaluation_harness import StrategyEvaluationInput, evaluate_strategy


OPERATING_POLICY_PATH = Path("docs/OPERATING_POLICY_AFTER_V4.md")
REPORT_ROOT = Path("reports/automated_proposal_dry_run")
REPORT_NAME = "AUTOMATED_PROPOSAL_DRY_RUN_REPORT.md"
JOURNAL_NAME = "AUTOMATED_PROPOSAL_DRY_RUN_JOURNAL.json"

DRY_RUN_ONLY = "DRY_RUN_ONLY"
NO_TRADE = "NO_TRADE"
REJECT = "REJECT"
TRADE_PROPOSAL = "TRADE_PROPOSAL"

AUTOMATED_DRY_RUN_NO_TRADE = "AUTOMATED_DRY_RUN_NO_TRADE"
AUTOMATED_DRY_RUN_REJECTED = "AUTOMATED_DRY_RUN_REJECTED"
AUTOMATED_DRY_RUN_PROPOSAL_CREATED = "AUTOMATED_DRY_RUN_PROPOSAL_CREATED"
AUTOMATED_DRY_RUN_BLOCKED = "AUTOMATED_DRY_RUN_BLOCKED"

SCENARIOS = {
    "proposal",
    "no_trade",
    "reject",
    "data_fail",
    "gate_fail",
    "negative_fail",
    "risk_fail",
}


@dataclass(frozen=True)
class AgentResult:
    status: str
    reason: str

    def as_dict(self) -> dict[str, object]:
        return {"status": self.status, "reason": self.reason}


@dataclass(frozen=True)
class AutomatedDryRunReport:
    symbol: str
    mode: str
    data_integrity_status: str
    market_context_result: AgentResult
    liquidity_result: AgentResult
    session_timing_result: AgentResult
    confirmation_result: AgentResult
    decision: str
    strategy_evaluation_status: str
    evaluation_gate_status: str
    negative_case_regression_status: str
    risk_dry_run_status: str
    journal_reference: str
    final_status: str
    reason: str
    report_path: str | None
    journal_path: str | None
    paper_order_request_created: bool = False
    human_approval_requested: bool = False
    manual_execution_confirmation_requested: bool = False
    paper_send_readiness: bool = False
    broker_execution_readiness: bool = False
    live_trading_assumption: bool = False
    batch_behavior: bool = False
    cancel_replace_behavior: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "mode": self.mode,
            "data_integrity_status": self.data_integrity_status,
            "market_context_result": self.market_context_result.as_dict(),
            "liquidity_result": self.liquidity_result.as_dict(),
            "session_timing_result": self.session_timing_result.as_dict(),
            "confirmation_result": self.confirmation_result.as_dict(),
            "decision": self.decision,
            "strategy_evaluation_status": self.strategy_evaluation_status,
            "evaluation_gate_status": self.evaluation_gate_status,
            "negative_case_regression_status": self.negative_case_regression_status,
            "risk_dry_run_status": self.risk_dry_run_status,
            "journal_reference": self.journal_reference,
            "final_status": self.final_status,
            "reason": self.reason,
            "report_path": self.report_path,
            "journal_path": self.journal_path,
            "paper_order_request_created": self.paper_order_request_created,
            "human_approval_requested": self.human_approval_requested,
            "manual_execution_confirmation_requested": self.manual_execution_confirmation_requested,
            "paper_send_readiness": self.paper_send_readiness,
            "broker_execution_readiness": self.broker_execution_readiness,
            "live_trading_assumption": self.live_trading_assumption,
            "batch_behavior": self.batch_behavior,
            "cancel_replace_behavior": self.cancel_replace_behavior,
        }


def run_automated_proposal_dry_run(
    *,
    symbols: Sequence[str],
    mode: str = DRY_RUN_ONLY,
    scenario: str = "proposal",
    output_root: Path = REPORT_ROOT,
    write_artifacts: bool = True,
) -> AutomatedDryRunReport:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unsupported scenario: {scenario}")
    policy_status = _load_operating_policy()
    block_reason = _hard_block_reason(symbols=symbols, mode=mode, policy_status=policy_status)
    symbol = symbols[0] if symbols else "UNKNOWN"
    if block_reason:
        return _finalize_report(
            symbol=symbol,
            mode=mode,
            data_integrity=AgentResult("NOT_RUN", block_reason),
            market_context=AgentResult("NOT_RUN", block_reason),
            liquidity=AgentResult("NOT_RUN", block_reason),
            session_timing=AgentResult("NOT_RUN", block_reason),
            confirmation=AgentResult("NOT_RUN", block_reason),
            decision=REJECT,
            strategy_status="NOT_RUN",
            gate_status="NOT_RUN",
            negative_status="NOT_RUN",
            risk_status="NOT_RUN",
            final_status=AUTOMATED_DRY_RUN_BLOCKED,
            reason=block_reason,
            output_root=output_root,
            write_artifacts=write_artifacts,
        )

    data_integrity = _data_integrity_result(scenario)
    if data_integrity.status != "PASS":
        return _finalize_report(
            symbol=symbol,
            mode=mode,
            data_integrity=data_integrity,
            market_context=AgentResult("NOT_RUN", data_integrity.reason),
            liquidity=AgentResult("NOT_RUN", data_integrity.reason),
            session_timing=AgentResult("NOT_RUN", data_integrity.reason),
            confirmation=AgentResult("NOT_RUN", data_integrity.reason),
            decision=REJECT,
            strategy_status="NOT_RUN",
            gate_status="NOT_RUN",
            negative_status="NOT_RUN",
            risk_status="NOT_RUN",
            final_status=AUTOMATED_DRY_RUN_BLOCKED,
            reason=data_integrity.reason,
            output_root=output_root,
            write_artifacts=write_artifacts,
        )

    proposal = _proposal_for(symbol, scenario)
    market_context = _market_context_result(proposal, scenario)
    liquidity = _liquidity_result(proposal, scenario)
    session_timing = _session_timing_result(proposal, scenario)
    confirmation = _confirmation_result(proposal, scenario)
    decision = _decision(
        market_context=market_context,
        liquidity=liquidity,
        session_timing=session_timing,
        confirmation=confirmation,
        scenario=scenario,
    )
    evaluation = evaluate_strategy(
        StrategyEvaluationInput(
            proposal=proposal,
            risk_evaluation=_risk_for(proposal, decision, scenario),
            journal_entry=_JournalFixture(decision),
            evaluation_type=_evaluation_type(decision),
            expected_rejection=decision in {NO_TRADE, REJECT},
            actual_rejection=decision in {NO_TRADE, REJECT},
            no_trade_decision=decision == NO_TRADE,
            data_fresh=True,
            data_complete=True,
            no_trade_better_than_trade=decision == NO_TRADE,
        )
    )
    gate = evaluate_gate(evaluation, journal_reference="automated-dry-run-journal")
    negative_status, negative_reason = _negative_case_status(scenario)
    risk = _risk_for(proposal, decision, scenario)

    if scenario == "negative_fail":
        final_status = AUTOMATED_DRY_RUN_BLOCKED
        reason = negative_reason
    elif risk.decision != RISK_APPROVED and decision == TRADE_PROPOSAL:
        final_status = AUTOMATED_DRY_RUN_BLOCKED
        reason = "; ".join(risk.rejection_reasons) or "risk dry-run failed"
    elif scenario == "gate_fail" or (decision == TRADE_PROPOSAL and gate.status != "EVALUATION_GATE_PASSED"):
        final_status = AUTOMATED_DRY_RUN_BLOCKED
        reason = "Evaluation-First Gate blocked automated dry-run proposal."
    elif decision == NO_TRADE:
        final_status = AUTOMATED_DRY_RUN_NO_TRADE
        reason = "No-trade selected by automated dry-run analysis."
    elif decision == REJECT:
        final_status = AUTOMATED_DRY_RUN_REJECTED
        reason = "Setup rejected by automated dry-run analysis."
    else:
        final_status = AUTOMATED_DRY_RUN_PROPOSAL_CREATED
        reason = "Dry-run trade proposal created; no approval, request, or send is authorized."

    return _finalize_report(
        symbol=symbol,
        mode=mode,
        data_integrity=data_integrity,
        market_context=market_context,
        liquidity=liquidity,
        session_timing=session_timing,
        confirmation=confirmation,
        decision=decision,
        strategy_status=evaluation.final_status,
        gate_status=gate.status,
        negative_status=negative_status,
        risk_status=risk.decision,
        final_status=final_status,
        reason=reason,
        output_root=output_root,
        write_artifacts=write_artifacts,
    )


def _load_operating_policy() -> str:
    if not OPERATING_POLICY_PATH.is_file():
        return "MISSING"
    text = OPERATING_POLICY_PATH.read_text(encoding="utf-8")
    return "PASS" if "V4 is the current operating baseline" in text else "FAIL"


def _hard_block_reason(*, symbols: Sequence[str], mode: str, policy_status: str) -> str | None:
    if policy_status != "PASS":
        return "Operating Policy After V4 is missing or invalid."
    if mode != DRY_RUN_ONLY:
        return "Mode must be DRY_RUN_ONLY."
    if os.environ.get("PAPER_ORDER_EXECUTION_ENABLED", "").lower() == "true":
        return "PAPER_ORDER_EXECUTION_ENABLED=true is blocked."
    if len(symbols) != 1:
        return "Exactly one symbol is required."
    if not symbols[0].strip():
        return "Symbol is required."
    return None


def _proposal_for(symbol: str, scenario: str) -> PaperTradeProposal:
    proposal = deterministic_valid_proposal()
    proposal = replace(proposal, symbol=symbol.upper())
    if scenario in {"no_trade", "gate_fail"}:
        return replace(proposal, liquidity_location="weak liquidity")
    if scenario == "reject":
        return replace(proposal, entry_confirmation="vague")
    if scenario == "risk_fail":
        return replace(proposal, risk_per_share=None, max_loss_amount=None)
    return proposal


def _data_integrity_result(scenario: str) -> AgentResult:
    if scenario == "data_fail":
        return AgentResult("FAIL", "Data integrity failed: configured data is incomplete.")
    return AgentResult("PASS", "Configured deterministic market data is fresh and complete.")


def _market_context_result(proposal: PaperTradeProposal, scenario: str) -> AgentResult:
    if not proposal.timeframe_context:
        return AgentResult("FAIL", "Missing higher-timeframe context.")
    return AgentResult("PASS", proposal.timeframe_context or "")


def _liquidity_result(proposal: PaperTradeProposal, scenario: str) -> AgentResult:
    if scenario in {"no_trade", "gate_fail"}:
        return AgentResult("WARN", "Weak liquidity location; no-trade should be preferred.")
    return AgentResult("PASS", proposal.liquidity_location or "")


def _session_timing_result(proposal: PaperTradeProposal, scenario: str) -> AgentResult:
    return AgentResult("PASS", proposal.session_timing or "market_open")


def _confirmation_result(proposal: PaperTradeProposal, scenario: str) -> AgentResult:
    if scenario == "reject":
        return AgentResult("FAIL", "Vague confirmation blocks setup quality.")
    return AgentResult("PASS", proposal.entry_confirmation or "")


def _decision(
    *,
    market_context: AgentResult,
    liquidity: AgentResult,
    session_timing: AgentResult,
    confirmation: AgentResult,
    scenario: str,
) -> str:
    if scenario in {"no_trade", "gate_fail"}:
        return NO_TRADE
    if scenario in {"reject", "risk_fail"}:
        return REJECT if scenario == "reject" else TRADE_PROPOSAL
    if any(result.status == "FAIL" for result in (market_context, liquidity, session_timing, confirmation)):
        return REJECT
    if any(result.status == "WARN" for result in (market_context, liquidity, session_timing, confirmation)):
        return NO_TRADE
    return TRADE_PROPOSAL


def _risk_for(proposal: PaperTradeProposal, decision: str, scenario: str) -> RiskEvaluation:
    risk = evaluate_risk(proposal, default_mock_snapshot())
    if decision in {NO_TRADE, REJECT} and risk.decision == RISK_REJECTED:
        return risk
    return risk


def _evaluation_type(decision: str) -> str:
    if decision == NO_TRADE:
        return "no_trade"
    if decision == REJECT:
        return "rejection"
    return "proposal"


def _negative_case_status(scenario: str) -> tuple[str, str]:
    if scenario == "negative_fail":
        return "FAIL", "Negative-case regression check failed."
    regression = run_negative_case_regression(write_report=False)
    if regression.summary.failed_regression_cases:
        return "FAIL", "Negative-case regression has failed cases."
    if regression.summary.missed_blocks:
        return "FAIL", "Negative-case regression has missed blocks."
    if regression.summary.false_passes:
        return "FAIL", "Negative-case regression has false passes."
    return "PASS", "Negative-case regression checks passed."


def _finalize_report(
    *,
    symbol: str,
    mode: str,
    data_integrity: AgentResult,
    market_context: AgentResult,
    liquidity: AgentResult,
    session_timing: AgentResult,
    confirmation: AgentResult,
    decision: str,
    strategy_status: str,
    gate_status: str,
    negative_status: str,
    risk_status: str,
    final_status: str,
    reason: str,
    output_root: Path,
    write_artifacts: bool,
) -> AutomatedDryRunReport:
    report_path: Path | None = None
    journal_path: Path | None = None
    journal_reference = "automated-dry-run-journal"
    if write_artifacts:
        report_dir = _timestamped_report_dir(output_root)
        journal_path = report_dir / JOURNAL_NAME
        report_path = report_dir / REPORT_NAME
        journal_payload = {
            "journal_reference": journal_reference,
            "symbol": symbol,
            "mode": mode,
            "decision": decision,
            "final_status": final_status,
            "reason": reason,
            "paper_order_request_created": False,
            "paper_send_readiness": False,
            "broker_execution_readiness": False,
        }
        journal_path.write_text(json.dumps(journal_payload, indent=2), encoding="utf-8")
        report = AutomatedDryRunReport(
            symbol=symbol,
            mode=mode,
            data_integrity_status=data_integrity.status,
            market_context_result=market_context,
            liquidity_result=liquidity,
            session_timing_result=session_timing,
            confirmation_result=confirmation,
            decision=decision,
            strategy_evaluation_status=strategy_status,
            evaluation_gate_status=gate_status,
            negative_case_regression_status=negative_status,
            risk_dry_run_status=risk_status,
            journal_reference=journal_reference,
            final_status=final_status,
            reason=reason,
            report_path=report_path.as_posix(),
            journal_path=journal_path.as_posix(),
        )
        report_path.write_text(_render_report(report), encoding="utf-8")
        return report
    return AutomatedDryRunReport(
        symbol=symbol,
        mode=mode,
        data_integrity_status=data_integrity.status,
        market_context_result=market_context,
        liquidity_result=liquidity,
        session_timing_result=session_timing,
        confirmation_result=confirmation,
        decision=decision,
        strategy_evaluation_status=strategy_status,
        evaluation_gate_status=gate_status,
        negative_case_regression_status=negative_status,
        risk_dry_run_status=risk_status,
        journal_reference=journal_reference,
        final_status=final_status,
        reason=reason,
        report_path=None,
        journal_path=None,
    )


def _render_report(report: AutomatedDryRunReport) -> str:
    return f"""# Automated Proposal Dry-Run Report

## Summary

- Symbol: {report.symbol}
- Mode: {report.mode}
- Data integrity status: {report.data_integrity_status}
- Market context result: {report.market_context_result.status} - {report.market_context_result.reason}
- Liquidity result: {report.liquidity_result.status} - {report.liquidity_result.reason}
- Session timing result: {report.session_timing_result.status} - {report.session_timing_result.reason}
- Confirmation result: {report.confirmation_result.status} - {report.confirmation_result.reason}
- Decision: {report.decision}
- Strategy evaluation status: {report.strategy_evaluation_status}
- Evaluation gate status: {report.evaluation_gate_status}
- Negative-case regression status: {report.negative_case_regression_status}
- Risk dry-run status: {report.risk_dry_run_status}
- Journal reference: {report.journal_reference}
- Final status: {report.final_status}
- Reason: {report.reason}

## Safety

No order was sent.
No Paper Order Request was created.
Live trading remains unsupported.
Paper send readiness: false.
Broker execution readiness: false.
Human Approval request created: false.
Manual Execution Confirmation request created: false.
"""


def _timestamped_report_dir(output_root: Path) -> Path:
    report_dir = output_root / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = 1
    while report_dir.exists():
        report_dir = output_root / f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{suffix}"
        suffix += 1
    report_dir.mkdir(parents=True, exist_ok=False)
    return report_dir


class _JournalFixture:
    def __init__(self, decision: str) -> None:
        self.reason_for_final_decision = f"Automated dry-run decision: {decision}."
        self.lessons_or_notes = (
            "Dry-run only; no approval, request, send, broker readiness, or live trading."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run automated proposal dry-run.")
    parser.add_argument("--symbol", action="append", required=True)
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="proposal")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = run_automated_proposal_dry_run(symbols=args.symbol, scenario=args.scenario)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(report.final_status)
        print(report.report_path)
    return 0 if report.final_status != AUTOMATED_DRY_RUN_BLOCKED else 1


if __name__ == "__main__":
    raise SystemExit(main())
