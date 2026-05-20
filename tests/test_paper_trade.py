from __future__ import annotations

import importlib.util
import sys
import unittest
from dataclasses import replace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "runtime"
PAPER_TRADE_PATH = RUNTIME_PATH / "paper_trade.py"
ACCOUNT_PATH = RUNTIME_PATH / "alpaca_paper_account.py"

if str(RUNTIME_PATH) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PATH))

account_spec = importlib.util.spec_from_file_location("alpaca_paper_account", ACCOUNT_PATH)
alpaca_paper_account = importlib.util.module_from_spec(account_spec)
assert account_spec.loader is not None
sys.modules["alpaca_paper_account"] = alpaca_paper_account
account_spec.loader.exec_module(alpaca_paper_account)

paper_spec = importlib.util.spec_from_file_location("paper_trade", PAPER_TRADE_PATH)
paper_trade = importlib.util.module_from_spec(paper_spec)
assert paper_spec.loader is not None
sys.modules["paper_trade"] = paper_trade
paper_spec.loader.exec_module(paper_trade)


class PaperTradeTests(unittest.TestCase):
    def test_valid_proposal_passes_schema_validation(self) -> None:
        validation = paper_trade.validate_proposal(valid_proposal())

        self.assertTrue(validation.passed)

    def test_missing_symbol_fails(self) -> None:
        validation = paper_trade.validate_proposal(replace(valid_proposal(), symbol=None))

        self.assertFalse(validation.passed)
        self.assertIn("missing symbol", validation.violations)

    def test_missing_fixed_risk_fails(self) -> None:
        evaluation = paper_trade.evaluate_risk(
            replace(valid_proposal(), risk_per_share=None),
            alpaca_paper_account.default_mock_snapshot(),
        )

        self.assertEqual(evaluation.decision, paper_trade.RISK_REJECTED)
        self.assertIn("missing fixed risk", evaluation.rejection_reasons)

    def test_paper_trading_only_false_fails(self) -> None:
        validation = paper_trade.validate_proposal(
            replace(valid_proposal(), paper_trading_only=False)
        )
        evaluation = paper_trade.evaluate_risk(
            replace(valid_proposal(), paper_trading_only=False),
            alpaca_paper_account.default_mock_snapshot(),
        )

        self.assertFalse(validation.passed)
        self.assertIn("missing paper trading flag", evaluation.rejection_reasons)

    def test_journal_ready_false_fails(self) -> None:
        validation = paper_trade.validate_proposal(replace(valid_proposal(), journal_ready=False))

        self.assertFalse(validation.passed)
        self.assertIn("missing journal readiness", validation.violations)

    def test_adlc_status_not_pass_fails(self) -> None:
        validation = paper_trade.validate_proposal(
            replace(valid_proposal(), adlc_compliance_status="FAIL")
        )

        self.assertFalse(validation.passed)
        self.assertIn("ADLC compliance status is not PASS", validation.violations)

    def test_max_loss_over_limit_is_rejected(self) -> None:
        evaluation = paper_trade.evaluate_risk(
            replace(valid_proposal(), max_loss_amount="1000"),
            alpaca_paper_account.default_mock_snapshot(),
        )

        self.assertEqual(evaluation.decision, paper_trade.RISK_REJECTED)
        self.assertIn("max loss exceeds limit", evaluation.rejection_reasons)

    def test_daily_risk_blocked_rejects_proposal(self) -> None:
        blocked_account = alpaca_paper_account.PaperAccountSnapshot(
            account=alpaca_paper_account.PaperAccountState(
                account_id="blocked",
                cash="1000",
                equity="1000",
                buying_power="0",
                portfolio_value="1000",
                day_trade_count=3,
                trading_blocked=True,
                transfers_blocked=False,
                account_blocked=False,
                status="ACTIVE",
                read_status="READ_OK",
                trading_allowed_in_principle=False,
                violations=("trading_blocked",),
            ),
            positions=(),
            existing_orders=(),
        )

        evaluation = paper_trade.evaluate_risk(valid_proposal(), blocked_account)

        self.assertEqual(evaluation.decision, paper_trade.RISK_REJECTED)
        self.assertIn("daily risk state blocked", evaluation.rejection_reasons)

    def test_malformed_proposal_rejected(self) -> None:
        evaluation = paper_trade.evaluate_risk(None, alpaca_paper_account.default_mock_snapshot())

        self.assertEqual(evaluation.decision, paper_trade.RISK_REJECTED)
        self.assertIn("malformed proposal", evaluation.rejection_reasons)

    def test_risk_approved_proposal_is_still_not_executable(self) -> None:
        evaluation = paper_trade.evaluate_risk(
            valid_proposal(),
            alpaca_paper_account.default_mock_snapshot(),
        )

        self.assertEqual(evaluation.decision, paper_trade.RISK_APPROVED)
        self.assertFalse(evaluation.executable)

    def test_no_alpaca_order_is_created(self) -> None:
        proposal = valid_proposal()
        evaluation = paper_trade.evaluate_risk(
            proposal,
            alpaca_paper_account.default_mock_snapshot(),
        )

        self.assertEqual(proposal.paper_trading_only, True)
        self.assertEqual(evaluation.decision, paper_trade.RISK_APPROVED)
        self.assertFalse(hasattr(evaluation, "order_id"))

    def test_no_buy_sell_cancel_replace_methods_exist(self) -> None:
        proposal = valid_proposal()

        self.assertFalse(hasattr(proposal, "buy"))
        self.assertFalse(hasattr(proposal, "sell"))
        self.assertFalse(hasattr(proposal, "cancel_order"))
        self.assertFalse(hasattr(proposal, "replace_order"))


def valid_proposal() -> paper_trade.PaperTradeProposal:
    return paper_trade.deterministic_valid_proposal("market_open")


if __name__ == "__main__":
    unittest.main()
