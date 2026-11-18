# Mahin — DQI Research (Proposed)

**Assignment status:** PROPOSED
**Starting profile:** Web development and research
**Member acceptance:** Not recorded

## Objective

Develop a source-backed DQI research package focused on reversible decoding,
verifier requirements, confidence bounds, and resource/complexity analysis.

## Proposed scope

- Study reversible Reed–Solomon decoder approaches relevant to the DQI task.
- Analyze the official verifier API and its input, output, and acceptance
  requirements.
- Derive the confidence-bound and shot-count constraints from official sources.
- Analyze decoder resource use and complexity; clearly distinguish estimates
  from measured verifier output.
- Prepare small diagnostic experiments only after the specific experiment is
  authorized.

## Context and evidence

The official DQI sample and verifier are local read-only reference artifacts.
The full 102,400-shot baseline has not been executed; the current status is
**BLOCKED** pending explicit approval from Yousuf. The exact proposed command,
parameters, memory/runtime estimate, timeout, and recovery procedure are recorded
in the [DQI execution approval request](../../BASELINE_EXECUTION_APPROVAL_REQUEST.md).

The [baseline status matrix](../../BASELINE_STATUS_MATRIX.md) and
[evidence reconciliation](../../BASELINE_EVIDENCE_RECONCILIATION.md) distinguish
partial diagnostics from full execution and strict baseline score reproduction.

## Expected deliverables

- A mathematical note on reversible Reed–Solomon decoding, with source references.
- A DQI API/requirements summary that does not infer undocumented behavior.
- A resource/complexity analysis with derived values separated from measurements.
- A bounded diagnostic proposal that records objective, inputs, command,
  authorization, expected resource use, and evidence classification before any
  diagnostic is run.
- A proposed analysis of the DQI full-baseline preparation requirements; not a
  claim that the full run occurred.

## Acceptance criteria

- Mathematical and API claims cite official verifier sources or primary references.
- Confidence-bound and shot-count requirements match the official verifier.
- Derived calculations are labeled as derived; measured results cite raw records.
- No partial diagnostic is called an official full-verifier PASS or baseline
  score reproduction.
- The 102,400-shot run is not executed without explicit Yousuf approval.

## Dependencies

- Read-only access to the official DQI verifier and sample.
- Existing verifier API, score-model, dependency, and baseline reports.
- Explicit Yousuf approval for the full 102,400-shot single-worker run.
- Separate authorization for any proposed small diagnostic.

## Risks

- Reversible decoder research may omit workspace, syndrome, or phase-correctness
  costs if resource analysis is incomplete.
- A confidence-bound diagnostic may be mistaken for full benchmark acceptance.
- The full run is resource-intensive and must not be launched from a research
  note or task assignment alone.

## Proposed reviewer

SeyamB is the proposed independent reviewer for evidence and validation;
Yousuf is the proposed reviewer for the authorization gate. Both assignments
remain **PROPOSED**.

## Status and acceptance record

| Field | Value |
|---|---|
| Work-package status | **PROPOSED** |
| Member acceptance | Not recorded |
| Acceptance date/channel | — |
| Proposed reviewer acceptance | Not recorded |
| DQI full-baseline status | **BLOCKED** pending explicit Yousuf approval |

## Restrictions

- Do not execute the full DQI 102,400-shot command without explicit approval
  from Yousuf.
- Do not run even a small diagnostic unless that diagnostic is authorized.
- Do not start optimization before baseline governance requirements are met.
- Do not modify official verifier code, competition artifacts, or raw execution
  evidence.
- Do not describe the approval request as a completed run or score.

## Related documents

- [Team structure](../TEAM_STRUCTURE.md)
- [Responsibility matrix](../TEAM_RESPONSIBILITY_MATRIX.md)
- [Task board](../TEAM_TASK_BOARD.md)
- [DQI workstream](../BENCHMARKS/DQI.md)
- [DQI execution approval request](../../BASELINE_EXECUTION_APPROVAL_REQUEST.md)
- [Official verifier API reference](../../OFFICIAL_VERIFIER_API_REFERENCE.md)
