# Phase 38 Paper Send Preflight Design

## 1. Purpose

Design Paper Send Preflight.

Paper Send Preflight determines whether a manually confirmed finalized Paper Order Request is eligible to be sent in a later controlled paper send phase.

Preflight does not send orders.
Preflight does not call Alpaca order API.
Preflight does not create broker execution readiness.
Preflight does not enable `PAPER_ORDER_EXECUTION_ENABLED`.
Preflight does not authorize live trading.

This phase is design only.

## 2. Context

Baseline V9 is `PASS`.

V9 allows:

- Automated dry-run analysis
- Paper Order Request Candidate
- Human Review Queue
- Finalized Paper Order Request
- Manual Execution Confirmation

V9 does not allow:

- Paper Send Preflight
- Paper Send
- Broker execution readiness
- Live trading

## 3. Scope

Paper Send Preflight is a deterministic, local eligibility check for a manually confirmed finalized Paper Order Request.

The preflight result may be used by a later controlled paper send phase, but it is not itself an order, order submission, broker instruction, Alpaca request, execution flag enablement, or live trading approval.

## 4. Required Flow

1. Load finalized Paper Order Request.
2. Load Manual Execution Confirmation.
3. Verify `request_status` is `PAPER_ORDER_REQUEST_FINALIZED`.
4. Verify `confirmation_status` is `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`.
5. Verify `paper_trading_only=true`.
6. Verify `live_trading_allowed=false`.
7. Verify `broker_execution_allowed=false` before preflight.
8. Verify `paper_send_preflight_required=true`.
9. Verify all confirmations are present.
10. Verify max notional `<= 100 USD`.
11. Verify order type is limit.
12. Verify time in force is day.
13. Verify no short selling.
14. Verify no crypto.
15. Verify no options.
16. Verify no margin/leverage.
17. Verify no extended hours.
18. Verify one order only.
19. Verify no batch behavior.
20. Verify no cancel/replace.
21. Verify paper account mode can be confirmed read-only if available.
22. Verify live endpoint is rejected if configuration is available.
23. Produce preflight result.
24. Write artifact.
25. Write journal entry.
26. Stop.

No order send, Alpaca order API call, broker execution readiness, execution flag enablement, live endpoint usage, or live trading action may occur in this flow.

## 5. Allowed Preflight Statuses

Allowed preflight statuses:

- `PAPER_ORDER_SEND_ALLOWED`
- `PAPER_ORDER_SEND_BLOCKED`
- `PAPER_ORDER_SEND_INVALID`
- `PAPER_ORDER_SEND_EXPIRED`

`PAPER_ORDER_SEND_ALLOWED` is not broker execution.
`PAPER_ORDER_SEND_ALLOWED` is not order submission.
`PAPER_ORDER_SEND_ALLOWED` does not call Alpaca.
`PAPER_ORDER_SEND_ALLOWED` does not enable `PAPER_ORDER_EXECUTION_ENABLED`.
`PAPER_ORDER_SEND_ALLOWED` only means the request may be considered by a later controlled paper send phase.

## 6. Required Preflight Fields

Each Paper Send Preflight record must include:

- `preflight_id`
- `paper_order_request_id`
- `manual_confirmation_id`
- `checked_at`
- `preflight_status`
- `paper_trading_only`
- `account_mode_checked`
- `live_endpoint_rejected`
- `max_notional_check`
- `order_type_check`
- `time_in_force_check`
- `no_short_check`
- `no_crypto_check`
- `no_options_check`
- `no_margin_check`
- `no_extended_hours_check`
- `one_order_only_check`
- `no_batch_check`
- `no_cancel_replace_check`
- `broker_execution_allowed`
- `live_trading_allowed`
- `failure_reasons`
- `final_status`

## 7. Required Hardcoded Safety Values

Every Paper Send Preflight result must hardcode:

- `broker_execution_allowed=false`
- `live_trading_allowed=false`

These values must not be configurable during Phase 38.

## 8. Hard Blocks

Paper Send Preflight must hard-block:

- Missing finalized request
- Missing manual confirmation
- Request status not `PAPER_ORDER_REQUEST_FINALIZED`
- Confirmation status not `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_PREFLIGHT`
- `paper_trading_only` not true
- `live_trading_allowed` true
- `broker_execution_allowed` true
- `paper_send_preflight_required` not true
- Missing required confirmation
- Notional `> 100 USD`
- Order type not limit
- Time in force not day
- Short selling
- Crypto
- Options
- Margin/leverage
- Extended hours
- More than one order
- Batch behavior
- Cancel/replace behavior
- `PAPER_ORDER_EXECUTION_ENABLED=true`
- Alpaca order API call
- Order send attempt
- Broker execution readiness attempt
- Live trading assumption
- Live endpoint

## 9. Required Artifact Path

Paper Send Preflight artifacts must be written to:

```text
reports/paper_send_preflight/<timestamp>/PAPER_SEND_PREFLIGHT.md
```

## 10. Required Artifact Content

The artifact must include:

- Preflight id
- Paper order request id
- Manual confirmation id
- Preflight status
- All checks
- Failure reasons
- `broker_execution_allowed`
- `live_trading_allowed`
- Final status
- Reason
- Statement: Paper Send Preflight does not send orders.
- Statement: `PAPER_ORDER_SEND_ALLOWED` is not broker execution.
- Statement: `PAPER_ORDER_SEND_ALLOWED` does not call Alpaca.
- Statement: `PAPER_ORDER_EXECUTION_ENABLED` was not enabled.
- Statement: No order was sent.
- Statement: No broker execution readiness was created.
- Statement: Live trading remains unsupported.

## 11. Required Journal Entry

The journal entry must record:

- Preflight id
- Paper order request id
- Manual confirmation id
- Preflight status
- All check results
- Failure reasons
- Broker execution allowed status
- Live trading allowed status
- Final status
- Reason

The journal entry must not contain secrets.

## 12. Success Criteria

Phase 38 is successful only if:

- Valid manually confirmed finalized request can produce `PAPER_ORDER_SEND_ALLOWED`.
- Invalid request produces `PAPER_ORDER_SEND_BLOCKED` or `PAPER_ORDER_SEND_INVALID`.
- Expired request or confirmation produces `PAPER_ORDER_SEND_EXPIRED`.
- Preflight cannot send orders.
- Preflight cannot create broker readiness.
- Preflight cannot enable execution.
- Preflight cannot call Alpaca order API.
- Preflight cannot authorize live trading.
- Live trading remains unsupported.

## 13. Failure Modes

Expected failure modes:

- Missing finalized request blocks preflight.
- Missing Manual Execution Confirmation blocks preflight.
- Failed request or confirmation status blocks preflight.
- Missing required confirmation blocks preflight.
- Notional above `100 USD` blocks preflight.
- Non-limit order blocks preflight.
- Non-day time in force blocks preflight.
- Short, crypto, options, margin, leverage, or extended-hours assumptions block preflight.
- Multiple orders, batch behavior, or cancel/replace assumptions block preflight.
- `PAPER_ORDER_EXECUTION_ENABLED=true` blocks preflight.
- Any live endpoint or live trading assumption blocks preflight.

## 14. What Remains Prohibited

The following remain prohibited:

- Order sending
- Broker execution readiness
- Alpaca order API
- Auto-send
- Live trading
- Live endpoints
- Batch orders
- Cancel/replace
- Multi-symbol automation
- Notional increase
- Higher frequency
- Enabling `PAPER_ORDER_EXECUTION_ENABLED`
- Bypassing V4/V5/V6/V7/V8/V9 gates
- Bypassing finalized Paper Order Request validation
- Bypassing Manual Execution Confirmation validation
- Bypassing Paper Send Preflight

## 15. Conditions Before Implementation

Before implementation:

- Baseline V9 must remain `PASS`.
- Manual Execution Confirmation must remain `PASS`.
- `PAPER_ORDER_EXECUTION_ENABLED` must remain unset.
- No Alpaca order API may be used.
- No Paper Send may be performed.
- No broker execution readiness may be created.
- No live endpoint may be used.
- No live trading may be supported.
- No credentials may be printed, logged, committed, or written to reports.

## 16. Live Trading Statement

Live trading remains unsupported.
