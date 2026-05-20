# Operating Policy After V12

## 1. Current Operating Baseline

V12 is the current operating baseline.

Baseline V12 is `PASS`.

V12 means the complete V10 pipeline produced one successful controlled Alpaca paper send with reconciliation matched.

The V12-proven pipeline is:

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

## 2. What V12 Proves

V12 proves:

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
- Alpaca paper order id: `30ad9c46-cba2-4d0b-9a82-4bc918def1f4`.
- Reconciliation status: `RECONCILIATION_MATCHED`.
- System returned to `DRY_RUN_ONLY`: confirmed.
- Secrets printed: no.

V12 does not prove or authorize automated Paper Send, live trading, live endpoints, increasing notional, batch orders, cancel/replace, multi-symbol automation, higher frequency, or bypassing any V12 gate.

## 3. Default Operating Mode

`DRY_RUN_ONLY` is the default mode.

`PAPER_ORDER_EXECUTION_ENABLED` must remain disabled by default.

`PAPER_ORDER_EXECUTION_ENABLED` may be enabled only for one explicit manual controlled paper send.

`PAPER_ORDER_EXECUTION_ENABLED` must be unset immediately after any manual send.

Every paper send must return the system to `DRY_RUN_ONLY`.

## 4. Allowed Operations After V12

Allowed after V12:

- Automated dry-run analysis.
- Paper Order Request Candidate creation.
- Human Review Queue.
- Finalized Paper Order Request creation.
- Manual Execution Confirmation.
- Paper Send Preflight.
- Controlled manual V10 paper sends under all V12 gates.
- Offline quality review.
- Negative-case expansion.
- Rejection quality improvement.
- `NO_TRADE` discipline improvement.
- Journal quality improvement.

## 5. Prohibited Operations After V12

Still prohibited after V12:

- Automated Paper Send.
- Live trading.
- Live endpoints.
- Increasing notional.
- Batch orders.
- Cancel/replace.
- Multi-symbol automation.
- Higher frequency.
- Bypassing Strategy Evaluation Harness.
- Bypassing Evaluation-First Gate.
- Bypassing Negative Case Regression.
- Bypassing Human Review.
- Bypassing Manual Execution Confirmation.
- Bypassing Paper Send Preflight.
- Leaving `PAPER_ORDER_EXECUTION_ENABLED` enabled.

## 6. Required Gates Before Any Controlled Paper Send

Before any controlled paper send, all gates must pass:

- Full tests `PASS`.
- Architecture validation `PASS`.
- V10 full pipeline dry-run regression `PASS`.
- Strategy Evaluation `PASS`.
- Evaluation-First Gate `PASS`.
- Negative Case Regression `PASS`.
- Candidate created from valid `TRADE_PROPOSAL`.
- Human Review approved.
- Finalized Paper Order Request exists.
- Manual Execution Confirmation exists.
- Paper Send Preflight `PAPER_ORDER_SEND_ALLOWED`.
- Alpaca paper account confirmed.
- Live endpoint rejected.
- `PAPER_ORDER_EXECUTION_ENABLED=true` only for that manual run.

If any gate is missing, failed, stale, or ambiguous, the controlled paper send is blocked.

## 7. Required Environment Handling

Environment handling rules:

- `.env.local` is local only and must never be committed.
- Do not create new `.env` files.
- Secrets must never be printed, logged, committed, or written to reports.
- Environment checks may confirm only whether required variables are present.
- `PAPER_ORDER_EXECUTION_ENABLED` must remain disabled by default.
- `PAPER_ORDER_EXECUTION_ENABLED=true` is allowed only during one explicit manual controlled paper send.
- `PAPER_ORDER_EXECUTION_ENABLED` must be unset immediately after any manual send.
- `ALPACA_PAPER=true` is required for any controlled paper send.
- Live endpoint configuration must be rejected.

## 8. Required Artifact Handling

Every controlled paper send must create artifacts under a timestamped directory.

Required artifacts:

- Controlled paper send report.
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
- Confirmation that live trading remains unsupported.

Artifacts must not contain secrets.

## 9. Required Post-Send Behavior

After every controlled paper send attempt:

- Run reconciliation.
- Create post-mortem.
- Create post-send safety artifact.
- Return system to `DRY_RUN_ONLY`.
- Unset `PAPER_ORDER_EXECUTION_ENABLED`.
- Confirm no live endpoint was used.
- Confirm no batch orders were created.
- Confirm no cancel/replace occurred.
- Confirm no extra orders were created.
- Confirm live trading remains unsupported.

## 10. Required Review Behavior

Every controlled paper send must be reviewed after the run.

Review must inspect:

- Controlled send report.
- Reconciliation artifact.
- Post-send safety artifact.
- Post-mortem.
- Whether all V12 gates were present and passed.
- Whether the send was one order only.
- Whether notional remained `<= 100 USD`.
- Whether order type remained limit.
- Whether time in force remained day.
- Whether any unexpected behavior occurred.
- Whether future sends should remain blocked, remain manual, or require redesign.

No future send may rely on a previous send's approval.

## 11. Conditions Before Another Controlled V10 Paper Send

Before another controlled V10 paper send:

- Baseline V12 must remain `PASS`.
- Full tests must be `PASS`.
- Architecture validation must be `PASS`.
- V10 full pipeline dry-run regression must be `PASS`.
- Strategy Evaluation must be `PASS`.
- Evaluation-First Gate must be `PASS`.
- Negative Case Regression must be `PASS`.
- Candidate must be created from valid `TRADE_PROPOSAL`.
- Human Review must be approved.
- Finalized Paper Order Request must exist.
- Manual Execution Confirmation must exist.
- Paper Send Preflight must be `PAPER_ORDER_SEND_ALLOWED`.
- Alpaca paper account must be confirmed.
- Live endpoint must be rejected.
- `PAPER_ORDER_EXECUTION_ENABLED=true` may be set only for that manual run.
- `PAPER_ORDER_EXECUTION_ENABLED` must be unset immediately after the run.
- Reconciliation must be ready.
- Post-mortem must be ready.
- Post-send safety artifact must be ready.

Future paper sends remain max notional `<= 100 USD`.
Future paper sends remain one order only.
Future paper sends remain limit order only.
Future paper sends remain day time-in-force only.

## 12. Conditions Before Automated Paper Send

Before automated Paper Send can be considered:

- Multiple controlled manual V10 paper sends must be completed and reviewed.
- Reconciliation must be consistently matched.
- Post-send safety must remain clean.
- Failure modes must be audited and documented.
- Human accountability boundaries must be redesigned.
- Risk controls must be expanded and revalidated.
- Automated Paper Send design must be separately approved.
- Automated Paper Send regression must prove no bypass of V4-V12 gates.
- Explicit change control must authorize the new autonomy boundary.

Automated Paper Send remains prohibited after V12.

## 13. Conditions Before Increasing Notional

Before increasing notional:

- The `<= 100 USD` notional limit must remain enforced until a future baseline explicitly changes it.
- Controlled paper send history must demonstrate process quality, not profit chasing.
- Reconciliation and post-send safety must remain clean across multiple controlled sends.
- Weekly Review and Failure Auditor findings must support any change.
- Risk Manager limits must be redesigned and revalidated.
- Evaluation metrics must prove selectivity and drawdown control.
- Human approval must explicitly authorize any proposed notional increase.

Increasing notional remains prohibited after V12.

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

Multi-symbol automation remains prohibited after V12.

## 15. Emergency Stop Procedure

Emergency stop procedure:

1. Run `unset PAPER_ORDER_EXECUTION_ENABLED`.
2. Return system to `DRY_RUN_ONLY`.
3. Stop all send attempts.
4. Run architecture validation.
5. Run full tests.
6. Inspect latest artifacts.
7. Do not resume until post-mortem is complete.

If any safety state is unclear, default action is no send.

## 16. Live Trading Statement

Live trading remains unsupported.

V12 is paper trading only. It does not authorize live trading, live endpoints, automated Paper Send, increasing notional, batch orders, cancel/replace, multi-symbol automation, higher frequency, or bypassing V4-V12 gates.
