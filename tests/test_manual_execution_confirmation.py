from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch


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


candidate_module = load_module("paper_order_request_candidate")
review_queue = load_module("human_review_queue")
finalized_request = load_module("finalized_paper_order_request")
manual_confirmation = load_module("manual_execution_confirmation")


class ManualExecutionConfirmationTests(unittest.TestCase):
    def test_manual_execution_confirmation_model_exists(self) -> None:
        self.assertTrue(hasattr(manual_confirmation, "ManualExecutionConfirmation"))

    def test_manual_confirmation_validator_exists(self) -> None:
        self.assertTrue(hasattr(manual_confirmation, "validate_manual_confirmation"))

    def test_finalized_paper_order_request_can_receive_manual_confirmation(self) -> None:
        result = confirm()

        self.assertEqual(
            result.final_status,
            manual_confirmation.MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT,
        )
        self.assertIsNotNone(result.confirmation)

    def test_missing_finalized_request_blocks_confirmation(self) -> None:
        result = confirm(request=None)

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("finalized request missing", result.reason)

    def test_request_not_finalized_blocks_confirmation(self) -> None:
        request = replace(
            valid_request(),
            request_status=finalized_request.PAPER_ORDER_REQUEST_BLOCKED,
        )
        result = confirm(request=request)

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("PAPER_ORDER_REQUEST_FINALIZED", result.reason)

    def test_expired_request_blocks_confirmation(self) -> None:
        result = confirm(request_expired=True)

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_EXPIRED)
        self.assertIn("request expired", result.reason)

    def test_missing_confirmer_blocks_confirmation(self) -> None:
        result = confirm(confirmer="")

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("confirmer is required", result.reason)

    def test_missing_paper_only_confirmation_blocks_confirmation(self) -> None:
        result = confirm(paper_only_confirmation=False)

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("paper_only_confirmation", result.reason)

    def test_missing_no_live_trading_confirmation_blocks_confirmation(self) -> None:
        result = confirm(no_live_trading_confirmation=False)

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("no_live_trading_confirmation", result.reason)

    def test_missing_finalized_request_reviewed_blocks_confirmation(self) -> None:
        result = confirm(finalized_request_reviewed=False)

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("finalized_request_reviewed", result.reason)

    def test_missing_risk_reviewed_blocks_confirmation(self) -> None:
        result = confirm(risk_reviewed=False)

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("risk_reviewed", result.reason)

    def test_missing_order_details_reviewed_blocks_confirmation(self) -> None:
        result = confirm(order_details_reviewed=False)

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("order_details_reviewed", result.reason)

    def test_missing_notional_limit_confirmation_blocks_confirmation(self) -> None:
        result = confirm(notional_limit_confirmation=False)

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("notional_limit_confirmation", result.reason)

    def test_missing_limit_order_confirmation_blocks_confirmation(self) -> None:
        result = confirm(limit_order_confirmation=False)

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("limit_order_confirmation", result.reason)

    def test_missing_day_time_in_force_confirmation_blocks_confirmation(self) -> None:
        result = confirm(day_time_in_force_confirmation=False)

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("day_time_in_force_confirmation", result.reason)

    def test_missing_no_short_confirmation_blocks_confirmation(self) -> None:
        result = confirm(no_short_confirmation=False)

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("no_short_confirmation", result.reason)

    def test_missing_no_crypto_confirmation_blocks_confirmation(self) -> None:
        result = confirm(no_crypto_confirmation=False)

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("no_crypto_confirmation", result.reason)

    def test_missing_no_options_confirmation_blocks_confirmation(self) -> None:
        result = confirm(no_options_confirmation=False)

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("no_options_confirmation", result.reason)

    def test_missing_no_margin_confirmation_blocks_confirmation(self) -> None:
        result = confirm(no_margin_confirmation=False)

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("no_margin_confirmation", result.reason)

    def test_missing_no_extended_hours_confirmation_blocks_confirmation(self) -> None:
        result = confirm(no_extended_hours_confirmation=False)

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("no_extended_hours_confirmation", result.reason)

    def test_request_paper_trading_only_false_blocks_confirmation(self) -> None:
        result = confirm(request=replace(valid_request(), paper_trading_only=False))

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("paper_trading_only=true", result.reason)

    def test_request_live_trading_allowed_true_blocks_confirmation(self) -> None:
        result = confirm(request=replace(valid_request(), live_trading_allowed=True))

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("live_trading_allowed=false", result.reason)

    def test_request_broker_execution_allowed_true_blocks_confirmation(self) -> None:
        result = confirm(request=replace(valid_request(), broker_execution_allowed=True))

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("broker_execution_allowed=false", result.reason)

    def test_request_manual_execution_confirmation_required_false_blocks(self) -> None:
        result = confirm(
            request=replace(valid_request(), manual_execution_confirmation_required=False)
        )

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("manual_execution_confirmation_required=true", result.reason)

    def test_execution_flag_true_blocks_confirmation(self) -> None:
        with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": "true"}):
            result = manual_confirmation.create_manual_execution_confirmation(
                request=valid_request(),
                confirmer="manual-confirmer",
                write_artifacts=False,
            )

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_INVALID)
        self.assertIn("PAPER_ORDER_EXECUTION_ENABLED=true", result.reason)

    def test_confirmation_hardcodes_broker_execution_allowed_false(self) -> None:
        self.assertFalse(confirm().confirmation.broker_execution_allowed)

    def test_confirmation_hardcodes_live_trading_allowed_false(self) -> None:
        self.assertFalse(confirm().confirmation.live_trading_allowed)

    def test_confirmation_hardcodes_paper_send_preflight_required_true(self) -> None:
        self.assertTrue(confirm().confirmation.paper_send_preflight_required)

    def test_confirmation_artifact_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = manual_confirmation.create_manual_execution_confirmation(
                request=valid_request(),
                confirmer="manual-confirmer",
                output_root=Path(tmp),
            )

            self.assertTrue(Path(result.report_path or "").exists())

    def test_confirmation_journal_entry_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = manual_confirmation.create_manual_execution_confirmation(
                request=valid_request(),
                confirmer="manual-confirmer",
                output_root=Path(tmp),
            )

            self.assertTrue(Path(result.journal_path or "").exists())

    def test_rejected_manual_confirmation_blocks_progression(self) -> None:
        result = confirm(
            confirmation_status=manual_confirmation.MANUAL_EXECUTION_REJECTED,
        )

        self.assertEqual(result.final_status, manual_confirmation.MANUAL_EXECUTION_REJECTED)
        self.assertFalse(result.paper_send_preflight_created)

    def test_needs_more_information_manual_confirmation_blocks_progression(self) -> None:
        result = confirm(
            confirmation_status=manual_confirmation.MANUAL_EXECUTION_NEEDS_MORE_INFORMATION,
        )

        self.assertEqual(
            result.final_status,
            manual_confirmation.MANUAL_EXECUTION_NEEDS_MORE_INFORMATION,
        )
        self.assertFalse(result.paper_send_preflight_created)

    def test_confirmation_does_not_create_paper_send_preflight(self) -> None:
        self.assertFalse(confirm().paper_send_preflight_created)

    def test_confirmation_does_not_send_orders(self) -> None:
        result = confirm()

        self.assertFalse(result.order_sent)
        self.assertNotIn("submit_order", source_text())
        self.assertNotIn("place_order", source_text())
        self.assertNotIn("send_paper_order_request", source_text())

    def test_confirmation_does_not_create_broker_execution_readiness(self) -> None:
        self.assertFalse(confirm().broker_execution_readiness)

    def test_confirmation_does_not_call_alpaca_order_api(self) -> None:
        source = source_text()

        self.assertFalse(confirm().alpaca_order_api_called)
        self.assertNotIn("alpaca_paper_order_adapter", source)
        self.assertNotIn("UrlLibAlpacaPaperOrderClient", source)
        self.assertNotIn("urlopen", source)
        self.assertNotIn("/v2/orders", source)

    def test_artifact_states_manual_execution_confirmation_does_not_send_orders(self) -> None:
        self.assertIn(
            "Manual Execution Confirmation does not send orders.",
            rendered_artifact(),
        )

    def test_artifact_states_paper_send_preflight_required_later(self) -> None:
        self.assertIn("Paper Send Preflight is still required later.", rendered_artifact())

    def test_artifact_states_no_order_was_sent(self) -> None:
        self.assertIn("No order was sent.", rendered_artifact())

    def test_artifact_states_no_broker_execution_readiness_created(self) -> None:
        self.assertIn("No broker execution readiness was created.", rendered_artifact())

    def test_artifact_states_live_trading_remains_unsupported(self) -> None:
        self.assertIn("Live trading remains unsupported.", rendered_artifact())

    def test_no_live_trading_exists(self) -> None:
        source = source_text()

        self.assertFalse(confirm().live_trading_assumption)
        self.assertNotIn("LIVE_ALPACA", source)
        self.assertNotIn("api.alpaca.markets", source)

    def test_no_batch_behavior_exists(self) -> None:
        self.assertNotIn("batch_order", source_text().lower())

    def test_no_cancel_replace_exists(self) -> None:
        source = source_text()

        self.assertNotIn("cancel_order", source)
        self.assertNotIn("replace_order", source)

    def test_no_credentials_env_files_or_llm_calls(self) -> None:
        before = env_files()
        confirm()

        self.assertEqual(before, env_files())
        self.assertNotIn("chat.completions", source_text())
        self.assertNotIn("responses.create", source_text())
        self.assertNotIn("OpenAI", source_text())


def valid_candidate():
    with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": ""}):
        result = candidate_module.create_paper_order_request_candidate(
            symbols=["SIM"],
            write_artifacts=False,
        )
    assert result.candidate is not None
    return result.candidate


def valid_review():
    with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": ""}):
        result = review_queue.create_human_review_record(
            candidate=valid_candidate(),
            reviewer="human-reviewer",
            review_status=review_queue.HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST,
            review_notes="Reviewed candidate.",
            write_artifacts=False,
        )
    assert result.record is not None
    return result.record


def valid_request():
    with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": ""}):
        result = finalized_request.finalize_paper_order_request(
            candidate=valid_candidate(),
            review=valid_review(),
            write_artifacts=False,
        )
    assert result.request is not None
    return result.request


def confirm(**overrides):
    request = overrides.pop("request", valid_request())
    confirmer = overrides.pop("confirmer", "manual-confirmer")
    with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": ""}):
        return manual_confirmation.create_manual_execution_confirmation(
            request=request,
            confirmer=confirmer,
            write_artifacts=False,
            **overrides,
        )


def rendered_artifact() -> str:
    with tempfile.TemporaryDirectory() as tmp:
        result = manual_confirmation.create_manual_execution_confirmation(
            request=valid_request(),
            confirmer="manual-confirmer",
            output_root=Path(tmp),
        )
        return Path(result.report_path or "").read_text(encoding="utf-8")


def source_text() -> str:
    return (RUNTIME_PATH / "manual_execution_confirmation.py").read_text(encoding="utf-8")


def env_files() -> set[str]:
    return {path.as_posix() for path in ROOT.glob(".env*")}


if __name__ == "__main__":
    unittest.main()
