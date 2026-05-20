# Phase 34 Finalized Paper Order Request From Human-Approved Candidate Design

## Purpose

Design how a human-approved Paper Order Request Candidate may be converted into a finalized Paper Order Request.

This phase is design only.

It must not send orders.
It must not enable `PAPER_ORDER_EXECUTION_ENABLED`.
It must not create broker execution readiness.
It must not bypass Manual Execution Confirmation.
It must not support live trading.

## Context

Baseline V7 is `PASS`.

V7 allows:

- Automated dry-run analysis
- Automated Paper Order Request Candidate creation
- Human Review Queue for candidates

V7 does not allow:

- Finalized Paper Order Request automation
- Manual Execution Confirmation
- Paper Send
- Broker execution readiness
- Live trading

Phase 34 designs the next artifact boundary: conversion from a human-approved candidate into a finalized Paper Order Request that still cannot be sent by itself.

## Important Boundary

Finalized Paper Order Request is not broker execution.
Finalized Paper Order Request cannot be sent by itself.
Finalized Paper Order Request does not authorize Alpaca order placement.
Finalized Paper Order Request still requires Manual Execution Confirmation later.
Finalized Paper Order Request still requires Paper Send Preflight later.

The finalized request is an artifact that may become eligible for a later Manual Execution Confirmation phase. It is not an execution instruction.

## Required Flow

1. Load Paper Order Request Candidate.
2. Load Human Review Record.
3. Verify human review status is `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST`.
4. Verify all candidate gates remain valid.
5. Verify candidate has not expired.
6. Verify review has not expired.
7. Verify `paper_trading_only=true`.
8. Verify `live_trading_allowed=false`.
9. Verify `broker_execution_allowed=false` before finalization.
10. Verify `manual_execution_confirmation_required=true`.
11. Create finalized Paper Order Request.
12. Write artifact.
13. Write journal entry.
14. Stop.

No order send, broker readiness, Manual Execution Confirmation, Alpaca call, or live trading action may occur in this flow.

## Required Finalized Request Fields

Each finalized Paper Order Request must include:

- `paper_order_request_id`
- `candidate_id`
- `review_id`
- `created_at`
- `symbol`
- `side`
- `order_type`
- `time_in_force`
- `notional`
- `quantity` optional
- `limit_price`
- `stop_loss`
- `target_1`
- `target_2` optional
- `thesis`
- `invalidation`
- `proposal_reference`
- `strategy_evaluation_reference`
- `evaluation_gate_reference`
- `negative_case_regression_reference`
- `risk_reference`
- `journal_reference`
- `human_review_reference`
- `paper_trading_only`
- `manual_execution_confirmation_required`
- `broker_execution_allowed`
- `live_trading_allowed`
- `request_status`

## Required Hardcoded Safety Values

Every finalized Paper Order Request must hardcode:

- `paper_trading_only=true`
- `manual_execution_confirmation_required=true`
- `broker_execution_allowed=false`
- `live_trading_allowed=false`

These values must not be user-configurable during Phase 34.

## Allowed Request Statuses

Allowed request statuses:

- `PAPER_ORDER_REQUEST_FINALIZED`
- `PAPER_ORDER_REQUEST_BLOCKED`
- `PAPER_ORDER_REQUEST_INVALID`
- `PAPER_ORDER_REQUEST_EXPIRED`

No request status may imply broker execution readiness, paper send readiness, Alpaca order placement, live trading approval, or Manual Execution Confirmation.

## Hard Blocks

The finalized request flow must hard-block:

- Human review not approved
- Candidate expired
- Review expired
- Candidate not `PAPER_ORDER_CANDIDATE_CREATED`
- Missing candidate
- Missing review
- Missing reviewer
- Missing paper-only confirmation
- Missing no-live-trading confirmation
- Missing risk review confirmation
- Missing evaluation review confirmation
- Missing negative-case review confirmation
- Missing journal review confirmation
- `broker_execution_allowed=true`
- `live_trading_allowed=true`
- `manual_execution_confirmation_required=false`
- `PAPER_ORDER_EXECUTION_ENABLED=true`
- Any order send attempt
- Any broker execution readiness attempt
- Any Manual Execution Confirmation creation
- Any live trading assumption
- Any live endpoint

## Required Artifact Path

Finalized Paper Order Request artifacts must be written to:

```text
reports/finalized_paper_order_request/<timestamp>/FINALIZED_PAPER_ORDER_REQUEST.md
```

## Required Artifact Content

The artifact must include:

- Paper order request id
- Candidate id
- Review id
- Symbol
- Side
- Order type
- Time in force
- Notional
- Limit price
- Request status
- All gate references
- Human review reference
- `paper_trading_only`
- `manual_execution_confirmation_required`
- `broker_execution_allowed`
- `live_trading_allowed`
- Final status
- Reason
- Statement: Finalized Paper Order Request is not broker execution.
- Statement: Manual Execution Confirmation is still required later.
- Statement: Paper Send Preflight is still required later.
- Statement: No order was sent.
- Statement: No broker execution readiness was created.
- Statement: Live trading remains unsupported.

## Required Journal Entry

The journal entry must record:

- Paper order request id
- Candidate id
- Review id
- Request status
- Human review status
- Gate references
- Paper-only status
- Manual Execution Confirmation requirement
- Broker execution allowed status
- Live trading allowed status
- Final status
- Reason

The journal entry must not contain secrets.

## Success Criteria

Phase 34 is successful only if:

- Human-approved candidate can become finalized Paper Order Request.
- Rejected candidate cannot become finalized Paper Order Request.
- Expired candidate cannot become finalized Paper Order Request.
- Missing review cannot create finalized Paper Order Request.
- Missing candidate cannot create finalized Paper Order Request.
- Finalized request cannot send orders.
- Finalized request cannot create broker readiness.
- Finalized request cannot replace Manual Execution Confirmation.
- Finalized request cannot enable execution.
- Finalized request cannot call Alpaca.
- Live trading remains unsupported.

## Required Tests

Implementation must test:

- Finalized Paper Order Request model exists.
- Finalized request validator exists.
- Human-approved candidate creates `PAPER_ORDER_REQUEST_FINALIZED`.
- Human-rejected candidate blocks.
- Human review needing more information blocks.
- Expired candidate blocks.
- Expired review blocks.
- Missing candidate blocks.
- Missing review blocks.
- Missing reviewer blocks.
- Missing paper-only confirmation blocks.
- Missing no-live-trading confirmation blocks.
- Missing risk review confirmation blocks.
- Missing evaluation review confirmation blocks.
- Missing negative-case review confirmation blocks.
- Missing journal review confirmation blocks.
- Candidate not `PAPER_ORDER_CANDIDATE_CREATED` blocks.
- `broker_execution_allowed=true` blocks.
- `live_trading_allowed=true` blocks.
- `manual_execution_confirmation_required=false` blocks.
- `PAPER_ORDER_EXECUTION_ENABLED=true` blocks.
- Finalized request hardcodes `paper_trading_only=true`.
- Finalized request hardcodes `manual_execution_confirmation_required=true`.
- Finalized request hardcodes `broker_execution_allowed=false`.
- Finalized request hardcodes `live_trading_allowed=false`.
- Artifact is written.
- Journal entry is written.
- No order is sent.
- No broker execution readiness is created.
- No Manual Execution Confirmation is created.
- No Alpaca order API call exists.
- No live trading exists.
- No batch behavior exists.
- No cancel/replace exists.

## Data Flow

1. Candidate artifact enters finalized request flow.
2. Human Review Record enters finalized request flow.
3. Validator checks candidate safety, review approval, confirmations, expiration, and execution flag state.
4. Finalized Paper Order Request artifact is created only if all checks pass.
5. Journal entry is written.
6. Flow stops.

No Paper Send, Manual Execution Confirmation, broker readiness, Alpaca call, or live trading action may be created.

## What Remains Prohibited

The following remain prohibited:

- Order sending
- Broker execution readiness
- Manual Execution Confirmation
- Auto-send
- Live trading
- Live endpoints
- Alpaca order API
- Batch orders
- Cancel/replace
- Multi-symbol automation
- Notional increase
- Higher frequency
- Enabling `PAPER_ORDER_EXECUTION_ENABLED`
- Bypassing V4/V5/V6/V7 gates
- Bypassing Human Review Queue
- Bypassing Paper Send Preflight

## Conditions Before Implementation

Before implementation:

- Baseline V7 must remain `PASS`.
- Human Review Queue must remain `PASS`.
- Candidate creation must remain `PASS`.
- `PAPER_ORDER_EXECUTION_ENABLED` must remain unset.
- No Alpaca API may be used.
- No Manual Execution Confirmation may be created.
- No Paper Send may be performed.
- No broker execution readiness may be created.
- No credentials may be printed, logged, committed, or written to reports.

## Live Trading Statement

Live trading remains unsupported.
