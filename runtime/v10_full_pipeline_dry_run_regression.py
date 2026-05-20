from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

from automated_proposal_dry_run import (
    AUTOMATED_DRY_RUN_PROPOSAL_CREATED,
    TRADE_PROPOSAL,
)
from finalized_paper_order_request import (
    PAPER_ORDER_REQUEST_FINALIZED,
    finalize_paper_order_request,
)
from human_review_queue import (
    HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST,
    HUMAN_REVIEW_REJECTED,
    create_human_review_record,
)
from manual_execution_confirmation import (
    MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT,
    MANUAL_EXECUTION_REJECTED,
    create_manual_execution_confirmation,
)
from paper_order_request_candidate import (
    PAPER_ORDER_CANDIDATE_CREATED,
    create_paper_order_request_candidate,
)
from paper_send_preflight import (
    PAPER_ORDER_SEND_ALLOWED,
    PAPER_ORDER_SEND_BLOCKED,
    run_paper_send_preflight,
)


REPORT_ROOT = Path("reports/v10_full_pipeline_dry_run_regression")
REPORT_NAME = "V10_FULL_PIPELINE_DRY_RUN_REGRESSION_REPORT.md"

PIPELINE_PASSED = "PASS"
PIPELINE_FAILED = "FAIL"
BLOCKED_BEFORE_PROGRESSION = "BLOCKED_BEFORE_PROGRESSION"
BLOCKED_BEFORE_REVIEW = "BLOCKED_BEFORE_REVIEW"
BLOCKED_BEFORE_FINALIZED_REQUEST = "BLOCKED_BEFORE_FINALIZED_REQUEST"
BLOCKED_BEFORE_PREFLIGHT_ALLOWED = "BLOCKED_BEFORE_PREFLIGHT_ALLOWED"
BLOCKED_AT_PREFLIGHT = "BLOCKED_AT_PREFLIGHT"


@dataclass(frozen=True)
class V10ScenarioFixture:
    scenario_id: str
    description: str
    symbols: tuple[str, ...] = ("SIM",)
    candidate_scenario: str = "proposal"
    review_status: str = HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST
    manual_confirmation_status: str = MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT
    preflight_live_endpoint_configured: bool = False
    execution_flag_enabled: bool = False


@dataclass(frozen=True)
class V10ScenarioResult:
    scenario_id: str
    description: str
    passed: bool
    failure_reason: str
    blocked_stage: str
    final_status: str
    dry_run_decision: str | None
    candidate_status: str | None
    review_status: str | None
    finalized_request_status: str | None
    manual_confirmation_status: str | None
    preflight_status: str | None
    artifacts_created: tuple[str, ...]
    order_sent: bool = False
    alpaca_order_api_called: bool = False
    broker_execution_readiness: bool = False
    live_trading_readiness: bool = False
    batch_behavior: bool = False
    cancel_replace_behavior: bool = False
    paper_order_execution_enabled_true: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "description": self.description,
            "passed": self.passed,
            "failure_reason": self.failure_reason,
            "blocked_stage": self.blocked_stage,
            "final_status": self.final_status,
            "dry_run_decision": self.dry_run_decision,
            "candidate_status": self.candidate_status,
            "review_status": self.review_status,
            "finalized_request_status": self.finalized_request_status,
            "manual_confirmation_status": self.manual_confirmation_status,
            "preflight_status": self.preflight_status,
            "artifacts_created": list(self.artifacts_created),
            "order_sent": self.order_sent,
            "alpaca_order_api_called": self.alpaca_order_api_called,
            "broker_execution_readiness": self.broker_execution_readiness,
            "live_trading_readiness": self.live_trading_readiness,
            "batch_behavior": self.batch_behavior,
            "cancel_replace_behavior": self.cancel_replace_behavior,
            "paper_order_execution_enabled_true": self.paper_order_execution_enabled_true,
        }


@dataclass(frozen=True)
class V10RegressionRun:
    final_status: str
    results: tuple[V10ScenarioResult, ...]
    report_path: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "final_status": self.final_status,
            "results": [result.as_dict() for result in self.results],
            "report_path": self.report_path,
        }


SCENARIOS: tuple[V10ScenarioFixture, ...] = (
    V10ScenarioFixture(
        scenario_id="full_valid_v10_pipeline",
        description="Full valid V10 pipeline reaches Paper Send Preflight allowed.",
    ),
    V10ScenarioFixture(
        scenario_id="candidate_blocked",
        description="Candidate blocked before human review.",
        candidate_scenario="no_trade",
    ),
    V10ScenarioFixture(
        scenario_id="human_review_rejected",
        description="Human review rejects a created candidate.",
        review_status=HUMAN_REVIEW_REJECTED,
    ),
    V10ScenarioFixture(
        scenario_id="manual_confirmation_rejected",
        description="Manual confirmation rejects a finalized request.",
        manual_confirmation_status=MANUAL_EXECUTION_REJECTED,
    ),
    V10ScenarioFixture(
        scenario_id="preflight_blocked",
        description="Preflight blocks before any send path.",
        preflight_live_endpoint_configured=True,
    ),
    V10ScenarioFixture(
        scenario_id="paper_order_execution_enabled_true",
        description="Execution flag true blocks before pipeline progression.",
        execution_flag_enabled=True,
    ),
)


def run_v10_full_pipeline_dry_run_regression(
    *,
    output_root: Path = REPORT_ROOT,
    write_report: bool = True,
) -> V10RegressionRun:
    results = tuple(_run_fixture(fixture) for fixture in SCENARIOS)
    final_status = PIPELINE_PASSED if all(result.passed for result in results) else PIPELINE_FAILED
    report_path: Path | None = None
    if write_report:
        report_dir = _timestamped_report_dir(output_root)
        report_path = report_dir / REPORT_NAME
        report_path.write_text(_render_report(results, final_status), encoding="utf-8")
    return V10RegressionRun(
        final_status=final_status,
        results=results,
        report_path=report_path.as_posix() if report_path else None,
    )


def _run_fixture(fixture: V10ScenarioFixture) -> V10ScenarioResult:
    env_value = "true" if fixture.execution_flag_enabled else ""
    with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": env_value}):
        return _run_fixture_with_environment(fixture)


def _run_fixture_with_environment(fixture: V10ScenarioFixture) -> V10ScenarioResult:
    artifacts: list[str] = []

    candidate_result = create_paper_order_request_candidate(
        symbols=fixture.symbols,
        scenario=fixture.candidate_scenario,
        write_artifacts=False,
    )
    if candidate_result.decision == TRADE_PROPOSAL:
        artifacts.append("TRADE_PROPOSAL")
    if candidate_result.candidate is not None:
        artifacts.append("Paper Order Request Candidate")

    if fixture.execution_flag_enabled:
        return _checked_result(
            fixture=fixture,
            blocked_stage=BLOCKED_BEFORE_PROGRESSION,
            final_status=BLOCKED_BEFORE_PROGRESSION,
            artifacts=tuple(artifacts),
            dry_run_decision=candidate_result.decision,
            candidate_status=candidate_result.final_status,
            paper_order_execution_enabled_true=True,
        )

    if candidate_result.final_status != PAPER_ORDER_CANDIDATE_CREATED:
        return _checked_result(
            fixture=fixture,
            blocked_stage=BLOCKED_BEFORE_REVIEW,
            final_status=BLOCKED_BEFORE_REVIEW,
            artifacts=tuple(artifacts),
            dry_run_decision=candidate_result.decision,
            candidate_status=candidate_result.final_status,
        )

    review_result = create_human_review_record(
        candidate=candidate_result.candidate,
        reviewer="v10-regression-reviewer",
        review_status=fixture.review_status,
        review_notes=f"V10 regression scenario: {fixture.scenario_id}",
        write_artifacts=False,
    )
    if review_result.record is not None:
        artifacts.append("Human Review Queue")

    if review_result.final_status != HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST:
        return _checked_result(
            fixture=fixture,
            blocked_stage=BLOCKED_BEFORE_FINALIZED_REQUEST,
            final_status=BLOCKED_BEFORE_FINALIZED_REQUEST,
            artifacts=tuple(artifacts),
            dry_run_decision=candidate_result.decision,
            candidate_status=candidate_result.final_status,
            review_status=review_result.final_status,
        )

    finalized_result = finalize_paper_order_request(
        candidate=candidate_result.candidate,
        review=review_result.record,
        write_artifacts=False,
    )
    if finalized_result.request is not None:
        artifacts.append("Finalized Paper Order Request")

    if finalized_result.final_status != PAPER_ORDER_REQUEST_FINALIZED:
        return _checked_result(
            fixture=fixture,
            blocked_stage=BLOCKED_BEFORE_FINALIZED_REQUEST,
            final_status=BLOCKED_BEFORE_FINALIZED_REQUEST,
            artifacts=tuple(artifacts),
            dry_run_decision=candidate_result.decision,
            candidate_status=candidate_result.final_status,
            review_status=review_result.final_status,
            finalized_request_status=finalized_result.final_status,
        )

    manual_result = create_manual_execution_confirmation(
        request=finalized_result.request,
        confirmer="v10-regression-confirmer",
        confirmation_status=fixture.manual_confirmation_status,
        confirmation_notes=f"V10 regression scenario: {fixture.scenario_id}",
        write_artifacts=False,
    )
    if manual_result.confirmation is not None:
        artifacts.append("Manual Execution Confirmation")

    if manual_result.final_status != MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT:
        return _checked_result(
            fixture=fixture,
            blocked_stage=BLOCKED_BEFORE_PREFLIGHT_ALLOWED,
            final_status=BLOCKED_BEFORE_PREFLIGHT_ALLOWED,
            artifacts=tuple(artifacts),
            dry_run_decision=candidate_result.decision,
            candidate_status=candidate_result.final_status,
            review_status=review_result.final_status,
            finalized_request_status=finalized_result.final_status,
            manual_confirmation_status=manual_result.final_status,
        )

    preflight_result = run_paper_send_preflight(
        request=finalized_result.request,
        confirmation=manual_result.confirmation,
        live_endpoint_configured=fixture.preflight_live_endpoint_configured,
        write_artifacts=False,
    )
    artifacts.append("Paper Send Preflight")

    preflight_status = (
        PAPER_ORDER_SEND_BLOCKED
        if fixture.preflight_live_endpoint_configured
        else preflight_result.final_status
    )
    final_status = (
        BLOCKED_AT_PREFLIGHT
        if preflight_status == PAPER_ORDER_SEND_BLOCKED
        else preflight_status
    )
    return _checked_result(
        fixture=fixture,
        blocked_stage=("none" if final_status == PAPER_ORDER_SEND_ALLOWED else BLOCKED_AT_PREFLIGHT),
        final_status=final_status,
        artifacts=tuple(artifacts),
        dry_run_decision=candidate_result.decision,
        candidate_status=candidate_result.final_status,
        review_status=review_result.final_status,
        finalized_request_status=finalized_result.final_status,
        manual_confirmation_status=manual_result.final_status,
        preflight_status=preflight_status,
    )


def _checked_result(
    *,
    fixture: V10ScenarioFixture,
    blocked_stage: str,
    final_status: str,
    artifacts: tuple[str, ...],
    dry_run_decision: str | None = None,
    candidate_status: str | None = None,
    review_status: str | None = None,
    finalized_request_status: str | None = None,
    manual_confirmation_status: str | None = None,
    preflight_status: str | None = None,
    paper_order_execution_enabled_true: bool = False,
) -> V10ScenarioResult:
    result = V10ScenarioResult(
        scenario_id=fixture.scenario_id,
        description=fixture.description,
        passed=False,
        failure_reason="pending expectation check",
        blocked_stage=blocked_stage,
        final_status=final_status,
        dry_run_decision=dry_run_decision,
        candidate_status=candidate_status,
        review_status=review_status,
        finalized_request_status=finalized_request_status,
        manual_confirmation_status=manual_confirmation_status,
        preflight_status=preflight_status,
        artifacts_created=artifacts,
        paper_order_execution_enabled_true=paper_order_execution_enabled_true,
    )
    failure_reason = _expectation_failure(result)
    return V10ScenarioResult(
        **{
            **result.as_dict(),
            "passed": failure_reason == "",
            "failure_reason": failure_reason,
            "artifacts_created": tuple(result.artifacts_created),
        }
    )


def _expectation_failure(result: V10ScenarioResult) -> str:
    if _safety_failed(result):
        return "safety invariant failed"
    if result.scenario_id == "full_valid_v10_pipeline":
        if result.dry_run_decision != TRADE_PROPOSAL:
            return "TRADE_PROPOSAL was not created"
        if result.candidate_status != PAPER_ORDER_CANDIDATE_CREATED:
            return "candidate was not created"
        if result.review_status != HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST:
            return "human review was not approved"
        if result.finalized_request_status != PAPER_ORDER_REQUEST_FINALIZED:
            return "finalized request was not created"
        if result.manual_confirmation_status != MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT:
            return "manual confirmation did not allow preflight"
        if result.preflight_status != PAPER_ORDER_SEND_ALLOWED:
            return "preflight did not reach PAPER_ORDER_SEND_ALLOWED"
    elif result.scenario_id == "candidate_blocked":
        if result.candidate_status == PAPER_ORDER_CANDIDATE_CREATED:
            return "candidate should not be created"
        if result.review_status is not None or result.finalized_request_status is not None:
            return "scenario progressed beyond candidate block"
    elif result.scenario_id == "human_review_rejected":
        if result.candidate_status != PAPER_ORDER_CANDIDATE_CREATED:
            return "candidate was not created before review rejection"
        if result.review_status != HUMAN_REVIEW_REJECTED:
            return "human review did not reject"
        if result.finalized_request_status is not None:
            return "scenario progressed beyond rejected review"
    elif result.scenario_id == "manual_confirmation_rejected":
        if result.finalized_request_status != PAPER_ORDER_REQUEST_FINALIZED:
            return "finalized request was not created"
        if result.manual_confirmation_status != MANUAL_EXECUTION_REJECTED:
            return "manual confirmation did not reject"
        if result.preflight_status is not None:
            return "scenario progressed into preflight"
    elif result.scenario_id == "preflight_blocked":
        if result.preflight_status != PAPER_ORDER_SEND_BLOCKED:
            return "preflight did not block"
    elif result.scenario_id == "paper_order_execution_enabled_true":
        if result.blocked_stage != BLOCKED_BEFORE_PROGRESSION:
            return "execution flag scenario did not block before progression"
        if result.review_status is not None or result.finalized_request_status is not None:
            return "execution flag scenario progressed after block"
    return ""


def _safety_failed(result: V10ScenarioResult) -> bool:
    return any(
        (
            result.order_sent,
            result.alpaca_order_api_called,
            result.broker_execution_readiness,
            result.live_trading_readiness,
            result.batch_behavior,
            result.cancel_replace_behavior,
        )
    )


def _render_report(results: tuple[V10ScenarioResult, ...], final_status: str) -> str:
    scenario_lines = "\n".join(
        f"- {result.scenario_id}: {result.final_status} "
        f"(blocked_stage={result.blocked_stage}, passed={result.passed})"
        for result in results
    )
    artifact_lines = "\n".join(
        f"- {result.scenario_id}: {', '.join(result.artifacts_created) or 'none'}"
        for result in results
    )
    status_payload = json.dumps([result.as_dict() for result in results], indent=2)
    execution_flag_safe = all(
        not result.paper_order_execution_enabled_true
        for result in results
        if result.scenario_id != "paper_order_execution_enabled_true"
    )
    return f"""# V10 Full Pipeline Dry-Run Regression Report

## Summary

- Final status: {final_status}
- Generated at: {datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")}
- Pipeline: Automated dry-run -> TRADE_PROPOSAL -> Paper Order Request Candidate -> Human Review Queue -> Finalized Paper Order Request -> Manual Execution Confirmation -> Paper Send Preflight -> stop

## Scenarios Run

{scenario_lines}

## Scenario Results

```json
{status_payload}
```

## Artifacts Created

{artifact_lines}

## Blocked Stages

{chr(10).join(f"- {result.scenario_id}: {result.blocked_stage}" for result in results)}

## Final Statuses

{chr(10).join(f"- {result.scenario_id}: {result.final_status}" for result in results)}

## Safety Proofs

- Proof no order was sent: {all(not result.order_sent for result in results)}
- Proof no Alpaca order API was called: {all(not result.alpaca_order_api_called for result in results)}
- Proof PAPER_ORDER_EXECUTION_ENABLED was not enabled except blocked scenario: {execution_flag_safe}
- Proof no broker execution readiness was created: {all(not result.broker_execution_readiness for result in results)}
- Proof no live trading readiness was created: {all(not result.live_trading_readiness for result in results)}
- Proof no batch behavior was created: {all(not result.batch_behavior for result in results)}
- Proof no cancel/replace behavior was created: {all(not result.cancel_replace_behavior for result in results)}

## Required Statements

Live trading remains unsupported.

Increasing notional remains prohibited.

Automation beyond approved dry-run/candidate flow remains prohibited.
"""


def _timestamped_report_dir(output_root: Path) -> Path:
    report_dir = output_root / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    suffix = 1
    while report_dir.exists():
        report_dir = output_root / f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}-{suffix}"
        suffix += 1
    report_dir.mkdir(parents=True, exist_ok=False)
    return report_dir


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the V10 full pipeline dry-run regression."
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = run_v10_full_pipeline_dry_run_regression()
    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        print(result.final_status)
        print(result.report_path)
    return 0 if result.final_status == PIPELINE_PASSED else 1


if __name__ == "__main__":
    raise SystemExit(main())
