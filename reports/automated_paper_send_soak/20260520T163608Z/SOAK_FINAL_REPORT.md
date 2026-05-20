# Soak Final Report

- Soak period: Accelerated Soak Run 1 Retry
- Number of attempted runs: 1
- Number of submitted paper orders: 1
- Number of blocked runs: 0
- Reconciliation results: ["RECONCILIATION_MATCHED"]
- Post-mortem results: ["PASS"]
- Daily order limit compliance: True
- Daily notional compliance: True
- daily notional limit not exceeded
- Cooldown compliance: True
- accelerated cooldown satisfied, 60 seconds
- Kill switch events: False
- Unresolved issues: False
- Approval-rate analysis: 1
- No-trade/rejection analysis: 0
- Journal quality analysis: acceptable
- Safety violations: []
- Recommendation: CONTINUE_SOAK
- Real Alpaca API called: true (Alpaca paper endpoint only)
- Real order sent: false
- Alpaca paper order sent: true
- Alpaca paper order id: f600c8a6-834e-4cc4-b529-89ffbfbadd86
- PASS, 746 tests
- Soak framework PASS
- Accelerated cooldown PASS
- .env.local flags restored to false
- accelerated_mode_enabled: True
- configured_cooldown_seconds: 60
- production_default_cooldown_seconds: 86400
- accelerated_mode_reason: accelerated soak run 1 retry
- alpaca_paper_confirmed: True
- live_endpoint_rejected: True
- live_trading_unsupported: True
- production_cooldown_remains_default: True
- does_not_authorize_frequency_increase: True
- does_not_authorize_live_trading: True

Accelerated cooldown was used for paper soak framework validation only.
Production/default cooldown remains 24 hours.
Live trading remains unsupported.
Increasing notional remains prohibited.
Multi-symbol automation remains prohibited.
Batch orders remain prohibited.
Cancel/replace remains prohibited.
Higher frequency outside accelerated paper soak test mode remains prohibited.
