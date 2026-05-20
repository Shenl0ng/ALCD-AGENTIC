# Baseline V15 Archive Manifest

## Archive Identity

- Archive name: Baseline V15 Real Market Paper-Only Archive
- Archive type: documentation manifest
- Archive status: MANIFEST_DEFINED
- Actual archive file: not created by this phase
- Git tag: not created by this phase
- Live trading: unsupported
- Paper-only: required

## PASS State

- Baseline V15 PASS.
- Phase 63 Full Regression PASS.
- Phase 64 Operator Runbook PASS.
- Phase 65 Controlled Live-Market Readiness Checklist PASS.
- Phase 66 Handoff Package PASS.
- Phase 67 Release Changelog PASS.

## Archive Contents — Required Docs

- `design/19_REAL_MARKET_DATA_ADAPTER.md`
- `docs/BASELINE_V15_REAL_MARKET_PAPER_ONLY_SYSTEM_FREEZE.md`
- `docs/OPERATING_POLICY_AFTER_PHASE_60_REAL_MARKET_PAPER_SOAK.md`
- `docs/BASELINE_V15_OPERATOR_RUNBOOK.md`
- `docs/PHASE_65_CONTROLLED_LIVE_MARKET_READINESS_CHECKLIST.md`
- `docs/BASELINE_V15_HANDOFF_PACKAGE.md`
- `docs/RELEASE_V15_REAL_MARKET_PAPER_ONLY_CHANGELOG.md`

## Archive Contents — Runtime Modules

- `runtime/market_data.py`
- `runtime/real_market_proposal_dry_run.py`
- `runtime/real_market_paper_order_run.py`
- `runtime/real_market_paper_reconciliation.py`
- `runtime/real_market_paper_soak_supervisor.py`

## Archive Contents — Tests

- `tests/test_real_market_data_adapter.py`
- `tests/test_real_market_proposal_dry_run.py`
- `tests/test_real_market_paper_order_run.py`
- `tests/test_real_market_paper_reconciliation.py`
- `tests/test_real_market_paper_soak_supervisor.py`

## Archive Contents — Report Families

- `reports/baseline_v15_full_regression/<timestamp>/BASELINE_V15_FULL_REGRESSION_AUDIT.md`
- `reports/real_market_data_adapter/<timestamp>/REAL_MARKET_DATA_ADAPTER_REPORT.md`
- `reports/real_market_proposal_dry_run/<timestamp>/REAL_MARKET_PROPOSAL_DRY_RUN_REPORT.md`
- `reports/real_market_paper_order_run/<timestamp>/REAL_MARKET_PAPER_ORDER_RUN_REPORT.md`
- `reports/real_market_paper_reconciliation/<timestamp>/REAL_MARKET_PAPER_RECONCILIATION_REPORT.md`
- `reports/real_market_paper_reconciliation/<timestamp>/POST_MORTEM.md`
- `reports/real_market_paper_reconciliation/<timestamp>/EVIDENCE_MANIFEST.md`
- `reports/real_market_paper_soak/<timestamp>/REAL_MARKET_PAPER_SOAK_REPORT.md`
- `reports/real_market_paper_soak/<timestamp>/SOAK_EVIDENCE_MANIFEST.md`

## Validation Commands

- `python3 -m unittest tests.test_real_market_data_adapter`
- `python3 -m unittest tests.test_real_market_proposal_dry_run`
- `python3 -m unittest tests.test_real_market_paper_order_run`
- `python3 -m unittest tests.test_real_market_paper_reconciliation`
- `python3 -m unittest tests.test_real_market_paper_soak_supervisor`
- `python3 -m unittest discover tests`

## Safety Posture

- V15 is paper-only.
- Live trading is unsupported.
- Real-money orders are unsupported.
- Human review is required.
- Manual execution confirmation is required.
- Preflight is required.
- Reconciliation is required.
- Post-mortem/evidence is required.
- Exactly one symbol is allowed.
- Market scanning is unsupported.
- Multi-symbol automation is unsupported.
- max_notional_usd <= 100 is required.
- `.env` mutation is prohibited.
- Secret printing is prohibited.
- Secret redaction before persistence is required.

## Archive Exclusions

The archive must exclude:

- `.env`
- Secrets.
- API keys.
- Broker credentials.
- Token files.
- Unredacted reports.
- Live trading credentials.
- Generated cache directories.
- Python bytecode caches.
- Local virtualenvs.

## Integrity Checklist

- [ ] Required docs present.
- [ ] Required runtime modules present.
- [ ] Required tests present.
- [ ] Required report families present.
- [ ] Full regression PASS.
- [ ] No `.env` included.
- [ ] No secrets included.
- [ ] No unredacted reports included.
- [ ] No live trading credentials included.
- [ ] No actual live orders present.
- [ ] No real-money order evidence present.
- [ ] Paper-only status confirmed.

## Final Exact Statements

Baseline V15 remains paper-only.

Live trading remains unsupported.

Real-money orders remain unsupported.

No archive file was created by Phase 68.

No git tag was created by Phase 68.

No runtime code was changed.

No tests were changed.

No order was sent.

No live order was sent.

The system must not mutate `.env`.

Secrets must be redacted before persistence.

## Final Status

Phase 68 Baseline V15 Archive Manifest Status: MANIFEST_DEFINED
