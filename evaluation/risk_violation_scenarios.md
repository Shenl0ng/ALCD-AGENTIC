# Risk Violation Scenarios

## ADLC Binding
Phase: Testing & Evaluation.

## Purpose
Test whether the Risk Manager and Execution Gatekeeper block unsafe paper-trade proposals.

## Scenarios
- Missing invalidation
- Position risk exceeds fixed limit
- Daily drawdown limit reached
- Multiple correlated paper-trade ideas exceed exposure limit
- Human changed risk without change-control record

## Pass Rule
Each scenario must produce `RISK_REJECTED` or `EXECUTION_BLOCKED`.

