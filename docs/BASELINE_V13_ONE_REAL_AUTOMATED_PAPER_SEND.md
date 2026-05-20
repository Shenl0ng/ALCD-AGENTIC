# Baseline V13 One Real Automated Paper Send

## 1. Baseline Name

Baseline V13 One Real Automated Paper Send.

## 2. Date

2026-05-20.

## 3. Difference From V1 Through V12

V1 established safe paper execution plus reconciliation.

V2 added the mandatory Evaluation-First Gate before Human Approval, Paper Order Request creation, and Paper Send.

V3 added the negative-case dataset and negative-case regression to prove the system can reject weak setups, recognize no-trade cases, block rubber-stamping, and prevent negative cases from creating paper send or broker execution readiness.

V4 added one successful V3-gated manual limited paper send.

V5 added automated proposal dry-run regression.

V6 added automated Paper Order Request Candidate creation.

V7 added the Human Review Queue.

V8 added finalized Paper Order Request creation from a human-approved candidate.

V9 added Manual Execution Confirmation for a finalized Paper Order Request.

V10 added Paper Send Preflight.

V11 added full V10 pipeline dry-run regression through `PAPER_ORDER_SEND_ALLOWED`.

V12 added one successful controlled V10 Alpaca paper send.

V13 adds one successful real automated Alpaca paper send after all V13 gates passed. V13 proves the system can perform one real automated Alpaca paper send, but it does not authorize repeated automated sends, general automated trading, live trading, increasing notional, batch orders, cancel/replace, or multi-symbol automation.

## 4. Completed Gates

Completed gates through V13:

- Baseline V12: `PASS`.
- Phase 44 Automated Paper Send Design: `PASS`.
- Phase 45 Automated Paper Send Implementation: `PASS`.
- Phase 47 Automated Paper Send Mocked Regression: `PASS`.
- Phase 48 One Real Automated Paper Send Design: `PASS`.
- Phase 49 One Real Automated Paper Send Implementation: `PASS`.
- One Real Automated Paper Send Run: `PASS`.
- Full tests: `PASS`, 684 tests.
- Architecture validation: `PASS`.
- V10 full pipeline dry-run regression: `PASS`.
- Automated paper send mocked regression: `PASS`.
- Strategy evaluation: `PASS`.
- Evaluation-First Gate: `EVALUATION_GATE_PASSED`.
- Negative Case Regression: `PASS`.
- Candidate status: `PAPER_ORDER_CANDIDATE_CREATED`.
- Human Review status: `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST`.
- Finalized Paper Order Request status: `PAPER_ORDER_REQUEST_FINALIZED`.
- Manual Execution Confirmation status: `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`.
- Paper Send Preflight status: `PAPER_ORDER_SEND_ALLOWED`.
- Automation kill switch status: inactive.
- Daily order limit status: not exceeded.
- Daily notional limit status: not exceeded.
- Cooldown status: satisfied.
- Previous reconciliation status: exists and matched.
- Previous post-mortem status: exists with no blockers.
- Unresolved issue status: none.
- Paper send status: `ONE_REAL_AUTOMATED_PAPER_SEND_SUBMITTED`.
- Reconciliation status: `RECONCILIATION_MATCHED`.
- Secrets printed: no.
- System returned to `DRY_RUN_ONLY`: confirmed.
- `PAPER_ORDER_EXECUTION_ENABLED` disabled/false after run: confirmed.
- `PAPER_AUTOMATED_SEND_ENABLED` disabled/false after run: confirmed.

## 5. Baseline V12 Reference

Baseline V12 reference:

- `docs/BASELINE_V12_SUCCESSFUL_CONTROLLED_V10_PAPER_SEND.md`

## 6. Phase 44 Design Result

Phase 44 Automated Paper Send Design result: `PASS`.

Reference:

- `design/15_AUTOMATED_PAPER_SEND.md`

## 7. Phase 45 Implementation Result

Phase 45 Automated Paper Send Implementation result: `PASS`.

Implementation references:

- `runtime/automated_paper_send.py`
- `tests/test_automated_paper_send.py`

## 8. Phase 47 Mocked Regression Result

Phase 47 Automated Paper Send Mocked Regression result: `PASS`.

References:

- `docs/PHASE_46_AUTOMATED_PAPER_SEND_MOCKED_REGRESSION_PLAN.md`
- `runtime/automated_paper_send_mocked_regression.py`
- `tests/test_automated_paper_send_mocked_regression.py`
- `reports/automated_paper_send_mocked_regression/`

## 9. Phase 48 Design Result

Phase 48 One Real Automated Paper Send Design result: `PASS`.

Reference:

- `design/16_ONE_REAL_AUTOMATED_PAPER_SEND.md`

## 10. Phase 49 Implementation Result

Phase 49 One Real Automated Paper Send Implementation result: `PASS`.

Implementation references:

- `runtime/one_real_automated_paper_send.py`
- `tests/test_one_real_automated_paper_send.py`

## 11. One Real Automated Paper Send Run Result

One Real Automated Paper Send Run result: `PASS`.

Known run values:

- Test status: `PASS`, 684 tests.
- Architecture validation: `PASS`.
- V10 full pipeline dry-run regression: `PASS`.
- Automated paper send mocked regression: `PASS`.
- Strategy evaluation: `PASS`.
- Evaluation-First Gate: `EVALUATION_GATE_PASSED`.
- Negative Case Regression: `PASS`.
- Candidate status: `PAPER_ORDER_CANDIDATE_CREATED`.
- Human Review status: `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST`.
- Finalized Paper Order Request status: `PAPER_ORDER_REQUEST_FINALIZED`.
- Manual Execution Confirmation status: `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`.
- Paper Send Preflight status: `PAPER_ORDER_SEND_ALLOWED`.
- Paper send status: `ONE_REAL_AUTOMATED_PAPER_SEND_SUBMITTED`.
- Alpaca paper order id: `d98b6356-9305-46d1-b73a-a312190c12cd`.
- Reconciliation status: `RECONCILIATION_MATCHED`.
- Secrets printed: no.
- System returned to `DRY_RUN_ONLY`: confirmed.
- `PAPER_ORDER_EXECUTION_ENABLED` disabled/false after run: confirmed.
- `PAPER_AUTOMATED_SEND_ENABLED` disabled/false after run: confirmed.

## 12. What V13 Proves

V13 proves:

- The system can perform one real automated Alpaca paper send.
- The automated send can occur only after V4-V13 gates pass.
- The automated send can submit one Alpaca paper order and then stop.
- The run can record the Alpaca paper order id.
- Reconciliation can complete with `RECONCILIATION_MATCHED`.
- Post-send safety can confirm the system returned to `DRY_RUN_ONLY`.
- Secrets were not printed.
- Live trading remains unsupported.

V13 does not authorize repeated automated sends, general automated trading, live trading, increasing notional, batch orders, cancel/replace, or multi-symbol automation.

## 13. Full Automated Paper Send Pipeline Proof

The successful V13 run used this pipeline:

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
-> Automated Alpaca Paper Send
-> Reconciliation
-> Post-send safety
-> Post-mortem
```

Pipeline proof:

- Candidate status: `PAPER_ORDER_CANDIDATE_CREATED`.
- Human Review status: `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST`.
- Finalized Paper Order Request status: `PAPER_ORDER_REQUEST_FINALIZED`.
- Manual Execution Confirmation status: `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`.
- Paper Send Preflight status: `PAPER_ORDER_SEND_ALLOWED`.
- Paper send status: `ONE_REAL_AUTOMATED_PAPER_SEND_SUBMITTED`.
- Reconciliation status: `RECONCILIATION_MATCHED`.

No stage may be skipped in future controlled sends.

## 14. Automation Safety Controls Proven

Automation safety controls proven:

- Automation kill switch status: inactive.
- Daily order limit status: not exceeded.
- Daily notional limit status: not exceeded.
- Cooldown status: satisfied.
- Previous reconciliation status: exists and matched.
- Previous post-mortem status: exists with no blockers.
- Unresolved issue status: none.
- Paper-only send path used.
- Live trading remains unsupported.
- Secrets printed: no.
- System returned to `DRY_RUN_ONLY`: confirmed.
- `PAPER_ORDER_EXECUTION_ENABLED` disabled/false after run: confirmed.
- `PAPER_AUTOMATED_SEND_ENABLED` disabled/false after run: confirmed.

## 15. Controlled Send Result

Controlled automated paper send result:

- Paper send status: `ONE_REAL_AUTOMATED_PAPER_SEND_SUBMITTED`.
- One controlled automated paper send only: confirmed.
- No repeated automated send authority: confirmed.
- No scheduled automated trading authority: confirmed.
- No batch orders: confirmed.
- No cancel/replace: confirmed.
- No multi-symbol automation: confirmed.
- No live trading: confirmed.

## 16. Alpaca Paper Order ID

Alpaca paper order id:

```text
d98b6356-9305-46d1-b73a-a312190c12cd
```

This is a paper order id only. It is not live trading evidence and does not authorize future automated sends.

## 17. Reconciliation Result

Reconciliation result: `RECONCILIATION_MATCHED`.

Reconciliation confirmed:

- Broker paper order id was recorded.
- No extra orders were created.
- No batch orders were created.
- No cancel/replace occurred.
- Live trading remains unsupported.

## 18. Artifact References

One real automated paper send artifact references:

- One-real automated paper send report: `reports/one_real_automated_paper_send/20260520T134219Z/ONE_REAL_AUTOMATED_PAPER_SEND_REPORT.md`
- Automation audit log: `reports/one_real_automated_paper_send/20260520T134219Z/AUTOMATION_AUDIT_LOG.md`
- Reconciliation: `reports/one_real_automated_paper_send/20260520T134219Z/RECONCILIATION.md`
- Post-send safety: `reports/one_real_automated_paper_send/20260520T134219Z/POST_SEND_SAFETY.md`
- Post-mortem: `reports/one_real_automated_paper_send/20260520T134219Z/POST_MORTEM.md`

## 19. Confirmed Safety Controls

Confirmed safety controls after V13:

- `PAPER_ORDER_EXECUTION_ENABLED` must remain disabled by default.
- `PAPER_AUTOMATED_SEND_ENABLED` must remain disabled by default.
- Future automated paper sends require explicit enablement and all V13 gates.
- System returned to `DRY_RUN_ONLY`: confirmed.
- Secrets printed: no.
- Paper trading only.
- One controlled automated paper send only.
- Reconciliation required.
- Post-send safety required.
- Post-mortem required.
- Increasing notional remains prohibited.
- Batch orders remain prohibited.
- Cancel/replace remains prohibited.
- Multi-symbol automation remains prohibited.
- Live trading remains unsupported.

## 20. What Is Allowed After V13

Allowed after V13:

- Continue automated dry-run analysis.
- Continue candidate creation.
- Continue human review queue.
- Continue finalized paper order requests.
- Continue manual execution confirmation.
- Continue paper send preflight.
- Continue controlled manual V10/V12 paper sends under all gates.
- Design automated paper send soak testing.
- Continue offline quality review.
- Continue negative-case expansion.
- Continue improving rejection and no-trade quality.

## 21. What Remains Prohibited

Still prohibited after V13:

- Repeated automated paper sends.
- Scheduled automated paper trading.
- Live trading.
- Increasing notional.
- Batch orders.
- Cancel/replace.
- Multi-symbol automation.
- Higher frequency.
- Removing human review.
- Removing manual execution confirmation.
- Bypassing V4-V13 gates.
- Leaving `PAPER_ORDER_EXECUTION_ENABLED` enabled by default.
- Leaving `PAPER_AUTOMATED_SEND_ENABLED` enabled by default.

## 22. Conditions Before Another Automated Paper Send

Before another automated paper send:

- Baseline V13 must remain `PASS`.
- Full tests must be `PASS`.
- Architecture validation must be `PASS`.
- V10 full pipeline dry-run regression must be `PASS`.
- Automated paper send mocked regression must be `PASS`.
- Strategy Evaluation must be `PASS`.
- Evaluation-First Gate must be `EVALUATION_GATE_PASSED`.
- Negative Case Regression must be `PASS`.
- Candidate must be `PAPER_ORDER_CANDIDATE_CREATED`.
- Human Review must be `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST`.
- Finalized Paper Order Request must be `PAPER_ORDER_REQUEST_FINALIZED`.
- Manual Execution Confirmation must be `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`.
- Paper Send Preflight must be `PAPER_ORDER_SEND_ALLOWED`.
- Automation kill switch must be inactive.
- Daily order limit must not be exceeded.
- Daily notional limit must not be exceeded.
- Cooldown must be satisfied.
- Previous reconciliation must exist and match.
- Previous post-mortem must exist with no blockers.
- No unresolved issue may exist.
- `PAPER_ORDER_EXECUTION_ENABLED` may be enabled only for the explicit approved run.
- `PAPER_AUTOMATED_SEND_ENABLED` may be enabled only for the explicit approved run.
- Both automation flags must be disabled or unset after the run.
- Reconciliation, post-send safety, and post-mortem artifacts must be created.
- No batch orders.
- No cancel/replace.
- No multi-symbol automation.
- No live trading.

## 23. Conditions Before Repeated Automated Paper Sends

Before repeated automated paper sends:

- Future repeated automation requires separate soak testing design, implementation, and audit.
- A soak test design must define frequency, limits, stop conditions, and failure modes.
- A soak test implementation must prove the controls without live trading authority.
- A mocked regression must cover repeated-send rejection and cooldown behavior.
- Audit artifacts must prove no extra orders, no batch behavior, no cancel/replace, and no bypass of V4-V13 gates.
- Weekly Review and Failure Auditor findings must support any expanded autonomy boundary.
- Human accountability boundaries must be explicitly reapproved.

Repeated automated paper sends remain prohibited after V13.

## 24. Conditions Before Increasing Notional

Before increasing notional:

- The current notional limit must remain enforced until a future baseline explicitly changes it.
- Controlled paper send history must demonstrate process quality, not profit chasing.
- Reconciliation and post-send safety must remain clean across multiple controlled sends.
- Weekly Review and Failure Auditor findings must support any change.
- Risk Manager limits must be redesigned and revalidated.
- Evaluation metrics must prove selectivity and drawdown control.
- Human approval must explicitly authorize any proposed notional increase.

Increasing notional remains prohibited after V13.

## 25. Conditions Before Multi-Symbol Automation

Before multi-symbol automation:

- One-symbol controlled send behavior must remain stable.
- Symbol selection governance must be designed.
- Data Integrity checks must be expanded for multiple symbols.
- Risk aggregation must be designed and validated.
- Batch behavior must remain blocked unless separately authorized by a future baseline.
- Multi-symbol failure modes must be documented.
- A separate multi-symbol dry-run regression must pass.
- Controlled send behavior must not be generalized into automated multi-symbol execution without explicit future authorization.

Multi-symbol automation remains prohibited after V13.

## 26. Conditions Before Live Trading

Before live trading:

- A future architecture phase must explicitly change the project scope.
- Human accountability, legal, operational, and financial risk controls must be redesigned.
- Live broker endpoint handling must be separately designed and reviewed.
- Live trading failure modes must be documented and audited.
- Evaluation metrics must prove capital preservation and process quality across sufficient paper history.
- Separate implementation, regression, reconciliation, post-send safety, and post-mortem controls must pass.
- Explicit human approval must authorize the scope change.

Live trading remains unsupported after V13.

## 27. Live Trading Statement

Live trading remains unsupported.

V13 does not authorize repeated automated sends.
V13 does not authorize general automated trading.
V13 does not authorize live trading.
V13 does not authorize increasing notional.
V13 does not authorize batch orders.
V13 does not authorize cancel/replace.
V13 does not authorize multi-symbol automation.

`PAPER_ORDER_EXECUTION_ENABLED` must remain disabled by default.
`PAPER_AUTOMATED_SEND_ENABLED` must remain disabled by default.

Future automated paper sends require explicit enablement and all V13 gates.
Future repeated automation requires separate soak testing design, implementation, and audit.
