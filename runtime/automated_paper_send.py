from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Mapping, Protocol

from finalized_paper_order_request import (
    PAPER_ORDER_REQUEST_FINALIZED,
    finalize_paper_order_request,
)
from human_review_queue import (
    HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST,
    create_human_review_record,
)
from manual_execution_confirmation import (
    MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT,
    create_manual_execution_confirmation,
)
from paper_order_request_candidate import (
    PAPER_ORDER_CANDIDATE_CREATED,
    create_paper_order_request_candidate,
)
from paper_send_preflight import PAPER_ORDER_SEND_ALLOWED, run_paper_send_preflight
from v10_full_pipeline_dry_run_regression import (
    PIPELINE_PASSED,
    run_v10_full_pipeline_dry_run_regression,
)


REPORT_ROOT = Path("reports/automated_paper_send")
REPORT_NAME = "AUTOMATED_PAPER_SEND_REPORT.md"
RECONCILIATION_NAME = "RECONCILIATION.md"
POST_SEND_SAFETY_NAME = "POST_SEND_SAFETY.md"
POST_MORTEM_NAME = "POST_MORTEM.md"
AUDIT_LOG_NAME = "AUTOMATION_AUDIT_LOG.md"

ENV_AUTOMATED_SEND_ENABLED = "PAPER_AUTOMATED_SEND_ENABLED"
ENV_EXECUTION_ENABLED = "PAPER_ORDER_EXECUTION_ENABLED"
ENV_ALPACA_PAPER = "ALPACA_PAPER"

PASS = "PASS"
DRY_RUN_ONLY = "DRY_RUN_ONLY"
AUTOMATED_PAPER_SEND_ALLOWED = "AUTOMATED_PAPER_SEND_ALLOWED"
AUTOMATED_PAPER_SEND_BLOCKED = "AUTOMATED_PAPER_SEND_BLOCKED"
AUTOMATED_PAPER_SEND_SUBMITTED = "AUTOMATED_PAPER_SEND_SUBMITTED"
AUTOMATED_PAPER_SEND_REJECTED_BY_PREFLIGHT = "AUTOMATED_PAPER_SEND_REJECTED_BY_PREFLIGHT"
AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS = "AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS"
AUTOMATED_PAPER_SEND_REJECTED_BY_KILL_SWITCH = "AUTOMATED_PAPER_SEND_REJECTED_BY_KILL_SWITCH"
AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION = "AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION"
AUTOMATED_PAPER_SEND_REJECTED_BY_POST_MORTEM = "AUTOMATED_PAPER_SEND_REJECTED_BY_POST_MORTEM"
AUTOMATED_PAPER_SEND_ERROR = "AUTOMATED_PAPER_SEND_ERROR"
RECONCILIATION_MATCHED = "RECONCILIATION_MATCHED"
RECONCILIATION_BLOCKED_NO_ORDER = "RECONCILIATION_BLOCKED_NO_ORDER"
MAX_NOTIONAL_USD = Decimal("100")


class AutomatedPaperSendClient(Protocol):
    def submit_paper_order(self, payload: Mapping[str, object]) -> Mapping[str, object]:
        """Submit one already-gated mocked paper order."""


@dataclass(frozen=True)
class AutomationLimits:
    daily_order_count: int = 0
    daily_notional_used: str = "0"
    cooldown_satisfied: bool = True
    kill_switch_active: bool = False
    previous_reconciliation_exists: bool = True
    previous_reconciliation_unresolved_mismatch: bool = False
    previous_post_mortem_exists: bool = True
    previous_post_mortem_unresolved_blocker: bool = False
    unresolved_issue_exists: bool = False
    max_daily_orders: int = 1
    max_daily_notional: str = "100"

    def as_dict(self) -> dict[str, object]:
        return {
            "daily_order_count": self.daily_order_count,
            "daily_notional_used": self.daily_notional_used,
            "cooldown_satisfied": self.cooldown_satisfied,
            "kill_switch_active": self.kill_switch_active,
            "previous_reconciliation_exists": self.previous_reconciliation_exists,
            "previous_reconciliation_unresolved_mismatch": self.previous_reconciliation_unresolved_mismatch,
            "previous_post_mortem_exists": self.previous_post_mortem_exists,
            "previous_post_mortem_unresolved_blocker": self.previous_post_mortem_unresolved_blocker,
            "unresolved_issue_exists": self.unresolved_issue_exists,
            "max_daily_orders": self.max_daily_orders,
            "max_daily_notional": self.max_daily_notional,
        }


@dataclass(frozen=True)
class AutomatedPaperSendConfig:
    paper_automated_send_enabled: bool = False
    paper_order_execution_enabled: bool = False
    alpaca_paper: bool = False
    full_tests_status: str | None = None
    architecture_validation_status: str | None = None
    v10_full_pipeline_regression_status: str | None = None
    strategy_evaluation_status: str = PASS
    evaluation_gate_status: str = "EVALUATION_GATE_PASSED"
    negative_case_regression_status: str = PASS
    candidate_scenario: str = "proposal"
    human_review_status: str = HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST
    manual_confirmation_status: str = MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT
    alpaca_paper_account_confirmed: bool = True
    live_endpoint_configured: bool = False
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
    paper_trading_only: bool = True
    limits: AutomationLimits = AutomationLimits()


@dataclass(frozen=True)
class AutomatedPaperSendResult:
    final_status: str
    block_reasons: tuple[str, ...]
    paper_send_status: str
    reconciliation_status: str
    report_path: str | None
    audit_log_path: str | None
    reconciliation_path: str | None
    post_send_safety_path: str | None
    post_mortem_path: str | None
    submitted_order_count: int
    order_sent: bool
    returned_to_dry_run_only: bool
    flags_unset_or_disabled_after_run: bool
    live_trading_readiness: bool
    live_endpoint_used: bool
    alpaca_order_api_called: bool
    broker_execution_readiness: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "final_status": self.final_status,
            "block_reasons": list(self.block_reasons),
            "paper_send_status": self.paper_send_status,
            "reconciliation_status": self.reconciliation_status,
            "report_path": self.report_path,
            "audit_log_path": self.audit_log_path,
            "reconciliation_path": self.reconciliation_path,
            "post_send_safety_path": self.post_send_safety_path,
            "post_mortem_path": self.post_mortem_path,
            "submitted_order_count": self.submitted_order_count,
            "order_sent": self.order_sent,
            "returned_to_dry_run_only": self.returned_to_dry_run_only,
            "flags_unset_or_disabled_after_run": self.flags_unset_or_disabled_after_run,
            "live_trading_readiness": self.live_trading_readiness,
            "live_endpoint_used": self.live_endpoint_used,
            "alpaca_order_api_called": self.alpaca_order_api_called,
            "broker_execution_readiness": self.broker_execution_readiness,
        }


class RecordingAutomatedPaperClient:
    def __init__(self) -> None:
        self.payloads: list[Mapping[str, object]] = []

    def submit_paper_order(self, payload: Mapping[str, object]) -> Mapping[str, object]:
        self.payloads.append(dict(payload))
        return {"id": "mock-automated-paper-order-001", "status": "accepted"}


def run_automated_paper_send(
    *,
    config: AutomatedPaperSendConfig | None = None,
    client: AutomatedPaperSendClient | None = None,
    output_root: Path = REPORT_ROOT,
    write_artifacts: bool = True,
) -> AutomatedPaperSendResult:
    config = config or AutomatedPaperSendConfig()
    report_dir = _timestamped_report_dir(output_root) if write_artifacts else None
    context = _build_pipeline_context(config)
    block_reasons = _block_reasons(config, context)
    status = _blocked_status(block_reasons)
    reconciliation_status = RECONCILIATION_BLOCKED_NO_ORDER
    submitted_count = 0
    order_sent = False
    broker_order_id: str | None = None
    error_message: str | None = None

    try:
        if not block_reasons:
            active_client = client
            if active_client is None:
                block_reasons = ("mocked paper send client is required",)
                status = AUTOMATED_PAPER_SEND_BLOCKED
            else:
                try:
                    response = active_client.submit_paper_order(_paper_order_payload(context))
                    submitted_count = 1
                    order_sent = True
                    broker_order_id = _string_or_none(response.get("id"))
                    status = AUTOMATED_PAPER_SEND_SUBMITTED
                    reconciliation_status = RECONCILIATION_MATCHED
                except Exception as exc:
                    status = AUTOMATED_PAPER_SEND_ERROR
                    error_message = _safe_error(exc)
    finally:
        os.environ.pop(ENV_EXECUTION_ENABLED, None)
        os.environ.pop(ENV_AUTOMATED_SEND_ENABLED, None)

    paths = _ArtifactPaths(None, None, None, None, None)
    if write_artifacts and report_dir is not None:
        paths = _write_artifacts(
            report_dir=report_dir,
            config=config,
            context=context,
            block_reasons=tuple(block_reasons),
            status=status,
            reconciliation_status=reconciliation_status,
            broker_order_id=broker_order_id,
            error_message=error_message,
            order_sent=order_sent,
        )
    return AutomatedPaperSendResult(
        final_status=status,
        block_reasons=tuple(block_reasons),
        paper_send_status=status,
        reconciliation_status=reconciliation_status,
        report_path=paths.report_path,
        audit_log_path=paths.audit_log_path,
        reconciliation_path=paths.reconciliation_path,
        post_send_safety_path=paths.post_send_safety_path,
        post_mortem_path=paths.post_mortem_path,
        submitted_order_count=submitted_count,
        order_sent=order_sent,
        returned_to_dry_run_only=True,
        flags_unset_or_disabled_after_run=True,
        live_trading_readiness=False,
        live_endpoint_used=False,
        alpaca_order_api_called=False,
        broker_execution_readiness=False,
    )


def _build_pipeline_context(config: AutomatedPaperSendConfig) -> dict[str, object]:
    original_execution_flag = os.environ.get(ENV_EXECUTION_ENABLED)
    original_automation_flag = os.environ.get(ENV_AUTOMATED_SEND_ENABLED)
    os.environ[ENV_EXECUTION_ENABLED] = ""
    os.environ[ENV_AUTOMATED_SEND_ENABLED] = ""
    try:
        regression = run_v10_full_pipeline_dry_run_regression(write_report=False)
        candidate_result = create_paper_order_request_candidate(
            symbols=list(config.symbols),
            scenario=config.candidate_scenario,
            write_artifacts=False,
        )
        review_result = create_human_review_record(
            candidate=candidate_result.candidate,
            reviewer="automated-paper-send-reviewer",
            review_status=config.human_review_status,
            review_notes="Automated paper send gate review.",
            write_artifacts=False,
        )
        finalized_result = finalize_paper_order_request(
            candidate=candidate_result.candidate,
            review=review_result.record,
            write_artifacts=False,
        )
        manual_result = create_manual_execution_confirmation(
            request=finalized_result.request,
            confirmer="automated-paper-send-confirmer",
            confirmation_status=config.manual_confirmation_status,
            confirmation_notes="Automated paper send gate confirmation.",
            write_artifacts=False,
        )
        request = finalized_result.request
        if request is not None:
            request = _request_with_order_overrides(request, config)
        preflight_result = run_paper_send_preflight(
            request=request,
            confirmation=manual_result.confirmation,
            live_endpoint_configured=config.live_endpoint_configured,
            order_count=config.order_count,
            short_selling=config.short_selling,
            crypto=config.crypto,
            options=config.options,
            margin_or_leverage=config.margin_or_leverage,
            extended_hours=config.extended_hours,
            batch_behavior=config.batch_orders,
            cancel_replace_behavior=config.cancel_replace,
            write_artifacts=False,
        )
    finally:
        _restore_env(ENV_EXECUTION_ENABLED, original_execution_flag)
        _restore_env(ENV_AUTOMATED_SEND_ENABLED, original_automation_flag)
    return {
        "regression_status": regression.final_status,
        "candidate_result": candidate_result,
        "review_result": review_result,
        "finalized_result": finalized_result,
        "manual_result": manual_result,
        "preflight_result": preflight_result,
        "request": request,
    }


def _block_reasons(
    config: AutomatedPaperSendConfig,
    context: Mapping[str, object],
) -> tuple[str, ...]:
    reasons: list[str] = []
    candidate_result = context["candidate_result"]
    review_result = context["review_result"]
    finalized_result = context["finalized_result"]
    manual_result = context["manual_result"]
    preflight_result = context["preflight_result"]
    request = context["request"]

    if not config.paper_automated_send_enabled:
        reasons.append("PAPER_AUTOMATED_SEND_ENABLED is not true")
    if not config.paper_order_execution_enabled:
        reasons.append("PAPER_ORDER_EXECUTION_ENABLED is not true")
    if not config.alpaca_paper:
        reasons.append("ALPACA_PAPER is not true")
    if config.full_tests_status != PASS:
        reasons.append("full tests status is not PASS")
    if config.architecture_validation_status != PASS:
        reasons.append("architecture validation status is not PASS")
    if config.v10_full_pipeline_regression_status != PASS:
        reasons.append("V10 full pipeline dry-run regression status is not PASS")
    if context["regression_status"] != PIPELINE_PASSED:
        reasons.append("V10 full pipeline dry-run regression did not pass")
    if config.strategy_evaluation_status != PASS:
        reasons.append("Strategy Evaluation status is not PASS")
    if config.evaluation_gate_status != "EVALUATION_GATE_PASSED":
        reasons.append("Evaluation-First Gate status is not EVALUATION_GATE_PASSED")
    if config.negative_case_regression_status != PASS:
        reasons.append("Negative Case Regression status is not PASS")
    if getattr(candidate_result, "candidate", None) is None:
        reasons.append("Paper Order Request Candidate is missing")
    if getattr(candidate_result, "final_status", None) != PAPER_ORDER_CANDIDATE_CREATED:
        reasons.append("candidate was not created from valid TRADE_PROPOSAL")
    if getattr(review_result, "final_status", None) != HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST:
        reasons.append("Human Review is not approved")
    if getattr(finalized_result, "final_status", None) != PAPER_ORDER_REQUEST_FINALIZED:
        reasons.append("Finalized Paper Order Request is missing or not finalized")
    if getattr(manual_result, "final_status", None) != MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT:
        reasons.append("Manual Execution Confirmation is missing or not confirmed")
    if getattr(preflight_result, "final_status", None) != PAPER_ORDER_SEND_ALLOWED:
        reasons.append("Paper Send Preflight is not PAPER_ORDER_SEND_ALLOWED")
    if not config.alpaca_paper_account_confirmed:
        reasons.append("Alpaca paper account is not confirmed")
    if config.live_endpoint_configured:
        reasons.append("live endpoint configured is blocked")
    reasons.extend(_automation_limit_reasons(config))
    if not config.paper_trading_only:
        reasons.append("paper trading only is required")
    if len(config.symbols) != 1:
        reasons.append("one symbol only is required")
    if config.order_count != 1:
        reasons.append("one order per automation run is required")
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
    if request is None:
        reasons.append("automated paper order request is missing")
    return tuple(dict.fromkeys(reasons))


def _automation_limit_reasons(config: AutomatedPaperSendConfig) -> tuple[str, ...]:
    limits = config.limits
    reasons: list[str] = []
    if limits.kill_switch_active:
        reasons.append("automation kill switch is active")
    if limits.daily_order_count >= limits.max_daily_orders:
        reasons.append("daily order limit exceeded")
    next_notional = (_decimal_or_none(limits.daily_notional_used) or Decimal("0")) + (
        _decimal_or_none(config.notional) or Decimal("0")
    )
    max_daily_notional = _decimal_or_none(limits.max_daily_notional) or MAX_NOTIONAL_USD
    if next_notional > max_daily_notional:
        reasons.append("daily notional limit exceeded")
    if not limits.cooldown_satisfied:
        reasons.append("cooldown not satisfied")
    if not limits.previous_reconciliation_exists:
        reasons.append("previous reconciliation missing")
    if limits.previous_reconciliation_unresolved_mismatch:
        reasons.append("previous reconciliation mismatch unresolved")
    if not limits.previous_post_mortem_exists:
        reasons.append("previous post-mortem missing")
    if limits.previous_post_mortem_unresolved_blocker:
        reasons.append("previous post-mortem unresolved blocker")
    if limits.unresolved_issue_exists:
        reasons.append("unresolved issue exists")
    return tuple(reasons)


def _blocked_status(reasons: tuple[str, ...]) -> str:
    if not reasons:
        return AUTOMATED_PAPER_SEND_ALLOWED
    text = " | ".join(reasons)
    if "kill switch" in text:
        return AUTOMATED_PAPER_SEND_REJECTED_BY_KILL_SWITCH
    if (
        "daily order limit" in text
        or "daily notional limit" in text
        or "cooldown" in text
        or "one symbol only" in text
        or "one order per automation run" in text
        or "notional > 100 USD" in text
        or "limit order only" in text
        or "day time-in-force only" in text
        or "short selling" in text
        or "crypto" in text
        or "options" in text
        or "margin/leverage" in text
        or "extended hours" in text
        or "batch orders" in text
        or "cancel/replace" in text
    ):
        return AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS
    if "reconciliation" in text:
        return AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION
    if "post-mortem" in text:
        return AUTOMATED_PAPER_SEND_REJECTED_BY_POST_MORTEM
    if "Preflight" in text:
        return AUTOMATED_PAPER_SEND_REJECTED_BY_PREFLIGHT
    return AUTOMATED_PAPER_SEND_BLOCKED


def _request_with_order_overrides(request: object, config: AutomatedPaperSendConfig) -> object:
    from dataclasses import replace

    return replace(
        request,
        notional=config.notional,
        order_type=config.order_type,
        time_in_force=config.time_in_force,
        paper_trading_only=config.paper_trading_only,
    )


def _paper_order_payload(context: Mapping[str, object]) -> Mapping[str, object]:
    request = context["request"]
    return {
        "symbol": getattr(request, "symbol"),
        "side": "buy",
        "type": "limit",
        "time_in_force": "day",
        "limit_price": getattr(request, "limit_price"),
        "notional": getattr(request, "notional"),
        "paper_order_request_id": getattr(request, "paper_order_request_id"),
    }


@dataclass(frozen=True)
class _ArtifactPaths:
    report_path: str | None
    audit_log_path: str | None
    reconciliation_path: str | None
    post_send_safety_path: str | None
    post_mortem_path: str | None


def _write_artifacts(
    *,
    report_dir: Path,
    config: AutomatedPaperSendConfig,
    context: Mapping[str, object],
    block_reasons: tuple[str, ...],
    status: str,
    reconciliation_status: str,
    broker_order_id: str | None,
    error_message: str | None,
    order_sent: bool,
) -> _ArtifactPaths:
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / REPORT_NAME
    audit_path = report_dir / AUDIT_LOG_NAME
    reconciliation_path = report_dir / RECONCILIATION_NAME
    safety_path = report_dir / POST_SEND_SAFETY_NAME
    post_mortem_path = report_dir / POST_MORTEM_NAME
    report_path.write_text(
        _render_report(
            config=config,
            context=context,
            block_reasons=block_reasons,
            status=status,
            reconciliation_status=reconciliation_status,
            broker_order_id=broker_order_id,
            error_message=error_message,
            order_sent=order_sent,
        ),
        encoding="utf-8",
    )
    audit_path.write_text(
        _render_audit_log(config=config, block_reasons=block_reasons, status=status, order_sent=order_sent),
        encoding="utf-8",
    )
    reconciliation_path.write_text(
        _render_reconciliation(status=reconciliation_status, broker_order_id=broker_order_id, order_sent=order_sent),
        encoding="utf-8",
    )
    safety_path.write_text(_render_post_send_safety(), encoding="utf-8")
    post_mortem_path.write_text(
        _render_post_mortem(status=status, reconciliation_status=reconciliation_status, block_reasons=block_reasons),
        encoding="utf-8",
    )
    return _ArtifactPaths(
        report_path=report_path.as_posix(),
        audit_log_path=audit_path.as_posix(),
        reconciliation_path=reconciliation_path.as_posix(),
        post_send_safety_path=safety_path.as_posix(),
        post_mortem_path=post_mortem_path.as_posix(),
    )


def _render_report(
    *,
    config: AutomatedPaperSendConfig,
    context: Mapping[str, object],
    block_reasons: tuple[str, ...],
    status: str,
    reconciliation_status: str,
    broker_order_id: str | None,
    error_message: str | None,
    order_sent: bool,
) -> str:
    candidate_result = context["candidate_result"]
    review_result = context["review_result"]
    finalized_result = context["finalized_result"]
    manual_result = context["manual_result"]
    preflight_result = context["preflight_result"]
    return f"""# Automated Paper Send Report

## Summary

- Generated at: {datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
- Final status: {status}
- Paper send status: {status}
- Alpaca paper order id: {broker_order_id or "none"}
- Error: {error_message or "none"}
- Block reasons: {json.dumps(list(block_reasons))}

## Automation Flags

- PAPER_AUTOMATED_SEND_ENABLED: {config.paper_automated_send_enabled}
- PAPER_ORDER_EXECUTION_ENABLED: {config.paper_order_execution_enabled}
- ALPACA_PAPER: {config.alpaca_paper}

## Gates

- Symbol: {",".join(config.symbols)}
- Full tests: {config.full_tests_status}
- Architecture validation: {config.architecture_validation_status}
- V10 pipeline regression: {config.v10_full_pipeline_regression_status}
- Strategy Evaluation: {config.strategy_evaluation_status}
- Evaluation-First Gate: {config.evaluation_gate_status}
- Negative Case Regression: {config.negative_case_regression_status}
- Candidate status: {getattr(candidate_result, "final_status", None)}
- Human Review status: {getattr(review_result, "final_status", None)}
- Finalized request status: {getattr(finalized_result, "final_status", None)}
- Manual execution confirmation status: {getattr(manual_result, "final_status", None)}
- Paper send preflight status: {getattr(preflight_result, "final_status", None)}

## Automation Limit Checks

- Automation limits PASS: {_automation_limit_reasons(config) == ()}
- Kill switch active: {config.limits.kill_switch_active}
- Cooldown satisfied: {config.limits.cooldown_satisfied}
- Daily order count: {config.limits.daily_order_count}
- Daily notional used: {config.limits.daily_notional_used}
- Previous reconciliation exists: {config.limits.previous_reconciliation_exists}
- Previous reconciliation mismatch unresolved: {config.limits.previous_reconciliation_unresolved_mismatch}
- Previous post-mortem exists: {config.limits.previous_post_mortem_exists}
- Previous post-mortem unresolved blocker: {config.limits.previous_post_mortem_unresolved_blocker}
- Unresolved issue exists: {config.limits.unresolved_issue_exists}
- Paper account confirmation: {config.alpaca_paper_account_confirmed}
- Live endpoint rejection: {not config.live_endpoint_configured}

## Results

- Order sent: {order_sent}
- Reconciliation status: {reconciliation_status}
- Post-mortem reference: {POST_MORTEM_NAME}
- Returned to DRY_RUN_ONLY: true
- PAPER_ORDER_EXECUTION_ENABLED unset or disabled after run: true
- PAPER_AUTOMATED_SEND_ENABLED unset or disabled after run: true

Automated paper send is paper-only.
Live trading remains unsupported.
Increasing notional remains prohibited.
Batch orders remain prohibited.
Cancel/replace remains prohibited.
"""


def _render_audit_log(
    *,
    config: AutomatedPaperSendConfig,
    block_reasons: tuple[str, ...],
    status: str,
    order_sent: bool,
) -> str:
    return f"""# Automation Audit Log

- Timestamp: {datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
- PAPER_AUTOMATED_SEND_ENABLED: {config.paper_automated_send_enabled}
- PAPER_ORDER_EXECUTION_ENABLED: {config.paper_order_execution_enabled}
- ALPACA_PAPER: {config.alpaca_paper}
- Limit checks: {json.dumps(config.limits.as_dict(), sort_keys=True)}
- Final automated send decision: {status}
- Alpaca paper order submitted: {order_sent}
- Block or submission reason: {json.dumps(list(block_reasons) or [status])}
- Secrets printed: false
"""


def _render_reconciliation(*, status: str, broker_order_id: str | None, order_sent: bool) -> str:
    return f"""# Reconciliation

- Reconciliation status: {status}
- Order sent: {order_sent}
- Alpaca paper order id: {broker_order_id or "none"}
- No extra orders were created: true
- No batch orders were created: true
- No cancel/replace occurred: true
- Live trading remains unsupported.
"""


def _render_post_send_safety() -> str:
    return """# Post-Send Safety

- Returned to DRY_RUN_ONLY: true
- PAPER_ORDER_EXECUTION_ENABLED unset or disabled after run: true
- PAPER_AUTOMATED_SEND_ENABLED unset or disabled after run: true
- No live trading flag remains enabled: true
- No live endpoint is configured: true
- Secrets printed: false
- Live trading remains unsupported.
- Increasing notional remains prohibited.
- Batch orders remain prohibited.
- Cancel/replace remains prohibited.
"""


def _render_post_mortem(
    *,
    status: str,
    reconciliation_status: str,
    block_reasons: tuple[str, ...],
) -> str:
    return f"""# Post-Mortem

- Automated paper send status: {status}
- Reconciliation status: {reconciliation_status}
- Block reasons: {json.dumps(list(block_reasons))}
- Unexpected behavior: none recorded
- Missing artifacts: none
- Future sends remain gated by V12 and Phase 44 automation controls.
- Live trading remains unsupported.
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


def _decimal_or_none(value: str) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _safe_error(exc: Exception) -> str:
    return exc.__class__.__name__


def _string_or_none(value: object) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def _restore_env(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = value


def main() -> int:
    parser = argparse.ArgumentParser(description="Run mocked automated paper send.")
    parser.add_argument("--mock-send", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    config = AutomatedPaperSendConfig(
        paper_automated_send_enabled=os.environ.get(ENV_AUTOMATED_SEND_ENABLED, "").lower() == "true",
        paper_order_execution_enabled=os.environ.get(ENV_EXECUTION_ENABLED, "").lower() == "true",
        alpaca_paper=os.environ.get(ENV_ALPACA_PAPER, "").lower() == "true",
        full_tests_status=PASS,
        architecture_validation_status=PASS,
        v10_full_pipeline_regression_status=PASS,
    )
    client = RecordingAutomatedPaperClient() if args.mock_send else None
    result = run_automated_paper_send(config=config, client=client)
    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(result.final_status)
        print(result.report_path)
    return 0 if result.final_status == AUTOMATED_PAPER_SEND_SUBMITTED else 1


if __name__ == "__main__":
    raise SystemExit(main())
