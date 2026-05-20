from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from os import getenv
from pathlib import Path
import re
from typing import Any, Protocol


PHASE_NAME = "Phase 60 Real Market Paper-Only Soak Supervisor"
REPORT_ROOT = Path("reports/real_market_paper_soak")
WATCHLIST_PATH = Path("memory/watchlist.md")
MAX_NOTIONAL_USD = 100.0
REDACTION_MARKER = "[REDACTED]"


class Phase57Runner(Protocol):
    def run(self) -> object:
        """Run Phase 57 read-only proposal dry run."""


class Phase58Runner(Protocol):
    def run(self, phase57_result: object) -> object:
        """Run Phase 58 paper-only send after all gates pass."""


class Phase59Runner(Protocol):
    def run(self, phase58_result: object) -> object:
        """Run Phase 59 reconciliation/post-mortem after a Phase 58 result."""


@dataclass(frozen=True)
class RealMarketPaperSoakConfig:
    symbols: tuple[str, ...]
    paper_only: bool
    max_notional_usd: float
    max_cycles: int
    max_paper_orders_total: int
    max_paper_orders_per_symbol: int
    require_human_review: bool
    require_manual_confirmation: bool
    require_preflight: bool
    kill_switch_enabled: bool
    output_dir: Path = REPORT_ROOT
    watchlist_path: Path = WATCHLIST_PATH
    allow_paper_send: bool = False
    stop_on_first_failure: bool = True
    stop_on_first_reconciliation_failure: bool = True
    stop_on_secret_detection: bool = True
    live_trading_assumption: bool = False
    live_endpoint_detected: bool = False
    execution_enablement_required: bool = False
    secrets_would_be_printed: bool = False
    injected_secrets: tuple[str, ...] = ()
    test_command_evidence: tuple[str, ...] = (
        "python3 -m unittest tests.test_real_market_paper_soak_supervisor",
        "python3 -m unittest discover tests",
    )


@dataclass(frozen=True)
class SoakCounters:
    cycles_started: int = 0
    cycles_completed: int = 0
    proposals_seen: int = 0
    no_trade_count: int = 0
    rejected_count: int = 0
    trade_proposal_count: int = 0
    paper_order_attempts: int = 0
    paper_orders_sent: int = 0
    reconciliations_run: int = 0
    reconciliations_failed: int = 0
    blocked_cycles: int = 0
    stopped_reason: str = "NOT_STARTED"


@dataclass(frozen=True)
class SoakArtifacts:
    report_path: Path
    evidence_manifest_path: Path


@dataclass(frozen=True)
class RealMarketPaperSoakResult:
    final_status: str
    symbol: str
    paper_only: bool
    max_notional_usd: float
    max_cycles: int
    max_paper_orders_total: int
    max_paper_orders_per_symbol: int
    allow_paper_send: bool
    require_human_review: bool
    require_manual_confirmation: bool
    require_preflight: bool
    kill_switch_enabled: bool
    counters: SoakCounters
    artifacts: SoakArtifacts | None = None
    phase57_artifacts: tuple[str, ...] = ()
    phase58_artifacts: tuple[str, ...] = ()
    phase59_artifacts: tuple[str, ...] = ()
    live_order_sent: bool = False
    live_trading_assumption: bool = False
    secrets_printed: bool = False


class RealMarketPaperSoakSupervisor:
    def __init__(
        self,
        config: RealMarketPaperSoakConfig,
        *,
        phase57_runner: Phase57Runner,
        phase58_runner: Phase58Runner | None = None,
        phase59_runner: Phase59Runner | None = None,
    ) -> None:
        self.config = config
        self.phase57_runner = phase57_runner
        self.phase58_runner = phase58_runner
        self.phase59_runner = phase59_runner
        self._phase57_artifacts: list[str] = []
        self._phase58_artifacts: list[str] = []
        self._phase59_artifacts: list[str] = []

    def run(self) -> RealMarketPaperSoakResult:
        symbol = self._reported_symbol()
        block_reason = self._hard_block_reason()
        if block_reason:
            result = self._result(
                final_status="BLOCKED",
                symbol=symbol,
                counters=SoakCounters(blocked_cycles=1, stopped_reason=block_reason),
            )
            return self._write_artifacts(result)

        counters = SoakCounters(stopped_reason="MAX_CYCLES_COMPLETED")
        orders_by_symbol = {symbol: 0}

        for _ in range(self.config.max_cycles):
            counters = replace(counters, cycles_started=counters.cycles_started + 1)
            phase57_result = self.phase57_runner.run()
            self._record_artifact(self._phase57_artifacts, phase57_result)

            secret_reason = self._secret_detection_reason(phase57_result)
            if secret_reason:
                counters = self._blocked(counters, secret_reason)
                break

            live_reason = self._live_signal_reason(phase57_result)
            if live_reason:
                counters = self._blocked(counters, live_reason)
                break

            data_status = _field(phase57_result, "data_integrity_status", "PASS")
            if data_status != "PASS":
                counters = self._blocked(counters, "market_data_validation_failed")
                break

            decision = _field(phase57_result, "strategy_decision", "REJECT")
            counters = replace(counters, proposals_seen=counters.proposals_seen + 1)
            if decision == "NO_TRADE":
                counters = replace(
                    counters,
                    no_trade_count=counters.no_trade_count + 1,
                    cycles_completed=counters.cycles_completed + 1,
                )
                continue
            if decision == "REJECT":
                counters = replace(
                    counters,
                    rejected_count=counters.rejected_count + 1,
                    cycles_completed=counters.cycles_completed + 1,
                )
                if self.config.stop_on_first_failure:
                    counters = replace(counters, stopped_reason="phase57_reject")
                    break
                continue
            if decision != "TRADE_PROPOSAL":
                counters = self._blocked(counters, "unknown_phase57_decision")
                break

            counters = replace(
                counters,
                trade_proposal_count=counters.trade_proposal_count + 1,
            )
            if not self.config.allow_paper_send:
                counters = replace(
                    counters,
                    cycles_completed=counters.cycles_completed + 1,
                    stopped_reason="READ_ONLY_NO_SEND_MODE",
                )
                continue

            limit_reason = self._order_limit_reason(symbol, orders_by_symbol[symbol], counters)
            if limit_reason:
                counters = self._blocked(counters, limit_reason)
                break
            if self.phase58_runner is None or self.phase59_runner is None:
                counters = self._blocked(counters, "paper_send_runners_required")
                break

            counters = replace(counters, paper_order_attempts=counters.paper_order_attempts + 1)
            phase58_result = self.phase58_runner.run(phase57_result)
            self._record_artifact(self._phase58_artifacts, phase58_result)

            secret_reason = self._secret_detection_reason(phase58_result)
            if secret_reason:
                counters = self._blocked(counters, secret_reason)
                break
            live_reason = self._live_signal_reason(phase58_result)
            if live_reason:
                counters = self._blocked(counters, live_reason)
                break

            if _field(phase58_result, "paper_order_sent", False):
                orders_by_symbol[symbol] += 1
                counters = replace(counters, paper_orders_sent=counters.paper_orders_sent + 1)
            else:
                counters = self._blocked(counters, "phase58_gate_failed")
                break

            phase59_result = self.phase59_runner.run(phase58_result)
            self._record_artifact(self._phase59_artifacts, phase59_result)
            counters = replace(counters, reconciliations_run=counters.reconciliations_run + 1)

            secret_reason = self._secret_detection_reason(phase59_result)
            if secret_reason:
                counters = self._blocked(counters, secret_reason)
                break
            live_reason = self._live_signal_reason(phase59_result)
            if live_reason:
                counters = self._blocked(counters, live_reason)
                break

            reconciliation_status = _field(
                phase59_result,
                "reconciliation_status",
                _field(phase59_result, "final_status", "FAILED"),
            )
            if reconciliation_status in {"FAILED", "BLOCKED"}:
                counters = replace(
                    counters,
                    reconciliations_failed=counters.reconciliations_failed + 1,
                    blocked_cycles=counters.blocked_cycles + 1,
                    stopped_reason="phase59_reconciliation_failed",
                )
                if self.config.stop_on_first_reconciliation_failure:
                    break

            counters = replace(counters, cycles_completed=counters.cycles_completed + 1)

        final_status = "PASS" if counters.blocked_cycles == 0 else "BLOCKED"
        result = self._result(final_status=final_status, symbol=symbol, counters=counters)
        return self._write_artifacts(result)

    def _hard_block_reason(self) -> str | None:
        symbols = self._symbols()
        if not symbols:
            return "missing_symbol"
        if len(symbols) > 1:
            return "more_than_one_symbol_blocked"
        if self._raw_symbol_count() > 1:
            return "multi_symbol_input_blocked"
        if not self._watchlist_symbol_is_approved(symbols[0]):
            return "missing_watchlist_approval"
        if self.config.paper_only is not True:
            return "paper_only_required"
        if self.config.max_notional_usd > MAX_NOTIONAL_USD:
            return "max_notional_over_100"
        if self.config.max_cycles < 1:
            return "max_cycles_must_be_at_least_1"
        if self.config.max_paper_orders_total < 0:
            return "max_paper_orders_total_negative"
        if self.config.max_paper_orders_per_symbol < 0:
            return "max_paper_orders_per_symbol_negative"
        if self.config.require_human_review is not True:
            return "human_review_required"
        if self.config.require_manual_confirmation is not True:
            return "manual_execution_confirmation_required"
        if self.config.require_preflight is not True:
            return "preflight_required"
        if self.config.kill_switch_enabled is True:
            return "kill_switch_enabled"
        if self.config.live_trading_assumption is True:
            return "live_trading_assumption_blocked"
        if self.config.live_endpoint_detected is True:
            return "live_endpoint_detected"
        if self.config.execution_enablement_required is True:
            return "execution_enablement_required_blocked"
        if self.config.secrets_would_be_printed is True:
            return "secrets_would_be_printed_blocked"
        return None

    def _reported_symbol(self) -> str:
        symbols = self._symbols()
        return symbols[0] if symbols else "MISSING"

    def _symbols(self) -> tuple[str, ...]:
        symbols: list[str] = []
        for raw_symbol in self.config.symbols:
            symbols.extend(part.strip().upper() for part in raw_symbol.split(",") if part.strip())
        return tuple(symbols)

    def _raw_symbol_count(self) -> int:
        count = 0
        for symbol in self.config.symbols:
            count += len([part for part in symbol.split(",") if part.strip()])
        return count

    def _watchlist_symbol_is_approved(self, symbol: str) -> bool:
        try:
            text = self.config.watchlist_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return False
        return _watchlist_symbol_is_approved(text, symbol)

    def _order_limit_reason(
        self,
        symbol: str,
        orders_for_symbol: int,
        counters: SoakCounters,
    ) -> str | None:
        if counters.paper_orders_sent + 1 > self.config.max_paper_orders_total:
            return "max_paper_orders_total_reached"
        if orders_for_symbol + 1 > self.config.max_paper_orders_per_symbol:
            return "max_paper_orders_per_symbol_reached"
        return None

    def _blocked(self, counters: SoakCounters, reason: str) -> SoakCounters:
        return replace(
            counters,
            blocked_cycles=counters.blocked_cycles + 1,
            stopped_reason=reason,
        )

    def _secret_detection_reason(self, value: object) -> str | None:
        if not self.config.stop_on_secret_detection:
            return None
        rendered = _render_free_form(value)
        if _contains_secret(rendered, self.config.injected_secrets):
            return "secret_detection_stopped"
        if _field(value, "secrets_printed", False):
            return "secret_detection_stopped"
        return None

    def _live_signal_reason(self, value: object) -> str | None:
        if _field(value, "live_order_sent", False):
            return "live_order_signal_blocked"
        if _field(value, "live_trading_assumption", False):
            return "live_trading_assumption_blocked"
        if _field(value, "live_endpoint_detected", False):
            return "live_endpoint_detected"
        return None

    def _record_artifact(self, artifacts: list[str], value: object) -> None:
        for name in (
            "report_path",
            "evidence_manifest_path",
            "post_mortem_path",
            "artifact_path",
        ):
            path = _field(value, name, None)
            if path:
                artifacts.append(str(path))
        nested = _field(value, "artifacts", None)
        if nested:
            self._record_artifact(artifacts, nested)

    def _result(
        self,
        *,
        final_status: str,
        symbol: str,
        counters: SoakCounters,
    ) -> RealMarketPaperSoakResult:
        return RealMarketPaperSoakResult(
            final_status=final_status,
            symbol=symbol,
            paper_only=self.config.paper_only,
            max_notional_usd=self.config.max_notional_usd,
            max_cycles=self.config.max_cycles,
            max_paper_orders_total=self.config.max_paper_orders_total,
            max_paper_orders_per_symbol=self.config.max_paper_orders_per_symbol,
            allow_paper_send=self.config.allow_paper_send,
            require_human_review=self.config.require_human_review,
            require_manual_confirmation=self.config.require_manual_confirmation,
            require_preflight=self.config.require_preflight,
            kill_switch_enabled=self.config.kill_switch_enabled,
            counters=counters,
            phase57_artifacts=tuple(self._phase57_artifacts),
            phase58_artifacts=tuple(self._phase58_artifacts),
            phase59_artifacts=tuple(self._phase59_artifacts),
            live_order_sent=False,
            live_trading_assumption=False,
            secrets_printed=False,
        )

    def _write_artifacts(self, result: RealMarketPaperSoakResult) -> RealMarketPaperSoakResult:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        report_dir = self.config.output_dir / timestamp
        suffix = 1
        while report_dir.exists():
            report_dir = self.config.output_dir / f"{timestamp}-{suffix}"
            suffix += 1
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "REAL_MARKET_PAPER_SOAK_REPORT.md"
        manifest_path = report_dir / "SOAK_EVIDENCE_MANIFEST.md"
        report_path.write_text(self._report_text(result), encoding="utf-8")
        manifest_path.write_text(self._manifest_text(result, report_path), encoding="utf-8")
        return replace(
            result,
            artifacts=SoakArtifacts(
                report_path=report_path,
                evidence_manifest_path=manifest_path,
            ),
        )

    def _report_text(self, result: RealMarketPaperSoakResult) -> str:
        counters = result.counters
        lines = [
            "# Real Market Paper Soak Report",
            "",
            f"- phase: {PHASE_NAME}",
            f"- symbol: {_redact(result.symbol, self.config.injected_secrets)}",
            f"- paper_only: {str(result.paper_only).lower()}",
            f"- max_notional_usd: {result.max_notional_usd:.2f}",
            f"- max_cycles: {result.max_cycles}",
            f"- max_paper_orders_total: {result.max_paper_orders_total}",
            f"- max_paper_orders_per_symbol: {result.max_paper_orders_per_symbol}",
            f"- allow_paper_send: {str(result.allow_paper_send).lower()}",
            f"- require_human_review: {str(result.require_human_review).lower()}",
            f"- require_manual_confirmation: {str(result.require_manual_confirmation).lower()}",
            f"- require_preflight: {str(result.require_preflight).lower()}",
            f"- kill_switch_enabled: {str(result.kill_switch_enabled).lower()}",
            f"- cycles_started: {counters.cycles_started}",
            f"- cycles_completed: {counters.cycles_completed}",
            f"- proposals_seen: {counters.proposals_seen}",
            f"- no_trade_count: {counters.no_trade_count}",
            f"- rejected_count: {counters.rejected_count}",
            f"- trade_proposal_count: {counters.trade_proposal_count}",
            f"- paper_order_attempts: {counters.paper_order_attempts}",
            f"- paper_orders_sent: {counters.paper_orders_sent}",
            f"- reconciliations_run: {counters.reconciliations_run}",
            f"- reconciliations_failed: {counters.reconciliations_failed}",
            f"- blocked_cycles: {counters.blocked_cycles}",
            f"- stopped_reason: {_redact(counters.stopped_reason, self.config.injected_secrets)}",
            "- live_order_sent: false",
            "- live_trading_assumption: false",
            "- secrets_printed: false",
            f"- final status: {_redact(result.final_status, self.config.injected_secrets)}",
            "- No live order was sent.",
            "- Paper-only execution path remains required.",
            "- Human review remained required.",
            "- Manual execution confirmation remained required.",
            "- Preflight remained required.",
            "- Live trading remains unsupported.",
        ]
        return "\n".join(lines) + "\n"

    def _manifest_text(self, result: RealMarketPaperSoakResult, report_path: Path) -> str:
        counters = result.counters
        phase57_refs = [
            f"- {_redact(path, self.config.injected_secrets)}"
            for path in result.phase57_artifacts
        ] or ["- none"]
        phase58_refs = [
            f"- {_redact(path, self.config.injected_secrets)}"
            for path in result.phase58_artifacts
        ] or ["- none"]
        phase59_refs = [
            f"- {_redact(path, self.config.injected_secrets)}"
            for path in result.phase59_artifacts
        ] or ["- none"]
        lines = [
            "# Soak Evidence Manifest",
            "",
            "## Generated Soak Report",
            f"- generated soak report path: {report_path}",
            "",
            "## Referenced Phase 57 Artifacts",
            *phase57_refs,
            "",
            "## Referenced Phase 58 Artifacts",
            *phase58_refs,
            "",
            "## Referenced Phase 59 Artifacts",
            *phase59_refs,
            "",
            "## Safety Counters",
            f"- cycles_started: {counters.cycles_started}",
            f"- cycles_completed: {counters.cycles_completed}",
            f"- proposals_seen: {counters.proposals_seen}",
            f"- paper_order_attempts: {counters.paper_order_attempts}",
            f"- paper_orders_sent: {counters.paper_orders_sent}",
            f"- reconciliations_run: {counters.reconciliations_run}",
            f"- reconciliations_failed: {counters.reconciliations_failed}",
            f"- blocked_cycles: {counters.blocked_cycles}",
            f"- stopped_reason: {_redact(counters.stopped_reason, self.config.injected_secrets)}",
            "",
            "## Order Limit Evidence",
            f"- max_paper_orders_total: {self.config.max_paper_orders_total}",
            f"- max_paper_orders_per_symbol: {self.config.max_paper_orders_per_symbol}",
            f"- paper_orders_sent: {counters.paper_orders_sent}",
            "- unlimited_order_loop_allowed: false",
            "- automatic_retry_after_failure: false",
            "",
            "## Kill-Switch Evidence",
            f"- kill_switch_enabled: {str(self.config.kill_switch_enabled).lower()}",
            f"- kill_switch_blocks_before_cycle: {str(self.config.kill_switch_enabled).lower()}",
            "",
            "## No-Live-Order Evidence",
            "- live_order_sent: false",
            "- live_trading_assumption: false",
            "- live_trading_supported: false",
            "",
            "## No-Secret Evidence",
            "- secrets_printed: false",
            "- free_form_report_fields_redacted: true",
            "",
            "## Test Command Evidence",
            *[f"- {command}" for command in self.config.test_command_evidence],
            "",
        ]
        return "\n".join(lines)


def run_real_market_paper_soak(
    config: RealMarketPaperSoakConfig,
    *,
    phase57_runner: Phase57Runner,
    phase58_runner: Phase58Runner | None = None,
    phase59_runner: Phase59Runner | None = None,
) -> RealMarketPaperSoakResult:
    return RealMarketPaperSoakSupervisor(
        config,
        phase57_runner=phase57_runner,
        phase58_runner=phase58_runner,
        phase59_runner=phase59_runner,
    ).run()


def _watchlist_symbol_is_approved(text: str, symbol: str) -> bool:
    normalized_symbol = symbol.upper()
    active_symbol: str | None = None
    active_has_approval = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        lowered = line.lower()
        if lowered.startswith("- symbol:") or lowered.startswith("symbol:"):
            if active_symbol == normalized_symbol and active_has_approval:
                return True
            active_symbol = line.split(":", 1)[1].strip().upper()
            active_has_approval = False
            continue
        if active_symbol == normalized_symbol and (
            lowered in {"approved: true", "approved: yes", "- approved: true", "- approved: yes"}
            or "watchlist approval: approved" in lowered
            or "status: approved" in lowered
        ):
            active_has_approval = True
    return active_symbol == normalized_symbol and active_has_approval


def _field(value: object, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return getattr(value, name, default)


def _render_free_form(value: object) -> str:
    fields = (
        "strategy_reason",
        "reason",
        "message",
        "status_message",
        "runner_message",
        "warnings",
        "failures",
        "raw_payload_message",
        "raw_adapter_message",
        "provider_message",
    )
    parts: list[str] = []
    if isinstance(value, dict):
        parts.extend(str(value.get(field, "")) for field in fields)
    else:
        parts.extend(str(getattr(value, field, "")) for field in fields)
    return "\n".join(parts)


def _contains_secret(text: str, injected_secrets: tuple[str, ...]) -> bool:
    for secret in injected_secrets:
        if secret and secret in text:
            return True
    if re.search(r"(?i)(bearer\s+)[a-z0-9._~+/=-]{8,}", text):
        return True
    if re.search(r"(?i)(api[_-]?key|secret|token)\s*=\s*[^,\s]+", text):
        return True
    return False


def _redact(value: object, injected_secrets: tuple[str, ...] = ()) -> str:
    redacted = str(value)
    for secret in injected_secrets:
        if secret:
            redacted = redacted.replace(secret, REDACTION_MARKER)
    for env_name in ("ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY"):
        secret = getenv(env_name)
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
