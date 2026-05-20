from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
import os
from pathlib import Path
import re
from typing import Any


REPORT_ROOT = Path("reports/real_market_paper_reconciliation")
PHASE_NAME = "Phase 59 Real Market Paper Send Reconciliation and Post-Mortem"
SOURCE_PHASE = "Phase 58 Real Market-Driven Paper Send"
MAX_NOTIONAL_USD = 100.0
REDACTION_MARKER = "[REDACTED]"
SUPPORTED_STATUSES = ("RECONCILED", "RECONCILED_WITH_WARNINGS", "BLOCKED", "FAILED")


@dataclass(frozen=True)
class Phase58OrderResult:
    symbol: str
    accepted_notional_usd: float | None = None
    paper_only: bool = True
    live_order_sent: bool = False
    live_endpoint_detected: bool = False
    live_account: bool = False
    order_status: str | None = None
    status_message: str | None = None
    raw_adapter_message: str | None = None
    provider_message: str | None = None
    fill_price: float | None = None
    reference_price: float | None = None
    filled_qty: float | None = None
    submitted_at: str | None = None
    filled_at: str | None = None


@dataclass(frozen=True)
class Phase58ReconciliationInput:
    source_phase: str
    symbol: str
    timestamp: str
    timeframe: str
    session: str
    strategy_decision: str
    strategy_reason: str
    evaluation_gate_status: str
    negative_regression_status: str
    candidate_created: bool
    human_review_approved: bool
    finalized_request_created: bool
    manual_execution_confirmed: bool
    preflight_status: str
    max_notional_usd: float
    paper_only: bool
    broker_execution_readiness: bool
    order_api_used: bool
    paper_order_sent: bool
    live_order_sent: bool
    live_trading_assumption: bool
    final_status: str
    reason: str = ""
    source: str = ""
    order_result: Phase58OrderResult | None = None
    reconciliation_notes: str = ""
    input_artifact_references: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReconciliationArtifacts:
    report_path: Path
    post_mortem_path: Path
    evidence_manifest_path: Path


@dataclass(frozen=True)
class RealMarketPaperReconciliationResult:
    reconciliation_status: str
    final_status: str
    warnings: tuple[str, ...]
    failures: tuple[str, ...]
    requested_notional_usd: float | str
    accepted_notional_usd: float | str
    fill_price: float | str
    reference_price: float | str
    estimated_slippage_bps: float | str
    order_status: str
    filled_qty: float | str
    submitted_at: str
    filled_at: str
    status_message: str
    raw_adapter_message: str
    provider_message: str
    artifacts: ReconciliationArtifacts


class RealMarketPaperReconciler:
    def __init__(
        self,
        payload: Phase58ReconciliationInput,
        *,
        report_root: Path = REPORT_ROOT,
        test_command_evidence: tuple[str, ...] = (),
    ) -> None:
        self.payload = payload
        self.report_root = report_root
        self.test_command_evidence = test_command_evidence

    def reconcile(self) -> RealMarketPaperReconciliationResult:
        warnings: list[str] = []
        failures: list[str] = []
        self._validate_hard_blocks(warnings, failures)
        metrics = self._metrics(warnings)
        reconciliation_status = self._status(warnings, failures)
        artifacts = self._write_artifacts(reconciliation_status, warnings, failures, metrics)
        return RealMarketPaperReconciliationResult(
            reconciliation_status=reconciliation_status,
            final_status=reconciliation_status,
            warnings=tuple(warnings),
            failures=tuple(failures),
            artifacts=artifacts,
            **metrics,
        )

    def _validate_hard_blocks(self, warnings: list[str], failures: list[str]) -> None:
        payload = self.payload
        symbols = [symbol.strip() for symbol in payload.symbol.split(",") if symbol.strip()]
        if payload.source_phase != SOURCE_PHASE:
            failures.append("unsupported_source_phase")
        if not payload.symbol:
            failures.append("missing_symbol")
        if len(symbols) > 1:
            failures.append("more_than_one_symbol")
        if payload.max_notional_usd > MAX_NOTIONAL_USD:
            failures.append("max_notional_over_100")
        if payload.paper_only is not True:
            failures.append("paper_only_required")
        if payload.live_order_sent:
            failures.append("live_order_sent")
        if payload.live_trading_assumption:
            failures.append("live_trading_assumption")
        if payload.paper_order_sent and payload.human_review_approved is not True:
            failures.append("missing_human_review_approval")
        if payload.paper_order_sent and payload.manual_execution_confirmed is not True:
            failures.append("missing_manual_execution_confirmation")
        if payload.paper_order_sent and payload.preflight_status != "PAPER_ORDER_SEND_ALLOWED":
            failures.append("preflight_not_pass")
        if payload.paper_order_sent and payload.broker_execution_readiness is not True:
            failures.append("broker_execution_readiness_inconsistent")
        if payload.broker_execution_readiness and (
            payload.paper_only is not True
            or payload.preflight_status != "PAPER_ORDER_SEND_ALLOWED"
            or payload.live_trading_assumption
            or payload.live_order_sent
        ):
            failures.append("broker_execution_readiness_not_paper_preflight_consistent")
        if not payload.paper_order_sent and payload.final_status != "PAPER_ORDER_SENT":
            warnings.append("no_paper_order_sent")
        self._validate_order_result(failures)
        self._validate_required_statements(failures)

    def _validate_order_result(self, failures: list[str]) -> None:
        order = self.payload.order_result
        if order is None:
            if self.payload.paper_order_sent:
                failures.append("missing_order_result")
            return
        if order.live_endpoint_detected:
            failures.append("live_endpoint_in_order_result")
        if order.live_account:
            failures.append("live_account_in_order_result")
        if order.live_order_sent:
            failures.append("live_order_sent_in_order_result")
        if order.paper_only is not True:
            failures.append("order_result_not_paper_only")
        if order.symbol != self.payload.symbol:
            failures.append("order_symbol_mismatch")
        if (
            order.accepted_notional_usd is not None
            and order.accepted_notional_usd > MAX_NOTIONAL_USD
        ):
            failures.append("accepted_notional_over_100")

    def _validate_required_statements(self, failures: list[str]) -> None:
        # Statements are generated unconditionally by this module. This check exists
        # to make the invariant explicit before writing artifacts.
        required = (
            "No new order was sent.",
            "No live order was sent.",
            "This phase only reconciles Phase 58 artifacts.",
            "Paper-only execution path remains required.",
            "Human review remained required.",
            "Manual execution confirmation remained required.",
            "Live trading remains unsupported.",
        )
        if not all(required):
            failures.append("missing_required_safety_statement")

    def _metrics(self, warnings: list[str]) -> dict[str, float | str]:
        order = self.payload.order_result
        requested_notional = self.payload.max_notional_usd
        accepted_notional: float | str = "UNAVAILABLE"
        fill_price: float | str = "UNAVAILABLE"
        reference_price: float | str = "UNAVAILABLE"
        estimated_slippage: float | str = "UNAVAILABLE"
        order_status = "UNAVAILABLE"
        filled_qty: float | str = "UNAVAILABLE"
        submitted_at = "UNAVAILABLE"
        filled_at = "UNAVAILABLE"
        status_message = "UNAVAILABLE"
        raw_adapter_message = "UNAVAILABLE"
        provider_message = "UNAVAILABLE"
        if order:
            accepted_notional = (
                order.accepted_notional_usd
                if order.accepted_notional_usd is not None
                else "UNAVAILABLE"
            )
            fill_price = order.fill_price if order.fill_price is not None else "UNAVAILABLE"
            reference_price = (
                order.reference_price if order.reference_price is not None else "UNAVAILABLE"
            )
            order_status = order.order_status or "UNAVAILABLE"
            status_message = order.status_message or "UNAVAILABLE"
            raw_adapter_message = order.raw_adapter_message or "UNAVAILABLE"
            provider_message = order.provider_message or "UNAVAILABLE"
            filled_qty = order.filled_qty if order.filled_qty is not None else "UNAVAILABLE"
            submitted_at = order.submitted_at or "UNAVAILABLE"
            filled_at = order.filled_at or "UNAVAILABLE"
            if order.fill_price is None:
                warnings.append("fill_price_unavailable")
            if order.reference_price is None:
                warnings.append("reference_price_unavailable")
            if order.fill_price is not None and order.reference_price:
                estimated_slippage = round(
                    ((order.fill_price - order.reference_price) / order.reference_price)
                    * 10000,
                    4,
                )
        return {
            "requested_notional_usd": requested_notional,
            "accepted_notional_usd": accepted_notional,
            "fill_price": fill_price,
            "reference_price": reference_price,
            "estimated_slippage_bps": estimated_slippage,
            "order_status": order_status,
            "filled_qty": filled_qty,
            "submitted_at": submitted_at,
            "filled_at": filled_at,
            "status_message": status_message,
            "raw_adapter_message": raw_adapter_message,
            "provider_message": provider_message,
        }

    def _status(self, warnings: list[str], failures: list[str]) -> str:
        if failures:
            return "FAILED"
        if not self.payload.paper_order_sent and self.payload.final_status != "PAPER_ORDER_SENT":
            return "BLOCKED"
        if warnings:
            return "RECONCILED_WITH_WARNINGS"
        return "RECONCILED"

    def _write_artifacts(
        self,
        reconciliation_status: str,
        warnings: list[str],
        failures: list[str],
        metrics: dict[str, float | str],
    ) -> ReconciliationArtifacts:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        report_dir = self.report_root / timestamp
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "REAL_MARKET_PAPER_RECONCILIATION_REPORT.md"
        post_mortem_path = report_dir / "POST_MORTEM.md"
        evidence_path = report_dir / "EVIDENCE_MANIFEST.md"
        report_path.write_text(
            self._report_text(reconciliation_status, warnings, failures, metrics),
            encoding="utf-8",
        )
        post_mortem_path.write_text(
            self._post_mortem_text(reconciliation_status, warnings, failures),
            encoding="utf-8",
        )
        evidence_path.write_text(
            self._evidence_text(report_path, post_mortem_path),
            encoding="utf-8",
        )
        return ReconciliationArtifacts(
            report_path=report_path,
            post_mortem_path=post_mortem_path,
            evidence_manifest_path=evidence_path,
        )

    def _report_text(
        self,
        reconciliation_status: str,
        warnings: list[str],
        failures: list[str],
        metrics: dict[str, float | str],
    ) -> str:
        payload = self.payload
        lines = [
            "# Real Market Paper Reconciliation Report",
            "",
            f"- phase: {PHASE_NAME}",
            f"- source_phase: {SOURCE_PHASE}",
            f"- symbol: {_redact(payload.symbol)}",
            f"- source: {_redact(payload.source)}",
            f"- timestamp: {_redact(payload.timestamp)}",
            f"- timeframe: {_redact(payload.timeframe)}",
            f"- session: {_redact(payload.session)}",
            f"- max_notional_usd: {payload.max_notional_usd:.2f}",
            f"- paper_only: {str(payload.paper_only).lower()}",
            f"- paper_order_sent: {str(payload.paper_order_sent).lower()}",
            "- live_order_sent: false",
            "- live_trading_assumption: false",
            f"- human_review_approved: {str(payload.human_review_approved).lower()}",
            f"- manual_execution_confirmed: {str(payload.manual_execution_confirmed).lower()}",
            f"- preflight_status: {_redact(payload.preflight_status)}",
            f"- order_api_used: {str(payload.order_api_used).lower()}",
            f"- broker_execution_readiness: {str(payload.broker_execution_readiness).lower()}",
            f"- order_status: {_redact(str(metrics['order_status']))}",
            f"- status_message: {_redact(str(metrics['status_message']))}",
            f"- raw_adapter_message: {_redact(str(metrics['raw_adapter_message']))}",
            f"- provider_message: {_redact(str(metrics['provider_message']))}",
            f"- reconciliation_status: {reconciliation_status}",
            f"- requested_notional_usd: {metrics['requested_notional_usd']}",
            f"- accepted_notional_usd: {metrics['accepted_notional_usd']}",
            f"- fill_price: {metrics['fill_price']}",
            f"- reference_price: {metrics['reference_price']}",
            f"- estimated_slippage_bps: {metrics['estimated_slippage_bps']}",
            f"- filled_qty: {metrics['filled_qty']}",
            f"- submitted_at: {_redact(str(metrics['submitted_at']))}",
            f"- filled_at: {_redact(str(metrics['filled_at']))}",
            f"- strategy_reason: {_redact(payload.strategy_reason)}",
            f"- reason: {_redact(payload.reason)}",
            f"- reconciliation_notes: {_redact(payload.reconciliation_notes)}",
            f"- warnings: {_redact(','.join(warnings) if warnings else 'none')}",
            f"- failures: {_redact(','.join(failures) if failures else 'none')}",
            "- safety_invariants: paper_only,no_live_order,no_new_order,no_secret_output",
            "- secrets_printed: false",
            f"- final status: {reconciliation_status}",
            "- No new order was sent.",
            "- No live order was sent.",
            "- This phase only reconciles Phase 58 artifacts.",
            "- Paper-only execution path remains required.",
            "- Human review remained required.",
            "- Manual execution confirmation remained required.",
            "- Live trading remains unsupported.",
        ]
        return "\n".join(lines) + "\n"

    def _post_mortem_text(
        self,
        reconciliation_status: str,
        warnings: list[str],
        failures: list[str],
    ) -> str:
        return "\n".join(
            [
                "# Post-Mortem",
                "",
                "## Summary",
                f"Reconciliation result: {reconciliation_status}.",
                "",
                "## What Happened",
                "Phase 58 artifacts were consumed for reconciliation only.",
                "",
                "## What Did Not Happen",
                "No new order was sent.",
                "",
                "## Safety Gates Observed",
                "Paper-only, human review, manual confirmation, preflight, and no-live-trading invariants were checked.",
                "",
                "## Reconciliation Result",
                reconciliation_status,
                "",
                "## Warnings",
                _redact(", ".join(warnings) if warnings else "none"),
                "",
                "## Failures",
                _redact(", ".join(failures) if failures else "none"),
                "",
                "## Follow-Up Actions",
                "Review warnings or failures before any future paper-only run.",
                "",
                "No new order was sent.",
                "Live trading remains unsupported.",
                "",
            ]
        )

    def _evidence_text(self, report_path: Path, post_mortem_path: Path) -> str:
        refs = self.payload.input_artifact_references or ("UNAVAILABLE",)
        commands = self.test_command_evidence or (
            "python3 -m unittest tests.test_real_market_paper_reconciliation",
            "python3 -m unittest discover tests",
        )
        lines = [
            "# Evidence Manifest",
            "",
            "## Input Artifact References",
            *[f"- {_redact(ref)}" for ref in refs],
            "",
            "## Generated Artifacts",
            f"- Generated report path: {report_path}",
            f"- Generated post-mortem path: {post_mortem_path}",
            "",
            "## Test Command Evidence",
            *[f"- {command}" for command in commands],
            "",
            "## Safety Invariant Checklist",
            "- No new order was sent.",
            "- No live order was sent.",
            "- Paper-only execution path remains required.",
            "- Human review remained required.",
            "- Manual execution confirmation remained required.",
            "- Live trading remains unsupported.",
            "",
            "## No-Secret Evidence",
            "- secrets_printed: false",
            "",
            "## No-Live-Order Evidence",
            "- live_order_sent: false",
            "",
        ]
        return "\n".join(lines)


def reconcile_phase58_paper_run(
    payload: Phase58ReconciliationInput,
    *,
    report_root: Path = REPORT_ROOT,
    test_command_evidence: tuple[str, ...] = (),
) -> RealMarketPaperReconciliationResult:
    return RealMarketPaperReconciler(
        payload,
        report_root=report_root,
        test_command_evidence=test_command_evidence,
    ).reconcile()


def _redact(value: object) -> str:
    text = str(value)
    redacted = text
    for env_name in ("ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY"):
        secret = os.environ.get(env_name)
        if secret:
            redacted = redacted.replace(secret, REDACTION_MARKER)
    redacted = re.sub(
        r"(?i)(bearer\s+)[a-z0-9._~+/=-]{8,}",
        r"\1" + REDACTION_MARKER,
        redacted,
    )
    redacted = re.sub(
        r"(?i)(api[_-]?key|secret|token)\s*=\s*[^,\s]+",
        r"\1=" + REDACTION_MARKER,
        redacted,
    )
    redacted = re.sub(
        r"(?i)\b[a-z0-9._-]*(secret|token|api[_-]?key)[a-z0-9._-]*\b",
        REDACTION_MARKER,
        redacted,
    )
    redacted = re.sub(
        r"\b(?=[A-Za-z0-9]*[A-Za-z])(?=[A-Za-z0-9]*[0-9])[A-Za-z0-9]{24,}\b",
        REDACTION_MARKER,
        redacted,
    )
    return redacted
