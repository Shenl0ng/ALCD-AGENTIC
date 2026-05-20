# Phase 28 Automated Proposal Dry-Run Regression Plan

## Purpose

Define how to run automated proposal dry-run regression after Phase 27.

This regression proves that the automated proposal dry-run runner can process one symbol and produce one of:

- NO_TRADE
- REJECT
- TRADE_PROPOSAL

The regression must also prove that the automated runner remains unable to create Paper Order Requests, request Human Approval, request Manual Execution Confirmation, send orders, or create broker execution readiness.

## Scope

Phase 28 is regression-only and offline-only.

It does not modify runtime code.
It does not create Paper Order Requests.
It does not request Human Approval.
It does not request Manual Execution Confirmation.
It does not enable PAPER_ORDER_EXECUTION_ENABLED.
It does not send orders.
It does not use the Alpaca order API.
It does not touch live trading.

## Required Constraints

- DRY_RUN_ONLY only
- One symbol only
- No paper order request
- No human approval request
- No manual execution confirmation
- No paper send
- No broker execution readiness
- No live trading
- No Alpaca order API
- No batch behavior
- No cancel/replace
- No execution flag enabled

## Regression Flow

1. Confirm Operating Policy After V4 remains in force.
2. Confirm DRY_RUN_ONLY mode.
3. Confirm PAPER_ORDER_EXECUTION_ENABLED is not enabled.
4. Run the automated proposal dry-run runner against each required scenario.
5. Capture the decision, gate status, risk dry-run status, final status, and report path for each scenario.
6. Verify no scenario created a Paper Order Request.
7. Verify no scenario requested Human Approval.
8. Verify no scenario requested Manual Execution Confirmation.
9. Verify no scenario sent an order.
10. Verify no scenario created paper send readiness.
11. Verify no scenario created broker execution readiness.
12. Write the automated proposal dry-run regression report.
13. Stop.

## Regression Scenarios

### 1. Strong Proposal Fixture

Expected result:

- TRADE_PROPOSAL may be created
- Strategy Evaluation PASS
- Evaluation-First Gate may pass
- Risk dry-run may pass
- No Paper Order Request
- No Human Approval request
- No Manual Execution Confirmation request
- No paper send readiness
- No broker execution readiness
- No order sent

### 2. Weak Setup Fixture

Expected result:

- REJECT or NO_TRADE
- Evaluation gate blocked or low score
- No Paper Order Request
- No Human Approval request
- No Manual Execution Confirmation request
- No paper send readiness
- No broker execution readiness
- No order sent

### 3. No-Trade Fixture

Expected result:

- NO_TRADE
- No Paper Order Request
- No Human Approval request
- No Manual Execution Confirmation request
- No paper send readiness
- No broker execution readiness
- No order sent

### 4. Data Integrity Failure Fixture

Expected result:

- AUTOMATED_DRY_RUN_BLOCKED
- No downstream trade progression
- No Paper Order Request
- No Human Approval request
- No Manual Execution Confirmation request
- No paper send readiness
- No broker execution readiness
- No order sent

### 5. Multiple Symbol Attempt

Expected result:

- Blocked
- No analysis progression
- No Paper Order Request
- No Human Approval request
- No Manual Execution Confirmation request
- No paper send readiness
- No broker execution readiness
- No order sent

### 6. PAPER_ORDER_EXECUTION_ENABLED=true Attempt

Expected result:

- Blocked immediately
- No analysis progression
- No Paper Order Request
- No Human Approval request
- No Manual Execution Confirmation request
- No paper send readiness
- No broker execution readiness
- No order sent

## Required Artifacts

The regression must write this report:

```text
reports/automated_proposal_dry_run_regression/<timestamp>/AUTOMATED_PROPOSAL_DRY_RUN_REGRESSION_REPORT.md
```

The report must include:

- Scenarios run
- Scenario results
- Decisions produced
- Gate statuses
- Blocked conditions
- Report paths for each scenario
- Proof no Paper Order Request was created
- Proof no Human Approval was requested
- Proof no Manual Execution Confirmation was requested
- Proof no order was sent
- Proof no broker execution readiness was created
- Statement: Live trading remains unsupported.

## Required Tests

The regression implementation must test:

- All required scenarios run.
- Strong proposal fixture can produce TRADE_PROPOSAL.
- Strong proposal fixture cannot create Paper Order Request.
- Weak setup fixture produces REJECT or NO_TRADE.
- No-trade fixture produces NO_TRADE.
- Data integrity failure fixture blocks.
- Multiple symbol attempt blocks.
- PAPER_ORDER_EXECUTION_ENABLED=true attempt blocks.
- No scenario requests Human Approval.
- No scenario requests Manual Execution Confirmation.
- No scenario sends orders.
- No scenario creates paper send readiness.
- No scenario creates broker execution readiness.
- No scenario uses Alpaca order API.
- No scenario uses live trading.
- No scenario uses batch behavior.
- No scenario uses cancel/replace.
- Regression report is generated.
- Regression report states: Live trading remains unsupported.

## Success Criteria

- All scenarios produce expected result.
- Strong proposal can produce TRADE_PROPOSAL but cannot progress to order request.
- Weak setup is rejected or no-trade.
- No-trade fixture produces NO_TRADE.
- Data integrity failure blocks.
- Multiple symbol attempt blocks.
- Execution flag attempt blocks.
- No scenario sends orders.
- No scenario creates Paper Order Request.
- No scenario requests Human Approval.
- No scenario requests Manual Execution Confirmation.
- No scenario creates paper send readiness.
- No scenario creates broker execution readiness.

## Failure Conditions

The regression fails if any scenario:

- Sends an order
- Creates a Paper Order Request
- Requests Human Approval
- Requests Manual Execution Confirmation
- Creates paper send readiness
- Creates broker execution readiness
- Uses live trading
- Uses live endpoints
- Uses the Alpaca order API
- Enables PAPER_ORDER_EXECUTION_ENABLED
- Processes more than one symbol without blocking
- Uses batch behavior
- Uses cancel/replace behavior
- Fails to write the required report

## What Remains Prohibited

- Paper Order Request creation
- Human Approval request
- Manual Execution Confirmation request
- Paper send
- Broker execution readiness
- Live trading
- Live endpoints
- Alpaca order API usage
- Batch orders
- Cancel/replace
- Notional increase
- Frequency increase
- Autonomous execution
- Enabling PAPER_ORDER_EXECUTION_ENABLED

## Implementation Conditions

Before Phase 28 implementation:

- Phase 27 Automated Proposal Dry-Run Implementation must remain PASS.
- Operating Policy After V4 must remain PASS.
- DRY_RUN_ONLY must remain the default mode.
- PAPER_ORDER_EXECUTION_ENABLED must remain unset.
- Runtime paper execution logic must not be changed.
- No credentials may be printed, logged, committed, or written to reports.

## Live Trading Statement

Live trading remains unsupported.
