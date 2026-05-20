from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
import os
from pathlib import Path
import re
from typing import Protocol


REPORT_ROOT = Path("reports/real_market_paper_order_run")
WATCHLIST_PATH = Path("memory/watchlist.md")
MAX_NOTIONAL_USD = 100.0
REDACTION_MARKER = "[REDACTED]"


class RealMarketPaperOrderRunError(RuntimeError):
    pass


class PaperOrderAdapter(Protocol):
    def send_paper_order(self, order: "PaperOrderRequest") -> "PaperOrderResult":
        """Send a paper-only order after all Phase 58 gates pass."""


@dataclass(frozen=True)
class Phase57Signal:
    strategy_decision: str
    strategy_reason: str
    symbol: str
    source: str
    timestamp: str
    timeframe: str
    session: str
    watchlist_approval_status: str
    freshness_status: str
    completeness_status: str
    data_integrity_status: str
    spread_available: bool
    volume_available: bool
    live_trading_assumption: bool = False
    broker_execution_readiness: bool = False
    live_endpoint_detected: bool = False
    non_paper_account_assumption: bool = False
    order_endpoint_live: bool = False


@dataclass(frozen=True)
class RealMarketPaperOrderRunConfig:
    symbols: tuple[str, ...]
    max_notional_usd: float
    paper_only: bool
    human_review_approved: bool
    manual_execution_confirmed: bool
    allow_paper_send: bool
    evaluation_gate_status: str
    negative_regression_status: str
    preflight_status: str
    watchlist_path: Path = WATCHLIST_PATH
    report_root: Path = REPORT_ROOT
    require_spread: bool = True
    require_volume: bool = True
    order_side: str = "buy"
    order_type: str = "limit"
    time_in_force: str = "day"
    live_trading_assumption: bool = False
    broker_execution_readiness: bool = False
    live_endpoint_detected: bool = False
    non_paper_account_assumption: bool = False
    order_endpoint_live: bool = False


@dataclass(frozen=True)
class PaperOrderCandidate:
    source_phase: str
    symbol: str
    max_notional_usd: float
    paper_only: bool
    live_trading_assumption: bool
    executable_before_human_review: bool
    human_review_required: bool
    manual_confirmation_required: bool


@dataclass(frozen=True)
class FinalizedPaperOrderRequest:
    symbol: str
    max_notional_usd: float
    paper_only: bool
    broker_execution_readiness: bool
    live_trading_assumption: bool
    order_side: str
    order_type: str
    time_in_force: str


@dataclass(frozen=True)
class PaperOrderRequest:
    symbol: str
    notional_usd: float
    paper_only: bool
    order_side: str
    order_type: str
    time_in_force: str
    live_trading_assumption: bool = False


@dataclass(frozen=True)
class PaperOrderResult:
    accepted: bool
    paper_order_id: str | None
    reconciliation_status: str
    paper_only: bool
    live_order_sent: bool = False


@dataclass(frozen=True)
class RealMarketPaperOrderRunResult:
    final_status: str
    reason: str
    symbol: str
    source: str
    timestamp: str
    timeframe: str
    session: str
    watchlist_approval_status: str
    freshness_status: str
    completeness_status: str
    data_integrity_status: str
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
    secrets_printed: bool
    reconciliation_status: str
    report_path: Path | None = None


class RealMarketPaperOrderRunner:
    def __init__(
        self,
        config: RealMarketPaperOrderRunConfig,
        *,
        phase57_signal: Phase57Signal,
        paper_order_adapter: PaperOrderAdapter,
    ) -> None:
        self.config = config
        self.phase57_signal = phase57_signal
        self.paper_order_adapter = paper_order_adapter

    def run(self) -> RealMarketPaperOrderRunResult:
        symbol = self._reported_symbol()
        try:
            symbol = self._single_symbol()
            self._require_watchlist_approval(symbol)
            self._require_static_safety_gates()
            self._require_phase57_signal(symbol)
            candidate = self._create_candidate(symbol)
            finalized = self._create_finalized_request(candidate)
            order = self._paper_order_from_finalized(finalized)
            paper_result = self.paper_order_adapter.send_paper_order(order)
            self._require_paper_result(paper_result)
            result = self._base_result(
                final_status="PAPER_ORDER_SENT",
                reason="All Phase 58 paper-only gates passed.",
                symbol=symbol,
                candidate_created=True,
                finalized_request_created=True,
                broker_execution_readiness=True,
                order_api_used=True,
                paper_order_sent=True,
                reconciliation_status=paper_result.reconciliation_status,
            )
            return self._write_report(result)
        except RealMarketPaperOrderRunError as exc:
            result = self._base_result(
                final_status="BLOCKED",
                reason=str(exc),
                symbol=symbol,
                candidate_created=False,
                finalized_request_created=False,
                broker_execution_readiness=False,
                order_api_used=False,
                paper_order_sent=False,
                reconciliation_status="NOT_RUN",
            )
            return self._write_report(result)

    def _reported_symbol(self) -> str:
        symbols = tuple(symbol.strip().upper() for symbol in self.config.symbols if symbol.strip())
        return symbols[0] if symbols else "MISSING"

    def _single_symbol(self) -> str:
        symbols = tuple(symbol.strip().upper() for symbol in self.config.symbols if symbol.strip())
        if not symbols:
            raise RealMarketPaperOrderRunError("missing_symbol")
        if len(symbols) != 1:
            raise RealMarketPaperOrderRunError("more_than_one_symbol_blocked")
        return symbols[0]

    def _require_watchlist_approval(self, symbol: str) -> None:
        try:
            text = self.config.watchlist_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise RealMarketPaperOrderRunError("watchlist_missing") from exc
        if not _watchlist_symbol_is_approved(text, symbol):
            raise RealMarketPaperOrderRunError("missing_watchlist_approval")

    def _require_static_safety_gates(self) -> None:
        if self.config.max_notional_usd > MAX_NOTIONAL_USD:
            raise RealMarketPaperOrderRunError("max_notional_over_100")
        if self.config.paper_only is not True:
            raise RealMarketPaperOrderRunError("paper_only_required")
        if self.config.human_review_approved is not True:
            raise RealMarketPaperOrderRunError("human_review_approval_required")
        if self.config.manual_execution_confirmed is not True:
            raise RealMarketPaperOrderRunError("manual_execution_confirmation_required")
        if self.config.allow_paper_send is not True:
            raise RealMarketPaperOrderRunError("allow_paper_send_required")
        if self.config.live_trading_assumption:
            raise RealMarketPaperOrderRunError("live_trading_assumption_blocked")
        if self.config.broker_execution_readiness:
            raise RealMarketPaperOrderRunError("broker_execution_readiness_before_preflight")
        if self.config.live_endpoint_detected:
            raise RealMarketPaperOrderRunError("live_endpoint_detected")
        if self.config.non_paper_account_assumption:
            raise RealMarketPaperOrderRunError("non_paper_account_assumption")
        if self.config.order_endpoint_live:
            raise RealMarketPaperOrderRunError("live_order_endpoint_detected")
        if self.config.evaluation_gate_status != "EVALUATION_GATE_PASSED":
            raise RealMarketPaperOrderRunError("evaluation_gate_failed")
        if self.config.negative_regression_status != "PASS":
            raise RealMarketPaperOrderRunError("negative_regression_failed")
        if self.config.preflight_status != "PAPER_ORDER_SEND_ALLOWED":
            raise RealMarketPaperOrderRunError("preflight_failed")

    def _require_phase57_signal(self, symbol: str) -> None:
        signal = self.phase57_signal
        if signal.symbol.strip().upper() != symbol:
            raise RealMarketPaperOrderRunError("phase57_symbol_mismatch")
        if signal.watchlist_approval_status != "APPROVED":
            raise RealMarketPaperOrderRunError("phase57_watchlist_not_approved")
        if signal.strategy_decision == "NO_TRADE":
            raise RealMarketPaperOrderRunError("phase57_no_trade")
        if signal.strategy_decision == "REJECT":
            raise RealMarketPaperOrderRunError("phase57_reject")
        if signal.strategy_decision != "TRADE_PROPOSAL":
            raise RealMarketPaperOrderRunError("phase57_trade_proposal_required")
        if signal.data_integrity_status != "PASS":
            raise RealMarketPaperOrderRunError("data_integrity_failed")
        if signal.freshness_status != "FRESH":
            raise RealMarketPaperOrderRunError("freshness_failed")
        if signal.completeness_status != "COMPLETE":
            raise RealMarketPaperOrderRunError("completeness_failed")
        if not signal.timestamp or signal.timestamp == "MISSING":
            raise RealMarketPaperOrderRunError("missing_timestamp")
        if not signal.symbol or signal.symbol == "MISSING":
            raise RealMarketPaperOrderRunError("missing_symbol")
        if not signal.timeframe or signal.timeframe == "MISSING":
            raise RealMarketPaperOrderRunError("missing_timeframe")
        if not signal.session or signal.session == "MISSING":
            raise RealMarketPaperOrderRunError("missing_session")
        if self.config.require_spread and not signal.spread_available:
            raise RealMarketPaperOrderRunError("missing_required_spread")
        if self.config.require_volume and not signal.volume_available:
            raise RealMarketPaperOrderRunError("missing_required_volume")
        if signal.live_endpoint_detected:
            raise RealMarketPaperOrderRunError("live_endpoint_detected")
        if signal.live_trading_assumption:
            raise RealMarketPaperOrderRunError("live_trading_assumption_blocked")
        if signal.broker_execution_readiness:
            raise RealMarketPaperOrderRunError("broker_execution_readiness_before_preflight")
        if signal.non_paper_account_assumption:
            raise RealMarketPaperOrderRunError("non_paper_account_assumption")
        if signal.order_endpoint_live:
            raise RealMarketPaperOrderRunError("live_order_endpoint_detected")

    def _create_candidate(self, symbol: str) -> PaperOrderCandidate:
        return PaperOrderCandidate(
            source_phase="Phase 58",
            symbol=symbol,
            max_notional_usd=self.config.max_notional_usd,
            paper_only=True,
            live_trading_assumption=False,
            executable_before_human_review=False,
            human_review_required=True,
            manual_confirmation_required=True,
        )

    def _create_finalized_request(
        self,
        candidate: PaperOrderCandidate,
    ) -> FinalizedPaperOrderRequest:
        return FinalizedPaperOrderRequest(
            symbol=candidate.symbol,
            max_notional_usd=candidate.max_notional_usd,
            paper_only=True,
            broker_execution_readiness=False,
            live_trading_assumption=False,
            order_side=self.config.order_side,
            order_type=self.config.order_type,
            time_in_force=self.config.time_in_force,
        )

    def _paper_order_from_finalized(
        self,
        finalized: FinalizedPaperOrderRequest,
    ) -> PaperOrderRequest:
        if not finalized.paper_only:
            raise RealMarketPaperOrderRunError("requested_order_not_paper_only")
        if finalized.max_notional_usd > MAX_NOTIONAL_USD:
            raise RealMarketPaperOrderRunError("max_notional_over_100")
        if finalized.live_trading_assumption:
            raise RealMarketPaperOrderRunError("live_trading_assumption_blocked")
        return PaperOrderRequest(
            symbol=finalized.symbol,
            notional_usd=finalized.max_notional_usd,
            paper_only=True,
            order_side=finalized.order_side,
            order_type=finalized.order_type,
            time_in_force=finalized.time_in_force,
            live_trading_assumption=False,
        )

    def _require_paper_result(self, result: PaperOrderResult) -> None:
        if not result.paper_only:
            raise RealMarketPaperOrderRunError("paper_adapter_returned_non_paper_result")
        if result.live_order_sent:
            raise RealMarketPaperOrderRunError("live_order_sent")
        if not result.accepted:
            raise RealMarketPaperOrderRunError("paper_order_not_accepted")

    def _base_result(
        self,
        *,
        final_status: str,
        reason: str,
        symbol: str,
        candidate_created: bool,
        finalized_request_created: bool,
        broker_execution_readiness: bool,
        order_api_used: bool,
        paper_order_sent: bool,
        reconciliation_status: str,
    ) -> RealMarketPaperOrderRunResult:
        signal = self.phase57_signal
        return RealMarketPaperOrderRunResult(
            final_status=final_status,
            reason=reason,
            symbol=symbol,
            source=signal.source,
            timestamp=signal.timestamp,
            timeframe=signal.timeframe,
            session=signal.session,
            watchlist_approval_status=signal.watchlist_approval_status,
            freshness_status=signal.freshness_status,
            completeness_status=signal.completeness_status,
            data_integrity_status=signal.data_integrity_status,
            strategy_decision=signal.strategy_decision,
            strategy_reason=signal.strategy_reason,
            evaluation_gate_status=self.config.evaluation_gate_status,
            negative_regression_status=self.config.negative_regression_status,
            candidate_created=candidate_created,
            human_review_approved=self.config.human_review_approved,
            finalized_request_created=finalized_request_created,
            manual_execution_confirmed=self.config.manual_execution_confirmed,
            preflight_status=self.config.preflight_status,
            max_notional_usd=self.config.max_notional_usd,
            paper_only=self.config.paper_only,
            broker_execution_readiness=broker_execution_readiness,
            order_api_used=order_api_used,
            paper_order_sent=paper_order_sent,
            live_order_sent=False,
            live_trading_assumption=False,
            secrets_printed=False,
            reconciliation_status=reconciliation_status,
        )

    def _write_report(
        self,
        result: RealMarketPaperOrderRunResult,
    ) -> RealMarketPaperOrderRunResult:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        report_dir = self.config.report_root / timestamp
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "REAL_MARKET_PAPER_ORDER_RUN_REPORT.md"
        lines = [
            "# Real Market Paper Order Run Report",
            "",
            "- phase: Phase 58 Real Market-Driven Paper Send",
            f"- symbol: {_redact_report_text(result.symbol)}",
            f"- source: {_redact_report_text(result.source)}",
            f"- timestamp: {_redact_report_text(result.timestamp)}",
            f"- timeframe: {_redact_report_text(result.timeframe)}",
            f"- session: {_redact_report_text(result.session)}",
            f"- watchlist approval status: {_redact_report_text(result.watchlist_approval_status)}",
            f"- freshness status: {_redact_report_text(result.freshness_status)}",
            f"- completeness status: {_redact_report_text(result.completeness_status)}",
            f"- data integrity status: {_redact_report_text(result.data_integrity_status)}",
            f"- strategy decision: {_redact_report_text(result.strategy_decision)}",
            f"- strategy reason: {_redact_report_text(result.strategy_reason)}",
            f"- evaluation gate status: {_redact_report_text(result.evaluation_gate_status)}",
            f"- negative regression status: {_redact_report_text(result.negative_regression_status)}",
            f"- candidate_created: {str(result.candidate_created).lower()}",
            f"- human_review_approved: {str(result.human_review_approved).lower()}",
            f"- finalized_request_created: {str(result.finalized_request_created).lower()}",
            f"- manual_execution_confirmed: {str(result.manual_execution_confirmed).lower()}",
            f"- preflight_status: {_redact_report_text(result.preflight_status)}",
            f"- max_notional_usd: {result.max_notional_usd:.2f}",
            f"- paper_only: {str(result.paper_only).lower()}",
            f"- broker_execution_readiness: {str(result.broker_execution_readiness).lower()}",
            f"- order_api_used: {str(result.order_api_used).lower()}",
            f"- paper_order_sent: {str(result.paper_order_sent).lower()}",
            "- live_order_sent: false",
            "- live_trading_assumption: false",
            "- secrets_printed: false",
            f"- reconciliation_status: {_redact_report_text(result.reconciliation_status)}",
            f"- final status: {_redact_report_text(result.final_status)}",
            f"- reason: {_redact_report_text(result.reason)}",
            "- No live order was sent.",
            "- Paper-only execution path was used.",
            "- Human review remained required.",
            "- Manual execution confirmation remained required.",
            "- Live trading remains unsupported.",
        ]
        report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return replace(result, report_path=report_path)


def run_real_market_paper_order(
    config: RealMarketPaperOrderRunConfig,
    *,
    phase57_signal: Phase57Signal,
    paper_order_adapter: PaperOrderAdapter,
) -> RealMarketPaperOrderRunResult:
    return RealMarketPaperOrderRunner(
        config,
        phase57_signal=phase57_signal,
        paper_order_adapter=paper_order_adapter,
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


def _redact_report_text(value: object) -> str:
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
