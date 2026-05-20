# Phase 30 Automated Paper Request With Human Approval Design

## Purpose

Design the next controlled step after Baseline V5: allowing the automated dry-run system to create a Paper Order Request Candidate only after all V5 gates pass, while still requiring human approval before any real Paper Order Request can be finalized.

This phase is semi-automation design only.

It must not send orders.
It must not enable `PAPER_ORDER_EXECUTION_ENABLED`.
It must not create broker execution readiness.
It must not bypass human approval.
It must not bypass manual execution confirmation.
It must not support live trading.

## Context

Baseline V5 is `PASS`.

V5 allows automated proposal dry-run only:

- One symbol
- `DRY_RUN_ONLY`
- May produce `NO_TRADE`, `REJECT`, or `TRADE_PROPOSAL`
- Cannot create Paper Order Requests
- Cannot request Human Approval
- Cannot request Manual Execution Confirmation
- Cannot send orders
- Cannot create broker execution readiness

Phase 30 does not authorize finalized Paper Order Request creation, paper sends, broker execution readiness, or live trading.

## New Concept: Paper Order Request Candidate

A Paper Order Request Candidate is a pre-request review artifact.

A candidate is not a broker order.
A candidate is not a finalized Paper Order Request.
A candidate cannot be sent.
A candidate cannot trigger Alpaca.
A candidate cannot create broker readiness.
A candidate only represents a reviewed proposal that may be presented to a human.

The candidate exists to separate automated analysis from any later human approval and request-finalization step.

## Allowed Automated Behavior

The automated system may:

- Run automated dry-run for one symbol.
- Produce `NO_TRADE`, `REJECT`, or `TRADE_PROPOSAL`.
- If `TRADE_PROPOSAL` passes all required gates, create a Paper Order Request Candidate.
- Write candidate artifact.
- Write journal entry.
- Stop.
- Wait for human review.

The automated system may not proceed beyond candidate creation.

## Required Gates Before Candidate Creation

All of the following must pass before candidate creation:

- `DRY_RUN_ONLY` mode
- `PAPER_ORDER_EXECUTION_ENABLED` is not enabled
- One symbol only
- Data Integrity `PASS`
- Strategy Evaluation `PASS`
- Evaluation-First Gate `PASS`
- Negative Case Regression `PASS`
- Proposal does not match known negative-case failure patterns
- Risk Manager dry-run/read-only `PASS`
- ADLC compliance `PASS`
- Journal readiness `PASS`
- No paper send readiness
- No broker execution readiness

If any gate fails, the candidate must not be created.

## Candidate Required Fields

Each Paper Order Request Candidate must include:

- `candidate_id`
- `created_at`
- `symbol`
- `proposal_id`
- `strategy_evaluation_reference`
- `evaluation_gate_reference`
- `negative_case_regression_reference`
- `risk_dry_run_reference`
- `journal_reference`
- `proposed_side`
- `proposed_order_type`
- `proposed_time_in_force`
- `proposed_notional`
- `proposed_quantity` optional
- `proposed_limit_price`
- `stop_loss`
- `target_1`
- `target_2` optional
- `thesis`
- `invalidation`
- `paper_trading_only`
- `human_approval_required`
- `manual_execution_confirmation_required`
- `broker_execution_allowed`
- `live_trading_allowed`
- `candidate_status`

## Required Hardcoded Candidate Safety Values

Every candidate must hardcode these safety values:

- `paper_trading_only: true`
- `human_approval_required: true`
- `manual_execution_confirmation_required: true`
- `broker_execution_allowed: false`
- `live_trading_allowed: false`

These values must not be user-configurable during Phase 30.

## Allowed Candidate Statuses

Allowed candidate statuses:

- `PAPER_ORDER_CANDIDATE_CREATED`
- `PAPER_ORDER_CANDIDATE_BLOCKED`
- `PAPER_ORDER_CANDIDATE_INVALID`
- `PAPER_ORDER_CANDIDATE_EXPIRED`

No candidate status may imply broker readiness, send readiness, or approval completion.

## Hard Blocks

The system must hard-block:

- Any attempt to send order
- Any attempt to create finalized Paper Order Request
- Any attempt to request Manual Execution Confirmation
- Any attempt to enable `PAPER_ORDER_EXECUTION_ENABLED`
- Any attempt to create broker execution readiness
- Any live trading assumption
- Any live endpoint
- Any batch behavior
- Any cancel/replace behavior
- More than one symbol
- Missing `human_approval_required=true`
- `broker_execution_allowed=true`
- `live_trading_allowed=true`

## Required Artifact Path

Candidate artifacts must be written to:

```text
reports/automated_paper_request_candidate/<timestamp>/PAPER_ORDER_REQUEST_CANDIDATE.md
```

## Required Report Content

The candidate report must include:

- Symbol
- Decision
- Candidate status
- Proposal reference
- Strategy evaluation status
- Evaluation gate status
- Negative Case Regression status
- Risk dry-run status
- Journal reference
- `paper_trading_only`
- `human_approval_required`
- `manual_execution_confirmation_required`
- `broker_execution_allowed`
- `live_trading_allowed`
- Final status
- Reason
- Statement: No order was sent.
- Statement: No finalized Paper Order Request was created.
- Statement: No broker execution readiness was created.
- Statement: Live trading remains unsupported.

## Success Criteria

Phase 30 is successful only if:

- Candidate can be created only from a valid `TRADE_PROPOSAL`.
- `NO_TRADE` does not create candidate.
- `REJECT` does not create candidate.
- Candidate requires human approval later.
- Candidate requires manual execution confirmation later.
- Candidate cannot be sent.
- Candidate cannot create broker readiness.
- Candidate cannot enable execution.
- Candidate cannot use Alpaca order API.
- Live trading remains unsupported.

## Required Tests

Implementation must test:

- Valid `TRADE_PROPOSAL` can create `PAPER_ORDER_CANDIDATE_CREATED`.
- `NO_TRADE` creates no candidate and returns blocked or no-candidate status.
- `REJECT` creates no candidate and returns blocked or no-candidate status.
- Candidate contains every required field.
- Candidate hardcodes `paper_trading_only: true`.
- Candidate hardcodes `human_approval_required: true`.
- Candidate hardcodes `manual_execution_confirmation_required: true`.
- Candidate hardcodes `broker_execution_allowed: false`.
- Candidate hardcodes `live_trading_allowed: false`.
- More than one symbol blocks.
- `PAPER_ORDER_EXECUTION_ENABLED=true` blocks.
- Missing Strategy Evaluation `PASS` blocks.
- Missing Evaluation-First Gate `PASS` blocks.
- Missing Negative Case Regression `PASS` blocks.
- Missing Risk Manager dry-run/read-only `PASS` blocks.
- Missing journal readiness blocks.
- Any paper send readiness blocks.
- Any broker execution readiness blocks.
- No finalized Paper Order Request is created.
- No Human Approval auto-approval occurs.
- No Manual Execution Confirmation request occurs.
- No order is sent.
- No Alpaca order API call exists.
- No live trading exists.
- No batch behavior exists.
- No cancel/replace behavior exists.

## Data Flow

1. Automated dry-run runner evaluates one symbol in `DRY_RUN_ONLY`.
2. Runner produces `NO_TRADE`, `REJECT`, or `TRADE_PROPOSAL`.
3. Gate checker verifies all required candidate gates.
4. Candidate builder runs only for valid `TRADE_PROPOSAL` after all gates pass.
5. Candidate artifact is written.
6. Journal entry is written.
7. System stops and waits for human review.

No downstream finalized Paper Order Request, Human Approval request, Manual Execution Confirmation request, Paper Send, Alpaca call, or broker readiness may be created in this phase.

## Human Approval Boundary

Human approval is required later, but Phase 30 must not request or grant it automatically.

The candidate may be presented to a human in a later phase, but the candidate itself must remain inert:

- It cannot approve itself.
- It cannot request Human Approval.
- It cannot request Manual Execution Confirmation.
- It cannot become a finalized Paper Order Request.
- It cannot send.

## What Remains Prohibited

The following remain prohibited:

- Finalized Paper Order Request creation
- Human Approval auto-approval
- Manual Execution Confirmation
- Paper Send
- Broker execution readiness
- Alpaca order API
- Live trading
- Live endpoints
- Batch orders
- Cancel/replace
- Multi-symbol automation
- Notional increase
- Higher frequency
- Enabling `PAPER_ORDER_EXECUTION_ENABLED`
- Bypassing V4/V5 gates
- Bypassing Evaluation-First Gate
- Bypassing Negative Case Regression
- Bypassing Risk Manager
- Bypassing journal readiness

## Conditions Before Implementation

Before implementation:

- Baseline V5 must remain `PASS`.
- Phase 29 regression must remain `PASS`.
- `DRY_RUN_ONLY` must remain the default operating mode.
- `PAPER_ORDER_EXECUTION_ENABLED` must remain unset.
- No Alpaca order API may be used.
- No finalized Paper Order Request may be created.
- No Paper Send may be performed.
- No credentials may be printed, logged, committed, or written to reports.

## Live Trading Statement

Live trading remains unsupported.
