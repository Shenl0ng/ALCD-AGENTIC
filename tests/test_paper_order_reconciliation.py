from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "runtime"

if str(RUNTIME_PATH) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PATH))


def load_module(name: str):
    path = RUNTIME_PATH / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


alpaca_paper_account = load_module("alpaca_paper_account")
human_approval = load_module("human_approval")
paper_trade = load_module("paper_trade")
paper_order_request = load_module("paper_order_request")
alpaca_paper_order_adapter = load_module("alpaca_paper_order_adapter")
paper_execution_dry_run = load_module("paper_execution_dry_run")
paper_order_reconciliation = load_module("paper_order_reconciliation")


class PaperOrderReconciliationTests(unittest.TestCase):
    def test_reconciliation_pending_before_status_check(self) -> None:
        execution_result, journal_entry = execution_bundle()

        result = paper_order_reconciliation.PaperOrderReconciler().pending(
            execution_result,
            previous_journal_entry=journal_entry,
        )

        self.assertEqual(
            result.report.final_reconciliation_status,
            paper_order_reconciliation.RECONCILIATION_PENDING,
        )
        self.assertIsNone(result.journal_entry)

    def test_pending_without_execution_result_is_blocked(self) -> None:
        result = paper_order_reconciliation.PaperOrderReconciler().pending(
            None,
            previous_journal_entry=None,
        )

        self.assertEqual(
            result.report.final_reconciliation_status,
            paper_order_reconciliation.RECONCILIATION_BLOCKED,
        )
        self.assertNotEqual(
            result.report.final_reconciliation_status,
            paper_order_reconciliation.RECONCILIATION_PENDING,
        )
        self.assertIn("missing Phase 9 execution result", result.report.mismatch_reasons)

    def test_matched_order_status_produces_matched(self) -> None:
        result = reconcile_with_observed()

        self.assertEqual(
            result.report.final_reconciliation_status,
            paper_order_reconciliation.RECONCILIATION_MATCHED,
        )
        self.assertEqual(result.report.mismatch_reasons, ())

    def test_symbol_mismatch_produces_mismatch(self) -> None:
        result = reconcile_with_observed({"symbol": "DIFF"})

        self.assert_mismatch(result, "symbol mismatch")

    def test_side_mismatch_produces_mismatch(self) -> None:
        result = reconcile_with_observed({"side": "sell"})

        self.assert_mismatch(result, "side mismatch")

    def test_quantity_mismatch_produces_mismatch(self) -> None:
        result = reconcile_with_observed({"qty": "2"})

        self.assert_mismatch(result, "quantity mismatch")

    def test_order_type_mismatch_produces_mismatch(self) -> None:
        result = reconcile_with_observed({"type": "market"})

        self.assert_mismatch(result, "order_type mismatch")

    def test_order_not_found_produces_order_not_found(self) -> None:
        execution_result, journal_entry = execution_bundle()
        result = paper_order_reconciliation.PaperOrderReconciler().reconcile(
            execution_result,
            previous_journal_entry=journal_entry,
            read_adapter=paper_order_reconciliation.StaticPaperOrderStatusReadOnlyAdapter(
                order_status=None
            ),
        )

        self.assertEqual(
            result.report.final_reconciliation_status,
            paper_order_reconciliation.RECONCILIATION_ORDER_NOT_FOUND,
        )

    def test_read_error_produces_read_error(self) -> None:
        execution_result, journal_entry = execution_bundle()
        result = paper_order_reconciliation.PaperOrderReconciler().reconcile(
            execution_result,
            previous_journal_entry=journal_entry,
            read_adapter=paper_order_reconciliation.StaticPaperOrderStatusReadOnlyAdapter(
                order_status=None,
                read_error=RuntimeError("read failed"),
            ),
        )

        self.assertEqual(
            result.report.final_reconciliation_status,
            paper_order_reconciliation.RECONCILIATION_READ_ERROR,
        )

    def test_missing_execution_result_blocks_reconciliation(self) -> None:
        result = paper_order_reconciliation.PaperOrderReconciler().reconcile(
            None,
            previous_journal_entry=None,
            read_adapter=paper_order_reconciliation.StaticPaperOrderStatusReadOnlyAdapter(
                order_status=None
            ),
        )

        self.assertEqual(
            result.report.final_reconciliation_status,
            paper_order_reconciliation.RECONCILIATION_BLOCKED,
        )
        self.assertIn("missing execution result", result.report.mismatch_reasons)

    def test_missing_paper_order_request_blocks_reconciliation(self) -> None:
        execution_result, journal_entry = execution_bundle()
        execution_result = replace(execution_result, paper_order_request_id=None)

        result = reconcile_execution_result(execution_result, journal_entry)

        self.assertEqual(
            result.report.final_reconciliation_status,
            paper_order_reconciliation.RECONCILIATION_BLOCKED,
        )
        self.assertIn("missing paper order request", result.report.mismatch_reasons)

    def test_missing_journal_reference_blocks_reconciliation(self) -> None:
        execution_result, _ = execution_bundle()

        result = reconcile_execution_result(execution_result, None)

        self.assertEqual(
            result.report.final_reconciliation_status,
            paper_order_reconciliation.RECONCILIATION_BLOCKED,
        )
        self.assertIn("missing journal reference", result.report.mismatch_reasons)

    def test_live_account_mode_blocks_reconciliation(self) -> None:
        execution_result, journal_entry = execution_bundle()
        snapshot = replace(alpaca_paper_account.default_mock_snapshot(), paper_mode=False)

        result = paper_order_reconciliation.PaperOrderReconciler().reconcile(
            execution_result,
            previous_journal_entry=journal_entry,
            read_adapter=paper_order_reconciliation.StaticPaperOrderStatusReadOnlyAdapter(
                order_status=observed_order(execution_result),
                snapshot=snapshot,
            ),
        )

        self.assertEqual(
            result.report.final_reconciliation_status,
            paper_order_reconciliation.RECONCILIATION_BLOCKED,
        )
        self.assertIn("live account mode blocks reconciliation", result.report.mismatch_reasons)

    def test_no_submit_method_is_called(self) -> None:
        execution_result, journal_entry = execution_bundle()
        adapter = GuardedReadOnlyAdapter(order_status=observed_order(execution_result))

        result = paper_order_reconciliation.PaperOrderReconciler().reconcile(
            execution_result,
            previous_journal_entry=journal_entry,
            read_adapter=adapter,
        )

        self.assertEqual(
            result.report.final_reconciliation_status,
            paper_order_reconciliation.RECONCILIATION_MATCHED,
        )
        self.assertFalse(adapter.submit_called)

    def test_reconciliation_does_not_call_read_snapshot(self) -> None:
        execution_result, journal_entry = execution_bundle()
        adapter = GuardedReadOnlyAdapter(order_status=observed_order(execution_result))

        paper_order_reconciliation.PaperOrderReconciler().reconcile(
            execution_result,
            previous_journal_entry=journal_entry,
            read_adapter=adapter,
        )

        self.assertFalse(adapter.snapshot_called)

    def test_reconciliation_calls_narrow_account_positions_read(self) -> None:
        execution_result, journal_entry = execution_bundle()
        adapter = GuardedReadOnlyAdapter(order_status=observed_order(execution_result))

        paper_order_reconciliation.PaperOrderReconciler().reconcile(
            execution_result,
            previous_journal_entry=journal_entry,
            read_adapter=adapter,
        )

        self.assertEqual(adapter.account_positions_reads, 1)

    def test_narrow_account_positions_method_does_not_read_orders(self) -> None:
        client = ReadOnlyPathRecorder()
        account_adapter = alpaca_paper_account.AlpacaPaperAccountReadOnlyAdapter(
            alpaca_paper_account.AlpacaPaperConfig(key_id="key", secret_key="secret"),
            client,
        )

        snapshot = account_adapter.read_account_and_positions_only()

        self.assertEqual(snapshot.existing_orders, ())
        self.assertEqual(client.calls, [("/v2/account", None), ("/v2/positions", None)])

    def test_existing_order_list_read_still_available_outside_reconciliation(self) -> None:
        client = ReadOnlyPathRecorder()
        account_adapter = alpaca_paper_account.AlpacaPaperAccountReadOnlyAdapter(
            alpaca_paper_account.AlpacaPaperConfig(key_id="key", secret_key="secret"),
            client,
        )

        account_adapter.read_existing_paper_orders()

        self.assertIn(("/v2/orders", {"status": "all", "limit": "50"}), client.calls)

    def test_no_cancel_replace_or_batch_method_exists(self) -> None:
        reconciler = paper_order_reconciliation.PaperOrderReconciler()

        self.assertFalse(hasattr(reconciler, "cancel_order"))
        self.assertFalse(hasattr(reconciler, "replace_order"))
        self.assertFalse(hasattr(reconciler, "batch_orders"))
        self.assertFalse(hasattr(reconciler, "submit_order"))

    def test_no_autonomous_follow_up_trade_is_created(self) -> None:
        result = reconcile_with_observed()

        self.assertEqual(
            result.report.default_action,
            paper_order_reconciliation.OBSERVE_AND_JOURNAL_ONLY,
        )
        self.assertNotEqual(result.report.final_reconciliation_status, "ORDER_CREATED")

    def test_journal_entry_is_written_after_reconciliation(self) -> None:
        result = reconcile_with_observed()

        self.assertIsNotNone(result.journal_entry)
        self.assertEqual(result.journal_entry.event_type, "paper_order_reconciliation")
        self.assertIn("no follow-up action taken", result.journal_entry.lessons_or_notes)

    def test_secrets_are_not_logged(self) -> None:
        execution_result, journal_entry = execution_bundle()
        os.environ["ALPACA_API_SECRET_KEY"] = "secret-value-not-in-report"
        try:
            result = paper_order_reconciliation.PaperOrderReconciler().reconcile(
                execution_result,
                previous_journal_entry=journal_entry,
                read_adapter=paper_order_reconciliation.StaticPaperOrderStatusReadOnlyAdapter(
                    order_status=None,
                    read_error=RuntimeError("secret-value-not-in-report failed"),
                ),
            )
        finally:
            os.environ.pop("ALPACA_API_SECRET_KEY", None)

        self.assertNotIn("secret-value-not-in-report", str(result.as_dict()))

    def test_no_env_file_is_created(self) -> None:
        before = env_files()

        reconcile_with_observed()

        self.assertEqual(before, env_files())

    def test_no_llm_calls_exist(self) -> None:
        sources = "\n".join(path.read_text(encoding="utf-8") for path in RUNTIME_PATH.glob("*.py"))

        self.assertNotIn("chat.completions", sources)
        self.assertNotIn("responses.create", sources)

    def assert_mismatch(self, result, reason: str) -> None:
        self.assertEqual(
            result.report.final_reconciliation_status,
            paper_order_reconciliation.RECONCILIATION_MISMATCH,
        )
        self.assertIn(reason, result.report.mismatch_reasons)


class GuardedReadOnlyAdapter(paper_order_reconciliation.StaticPaperOrderStatusReadOnlyAdapter):
    def __init__(self, *, order_status):
        super().__init__(order_status=order_status)
        self.submit_called = False
        self.snapshot_called = False

    def submit_order(self, payload):
        self.submit_called = True
        raise AssertionError("submit_order must not be called")

    def read_snapshot(self):
        self.snapshot_called = True
        raise AssertionError("read_snapshot must not be called by reconciliation")


class ReadOnlyPathRecorder:
    def __init__(self):
        self.calls = []

    def get_json(self, path, params=None):
        self.calls.append((path, params))
        if path == "/v2/account":
            return {
                "id": "acct-123",
                "cash": "1000",
                "equity": "1000",
                "buying_power": "1000",
                "portfolio_value": "1000",
                "daytrade_count": 0,
                "trading_blocked": False,
                "transfers_blocked": False,
                "account_blocked": False,
                "status": "ACTIVE",
            }
        if path == "/v2/positions":
            return []
        if path == "/v2/orders":
            return []
        raise AssertionError(f"Unexpected path: {path}")


def execution_bundle():
    _, _, _, journal, request, _ = paper_order_request.deterministic_valid_request()
    request = replace(request, quantity="1")
    confirmation = paper_execution_dry_run.confirmed_manual_execution(request)
    adapter = alpaca_paper_order_adapter.AlpacaPaperOrderAdapter(
        alpaca_paper_order_adapter.PaperOrderAdapterConfig(
            execution_enabled=True,
            execution_mode=alpaca_paper_order_adapter.MOCKED_PAPER_SEND,
        ),
        alpaca_paper_order_adapter.RecordingMockPaperClient(),
    )
    result = adapter.send_paper_order_request(
        request,
        account=alpaca_paper_account.default_mock_snapshot(),
        journal_commit=journal,
        manual_confirmation=confirmation,
    )
    assert result.execution_result is not None
    assert result.journal_entry is not None
    return result.execution_result, result.journal_entry


def observed_order(execution_result, changes=None):
    payload = {
        "id": execution_result.alpaca_order_id,
        "symbol": execution_result.symbol,
        "side": execution_result.side,
        "qty": execution_result.quantity,
        "type": execution_result.order_type,
        "time_in_force": execution_result.time_in_force,
        "status": "accepted",
    }
    payload.update(changes or {})
    return payload


def reconcile_with_observed(changes=None):
    execution_result, journal_entry = execution_bundle()
    return paper_order_reconciliation.PaperOrderReconciler().reconcile(
        execution_result,
        previous_journal_entry=journal_entry,
        read_adapter=paper_order_reconciliation.StaticPaperOrderStatusReadOnlyAdapter(
            order_status=observed_order(execution_result, changes)
        ),
    )


def reconcile_execution_result(execution_result, journal_entry):
    return paper_order_reconciliation.PaperOrderReconciler().reconcile(
        execution_result,
        previous_journal_entry=journal_entry,
        read_adapter=paper_order_reconciliation.StaticPaperOrderStatusReadOnlyAdapter(
            order_status=observed_order(execution_result)
        ),
    )


def env_files() -> set[str]:
    return {
        path.as_posix()
        for path in ROOT.rglob(".env*")
        if "__pycache__" not in path.parts
    }


if __name__ == "__main__":
    unittest.main()
