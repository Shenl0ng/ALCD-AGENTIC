# Selective Execution System

## ADLC Binding
Phase: Architecture Design and Simulation & Proof of Value.

## Core Rule
The strategy is selective by default. A trade candidate exists only when all required gates pass. Any missing gate returns `NO_TRADE`.

## Required Gates
1. Data integrity is acceptable.
2. Higher-timeframe context is clear.
3. Price is at a strong liquidity location.
4. The session and timing window are valid.
5. Simple confirmation appears after location is reached.
6. Invalidation is explicit.
7. Fixed risk is within limits.
8. Journal entry can be prepared before paper-trade authorization.
9. Human approval rules are satisfied.

## Veto Logic
Every specialist gate has independent veto authority. A downstream agent may not revive a rejected setup.

## Paper-Only Execution Standard
`PAPER_TRADE_ALLOWED` is an architecture status, not broker execution. It means the system has permission to record an approved paper trade in memory.

