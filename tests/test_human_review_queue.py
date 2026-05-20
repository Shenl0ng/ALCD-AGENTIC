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


class HumanReviewQueueTests(unittest.TestCase):
    def test_human_review_queue_model_exists(self) -> None:
        self.assertTrue(hasattr(review_queue, "HumanReviewQueue"))

    def test_human_review_record_model_exists(self) -> None:
        self.assertTrue(hasattr(review_queue, "HumanReviewRecord"))

    def test_review_validator_exists(self) -> None:
        self.assertTrue(hasattr(review_queue, "validate_review"))

    def test_valid_candidate_can_enter_review_queue(self) -> None:
        result = create_review()

        self.assertTrue(result.validation.passed)
        self.assertEqual(result.candidate_id, valid_candidate().candidate_id)

    def test_human_can_approve_candidate_for_future_request_finalization(self) -> None:
        result = create_review(
            review_status=review_queue.HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST
        )

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST)
        self.assertIn("future Paper Order Request", result.reason)

    def test_human_can_reject_candidate(self) -> None:
        result = create_review(review_status=review_queue.HUMAN_REVIEW_REJECTED)

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_REJECTED)

    def test_human_can_request_more_information(self) -> None:
        result = create_review(review_status=review_queue.HUMAN_REVIEW_NEEDS_MORE_INFORMATION)

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_NEEDS_MORE_INFORMATION)

    def test_expired_candidate_blocks_review(self) -> None:
        result = create_review(candidate_expired=True)

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_BLOCKED)
        self.assertIn("candidate expired", result.reason)

    def test_missing_candidate_blocks_review(self) -> None:
        result = create_review(candidate=None)

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_BLOCKED)
        self.assertIn("candidate missing", result.reason)

    def test_candidate_not_created_blocks_review(self) -> None:
        candidate = replace(
            valid_candidate(),
            candidate_status=candidate_module.PAPER_ORDER_CANDIDATE_BLOCKED,
        )
        result = create_review(candidate=candidate)

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_BLOCKED)
        self.assertIn("PAPER_ORDER_CANDIDATE_CREATED", result.reason)

    def test_missing_reviewer_blocks_review(self) -> None:
        result = create_review(reviewer="")

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_BLOCKED)
        self.assertIn("reviewer is required", result.reason)

    def test_missing_paper_only_confirmation_blocks_review(self) -> None:
        result = create_review(paper_only_confirmation=False)

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_BLOCKED)
        self.assertIn("paper_only_confirmation", result.reason)

    def test_missing_no_live_trading_confirmation_blocks_review(self) -> None:
        result = create_review(no_live_trading_confirmation=False)

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_BLOCKED)
        self.assertIn("no_live_trading_confirmation", result.reason)

    def test_missing_risk_review_confirmation_blocks_review(self) -> None:
        result = create_review(risk_review_confirmation=False)

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_BLOCKED)
        self.assertIn("risk_review_confirmation", result.reason)

    def test_missing_evaluation_review_confirmation_blocks_review(self) -> None:
        result = create_review(evaluation_review_confirmation=False)

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_BLOCKED)
        self.assertIn("evaluation_review_confirmation", result.reason)

    def test_missing_negative_case_review_confirmation_blocks_review(self) -> None:
        result = create_review(negative_case_review_confirmation=False)

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_BLOCKED)
        self.assertIn("negative_case_review_confirmation", result.reason)

    def test_missing_journal_review_confirmation_blocks_review(self) -> None:
        result = create_review(journal_review_confirmation=False)

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_BLOCKED)
        self.assertIn("journal_review_confirmation", result.reason)

    def test_broker_execution_allowed_true_blocks_review(self) -> None:
        result = create_review(candidate=replace(valid_candidate(), broker_execution_allowed=True))

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_BLOCKED)
        self.assertIn("broker_execution_allowed=true", result.reason)

    def test_live_trading_allowed_true_blocks_review(self) -> None:
        result = create_review(candidate=replace(valid_candidate(), live_trading_allowed=True))

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_BLOCKED)
        self.assertIn("live_trading_allowed=true", result.reason)

    def test_missing_human_approval_required_true_blocks_review(self) -> None:
        result = create_review(candidate=replace(valid_candidate(), human_approval_required=False))

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_BLOCKED)
        self.assertIn("human_approval_required=true", result.reason)

    def test_missing_manual_execution_confirmation_required_true_blocks_review(self) -> None:
        result = create_review(
            candidate=replace(valid_candidate(), manual_execution_confirmation_required=False)
        )

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_BLOCKED)
        self.assertIn("manual_execution_confirmation_required=true", result.reason)

    def test_execution_flag_true_blocks_review(self) -> None:
        with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": "true"}):
            result = review_queue.create_human_review_record(
                candidate=valid_candidate(),
                reviewer="human-reviewer",
                review_status=review_queue.HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST,
                review_notes="Reviewed candidate.",
                write_artifacts=False,
            )

        self.assertEqual(result.final_status, review_queue.HUMAN_REVIEW_BLOCKED)
        self.assertIn("PAPER_ORDER_EXECUTION_ENABLED=true", result.reason)

    def test_review_does_not_create_finalized_paper_order_request(self) -> None:
        self.assertFalse(create_review().finalized_paper_order_request_created)

    def test_review_does_not_create_manual_execution_confirmation(self) -> None:
        result = create_review()

        self.assertFalse(result.manual_execution_confirmation_created)
        self.assertNotIn("manual_execution_confirmation", source_imports())

    def test_review_does_not_send_orders(self) -> None:
        result = create_review()

        self.assertFalse(result.order_sent)
        self.assertNotIn("submit_order", source_text())
        self.assertNotIn("place_order", source_text())
        self.assertNotIn("send_paper_order_request", source_text())

    def test_review_does_not_create_broker_execution_readiness(self) -> None:
        self.assertFalse(create_review().broker_execution_readiness)

    def test_review_artifact_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = review_queue.create_human_review_record(
                candidate=valid_candidate(),
                reviewer="human-reviewer",
                review_status=review_queue.HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST,
                review_notes="Reviewed candidate.",
                output_root=Path(tmp),
            )

            self.assertTrue(Path(result.report_path or "").exists())

    def test_review_journal_entry_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = review_queue.create_human_review_record(
                candidate=valid_candidate(),
                reviewer="human-reviewer",
                review_status=review_queue.HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST,
                review_notes="Reviewed candidate.",
                output_root=Path(tmp),
            )

            self.assertTrue(Path(result.journal_path or "").exists())

    def test_artifact_states_human_review_does_not_authorize_order_sending(self) -> None:
        rendered = rendered_review_artifact()

        self.assertIn("Human review does not authorize order sending.", rendered)

    def test_artifact_states_manual_execution_confirmation_required_later(self) -> None:
        rendered = rendered_review_artifact()

        self.assertIn("Manual Execution Confirmation is still required later.", rendered)

    def test_artifact_states_no_order_was_sent(self) -> None:
        rendered = rendered_review_artifact()

        self.assertIn("No order was sent.", rendered)

    def test_artifact_states_no_broker_execution_readiness_created(self) -> None:
        rendered = rendered_review_artifact()

        self.assertIn("No broker execution readiness was created.", rendered)

    def test_artifact_states_live_trading_remains_unsupported(self) -> None:
        rendered = rendered_review_artifact()

        self.assertIn("Live trading remains unsupported.", rendered)

    def test_no_alpaca_order_api_calls_exist(self) -> None:
        source = source_text()

        self.assertNotIn("alpaca_paper_order_adapter", source)
        self.assertNotIn("UrlLibAlpacaPaperOrderClient", source)
        self.assertNotIn("urlopen", source)
        self.assertNotIn("/v2/orders", source)

    def test_no_live_trading_exists(self) -> None:
        source = source_text()

        self.assertFalse(create_review().live_trading_assumption)
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
        create_review()

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


def create_review(**overrides):
    candidate = overrides.pop("candidate", valid_candidate())
    with patch.dict(os.environ, {"PAPER_ORDER_EXECUTION_ENABLED": ""}):
        return review_queue.create_human_review_record(
            candidate=candidate,
            reviewer=overrides.pop("reviewer", "human-reviewer"),
            review_status=overrides.pop(
                "review_status", review_queue.HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST
            ),
            review_notes=overrides.pop("review_notes", "Reviewed candidate."),
            write_artifacts=False,
            **overrides,
        )


def rendered_review_artifact() -> str:
    with tempfile.TemporaryDirectory() as tmp:
        result = review_queue.create_human_review_record(
            candidate=valid_candidate(),
            reviewer="human-reviewer",
            review_status=review_queue.HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST,
            review_notes="Reviewed candidate.",
            output_root=Path(tmp),
        )
        return Path(result.report_path or "").read_text(encoding="utf-8")


def source_text() -> str:
    return (RUNTIME_PATH / "human_review_queue.py").read_text(encoding="utf-8")


def source_imports() -> str:
    return "\n".join(
        line
        for line in source_text().splitlines()
        if line.startswith("from ") or line.startswith("import ")
    )


def env_files() -> set[str]:
    return {path.as_posix() for path in ROOT.glob(".env*")}


if __name__ == "__main__":
    unittest.main()
