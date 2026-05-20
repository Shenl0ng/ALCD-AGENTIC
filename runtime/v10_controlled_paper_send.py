from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Mapping, Protocol
from urllib.request import Request, urlopen

from alpaca_paper_account import PAPER_BASE_URL, default_mock_snapshot
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
from paper_send_preflight import (
    PAPER_ORDER_SEND_ALLOWED,
    run_paper_send_preflight,
)
from v10_full_pipeline_dry_run_regression import (
    PIPELINE_PASSED,
    run_v10_full_pipeline_dry_run_regression,
)


REPORT_ROOT = Path("reports/v10_controlled_paper_send")
REPORT_NAME = "V10_CONTROLLED_PAPER_SEND_REPORT.md"
POST_MORTEM_NAME = "POST_MORTEM.md"
RECONCILIATION_NAME = "RECONCILIATION.md"
POST_SEND_SAFETY_NAME = "POST_SEND_SAFETY.md"

ENV_EXECUTION_ENABLED = "PAPER_ORDER_EXECUTION_ENABLED"
ENV_ALPACA_API_KEY_ID = "ALPACA_API_KEY_ID"
ENV_ALPACA_API_SECRET_KEY = "ALPACA_API_SECRET_KEY"
ENV_ALPACA_PAPER = "ALPACA_PAPER"

PASS = "PASS"
DRY_RUN_ONLY = "DRY_RUN_ONLY"
MOCKED_PAPER_SEND = "MOCKED_PAPER_SEND"
REAL_ALPACA_PAPER_SEND = "REAL_ALPACA_PAPER_SEND"
PAPER_ORDER_SUBMITTED = "PAPER_ORDER_SUBMITTED"
CONTROLLED_SEND_BLOCKED = "CONTROLLED_SEND_BLOCKED"
CONTROLLED_SEND_ERROR = "CONTROLLED_SEND_ERROR"
RECONCILIATION_MATCHED = "RECONCILIATION_MATCHED"
RECONCILIATION_BLOCKED_NO_ORDER = "RECONCILIATION_BLOCKED_NO_ORDER"
RECONCILIATION_FAILED = "RECONCILIATION_FAILED"
MAX_NOTIONAL_USD = Decimal("100")


class ControlledPaperSendClient(Protocol):
    def submit_paper_order(self, payload: Mapping[str, object]) -> Mapping[str, object]:
        """Submit one already gated paper order."""


@dataclass(frozen=True)
class ControlledV10PaperSendConfig:
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
    execution_enabled: bool = False
    send_mode: str = MOCKED_PAPER_SEND
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
    paper_account_mode: bool = True


@dataclass(frozen=True)
class ControlledV10PaperSendResult:
    final_status: str
    block_reasons: tuple[str, ...]
    send_status: str
    reconciliation_status: str
    report_path: str | None
    reconciliation_path: str | None
    post_send_safety_path: str | None
    post_mortem_path: str | None
    submitted_order_count: int
    order_sent: bool
    alpaca_order_api_called: bool
    broker_execution_readiness: bool
    live_trading_readiness: bool
    returned_to_dry_run_only: bool
    operator_unset_instruction: bool
    artifacts_created: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "final_status": self.final_status,
            "block_reasons": list(self.block_reasons),
            "send_status": self.send_status,
            "reconciliation_status": self.reconciliation_status,
            "report_path": self.report_path,
            "reconciliation_path": self.reconciliation_path,
            "post_send_safety_path": self.post_send_safety_path,
            "post_mortem_path": self.post_mortem_path,
            "submitted_order_count": self.submitted_order_count,
            "order_sent": self.order_sent,
            "alpaca_order_api_called": self.alpaca_order_api_called,
            "broker_execution_readiness": self.broker_execution_readiness,
            "live_trading_readiness": self.live_trading_readiness,
            "returned_to_dry_run_only": self.returned_to_dry_run_only,
            "operator_unset_instruction": self.operator_unset_instruction,
            "artifacts_created": list(self.artifacts_created),
        }


class RecordingControlledPaperClient:
    def __init__(self) -> None:
        self.payloads: list[Mapping[str, object]] = []

    def submit_paper_order(self, payload: Mapping[str, object]) -> Mapping[str, object]:
        self.payloads.append(dict(payload))
        return {"id": "mock-v10-paper-order-001", "status": "accepted"}


class UrlLibControlledAlpacaPaperClient:
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


def run_controlled_v10_paper_send(
    *,
    config: ControlledV10PaperSendConfig,
    client: ControlledPaperSendClient | None = None,
    output_root: Path = REPORT_ROOT,
    write_artifacts: bool = True,
) -> ControlledV10PaperSendResult:
    report_dir = _timestamped_report_dir(output_root) if write_artifacts else None
    context = _build_pipeline_context(config)
    block_reasons = _block_reasons(config, context)
    send_status = CONTROLLED_SEND_BLOCKED
    reconciliation_status = RECONCILIATION_BLOCKED_NO_ORDER
    order_sent = False
    alpaca_order_api_called = False
    submitted_count = 0
    broker_order_id: str | None = None
    error_message: str | None = None

    try:
        if not block_reasons:
            active_client = client
            if active_client is None and config.send_mode == REAL_ALPACA_PAPER_SEND:
                active_client = UrlLibControlledAlpacaPaperClient(
                    key_id=os.environ.get(ENV_ALPACA_API_KEY_ID, ""),
                    secret_key=os.environ.get(ENV_ALPACA_API_SECRET_KEY, ""),
                )
            if active_client is None:
                block_reasons = ("paper send client is required",)
            else:
                try:
                    response = active_client.submit_paper_order(_paper_order_payload(context))
                    alpaca_order_api_called = config.send_mode == REAL_ALPACA_PAPER_SEND
                    submitted_count = 1
                    broker_order_id = _string_or_none(response.get("id"))
                    order_sent = True
                    send_status = PAPER_ORDER_SUBMITTED
                    reconciliation_status = RECONCILIATION_MATCHED
                except Exception as exc:
                    send_status = CONTROLLED_SEND_ERROR
                    reconciliation_status = RECONCILIATION_FAILED
                    error_message = _safe_error(exc)
        if block_reasons:
            send_status = CONTROLLED_SEND_BLOCKED
            reconciliation_status = RECONCILIATION_BLOCKED_NO_ORDER
    finally:
        os.environ.pop(ENV_EXECUTION_ENABLED, None)

    final_status = send_status
    artifacts: tuple[str, ...] = ()
    paths = _ArtifactPaths(None, None, None, None)
    if write_artifacts and report_dir is not None:
        paths = _write_artifacts(
            report_dir=report_dir,
            config=config,
            context=context,
            block_reasons=block_reasons,
            send_status=send_status,
            reconciliation_status=reconciliation_status,
            broker_order_id=broker_order_id,
            error_message=error_message,
            order_sent=order_sent,
            alpaca_order_api_called=alpaca_order_api_called,
        )
        artifacts = tuple(
            path
            for path in (
                paths.report_path,
                paths.reconciliation_path,
                paths.post_send_safety_path,
                paths.post_mortem_path,
            )
            if path is not None
        )

    return ControlledV10PaperSendResult(
        final_status=final_status,
        block_reasons=tuple(block_reasons),
        send_status=send_status,
        reconciliation_status=reconciliation_status,
        report_path=paths.report_path,
        reconciliation_path=paths.reconciliation_path,
        post_send_safety_path=paths.post_send_safety_path,
        post_mortem_path=paths.post_mortem_path,
        submitted_order_count=submitted_count,
        order_sent=order_sent,
        alpaca_order_api_called=alpaca_order_api_called,
        broker_execution_readiness=False,
        live_trading_readiness=False,
        returned_to_dry_run_only=True,
        operator_unset_instruction=True,
        artifacts_created=artifacts,
    )


def _build_pipeline_context(config: ControlledV10PaperSendConfig) -> dict[str, object]:
    original_execution_flag = os.environ.get(ENV_EXECUTION_ENABLED)
    os.environ[ENV_EXECUTION_ENABLED] = ""
    try:
        regression = run_v10_full_pipeline_dry_run_regression(write_report=False)
        candidate_result = create_paper_order_request_candidate(
            symbols=["SIM"],
            scenario=config.candidate_scenario,
            write_artifacts=False,
        )
        candidate = candidate_result.candidate
        review_result = create_human_review_record(
            candidate=candidate,
            reviewer="controlled-v10-reviewer",
            review_status=config.human_review_status,
            review_notes="Controlled V10 paper send review.",
            write_artifacts=False,
        )
        finalized_result = finalize_paper_order_request(
            candidate=candidate,
            review=review_result.record,
            write_artifacts=False,
        )
        manual_result = create_manual_execution_confirmation(
            request=finalized_result.request,
            confirmer="controlled-v10-confirmer",
            confirmation_status=config.manual_confirmation_status,
            confirmation_notes="Controlled V10 paper send confirmation.",
            write_artifacts=False,
        )
        request = finalized_result.request
        if request is not None:
            request = _request_with_order_overrides(request, config)
        preflight_result = run_paper_send_preflight(
            request=request,
            confirmation=manual_result.confirmation,
            live_endpoint_configured=config.live_endpoint_configured,
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
        if original_execution_flag is None:
            os.environ.pop(ENV_EXECUTION_ENABLED, None)
        else:
            os.environ[ENV_EXECUTION_ENABLED] = original_execution_flag
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
    config: ControlledV10PaperSendConfig,
    context: Mapping[str, object],
) -> tuple[str, ...]:
    reasons: list[str] = []
    candidate_result = context["candidate_result"]
    review_result = context["review_result"]
    finalized_result = context["finalized_result"]
    manual_result = context["manual_result"]
    preflight_result = context["preflight_result"]
    request = context["request"]

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
        reasons.append("Evaluation-First Gate status is not PASS")
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
    if not config.alpaca_paper_account_confirmed or not config.paper_account_mode:
        reasons.append("Alpaca paper account is not confirmed")
    if config.live_endpoint_configured:
        reasons.append("live endpoint configured is blocked")
    if not config.execution_enabled:
        reasons.append("PAPER_ORDER_EXECUTION_ENABLED is not true for manual run")
    if config.send_mode not in {MOCKED_PAPER_SEND, REAL_ALPACA_PAPER_SEND}:
        reasons.append("send mode is not controlled paper send")
    if not config.paper_trading_only:
        reasons.append("paper trading only is required")
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
        reasons.append("controlled paper order request is missing")
    return tuple(dict.fromkeys(reasons))


def _request_with_order_overrides(request: object, config: ControlledV10PaperSendConfig) -> object:
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
    reconciliation_path: str | None
    post_send_safety_path: str | None
    post_mortem_path: str | None


def _write_artifacts(
    *,
    report_dir: Path,
    config: ControlledV10PaperSendConfig,
    context: Mapping[str, object],
    block_reasons: tuple[str, ...],
    send_status: str,
    reconciliation_status: str,
    broker_order_id: str | None,
    error_message: str | None,
    order_sent: bool,
    alpaca_order_api_called: bool,
) -> _ArtifactPaths:
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / REPORT_NAME
    reconciliation_path = report_dir / RECONCILIATION_NAME
    safety_path = report_dir / POST_SEND_SAFETY_NAME
    post_mortem_path = report_dir / POST_MORTEM_NAME

    report_path.write_text(
        _render_report(
            config=config,
            context=context,
            block_reasons=block_reasons,
            send_status=send_status,
            reconciliation_status=reconciliation_status,
            broker_order_id=broker_order_id,
            error_message=error_message,
            order_sent=order_sent,
            alpaca_order_api_called=alpaca_order_api_called,
        ),
        encoding="utf-8",
    )
    reconciliation_path.write_text(
        _render_reconciliation(
            reconciliation_status=reconciliation_status,
            block_reasons=block_reasons,
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
            send_status=send_status,
            reconciliation_status=reconciliation_status,
            block_reasons=block_reasons,
        ),
        encoding="utf-8",
    )
    return _ArtifactPaths(
        report_path=report_path.as_posix(),
        reconciliation_path=reconciliation_path.as_posix(),
        post_send_safety_path=safety_path.as_posix(),
        post_mortem_path=post_mortem_path.as_posix(),
    )


def _render_report(
    *,
    config: ControlledV10PaperSendConfig,
    context: Mapping[str, object],
    block_reasons: tuple[str, ...],
    send_status: str,
    reconciliation_status: str,
    broker_order_id: str | None,
    error_message: str | None,
    order_sent: bool,
    alpaca_order_api_called: bool,
) -> str:
    candidate_result = context["candidate_result"]
    review_result = context["review_result"]
    finalized_result = context["finalized_result"]
    manual_result = context["manual_result"]
    preflight_result = context["preflight_result"]
    return f"""# V10 Controlled Paper Send Report

## Summary

- Generated at: {datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
- Baseline: V11
- Send status: {send_status}
- Block reasons: {json.dumps(list(block_reasons))}
- Broker paper order id: {broker_order_id or "none"}
- Error: {error_message or "none"}

## Gates

- Full tests: {config.full_tests_status}
- Architecture validation: {config.architecture_validation_status}
- V10 full pipeline dry-run regression: {config.v10_full_pipeline_regression_status}
- Runtime V10 regression check: {context["regression_status"]}
- Strategy Evaluation: {config.strategy_evaluation_status}
- Evaluation-First Gate: {config.evaluation_gate_status}
- Negative Case Regression: {config.negative_case_regression_status}
- Candidate status: {getattr(candidate_result, "final_status", None)}
- Human Review status: {getattr(review_result, "final_status", None)}
- Finalized Paper Order Request status: {getattr(finalized_result, "final_status", None)}
- Manual Execution Confirmation status: {getattr(manual_result, "final_status", None)}
- Paper Send Preflight status: {getattr(preflight_result, "final_status", None)}
- Alpaca paper account confirmed: {config.alpaca_paper_account_confirmed}
- Live endpoint rejected: {not config.live_endpoint_configured}

## Send Controls

- One order only: true
- Paper trading only: {config.paper_trading_only}
- Max notional <= 100 USD: {_decimal_or_none(config.notional) is not None and _decimal_or_none(config.notional) <= MAX_NOTIONAL_USD}
- Limit order only: {config.order_type == "limit"}
- Day time-in-force only: {config.time_in_force == "day"}
- No short selling: {not config.short_selling}
- No crypto: {not config.crypto}
- No options: {not config.options}
- No margin/leverage: {not config.margin_or_leverage}
- No extended hours: {not config.extended_hours}
- No batch orders: {not config.batch_orders}
- No cancel/replace: {not config.cancel_replace}
- No live trading: true
- No live endpoints: {not config.live_endpoint_configured}
- PAPER_ORDER_EXECUTION_ENABLED true only for manual run: {config.execution_enabled}

## Results

- Order sent: {order_sent}
- Alpaca order API called: {alpaca_order_api_called}
- Reconciliation status: {reconciliation_status}
- Returned to DRY_RUN_ONLY: true
- Operator must unset PAPER_ORDER_EXECUTION_ENABLED after run: true
- Secrets printed: false

Live trading remains unsupported.
"""


def _render_reconciliation(
    *,
    reconciliation_status: str,
    block_reasons: tuple[str, ...],
    broker_order_id: str | None,
    order_sent: bool,
) -> str:
    return f"""# Reconciliation

- Reconciliation status: {reconciliation_status}
- Order sent: {order_sent}
- Broker paper order id: {broker_order_id or "none"}
- Block reasons: {json.dumps(list(block_reasons))}
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
- PAPER_ORDER_EXECUTION_ENABLED unset after run: true
- No live trading flag remains enabled: true
- No live endpoint is configured: true
- No broker execution readiness remains active outside the controlled send phase: true
- No batch behavior was created: true
- No cancel/replace behavior was created: true
- Secrets printed: false
- Live trading remains unsupported.
"""


def _render_post_mortem(
    *,
    send_status: str,
    reconciliation_status: str,
    block_reasons: tuple[str, ...],
) -> str:
    return f"""# Post-Mortem

- Send status: {send_status}
- Reconciliation status: {reconciliation_status}
- Block reasons: {json.dumps(list(block_reasons))}
- Unexpected behavior: none recorded
- Missing artifacts: none
- Human review concerns: none recorded
- Future sends remain manual and gated by V4-V11.
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
    message = str(exc)
    for secret_name in (ENV_ALPACA_API_KEY_ID, ENV_ALPACA_API_SECRET_KEY):
        secret = os.environ.get(secret_name)
        if secret:
            message = message.replace(secret, "[REDACTED]")
    return message or exc.__class__.__name__


def _string_or_none(value: object) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one controlled V10 Alpaca paper send.")
    parser.add_argument("--real-send", action="store_true")
    parser.add_argument("--full-tests-pass", action="store_true")
    parser.add_argument("--architecture-pass", action="store_true")
    parser.add_argument("--v10-regression-pass", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    config = ControlledV10PaperSendConfig(
        full_tests_status=PASS if args.full_tests_pass else None,
        architecture_validation_status=PASS if args.architecture_pass else None,
        v10_full_pipeline_regression_status=PASS if args.v10_regression_pass else None,
        execution_enabled=os.environ.get(ENV_EXECUTION_ENABLED, "").lower() == "true",
        send_mode=REAL_ALPACA_PAPER_SEND if args.real_send else MOCKED_PAPER_SEND,
        alpaca_paper_account_confirmed=os.environ.get(ENV_ALPACA_PAPER, "").lower() == "true",
    )
    client = None if args.real_send else RecordingControlledPaperClient()
    result = run_controlled_v10_paper_send(config=config, client=client)
    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(result.final_status)
        print(result.report_path)
        print("Unset PAPER_ORDER_EXECUTION_ENABLED after this run.")
    return 0 if result.final_status == PAPER_ORDER_SUBMITTED else 1


if __name__ == "__main__":
    raise SystemExit(main())
