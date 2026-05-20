# First Controlled Paper Send Report

## Date
2026-05-20T02:04:41Z

## Environment
- Mode: REAL_ALPACA_PAPER_SEND
- Paper execution enabled: True
- Alpaca account mode: PAPER
- Live endpoint rejected: True

## Proposal
- Proposal ID: paper-market_open-001
- Symbol: SIM
- Side: long
- Notional: 100
- Order type: limit
- Time in force: day

## Gates
- Proposal validation: PASS
- Risk approval: RISK_APPROVED
- Human approval: HUMAN_APPROVED_FOR_PAPER_ONLY
- Manual execution confirmation: MANUAL_EXECUTION_CONFIRMED_FOR_PAPER_ONLY
- Journal commit: human_approved_for_paper_only
- Preflight: PAPER_ORDER_SEND_ALLOWED

## Send Result
- Final status: PAPER_ORDER_SUBMITTED
- Alpaca order ID: e9b866d3-0f02-4d33-ba80-4d7a19242533
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
- Execution flag disabled after test: True
- Returned to DRY_RUN_ONLY: True

## Lessons
- What worked: Phase 25 gates completed and paper send path either submitted or safely blocked.
- What failed: none
- What must be fixed before next paper send: Run full V3 gates again; do not increase notional or automate.
