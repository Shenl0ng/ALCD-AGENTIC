# No-Trade Rules

## ADLC Binding
Phase: Scope & Constraints.

## Default Decision
The default decision is `NO_TRADE`.

## Mandatory No-Trade Conditions
- Market data is stale, missing, or contradictory.
- Higher-timeframe context is mixed.
- Price is not at a strong liquidity location.
- Session or timing window is invalid.
- Confirmation is absent, late, or overcomplicated.
- Invalidation is undefined.
- Risk exceeds fixed limits.
- Daily risk state blocks new trades.
- Human approval is required but missing.
- Journal readiness is missing.
- Any live-trading implication appears.

## Control Rule
A no-trade decision is a successful control outcome when it prevents low-quality or unsafe action.

