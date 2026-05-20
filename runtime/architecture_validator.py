from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REQUIRED_FILES = [
    "AGENTS.md",
    "agents/00_ORCHESTRATOR.md",
    "agents/01_DATA_INTEGRITY_AGENT.md",
    "agents/02_MARKET_CONTEXT_AGENT.md",
    "agents/03_LIQUIDITY_AGENT.md",
    "agents/04_SESSION_TIMING_AGENT.md",
    "agents/05_CONFIRMATION_AGENT.md",
    "agents/06_TRADE_PROPOSAL_AGENT.md",
    "agents/07_RISK_MANAGER_AGENT.md",
    "agents/08_EXECUTION_GATEKEEPER_AGENT.md",
    "agents/09_JOURNAL_AGENT.md",
    "agents/10_WEEKLY_REVIEW_AGENT.md",
    "agents/11_FAILURE_AUDITOR_AGENT.md",
    "strategy/00_STRATEGY_SOURCE_PDF.md",
    "strategy/01_SELECTIVE_EXECUTION_SYSTEM.md",
    "strategy/02_NO_TRADE_RULES.md",
    "governance/00_ADLC_OPERATING_MODEL.md",
    "governance/01_PROBLEM_HYPOTHESIS.md",
    "governance/02_SCOPE_AND_CONSTRAINTS.md",
    "governance/03_HUMAN_AGENT_RESPONSIBILITY.md",
    "governance/04_AUTONOMY_BOUNDARIES.md",
    "governance/05_SUCCESS_METRICS.md",
    "governance/06_FAILURE_MODES.md",
    "governance/07_EVALUATION_PROTOCOL.md",
    "governance/08_DEPLOYMENT_MONITORING.md",
    "governance/09_CHANGE_CONTROL.md",
    "governance/10_ADLC_TRACEABILITY_MATRIX.md",
    "governance/paper_trading_only.md",
    "governance/human_approval.md",
    "governance/risk_limits.md",
    "memory/market_data_status.md",
    "memory/market_context.md",
    "memory/liquidity_map.md",
    "memory/watchlist.md",
    "memory/risk_state.md",
    "memory/trade_proposals.md",
    "memory/rejected_trades.md",
    "memory/approved_paper_trades.md",
    "memory/journal.md",
    "memory/lessons_learned.md",
    "memory/failure_reports.md",
    "routines/premarket.md",
    "routines/market_open.md",
    "routines/midday.md",
    "routines/market_close.md",
    "routines/weekly_review.md",
    "evaluation/behavioral_test_cases.md",
    "evaluation/no_trade_scenarios.md",
    "evaluation/risk_violation_scenarios.md",
    "evaluation/hallucination_checks.md",
    "evaluation/paper_trading_scorecard.md",
    "design/00_RUNTIME_SYSTEM_DESIGN.md",
    "design/01_IMPLEMENTATION_PLAN.md",
]

AGENT_REQUIRED_SECTIONS = [
    "Role",
    "Non-role",
    "ADLC Binding",
    "Inputs",
    "Outputs",
    "Autonomy Boundary",
    "Can Approve?",
    "Can Reject?",
    "Can Execute?",
    "Required Reads",
    "Required Writes",
    "Failure Modes",
    "Stop Conditions",
    "Output Format",
]

GOVERNANCE_ADLC_HEADING = "## ADLC Binding"
DEFAULT_NO_TRADE_TEXT = "NO_TRADE"
PAPER_TRADING_ONLY_FILE = "governance/paper_trading_only.md"
EXECUTION_GATEKEEPER_FILE = "agents/08_EXECUTION_GATEKEEPER_AGENT.md"
ORCHESTRATOR_FILE = "agents/00_ORCHESTRATOR.md"


@dataclass(frozen=True)
class ValidationIssue:
    check: str
    path: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    root: Path
    checked_files: int
    issues: tuple[ValidationIssue, ...]

    @property
    def passed(self) -> bool:
        return not self.issues

    @property
    def status(self) -> str:
        return "PASS" if self.passed else "FAIL"


def load_markdown_files(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for relative_path in REQUIRED_FILES:
        path = root / relative_path
        if path.exists() and path.is_file():
            files[relative_path] = path.read_text(encoding="utf-8")
    return files


def validate(root: Path) -> ValidationReport:
    root = root.resolve()
    files = load_markdown_files(root)
    issues: list[ValidationIssue] = []

    issues.extend(_validate_required_files(root))
    issues.extend(_validate_governance_adlc(root))
    issues.extend(_validate_agent_sections(root))
    issues.extend(_validate_execution_gatekeeper(root))
    issues.extend(_validate_orchestrator_single_model_block(root))
    issues.extend(_validate_paper_trading_only(root))
    issues.extend(_validate_default_no_trade(files))

    return ValidationReport(root=root, checked_files=len(files), issues=tuple(issues))


def _validate_required_files(root: Path) -> Iterable[ValidationIssue]:
    for relative_path in REQUIRED_FILES:
        path = root / relative_path
        if not path.is_file():
            yield ValidationIssue(
                check="required_file",
                path=relative_path,
                message="Required markdown file is missing.",
            )


def _validate_governance_adlc(root: Path) -> Iterable[ValidationIssue]:
    for path in sorted((root / "governance").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        if GOVERNANCE_ADLC_HEADING not in text:
            yield ValidationIssue(
                check="governance_adlc_binding",
                path=_relative(root, path),
                message="Governance file is missing ## ADLC Binding.",
            )


def _validate_agent_sections(root: Path) -> Iterable[ValidationIssue]:
    for path in sorted((root / "agents").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for section in AGENT_REQUIRED_SECTIONS:
            if f"## {section}" not in text:
                yield ValidationIssue(
                    check="agent_required_section",
                    path=_relative(root, path),
                    message=f"Agent file is missing ## {section}.",
                )


def _validate_execution_gatekeeper(root: Path) -> Iterable[ValidationIssue]:
    text = _read_required(root, EXECUTION_GATEKEEPER_FILE)
    required = (
        "Gate status only. It cannot approve trade quality, cannot approve risk, "
        "and cannot approve live or broker execution."
    )
    if required not in text:
        yield ValidationIssue(
            check="execution_gatekeeper_authority",
            path=EXECUTION_GATEKEEPER_FILE,
            message="Execution Gatekeeper authority wording is missing or too broad.",
        )
    if "## Can Execute?\nNo." not in text:
        yield ValidationIssue(
            check="execution_gatekeeper_no_execute",
            path=EXECUTION_GATEKEEPER_FILE,
            message="Execution Gatekeeper must explicitly state it cannot execute.",
        )


def _validate_orchestrator_single_model_block(root: Path) -> Iterable[ValidationIssue]:
    text = _read_required(root, ORCHESTRATOR_FILE)
    required = (
        "Any workflow asks one model or one agent to perform context analysis, "
        "proposal creation, risk approval, execution gatekeeping, and journaling "
        "without specialist handoff"
    )
    if required not in text:
        yield ValidationIssue(
            check="orchestrator_single_model_block",
            path=ORCHESTRATOR_FILE,
            message="Orchestrator does not block single-model workflow collapse.",
        )


def _validate_paper_trading_only(root: Path) -> Iterable[ValidationIssue]:
    text = _read_required(root, PAPER_TRADING_ONLY_FILE)
    required_phrases = [
        "Paper Trading Only",
        "The system may only evaluate and record paper-trade decisions.",
        "It must not connect to, instruct, or simulate through a live broker.",
        "Live order placement",
        "Broker API connection",
        "EXECUTION_BLOCKED",
    ]
    for phrase in required_phrases:
        if phrase not in text:
            yield ValidationIssue(
                check="paper_trading_only",
                path=PAPER_TRADING_ONLY_FILE,
                message=f"Paper-trading-only control is missing: {phrase}",
            )


def _validate_default_no_trade(files: dict[str, str]) -> Iterable[ValidationIssue]:
    paths_with_default = [
        path for path, text in files.items() if DEFAULT_NO_TRADE_TEXT in text
    ]
    if not paths_with_default:
        yield ValidationIssue(
            check="default_no_trade",
            path=".",
            message="No loaded markdown file declares NO_TRADE.",
        )


def _read_required(root: Path, relative_path: str) -> str:
    path = root / relative_path
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def format_report(report: ValidationReport) -> str:
    lines = [
        "# Architecture Validation Report",
        "",
        f"Root: {report.root}",
        f"Status: {report.status}",
        f"Loaded Markdown Files: {report.checked_files}",
        "",
    ]
    if report.passed:
        lines.append("No validation issues found.")
        return "\n".join(lines)

    lines.append("Issues:")
    for issue in report.issues:
        lines.append(f"- [{issue.check}] {issue.path}: {issue.message}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the markdown-only Phase 0 architecture controls."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Repository root containing architecture markdown files.",
    )
    args = parser.parse_args()

    report = validate(Path(args.root))
    print(format_report(report))
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

