from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "runtime"
MODULE_PATH = RUNTIME_PATH / "real_market_paper_reconciliation.py"

if str(RUNTIME_PATH) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PATH))

spec = importlib.util.spec_from_file_location("real_market_paper_reconciliation", MODULE_PATH)
reconciliation = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["real_market_paper_reconciliation"] = reconciliation
spec.loader.exec_module(reconciliation)


class RealMarketPaperReconciliationTests(unittest.TestCase):
    def test_valid_phase58_fake_paper_send_reconciles(self) -> None:
        with recon_context() as ctx:
            result = reconciliation.reconcile_phase58_paper_run(
                valid_payload(),
                report_root=ctx.report_root,
            )

            self.assertEqual(result.reconciliation_status, "RECONCILED")
            self.assertEqual(result.failures, ())
            self.assertEqual(result.requested_notional_usd, 100.0)
            self.assertTrue(result.artifacts.report_path.exists())

    def test_valid_phase58_no_send_reconciles_as_blocked(self) -> None:
        with recon_context() as ctx:
            result = reconciliation.reconcile_phase58_paper_run(
                valid_payload(
                    paper_order_sent=False,
                    order_api_used=False,
                    broker_execution_readiness=False,
                    final_status="BLOCKED",
                    order_result=None,
                ),
                report_root=ctx.report_root,
            )

            self.assertEqual(result.reconciliation_status, "BLOCKED")
            self.assertIn("no_paper_order_sent", result.warnings)

    def test_unsupported_source_phase_fails(self) -> None:
        with recon_context() as ctx:
            result = reconciliation.reconcile_phase58_paper_run(
                valid_payload(source_phase="Phase 99 Unsupported"),
                report_root=ctx.report_root,
            )

            report = result.artifacts.report_path.read_text(encoding="utf-8")
            self.assertEqual(result.reconciliation_status, "FAILED")
            self.assertIn("unsupported_source_phase", result.failures)
            self.assertIn("unsupported_source_phase", report)

    def test_missing_symbol_fails(self) -> None:
        self.assert_failed(valid_payload(symbol=""), "missing_symbol")

    def test_more_than_one_symbol_fails(self) -> None:
        self.assert_failed(valid_payload(symbol="AAPL,MSFT"), "more_than_one_symbol")

    def test_max_notional_over_100_fails(self) -> None:
        self.assert_failed(valid_payload(max_notional_usd=101.0), "max_notional_over_100")

    def test_paper_only_false_fails(self) -> None:
        self.assert_failed(valid_payload(paper_only=False), "paper_only_required")

    def test_live_order_sent_true_fails(self) -> None:
        self.assert_failed(valid_payload(live_order_sent=True), "live_order_sent")

    def test_live_trading_assumption_true_fails(self) -> None:
        self.assert_failed(
            valid_payload(live_trading_assumption=True),
            "live_trading_assumption",
        )

    def test_missing_human_review_with_paper_order_sent_fails(self) -> None:
        self.assert_failed(
            valid_payload(human_review_approved=False),
            "missing_human_review_approval",
        )

    def test_missing_manual_confirmation_with_paper_order_sent_fails(self) -> None:
        self.assert_failed(
            valid_payload(manual_execution_confirmed=False),
            "missing_manual_execution_confirmation",
        )

    def test_preflight_not_pass_with_paper_order_sent_fails(self) -> None:
        self.assert_failed(
            valid_payload(preflight_status="BLOCKED"),
            "preflight_not_pass",
        )

    def test_broker_execution_readiness_inconsistency_fails(self) -> None:
        self.assert_failed(
            valid_payload(broker_execution_readiness=True, preflight_status="BLOCKED"),
            "broker_execution_readiness_not_paper_preflight_consistent",
        )

    def test_missing_order_result_when_paper_order_sent_fails_without_fabricated_data(self) -> None:
        with recon_context() as ctx:
            result = reconciliation.reconcile_phase58_paper_run(
                valid_payload(order_result=None),
                report_root=ctx.report_root,
            )

            report = result.artifacts.report_path.read_text(encoding="utf-8")
            self.assertEqual(result.reconciliation_status, "FAILED")
            self.assertIn("missing_order_result", result.failures)
            self.assertIn("order_status: UNAVAILABLE", report)
            self.assertIn("fill_price: UNAVAILABLE", report)

    def test_live_endpoint_in_order_result_fails(self) -> None:
        self.assert_failed(
            valid_payload(order_result=valid_order_result(live_endpoint_detected=True)),
            "live_endpoint_in_order_result",
        )

    def test_live_account_implication_fails(self) -> None:
        self.assert_failed(
            valid_payload(order_result=valid_order_result(live_account=True)),
            "live_account_in_order_result",
        )

    def test_missing_optional_fill_price_warns_without_fabricating_data(self) -> None:
        with recon_context() as ctx:
            result = reconciliation.reconcile_phase58_paper_run(
                valid_payload(
                    order_result=valid_order_result(fill_price=None, reference_price=190.0)
                ),
                report_root=ctx.report_root,
            )

            self.assertEqual(result.reconciliation_status, "RECONCILED_WITH_WARNINGS")
            self.assertIn("fill_price_unavailable", result.warnings)
            self.assertEqual(result.fill_price, "UNAVAILABLE")

    def test_slippage_bps_calculation_when_prices_exist(self) -> None:
        with recon_context() as ctx:
            result = reconciliation.reconcile_phase58_paper_run(
                valid_payload(
                    order_result=valid_order_result(fill_price=101.0, reference_price=100.0)
                ),
                report_root=ctx.report_root,
            )

            self.assertEqual(result.estimated_slippage_bps, 100.0)

    def test_no_order_adapter_or_automated_send_import_and_no_order_endpoint(self) -> None:
        module_text = MODULE_PATH.read_text(encoding="utf-8")
        import_lines = [
            line
            for line in module_text.splitlines()
            if line.startswith("import ") or line.startswith("from ")
        ]

        self.assertFalse(any("alpaca_paper_order_adapter" in line for line in import_lines))
        self.assertFalse(any("automated_paper_send" in line for line in import_lines))
        self.assertFalse(any("one_real_automated_paper_send" in line for line in import_lines))
        self.assertNotIn("/v2/orders", module_text)
        self.assertNotIn("urlopen", module_text)

    def test_secret_in_strategy_reason_is_redacted(self) -> None:
        self.assert_report_redacts(
            valid_payload(strategy_reason="secret=PHASE59_STRATEGY_SECRET"),
            "PHASE59_STRATEGY_SECRET",
        )

    def test_secret_in_reason_is_redacted(self) -> None:
        self.assert_report_redacts(
            valid_payload(reason="api_key=PHASE59_REASON_SECRET"),
            "PHASE59_REASON_SECRET",
        )

    def test_secret_in_reconciliation_notes_is_redacted(self) -> None:
        self.assert_report_redacts(
            valid_payload(reconciliation_notes="token=PHASE59_NOTE_SECRET"),
            "PHASE59_NOTE_SECRET",
        )

    def test_source_field_is_reported_and_redacted(self) -> None:
        exact_secret = "PHASE59_SOURCE_SECRET"
        with recon_context() as ctx:
            result = reconciliation.reconcile_phase58_paper_run(
                valid_payload(source=f"secret={exact_secret}"),
                report_root=ctx.report_root,
            )

            report = result.artifacts.report_path.read_text(encoding="utf-8")
            self.assertIn("source:", report)
            self.assertNotIn(exact_secret, report)
            self.assertIn("[REDACTED]", report)

    def test_status_raw_and_provider_messages_are_redacted(self) -> None:
        secrets = {
            "status": "PHASE59_STATUS_SECRET",
            "raw": "PHASE59_RAW_SECRET",
            "provider": "PHASE59_PROVIDER_SECRET",
            "order": "PHASE59_ORDER_STATUS_SECRET",
        }
        with recon_context() as ctx:
            result = reconciliation.reconcile_phase58_paper_run(
                valid_payload(
                    order_result=valid_order_result(
                        order_status=f"secret={secrets['order']}",
                        status_message=f"token={secrets['status']}",
                        raw_adapter_message=f"api_key={secrets['raw']}",
                        provider_message=f"bearer {secrets['provider']}123456789",
                    )
                ),
                report_root=ctx.report_root,
            )

            report = result.artifacts.report_path.read_text(encoding="utf-8")
            self.assertIn("status_message:", report)
            self.assertIn("raw_adapter_message:", report)
            self.assertIn("provider_message:", report)
            for exact_secret in secrets.values():
                self.assertNotIn(exact_secret, report)
            self.assertIn("[REDACTED]", report)

    def test_required_safety_statements_remain_present(self) -> None:
        with recon_context() as ctx:
            result = reconciliation.reconcile_phase58_paper_run(
                valid_payload(strategy_reason="bearer PHASE59SECRETTOKEN123456789"),
                report_root=ctx.report_root,
            )

            report = result.artifacts.report_path.read_text(encoding="utf-8")
            self.assertIn("[REDACTED]", report)
            self.assertIn("No new order was sent.", report)
            self.assertIn("No live order was sent.", report)
            self.assertIn("This phase only reconciles Phase 58 artifacts.", report)
            self.assertIn("Paper-only execution path remains required.", report)
            self.assertIn("Human review remained required.", report)
            self.assertIn("Manual execution confirmation remained required.", report)
            self.assertIn("Live trading remains unsupported.", report)

    def test_post_mortem_and_evidence_manifest_are_created(self) -> None:
        with recon_context() as ctx:
            result = reconciliation.reconcile_phase58_paper_run(
                valid_payload(input_artifact_references=("phase58-report.md",)),
                report_root=ctx.report_root,
            )

            self.assertTrue(result.artifacts.post_mortem_path.exists())
            self.assertTrue(result.artifacts.evidence_manifest_path.exists())
            post_mortem = result.artifacts.post_mortem_path.read_text(encoding="utf-8")
            manifest = result.artifacts.evidence_manifest_path.read_text(encoding="utf-8")
            self.assertIn("Summary", post_mortem)
            self.assertIn("What Happened", post_mortem)
            self.assertIn("What Did Not Happen", post_mortem)
            self.assertIn("Safety Gates Observed", post_mortem)
            self.assertIn("Reconciliation Result", post_mortem)
            self.assertIn("Warnings", post_mortem)
            self.assertIn("Failures", post_mortem)
            self.assertIn("Follow-Up Actions", post_mortem)
            self.assertIn("No new order was sent.", post_mortem)
            self.assertIn("Live trading remains unsupported.", post_mortem)
            self.assertIn("Input Artifact References", manifest)
            self.assertIn("Generated report path", manifest)
            self.assertIn("Generated post-mortem path", manifest)
            self.assertIn("Test Command Evidence", manifest)
            self.assertIn("Safety Invariant Checklist", manifest)
            self.assertIn("No-Secret Evidence", manifest)
            self.assertIn("No-Live-Order Evidence", manifest)
            self.assertIn("phase58-report.md", manifest)
            self.assertIn("No live order was sent.", manifest)

    def test_no_env_file_is_created(self) -> None:
        with recon_context() as ctx:
            reconciliation.reconcile_phase58_paper_run(valid_payload(), report_root=ctx.report_root)

            self.assertFalse((ctx.root / ".env").exists())

    def test_no_secrets_are_printed_to_artifacts(self) -> None:
        secret = "api_key=PHASE59_EXACT_SECRET"
        with recon_context() as ctx:
            result = reconciliation.reconcile_phase58_paper_run(
                valid_payload(strategy_reason=secret, reconciliation_notes=secret),
                report_root=ctx.report_root,
            )

            for path in (
                result.artifacts.report_path,
                result.artifacts.post_mortem_path,
                result.artifacts.evidence_manifest_path,
            ):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("PHASE59_EXACT_SECRET", text)
            self.assertIn("[REDACTED]", result.artifacts.report_path.read_text(encoding="utf-8"))

    def assert_failed(self, payload, expected_failure: str) -> None:
        with recon_context() as ctx:
            result = reconciliation.reconcile_phase58_paper_run(
                payload,
                report_root=ctx.report_root,
            )

            self.assertEqual(result.reconciliation_status, "FAILED")
            self.assertIn(expected_failure, result.failures)

    def assert_report_redacts(self, payload, exact_secret: str) -> None:
        with recon_context() as ctx:
            result = reconciliation.reconcile_phase58_paper_run(
                payload,
                report_root=ctx.report_root,
            )

            report = result.artifacts.report_path.read_text(encoding="utf-8")
            self.assertNotIn(exact_secret, report)
            self.assertIn("[REDACTED]", report)


class recon_context:
    def __enter__(self) -> recon_context:
        self._temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self._temp_dir.name)
        self.report_root = self.root / "reports" / "real_market_paper_reconciliation"
        return self

    def __exit__(self, *args: object) -> None:
        self._temp_dir.cleanup()


def valid_payload(**overrides):
    values = {
        "source_phase": reconciliation.SOURCE_PHASE,
        "symbol": "AAPL",
        "timestamp": "2026-05-20T13:30:00+00:00",
        "timeframe": "1m",
        "session": "market_open",
        "strategy_decision": "TRADE_PROPOSAL",
        "strategy_reason": "Validated Phase 58 paper proposal.",
        "evaluation_gate_status": "EVALUATION_GATE_PASSED",
        "negative_regression_status": "PASS",
        "candidate_created": True,
        "human_review_approved": True,
        "finalized_request_created": True,
        "manual_execution_confirmed": True,
        "preflight_status": "PAPER_ORDER_SEND_ALLOWED",
        "max_notional_usd": 100.0,
        "paper_only": True,
        "broker_execution_readiness": True,
        "order_api_used": True,
        "paper_order_sent": True,
        "live_order_sent": False,
        "live_trading_assumption": False,
        "final_status": "PAPER_ORDER_SENT",
        "reason": "All Phase 58 gates passed.",
        "source": "fake_read_only_market_data",
        "order_result": valid_order_result(),
        "reconciliation_notes": "No discrepancies.",
        "input_artifact_references": ("reports/real_market_paper_order_run/fake.md",),
    }
    values.update(overrides)
    return reconciliation.Phase58ReconciliationInput(**values)


def valid_order_result(**overrides):
    values = {
        "symbol": "AAPL",
        "accepted_notional_usd": 100.0,
        "paper_only": True,
        "live_order_sent": False,
        "live_endpoint_detected": False,
        "live_account": False,
        "order_status": "filled",
        "status_message": "filled",
        "fill_price": 189.2,
        "reference_price": 189.0,
        "filled_qty": 0.5285,
        "submitted_at": "2026-05-20T13:31:00+00:00",
        "filled_at": "2026-05-20T13:31:03+00:00",
    }
    values.update(overrides)
    return reconciliation.Phase58OrderResult(**values)


if __name__ == "__main__":
    unittest.main()
