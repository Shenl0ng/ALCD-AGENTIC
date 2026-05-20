# Watchlist

## ADLC Binding
Phase: Preparation & Monitoring.

## Purpose
Tracks symbols eligible for observation during routines.

## Required Fields
- Symbol
- Reason for watchlist inclusion
- Required context condition
- Required liquidity condition
- Expiration or review date

## Control Rule
Watchlist inclusion is not a trade proposal.

## Approved Symbols

- Symbol: AAPL
  approval_status: approved
  mode: paper_only
  max_notional_usd: 100
  one_symbol_only: true
  live_trading_allowed: false
  market_scanning_allowed: false
  auto_selection_allowed: false
  human_review_required: true
  manual_confirmation_required: true
  preflight_required: true
  notes: Approved for Baseline V15 paper-only operational testing.
