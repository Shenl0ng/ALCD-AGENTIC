from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence


DATASET_PATH = Path("evaluation/negative_cases/negative_case_dataset.json")
REPORT_PATH = Path("reports/negative_case_dataset/NEGATIVE_CASE_DATASET_SUMMARY.md")

REQUIRED_FIELDS = (
    "case_id",
    "category",
    "input_summary",
    "agent_outputs",
    "expected_decision",
    "expected_gate_status",
    "expected_score_band",
    "expected_rejection_reason",
    "expected_journal_note",
    "why_no_trade_is_correct",
    "prohibited_outcome",
)

REQUIRED_CATEGORIES = (
    "Missing higher-timeframe context",
    "Generic higher-timeframe context",
    "Weak liquidity location",
    "Vague liquidity language",
    "Vague confirmation",
    "Non-observable confirmation",
    "Generic thesis",
    "Thesis reusable for any symbol",
    "Missing credible invalidation",
    "Risk valid but setup weak",
    "Forced trade behavior",
    "Excessive confidence without evidence",
    "Specialist agent rubber-stamping",
    "Human approval rubber-stamping",
    "Evaluation score inflation",
    "No-trade should be preferred",
    "Journal too weak",
    "Data integrity incomplete",
    "ADLC compliance incomplete",
    "Live trading assumption",
)

REQUIRED_EXPECTED_DECISIONS = (
    "REJECT",
    "NO_TRADE",
    "BLOCK_EVALUATION_GATE",
    "BLOCK_HUMAN_APPROVAL",
    "BLOCK_PAPER_REQUEST",
)

WEAK_SETUP_CATEGORIES = {
    "Missing higher-timeframe context",
    "Generic higher-timeframe context",
    "Weak liquidity location",
    "Vague liquidity language",
    "Vague confirmation",
    "Non-observable confirmation",
    "Generic thesis",
    "Thesis reusable for any symbol",
    "Missing credible invalidation",
    "Risk valid but setup weak",
    "Forced trade behavior",
    "Excessive confidence without evidence",
}

RUBBER_STAMPING_CATEGORIES = {
    "Specialist agent rubber-stamping",
    "Human approval rubber-stamping",
}

JOURNAL_EVIDENCE_FAILURE_CATEGORIES = {
    "Journal too weak",
    "Data integrity incomplete",
    "ADLC compliance incomplete",
    "Missing credible invalidation",
}

PROHIBITED_RECOMMENDATION_PHRASES = (
    "recommend live trading",
    "allow live trading",
    "live trading supported",
    "enable live trading",
    "recommend increasing notional",
    "increase notional allowed",
    "allow increasing notional",
    "recommend automation",
    "automation allowed",
    "enable automation",
)


@dataclass(frozen=True)
class DatasetSummary:
    total_cases: int
    category_counts: Mapping[str, int]
    expected_decision_counts: Mapping[str, int]
    no_trade_case_count: int
    weak_setup_rejection_count: int
    rubber_stamping_case_count: int
    journal_evidence_failure_count: int
    prohibited_outcomes: Mapping[str, int]


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    errors: tuple[str, ...]
    summary: DatasetSummary


def load_dataset(path: Path = DATASET_PATH) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("negative case dataset must be a JSON array")
    return payload


def validate_dataset(cases: Sequence[Mapping[str, object]]) -> ValidationResult:
    errors: list[str] = []
    case_ids: set[str] = set()

    for index, case in enumerate(cases):
        label = str(case.get("case_id") or f"index {index}")
        missing = [field for field in REQUIRED_FIELDS if field not in case]
        if missing:
            errors.append(f"{label}: missing required field(s): {', '.join(missing)}")
        case_id = str(case.get("case_id", ""))
        if case_id in case_ids:
            errors.append(f"{label}: duplicate case_id")
        if case_id:
            case_ids.add(case_id)
        if not str(case.get("prohibited_outcome", "")).strip():
            errors.append(f"{label}: prohibited_outcome is required")
        unsafe = _unsafe_recommendation(case)
        if unsafe:
            errors.append(f"{label}: unsafe recommendation detected: {unsafe}")

    summary = summarize_dataset(cases)
    categories = set(summary.category_counts)
    expected_decisions = set(summary.expected_decision_counts)

    if summary.total_cases < 30:
        errors.append("dataset must contain at least 30 negative cases")
    if summary.no_trade_case_count < 10:
        errors.append("dataset must contain at least 10 explicit NO_TRADE cases")
    if summary.weak_setup_rejection_count < 10:
        errors.append("dataset must contain at least 10 weak setup rejection cases")
    if summary.rubber_stamping_case_count < 5:
        errors.append("dataset must contain at least 5 rubber-stamping cases")
    if summary.journal_evidence_failure_count < 5:
        errors.append("dataset must contain at least 5 journal/evidence failure cases")

    missing_categories = [category for category in REQUIRED_CATEGORIES if category not in categories]
    if missing_categories:
        errors.append(f"missing required categories: {', '.join(missing_categories)}")

    missing_decisions = [
        decision for decision in REQUIRED_EXPECTED_DECISIONS if decision not in expected_decisions
    ]
    if missing_decisions:
        errors.append(f"missing expected decisions: {', '.join(missing_decisions)}")

    return ValidationResult(
        passed=not errors,
        errors=tuple(errors),
        summary=summary,
    )


def summarize_dataset(cases: Sequence[Mapping[str, object]]) -> DatasetSummary:
    category_counts: dict[str, int] = {}
    decision_counts: dict[str, int] = {}
    prohibited_counts: dict[str, int] = {}

    for case in cases:
        category = str(case.get("category", ""))
        decision = str(case.get("expected_decision", ""))
        prohibited = str(case.get("prohibited_outcome", ""))
        category_counts[category] = category_counts.get(category, 0) + 1
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
        prohibited_counts[prohibited] = prohibited_counts.get(prohibited, 0) + 1

    return DatasetSummary(
        total_cases=len(cases),
        category_counts=dict(sorted(category_counts.items())),
        expected_decision_counts=dict(sorted(decision_counts.items())),
        no_trade_case_count=sum(
            1 for case in cases if case.get("expected_decision") == "NO_TRADE"
        ),
        weak_setup_rejection_count=sum(
            1
            for case in cases
            if case.get("expected_decision") == "REJECT"
            and case.get("category") in WEAK_SETUP_CATEGORIES
        ),
        rubber_stamping_case_count=sum(
            1 for case in cases if case.get("category") in RUBBER_STAMPING_CATEGORIES
        ),
        journal_evidence_failure_count=sum(
            1
            for case in cases
            if case.get("category") in JOURNAL_EVIDENCE_FAILURE_CATEGORIES
        ),
        prohibited_outcomes=dict(sorted(prohibited_counts.items())),
    )


def write_summary_report(
    cases: Sequence[Mapping[str, object]],
    output_path: Path = REPORT_PATH,
) -> Path:
    result = validate_dataset(cases)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_summary_report(result), encoding="utf-8")
    return output_path


def render_summary_report(result: ValidationResult) -> str:
    summary = result.summary
    lines = [
        "# Negative Case Dataset Summary",
        "",
        "## Validation Status",
        "",
        "PASS" if result.passed else "FAIL",
        "",
        "## Total Cases",
        "",
        str(summary.total_cases),
        "",
        "## Category Counts",
        "",
    ]
    lines.extend(f"- {category}: {count}" for category, count in summary.category_counts.items())
    lines.extend(
        [
            "",
            "## Expected Decision Counts",
            "",
        ]
    )
    lines.extend(
        f"- {decision}: {count}"
        for decision, count in summary.expected_decision_counts.items()
    )
    lines.extend(
        [
            "",
            "## Required Case Counts",
            "",
            f"- NO_TRADE case count: {summary.no_trade_case_count}",
            f"- Weak setup rejection count: {summary.weak_setup_rejection_count}",
            f"- Rubber-stamping case count: {summary.rubber_stamping_case_count}",
            f"- Journal/evidence failure count: {summary.journal_evidence_failure_count}",
            "",
            "## Prohibited Outcomes Summary",
            "",
        ]
    )
    lines.extend(
        f"- {outcome}: {count}"
        for outcome, count in summary.prohibited_outcomes.items()
    )
    if result.errors:
        lines.extend(["", "## Validation Errors", ""])
        lines.extend(f"- {error}" for error in result.errors)
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "Live trading remains unsupported.",
            "Increasing notional remains prohibited.",
            "Automation remains prohibited.",
            "No Alpaca API, broker calls, order sends, LLM calls, credentials, or `.env` creation are part of this dataset.",
            "",
        ]
    )
    return "\n".join(lines)


def _unsafe_recommendation(case: Mapping[str, object]) -> str:
    text = json.dumps(case, sort_keys=True).lower()
    for phrase in PROHIBITED_RECOMMENDATION_PHRASES:
        if phrase in text:
            return phrase
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the offline negative case dataset.")
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--report", type=Path, default=REPORT_PATH)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    cases = load_dataset(args.dataset)
    result = validate_dataset(cases)
    if args.write_report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(render_summary_report(result), encoding="utf-8")
    if result.passed:
        print("PASS")
        return 0
    for error in result.errors:
        print(error)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
