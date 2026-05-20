from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from alpaca_paper_account import PaperAccountSnapshot, default_mock_snapshot
from alpaca_paper_order_adapter import (
    MOCKED_PAPER_SEND,
    PAPER_ORDER_SUBMITTED,
    AlpacaPaperOrderAdapter,
    PaperOrderAdapterConfig,
    PaperOrderExecutionResult,
    RecordingMockPaperClient,
)
from human_approval import JournalEntry, commit_journal_entry
from paper_execution_dry_run import confirmed_manual_execution
from paper_order_request import deterministic_valid_request


RECONCILIATION_PENDING = "RECONCILIATION_PENDING"
RECONCILIATION_MATCHED = "RECONCILIATION_MATCHED"
RECONCILIATION_MISMATCH = "RECONCILIATION_MISMATCH"
RECONCILIATION_ORDER_NOT_FOUND = "RECONCILIATION_ORDER_NOT_FOUND"
RECONCILIATION_READ_ERROR = "RECONCILIATION_READ_ERROR"
RECONCILIATION_BLOCKED = "RECONCILIATION_BLOCKED"
OBSERVE_AND_JOURNAL_ONLY = "OBSERVE_AND_JOURNAL_ONLY"


class PaperOrderStatusReadOnlyAdapter(Protocol):
    def read_account_and_positions_only(self) -> PaperAccountSnapshot:
        """Read current paper account and positions without listing orders."""

    def read_paper_order_status(self, order_id: str) -> Mapping[str, Any] | None:
        """Read one Alpaca paper order status by id."""


@dataclass(frozen=True)
class PaperOrderReconciliationReport:
    reconciliation_id: str
    execution_result_id: str | None
    paper_order_request_id: str | None
    alpaca_order_id: str | None
    checked_at: str
    expected_values: Mapping[str, object]
    observed_values: Mapping[str, object]
    account_mode: str | None
    order_status: str | None
    match_status: str
    mismatch_reasons: tuple[str, ...]
    final_reconciliation_status: str
    journal_entry_reference: str | None
    adlc_compliance_reference: str | None
    default_action: str = OBSERVE_AND_JOURNAL_ONLY

    def as_dict(self) -> dict[str, object]:
        return {
            "reconciliation_id": self.reconciliation_id,
            "execution_result_id": self.execution_result_id,
            "paper_order_request_id": self.paper_order_request_id,
            "alpaca_order_id": self.alpaca_order_id,
            "checked_at": self.checked_at,
            "expected_values": dict(self.expected_values),
            "observed_values": dict(self.observed_values),
            "account_mode": self.account_mode,
            "order_status": self.order_status,
            "match_status": self.match_status,
            "mismatch_reasons": list(self.mismatch_reasons),
            "final_reconciliation_status": self.final_reconciliation_status,
            "journal_entry_reference": self.journal_entry_reference,
            "adlc_compliance_reference": self.adlc_compliance_reference,
            "default_action": self.default_action,
        }


@dataclass(frozen=True)
class PaperOrderReconciliationResult:
    report: PaperOrderReconciliationReport
    journal_entry: JournalEntry | None

    def as_dict(self) -> dict[str, object]:
        return {
            "report": self.report.as_dict(),
            "journal_entry": self.journal_entry.as_dict() if self.journal_entry else None,
        }


class StaticPaperOrderStatusReadOnlyAdapter:
    def __init__(
        self,
        *,
        order_status: Mapping[str, Any] | None,
        snapshot: PaperAccountSnapshot | None = None,
        read_error: Exception | None = None,
    ) -> None:
        self._order_status = order_status
        self._snapshot = snapshot or default_mock_snapshot()
        self._read_error = read_error
        self.order_reads = 0
        self.snapshot_reads = 0
        self.account_positions_reads = 0

    def read_snapshot(self) -> PaperAccountSnapshot:
        self.snapshot_reads += 1
        if self._read_error is not None:
            raise self._read_error
        return self._snapshot

    def read_account_and_positions_only(self) -> PaperAccountSnapshot:
        self.account_positions_reads += 1
        if self._read_error is not None:
            raise self._read_error
        return PaperAccountSnapshot(
            account=self._snapshot.account,
            positions=self._snapshot.positions,
            existing_orders=(),
            paper_mode=self._snapshot.paper_mode,
        )

    def read_paper_order_status(self, order_id: str) -> Mapping[str, Any] | None:
        self.order_reads += 1
        if self._read_error is not None:
            raise self._read_error
        return self._order_status


class PaperOrderReconciler:
    def pending(
        self,
        execution_result: PaperOrderExecutionResult | None,
        *,
        previous_journal_entry: JournalEntry | None,
    ) -> PaperOrderReconciliationResult:
        if execution_result is None:
            report = _report(
                None,
                final_status=RECONCILIATION_BLOCKED,
                match_status=RECONCILIATION_BLOCKED,
                mismatch_reasons=("missing Phase 9 execution result",),
                journal_entry_reference=_journal_reference(previous_journal_entry),
            )
            return PaperOrderReconciliationResult(report=report, journal_entry=None)
        report = _report(
            execution_result,
            final_status=RECONCILIATION_PENDING,
            match_status=RECONCILIATION_PENDING,
            mismatch_reasons=(),
            journal_entry_reference=_journal_reference(previous_journal_entry),
        )
        return PaperOrderReconciliationResult(report=report, journal_entry=None)

    def reconcile(
        self,
        execution_result: PaperOrderExecutionResult | None,
        *,
        previous_journal_entry: JournalEntry | None,
        read_adapter: PaperOrderStatusReadOnlyAdapter,
    ) -> PaperOrderReconciliationResult:
        block_reasons = _block_reasons(execution_result, previous_journal_entry)
        if block_reasons:
            report = _report(
                execution_result,
                final_status=RECONCILIATION_BLOCKED,
                match_status=RECONCILIATION_BLOCKED,
                mismatch_reasons=block_reasons,
                journal_entry_reference=_journal_reference(previous_journal_entry),
            )
            return PaperOrderReconciliationResult(
                report=report,
                journal_entry=_journal_entry(report),
            )

        assert execution_result is not None
        try:
            snapshot = read_adapter.read_account_and_positions_only()
            if not snapshot.paper_mode:
                report = _report(
                    execution_result,
                    final_status=RECONCILIATION_BLOCKED,
                    match_status=RECONCILIATION_BLOCKED,
                    mismatch_reasons=("live account mode blocks reconciliation",),
                    journal_entry_reference=_journal_reference(previous_journal_entry),
                    account_mode="NON_PAPER",
                )
                return PaperOrderReconciliationResult(
                    report=report,
                    journal_entry=_journal_entry(report),
                )
            observed = read_adapter.read_paper_order_status(execution_result.alpaca_order_id or "")
        except Exception as exc:
            report = _report(
                execution_result,
                final_status=RECONCILIATION_READ_ERROR,
                match_status=RECONCILIATION_READ_ERROR,
                mismatch_reasons=(_safe_error(exc),),
                journal_entry_reference=_journal_reference(previous_journal_entry),
            )
            return PaperOrderReconciliationResult(
                report=report,
                journal_entry=_journal_entry(report),
            )

        if not observed:
            report = _report(
                execution_result,
                final_status=RECONCILIATION_ORDER_NOT_FOUND,
                match_status=RECONCILIATION_ORDER_NOT_FOUND,
                mismatch_reasons=("order not found",),
                journal_entry_reference=_journal_reference(previous_journal_entry),
                account_mode="PAPER",
            )
            return PaperOrderReconciliationResult(
                report=report,
                journal_entry=_journal_entry(report),
            )

        observed_values = _observed_values(observed)
        mismatch_reasons = _mismatch_reasons(_expected_values(execution_result), observed_values)
        final_status = RECONCILIATION_MISMATCH if mismatch_reasons else RECONCILIATION_MATCHED
        report = _report(
            execution_result,
            final_status=final_status,
            match_status=final_status,
            mismatch_reasons=mismatch_reasons,
            journal_entry_reference=_journal_reference(previous_journal_entry),
            observed_values=observed_values,
            account_mode="PAPER",
            order_status=_string_or_none(observed_values.get("order_status")),
        )
        return PaperOrderReconciliationResult(
            report=report,
            journal_entry=_journal_entry(report),
        )


def _block_reasons(
    execution_result: PaperOrderExecutionResult | None,
    previous_journal_entry: JournalEntry | None,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if execution_result is None:
        reasons.append("missing execution result")
        return tuple(reasons)
    if not execution_result.paper_order_request_id:
        reasons.append("missing paper order request")
    if not execution_result.journal_entry_id or previous_journal_entry is None:
        reasons.append("missing journal reference")
    if execution_result.account_mode != "PAPER":
        reasons.append("live account mode blocks reconciliation")
    return tuple(reasons)


def _expected_values(execution_result: PaperOrderExecutionResult | None) -> Mapping[str, object]:
    if execution_result is None:
        return {}
    return {
        "broker": execution_result.broker,
        "account_mode": execution_result.account_mode,
        "symbol": execution_result.symbol,
        "side": execution_result.side,
        "quantity": execution_result.quantity,
        "notional": execution_result.notional,
        "order_type": execution_result.order_type,
        "time_in_force": execution_result.time_in_force,
        "alpaca_order_id": execution_result.alpaca_order_id,
        "journaled_execution_status": execution_result.final_status,
    }


def _observed_values(observed: Mapping[str, Any]) -> Mapping[str, object]:
    return {
        "broker": "alpaca",
        "account_mode": "PAPER",
        "symbol": _string_or_none(observed.get("symbol")),
        "side": _string_or_none(observed.get("side")),
        "quantity": _string_or_none(observed.get("qty") or observed.get("quantity")),
        "notional": _string_or_none(observed.get("notional")),
        "order_type": _string_or_none(observed.get("type") or observed.get("order_type")),
        "time_in_force": _string_or_none(observed.get("time_in_force")),
        "alpaca_order_id": _string_or_none(observed.get("id")),
        "order_status": _string_or_none(observed.get("status")),
    }


def _mismatch_reasons(
    expected_values: Mapping[str, object],
    observed_values: Mapping[str, object],
) -> tuple[str, ...]:
    reasons: list[str] = []
    for key in (
        "broker",
        "account_mode",
        "symbol",
        "side",
        "quantity",
        "notional",
        "order_type",
        "time_in_force",
        "alpaca_order_id",
    ):
        expected = expected_values.get(key)
        observed = observed_values.get(key)
        if expected in (None, "") and observed in (None, ""):
            continue
        if str(expected) != str(observed):
            reasons.append(f"{key} mismatch")
    if expected_values.get("journaled_execution_status") != PAPER_ORDER_SUBMITTED:
        reasons.append("journaled execution status mismatch")
    if not observed_values.get("order_status"):
        reasons.append("current order status missing")
    return tuple(reasons)


def _report(
    execution_result: PaperOrderExecutionResult | None,
    *,
    final_status: str,
    match_status: str,
    mismatch_reasons: tuple[str, ...],
    journal_entry_reference: str | None,
    observed_values: Mapping[str, object] | None = None,
    account_mode: str | None = None,
    order_status: str | None = None,
) -> PaperOrderReconciliationReport:
    execution_id = execution_result.execution_result_id if execution_result else None
    request_id = execution_result.paper_order_request_id if execution_result else None
    return PaperOrderReconciliationReport(
        reconciliation_id=f"reconciliation-{execution_id or 'blocked'}",
        execution_result_id=execution_id,
        paper_order_request_id=request_id,
        alpaca_order_id=execution_result.alpaca_order_id if execution_result else None,
        checked_at="2026-05-19T13:39:00+00:00",
        expected_values=_expected_values(execution_result),
        observed_values=observed_values or {},
        account_mode=account_mode or (execution_result.account_mode if execution_result else None),
        order_status=order_status,
        match_status=match_status,
        mismatch_reasons=mismatch_reasons,
        final_reconciliation_status=final_status,
        journal_entry_reference=journal_entry_reference,
        adlc_compliance_reference=(
            execution_result.adlc_compliance_reference if execution_result else None
        ),
    )


def _journal_entry(report: PaperOrderReconciliationReport) -> JournalEntry:
    return commit_journal_entry(
        proposal=None,
        risk_status="OBSERVE_ONLY",
        human_approval_status="OBSERVE_ONLY",
        gatekeeper_status="OBSERVE_AND_JOURNAL_ONLY",
        event_type="paper_order_reconciliation",
        reason_for_final_decision=report.final_reconciliation_status,
        lessons_or_notes=(
            "reconciliation attempted; "
            f"order status observed={report.order_status or 'none'}; "
            f"match status={report.match_status}; "
            f"mismatch reasons={'; '.join(report.mismatch_reasons) or 'none'}; "
            "no follow-up action taken"
        ),
        routine_name="post_send_reconciliation",
        adlc_status=report.adlc_compliance_reference or "UNKNOWN",
    )


def _journal_reference(journal_entry: JournalEntry | None) -> str | None:
    if journal_entry is None:
        return None
    return f"journal-{journal_entry.proposal_id}-{journal_entry.event_type}"


def _safe_error(exc: Exception) -> str:
    message = str(exc)
    for secret_name in ("ALPACA_API_KEY_ID", "ALPACA_API_SECRET_KEY"):
        secret = os.environ.get(secret_name)
        if secret:
            message = message.replace(secret, "[REDACTED]")
    return message or exc.__class__.__name__


def _string_or_none(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)


def deterministic_reconciliation_result() -> PaperOrderReconciliationResult:
    _, _, _, journal, request, _ = deterministic_valid_request()
    request = request.__class__(**{**request.as_dict(), "quantity": "1"})
    confirmation = confirmed_manual_execution(request)
    adapter = AlpacaPaperOrderAdapter(
        PaperOrderAdapterConfig(execution_enabled=True, execution_mode=MOCKED_PAPER_SEND),
        RecordingMockPaperClient(),
    )
    send_result = adapter.send_paper_order_request(
        request,
        account=default_mock_snapshot(),
        journal_commit=journal,
        manual_confirmation=confirmation,
    )
    assert send_result.execution_result is not None
    assert send_result.journal_entry is not None
    order_status = {
        "id": send_result.execution_result.alpaca_order_id,
        "symbol": send_result.execution_result.symbol,
        "side": send_result.execution_result.side,
        "qty": send_result.execution_result.quantity,
        "type": send_result.execution_result.order_type,
        "time_in_force": send_result.execution_result.time_in_force,
        "status": "accepted",
    }
    return PaperOrderReconciler().reconcile(
        send_result.execution_result,
        previous_journal_entry=send_result.journal_entry,
        read_adapter=StaticPaperOrderStatusReadOnlyAdapter(order_status=order_status),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic paper order reconciliation.")
    parser.add_argument("--pending", action="store_true")
    args = parser.parse_args()

    if args.pending:
        _, _, _, journal, request, _ = deterministic_valid_request()
        request = request.__class__(**{**request.as_dict(), "quantity": "1"})
        confirmation = confirmed_manual_execution(request)
        adapter = AlpacaPaperOrderAdapter(
            PaperOrderAdapterConfig(execution_enabled=True, execution_mode=MOCKED_PAPER_SEND),
            RecordingMockPaperClient(),
        )
        send_result = adapter.send_paper_order_request(
            request,
            account=default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=confirmation,
        )
        result = PaperOrderReconciler().pending(
            send_result.execution_result,
            previous_journal_entry=send_result.journal_entry,
        )
    else:
        result = deterministic_reconciliation_result()
    print(json.dumps(result.as_dict(), indent=2))
    return 0 if result.report.final_reconciliation_status != RECONCILIATION_READ_ERROR else 1


if __name__ == "__main__":
    raise SystemExit(main())
