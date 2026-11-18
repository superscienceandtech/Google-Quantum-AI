# SeyamB — Verification and Data Integrity (Proposed)

**Assignment status:** PROPOSED
**Starting profile:** Data cleaning, error detection, and validation
**Member acceptance:** Not recorded

## Objective

Propose an independent verification and data-integrity workstream that preserves
raw evidence, validates inputs and outputs, and reports only what the evidence
actually establishes.

## Proposed scope

- Inventory existing tests, validation checks, and experiment records.
- Validate checksums and input/output schemas without modifying official inputs.
- Review evidence provenance and classify each run by its actual verification level.
- Propose regression checks using synthetic fixtures where implementation support
  exists.
- Independently review experimental claims and reproducibility documentation.

## Context and evidence

Existing baseline reports distinguish file integrity, schema/register/structural
checks, partial diagnostics, official full-verifier executions, and strict
baseline score reproduction. Preserve those distinctions:

- INVSQRT and DFTHC-SOS each have two raw official full-verifier PASS records.
  Their strict baseline status remains **NOT REPRODUCED** because provenance is
  incomplete.
- DQI's full 102,400-shot run is absent and remains **BLOCKED** pending explicit
  Yousuf approval.

Primary records:
[baseline status matrix](../../BASELINE_STATUS_MATRIX.md),
[baseline reconciliation](../../BASELINE_EVIDENCE_RECONCILIATION.md), and
[experiment record standard](../../EXPERIMENT_RECORD_STANDARD.md).

## Evidence classification

Use the project's evidence levels consistently:

1. `FILE_INTEGRITY_CHECK`
2. `SCHEMA_VALIDATION`
3. `REGISTER_VALIDATION`
4. `STRUCTURAL_CIRCUIT_VALIDATION`
5. `PARTIAL_DIAGNOSTIC`
6. `OFFICIAL_VERIFIER_FULL_EXECUTION`
7. `OFFICIAL_BASELINE_SCORE_REPRODUCTION`

Levels 1–6 do not prove level 7. A successful parse or structural validation is
not an official verifier PASS. An official full-verifier PASS does not, by
itself, establish strict baseline reproduction when required provenance is
missing.

## Expected deliverables

- A repository test inventory with test purpose and evidence level.
- A data-integrity checklist covering artifact checksums and input/output schema.
- Independent review notes for benchmark claims and experiment records.
- Reproducibility guidance that preserves original stdout, stderr, timing, and
  metadata without rewriting raw evidence.
- Proposed regression checks using synthetic fixtures if and when a supported
  test harness exists.

## Acceptance criteria

- Every validation states what it proves and what it does not prove.
- A `PASS` claim is tied to the official verifier output and exact run evidence.
- Strict status remains **NOT REPRODUCED** where required execution provenance is
  absent.
- No score is invented, inferred from a partial check, or promoted without the
  official score output.
- Original competition artifacts and raw run outputs remain unchanged.

## Dependencies

- Read-only access to the existing reports and raw evidence.
- Source-backed verifier/API references for the relevant benchmark.
- A separate approved test harness before adding executable regression tests.

## Risks

- Treating structural validity as verifier acceptance.
- Treating a full verifier PASS as strict baseline reproduction despite missing
  provenance.
- Rewriting raw output or file metadata and destroying provenance.

## Proposed reviewer

Yousuf is the proposed reviewer for evidence conclusions and approval gates.
This reviewer assignment is **PROPOSED**.

## Status and acceptance record

| Field | Value |
|---|---|
| Work-package status | **PROPOSED** |
| Member acceptance | Not recorded |
| Acceptance date/channel | — |
| Proposed reviewer acceptance | Not recorded |

## Restrictions

- Do not modify official verifier code, competition artifacts, raw outputs, or
  existing execution evidence.
- Do not label parsing, schema validation, structural validation, or partial
  diagnostics as an official full-verifier PASS.
- Do not label INVSQRT or DFTHC-SOS as strict baseline reproduced without the
  missing provenance; keep DQI blocked absent explicit Yousuf approval.
- Do not run a full benchmark or start optimization without the required approval.
- Do not commit credentials or publish restricted competition files.

## Related documents

- [Team structure](../TEAM_STRUCTURE.md)
- [Responsibility matrix](../TEAM_RESPONSIBILITY_MATRIX.md)
- [Task board](../TEAM_TASK_BOARD.md)
- [INVSQRT workstream](../BENCHMARKS/INVSQRT.md)
- [DQI workstream](../BENCHMARKS/DQI.md)
- [DFTHC-SOS workstream](../BENCHMARKS/DFTHC-SOS.md)
