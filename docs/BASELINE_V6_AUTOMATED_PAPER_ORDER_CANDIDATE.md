# Baseline V6 Automated Paper Order Request Candidate

## 1. Baseline Name

Baseline V6 Automated Paper Order Request Candidate.

## 2. Date

2026-05-20.

## 3. Difference From V1, V2, V3, V4, And V5

V1 established safe paper execution plus reconciliation.

V2 added the mandatory Evaluation-First Gate before Human Approval, Paper Order Request creation, and Paper Send.

V3 added the negative-case dataset and negative-case regression to prove the system can reject weak setups, recognize no-trade cases, block rubber-stamping, and prevent negative cases from creating paper send or broker execution readiness.

V4 added one successful V3-gated manual limited paper send. V4 did not expand notional, frequency, automation, or live trading authority.

V5 added automated proposal dry-run regression. V5 allowed automated analysis only in `DRY_RUN_ONLY`, one symbol only, and prohibited Paper Order Requests, Human Approval requests, Manual Execution Confirmation requests, order sends, broker readiness, multi-symbol automation, and live trading.

V6 adds automated Paper Order Request Candidate creation. A candidate is an inert review artifact created only after V5 gates pass for a valid `TRADE_PROPOSAL`. V6 does not authorize finalized Paper Order Request automation, Human Approval auto-approval, Manual Execution Confirmation automation, automated paper sends, broker execution readiness, notional increase, multi-symbol automation, or live trading.

## 4. Completed Gates

Completed gates through V6:

- Baseline V5: `PASS`.
- Phase 30 Automated Paper Request With Human Approval Design: `PASS`.
- Phase 31 Automated Paper Request Candidate Implementation: `PASS`.
- Candidate creation from valid `TRADE_PROPOSAL`: `PASS`.
- `NO_TRADE` candidate block: `PASS`.
- `REJECT` candidate block: `PASS`.
- Data integrity failure candidate block: `PASS`.
- Strategy Evaluation failure candidate block: `PASS`.
- Evaluation-First Gate block: `PASS`.
- Negative Case Regression failure candidate block: `PASS`.
- Known negative-case failure pattern block: `PASS`.
- Risk dry-run failure candidate block: `PASS`.
- `PAPER_ORDER_EXECUTION_ENABLED=true` candidate block: `PASS`.
- Multiple-symbol candidate block: `PASS`.
- Paper send readiness block: `PASS`.
- Broker execution readiness block: `PASS`.
- Full tests after Phase 31: `PASS`, 363 tests.
- No finalized Paper Order Request created: confirmed.
- No Human Approval requested automatically: confirmed.
- No Manual Execution Confirmation requested: confirmed.
- No order sent: confirmed.
- No broker execution readiness created: confirmed.

## 5. Baseline V5 Reference

Baseline V5 reference:

- `docs/BASELINE_V5_AUTOMATED_PROPOSAL_DRY_RUN.md`

## 6. Phase 30 Design Result

Phase 30 Automated Paper Request With Human Approval Design result: `PASS`.

Reference:

- `design/09_AUTOMATED_PAPER_REQUEST_WITH_HUMAN_APPROVAL.md`

## 7. Phase 31 Implementation Result

Phase 31 Automated Paper Request Candidate Implementation result: `PASS`.

Candidate artifact reference:

- `reports/automated_paper_request_candidate/20260520T100855Z/PAPER_ORDER_REQUEST_CANDIDATE.md`

Candidate journal reference:

- `reports/automated_paper_request_candidate/20260520T100855Z/PAPER_ORDER_REQUEST_CANDIDATE_JOURNAL.json`

## 8. What Phase 31 Proved

Phase 31 proved:

- A valid `TRADE_PROPOSAL` can create a Paper Order Request Candidate.
- `NO_TRADE` does not create a candidate.
- `REJECT` does not create a candidate.
- Data integrity failure blocks candidate creation.
- Strategy Evaluation failure blocks candidate creation.
- Evaluation-First Gate blocked status blocks candidate creation.
- Negative Case Regression failure blocks candidate creation.
- Known negative-case failure patterns block candidate creation.
- Risk dry-run failure blocks candidate creation.
- `PAPER_ORDER_EXECUTION_ENABLED=true` blocks candidate creation.
- More than one symbol blocks candidate creation.
- Paper send readiness blocks candidate creation.
- Broker execution readiness blocks candidate creation.
- Candidate artifact writing works.
- Candidate journal writing works.
- No finalized Paper Order Request is created.
- No Human Approval is requested automatically.
- No Manual Execution Confirmation is requested.
- No order is sent.
- No broker execution readiness is created.

Phase 31 does not prove readiness for finalized Paper Order Request automation, Human Approval workflow automation, Manual Execution Confirmation automation, automated Paper Send, higher notional, higher frequency, multi-symbol automation, or live trading.

## 9. Automated Candidate Capabilities

Allowed automated candidate capabilities after V6:

- Run automated dry-run analysis in `DRY_RUN_ONLY`.
- Process one symbol only.
- Create a Paper Order Request Candidate only from a valid `TRADE_PROPOSAL`.
- Require all candidate gates before candidate creation.
- Write candidate artifact.
- Write candidate journal entry.
- Stop after candidate creation.
- Preserve later human approval requirement.
- Preserve later manual execution confirmation requirement.

Candidate is not a broker order.
Candidate is not a finalized Paper Order Request.
Candidate cannot be sent.
Candidate cannot trigger Alpaca.
Candidate cannot create broker execution readiness.
Candidate requires human approval later.
Candidate requires manual execution confirmation later.

## 10. Automated Candidate Prohibitions

Automated candidate prohibitions after V6:

- Candidate cannot become a finalized Paper Order Request.
- Candidate cannot request Human Approval automatically.
- Candidate cannot request Manual Execution Confirmation.
- Candidate cannot send orders.
- Candidate cannot create paper send readiness.
- Candidate cannot create broker execution readiness.
- Candidate cannot enable `PAPER_ORDER_EXECUTION_ENABLED`.
- Candidate cannot trigger Alpaca.
- Candidate cannot use Alpaca order API.
- Candidate cannot use live trading.
- Candidate cannot use live endpoints.
- Candidate cannot use batch orders.
- Candidate cannot use cancel/replace.
- Candidate cannot process multiple symbols.

## 11. Candidate Safety Values

Every candidate must have these safety values:

- `paper_trading_only=true`
- `human_approval_required=true`
- `manual_execution_confirmation_required=true`
- `broker_execution_allowed=false`
- `live_trading_allowed=false`

These values were confirmed in the Phase 31 candidate artifact.

## 12. Candidate Required Gates

Candidate creation requires:

- `DRY_RUN_ONLY` mode.
- `PAPER_ORDER_EXECUTION_ENABLED` is not enabled.
- One symbol only.
- Automated dry-run decision is `TRADE_PROPOSAL`.
- Data Integrity `PASS`.
- Strategy Evaluation `PASS`.
- Evaluation-First Gate `EVALUATION_GATE_PASSED`.
- Negative Case Regression `PASS`.
- Proposal does not match known negative-case failure patterns.
- Risk Manager dry-run/read-only `PASS`.
- ADLC compliance `PASS`.
- Journal readiness `PASS`.
- No paper send readiness.
- No broker execution readiness.
- No live trading assumption.

## 13. Candidate Required Artifact

Required candidate artifact path:

```text
reports/automated_paper_request_candidate/<timestamp>/PAPER_ORDER_REQUEST_CANDIDATE.md
```

Phase 31 generated:

```text
reports/automated_paper_request_candidate/20260520T100855Z/PAPER_ORDER_REQUEST_CANDIDATE.md
```

## 14. Confirmed Safety Controls

Confirmed safety controls:

- Candidate is not a broker order.
- Candidate is not a finalized Paper Order Request.
- Candidate cannot be sent.
- Candidate cannot trigger Alpaca.
- Candidate cannot create broker execution readiness.
- Candidate requires human approval later.
- Candidate requires manual execution confirmation later.
- `paper_trading_only=true`.
- `human_approval_required=true`.
- `manual_execution_confirmation_required=true`.
- `broker_execution_allowed=false`.
- `live_trading_allowed=false`.
- No finalized Paper Order Request created.
- No Human Approval requested automatically.
- No Manual Execution Confirmation requested.
- No order sent.
- No broker execution readiness created.
- Live trading remains unsupported.

## 15. What Is Allowed After V6

After V6, the system may:

- Continue automated dry-run analysis.
- Continue automated Paper Order Request Candidate creation.
- Continue manual limited paper sends under V4/V5/V6 gates.
- Continue offline quality review.
- Continue negative-case expansion.
- Continue improving rejection and no-trade quality.
- Continue improving journal specificity.
- Continue improving strategy scoring.
- Continue deterministic candidate tests and audits.

## 16. What Remains Prohibited

The following remain prohibited after V6:

- Finalized Paper Order Request automation.
- Human Approval auto-approval.
- Manual Execution Confirmation automation.
- Automated Paper Send.
- Broker execution readiness.
- Increasing notional.
- Live trading.
- Batch orders.
- Cancel/replace.
- Multi-symbol automation.
- Higher frequency.
- Bypassing V4/V5/V6 gates.
- Bypassing Evaluation-First Gate.
- Bypassing Negative Case Regression.
- Bypassing Risk Manager.
- Bypassing journal readiness.
- Enabling `PAPER_ORDER_EXECUTION_ENABLED` outside a separately approved manual run.
- Alpaca order API usage from automated candidate flow.
- Live endpoints.
- Creating `.env` files with secrets.
- Printing secrets.

## 17. Conditions Before Finalized Paper Order Request

Before finalized Paper Order Request creation can be considered:

- Complete a separate design phase.
- Complete a separate implementation phase.
- Complete a separate audit.
- Preserve candidate safety values.
- Require explicit human approval.
- Require manual execution confirmation before any send path.
- Preserve V4/V5/V6 gates.
- Preserve no broker readiness from candidates.
- Demonstrate multiple clean candidate runs.
- Do not increase notional.
- Do not add live trading.

## 18. Conditions Before Human Approval Workflow

Before a Human Approval workflow can be considered:

- Complete a separate design phase.
- Complete a separate implementation phase.
- Complete a separate audit.
- Human Approval must not be auto-approval.
- Human Approval must be explicit, reviewable, and artifact-backed.
- Candidate fields and gate artifacts must be visible to the human.
- Approval must not create broker readiness.
- Approval must not send orders.
- Approval must not bypass Manual Execution Confirmation.
- Do not add live trading.

## 19. Conditions Before Manual Execution Confirmation

Before Manual Execution Confirmation can be considered:

- Complete a separate design phase.
- Complete a separate implementation phase.
- Complete a separate audit.
- Require finalized Paper Order Request controls first.
- Require explicit Human Approval first.
- Require journal readiness first.
- Require paper-only preflight first.
- Confirmation must not be automated.
- Confirmation must not bypass Paper Send Preflight.
- Do not add live trading.

## 20. Conditions Before Automated Paper Send

Before automated Paper Send can be considered:

- Complete a separate design phase.
- Complete a separate implementation phase.
- Complete a separate audit.
- Demonstrate multiple clean V4/V5/V6 manual runs.
- Demonstrate safe finalized Paper Order Request workflow.
- Demonstrate safe Human Approval workflow.
- Demonstrate safe Manual Execution Confirmation workflow.
- Demonstrate no broker readiness from negative cases or candidates.
- Preserve reconciliation and post-mortem requirements.
- Require explicit human approval for the scope change.
- Do not increase notional.
- Do not add live trading.

## 21. Conditions Before Increasing Notional

Before increasing notional can be considered:

- Complete a separate design phase.
- Complete a separate implementation phase.
- Complete a separate audit.
- Complete multiple clean V4/V5/V6 runs.
- Resolve all approval-rate, rejection-quality, and no-trade discipline red flags.
- Show improved negative-case metrics.
- Show improved candidate quality metrics.
- Show improved journal specificity.
- Require explicit human approval.
- Keep live trading unsupported.

## 22. Conditions Before Multi-Symbol Automation

Before multi-symbol automation can be considered:

- Complete a separate design phase.
- Complete a separate implementation phase.
- Complete a separate audit.
- Preserve one-symbol discipline until redesigned.
- Prove strong no-trade discipline.
- Prove strong rejection quality.
- Prove no approval-rate red flags.
- Prove no rubber-stamping red flags.
- Prove no broker readiness from candidates.
- Prove no live trading assumptions.
- Require explicit human approval.
- Keep live trading unsupported.

## 23. Live Trading Statement

Live trading remains unsupported.
