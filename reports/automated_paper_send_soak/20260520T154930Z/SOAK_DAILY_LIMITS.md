# Soak Daily Limits

## Soak Run 1 Limit Status

- Attempted run: yes
- Submitted paper orders for this attempt: 0
- Real order sent: no
- Daily order limit status: not exceeded
- Daily notional used by this attempt: 0
- Daily notional limit status: not exceeded
- Cooldown status: not satisfied
- Failed gate: cooldown satisfied
- Block reason: 24-hour cooldown not satisfied
- Previous automated paper send: 2026-05-20T13:42:19Z
- Minimum cooldown required by Phase 52: 24 hours
- Expected safety behavior: true
- Kill switch status: inactive
- Batch/cancel/replace attempt: no
- Live endpoint detected: no
- Secret exposure: no
- `.env.local` PAPER_ORDER_EXECUTION_ENABLED restored to false: true
- `.env.local` PAPER_AUTOMATED_SEND_ENABLED restored to false: true

The cooldown safety control worked. Soak Run 1 was blocked before send.

Live trading remains unsupported.
Increasing notional remains prohibited.
Multi-symbol automation remains prohibited.
Batch orders remain prohibited.
Cancel/replace remains prohibited.
