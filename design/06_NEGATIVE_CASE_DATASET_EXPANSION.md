# Phase 21 Negative Case Dataset Expansion Design

## 1. Purpose

Phase 21 designs an offline negative-case dataset for rejected trades, no-trade decisions, weak setups, blocked approvals, gate failures, and journal failures.

The purpose is to reduce approval bias by giving the strategy evaluation process more explicit examples where the correct outcome is rejection, no-trade, blocked evaluation, blocked human approval, or blocked paper request.

This phase is offline design only. It does not send orders, create paper order requests, approve trades, modify execution logic, modify risk limits, increase notional, add automation, create `.env` files, print secrets, use Alpaca, or authorize live trading.

## 2. Why This Phase Is Needed

The post-tightening Offline Strategy Quality Review completed with:

- Review status: `REVIEW_COMPLETE`
- Recommendation: `CONTINUE_MANUAL_LIMITED_PAPER`
- Red flag still detected: `too many approvals`
- Increasing notional allowed: no
- Automation allowed: no

The system has added tighter approval rules, but the reviewed artifact set remains approval-heavy. A negative-case dataset is needed so future offline evaluation can test whether the system correctly prefers rejection and no-trade when evidence is weak, vague, generic, incomplete, or rubber-stamped.

This phase treats excessive approvals as an evaluation quality problem, not an execution opportunity.

## 3. Source Report Path

`reports/offline_strategy_quality_review/20260520T005129Z/OFFLINE_STRATEGY_QUALITY_REVIEW.md`

## 4. Red Flag Addressed

Red flag addressed: `too many approvals`.

The dataset must directly test whether the system blocks approval-heavy behavior and rewards capital-preserving decisions.

## 5. Dataset Categories

The offline dataset must include cases from all of these categories:

- Missing higher-timeframe context
- Generic higher-timeframe context
- Weak liquidity location
- Vague liquidity language
- Vague confirmation
- Non-observable confirmation
- Generic thesis
- Thesis reusable for any symbol
- Missing credible invalidation
- Risk valid but setup weak
- Forced trade behavior
- Excessive confidence without evidence
- Specialist agent rubber-stamping
- Human approval rubber-stamping
- Evaluation score inflation
- No-trade should be preferred
- Journal too weak
- Data integrity incomplete
- ADLC compliance incomplete
- Live trading assumption

## 6. Required Negative Case Types

Negative cases must include any setup where approval would be lower quality than rejection or no-trade.

Required negative case types:

- Setup lacks specific higher-timeframe context.
- Setup uses directional bias without market structure evidence.
- Liquidity location is weak, vague, or not price-relevant.
- Confirmation is vague, subjective, or not observable.
- Thesis could be reused across unrelated symbols.
- Invalidation is missing, circular, or not credible.
- Risk parameters are valid, but setup quality is poor.
- Agent outputs show excessive agreement without independent reasoning.
- Human approval repeats automated output without challenge.
- Evaluation score is high despite weak evidence.
- Journal note is too thin for later review.
- Data integrity is incomplete or stale.
- ADLC traceability is incomplete.
- Any case assumes live trading is available.

## 7. Required No-Trade Case Types

The dataset must include at least 10 explicit `NO_TRADE` cases.

Required no-trade case types:

- Context is plausible but not specific enough.
- Liquidity is nearby but not meaningful enough.
- Price has not reached the relevant liquidity location.
- Confirmation is technically present but low quality.
- Session timing is outside the preferred window.
- Setup quality is weaker than waiting.
- Approval rate is already above warning threshold.
- Agents disagree or produce incomplete outputs.
- Journal evidence is insufficient before decision time.
- The best capital-preserving decision is to wait.

## 8. Required Rejection Case Types

The dataset must include at least 10 weak setup rejection cases.

Required rejection case types:

- `REJECT` for generic higher-timeframe context.
- `REJECT` for vague liquidity location.
- `REJECT` for vague confirmation.
- `REJECT` for thesis reusable for any symbol.
- `REJECT` for missing credible invalidation.
- `REJECT` when risk is valid but setup is weak.
- `REJECT` when no-trade is clearly better.
- `REJECT` when the proposal appears forced.
- `REJECT` when confidence exceeds available evidence.
- `REJECT` when specialist agents did not provide differentiated reasoning.

## 9. Required Rubber-Stamping Case Types

The dataset must include at least 5 rubber-stamping cases.

Required rubber-stamping case types:

- Specialist agents repeat the same conclusion without role-specific evidence.
- Risk Manager approves weak setup quality because numeric risk is valid.
- Trade Proposal Agent converts weak evidence into an approval-ready proposal.
- Human Approval repeats the Evaluation-First Gate score without independent challenge.
- Execution Gatekeeper is expected to block because approval quality is rubber-stamped.

## 10. Required Weak Setup Case Types

Weak setup cases must test whether the system can reject technically complete but low-quality proposals.

Required weak setup case types:

- Complete fields but generic thesis.
- Valid stop and target but weak liquidity.
- Valid session timing but weak confirmation.
- Observable confirmation at the wrong location.
- Strong confidence language without evidence.
- Setup depends on hindsight rather than pre-decision evidence.
- Setup passes one specialist agent but fails the combined strategy standard.

## 11. Required Evaluation-Gate Failure Case Types

Evaluation-gate failure cases must produce `BLOCK_EVALUATION_GATE`.

Required failure case types:

- Score below tightened threshold.
- Liquidity score below required level.
- Confirmation score below required level.
- Journal quality score below required level.
- Data integrity status is incomplete.
- ADLC compliance is incomplete.
- Evaluation score is inflated relative to evidence.
- Approval-rate hard block should prevent approval.

## 12. Required Journal Failure Case Types

The dataset must include at least 5 journal or evidence failure cases.

Required journal failure case types:

- Journal omits why no-trade was not selected.
- Journal omits higher-timeframe context.
- Journal omits specific liquidity level.
- Journal omits observable confirmation.
- Journal omits credible invalidation.
- Journal uses reusable template language.
- Journal cannot support later post-mortem review.

## 13. Dataset Schema

Each case must define:

- `case_id`
- `category`
- `input_summary`
- `agent_outputs`
- `expected_decision`
- `expected_gate_status`
- `expected_score_band`
- `expected_rejection_reason`
- `expected_journal_note`
- `why_no_trade_is_correct`
- `prohibited_outcome`

Schema requirements:

- `case_id` must be unique and stable.
- `category` must match one required dataset category.
- `agent_outputs` must preserve role separation and show each relevant agent's output independently.
- `expected_decision` must use an allowed decision label.
- `expected_gate_status` must show whether the case is rejected, allowed to remain no-trade, or blocked before any paper request.
- `expected_score_band` must be low enough to prevent approval when evidence is weak.
- `expected_rejection_reason` must be specific, not generic.
- `expected_journal_note` must show what should be recorded for later review.
- `why_no_trade_is_correct` must explain the capital-preservation rationale.
- `prohibited_outcome` must name the unsafe or incorrect result the evaluation must prevent.

## 14. Expected Labels

Expected decisions must include:

- `REJECT`
- `NO_TRADE`
- `BLOCK_EVALUATION_GATE`
- `BLOCK_HUMAN_APPROVAL`
- `BLOCK_PAPER_REQUEST`

The dataset must not include `APPROVE` as an expected decision for any negative case.

## 15. Expected Gate Outcome

Expected gate outcomes must preserve this safety order:

1. Weak or incomplete evidence should become `NO_TRADE` or `REJECT`.
2. Scoring, data, ADLC, or journal failures should become `BLOCK_EVALUATION_GATE`.
3. Rubber-stamped approval should become `BLOCK_HUMAN_APPROVAL`.
4. Any attempted paper request from a negative case should become `BLOCK_PAPER_REQUEST`.

No negative case may proceed to order sending.

## 16. Expected Scoring Outcome

Expected scoring must reduce approval bias.

Required scoring outcomes:

- Generic context must cap the strategy score below approval threshold.
- Weak liquidity must cap liquidity score below approval threshold.
- Vague confirmation must cap confirmation score below approval threshold.
- Journal weakness must cap journal quality below approval threshold.
- Rubber-stamping must trigger a hard block or severe score penalty.
- Evaluation score inflation must be detected as a failure pattern.
- No-trade decisions must be scored as correct when evidence is insufficient.

## 17. Required Reports

Future implementation must produce offline reports only.

Required reports:

- Negative-case dataset inventory report.
- Category coverage report.
- Expected decision distribution report.
- No-trade coverage report.
- Weak setup rejection coverage report.
- Rubber-stamping detection report.
- Journal and evidence failure report.
- Evaluation-gate failure report.
- Approval-bias reduction summary.

Reports must not include secrets, credentials, account identifiers, order identifiers from new order activity, or live trading assumptions.

## 18. Required Tests

Future implementation must add offline tests only.

Required tests:

- Dataset contains at least 30 negative cases.
- Dataset contains at least 10 explicit `NO_TRADE` cases.
- Dataset contains at least 10 weak setup rejection cases.
- Dataset contains at least 5 rubber-stamping cases.
- Dataset contains at least 5 journal or evidence failure cases.
- Every required category is represented.
- Every case has all required schema fields.
- No negative case expects approval.
- No negative case creates a paper order request.
- No case enables `PAPER_ORDER_EXECUTION_ENABLED`.
- No test uses Alpaca API.
- No test sends orders.
- No test modifies execution logic.
- No test increases notional limits.
- No test adds automation.
- No test creates `.env` files.

## 19. What Remains Prohibited

The following remain prohibited:

- Sending orders.
- Creating paper order requests.
- Approving trades from this dataset.
- Enabling `PAPER_ORDER_EXECUTION_ENABLED`.
- Using Alpaca API.
- Modifying execution logic.
- Modifying risk limits.
- Increasing notional.
- Adding automation.
- Creating `.env` files.
- Printing secrets.
- Recommending automation.
- Recommending live trading.
- Recommending batch orders.
- Recommending cancel/replace behavior.
- Recommending higher frequency.

## 20. Conditions Before Implementation

Implementation may begin only after this design is accepted and the work remains offline.

Before implementation:

- Dataset storage location must be selected under architecture or evaluation scope.
- Case format must be reviewed for ADLC traceability.
- Evaluation harness behavior must remain offline.
- Tests must prove no order path is invoked.
- Tests must prove no Alpaca API path is invoked.
- Tests must prove no notional limit is increased.
- Reports must be offline artifacts only.
- Human accountability and manual limited paper status must remain unchanged.

Implementation must not proceed if it requires execution changes, new automation, API access, secrets, or order creation.

## 21. Explicit Live Trading Boundary

Live trading remains unsupported.

This phase does not design, imply, prepare, or authorize live trading. Any case that assumes live trading availability must be labeled as a failure and must produce a blocking outcome.

## Minimum Dataset Composition

The future dataset must contain enough negative examples to reduce approval bias:

- At least 30 negative cases.
- At least 10 explicit `NO_TRADE` cases.
- At least 10 weak setup rejection cases.
- At least 5 rubber-stamping cases.
- At least 5 journal or evidence failure cases.

Minimum case distribution:

| Case range | Primary purpose | Expected decisions |
| --- | --- | --- |
| `NC-001` to `NC-010` | Explicit no-trade examples | `NO_TRADE` |
| `NC-011` to `NC-020` | Weak setup rejection examples | `REJECT` |
| `NC-021` to `NC-025` | Rubber-stamping examples | `BLOCK_HUMAN_APPROVAL`, `BLOCK_PAPER_REQUEST` |
| `NC-026` to `NC-030` | Journal, evidence, data, ADLC, and gate failures | `BLOCK_EVALUATION_GATE`, `REJECT` |

Additional cases should expand underrepresented categories before adding more approval-adjacent examples.

## Offline Safety Statement

Phase 21 is an offline dataset design phase only.

No order was sent by this design. No paper order request is authorized by this design. No execution runtime change is authorized by this design. No notional increase is authorized by this design. No automation is authorized by this design. Alpaca remains untouched.
