# Phase 36 Manual Execution Confirmation Design

## Purpose

Design how a finalized Paper Order Request may receive explicit Manual Execution Confirmation.

This phase is design only.

Manual Execution Confirmation means:

- A human explicitly confirms that this specific finalized Paper Order Request may advance to Paper Send Preflight in a later phase.

Manual Execution Confirmation does not mean:

- Order send
- Broker execution
- Alpaca order placement
- Live trading approval
- Preflight approval by itself
- `PAPER_ORDER_EXECUTION_ENABLED` enablement by itself

This phase must not send orders.
This phase must not enable `PAPER_ORDER_EXECUTION_ENABLED`.
This phase must not use Alpaca API.
This phase must not modify runtime code.
This phase must not add live trading.
This phase must not create `.env` files.
This phase must not print secrets.

## Context

Baseline V8 is `PASS`.

V8 allows:

- Automated dry-run analysis
- Automated Paper Order Request Candidate creation
- Human Review Queue
- Finalized Paper Order Request from human-approved candidate

V8 does not allow:

- Manual Execution Confirmation
- Paper Send Preflight
- Paper Send
- Broker execution readiness
- Live trading

Phase 36 designs the next manual control point after finalized Paper Order Request creation and before any Paper Send Preflight phase.

## Required Flow

1. Load finalized Paper Order Request.
2. Verify `request_status` is `PAPER_ORDER_REQUEST_FINALIZED`.
3. Verify request has not expired.
4. Verify `paper_trading_only=true`.
5. Verify `live_trading_allowed=false`.
6. Verify `broker_execution_allowed=false` before confirmation.
7. Verify `manual_execution_confirmation_required=true`.
8. Verify human review reference exists.
9. Verify journal reference exists.
10. Verify all gate references exist.
11. Create Manual Execution Confirmation record.
12. Write artifact.
13. Write journal entry.
14. Stop.

No order send, Paper Send Preflight, broker readiness, Alpaca call, execution flag enablement, or live trading action may occur in this flow.

## Required Confirmation Fields

Each Manual Execution Confirmation record must include:

- `manual_confirmation_id`
- `paper_order_request_id`
- `candidate_id`
- `review_id`
- `confirmed_at`
- `confirmer`
- `confirmation_status`
- `confirmation_notes`
- `paper_only_confirmation`
- `no_live_trading_confirmation`
- `finalized_request_reviewed`
- `risk_reviewed`
- `order_details_reviewed`
- `notional_limit_confirmation`
- `limit_order_confirmation`
- `day_time_in_force_confirmation`
- `no_short_confirmation`
- `no_crypto_confirmation`
- `no_options_confirmation`
- `no_margin_confirmation`
- `no_extended_hours_confirmation`
- `broker_execution_allowed`
- `live_trading_allowed`
- `paper_send_preflight_required`

## Allowed Confirmation Statuses

Allowed confirmation statuses:

- `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`
- `MANUAL_EXECUTION_REJECTED`
- `MANUAL_EXECUTION_NEEDS_MORE_INFORMATION`
- `MANUAL_EXECUTION_EXPIRED`
- `MANUAL_EXECUTION_INVALID`

No confirmation status may imply order sending, broker execution readiness, Alpaca order placement, live trading approval, or execution flag enablement.

## Required Hardcoded Safety Values

Every Manual Execution Confirmation record must hardcode:

- `broker_execution_allowed=false`
- `live_trading_allowed=false`
- `paper_send_preflight_required=true`

These values must not be user-configurable during Phase 36.

## Hard Blocks

The Manual Execution Confirmation flow must hard-block:

- Missing finalized request
- Request status not `PAPER_ORDER_REQUEST_FINALIZED`
- Request expired
- Missing confirmer
- Missing `paper_only_confirmation`
- Missing `no_live_trading_confirmation`
- Missing `finalized_request_reviewed`
- Missing `risk_reviewed`
- Missing `order_details_reviewed`
- Missing `notional_limit_confirmation`
- Missing `limit_order_confirmation`
- Missing `day_time_in_force_confirmation`
- Missing `no_short_confirmation`
- Missing `no_crypto_confirmation`
- Missing `no_options_confirmation`
- Missing `no_margin_confirmation`
- Missing `no_extended_hours_confirmation`
- Request `paper_trading_only` not true
- Request `live_trading_allowed` true
- Request `broker_execution_allowed` true
- Request `manual_execution_confirmation_required` not true
- `PAPER_ORDER_EXECUTION_ENABLED=true`
- Any order send attempt
- Any broker execution readiness attempt
- Any Alpaca order API call
- Any live trading assumption
- Any live endpoint

## Required Artifact Path

Manual Execution Confirmation artifacts must be written to:

```text
reports/manual_execution_confirmation/<timestamp>/MANUAL_EXECUTION_CONFIRMATION.md
```

## Required Artifact Content

The artifact must include:

- Manual confirmation id
- Paper order request id
- Candidate id
- Review id
- Confirmer
- Confirmation status
- Confirmation notes
- All required confirmations
- `broker_execution_allowed`
- `live_trading_allowed`
- `paper_send_preflight_required`
- Final status
- Reason
- Statement: Manual Execution Confirmation does not send orders.
- Statement: Paper Send Preflight is still required later.
- Statement: No order was sent.
- Statement: No broker execution readiness was created.
- Statement: Live trading remains unsupported.

## Required Journal Entry

The journal entry must record:

- Manual confirmation id
- Paper order request id
- Candidate id
- Review id
- Confirmer
- Confirmation status
- Confirmation notes
- All required confirmations
- Broker execution allowed status
- Live trading allowed status
- Paper Send Preflight required status
- Final status
- Reason

The journal entry must not contain secrets.

## Success Criteria

Phase 36 is successful only if:

- Finalized Paper Order Request can receive manual confirmation.
- Rejected manual confirmation blocks progression.
- Missing confirmations block progression.
- Manual Execution Confirmation cannot send orders.
- Manual Execution Confirmation cannot create broker readiness.
- Manual Execution Confirmation cannot enable `PAPER_ORDER_EXECUTION_ENABLED`.
- Manual Execution Confirmation cannot call Alpaca order API.
- Manual Execution Confirmation cannot bypass Paper Send Preflight.
- Live trading remains unsupported.

## Required Tests

Implementation must test:

- Manual Execution Confirmation model exists.
- Manual confirmation validator exists.
- Finalized Paper Order Request can receive `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`.
- Rejected manual confirmation blocks.
- Needs-more-information manual confirmation blocks.
- Expired request blocks.
- Missing finalized request blocks.
- Request status not `PAPER_ORDER_REQUEST_FINALIZED` blocks.
- Missing confirmer blocks.
- Missing paper-only confirmation blocks.
- Missing no-live-trading confirmation blocks.
- Missing finalized-request-reviewed confirmation blocks.
- Missing risk-reviewed confirmation blocks.
- Missing order-details-reviewed confirmation blocks.
- Missing notional-limit confirmation blocks.
- Missing limit-order confirmation blocks.
- Missing day time-in-force confirmation blocks.
- Missing no-short confirmation blocks.
- Missing no-crypto confirmation blocks.
- Missing no-options confirmation blocks.
- Missing no-margin confirmation blocks.
- Missing no-extended-hours confirmation blocks.
- Request `paper_trading_only=false` blocks.
- Request `live_trading_allowed=true` blocks.
- Request `broker_execution_allowed=true` blocks.
- Request `manual_execution_confirmation_required=false` blocks.
- `PAPER_ORDER_EXECUTION_ENABLED=true` blocks.
- Confirmation hardcodes `broker_execution_allowed=false`.
- Confirmation hardcodes `live_trading_allowed=false`.
- Confirmation hardcodes `paper_send_preflight_required=true`.
- Artifact is written.
- Journal entry is written.
- No order is sent.
- No broker execution readiness is created.
- No Alpaca order API call exists.
- No live trading exists.
- No batch behavior exists.
- No cancel/replace exists.

## Data Flow

1. Finalized Paper Order Request enters manual confirmation flow.
2. Validator checks request status, request safety values, references, expiration, confirmer, confirmations, and execution flag state.
3. Manual Execution Confirmation record is created only if all checks pass.
4. Journal entry is written.
5. Flow stops.

No Paper Send Preflight, order send, broker readiness, Alpaca call, execution flag enablement, or live trading action may be created.

## What Remains Prohibited

The following remain prohibited:

- Order sending
- Paper Send Preflight
- Broker execution readiness
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
- Bypassing V4/V5/V6/V7/V8 gates
- Bypassing finalized request validation
- Bypassing Paper Send Preflight

## Conditions Before Implementation

Before implementation:

- Baseline V8 must remain `PASS`.
- Finalized Paper Order Request flow must remain `PASS`.
- `PAPER_ORDER_EXECUTION_ENABLED` must remain unset.
- No Alpaca API may be used.
- No Paper Send Preflight may be created.
- No Paper Send may be performed.
- No broker execution readiness may be created.
- No credentials may be printed, logged, committed, or written to reports.

## Live Trading Statement

Live trading remains unsupported.
