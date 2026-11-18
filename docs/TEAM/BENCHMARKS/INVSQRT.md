# INVSQRT Workstream

## Status and objective

**Work-package status:** PROPOSED
**Strict baseline status:** NOT REPRODUCED
**Optimization status:** BLOCKED until strict baseline governance requirements
are met and Yousuf explicitly authorizes optimization.

Analyze the INVSQRT circuit contract, resource accounting, phase precision, and
reversible restoration. This document allocates analysis and preparation work;
it does not authorize candidate implementation, optimization, or a full
benchmark execution.

## Context and current evidence

The official operation is required over `x ∈ [1, 3,133,452]`, with 64 shots per
`x`, for 200,540,928 total shots. The existing raw records show two full
official-verifier executions with exit code 0 and PASS output. Both report score
`2076774.233715282`, 260 qubits, 7,735 Toffolis, and 7,987.593206597238
Toffoli-equivalent cost.

These are official full-execution results, not strict baseline reproduction:
required execution provenance is incomplete. Do not infer execution timestamps
from file mtimes or upgrade the status.

## Exact paths in scope

Reference-only paths:

- `external/verifiers/invsqrt/verify_submission_invsqrt.py`
- `external/verifiers/invsqrt/nr_reference_circuit.py`
- `external/sample_submission/invsqrt.kmb`
- `results/raw/`
- `docs/BASELINE_EVIDENCE_RECONCILIATION.md`
- `docs/BASELINE_STATUS_MATRIX.md`
- `docs/BASELINE_REPRODUCTION_REPORT.md`
- `docs/OFFICIAL_VERIFIER_API_REFERENCE.md`
- `docs/COMPETITION_REQUIREMENTS_MATRIX.md`
- `docs/SCORE_MODEL_VERIFICATION.md`

Official verifier, reference source, sample circuit, and raw evidence are
read-only. There is no candidate implementation path in the current repository;
do not invent one in this workstream.

## Proposed ownership

- **Proposed workstream lead:** Yousuf — architecture, research framing, and
  approval gate.
- **Proposed evidence reviewer:** SeyamB — independent validation and evidence
  classification.
- **Proposed tooling reviewer:** Srijon, only if implementation or test tooling
  is later proposed.

All assignments and reviewer roles are **PROPOSED** until explicitly accepted.

## Expected deliverables

- Circuit-contract analysis covering the all-input domain and tracked phase.
- Resource-accounting note that separates measured output from derived estimates.
- Reversible-restoration analysis, including register cleanliness and target
  phase correctness.
- A ranked list of testable optimization hypotheses, held for later review;
  listing a hypothesis does not authorize implementing or testing it.
- Evidence updates that link to existing raw results without rewriting them.

## Acceptance criteria

- The exact official domain, 64 shots per `x`, and 200,540,928 total shots are
  stated correctly.
- Measured metrics are traceable to official verifier output; estimates and
  hypotheses are labeled as such.
- Strict status remains **NOT REPRODUCED** until the missing provenance is
  established by sufficient evidence.
- The analysis does not start optimization or promote an unverified candidate.
- Any later claim of full acceptance is supported by complete official verifier
  output and the applicable approval record.

## Tests and verification required

No project source or test suite exists for a candidate implementation. Before
future candidate work is considered, its test plan must include:

1. Synthetic computational-basis checks for correct phase and restoration of
   clean/work registers.
2. Resource-accounting checks that independently verify qubit, Toffoli, T, and
   official cost calculations.
3. Regression checks against the official circuit contract for representative
   and boundary-domain inputs.
4. An official full-domain verifier run covering all 200,540,928 shots, only
   after explicit approval. A partial diagnostic cannot satisfy this criterion.

These are future requirements, not tests run by this documentation task.

## Dependencies

- Project-lead approval of any proposed experiment or optimization.
- Completion of the strict baseline provenance requirements before optimization.
- Independent evidence review and a test harness if candidate code is proposed.
- Read-only use of official verifier and sample artifacts.

## Risks

- The workload is large; a full run must not be launched from a documentation
  task or an unapproved experiment proposal.
- Treating the two historical PASS records as strict reproduction could bypass
  missing provenance gates.
- Incomplete restoration or phase accounting can invalidate an otherwise
  structurally valid circuit.
- Estimated resource improvements may not match the official verifier score.

## Restrictions and gates

- Do not modify the official verifier, reference circuit, sample submission, or
  raw evidence.
- Do not run a full benchmark without explicit authorization.
- Do not implement or execute optimization before strict baseline reproduction
  and explicit Yousuf approval.
- Do not describe a parse, schema check, structural check, or partial diagnostic
  as official full-verifier acceptance or baseline score reproduction.
- Do not promote or replace the official sample baseline with an unverified
  candidate.

## Related documents

- [Team structure](../TEAM_STRUCTURE.md)
- [Responsibility matrix](../TEAM_RESPONSIBILITY_MATRIX.md)
- [Task board](../TEAM_TASK_BOARD.md)
- [Baseline evidence reconciliation](../../BASELINE_EVIDENCE_RECONCILIATION.md)
- [Baseline status matrix](../../BASELINE_STATUS_MATRIX.md)
- [Official verifier API reference](../../OFFICIAL_VERIFIER_API_REFERENCE.md)
- [Score model verification](../../SCORE_MODEL_VERIFICATION.md)
