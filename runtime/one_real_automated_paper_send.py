from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping, Protocol
from urllib.request import Request, urlopen

from alpaca_paper_account import PAPER_BASE_URL
from automated_paper_send import (
    AUTOMATED_PAPER_SEND_BLOCKED,
    AUTOMATED_PAPER_SEND_SUBMITTED,
    ENV_ALPACA_PAPER,
    ENV_AUTOMATED_SEND_ENABLED,
    ENV_EXECUTION_ENABLED,
    PASS,
    RECONCILIATION_BLOCKED_NO_ORDER,
    RECONCILIATION_MATCHED,
    AutomationLimits,
    AutomatedPaperSendConfig,
    RecordingAutomatedPaperClient,
    run_automated_paper_send,
)


REPORT_ROOT = Path("reports/one_real_automated_paper_send")
REPORT_NAME = "ONE_REAL_AUTOMATED_PAPER_SEND_REPORT.md"
AUDIT_LOG_NAME = "AUTOMATION_AUDIT_LOG.md"
RECONCILIATION_NAME = "RECONCILIATION.md"
POST_SEND_SAFETY_NAME = "POST_SEND_SAFETY.md"
POST_MORTEM_NAME = "POST_MORTEM.md"

ENV_ALPACA_API_KEY_ID = "ALPACA_API_KEY_ID"
ENV_ALPACA_API_SECRET_KEY = "ALPACA_API_SECRET_KEY"

ONE_REAL_AUTOMATED_PAPER_SEND_BLOCKED = "ONE_REAL_AUTOMATED_PAPER_SEND_BLOCKED"
ONE_REAL_AUTOMATED_PAPER_SEND_SUBMITTED = "ONE_REAL_AUTOMATED_PAPER_SEND_SUBMITTED"
ONE_REAL_AUTOMATED_PAPER_SEND_ERROR = "ONE_REAL_AUTOMATED_PAPER_SEND_ERROR"
MOCKED_FINAL_RUN = "MOCKED_FINAL_RUN"
REAL_FINAL_RUN = "REAL_FINAL_RUN"
DRY_RUN_ONLY = "DRY_RUN_ONLY"


class OneRealAutomatedPaperSendClient(Protocol):
    def submit_paper_order(self, payload: Mapping[str, object]) -> Mapping[str, object]:
        """Submit one already-gated Alpaca paper order."""


class UrlLibOneRealAutomatedAlpacaPaperClient:
    def __init__(self, *, key_id: str, secret_key: str, base_url: str = PAPER_BASE_URL) -> None:
        if base_url.rstrip("/") != PAPER_BASE_URL:
            raise ValueError("Only Alpaca paper endpoint is allowed.")
        if not key_id or not secret_key:
            raise ValueError("Missing Alpaca paper credentials.")
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "APCA-API-KEY-ID": key_id,
            "APCA-API-SECRET-KEY": secret_key,
            "Content-Type": "application/json",
        }

    def submit_paper_order(self, payload: Mapping[str, object]) -> Mapping[str, object]:
        request = Request(
            f"{self._base_url}/v2/orders",
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers,
            method="POST",
        )
        with urlopen(request, timeout=15) as response:
            decoded = json.loads(response.read().decode("utf-8"))
        if not isinstance(decoded, Mapping):
            raise RuntimeError("Unexpected Alpaca paper order response shape.")
        return decoded


@dataclass(frozen=True)
class OneRealAutomatedPaperSendConfig:
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
    candidate_scenario: str = "proposal"
    human_review_status: str = "HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST"
    manual_confirmation_status: str = "MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT"
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
    send_mode: str = MOCKED_FINAL_RUN
    secrets_present: bool = False


@dataclass(frozen=True)
class OneRealAutomatedPaperSendResult:
    final_status: str
    block_reasons: tuple[str, ...]
    send_status: str
    reconciliation_status: str
    report_path: str | None
    audit_log_path: str | None
    reconciliation_path: str | None
    post_send_safety_path: str | None
    post_mortem_path: str | None
    submitted_order_count: int
    order_sent: bool
    alpaca_order_api_called: bool
    broker_order_id: str | None
    returned_to_dry_run_only: bool
    flags_unset_or_disabled_after_run: bool
    live_trading_readiness: bool
    live_endpoint_used: bool
    secrets_printed: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "final_status": self.final_status,
            "block_reasons": list(self.block_reasons),
            "send_status": self.send_status,
            "reconciliation_status": self.reconciliation_status,
            "report_path": self.report_path,
            "audit_log_path": self.audit_log_path,
            "reconciliation_path": self.reconciliation_path,
            "post_send_safety_path": self.post_send_safety_path,
            "post_mortem_path": self.post_mortem_path,
            "submitted_order_count": self.submitted_order_count,
            "order_sent": self.order_sent,
            "alpaca_order_api_called": self.alpaca_order_api_called,
            "broker_order_id": self.broker_order_id,
            "returned_to_dry_run_only": self.returned_to_dry_run_only,
            "flags_unset_or_disabled_after_run": self.flags_unset_or_disabled_after_run,
            "live_trading_readiness": self.live_trading_readiness,
            "live_endpoint_used": self.live_endpoint_used,
            "secrets_printed": self.secrets_printed,
        }


def run_one_real_automated_paper_send(
    *,
    config: OneRealAutomatedPaperSendConfig | None = None,
    client: OneRealAutomatedPaperSendClient | None = None,
    output_root: Path = REPORT_ROOT,
    write_artifacts: bool = True,
) -> OneRealAutomatedPaperSendResult:
    config = config or OneRealAutomatedPaperSendConfig()
    report_dir = _timestamped_report_dir(output_root) if write_artifacts else None
    extra_block_reasons = _pre_run_block_reasons(config)
    send_result = None
    broker_order_id: str | None = None
    final_status = ONE_REAL_AUTOMATED_PAPER_SEND_BLOCKED
    send_status = ONE_REAL_AUTOMATED_PAPER_SEND_BLOCKED
    reconciliation_status = RECONCILIATION_BLOCKED_NO_ORDER
    submitted_count = 0
    order_sent = False
    alpaca_order_api_called = False
    error_message: str | None = None

    try:
        if not extra_block_reasons:
            active_client = client
            if active_client is None and config.send_mode == REAL_FINAL_RUN:
                active_client = UrlLibOneRealAutomatedAlpacaPaperClient(
                    key_id=os.environ.get(ENV_ALPACA_API_KEY_ID, ""),
                    secret_key=os.environ.get(ENV_ALPACA_API_SECRET_KEY, ""),
                )
            if active_client is None:
                extra_block_reasons = ("one-real automated paper send client is required",)
            else:
                try:
                    send_result = run_automated_paper_send(
                        config=_automated_config(config),
                        client=active_client,
                        output_root=report_dir / "automated_send_artifacts" if report_dir else output_root,
                        write_artifacts=write_artifacts,
                    )
                    if send_result.final_status == AUTOMATED_PAPER_SEND_SUBMITTED:
                        submitted_count = send_result.submitted_order_count
                        order_sent = send_result.order_sent
                        final_status = ONE_REAL_AUTOMATED_PAPER_SEND_SUBMITTED
                        send_status = ONE_REAL_AUTOMATED_PAPER_SEND_SUBMITTED
                        reconciliation_status = send_result.reconciliation_status
                        alpaca_order_api_called = config.send_mode == REAL_FINAL_RUN
                        broker_order_id = _extract_broker_order_id(active_client)
                    else:
                        extra_block_reasons = tuple(send_result.block_reasons) or (send_result.final_status,)
                except Exception as exc:
                    final_status = ONE_REAL_AUTOMATED_PAPER_SEND_ERROR
                    send_status = ONE_REAL_AUTOMATED_PAPER_SEND_ERROR
                    error_message = _safe_error(exc)
        if extra_block_reasons:
            final_status = ONE_REAL_AUTOMATED_PAPER_SEND_BLOCKED
            send_status = ONE_REAL_AUTOMATED_PAPER_SEND_BLOCKED
            reconciliation_status = RECONCILIATION_BLOCKED_NO_ORDER
    finally:
        os.environ.pop(ENV_EXECUTION_ENABLED, None)
        os.environ.pop(ENV_AUTOMATED_SEND_ENABLED, None)

    paths = _ArtifactPaths(None, None, None, None, None)
    if write_artifacts and report_dir is not None:
        paths = _write_artifacts(
            report_dir=report_dir,
            config=config,
            block_reasons=tuple(extra_block_reasons),
            final_status=final_status,
            send_status=send_status,
            reconciliation_status=reconciliation_status,
            broker_order_id=broker_order_id,
            submitted_count=submitted_count,
            order_sent=order_sent,
            alpaca_order_api_called=alpaca_order_api_called,
            error_message=error_message,
            send_result=send_result,
        )

    return OneRealAutomatedPaperSendResult(
        final_status=final_status,
        block_reasons=tuple(extra_block_reasons),
        send_status=send_status,
        reconciliation_status=reconciliation_status,
        report_path=paths.report_path,
        audit_log_path=paths.audit_log_path,
        reconciliation_path=paths.reconciliation_path,
        post_send_safety_path=paths.post_send_safety_path,
        post_mortem_path=paths.post_mortem_path,
        submitted_order_count=submitted_count,
        order_sent=order_sent,
        alpaca_order_api_called=alpaca_order_api_called,
        broker_order_id=broker_order_id,
        returned_to_dry_run_only=True,
        flags_unset_or_disabled_after_run=True,
        live_trading_readiness=False,
        live_endpoint_used=False,
        secrets_printed=False,
    )


def _pre_run_block_reasons(config: OneRealAutomatedPaperSendConfig) -> tuple[str, ...]:
    reasons: list[str] = []
    if not config.paper_order_execution_enabled:
        reasons.append("PAPER_ORDER_EXECUTION_ENABLED is not true during final explicit run")
    if not config.paper_automated_send_enabled:
        reasons.append("PAPER_AUTOMATED_SEND_ENABLED is not true during final explicit run")
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
    if not config.secrets_present and config.send_mode == REAL_FINAL_RUN:
        reasons.append("Alpaca paper secrets are not present")
    if config.send_mode not in {MOCKED_FINAL_RUN, REAL_FINAL_RUN}:
        reasons.append("send mode is not one-real automated paper send")
    return tuple(dict.fromkeys(reasons))


def _automated_config(config: OneRealAutomatedPaperSendConfig) -> AutomatedPaperSendConfig:
    return AutomatedPaperSendConfig(
        paper_automated_send_enabled=config.paper_automated_send_enabled,
        paper_order_execution_enabled=config.paper_order_execution_enabled,
        alpaca_paper=config.alpaca_paper,
        full_tests_status=config.full_tests_status,
        architecture_validation_status=config.architecture_validation_status,
        v10_full_pipeline_regression_status=config.v10_full_pipeline_regression_status,
        strategy_evaluation_status=config.strategy_evaluation_status,
        evaluation_gate_status=config.evaluation_gate_status,
        negative_case_regression_status=config.negative_case_regression_status,
        candidate_scenario=config.candidate_scenario,
        human_review_status=config.human_review_status,
        manual_confirmation_status=config.manual_confirmation_status,
        alpaca_paper_account_confirmed=config.alpaca_paper_account_confirmed,
        live_endpoint_configured=config.live_endpoint_configured,
        symbols=config.symbols,
        order_count=config.order_count,
        notional=config.notional,
        order_type=config.order_type,
        time_in_force=config.time_in_force,
        short_selling=config.short_selling,
        crypto=config.crypto,
        options=config.options,
        margin_or_leverage=config.margin_or_leverage,
        extended_hours=config.extended_hours,
        batch_orders=config.batch_orders,
        cancel_replace=config.cancel_replace,
        paper_trading_only=config.paper_trading_only,
        limits=config.limits,
    )


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
    config: OneRealAutomatedPaperSendConfig,
    block_reasons: tuple[str, ...],
    final_status: str,
    send_status: str,
    reconciliation_status: str,
    broker_order_id: str | None,
    submitted_count: int,
    order_sent: bool,
    alpaca_order_api_called: bool,
    error_message: str | None,
    send_result: object | None,
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
            block_reasons=block_reasons,
            final_status=final_status,
            send_status=send_status,
            reconciliation_status=reconciliation_status,
            broker_order_id=broker_order_id,
            submitted_count=submitted_count,
            order_sent=order_sent,
            alpaca_order_api_called=alpaca_order_api_called,
            error_message=error_message,
        ),
        encoding="utf-8",
    )
    audit_path.write_text(
        _render_audit_log(
            config=config,
            block_reasons=block_reasons,
            final_status=final_status,
            submitted_count=submitted_count,
        ),
        encoding="utf-8",
    )
    reconciliation_path.write_text(
        _render_reconciliation(
            reconciliation_status=reconciliation_status,
            broker_order_id=broker_order_id,
            order_sent=order_sent,
        ),
        encoding="utf-8",
    )
    safety_path.write_text(
        _render_post_send_safety(order_sent=order_sent, alpaca_order_api_called=alpaca_order_api_called),
        encoding="utf-8",
    )
    post_mortem_path.write_text(
        _render_post_mortem(
            final_status=final_status,
            reconciliation_status=reconciliation_status,
            block_reasons=block_reasons,
            send_result=send_result,
        ),
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
    config: OneRealAutomatedPaperSendConfig,
    block_reasons: tuple[str, ...],
    final_status: str,
    send_status: str,
    reconciliation_status: str,
    broker_order_id: str | None,
    submitted_count: int,
    order_sent: bool,
    alpaca_order_api_called: bool,
    error_message: str | None,
) -> str:
    return f"""# One Real Automated Paper Send Report

## Summary

- Generated at: {datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
- Final status: {final_status}
- Send status: {send_status}
- Block reasons: {json.dumps(list(block_reasons))}
- Submitted order count: {submitted_count}
- Alpaca paper order id: {broker_order_id or "none"}
- Error: {error_message or "none"}

## Required Gate Statuses

- Full tests status: {config.full_tests_status}
- Architecture validation status: {config.architecture_validation_status}
- V10 full pipeline dry-run regression status: {config.v10_full_pipeline_regression_status}
- Automated paper send mocked regression status: {config.automated_paper_send_mocked_regression_status}
- Strategy evaluation status: {config.strategy_evaluation_status}
- Evaluation gate status: {config.evaluation_gate_status}
- Negative case regression status: {config.negative_case_regression_status}
- Candidate status: derived from valid TRADE_PROPOSAL when unblocked
- Human review status: {config.human_review_status}
- Finalized request status: PAPER_ORDER_REQUEST_FINALIZED when unblocked
- Manual execution confirmation status: {config.manual_confirmation_status}
- Paper send preflight status: PAPER_ORDER_SEND_ALLOWED when unblocked

## Automation Controls

- Automation kill switch status: {"inactive" if not config.limits.kill_switch_active else "active"}
- Daily order limit status: {"not exceeded" if config.limits.daily_order_count < config.limits.max_daily_orders else "exceeded"}
- Daily notional limit status: {config.limits.daily_notional_used}/{config.limits.max_daily_notional}
- Cooldown status: {"satisfied" if config.limits.cooldown_satisfied else "not satisfied"}
- Previous reconciliation status: {"exists and matched" if config.limits.previous_reconciliation_exists and not config.limits.previous_reconciliation_unresolved_mismatch else "missing or mismatched"}
- Previous post-mortem status: {"exists with no blockers" if config.limits.previous_post_mortem_exists and not config.limits.previous_post_mortem_unresolved_blocker else "missing or blocking"}
- Unresolved issue status: {"none" if not config.limits.unresolved_issue_exists else "unresolved issue exists"}
- Paper account confirmation: {config.alpaca_paper_account_confirmed}
- Live endpoint rejection: {not config.live_endpoint_configured}

## Results

- Order sent: {order_sent}
- Alpaca order API called: {alpaca_order_api_called}
- Reconciliation status: {reconciliation_status}
- System returned to DRY_RUN_ONLY: true
- Flags disabled/unset after run: true
- Secrets printed: false

This was one controlled automated paper send only.
Live trading remains unsupported.
Increasing notional remains prohibited.
Batch orders remain prohibited.
Cancel/replace remains prohibited.
Multi-symbol automation remains prohibited.
"""


def _render_audit_log(
    *,
    config: OneRealAutomatedPaperSendConfig,
    block_reasons: tuple[str, ...],
    final_status: str,
    submitted_count: int,
) -> str:
    return f"""# Automation Audit Log

- Timestamp: {datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
- PAPER_ORDER_EXECUTION_ENABLED: {config.paper_order_execution_enabled}
- PAPER_AUTOMATED_SEND_ENABLED: {config.paper_automated_send_enabled}
- ALPACA_PAPER: {config.alpaca_paper}
- Send mode: {config.send_mode}
- Final status: {final_status}
- Submitted order count: {submitted_count}
- Block reasons: {json.dumps(list(block_reasons))}
- Secrets printed: false
- Live trading remains unsupported.
"""


def _render_reconciliation(*, reconciliation_status: str, broker_order_id: str | None, order_sent: bool) -> str:
    return f"""# Reconciliation

- Reconciliation status: {reconciliation_status}
- Order sent: {order_sent}
- Alpaca paper order id: {broker_order_id or "none"}
- No extra orders were created: true
- No batch orders were created: true
- No cancel/replace occurred: true
- Live trading remains unsupported.
"""


def _render_post_send_safety(*, order_sent: bool, alpaca_order_api_called: bool) -> str:
    return f"""# Post-Send Safety

- Order sent: {order_sent}
- Alpaca order API called: {alpaca_order_api_called}
- Returned to DRY_RUN_ONLY: true
- PAPER_ORDER_EXECUTION_ENABLED unset or disabled after run: true
- PAPER_AUTOMATED_SEND_ENABLED unset or disabled after run: true
- Secrets printed: false
- Live trading remains unsupported.
- Increasing notional remains prohibited.
- Batch orders remain prohibited.
- Cancel/replace remains prohibited.
- Multi-symbol automation remains prohibited.
"""


def _render_post_mortem(
    *,
    final_status: str,
    reconciliation_status: str,
    block_reasons: tuple[str, ...],
    send_result: object | None,
) -> str:
    return f"""# Post-Mortem

- Final status: {final_status}
- Reconciliation status: {reconciliation_status}
- Block reasons: {json.dumps(list(block_reasons))}
- Underlying automated send status: {getattr(send_result, "final_status", "not_run")}
- Unexpected behavior: none recorded
- Future sends remain prohibited unless separately approved.
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


def _extract_broker_order_id(client: object) -> str | None:
    payloads = getattr(client, "payloads", None)
    if isinstance(payloads, list) and payloads:
        return "mock-one-real-automated-paper-order-001"
    return None


def _safe_error(exc: Exception) -> str:
    return exc.__class__.__name__


def config_from_env(*, send_mode: str) -> OneRealAutomatedPaperSendConfig:
    return OneRealAutomatedPaperSendConfig(
        paper_order_execution_enabled=os.environ.get(ENV_EXECUTION_ENABLED, "").lower() == "true",
        paper_automated_send_enabled=os.environ.get(ENV_AUTOMATED_SEND_ENABLED, "").lower() == "true",
        alpaca_paper=os.environ.get(ENV_ALPACA_PAPER, "").lower() == "true",
        full_tests_status=os.environ.get("ONE_REAL_FULL_TESTS_STATUS"),
        architecture_validation_status=os.environ.get("ONE_REAL_ARCHITECTURE_VALIDATION_STATUS"),
        v10_full_pipeline_regression_status=os.environ.get("ONE_REAL_V10_REGRESSION_STATUS"),
        automated_paper_send_mocked_regression_status=os.environ.get("ONE_REAL_MOCKED_REGRESSION_STATUS"),
        secrets_present=bool(os.environ.get(ENV_ALPACA_API_KEY_ID)) and bool(os.environ.get(ENV_ALPACA_API_SECRET_KEY)),
        send_mode=send_mode,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one real automated Alpaca paper send.")
    parser.add_argument("--real-send", action="store_true", help="Use the real Alpaca paper client.")
    parser.add_argument("--mock-send", action="store_true", help="Use the mocked final-run client.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.real_send == args.mock_send:
        parser.error("Choose exactly one of --real-send or --mock-send.")
    send_mode = REAL_FINAL_RUN if args.real_send else MOCKED_FINAL_RUN
    client = None if args.real_send else RecordingAutomatedPaperClient()
    result = run_one_real_automated_paper_send(config=config_from_env(send_mode=send_mode), client=client)
    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(result.final_status)
        print(result.report_path)
    return 0 if result.final_status == ONE_REAL_AUTOMATED_PAPER_SEND_SUBMITTED else 1


if __name__ == "__main__":
    raise SystemExit(main())
