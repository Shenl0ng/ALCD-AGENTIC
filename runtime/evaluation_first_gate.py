from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from strategy_evaluation_harness import EVALUATION_PASS, StrategyEvaluationReport


EVALUATION_GATE_PASSED = "EVALUATION_GATE_PASSED"
EVALUATION_GATE_BLOCKED = "EVALUATION_GATE_BLOCKED"
DATA_INTEGRITY_PASS = "PASS"
MINIMUM_EVALUATION_SCORE = 2.8
APPROVAL_RATE_WARNING_THRESHOLD = 0.6
APPROVAL_RATE_HARD_BLOCK_THRESHOLD = 0.8

REQUIRED_PASSING_DIMENSIONS = {
    "higher_timeframe_context_quality": 2,
    "liquidity_location_quality": 3,
    "session_timing_quality": 2,
    "entry_confirmation_quality": 3,
    "fixed_risk_quality": 3,
    "reward_risk_quality": 2,
    "journal_readiness": 3,
    "data_freshness": 3,
    "data_completeness": 3,
    "specialist_agent_sequencing": 3,
    "risk_manager_decision_quality": 2,
}


@dataclass(frozen=True)
class EvaluationGateResult:
    proposal_id: str | None
    status: str
    score: float
    failed_dimensions: tuple[str, ...]
    hard_fail_reasons: tuple[str, ...]
    required_improvements: tuple[str, ...]
    adlc_status: str
    data_integrity_status: str
    dimensions_passed: tuple[str, ...]
    journal_reference: str | None = None
    soft_warning_reasons: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return self.status == EVALUATION_GATE_PASSED

    def as_dict(self) -> dict[str, object]:
        payload = {
            "proposal_id": self.proposal_id,
            "status": self.status,
            "score": self.score,
            "adlc_status": self.adlc_status,
            "data_integrity_status": self.data_integrity_status,
            "journal_reference": self.journal_reference,
            "soft_warning_reasons": list(self.soft_warning_reasons),
        }
        if self.passed:
            payload["dimensions_passed"] = list(self.dimensions_passed)
        else:
            payload["failed_dimensions"] = list(self.failed_dimensions)
            payload["hard_fail_reasons"] = list(self.hard_fail_reasons)
            payload["required_improvements"] = list(self.required_improvements)
        return payload


@dataclass(frozen=True)
class EvaluationGateJournalEntry:
    timestamp: str
    proposal_id: str | None
    event_type: str
    gate_status: str
    score_summary: str
    hard_fail_reasons: tuple[str, ...]
    reason_for_final_decision: str
    lessons_or_notes: str

    def as_dict(self) -> dict[str, object]:
        return {
            "timestamp": self.timestamp,
            "proposal_id": self.proposal_id,
            "event_type": self.event_type,
            "gate_status": self.gate_status,
            "score_summary": self.score_summary,
            "hard_fail_reasons": list(self.hard_fail_reasons),
            "reason_for_final_decision": self.reason_for_final_decision,
            "lessons_or_notes": self.lessons_or_notes,
        }


def evaluate_gate(
    evaluation_report: StrategyEvaluationReport | None,
    *,
    data_integrity_status: str = DATA_INTEGRITY_PASS,
    journal_reference: str | None = None,
    approval_count: int = 0,
    rejection_count: int = 0,
) -> EvaluationGateResult:
    if evaluation_report is None:
        return EvaluationGateResult(
            proposal_id=None,
            status=EVALUATION_GATE_BLOCKED,
            score=0.0,
            failed_dimensions=("strategy_evaluation_report",),
            hard_fail_reasons=("missing strategy evaluation report",),
            required_improvements=("Run Strategy Evaluation Harness before human approval.",),
            adlc_status="FAIL",
            data_integrity_status=data_integrity_status,
            dimensions_passed=(),
            journal_reference=journal_reference,
            soft_warning_reasons=(),
        )

    dimensions = dict(evaluation_report.dimension_scores)
    failed_dimensions = _failed_dimensions(dimensions)
    hard_fail_reasons = _hard_fail_reasons(evaluation_report, data_integrity_status)
    soft_warnings = _soft_warning_reasons(
        evaluation_report,
        approval_count=approval_count,
        rejection_count=rejection_count,
    )
    if evaluation_report.final_status != EVALUATION_PASS:
        hard_fail_reasons.append("strategy evaluation status is not PASS")
    if evaluation_report.evaluation_score < MINIMUM_EVALUATION_SCORE:
        hard_fail_reasons.append("minimum score threshold not met")
    if evaluation_report.adlc_compliance_status != "PASS":
        hard_fail_reasons.append("ADLC compliance is not PASS")

    status = EVALUATION_GATE_BLOCKED if hard_fail_reasons or failed_dimensions else EVALUATION_GATE_PASSED
    improvements = tuple(
        dict.fromkeys(
            list(evaluation_report.improvement_recommendations)
            + [f"Fix: {reason}." for reason in hard_fail_reasons]
            + [f"Improve {dimension}." for dimension in failed_dimensions]
        )
    )
    return EvaluationGateResult(
        proposal_id=evaluation_report.proposal_id,
        status=status,
        score=evaluation_report.evaluation_score,
        failed_dimensions=tuple(dict.fromkeys(failed_dimensions)),
        hard_fail_reasons=tuple(dict.fromkeys(hard_fail_reasons)),
        required_improvements=improvements,
        adlc_status=evaluation_report.adlc_compliance_status,
        data_integrity_status=data_integrity_status,
        dimensions_passed=_dimensions_passed(dimensions) if status == EVALUATION_GATE_PASSED else (),
        journal_reference=journal_reference,
        soft_warning_reasons=tuple(dict.fromkeys(soft_warnings)),
    )


def evaluation_gate_journal_entry(result: EvaluationGateResult) -> EvaluationGateJournalEntry:
    event_type = "evaluation_gate_passed" if result.passed else "evaluation_gate_blocked"
    reasons = result.hard_fail_reasons
    decision = result.status if result.passed else "; ".join(reasons or result.failed_dimensions)
    return EvaluationGateJournalEntry(
        timestamp="2026-05-20T00:00:00+00:00",
        proposal_id=result.proposal_id,
        event_type=event_type,
        gate_status=result.status,
        score_summary=f"score={result.score}",
        hard_fail_reasons=reasons,
        reason_for_final_decision=decision,
        lessons_or_notes="Evaluation gate completed; no order action was taken.",
    )


def evaluation_gate_passed(result: EvaluationGateResult | None) -> bool:
    return result is not None and result.status == EVALUATION_GATE_PASSED


def _failed_dimensions(dimensions: Mapping[str, int]) -> list[str]:
    failed: list[str] = []
    for dimension, minimum in REQUIRED_PASSING_DIMENSIONS.items():
        if dimensions.get(dimension, 0) < minimum:
            failed.append(dimension)
    return failed


def _dimensions_passed(dimensions: Mapping[str, int]) -> tuple[str, ...]:
    return tuple(
        dimension
        for dimension, minimum in REQUIRED_PASSING_DIMENSIONS.items()
        if dimensions.get(dimension, 0) >= minimum
    )


def _hard_fail_reasons(
    evaluation_report: StrategyEvaluationReport,
    data_integrity_status: str,
) -> list[str]:
    dimensions = evaluation_report.dimension_scores
    reasons = list(evaluation_report.rejection_reasons)
    if "live trading assumption" in reasons:
        reasons.append("live trading assumption")
    if dimensions.get("fixed_risk_quality", 0) < 3:
        reasons.append("missing fixed risk")
    if dimensions.get("journal_readiness", 0) < 3:
        reasons.append("missing journal readiness")
    if dimensions.get("specialist_agent_sequencing", 0) < 3:
        reasons.append("bypassed specialist agents")
    if (
        data_integrity_status != DATA_INTEGRITY_PASS
        or dimensions.get("data_freshness", 0) < 3
        or dimensions.get("data_completeness", 0) < 3
    ):
        reasons.append("missing data integrity")
    if "forced trade" in reasons:
        reasons.append("forced trade behavior")
    if dimensions.get("entry_confirmation_quality", 0) < 3:
        reasons.append("vague confirmation")
    if dimensions.get("liquidity_location_quality", 0) < 3:
        reasons.append("weak or missing liquidity location")
    if dimensions.get("higher_timeframe_context_quality", 0) < 3:
        reasons.append("missing higher-timeframe context")
    if "excessive confidence" in reasons:
        reasons.append("excessive confidence without evidence")
    if "generic higher-timeframe context" in reasons:
        reasons.append("generic higher-timeframe context")
    if "vague liquidity" in reasons:
        reasons.append("vague liquidity")
    if "vague confirmation" in reasons:
        reasons.append("vague confirmation")
    if "specialist agent rubber-stamping" in reasons:
        reasons.append("specialist agent rubber-stamping")
    if "human approval rubber-stamping" in reasons:
        reasons.append("human approval rubber-stamping")
    if "no-trade better than approval" in reasons:
        reasons.append("no-trade better than approval")
    if "generic thesis" in reasons:
        reasons.append("generic thesis")
    if "approval-rate hard block threshold active" in reasons:
        reasons.append("approval-rate hard block threshold active")
    return reasons


def _soft_warning_reasons(
    evaluation_report: StrategyEvaluationReport,
    *,
    approval_count: int,
    rejection_count: int,
) -> list[str]:
    warnings = [
        reason
        for reason in evaluation_report.rejection_reasons
        if reason == "approval-rate warning threshold active"
    ]
    total = approval_count + rejection_count
    if total > 0:
        rate = approval_count / total
        if rate >= APPROVAL_RATE_WARNING_THRESHOLD and rate < APPROVAL_RATE_HARD_BLOCK_THRESHOLD:
            warnings.append("approval-rate warning threshold active")
    return warnings
