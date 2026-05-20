# Phase 11 Repeatability Validation Plan

## 1. Purpose

Phase 11 validates that the Baseline Safe Paper Execution V1 process is repeatable across 2-3 additional controlled Alpaca paper sends without weakening safety controls.

This phase is manual only. It does not add automation, new order behavior, larger order size, live trading, cancel/replace, or batch orders.

## 2. Entry Criteria

- Baseline Safe Paper Execution V1 is documented and reviewed.
- First controlled paper send post-mortem is complete.
- System default is `DRY_RUN_ONLY`.
- `PAPER_ORDER_EXECUTION_ENABLED` is unset or false before the manual send window.
- `.env.local`, if used, remains local only and is not committed.
- No unresolved safety issue exists from the previous run.

## 3. Per-Run Checklist

Complete this checklist separately for each of the 2-3 repeatability runs.

- Confirm this is manual only.
- Confirm this is paper trading only.
- Confirm live trading remains unsupported.
- Confirm Alpaca paper account.
- Confirm live endpoint is rejected.
- Confirm max notional is `<= 100 USD`.
- Confirm order type is limit.
- Confirm time in force is day.
- Confirm one order maximum for this run.
- Confirm no batch orders.
- Confirm no automation.
- Confirm no short selling.
- Confirm no crypto.
- Confirm no options.
- Confirm no margin/leverage.
- Confirm no extended hours.
- Confirm no cancel/replace.
- Run full tests before send.
- Run architecture validation before send.
- Run dry-run flow before send.
- Run mocked paper send before send.
- Confirm proposal validation passed.
- Confirm Risk Manager output is `RISK_APPROVED`.
- Confirm human approval is `HUMAN_APPROVED_FOR_PAPER_ONLY`.
- Confirm manual execution confirmation is `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY`.
- Confirm journal commit exists before send.
- Confirm preflight status is `PAPER_ORDER_SEND_ALLOWED`.
- Enable `PAPER_ORDER_EXECUTION_ENABLED=true` only for the manual send window.
- Use execution mode `REAL_ALPACA_PAPER_SEND` only for the manual send.

## 4. Post-Run Checklist

Complete this checklist after each repeatability run.

- Confirm execution result was recorded.
- Confirm Alpaca paper order id if returned.
- Confirm post-send journal entry exists.
- Run reconciliation after send.
- Confirm reconciliation status.
- Confirm mismatches, if any, are documented.
- Confirm no follow-up order was created.
- Confirm no cancel/replace happened.
- Confirm live trading was not touched.
- Confirm post-send safety artifact exists.
- Generate the first controlled paper send style report for the run.
- Create a post-mortem for the run.
- Unset `PAPER_ORDER_EXECUTION_ENABLED` after the send.
- Return system to `DRY_RUN_ONLY` after the send.
- Review the run before considering the next repeatability run.

## 5. Failure Conditions

Any of the following is a failed run:

- Full tests fail.
- Architecture validation fails.
- Dry run fails.
- Mocked send fails.
- Proposal validation is not `PASS`.
- Risk Manager output is not `RISK_APPROVED`.
- Human approval is not `HUMAN_APPROVED_FOR_PAPER_ONLY`.
- Manual execution confirmation is not `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY`.
- Journal commit is missing before send.
- Preflight is not `PAPER_ORDER_SEND_ALLOWED`.
- Account mode is not paper.
- Live endpoint is not rejected.
- Notional exceeds `100 USD`.
- Order is not limit/day.
- Reconciliation is `RECONCILIATION_MISMATCH`, `RECONCILIATION_ORDER_NOT_FOUND`, `RECONCILIATION_READ_ERROR`, or `RECONCILIATION_BLOCKED`.
- Post-send journal entry is missing.
- Post-mortem is missing.
- `PAPER_ORDER_EXECUTION_ENABLED` remains enabled after the send.
- System does not return to `DRY_RUN_ONLY`.

## 6. Stop Conditions

Stop Phase 11 immediately if any failure condition occurs.

Also stop if:

- A live endpoint is observed.
- Any live trading behavior appears.
- More than one order is attempted in a run.
- Any batch order behavior appears.
- Any cancel/replace behavior appears.
- Any autonomous follow-up trade appears.
- Any credential or secret is printed, logged, committed, or written to a report.
- Any `.env` file with real values is created or tracked.

## 7. Success Criteria

Phase 11 succeeds only if 2-3 additional controlled paper sends complete with:

- Full tests passing before each send.
- Architecture validation passing before each send.
- Dry run passing before each send.
- Mocked paper send passing before each send.
- All required gates passing before each send.
- Each order submitted as paper-only, limit, day, max `100 USD`.
- Exactly one order attempted per run.
- Reconciliation matched for each run.
- Post-send journal entry exists for each run.
- Post-mortem exists for each run.
- No follow-up orders.
- No cancel/replace.
- No batch orders.
- No live trading.
- `PAPER_ORDER_EXECUTION_ENABLED` unset after each run.
- System returned to `DRY_RUN_ONLY` after each run.

## 8. What Remains Prohibited

- Live trading.
- Live Alpaca endpoints.
- Autonomous execution.
- Batch orders.
- Cancel/replace.
- Market orders.
- Short selling.
- Crypto.
- Options.
- Margin or leverage.
- Extended-hours trading.
- Increasing order size.
- Expanding instruments.
- Skipping human approval.
- Skipping manual execution confirmation.
- Skipping Risk Manager approval.
- Skipping journal commit.
- Skipping reconciliation.
- Committing credentials.
- Creating `.env` files with real values.

## 9. When To Proceed To The Next Phase

Proceed to the next phase only after:

- 2-3 repeatability runs meet all success criteria.
- Every run has a report and post-mortem.
- No unresolved safety issue remains.
- Governance documents are updated with lessons learned.
- A new phase plan explicitly defines any proposed scope increase.

Increasing size, automation, instruments, or execution autonomy requires a separate phase and audit. Phase 11 does not authorize those changes.

## 10. Live Trading Remains Unsupported

Live trading remains unsupported.

Phase 11 validates repeatable controlled paper execution only. It does not authorize live trading, live endpoints, automation, cancel/replace, batch orders, or increased order size.
