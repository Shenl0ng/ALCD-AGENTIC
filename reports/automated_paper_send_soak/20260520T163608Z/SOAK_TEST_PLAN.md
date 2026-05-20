# Soak Test Plan

- Soak period: Accelerated Soak Run 1 Retry
- Maximum submitted paper orders per day: 1
- Maximum notional per day: <= 100 USD
- Cooldown rule: production/default cooldown remains 24 hours unless explicit paper-only accelerated soak mode is validated
- accelerated_mode_enabled: True
- configured_cooldown_seconds: 60
- production_default_cooldown_seconds: 86400
- accelerated_mode_reason: accelerated soak run 1 retry
- Kill switch rule: active kill switch blocks all runs
- Required V13 gates: all gates must pass before every run
- Required artifacts per run: registry, daily limits, quality review, final report
- Stop conditions: reconciliation mismatch, missing reconciliation, missing post-mortem, blocker, kill switch, secret exposure, live endpoint, daily limit, cooldown, batch/cancel/replace, quality red flags, failed V13 gate
- Success criteria: all submitted paper orders reconcile matched, every send has post-mortem, no unresolved issues, no live endpoint, no secrets printed
- Review cadence: after every attempted run and at end of soak

Accelerated cooldown was used for paper soak framework validation only.
Production/default cooldown remains 24 hours.
Live trading remains unsupported.
