from __future__ import annotations

import importlib.util
import sys
import unittest
from dataclasses import dataclass, replace
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


strategy_evaluation_harness = load_module("strategy_evaluation_harness")


class StrategyEvaluationHarnessTests(unittest.TestCase):
    def test_harness_imports_without_importing_alpaca_account_module(self) -> None:
        module_name = "strategy_evaluation_harness_import_check"
        sys.modules.pop("alpaca_paper_account", None)
        path = RUNTIME_PATH / "strategy_evaluation_harness.py"
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        self.assertNotIn("alpaca_paper_account", sys.modules)

    def test_test_file_does_not_import_alpaca_account_module(self) -> None:
        source = Path(__file__).read_text(encoding="utf-8")
        import_lines = [
            line.strip()
            for line in source.splitlines()
            if line.strip().startswith(("import ", "from ", "load_module("))
        ]

        self.assertNotIn("load_module(\"alpaca_paper_account\")", import_lines)
        self.assertFalse(any("default_mock_snapshot" in line for line in import_lines))

    def test_strong_valid_proposal_scores_high(self) -> None:
        report = evaluate(proposal=valid_proposal())

        self.assertEqual(report.final_status, strategy_evaluation_harness.EVALUATION_PASS)
        self.assertGreaterEqual(report.evaluation_score, 2.5)

    def test_weak_liquidity_scores_low(self) -> None:
        report = evaluate(proposal=replace(valid_proposal(), liquidity_location="weak liquidity"))

        self.assertLessEqual(report.dimension_scores["liquidity_location_quality"], 1)

    def test_vague_confirmation_scores_low(self) -> None:
        report = evaluate(proposal=replace(valid_proposal(), entry_confirmation="vague"))

        self.assertLessEqual(report.dimension_scores["entry_confirmation_quality"], 1)

    def test_missing_fixed_risk_fails(self) -> None:
        report = evaluate(
            proposal=replace(valid_proposal(), risk_per_share=None, max_loss_amount=None)
        )

        self.assertEqual(report.final_status, strategy_evaluation_harness.EVALUATION_FAIL)
        self.assertIn("missing fixed risk", report.rejection_reasons)

    def test_missing_journal_readiness_fails(self) -> None:
        proposal = replace(valid_proposal(), journal_ready=False)
        report = evaluate(proposal=proposal, journal=None)

        self.assertEqual(report.final_status, strategy_evaluation_harness.EVALUATION_FAIL)
        self.assertIn("missing journal readiness", report.rejection_reasons)

    def test_bypassed_specialist_agents_fail(self) -> None:
        report = evaluate(
            proposal=replace(valid_proposal(), source_agent_outputs={}),
            bypassed_specialist_agents=True,
        )

        self.assertEqual(report.final_status, strategy_evaluation_harness.EVALUATION_FAIL)
        self.assertIn("bypassed specialist agents", report.rejection_reasons)

    def test_correct_no_trade_scores_high(self) -> None:
        report = evaluate(
            proposal=replace(valid_proposal(), liquidity_location="weak liquidity"),
            evaluation_type="no_trade",
            expected_rejection=True,
            actual_rejection=True,
            no_trade_decision=True,
        )

        self.assertEqual(report.dimension_scores["no_trade_discipline"], 3)
        self.assertEqual(
            report.no_trade_discipline_status,
            strategy_evaluation_harness.NO_TRADE_DISCIPLINE_PASS,
        )

    def test_forced_trade_scores_low(self) -> None:
        report = evaluate(forced_trade=True)

        self.assertEqual(report.final_status, strategy_evaluation_harness.EVALUATION_FAIL)
        self.assertEqual(report.dimension_scores["no_trade_discipline"], 0)
        self.assertIn("forced trade", report.rejection_reasons)

    def test_correct_rejection_of_weak_setup_scores_high(self) -> None:
        report = evaluate(
            proposal=replace(valid_proposal(), liquidity_location="weak liquidity"),
            evaluation_type="rejection",
            expected_rejection=True,
            actual_rejection=True,
        )

        self.assertEqual(report.dimension_scores["correct_rejection_of_weak_setups"], 3)

    def test_rejected_malformed_proposal_uses_local_risk_rejected_fixture(self) -> None:
        proposal = replace(valid_proposal(), risk_per_share=None, max_loss_amount=None)
        report = evaluate(
            proposal=proposal,
            risk=risk_rejected_fixture(),
            evaluation_type="rejection",
            expected_rejection=True,
            actual_rejection=True,
        )

        self.assertEqual(report.final_status, strategy_evaluation_harness.EVALUATION_FAIL)
        self.assertIn("missing fixed risk", report.rejection_reasons)

    def test_live_trading_assumption_fails(self) -> None:
        report = evaluate(live_trading_assumption=True)

        self.assertEqual(report.final_status, strategy_evaluation_harness.EVALUATION_FAIL)
        self.assertEqual(report.adlc_compliance_status, "FAIL")
        self.assertIn("live trading assumption", report.rejection_reasons)

    def test_poor_journal_quality_scores_low(self) -> None:
        proposal = replace(
            valid_proposal(),
            thesis="thin",
            why_now="thin",
            why_this_level="thin",
            what_invalidates_trade="thin",
        )
        report = evaluate(proposal=proposal, journal=journal_for(proposal, notes="thin"))

        self.assertLessEqual(report.dimension_scores["journal_readiness"], 1)

    def test_strong_journal_quality_scores_high(self) -> None:
        report = evaluate(proposal=valid_proposal())

        self.assertEqual(report.dimension_scores["journal_readiness"], 3)

    def test_data_stale_fails_or_scores_low(self) -> None:
        report = evaluate(data_fresh=False)

        self.assertEqual(report.final_status, strategy_evaluation_harness.EVALUATION_FAIL)
        self.assertEqual(report.dimension_scores["data_freshness"], 0)
        self.assertIn("stale data", report.rejection_reasons)

    def test_missing_data_fields_fail(self) -> None:
        report = evaluate(data_complete=False)

        self.assertEqual(report.final_status, strategy_evaluation_harness.EVALUATION_FAIL)
        self.assertEqual(report.dimension_scores["data_completeness"], 0)
        self.assertIn("missing data fields", report.rejection_reasons)

    def test_evaluation_report_is_generated(self) -> None:
        report = evaluate()
        payload = report.as_dict()

        self.assertIn("evaluation_score", payload)
        self.assertIn("dimension_scores", payload)
        self.assertIn("improvement_recommendations", payload)
        self.assertIn("adlc_compliance_status", payload)

    def test_harness_does_not_call_alpaca(self) -> None:
        source = source_text()

        self.assertNotIn("UrlLib", source)
        self.assertNotIn("urlopen", source)
        self.assertNotIn("/v2/orders", source)
        self.assertNotIn("AlpacaPaperOrderAdapter", source)

    def test_harness_does_not_send_orders(self) -> None:
        source = source_text()

        self.assertNotIn("send_paper_order_request", source)
        self.assertNotIn("submit_order", source)
        self.assertNotIn("place_order", source)

    def test_harness_does_not_enable_execution(self) -> None:
        source = source_text()

        self.assertNotIn("PAPER_ORDER_EXECUTION_ENABLED", source)
        self.assertNotIn("REAL_ALPACA_PAPER_SEND", source)

    def test_harness_does_not_use_llm_calls(self) -> None:
        source = source_text()

        self.assertNotIn("chat.completions", source)
        self.assertNotIn("responses.create", source)
        self.assertNotIn("OpenAI", source)


def evaluate(
    *,
    proposal=None,
    journal=None,
    evaluation_type="proposal",
    expected_rejection=False,
    actual_rejection=False,
    no_trade_decision=False,
    forced_trade=False,
    live_trading_assumption=False,
    data_fresh=True,
    data_complete=True,
    bypassed_specialist_agents=False,
    specialist_rubber_stamping=False,
    human_approval_rubber_stamping=False,
    no_trade_better_than_trade=False,
    excessive_confidence=False,
    approval_count=0,
    rejection_count=0,
    risk=None,
):
    proposal = valid_proposal() if proposal is None else proposal
    risk = risk if risk is not None else risk_for(proposal)
    if journal is None and proposal.journal_ready:
        journal = journal_for(proposal)
    return strategy_evaluation_harness.evaluate_strategy(
        strategy_evaluation_harness.StrategyEvaluationInput(
            proposal=proposal,
            risk_evaluation=risk,
            journal_entry=journal,
            evaluation_type=evaluation_type,
            data_fresh=data_fresh,
            data_complete=data_complete,
            expected_rejection=expected_rejection,
            actual_rejection=actual_rejection,
            no_trade_decision=no_trade_decision,
            forced_trade=forced_trade,
            live_trading_assumption=live_trading_assumption,
            excessive_confidence=excessive_confidence,
            bypassed_specialist_agents=bypassed_specialist_agents,
            specialist_rubber_stamping=specialist_rubber_stamping,
            human_approval_rubber_stamping=human_approval_rubber_stamping,
            no_trade_better_than_trade=no_trade_better_than_trade,
            approval_count=approval_count,
            rejection_count=rejection_count,
        )
    )


def valid_proposal():
    return ProposalFixture()


def risk_for(proposal):
    validation_status = "PASS" if proposal.risk_per_share and proposal.max_loss_amount else "FAIL"
    return RiskEvaluationFixture(
        decision=(
            strategy_evaluation_harness.RISK_APPROVED
            if validation_status == "PASS"
            else strategy_evaluation_harness.RISK_REJECTED
        ),
        rejection_reasons=() if validation_status == "PASS" else ("missing fixed risk",),
        executable=False,
    )


def risk_rejected_fixture():
    return RiskEvaluationFixture(
        decision=strategy_evaluation_harness.RISK_REJECTED,
        rejection_reasons=("missing fixed risk",),
        executable=False,
    )


def journal_for(proposal, notes=None):
    return JournalFixture(
        reason_for_final_decision="Valid paper-only proposal with clear context and risk.",
        lessons_or_notes=notes
        or "Strong journal entry with context, liquidity, confirmation, invalidation, and risk.",
    )


def source_text() -> str:
    return (RUNTIME_PATH / "strategy_evaluation_harness.py").read_text(encoding="utf-8")


@dataclass(frozen=True)
class RiskEvaluationFixture:
    decision: str
    rejection_reasons: tuple[str, ...] = ()
    executable: bool = False


@dataclass(frozen=True)
class JournalFixture:
    reason_for_final_decision: str
    lessons_or_notes: str


@dataclass(frozen=True)
class ProposalFixture:
    proposal_id: str = "paper-market_open-001"
    timeframe_context: str = "Daily structure holds above the prior 100.00 session low after a failed breakdown."
    liquidity_location: str = "Prior session low at 100.00 reclaim liquidity level"
    session_timing: str = "market_open"
    entry_confirmation: str = "15-minute candle close above 100.00 reclaim with hold above the level"
    risk_per_share: str | None = "2"
    max_loss_amount: str | None = "200"
    stop_loss: str | None = "98"
    expected_reward_risk: str | None = "2"
    thesis: str = "SIM paper-only long tests a reclaimed 100.00 prior-session low after failed downside liquidity."
    why_now: str = "Market-open timing follows the 15-minute close back above 100.00 with risk fixed before approval."
    why_this_level: str = "100.00 is the named prior-session low and failed breakdown liquidity reference."
    what_invalidates_trade: str = "A 15-minute close below 98.00 invalidates the reclaimed-low thesis."
    paper_trading_only: bool = True
    adlc_compliance_status: str = "PASS"
    journal_ready: bool = True
    source_agent_outputs: dict[str, str] | None = None

    def __post_init__(self) -> None:
        if self.source_agent_outputs is None:
            object.__setattr__(
                self,
                "source_agent_outputs",
                {
                    "Market Context Agent": "PASS",
                    "Liquidity Agent": "PASS",
                    "Session Timing Agent": "PASS",
                    "Confirmation Agent": "PASS",
                },
            )


if __name__ == "__main__":
    unittest.main()
