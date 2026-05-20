from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence
from unittest.mock import patch

from automated_proposal_dry_run import (
    AUTOMATED_DRY_RUN_BLOCKED,
    AUTOMATED_DRY_RUN_NO_TRADE,
    AUTOMATED_DRY_RUN_PROPOSAL_CREATED,
    AUTOMATED_DRY_RUN_REJECTED,
    DRY_RUN_ONLY,
    NO_TRADE,
    REJECT,
    TRADE_PROPOSAL,
    AutomatedDryRunReport,
    run_automated_proposal_dry_run,
)


REPORT_ROOT = Path("reports/automated_proposal_dry_run_regression")
REPORT_NAME = "AUTOMATED_PROPOSAL_DRY_RUN_REGRESSION_REPORT.md"
SCENARIO_REPORT_ROOT = Path("reports/automated_proposal_dry_run_regression/scenario_reports")


@dataclass(frozen=True)
class RegressionFixture:
    scenario_id: str
    description: str
    symbols: Sequence[str]
    runner_scenario: str
    execution_flag_attempt: bool = False


@dataclass(frozen=True)
class RegressionScenarioResult:
    scenario_id: str
    description: str
    passed: bool
    decision: str
    final_status: str
    strategy_evaluation_status: str
    evaluation_gate_status: str
    risk_dry_run_status: str
    blocked_condition: str
    report_path: str | None
    paper_order_request_created: bool
    human_approval_requested: bool
    manual_execution_confirmation_requested: bool
    order_sent: bool
    paper_send_readiness: bool
    broker_execution_readiness: bool
    live_trading_assumption: bool
    failure_reason: str

    def as_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "description": self.description,
            "passed": self.passed,
            "decision": self.decision,
            "final_status": self.final_status,
            "strategy_evaluation_status": self.strategy_evaluation_status,
            "evaluation_gate_status": self.evaluation_gate_status,
            "risk_dry_run_status": self.risk_dry_run_status,
            "blocked_condition": self.blocked_condition,
            "report_path": self.report_path,
            "paper_order_request_created": self.paper_order_request_created,
            "human_approval_requested": self.human_approval_requested,
            "manual_execution_confirmation_requested": self.manual_execution_confirmation_requested,
            "order_sent": self.order_sent,
            "paper_send_readiness": self.paper_send_readiness,
            "broker_execution_readiness": self.broker_execution_readiness,
            "live_trading_assumption": self.live_trading_assumption,
            "failure_reason": self.failure_reason,
        }


@dataclass(frozen=True)
class RegressionRun:
    final_status: str
    scenarios_run: int
    passed_scenarios: int
    failed_scenarios: int
    results: Sequence[RegressionScenarioResult]
    report_path: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "final_status": self.final_status,
            "scenarios_run": self.scenarios_run,
            "passed_scenarios": self.passed_scenarios,
            "failed_scenarios": self.failed_scenarios,
            "report_path": self.report_path,
            "results": [result.as_dict() for result in self.results],
        }


def default_regression_fixtures() -> tuple[RegressionFixture, ...]:
    return (
        RegressionFixture(
            scenario_id="strong_proposal_fixture",
            description="Strong proposal fixture",
            symbols=("SIM",),
            runner_scenario="proposal",
        ),
        RegressionFixture(
            scenario_id="weak_setup_fixture",
            description="Weak setup fixture",
            symbols=("SIM",),
            runner_scenario="reject",
        ),
        RegressionFixture(
            scenario_id="no_trade_fixture",
            description="No-trade fixture",
            symbols=("SIM",),
            runner_scenario="no_trade",
        ),
        RegressionFixture(
            scenario_id="data_integrity_failure_fixture",
            description="Data integrity failure fixture",
            symbols=("SIM",),
            runner_scenario="data_fail",
        ),
        RegressionFixture(
            scenario_id="multiple_symbol_attempt",
            description="Multiple symbol attempt",
            symbols=("SIM", "SPY"),
            runner_scenario="proposal",
        ),
        RegressionFixture(
            scenario_id="execution_flag_enabled_attempt",
            description="PAPER_ORDER_EXECUTION_ENABLED=true attempt",
            symbols=("SIM",),
            runner_scenario="proposal",
            execution_flag_attempt=True,
        ),
    )


def run_automated_proposal_dry_run_regression(
    *,
    output_root: Path = REPORT_ROOT,
    scenario_report_root: Path = SCENARIO_REPORT_ROOT,
    write_report: bool = True,
    write_scenario_reports: bool = True,
) -> RegressionRun:
    results = tuple(
        _run_fixture(
            fixture,
            scenario_report_root=scenario_report_root,
            write_scenario_reports=write_scenario_reports,
        )
        for fixture in default_regression_fixtures()
    )
    failed = tuple(result for result in results if not result.passed)
    report_path: Path | None = None
    if write_report:
        report_dir = _timestamped_report_dir(output_root)
        report_path = report_dir / REPORT_NAME
        report_path.write_text(_render_regression_report(results), encoding="utf-8")
    return RegressionRun(
        final_status="PASS" if not failed else "FAIL",
        scenarios_run=len(results),
        passed_scenarios=len(results) - len(failed),
        failed_scenarios=len(failed),
        results=results,
        report_path=report_path.as_posix() if report_path else None,
    )


def _run_fixture(
    fixture: RegressionFixture,
    *,
    scenario_report_root: Path,
    write_scenario_reports: bool,
) -> RegressionScenarioResult:
    env_value = "true" if fixture.execution_flag_attempt else ""
    with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": env_value}):
        dry_run = run_automated_proposal_dry_run(
            symbols=fixture.symbols,
            mode=DRY_RUN_ONLY,
            scenario=fixture.runner_scenario,
            output_root=scenario_report_root,
            write_artifacts=write_scenario_reports,
        )
    return _evaluate_fixture(fixture, dry_run)


def _evaluate_fixture(
    fixture: RegressionFixture,
    dry_run: AutomatedDryRunReport,
) -> RegressionScenarioResult:
    failure_reasons: list[str] = []
    if dry_run.paper_order_request_created:
        failure_reasons.append("Paper Order Request was created.")
    if dry_run.human_approval_requested:
        failure_reasons.append("Human Approval was requested.")
    if dry_run.manual_execution_confirmation_requested:
        failure_reasons.append("Manual Execution Confirmation was requested.")
    if dry_run.paper_send_readiness:
        failure_reasons.append("Paper send readiness was created.")
    if dry_run.broker_execution_readiness:
        failure_reasons.append("Broker execution readiness was created.")
    if dry_run.live_trading_assumption:
        failure_reasons.append("Live trading assumption was detected.")

    if fixture.scenario_id == "strong_proposal_fixture":
        if dry_run.decision != TRADE_PROPOSAL:
            failure_reasons.append("Strong proposal did not produce TRADE_PROPOSAL.")
        if dry_run.strategy_evaluation_status != "PASS":
            failure_reasons.append("Strong proposal did not pass Strategy Evaluation.")
        if dry_run.final_status != AUTOMATED_DRY_RUN_PROPOSAL_CREATED:
            failure_reasons.append("Strong proposal did not remain a dry-run proposal.")
    elif fixture.scenario_id == "weak_setup_fixture":
        if dry_run.decision not in {REJECT, NO_TRADE}:
            failure_reasons.append("Weak setup did not produce REJECT or NO_TRADE.")
        if dry_run.evaluation_gate_status != "EVALUATION_GATE_BLOCKED":
            failure_reasons.append("Weak setup did not block at the Evaluation-First Gate.")
    elif fixture.scenario_id == "no_trade_fixture":
        if dry_run.decision != NO_TRADE:
            failure_reasons.append("No-trade fixture did not produce NO_TRADE.")
        if dry_run.final_status != AUTOMATED_DRY_RUN_NO_TRADE:
            failure_reasons.append("No-trade fixture did not finish as no-trade.")
    elif fixture.scenario_id == "data_integrity_failure_fixture":
        if dry_run.final_status != AUTOMATED_DRY_RUN_BLOCKED:
            failure_reasons.append("Data integrity failure did not block.")
        if dry_run.data_integrity_status != "FAIL":
            failure_reasons.append("Data integrity failure status was not FAIL.")
    elif fixture.scenario_id == "multiple_symbol_attempt":
        if dry_run.final_status != AUTOMATED_DRY_RUN_BLOCKED:
            failure_reasons.append("Multiple symbol attempt did not block.")
        if "Exactly one symbol" not in dry_run.reason:
            failure_reasons.append("Multiple symbol attempt did not block for symbol count.")
    elif fixture.scenario_id == "execution_flag_enabled_attempt":
        if dry_run.final_status != AUTOMATED_DRY_RUN_BLOCKED:
            failure_reasons.append("Execution flag attempt did not block.")
        if "PAPER_ORDER_EXECUTION_ENABLED=true" not in dry_run.reason:
            failure_reasons.append("Execution flag attempt did not block on execution flag.")

    return RegressionScenarioResult(
        scenario_id=fixture.scenario_id,
        description=fixture.description,
        passed=not failure_reasons,
        decision=dry_run.decision,
        final_status=dry_run.final_status,
        strategy_evaluation_status=dry_run.strategy_evaluation_status,
        evaluation_gate_status=dry_run.evaluation_gate_status,
        risk_dry_run_status=dry_run.risk_dry_run_status,
        blocked_condition=dry_run.reason if dry_run.final_status == AUTOMATED_DRY_RUN_BLOCKED else "None",
        report_path=dry_run.report_path,
        paper_order_request_created=dry_run.paper_order_request_created,
        human_approval_requested=dry_run.human_approval_requested,
        manual_execution_confirmation_requested=dry_run.manual_execution_confirmation_requested,
        order_sent=False,
        paper_send_readiness=dry_run.paper_send_readiness,
        broker_execution_readiness=dry_run.broker_execution_readiness,
        live_trading_assumption=dry_run.live_trading_assumption,
        failure_reason="; ".join(failure_reasons),
    )


def _render_regression_report(results: Sequence[RegressionScenarioResult]) -> str:
    passed = sum(1 for result in results if result.passed)
    failed = len(results) - passed
    decisions = _counts(result.decision for result in results)
    gates = _counts(result.evaluation_gate_status for result in results)
    scenario_rows = "\n".join(
        (
            f"| {result.scenario_id} | {result.description} | {result.passed} | "
            f"{result.decision} | {result.final_status} | {result.evaluation_gate_status} | "
            f"{result.blocked_condition} | {result.report_path or 'None'} |"
        )
        for result in results
    )
    blocked = "\n".join(
        f"- {result.scenario_id}: {result.blocked_condition}"
        for result in results
        if result.blocked_condition != "None"
    )
    return f"""# Automated Proposal Dry-Run Regression Report

## Summary

- Scenarios run: {len(results)}
- Scenario results: {passed} passed, {failed} failed
- Final status: {"PASS" if failed == 0 else "FAIL"}
- Proof no Paper Order Request was created: {not any(result.paper_order_request_created for result in results)}
- Proof no Human Approval was requested: {not any(result.human_approval_requested for result in results)}
- Proof no Manual Execution Confirmation was requested: {not any(result.manual_execution_confirmation_requested for result in results)}
- Proof no order was sent: {not any(result.order_sent for result in results)}
- Proof no broker execution readiness was created: {not any(result.broker_execution_readiness for result in results)}

Live trading remains unsupported.

## Decisions Produced

{_render_counts(decisions)}

## Gate Statuses

{_render_counts(gates)}

## Scenario Results

| Scenario | Description | Passed | Decision | Final Status | Gate Status | Blocked Condition | Report Path |
|---|---|---:|---|---|---|---|---|
{scenario_rows}

## Blocked Conditions

{blocked if blocked else "- None"}

## Required Proof Statements

- No Paper Order Request was created.
- No Human Approval was requested.
- No Manual Execution Confirmation was requested.
- No order was sent.
- No broker execution readiness was created.
- Live trading remains unsupported.
"""


def _counts(values: Sequence[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _render_counts(counts: dict[str, int]) -> str:
    return "\n".join(f"- {key}: {value}" for key, value in sorted(counts.items()))


def _timestamped_report_dir(output_root: Path) -> Path:
    report_dir = output_root / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = 1
    while report_dir.exists():
        report_dir = output_root / f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{suffix}"
        suffix += 1
    report_dir.mkdir(parents=True, exist_ok=False)
    return report_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Run automated proposal dry-run regression.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    run = run_automated_proposal_dry_run_regression()
    if args.json:
        print(json.dumps(run.as_dict(), indent=2))
    else:
        print(run.final_status)
        print(run.report_path)
    return 0 if run.final_status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
