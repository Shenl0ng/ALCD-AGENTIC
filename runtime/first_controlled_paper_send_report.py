from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping


MISSING_RUN_OUTPUT = "MISSING_RUN_OUTPUT"
REPORT_READY = "REPORT_READY"
REPORT_BLOCKED = "REPORT_BLOCKED"

REPORT_ROOT = Path("reports/first_controlled_paper_send")
TEMPLATE_PATH = Path("docs/FIRST_CONTROLLED_PAPER_SEND_REPORT_TEMPLATE.md")
FINAL_REPORT_NAME = "FIRST_CONTROLLED_PAPER_SEND_REPORT.md"
EMPTY_REPORT_NAME = "FIRST_CONTROLLED_PAPER_SEND_REPORT_EMPTY.md"
STATUS_NAME = "artifact_status.json"

REQUIRED_ARTIFACTS = {
    "pre_send_checklist": "pre_send_checklist.json",
    "proposal_validation": "proposal_validation.json",
    "risk_evaluation": "risk_evaluation.json",
    "human_approval": "human_approval.json",
    "manual_execution_confirmation": "manual_execution_confirmation.json",
    "journal_commit": "journal_commit.json",
    "preflight": "preflight.json",
    "paper_send_result": "paper_send_result.json",
    "reconciliation": "reconciliation.json",
    "post_send_safety": "post_send_safety.json",
}


@dataclass(frozen=True)
class ReportGenerationResult:
    status: str
    report_dir: str
    missing_artifacts: tuple[str, ...]
    report_path: str | None
    status_path: str
    missing_fields: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "report_dir": self.report_dir,
            "missing_artifacts": list(self.missing_artifacts),
            "missing_fields": list(self.missing_fields),
            "report_path": self.report_path,
            "status_path": self.status_path,
        }


def create_timestamped_report_dir(root: Path = REPORT_ROOT) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_dir = root / timestamp
    suffix = 1
    while report_dir.exists():
        report_dir = root / f"{timestamp}-{suffix}"
        suffix += 1
    report_dir.mkdir(parents=True, exist_ok=False)
    return report_dir


def generate_first_controlled_paper_send_report(
    report_dir: Path,
    *,
    template_path: Path = TEMPLATE_PATH,
) -> ReportGenerationResult:
    report_dir.mkdir(parents=True, exist_ok=True)
    missing = missing_artifacts(report_dir)
    status_path = report_dir / STATUS_NAME

    if len(missing) == len(REQUIRED_ARTIFACTS):
        empty_path = report_dir / EMPTY_REPORT_NAME
        empty_path.write_text(_template_text(template_path), encoding="utf-8")
        result = ReportGenerationResult(
            status=MISSING_RUN_OUTPUT,
            report_dir=report_dir.as_posix(),
            missing_artifacts=missing,
            missing_fields=(),
            report_path=None,
            status_path=status_path.as_posix(),
        )
        _write_status(status_path, result)
        return result

    if missing:
        result = ReportGenerationResult(
            status=REPORT_BLOCKED,
            report_dir=report_dir.as_posix(),
            missing_artifacts=missing,
            missing_fields=(),
            report_path=None,
            status_path=status_path.as_posix(),
        )
        _write_status(status_path, result)
        return result

    artifacts = _read_artifacts(report_dir)
    missing_fields = _missing_required_fields(artifacts)
    if missing_fields:
        result = ReportGenerationResult(
            status=REPORT_BLOCKED,
            report_dir=report_dir.as_posix(),
            missing_artifacts=(),
            missing_fields=missing_fields,
            report_path=None,
            status_path=status_path.as_posix(),
        )
        _write_status(status_path, result)
        return result

    report_path = report_dir / FINAL_REPORT_NAME
    report_path.write_text(_render_report(artifacts), encoding="utf-8")
    result = ReportGenerationResult(
        status=REPORT_READY,
        report_dir=report_dir.as_posix(),
        missing_artifacts=(),
        missing_fields=(),
        report_path=report_path.as_posix(),
        status_path=status_path.as_posix(),
    )
    _write_status(status_path, result)
    return result


def missing_artifacts(report_dir: Path) -> tuple[str, ...]:
    return tuple(
        filename for filename in REQUIRED_ARTIFACTS.values() if not (report_dir / filename).exists()
    )


def _read_artifacts(report_dir: Path) -> dict[str, Mapping[str, Any]]:
    artifacts: dict[str, Mapping[str, Any]] = {}
    for key, filename in REQUIRED_ARTIFACTS.items():
        decoded = json.loads((report_dir / filename).read_text(encoding="utf-8"))
        if not isinstance(decoded, Mapping):
            raise ValueError(f"{filename} must contain a JSON object")
        artifacts[key] = decoded
    return artifacts


def _missing_required_fields(artifacts: Mapping[str, Mapping[str, Any]]) -> tuple[str, ...]:
    required_paths = (
        "reconciliation.report.final_reconciliation_status",
    )
    missing: list[str] = []
    for path in required_paths:
        if _path_value(artifacts, path) in (None, "", "missing"):
            missing.append(path)
    return tuple(missing)


def _path_value(source: Mapping[str, Any], path: str) -> Any:
    current: Any = source
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def _render_report(artifacts: Mapping[str, Mapping[str, Any]]) -> str:
    pre_send = artifacts["pre_send_checklist"]
    proposal = artifacts["proposal_validation"]
    risk = artifacts["risk_evaluation"]
    approval = artifacts["human_approval"]
    manual = artifacts["manual_execution_confirmation"]
    journal = artifacts["journal_commit"]
    preflight = artifacts["preflight"]
    send = artifacts["paper_send_result"]
    reconciliation = artifacts["reconciliation"]
    safety = artifacts["post_send_safety"]

    execution_result = _mapping(send.get("execution_result"))
    report = _mapping(reconciliation.get("report"))
    post_send_journal = _mapping(send.get("journal_entry"))
    reconciliation_journal = _mapping(reconciliation.get("journal_entry"))

    return f"""# First Controlled Paper Send Report

## Date
{_value(pre_send, "date")}

## Environment
- Mode: {_value(pre_send, "mode")}
- Paper execution enabled: {_value(pre_send, "paper_execution_enabled")}
- Alpaca account mode: {_value(pre_send, "alpaca_account_mode")}
- Live endpoint rejected: {_value(pre_send, "live_endpoint_rejected")}

## Proposal
- Proposal ID: {_first_value(proposal, "proposal_id", "paper_order_request_id")}
- Symbol: {_first_value(proposal, "symbol", "request.symbol")}
- Side: {_first_value(proposal, "side", "direction")}
- Notional: {_first_value(proposal, "notional", "max_notional")}
- Order type: {_first_value(proposal, "order_type")}
- Time in force: {_first_value(proposal, "time_in_force")}

## Gates
- Proposal validation: {_first_value(proposal, "status", "validation_status")}
- Risk approval: {_first_value(risk, "decision", "risk_approval")}
- Human approval: {_first_value(approval, "approval_state", "human_approval")}
- Manual execution confirmation: {_first_value(manual, "confirmation_state", "manual_execution_confirmation")}
- Journal commit: {_first_value(journal, "event_type", "journal_commit_reference")}
- Preflight: {_first_value(preflight, "final_decision", "preflight_status")}

## Send Result
- Final status: {_first_value(send, "status", "final_status")}
- Alpaca order ID: {_value(execution_result, "alpaca_order_id", missing="not returned in artifact")}
- Broker status: {_value(execution_result, "alpaca_order_status", missing="not returned in artifact")}

## Reconciliation
- Reconciliation status: {_value(report, "final_reconciliation_status")}
- Mismatches: {_list_value(report.get("mismatch_reasons"))}
- Account state checked: {_value(safety, "account_state_checked")}
- Position state checked: {_value(safety, "position_state_checked")}

## Journal
- Pre-send journal entry: {_first_value(journal, "event_type", "journal_entry_id")}
- Post-send journal entry: {_first_value(post_send_journal, "event_type", "journal_entry_id")}
- Reconciliation journal entry: {_first_value(reconciliation_journal, "event_type", "journal_entry_id")}

## Safety
- Follow-up orders created: {_value(safety, "follow_up_orders_created")}
- Cancel/replace used: {_value(safety, "cancel_replace_used")}
- Live trading touched: {_value(safety, "live_trading_touched")}
- Execution flag disabled after test: {_value(safety, "execution_flag_disabled_after_test")}
- Returned to DRY_RUN_ONLY: {_value(safety, "returned_to_dry_run_only")}

## Lessons
- What worked: {_value(safety, "what_worked")}
- What failed: {_value(safety, "what_failed")}
- What must be fixed before next paper send: {_value(safety, "must_fix_before_next_send")}
"""


def _template_text(template_path: Path) -> str:
    return template_path.read_text(encoding="utf-8")


def _write_status(path: Path, result: ReportGenerationResult) -> None:
    path.write_text(json.dumps(result.as_dict(), indent=2), encoding="utf-8")


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _first_value(source: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = source.get(key)
        if value not in (None, ""):
            return str(value)
    return "missing from artifact"


def _value(source: Mapping[str, Any], key: str, *, missing: str = "missing from artifact") -> str:
    value = source.get(key)
    if value in (None, ""):
        return missing
    return str(value)


def _list_value(value: object) -> str:
    if isinstance(value, list):
        return "none" if not value else "; ".join(str(item) for item in value)
    if isinstance(value, tuple):
        return "none" if not value else "; ".join(str(item) for item in value)
    if value in (None, ""):
        return "missing from artifact"
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate first controlled paper send report.")
    parser.add_argument("--report-dir", type=Path)
    args = parser.parse_args()

    report_dir = args.report_dir or create_timestamped_report_dir()
    result = generate_first_controlled_paper_send_report(report_dir)
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.status == REPORT_READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
