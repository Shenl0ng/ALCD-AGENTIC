# Operating Policy After V13

## 1. Current Operating Baseline

V13 is the current operating baseline.

Baseline V13 is `PASS`.

V13 means one real automated Alpaca paper send completed successfully after all V12/V13 gates passed, reconciliation matched, and the system returned to `DRY_RUN_ONLY`.

The V13-proven pipeline is:

```text
Automated dry-run analysis
-> Strategy Evaluation Harness
-> Evaluation-First Gate
-> Negative Case Regression
-> Paper Order Request Candidate
-> Human Review Queue
-> Finalized Paper Order Request
-> Manual Execution Confirmation
-> Paper Send Preflight
-> One Real Automated Alpaca Paper Send
-> Reconciliation
-> Post-send safety
-> Post-mortem
```

## 2. What V13 Proves

V13 proves:

- One real automated Alpaca paper send completed successfully.
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
- Kill switch: inactive.
- Daily order limit: not exceeded.
- Daily notional limit: not exceeded.
- Cooldown: satisfied.
- Previous reconciliation: exists and matched.
- Previous post-mortem: exists with no blockers.
- Unresolved issue status: none.
- Paper send status: `ONE_REAL_AUTOMATED_PAPER_SEND_SUBMITTED`.
- Alpaca paper order id: `d98b6356-9305-46d1-b73a-a312190c12cd`.
- Reconciliation status: `RECONCILIATION_MATCHED`.
- System returned to `DRY_RUN_ONLY`: confirmed.
- `PAPER_ORDER_EXECUTION_ENABLED` was disabled/false after run.
- `PAPER_AUTOMATED_SEND_ENABLED` was disabled/false after run.
- Secrets printed: no.

V13 does not prove or authorize repeated automated paper sends, scheduled automated paper trading, live trading, live endpoints, increasing notional, batch orders, cancel/replace, multi-symbol automation, higher frequency, or bypassing any V13 gate.

## 3. Default Operating Mode

`DRY_RUN_ONLY` is the default mode.

`PAPER_ORDER_EXECUTION_ENABLED` must remain disabled by default.

`PAPER_AUTOMATED_SEND_ENABLED` must remain disabled by default.

A future automated paper send requires explicit enablement of both flags for that run only.

Both flags must be disabled or unset immediately after any run.

Every paper send must return the system to `DRY_RUN_ONLY`.

## 4. Allowed Operations After V13

Allowed after V13:

- Automated dry-run analysis.
- Candidate creation.
- Human Review Queue.
- Finalized Paper Order Request.
- Manual Execution Confirmation.
- Paper Send Preflight.
- One-off automated paper sends only under all V13 gates.
- Automated paper send soak testing design.
- Offline quality review.
- Negative-case expansion.
- Rejection quality improvement.
- `NO_TRADE` discipline improvement.
- Journal quality improvement.

## 5. Prohibited Operations After V13

Still prohibited after V13:

- Repeated automated paper sends without soak testing design and audit.
- Scheduled automated paper trading.
- Live trading.
- Live endpoints.
- Increasing notional.
- Batch orders.
- Cancel/replace.
- Multi-symbol automation.
- Higher frequency.
- Removing Human Review.
- Removing Manual Execution Confirmation.
- Bypassing Strategy Evaluation Harness.
- Bypassing Evaluation-First Gate.
- Bypassing Negative Case Regression.
- Bypassing Paper Send Preflight.
- Leaving `PAPER_ORDER_EXECUTION_ENABLED` enabled.
- Leaving `PAPER_AUTOMATED_SEND_ENABLED` enabled.

## 6. Required Gates Before Any Future Automated Paper Send

Before any future automated paper send, all V13 gates must pass:

- Baseline V13 remains `PASS`.
- Full tests `PASS`.
- Architecture validation `PASS`.
- V10 full pipeline dry-run regression `PASS`.
- Automated paper send mocked regression `PASS`.
- Strategy Evaluation `PASS`.
- Evaluation-First Gate `EVALUATION_GATE_PASSED`.
- Negative Case Regression `PASS`.
- Candidate status `PAPER_ORDER_CANDIDATE_CREATED`.
- Human Review status `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST`.
- Finalized Paper Order Request status `PAPER_ORDER_REQUEST_FINALIZED`.
- Manual Execution Confirmation status `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`.
- Paper Send Preflight status `PAPER_ORDER_SEND_ALLOWED`.
- Kill switch inactive.
- Daily order limit not exceeded.
- Daily notional limit not exceeded.
- Cooldown satisfied.
- Previous reconciliation exists and matched.
- Previous post-mortem exists with no blockers.
- Unresolved issue status none.
- Alpaca paper account confirmed.
- Live endpoint rejected.

If any gate is missing, failed, stale, or ambiguous, the automated paper send is blocked.

## 7. Required Environment Handling

Environment handling rules:

- `.env.local` is local only and must never be committed.
- Do not create new `.env` files.
- Secrets must never be printed, logged, committed, or written to reports.
- Environment checks may confirm only whether required variables are present.
- `PAPER_ORDER_EXECUTION_ENABLED` must remain disabled by default.
- `PAPER_AUTOMATED_SEND_ENABLED` must remain disabled by default.
- `PAPER_ORDER_EXECUTION_ENABLED=true` is allowed only during one explicit approved automated paper send run.
- `PAPER_AUTOMATED_SEND_ENABLED=true` is allowed only during one explicit approved automated paper send run.
- Both flags must be disabled or unset immediately after any run.
- `ALPACA_PAPER=true` is required for any approved paper send.
- Live endpoint configuration must be rejected.

## 8. Required Artifact Handling

Every paper send must create artifacts under a timestamped directory.

Required artifacts:

- One-real automated paper send report.
- Automation audit log.
- Reconciliation artifact.
- Post-send safety artifact.
- Post-mortem.

Artifacts must include:

- Gate statuses.
- Paper send status.
- Alpaca paper order id if returned.
- Reconciliation status.
- Post-send safety status.
- Explicit block reason if blocked.
- Confirmation that secrets were not printed.
- Confirmation that `PAPER_ORDER_EXECUTION_ENABLED` was disabled or unset after the run.
- Confirmation that `PAPER_AUTOMATED_SEND_ENABLED` was disabled or unset after the run.
- Confirmation that the system returned to `DRY_RUN_ONLY`.
- Confirmation that live trading remains unsupported.

Artifacts must not contain secrets.

## 9. Required Post-Send Behavior

After every paper send attempt:

- Run reconciliation.
- Create post-mortem.
- Create post-send safety artifact.
- Create automation audit log.
- Return system to `DRY_RUN_ONLY`.
- Unset or disable `PAPER_ORDER_EXECUTION_ENABLED`.
- Unset or disable `PAPER_AUTOMATED_SEND_ENABLED`.
- Confirm no live endpoint was used.
- Confirm no batch orders were created.
- Confirm no cancel/replace occurred.
- Confirm no extra orders were created.
- Confirm live trading remains unsupported.

## 10. Required Review Behavior

Every paper send must be reviewed after the run.

Review must inspect:

- One-real automated paper send report.
- Automation audit log.
- Reconciliation artifact.
- Post-send safety artifact.
- Post-mortem.
- Whether all V13 gates were present and passed.
- Whether the send was one order only.
- Whether notional remained `<= 100 USD`.
- Whether one symbol only was used.
- Whether order type remained limit.
- Whether time in force remained day.
- Whether both automation flags were disabled or unset after the run.
- Whether any unexpected behavior occurred.
- Whether future sends should remain blocked, remain one-off only, or require redesign.

No future send may rely on a previous send's approval.

## 11. Conditions Before Another One-Off Automated Paper Send

Before another one-off automated paper send:

- Baseline V13 must remain `PASS`.
- All V13 gates must pass.
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
- Kill switch must be inactive.
- Daily order limit must not be exceeded.
- Daily notional limit must not be exceeded.
- Cooldown must be satisfied.
- Previous reconciliation must exist and match.
- Previous post-mortem must exist with no blockers.
- No unresolved issue may exist.
- `PAPER_ORDER_EXECUTION_ENABLED=true` may be set only for that approved run.
- `PAPER_AUTOMATED_SEND_ENABLED=true` may be set only for that approved run.
- Both flags must be disabled or unset immediately after the run.
- Reconciliation must be ready.
- Post-send safety artifact must be ready.
- Post-mortem must be ready.

Future automated paper sends remain max notional `<= 100 USD`.
Future automated paper sends remain one symbol only.
Future automated paper sends remain one order only.
Future automated paper sends remain limit order only.
Future automated paper sends remain day time-in-force only.

## 12. Conditions Before Repeated Automated Paper Sends

Before repeated automated paper sends:

- A separate soak testing design must be approved.
- A separate soak testing implementation must be completed.
- A separate soak testing audit must pass.
- Repeated-send frequency, limits, stop conditions, and failure modes must be documented.
- Mocked regression must prove repeated-send rejection, cooldown behavior, and limit enforcement.
- Audit artifacts must prove no extra orders, no batch behavior, no cancel/replace, and no bypass of V4-V13 gates.
- Weekly Review and Failure Auditor findings must support the expanded autonomy boundary.
- Human accountability boundaries must be explicitly reapproved.

Repeated automated paper sends remain prohibited after V13 until those conditions are met.

## 13. Conditions Before Increasing Notional

Before increasing notional:

- The `<= 100 USD` notional limit must remain enforced until a future baseline explicitly changes it.
- Controlled paper send history must demonstrate process quality, not profit chasing.
- Reconciliation and post-send safety must remain clean across multiple controlled sends.
- Weekly Review and Failure Auditor findings must support any change.
- Risk Manager limits must be redesigned and revalidated.
- Evaluation metrics must prove selectivity and drawdown control.
- Human approval must explicitly authorize any proposed notional increase.

Increasing notional remains prohibited after V13.

## 14. Conditions Before Multi-Symbol Automation

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

## 15. Conditions Before Live Trading

Before live trading:

- A future architecture phase must explicitly change the project scope.
- Human accountability, legal, operational, and financial risk controls must be redesigned.
- Live broker endpoint handling must be separately designed and reviewed.
- Live trading failure modes must be documented and audited.
- Evaluation metrics must prove capital preservation and process quality across sufficient paper history.
- Separate implementation, regression, reconciliation, post-send safety, and post-mortem controls must pass.
- Explicit human approval must authorize the scope change.

Live trading remains unsupported after V13.

## 16. Emergency Stop Procedure

Emergency stop procedure:

1. Run `unset PAPER_ORDER_EXECUTION_ENABLED`.
2. Run `unset PAPER_AUTOMATED_SEND_ENABLED`.
3. Return system to `DRY_RUN_ONLY`.
4. Stop all send attempts.
5. Run architecture validation.
6. Run full tests.
7. Inspect latest artifacts.
8. Complete post-mortem before resuming.

If any safety state is unclear, default action is no send.

## 17. Live Trading Statement

Live trading remains unsupported.

V13 is paper trading only. It does not authorize repeated automated paper sends, scheduled automated paper trading, live trading, live endpoints, increasing notional, batch orders, cancel/replace, multi-symbol automation, higher frequency, removing Human Review, removing Manual Execution Confirmation, or bypassing any V13 gate.
