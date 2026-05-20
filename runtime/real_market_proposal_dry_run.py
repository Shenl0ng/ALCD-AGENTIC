from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import os
from pathlib import Path
from typing import Protocol

from market_data import (
    MAX_FRESHNESS_AGE,
    MarketDataAdapter,
    MarketDataSnapshot,
    RealMarketDataAdapter,
    RealMarketDataConfig,
    validate_market_data,
)


REPORT_ROOT = Path("reports/real_market_proposal_dry_run")
WATCHLIST_PATH = Path("memory/watchlist.md")
BLOCKING_ENV_FLAGS = (
    "PAPER_ORDER_EXECUTION_ENABLED",
    "PAPER_AUTOMATED_SEND_ENABLED",
    "PAPER_SOAK_TEST_ACCELERATED",
)


class RealMarketProposalDryRunError(RuntimeError):
    pass


class DryRunMarketDataAdapter(Protocol):
    def load_snapshot(self, routine_name: str) -> MarketDataSnapshot:
        """Load a read-only market data snapshot for dry-run proposal evaluation."""


@dataclass(frozen=True)
class RealMarketProposalDryRunConfig:
    symbols: tuple[str, ...]
    base_url: str = "https://data.alpaca.markets"
    timeframe: str = "1m"
    session: str = "market_open"
    watchlist_path: Path = WATCHLIST_PATH
    report_root: Path = REPORT_ROOT
    require_spread: bool = True
    require_volume: bool = True
    max_age: timedelta = MAX_FRESHNESS_AGE
    as_of: datetime | None = None
    allow_trade_proposal: bool = False
    api_key_id: str | None = None
    api_secret_key: str | None = None


@dataclass(frozen=True)
class DryRunProposal:
    symbol: str
    source: str
    timestamp: str
    timeframe: str
    session: str
    market_data_validation_status: str
    strategy_decision: str
    reason: str
    paper_trading_only: bool = True
    executable: bool = False
    broker_execution_readiness: bool = False
    paper_order_request_created: bool = False
    human_review_requested: bool = False
    finalized_request_created: bool = False
    manual_confirmation_requested: bool = False
    paper_send_preflight_run: bool = False
    paper_order_sent: bool = False
    live_trading_assumption: bool = False


@dataclass(frozen=True)
class RealMarketProposalDryRunResult:
    final_status: str
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
    violations: tuple[str, ...]
    evaluation_status: str = "NOT_RUN"
    evaluation_gate_status: str = "NOT_RUN"
    negative_regression_status: str = "NOT_RUN"
    proposal: DryRunProposal | None = None
    report_path: Path | None = None
    paper_order_request_created: bool = False
    human_review_requested: bool = False
    finalized_request_created: bool = False
    manual_confirmation_requested: bool = False
    paper_send_preflight_run: bool = False
    broker_execution_readiness: bool = False
    paper_order_sent: bool = False
    live_trading_assumption: bool = False
    secrets_printed: bool = False
    order_api_used: bool = False


class RealMarketProposalDryRunRunner:
    def __init__(
        self,
        config: RealMarketProposalDryRunConfig,
        *,
        market_data_adapter: DryRunMarketDataAdapter | None = None,
        environ: dict[str, str] | None = None,
    ) -> None:
        self.config = config
        self.environ = environ if environ is not None else os.environ
        self.market_data_adapter = market_data_adapter

    def run(self) -> RealMarketProposalDryRunResult:
        symbol = "MISSING"
        try:
            symbol = self._single_symbol()
            self._block_execution_flags()
            self._require_watchlist_approval(symbol)
            adapter = self.market_data_adapter or self._real_adapter()
            snapshot = adapter.load_snapshot(self.config.session)
            validation = validate_market_data(
                snapshot,
                as_of=self.config.as_of or datetime.now(UTC),
                max_age=self.config.max_age,
                require_spread=self.config.require_spread,
                require_volume=self.config.require_volume,
            )
            if not validation.passed:
                result = self._result_from_snapshot(
                    snapshot,
                    "REJECT",
                    "REJECT",
                    "Data Integrity rejected market data: "
                    + ",".join(validation.violations),
                    validation,
                    "APPROVED",
                )
                return self._write_report(result)

            decision, reason = self._strategy_decision(snapshot)
            proposal = None
            if decision == "TRADE_PROPOSAL":
                proposal = DryRunProposal(
                    symbol=snapshot.symbol or "MISSING",
                    source=snapshot.source or "MISSING",
                    timestamp=snapshot.timestamp.isoformat()
                    if snapshot.timestamp
                    else "MISSING",
                    timeframe=snapshot.timeframe or "MISSING",
                    session=snapshot.session or "MISSING",
                    market_data_validation_status=validation.data_integrity_status,
                    strategy_decision=decision,
                    reason=reason,
                )
            result = self._result_from_snapshot(
                snapshot,
                decision,
                decision,
                reason,
                validation,
                "APPROVED",
                proposal=proposal,
            )
            return self._write_report(result)
        except RealMarketProposalDryRunError as exc:
            result = RealMarketProposalDryRunResult(
                final_status="REJECT",
                strategy_decision="REJECT",
                strategy_reason=str(exc),
                symbol=symbol,
                source="MISSING",
                timestamp="MISSING",
                timeframe=self.config.timeframe or "MISSING",
                session=self.config.session or "MISSING",
                watchlist_approval_status="REJECTED",
                freshness_status="UNKNOWN",
                completeness_status="UNKNOWN",
                data_integrity_status="FAIL",
                violations=(str(exc),),
            )
            return self._write_report(result)
        except Exception:
            result = RealMarketProposalDryRunResult(
                final_status="REJECT",
                strategy_decision="REJECT",
                strategy_reason="Market data adapter blocked dry run.",
                symbol=symbol,
                source="MISSING",
                timestamp="MISSING",
                timeframe=self.config.timeframe or "MISSING",
                session=self.config.session or "MISSING",
                watchlist_approval_status="APPROVED",
                freshness_status="UNKNOWN",
                completeness_status="UNKNOWN",
                data_integrity_status="FAIL",
                violations=("market_data_adapter_blocked",),
            )
            return self._write_report(result)

    def _single_symbol(self) -> str:
        symbols = tuple(symbol.strip().upper() for symbol in self.config.symbols if symbol.strip())
        if not symbols:
            raise RealMarketProposalDryRunError("missing_symbol")
        if len(symbols) != 1:
            raise RealMarketProposalDryRunError("more_than_one_symbol_blocked")
        return symbols[0]

    def _block_execution_flags(self) -> None:
        enabled = [
            name
            for name in BLOCKING_ENV_FLAGS
            if self.environ.get(name, "").strip().lower() == "true"
        ]
        if enabled:
            raise RealMarketProposalDryRunError(
                "execution_flag_enabled_for_dry_run: " + ",".join(enabled)
            )

    def _require_watchlist_approval(self, symbol: str) -> None:
        try:
            text = self.config.watchlist_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise RealMarketProposalDryRunError("watchlist_missing") from exc
        if not _watchlist_symbol_is_approved(text, symbol):
            raise RealMarketProposalDryRunError("missing_watchlist_approval")

    def _real_adapter(self) -> MarketDataAdapter:
        return RealMarketDataAdapter(
            RealMarketDataConfig(
                symbols=self.config.symbols,
                base_url=self.config.base_url,
                timeframe=self.config.timeframe,
                session=self.config.session,
                watchlist_path=self.config.watchlist_path,
                require_spread=self.config.require_spread,
                require_volume=self.config.require_volume,
                max_age=self.config.max_age,
                as_of=self.config.as_of,
                api_key_id=self.config.api_key_id,
                api_secret_key=self.config.api_secret_key,
            )
        )

    def _strategy_decision(self, snapshot: MarketDataSnapshot) -> tuple[str, str]:
        if not self.config.allow_trade_proposal:
            return (
                "NO_TRADE",
                "Dry-run strategy evidence is incomplete; default decision is NO_TRADE.",
            )
        if (
            snapshot.last_price is None
            or not snapshot.bar_available
            or not snapshot.spread_available
            or not snapshot.volume_available
        ):
            return (
                "NO_TRADE",
                "Required market fields for a dry-run proposal are unavailable.",
            )
        return (
            "TRADE_PROPOSAL",
            "Validated read-only market data met conservative dry-run strategy checks.",
        )

    def _result_from_snapshot(
        self,
        snapshot: MarketDataSnapshot,
        final_status: str,
        strategy_decision: str,
        strategy_reason: str,
        validation,
        watchlist_status: str,
        *,
        proposal: DryRunProposal | None = None,
    ) -> RealMarketProposalDryRunResult:
        return RealMarketProposalDryRunResult(
            final_status=final_status,
            strategy_decision=strategy_decision,
            strategy_reason=strategy_reason,
            symbol=snapshot.symbol or "MISSING",
            source=snapshot.source or "MISSING",
            timestamp=snapshot.timestamp.isoformat() if snapshot.timestamp else "MISSING",
            timeframe=snapshot.timeframe or "MISSING",
            session=snapshot.session or "MISSING",
            watchlist_approval_status=watchlist_status,
            freshness_status=validation.freshness_status,
            completeness_status=validation.completeness_status,
            data_integrity_status=validation.data_integrity_status,
            violations=tuple(validation.violations),
            proposal=proposal,
        )

    def _write_report(
        self,
        result: RealMarketProposalDryRunResult,
    ) -> RealMarketProposalDryRunResult:
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        report_dir = self.config.report_root / timestamp
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / "REAL_MARKET_PROPOSAL_DRY_RUN_REPORT.md"
        lines = [
            "# Real Market Proposal Dry Run Report",
            "",
            "- phase: Phase 57 Real Market-Driven Proposal Dry Run",
            f"- symbol: {result.symbol}",
            f"- source: {result.source}",
            f"- timestamp: {result.timestamp}",
            f"- timeframe: {result.timeframe}",
            f"- session: {result.session}",
            f"- watchlist approval status: {result.watchlist_approval_status}",
            f"- freshness status: {result.freshness_status}",
            f"- completeness status: {result.completeness_status}",
            f"- data integrity status: {result.data_integrity_status}",
            f"- strategy decision: {result.strategy_decision}",
            f"- strategy reason: {_redact(result.strategy_reason)}",
            f"- evaluation status: {result.evaluation_status}",
            f"- evaluation gate status: {result.evaluation_gate_status}",
            f"- negative regression status: {result.negative_regression_status}",
            "- paper_order_request_created: false",
            "- human_review_requested: false",
            "- finalized_request_created: false",
            "- manual_confirmation_requested: false",
            "- paper_send_preflight_run: false",
            "- broker_execution_readiness: false",
            "- paper_order_sent: false",
            "- live_trading_assumption: false",
            "- secrets_printed: false",
            "- order_api_used: false",
            f"- final status: {result.final_status}",
            "- No order was sent.",
            "- No paper order candidate was created.",
            "- No human review item was created.",
            "- Live trading remains unsupported.",
            "- This run is read-only and dry-run only.",
        ]
        report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return RealMarketProposalDryRunResult(
            **{**result.__dict__, "report_path": report_path}
        )


def run_real_market_proposal_dry_run(
    config: RealMarketProposalDryRunConfig,
    *,
    market_data_adapter: DryRunMarketDataAdapter | None = None,
    environ: dict[str, str] | None = None,
) -> RealMarketProposalDryRunResult:
    return RealMarketProposalDryRunRunner(
        config,
        market_data_adapter=market_data_adapter,
        environ=environ,
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


def _redact(text: str) -> str:
    redacted = text
    for env_name in ("ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY"):
        value = os.environ.get(env_name)
        if value:
            redacted = redacted.replace(value, "[REDACTED]")
    return redacted
