# Paper Trading Only

## ADLC Binding
Phase: Scope & Constraints.
Control Type: Mandatory operating control.
Block Authority: Yes.

## Operational Control
The system may only evaluate and record paper-trade decisions. It must not connect to, instruct, or simulate through a live broker.

## Required Label
Every proposal and approval must state `Paper Mode: REQUIRED`.

## Prohibited Activity
- Broker API connection
- Live order placement
- Credential creation
- Environment variable setup
- Automated position management

## Block Condition
If paper mode is absent or ambiguous, execution gate status must be `EXECUTION_BLOCKED`.

Execution gate status must also be `EXECUTION_BLOCKED` when risk approval, journal readiness, or required human approval is missing.
