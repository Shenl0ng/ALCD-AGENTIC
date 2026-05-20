# Baseline V11 V10 Full Pipeline Dry-Run Regression

## 1. Baseline Name

Baseline V11 V10 Full Pipeline Dry-Run Regression.

## 2. Date

2026-05-20.

## 3. Difference From V1 Through V10

V1 established safe paper execution plus reconciliation.

V2 added the mandatory Evaluation-First Gate before Human Approval, Paper Order Request creation, and Paper Send.

V3 added the negative-case dataset and negative-case regression to prove the system can reject weak setups, recognize no-trade cases, block rubber-stamping, and prevent negative cases from creating paper send or broker execution readiness.

V4 added one successful V3-gated manual limited paper send. V4 did not expand notional, frequency, automation, or live trading authority.

V5 added automated proposal dry-run regression. V5 allowed automated analysis only in `DRY_RUN_ONLY`, one symbol only, and prohibited Paper Order Requests, Human Approval requests, Manual Execution Confirmation requests, order sends, broker readiness, multi-symbol automation, and live trading.

V6 added automated Paper Order Request Candidate creation. A candidate is an inert review artifact and is not a broker order, not a finalized Paper Order Request, cannot be sent, cannot trigger Alpaca, and cannot create broker execution readiness.

V7 added the Human Review Queue for candidates. V7 allowed a human to review a Paper Order Request Candidate and record a review status, but review approval did not authorize order sending, broker execution, Manual Execution Confirmation, or finalized Paper Order Request creation.

V8 added finalized Paper Order Request creation from a human-approved candidate. V8 creates an inert finalized request artifact only. Finalized Paper Order Request is not broker execution, cannot be sent by itself, does not authorize Alpaca order placement, still requires Manual Execution Confirmation later, and still requires Paper Send Preflight later.

V9 added Manual Execution Confirmation for a finalized Paper Order Request. Manual Execution Confirmation records explicit human confirmation that a specific finalized request may advance to Paper Send Preflight in a later phase, but it does not create Paper Send Preflight, send orders, create broker execution readiness, call Alpaca order API, enable `PAPER_ORDER_EXECUTION_ENABLED`, or support live trading.

V10 added Paper Send Preflight. Paper Send Preflight checks whether a manually confirmed finalized Paper Order Request is eligible to be considered by a later controlled paper send phase. It does not send orders, create broker execution readiness, call Alpaca, enable `PAPER_ORDER_EXECUTION_ENABLED`, or authorize live trading.

V11 adds full V10 pipeline dry-run regression through `PAPER_ORDER_SEND_ALLOWED`. V11 proves the complete dry-run path can progress from automated dry-run analysis through Paper Send Preflight and stop, without sending an order, calling Alpaca order API, enabling execution outside the blocked test scenario, or creating broker execution readiness.

## 4. Completed Gates

Completed gates through V11:

- Baseline V10: `PASS`.
- Phase 40 V10 Full Pipeline Dry-Run Regression Plan: `PASS`.
- Phase 41 V10 Full Pipeline Dry-Run Regression Implementation: `PASS`.
- Regression runner exists: `PASS`.
- Regression report generated: `PASS`.
- Full valid V10 pipeline scenario: `PASS`.
- Candidate blocked scenario: `PASS`.
- Human review rejected scenario: `PASS`.
- Manual confirmation rejected scenario: `PASS`.
- Preflight blocked scenario: `PASS`.
- `PAPER_ORDER_EXECUTION_ENABLED=true` blocked scenario: `PASS`.
- Full valid V10 pipeline reaches `PAPER_ORDER_SEND_ALLOWED`: `PASS`.
- Candidate blocked scenario blocks before review: `PASS`.
- Human review rejected scenario blocks before finalized request: `PASS`.
- Manual confirmation rejected scenario blocks before preflight allowed: `PASS`.
- Preflight blocked scenario produces `PAPER_ORDER_SEND_BLOCKED`: `PASS`.
- `PAPER_ORDER_EXECUTION_ENABLED=true` scenario blocks before progression: `PASS`.
- Full tests after Phase 41: `PASS`, 547 tests.
- No order sent during regression: confirmed.
- No Alpaca order API called during regression: confirmed.
- No broker execution readiness created: confirmed.
- No live trading readiness created: confirmed.
- No batch behavior created: confirmed.
- No cancel/replace behavior created: confirmed.
- Live trading remains unsupported.

## 5. Baseline V10 Reference

Baseline V10 reference:

- `docs/BASELINE_V10_PAPER_SEND_PREFLIGHT.md`

## 6. Phase 40 Plan Result

Phase 40 V10 Full Pipeline Dry-Run Regression Plan result: `PASS`.

Reference:

- `docs/PHASE_40_V10_FULL_PIPELINE_DRY_RUN_REGRESSION_PLAN.md`

## 7. Phase 41 Implementation Result

Phase 41 V10 Full Pipeline Dry-Run Regression Implementation result: `PASS`.

Regression runner reference:

- `runtime/v10_full_pipeline_dry_run_regression.py`

Regression test reference:

- `tests/test_v10_full_pipeline_dry_run_regression.py`

Regression report reference:

- `reports/v10_full_pipeline_dry_run_regression/20260520T110737Z/V10_FULL_PIPELINE_DRY_RUN_REGRESSION_REPORT.md`

## 8. What Phase 41 Proved

Phase 41 proved:

- Full V10 pipeline can reach `PAPER_ORDER_SEND_ALLOWED` in dry-run regression.
- `PAPER_ORDER_SEND_ALLOWED` is not broker execution.
- `PAPER_ORDER_SEND_ALLOWED` is not order submission.
- No order was sent during regression.
- No Alpaca order API was called during regression.
- No broker execution readiness was created.
- `PAPER_ORDER_EXECUTION_ENABLED` was not enabled except blocked test scenario.
- Invalid scenarios blocked at the correct stage.
- Candidate blocked scenario blocked before review.
- Human review rejected scenario blocked before finalized request.
- Manual confirmation rejected scenario blocked before preflight allowed.
- Preflight blocked scenario produced `PAPER_ORDER_SEND_BLOCKED`.
- `PAPER_ORDER_EXECUTION_ENABLED=true` scenario blocked before progression.
- Live trading remains unsupported.

Phase 41 does not prove readiness for automated Paper Send, increasing notional, multi-symbol automation, higher frequency, batch orders, cancel/replace, broker execution readiness outside a controlled send phase, or live trading.

## 9. Full V10 Pipeline Coverage

The V11 dry-run regression covers this full V10 pipeline:

```text
Automated dry-run
-> TRADE_PROPOSAL
-> Paper Order Request Candidate
-> Human Review Queue
-> Finalized Paper Order Request
-> Manual Execution Confirmation
-> Paper Send Preflight
-> stop
```

The valid scenario confirmed:

- `TRADE_PROPOSAL` created.
- Paper Order Request Candidate created.
- Human Review Queue approved for paper request.
- Finalized Paper Order Request created.
- Manual Execution Confirmation confirmed for Paper Send Preflight.
- Paper Send Preflight reached `PAPER_ORDER_SEND_ALLOWED`.
- Pipeline stopped after preflight.
- No order was sent.

## 10. Regression Scenario Coverage

V11 regression scenario coverage:

- Full valid V10 pipeline: reached `PAPER_ORDER_SEND_ALLOWED`.
- Candidate blocked scenario: blocked before Human Review Queue.
- Human review rejected scenario: blocked before finalized Paper Order Request.
- Manual confirmation rejected scenario: blocked before preflight allowed.
- Preflight blocked scenario: produced `PAPER_ORDER_SEND_BLOCKED`.
- `PAPER_ORDER_EXECUTION_ENABLED=true` scenario: blocked before progression.

Each invalid scenario blocked at the correct stage and did not progress into later pipeline stages.

## 11. Confirmed Safety Controls

Confirmed safety controls after V11:

- Paper trading only.
- One symbol only.
- Max notional remains `<= 100 USD`.
- Limit order only.
- Day time-in-force only.
- No short selling.
- No crypto.
- No options.
- No margin/leverage.
- No extended hours.
- No batch behavior.
- No cancel/replace behavior.
- No live trading.
- No live endpoints.
- No Alpaca order API calls.
- No order submission.
- No broker execution readiness.
- No live trading readiness.
- `PAPER_ORDER_EXECUTION_ENABLED` remains disabled except inside the blocked test scenario.
- Human review remains required before finalized Paper Order Request creation.
- Manual Execution Confirmation remains required before Paper Send Preflight.
- Paper Send Preflight remains a stop point, not execution authority.

## 12. What Is Allowed After V11

Allowed after V11:

- Continue automated dry-run analysis.
- Continue automated Paper Order Request Candidate creation.
- Continue Human Review Queue.
- Continue finalized Paper Order Request creation from human-approved candidates.
- Continue Manual Execution Confirmation.
- Continue Paper Send Preflight.
- Continue full pipeline dry-run regression.
- Continue manual limited paper sends under V4-V11 gates.
- Design one controlled V10 paper send.

## 13. What Remains Prohibited

Still prohibited after V11:

- Automated Paper Send.
- Broker execution readiness outside controlled send phase.
- Increasing notional.
- Live trading.
- Batch orders.
- Cancel/replace.
- Multi-symbol automation.
- Higher frequency.
- Bypassing V4-V11 gates.
- Alpaca order API use outside an explicitly approved controlled paper send phase.
- Enabling `PAPER_ORDER_EXECUTION_ENABLED` outside an explicitly blocked safety test or approved controlled paper send phase.

## 14. Conditions Before Controlled V10 Paper Send

Before any controlled V10 paper send:

- Baseline V11 must remain `PASS`.
- Full V10 pipeline dry-run regression must remain `PASS`.
- The exact trade must pass V4-V11 gates.
- One symbol only.
- Max notional `<= 100 USD`.
- Limit order only.
- Day time-in-force only.
- No short selling.
- No crypto.
- No options.
- No margin/leverage.
- No extended hours.
- No batch behavior.
- No cancel/replace behavior.
- Human review must approve the candidate.
- Finalized Paper Order Request must exist.
- Manual Execution Confirmation must exist.
- Paper Send Preflight must produce `PAPER_ORDER_SEND_ALLOWED`.
- Any broker execution readiness must be explicitly scoped to one controlled paper send phase only.
- Post-send reconciliation and journaling must be ready before the send.

## 15. Conditions Before Automated Paper Send

Before automated Paper Send can be considered:

- Multiple controlled manual V10 paper sends must be completed and reviewed.
- Post-send reconciliation must be consistently successful.
- Failure modes must be audited and documented.
- Human accountability boundaries must be redefined.
- Risk controls must be expanded and revalidated.
- Automated Paper Send design must be separately approved.
- Automated Paper Send regression must prove no bypass of V4-V11 gates.
- Explicit change control must authorize the new autonomy boundary.

Automated Paper Send remains prohibited after V11.

## 16. Conditions Before Increasing Notional

Before increasing notional:

- The `<= 100 USD` notional limit must remain enforced until a future baseline explicitly changes it.
- Controlled paper send history must demonstrate process quality, not profit chasing.
- Weekly Review and Failure Auditor findings must support any change.
- Risk Manager limits must be redesigned and revalidated.
- Evaluation metrics must prove selectivity and drawdown control.
- Human approval must explicitly authorize any proposed notional increase.

Increasing notional remains prohibited after V11.

## 17. Conditions Before Multi-Symbol Automation

Before multi-symbol automation:

- One-symbol regression must remain stable.
- Symbol selection governance must be designed.
- Data Integrity checks must be expanded for multiple symbols.
- Risk aggregation must be designed and validated.
- Batch behavior must remain blocked unless separately authorized by a future baseline.
- Multi-symbol failure modes must be documented.
- A separate multi-symbol dry-run regression must pass.

Multi-symbol automation remains prohibited after V11.

## 18. Live Trading Statement

Live trading remains unsupported.

V11 does not authorize live trading, live endpoints, real-money execution, automated Paper Send, notional increase, batch orders, cancel/replace behavior, multi-symbol automation, or bypassing V4-V11 gates.
