# Failure Modes

## ADLC Binding
Phase: Testing & Evaluation / Deployment Monitoring.
Control Type: Mandatory operating control.
Block Authority: Yes.

## Operational Control
Known failure modes must be checked during routines, evaluation, and weekly review.

## Critical Failure Modes
- Monolithic agent behavior
- Paper/live boundary confusion
- Stale or hallucinated market data
- Weak liquidity treated as valid
- Timing window ignored
- Risk limit changed without human approval
- Journal omission
- Veto overridden downstream
- PnL used as sole success measure

## Escalation
Critical failures require a memory/failure_reports.md entry and block the current workflow.

## Block Condition
Repeated unresolved critical failures block further paper-trade approvals until reviewed.
