# Simulated Paper Trade Proposal

This is an internal paper-only proposal fixture. It is not executable.

Paper Mode: REQUIRED

```json
{
  "proposal_id": "paper-market_open-001",
  "created_at": "2026-05-19T13:31:00+00:00",
  "routine_name": "market_open",
  "symbol": "SIM",
  "direction": "long",
  "setup_type": "liquidity_reclaim",
  "timeframe_context": "higher-timeframe context aligned",
  "liquidity_location": "prior session low reclaim",
  "session_timing": "market_open",
  "entry_confirmation": "deterministic confirmation fixture",
  "proposed_entry": "100",
  "invalidation_level": "98",
  "stop_loss": "98",
  "target_1": "104",
  "target_2": "106",
  "risk_per_share": "2",
  "proposed_position_size": "100",
  "max_loss_amount": "200",
  "max_loss_pct_equity": "0.002",
  "expected_reward_risk": "2",
  "thesis": "Paper-only setup fixture with context, liquidity, timing, and confirmation aligned.",
  "why_now": "All deterministic specialist outputs passed before proposal creation.",
  "why_this_level": "The level is the deterministic liquidity fixture.",
  "what_invalidates_trade": "A move through the invalidation level invalidates the idea.",
  "paper_trading_only": true,
  "human_approval_required": true,
  "source_agent_outputs": {
    "Market Context Agent": "PASS",
    "Liquidity Agent": "PASS",
    "Session Timing Agent": "PASS",
    "Confirmation Agent": "PASS"
  },
  "adlc_compliance_status": "PASS",
  "journal_ready": true
}
```
