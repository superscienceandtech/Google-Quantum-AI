# Yousuf — Proposed Individual Tasks

**Assignment status:** PROPOSED — no acceptance of these task scopes is recorded.
**Project role:** Team Lead and Chief Research Architect.

## Objective

Provide architecture and research leadership for verifiable quantum circuit
compilation while keeping benchmark decisions grounded in official evidence and
explicit approval gates.

## Proposed scope

1. Maintain the overall technical architecture and research priorities.
2. Define testable research hypotheses and cross-benchmark integration boundaries.
3. Own the decision gate for strict baseline readiness and any optimization start.
4. Review final technical results and proposed release evidence.
5. Decide whether to authorize the DQI 102,400-shot baseline execution.

The project-lead role is established, but acceptance of these individual work
packages remains **PROPOSED** until recorded.

## Context and evidence

The current [baseline status matrix](../../BASELINE_STATUS_MATRIX.md) records:

- INVSQRT: two raw full-verifier PASS runs; strict status **NOT REPRODUCED** due
  incomplete run provenance.
- DFTHC-SOS: two raw full-verifier PASS runs; strict status **NOT REPRODUCED**
  due incomplete run provenance.
- DQI: full 102,400-shot baseline **BLOCKED** pending explicit approval.

Do not treat historical PASS output as complete baseline reproduction evidence,
and do not infer missing timestamps or execution provenance.

## Expected deliverables

- Research priorities and hypotheses with source/evidence references.
- Architecture decisions that identify affected benchmark interfaces and risks.
- Written baseline/optimization gate decisions that do not overstate the evidence.
- Final review notes for proposed integration or release work.
- If DQI is authorized later, an explicit approval record before execution.

## Acceptance criteria

- Each decision links to the relevant official source, baseline record, or
  verifier output.
- Proposed experiments have a stated objective, dependencies, success/failure
  criteria, and reviewer before execution.
- No benchmark is called reproduced without the required complete provenance.
- No optimization is approved before baseline governance requirements are met.
- No candidate is promoted without the applicable authoritative verifier evidence.

## Dependencies

- Existing reports and raw evidence remain read-only inputs.
- Individual member scopes must be accepted before delegated ownership is active.
- Full DQI execution depends on explicit Yousuf approval and a ready approved
  command/recovery plan.

## Risks

- Conflating official verifier PASS with strict baseline reproduction could
  authorize optimization prematurely.
- Cross-benchmark integration could obscure task-specific verifier contracts.
- A proposed role may be mistaken for accepted ownership if status labels are
  omitted from downstream task records.

## Proposed reviewers

- SeyamB — independent evidence and validation review (**PROPOSED**).
- Srijon — reproducibility and infrastructure review where applicable
  (**PROPOSED**).

## Status and acceptance record

| Field | Value |
|---|---|
| Work-package status | **PROPOSED** |
| Member acceptance | Not recorded |
| Acceptance date/channel | — |
| Proposed reviewer acceptance | Not recorded |

## Restrictions

- Do not run the DQI 102,400-shot baseline without explicit approval.
- Do not authorize optimization before baseline governance requirements are met.
- Do not modify official verifier code, competition artifacts, or raw execution
  evidence as part of this scope.
- Do not commit, push, merge, or publish without the required project-lead
  approval.

## Related documents

- [Team structure](../TEAM_STRUCTURE.md)
- [Responsibility matrix](../TEAM_RESPONSIBILITY_MATRIX.md)
- [Task board](../TEAM_TASK_BOARD.md)
- [INVSQRT workstream](../BENCHMARKS/INVSQRT.md)
- [DQI workstream](../BENCHMARKS/DQI.md)
- [DFTHC-SOS workstream](../BENCHMARKS/DFTHC-SOS.md)
- [DQI execution approval request](../../BASELINE_EXECUTION_APPROVAL_REQUEST.md)
