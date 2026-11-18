# SeyamR — Prototyping and Automation (Proposed)

**Assignment status:** PROPOSED
**Starting profile:** Rapid prototyping and implementation
**Member acceptance:** Not recorded

## Objective

Propose reproducible experiment tooling and isolated prototypes that improve
iteration and reporting without changing official artifacts or replacing a
verified baseline with an unverified candidate.

## Proposed scope

- Prepare reproducible experiment scripts after a work package and candidate
  location are approved.
- Prototype benchmark ideas in an isolated branch or workspace.
- Capture experiment metadata, including inputs, command, environment, artifact
  hashes, timestamps when available, exit status, runtime, and peak memory.
- Prepare concise reporting and visualization for accepted experiments.
- Support benchmark automation only when it is bounded and explicitly approved.

No candidate-code directory is established in the current repository. Any
implementation location must be agreed through a separate architecture decision
before code is added.

## Context and evidence

The repository currently has no tracked implementation source or test suite.
INVSQRT and DFTHC-SOS have historical raw official full-verifier PASS results,
but strict status remains **NOT REPRODUCED**. DQI's full 102,400-shot run remains
**BLOCKED** pending explicit Yousuf approval.

See the [baseline status matrix](../../BASELINE_STATUS_MATRIX.md),
[experiment record standard](../../EXPERIMENT_RECORD_STANDARD.md), and
[benchmark task specifications](../BENCHMARKS/).

## Expected deliverables

- A proposed experiment automation interface and metadata schema.
- Reproducible scripts for accepted, bounded experiments.
- Isolated prototype results with explicit evidence classification.
- Experiment records that preserve exact commands, available timestamps, runtime,
  resource use, candidate/input checksums, and raw output references.
- Reports that separate measured verifier outputs from hypotheses and estimates.

## Acceptance criteria

- An experiment can be repeated from its recorded inputs and command where the
  environment permits.
- Missing timestamps or metrics are recorded as unavailable, never invented.
- Prototype results are not described as official verifier PASS or baseline
  score reproduction without the required run evidence.
- No candidate replaces an official baseline absent explicit approval and
  authoritative verification.
- Automation cannot launch full benchmarks by default.

## Dependencies

- Explicit acceptance of a benchmark-specific work package.
- Approved candidate location and bounded experiment design.
- Required project-lead authorization before any full benchmark or diagnostic
  execution.
- Read-only access to official verifier inputs and raw historical records.

## Risks

- Automated defaults could trigger expensive or unauthorized full workloads.
- Incomplete metadata could make an experiment unreproducible.
- A prototype could be mistaken for an accepted candidate.

## Proposed reviewers

- Srijon — proposed review of automation boundaries and reproducibility tooling.
- SeyamB — proposed review of metadata completeness and evidence classification.

Both reviewer assignments are **PROPOSED**.

## Status and acceptance record

| Field | Value |
|---|---|
| Work-package status | **PROPOSED** |
| Member acceptance | Not recorded |
| Acceptance date/channel | — |
| Proposed reviewer acceptance | Not recorded |

## Restrictions

- Do not modify official verifier code, competition artifacts, shared libraries,
  or raw experiment outputs.
- Do not run full benchmarks or diagnostics without the applicable explicit
  authorization.
- Do not begin optimization before baseline governance requirements are met.
- Do not let an unverified prototype replace or overwrite an official baseline.
- Do not create or push branches, publish results, or commit restricted files
  without the required project-lead approval.

## Related documents

- [Team structure](../TEAM_STRUCTURE.md)
- [Responsibility matrix](../TEAM_RESPONSIBILITY_MATRIX.md)
- [Task board](../TEAM_TASK_BOARD.md)
- [INVSQRT workstream](../BENCHMARKS/INVSQRT.md)
- [DQI workstream](../BENCHMARKS/DQI.md)
- [DFTHC-SOS workstream](../BENCHMARKS/DFTHC-SOS.md)
- [Experiment record standard](../../EXPERIMENT_RECORD_STANDARD.md)
