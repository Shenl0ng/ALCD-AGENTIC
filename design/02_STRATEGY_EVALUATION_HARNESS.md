# Phase 12 Strategy Evaluation Harness Design

## 1. Purpose

Phase 12 defines a strategy evaluation harness for scoring trade proposal quality before any future controlled paper sends are allowed.

The harness evaluates whether the multi-agent decision system is selecting well, rejecting weak setups correctly, preserving risk controls, and journaling decisions with enough clarity for review.

The harness is a design phase only. It does not change execution behavior, increase notional, add automation, add Alpaca behavior, or authorize live trading.

## 2. Why Phase 12 Comes After Repeatability

Phase 11 proved the existing controlled paper-send path is repeatable under strict safety gates. Three controlled paper sends submitted and reconciled as matched, but Phase 11 did not prove that future trade ideas are high quality.

Phase 12 comes next because the next risk is not mechanical execution. The next risk is poor selection: forced trades, weak liquidity, vague confirmation, missing risk definition, or excessive confidence.

Before any future sends, the system must prove it can score proposal quality and reward correct no-trade behavior.

## 3. Inputs

The harness uses only existing paper-mode and architecture artifacts:

- Trade proposal records.
- Specialist-agent outputs from Market Context, Liquidity, Session Timing, and Confirmation agents.
- Data Integrity Agent output.
- Risk Manager output.
- Human approval records.
- Journal entries.
- Failure auditor notes.
- Weekly review notes.
- No-trade scenarios.
- Risk violation scenarios.
- Paper trading scorecards.
- Phase 11 repeatability summary.

No Alpaca API access is required for Phase 12 design.

## 4. Outputs

The harness must produce:

- Strategy evaluation report.
- Per-proposal scorecard.
- No-trade quality score.
- Rejection quality score.
- Setup quality score.
- Risk quality score.
- Journal quality score.
- ADLC compliance score.
- Data integrity score.
- Human approval quality review.
- Final recommendation: `PASS`, `FAIL`, or `NEEDS_REVIEW`.
- Explicit block reasons for failed proposals.

## 5. Evaluation Dimensions

The required evaluation dimensions are:

- Higher-timeframe context quality.
- Liquidity location quality.
- Session/timing quality.
- Entry confirmation quality.
- Fixed risk quality.
- Reward/risk quality.
- Journal readiness.
- Data freshness.
- Data completeness.
- Specialist-agent sequencing.
- Risk Manager decision quality.
- No-trade discipline.
- Whether the system rejected weak setups correctly.

## 6. Required Scoring Rubric

Each dimension is scored from `0` to `3`.

- `0`: Missing, unsafe, vague, or bypassed.
- `1`: Present but weak, incomplete, or poorly justified.
- `2`: Acceptable and specific enough for paper-mode review.
- `3`: Strong, clear, role-aligned, and reviewable.

Automatic fail conditions:

- Any live trading assumption.
- Any live endpoint assumption.
- Missing Risk Manager decision.
- Missing human approval when a send is proposed.
- Missing manual execution confirmation when a send is proposed.
- Missing journal readiness.
- Bypassed specialist-agent sequencing.
- Missing fixed risk.
- Proposal attempts to override a veto.

## 7. No-Trade Scoring

No-trade decisions are first-class positive outcomes.

The harness rewards:

- Waiting when location is weak.
- Rejecting unclear higher-timeframe context.
- Rejecting poor session timing.
- Rejecting vague confirmation.
- Rejecting missing invalidation.
- Rejecting excessive risk.
- Recording a clear no-trade journal entry.

No-trade scoring:

- `3`: Correct no-trade with clear veto reason and journal-ready explanation.
- `2`: Correct no-trade with adequate reason.
- `1`: No-trade decision is probably correct but reasoning is thin.
- `0`: Trade was forced, veto was ignored, or no-trade was not considered.

## 8. Rejection Quality Scoring

Rejected setups must be scored for decision quality, not treated as failures.

The harness rewards correctly rejecting weak trades, including:

- Weak liquidity.
- Conflicting higher-timeframe context.
- Invalid session/timing.
- Vague confirmation.
- Poor reward/risk.
- Missing fixed risk.
- Weak journal reasoning.

Rejection quality scoring:

- `3`: Rejection is specific, role-aligned, and tied to a clear failed gate.
- `2`: Rejection is valid and understandable.
- `1`: Rejection is valid but underspecified.
- `0`: Rejection is missing, incorrect, or overridden downstream.

## 9. Setup Quality Scoring

Setup quality measures whether a proposal satisfies the selective execution model.

Required evidence:

- Clear higher-timeframe context.
- Strong liquidity location.
- Valid session/timing window.
- Simple entry confirmation after price reaches location.
- Explicit invalidation.
- Reward/risk defined before approval.

Penalties:

- Forced trades.
- Weak liquidity.
- Excessive confidence.
- Setup based on one magic indicator.
- Proposal created before specialist gates complete.

## 10. Risk Quality Scoring

Risk quality measures whether the idea is survivable and reviewable before paper execution.

Required evidence:

- Fixed max loss.
- Explicit stop/invalidation.
- Reward/risk stated.
- Notional remains within approved limits.
- Risk Manager decision is preserved.
- No margin/leverage.
- No short selling unless a future approved phase allows it.

Automatic risk fail:

- Missing fixed risk.
- Notional increase assumption.
- Any live trading assumption.
- Any bypass of Risk Manager.

## 11. Journal Quality Scoring

Journal quality measures whether the decision can be audited later.

The harness rewards:

- Clear thesis.
- Clear reason for approval or rejection.
- Clear invalidation.
- Agent outputs referenced.
- Risk decision referenced.
- Human approval status referenced when applicable.
- No-trade decisions recorded with useful lessons.

Penalties:

- Poor journal reasoning.
- Missing veto reason.
- Missing source-agent context.
- Missing risk reference.
- Overconfident or vague language.

## 12. ADLC Compliance Scoring

ADLC compliance measures whether the proposal and review follow the Agentic Development Life Cycle.

Required checks:

- Scope and constraints are respected.
- Agent roles remain narrow.
- Autonomy boundaries are preserved.
- Failure modes are visible.
- Evaluation artifacts exist.
- Paper-only boundary is explicit.
- No implementation leap occurs without design approval.

Score `0` for any proposal that assumes live trading, automation, or unapproved scope expansion.

## 13. Data Integrity Scoring

Data integrity scoring measures whether the proposal is based on usable data.

Required checks:

- Data freshness is stated.
- Data completeness is stated.
- Missing or stale data triggers no-trade.
- Data Integrity Agent output exists before market analysis.
- No specialist agent proceeds on unverified data.

Penalties:

- Missing freshness.
- Missing completeness.
- Analysis based on stale or unknown data.
- Data Integrity veto ignored.

## 14. Human Approval Quality Review

Human approval quality is reviewed separately from automated scoring.

Required review questions:

- Did the human approve paper-only execution explicitly?
- Did the human approval reference the Risk Manager decision?
- Did the approval preserve the paper-only boundary?
- Did the approval avoid authorizing live trading?
- Did the approval avoid bypassing journaling?
- Did the manual execution confirmation remain separate from human approval?

Approval quality fails if it authorizes live trading, bypasses risk, bypasses journaling, or approves a proposal with unresolved specialist vetoes.

## 15. Failure Modes

Known failure modes:

- Forced trade despite weak setup.
- Weak liquidity accepted.
- Vague confirmation accepted.
- Missing fixed risk.
- Excessive confidence.
- Poor journal reasoning.
- Bypassed specialist agents.
- Risk Manager decision ignored.
- Human approval treated as execution permission.
- Manual confirmation skipped.
- No-trade not rewarded.
- Rejected setup treated as a system failure.
- Live trading assumption appears.
- Data freshness or completeness missing.

Any live trading assumption is an automatic failure.

## 16. Pass/Fail Criteria

Harness pass criteria:

- No automatic fail condition is present.
- Average score is at least `2.0`.
- No critical dimension scores `0`.
- No-trade and rejection decisions are scored as valid positive outcomes.
- Every proposed send has Risk Manager approval, human approval, manual confirmation, journal readiness, and ADLC `PASS`.
- Weak setups are rejected correctly.

Harness fail criteria:

- Any live trading assumption.
- Any proposed notional increase.
- Any automation assumption.
- Any bypassed specialist veto.
- Any missing fixed risk.
- Any missing journal readiness.
- Any missing Risk Manager decision.
- Any missing human approval for a proposed send.
- Any scorecard that treats no-trade discipline as negative behavior.

## 17. Required Test Scenarios

Required scenarios:

- Strong setup that passes all specialist gates.
- Weak higher-timeframe context that must be rejected.
- Weak liquidity location that must be rejected.
- Invalid session/timing that must be rejected.
- Vague confirmation that must be rejected.
- Missing fixed risk that must be rejected.
- Poor reward/risk that must be rejected.
- Stale data that must produce no-trade.
- Incomplete data that must produce no-trade.
- Specialist-agent sequencing violation that must fail.
- Risk Manager rejection that cannot be overridden.
- Human approval missing for a proposed send.
- Manual execution confirmation missing for a proposed send.
- Strong no-trade decision with clear journal.
- Rejected weak setup with high rejection quality score.
- Proposal with live trading assumption that must automatically fail.

## 18. What Remains Prohibited

Phase 12 does not allow:

- Live trading.
- Live Alpaca endpoints.
- Increased notional.
- Automation.
- Batch orders.
- Cancel/replace.
- Market orders.
- Short selling.
- Crypto.
- Options.
- Margin or leverage.
- Extended-hours trading.
- Skipping Risk Manager.
- Skipping human approval.
- Skipping manual execution confirmation.
- Skipping journal commit.
- Skipping reconciliation.
- Treating the harness as execution permission.

## 19. Conditions Before Implementation

Implementation may begin only after this design passes audit.

Before implementation:

- Define exact scorecard schema.
- Define artifact locations.
- Define test fixtures.
- Define failure-report format.
- Confirm no runtime execution logic changes are included.
- Confirm no notional increase is included.
- Confirm no automation is included.
- Confirm live trading remains unsupported.

Recommendation:

- Do not increase notional yet.
- Do not add automation yet.
- Implement only after this design passes audit.

## 20. Live Trading Remains Unsupported

Live trading remains unsupported.

Phase 12 evaluates strategy and proposal quality for controlled paper-mode review only. It does not authorize live trading, live endpoints, automation, increased notional, or any new execution behavior.
