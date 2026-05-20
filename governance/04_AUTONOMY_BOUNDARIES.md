# Autonomy Boundaries

## ADLC Binding
Phase: Human-Agent Responsibility / Scope & Constraints.
Control Type: Mandatory operating control.
Block Authority: Yes.

## Operational Control
Agent autonomy is narrow, role-specific, and veto-oriented.

## Boundary Rules
- Agents may only read and write their assigned files.
- Agents may not merge responsibilities across analysis, approval, execution, and journaling.
- Approval is separated from proposal.
- Execution gatekeeping is separated from risk approval.
- Journaling is separated from trade selection.

## Maximum Autonomy
The maximum permitted autonomous action is to produce a structured markdown decision or veto.

## Block Condition
Any agent attempting to place, simulate through broker APIs, or manage orders is outside autonomy boundaries.
