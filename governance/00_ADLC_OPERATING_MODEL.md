# ADLC Operating Model

## ADLC Binding
Phase: All ADLC phases.
Control Type: Mandatory operating control.
Block Authority: Yes.

## Operational Control
ADLC is mandatory. It defines which files exist, which agents may act, which routines may run, what gets validated, what gets blocked, and what must be reviewed.

## Phase Mapping
| ADLC Phase | Control Purpose | Project Files |
|---|---|---|
| Preparation & Hypothesis | Define the trading problem before design | governance/01_PROBLEM_HYPOTHESIS.md, strategy/00_STRATEGY_SOURCE_PDF.md |
| Scope & Constraints | Bound paper-only activity and risk | governance/02_SCOPE_AND_CONSTRAINTS.md, governance/risk_limits.md |
| Human-Agent Responsibility | Preserve accountability | governance/03_HUMAN_AGENT_RESPONSIBILITY.md, governance/human_approval.md |
| Architecture Design | Separate agent responsibilities | agents/, routines/, memory/ |
| Simulation & Proof of Value | Validate behavior before any implementation | evaluation/, memory/rejected_trades.md |
| Testing & Evaluation | Test reasoning, vetoes, hallucination, and risk | governance/07_EVALUATION_PROTOCOL.md, evaluation/ |
| Deployment Monitoring | Monitor paper-trading behavior | memory/journal.md, governance/08_DEPLOYMENT_MONITORING.md |
| Maintenance & Learning | Improve through review and change control | memory/lessons_learned.md, governance/09_CHANGE_CONTROL.md |

## Mandatory Rule
If an action lacks ADLC phase, owner, input, output, veto path, and human accountability, it is blocked.
