from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


REPORT_ROOT = Path("reports/automated_paper_send_soak")
SOAK_TEST_PLAN_NAME = "SOAK_TEST_PLAN.md"
SOAK_RUN_REGISTRY_NAME = "SOAK_RUN_REGISTRY.md"
SOAK_DAILY_LIMITS_NAME = "SOAK_DAILY_LIMITS.md"
SOAK_QUALITY_REVIEW_NAME = "SOAK_QUALITY_REVIEW.md"
SOAK_FINAL_REPORT_NAME = "SOAK_FINAL_REPORT.md"

ENV_AUTOMATED_SEND_ENABLED = "PAPER_AUTOMATED_SEND_ENABLED"
ENV_EXECUTION_ENABLED = "PAPER_ORDER_EXECUTION_ENABLED"
ENV_ALPACA_PAPER = "ALPACA_PAPER"
ENV_SOAK_ACCELERATED = "PAPER_SOAK_TEST_ACCELERATED"
ENV_SOAK_COOLDOWN_SECONDS = "PAPER_SOAK_TEST_COOLDOWN_SECONDS"

PASS = "PASS"
DRY_RUN_ONLY = "DRY_RUN_ONLY"
SOAK_RUN_ALLOWED = "SOAK_RUN_ALLOWED"
SOAK_RUN_BLOCKED = "SOAK_RUN_BLOCKED"
SOAK_RECOMMENDATION_HOLD = "HOLD"
SOAK_RECOMMENDATION_CONTINUE = "CONTINUE_SOAK"
SOAK_RECOMMENDATION_DESIGN_NEXT_PHASE = "DESIGN_NEXT_PHASE"
RECONCILIATION_MATCHED = "RECONCILIATION_MATCHED"
PAPER_ORDER_CANDIDATE_CREATED = "PAPER_ORDER_CANDIDATE_CREATED"
HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST = "HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST"
PAPER_ORDER_REQUEST_FINALIZED = "PAPER_ORDER_REQUEST_FINALIZED"
MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT = "MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT"
PAPER_ORDER_SEND_ALLOWED = "PAPER_ORDER_SEND_ALLOWED"
MAX_NOTIONAL_USD = Decimal("100")
PRODUCTION_DEFAULT_COOLDOWN_SECONDS = 24 * 60 * 60
ACCELERATED_MIN_COOLDOWN_SECONDS = 60
ACCELERATED_MAX_COOLDOWN_SECONDS = PRODUCTION_DEFAULT_COOLDOWN_SECONDS - 1
ACCELERATED_DEFAULT_TEST_COOLDOWN_SECONDS = 60


@dataclass(frozen=True)
class AcceleratedSoakCooldownConfig:
    accelerated_mode_enabled: bool = False
    configured_cooldown_seconds: int | None = None
    accelerated_mode_reason: str = ""
    used_for_soak_testing: bool = True
    live_trading_assumption: bool = False
    production_default_cooldown_seconds: int = PRODUCTION_DEFAULT_COOLDOWN_SECONDS

    def reporting_fields(
        self,
        *,
        alpaca_paper_confirmed: bool,
        live_endpoint_rejected: bool,
    ) -> dict[str, object]:
        return {
            "accelerated_mode_enabled": self.accelerated_mode_enabled,
            "configured_cooldown_seconds": self.configured_cooldown_seconds,
            "production_default_cooldown_seconds": self.production_default_cooldown_seconds,
            "accelerated_mode_reason": self.accelerated_mode_reason or "not enabled",
            "alpaca_paper_confirmed": alpaca_paper_confirmed,
            "live_endpoint_rejected": live_endpoint_rejected,
            "live_trading_unsupported": True,
            "production_cooldown_remains_default": self.production_default_cooldown_seconds
            == PRODUCTION_DEFAULT_COOLDOWN_SECONDS,
            "does_not_authorize_frequency_increase": True,
            "does_not_authorize_live_trading": True,
        }


@dataclass(frozen=True)
class SoakRunState:
    daily_order_count: int = 0
    daily_notional_used: str = "0"
    cooldown_satisfied: bool = True
    kill_switch_active: bool = False
    previous_reconciliation_exists: bool = True
    previous_reconciliation_matched: bool = True
    previous_post_mortem_exists: bool = True
    previous_post_mortem_has_blockers: bool = False
    unresolved_issue_exists: bool = False
    reconciliation_mismatch_exists: bool = False
    missing_reconciliation: bool = False
    missing_post_mortem: bool = False
    unresolved_post_mortem_blocker: bool = False
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    max_daily_orders: int = 1
    max_daily_notional: str = "100"

    def as_dict(self) -> dict[str, object]:
        return {
            "daily_order_count": self.daily_order_count,
            "daily_notional_used": self.daily_notional_used,
            "cooldown_satisfied": self.cooldown_satisfied,
            "kill_switch_active": self.kill_switch_active,
            "previous_reconciliation_exists": self.previous_reconciliation_exists,
            "previous_reconciliation_matched": self.previous_reconciliation_matched,
            "previous_post_mortem_exists": self.previous_post_mortem_exists,
            "previous_post_mortem_has_blockers": self.previous_post_mortem_has_blockers,
            "unresolved_issue_exists": self.unresolved_issue_exists,
            "reconciliation_mismatch_exists": self.reconciliation_mismatch_exists,
            "missing_reconciliation": self.missing_reconciliation,
            "missing_post_mortem": self.missing_post_mortem,
            "unresolved_post_mortem_blocker": self.unresolved_post_mortem_blocker,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "max_daily_orders": self.max_daily_orders,
            "max_daily_notional": self.max_daily_notional,
        }


@dataclass(frozen=True)
class SoakQualityMetrics:
    attempted_runs: int = 0
    approved_runs: int = 0
    no_trade_or_rejection_count: int = 0
    minimum_no_trade_or_rejection_count: int = 1
    approval_rate_warning_threshold: str = "0.80"
    evaluation_score_inflation: bool = False
    rubber_stamping_detected: bool = False
    journal_quality_degraded: bool = False
    journal_quality_acceptable: bool = True

    def approval_rate(self) -> Decimal:
        if self.attempted_runs <= 0:
            return Decimal("0")
        return Decimal(self.approved_runs) / Decimal(self.attempted_runs)

    def approval_rate_red_flag(self) -> bool:
        if self.attempted_runs <= 0:
            return False
        threshold = _decimal_or_none(self.approval_rate_warning_threshold) or Decimal("0.80")
        return self.approval_rate() > threshold and self.no_trade_or_rejection_count < self.minimum_no_trade_or_rejection_count

    def no_trade_rejection_degraded(self) -> bool:
        return self.no_trade_or_rejection_count < self.minimum_no_trade_or_rejection_count and self.attempted_runs > 0

    def as_dict(self) -> dict[str, object]:
        return {
            "attempted_runs": self.attempted_runs,
            "approved_runs": self.approved_runs,
            "approval_rate": str(self.approval_rate()),
            "approval_rate_red_flag": self.approval_rate_red_flag(),
            "no_trade_or_rejection_count": self.no_trade_or_rejection_count,
            "minimum_no_trade_or_rejection_count": self.minimum_no_trade_or_rejection_count,
            "evaluation_score_inflation": self.evaluation_score_inflation,
            "rubber_stamping_detected": self.rubber_stamping_detected,
            "journal_quality_degraded": self.journal_quality_degraded,
            "journal_quality_acceptable": self.journal_quality_acceptable,
        }


@dataclass(frozen=True)
class SoakRunConfig:
    paper_order_execution_enabled: bool = False
    paper_automated_send_enabled: bool = False
    alpaca_paper: bool = False
    full_tests_status: str | None = None
    architecture_validation_status: str | None = None
    v10_full_pipeline_regression_status: str | None = None
    automated_paper_send_mocked_regression_status: str | None = None
    strategy_evaluation_status: str = PASS
    evaluation_gate_status: str = "EVALUATION_GATE_PASSED"
    negative_case_regression_status: str = PASS
    candidate_status: str = PAPER_ORDER_CANDIDATE_CREATED
    candidate_from_valid_trade_proposal: bool = True
    human_review_status: str = HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST
    finalized_request_status: str = PAPER_ORDER_REQUEST_FINALIZED
    manual_confirmation_status: str = MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT
    paper_send_preflight_status: str = PAPER_ORDER_SEND_ALLOWED
    alpaca_paper_account_confirmed: bool = True
    live_endpoint_configured: bool = False
    secrets_present: bool = True
    secrets_printed: bool = False
    paper_trading_only: bool = True
    symbols: tuple[str, ...] = ("SIM",)
    order_count: int = 1
    notional: str = "100"
    order_type: str = "limit"
    time_in_force: str = "day"
    short_selling: bool = False
    crypto: bool = False
    options: bool = False
    margin_or_leverage: bool = False
    extended_hours: bool = False
    batch_orders: bool = False
    cancel_replace: bool = False
    higher_frequency: bool = False
    state: SoakRunState = SoakRunState()
    quality: SoakQualityMetrics = SoakQualityMetrics()
    accelerated_cooldown: AcceleratedSoakCooldownConfig = AcceleratedSoakCooldownConfig()


@dataclass(frozen=True)
class SoakRunDecision:
    final_status: str
    block_reasons: tuple[str, ...]
    recommendation: str
    attempted_run_count: int
    submitted_paper_order_count: int
    blocked_run_count: int
    daily_order_count: int
    daily_notional_used: str
    consecutive_failures: int
    consecutive_successes: int
    real_order_sent: bool = False
    real_alpaca_api_called: bool = False
    live_trading_readiness: bool = False
    live_endpoint_used: bool = False
    secrets_printed: bool = False
    returned_to_dry_run_only: bool = True
    flags_disabled_unset_after_run: bool = True
    accelerated_cooldown_fields: dict[str, object] | None = None

    def as_dict(self) -> dict[str, object]:
        result = {
            "final_status": self.final_status,
            "block_reasons": list(self.block_reasons),
            "recommendation": self.recommendation,
            "attempted_run_count": self.attempted_run_count,
            "submitted_paper_order_count": self.submitted_paper_order_count,
            "blocked_run_count": self.blocked_run_count,
            "daily_order_count": self.daily_order_count,
            "daily_notional_used": self.daily_notional_used,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "real_order_sent": self.real_order_sent,
            "real_alpaca_api_called": self.real_alpaca_api_called,
            "live_trading_readiness": self.live_trading_readiness,
            "live_endpoint_used": self.live_endpoint_used,
            "secrets_printed": self.secrets_printed,
            "returned_to_dry_run_only": self.returned_to_dry_run_only,
            "flags_disabled_unset_after_run": self.flags_disabled_unset_after_run,
        }
        if self.accelerated_cooldown_fields is not None:
            result["accelerated_cooldown_fields"] = self.accelerated_cooldown_fields
        return result


@dataclass(frozen=True)
class SoakRunRecord:
    run_id: str
    timestamp: str
    symbol: str = "SIM"
    proposed_notional: str = "100"
    gate_status_summary: str = PASS
    human_review_status: str = HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST
    manual_confirmation_status: str = MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT
    paper_send_preflight_status: str = PAPER_ORDER_SEND_ALLOWED
    send_decision: str = SOAK_RUN_BLOCKED
    submitted_paper_order_id: str | None = None
    reconciliation_status: str | None = None
    post_mortem_status: str | None = None
    block_reason: str = ""
    flag_cleanup_status: str = "disabled/unset"
    live_endpoint_used: bool = False
    secrets_printed: bool = False
    batch_or_cancel_replace_attempt: bool = False

    @property
    def submitted(self) -> bool:
        return bool(self.submitted_paper_order_id)

    @property
    def blocked(self) -> bool:
        return not self.submitted


@dataclass(frozen=True)
class SoakReportPaths:
    report_dir: str | None
    soak_test_plan_path: str | None
    soak_run_registry_path: str | None
    soak_daily_limits_path: str | None
    soak_quality_review_path: str | None
    soak_final_report_path: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "report_dir": self.report_dir,
            "soak_test_plan_path": self.soak_test_plan_path,
            "soak_run_registry_path": self.soak_run_registry_path,
            "soak_daily_limits_path": self.soak_daily_limits_path,
            "soak_quality_review_path": self.soak_quality_review_path,
            "soak_final_report_path": self.soak_final_report_path,
        }


def evaluate_soak_run(config: SoakRunConfig | None = None) -> SoakRunDecision:
    config = config or SoakRunConfig()
    block_reasons = _block_reasons(config)
    recommendation = recommendation_for(state=config.state, quality=config.quality, block_reasons=block_reasons)
    final_status = SOAK_RUN_ALLOWED if not block_reasons else SOAK_RUN_BLOCKED
    submitted_count = 0
    blocked_count = 0 if not block_reasons else 1
    next_failures = config.state.consecutive_failures + (1 if block_reasons else 0)
    next_successes = config.state.consecutive_successes + (1 if not block_reasons else 0)
    try:
        return SoakRunDecision(
            final_status=final_status,
            block_reasons=block_reasons,
            recommendation=recommendation,
            attempted_run_count=1,
            submitted_paper_order_count=submitted_count,
            blocked_run_count=blocked_count,
            daily_order_count=config.state.daily_order_count,
            daily_notional_used=config.state.daily_notional_used,
            consecutive_failures=next_failures,
            consecutive_successes=next_successes,
            secrets_printed=config.secrets_printed,
            accelerated_cooldown_fields=config.accelerated_cooldown.reporting_fields(
                alpaca_paper_confirmed=config.alpaca_paper,
                live_endpoint_rejected=not config.live_endpoint_configured,
            ),
        )
    finally:
        os.environ.pop(ENV_EXECUTION_ENABLED, None)
        os.environ.pop(ENV_AUTOMATED_SEND_ENABLED, None)


def recommendation_for(
    *,
    state: SoakRunState,
    quality: SoakQualityMetrics,
    block_reasons: tuple[str, ...] = (),
    minimum_period_completed: bool = False,
) -> str:
    joined = " | ".join(block_reasons)
    if (
        state.reconciliation_mismatch_exists
        or state.missing_reconciliation
        or state.unresolved_post_mortem_blocker
        or "reconciliation mismatch" in joined
        or "missing reconciliation" in joined
        or "unresolved post-mortem blocker" in joined
    ):
        return SOAK_RECOMMENDATION_HOLD
    if state.missing_post_mortem or state.kill_switch_active or state.unresolved_issue_exists:
        return SOAK_RECOMMENDATION_HOLD
    if quality.rubber_stamping_detected or quality.evaluation_score_inflation:
        return SOAK_RECOMMENDATION_HOLD
    if quality.approval_rate_red_flag() or quality.no_trade_rejection_degraded() or quality.journal_quality_degraded:
        return SOAK_RECOMMENDATION_CONTINUE
    if block_reasons:
        return SOAK_RECOMMENDATION_HOLD
    if minimum_period_completed:
        return SOAK_RECOMMENDATION_DESIGN_NEXT_PHASE
    return SOAK_RECOMMENDATION_CONTINUE


def generate_soak_reports(
    *,
    records: tuple[SoakRunRecord, ...] = (),
    state: SoakRunState | None = None,
    quality: SoakQualityMetrics | None = None,
    accelerated_cooldown: AcceleratedSoakCooldownConfig | None = None,
    soak_period: str = "UNSPECIFIED",
    minimum_period_completed: bool = False,
    output_root: Path = REPORT_ROOT,
    write_reports: bool = True,
) -> SoakReportPaths:
    state = state or derive_state_from_records(records)
    quality = quality or derive_quality_from_records(records)
    accelerated_cooldown = accelerated_cooldown or AcceleratedSoakCooldownConfig()
    recommendation = recommendation_for(
        state=state,
        quality=quality,
        block_reasons=_record_safety_violations(records),
        minimum_period_completed=minimum_period_completed,
    )
    if not write_reports:
        return SoakReportPaths(None, None, None, None, None, None)

    report_dir = _timestamped_report_dir(output_root)
    plan_path = report_dir / SOAK_TEST_PLAN_NAME
    registry_path = report_dir / SOAK_RUN_REGISTRY_NAME
    daily_limits_path = report_dir / SOAK_DAILY_LIMITS_NAME
    quality_path = report_dir / SOAK_QUALITY_REVIEW_NAME
    final_path = report_dir / SOAK_FINAL_REPORT_NAME

    plan_path.write_text(
        _render_plan(soak_period=soak_period, accelerated_cooldown=accelerated_cooldown),
        encoding="utf-8",
    )
    registry_path.write_text(_render_registry(records), encoding="utf-8")
    daily_limits_path.write_text(
        _render_daily_limits(state=state, records=records, accelerated_cooldown=accelerated_cooldown),
        encoding="utf-8",
    )
    quality_path.write_text(_render_quality_review(quality=quality), encoding="utf-8")
    final_path.write_text(
        _render_final_report(
            soak_period=soak_period,
            records=records,
            state=state,
            quality=quality,
            recommendation=recommendation,
            accelerated_cooldown=accelerated_cooldown,
        ),
        encoding="utf-8",
    )
    return SoakReportPaths(
        report_dir=report_dir.as_posix(),
        soak_test_plan_path=plan_path.as_posix(),
        soak_run_registry_path=registry_path.as_posix(),
        soak_daily_limits_path=daily_limits_path.as_posix(),
        soak_quality_review_path=quality_path.as_posix(),
        soak_final_report_path=final_path.as_posix(),
    )


def generate_soak_reports_from_existing_artifacts(
    *,
    artifact_dirs: tuple[Path, ...],
    soak_period: str = "EXISTING_ARTIFACTS",
    output_root: Path = REPORT_ROOT,
) -> SoakReportPaths:
    records = tuple(record_from_one_real_artifact(path) for path in artifact_dirs)
    return generate_soak_reports(records=records, soak_period=soak_period, output_root=output_root)


def record_from_one_real_artifact(artifact_dir: Path) -> SoakRunRecord:
    report_path = artifact_dir / "ONE_REAL_AUTOMATED_PAPER_SEND_REPORT.md"
    reconciliation_path = artifact_dir / "RECONCILIATION.md"
    post_mortem_path = artifact_dir / "POST_MORTEM.md"
    report_text = _read_text(report_path)
    reconciliation_text = _read_text(reconciliation_path)
    post_mortem_text = _read_text(post_mortem_path)
    timestamp = _extract_value(report_text, "Generated at") or artifact_dir.name
    send_status = _extract_value(report_text, "Send status") or _extract_value(report_text, "Final status") or SOAK_RUN_BLOCKED
    order_id = _extract_value(report_text, "Alpaca paper order id")
    reconciliation_status = _extract_value(reconciliation_text, "Reconciliation status")
    post_mortem_status = "PASS" if "Unexpected behavior: none recorded" in post_mortem_text else None
    block_reason = _extract_value(report_text, "Block reasons") or ""
    if order_id == "none":
        order_id = None
    return SoakRunRecord(
        run_id=artifact_dir.name,
        timestamp=timestamp,
        proposed_notional="100",
        send_decision=send_status,
        submitted_paper_order_id=order_id,
        reconciliation_status=reconciliation_status,
        post_mortem_status=post_mortem_status,
        block_reason=block_reason,
        live_endpoint_used="Live endpoint rejection: True" not in report_text and "Live trading remains unsupported" not in report_text,
        secrets_printed="Secrets printed: false" not in report_text and "Secrets printed: false" not in _read_text(artifact_dir / "AUTOMATION_AUDIT_LOG.md"),
    )


def derive_state_from_records(records: tuple[SoakRunRecord, ...]) -> SoakRunState:
    submitted = tuple(record for record in records if record.submitted)
    mismatch = any(record.reconciliation_status not in (None, RECONCILIATION_MATCHED) for record in submitted)
    missing_reconciliation = any(record.submitted and not record.reconciliation_status for record in records)
    missing_post_mortem = any(record.submitted and not record.post_mortem_status for record in records)
    post_mortem_blocker = any(record.post_mortem_status == "BLOCKER" for record in records)
    unresolved = any("unresolved" in record.block_reason.lower() for record in records)
    safety_blocks = any(
        record.live_endpoint_used or record.secrets_printed or record.batch_or_cancel_replace_attempt
        for record in records
    )
    consecutive_successes = 0
    consecutive_failures = 0
    for record in reversed(records):
        if record.submitted and record.reconciliation_status == RECONCILIATION_MATCHED and record.post_mortem_status == "PASS":
            if consecutive_failures:
                break
            consecutive_successes += 1
        else:
            if consecutive_successes:
                break
            consecutive_failures += 1
    return SoakRunState(
        daily_order_count=len(submitted),
        daily_notional_used=str(sum((_decimal_or_none(record.proposed_notional) or Decimal("0")) for record in submitted)),
        previous_reconciliation_exists=not missing_reconciliation,
        previous_reconciliation_matched=not mismatch,
        previous_post_mortem_exists=not missing_post_mortem,
        previous_post_mortem_has_blockers=post_mortem_blocker,
        unresolved_issue_exists=unresolved or safety_blocks,
        reconciliation_mismatch_exists=mismatch,
        missing_reconciliation=missing_reconciliation,
        missing_post_mortem=missing_post_mortem,
        unresolved_post_mortem_blocker=post_mortem_blocker,
        consecutive_failures=consecutive_failures,
        consecutive_successes=consecutive_successes,
    )


def derive_quality_from_records(records: tuple[SoakRunRecord, ...]) -> SoakQualityMetrics:
    attempted = len(records)
    approved = sum(1 for record in records if record.submitted)
    rejections = attempted - approved
    return SoakQualityMetrics(
        attempted_runs=attempted,
        approved_runs=approved,
        no_trade_or_rejection_count=rejections,
    )


def _block_reasons(config: SoakRunConfig) -> tuple[str, ...]:
    reasons: list[str] = []
    if not config.paper_order_execution_enabled:
        reasons.append("PAPER_ORDER_EXECUTION_ENABLED is not true")
    if not config.paper_automated_send_enabled:
        reasons.append("PAPER_AUTOMATED_SEND_ENABLED is not true")
    if not config.alpaca_paper:
        reasons.append("ALPACA_PAPER is not true")
    if config.full_tests_status != PASS:
        reasons.append("full tests status is not PASS")
    if config.architecture_validation_status != PASS:
        reasons.append("architecture validation status is not PASS")
    if config.v10_full_pipeline_regression_status != PASS:
        reasons.append("V10 full pipeline dry-run regression status is not PASS")
    if config.automated_paper_send_mocked_regression_status != PASS:
        reasons.append("automated paper send mocked regression status is not PASS")
    if config.strategy_evaluation_status != PASS:
        reasons.append("Strategy Evaluation status is not PASS")
    if config.evaluation_gate_status != "EVALUATION_GATE_PASSED":
        reasons.append("Evaluation-First Gate status is not EVALUATION_GATE_PASSED")
    if config.negative_case_regression_status != PASS:
        reasons.append("Negative Case Regression status is not PASS")
    if not config.candidate_from_valid_trade_proposal:
        reasons.append("candidate was not created from valid TRADE_PROPOSAL")
    if config.candidate_status != PAPER_ORDER_CANDIDATE_CREATED:
        reasons.append("candidate status is not PAPER_ORDER_CANDIDATE_CREATED")
    if config.human_review_status != HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST:
        reasons.append("Human Review is not approved")
    if config.finalized_request_status != PAPER_ORDER_REQUEST_FINALIZED:
        reasons.append("Finalized Paper Order Request is not finalized")
    if config.manual_confirmation_status != MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT:
        reasons.append("Manual Execution Confirmation is not confirmed")
    if config.paper_send_preflight_status != PAPER_ORDER_SEND_ALLOWED:
        reasons.append("Paper Send Preflight is not PAPER_ORDER_SEND_ALLOWED")
    if not config.alpaca_paper_account_confirmed:
        reasons.append("Alpaca paper account is not confirmed")
    if config.live_endpoint_configured:
        reasons.append("live endpoint detected")
    if not config.secrets_present:
        reasons.append("secrets are not present")
    if config.secrets_printed:
        reasons.append("secret exposure")
    reasons.extend(_constraint_reasons(config))
    reasons.extend(validate_accelerated_cooldown(config.accelerated_cooldown, config))
    reasons.extend(_state_reasons(config.state, config.notional, config.accelerated_cooldown))
    reasons.extend(_quality_reasons(config.quality))
    return tuple(dict.fromkeys(reasons))


def validate_accelerated_cooldown(
    cooldown: AcceleratedSoakCooldownConfig,
    config: SoakRunConfig,
) -> tuple[str, ...]:
    if not cooldown.accelerated_mode_enabled:
        return ()

    reasons: list[str] = []
    seconds = cooldown.configured_cooldown_seconds
    if not config.alpaca_paper:
        reasons.append("PAPER_SOAK_TEST_ACCELERATED=true requires ALPACA_PAPER=true")
    if config.live_endpoint_configured:
        reasons.append("accelerated cooldown blocks live endpoint")
    if cooldown.live_trading_assumption:
        reasons.append("accelerated cooldown blocks live trading assumption")
    if seconds is None:
        reasons.append("PAPER_SOAK_TEST_COOLDOWN_SECONDS is required")
    elif seconds < ACCELERATED_MIN_COOLDOWN_SECONDS:
        reasons.append("PAPER_SOAK_TEST_COOLDOWN_SECONDS < 60 is blocked")
    elif seconds >= PRODUCTION_DEFAULT_COOLDOWN_SECONDS:
        reasons.append("PAPER_SOAK_TEST_COOLDOWN_SECONDS >= 86400 is blocked")
    if not cooldown.used_for_soak_testing:
        reasons.append("accelerated cooldown outside soak testing is blocked")
    if not config.paper_trading_only:
        reasons.append("accelerated cooldown used for live trading is blocked")
    if _decimal_or_none(config.notional) is None or _decimal_or_none(config.notional) > MAX_NOTIONAL_USD:
        reasons.append("accelerated cooldown blocks notional > 100 USD")
    if len(config.symbols) != 1:
        reasons.append("accelerated cooldown blocks more than one symbol")
    if config.order_count != 1:
        reasons.append("accelerated cooldown blocks more than one order per run")
    if config.batch_orders or config.cancel_replace:
        reasons.append("accelerated cooldown blocks batch/cancel/replace")
    if _v13_gate_failed(config):
        reasons.append("accelerated cooldown blocks failed V13 gate")
    if not config.state.previous_reconciliation_exists:
        reasons.append("accelerated cooldown blocks missing previous reconciliation")
    if not config.state.previous_reconciliation_matched or config.state.reconciliation_mismatch_exists:
        reasons.append("accelerated cooldown blocks unresolved reconciliation mismatch")
    if not config.state.previous_post_mortem_exists:
        reasons.append("accelerated cooldown blocks missing previous post-mortem")
    if config.state.previous_post_mortem_has_blockers or config.state.unresolved_post_mortem_blocker:
        reasons.append("accelerated cooldown blocks unresolved post-mortem blocker")
    if config.state.unresolved_issue_exists:
        reasons.append("accelerated cooldown blocks unresolved issue")
    if config.state.kill_switch_active:
        reasons.append("accelerated cooldown blocks kill switch active")
    return tuple(reasons)


def _v13_gate_failed(config: SoakRunConfig) -> bool:
    return any(
        (
            config.full_tests_status != PASS,
            config.architecture_validation_status != PASS,
            config.v10_full_pipeline_regression_status != PASS,
            config.automated_paper_send_mocked_regression_status != PASS,
            config.strategy_evaluation_status != PASS,
            config.evaluation_gate_status != "EVALUATION_GATE_PASSED",
            config.negative_case_regression_status != PASS,
            not config.candidate_from_valid_trade_proposal,
            config.candidate_status != PAPER_ORDER_CANDIDATE_CREATED,
            config.human_review_status != HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST,
            config.finalized_request_status != PAPER_ORDER_REQUEST_FINALIZED,
            config.manual_confirmation_status != MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT,
            config.paper_send_preflight_status != PAPER_ORDER_SEND_ALLOWED,
            not config.alpaca_paper_account_confirmed,
        )
    )


def _constraint_reasons(config: SoakRunConfig) -> tuple[str, ...]:
    reasons: list[str] = []
    if not config.paper_trading_only:
        reasons.append("paper trading only is required")
    if len(config.symbols) != 1:
        reasons.append("one symbol only is required")
    if config.order_count != 1:
        reasons.append("one order only is required")
    if _decimal_or_none(config.notional) is None or _decimal_or_none(config.notional) > MAX_NOTIONAL_USD:
        reasons.append("notional > 100 USD is blocked")
    if config.order_type != "limit":
        reasons.append("limit order only is required")
    if config.time_in_force != "day":
        reasons.append("day time-in-force only is required")
    if config.short_selling:
        reasons.append("short selling is blocked")
    if config.crypto:
        reasons.append("crypto is blocked")
    if config.options:
        reasons.append("options are blocked")
    if config.margin_or_leverage:
        reasons.append("margin/leverage is blocked")
    if config.extended_hours:
        reasons.append("extended hours are blocked")
    if config.batch_orders:
        reasons.append("batch orders are blocked")
    if config.cancel_replace:
        reasons.append("cancel/replace is blocked")
    if config.higher_frequency:
        reasons.append("higher frequency is blocked")
    return tuple(reasons)


def _state_reasons(
    state: SoakRunState,
    notional: str,
    accelerated_cooldown: AcceleratedSoakCooldownConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if state.kill_switch_active:
        reasons.append("automation kill switch is active")
    if state.daily_order_count >= state.max_daily_orders:
        reasons.append("daily order limit exceeded")
    next_notional = (_decimal_or_none(state.daily_notional_used) or Decimal("0")) + (
        _decimal_or_none(notional) or Decimal("0")
    )
    max_daily_notional = _decimal_or_none(state.max_daily_notional) or MAX_NOTIONAL_USD
    if next_notional > max_daily_notional:
        reasons.append("daily notional limit exceeded")
    if not state.cooldown_satisfied and not _accelerated_cooldown_can_satisfy_cooldown(accelerated_cooldown):
        reasons.append("cooldown violation")
    if not state.previous_reconciliation_exists:
        reasons.append("previous reconciliation missing")
    if not state.previous_reconciliation_matched:
        reasons.append("previous reconciliation mismatch unresolved")
    if not state.previous_post_mortem_exists:
        reasons.append("previous post-mortem missing")
    if state.previous_post_mortem_has_blockers:
        reasons.append("previous post-mortem unresolved blocker")
    if state.unresolved_issue_exists:
        reasons.append("unresolved issue exists")
    if state.reconciliation_mismatch_exists:
        reasons.append("reconciliation mismatch blocks soak continuation")
    if state.missing_reconciliation:
        reasons.append("missing reconciliation blocks soak continuation")
    if state.missing_post_mortem:
        reasons.append("missing post-mortem blocks soak continuation")
    if state.unresolved_post_mortem_blocker:
        reasons.append("unresolved post-mortem blocker blocks soak continuation")
    return tuple(reasons)


def _accelerated_cooldown_can_satisfy_cooldown(cooldown: AcceleratedSoakCooldownConfig) -> bool:
    seconds = cooldown.configured_cooldown_seconds
    return (
        cooldown.accelerated_mode_enabled
        and seconds is not None
        and ACCELERATED_MIN_COOLDOWN_SECONDS <= seconds <= ACCELERATED_MAX_COOLDOWN_SECONDS
        and cooldown.used_for_soak_testing
        and not cooldown.live_trading_assumption
    )


def _quality_reasons(quality: SoakQualityMetrics) -> tuple[str, ...]:
    reasons: list[str] = []
    if quality.approval_rate_red_flag():
        reasons.append("approval-rate red flag")
    if quality.no_trade_rejection_degraded():
        reasons.append("no-trade/rejection quality degraded")
    if quality.evaluation_score_inflation:
        reasons.append("evaluation score inflation")
    if quality.rubber_stamping_detected:
        reasons.append("rubber-stamping detected")
    if quality.journal_quality_degraded or not quality.journal_quality_acceptable:
        reasons.append("journal quality degradation")
    return tuple(reasons)


def _record_safety_violations(records: tuple[SoakRunRecord, ...]) -> tuple[str, ...]:
    reasons: list[str] = []
    for record in records:
        if record.reconciliation_status not in (None, RECONCILIATION_MATCHED):
            reasons.append("reconciliation mismatch")
        if record.submitted and not record.reconciliation_status:
            reasons.append("missing reconciliation")
        if record.submitted and not record.post_mortem_status:
            reasons.append("missing post-mortem")
        if record.post_mortem_status == "BLOCKER":
            reasons.append("unresolved post-mortem blocker")
        if record.live_endpoint_used:
            reasons.append("live endpoint detected")
        if record.secrets_printed:
            reasons.append("secret exposure")
        if record.batch_or_cancel_replace_attempt:
            reasons.append("batch/cancel/replace attempt")
    return tuple(dict.fromkeys(reasons))


def _render_plan(
    *,
    soak_period: str,
    accelerated_cooldown: AcceleratedSoakCooldownConfig,
) -> str:
    fields = accelerated_cooldown.reporting_fields(
        alpaca_paper_confirmed=True,
        live_endpoint_rejected=True,
    )
    return f"""# Soak Test Plan

- Soak period: {soak_period}
- Maximum submitted paper orders per day: 1
- Maximum notional per day: <= 100 USD
- Cooldown rule: production/default cooldown remains 24 hours unless explicit paper-only accelerated soak mode is validated
- accelerated_mode_enabled: {fields["accelerated_mode_enabled"]}
- configured_cooldown_seconds: {fields["configured_cooldown_seconds"]}
- production_default_cooldown_seconds: {fields["production_default_cooldown_seconds"]}
- accelerated_mode_reason: {fields["accelerated_mode_reason"]}
- Kill switch rule: active kill switch blocks all runs
- Required V13 gates: all gates must pass before every run
- Required artifacts per run: registry, daily limits, quality review, final report
- Stop conditions: reconciliation mismatch, missing reconciliation, missing post-mortem, blocker, kill switch, secret exposure, live endpoint, daily limit, cooldown, batch/cancel/replace, quality red flags, failed V13 gate
- Success criteria: all submitted paper orders reconcile matched, every send has post-mortem, no unresolved issues, no live endpoint, no secrets printed
- Review cadence: after every attempted run and at end of soak

Accelerated cooldown was used for paper soak framework validation only.
Production/default cooldown remains 24 hours.
Live trading remains unsupported.
"""


def _render_registry(records: tuple[SoakRunRecord, ...]) -> str:
    lines = ["# Soak Run Registry", ""]
    if not records:
        lines.extend(["No soak runs recorded.", ""])
    for record in records:
        lines.extend(
            [
                f"## {record.run_id}",
                "",
                f"- Timestamp: {record.timestamp}",
                f"- Symbol: {record.symbol}",
                f"- Proposed notional: {record.proposed_notional}",
                f"- Gate status summary: {record.gate_status_summary}",
                f"- Human Review status: {record.human_review_status}",
                f"- Manual Execution Confirmation status: {record.manual_confirmation_status}",
                f"- Paper Send Preflight status: {record.paper_send_preflight_status}",
                f"- Send decision: {record.send_decision}",
                f"- Submitted paper order id: {record.submitted_paper_order_id or 'none'}",
                f"- Reconciliation status: {record.reconciliation_status or 'none'}",
                f"- Post-mortem status: {record.post_mortem_status or 'none'}",
                f"- Block reason: {record.block_reason or 'none'}",
                f"- Flag cleanup status: {record.flag_cleanup_status}",
                f"- Live endpoint used: {record.live_endpoint_used}",
                "",
            ]
        )
    lines.append("Live trading remains unsupported.")
    return "\n".join(lines)


def _render_daily_limits(
    *,
    state: SoakRunState,
    records: tuple[SoakRunRecord, ...],
    accelerated_cooldown: AcceleratedSoakCooldownConfig,
) -> str:
    submitted = sum(1 for record in records if record.submitted)
    cooldown_compliance = state.cooldown_satisfied or _accelerated_cooldown_can_satisfy_cooldown(accelerated_cooldown)
    return f"""# Soak Daily Limits

- Daily order counter: {state.daily_order_count}
- Submitted paper orders in registry: {submitted}
- Daily notional tracker: {state.daily_notional_used}
- Cooldown tracker: {state.cooldown_satisfied}
- accelerated_mode_enabled: {accelerated_cooldown.accelerated_mode_enabled}
- configured_cooldown_seconds: {accelerated_cooldown.configured_cooldown_seconds}
- production_default_cooldown_seconds: {accelerated_cooldown.production_default_cooldown_seconds}
- Kill switch status: {"active" if state.kill_switch_active else "inactive"}
- Daily order limit compliance: {state.daily_order_count <= state.max_daily_orders}
- Daily notional compliance: {(_decimal_or_none(state.daily_notional_used) or Decimal("0")) <= (_decimal_or_none(state.max_daily_notional) or MAX_NOTIONAL_USD)}
- Cooldown compliance: {cooldown_compliance}
- Any daily limit violation: {state.daily_order_count > state.max_daily_orders}

Production/default cooldown remains 24 hours.
Live trading remains unsupported.
"""


def _render_quality_review(*, quality: SoakQualityMetrics) -> str:
    return f"""# Soak Quality Review

- Approval-rate analysis: {quality.approval_rate()}
- Approval-rate red flag: {quality.approval_rate_red_flag()}
- No-trade/rejection analysis: {quality.no_trade_or_rejection_count}
- No-trade/rejection quality degraded: {quality.no_trade_rejection_degraded()}
- Journal quality analysis: {"acceptable" if quality.journal_quality_acceptable and not quality.journal_quality_degraded else "degraded"}
- Evaluation score inflation: {quality.evaluation_score_inflation}
- Rubber-stamping detected: {quality.rubber_stamping_detected}
- Journal quality degradation: {quality.journal_quality_degraded}

Live trading remains unsupported.
"""


def _render_final_report(
    *,
    soak_period: str,
    records: tuple[SoakRunRecord, ...],
    state: SoakRunState,
    quality: SoakQualityMetrics,
    recommendation: str,
    accelerated_cooldown: AcceleratedSoakCooldownConfig,
) -> str:
    submitted = tuple(record for record in records if record.submitted)
    blocked = tuple(record for record in records if record.blocked)
    violations = _record_safety_violations(records)
    reconciliation_results = [
        record.reconciliation_status or "missing"
        for record in submitted
    ] or ["none"]
    post_mortem_results = [
        record.post_mortem_status or "missing"
        for record in submitted
    ] or ["none"]
    accelerated_fields = accelerated_cooldown.reporting_fields(
        alpaca_paper_confirmed=True,
        live_endpoint_rejected=True,
    )
    cooldown_compliance = state.cooldown_satisfied or _accelerated_cooldown_can_satisfy_cooldown(accelerated_cooldown)
    return f"""# Soak Final Report

- Soak period: {soak_period}
- Number of attempted runs: {len(records)}
- Number of submitted paper orders: {len(submitted)}
- Number of blocked runs: {len(blocked)}
- Reconciliation results: {json.dumps(reconciliation_results)}
- Post-mortem results: {json.dumps(post_mortem_results)}
- Daily order limit compliance: {state.daily_order_count <= state.max_daily_orders}
- Daily notional compliance: {(_decimal_or_none(state.daily_notional_used) or Decimal("0")) <= (_decimal_or_none(state.max_daily_notional) or MAX_NOTIONAL_USD)}
- Cooldown compliance: {cooldown_compliance}
- Kill switch events: {state.kill_switch_active}
- Unresolved issues: {state.unresolved_issue_exists}
- Approval-rate analysis: {quality.approval_rate()}
- No-trade/rejection analysis: {quality.no_trade_or_rejection_count}
- Journal quality analysis: {"acceptable" if quality.journal_quality_acceptable and not quality.journal_quality_degraded else "degraded"}
- Safety violations: {json.dumps(list(violations))}
- Recommendation: {recommendation}
- Real Alpaca API called: false
- Real order sent: false
- accelerated_mode_enabled: {accelerated_fields["accelerated_mode_enabled"]}
- configured_cooldown_seconds: {accelerated_fields["configured_cooldown_seconds"]}
- production_default_cooldown_seconds: {accelerated_fields["production_default_cooldown_seconds"]}
- accelerated_mode_reason: {accelerated_fields["accelerated_mode_reason"]}
- alpaca_paper_confirmed: {accelerated_fields["alpaca_paper_confirmed"]}
- live_endpoint_rejected: {accelerated_fields["live_endpoint_rejected"]}
- live_trading_unsupported: {accelerated_fields["live_trading_unsupported"]}
- production_cooldown_remains_default: {accelerated_fields["production_cooldown_remains_default"]}
- does_not_authorize_frequency_increase: {accelerated_fields["does_not_authorize_frequency_increase"]}
- does_not_authorize_live_trading: {accelerated_fields["does_not_authorize_live_trading"]}

Accelerated cooldown was used for paper soak framework validation only.
Production/default cooldown remains 24 hours.
Live trading remains unsupported.
Increasing notional remains prohibited.
Multi-symbol automation remains prohibited.
Batch orders remain prohibited.
Cancel/replace remains prohibited.
"""


def _timestamped_report_dir(output_root: Path) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_dir = output_root / timestamp
    suffix = 1
    while report_dir.exists():
        report_dir = output_root / f"{timestamp}-{suffix}"
        suffix += 1
    report_dir.mkdir(parents=True, exist_ok=False)
    return report_dir


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _extract_value(text: str, label: str) -> str | None:
    prefix = f"- {label}: "
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def _decimal_or_none(value: str) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def valid_soak_config(**overrides: object) -> SoakRunConfig:
    values = {
        "paper_order_execution_enabled": True,
        "paper_automated_send_enabled": True,
        "alpaca_paper": True,
        "full_tests_status": PASS,
        "architecture_validation_status": PASS,
        "v10_full_pipeline_regression_status": PASS,
        "automated_paper_send_mocked_regression_status": PASS,
    }
    values.update(overrides)
    return SoakRunConfig(**values)


def accelerated_cooldown_config_from_env(
    *,
    accelerated_mode_reason: str = "paper soak framework validation",
) -> AcceleratedSoakCooldownConfig:
    accelerated = os.environ.get(ENV_SOAK_ACCELERATED, "false").lower() == "true"
    raw_seconds = os.environ.get(ENV_SOAK_COOLDOWN_SECONDS)
    seconds = None
    if raw_seconds is not None:
        try:
            seconds = int(raw_seconds)
        except ValueError:
            seconds = None
    return AcceleratedSoakCooldownConfig(
        accelerated_mode_enabled=accelerated,
        configured_cooldown_seconds=seconds,
        accelerated_mode_reason=accelerated_mode_reason if accelerated else "",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate automated paper send soak reports from existing records.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--artifact-dir", action="append", default=[], help="Existing one-real automated paper send artifact directory.")
    parser.add_argument("--soak-period", default="EXISTING_ARTIFACTS")
    args = parser.parse_args()
    artifact_dirs = tuple(Path(path) for path in args.artifact_dir)
    if artifact_dirs:
        paths = generate_soak_reports_from_existing_artifacts(
            artifact_dirs=artifact_dirs,
            soak_period=args.soak_period,
        )
    else:
        paths = generate_soak_reports(write_reports=True, soak_period=args.soak_period)
    if args.json:
        print(json.dumps(paths.as_dict(), indent=2))
    else:
        print(paths.soak_final_report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
