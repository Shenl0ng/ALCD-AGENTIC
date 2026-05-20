# Phase 46 Automated Paper Send Mocked Regression Plan

## Purpose

Define a mocked regression for automated paper send after Phase 45.

Phase 46 must prove that automated paper send works end-to-end with a mocked Alpaca client while still enforcing all safety gates, limits, kill switch, cooldown, reconciliation dependency, post-mortem dependency, and audit log requirements.

Phase 46 must not send real orders.

## Context

- Phase 45 Automated Paper Send Implementation: PASS
- Automated paper send remains disabled by default.
- `PAPER_AUTOMATED_SEND_ENABLED` must not be enabled for real use in this phase.
- `PAPER_ORDER_EXECUTION_ENABLED` must not be enabled for real use in this phase.
- Real Alpaca API must not be used in this phase.
- Live trading remains unsupported.

## Regression Scope

Allowed:

- Run automated paper send with a mocked Alpaca client only.
- Enable `PAPER_AUTOMATED_SEND_ENABLED=true` in test context only.
- Enable `PAPER_ORDER_EXECUTION_ENABLED=true` in test context only.
- Enable `ALPACA_PAPER=true` in test context only.
- Verify all V12 gates, automation limits, dependency checks, artifacts, and audit log behavior.
- Generate a timestamped mocked regression report.

Not allowed:

- Real Alpaca API calls.
- Real order submission.
- Live trading.
- Live endpoints.
- Increasing notional.
- Batch orders.
- Cancel/replace.
- Creating `.env` files.
- Printing secrets.

## Required Report Path

```text
reports/automated_paper_send_mocked_regression/<timestamp>/AUTOMATED_PAPER_SEND_MOCKED_REGRESSION_REPORT.md
```

## Required Scenarios

### 1. Full Valid Mocked Automated Paper Send

Expected:

- `PAPER_AUTOMATED_SEND_ENABLED=true` in test context only.
- `PAPER_ORDER_EXECUTION_ENABLED=true` in test context only.
- `ALPACA_PAPER=true` in test context only.
- All V12 gates PASS.
- Automation limits PASS.
- Kill switch inactive.
- Cooldown satisfied.
- Previous reconciliation exists and matched.
- Previous post-mortem exists with no blockers.
- No unresolved issue.
- Mocked Alpaca client receives exactly one paper limit/day order.
- Automated send status `AUTOMATED_PAPER_SEND_SUBMITTED`.
- Mocked reconciliation `RECONCILIATION_MATCHED`.
- Post-send safety artifact written.
- Post-mortem written.
- Automation audit log written.
- System returns to `DRY_RUN_ONLY`.
- Flags disabled/unset after test context.

### 2. Default Disabled Scenario

Expected:

- `PAPER_AUTOMATED_SEND_ENABLED=false` blocks send.
- No mocked order sent.

### 3. Execution Flag Disabled Scenario

Expected:

- `PAPER_ORDER_EXECUTION_ENABLED=false` blocks send.
- No mocked order sent.

### 4. Kill Switch Scenario

Expected:

- Kill switch active blocks send.
- Status `AUTOMATED_PAPER_SEND_REJECTED_BY_KILL_SWITCH`.

### 5. Daily Order Limit Scenario

Expected:

- Daily order limit exceeded blocks send.
- Status `AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS`.

### 6. Daily Notional Limit Scenario

Expected:

- Daily notional limit exceeded blocks send.
- Status `AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS`.

### 7. Cooldown Scenario

Expected:

- Cooldown not satisfied blocks send.
- Status `AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS`.

### 8. Missing Previous Reconciliation Scenario

Expected:

- Blocks send.
- Status `AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION`.

### 9. Unresolved Reconciliation Mismatch Scenario

Expected:

- Blocks send.
- Status `AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION`.

### 10. Missing Post-Mortem Scenario

Expected:

- Blocks send.
- Status `AUTOMATED_PAPER_SEND_REJECTED_BY_POST_MORTEM`.

### 11. Unresolved Issue Scenario

Expected:

- Blocks send.
- Status `AUTOMATED_PAPER_SEND_BLOCKED`.

### 12. Live Endpoint Scenario

Expected:

- Blocks send.
- No mocked order sent.

### 13. Notional Over 100 Scenario

Expected:

- Blocks send.
- No mocked order sent.

### 14. Batch/Cancel/Replace Scenario

Expected:

- Blocks send.
- No mocked order sent.

## Required Report Contents

The mocked regression report must include:

- Scenarios run.
- Scenario results.
- Mocked order count.
- Gate results.
- Limit results.
- Kill switch results.
- Cooldown results.
- Reconciliation dependency results.
- Post-mortem dependency results.
- Audit log results.
- Proof no real Alpaca API was called.
- Proof no real order was sent.
- Proof system returned to `DRY_RUN_ONLY`.
- Proof flags were disabled/unset after test context.
- Statement: Automated paper send remains paper-only.
- Statement: Live trading remains unsupported.
- Statement: Increasing notional remains prohibited.
- Statement: Batch orders remain prohibited.
- Statement: Cancel/replace remains prohibited.

## Success Criteria

- All scenarios produce expected results.
- Full valid mocked scenario submits exactly one mocked paper limit/day order.
- All blocked scenarios send zero mocked orders.
- No real Alpaca API is called.
- No real order is sent.
- System returns to `DRY_RUN_ONLY`.
- Flags are disabled/unset after test context.

## Safety Requirements

- `PAPER_AUTOMATED_SEND_ENABLED=true` is permitted only inside mocked test context.
- `PAPER_ORDER_EXECUTION_ENABLED=true` is permitted only inside mocked test context.
- `ALPACA_PAPER=true` is permitted only inside mocked test context.
- Real Alpaca API must not be called.
- Real order submission must not occur.
- Secrets must not be printed, logged, committed, or written to reports.
- Live endpoints must remain blocked.
- Live trading remains unsupported.
- Increasing notional remains prohibited.
- Batch orders remain prohibited.
- Cancel/replace remains prohibited.
