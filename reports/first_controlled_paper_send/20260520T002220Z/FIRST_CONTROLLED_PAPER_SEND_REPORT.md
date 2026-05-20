# First Controlled Paper Send Report

## Date
missing from artifact

## Environment
- Mode: REAL_ALPACA_PAPER_SEND
- Paper execution enabled: True
- Alpaca account mode: PAPER
- Live endpoint rejected: True

## Proposal
- Proposal ID: missing from artifact
- Symbol: missing from artifact
- Side: missing from artifact
- Notional: missing from artifact
- Order type: missing from artifact
- Time in force: missing from artifact

## Gates
- Proposal validation: PASS
- Risk approval: RISK_APPROVED
- Human approval: HUMAN_APPROVED_FOR_PAPER_ONLY
- Manual execution confirmation: MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY
- Journal commit: human_approved_for_paper_only
- Preflight: PAPER_ORDER_SEND_ALLOWED

## Send Result
- Final status: PAPER_ORDER_SUBMITTED
- Alpaca order ID: 6c94d173-1173-480f-9003-dcd16e3553b7
- Broker status: accepted

## Reconciliation
- Reconciliation status: RECONCILIATION_MATCHED
- Mismatches: none
- Account state checked: True
- Position state checked: True

## Journal
- Pre-send journal entry: human_approved_for_paper_only
- Post-send journal entry: paper_order_send_submitted
- Reconciliation journal entry: paper_order_reconciliation

## Safety
- Follow-up orders created: False
- Cancel/replace used: False
- Live trading touched: False
- Execution flag disabled after test: subshell_unset; unset parent shell manually
- Returned to DRY_RUN_ONLY: True

## Lessons
- What worked: phase 16 evaluation-gated regression completed through send attempt and artifact writing
- What failed: none recorded in workflow artifact
- What must be fixed before next paper send: review artifacts before any next paper send; unset parent PAPER_ORDER_EXECUTION_ENABLED
