from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Mapping


HOLD = "HOLD"
CONTINUE_MANUAL_LIMITED_PAPER = "CONTINUE_MANUAL_LIMITED_PAPER"
PROCEED_TO_NEXT_DESIGN_PHASE = "PROCEED_TO_NEXT_DESIGN_PHASE"
REVIEW_COMPLETE = "REVIEW_COMPLETE"
REVIEW_BLOCKED = "REVIEW_BLOCKED"
REPORT_ROOT = Path("reports/offline_strategy_quality_review")
REPORT_NAME = "OFFLINE_STRATEGY_QUALITY_REVIEW.md"

REQUIRED_DATASET_FILES = (
    Path("reports/phase_11_repeatability/PHASE_11_REPEATABILITY_SUMMARY.md"),
    Path("reports/phase_16_evaluation_gated_regression/PHASE_16_EVALUATION_GATED_REGRESSION_SUMMARY.md"),
    Path("docs/BASELINE_SAFE_PAPER_EXECUTION_V2.md"),
)

SCORE_KEYS = (
    "strategy_quality",
    "no_trade_discipline",
    "rejection_quality",
    "journal_quality",
    "evaluation_gate_quality",
    "risk_discipline",
    "adlc_compliance",
    "data_integrity",
)


@dataclass(frozen=True)
class ArtifactRecord:
    path: str
    text: str


@dataclass(frozen=True)
class OfflineStrategyQualityReview:
    review_status: str
    dataset_reviewed: tuple[str, ...]
    artifacts_reviewed: int
    scores: Mapping[str, int]
    red_flags: tuple[str, ...]
    failure_patterns: tuple[str, ...]
    improvement_recommendations: tuple[str, ...]
    recommendation: str
    report_path: str | None

    def as_dict(self) -> dict[str, object]:
        return {
            "review_status": self.review_status,
            "dataset_reviewed": list(self.dataset_reviewed),
            "artifacts_reviewed": self.artifacts_reviewed,
            "scores": dict(self.scores),
            "red_flags": list(self.red_flags),
            "failure_patterns": list(self.failure_patterns),
            "improvement_recommendations": list(self.improvement_recommendations),
            "recommendation": self.recommendation,
            "report_path": self.report_path,
        }


def run_offline_strategy_quality_review(
    root: Path = Path("."),
    *,
    output_root: Path = REPORT_ROOT,
) -> OfflineStrategyQualityReview:
    root = root.resolve()
    missing = _missing_required_dataset(root)
    artifacts = _collect_artifacts(root) if not missing else ()
    red_flags = list(_red_flags(artifacts, missing))
    failure_patterns = list(_failure_patterns(red_flags))
    scores = _scores(artifacts, red_flags, missing)
    recommendation = _recommendation(missing, red_flags, artifacts)
    recommendations = _improvement_recommendations(red_flags, missing)
    status = REVIEW_BLOCKED if missing else REVIEW_COMPLETE

    review = OfflineStrategyQualityReview(
        review_status=status,
        dataset_reviewed=tuple(record.path for record in artifacts),
        artifacts_reviewed=len(artifacts),
        scores=scores,
        red_flags=tuple(dict.fromkeys(red_flags)),
        failure_patterns=tuple(dict.fromkeys(failure_patterns)),
        improvement_recommendations=recommendations,
        recommendation=recommendation,
        report_path=None,
    )
    report_dir = _timestamped_report_dir(root / output_root)
    report_path = report_dir / REPORT_NAME
    final_review = OfflineStrategyQualityReview(
        **{**review.as_dict(), "report_path": report_path.as_posix()}
    )
    report_path.write_text(_render_report(final_review), encoding="utf-8")
    return final_review


def _missing_required_dataset(root: Path) -> tuple[str, ...]:
    return tuple(path.as_posix() for path in REQUIRED_DATASET_FILES if not (root / path).exists())


def _collect_artifacts(root: Path) -> tuple[ArtifactRecord, ...]:
    candidates: list[Path] = []
    for required in REQUIRED_DATASET_FILES:
        candidates.append(root / required)
    candidates.extend(sorted((root / "reports" / "first_controlled_paper_send").glob("*/*.md")))
    candidates.extend(sorted((root / "reports" / "first_controlled_paper_send").glob("*/*.json")))
    candidates.extend(sorted((root / "memory").glob("*.md")))
    candidates.extend(sorted((root / "evaluation").glob("*.md")))

    records: list[ArtifactRecord] = []
    seen: set[Path] = set()
    for path in candidates:
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        records.append(
            ArtifactRecord(
                path=path.relative_to(root).as_posix(),
                text=path.read_text(encoding="utf-8"),
            )
        )
    return tuple(records)


def _red_flags(
    artifacts: tuple[ArtifactRecord, ...],
    missing: tuple[str, ...],
) -> tuple[str, ...]:
    if missing:
        return tuple(f"missing dataset artifact: {path}" for path in missing)

    text = _combined_text(artifacts)
    approval_count = _count_any(text, ("human_approved_for_paper_only", "paper_order_submitted"))
    rejection_count = _count_any(text, ("rejected", "rejection", "no_trade", "no trade"))

    flags: list[str] = []
    if approval_count >= 4 or _approval_rejection_ratio_flags(approval_count, rejection_count):
        flags.append("too many approvals")
    if rejection_count < 2:
        flags.append("too few rejections")
    if not _has_artifact(artifacts, ("no_trade", "no trade", "no-trade")):
        flags.append("no-trade artifacts missing")
    if _has_any(text, ("weak journal", "thin journal", "poor journal", "journal reasoning weak")):
        flags.append("weak journal reasoning")
    if _has_any(text, ("vague liquidity", "weak liquidity", "liquidity unclear")):
        flags.append("vague liquidity language")
    if _has_any(text, ("vague confirmation", "confirmation unclear", "unclear confirmation")):
        flags.append("vague confirmation language")
    if _repeated_generic_thesis(artifacts):
        flags.append("repeated generic thesis text")
    if _has_any(text, ("score inflation", "inflated score", "evaluation score inflation")):
        flags.append("evaluation score inflation")
    if _has_any(text, ("risk rubber-stamp", "risk approval without meaningful challenge")):
        flags.append("risk approval without meaningful challenge")
    if _has_any(text, ("human approval rubber-stamping", "human rubber-stamp")):
        flags.append("human approval rubber-stamping")
    if _agent_rubber_stamping_detected(text):
        flags.append("agent rubber-stamping")
    if _has_any(text, ("no-trade avoidance", "forced trade", "pressure to trade")):
        flags.append("no-trade avoidance")
    if _has_any(text, ("increase size before quality improves", "increase notional before quality improves")):
        flags.append("suggestion to increase size before quality improves")
    return tuple(dict.fromkeys(flags))


def _failure_patterns(red_flags: Iterable[str]) -> tuple[str, ...]:
    patterns: list[str] = []
    for flag in red_flags:
        if flag in {
            "too many approvals",
            "too few rejections",
            "no-trade artifacts missing",
            "no-trade avoidance",
        }:
            patterns.append("selectivity drift")
        if flag in {
            "weak journal reasoning",
            "vague liquidity language",
            "vague confirmation language",
            "repeated generic thesis text",
        }:
            patterns.append("evidence quality drift")
        if flag in {
            "evaluation score inflation",
            "risk approval without meaningful challenge",
            "human approval rubber-stamping",
            "agent rubber-stamping",
        }:
            patterns.append("gate performativity or rubber-stamping")
        if "missing dataset artifact" in flag:
            patterns.append("insufficient offline dataset")
    return tuple(dict.fromkeys(patterns))


def _scores(
    artifacts: tuple[ArtifactRecord, ...],
    red_flags: list[str],
    missing: tuple[str, ...],
) -> Mapping[str, int]:
    if missing:
        return {key: 0 for key in SCORE_KEYS}
    text = _combined_text(artifacts)
    return {
        "strategy_quality": _score(3, red_flags, ("too many approvals", "too few rejections", "no-trade avoidance")),
        "no_trade_discipline": _score(2 if _has_artifact(artifacts, ("no_trade", "no trade", "no-trade")) else 1, red_flags, ("no-trade artifacts missing", "no-trade avoidance")),
        "rejection_quality": _score(2 if _has_any(text, ("rejected", "rejection")) else 1, red_flags, ("too few rejections",)),
        "journal_quality": _score(3, red_flags, ("weak journal reasoning", "repeated generic thesis text")),
        "evaluation_gate_quality": _score(3, red_flags, ("evaluation score inflation",)),
        "risk_discipline": _score(3, red_flags, ("risk approval without meaningful challenge", "agent rubber-stamping", "suggestion to increase size before quality improves")),
        "adlc_compliance": 3 if _has_any(text, ("adlc", "baseline safe paper execution v2")) else 1,
        "data_integrity": 3 if _has_any(text, ("data integrity", "data freshness", "data completeness")) else 1,
    }


def _score(base: int, red_flags: list[str], penalties: tuple[str, ...]) -> int:
    penalty_count = sum(1 for flag in penalties if flag in red_flags)
    return max(0, base - penalty_count)


def _recommendation(
    missing: tuple[str, ...],
    red_flags: list[str],
    artifacts: tuple[ArtifactRecord, ...],
) -> str:
    if missing:
        return HOLD
    if any(flag in red_flags for flag in ("suggestion to increase size before quality improves", "evaluation score inflation")):
        return HOLD
    if red_flags:
        return CONTINUE_MANUAL_LIMITED_PAPER
    if not _has_artifact(artifacts, ("no_trade", "no trade", "no-trade")):
        return CONTINUE_MANUAL_LIMITED_PAPER
    return PROCEED_TO_NEXT_DESIGN_PHASE


def _improvement_recommendations(
    red_flags: list[str],
    missing: tuple[str, ...],
) -> tuple[str, ...]:
    recommendations = [
        "Improve quality before increasing notional.",
        "Improve rejection quality before increasing frequency.",
        "Improve no-trade discipline before automation.",
        "Keep live trading unsupported.",
        "Do not recommend increasing notional.",
        "Do not recommend automation.",
    ]
    for path in missing:
        recommendations.append(f"Restore missing dataset artifact: {path}.")
    for flag in red_flags:
        recommendations.append(f"Review red flag: {flag}.")
    return tuple(dict.fromkeys(recommendations))


def _timestamped_report_dir(root: Path) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    report_dir = root / timestamp
    suffix = 1
    while report_dir.exists():
        report_dir = root / f"{timestamp}-{suffix}"
        suffix += 1
    report_dir.mkdir(parents=True, exist_ok=False)
    return report_dir


def _render_report(review: OfflineStrategyQualityReview) -> str:
    scores = dict(review.scores)
    return f"""# Offline Strategy Quality Review

## Review Status

{review.review_status}

## Dataset Reviewed

{_bullet_list(review.dataset_reviewed)}

## Number Of Artifacts Reviewed

{review.artifacts_reviewed}

## Scores

- Strategy quality score: {scores.get("strategy_quality", 0)}
- No-trade discipline score: {scores.get("no_trade_discipline", 0)}
- Rejection quality score: {scores.get("rejection_quality", 0)}
- Journal quality score: {scores.get("journal_quality", 0)}
- Evaluation-gate quality score: {scores.get("evaluation_gate_quality", 0)}
- Risk discipline score: {scores.get("risk_discipline", 0)}
- ADLC compliance score: {scores.get("adlc_compliance", 0)}
- Data integrity score: {scores.get("data_integrity", 0)}

## Red Flags Detected

{_bullet_list(review.red_flags) if review.red_flags else "- None"}

## Failure Patterns

{_bullet_list(review.failure_patterns) if review.failure_patterns else "- None"}

## Improvement Recommendations

{_bullet_list(review.improvement_recommendations)}

## Recommendation

{review.recommendation}

## Safety Boundary

Offline review only. No orders, approvals, paper order requests, risk limit changes, automation, live trading, credentials, or LLM calls are authorized.

Live trading remains unsupported.
"""


def _bullet_list(values: Iterable[str]) -> str:
    items = tuple(values)
    if not items:
        return "- None"
    return "\n".join(f"- `{item}`" for item in items)


def _combined_text(artifacts: tuple[ArtifactRecord, ...]) -> str:
    return "\n".join(record.text for record in artifacts).lower()


def _has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term.lower() in text for term in terms)


def _count_any(text: str, terms: tuple[str, ...]) -> int:
    return sum(text.count(term.lower()) for term in terms)


def _approval_rejection_ratio_flags(approval_count: int, rejection_count: int) -> bool:
    if approval_count < 2:
        return False
    if rejection_count == 0:
        return True
    return approval_count / rejection_count >= 3


def _has_artifact(artifacts: tuple[ArtifactRecord, ...], terms: tuple[str, ...]) -> bool:
    return any(
        any(term.lower() in record.path.lower() or term.lower() in record.text.lower() for term in terms)
        for record in artifacts
    )


def _repeated_generic_thesis(artifacts: tuple[ArtifactRecord, ...]) -> bool:
    thesis_lines: dict[str, int] = {}
    for record in artifacts:
        for line in record.text.splitlines():
            normalized = line.strip().lower()
            if "paper-only setup fixture" in normalized or "generic thesis" in normalized:
                thesis_lines[normalized] = thesis_lines.get(normalized, 0) + 1
    return any(count >= 2 for count in thesis_lines.values())


def _agent_rubber_stamping_detected(text: str) -> bool:
    explicit_markers = (
        "agent rubber-stamping",
        "specialist rubber-stamping",
        "all agents approving with no objections",
        "no agent-specific reasoning",
        "no disagreement or challenge",
        "evaluation gate pass with no dimension-level reasoning",
        "risk manager approval without meaningful challenge",
    )
    if _has_any(text, explicit_markers):
        return True

    generic_approval_count = _count_any(
        text,
        (
            "looks good",
            "approved",
            "valid setup",
            "pass",
        ),
    )
    evidence_count = _count_any(
        text,
        (
            "because",
            "liquidity",
            "higher-timeframe",
            "invalidation",
            "fixed risk",
            "rejected",
            "challenge",
            "objection",
        ),
    )
    return generic_approval_count >= 6 and evidence_count <= 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run offline strategy quality review.")
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()

    result = run_offline_strategy_quality_review(args.root)
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.review_status == REVIEW_COMPLETE else 1


if __name__ == "__main__":
    raise SystemExit(main())
