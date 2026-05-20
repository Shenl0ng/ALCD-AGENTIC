from __future__ import annotations

import importlib.util
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
paper_trade = load_module("paper_trade")
human_approval = load_module("human_approval")
paper_order_request = load_module("paper_order_request")


class PaperOrderRequestTests(unittest.TestCase):
    def test_valid_approved_proposal_creates_paper_order_request(self) -> None:
        _, _, _, _, request, validation = valid_request_bundle()

        self.assertEqual(
            request.final_status,
            paper_order_request.PAPER_ORDER_REQUEST_CREATED,
        )
        self.assertTrue(validation.passed)

    def test_missing_risk_approval_blocks_request(self) -> None:
        proposal = paper_trade.deterministic_valid_proposal()
        risk = paper_trade.RiskEvaluation(
            decision=paper_trade.RISK_REJECTED,
            rejection_reasons=("max loss exceeds limit",),
            proposal_validation=paper_trade.validate_proposal(proposal),
        )
        approval = human_approval.deterministic_human_approval(proposal)
        journal = approval_journal(proposal, risk, approval)

        status = paper_order_request.gatekeeper_request_status(
            proposal=proposal,
            risk_evaluation=risk,
            approval=approval,
            journal_commit=journal,
        )

        self.assertEqual(status, paper_order_request.EXECUTION_BLOCKED)

    def test_missing_human_approval_blocks_request(self) -> None:
        proposal, risk, _, journal, _, _ = valid_request_bundle()

        status = paper_order_request.gatekeeper_request_status(
            proposal=proposal,
            risk_evaluation=risk,
            approval=None,
            journal_commit=journal,
        )

        self.assertEqual(status, paper_order_request.EXECUTION_BLOCKED)

    def test_human_rejected_blocks_request(self) -> None:
        proposal = paper_trade.deterministic_valid_proposal()
        risk = paper_trade.evaluate_risk(proposal, alpaca_paper_account.default_mock_snapshot())
        approval = human_approval.deterministic_human_approval(
            proposal,
            human_approval.HUMAN_REJECTED,
        )
        journal = approval_journal(proposal, risk, approval)

        status = paper_order_request.gatekeeper_request_status(
            proposal=proposal,
            risk_evaluation=risk,
            approval=approval,
            journal_commit=journal,
        )

        self.assertEqual(status, paper_order_request.EXECUTION_BLOCKED)

    def test_missing_journal_commit_blocks_request(self) -> None:
        proposal, risk, approval, _, _, _ = valid_request_bundle()

        status = paper_order_request.gatekeeper_request_status(
            proposal=proposal,
            risk_evaluation=risk,
            approval=approval,
            journal_commit=None,
        )

        self.assertEqual(status, paper_order_request.EXECUTION_BLOCKED)

    def test_adlc_fail_blocks_request(self) -> None:
        proposal = replace(
            paper_trade.deterministic_valid_proposal(),
            adlc_compliance_status="FAIL",
        )
        risk = paper_trade.evaluate_risk(proposal, alpaca_paper_account.default_mock_snapshot())
        approval = human_approval.deterministic_human_approval(proposal)
        journal = approval_journal(proposal, risk, approval)

        status = paper_order_request.gatekeeper_request_status(
            proposal=proposal,
            risk_evaluation=risk,
            approval=approval,
            journal_commit=journal,
        )

        self.assertEqual(status, paper_order_request.EXECUTION_BLOCKED)

    def test_paper_trading_only_false_blocks_request(self) -> None:
        proposal = replace(
            paper_trade.deterministic_valid_proposal(),
            paper_trading_only=False,
        )
        risk = paper_trade.evaluate_risk(proposal, alpaca_paper_account.default_mock_snapshot())
        approval = human_approval.deterministic_human_approval(proposal)
        journal = approval_journal(proposal, risk, approval)

        status = paper_order_request.gatekeeper_request_status(
            proposal=proposal,
            risk_evaluation=risk,
            approval=approval,
            journal_commit=journal,
        )

        self.assertEqual(status, paper_order_request.EXECUTION_BLOCKED)

    def test_broker_execution_allowed_true_fails_validation(self) -> None:
        proposal, risk, approval, journal, request, _ = valid_request_bundle()
        request = replace(request, broker_execution_allowed=True)

        validation = paper_order_request.validate_paper_order_request(
            request,
            proposal=proposal,
            risk_evaluation=risk,
            approval=approval,
            journal_commit=journal,
        )

        self.assertFalse(validation.passed)
        self.assertIn("broker_execution_allowed is true", validation.violations)

    def test_live_trading_allowed_true_fails_validation(self) -> None:
        proposal, risk, approval, journal, request, _ = valid_request_bundle()
        request = replace(request, live_trading_allowed=True)

        validation = paper_order_request.validate_paper_order_request(
            request,
            proposal=proposal,
            risk_evaluation=risk,
            approval=approval,
            journal_commit=journal,
        )

        self.assertFalse(validation.passed)
        self.assertIn("live_trading_allowed is true", validation.violations)

    def test_missing_quantity_and_notional_fails(self) -> None:
        proposal, risk, approval, journal, request, _ = valid_request_bundle()
        request = replace(request, quantity=None, notional=None)

        validation = paper_order_request.validate_paper_order_request(
            request,
            proposal=proposal,
            risk_evaluation=risk,
            approval=approval,
            journal_commit=journal,
        )

        self.assertFalse(validation.passed)
        self.assertIn("quantity and notional are both missing", validation.violations)

    def test_invalid_gatekeeper_status_blocks_request(self) -> None:
        proposal, risk, approval, journal, request, _ = valid_request_bundle()
        request = replace(request, gatekeeper_status="EXECUTION_BLOCKED")

        validation = paper_order_request.validate_paper_order_request(
            request,
            proposal=proposal,
            risk_evaluation=risk,
            approval=approval,
            journal_commit=journal,
        )

        self.assertFalse(validation.passed)
        self.assertIn(
            "gatekeeper status is not READY_FOR_PAPER_ORDER_REQUEST",
            validation.violations,
        )

    def test_gatekeeper_cannot_output_order_placed(self) -> None:
        with self.assertRaises(ValueError):
            paper_order_request.assert_gatekeeper_output_allowed("ORDER_PLACED")

    def test_gatekeeper_cannot_output_buy_or_sell(self) -> None:
        for status in ("BUY", "SELL"):
            with self.assertRaises(ValueError):
                paper_order_request.assert_gatekeeper_output_allowed(status)

    def test_gatekeeper_cannot_output_sent_to_broker(self) -> None:
        with self.assertRaises(ValueError):
            paper_order_request.assert_gatekeeper_output_allowed("SENT_TO_BROKER")

    def test_no_alpaca_order_is_created(self) -> None:
        _, _, _, _, request, _ = valid_request_bundle()

        self.assertFalse(hasattr(request, "alpaca_order_id"))
        self.assertFalse(hasattr(request, "submit_order"))

    def test_no_buy_sell_cancel_replace_methods_exist(self) -> None:
        _, _, _, _, request, _ = valid_request_bundle()

        self.assertFalse(hasattr(request, "buy"))
        self.assertFalse(hasattr(request, "sell"))
        self.assertFalse(hasattr(request, "cancel_order"))
        self.assertFalse(hasattr(request, "replace_order"))


def valid_request_bundle():
    return paper_order_request.deterministic_valid_request()


def approval_journal(proposal, risk, approval):
    return human_approval.commit_journal_entry(
        proposal=proposal,
        risk_status=risk.decision,
        human_approval_status=approval.approval_state,
        gatekeeper_status=paper_order_request.EXECUTION_BLOCKED,
        event_type="human_approved_for_paper_only",
        reason_for_final_decision="Human paper-only approval recorded.",
        lessons_or_notes="Journal commit precedes paper order request.",
    )


if __name__ == "__main__":
    unittest.main()
