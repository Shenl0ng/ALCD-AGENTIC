from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping


EVALUATION_PASS = "PASS"
EVALUATION_FAIL = "FAIL"
EVALUATION_NEEDS_REVIEW = "NEEDS_REVIEW"
RISK_APPROVED = "RISK_APPROVED"
RISK_REJECTED = "RISK_REJECTED"
MINIMUM_STRATEGY_EVALUATION_SCORE = 2.6

NO_TRADE_DISCIPLINE_PASS = "NO_TRADE_DISCIPLINE_PASS"
NO_TRADE_DISCIPLINE_FAIL = "NO_TRADE_DISCIPLINE_FAIL"

DIMENSIONS = (
    "higher_timeframe_context_quality",
    "liquidity_location_quality",
    "session_timing_quality",
    "entry_confirmation_quality",
    "fixed_risk_quality",
    "reward_risk_quality",
    "journal_readiness",
    "data_freshness",
    "data_completeness",
    "specialist_agent_sequencing",
    "risk_manager_decision_quality",
    "no_trade_discipline",
    "correct_rejection_of_weak_setups",
)

REQUIRED_SPECIALISTS = (
    "Market Context Agent",
    "Liquidity Agent",
    "Session Timing Agent",
    "Confirmation Agent",
)


@dataclass(frozen=True)
class StrategyEvaluationInput:
    proposal: object | None
    risk_evaluation: object | None
    journal_entry: object | None
    evaluation_type: str = "proposal"
    data_fresh: bool = True
    data_complete: bool = True
    expected_rejection: bool = False
    actual_rejection: bool = False
    no_trade_decision: bool = False
    forced_trade: bool = False
    live_trading_assumption: bool = False
    excessive_confidence: bool = False
    bypassed_specialist_agents: bool = False
    specialist_rubber_stamping: bool = False
    human_approval_rubber_stamping: bool = False
    no_trade_better_than_trade: bool = False
    approval_count: int = 0
    rejection_count: int = 0
    approval_rate_warning_threshold: float = 0.6
    approval_rate_hard_block_threshold: float = 0.8


@dataclass(frozen=True)
class StrategyEvaluationReport:
    evaluation_id: str
    proposal_id: str | None
    evaluation_score: float
    dimension_scores: Mapping[str, int]
    final_status: str
    rejection_reasons: tuple[str, ...]
    improvement_recommendations: tuple[str, ...]
    adlc_compliance_status: str
    no_trade_discipline_status: str

    def as_dict(self) -> dict[str, object]:
        return {
            "evaluation_id": self.evaluation_id,
            "proposal_id": self.proposal_id,
            "evaluation_score": self.evaluation_score,
            "dimension_scores": dict(self.dimension_scores),
            "final_status": self.final_status,
            "rejection_reasons": list(self.rejection_reasons),
            "improvement_recommendations": list(self.improvement_recommendations),
            "adlc_compliance_status": self.adlc_compliance_status,
            "no_trade_discipline_status": self.no_trade_discipline_status,
        }


def evaluate_strategy(input_data: StrategyEvaluationInput) -> StrategyEvaluationReport:
    proposal = input_data.proposal
    risk = input_data.risk_evaluation
    journal = input_data.journal_entry

    scores = {
        "higher_timeframe_context_quality": _context_score(_get(proposal, "timeframe_context")),
        "liquidity_location_quality": _liquidity_score(_get(proposal, "liquidity_location")),
        "session_timing_quality": _text_score(
            _get(proposal, "session_timing"), strong=("open", "valid", "window")
        ),
        "entry_confirmation_quality": _confirmation_score(_get(proposal, "entry_confirmation")),
        "fixed_risk_quality": _fixed_risk_score(proposal),
        "reward_risk_quality": _reward_risk_score(proposal),
        "journal_readiness": _journal_readiness_score(proposal, journal),
        "data_freshness": 3 if input_data.data_fresh else 0,
        "data_completeness": 3 if input_data.data_complete else 0,
        "specialist_agent_sequencing": _specialist_score(proposal, input_data),
        "risk_manager_decision_quality": _risk_score(risk, input_data),
        "no_trade_discipline": _no_trade_score(input_data),
        "correct_rejection_of_weak_setups": _rejection_score(input_data),
    }

    reasons = _rejection_reasons(input_data, scores)
    recommendations = _recommendations(reasons, scores)
    adlc_status = "PASS" if proposal and getattr(proposal, "adlc_compliance_status", None) == "PASS" else "FAIL"
    if input_data.live_trading_assumption:
        adlc_status = "FAIL"
    no_trade_status = (
        NO_TRADE_DISCIPLINE_PASS
        if scores["no_trade_discipline"] >= 2
        else NO_TRADE_DISCIPLINE_FAIL
    )
    score = round(sum(scores.values()) / len(DIMENSIONS), 2)
    final_status = _final_status(score, reasons, scores)
    proposal_id = getattr(proposal, "proposal_id", None) if proposal else None
    return StrategyEvaluationReport(
        evaluation_id=f"strategy-evaluation-{proposal_id or input_data.evaluation_type}",
        proposal_id=proposal_id,
        evaluation_score=score,
        dimension_scores=scores,
        final_status=final_status,
        rejection_reasons=tuple(dict.fromkeys(reasons)),
        improvement_recommendations=tuple(dict.fromkeys(recommendations)),
        adlc_compliance_status=adlc_status,
        no_trade_discipline_status=no_trade_status,
    )


def deterministic_valid_evaluation() -> StrategyEvaluationReport:
    proposal = DeterministicProposal()
    risk = DeterministicRiskEvaluation(decision=RISK_APPROVED)
    journal = DeterministicJournalEntry(
        reason_for_final_decision=(
            "Paper-only SIM proposal uses the 100.00 prior session low reclaim after a "
            "15-minute close above the level, with fixed risk and no-trade rejected only "
            "because context, liquidity, confirmation, and invalidation are specific."
        ),
        lessons_or_notes=(
            "Journal records the exact level, observable confirmation, stop at 98.00, "
            "and invalidation on a close back below the reclaimed prior-session low."
        ),
    )
    return evaluate_strategy(
        StrategyEvaluationInput(proposal=proposal, risk_evaluation=risk, journal_entry=journal)
    )


@dataclass(frozen=True)
class DeterministicRiskEvaluation:
    decision: str
    rejection_reasons: tuple[str, ...] = ()
    executable: bool = False


@dataclass(frozen=True)
class DeterministicJournalEntry:
    reason_for_final_decision: str
    lessons_or_notes: str


@dataclass(frozen=True)
class DeterministicProposal:
    proposal_id: str = "paper-market_open-001"
    timeframe_context: str = "Daily trend structure is above the prior 100.00 session low after a failed breakdown."
    liquidity_location: str = "Prior session low at 100.00 reclaim liquidity level"
    session_timing: str = "market_open"
    entry_confirmation: str = "15-minute candle close above 100.00 reclaim with hold above the level"
    risk_per_share: str = "2"
    max_loss_amount: str = "200"
    stop_loss: str = "98"
    expected_reward_risk: str = "2"
    thesis: str = "SIM paper-only long tests a reclaimed 100.00 prior-session low after failed downside liquidity."
    why_now: str = "Market-open timing follows the 15-minute close back above 100.00 with risk fixed before approval."
    why_this_level: str = "100.00 is the named prior-session low and failed breakdown liquidity reference."
    what_invalidates_trade: str = "A 15-minute close below 98.00 invalidates the reclaimed-low thesis."
    paper_trading_only: bool = True
    adlc_compliance_status: str = "PASS"
    journal_ready: bool = True
    source_agent_outputs: Mapping[str, str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.source_agent_outputs is None:
            object.__setattr__(
                self,
                "source_agent_outputs",
                {
                    "Market Context Agent": "PASS",
                    "Liquidity Agent": "PASS",
                    "Session Timing Agent": "PASS",
                    "Confirmation Agent": "PASS",
                },
            )


def _final_status(score: float, reasons: list[str], scores: Mapping[str, int]) -> str:
    if reasons:
        return EVALUATION_FAIL
    if any(scores[dimension] == 0 for dimension in ("fixed_risk_quality", "journal_readiness")):
        return EVALUATION_FAIL
    if score >= MINIMUM_STRATEGY_EVALUATION_SCORE:
        return EVALUATION_PASS
    return EVALUATION_NEEDS_REVIEW


def _rejection_reasons(
    input_data: StrategyEvaluationInput,
    scores: Mapping[str, int],
) -> list[str]:
    proposal = input_data.proposal
    risk = input_data.risk_evaluation
    reasons: list[str] = []
    if proposal is None:
        reasons.append("missing proposal")
    if input_data.live_trading_assumption or (proposal and not getattr(proposal, "paper_trading_only", False)):
        reasons.append("live trading assumption")
    if scores["fixed_risk_quality"] == 0:
        reasons.append("missing fixed risk")
    if scores["higher_timeframe_context_quality"] < 3:
        reasons.append("generic higher-timeframe context")
    if scores["liquidity_location_quality"] < 3:
        reasons.append("vague liquidity")
    if scores["entry_confirmation_quality"] < 3:
        reasons.append("vague confirmation")
    if scores["journal_readiness"] == 0:
        reasons.append("missing journal readiness")
    if proposal is not None and _generic_thesis(proposal):
        reasons.append("generic thesis")
    if scores["specialist_agent_sequencing"] == 0:
        reasons.append("bypassed specialist agents")
    if not input_data.data_fresh:
        reasons.append("stale data")
    if not input_data.data_complete:
        reasons.append("missing data fields")
    if risk is None:
        reasons.append("missing Risk Manager decision")
    elif getattr(risk, "decision", None) == RISK_REJECTED and input_data.evaluation_type == "proposal":
        reasons.append("Risk Manager rejected proposal")
    if input_data.forced_trade:
        reasons.append("forced trade")
    if input_data.excessive_confidence:
        reasons.append("excessive confidence")
    if input_data.specialist_rubber_stamping:
        reasons.append("specialist agent rubber-stamping")
    if input_data.human_approval_rubber_stamping:
        reasons.append("human approval rubber-stamping")
    if input_data.no_trade_better_than_trade:
        reasons.append("no-trade better than approval")
    if _approval_rate(input_data) >= input_data.approval_rate_hard_block_threshold:
        reasons.append("approval-rate hard block threshold active")
    return reasons


def _recommendations(reasons: list[str], scores: Mapping[str, int]) -> list[str]:
    recommendations: list[str] = [
        "Do not increase notional yet.",
        "Do not add automation yet.",
    ]
    for reason in reasons:
        recommendations.append(f"Fix: {reason}.")
    for dimension, score in scores.items():
        if score <= 1:
            recommendations.append(f"Improve {dimension}.")
    return recommendations


def _text_score(value: str | None, *, strong: tuple[str, ...]) -> int:
    if not value:
        return 0
    normalized = value.lower()
    if any(bad in normalized for bad in ("weak", "vague", "unclear", "unknown", "missing")):
        return 1
    if any(token in normalized for token in strong):
        return 3
    return 2


def _context_score(value: str | None) -> int:
    if not value:
        return 0
    normalized = value.lower()
    if any(bad in normalized for bad in ("generic", "vague", "unclear", "aligned", "looks good")):
        return 1
    if any(token in normalized for token in ("daily", "weekly", "higher-timeframe", "session", "range", "structure", "trend")) and _has_specific_reference(normalized):
        return 3
    return 2


def _liquidity_score(value: str | None) -> int:
    if not value:
        return 0
    normalized = value.lower()
    if any(bad in normalized for bad in ("generic", "vague", "unclear", "weak", "liquidity area")):
        return 1
    if _has_specific_reference(normalized) and any(
        token in normalized
        for token in ("prior", "session", "low", "high", "reclaim", "sweep", "range", "vwap", "imbalance")
    ):
        return 3
    return 2


def _confirmation_score(value: str | None) -> int:
    if not value:
        return 0
    normalized = value.lower()
    if any(bad in normalized for bad in ("generic", "vague", "unclear", "confirmation fixture", "looks good")):
        return 1
    if _has_specific_reference(normalized) and any(
        token in normalized
        for token in ("close", "candle", "break", "reclaim", "hold", "above", "below", "volume")
    ):
        return 3
    return 2


def _fixed_risk_score(proposal: object | None) -> int:
    if proposal is None:
        return 0
    required = (
        getattr(proposal, "risk_per_share", None),
        getattr(proposal, "max_loss_amount", None),
        getattr(proposal, "stop_loss", None),
    )
    if any(value in (None, "") for value in required):
        return 0
    if getattr(proposal, "what_invalidates_trade", None):
        return 3
    return 2


def _reward_risk_score(proposal: object | None) -> int:
    value = _decimal_or_none(_get(proposal, "expected_reward_risk"))
    if value is None:
        return 0
    if value >= Decimal("2"):
        return 3
    if value >= Decimal("1"):
        return 2
    return 1


def _journal_readiness_score(
    proposal: object | None,
    journal: object | None,
) -> int:
    if proposal is None or not getattr(proposal, "journal_ready", False) or journal is None:
        return 0
    text = " ".join(
        value or ""
        for value in (
            getattr(proposal, "thesis", None),
            getattr(proposal, "why_now", None),
            getattr(proposal, "why_this_level", None),
            getattr(proposal, "what_invalidates_trade", None),
            getattr(journal, "reason_for_final_decision", None),
            getattr(journal, "lessons_or_notes", None),
        )
    )
    if len(text.strip()) < 80:
        return 1
    if _generic_thesis(proposal):
        return 1
    if not _credible_invalidation(getattr(proposal, "what_invalidates_trade", None)):
        return 0
    if all(
        getattr(proposal, field, None)
        for field in ("thesis", "why_now", "what_invalidates_trade")
    ):
        return 3
    return 2


def _specialist_score(
    proposal: object | None,
    input_data: StrategyEvaluationInput,
) -> int:
    if input_data.bypassed_specialist_agents or proposal is None:
        return 0
    outputs = getattr(proposal, "source_agent_outputs", None) or {}
    if not outputs:
        return 0
    if all(str(outputs.get(agent, "")).lower() in {"approved", "looks good", "valid setup"} for agent in REQUIRED_SPECIALISTS):
        return 1
    if all(outputs.get(agent) == "PASS" for agent in REQUIRED_SPECIALISTS):
        return 3
    if any(agent in outputs for agent in REQUIRED_SPECIALISTS):
        return 1
    return 0


def _risk_score(
    risk: object | None,
    input_data: StrategyEvaluationInput,
) -> int:
    if risk is None:
        return 0
    decision = getattr(risk, "decision", None)
    if decision == RISK_APPROVED and not input_data.forced_trade:
        return 3
    if decision == RISK_REJECTED and input_data.actual_rejection:
        return 3
    if decision == RISK_REJECTED:
        return 1
    return 2


def _no_trade_score(input_data: StrategyEvaluationInput) -> int:
    if input_data.forced_trade:
        return 0
    if input_data.no_trade_decision:
        return 3
    if input_data.expected_rejection and input_data.actual_rejection:
        return 3
    if input_data.evaluation_type == "proposal":
        return 2
    return 1


def _rejection_score(input_data: StrategyEvaluationInput) -> int:
    if input_data.expected_rejection and input_data.actual_rejection:
        return 3
    if input_data.expected_rejection and not input_data.actual_rejection:
        return 0
    if input_data.forced_trade:
        return 0
    if input_data.evaluation_type == "proposal":
        return 2
    return 1


def _has_specific_reference(value: str) -> bool:
    return any(char.isdigit() for char in value) or any(
        token in value for token in ("prior session", "daily", "weekly", "vwap", "range high", "range low")
    )


def _generic_thesis(proposal: object | None) -> bool:
    if proposal is None:
        return True
    text = " ".join(
        str(getattr(proposal, field, "") or "").lower()
        for field in ("thesis", "why_now", "why_this_level")
    )
    generic_markers = (
        "paper-only setup fixture",
        "context, liquidity, timing",
        "all deterministic specialist outputs passed",
        "valid setup",
        "looks good",
        "could apply to any symbol",
    )
    return any(marker in text for marker in generic_markers)


def _credible_invalidation(value: object | None) -> bool:
    text = str(value or "").lower()
    if not text or any(marker in text for marker in ("thin", "generic", "missing", "invalidates the idea")):
        return False
    return any(token in text for token in ("below", "above", "close", "stop", "98", "level"))


def _approval_rate(input_data: StrategyEvaluationInput) -> float:
    total = input_data.approval_count + input_data.rejection_count
    if total <= 0:
        return 0.0
    return input_data.approval_count / total


def _get(proposal: object | None, field: str) -> str | None:
    if proposal is None:
        return None
    value = getattr(proposal, field, None)
    return str(value) if value not in (None, "") else None


def _decimal_or_none(value: str | None) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic strategy evaluation harness.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = deterministic_valid_evaluation()
    payload = report.as_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(json.dumps(payload, indent=2))
    return 0 if report.final_status == EVALUATION_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
