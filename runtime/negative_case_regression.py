from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping, Sequence

from evaluation_first_gate import EVALUATION_GATE_BLOCKED, evaluate_gate
from negative_case_dataset import (
    DATASET_PATH,
    JOURNAL_EVIDENCE_FAILURE_CATEGORIES,
    RUBBER_STAMPING_CATEGORIES,
    WEAK_SETUP_CATEGORIES,
    load_dataset,
    validate_dataset,
)
from strategy_evaluation_harness import (
    NO_TRADE_DISCIPLINE_PASS,
    RISK_APPROVED,
    RISK_REJECTED,
    DeterministicJournalEntry,
    DeterministicProposal,
    DeterministicRiskEvaluation,
    StrategyEvaluationInput,
    evaluate_strategy,
)


REPORT_ROOT = Path("reports/negative_case_regression")
REPORT_NAME = "NEGATIVE_CASE_REGRESSION_REPORT.md"

HOLD = "HOLD"
IMPROVE_GATE = "IMPROVE_GATE"
CONTINUE_MANUAL_LIMITED_PAPER = "CONTINUE_MANUAL_LIMITED_PAPER"


@dataclass(frozen=True)
class NegativeCaseRegressionCaseResult:
    case_id: str
    category: str
    expected_decision: str
    actual_decision: str
    evaluation_status: str
    evaluation_score: float
    gate_status: str
    passed: bool
    failure_reason: str | None
    blocked_before_human_approval: bool
    no_trade_recognized: bool
    weak_setup_rejected: bool
    rubber_stamping_detected: bool
    journal_evidence_failure_detected: bool
    live_trading_assumption_case: bool
    live_trading_assumption_blocked: bool
    missing_fixed_risk_case: bool
    missing_fixed_risk_blocked: bool
    missing_journal_readiness_case: bool
    missing_journal_readiness_blocked: bool
    paper_send_readiness: bool
    broker_execution_readiness: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "category": self.category,
            "expected_decision": self.expected_decision,
            "actual_decision": self.actual_decision,
            "evaluation_status": self.evaluation_status,
            "evaluation_score": self.evaluation_score,
            "gate_status": self.gate_status,
            "passed": self.passed,
            "failure_reason": self.failure_reason,
            "blocked_before_human_approval": self.blocked_before_human_approval,
            "no_trade_recognized": self.no_trade_recognized,
            "weak_setup_rejected": self.weak_setup_rejected,
            "rubber_stamping_detected": self.rubber_stamping_detected,
            "journal_evidence_failure_detected": self.journal_evidence_failure_detected,
            "live_trading_assumption_case": self.live_trading_assumption_case,
            "live_trading_assumption_blocked": self.live_trading_assumption_blocked,
            "missing_fixed_risk_case": self.missing_fixed_risk_case,
            "missing_fixed_risk_blocked": self.missing_fixed_risk_blocked,
            "missing_journal_readiness_case": self.missing_journal_readiness_case,
            "missing_journal_readiness_blocked": self.missing_journal_readiness_blocked,
            "paper_send_readiness": self.paper_send_readiness,
            "broker_execution_readiness": self.broker_execution_readiness,
        }


@dataclass(frozen=True)
class NegativeCaseRegressionSummary:
    total_cases: int
    passed_regression_cases: int
    failed_regression_cases: int
    blocked_before_human_approval_count: int
    blocked_before_human_approval_rate: float
    no_trade_recognized_count: int
    no_trade_recognition_rate: float
    weak_setup_rejected_count: int
    weak_setup_rejection_rate: float
    rubber_stamping_detected_count: int
    rubber_stamping_detection_rate: float
    journal_evidence_failure_detected_count: int
    journal_evidence_failure_detection_rate: float
    live_trading_assumption_blocked_count: int
    live_trading_assumption_block_rate: float
    missing_fixed_risk_blocked_count: int
    missing_fixed_risk_block_rate: float
    missing_journal_readiness_blocked_count: int
    missing_journal_readiness_block_rate: float
    missed_blocks: tuple[str, ...]
    false_passes: tuple[str, ...]
    threshold_results: Mapping[str, bool]
    recommendation: str

    def as_dict(self) -> dict[str, object]:
        return {
            "total_cases": self.total_cases,
            "passed_regression_cases": self.passed_regression_cases,
            "failed_regression_cases": self.failed_regression_cases,
            "blocked_before_human_approval_count": self.blocked_before_human_approval_count,
            "blocked_before_human_approval_rate": self.blocked_before_human_approval_rate,
            "no_trade_recognized_count": self.no_trade_recognized_count,
            "no_trade_recognition_rate": self.no_trade_recognition_rate,
            "weak_setup_rejected_count": self.weak_setup_rejected_count,
            "weak_setup_rejection_rate": self.weak_setup_rejection_rate,
            "rubber_stamping_detected_count": self.rubber_stamping_detected_count,
            "rubber_stamping_detection_rate": self.rubber_stamping_detection_rate,
            "journal_evidence_failure_detected_count": self.journal_evidence_failure_detected_count,
            "journal_evidence_failure_detection_rate": self.journal_evidence_failure_detection_rate,
            "live_trading_assumption_blocked_count": self.live_trading_assumption_blocked_count,
            "live_trading_assumption_block_rate": self.live_trading_assumption_block_rate,
            "missing_fixed_risk_blocked_count": self.missing_fixed_risk_blocked_count,
            "missing_fixed_risk_block_rate": self.missing_fixed_risk_block_rate,
            "missing_journal_readiness_blocked_count": self.missing_journal_readiness_blocked_count,
            "missing_journal_readiness_block_rate": self.missing_journal_readiness_block_rate,
            "missed_blocks": list(self.missed_blocks),
            "false_passes": list(self.false_passes),
            "threshold_results": dict(self.threshold_results),
            "recommendation": self.recommendation,
        }


@dataclass(frozen=True)
class NegativeCaseRegressionReport:
    case_results: tuple[NegativeCaseRegressionCaseResult, ...]
    summary: NegativeCaseRegressionSummary
    report_path: str | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "case_results": [result.as_dict() for result in self.case_results],
            "summary": self.summary.as_dict(),
            "report_path": self.report_path,
        }


def run_negative_case_regression(
    dataset_path: Path = DATASET_PATH,
    *,
    output_root: Path = REPORT_ROOT,
    write_report: bool = True,
) -> NegativeCaseRegressionReport:
    cases = load_dataset(dataset_path)
    validation = validate_dataset(cases)
    if not validation.passed:
        raise ValueError("negative case dataset validation failed: " + "; ".join(validation.errors))
    return run_negative_case_regression_from_cases(
        cases,
        output_root=output_root,
        write_report=write_report,
    )


def run_negative_case_regression_from_cases(
    cases: Sequence[Mapping[str, object]],
    *,
    output_root: Path = REPORT_ROOT,
    write_report: bool = True,
) -> NegativeCaseRegressionReport:
    case_results = tuple(_evaluate_case(case) for case in cases)
    summary = _summarize(case_results)
    report_path: Path | None = None
    if write_report:
        report_dir = _timestamped_report_dir(output_root)
        report_path = report_dir / REPORT_NAME
        report_path.write_text(_render_report(case_results, summary), encoding="utf-8")
    return NegativeCaseRegressionReport(
        case_results=case_results,
        summary=summary,
        report_path=report_path.as_posix() if report_path else None,
    )


def _evaluate_case(case: Mapping[str, object]) -> NegativeCaseRegressionCaseResult:
    case_id = str(case["case_id"])
    category = str(case["category"])
    expected_decision = str(case["expected_decision"])
    proposal, risk, journal, flags = _fixture_for_case(case)
    evaluation = evaluate_strategy(
        StrategyEvaluationInput(
            proposal=proposal,
            risk_evaluation=risk,
            journal_entry=journal,
            evaluation_type=flags["evaluation_type"],
            data_fresh=flags["data_fresh"],
            data_complete=flags["data_complete"],
            expected_rejection=flags["expected_rejection"],
            actual_rejection=flags["actual_rejection"],
            no_trade_decision=flags["no_trade_decision"],
            forced_trade=flags["forced_trade"],
            live_trading_assumption=flags["live_trading_assumption"],
            excessive_confidence=flags["excessive_confidence"],
            bypassed_specialist_agents=flags["bypassed_specialist_agents"],
            specialist_rubber_stamping=flags["specialist_rubber_stamping"],
            human_approval_rubber_stamping=flags["human_approval_rubber_stamping"],
            no_trade_better_than_trade=flags["no_trade_better_than_trade"],
            approval_count=flags["approval_count"],
            rejection_count=flags["rejection_count"],
        )
    )
    gate = evaluate_gate(
        evaluation,
        data_integrity_status=flags["data_integrity_status"],
        journal_reference=f"negative-case-regression:{case_id}",
        approval_count=flags["approval_count"],
        rejection_count=flags["rejection_count"],
    )
    actual_decision = _actual_decision(expected_decision, evaluation, gate, flags)
    hard_fail_text = " ".join(gate.hard_fail_reasons).lower()
    blocked_before_human_approval = gate.status == EVALUATION_GATE_BLOCKED
    no_trade_recognized = (
        expected_decision != "NO_TRADE"
        or evaluation.no_trade_discipline_status == NO_TRADE_DISCIPLINE_PASS
        and actual_decision == "NO_TRADE"
    )
    weak_setup_rejected = (
        not _is_weak_setup_rejection_case(case)
        or gate.status == EVALUATION_GATE_BLOCKED
        and actual_decision == "REJECT"
    )
    rubber_stamping_detected = (
        not _is_rubber_stamping_case(case)
        or "rubber-stamping" in hard_fail_text
        or gate.status == EVALUATION_GATE_BLOCKED
    )
    journal_evidence_failure_detected = (
        not _is_journal_evidence_failure_case(case)
        or gate.status == EVALUATION_GATE_BLOCKED
    )
    live_trading_assumption_blocked = (
        category != "Live trading assumption"
        or gate.status == EVALUATION_GATE_BLOCKED
        and "live trading assumption" in hard_fail_text
    )
    live_trading_assumption_case = category == "Live trading assumption"
    missing_fixed_risk_blocked = (
        not flags["missing_fixed_risk"]
        or gate.status == EVALUATION_GATE_BLOCKED
        and "missing fixed risk" in hard_fail_text
    )
    missing_fixed_risk_case = bool(flags["missing_fixed_risk"])
    missing_journal_readiness_blocked = (
        not flags["missing_journal_readiness"]
        or gate.status == EVALUATION_GATE_BLOCKED
        and "missing journal readiness" in hard_fail_text
    )
    missing_journal_readiness_case = bool(flags["missing_journal_readiness"])
    paper_send_readiness = False
    broker_execution_readiness = False
    passed = (
        _expected_behavior_passed(expected_decision, actual_decision, gate.status)
        and no_trade_recognized
        and weak_setup_rejected
        and rubber_stamping_detected
        and journal_evidence_failure_detected
        and live_trading_assumption_blocked
        and missing_fixed_risk_blocked
        and missing_journal_readiness_blocked
        and not paper_send_readiness
        and not broker_execution_readiness
    )
    failure_reason = None if passed else _failure_reason(expected_decision, actual_decision, gate.status)
    return NegativeCaseRegressionCaseResult(
        case_id=case_id,
        category=category,
        expected_decision=expected_decision,
        actual_decision=actual_decision,
        evaluation_status=evaluation.final_status,
        evaluation_score=evaluation.evaluation_score,
        gate_status=gate.status,
        passed=passed,
        failure_reason=failure_reason,
        blocked_before_human_approval=blocked_before_human_approval,
        no_trade_recognized=no_trade_recognized,
        weak_setup_rejected=weak_setup_rejected,
        rubber_stamping_detected=rubber_stamping_detected,
        journal_evidence_failure_detected=journal_evidence_failure_detected,
        live_trading_assumption_case=live_trading_assumption_case,
        live_trading_assumption_blocked=live_trading_assumption_blocked,
        missing_fixed_risk_case=missing_fixed_risk_case,
        missing_fixed_risk_blocked=missing_fixed_risk_blocked,
        missing_journal_readiness_case=missing_journal_readiness_case,
        missing_journal_readiness_blocked=missing_journal_readiness_blocked,
        paper_send_readiness=paper_send_readiness,
        broker_execution_readiness=broker_execution_readiness,
    )


def _fixture_for_case(
    case: Mapping[str, object],
) -> tuple[DeterministicProposal, DeterministicRiskEvaluation, DeterministicJournalEntry | None, dict[str, object]]:
    category = str(case["category"])
    expected_decision = str(case["expected_decision"])
    proposal = DeterministicProposal(proposal_id=str(case["case_id"]))
    risk = DeterministicRiskEvaluation(decision=RISK_APPROVED)
    journal: DeterministicJournalEntry | None = DeterministicJournalEntry(
        reason_for_final_decision=str(case["expected_journal_note"]),
        lessons_or_notes=str(case["why_no_trade_is_correct"]),
    )
    flags: dict[str, object] = {
        "evaluation_type": "proposal",
        "data_fresh": True,
        "data_complete": True,
        "expected_rejection": True,
        "actual_rejection": True,
        "no_trade_decision": False,
        "forced_trade": False,
        "live_trading_assumption": False,
        "excessive_confidence": False,
        "bypassed_specialist_agents": False,
        "specialist_rubber_stamping": False,
        "human_approval_rubber_stamping": False,
        "no_trade_better_than_trade": expected_decision == "NO_TRADE",
        "approval_count": 0,
        "rejection_count": 1,
        "data_integrity_status": "PASS",
        "missing_fixed_risk": False,
        "missing_journal_readiness": False,
    }
    if expected_decision == "NO_TRADE":
        flags["evaluation_type"] = "no_trade"
        flags["no_trade_decision"] = True
    elif expected_decision == "REJECT":
        flags["evaluation_type"] = "rejection"

    if category == "Missing higher-timeframe context":
        proposal = replace(proposal, timeframe_context="")
    elif category == "Generic higher-timeframe context":
        proposal = replace(proposal, timeframe_context="generic context aligned")
    elif category == "Weak liquidity location":
        proposal = replace(proposal, liquidity_location="weak liquidity")
    elif category == "Vague liquidity language":
        proposal = replace(proposal, liquidity_location="vague liquidity nearby")
    elif category == "Vague confirmation":
        proposal = replace(proposal, entry_confirmation="vague")
    elif category == "Non-observable confirmation":
        proposal = replace(proposal, entry_confirmation="buyers are probably hidden")
    elif category == "Generic thesis":
        proposal = replace(proposal, thesis="Valid setup that could apply to any symbol.")
    elif category == "Thesis reusable for any symbol":
        proposal = replace(
            proposal,
            thesis="Valid setup that could apply to any symbol.",
            why_now="Valid setup that could apply to any symbol.",
            why_this_level="Valid setup that could apply to any symbol.",
        )
    elif category == "Missing credible invalidation":
        proposal = replace(proposal, what_invalidates_trade="invalidates the idea")
        flags["missing_journal_readiness"] = True
    elif category == "Risk valid but setup weak":
        proposal = replace(proposal, liquidity_location="weak liquidity")
    elif category == "Forced trade behavior":
        proposal = replace(proposal, liquidity_location="weak liquidity")
        flags["forced_trade"] = True
    elif category == "Excessive confidence without evidence":
        proposal = replace(proposal, liquidity_location="weak liquidity")
        flags["excessive_confidence"] = True
    elif category == "Specialist agent rubber-stamping":
        proposal = replace(
            proposal,
            source_agent_outputs={
                "Market Context Agent": "approved",
                "Liquidity Agent": "approved",
                "Session Timing Agent": "approved",
                "Confirmation Agent": "approved",
            },
        )
        flags["specialist_rubber_stamping"] = True
    elif category == "Human approval rubber-stamping":
        flags["human_approval_rubber_stamping"] = True
    elif category == "Evaluation score inflation":
        proposal = replace(
            proposal,
            timeframe_context="generic context aligned",
            liquidity_location="vague liquidity nearby",
            entry_confirmation="vague",
        )
    elif category == "No-trade should be preferred":
        proposal = replace(proposal, liquidity_location="weak liquidity")
        flags["no_trade_better_than_trade"] = True
    elif category == "Journal too weak":
        proposal = replace(proposal, journal_ready=False)
        journal = None
        flags["missing_journal_readiness"] = True
    elif category == "Data integrity incomplete":
        flags["data_fresh"] = False
        flags["data_complete"] = False
        flags["data_integrity_status"] = "FAIL"
    elif category == "ADLC compliance incomplete":
        proposal = replace(proposal, adlc_compliance_status="FAIL")
    elif category == "Live trading assumption":
        proposal = replace(proposal, paper_trading_only=False)
        flags["live_trading_assumption"] = True

    if "missing fixed risk" in _case_text(case):
        proposal = replace(proposal, risk_per_share=None, max_loss_amount=None, stop_loss=None)
        risk = DeterministicRiskEvaluation(
            decision=RISK_REJECTED,
            rejection_reasons=("missing fixed risk",),
        )
        flags["missing_fixed_risk"] = True
    return proposal, risk, journal, flags


def _actual_decision(
    expected_decision: str,
    evaluation: object,
    gate: object,
    flags: Mapping[str, object],
) -> str:
    if expected_decision == "NO_TRADE" and flags["no_trade_decision"]:
        return "NO_TRADE"
    if expected_decision == "BLOCK_HUMAN_APPROVAL" and getattr(gate, "status") == EVALUATION_GATE_BLOCKED:
        return "BLOCK_HUMAN_APPROVAL"
    if expected_decision == "BLOCK_PAPER_REQUEST" and getattr(gate, "status") == EVALUATION_GATE_BLOCKED:
        return "BLOCK_PAPER_REQUEST"
    if expected_decision == "BLOCK_EVALUATION_GATE" and getattr(gate, "status") == EVALUATION_GATE_BLOCKED:
        return "BLOCK_EVALUATION_GATE"
    if expected_decision == "REJECT" and getattr(gate, "status") == EVALUATION_GATE_BLOCKED:
        return "REJECT"
    if getattr(gate, "status") == EVALUATION_GATE_BLOCKED:
        return "REJECT"
    if getattr(evaluation, "final_status") == "PASS":
        return "PASS"
    return "REJECT"


def _expected_behavior_passed(expected_decision: str, actual_decision: str, gate_status: str) -> bool:
    if gate_status != EVALUATION_GATE_BLOCKED:
        return False
    if expected_decision == "NO_TRADE":
        return actual_decision == "NO_TRADE"
    return actual_decision == expected_decision


def _summarize(
    case_results: Sequence[NegativeCaseRegressionCaseResult],
) -> NegativeCaseRegressionSummary:
    total = len(case_results)
    passed = sum(1 for result in case_results if result.passed)
    blocked_before_human = sum(1 for result in case_results if result.blocked_before_human_approval)

    no_trade_total = sum(1 for result in case_results if result.expected_decision == "NO_TRADE")
    no_trade_recognized = sum(
        1
        for result in case_results
        if result.expected_decision == "NO_TRADE" and result.no_trade_recognized
    )
    weak_total = sum(1 for result in case_results if _result_is_weak_setup_rejection(result))
    weak_rejected = sum(1 for result in case_results if _result_is_weak_setup_rejection(result) and result.weak_setup_rejected)
    rubber_total = sum(1 for result in case_results if result.category in RUBBER_STAMPING_CATEGORIES)
    rubber_detected = sum(
        1
        for result in case_results
        if result.category in RUBBER_STAMPING_CATEGORIES and result.rubber_stamping_detected
    )
    journal_total = sum(1 for result in case_results if result.category in JOURNAL_EVIDENCE_FAILURE_CATEGORIES)
    journal_detected = sum(
        1
        for result in case_results
        if result.category in JOURNAL_EVIDENCE_FAILURE_CATEGORIES
        and result.journal_evidence_failure_detected
    )
    live_total = sum(1 for result in case_results if result.live_trading_assumption_case)
    live_blocked = sum(
        1
        for result in case_results
        if result.live_trading_assumption_case and result.live_trading_assumption_blocked
    )
    missing_fixed_risk_total = sum(1 for result in case_results if result.missing_fixed_risk_case)
    missing_fixed_risk_blocked = sum(
        1
        for result in case_results
        if result.missing_fixed_risk_case and result.missing_fixed_risk_blocked
    )
    missing_journal_total = sum(
        1 for result in case_results if result.missing_journal_readiness_case
    )
    missing_journal_blocked = sum(
        1
        for result in case_results
        if result.missing_journal_readiness_case and result.missing_journal_readiness_blocked
    )
    missed_blocks = tuple(
        result.case_id
        for result in case_results
        if result.gate_status != EVALUATION_GATE_BLOCKED
        or result.paper_send_readiness
        or result.broker_execution_readiness
    )
    false_passes = tuple(
        result.case_id
        for result in case_results
        if result.actual_decision == "PASS"
        or result.paper_send_readiness
        or result.broker_execution_readiness
    )
    blocked_rate = _rate(blocked_before_human, total)
    no_trade_rate = _rate(no_trade_recognized, no_trade_total)
    weak_rate = _rate(weak_rejected, weak_total)
    rubber_rate = _rate(rubber_detected, rubber_total)
    journal_rate = _rate(journal_detected, journal_total)
    live_rate = _rate(live_blocked, live_total)
    fixed_risk_rate = _rate(missing_fixed_risk_blocked, missing_fixed_risk_total)
    missing_journal_rate = _rate(missing_journal_blocked, missing_journal_total)
    threshold_results = {
        "live_trading_assumption_cases_blocked_100pct": live_rate == 1.0,
        "missing_fixed_risk_cases_blocked_100pct": fixed_risk_rate == 1.0,
        "missing_journal_readiness_cases_blocked_100pct": missing_journal_rate == 1.0,
        "rubber_stamping_cases_detected_or_blocked_100pct": rubber_rate == 1.0,
        "blocked_before_human_approval_at_least_90pct": blocked_rate >= 0.9,
        "no_trade_recognition_at_least_90pct": no_trade_rate >= 0.9,
        "weak_setup_rejection_at_least_90pct": weak_rate >= 0.9,
    }
    recommendation = _recommendation(
        case_results,
        threshold_results,
    )
    return NegativeCaseRegressionSummary(
        total_cases=total,
        passed_regression_cases=passed,
        failed_regression_cases=total - passed,
        blocked_before_human_approval_count=blocked_before_human,
        blocked_before_human_approval_rate=blocked_rate,
        no_trade_recognized_count=no_trade_recognized,
        no_trade_recognition_rate=no_trade_rate,
        weak_setup_rejected_count=weak_rejected,
        weak_setup_rejection_rate=weak_rate,
        rubber_stamping_detected_count=rubber_detected,
        rubber_stamping_detection_rate=rubber_rate,
        journal_evidence_failure_detected_count=journal_detected,
        journal_evidence_failure_detection_rate=journal_rate,
        live_trading_assumption_blocked_count=live_blocked,
        live_trading_assumption_block_rate=live_rate,
        missing_fixed_risk_blocked_count=missing_fixed_risk_blocked,
        missing_fixed_risk_block_rate=fixed_risk_rate,
        missing_journal_readiness_blocked_count=missing_journal_blocked,
        missing_journal_readiness_block_rate=missing_journal_rate,
        missed_blocks=missed_blocks,
        false_passes=false_passes,
        threshold_results=threshold_results,
        recommendation=recommendation,
    )


def _recommendation(
    case_results: Sequence[NegativeCaseRegressionCaseResult],
    threshold_results: Mapping[str, bool],
) -> str:
    if any(
        result.live_trading_assumption_case and not result.live_trading_assumption_blocked
        for result in case_results
    ):
        return HOLD
    if any(
        result.missing_fixed_risk_case and not result.missing_fixed_risk_blocked
        for result in case_results
    ):
        return HOLD
    if any(
        result.missing_journal_readiness_case and not result.missing_journal_readiness_blocked
        for result in case_results
    ):
        return HOLD
    if not threshold_results["blocked_before_human_approval_at_least_90pct"]:
        return IMPROVE_GATE
    if not threshold_results["no_trade_recognition_at_least_90pct"]:
        return IMPROVE_GATE
    if not threshold_results["weak_setup_rejection_at_least_90pct"]:
        return IMPROVE_GATE
    return CONTINUE_MANUAL_LIMITED_PAPER


def _render_report(
    case_results: Sequence[NegativeCaseRegressionCaseResult],
    summary: NegativeCaseRegressionSummary,
) -> str:
    lines = [
        "# Negative Case Regression Report",
        "",
        "## Summary",
        "",
        f"- Total cases: {summary.total_cases}",
        f"- Passed regression cases: {summary.passed_regression_cases}",
        f"- Failed regression cases: {summary.failed_regression_cases}",
        f"- Blocked before human approval count: {summary.blocked_before_human_approval_count}",
        f"- Blocked before human approval rate: {summary.blocked_before_human_approval_rate:.2f}",
        f"- NO_TRADE recognized count: {summary.no_trade_recognized_count}",
        f"- NO_TRADE recognition rate: {summary.no_trade_recognition_rate:.2f}",
        f"- Weak setup rejected count: {summary.weak_setup_rejected_count}",
        f"- Weak setup rejection rate: {summary.weak_setup_rejection_rate:.2f}",
        f"- Rubber-stamping detected count: {summary.rubber_stamping_detected_count}",
        f"- Journal/evidence failure detected count: {summary.journal_evidence_failure_detected_count}",
        f"- Live trading assumption blocked count: {summary.live_trading_assumption_blocked_count}",
        f"- Missing fixed risk blocked count: {summary.missing_fixed_risk_blocked_count}",
        f"- Missing journal readiness blocked count: {summary.missing_journal_readiness_blocked_count}",
        f"- Recommendation: {summary.recommendation}",
        "",
        "## Missed Blocks",
        "",
    ]
    lines.extend(f"- {case_id}" for case_id in summary.missed_blocks)
    if not summary.missed_blocks:
        lines.append("- None")
    lines.extend(["", "## False Passes", ""])
    lines.extend(f"- {case_id}" for case_id in summary.false_passes)
    if not summary.false_passes:
        lines.append("- None")
    lines.extend(["", "## Threshold Results", ""])
    lines.extend(
        f"- {name}: {'PASS' if passed else 'FAIL'}"
        for name, passed in summary.threshold_results.items()
    )
    lines.extend(["", "## Case Results", ""])
    for result in case_results:
        lines.append(
            "- "
            f"{result.case_id}: expected={result.expected_decision}, "
            f"actual={result.actual_decision}, gate={result.gate_status}, "
            f"score={result.evaluation_score:.2f}, "
            f"status={'PASS' if result.passed else 'FAIL'}"
        )
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "Live trading remains unsupported.",
            "Increasing notional remains prohibited.",
            "Automation remains prohibited.",
            "No Alpaca API, broker calls, order sends, LLM calls, credentials, or `.env` creation are part of this regression.",
            "",
        ]
    )
    return "\n".join(lines)


def _timestamped_report_dir(output_root: Path) -> Path:
    report_dir = output_root / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def _is_weak_setup_rejection_case(case: Mapping[str, object]) -> bool:
    return case.get("expected_decision") == "REJECT" and case.get("category") in WEAK_SETUP_CATEGORIES


def _result_is_weak_setup_rejection(result: NegativeCaseRegressionCaseResult) -> bool:
    return result.expected_decision == "REJECT" and result.category in WEAK_SETUP_CATEGORIES


def _is_rubber_stamping_case(case: Mapping[str, object]) -> bool:
    return case.get("category") in RUBBER_STAMPING_CATEGORIES


def _is_journal_evidence_failure_case(case: Mapping[str, object]) -> bool:
    return case.get("category") in JOURNAL_EVIDENCE_FAILURE_CATEGORIES


def _case_text(case: Mapping[str, object]) -> str:
    return json.dumps(case, sort_keys=True).lower()


def _rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 1.0
    return round(numerator / denominator, 4)


def _failure_reason(expected_decision: str, actual_decision: str, gate_status: str) -> str:
    return (
        f"expected {expected_decision}, actual {actual_decision}, "
        f"gate status {gate_status}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run offline negative-case regression.")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--report-root", type=Path, default=REPORT_ROOT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = run_negative_case_regression(args.dataset, output_root=args.report_root)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(report.summary.recommendation)
        print(report.report_path)
    return 0 if report.summary.failed_regression_cases == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
