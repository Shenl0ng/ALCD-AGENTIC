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


strategy_evaluation_harness = load_module("strategy_evaluation_harness")
evaluation_first_gate = load_module("evaluation_first_gate")
alpaca_paper_account = load_module("alpaca_paper_account")
human_approval = load_module("human_approval")
paper_order_request = load_module("paper_order_request")
alpaca_paper_order_adapter = load_module("alpaca_paper_order_adapter")


class EvaluationFirstGateTests(unittest.TestCase):
    def test_strong_valid_proposal_passes_gate(self) -> None:
        result = gate_result()

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_PASSED)
        self.assertGreaterEqual(result.score, evaluation_first_gate.MINIMUM_EVALUATION_SCORE)

    def test_generic_higher_timeframe_context_blocks_approval(self) -> None:
        result = gate_result(proposal=replace(valid_proposal(), timeframe_context="context aligned"))

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("generic higher-timeframe context", result.hard_fail_reasons)

    def test_specific_higher_timeframe_context_can_pass(self) -> None:
        result = gate_result(
            proposal=replace(
                valid_proposal(),
                timeframe_context="Daily structure holds above the prior 100.00 session low.",
            )
        )

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_PASSED)

    def test_weak_liquidity_blocks_gate(self) -> None:
        result = gate_result(proposal=replace(valid_proposal(), liquidity_location="weak liquidity"))

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("weak or missing liquidity location", result.hard_fail_reasons)

    def test_specific_named_price_relevant_liquidity_can_pass(self) -> None:
        result = gate_result(
            proposal=replace(
                valid_proposal(),
                liquidity_location="Prior session low at 100.00 reclaim liquidity level",
            )
        )

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_PASSED)

    def test_vague_confirmation_blocks_gate(self) -> None:
        result = gate_result(proposal=replace(valid_proposal(), entry_confirmation="vague"))

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("vague confirmation", result.hard_fail_reasons)

    def test_observable_confirmation_can_pass(self) -> None:
        result = gate_result(
            proposal=replace(
                valid_proposal(),
                entry_confirmation="15-minute candle close above 100.00 reclaim with hold above the level",
            )
        )

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_PASSED)

    def test_missing_fixed_risk_blocks_gate(self) -> None:
        result = gate_result(
            proposal=replace(valid_proposal(), risk_per_share="", max_loss_amount="")
        )

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("missing fixed risk", result.hard_fail_reasons)

    def test_generic_thesis_blocks_approval(self) -> None:
        result = gate_result(
            proposal=replace(valid_proposal(), thesis="Valid setup that could apply to any symbol.")
        )

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("generic thesis", result.hard_fail_reasons)

    def test_specific_thesis_can_pass(self) -> None:
        result = gate_result(
            proposal=replace(
                valid_proposal(),
                thesis="SIM paper-only long tests a reclaimed 100.00 prior-session low after failed downside liquidity.",
            )
        )

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_PASSED)

    def test_missing_credible_invalidation_blocks_approval(self) -> None:
        result = gate_result(
            proposal=replace(valid_proposal(), what_invalidates_trade="invalidates the idea")
        )

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("missing journal readiness", result.hard_fail_reasons)

    def test_credible_invalidation_can_pass(self) -> None:
        result = gate_result(
            proposal=replace(
                valid_proposal(),
                what_invalidates_trade="A 15-minute close below 98.00 invalidates the reclaimed-low thesis.",
            )
        )

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_PASSED)

    def test_missing_journal_readiness_blocks_gate(self) -> None:
        result = gate_result(proposal=replace(valid_proposal(), journal_ready=False), journal=None)

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("missing journal readiness", result.hard_fail_reasons)

    def test_bypassed_specialist_agents_block_gate(self) -> None:
        result = gate_result(
            proposal=replace(valid_proposal(), source_agent_outputs={}),
            bypassed_specialist_agents=True,
        )

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("bypassed specialist agents", result.hard_fail_reasons)

    def test_specialist_agent_rubber_stamping_blocks_approval(self) -> None:
        result = gate_result(specialist_rubber_stamping=True)

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("specialist agent rubber-stamping", result.hard_fail_reasons)

    def test_human_approval_rubber_stamping_blocks_approval(self) -> None:
        result = gate_result(human_approval_rubber_stamping=True)

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("human approval rubber-stamping", result.hard_fail_reasons)

    def test_no_trade_better_than_trade_blocks_approval(self) -> None:
        result = gate_result(no_trade_better_than_trade=True)

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("no-trade better than approval", result.hard_fail_reasons)

    def test_risk_valid_but_weak_setup_quality_blocks_approval(self) -> None:
        result = gate_result(
            proposal=replace(valid_proposal(), liquidity_location="acceptable but not strong liquidity near level")
        )

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("weak or missing liquidity location", result.hard_fail_reasons)

    def test_repetitive_approval_language_blocks_approval(self) -> None:
        result = gate_result(
            proposal=replace(
                valid_proposal(),
                thesis="Valid setup that looks good. Valid setup that looks good.",
                why_now="Valid setup that looks good.",
                why_this_level="Valid setup that looks good.",
            )
        )

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("generic thesis", result.hard_fail_reasons)

    def test_missing_data_integrity_blocks_gate(self) -> None:
        result = gate_result(data_integrity_status="FAIL")

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("missing data integrity", result.hard_fail_reasons)

    def test_live_trading_assumption_blocks_gate(self) -> None:
        result = gate_result(live_trading_assumption=True)

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("live trading assumption", result.hard_fail_reasons)

    def test_forced_trade_behavior_blocks_gate(self) -> None:
        result = gate_result(forced_trade=True)

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("forced trade behavior", result.hard_fail_reasons)

    def test_missing_higher_timeframe_context_blocks_gate(self) -> None:
        result = gate_result(proposal=replace(valid_proposal(), timeframe_context=""))

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("missing higher-timeframe context", result.hard_fail_reasons)

    def test_excessive_confidence_without_evidence_blocks_gate(self) -> None:
        result = gate_result(excessive_confidence=True)

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("excessive confidence without evidence", result.hard_fail_reasons)

    def test_low_score_blocks_gate(self) -> None:
        result = evaluation_first_gate.evaluate_gate(
            strategy_evaluation_harness.evaluate_strategy(
                strategy_evaluation_harness.StrategyEvaluationInput(
                    proposal=None,
                    risk_evaluation=None,
                    journal_entry=None,
                )
            )
        )

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("minimum score threshold not met", result.hard_fail_reasons)

    def test_waiting_no_trade_receives_positive_score(self) -> None:
        report = evaluation_report(
            proposal=replace(valid_proposal(), liquidity_location="weak liquidity"),
            evaluation_type="no_trade",
            expected_rejection=True,
            actual_rejection=True,
            no_trade_decision=True,
        )

        self.assertEqual(report.dimension_scores["no_trade_discipline"], 3)

    def test_rejection_of_mediocre_setup_receives_positive_score(self) -> None:
        report = evaluation_report(
            proposal=replace(valid_proposal(), liquidity_location="weak liquidity"),
            evaluation_type="rejection",
            expected_rejection=True,
            actual_rejection=True,
        )

        self.assertEqual(report.dimension_scores["correct_rejection_of_weak_setups"], 3)

    def test_approval_rejection_ratio_warning_triggers(self) -> None:
        result = gate_result(approval_count=3, rejection_count=2)

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_PASSED)
        self.assertIn("approval-rate warning threshold active", result.soft_warning_reasons)

    def test_approval_rate_hard_block_triggers(self) -> None:
        result = gate_result(approval_count=8, rejection_count=2)

        self.assertEqual(result.status, evaluation_first_gate.EVALUATION_GATE_BLOCKED)
        self.assertIn("approval-rate hard block threshold active", result.hard_fail_reasons)

    def test_human_approval_cannot_start_without_gate_pass(self) -> None:
        proposal, risk, _, _, _, _ = paper_order_request.deterministic_valid_request()

        record = human_approval.enter_human_review(proposal, risk)

        self.assertEqual(record.approval_state, human_approval.HUMAN_APPROVAL_INVALID)

    def test_paper_order_request_cannot_be_created_without_gate_pass(self) -> None:
        proposal, risk, approval, journal, _, _ = paper_order_request.deterministic_valid_request()
        status = paper_order_request.gatekeeper_request_status(
            proposal=proposal,
            risk_evaluation=risk,
            approval=approval,
            journal_commit=journal,
            evaluation_gate=None,
        )
        request = paper_order_request.create_paper_order_request(
            proposal=proposal,
            risk_evaluation=risk,
            approval=approval,
            journal_commit=journal,
            gatekeeper_status=status,
            evaluation_gate=None,
        )

        self.assertEqual(request.final_status, paper_order_request.PAPER_ORDER_REQUEST_BLOCKED)

    def test_paper_send_cannot_occur_without_gate_pass(self) -> None:
        _, _, _, journal, request, _ = paper_order_request.deterministic_valid_request()
        request = replace(request, evaluation_gate_reference=None)
        client = alpaca_paper_order_adapter.RecordingMockPaperClient()
        adapter = alpaca_paper_order_adapter.AlpacaPaperOrderAdapter(
            alpaca_paper_order_adapter.PaperOrderAdapterConfig(
                execution_enabled=True,
                execution_mode=alpaca_paper_order_adapter.MOCKED_PAPER_SEND,
            ),
            client,
        )

        result = adapter.send_paper_order_request(
            request,
            account=alpaca_paper_account.default_mock_snapshot(),
            journal_commit=journal,
            manual_confirmation=manual_confirmation(request),
        )

        self.assertEqual(result.status, alpaca_paper_order_adapter.PAPER_ORDER_REJECTED_BY_PREFLIGHT)
        self.assertIn("evaluation gate did not pass", result.preflight.violations)
        self.assertEqual(client.payloads, [])

    def test_blocked_gate_writes_journal_entry(self) -> None:
        entry = evaluation_first_gate.evaluation_gate_journal_entry(
            gate_result(proposal=replace(valid_proposal(), liquidity_location="weak liquidity"))
        )

        self.assertEqual(entry.event_type, "evaluation_gate_blocked")
        self.assertIn("weak or missing liquidity location", entry.hard_fail_reasons)

    def test_passed_gate_writes_journal_entry(self) -> None:
        entry = evaluation_first_gate.evaluation_gate_journal_entry(gate_result())

        self.assertEqual(entry.event_type, "evaluation_gate_passed")
        self.assertIn("score=", entry.score_summary)

    def test_no_alpaca_calls_exist(self) -> None:
        source = gate_source()

        self.assertNotIn("urlopen", source)
        self.assertNotIn("/v2/orders", source)
        self.assertNotIn("Alpaca", source)

    def test_no_order_is_sent(self) -> None:
        result = evaluation_first_gate.evaluate_gate(evaluation_report())

        self.assertFalse(hasattr(result, "send_paper_order_request"))
        self.assertFalse(hasattr(result, "submit_order"))
        self.assertFalse(hasattr(result, "place_order"))

    def test_no_execution_flag_is_enabled(self) -> None:
        self.assertNotIn("PAPER_ORDER_EXECUTION_ENABLED", gate_source())

    def test_no_automation_is_added(self) -> None:
        source = gate_source().lower()

        self.assertNotIn("autonomous", source)
        self.assertNotIn("scheduler", source)


def valid_proposal():
    return strategy_evaluation_harness.DeterministicProposal()


def evaluation_report(
    *,
    proposal=None,
    journal=None,
    data_fresh=True,
    data_complete=True,
    bypassed_specialist_agents=False,
    live_trading_assumption=False,
    forced_trade=False,
    excessive_confidence=False,
    specialist_rubber_stamping=False,
    human_approval_rubber_stamping=False,
    no_trade_better_than_trade=False,
    evaluation_type="proposal",
    expected_rejection=False,
    actual_rejection=False,
    no_trade_decision=False,
    approval_count=0,
    rejection_count=0,
):
    proposal = valid_proposal() if proposal is None else proposal
    risk = strategy_evaluation_harness.DeterministicRiskEvaluation(
        decision=strategy_evaluation_harness.RISK_APPROVED
    )
    if journal is None and getattr(proposal, "journal_ready", False):
        journal = JournalFixture()
    return strategy_evaluation_harness.evaluate_strategy(
        strategy_evaluation_harness.StrategyEvaluationInput(
            proposal=proposal,
            risk_evaluation=risk,
            journal_entry=journal,
            data_fresh=data_fresh,
            data_complete=data_complete,
            bypassed_specialist_agents=bypassed_specialist_agents,
            live_trading_assumption=live_trading_assumption,
            forced_trade=forced_trade,
            excessive_confidence=excessive_confidence,
            specialist_rubber_stamping=specialist_rubber_stamping,
            human_approval_rubber_stamping=human_approval_rubber_stamping,
            no_trade_better_than_trade=no_trade_better_than_trade,
            evaluation_type=evaluation_type,
            expected_rejection=expected_rejection,
            actual_rejection=actual_rejection,
            no_trade_decision=no_trade_decision,
            approval_count=approval_count,
            rejection_count=rejection_count,
        )
    )


def gate_result(*, data_integrity_status="PASS", approval_count=0, rejection_count=0, **kwargs):
    return evaluation_first_gate.evaluate_gate(
        evaluation_report(approval_count=approval_count, rejection_count=rejection_count, **kwargs),
        data_integrity_status=data_integrity_status,
        journal_reference="journal-evaluation-gate",
        approval_count=approval_count,
        rejection_count=rejection_count,
    )


class JournalFixture:
    reason_for_final_decision = (
        "Paper-only SIM proposal uses the 100.00 prior session low reclaim after a "
        "15-minute close above the level, with fixed risk and no-trade rejected only "
        "because context, liquidity, confirmation, and invalidation are specific."
    )
    lessons_or_notes = (
        "Journal records the exact level, observable confirmation, stop at 98.00, "
        "and invalidation on a close back below the reclaimed prior-session low."
    )


class ManualConfirmation:
    confirmation_id = "manual-confirmation-test"
    confirmation_state = alpaca_paper_order_adapter.MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY
    paper_only_confirmation = True

    def __init__(self, request):
        self.paper_order_request_id = request.paper_order_request_id


def manual_confirmation(request):
    return ManualConfirmation(request)


def gate_source() -> str:
    return (RUNTIME_PATH / "evaluation_first_gate.py").read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
