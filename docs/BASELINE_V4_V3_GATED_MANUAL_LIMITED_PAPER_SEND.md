# Baseline V4 V3-Gated Manual Limited Paper Send

## 1. Baseline Name

Baseline V4 V3-Gated Manual Limited Paper Send.

## 2. Date

2026-05-20.

## 3. Difference From V1, V2, And V3

V1 established safe paper execution plus reconciliation.

V2 added the mandatory Evaluation-First Gate before Human Approval, Paper Order Request creation, and Paper Send.

V3 added the negative-case dataset and negative-case regression to prove the system can reject weak setups, recognize no-trade cases, block rubber-stamping, and prevent negative cases from creating paper send or broker execution readiness.

V4 adds one successful V3-gated manual limited paper send. V4 does not expand notional, frequency, automation, or live trading authority.

## 4. Completed Gates

Completed gates through V4:

- Baseline Selective Evaluation V3: `PASS`.
- Phase 25 V3-Gated Manual Paper Send: `PASS`.
- Full tests: `PASS`, 289 tests.
- Architecture validation: `PASS`.
- Strategy Evaluation: `PASS`.
- Evaluation-First Gate: `EVALUATION_GATE_PASSED`.
- Negative Case Regression: `PASS`.
- Negative-case readiness: no paper send readiness, no broker execution readiness, proposal did not match known negative-case failure patterns.
- Dry-run: `DRY_RUN_COMPLETED`.
- Mocked send: `MOCKED_PAPER_SEND_COMPLETED`.
- Paper send: `PAPER_ORDER_SUBMITTED`.
- Reconciliation: `RECONCILIATION_MATCHED`.
- System returned to `DRY_RUN_ONLY`: confirmed.
- Secrets printed: no.

## 5. Baseline V3 Reference

Baseline V3 reference:

- `docs/BASELINE_SELECTIVE_EVALUATION_V3.md`

## 6. Phase 25 Plan Reference

Phase 25 plan reference:

- `docs/PHASE_25_V3_GATED_MANUAL_LIMITED_PAPER_SEND_PLAN.md`

## 7. Phase 25 Run Summary Reference

Phase 25 run summary reference:

- `reports/first_controlled_paper_send/20260520T020441Z/PHASE_25_RUN_SUMMARY.md`

## 8. Controlled Paper Send Report Reference

Controlled paper send report reference:

- `reports/first_controlled_paper_send/20260520T020441Z/FIRST_CONTROLLED_PAPER_SEND_REPORT.md`

## 9. Post-Mortem Reference

Post-mortem reference:

- `reports/first_controlled_paper_send/20260520T020441Z/POST_MORTEM.md`

## 10. Test Result

Test status: `PASS`, 289 tests.

## 11. Architecture Validation Result

Architecture validation: `PASS`.

## 12. Strategy Evaluation Result

Strategy evaluation: `PASS`.

## 13. Evaluation-First Gate Result

Evaluation-First Gate: `EVALUATION_GATE_PASSED`.

## 14. Negative Case Regression Result

Negative Case Regression: `PASS`.

## 15. Negative-Case Readiness Result

Negative-case readiness:

- No paper send readiness from negative cases.
- No broker execution readiness from negative cases.
- Proposal did not match known negative-case failure patterns.

## 16. Dry-Run Result

Dry-run: `DRY_RUN_COMPLETED`.

## 17. Mocked Send Result

Mocked send: `MOCKED_PAPER_SEND_COMPLETED`.

## 18. Paper Send Result

Paper send: `PAPER_ORDER_SUBMITTED`.

## 19. Alpaca Paper Order ID

Alpaca paper order id:

- `e9b866d3-0f02-4d33-ba80-4d7a19242533`

## 20. Reconciliation Result

Reconciliation: `RECONCILIATION_MATCHED`.

## 21. Safety Controls Confirmed

Safety controls confirmed:

- Paper trading only.
- Manual limited paper send only.
- One order only.
- Max notional `<= 100 USD`.
- Limit order only.
- Time in force: `day`.
- No live trading touched.
- No live endpoints used.
- No batch orders.
- No cancel/replace.
- No short selling.
- No crypto.
- No options.
- No margin or leverage.
- No extended hours.
- No notional increase.
- No frequency increase.
- Strategy Evaluation required.
- Evaluation-First Gate required.
- Negative Case Regression required.
- Risk Manager required.
- Human Approval required.
- Journal Commit required.
- Manual Execution Confirmation required.
- Paper Send Preflight required.
- Reconciliation required.
- Post-mortem required.
- Secrets printed: no.
- System returned to `DRY_RUN_ONLY`: confirmed.

## 22. What V4 Proves

V4 proves:

- The system can complete a manual limited Alpaca paper send under V3 gates.
- The send path can remain gated by Strategy Evaluation, Evaluation-First Gate, Negative Case Regression, Risk Manager, Human Approval, Journal Commit, Manual Execution Confirmation, Paper Send Preflight, Reconciliation, and Post-Mortem.
- Negative-case protections can remain active before a controlled paper send.
- Negative cases do not create paper send readiness.
- Negative cases do not create broker execution readiness.
- A valid proposal can pass V3 checks without matching known negative-case failure patterns.
- The system can submit one paper order and reconcile it as matched.
- The system can return to `DRY_RUN_ONLY` after the run.

V4 does not prove readiness for higher frequency, higher notional, automation, or live trading.

## 23. What Is Allowed After V4

After V4, the system may:

- Continue manual limited paper sends only under V4 gates.
- Continue offline quality review.
- Continue negative-case expansion.
- Continue improving rejection quality.
- Continue improving no-trade quality.
- Continue running deterministic tests.
- Continue running negative-case regression before future controlled paper sends.

## 24. What Remains Prohibited

The following remain prohibited after V4:

- Increasing notional.
- Automation.
- Live trading.
- Batch orders.
- Cancel/replace.
- Higher frequency.
- Bypassing Evaluation-First Gate.
- Bypassing Negative Case Regression.
- Bypassing Risk Manager.
- Bypassing Human Approval.
- Bypassing Journal Commit.
- Bypassing Manual Execution Confirmation.
- Bypassing Paper Send Preflight.
- Broker execution from negative cases.
- Paper send readiness from negative cases.
- Live endpoints.
- Market orders.
- Short selling.
- Crypto.
- Options.
- Margin or leverage.
- Extended-hours trading.
- Creating `.env` files with secrets.
- Printing secrets.
- LLM API calls.

## 25. Conditions Before Another Paper Send

Before another paper send:

- Review this V4 baseline.
- Run full tests and require `PASS`.
- Run architecture validation and require `PASS`.
- Run Strategy Evaluation and require `PASS`.
- Run Evaluation-First Gate and require `EVALUATION_GATE_PASSED`.
- Run Negative Case Regression and require `PASS`.
- Confirm no missed blocks or false passes in negative-case regression.
- Confirm no negative case produces paper send readiness.
- Confirm no negative case produces broker execution readiness.
- Confirm the proposal does not match known negative-case failure patterns.
- Confirm Risk Manager output is `RISK_APPROVED`.
- Confirm Human Approval is `HUMAN_APPROVED_FOR_PAPER_ONLY`.
- Confirm Journal Commit exists before send.
- Confirm Manual Execution Confirmation is `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY`.
- Confirm Paper Send Preflight is `PAPER_ORDER_SEND_ALLOWED`.
- Confirm paper account mode.
- Confirm live endpoint rejection.
- Confirm max notional remains `<= 100 USD`.
- Confirm one order only.
- Confirm limit order only.
- Confirm time in force is `day`.
- Reconcile after send if submitted.
- Create report, post-mortem, and run summary.
- Return system to `DRY_RUN_ONLY`.
- Unset `PAPER_ORDER_EXECUTION_ENABLED` after the run.

## 26. Conditions Before Increasing Notional

Increasing notional is prohibited by V4.

Before any notional increase:

- A future design phase must explicitly justify the change.
- Offline quality review must show approval bias is resolved.
- Negative-case regression must continue to pass.
- Rejection and no-trade quality must improve.
- Risk governance must be updated.
- Deterministic tests must prove the new cap is enforced.
- Human accountability must remain mandatory.

V4 does not recommend increasing notional.

## 27. Conditions Before Automation

Automation is prohibited by V4.

Before any automation:

- A future design phase must explicitly justify the change.
- Offline quality review must show no approval-bias red flag.
- Negative-case regression must continue to pass.
- No-trade recognition must remain strong.
- Weak setup rejection must remain strong.
- Rubber-stamping detection must remain strong.
- Journal/evidence failure detection must remain strong.
- Human accountability requirements must be redesigned and approved.

V4 does not recommend automation.

## 28. Explicit Live Trading Boundary

Live trading remains unsupported.

V4 does not design, imply, prepare, or authorize live trading. Any live trading assumption remains a blocking failure.

## Offline Safety Statement

This baseline records a completed controlled paper send. It does not send a new order, enable `PAPER_ORDER_EXECUTION_ENABLED`, use Alpaca API, modify runtime code, add features, create `.env` files, or print secrets.
