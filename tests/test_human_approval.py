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
strategy_evaluation_harness = load_module("strategy_evaluation_harness")
evaluation_first_gate = load_module("evaluation_first_gate")
human_approval = load_module("human_approval")


class HumanApprovalTests(unittest.TestCase):
    def test_risk_approved_proposal_enters_human_review(self) -> None:
        proposal = valid_proposal()
        risk = approved_risk(proposal)

        record = human_approval.enter_human_review(proposal, risk, passed_gate(proposal, risk))

        self.assertEqual(record.approval_state, human_approval.HUMAN_REVIEW_REQUIRED)

    def test_human_approval_cannot_start_without_gate_pass(self) -> None:
        proposal = valid_proposal()
        risk = approved_risk(proposal)

        record = human_approval.enter_human_review(proposal, risk)

        self.assertEqual(record.approval_state, human_approval.HUMAN_APPROVAL_INVALID)

    def test_non_risk_approved_proposal_cannot_enter_human_review(self) -> None:
        proposal = valid_proposal()
        risk = paper_trade.RiskEvaluation(
            decision=paper_trade.RISK_REJECTED,
            rejection_reasons=("max loss exceeds limit",),
            proposal_validation=paper_trade.validate_proposal(proposal),
        )

        record = human_approval.enter_human_review(proposal, risk)

        self.assertEqual(record.approval_state, human_approval.HUMAN_APPROVAL_INVALID)

    def test_paper_trading_only_false_blocks_approval(self) -> None:
        proposal = replace(valid_proposal(), paper_trading_only=False)
        validation = validate(proposal, approved_risk(valid_proposal()))

        self.assertFalse(validation.passed)
        self.assertIn("proposal is not paper-only", validation.violations)

    def test_journal_ready_false_blocks_approval(self) -> None:
        proposal = replace(valid_proposal(), journal_ready=False)
        validation = validate(proposal, approved_risk(valid_proposal()))

        self.assertFalse(validation.passed)
        self.assertIn("journal_ready is false", validation.violations)

    def test_adlc_fail_blocks_approval(self) -> None:
        proposal = replace(valid_proposal(), adlc_compliance_status="FAIL")
        validation = validate(proposal, approved_risk(valid_proposal()))

        self.assertFalse(validation.passed)
        self.assertIn("ADLC compliance is not PASS", validation.violations)

    def test_missing_reviewer_blocks_approval(self) -> None:
        proposal = valid_proposal()
        approval = human_approval.deterministic_human_approval(proposal, reviewer=None)

        validation = human_approval.validate_approval(proposal, approved_risk(proposal), approval)

        self.assertFalse(validation.passed)
        self.assertIn("reviewer is missing", validation.violations)

    def test_human_approval_cannot_bypass_risk_approval(self) -> None:
        proposal = valid_proposal()
        approval = replace(
            human_approval.deterministic_human_approval(proposal),
            bypass_risk_manager=True,
        )
        validation = human_approval.validate_approval(proposal, approved_risk(proposal), approval)

        self.assertFalse(validation.passed)
        self.assertIn("approval attempts to bypass Risk Manager", validation.violations)

    def test_human_approval_cannot_bypass_journal_readiness(self) -> None:
        proposal = valid_proposal()
        approval = replace(
            human_approval.deterministic_human_approval(proposal),
            bypass_journal_agent=True,
        )
        validation = human_approval.validate_approval(proposal, approved_risk(proposal), approval)

        self.assertFalse(validation.passed)
        self.assertIn("approval attempts to bypass Journal Agent", validation.violations)

    def test_human_approval_cannot_authorize_live_trading(self) -> None:
        proposal = valid_proposal()
        approval = replace(
            human_approval.deterministic_human_approval(proposal),
            live_trading_authorized=True,
        )
        validation = human_approval.validate_approval(proposal, approved_risk(proposal), approval)

        self.assertFalse(validation.passed)
        self.assertIn("approval attempts to authorize live trading", validation.violations)

    def test_human_rejection_blocks_downstream_flow(self) -> None:
        proposal = valid_proposal()
        approval = human_approval.deterministic_human_approval(
            proposal,
            human_approval.HUMAN_REJECTED,
        )

        self.assertEqual(approval.approval_state, human_approval.HUMAN_REJECTED)

    def test_approval_record_is_journaled(self) -> None:
        proposal = valid_proposal()
        approval = human_approval.deterministic_human_approval(proposal)
        journal = human_approval.commit_journal_entry(
            proposal=proposal,
            risk_status=paper_trade.RISK_APPROVED,
            human_approval_status=approval.approval_state,
            gatekeeper_status="EXECUTION_BLOCKED",
            event_type="human_approved_for_paper_only",
            reason_for_final_decision="Approval recorded; execution remains blocked.",
            lessons_or_notes="No order was requested.",
        )

        self.assertEqual(journal.proposal_id, proposal.proposal_id)
        self.assertEqual(journal.human_approval_status, human_approval.HUMAN_APPROVED_FOR_PAPER_ONLY)
        self.assertTrue(journal.paper_trading_confirmation)

    def test_execution_remains_blocked_after_human_approval(self) -> None:
        proposal = valid_proposal()
        approval = human_approval.deterministic_human_approval(proposal)
        journal = human_approval.commit_journal_entry(
            proposal=proposal,
            risk_status=paper_trade.RISK_APPROVED,
            human_approval_status=approval.approval_state,
            gatekeeper_status="EXECUTION_BLOCKED",
            event_type="final_decision",
            reason_for_final_decision="No execution authority exists.",
            lessons_or_notes="Human approval is paper-only.",
        )

        self.assertEqual(journal.gatekeeper_status, "EXECUTION_BLOCKED")

    def test_no_alpaca_order_is_created(self) -> None:
        approval = human_approval.deterministic_human_approval(valid_proposal())

        self.assertFalse(hasattr(approval, "order_id"))
        self.assertFalse(hasattr(approval, "submit_order"))

    def test_no_buy_sell_cancel_replace_methods_exist(self) -> None:
        approval = human_approval.deterministic_human_approval(valid_proposal())

        self.assertFalse(hasattr(approval, "buy"))
        self.assertFalse(hasattr(approval, "sell"))
        self.assertFalse(hasattr(approval, "cancel_order"))
        self.assertFalse(hasattr(approval, "replace_order"))


def valid_proposal():
    return paper_trade.deterministic_valid_proposal("market_open")


def approved_risk(proposal):
    return paper_trade.evaluate_risk(proposal, alpaca_paper_account.default_mock_snapshot())


def validate(proposal, risk):
    approval = human_approval.deterministic_human_approval(proposal)
    return human_approval.validate_approval(proposal, risk, approval)


class JournalFixture:
    reason_for_final_decision = "Evaluation fixture with clear context and fixed risk."
    lessons_or_notes = "Strong journal readiness for deterministic approval gate test."


def passed_gate(proposal, risk):
    report = strategy_evaluation_harness.evaluate_strategy(
        strategy_evaluation_harness.StrategyEvaluationInput(
            proposal=proposal,
            risk_evaluation=risk,
            journal_entry=JournalFixture(),
        )
    )
    return evaluation_first_gate.evaluate_gate(report)


if __name__ == "__main__":
    unittest.main()
