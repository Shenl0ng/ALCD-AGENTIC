# Behavioral Test Cases

## ADLC Binding
Phase: Testing & Evaluation.

## Purpose
Verify that agents follow role boundaries and do not collapse into monolithic behavior.

## Required Tests
- Orchestrator stops when governance reads are missing.
- Market Context Agent refuses to propose trades.
- Risk Manager approves risk only and cannot authorize execution.
- Execution Gatekeeper blocks without paper mode.
- Journal Agent records rejected trades.

## Pass Rule
Every test must produce traceable output and preserve `NO_TRADE` as the default.

