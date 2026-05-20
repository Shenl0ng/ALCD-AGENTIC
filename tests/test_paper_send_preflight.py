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
paper_send_preflight = load_module("paper_send_preflight")


class PaperSendPreflightTests(unittest.TestCase):
    def test_paper_send_preflight_model_exists(self) -> None:
        self.assertTrue(hasattr(paper_send_preflight, "PaperSendPreflight"))

    def test_preflight_validator_exists(self) -> None:
        self.assertTrue(hasattr(paper_send_preflight, "validate_paper_send_preflight"))

    def test_valid_request_and_confirmation_can_produce_send_allowed(self) -> None:
        result = preflight()

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_ALLOWED)
        self.assertIsNotNone(result.preflight)

    def test_missing_finalized_request_blocks_preflight(self) -> None:
        result = preflight(request=None)

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_BLOCKED)
        self.assertIn("finalized request missing", result.reason)

    def test_missing_manual_confirmation_blocks_preflight(self) -> None:
        result = preflight(confirmation=None)

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_BLOCKED)
        self.assertIn("manual confirmation missing", result.reason)

    def test_request_not_finalized_blocks_preflight(self) -> None:
        request = replace(
            valid_request(),
            request_status=finalized_request.PAPER_ORDER_REQUEST_BLOCKED,
        )
        result = preflight(request=request)

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("PAPER_ORDER_REQUEST_FINALIZED", result.reason)

    def test_confirmation_not_confirmed_for_preflight_blocks_preflight(self) -> None:
        confirmation = valid_confirmation(
            confirmation_status=manual_confirmation.MANUAL_EXECUTION_REJECTED
        )
        result = preflight(confirmation=confirmation)

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT", result.reason)

    def test_paper_trading_only_false_blocks_preflight(self) -> None:
        result = preflight(request=replace(valid_request(), paper_trading_only=False))

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("paper_trading_only=true", result.reason)

    def test_live_trading_allowed_true_blocks_preflight(self) -> None:
        result = preflight(request=replace(valid_request(), live_trading_allowed=True))

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("live_trading_allowed=false", result.reason)

    def test_broker_execution_allowed_true_blocks_preflight(self) -> None:
        result = preflight(request=replace(valid_request(), broker_execution_allowed=True))

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("broker_execution_allowed=false", result.reason)

    def test_paper_send_preflight_required_false_blocks_preflight(self) -> None:
        confirmation = replace(valid_confirmation(), paper_send_preflight_required=False)
        result = preflight(confirmation=confirmation)

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("paper_send_preflight_required=true", result.reason)

    def test_notional_over_100_blocks_preflight(self) -> None:
        result = preflight(request=replace(valid_request(), notional="101"))

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("notional > 100 USD", result.reason)

    def test_market_order_blocks_preflight(self) -> None:
        result = preflight(request=replace(valid_request(), order_type="market"))

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("order type must be limit", result.reason)

    def test_non_day_time_in_force_blocks_preflight(self) -> None:
        result = preflight(request=replace(valid_request(), time_in_force="gtc"))

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("time in force must be day", result.reason)

    def test_short_selling_blocks_preflight(self) -> None:
        result = preflight(short_selling=True)

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("short selling is blocked", result.reason)

    def test_crypto_blocks_preflight(self) -> None:
        result = preflight(crypto=True)

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("crypto is blocked", result.reason)

    def test_options_blocks_preflight(self) -> None:
        result = preflight(options=True)

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("options are blocked", result.reason)

    def test_margin_leverage_blocks_preflight(self) -> None:
        result = preflight(margin_or_leverage=True)

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("margin/leverage is blocked", result.reason)

    def test_extended_hours_blocks_preflight(self) -> None:
        result = preflight(extended_hours=True)

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("extended hours are blocked", result.reason)

    def test_multiple_orders_block_preflight(self) -> None:
        result = preflight(order_count=2)

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("one order only", result.reason)

    def test_batch_behavior_blocks_preflight(self) -> None:
        result = preflight(batch_behavior=True)

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("batch behavior is blocked", result.reason)

    def test_cancel_replace_behavior_blocks_preflight(self) -> None:
        result = preflight(cancel_replace_behavior=True)

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("cancel/replace behavior is blocked", result.reason)

    def test_execution_flag_true_blocks_preflight(self) -> None:
        with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": "true"}):
            result = paper_send_preflight.run_paper_send_preflight(
                request=valid_request(),
                confirmation=valid_confirmation(),
                write_artifacts=False,
            )

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("PAPER_ORDER_EXECUTION_ENABLED=true", result.reason)

    def test_live_endpoint_configured_blocks_preflight(self) -> None:
        result = preflight(live_endpoint_configured=True)

        self.assertEqual(result.final_status, paper_send_preflight.PAPER_ORDER_SEND_INVALID)
        self.assertIn("live endpoint configured is blocked", result.reason)

    def test_preflight_hardcodes_broker_execution_allowed_false(self) -> None:
        self.assertFalse(preflight().preflight.broker_execution_allowed)

    def test_preflight_hardcodes_live_trading_allowed_false(self) -> None:
        self.assertFalse(preflight().preflight.live_trading_allowed)

    def test_preflight_artifact_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = paper_send_preflight.run_paper_send_preflight(
                request=valid_request(),
                confirmation=valid_confirmation(),
                output_root=Path(tmp),
            )

            self.assertTrue(Path(result.report_path or "").exists())

    def test_preflight_journal_entry_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = paper_send_preflight.run_paper_send_preflight(
                request=valid_request(),
                confirmation=valid_confirmation(),
                output_root=Path(tmp),
            )

            self.assertTrue(Path(result.journal_path or "").exists())

    def test_artifact_states_paper_send_preflight_does_not_send_orders(self) -> None:
        self.assertIn("Paper Send Preflight does not send orders.", rendered_artifact())

    def test_artifact_states_send_allowed_is_not_broker_execution(self) -> None:
        self.assertIn("PAPER_ORDER_SEND_ALLOWED is not broker execution.", rendered_artifact())

    def test_artifact_states_send_allowed_does_not_call_alpaca(self) -> None:
        self.assertIn("PAPER_ORDER_SEND_ALLOWED does not call Alpaca.", rendered_artifact())

    def test_artifact_states_execution_flag_was_not_enabled(self) -> None:
        self.assertIn("PAPER_ORDER_EXECUTION_ENABLED was not enabled.", rendered_artifact())

    def test_artifact_states_no_order_was_sent(self) -> None:
        self.assertIn("No order was sent.", rendered_artifact())

    def test_artifact_states_no_broker_execution_readiness_created(self) -> None:
        self.assertIn("No broker execution readiness was created.", rendered_artifact())

    def test_artifact_states_live_trading_remains_unsupported(self) -> None:
        self.assertIn("Live trading remains unsupported.", rendered_artifact())

    def test_preflight_does_not_send_orders(self) -> None:
        result = preflight()

        self.assertFalse(result.order_sent)
        self.assertNotIn("submit_order", source_text())
        self.assertNotIn("place_order", source_text())
        self.assertNotIn("send_paper_order_request", source_text())

    def test_preflight_does_not_call_alpaca_order_api(self) -> None:
        source = source_text()

        self.assertFalse(preflight().alpaca_order_api_called)
        self.assertNotIn("alpaca_paper_order_adapter", source)
        self.assertNotIn("UrlLibAlpacaPaperOrderClient", source)
        self.assertNotIn("urlopen", source)
        self.assertNotIn("/v2/orders", source)

    def test_preflight_does_not_create_broker_execution_readiness(self) -> None:
        self.assertFalse(preflight().broker_execution_readiness)

    def test_no_live_trading_exists(self) -> None:
        source = source_text()

        self.assertFalse(preflight().live_trading_assumption)
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
        preflight()

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


def valid_confirmation(**overrides):
    request = overrides.pop("request", valid_request())
    with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": ""}):
        result = manual_confirmation.create_manual_execution_confirmation(
            request=request,
            confirmer="manual-confirmer",
            write_artifacts=False,
            **overrides,
        )
    assert result.confirmation is not None
    return result.confirmation


def preflight(**overrides):
    request = overrides.pop("request", valid_request())
    confirmation = overrides.pop("confirmation", valid_confirmation())
    with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": ""}):
        return paper_send_preflight.run_paper_send_preflight(
            request=request,
            confirmation=confirmation,
            write_artifacts=False,
            **overrides,
        )


def rendered_artifact() -> str:
    with tempfile.TemporaryDirectory() as tmp:
        result = paper_send_preflight.run_paper_send_preflight(
            request=valid_request(),
            confirmation=valid_confirmation(),
            output_root=Path(tmp),
        )
        return Path(result.report_path or "").read_text(encoding="utf-8")


def source_text() -> str:
    return (RUNTIME_PATH / "paper_send_preflight.py").read_text(encoding="utf-8")


def env_files() -> set[str]:
    return {path.as_posix() for path in ROOT.glob(".env*")}


if __name__ == "__main__":
    unittest.main()
