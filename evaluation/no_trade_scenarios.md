# No-Trade Scenarios

## ADLC Binding
Phase: Testing & Evaluation.

## Purpose
Validate that the system rejects weak or incomplete trade conditions.

## Scenarios
- Strong move but no liquidity location
- Liquidity location but mixed higher-timeframe context
- Confirmation before approved timing window
- Good setup after timing window expires
- Valid setup but journal readiness missing

## Pass Rule
Each scenario must end in `NO_TRADE` or `EXECUTION_BLOCKED` with the responsible gate named.

