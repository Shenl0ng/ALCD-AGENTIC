# Phase 19 Approval Selectivity Tightening Design

## 1. Purpose

Phase 19 designs stricter approval selectivity rules.

The goal is to approve fewer trades, reject weak setups more explicitly, and improve no-trade discipline before any future frequency increase is considered.

This phase is design only. It does not send orders, enable `PAPER_ORDER_EXECUTION_ENABLED`, use Alpaca, modify execution logic, increase notional, add automation, create `.env` files, or authorize live trading.

## 2. Why This Phase Is Needed

The latest Offline Strategy Quality Review completed with:

- Review status: `REVIEW_COMPLETE`
- Recommendation: `CONTINUE_MANUAL_LIMITED_PAPER`
- Red flag detected: `too many approvals`
- Increasing notional allowed: no
- Automation allowed: no

The system has proven controlled paper execution and evaluation-gated sequencing, but the review identified selectivity drift. Before any scope expansion, the system must become harder to approve and better at rejecting mediocre setups.

## 3. Source Report Path

`reports/offline_strategy_quality_review/20260520T003717Z/OFFLINE_STRATEGY_QUALITY_REVIEW.md`

## 4. Red Flag Addressed

Red flag addressed: `too many approvals`.

This phase treats excessive approval rate as a strategy quality issue, not an execution issue.

## 5. Required Changes To Approval Criteria

A proposal may pass only if:

- Higher-timeframe context is specific, not generic.
- Liquidity location is specific, named, and price-relevant.
- Confirmation is observable and not vague.
- Risk is fixed before approval.
- Reward/risk is acceptable.
- Journal thesis is specific.
- At least one credible invalidation reason is present.
- Data integrity is `PASS`.
- Evaluation-First Gate is `PASS`.
- No specialist agent rubber-stamping is detected.
- No human approval rubber-stamping is detected.

Additional approval constraints:

- The thesis must be symbol-specific or level-specific.
- Liquidity reasoning must name the relevant level, sweep, reclaim, imbalance, or prior range reference.
- Confirmation must describe observable price behavior, not sentiment or confidence.
- Approval must include a reason why no-trade was rejected as the better option.
- Approval must preserve manual paper-only execution.

## 6. Required Changes To Rejection Criteria

The system must reject when:

- Liquidity is vague.
- Confirmation is vague.
- Context is generic.
- Thesis could apply to any symbol.
- Risk is valid but setup quality is weak.
- Approval language is repetitive.
- Agents do not independently challenge the setup.
- No-trade would be the better decision.

Additional rejection triggers:

- Higher-timeframe context is only directional bias without a specific market structure reason.
- Liquidity location lacks a clear price reference.
- Confirmation appears before price reaches the relevant location.
- Journal text repeats prior templates without new reasoning.
- Risk Manager approves without meaningful challenge.
- Human Approval repeats automated scoring without independent review.

## 7. Required Changes To No-Trade Criteria

The system must explicitly reward:

- Waiting.
- Rejecting mediocre setups.
- Blocking over-approved flows.
- Preserving capital.
- Identifying unclear context.
- Identifying insufficient liquidity quality.

No-trade should be the default when:

- Liquidity quality is acceptable but not strong.
- Confirmation is technically present but weak.
- Context is plausible but generic.
- Journal reasoning is thin.
- Approval rate is above warning threshold.
- Agents did not produce differentiated reasoning.

## 8. Required Changes To Scoring Thresholds

Threshold direction:

- Raise minimum evaluation score.
- Require stronger liquidity score.
- Require stronger confirmation score.
- Require stronger journal quality score.
- Add approval/rejection ratio monitoring.
- Add approval-rate warning threshold.
- Add approval-rate hard block threshold.

Proposed threshold design for implementation:

- Overall evaluation score must exceed the current pass threshold.
- Liquidity location quality must score maximum or near-maximum.
- Entry confirmation quality must score maximum or near-maximum.
- Journal readiness and journal quality must score maximum for approval.
- Approval/rejection ratio above warning threshold triggers manual review.
- Approval/rejection ratio above hard block threshold prevents additional approvals until offline review clears the issue.

## 9. Required Changes To Journal Requirements

Journal entries must include:

- Specific higher-timeframe context.
- Specific liquidity level or location.
- Observable confirmation.
- Fixed risk.
- Reward/risk.
- Invalidation reason.
- Why this trade is better than no-trade.
- Which agents challenged the setup.
- Whether approval-rate warning or hard block thresholds were active.
- Whether any rubber-stamping signal was detected.

Generic journal language must lower journal quality score and may block approval.

## 10. Required Changes To Evaluation-Gate Blocking Rules

The Evaluation-First Gate must block when:

- Liquidity language is vague.
- Confirmation language is vague.
- Higher-timeframe context is generic.
- Journal thesis could apply to any symbol.
- Evaluation score is below the tightened threshold.
- Liquidity score is below the tightened threshold.
- Confirmation score is below the tightened threshold.
- Journal quality score is below the tightened threshold.
- Agent rubber-stamping is detected.
- Human approval rubber-stamping is detected.
- Approval-rate hard block threshold is active.

The gate should warn, but not necessarily hard-block, when:

- Approval-rate warning threshold is active.
- Rejection count is lower than expected.
- No-trade count is lower than expected.
- Journal language is specific but thin.

## 11. Required Changes To Human Approval Review

Human Approval must become more adversarial.

The reviewer must confirm:

- Why this setup deserves approval instead of no-trade.
- Which specific evidence supports the liquidity location.
- Which observable behavior confirms entry.
- What invalidates the setup.
- Whether the journal is specific enough for post-mortem review.
- Whether any agent appears to rubber-stamp.
- Whether the recent approval rate is too high.

Human Approval must reject if:

- The reviewer cannot explain why no-trade is worse.
- The reviewer only repeats the Evaluation-First Gate output.
- The reviewer does not challenge the setup.
- The approval language is generic.

## 12. Required Changes To Weekly/Offline Review

Weekly/offline review must track:

- Approval count.
- Rejection count.
- No-trade count.
- Approval/rejection ratio.
- Approval/no-trade ratio.
- Number of hard blocks from selectivity rules.
- Number of soft warnings from selectivity rules.
- Repeated journal phrases.
- Repeated approval phrases.
- Agent-specific reasoning quality.
- Human approval challenge quality.

Review outcome must remain `HOLD` or `CONTINUE_MANUAL_LIMITED_PAPER` while approval-rate red flags remain unresolved.

## 13. New Hard-Fail Conditions

New hard-fail conditions:

- Generic higher-timeframe context.
- Vague liquidity location.
- Vague confirmation.
- Generic thesis that could apply to any symbol.
- Missing credible invalidation reason.
- Agent rubber-stamping detected.
- Human approval rubber-stamping detected.
- Approval-rate hard block threshold active.
- Risk approval without meaningful challenge when setup quality is weak.
- No-trade is clearly better than approval.

## 14. New Soft-Warning Conditions

New soft-warning conditions:

- Approval-rate warning threshold active.
- Rejection count below expected level.
- No-trade count below expected level.
- Liquidity reasoning specific but not strong.
- Confirmation observable but not decisive.
- Journal specific but thin.
- Human approval challenges the setup but weakly.
- Agents disagree only superficially.

Soft warnings require review before the next paper send series.

## 15. Required Test Scenarios

Implementation must test:

- Generic higher-timeframe context blocks approval.
- Vague liquidity blocks approval.
- Vague confirmation blocks approval.
- Generic thesis blocks approval.
- Missing invalidation blocks approval.
- Valid risk but weak setup blocks approval.
- Repetitive approval language blocks approval.
- Agent rubber-stamping blocks approval.
- Human approval rubber-stamping blocks approval.
- No-trade better than approval blocks approval.
- Waiting is rewarded.
- Rejecting mediocre setup is rewarded.
- Approval-rate warning threshold produces warning.
- Approval-rate hard block threshold blocks approval.
- Approval/rejection ratio is calculated.
- No-trade count is included in selectivity review.
- Tightened thresholds prevent over-approval.
- No order is sent.
- No Alpaca calls occur.
- No execution flag is enabled.
- No automation is added.
- No notional increase is recommended.
- No LLM calls occur.

## 16. What Remains Allowed

The system may still:

- Run architecture validation.
- Run deterministic tests.
- Run Strategy Evaluation.
- Run Evaluation-First Gate checks.
- Run offline strategy quality review.
- Run dry-run flow.
- Run mocked paper send.
- Run another manual limited paper send only if all existing V2 gates and future selectivity rules pass.
- Generate reports and post-mortems from real artifacts.
- Continue manual limited paper review.
- Plan the next design phase.

## 17. What Remains Prohibited

The following remain prohibited:

- Increasing notional.
- Automation.
- Live trading.
- Live endpoints.
- Batch orders.
- Cancel/replace.
- Higher frequency.
- Market orders.
- Short selling.
- Crypto.
- Options.
- Margin or leverage.
- Extended-hours trading.
- Autonomous follow-up trades.
- Bypassing Strategy Evaluation.
- Bypassing Evaluation-First Gate.
- Bypassing Risk Manager.
- Bypassing Human Approval.
- Bypassing Manual Execution Confirmation.
- Bypassing Journal Agent.
- Bypassing Execution Gatekeeper.
- Committing credentials.
- Creating `.env` files with real values.
- LLM API calls.

This design does not recommend increasing notional, automation, live trading, batch orders, cancel/replace, or higher frequency.

## 18. Conditions Before Implementation

Before implementation:

- This design must pass audit.
- The current offline review red flag must remain visible.
- Current V2 execution safety controls must remain unchanged.
- The implementation must be deterministic.
- Tests must prove stricter approval criteria block weak setups.
- Tests must prove no-trade and rejection quality are rewarded.
- Tests must prove approval-rate warning and hard-block thresholds work.
- Tests must prove no Alpaca calls occur.
- Tests must prove no order sends occur.
- Tests must prove no execution logic is weakened.
- Tests must prove no automation is added.
- Tests must prove no notional increase is recommended.

## 19. Live Trading Remains Unsupported

Live trading remains unsupported.

Phase 19 only designs approval selectivity tightening for manual limited paper trading. It does not authorize live trading, live endpoints, automation, increased notional, batch orders, cancel/replace, or higher frequency.
