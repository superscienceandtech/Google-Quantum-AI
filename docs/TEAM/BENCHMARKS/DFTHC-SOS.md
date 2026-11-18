# DFTHC-SOS Workstream

## Status and objective

**Work-package status:** PROPOSED
**Strict baseline status:** NOT REPRODUCED
**Optimization status:** BLOCKED until strict baseline governance requirements
are met and Yousuf explicitly authorizes optimization.

Analyze factorization, Givens-tree inputs, ANGLE circuits, Lambda and energy-gap
constraints, and resource accounting. This document proposes an analysis and
validation workstream; it does not authorize implementation, optimization, or a
full benchmark execution.

## Context and current evidence

Two raw full-verifier runs, 002 and 003, report official PASS with score
`3355599588.3155365`. The recorded output includes `Lambda=308.4559397330944`,
`E_gap=3.965477244291833`, residuals `0.0031851950317991775` and
`0.018639570630974073`, `T_total=93237`, `Q_total=730`, and 254,464 verified
shots.

These are official full-execution results, not strict baseline reproduction:
required execution provenance is incomplete. Do not infer run timestamps from
file mtimes or upgrade the status.

The verifier requirements include residuals no greater than `0.020 Ha`,
strict `Lambda > 49.0 Ha`, strict `E_gap > 3.914898 Ha`, and
`0 < E_gap < 2*Lambda`. The ANGLE width cap is 128 qubits, and `Z_POW` is
forbidden inside ANGLE circuits. These constraints are recorded in the
[competition requirements matrix](../../COMPETITION_REQUIREMENTS_MATRIX.md) and
[score model verification](../../SCORE_MODEL_VERIFICATION.md).

## Exact paths in scope

Read-only official inputs and verifier:

- `external/verifiers/dfthcsos/verify.py`
- `external/verifiers/dfthcsos/FeMoCo76o113e.fcidump`
- `external/verifiers/dfthcsos/FeMoCo76o113e.fixed_shifts.npz`
- `external/verifiers/dfthcsos/scoreinfra/`
- `external/sample_submission/dfthcsos/submission.npz`
- `external/sample_submission/dfthcsos/angle_k_0.kmb`
- `external/sample_submission/dfthcsos/angle_k_1.kmb`
- `external/sample_submission/dfthcsos/angle_k_2.kmb`
- `external/sample_submission/dfthcsos/angle_k_3.kmb`
- `external/sample_submission/dfthcsos/angle_k_4.kmb`
- `external/sample_submission/dfthcsos/angle_k_5.kmb`
- `external/sample_submission/dfthcsos/angle_k_6.kmb`
- `external/sample_submission/dfthcsos/angle_k_7.kmb`
- `external/sample_submission/dfthcsos/angle_k_8.kmb`
- `external/sample_submission/dfthcsos/angle_k_9.kmb`
- `results/raw/`
- `docs/BASELINE_EVIDENCE_RECONCILIATION.md`
- `docs/BASELINE_STATUS_MATRIX.md`
- `docs/BASELINE_REPRODUCTION_REPORT.md`
- `docs/OFFICIAL_VERIFIER_API_REFERENCE.md`
- `docs/COMPETITION_REQUIREMENTS_MATRIX.md`
- `docs/SCORE_MODEL_VERIFICATION.md`

Official verifier, FeMoCo data, fixed shifts, sample submission, and raw
evidence are read-only. There is no candidate implementation path in the
current repository; do not invent one in this workstream.

## Proposed ownership

- **Proposed workstream lead:** Yousuf — architecture, research framing, and
  approval gate.
- **Proposed evidence reviewer:** SeyamB — independent validation and evidence
  classification.
- **Proposed math reviewer:** Mahin, if accepted for this workstream.

All assignments and reviewer roles are **PROPOSED** until explicitly accepted.

## Expected deliverables

- Factorization analysis with source-backed assumptions and data-integrity checks.
- Givens-tree and ANGLE circuit analysis covering all ten circuits.
- Resource accounting for `Lambda`, `E_gap`, `lambda_eff`, `T_total`, and
  `Q_total`, with measured values distinguished from estimates.
- A ranked list of testable optimization hypotheses held for later review;
  listing a hypothesis does not authorize implementation or execution.
- Evidence updates that link to existing raw results without rewriting them.

## Acceptance criteria

- Both residuals satisfy `<= 0.020 Ha`; Lambda satisfies the strict `> 49.0 Ha`
  floor; E_gap satisfies strict `> 3.914898 Ha` and `0 < E_gap < 2*Lambda`.
- All required ANGLE circuits and submission data are accounted for; each ANGLE
  circuit stays within 128 qubits and contains no forbidden `Z_POW`.
- Resource counts and the official score formula use source-backed definitions.
- Historical PASS results remain separate from strict baseline status
  **NOT REPRODUCED** until the missing provenance is established.
- No candidate is promoted without the applicable approval and authoritative
  verifier evidence.

## Tests and verification required

No candidate source or test framework exists today. A future implementation's
test plan must include:

1. Input/factorization checks that validate the expected data shape and derived
   residuals without modifying official inputs.
2. Per-circuit structural checks for the `selection` and `word_*` registers,
   clean workspace and addresses, the ANGLE qubit cap, and forbidden gates.
3. Independent resource-accounting checks for `lambda_eff`, `T_total`,
   `Q_total`, and score calculation.
4. An official full-verifier run over the complete 254,464-shot workload, only
   after explicit authorization. Structural checks are not a substitute.

These are future requirements, not tests run by this documentation task.

## Dependencies

- Project-lead approval of any proposed experiment or optimization.
- Completion of strict baseline provenance requirements before optimization.
- Independent evidence and mathematical review.
- Read-only use of official verifier, data, fixed shifts, and sample circuits.

## Risks

- A malformed or modified input dataset could invalidate otherwise correct
  factorization calculations.
- Equality at a strict Lambda or energy-gap floor is rejected.
- Resource-accounting omissions can produce a false score estimate.
- The full verifier workload must not be launched from a documentation task or
  an unapproved proposal.

## Restrictions and gates

- Do not modify official verifier code, FeMoCo data, fixed shifts, sample
  circuits, or raw execution evidence.
- Do not run a full benchmark without explicit authorization.
- Do not implement or execute optimization before strict baseline reproduction
  and explicit Yousuf approval.
- Do not describe a path, schema, or structural check as official full-verifier
  acceptance or baseline score reproduction.
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
