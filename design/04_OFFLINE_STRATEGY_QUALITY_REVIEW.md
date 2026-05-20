# Phase 17 Offline Strategy Quality Review Design

## 1. Purpose

Phase 17 defines an offline strategy quality review process.

The review evaluates prior proposals, rejected trades, no-trade decisions, journals, paper send reports, post-mortems, strategy evaluation artifacts, and evaluation gate artifacts.

This phase is offline only. It does not send orders, create paper order requests, approve trades, modify risk limits, increase notional, add automation, use Alpaca, create `.env` files, or authorize live trading.

## 2. Why This Phase Comes After Baseline V2

Baseline Safe Paper Execution V2 confirmed that controlled paper execution can be gated by deterministic strategy evaluation and the Evaluation-First Gate.

The next risk is not mechanical execution. The next risk is quality drift:

- The system may approve too many setups.
- Rejections may become too rare.
- Journals may become generic.
- Liquidity and confirmation language may become vague.
- Evaluation scores may inflate.
- Human approval may rubber-stamp prior outputs.

Phase 17 comes after V2 to review whether the system is actually becoming more selective and reviewable before any future scope expansion is considered.

## 3. Inputs

Required inputs:

- `reports/phase_11_repeatability/PHASE_11_REPEATABILITY_SUMMARY.md`
- `reports/phase_16_evaluation_gated_regression/PHASE_16_EVALUATION_GATED_REGRESSION_SUMMARY.md`
- `docs/BASELINE_SAFE_PAPER_EXECUTION_V2.md`
- Prior controlled paper send reports.
- Prior post-mortems.
- Strategy evaluation outputs.
- Evaluation gate outputs.
- Rejected trade artifacts.
- No-trade artifacts.
- Journal entries.

Optional supporting inputs:

- ADLC traceability artifacts.
- Risk violation scenarios.
- No-trade scenarios.
- Paper trading scorecards.
- Failure auditor notes.
- Weekly review notes.

## 4. Outputs

The offline review must produce:

- Strategy quality review report.
- Proposal quality summary.
- Rejection quality summary.
- No-trade discipline summary.
- Journal quality summary.
- Evaluation-gate quality summary.
- Risk discipline summary.
- ADLC compliance summary.
- Data integrity summary.
- Failure pattern report.
- Red-flag list.
- Recommendation: `HOLD`, `CONTINUE_PAPER_ONLY`, or `PROCEED_TO_NEXT_DESIGN_PHASE`.

Outputs must not approve trades, create paper order requests, send orders, increase notional, or enable automation.

## 5. Review Cadence

Minimum cadence:

- After every controlled paper send.
- After every post-mortem.
- Before any additional paper send series.
- Before any proposed notional increase.
- Before any proposed automation design.
- Before any future phase that expands execution scope.

Recommended cadence:

- Weekly offline review while paper execution remains active.
- Immediate review after any blocked gate, mismatch, weak journal, or unexplained approval.

## 6. Review Dataset

The review dataset must include both executed and non-executed decisions.

Required categories:

- Controlled paper sends.
- Submitted paper order reports.
- Reconciled paper order reports.
- Post-mortems.
- Strategy Evaluation Harness outputs.
- Evaluation-First Gate outputs.
- Approved proposals.
- Rejected proposals.
- No-trade decisions.
- Journal entries.
- Risk Manager decisions.
- Human Approval records.
- Manual Execution Confirmation records.
- Execution Gatekeeper records.

The dataset must not be limited to successful sends. Correct rejections and correct waiting are first-class review outcomes.

## 7. Strategy Quality Dimensions

The review must evaluate:

- Did the system trade selectively?
- Did it correctly reject weak setups?
- Did it avoid forced trades?
- Did it reward waiting?
- Did the liquidity reasoning improve?
- Did the higher-timeframe context matter?
- Did the entry confirmation remain simple and clear?
- Did fixed risk remain explicit?
- Did the journal explain why the trade existed?
- Did any gate become performative instead of meaningful?
- Did any agent appear to rubber-stamp prior outputs?

Additional dimensions:

- Session/timing relevance.
- Reward/risk clarity.
- Invalidation clarity.
- Proposal specificity.
- Agent sequencing integrity.
- Paper-only boundary clarity.

## 8. No-Trade Discipline Review

No-trade decisions must be scored as positive outcomes when they are correct.

Review questions:

- Did the system wait when liquidity was weak?
- Did it reject vague confirmation?
- Did it avoid trading during poor timing windows?
- Did it reject stale or incomplete data?
- Did it record a useful no-trade journal entry?
- Did it avoid manufacturing a trade just to continue the workflow?

Red flags:

- No-trade avoidance.
- Too few no-trade decisions.
- Repeated pressure to trade.
- Thin no-trade reasoning.
- Missing veto reason.

## 9. Rejection Quality Review

Rejected trades must be reviewed for quality, not treated as operational failures.

Review questions:

- Was the rejection tied to a specific failed gate?
- Was weak liquidity identified clearly?
- Was higher-timeframe conflict described?
- Was confirmation vague or absent?
- Was fixed risk missing or incomplete?
- Did Risk Manager challenge the setup meaningfully?
- Did the journal preserve the rejection reason?

Red flags:

- Too few rejections.
- Generic rejection reasons.
- Rejections overridden downstream.
- Human approval after a meaningful veto.
- Evaluation score inflation on weak setups.

## 10. Journal Quality Review

Journal entries must explain why a trade existed, why it was rejected, or why waiting was correct.

Review questions:

- Does the journal state the thesis?
- Does it state why now?
- Does it state why this liquidity location?
- Does it state what invalidates the idea?
- Does it reference specialist-agent outputs?
- Does it reference Risk Manager output?
- Does it preserve human accountability?
- Does it avoid generic repeated text?

Red flags:

- Weak journal reasoning.
- Repeated use of generic thesis text.
- Missing invalidation.
- Missing liquidity rationale.
- Missing risk reference.
- Missing reason for no-trade.
- Overconfident language without evidence.

## 11. Evaluation-Gate Quality Review

The Evaluation-First Gate must remain meaningful.

Review questions:

- Did the gate block weak setups?
- Did it allow only proposals with strong enough score and no hard-fail condition?
- Did it preserve ADLC compliance?
- Did it detect missing fixed risk?
- Did it detect missing journal readiness?
- Did it detect specialist sequencing violations?
- Did it detect data integrity failures?
- Did it prevent Human Approval before gate pass?
- Did it prevent Paper Order Request creation before gate pass?
- Did it prevent Paper Send before gate pass?

Red flags:

- Any gate became performative instead of meaningful.
- Scores drift upward without better evidence.
- Hard-fail conditions are ignored.
- Gate outputs are accepted without artifact references.
- Human approval rubber-stamps gate output.

## 12. Risk Discipline Review

Risk discipline must remain more important than execution count.

Review questions:

- Did fixed risk remain explicit?
- Did notional stay within the approved cap?
- Did Risk Manager challenge weak setups?
- Did Risk Manager reject malformed proposals?
- Did the system avoid margin, leverage, short selling, options, crypto, and extended hours?
- Did the system avoid suggesting size increases before quality improved?

Red flags:

- Risk approval without meaningful challenge.
- Missing fixed risk.
- Any suggestion to increase size before quality improves.
- Increasing frequency before rejection quality improves.
- Treating paper fills as proof of strategy quality.

## 13. ADLC Compliance Review

The offline review must verify that ADLC controls remain active.

Review questions:

- Did every phase stay within its approved scope?
- Did implementation follow approved design?
- Did specialist-agent separation remain intact?
- Did autonomy boundaries remain visible?
- Were failure modes captured?
- Were reports and post-mortems created?
- Were changes audited before scope expansion?

Red flags:

- Implementation before design approval.
- Missing audit.
- Missing report artifact.
- Missing post-mortem.
- Agent role collapse.
- Any live trading assumption.

## 14. Data Integrity Review

Data integrity review must check whether decisions were based on usable data.

Review questions:

- Was data freshness recorded?
- Was data completeness recorded?
- Were stale or missing data conditions blocked?
- Did specialist agents proceed only after Data Integrity passed?
- Did evaluation scores reflect data quality?

Red flags:

- Missing data freshness.
- Missing data completeness.
- Stale data accepted.
- Data Integrity Agent bypassed.
- Evaluation gate passed despite missing data integrity.

## 15. Failure Pattern Detection

The review must identify repeated failure patterns across artifacts.

Patterns to detect:

- Too many approvals.
- Too few rejections.
- Weak journal reasoning.
- Vague liquidity language.
- Vague confirmation language.
- Repeated use of generic thesis text.
- Evaluation score inflation.
- Risk approval without meaningful challenge.
- Human approval rubber-stamping.
- No-trade avoidance.
- Any suggestion to increase size before quality improves.
- Any agent rubber-stamping prior outputs.
- Any gate becoming performative.

Detected patterns must be recorded as blockers before any scope expansion.

## 16. Scoring Method

Each review dimension is scored from `0` to `3`.

- `0`: Missing, unsafe, bypassed, or unsupported.
- `1`: Present but weak, generic, or poorly justified.
- `2`: Acceptable and reviewable.
- `3`: Strong, specific, role-aligned, and useful for future review.

Required rollups:

- Proposal quality average.
- Rejection quality average.
- No-trade discipline average.
- Journal quality average.
- Evaluation-gate quality average.
- Risk discipline average.
- ADLC compliance score.
- Data integrity score.

Automatic `HOLD` conditions:

- Any live trading assumption.
- Any unreviewed scope expansion.
- Any missing post-mortem for a send.
- Any unreconciled paper send.
- Any ignored hard-fail condition.
- Any recommendation to increase notional before quality improves.
- Any recommendation to automate before no-trade discipline improves.

## 17. Required Reports

Phase 17 implementation must produce:

- Offline strategy quality review report.
- Red-flag report.
- Rejection quality report.
- No-trade discipline report.
- Journal quality report.
- Evaluation-gate quality report.
- Risk discipline report.
- ADLC compliance report.
- Data integrity report.
- Recommendation report.

Reports must be read-only summaries of prior artifacts. They must not trigger execution or approvals.

## 18. Required Test Scenarios

Implementation must test:

- Prior successful paper send is included in review.
- Prior blocked attempt is included in review.
- Rejected trade artifacts are scored.
- No-trade artifacts are scored.
- Weak journal reasoning scores low.
- Generic repeated thesis text scores low.
- Vague liquidity language scores low.
- Vague confirmation language scores low.
- Correct rejection scores high.
- Correct no-trade scores high.
- Evaluation score inflation is flagged.
- Human approval rubber-stamping is flagged.
- Risk approval without meaningful challenge is flagged.
- Any live trading assumption produces `HOLD`.
- Any recommendation to increase size before quality improves produces `HOLD`.
- Reports are generated without Alpaca calls.
- Reports are generated without order sends.
- Reports do not enable `PAPER_ORDER_EXECUTION_ENABLED`.
- Reports do not create `.env` files.
- Reports do not use LLM API calls.

## 19. What Remains Prohibited

The following remain prohibited:

- Sending orders.
- Creating paper order requests.
- Approving trades.
- Modifying risk limits.
- Increasing notional.
- Adding automation.
- Live trading.
- Live endpoints.
- Batch orders.
- Cancel/replace.
- Higher frequency execution.
- Market orders.
- Short selling.
- Crypto.
- Options.
- Margin or leverage.
- Extended-hours trading.
- Autonomous follow-up trades.
- Committing credentials.
- Creating `.env` files with real values.
- LLM API calls.

## 20. Conditions Before Any Implementation

Before implementing Phase 17:

- This design must pass audit.
- Scope must remain offline-only.
- Inputs must be existing artifacts only.
- Outputs must be review reports only.
- Tests must prove no Alpaca calls occur.
- Tests must prove no order behavior exists.
- Tests must prove no approvals are created.
- Tests must prove no risk limits are modified.
- Tests must prove no notional increase is recommended.
- Tests must prove no automation is recommended.

Implementation must recommend:

- Improve quality before increasing notional.
- Improve rejection quality before increasing frequency.
- Improve no-trade discipline before automation.
- Keep live trading unsupported.

## 21. Live Trading Remains Unsupported

Live trading remains unsupported.

Phase 17 is an offline review design only. It does not authorize live trading, live endpoints, automation, increased notional, paper order requests, approvals, or order sends.
