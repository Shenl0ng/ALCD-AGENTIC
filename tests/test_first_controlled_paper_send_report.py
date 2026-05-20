from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "runtime"
TEMPLATE_PATH = ROOT / "docs" / "FIRST_CONTROLLED_PAPER_SEND_REPORT_TEMPLATE.md"

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


report_generator = load_module("first_controlled_paper_send_report")


class FirstControlledPaperSendReportTests(unittest.TestCase):
    def test_report_is_not_generated_from_template_alone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)

            result = report_generator.generate_first_controlled_paper_send_report(
                report_dir,
                template_path=TEMPLATE_PATH,
            )

            self.assertEqual(result.status, report_generator.MISSING_RUN_OUTPUT)
            self.assertIsNone(result.report_path)
            self.assertFalse((report_dir / report_generator.FINAL_REPORT_NAME).exists())
            self.assertTrue((report_dir / report_generator.EMPTY_REPORT_NAME).exists())

    def test_missing_send_result_blocks_report_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            write_complete_artifacts(report_dir)
            (report_dir / "paper_send_result.json").unlink()

            result = report_generator.generate_first_controlled_paper_send_report(
                report_dir,
                template_path=TEMPLATE_PATH,
            )

            self.assertEqual(result.status, report_generator.REPORT_BLOCKED)
            self.assertIn("paper_send_result.json", result.missing_artifacts)
            self.assertFalse((report_dir / report_generator.FINAL_REPORT_NAME).exists())

    def test_missing_reconciliation_output_blocks_report_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            write_complete_artifacts(report_dir)
            (report_dir / "reconciliation.json").unlink()

            result = report_generator.generate_first_controlled_paper_send_report(
                report_dir,
                template_path=TEMPLATE_PATH,
            )

            self.assertEqual(result.status, report_generator.REPORT_BLOCKED)
            self.assertIn("reconciliation.json", result.missing_artifacts)
            self.assertEqual(result.missing_fields, ())

    def test_missing_reconciliation_status_field_blocks_report_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            artifacts = complete_artifacts()
            artifacts["reconciliation"] = {"report": {}, "journal_entry": artifacts["reconciliation"]["journal_entry"]}
            write_artifacts(report_dir, artifacts)

            result = report_generator.generate_first_controlled_paper_send_report(
                report_dir,
                template_path=TEMPLATE_PATH,
            )
            status = json.loads(Path(result.status_path).read_text(encoding="utf-8"))

            self.assertEqual(result.status, report_generator.REPORT_BLOCKED)
            self.assertEqual(result.missing_artifacts, ())
            self.assertIn(
                "reconciliation.report.final_reconciliation_status",
                result.missing_fields,
            )
            self.assertIn(
                "reconciliation.report.final_reconciliation_status",
                status["missing_fields"],
            )
            self.assertFalse((report_dir / report_generator.FINAL_REPORT_NAME).exists())

    def test_missing_safety_output_blocks_report_completion(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            write_complete_artifacts(report_dir)
            (report_dir / "post_send_safety.json").unlink()

            result = report_generator.generate_first_controlled_paper_send_report(
                report_dir,
                template_path=TEMPLATE_PATH,
            )

            self.assertEqual(result.status, report_generator.REPORT_BLOCKED)
            self.assertIn("post_send_safety.json", result.missing_artifacts)

    def test_completed_report_never_renders_missing_reconciliation_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            write_complete_artifacts(report_dir)

            result = report_generator.generate_first_controlled_paper_send_report(
                report_dir,
                template_path=TEMPLATE_PATH,
            )
            report = Path(result.report_path or "").read_text(encoding="utf-8")

            self.assertEqual(result.status, report_generator.REPORT_READY)
            self.assertNotIn("Reconciliation status: missing", report)

    def test_fake_or_missing_alpaca_order_id_is_not_invented(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            artifacts = complete_artifacts()
            artifacts["paper_send_result"]["execution_result"].pop("alpaca_order_id")
            write_artifacts(report_dir, artifacts)

            result = report_generator.generate_first_controlled_paper_send_report(
                report_dir,
                template_path=TEMPLATE_PATH,
            )
            report = Path(result.report_path or "").read_text(encoding="utf-8")

            self.assertEqual(result.status, report_generator.REPORT_READY)
            self.assertIn("Alpaca order ID: not returned in artifact", report)
            self.assertNotIn("generated", report.lower())
            self.assertNotIn("fake", report.lower())

    def test_complete_artifact_set_generates_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            write_complete_artifacts(report_dir)

            result = report_generator.generate_first_controlled_paper_send_report(
                report_dir,
                template_path=TEMPLATE_PATH,
            )

            self.assertEqual(result.status, report_generator.REPORT_READY)
            self.assertEqual(result.missing_artifacts, ())
            self.assertTrue((report_dir / report_generator.FINAL_REPORT_NAME).exists())
            report = Path(result.report_path or "").read_text(encoding="utf-8")
            self.assertIn("Alpaca order ID: alpaca-paper-order-from-artifact", report)
            self.assertIn("Reconciliation status: RECONCILIATION_MATCHED", report)

    def test_generator_lists_missing_artifacts_clearly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            write_artifacts(report_dir, {"pre_send_checklist": complete_artifacts()["pre_send_checklist"]})

            result = report_generator.generate_first_controlled_paper_send_report(
                report_dir,
                template_path=TEMPLATE_PATH,
            )
            status = json.loads(Path(result.status_path).read_text(encoding="utf-8"))

            self.assertEqual(result.status, report_generator.REPORT_BLOCKED)
            self.assertIn("paper_send_result.json", status["missing_artifacts"])
            self.assertIn("reconciliation.json", status["missing_artifacts"])
            self.assertIn("post_send_safety.json", status["missing_artifacts"])
            self.assertEqual(status["missing_fields"], [])

    def test_missing_artifact_files_and_missing_fields_are_reported_separately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            artifacts = complete_artifacts()
            artifacts["reconciliation"] = {"report": {}, "journal_entry": artifacts["reconciliation"]["journal_entry"]}
            write_artifacts(report_dir, artifacts)

            field_result = report_generator.generate_first_controlled_paper_send_report(
                report_dir,
                template_path=TEMPLATE_PATH,
            )
            self.assertEqual(field_result.missing_artifacts, ())
            self.assertIn(
                "reconciliation.report.final_reconciliation_status",
                field_result.missing_fields,
            )

            (report_dir / "paper_send_result.json").unlink()
            artifact_result = report_generator.generate_first_controlled_paper_send_report(
                report_dir,
                template_path=TEMPLATE_PATH,
            )
            self.assertIn("paper_send_result.json", artifact_result.missing_artifacts)
            self.assertEqual(artifact_result.missing_fields, ())

    def test_no_live_trading_is_added(self) -> None:
        source = (RUNTIME_PATH / "first_controlled_paper_send_report.py").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("send_live", source)
        self.assertNotIn("live_trade", source)
        self.assertNotIn("api.alpaca.markets", source)

    def test_no_new_order_behavior_is_added(self) -> None:
        source = (RUNTIME_PATH / "first_controlled_paper_send_report.py").read_text(
            encoding="utf-8"
        )

        self.assertNotIn("submit_order", source)
        self.assertNotIn("send_paper_order_request", source)
        self.assertNotIn("cancel_order", source)
        self.assertNotIn("replace_order", source)
        self.assertNotIn("batch_orders", source)

    def test_no_credentials_or_env_files_are_created(self) -> None:
        before = env_files()
        with tempfile.TemporaryDirectory() as tmp:
            report_dir = Path(tmp)
            write_complete_artifacts(report_dir)
            report_generator.generate_first_controlled_paper_send_report(
                report_dir,
                template_path=TEMPLATE_PATH,
            )

        self.assertEqual(before, env_files())


def write_complete_artifacts(report_dir: Path) -> None:
    write_artifacts(report_dir, complete_artifacts())


def write_artifacts(report_dir: Path, artifacts: dict[str, object]) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    for key, payload in artifacts.items():
        filename = report_generator.REQUIRED_ARTIFACTS[key]
        (report_dir / filename).write_text(json.dumps(payload), encoding="utf-8")


def complete_artifacts() -> dict[str, object]:
    return {
        "pre_send_checklist": {
            "date": "2026-05-19",
            "mode": "REAL_ALPACA_PAPER_SEND",
            "paper_execution_enabled": True,
            "alpaca_account_mode": "PAPER",
            "live_endpoint_rejected": True,
        },
        "proposal_validation": {
            "proposal_id": "paper-market_open-001",
            "symbol": "SIM",
            "side": "buy",
            "notional": "100",
            "order_type": "limit",
            "time_in_force": "day",
            "status": "PASS",
        },
        "risk_evaluation": {"decision": "RISK_APPROVED"},
        "human_approval": {"approval_state": "HUMAN_APPROVED_FOR_PAPER_ONLY"},
        "manual_execution_confirmation": {
            "confirmation_state": "MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY"
        },
        "journal_commit": {"event_type": "human_approved_for_paper_only"},
        "preflight": {"final_decision": "PAPER_ORDER_SEND_ALLOWED"},
        "paper_send_result": {
            "status": "PAPER_ORDER_SUBMITTED",
            "execution_result": {
                "alpaca_order_id": "alpaca-paper-order-from-artifact",
                "alpaca_order_status": "accepted",
            },
            "journal_entry": {"event_type": "paper_order_send_submitted"},
        },
        "reconciliation": {
            "report": {
                "final_reconciliation_status": "RECONCILIATION_MATCHED",
                "mismatch_reasons": [],
            },
            "journal_entry": {"event_type": "paper_order_reconciliation"},
        },
        "post_send_safety": {
            "account_state_checked": True,
            "position_state_checked": True,
            "follow_up_orders_created": False,
            "cancel_replace_used": False,
            "live_trading_touched": False,
            "execution_flag_disabled_after_test": True,
            "returned_to_dry_run_only": True,
            "what_worked": "all required artifacts were present",
            "what_failed": "none recorded",
            "must_fix_before_next_send": "none recorded",
        },
    }


def env_files() -> set[str]:
    return {
        path.as_posix()
        for path in ROOT.rglob(".env*")
        if "__pycache__" not in path.parts
    }


if __name__ == "__main__":
    unittest.main()
