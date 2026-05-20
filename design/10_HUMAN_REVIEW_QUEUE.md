# Phase 32 Human Review Queue Design

## Purpose

Design a Human Review Queue for automated Paper Order Request Candidates.

The queue allows candidates to be reviewed by a human before any finalized Paper Order Request can exist.

This phase is design only.

It must not send orders.
It must not create broker readiness.
It must not bypass human approval.
It must not bypass manual execution confirmation.
It must not support live trading.

## Context

Baseline V6 is `PASS`.

V6 allows automated Paper Order Request Candidate creation, but candidates:

- Are not broker orders
- Are not finalized Paper Order Requests
- Cannot be sent
- Cannot trigger Alpaca
- Cannot create broker execution readiness
- Require human approval later
- Require manual execution confirmation later

Phase 32 designs the human review step after candidate creation and before any later finalized Paper Order Request phase.

## Queue Role

The Human Review Queue is an inert review workflow.

It may receive a valid Paper Order Request Candidate and produce a Human Review Record.

It must not create a finalized Paper Order Request.
It must not send orders.
It must not create broker execution readiness.
It must not request or create Manual Execution Confirmation.
It must not enable `PAPER_ORDER_EXECUTION_ENABLED`.
It must not use Alpaca API.
It must not support live trading.

## Allowed Queue Behavior

The queue may:

- Accept Paper Order Request Candidates.
- Store candidates for human review.
- Display candidate summary.
- Display all gate references.
- Display risk dry-run result.
- Display evaluation result.
- Display negative-case regression result.
- Display journal reference.
- Allow human reviewer to choose:
  - `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST`
  - `HUMAN_REVIEW_REJECTED`
  - `HUMAN_REVIEW_NEEDS_MORE_INFORMATION`
  - `HUMAN_REVIEW_EXPIRED`
  - `HUMAN_REVIEW_INVALID`
- Write review artifact.
- Write journal entry.
- Stop.

The queue must stop after writing the review artifact and journal entry.

## Human Review Approval Meaning

Human review approval means:

- The candidate may become eligible for a finalized Paper Order Request in a later phase.

Human review approval does not mean:

- Order send approval
- Broker execution approval
- Live trading approval
- Manual Execution Confirmation
- Paper send readiness
- Finalized Paper Order Request creation

## Required Review Record Fields

Each Human Review Record must include:

- `review_id`
- `candidate_id`
- `reviewed_at`
- `reviewer`
- `review_status`
- `review_notes`
- `paper_only_confirmation`
- `no_live_trading_confirmation`
- `risk_review_confirmation`
- `evaluation_review_confirmation`
- `negative_case_review_confirmation`
- `journal_review_confirmation`
- `requested_changes` optional
- `expiration_at` optional

## Allowed Review Statuses

Allowed review statuses:

- `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST`
- `HUMAN_REVIEW_REJECTED`
- `HUMAN_REVIEW_NEEDS_MORE_INFORMATION`
- `HUMAN_REVIEW_EXPIRED`
- `HUMAN_REVIEW_INVALID`

No review status may imply order send approval, broker execution approval, live trading approval, Manual Execution Confirmation, or paper send readiness.

## Hard Blocks

The Human Review Queue must hard-block:

- Missing reviewer
- Missing `paper_only_confirmation`
- Missing `no_live_trading_confirmation`
- Missing `risk_review_confirmation`
- Missing `evaluation_review_confirmation`
- Missing `negative_case_review_confirmation`
- Missing `journal_review_confirmation`
- Candidate status not `PAPER_ORDER_CANDIDATE_CREATED`
- Candidate has `broker_execution_allowed=true`
- Candidate has `live_trading_allowed=true`
- Candidate missing `human_approval_required=true`
- Candidate missing `manual_execution_confirmation_required=true`
- Candidate expired
- Any attempt to send order
- Any attempt to create broker readiness
- Any attempt to create Manual Execution Confirmation
- Any attempt to enable `PAPER_ORDER_EXECUTION_ENABLED`

## Required Artifacts

Human Review Queue artifacts must be written to:

```text
reports/human_review_queue/<timestamp>/HUMAN_REVIEW_RECORD.md
```

## Required Report Content

The Human Review Record report must include:

- Candidate id
- Reviewer
- Review status
- Review notes
- Gate references
- Risk review confirmation
- Evaluation review confirmation
- Negative-case review confirmation
- Journal review confirmation
- Paper-only confirmation
- No-live-trading confirmation
- Final status
- Reason
- Statement: Human review does not authorize order sending.
- Statement: Manual Execution Confirmation is still required later.
- Statement: No order was sent.
- Statement: No broker execution readiness was created.
- Statement: Live trading remains unsupported.

## Required Journal Entry

The review journal entry must record:

- Candidate id
- Review id
- Reviewer
- Review status
- Review notes
- Whether paper-only confirmation was present
- Whether no-live-trading confirmation was present
- Whether risk review confirmation was present
- Whether evaluation review confirmation was present
- Whether negative-case review confirmation was present
- Whether journal review confirmation was present
- Final status
- Reason

The journal entry must not contain secrets.

## Success Criteria

Phase 32 is successful only if:

- Valid candidate can enter review queue.
- Human can approve candidate for future Paper Order Request finalization.
- Human can reject candidate.
- Human can request more information.
- Human review cannot send orders.
- Human review cannot create broker readiness.
- Human review cannot replace Manual Execution Confirmation.
- Human review cannot create a finalized Paper Order Request.
- Human review cannot enable execution.
- Live trading remains unsupported.

## Required Tests

Implementation must test:

- Valid candidate can enter review queue.
- `HUMAN_REVIEW_APPROVED_FOR_PAPER_REQUEST` can be recorded.
- `HUMAN_REVIEW_REJECTED` can be recorded.
- `HUMAN_REVIEW_NEEDS_MORE_INFORMATION` can be recorded.
- Missing reviewer blocks.
- Missing paper-only confirmation blocks.
- Missing no-live-trading confirmation blocks.
- Missing risk review confirmation blocks.
- Missing evaluation review confirmation blocks.
- Missing negative-case review confirmation blocks.
- Missing journal review confirmation blocks.
- Candidate status other than `PAPER_ORDER_CANDIDATE_CREATED` blocks.
- Candidate with `broker_execution_allowed=true` blocks.
- Candidate with `live_trading_allowed=true` blocks.
- Candidate missing `human_approval_required=true` blocks.
- Candidate missing `manual_execution_confirmation_required=true` blocks.
- Expired candidate blocks.
- Review artifact is written.
- Journal entry is written.
- No order is sent.
- No broker execution readiness is created.
- No Manual Execution Confirmation is created.
- No finalized Paper Order Request is created.
- No Alpaca API calls exist.
- No live trading exists.
- No batch behavior exists.
- No cancel/replace exists.

## Data Flow

1. Load a Paper Order Request Candidate.
2. Validate candidate safety fields.
3. Validate reviewer and confirmations.
4. Validate review status.
5. Write Human Review Record.
6. Write review journal entry.
7. Stop.

No finalized Paper Order Request, Manual Execution Confirmation, broker readiness, Alpaca call, Paper Send, or live trading action may occur.

## Autonomy Boundary

The Human Review Queue can store and record a human decision.

It cannot:

- Auto-approve a candidate
- Auto-create a finalized Paper Order Request
- Auto-create Manual Execution Confirmation
- Auto-send an order
- Auto-create broker execution readiness
- Auto-enable execution

## What Remains Prohibited

The following remain prohibited:

- Order sending
- Broker execution readiness
- Manual Execution Confirmation
- Auto-approval
- Finalized Paper Order Request creation
- Live trading
- Live endpoints
- Alpaca order API
- Batch orders
- Cancel/replace
- Multi-symbol automation
- Notional increase
- Higher frequency
- Enabling `PAPER_ORDER_EXECUTION_ENABLED`
- Bypassing V4/V5/V6 gates

## Conditions Before Implementation

Before implementation:

- Baseline V6 must remain `PASS`.
- Candidate creation must remain candidate-only.
- Human review must remain artifact-only.
- `PAPER_ORDER_EXECUTION_ENABLED` must remain unset.
- No Alpaca API may be used.
- No finalized Paper Order Request may be created.
- No Manual Execution Confirmation may be created.
- No Paper Send may be performed.
- No credentials may be printed, logged, committed, or written to reports.

## Live Trading Statement

Live trading remains unsupported.
