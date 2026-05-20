from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "runtime"
SIMULATION_PATH = RUNTIME_PATH / "simulation.py"

if str(RUNTIME_PATH) not in sys.path:
    sys.path.insert(0, str(RUNTIME_PATH))

spec = importlib.util.spec_from_file_location("simulation", SIMULATION_PATH)
simulation = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["simulation"] = simulation
spec.loader.exec_module(simulation)


class SimulationRuntimeTests(unittest.TestCase):
    def run_in_temp_repo(
        self,
        routine: str,
        fixture: dict[str, str] | None = None,
        market_data_fixture: str = "fresh",
        paper_account_adapter=None,
    ):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir) / "repo"
            shutil.copytree(ROOT, temp_root)
            runtime = simulation.SimulationRuntime(temp_root)
            adapter = simulation.MockMarketDataAdapter(market_data_fixture)
            report = runtime.run_routine(
                routine,
                fixture=fixture,
                market_data_adapter=adapter,
                paper_account_adapter=paper_account_adapter,
                write_report=True,
            )
            written_texts = [
                (temp_root / path).read_text(encoding="utf-8")
                for path in report.files_written
            ]
            report_path = (
                temp_root
                / "test"
                / "sandbox"
                / "reports"
                / f"{routine}_simulation_report.json"
            )
            report_text = report_path.read_text(encoding="utf-8")
            return report, written_texts, report_text

    def test_correct_agent_sequence_for_full_pass(self) -> None:
        report, _, _ = self.run_in_temp_repo("market_open", full_pass_fixture())

        self.assertEqual(report.agents_invoked, simulation.REQUIRED_AGENT_SEQUENCE)

    def test_veto_stops_workflow(self) -> None:
        report, _, _ = self.run_in_temp_repo(
            "market_open",
            {"Liquidity Agent": "REJECT"},
        )

        self.assertEqual(report.final_status, "NO_TRADE")
        self.assertIn("Liquidity Agent", report.vetoes_triggered)
        self.assertNotIn("Session Timing Agent", report.agents_invoked)
        self.assertEqual(report.agents_invoked[-1], "Journal Agent")

    def test_no_single_agent_collapse(self) -> None:
        report, _, _ = self.run_in_temp_repo("market_open", full_pass_fixture())

        self.assertGreaterEqual(len(set(report.agents_invoked)), 10)
        self.assertIn("Trade Proposal Agent", report.agents_invoked)
        self.assertIn("Final Risk Manager Check", report.agents_invoked)
        self.assertIn("Execution Gatekeeper", report.agents_invoked)
        self.assertIn("Journal Agent", report.agents_invoked)

    def test_paper_only_enforcement(self) -> None:
        report, written_texts, _ = self.run_in_temp_repo("market_open", full_pass_fixture())

        self.assertTrue(report.paper_only_enforced)
        self.assertFalse(report.prohibited_behavior_detected)
        for text in written_texts:
            self.assertIn("Paper Mode: REQUIRED", text)

    def test_journal_readiness_before_gate_status(self) -> None:
        report, _, _ = self.run_in_temp_repo("market_open", full_pass_fixture())

        self.assertTrue(report.journal_ready_before_gate)
        self.assertLess(
            report.agents_invoked.index("Trade Proposal Agent"),
            report.agents_invoked.index("Execution Gatekeeper"),
        )

    def test_risk_approval_required_before_gate_status(self) -> None:
        report, _, _ = self.run_in_temp_repo(
            "market_open",
            {**full_pass_fixture(), "Final Risk Manager Check": "REJECT"},
        )

        self.assertEqual(report.final_status, "NO_TRADE")
        self.assertIn("Final Risk Manager Check", report.vetoes_triggered)
        self.assertNotIn("Execution Gatekeeper", report.agents_invoked)

    def test_default_no_trade(self) -> None:
        report, _, _ = self.run_in_temp_repo("market_open")

        self.assertEqual(report.final_status, "NO_TRADE")
        self.assertIn("Confirmation Agent", report.vetoes_triggered)

    def test_no_broker_order_api_behavior(self) -> None:
        report, written_texts, report_text = self.run_in_temp_repo(
            "market_open",
            full_pass_fixture(),
        )

        self.assertFalse(report.prohibited_behavior_detected)
        for text in written_texts + [report_text]:
            text = text.lower()
            self.assertNotIn("alpaca", text)
            self.assertNotIn("place order", text)
            self.assertNotIn("live trading allowed", text)
            self.assertNotIn("llm call", text)

    def test_all_required_routines_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir) / "repo"
            shutil.copytree(ROOT, temp_root)
            runtime = simulation.SimulationRuntime(temp_root)
            reports = runtime.run_all()

        self.assertEqual(
            [report.routine_name for report in reports],
            list(simulation.ROUTINES),
        )

    def test_fresh_market_data_passes_data_integrity(self) -> None:
        report, _, report_text = self.run_in_temp_repo("market_open")

        self.assertEqual(report.market_data.data_integrity_status, "PASS")
        self.assertEqual(report.market_data.freshness_status, "FRESH")
        self.assertEqual(report.market_data.completeness_status, "COMPLETE")
        self.assertIn('"data_source": "deterministic_mock"', report_text)

    def test_stale_market_data_fails_data_integrity(self) -> None:
        report, _, _ = self.run_in_temp_repo("market_open", market_data_fixture="stale")

        self.assertEqual(report.market_data.data_integrity_status, "FAIL")
        self.assertEqual(report.market_data.freshness_status, "STALE")
        self.assertIn("Data Integrity Agent", report.vetoes_triggered)

    def test_missing_timestamp_fails_data_integrity(self) -> None:
        report, _, _ = self.run_in_temp_repo(
            "market_open",
            market_data_fixture="missing_timestamp",
        )

        self.assertEqual(report.market_data.data_integrity_status, "FAIL")
        self.assertIn("missing_timestamp", report.market_data.violations)

    def test_missing_symbol_fails_data_integrity(self) -> None:
        report, _, _ = self.run_in_temp_repo(
            "market_open",
            market_data_fixture="missing_symbol",
        )

        self.assertEqual(report.market_data.data_integrity_status, "FAIL")
        self.assertIn("missing_symbol", report.market_data.violations)

    def test_missing_timeframe_fails_data_integrity(self) -> None:
        report, _, _ = self.run_in_temp_repo(
            "market_open",
            market_data_fixture="missing_timeframe",
        )

        self.assertEqual(report.market_data.data_integrity_status, "FAIL")
        self.assertIn("missing_timeframe", report.market_data.violations)

    def test_missing_source_label_fails_data_integrity(self) -> None:
        report, _, _ = self.run_in_temp_repo(
            "market_open",
            market_data_fixture="missing_source",
        )

        self.assertEqual(report.market_data.data_integrity_status, "FAIL")
        self.assertIn("missing_source", report.market_data.violations)

    def test_downstream_agents_do_not_run_if_data_integrity_fails(self) -> None:
        report, _, _ = self.run_in_temp_repo("market_open", market_data_fixture="stale")

        self.assertEqual(
            report.agents_invoked,
            ("Orchestrator", "Data Integrity Agent", "Journal Agent"),
        )
        self.assertEqual(report.final_status, "NO_TRADE")

    def test_market_data_cannot_create_trade_without_full_specialist_sequence(self) -> None:
        report, _, _ = self.run_in_temp_repo("market_open")

        self.assertEqual(report.market_data.data_integrity_status, "PASS")
        self.assertEqual(report.final_status, "NO_TRADE")
        self.assertNotIn("Trade Proposal Agent", report.agents_invoked)
        self.assertIn("Confirmation Agent", report.vetoes_triggered)

    def test_risk_manager_reads_account_state_but_cannot_execute(self) -> None:
        blocked_snapshot = simulation.PaperAccountSnapshot(
            account=simulation.PaperAccountState(
                account_id="blocked-paper",
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
        account_adapter = simulation.MockAlpacaPaperAccountReadOnlyAdapter(blocked_snapshot)

        report, written_texts, _ = self.run_in_temp_repo(
            "market_open",
            fixture=full_pass_fixture(),
            paper_account_adapter=account_adapter,
        )

        self.assertEqual(report.final_status, "NO_TRADE")
        self.assertIn("Initial Risk State Check", report.vetoes_triggered)
        self.assertNotIn("Execution Gatekeeper", report.agents_invoked)
        self.assertFalse(report.paper_account.account.trading_allowed_in_principle)
        self.assertTrue(any("Agent: Initial Risk State Check" in text for text in written_texts))

    def test_default_action_remains_no_trade_until_all_gates_pass(self) -> None:
        report, _, _ = self.run_in_temp_repo("market_open")

        self.assertEqual(report.final_status, "NO_TRADE")
        self.assertIsNone(report.paper_order_request)

    def test_all_gates_pass_creates_internal_paper_order_request_only(self) -> None:
        report, _, _ = self.run_in_temp_repo("market_open", fixture=full_pass_fixture())

        self.assertEqual(report.risk_evaluation.decision, "RISK_APPROVED")
        self.assertEqual(
            report.human_approval.approval_state,
            "HUMAN_APPROVED_FOR_PAPER_ONLY",
        )
        self.assertEqual(
            report.paper_order_request.gatekeeper_status,
            "READY_FOR_PAPER_ORDER_REQUEST",
        )
        self.assertEqual(report.final_status, "PAPER_ORDER_REQUEST_CREATED")
        self.assertFalse(report.paper_order_request.broker_execution_allowed)
        self.assertFalse(report.paper_order_request.live_trading_allowed)


def full_pass_fixture() -> dict[str, str]:
    return {
        "Data Integrity Agent": "PASS",
        "Initial Risk State Check": "PASS",
        "Market Context Agent": "PASS",
        "Liquidity Agent": "PASS",
        "Session Timing Agent": "PASS",
        "Confirmation Agent": "PASS",
        "Trade Proposal Agent": "PASS",
        "Final Risk Manager Check": "PASS",
        "Execution Gatekeeper": "PASS",
    }


if __name__ == "__main__":
    unittest.main()
