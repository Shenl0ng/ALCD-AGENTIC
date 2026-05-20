# Soak Daily Limits

- Daily order counter: 1
- Submitted paper orders in registry: 1
- Daily notional tracker: 100
- Cooldown tracker: True
- accelerated_mode_enabled: True
- configured_cooldown_seconds: 60
- production_default_cooldown_seconds: 86400
- Kill switch status: inactive
- Daily order limit compliance: True
- Daily notional compliance: True
- daily notional limit not exceeded
- Cooldown compliance: True
- accelerated cooldown satisfied, 60 seconds
- Any daily limit violation: False
- PASS, 746 tests
- Soak framework PASS
- Accelerated cooldown PASS
- .env.local flags restored to false

Production/default cooldown remains 24 hours.
Live trading remains unsupported.
Higher frequency outside accelerated paper soak test mode remains prohibited.
