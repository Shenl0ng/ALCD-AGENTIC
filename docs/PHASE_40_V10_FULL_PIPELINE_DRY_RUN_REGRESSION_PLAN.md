# Phase 40 V10 Full Pipeline Dry-Run Regression Plan

## Purpose

Define a full V10 pipeline dry-run regression from automated analysis through Paper Send Preflight, without sending any order.

This phase must prove that the complete V10 pipeline can produce `PAPER_ORDER_SEND_ALLOWED` without sending an order, calling Alpaca order API, enabling `PAPER_ORDER_EXECUTION_ENABLED`, or creating broker execution readiness.

## Context

Baseline V10 is `PASS`.

V10 pipeline:

```text
Automated dry-run
-> TRADE_PROPOSAL
-> Paper Order Request Candidate
-> Human Review Queue
-> Finalized Paper Order Request
-> Manual Execution Confirmation
-> Paper Send Preflight
-> stop
```

This regression is dry-run validation only. It does not authorize Paper Send, broker execution, Alpaca order API usage, execution flag enablement, live trading, notional increase, automation beyond approved dry-run/candidate flow, or multi-symbol automation.

## Required Constraints

The regression must enforce:

- `DRY_RUN_ONLY` unless explicitly inside preflight checks.
- One symbol only.
- Max notional `<= 100 USD`.
- Limit order only.
- Day time-in-force only.
- No short selling.
- No crypto.
- No options.
- No margin/leverage.
- No extended hours.
- No batch behavior.
- No cancel/replace.
- No live trading.
- No live endpoints.
- No Alpaca order API.
- No `PAPER_ORDER_EXECUTION_ENABLED=true`.
- No order sent.
- No broker execution readiness.

## Regression Flow

For each scenario, the regression runner must:

1. Confirm `DRY_RUN_ONLY` where applicable.
2. Confirm `PAPER_ORDER_EXECUTION_ENABLED` is not enabled.
3. Confirm one symbol only.
4. Run automated dry-run analysis.
5. Attempt Paper Order Request Candidate creation only when a valid `TRADE_PROPOSAL` exists.
6. Attempt Human Review Queue only when candidate creation succeeds.
7. Attempt finalized Paper Order Request only when human review approval permits it.
8. Attempt Manual Execution Confirmation only when finalized request exists.
9. Attempt Paper Send Preflight only when manual confirmation permits it.
10. Stop after preflight or the first blocked stage.
11. Record artifacts created, blocked stage, final status, and safety proofs.

No scenario may progress to Paper Send, broker execution readiness, Alpaca order API, live trading, or execution flag enablement.

## Required Regression Scenarios

### 1. Full Valid V10 Pipeline

Expected:

- `TRADE_PROPOSAL`
- Candidate created
- Human review approved for paper request
- Finalized request created
- Manual execution confirmed for paper preflight
- Preflight status `PAPER_ORDER_SEND_ALLOWED`
- No order sent
- No broker execution readiness

### 2. Candidate Blocked Scenario

Expected:

- Candidate not created
- No review
- No finalized request
- No manual confirmation
- No preflight
- No order sent

### 3. Human Review Rejected Scenario

Expected:

- Candidate created
- Human review rejected
- No finalized request
- No manual confirmation
- No preflight
- No order sent

### 4. Manual Confirmation Rejected Scenario

Expected:

- Finalized request created
- Manual confirmation rejected
- No preflight allowed
- No order sent

### 5. Preflight Blocked Scenario

Expected:

- Preflight status `PAPER_ORDER_SEND_BLOCKED`
- No order sent
- No broker execution readiness

### 6. `PAPER_ORDER_EXECUTION_ENABLED=true` Scenario

Expected:

- Blocked before progression
- No order sent

## Required Report Path

The regression report must be written to:

```text
reports/v10_full_pipeline_dry_run_regression/<timestamp>/V10_FULL_PIPELINE_DRY_RUN_REGRESSION_REPORT.md
```

## Required Report Content

The report must include:

- Scenarios run
- Scenario results
- Artifacts created
- Blocked stages
- Final statuses
- Proof no order was sent
- Proof no Alpaca order API was called
- Proof `PAPER_ORDER_EXECUTION_ENABLED` was not enabled
- Proof no broker execution readiness was created
- Statement: Live trading remains unsupported.
- Statement: Increasing notional remains prohibited.
- Statement: Automation beyond approved dry-run/candidate flow remains prohibited.

## Success Criteria

Phase 40 is successful only if:

- All scenarios produce expected results.
- Valid scenario reaches `PAPER_ORDER_SEND_ALLOWED`.
- Invalid scenarios block at the correct stage.
- No scenario sends orders.
- No scenario creates broker execution readiness.
- No scenario calls Alpaca order API.
- No scenario enables `PAPER_ORDER_EXECUTION_ENABLED`.
- Live trading remains unsupported.

## Failure Conditions

The regression must fail if:

- Any invalid scenario progresses beyond its expected blocked stage.
- Any scenario sends an order.
- Any scenario calls Alpaca order API.
- Any scenario creates broker execution readiness.
- Any scenario enables `PAPER_ORDER_EXECUTION_ENABLED`.
- Any scenario touches live trading or live endpoints.
- Any scenario increases notional above `100 USD`.
- Any scenario introduces batch behavior or cancel/replace behavior.

## What Remains Prohibited

The following remain prohibited:

- Order sending
- Alpaca order API
- Broker execution readiness
- Live trading
- Live endpoints
- `PAPER_ORDER_EXECUTION_ENABLED=true`
- Increasing notional
- Batch orders
- Cancel/replace
- Multi-symbol automation
- Higher frequency
- Automated Paper Send
- Bypassing V4-V10 gates

## Conditions Before Implementation

Before implementation:

- Baseline V10 must remain `PASS`.
- Phase 39 Paper Send Preflight Implementation must remain `PASS`.
- `PAPER_ORDER_EXECUTION_ENABLED` must remain unset.
- No Alpaca order API may be used.
- No Paper Send may be performed.
- No broker execution readiness may be created.
- No live endpoint may be used.
- No live trading may be supported.
- No credentials may be printed, logged, committed, or written to reports.

## Live Trading Statement

Live trading remains unsupported.
