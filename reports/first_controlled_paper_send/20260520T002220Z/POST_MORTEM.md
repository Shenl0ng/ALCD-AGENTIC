# Phase 16 Evaluation-Gated Regression Post-Mortem

## Summary

One controlled Alpaca paper send regression was attempted after the Phase 15 Evaluation-First Gate. The send status was `PAPER_ORDER_SUBMITTED` and reconciliation status was `RECONCILIATION_MATCHED`.

## Source Report

/Users/illium/Movies/CODE/ALCD-AGENTIC/reports/first_controlled_paper_send/20260520T002220Z/FIRST_CONTROLLED_PAPER_SEND_REPORT.md

## What Passed

- Proposal validation: `PASS`
- Strategy Evaluation: `PASS`
- Evaluation-First Gate: `EVALUATION_GATE_PASSED`
- Risk Manager: `RISK_APPROVED`
- Human Approval: `HUMAN_APPROVED_FOR_PAPER_ONLY`
- Manual Execution Confirmation: `MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY`
- Preflight: `PAPER_ORDER_SEND_ALLOWED`

## What Was Submitted

- Broker: Alpaca paper
- Symbol: `SIM`
- Side: `buy`
- Quantity: `1`
- Order type: `limit`
- Time in force: `day`
- Limit price: `100`

## Alpaca Paper Order ID

6c94d173-1173-480f-9003-dcd16e3553b7

## Reconciliation Result

RECONCILIATION_MATCHED

## Mismatches

None recorded

## Safety Gates

The Evaluation-First Gate was required before Human Approval, Paper Order Request creation, and Paper Send. No follow-up order, cancel/replace, live trading, batch order, automation, or live endpoint was used.

## Secrets

Secrets were protected. Secret values were not printed in this workflow output or written to artifacts by this script.

## Execution Flag

`PAPER_ORDER_EXECUTION_ENABLED` was unset inside the workflow subprocess after the send. The parent shell must still be unset manually.

## DRY_RUN_ONLY

The workflow returned to `DRY_RUN_ONLY` configuration after the send attempt.

## Another Paper Send Allowed Now

No. Another paper send requires a new manual run, full pre-send checks, and review of this post-mortem.

## Required Changes Before Next Paper Send

Review generated artifacts and unset `PAPER_ORDER_EXECUTION_ENABLED` in the parent shell.

## Recommendation

HOLD
