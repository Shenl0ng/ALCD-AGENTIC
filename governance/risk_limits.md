# Risk Limits

## ADLC Binding
Phase: Scope & Constraints.
Control Type: Mandatory operating control.
Block Authority: Yes.

## Operational Control
Risk is fixed, explicit, and human-owned.

## Default Limits
- Paper trades only
- One active paper-trade idea per symbol unless human-approved
- Every proposal requires invalidation
- Risk must be defined before gatekeeping
- Daily drawdown limit blocks new paper-trade approvals

## Risk Manager Authority
The Risk Manager may approve risk compliance only. It may not approve execution.

## Block Condition
Undefined risk, undefined invalidation, exceeded exposure, or breached daily loss state requires `RISK_REJECTED`.
