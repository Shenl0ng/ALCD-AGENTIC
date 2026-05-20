# Negative Case Dataset Summary

## Validation Status

PASS

## Total Cases

33

## Category Counts

- ADLC compliance incomplete: 1
- Data integrity incomplete: 1
- Evaluation score inflation: 1
- Excessive confidence without evidence: 1
- Forced trade behavior: 1
- Generic higher-timeframe context: 2
- Generic thesis: 2
- Human approval rubber-stamping: 2
- Journal too weak: 2
- Live trading assumption: 1
- Missing credible invalidation: 1
- Missing higher-timeframe context: 2
- No-trade should be preferred: 1
- Non-observable confirmation: 2
- Risk valid but setup weak: 2
- Specialist agent rubber-stamping: 3
- Thesis reusable for any symbol: 2
- Vague confirmation: 2
- Vague liquidity language: 2
- Weak liquidity location: 2

## Expected Decision Counts

- BLOCK_EVALUATION_GATE: 6
- BLOCK_HUMAN_APPROVAL: 4
- BLOCK_PAPER_REQUEST: 2
- NO_TRADE: 10
- REJECT: 11

## Required Case Counts

- NO_TRADE case count: 10
- Weak setup rejection count: 11
- Rubber-stamping case count: 5
- Journal/evidence failure count: 5

## Prohibited Outcomes Summary

- Approval based only on risk limits: 1
- Approval because risk math is valid: 1
- Approval because the system has been inactive: 1
- Approval from confidence language: 1
- Approval from copied gate output: 1
- Approval from feeling-based confirmation: 1
- Approval from generic context: 1
- Approval from generic directional bias: 1
- Approval from generic thesis: 1
- Approval from hidden-buyer assumption: 1
- Approval from inferred participant behavior: 1
- Approval from inflated evaluation score: 1
- Approval from lower-timeframe signal alone: 1
- Approval from minor midpoint reaction: 1
- Approval from one-word human review: 1
- Approval from reusable thesis: 1
- Approval from reusable trend continuation language: 1
- Approval from shallow specialist agreement: 1
- Approval from subjective confirmation: 1
- Approval from symbol-agnostic thesis: 1
- Approval from unnamed liquidity: 1
- Approval from vague liquidity claim: 1
- Approval from weak liquidity: 1
- Approval with incomplete data integrity: 1
- Approval with journal that cannot justify trade over no-trade: 1
- Approval with unauditable journal: 1
- Approval without ADLC traceability: 1
- Approval without credible invalidation: 1
- Approval without higher-timeframe review: 1
- Human approval from repeated agent text: 1
- Non-paper execution path proceeds: 1
- Paper order request from rubber-stamped approval: 1
- Trade approval before liquidity interaction: 1

## Safety Boundary

Live trading remains unsupported.
Increasing notional remains prohibited.
Automation remains prohibited.
No Alpaca API, broker calls, order sends, LLM calls, credentials, or `.env` creation are part of this dataset.
