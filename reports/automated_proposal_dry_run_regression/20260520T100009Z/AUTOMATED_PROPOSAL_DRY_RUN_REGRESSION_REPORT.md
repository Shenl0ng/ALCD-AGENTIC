# Automated Proposal Dry-Run Regression Report

## Summary

- Scenarios run: 6
- Scenario results: 6 passed, 0 failed
- Final status: PASS
- Proof no Paper Order Request was created: True
- Proof no Human Approval was requested: True
- Proof no Manual Execution Confirmation was requested: True
- Proof no order was sent: True
- Proof no broker execution readiness was created: True

Live trading remains unsupported.

## Decisions Produced

- NO_TRADE: 1
- REJECT: 4
- TRADE_PROPOSAL: 1

## Gate Statuses

- EVALUATION_GATE_BLOCKED: 2
- EVALUATION_GATE_PASSED: 1
- NOT_RUN: 3

## Scenario Results

| Scenario | Description | Passed | Decision | Final Status | Gate Status | Blocked Condition | Report Path |
|---|---|---:|---|---|---|---|---|
| strong_proposal_fixture | Strong proposal fixture | True | TRADE_PROPOSAL | AUTOMATED_DRY_RUN_PROPOSAL_CREATED | EVALUATION_GATE_PASSED | None | reports/automated_proposal_dry_run_regression/scenario_reports/20260520T100009Z/AUTOMATED_PROPOSAL_DRY_RUN_REPORT.md |
| weak_setup_fixture | Weak setup fixture | True | REJECT | AUTOMATED_DRY_RUN_REJECTED | EVALUATION_GATE_BLOCKED | None | reports/automated_proposal_dry_run_regression/scenario_reports/20260520T100009Z-1/AUTOMATED_PROPOSAL_DRY_RUN_REPORT.md |
| no_trade_fixture | No-trade fixture | True | NO_TRADE | AUTOMATED_DRY_RUN_NO_TRADE | EVALUATION_GATE_BLOCKED | None | reports/automated_proposal_dry_run_regression/scenario_reports/20260520T100009Z-2/AUTOMATED_PROPOSAL_DRY_RUN_REPORT.md |
| data_integrity_failure_fixture | Data integrity failure fixture | True | REJECT | AUTOMATED_DRY_RUN_BLOCKED | NOT_RUN | Data integrity failed: configured data is incomplete. | reports/automated_proposal_dry_run_regression/scenario_reports/20260520T100009Z-3/AUTOMATED_PROPOSAL_DRY_RUN_REPORT.md |
| multiple_symbol_attempt | Multiple symbol attempt | True | REJECT | AUTOMATED_DRY_RUN_BLOCKED | NOT_RUN | Exactly one symbol is required. | reports/automated_proposal_dry_run_regression/scenario_reports/20260520T100009Z-4/AUTOMATED_PROPOSAL_DRY_RUN_REPORT.md |
| execution_flag_enabled_attempt | PAPER_ORDER_EXECUTION_ENABLED=true attempt | True | REJECT | AUTOMATED_DRY_RUN_BLOCKED | NOT_RUN | PAPER_ORDER_EXECUTION_ENABLED=true is blocked. | reports/automated_proposal_dry_run_regression/scenario_reports/20260520T100009Z-5/AUTOMATED_PROPOSAL_DRY_RUN_REPORT.md |

## Blocked Conditions

- data_integrity_failure_fixture: Data integrity failed: configured data is incomplete.
- multiple_symbol_attempt: Exactly one symbol is required.
- execution_flag_enabled_attempt: PAPER_ORDER_EXECUTION_ENABLED=true is blocked.

## Required Proof Statements

- No Paper Order Request was created.
- No Human Approval was requested.
- No Manual Execution Confirmation was requested.
- No order was sent.
- No broker execution readiness was created.
- Live trading remains unsupported.
