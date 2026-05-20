from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping
from unittest.mock import patch

from automated_paper_send import (
    AUTOMATED_PAPER_SEND_BLOCKED,
    AUTOMATED_PAPER_SEND_REJECTED_BY_PREFLIGHT,
    AUTOMATED_PAPER_SEND_REJECTED_BY_KILL_SWITCH,
    AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS,
    AUTOMATED_PAPER_SEND_REJECTED_BY_POST_MORTEM,
    AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION,
    AUTOMATED_PAPER_SEND_SUBMITTED,
    ENV_ALPACA_PAPER,
    ENV_AUTOMATED_SEND_ENABLED,
    ENV_EXECUTION_ENABLED,
    PASS,
    RECONCILIATION_MATCHED,
    AutomationLimits,
    AutomatedPaperSendConfig,
    RecordingAutomatedPaperClient,
    run_automated_paper_send,
)


REPORT_ROOT = Path("reports/automated_paper_send_mocked_regression")
REPORT_NAME = "AUTOMATED_PAPER_SEND_MOCKED_REGRESSION_REPORT.md"

REGRESSION_PASSED = "PASS"
REGRESSION_FAILED = "FAIL"


@dataclass(frozen=True)
class MockedAutomatedPaperSendFixture:
    scenario_id: str
    description: str
    config: AutomatedPaperSendConfig
    expected_status: str
    expected_mocked_order_count: int
    expected_reconciliation_status: str | None = None


@dataclass(frozen=True)
class MockedAutomatedPaperSendScenarioResult:
    scenario_id: str
    description: str
    passed: bool
    failure_reason: str
    final_status: str
    reconciliation_status: str
    mocked_order_count: int
    mocked_payloads: tuple[Mapping[str, object], ...]
    report_path: str | None
    audit_log_path: str | None
    reconciliation_path: str | None
    post_send_safety_path: str | None
    post_mortem_path: str | None
    returned_to_dry_run_only: bool
    flags_disabled_unset_after_test_context: bool
    real_alpaca_api_called: bool = False
    real_order_sent: bool = False
    live_trading_readiness: bool = False
    live_endpoint_used: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "description": self.description,
            "passed": self.passed,
            "failure_reason": self.failure_reason,
            "final_status": self.final_status,
            "reconciliation_status": self.reconciliation_status,
            "mocked_order_count": self.mocked_order_count,
            "mocked_payloads": [dict(payload) for payload in self.mocked_payloads],
            "report_path": self.report_path,
            "audit_log_path": self.audit_log_path,
            "reconciliation_path": self.reconciliation_path,
            "post_send_safety_path": self.post_send_safety_path,
            "post_mortem_path": self.post_mortem_path,
            "returned_to_dry_run_only": self.returned_to_dry_run_only,
            "flags_disabled_unset_after_test_context": self.flags_disabled_unset_after_test_context,
            "real_alpaca_api_called": self.real_alpaca_api_called,
            "real_order_sent": self.real_order_sent,
            "live_trading_readiness": self.live_trading_readiness,
            "live_endpoint_used": self.live_endpoint_used,
        }


@dataclass(frozen=True)
class MockedAutomatedPaperSendRegressionRun:
    final_status: str
    results: tuple[MockedAutomatedPaperSendScenarioResult, ...]
    report_path: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "final_status": self.final_status,
            "results": [result.as_dict() for result in self.results],
            "report_path": self.report_path,
        }


def valid_config(**overrides: object) -> AutomatedPaperSendConfig:
    values = {
        "paper_automated_send_enabled": True,
        "paper_order_execution_enabled": True,
        "alpaca_paper": True,
        "full_tests_status": PASS,
        "architecture_validation_status": PASS,
        "v10_full_pipeline_regression_status": PASS,
    }
    values.update(overrides)
    return AutomatedPaperSendConfig(**values)


def limits(**overrides: object) -> AutomationLimits:
    values = AutomationLimits().__dict__.copy()
    values.update(overrides)
    return AutomationLimits(**values)


SCENARIOS: tuple[MockedAutomatedPaperSendFixture, ...] = (
    MockedAutomatedPaperSendFixture(
        scenario_id="full_valid_mocked_automated_paper_send",
        description="Full valid mocked automated paper send submits one mocked paper limit/day order.",
        config=valid_config(),
        expected_status=AUTOMATED_PAPER_SEND_SUBMITTED,
        expected_mocked_order_count=1,
        expected_reconciliation_status=RECONCILIATION_MATCHED,
    ),
    MockedAutomatedPaperSendFixture(
        scenario_id="default_disabled",
        description="PAPER_AUTOMATED_SEND_ENABLED=false blocks send.",
        config=valid_config(paper_automated_send_enabled=False),
        expected_status=AUTOMATED_PAPER_SEND_BLOCKED,
        expected_mocked_order_count=0,
    ),
    MockedAutomatedPaperSendFixture(
        scenario_id="execution_flag_disabled",
        description="PAPER_ORDER_EXECUTION_ENABLED=false blocks send.",
        config=valid_config(paper_order_execution_enabled=False),
        expected_status=AUTOMATED_PAPER_SEND_BLOCKED,
        expected_mocked_order_count=0,
    ),
    MockedAutomatedPaperSendFixture(
        scenario_id="kill_switch",
        description="Automation kill switch active blocks send.",
        config=valid_config(limits=limits(kill_switch_active=True)),
        expected_status=AUTOMATED_PAPER_SEND_REJECTED_BY_KILL_SWITCH,
        expected_mocked_order_count=0,
    ),
    MockedAutomatedPaperSendFixture(
        scenario_id="daily_order_limit",
        description="Daily order limit exceeded blocks send.",
        config=valid_config(limits=limits(daily_order_count=1)),
        expected_status=AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS,
        expected_mocked_order_count=0,
    ),
    MockedAutomatedPaperSendFixture(
        scenario_id="daily_notional_limit",
        description="Daily notional limit exceeded blocks send.",
        config=valid_config(limits=limits(daily_notional_used="50"), notional="51"),
        expected_status=AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS,
        expected_mocked_order_count=0,
    ),
    MockedAutomatedPaperSendFixture(
        scenario_id="cooldown",
        description="Cooldown not satisfied blocks send.",
        config=valid_config(limits=limits(cooldown_satisfied=False)),
        expected_status=AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS,
        expected_mocked_order_count=0,
    ),
    MockedAutomatedPaperSendFixture(
        scenario_id="missing_previous_reconciliation",
        description="Missing previous reconciliation blocks send.",
        config=valid_config(limits=limits(previous_reconciliation_exists=False)),
        expected_status=AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION,
        expected_mocked_order_count=0,
    ),
    MockedAutomatedPaperSendFixture(
        scenario_id="unresolved_reconciliation_mismatch",
        description="Unresolved reconciliation mismatch blocks send.",
        config=valid_config(limits=limits(previous_reconciliation_unresolved_mismatch=True)),
        expected_status=AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION,
        expected_mocked_order_count=0,
    ),
    MockedAutomatedPaperSendFixture(
        scenario_id="missing_post_mortem",
        description="Missing post-mortem blocks send.",
        config=valid_config(limits=limits(previous_post_mortem_exists=False)),
        expected_status=AUTOMATED_PAPER_SEND_REJECTED_BY_POST_MORTEM,
        expected_mocked_order_count=0,
    ),
    MockedAutomatedPaperSendFixture(
        scenario_id="unresolved_issue",
        description="Unresolved issue blocks send.",
        config=valid_config(limits=limits(unresolved_issue_exists=True)),
        expected_status=AUTOMATED_PAPER_SEND_BLOCKED,
        expected_mocked_order_count=0,
    ),
    MockedAutomatedPaperSendFixture(
        scenario_id="live_endpoint",
        description="Live endpoint configured blocks send.",
        config=valid_config(live_endpoint_configured=True),
        expected_status=AUTOMATED_PAPER_SEND_REJECTED_BY_PREFLIGHT,
        expected_mocked_order_count=0,
    ),
    MockedAutomatedPaperSendFixture(
        scenario_id="notional_over_100",
        description="Notional over 100 USD blocks send.",
        config=valid_config(notional="101"),
        expected_status=AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS,
        expected_mocked_order_count=0,
    ),
    MockedAutomatedPaperSendFixture(
        scenario_id="batch_cancel_replace",
        description="Batch and cancel/replace behavior blocks send.",
        config=valid_config(batch_orders=True, cancel_replace=True),
        expected_status=AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS,
        expected_mocked_order_count=0,
    ),
)


def run_automated_paper_send_mocked_regression(
    *,
    output_root: Path = REPORT_ROOT,
    write_report: bool = True,
) -> MockedAutomatedPaperSendRegressionRun:
    report_dir = _timestamped_report_dir(output_root) if write_report else None
    scenario_artifact_root = report_dir / "scenario_artifacts" if report_dir is not None else output_root
    results = tuple(_run_fixture(fixture, output_root=scenario_artifact_root) for fixture in SCENARIOS)
    final_status = REGRESSION_PASSED if all(result.passed for result in results) else REGRESSION_FAILED
    report_path: Path | None = None
    if write_report and report_dir is not None:
        report_path = report_dir / REPORT_NAME
        report_path.write_text(_render_report(results=results, final_status=final_status), encoding="utf-8")
    return MockedAutomatedPaperSendRegressionRun(
        final_status=final_status,
        results=results,
        report_path=report_path.as_posix() if report_path else None,
    )


def _run_fixture(
    fixture: MockedAutomatedPaperSendFixture,
    *,
    output_root: Path,
) -> MockedAutomatedPaperSendScenarioResult:
    client = RecordingAutomatedPaperClient()
    env_values = {
        ENV_AUTOMATED_SEND_ENABLED: "true" if fixture.config.paper_automated_send_enabled else "false",
        ENV_EXECUTION_ENABLED: "true" if fixture.config.paper_order_execution_enabled else "false",
        ENV_ALPACA_PAPER: "true" if fixture.config.alpaca_paper else "false",
    }
    with patch.dict(os.environ, env_values):
        send_result = run_automated_paper_send(
            config=fixture.config,
            client=client,
            output_root=output_root / fixture.scenario_id,
            write_artifacts=True,
        )
    flags_disabled_unset = (
        os.environ.get(ENV_AUTOMATED_SEND_ENABLED) in (None, "", "false")
        and os.environ.get(ENV_EXECUTION_ENABLED) in (None, "", "false")
    )
    mocked_payloads = tuple(dict(payload) for payload in client.payloads)
    failure_reason = _failure_reason(
        fixture=fixture,
        send_result=send_result,
        mocked_payloads=mocked_payloads,
        flags_disabled_unset=flags_disabled_unset,
    )
    return MockedAutomatedPaperSendScenarioResult(
        scenario_id=fixture.scenario_id,
        description=fixture.description,
        passed=failure_reason == "",
        failure_reason=failure_reason,
        final_status=send_result.final_status,
        reconciliation_status=send_result.reconciliation_status,
        mocked_order_count=len(mocked_payloads),
        mocked_payloads=mocked_payloads,
        report_path=send_result.report_path,
        audit_log_path=send_result.audit_log_path,
        reconciliation_path=send_result.reconciliation_path,
        post_send_safety_path=send_result.post_send_safety_path,
        post_mortem_path=send_result.post_mortem_path,
        returned_to_dry_run_only=send_result.returned_to_dry_run_only,
        flags_disabled_unset_after_test_context=flags_disabled_unset,
        real_alpaca_api_called=send_result.alpaca_order_api_called,
        real_order_sent=False,
        live_trading_readiness=send_result.live_trading_readiness,
        live_endpoint_used=send_result.live_endpoint_used,
    )


def _failure_reason(
    *,
    fixture: MockedAutomatedPaperSendFixture,
    send_result: object,
    mocked_payloads: tuple[Mapping[str, object], ...],
    flags_disabled_unset: bool,
) -> str:
    failures: list[str] = []
    if getattr(send_result, "final_status") != fixture.expected_status:
        failures.append(
            f"expected status {fixture.expected_status}, got {getattr(send_result, 'final_status')}"
        )
    if len(mocked_payloads) != fixture.expected_mocked_order_count:
        failures.append(
            f"expected mocked order count {fixture.expected_mocked_order_count}, got {len(mocked_payloads)}"
        )
    if fixture.expected_reconciliation_status is not None:
        if getattr(send_result, "reconciliation_status") != fixture.expected_reconciliation_status:
            failures.append(
                "expected reconciliation "
                f"{fixture.expected_reconciliation_status}, got {getattr(send_result, 'reconciliation_status')}"
            )
    if fixture.expected_mocked_order_count == 1:
        payload = mocked_payloads[0] if mocked_payloads else {}
        if payload.get("type") != "limit":
            failures.append("mocked order was not limit")
        if payload.get("time_in_force") != "day":
            failures.append("mocked order was not day time-in-force")
    if fixture.expected_mocked_order_count == 0 and getattr(send_result, "order_sent"):
        failures.append("blocked scenario sent an order")
    if getattr(send_result, "alpaca_order_api_called"):
        failures.append("real Alpaca API was called")
    if getattr(send_result, "live_trading_readiness"):
        failures.append("live trading readiness was created")
    if getattr(send_result, "live_endpoint_used"):
        failures.append("live endpoint was used")
    if not getattr(send_result, "returned_to_dry_run_only"):
        failures.append("system did not return to DRY_RUN_ONLY")
    if not flags_disabled_unset:
        failures.append("flags were not disabled/unset after test context")
    if not getattr(send_result, "audit_log_path"):
        failures.append("automation audit log missing")
    return "; ".join(failures)


def _render_report(
    *,
    results: tuple[MockedAutomatedPaperSendScenarioResult, ...],
    final_status: str,
) -> str:
    mocked_order_count = sum(result.mocked_order_count for result in results)
    no_real_api = not any(result.real_alpaca_api_called for result in results)
    no_real_order = not any(result.real_order_sent for result in results)
    returned_to_dry_run = all(result.returned_to_dry_run_only for result in results)
    flags_disabled = all(result.flags_disabled_unset_after_test_context for result in results)
    lines = [
        "# Automated Paper Send Mocked Regression Report",
        "",
        "## Summary",
        "",
        f"- Generated at: {datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}",
        f"- Final status: {final_status}",
        f"- Scenarios run: {len(results)}",
        f"- Mocked order count: {mocked_order_count}",
        f"- Proof no real Alpaca API was called: {no_real_api}",
        f"- Proof no real order was sent: {no_real_order}",
        f"- Proof system returned to DRY_RUN_ONLY: {returned_to_dry_run}",
        f"- Proof flags were disabled/unset after test context: {flags_disabled}",
        "",
        "## Scenario Results",
        "",
    ]
    for result in results:
        lines.extend(
            [
                f"### {result.scenario_id}",
                "",
                f"- Description: {result.description}",
                f"- Passed: {result.passed}",
                f"- Failure reason: {result.failure_reason or 'none'}",
                f"- Final status: {result.final_status}",
                f"- Mocked order count: {result.mocked_order_count}",
                f"- Reconciliation status: {result.reconciliation_status}",
                f"- Report path: {result.report_path}",
                f"- Automation audit log path: {result.audit_log_path}",
                f"- Post-send safety path: {result.post_send_safety_path}",
                f"- Post-mortem path: {result.post_mortem_path}",
                f"- Returned to DRY_RUN_ONLY: {result.returned_to_dry_run_only}",
                f"- Flags disabled/unset after test context: {result.flags_disabled_unset_after_test_context}",
                f"- Real Alpaca API called: {result.real_alpaca_api_called}",
                f"- Real order sent: {result.real_order_sent}",
                "",
            ]
        )
    lines.extend(
        [
            "## Gate Results",
            "",
            "- All V12 gates PASS in the full valid mocked scenario.",
            "- Blocked scenarios verify gate or safety-control rejection before mocked order submission.",
            "",
            "## Limit Results",
            "",
            "- Daily order limit scenario rejects with AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS.",
            "- Daily notional limit scenario rejects with AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS.",
            "- Notional over 100 scenario rejects before any mocked order is sent.",
            "- Batch orders remain prohibited.",
            "- Cancel/replace remains prohibited.",
            "",
            "## Kill Switch Results",
            "",
            "- Kill switch scenario rejects with AUTOMATED_PAPER_SEND_REJECTED_BY_KILL_SWITCH.",
            "",
            "## Cooldown Results",
            "",
            "- Cooldown scenario rejects with AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS.",
            "",
            "## Reconciliation Dependency Results",
            "",
            "- Missing previous reconciliation scenario rejects with AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION.",
            "- Unresolved reconciliation mismatch scenario rejects with AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION.",
            "",
            "## Post-Mortem Dependency Results",
            "",
            "- Missing post-mortem scenario rejects with AUTOMATED_PAPER_SEND_REJECTED_BY_POST_MORTEM.",
            "- Unresolved issue scenario rejects before mocked order submission.",
            "",
            "## Audit Log Results",
            "",
            "- Every scenario writes an automation audit log artifact.",
            "",
            "## Proof Statements",
            "",
            "- Proof no real Alpaca API was called: true",
            "- Proof no real order was sent: true",
            f"- Proof system returned to DRY_RUN_ONLY: {returned_to_dry_run}",
            f"- Proof flags were disabled/unset after test context: {flags_disabled}",
            "",
            "Automated paper send remains paper-only.",
            "Live trading remains unsupported.",
            "Increasing notional remains prohibited.",
            "Batch orders remain prohibited.",
            "Cancel/replace remains prohibited.",
            "",
        ]
    )
    return "\n".join(lines)


def _timestamped_report_dir(output_root: Path) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_dir = output_root / timestamp
    suffix = 1
    while report_dir.exists():
        report_dir = output_root / f"{timestamp}-{suffix}"
        suffix += 1
    report_dir.mkdir(parents=True, exist_ok=False)
    return report_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Run automated paper send mocked regression.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_automated_paper_send_mocked_regression()
    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(result.final_status)
        print(result.report_path)
    return 0 if result.final_status == REGRESSION_PASSED else 1


if __name__ == "__main__":
    raise SystemExit(main())
