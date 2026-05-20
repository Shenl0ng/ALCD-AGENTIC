# Hallucination Checks

## ADLC Binding
Phase: Testing & Evaluation, Deployment Monitoring.

## Purpose
Detect fabricated data, invented approvals, unsupported market claims, and missing source timestamps.

## Checks
- Data timestamps must be explicit.
- Market structure claims must link to available memory.
- Human approval must not be assumed.
- Risk state must not be invented.
- Missing data must become a block, not a guess.

## Pass Rule
Any unknown required fact must produce a block or explicit uncertainty.

