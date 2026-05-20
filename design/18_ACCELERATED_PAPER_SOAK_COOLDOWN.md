# Phase 53 Accelerated Paper Soak Cooldown Design

## 1. Purpose

Design an explicit accelerated cooldown mode for paper-only soak testing.

This phase is design only.

This design preserves the production/default 24-hour cooldown.
This design does not authorize live trading.
This design does not authorize increasing notional.
This design does not authorize multi-symbol automation.
This design does not authorize batch orders.
This design does not authorize cancel/replace.
This design does not remove Human Review.
This design does not remove Manual Execution Confirmation.

## 2. Context

- Baseline V13: `PASS`.
- Operating Policy After V13: `PASS`.
- Phase 50 Automated Paper Send Soak Testing Design: `PASS`.
- Phase 51 Automated Paper Send Soak Testing Implementation: `PASS`.
- Phase 52 Automated Paper Send Soak Test Run Plan: `PASS`.
- Soak Run 1 cooldown block report: `PASS`.

V13 proves one real automated Alpaca paper send completed successfully with reconciliation matched.

Soak Run 1 proved the 24-hour cooldown blocks correctly before send.

## 3. Problem

The production soak cooldown is 24 hours. This is correct for operational safety, but too slow for development validation of the soak framework.

Development needs a shorter paper-only cooldown mode that can validate soak mechanics without weakening production defaults or expanding trading authority.

## 4. Required Default Behavior

Default behavior:

- Production/default cooldown remains 24 hours.
- Accelerated cooldown is disabled by default.
- `DRY_RUN_ONLY` remains default.
- `PAPER_ORDER_EXECUTION_ENABLED=false` by default.
- `PAPER_AUTOMATED_SEND_ENABLED=false` by default.
- `PAPER_SOAK_TEST_ACCELERATED=false` by default.

No accelerated behavior may occur unless the accelerated test mode is explicitly enabled and all required accelerated-mode checks pass.

## 5. Required Accelerated Cooldown Flags

Required accelerated cooldown flags:

- `PAPER_SOAK_TEST_ACCELERATED=true`
- `PAPER_SOAK_TEST_COOLDOWN_SECONDS` configured
- `ALPACA_PAPER=true`
- `PAPER_ORDER_EXECUTION_ENABLED=true` only for run
- `PAPER_AUTOMATED_SEND_ENABLED=true` only for run

`PAPER_ORDER_EXECUTION_ENABLED` and `PAPER_AUTOMATED_SEND_ENABLED` must be disabled or unset immediately after the individual run.

## 6. Allowed Accelerated Cooldown Range

Allowed accelerated cooldown range:

- Minimum: 60 seconds.
- Maximum: 23 hours 59 minutes 59 seconds.
- Default test value: 60 seconds.

`PAPER_SOAK_TEST_COOLDOWN_SECONDS` must be an integer number of seconds.

Values below 60 seconds are blocked.

Values greater than or equal to 86400 seconds are blocked in accelerated mode because that is the production/default 24-hour boundary.

## 7. Hard Blocks

Accelerated cooldown must hard block when any condition is true:

- `PAPER_SOAK_TEST_ACCELERATED=true` with `ALPACA_PAPER` not true.
- `PAPER_SOAK_TEST_ACCELERATED=true` with live endpoint.
- `PAPER_SOAK_TEST_ACCELERATED=true` with live trading assumption.
- `PAPER_SOAK_TEST_COOLDOWN_SECONDS` missing.
- `PAPER_SOAK_TEST_COOLDOWN_SECONDS < 60`.
- `PAPER_SOAK_TEST_COOLDOWN_SECONDS >= 86400`.
- Accelerated cooldown used outside soak testing.
- Accelerated cooldown used for live trading.
- Accelerated cooldown used with notional `> 100 USD`.
- Accelerated cooldown used with more than one symbol.
- Accelerated cooldown used with more than one order per run.
- Accelerated cooldown used with batch/cancel/replace.
- Accelerated cooldown used if any V13 gate fails.
- Accelerated cooldown used if previous reconciliation is missing or mismatched.
- Accelerated cooldown used if previous post-mortem is missing or blocking.
- Accelerated cooldown used if unresolved issue exists.
- Accelerated cooldown used if kill switch active.

Any hard block stops before order submission.

## 8. Required Gate Preservation

Accelerated cooldown cannot bypass V13 gates.

Every accelerated soak run still requires:

1. Full tests `PASS`.
2. Architecture validation `PASS`.
3. V10 full pipeline dry-run regression `PASS`.
4. Automated paper send mocked regression `PASS`.
5. Soak framework status `PASS`.
6. Strategy Evaluation `PASS`.
7. Evaluation-First Gate `EVALUATION_GATE_PASSED`.
8. Negative Case Regression `PASS`.
9. Candidate created from valid `TRADE_PROPOSAL`.
10. Human Review status `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST`.
11. Finalized Paper Order Request status `PAPER_ORDER_REQUEST_FINALIZED`.
12. Manual Execution Confirmation status `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`.
13. Paper Send Preflight status `PAPER_ORDER_SEND_ALLOWED`.
14. Automation kill switch inactive.
15. Daily order limit not exceeded.
16. Daily notional limit not exceeded.
17. Accelerated cooldown satisfied.
18. Previous reconciliation exists and matched.
19. Previous post-mortem exists with no blockers.
20. No unresolved issue exists.
21. Alpaca paper account confirmed.
22. Live endpoint rejected.
23. Secrets present but never printed.

## 9. Required Safety Constraints

Accelerated cooldown preserves all soak constraints:

- Paper trading only.
- One symbol only.
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
- No multi-symbol automation.
- No higher frequency outside explicit accelerated test mode.

## 10. Required Audit And Reporting

Every accelerated soak run must record:

- Accelerated mode enabled.
- Configured cooldown seconds.
- Reason for accelerated test.
- Confirmation `ALPACA_PAPER=true`.
- Confirmation live trading unsupported.
- Confirmation live endpoint rejected.
- Confirmation production cooldown remains 24h by default.
- Confirmation this does not authorize production frequency increase.
- Confirmation this does not authorize live trading.
- Confirmation this does not authorize higher frequency outside test mode.

Reports must state:

- Accelerated cooldown was used for paper soak framework validation only.
- Production/default cooldown remains 24 hours.
- Live trading remains unsupported.
- Increasing notional remains prohibited.
- Multi-symbol automation remains prohibited.
- Batch orders remain prohibited.
- Cancel/replace remains prohibited.

## 11. Required Report Fields

Accelerated cooldown reports must include:

- `PAPER_SOAK_TEST_ACCELERATED` status.
- `PAPER_SOAK_TEST_COOLDOWN_SECONDS` value.
- Production/default cooldown value: 86400 seconds.
- Accelerated cooldown range validation result.
- Accelerated test reason.
- V13 gate summary.
- Reconciliation dependency status.
- Post-mortem dependency status.
- Unresolved issue status.
- Kill switch status.
- Live endpoint rejection status.
- Secret-printing status.
- Flag cleanup status.
- Recommendation.

Reports must not contain secrets.

## 12. Success Criteria

Success criteria:

- Developer can validate soak mechanics without waiting 24 hours.
- Production/default cooldown remains unchanged.
- Accelerated mode is explicit, auditable, and paper-only.
- Accelerated mode cannot be used with live trading.
- Accelerated mode cannot bypass V13 gates.
- Accelerated mode cannot bypass reconciliation requirements.
- Accelerated mode cannot bypass post-mortem requirements.
- Accelerated mode cannot bypass unresolved issue blocking.
- Accelerated mode cannot bypass kill switch blocking.

## 13. Failure Conditions

Failure conditions:

- Accelerated mode changes production/default cooldown.
- Accelerated mode runs by default.
- Accelerated mode allows live trading.
- Accelerated mode allows live endpoint usage.
- Accelerated mode allows notional `> 100 USD`.
- Accelerated mode allows more than one symbol.
- Accelerated mode allows more than one order per run.
- Accelerated mode allows batch/cancel/replace.
- Accelerated mode bypasses any V13 gate.
- Accelerated mode bypasses reconciliation or post-mortem dependency.
- Accelerated mode runs with unresolved issues.
- Accelerated mode runs while kill switch is active.
- Accelerated mode prints, logs, commits, or reports secrets.

## 14. What Remains Prohibited

Still prohibited:

- Live trading.
- Live endpoints.
- Increasing notional.
- Multi-symbol automation.
- Batch orders.
- Cancel/replace.
- Removing Human Review.
- Removing Manual Execution Confirmation.
- Removing Strategy Evaluation Harness.
- Bypassing Evaluation-First Gate.
- Bypassing Negative Case Regression.
- Bypassing Paper Send Preflight.
- Higher frequency outside explicit accelerated paper soak test mode.
- Production frequency increase.
- Leaving `PAPER_ORDER_EXECUTION_ENABLED` enabled by default.
- Leaving `PAPER_AUTOMATED_SEND_ENABLED` enabled by default.
- Leaving `PAPER_SOAK_TEST_ACCELERATED` enabled by default.

## 15. Live Trading Statement

Live trading remains unsupported.

Phase 53 is a paper-only cooldown design for soak framework validation. It does not authorize live trading, increasing notional, multi-symbol automation, batch orders, cancel/replace, removal of Human Review, removal of Manual Execution Confirmation, production frequency increase, or bypassing any V13 gate.
