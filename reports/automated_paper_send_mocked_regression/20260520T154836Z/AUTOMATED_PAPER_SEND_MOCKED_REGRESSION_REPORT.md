# Automated Paper Send Mocked Regression Report

## Summary

- Generated at: 2026-05-20T15:48:36Z
- Final status: PASS
- Scenarios run: 14
- Mocked order count: 1
- Proof no real Alpaca API was called: True
- Proof no real order was sent: True
- Proof system returned to DRY_RUN_ONLY: True
- Proof flags were disabled/unset after test context: True

## Scenario Results

### full_valid_mocked_automated_paper_send

- Description: Full valid mocked automated paper send submits one mocked paper limit/day order.
- Passed: True
- Failure reason: none
- Final status: AUTOMATED_PAPER_SEND_SUBMITTED
- Mocked order count: 1
- Reconciliation status: RECONCILIATION_MATCHED
- Report path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/full_valid_mocked_automated_paper_send/20260520T154836Z/AUTOMATED_PAPER_SEND_REPORT.md
- Automation audit log path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/full_valid_mocked_automated_paper_send/20260520T154836Z/AUTOMATION_AUDIT_LOG.md
- Post-send safety path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/full_valid_mocked_automated_paper_send/20260520T154836Z/POST_SEND_SAFETY.md
- Post-mortem path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/full_valid_mocked_automated_paper_send/20260520T154836Z/POST_MORTEM.md
- Returned to DRY_RUN_ONLY: True
- Flags disabled/unset after test context: True
- Real Alpaca API called: False
- Real order sent: False

### default_disabled

- Description: PAPER_AUTOMATED_SEND_ENABLED=false blocks send.
- Passed: True
- Failure reason: none
- Final status: AUTOMATED_PAPER_SEND_BLOCKED
- Mocked order count: 0
- Reconciliation status: RECONCILIATION_BLOCKED_NO_ORDER
- Report path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/default_disabled/20260520T154836Z/AUTOMATED_PAPER_SEND_REPORT.md
- Automation audit log path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/default_disabled/20260520T154836Z/AUTOMATION_AUDIT_LOG.md
- Post-send safety path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/default_disabled/20260520T154836Z/POST_SEND_SAFETY.md
- Post-mortem path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/default_disabled/20260520T154836Z/POST_MORTEM.md
- Returned to DRY_RUN_ONLY: True
- Flags disabled/unset after test context: True
- Real Alpaca API called: False
- Real order sent: False

### execution_flag_disabled

- Description: PAPER_ORDER_EXECUTION_ENABLED=false blocks send.
- Passed: True
- Failure reason: none
- Final status: AUTOMATED_PAPER_SEND_BLOCKED
- Mocked order count: 0
- Reconciliation status: RECONCILIATION_BLOCKED_NO_ORDER
- Report path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/execution_flag_disabled/20260520T154836Z/AUTOMATED_PAPER_SEND_REPORT.md
- Automation audit log path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/execution_flag_disabled/20260520T154836Z/AUTOMATION_AUDIT_LOG.md
- Post-send safety path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/execution_flag_disabled/20260520T154836Z/POST_SEND_SAFETY.md
- Post-mortem path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/execution_flag_disabled/20260520T154836Z/POST_MORTEM.md
- Returned to DRY_RUN_ONLY: True
- Flags disabled/unset after test context: True
- Real Alpaca API called: False
- Real order sent: False

### kill_switch

- Description: Automation kill switch active blocks send.
- Passed: True
- Failure reason: none
- Final status: AUTOMATED_PAPER_SEND_REJECTED_BY_KILL_SWITCH
- Mocked order count: 0
- Reconciliation status: RECONCILIATION_BLOCKED_NO_ORDER
- Report path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/kill_switch/20260520T154836Z/AUTOMATED_PAPER_SEND_REPORT.md
- Automation audit log path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/kill_switch/20260520T154836Z/AUTOMATION_AUDIT_LOG.md
- Post-send safety path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/kill_switch/20260520T154836Z/POST_SEND_SAFETY.md
- Post-mortem path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/kill_switch/20260520T154836Z/POST_MORTEM.md
- Returned to DRY_RUN_ONLY: True
- Flags disabled/unset after test context: True
- Real Alpaca API called: False
- Real order sent: False

### daily_order_limit

- Description: Daily order limit exceeded blocks send.
- Passed: True
- Failure reason: none
- Final status: AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS
- Mocked order count: 0
- Reconciliation status: RECONCILIATION_BLOCKED_NO_ORDER
- Report path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/daily_order_limit/20260520T154836Z/AUTOMATED_PAPER_SEND_REPORT.md
- Automation audit log path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/daily_order_limit/20260520T154836Z/AUTOMATION_AUDIT_LOG.md
- Post-send safety path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/daily_order_limit/20260520T154836Z/POST_SEND_SAFETY.md
- Post-mortem path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/daily_order_limit/20260520T154836Z/POST_MORTEM.md
- Returned to DRY_RUN_ONLY: True
- Flags disabled/unset after test context: True
- Real Alpaca API called: False
- Real order sent: False

### daily_notional_limit

- Description: Daily notional limit exceeded blocks send.
- Passed: True
- Failure reason: none
- Final status: AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS
- Mocked order count: 0
- Reconciliation status: RECONCILIATION_BLOCKED_NO_ORDER
- Report path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/daily_notional_limit/20260520T154836Z/AUTOMATED_PAPER_SEND_REPORT.md
- Automation audit log path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/daily_notional_limit/20260520T154836Z/AUTOMATION_AUDIT_LOG.md
- Post-send safety path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/daily_notional_limit/20260520T154836Z/POST_SEND_SAFETY.md
- Post-mortem path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/daily_notional_limit/20260520T154836Z/POST_MORTEM.md
- Returned to DRY_RUN_ONLY: True
- Flags disabled/unset after test context: True
- Real Alpaca API called: False
- Real order sent: False

### cooldown

- Description: Cooldown not satisfied blocks send.
- Passed: True
- Failure reason: none
- Final status: AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS
- Mocked order count: 0
- Reconciliation status: RECONCILIATION_BLOCKED_NO_ORDER
- Report path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/cooldown/20260520T154836Z/AUTOMATED_PAPER_SEND_REPORT.md
- Automation audit log path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/cooldown/20260520T154836Z/AUTOMATION_AUDIT_LOG.md
- Post-send safety path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/cooldown/20260520T154836Z/POST_SEND_SAFETY.md
- Post-mortem path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/cooldown/20260520T154836Z/POST_MORTEM.md
- Returned to DRY_RUN_ONLY: True
- Flags disabled/unset after test context: True
- Real Alpaca API called: False
- Real order sent: False

### missing_previous_reconciliation

- Description: Missing previous reconciliation blocks send.
- Passed: True
- Failure reason: none
- Final status: AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION
- Mocked order count: 0
- Reconciliation status: RECONCILIATION_BLOCKED_NO_ORDER
- Report path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/missing_previous_reconciliation/20260520T154836Z/AUTOMATED_PAPER_SEND_REPORT.md
- Automation audit log path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/missing_previous_reconciliation/20260520T154836Z/AUTOMATION_AUDIT_LOG.md
- Post-send safety path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/missing_previous_reconciliation/20260520T154836Z/POST_SEND_SAFETY.md
- Post-mortem path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/missing_previous_reconciliation/20260520T154836Z/POST_MORTEM.md
- Returned to DRY_RUN_ONLY: True
- Flags disabled/unset after test context: True
- Real Alpaca API called: False
- Real order sent: False

### unresolved_reconciliation_mismatch

- Description: Unresolved reconciliation mismatch blocks send.
- Passed: True
- Failure reason: none
- Final status: AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION
- Mocked order count: 0
- Reconciliation status: RECONCILIATION_BLOCKED_NO_ORDER
- Report path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/unresolved_reconciliation_mismatch/20260520T154836Z/AUTOMATED_PAPER_SEND_REPORT.md
- Automation audit log path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/unresolved_reconciliation_mismatch/20260520T154836Z/AUTOMATION_AUDIT_LOG.md
- Post-send safety path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/unresolved_reconciliation_mismatch/20260520T154836Z/POST_SEND_SAFETY.md
- Post-mortem path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/unresolved_reconciliation_mismatch/20260520T154836Z/POST_MORTEM.md
- Returned to DRY_RUN_ONLY: True
- Flags disabled/unset after test context: True
- Real Alpaca API called: False
- Real order sent: False

### missing_post_mortem

- Description: Missing post-mortem blocks send.
- Passed: True
- Failure reason: none
- Final status: AUTOMATED_PAPER_SEND_REJECTED_BY_POST_MORTEM
- Mocked order count: 0
- Reconciliation status: RECONCILIATION_BLOCKED_NO_ORDER
- Report path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/missing_post_mortem/20260520T154836Z/AUTOMATED_PAPER_SEND_REPORT.md
- Automation audit log path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/missing_post_mortem/20260520T154836Z/AUTOMATION_AUDIT_LOG.md
- Post-send safety path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/missing_post_mortem/20260520T154836Z/POST_SEND_SAFETY.md
- Post-mortem path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/missing_post_mortem/20260520T154836Z/POST_MORTEM.md
- Returned to DRY_RUN_ONLY: True
- Flags disabled/unset after test context: True
- Real Alpaca API called: False
- Real order sent: False

### unresolved_issue

- Description: Unresolved issue blocks send.
- Passed: True
- Failure reason: none
- Final status: AUTOMATED_PAPER_SEND_BLOCKED
- Mocked order count: 0
- Reconciliation status: RECONCILIATION_BLOCKED_NO_ORDER
- Report path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/unresolved_issue/20260520T154836Z/AUTOMATED_PAPER_SEND_REPORT.md
- Automation audit log path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/unresolved_issue/20260520T154836Z/AUTOMATION_AUDIT_LOG.md
- Post-send safety path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/unresolved_issue/20260520T154836Z/POST_SEND_SAFETY.md
- Post-mortem path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/unresolved_issue/20260520T154836Z/POST_MORTEM.md
- Returned to DRY_RUN_ONLY: True
- Flags disabled/unset after test context: True
- Real Alpaca API called: False
- Real order sent: False

### live_endpoint

- Description: Live endpoint configured blocks send.
- Passed: True
- Failure reason: none
- Final status: AUTOMATED_PAPER_SEND_REJECTED_BY_PREFLIGHT
- Mocked order count: 0
- Reconciliation status: RECONCILIATION_BLOCKED_NO_ORDER
- Report path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/live_endpoint/20260520T154836Z/AUTOMATED_PAPER_SEND_REPORT.md
- Automation audit log path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/live_endpoint/20260520T154836Z/AUTOMATION_AUDIT_LOG.md
- Post-send safety path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/live_endpoint/20260520T154836Z/POST_SEND_SAFETY.md
- Post-mortem path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/live_endpoint/20260520T154836Z/POST_MORTEM.md
- Returned to DRY_RUN_ONLY: True
- Flags disabled/unset after test context: True
- Real Alpaca API called: False
- Real order sent: False

### notional_over_100

- Description: Notional over 100 USD blocks send.
- Passed: True
- Failure reason: none
- Final status: AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS
- Mocked order count: 0
- Reconciliation status: RECONCILIATION_BLOCKED_NO_ORDER
- Report path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/notional_over_100/20260520T154836Z/AUTOMATED_PAPER_SEND_REPORT.md
- Automation audit log path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/notional_over_100/20260520T154836Z/AUTOMATION_AUDIT_LOG.md
- Post-send safety path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/notional_over_100/20260520T154836Z/POST_SEND_SAFETY.md
- Post-mortem path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/notional_over_100/20260520T154836Z/POST_MORTEM.md
- Returned to DRY_RUN_ONLY: True
- Flags disabled/unset after test context: True
- Real Alpaca API called: False
- Real order sent: False

### batch_cancel_replace

- Description: Batch and cancel/replace behavior blocks send.
- Passed: True
- Failure reason: none
- Final status: AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS
- Mocked order count: 0
- Reconciliation status: RECONCILIATION_BLOCKED_NO_ORDER
- Report path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/batch_cancel_replace/20260520T154836Z/AUTOMATED_PAPER_SEND_REPORT.md
- Automation audit log path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/batch_cancel_replace/20260520T154836Z/AUTOMATION_AUDIT_LOG.md
- Post-send safety path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/batch_cancel_replace/20260520T154836Z/POST_SEND_SAFETY.md
- Post-mortem path: reports/automated_paper_send_mocked_regression/20260520T154836Z/scenario_artifacts/batch_cancel_replace/20260520T154836Z/POST_MORTEM.md
- Returned to DRY_RUN_ONLY: True
- Flags disabled/unset after test context: True
- Real Alpaca API called: False
- Real order sent: False

## Gate Results

- All V12 gates PASS in the full valid mocked scenario.
- Blocked scenarios verify gate or safety-control rejection before mocked order submission.

## Limit Results

- Daily order limit scenario rejects with AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS.
- Daily notional limit scenario rejects with AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS.
- Notional over 100 scenario rejects before any mocked order is sent.
- Batch orders remain prohibited.
- Cancel/replace remains prohibited.

## Kill Switch Results

- Kill switch scenario rejects with AUTOMATED_PAPER_SEND_REJECTED_BY_KILL_SWITCH.

## Cooldown Results

- Cooldown scenario rejects with AUTOMATED_PAPER_SEND_REJECTED_BY_LIMITS.

## Reconciliation Dependency Results

- Missing previous reconciliation scenario rejects with AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION.
- Unresolved reconciliation mismatch scenario rejects with AUTOMATED_PAPER_SEND_REJECTED_BY_RECONCILIATION.

## Post-Mortem Dependency Results

- Missing post-mortem scenario rejects with AUTOMATED_PAPER_SEND_REJECTED_BY_POST_MORTEM.
- Unresolved issue scenario rejects before mocked order submission.

## Audit Log Results

- Every scenario writes an automation audit log artifact.

## Proof Statements

- Proof no real Alpaca API was called: true
- Proof no real order was sent: true
- Proof system returned to DRY_RUN_ONLY: True
- Proof flags were disabled/unset after test context: True

Automated paper send remains paper-only.
Live trading remains unsupported.
Increasing notional remains prohibited.
Batch orders remain prohibited.
Cancel/replace remains prohibited.
