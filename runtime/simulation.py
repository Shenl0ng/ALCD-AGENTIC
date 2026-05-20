from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping, Protocol

from alpaca_paper_account import (
    AlpacaPaperAccountReadOnlyAdapter,
    AlpacaPaperConfig,
    AlpacaReadOnlyError,
    MockAlpacaPaperAccountReadOnlyAdapter,
    PaperAccountState,
    PaperAccountSnapshot,
    unavailable_snapshot,
)
from architecture_validator import REQUIRED_FILES, validate
from market_data import (
    MOCK_MARKET_DATA_FIXTURES,
    MarketDataAdapter,
    MarketDataValidation,
    MockMarketDataAdapter,
    validate_market_data,
)
from human_approval import (
    HUMAN_APPROVED_FOR_PAPER_ONLY,
    HUMAN_REJECTED,
    ApprovalRecord,
    ApprovalValidation,
    JournalEntry,
    commit_journal_entry,
    deterministic_human_approval,
    enter_human_review,
    validate_approval,
)
from evaluation_first_gate import (
    EvaluationGateResult,
    evaluate_gate,
    evaluation_gate_journal_entry,
)
from paper_trade import (
    RISK_APPROVED,
    RISK_REJECTED,
    PaperTradeProposal,
    ProposalValidation,
    RiskEvaluation,
    deterministic_valid_proposal,
    evaluate_risk,
    validate_proposal,
)
from paper_order_request import (
    PAPER_ORDER_REQUEST_CREATED,
    PaperOrderRequest,
    PaperOrderRequestValidation,
    create_paper_order_request,
    gatekeeper_request_status,
    request_journal_entry,
    validate_paper_order_request,
)
from strategy_evaluation_harness import StrategyEvaluationInput, StrategyEvaluationReport, evaluate_strategy


ROUTINES = ("premarket", "market_open", "midday", "market_close", "weekly_review")

REQUIRED_AGENT_SEQUENCE = (
    "Orchestrator",
    "Data Integrity Agent",
    "Initial Risk State Check",
    "Market Context Agent",
    "Liquidity Agent",
    "Session Timing Agent",
    "Confirmation Agent",
    "Trade Proposal Agent",
    "Final Risk Manager Check",
    "Strategy Evaluation Gate",
    "Execution Gatekeeper",
    "Journal Agent",
)

PROHIBITED_TERMS = (
    "live trading",
    "llm",
    "credential",
    ".env",
)

FIXTURES: dict[str, dict[str, str]] = {
    "premarket": {
        "Data Integrity Agent": "PASS",
        "Initial Risk State Check": "PASS",
        "Market Context Agent": "PASS",
        "Liquidity Agent": "PASS",
        "Session Timing Agent": "REJECT",
    },
    "market_open": {
        "Data Integrity Agent": "PASS",
        "Initial Risk State Check": "PASS",
        "Market Context Agent": "PASS",
        "Liquidity Agent": "PASS",
        "Session Timing Agent": "PASS",
        "Confirmation Agent": "REJECT",
    },
    "midday": {
        "Data Integrity Agent": "PASS",
        "Initial Risk State Check": "PASS",
        "Market Context Agent": "PASS",
        "Liquidity Agent": "REJECT",
    },
    "market_close": {
        "Data Integrity Agent": "PASS",
        "Initial Risk State Check": "PASS",
        "Market Context Agent": "REJECT",
    },
    "weekly_review": {
        "Data Integrity Agent": "PASS",
        "Initial Risk State Check": "PASS",
        "Market Context Agent": "PASS",
        "Liquidity Agent": "PASS",
        "Session Timing Agent": "PASS",
        "Confirmation Agent": "REJECT",
    },
}

READ_FILES = tuple(REQUIRED_FILES)


class PaperAccountAdapter(Protocol):
    def read_snapshot(self) -> PaperAccountSnapshot:
        """Read paper account state without creating, changing, or removing anything."""


@dataclass(frozen=True)
class AgentOutput:
    agent: str
    status: str
    decision: str
    files_read: tuple[str, ...]
    files_written: tuple[str, ...] = ()
    reason: str = "deterministic fixture"

    @property
    def rejected(self) -> bool:
        return self.status == "REJECT"


@dataclass(frozen=True)
class SimulationReport:
    routine_name: str
    agents_invoked: tuple[str, ...]
    files_read: tuple[str, ...]
    files_written: tuple[str, ...]
    vetoes_triggered: tuple[str, ...]
    final_status: str
    adlc_compliance_status: str
    paper_only_enforced: bool
    journal_ready_before_gate: bool
    risk_approved_before_gate: bool
    prohibited_behavior_detected: bool
    market_data: MarketDataValidation
    paper_account: PaperAccountSnapshot
    proposal_validation: ProposalValidation | None
    risk_evaluation: RiskEvaluation | None
    strategy_evaluation: StrategyEvaluationReport | None
    evaluation_gate: EvaluationGateResult | None
    human_approval: ApprovalRecord | None
    approval_validation: ApprovalValidation | None
    journal_commit: JournalEntry | None
    paper_order_request: PaperOrderRequest | None
    paper_order_request_validation: PaperOrderRequestValidation | None
    request_journal_commit: JournalEntry | None

    def as_dict(self) -> dict[str, object]:
        return {
            "routine_name": self.routine_name,
            "agents_invoked": list(self.agents_invoked),
            "files_read": list(self.files_read),
            "files_written": list(self.files_written),
            "vetoes_triggered": list(self.vetoes_triggered),
            "final_status": self.final_status,
            "adlc_compliance_status": self.adlc_compliance_status,
            "paper_only_enforced": self.paper_only_enforced,
            "journal_ready_before_gate": self.journal_ready_before_gate,
            "risk_approved_before_gate": self.risk_approved_before_gate,
            "prohibited_behavior_detected": self.prohibited_behavior_detected,
            "market_data": self.market_data.as_dict(),
            "paper_account": self.paper_account.as_dict(),
            "proposal_validation": (
                self.proposal_validation.as_dict() if self.proposal_validation else None
            ),
            "risk_evaluation": self.risk_evaluation.as_dict() if self.risk_evaluation else None,
            "strategy_evaluation": (
                self.strategy_evaluation.as_dict() if self.strategy_evaluation else None
            ),
            "evaluation_gate": self.evaluation_gate.as_dict() if self.evaluation_gate else None,
            "human_approval": self.human_approval.as_dict() if self.human_approval else None,
            "approval_validation": (
                self.approval_validation.as_dict() if self.approval_validation else None
            ),
            "journal_commit": self.journal_commit.as_dict() if self.journal_commit else None,
            "paper_order_request": (
                self.paper_order_request.as_dict() if self.paper_order_request else None
            ),
            "paper_order_request_validation": (
                self.paper_order_request_validation.as_dict()
                if self.paper_order_request_validation
                else None
            ),
            "request_journal_commit": (
                self.request_journal_commit.as_dict() if self.request_journal_commit else None
            ),
        }


@dataclass
class SimulationRuntime:
    root: Path
    sandbox_root: Path | None = None
    _files_written: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.root = self.root.resolve()
        if self.sandbox_root is None:
            self.sandbox_root = self.root / "test" / "sandbox"
        else:
            self.sandbox_root = self.sandbox_root.resolve()

    def run_all(self) -> tuple[SimulationReport, ...]:
        return tuple(self.run_routine(routine) for routine in ROUTINES)

    def run_routine(
        self,
        routine_name: str,
        fixture: Mapping[str, str] | None = None,
        market_data_adapter: MarketDataAdapter | None = None,
        paper_account_adapter: PaperAccountAdapter | None = None,
        write_report: bool = True,
    ) -> SimulationReport:
        if routine_name not in ROUTINES:
            raise ValueError(f"Unknown routine: {routine_name}")

        architecture_report = validate(self.root)
        fixture_values = dict(FIXTURES[routine_name])
        if fixture:
            fixture_values.update(fixture)

        files_read = self._load_markdown_files()
        adapter = market_data_adapter or MockMarketDataAdapter()
        market_data = validate_market_data(adapter.load_snapshot(routine_name))
        if not market_data.passed:
            fixture_values["Data Integrity Agent"] = "REJECT"

        paper_account = (paper_account_adapter or MockAlpacaPaperAccountReadOnlyAdapter()).read_snapshot()
        if not paper_account.account.trading_allowed_in_principle:
            fixture_values["Initial Risk State Check"] = "REJECT"

        outputs: list[AgentOutput] = []
        vetoes: list[str] = []
        risk_approved = False
        journal_ready = False
        gate_seen = False
        stopped = False
        proposal: PaperTradeProposal | None = None
        proposal_validation: ProposalValidation | None = None
        risk_evaluation: RiskEvaluation | None = None
        strategy_evaluation: StrategyEvaluationReport | None = None
        evaluation_gate: EvaluationGateResult | None = None
        human_approval: ApprovalRecord | None = None
        approval_validation: ApprovalValidation | None = None
        journal_commit: JournalEntry | None = None
        paper_order_request: PaperOrderRequest | None = None
        paper_order_request_validation: PaperOrderRequestValidation | None = None
        request_journal_commit: JournalEntry | None = None

        outputs.append(
            AgentOutput(
                agent="Orchestrator",
                status="PASS" if architecture_report.passed else "REJECT",
                decision="WORKFLOW_STARTED" if architecture_report.passed else "ADLC_BLOCKED",
                files_read=files_read,
            )
        )
        if not architecture_report.passed:
            vetoes.append("Orchestrator")
            stopped = True

        for agent in REQUIRED_AGENT_SEQUENCE[1:-1]:
            if stopped:
                break

            status = fixture_values.get(agent, "PASS")
            if agent == "Trade Proposal Agent" and status == "PASS":
                proposal = deterministic_valid_proposal(routine_name)
                proposal_validation = validate_proposal(proposal)
                if not proposal_validation.passed:
                    status = "REJECT"
                    fixture_values[agent] = "REJECT"
            if agent == "Final Risk Manager Check" and status == "PASS":
                risk_evaluation = evaluate_risk(proposal, paper_account)
                if risk_evaluation.decision == RISK_REJECTED:
                    status = "REJECT"
                    fixture_values[agent] = "REJECT"
            if agent == "Strategy Evaluation Gate" and status == "PASS":
                if proposal is not None and risk_evaluation is not None:
                    strategy_evaluation = evaluate_strategy(
                        StrategyEvaluationInput(
                            proposal=proposal,
                            risk_evaluation=risk_evaluation,
                            journal_entry=_EvaluationJournalFixture(),
                        )
                    )
                    evaluation_gate = evaluate_gate(
                        strategy_evaluation,
                        data_integrity_status=market_data.data_integrity_status,
                        journal_reference="journal-evaluation-gate",
                    )
                    evaluation_gate_journal_entry(evaluation_gate)
                    if not evaluation_gate.passed:
                        status = "REJECT"
                        fixture_values[agent] = "REJECT"
                else:
                    status = "REJECT"
                    fixture_values[agent] = "REJECT"
                if status == "PASS" and proposal is not None and risk_evaluation is not None:
                    review_record = enter_human_review(proposal, risk_evaluation, evaluation_gate)
                    requested_state = fixture_values.get(
                        "Human Approval State",
                        HUMAN_APPROVED_FOR_PAPER_ONLY,
                    )
                    human_approval = deterministic_human_approval(
                        proposal,
                        requested_state,
                        fixture_values.get("Human Reviewer", "human-reviewer"),
                    )
                    if review_record.approval_state == "HUMAN_APPROVAL_INVALID":
                        human_approval = review_record
                    approval_validation = validate_approval(
                        proposal,
                        risk_evaluation,
                        human_approval,
                    )
                    if (
                        not approval_validation.passed
                        or human_approval.approval_state == HUMAN_REJECTED
                    ):
                        status = "REJECT"
                        fixture_values[agent] = "REJECT"
                    journal_commit = commit_journal_entry(
                        proposal=proposal,
                        risk_status=risk_evaluation.decision,
                        human_approval_status=human_approval.approval_state,
                        gatekeeper_status="EXECUTION_BLOCKED",
                        event_type=(
                            "human_rejected"
                            if human_approval.approval_state == HUMAN_REJECTED
                            else "human_approved_for_paper_only"
                        ),
                        reason_for_final_decision=human_approval.approval_state,
                        lessons_or_notes="Human approval is paper-only and does not execute.",
                        routine_name=routine_name,
                        adlc_status="PASS" if architecture_report.passed else "ADLC_BLOCKED",
                    )

            gatekeeper_status_for_request = None
            if agent == "Execution Gatekeeper":
                gatekeeper_status_for_request = gatekeeper_request_status(
                    proposal=proposal,
                    risk_evaluation=risk_evaluation,
                    approval=human_approval,
                    journal_commit=journal_commit,
                    evaluation_gate=evaluation_gate,
                )

            decision = self._decision_for(
                agent,
                status,
                risk_approved,
                journal_ready,
                risk_evaluation,
                gatekeeper_status_for_request,
            )
            reason = (
                ",".join(market_data.violations)
                if agent == "Data Integrity Agent" and not market_data.passed
                else "deterministic fixture"
            )
            if agent == "Initial Risk State Check":
                reason = (
                    ",".join(paper_account.account.violations)
                    if not paper_account.account.trading_allowed_in_principle
                    else "paper account read-only state allows risk review in principle"
                )
            if agent == "Trade Proposal Agent" and proposal_validation is not None:
                reason = ",".join(proposal_validation.violations) or "proposal validation passed"
            if agent == "Final Risk Manager Check" and risk_evaluation is not None:
                reason = ",".join(risk_evaluation.rejection_reasons) or "risk evaluation approved"
            if agent == "Strategy Evaluation Gate" and evaluation_gate is not None:
                reason = ",".join(evaluation_gate.hard_fail_reasons) or evaluation_gate.status
                if approval_validation is not None and not approval_validation.passed:
                    reason = ",".join(approval_validation.violations)
                if human_approval is not None and human_approval.approval_state == HUMAN_REJECTED:
                    reason = "human rejected"
            output = AgentOutput(
                agent=agent,
                status=status,
                decision=decision,
                files_read=files_read,
                files_written=self._sandbox_writes_for(agent, status),
                reason=reason,
            )
            outputs.append(output)

            if agent == "Trade Proposal Agent" and status == "PASS":
                journal_ready = True
            if agent == "Final Risk Manager Check" and decision == RISK_APPROVED:
                risk_approved = True
            if agent == "Execution Gatekeeper":
                gate_seen = True
                if not journal_ready or not risk_approved:
                    vetoes.append(agent)
                    stopped = True
                elif (
                    proposal is not None
                    and risk_evaluation is not None
                    and human_approval is not None
                    and journal_commit is not None
                    and gatekeeper_status_for_request is not None
                ):
                    paper_order_request = create_paper_order_request(
                        proposal=proposal,
                        risk_evaluation=risk_evaluation,
                        approval=human_approval,
                        journal_commit=journal_commit,
                        gatekeeper_status=gatekeeper_status_for_request,
                        evaluation_gate=evaluation_gate,
                    )
                    paper_order_request_validation = validate_paper_order_request(
                        paper_order_request,
                        proposal=proposal,
                        risk_evaluation=risk_evaluation,
                        approval=human_approval,
                        journal_commit=journal_commit,
                        evaluation_gate=evaluation_gate,
                    )
                    request_journal_commit = request_journal_entry(
                        request=paper_order_request,
                        proposal=proposal,
                        risk_status=risk_evaluation.decision,
                        human_approval_status=human_approval.approval_state,
                        validation=paper_order_request_validation,
                    )
                    if not paper_order_request_validation.passed:
                        vetoes.append(agent)
                        stopped = True

            if output.rejected:
                vetoes.append(agent)
                stopped = True

        journal_output = AgentOutput(
            agent="Journal Agent",
            status="PASS",
            decision="DECISION_RECORDED",
            files_read=files_read,
            files_written=("test/sandbox/memory/journal.md",),
        )
        outputs.append(journal_output)

        final_status = self._final_status(outputs, vetoes, gate_seen)
        if (
            paper_order_request is not None
            and paper_order_request_validation is not None
            and paper_order_request_validation.passed
        ):
            final_status = PAPER_ORDER_REQUEST_CREATED
        if journal_commit is None:
            journal_commit = commit_journal_entry(
                proposal=proposal,
                risk_status=risk_evaluation.decision if risk_evaluation else "NOT_RUN",
                human_approval_status=(
                    human_approval.approval_state if human_approval else "NOT_REQUESTED"
                ),
                gatekeeper_status=(
                    "EXECUTION_BLOCKED" if final_status == "NO_TRADE" else final_status
                ),
                event_type="final_decision",
                reason_for_final_decision=final_status,
                lessons_or_notes="Journal commit records paper-only decision; no order request.",
                routine_name=routine_name,
                adlc_status="PASS" if architecture_report.passed else "ADLC_BLOCKED",
            )
        adlc_status = "ADLC_PASS" if architecture_report.passed else "ADLC_BLOCKED"
        report = SimulationReport(
            routine_name=routine_name,
            agents_invoked=tuple(output.agent for output in outputs),
            files_read=files_read,
            files_written=self._write_memory_records(
                routine_name,
                outputs,
                final_status,
                proposal,
                risk_evaluation,
                human_approval,
                approval_validation,
                journal_commit,
                strategy_evaluation,
                evaluation_gate,
                paper_order_request,
                paper_order_request_validation,
                request_journal_commit,
            ),
            vetoes_triggered=tuple(vetoes),
            final_status=final_status,
            adlc_compliance_status=adlc_status,
            paper_only_enforced=True,
            journal_ready_before_gate=not gate_seen or journal_ready,
            risk_approved_before_gate=not gate_seen or risk_approved,
            prohibited_behavior_detected=self._has_prohibited_behavior(outputs),
            market_data=market_data,
            paper_account=paper_account,
            proposal_validation=proposal_validation,
            risk_evaluation=risk_evaluation,
            strategy_evaluation=strategy_evaluation,
            evaluation_gate=evaluation_gate,
            human_approval=human_approval,
            approval_validation=approval_validation,
            journal_commit=journal_commit,
            paper_order_request=paper_order_request,
            paper_order_request_validation=paper_order_request_validation,
            request_journal_commit=request_journal_commit,
        )

        if write_report:
            self._write_report(report)
        return report

    def _load_markdown_files(self) -> tuple[str, ...]:
        loaded: list[str] = []
        for relative_path in READ_FILES:
            path = self.root / relative_path
            if path.is_file():
                path.read_text(encoding="utf-8")
                loaded.append(relative_path)
        return tuple(loaded)

    def _decision_for(
        self,
        agent: str,
        status: str,
        risk_approved: bool,
        journal_ready: bool,
        risk_evaluation: RiskEvaluation | None = None,
        gatekeeper_status_for_request: str | None = None,
    ) -> str:
        if status == "REJECT":
            if agent in {"Initial Risk State Check", "Final Risk Manager Check"}:
                return RISK_REJECTED
            if agent == "Execution Gatekeeper":
                return "EXECUTION_BLOCKED"
            return "NO_TRADE"
        if agent == "Initial Risk State Check":
            return "RISK_REVIEW_ALLOWED"
        if agent == "Final Risk Manager Check":
            return risk_evaluation.decision if risk_evaluation else RISK_APPROVED
        if agent == "Strategy Evaluation Gate":
            return "EVALUATION_GATE_PASSED" if status == "PASS" else "EVALUATION_GATE_BLOCKED"
        if agent == "Execution Gatekeeper":
            return gatekeeper_status_for_request or "EXECUTION_BLOCKED"
        if agent == "Trade Proposal Agent":
            return "PAPER_PROPOSAL_CREATED"
        return "PASS"

    def _sandbox_writes_for(self, agent: str, status: str) -> tuple[str, ...]:
        if agent == "Initial Risk State Check":
            if status == "REJECT":
                return ("test/sandbox/memory/rejected_trades.md",)
            return ()
        if agent == "Final Risk Manager Check":
            if status == "REJECT":
                return (
                    "test/sandbox/memory/rejected_trades.md",
                    "test/sandbox/reports/risk_evaluation_report.json",
                )
            return ("test/sandbox/reports/risk_evaluation_report.json",)
        if agent == "Strategy Evaluation Gate":
            if status == "REJECT":
                return (
                    "test/sandbox/memory/rejected_trades.md",
                    "test/sandbox/reports/strategy_evaluation_report.json",
                    "test/sandbox/reports/evaluation_gate_report.json",
                    "test/sandbox/reports/human_approval_report.json",
                )
            return (
                "test/sandbox/reports/strategy_evaluation_report.json",
                "test/sandbox/reports/evaluation_gate_report.json",
                "test/sandbox/reports/human_approval_report.json",
            )
        if status == "REJECT":
            return ("test/sandbox/memory/rejected_trades.md",)
        if agent == "Trade Proposal Agent":
            return ("test/sandbox/memory/trade_proposals.md",)
        if agent == "Execution Gatekeeper":
            return (
                "test/sandbox/reports/paper_order_request_report.json",
                "test/sandbox/memory/paper_order_requests.md",
            )
        return ()

    def _write_memory_records(
        self,
        routine_name: str,
        outputs: list[AgentOutput],
        final_status: str,
        proposal: PaperTradeProposal | None,
        risk_evaluation: RiskEvaluation | None,
        human_approval: ApprovalRecord | None,
        approval_validation: ApprovalValidation | None,
        journal_commit: JournalEntry | None,
        strategy_evaluation: StrategyEvaluationReport | None,
        evaluation_gate: EvaluationGateResult | None,
        paper_order_request: PaperOrderRequest | None,
        paper_order_request_validation: PaperOrderRequestValidation | None,
        request_journal_commit: JournalEntry | None,
    ) -> tuple[str, ...]:
        assert self.sandbox_root is not None
        memory_dir = self.sandbox_root / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).isoformat()
        written: set[str] = set()

        for output in outputs:
            for relative_path in output.files_written:
                path = self.root / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                if relative_path.endswith("risk_evaluation_report.json"):
                    payload = risk_evaluation.as_dict() if risk_evaluation else {}
                    payload["paper_mode_label"] = "Paper Mode: REQUIRED"
                    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
                    written.add(relative_path)
                    continue
                if relative_path.endswith("human_approval_report.json"):
                    payload = {
                        "approval": human_approval.as_dict() if human_approval else None,
                        "validation": (
                            approval_validation.as_dict() if approval_validation else None
                        ),
                        "paper_mode_label": "Paper Mode: REQUIRED",
                    }
                    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
                    written.add(relative_path)
                    continue
                if relative_path.endswith("strategy_evaluation_report.json"):
                    payload = strategy_evaluation.as_dict() if strategy_evaluation else {}
                    payload["paper_mode_label"] = "Paper Mode: REQUIRED"
                    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
                    written.add(relative_path)
                    continue
                if relative_path.endswith("evaluation_gate_report.json"):
                    payload = evaluation_gate.as_dict() if evaluation_gate else {}
                    payload["paper_mode_label"] = "Paper Mode: REQUIRED"
                    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
                    written.add(relative_path)
                    continue
                if relative_path.endswith("paper_order_request_report.json"):
                    payload = {
                        "request": (
                            paper_order_request.as_dict() if paper_order_request else None
                        ),
                        "validation": (
                            paper_order_request_validation.as_dict()
                            if paper_order_request_validation
                            else None
                        ),
                        "request_journal_commit": (
                            request_journal_commit.as_dict() if request_journal_commit else None
                        ),
                        "paper_mode_label": "Paper Mode: REQUIRED",
                    }
                    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
                    written.add(relative_path)
                    continue
                if relative_path.endswith("paper_order_requests.md"):
                    request_lines = [
                        "# Simulated Paper Order Request",
                        "",
                        "Internal request only. No broker order or execution is created.",
                        "",
                        "Paper Mode: REQUIRED",
                        "",
                        "```json",
                        json.dumps(
                            paper_order_request.as_dict() if paper_order_request else {},
                            indent=2,
                        ),
                        "```",
                        "",
                    ]
                    path.write_text("\n".join(request_lines), encoding="utf-8")
                    written.add(relative_path)
                    continue
                if relative_path.endswith("trade_proposals.md") and proposal is not None:
                    proposal_lines = [
                        "# Simulated Paper Trade Proposal",
                        "",
                        "This is an internal paper-only proposal fixture. It is not executable.",
                        "",
                        "Paper Mode: REQUIRED",
                        "",
                        "```json",
                        json.dumps(proposal.as_dict(), indent=2),
                        "```",
                        "",
                    ]
                    path.write_text("\n".join(proposal_lines), encoding="utf-8")
                    written.add(relative_path)
                    continue
                path.write_text(
                    "\n".join(
                        [
                            f"# Simulated {output.agent} Output",
                            "",
                            f"Timestamp: {timestamp}",
                            f"Routine: {routine_name}",
                            f"Agent: {output.agent}",
                            f"Decision: {output.decision}",
                        f"Reason: {output.reason}",
                        "Journal Commit:",
                        json.dumps(journal_commit.as_dict() if journal_commit else {}, indent=2),
                            f"Final Status: {final_status}",
                            "Paper Mode: REQUIRED",
                            "Broker/Order/API Behavior: PROHIBITED",
                            "ADLC Compliance: ADLC_PASS",
                            "",
                        ]
                    ),
                    encoding="utf-8",
                )
                written.add(relative_path)
        self._files_written.extend(sorted(written))
        return tuple(sorted(written))

    def _write_report(self, report: SimulationReport) -> None:
        assert self.sandbox_root is not None
        report_dir = self.sandbox_root / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        relative_path = f"test/sandbox/reports/{report.routine_name}_simulation_report.json"
        path = self.root / relative_path
        path.write_text(json.dumps(report.as_dict(), indent=2) + "\n", encoding="utf-8")
        self._files_written.append(relative_path)

    def _final_status(
        self,
        outputs: list[AgentOutput],
        vetoes: list[str],
        gate_seen: bool,
    ) -> str:
        if vetoes:
            return "NO_TRADE"
        gate_outputs = [output for output in outputs if output.agent == "Execution Gatekeeper"]
        if gate_seen and gate_outputs and gate_outputs[-1].decision == "PAPER_TRADE_ALLOWED":
            return "PAPER_TRADE_ALLOWED"
        return "NO_TRADE"

    def _has_prohibited_behavior(self, outputs: list[AgentOutput]) -> bool:
        text = " ".join(output.decision for output in outputs).lower()
        return any(term in text for term in PROHIBITED_TERMS)


class _EvaluationJournalFixture:
    reason_for_final_decision = "Strategy evaluation passed before human approval."
    lessons_or_notes = "Evaluation-first gate fixture preserves journal readiness."


def format_markdown_report(reports: tuple[SimulationReport, ...]) -> str:
    lines = ["# Phase 6 Simulation Report", ""]
    for report in reports:
        lines.extend(
            [
                f"## {report.routine_name}",
                f"- Agents Invoked: {', '.join(report.agents_invoked)}",
                f"- Files Read: {len(report.files_read)} markdown files",
                f"- Files Written: {', '.join(report.files_written) or 'None'}",
                f"- Vetoes Triggered: {', '.join(report.vetoes_triggered) or 'None'}",
                f"- Final Status: {report.final_status}",
                f"- ADLC Compliance Status: {report.adlc_compliance_status}",
                f"- Data Source: {report.market_data.data_source}",
                f"- Data Timestamp: {report.market_data.data_timestamp}",
                f"- Timeframe: {report.market_data.timeframe}",
                f"- Freshness Status: {report.market_data.freshness_status}",
                f"- Completeness Status: {report.market_data.completeness_status}",
                f"- Data Integrity Status: {report.market_data.data_integrity_status}",
                f"- Paper Account Read Status: {report.paper_account.account.read_status}",
                (
                    "- Paper Account Trading Allowed In Principle: "
                    f"{report.paper_account.account.trading_allowed_in_principle}"
                ),
                (
                    "- Proposal Validation Status: "
                    f"{report.proposal_validation.status if report.proposal_validation else 'NOT_CREATED'}"
                ),
                (
                    "- Risk Evaluation Decision: "
                    f"{report.risk_evaluation.decision if report.risk_evaluation else 'NOT_RUN'}"
                ),
                (
                    "- Human Approval Status: "
                    f"{report.human_approval.approval_state if report.human_approval else 'NOT_REQUESTED'}"
                ),
                (
                    "- Journal Commit Event: "
                    f"{report.journal_commit.event_type if report.journal_commit else 'NOT_COMMITTED'}"
                ),
                (
                    "- Paper Order Request Status: "
                    f"{report.paper_order_request.final_status if report.paper_order_request else 'NOT_CREATED'}"
                ),
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic Phase 4 workflow simulation.")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--routine", choices=ROUTINES)
    parser.add_argument(
        "--market-data-fixture",
        choices=tuple(MOCK_MARKET_DATA_FIXTURES),
        default="fresh",
    )
    parser.add_argument(
        "--paper-account-source",
        choices=("mock", "env"),
        default="mock",
    )
    args = parser.parse_args()

    runtime = SimulationRuntime(Path(args.root))
    adapter = MockMarketDataAdapter(args.market_data_fixture)
    account_adapter: PaperAccountAdapter
    if args.paper_account_source == "env":
        try:
            account_adapter = AlpacaPaperAccountReadOnlyAdapter(AlpacaPaperConfig.from_env())
        except AlpacaReadOnlyError as error:
            account_adapter = MockAlpacaPaperAccountReadOnlyAdapter(
                unavailable_snapshot(type(error).__name__)
            )
    else:
        account_adapter = MockAlpacaPaperAccountReadOnlyAdapter()
    reports = (
        (
            runtime.run_routine(
                args.routine,
                market_data_adapter=adapter,
                paper_account_adapter=account_adapter,
            ),
        )
        if args.routine
        else tuple(
            runtime.run_routine(
                routine,
                market_data_adapter=adapter,
                paper_account_adapter=account_adapter,
            )
            for routine in ROUTINES
        )
    )
    print(format_markdown_report(reports))
    return 0 if all(report.adlc_compliance_status == "ADLC_PASS" for report in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
