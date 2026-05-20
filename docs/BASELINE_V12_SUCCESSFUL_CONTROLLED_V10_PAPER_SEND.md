# Baseline V12 Successful Controlled V10 Paper Send

## 1. Baseline Name

Baseline V12 Successful Controlled V10 Paper Send.

## 2. Date

2026-05-20.

## 3. Difference From V1 Through V11

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

V11 added full V10 pipeline dry-run regression through `PAPER_ORDER_SEND_ALLOWED`. V11 proved the complete dry-run path can progress from automated dry-run analysis through Paper Send Preflight and stop, without sending an order, calling Alpaca order API, enabling execution outside the blocked test scenario, or creating broker execution readiness.

V12 adds one successful controlled V10 Alpaca paper send. V12 proves the complete V10 pipeline can produce one controlled Alpaca paper order after all V12 gates pass, while preserving paper-only, one-order, limit/day, max-notional, reconciliation, post-send safety, and post-mortem controls.

## 4. Completed Gates

Completed gates through V12:

- Baseline V11: `PASS`.
- Phase 42 Controlled V10 Paper Send Design: `PASS`.
- Phase 43 Controlled V10 Paper Send Implementation: `PASS`.
- Phase 43 Controlled V10 Paper Send Run: `PASS`.
- Full tests: `PASS`, 582 tests.
- Architecture validation: `PASS`.
- V10 full pipeline dry-run regression: `PASS`.
- Strategy evaluation: `PASS`.
- Evaluation-First Gate: `EVALUATION_GATE_PASSED`.
- Negative Case Regression: `PASS`.
- Candidate status: `PAPER_ORDER_CANDIDATE_CREATED`.
- Human Review status: `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST`.
- Finalized Paper Order Request status: `PAPER_ORDER_REQUEST_FINALIZED`.
- Manual Execution Confirmation status: `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`.
- Paper Send Preflight status: `PAPER_ORDER_SEND_ALLOWED`.
- Paper send status: `PAPER_ORDER_SUBMITTED`.
- Reconciliation status: `RECONCILIATION_MATCHED`.
- Secrets printed: no.
- System returned to `DRY_RUN_ONLY`: confirmed.
- Increasing notional remains prohibited.
- Automation beyond approved V10 pipeline remains prohibited.
- Batch orders remain prohibited.
- Cancel/replace remains prohibited.
- Live trading remains unsupported.

## 5. Baseline V11 Reference

Baseline V11 reference:

- `docs/BASELINE_V11_V10_FULL_PIPELINE_DRY_RUN_REGRESSION.md`

## 6. Phase 42 Design Result

Phase 42 Controlled V10 Paper Send Design result: `PASS`.

Reference:

- `design/14_CONTROLLED_V10_PAPER_SEND.md`

## 7. Phase 43 Implementation Result

Phase 43 Controlled V10 Paper Send Implementation result: `PASS`.

Implementation references:

- `runtime/v10_controlled_paper_send.py`
- `tests/test_v10_controlled_paper_send.py`

## 8. Phase 43 Run Result

Phase 43 Controlled V10 Paper Send Run result: `PASS`.

Known run values:

- Test status: Full tests: `PASS`, 582 tests.
- Architecture validation: `PASS`.
- V10 full pipeline dry-run regression: `PASS`.
- Strategy evaluation: `PASS`.
- Evaluation-First Gate: `EVALUATION_GATE_PASSED`.
- Negative Case Regression: `PASS`.
- Candidate status: `PAPER_ORDER_CANDIDATE_CREATED`.
- Human Review status: `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST`.
- Finalized Paper Order Request status: `PAPER_ORDER_REQUEST_FINALIZED`.
- Manual Execution Confirmation status: `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`.
- Paper Send Preflight status: `PAPER_ORDER_SEND_ALLOWED`.
- Paper send status: `PAPER_ORDER_SUBMITTED`.
- Alpaca paper order id: `30ad9c46-cba2-4d0b-9a82-4bc918def1f4`.
- Reconciliation status: `RECONCILIATION_MATCHED`.
- Secrets printed: no.
- System returned to `DRY_RUN_ONLY`: confirmed.

## 9. What Phase 43 Proved

Phase 43 proved:

- V12 proves the complete V10 pipeline can produce one controlled Alpaca paper order.
- The controlled send can submit one Alpaca paper limit/day order only after all V12 gates pass.
- `PAPER_ORDER_SEND_ALLOWED` can feed a controlled manual paper send phase.
- Reconciliation can complete with `RECONCILIATION_MATCHED`.
- Required controlled-send artifacts can be written.
- Required post-send safety checks can be written.
- Required post-mortem can be written.
- Secrets were not printed.
- System returned to `DRY_RUN_ONLY`.
- Live trading remains unsupported.

Phase 43 did not prove or authorize general automation, automated Paper Send, live trading, notional increase, batch orders, cancel/replace, multi-symbol automation, higher frequency, or bypassing V4-V12 gates.

## 10. Full V10 Pipeline Proof

The successful controlled send used this V10 pipeline:

```text
Automated dry-run
-> Strategy Evaluation Harness
-> Evaluation-First Gate
-> Negative Case Regression
-> Paper Order Request Candidate
-> Human Review Queue
-> Finalized Paper Order Request
-> Manual Execution Confirmation
-> Paper Send Preflight
-> Controlled Alpaca Paper Send
-> Reconciliation
-> Post-mortem
```

Pipeline proof:

- Candidate status: `PAPER_ORDER_CANDIDATE_CREATED`.
- Human Review status: `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST`.
- Finalized Paper Order Request status: `PAPER_ORDER_REQUEST_FINALIZED`.
- Manual Execution Confirmation status: `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`.
- Paper Send Preflight status: `PAPER_ORDER_SEND_ALLOWED`.
- Paper send status: `PAPER_ORDER_SUBMITTED`.
- Reconciliation status: `RECONCILIATION_MATCHED`.

No stage may be skipped in future controlled sends.

## 11. Controlled Paper Send Result

Controlled paper send result:

- Paper send status: `PAPER_ORDER_SUBMITTED`.
- One order only: confirmed.
- Paper trading only: confirmed.
- Max notional `<= 100 USD`: confirmed.
- Limit order only: confirmed.
- Day time-in-force only: confirmed.
- No short selling: confirmed.
- No crypto: confirmed.
- No options: confirmed.
- No margin/leverage: confirmed.
- No extended hours: confirmed.
- No batch orders: confirmed.
- No cancel/replace: confirmed.
- No live trading: confirmed.
- No live endpoints: confirmed.

## 12. Alpaca Paper Order ID

Alpaca paper order id:

```text
30ad9c46-cba2-4d0b-9a82-4bc918def1f4
```

This is a paper order id only. It is not live trading evidence and does not authorize future automated sends.

## 13. Reconciliation Result

Reconciliation result: `RECONCILIATION_MATCHED`.

Reconciliation confirmed:

- Broker paper order id was recorded.
- No extra orders were created.
- No batch orders were created.
- No cancel/replace occurred.
- Live trading remains unsupported.

## 14. Artifact References

Controlled send artifact references:

- V10 controlled send report: `reports/v10_controlled_paper_send/20260520T112905Z/V10_CONTROLLED_PAPER_SEND_REPORT.md`
- Reconciliation: `reports/v10_controlled_paper_send/20260520T112905Z/RECONCILIATION.md`
- Post-send safety: `reports/v10_controlled_paper_send/20260520T112905Z/POST_SEND_SAFETY.md`
- Post-mortem: `reports/v10_controlled_paper_send/20260520T112905Z/POST_MORTEM.md`

## 15. Confirmed Safety Controls

Confirmed safety controls after V12:

- `PAPER_ORDER_EXECUTION_ENABLED` must remain disabled by default.
- Future sends require explicit manual enablement and all V12 gates.
- System returned to `DRY_RUN_ONLY`: confirmed.
- Secrets printed: no.
- Paper trading only.
- One order only.
- Max notional `<= 100 USD`.
- Limit order only.
- Day time-in-force only.
- No short selling.
- No crypto.
- No options.
- No margin/leverage.
- No extended hours.
- No batch orders.
- No cancel/replace.
- No live trading.
- No live endpoints.
- Reconciliation required.
- Post-send safety required.
- Post-mortem required.
- Increasing notional remains prohibited.
- Automation beyond approved V10 pipeline remains prohibited.
- Batch orders remain prohibited.
- Cancel/replace remains prohibited.
- Live trading remains unsupported.

## 16. What Is Allowed After V12

Allowed after V12:

- Continue automated dry-run analysis.
- Continue automated Paper Order Request Candidate creation.
- Continue Human Review Queue.
- Continue finalized Paper Order Request creation from human-approved candidates.
- Continue Manual Execution Confirmation.
- Continue Paper Send Preflight.
- Continue controlled manual V10 paper sends only under V12 gates.
- Continue offline quality review.
- Continue negative-case expansion.
- Continue improving rejection and no-trade quality.

## 17. What Remains Prohibited

Still prohibited after V12:

- Automated Paper Send.
- Live trading.
- Increasing notional.
- Batch orders.
- Cancel/replace.
- Multi-symbol automation.
- Higher frequency.
- Bypassing V4-V12 gates.
- Leaving `PAPER_ORDER_EXECUTION_ENABLED` enabled by default.
- General broker execution readiness.
- Live endpoints.
- Secret printing.

## 18. Conditions Before Another Controlled Paper Send

Before another controlled V10 paper send:

- Baseline V12 must remain `PASS`.
- Full tests must be `PASS`.
- Architecture validation must be `PASS`.
- V10 full pipeline dry-run regression must be `PASS`.
- Strategy Evaluation must be `PASS`.
- Evaluation-First Gate must be `EVALUATION_GATE_PASSED`.
- Negative Case Regression must be `PASS`.
- Candidate must be created from a valid `TRADE_PROPOSAL`.
- Human Review must be `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST`.
- Finalized Paper Order Request must be `PAPER_ORDER_REQUEST_FINALIZED`.
- Manual Execution Confirmation must be `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`.
- Paper Send Preflight must be `PAPER_ORDER_SEND_ALLOWED`.
- Alpaca paper account must be confirmed.
- Live endpoint must be rejected.
- `PAPER_ORDER_EXECUTION_ENABLED=true` may be set only for the explicit manual send run.
- `PAPER_ORDER_EXECUTION_ENABLED` must be unset after the run.
- Reconciliation, post-send safety, and post-mortem artifacts must be created.
- Notional must remain `<= 100 USD`.
- One order only.
- Limit/day only.
- No batch orders.
- No cancel/replace.
- No live trading.

## 19. Conditions Before Automated Paper Send

Before automated Paper Send can be considered:

- Multiple controlled manual V10 paper sends must be completed and reviewed.
- Reconciliation must be consistently `RECONCILIATION_MATCHED`.
- Failure modes must be audited and documented.
- Weekly Review and Failure Auditor findings must support any change.
- Human accountability boundaries must be redesigned.
- Risk controls must be expanded and revalidated.
- Automated Paper Send design must be separately approved.
- Automated Paper Send regression must prove no bypass of V4-V12 gates.
- Explicit change control must authorize the new autonomy boundary.

Automated Paper Send remains prohibited after V12.

## 20. Conditions Before Increasing Notional

Before increasing notional:

- The `<= 100 USD` notional limit must remain enforced until a future baseline explicitly changes it.
- Controlled paper send history must demonstrate process quality, not profit chasing.
- Reconciliation and post-send safety must remain clean across multiple controlled sends.
- Weekly Review and Failure Auditor findings must support any change.
- Risk Manager limits must be redesigned and revalidated.
- Evaluation metrics must prove selectivity and drawdown control.
- Human approval must explicitly authorize any proposed notional increase.

Increasing notional remains prohibited after V12.

## 21. Conditions Before Multi-Symbol Automation

Before multi-symbol automation:

- One-symbol controlled send behavior must remain stable.
- Symbol selection governance must be designed.
- Data Integrity checks must be expanded for multiple symbols.
- Risk aggregation must be designed and validated.
- Batch behavior must remain blocked unless separately authorized by a future baseline.
- Multi-symbol failure modes must be documented.
- A separate multi-symbol dry-run regression must pass.
- Controlled send behavior must not be generalized into automated multi-symbol execution without explicit future authorization.

Multi-symbol automation remains prohibited after V12.

## 22. Live Trading Statement

Live trading remains unsupported.

V12 does not authorize general automation.
V12 does not authorize automated paper sends.
V12 does not authorize live trading.
V12 does not authorize increasing notional.
V12 does not authorize batch orders.
V12 does not authorize cancel/replace.

`PAPER_ORDER_EXECUTION_ENABLED` must remain disabled by default.

Future sends require explicit manual enablement and all V12 gates.
