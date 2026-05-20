from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Mapping

from alpaca_paper_account import PaperAccountSnapshot, default_mock_snapshot


RISK_APPROVED = "RISK_APPROVED"
RISK_REJECTED = "RISK_REJECTED"
VALIDATION_PASS = "PASS"
VALIDATION_FAIL = "FAIL"


@dataclass(frozen=True)
class PaperTradeProposal:
    proposal_id: str | None
    created_at: str | None
    routine_name: str | None
    symbol: str | None
    direction: str | None
    setup_type: str | None
    timeframe_context: str | None
    liquidity_location: str | None
    session_timing: str | None
    entry_confirmation: str | None
    proposed_entry: str | None
    invalidation_level: str | None
    stop_loss: str | None
    target_1: str | None
    target_2: str | None
    risk_per_share: str | None
    proposed_position_size: str | None
    max_loss_amount: str | None
    max_loss_pct_equity: str | None
    expected_reward_risk: str | None
    thesis: str | None
    why_now: str | None
    why_this_level: str | None
    what_invalidates_trade: str | None
    paper_trading_only: bool
    human_approval_required: bool | None
    source_agent_outputs: Mapping[str, str] | None
    adlc_compliance_status: str | None
    journal_ready: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "proposal_id": self.proposal_id,
            "created_at": self.created_at,
            "routine_name": self.routine_name,
            "symbol": self.symbol,
            "direction": self.direction,
            "setup_type": self.setup_type,
            "timeframe_context": self.timeframe_context,
            "liquidity_location": self.liquidity_location,
            "session_timing": self.session_timing,
            "entry_confirmation": self.entry_confirmation,
            "proposed_entry": self.proposed_entry,
            "invalidation_level": self.invalidation_level,
            "stop_loss": self.stop_loss,
            "target_1": self.target_1,
            "target_2": self.target_2,
            "risk_per_share": self.risk_per_share,
            "proposed_position_size": self.proposed_position_size,
            "max_loss_amount": self.max_loss_amount,
            "max_loss_pct_equity": self.max_loss_pct_equity,
            "expected_reward_risk": self.expected_reward_risk,
            "thesis": self.thesis,
            "why_now": self.why_now,
            "why_this_level": self.why_this_level,
            "what_invalidates_trade": self.what_invalidates_trade,
            "paper_trading_only": self.paper_trading_only,
            "human_approval_required": self.human_approval_required,
            "source_agent_outputs": dict(self.source_agent_outputs or {}),
            "adlc_compliance_status": self.adlc_compliance_status,
            "journal_ready": self.journal_ready,
        }


@dataclass(frozen=True)
class ProposalValidation:
    status: str
    violations: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.status == VALIDATION_PASS

    def as_dict(self) -> dict[str, object]:
        return {"status": self.status, "violations": list(self.violations)}


@dataclass(frozen=True)
class RiskLimits:
    max_loss_amount: Decimal = Decimal("500")
    max_loss_pct_equity: Decimal = Decimal("0.01")
    max_exposure_pct_equity: Decimal = Decimal("0.25")


@dataclass(frozen=True)
class RiskEvaluation:
    decision: str
    rejection_reasons: tuple[str, ...]
    proposal_validation: ProposalValidation
    executable: bool = False

    @property
    def approved(self) -> bool:
        return self.decision == RISK_APPROVED

    def as_dict(self) -> dict[str, object]:
        return {
            "decision": self.decision,
            "rejection_reasons": list(self.rejection_reasons),
            "proposal_validation": self.proposal_validation.as_dict(),
            "executable": self.executable,
        }


def deterministic_valid_proposal(routine_name: str = "market_open") -> PaperTradeProposal:
    return PaperTradeProposal(
        proposal_id=f"paper-{routine_name}-001",
        created_at="2026-05-19T13:31:00+00:00",
        routine_name=routine_name,
        symbol="SIM",
        direction="long",
        setup_type="liquidity_reclaim",
        timeframe_context="Daily structure holds above the prior 100.00 session low after a failed breakdown.",
        liquidity_location="Prior session low at 100.00 reclaim liquidity level",
        session_timing="market_open",
        entry_confirmation="15-minute candle close above 100.00 reclaim with hold above the level",
        proposed_entry="100",
        invalidation_level="98",
        stop_loss="98",
        target_1="104",
        target_2="106",
        risk_per_share="2",
        proposed_position_size="100",
        max_loss_amount="200",
        max_loss_pct_equity="0.002",
        expected_reward_risk="2",
        thesis="SIM paper-only long tests a reclaimed 100.00 prior-session low after failed downside liquidity.",
        why_now="Market-open timing follows the 15-minute close back above 100.00 with risk fixed before approval.",
        why_this_level="100.00 is the named prior-session low and failed breakdown liquidity reference.",
        what_invalidates_trade="A 15-minute close below 98.00 invalidates the reclaimed-low thesis.",
        paper_trading_only=True,
        human_approval_required=True,
        source_agent_outputs={
            "Market Context Agent": "PASS",
            "Liquidity Agent": "PASS",
            "Session Timing Agent": "PASS",
            "Confirmation Agent": "PASS",
        },
        adlc_compliance_status="PASS",
        journal_ready=True,
    )


def validate_proposal(proposal: PaperTradeProposal | None) -> ProposalValidation:
    if proposal is None:
        return ProposalValidation(VALIDATION_FAIL, ("malformed proposal",))

    violations: list[str] = []
    required_values = {
        "symbol": proposal.symbol,
        "direction": proposal.direction,
        "proposed_entry": proposal.proposed_entry,
        "invalidation_level": proposal.invalidation_level,
        "stop_loss": proposal.stop_loss,
        "max_loss_amount": proposal.max_loss_amount,
        "max_loss_pct_equity": proposal.max_loss_pct_equity,
        "thesis": proposal.thesis,
    }
    for field_name, value in required_values.items():
        if value in (None, ""):
            violations.append(f"missing {field_name}")

    if not proposal.paper_trading_only:
        violations.append("missing paper trading flag")
    if not proposal.source_agent_outputs:
        violations.append("missing source agent outputs")
    if not proposal.journal_ready:
        violations.append("missing journal readiness")
    if proposal.adlc_compliance_status != "PASS":
        violations.append("ADLC compliance status is not PASS")

    return ProposalValidation(
        VALIDATION_FAIL if violations else VALIDATION_PASS,
        tuple(violations),
    )


def evaluate_risk(
    proposal: PaperTradeProposal | None,
    account: PaperAccountSnapshot,
    limits: RiskLimits = RiskLimits(),
) -> RiskEvaluation:
    validation = validate_proposal(proposal)
    reasons: list[str] = []

    if not validation.passed:
        reasons.append("malformed proposal")
        reasons.extend(validation.violations)
    if proposal is None:
        return _risk_rejected(reasons, validation)

    if not proposal.risk_per_share or not proposal.proposed_position_size:
        reasons.append("missing fixed risk")
    if not proposal.paper_trading_only:
        reasons.append("missing paper trading flag")
    if proposal.human_approval_required is not True:
        reasons.append("missing human approval requirement")
    if not proposal.journal_ready:
        reasons.append("missing journal readiness")
    if not account.account.trading_allowed_in_principle:
        reasons.append("daily risk state blocked")

    parsed = _parse_numbers(proposal)
    if parsed is None:
        reasons.append("malformed proposal")
        return _risk_rejected(reasons, validation)

    proposed_entry, invalidation_level, stop_loss, max_loss, max_loss_pct, position_size = parsed
    if proposal.direction == "long" and not (
        invalidation_level < proposed_entry and stop_loss <= proposed_entry
    ):
        reasons.append("invalid stop/invalidation relationship")
    if proposal.direction == "short" and not (
        invalidation_level > proposed_entry and stop_loss >= proposed_entry
    ):
        reasons.append("invalid stop/invalidation relationship")

    if max_loss > limits.max_loss_amount:
        reasons.append("max loss exceeds limit")
    if max_loss_pct > limits.max_loss_pct_equity:
        reasons.append("max loss pct exceeds limit")

    equity = _decimal_or_none(account.account.equity)
    if equity is None or equity <= Decimal("0"):
        reasons.append("daily risk state blocked")
    else:
        exposure = proposed_entry * position_size
        if exposure > equity * limits.max_exposure_pct_equity:
            reasons.append("exposure limit exceeded")

    if reasons:
        return _risk_rejected(reasons, validation)
    return RiskEvaluation(
        decision=RISK_APPROVED,
        rejection_reasons=(),
        proposal_validation=validation,
        executable=False,
    )


def _risk_rejected(
    reasons: list[str],
    validation: ProposalValidation,
) -> RiskEvaluation:
    return RiskEvaluation(
        decision=RISK_REJECTED,
        rejection_reasons=tuple(dict.fromkeys(reasons)),
        proposal_validation=validation,
        executable=False,
    )


def _parse_numbers(
    proposal: PaperTradeProposal,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal] | None:
    values = (
        proposal.proposed_entry,
        proposal.invalidation_level,
        proposal.stop_loss,
        proposal.max_loss_amount,
        proposal.max_loss_pct_equity,
        proposal.proposed_position_size,
    )
    if any(value in (None, "") for value in values):
        return None
    try:
        return tuple(Decimal(str(value)) for value in values)  # type: ignore[return-value]
    except InvalidOperation:
        return None


def _decimal_or_none(value: str | None) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except InvalidOperation:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a deterministic paper proposal fixture.")
    parser.add_argument("--routine", default="market_open")
    parser.add_argument("--evaluate-risk", action="store_true")
    args = parser.parse_args()

    proposal = deterministic_valid_proposal(args.routine)
    if args.evaluate_risk:
        payload = evaluate_risk(proposal, default_mock_snapshot()).as_dict()
    else:
        payload = {
            "proposal": proposal.as_dict(),
            "validation": validate_proposal(proposal).as_dict(),
        }
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
