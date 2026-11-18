# DQI Workstream

## Status and objective

**Work-package status:** PROPOSED
**Full baseline status:** BLOCKED
**Execution approval:** Awaiting explicit Yousuf approval
**Optimization status:** Not authorized

Analyze the reversible Reed–Solomon decoder, official verifier API, confidence
bounds, and resource/complexity requirements. Prepare for a governed baseline
run without executing it. No task assignment or this specification authorizes
the 102,400-shot run.

## Context and current evidence

The official verifier defaults to 102,400 shots, batch size 256, and
`log2_delta=-128`; its default worker count is four. The existing approval
request proposes one worker due the observed memory use of small diagnostics.
There is no full 102,400-shot result: the existing run placeholders and
`BASE-DQI-001` raw stdout/stderr records are empty. No official full-verifier
PASS or baseline score exists.

The prepared command, estimated runtime/memory, timeout, and recovery procedure
are recorded in the
[DQI execution approval request](../../BASELINE_EXECUTION_APPROVAL_REQUEST.md).
That request is awaiting approval; the command has not been executed.

## Exact paths in scope

Read-only reference paths:

- `external/verifiers/dqi/verify_submission_dqi.py`
- `external/verifiers/dqi/dqi_reference_circuit.py`
- `external/sample_submission/dqi.kmb`
- `results/raw/`
- `docs/evidence/`
- `docs/BASELINE_EVIDENCE_RECONCILIATION.md`
- `docs/BASELINE_STATUS_MATRIX.md`
- `docs/BASELINE_EXECUTION_APPROVAL_REQUEST.md`
- `docs/OFFICIAL_VERIFIER_API_REFERENCE.md`
- `docs/SCORE_MODEL_VERIFICATION.md`
- `docs/COMPETITION_REQUIREMENTS_MATRIX.md`

The verifier, reference source, sample circuit, and existing raw evidence are
read-only. There is no candidate implementation path or project test suite in
the current repository; do not invent one in this workstream.

## Proposed ownership

- **Proposed workstream lead:** Mahin — decoder research, API/math analysis, and
  resource/complexity study.
- **Proposed evidence reviewer:** SeyamB — independent validation and evidence
  classification.
- **Execution approval authority:** Yousuf — explicit approval is required before
  the full run.

All work and reviewer assignments remain **PROPOSED** until accepted.

## Expected deliverables

- Source-backed analysis of reversible Reed–Solomon decoding, syndrome
  preservation, workspace cleanup, and target phase correctness.
- Official verifier API and input/output requirements summary.
- Confidence-bound and shot-count analysis, with derivations distinct from
  measured results.
- Resource/complexity estimates with assumptions and calculations recorded.
- A bounded diagnostic proposal, if needed, with specific authorization and
  evidence level recorded before execution.
- A baseline readiness checklist that references the existing approval request
  rather than silently changing or running its command.

## Acceptance criteria

- Decoder and verifier claims cite the official source or primary research
  material; undocumented behavior is not invented.
- The full baseline parameters are recorded as 102,400 shots, batch size 256,
  `log2_delta=-128`, and one worker for the proposed approved run.
- Confidence-bound results are compared with the official rejection threshold
  `eps_plus < 1/16`; diagnostics are not presented as full acceptance.
- The workstream clearly states that no full 102,400-shot execution or official
  score exists in the available records.
- No full run starts unless Yousuf explicitly approves the exact run.
- Optimization remains unauthorized until baseline governance requirements are
  met.

## Tests and verification required

No candidate source or test framework exists today. A future implementation's
test plan must include:

1. Reversible decoder tests for syndrome preservation, clean workspace, and
   correct target phase.
2. Confidence-bound tests for the verifier's `eps_plus < 1/16` acceptance
   threshold and shot-count calculations.
3. Resource-accounting checks that cover decoder workspace and the official
   score inputs.
4. A 102,400-shot official verifier run, only after explicit Yousuf approval.

This documentation task performs only path/existence and evidence-record checks;
it does not run the DQI verifier or any benchmark.

## Dependencies

- Explicit Yousuf approval of the 102,400-shot single-worker run and its
  execution boundary.
- A verified runtime with the official verifier dependencies.
- Read-only use of official verifier, sample, and current evidence records.
- A separately approved candidate implementation location and test strategy,
  if implementation is later authorized.

## Risks

- The 102,400-shot run is resource-intensive. Existing diagnostics used about
  3.5 GB peak RSS; the approval request estimates 3.5–4.0 GB for a single worker
  and proposes a 16-hour timeout. These are estimates, not guarantees.
- A partial diagnostic or parse may be mistaken for official acceptance.
- Decoder workspace or phase costs may be omitted from resource estimates.
- Running the full workload before approval would violate the project's
  execution gate.

## Restrictions and approval gate

- **Do not execute the 102,400-shot command without explicit Yousuf approval.**
- Do not run even a small diagnostic unless that diagnostic is authorized.
- Do not start optimization before baseline governance requirements are met.
- Do not modify official verifier code, competition artifacts, or raw execution
  evidence.
- Do not report a PASS, measured score, or full execution result unless the
  corresponding official output exists.
- Do not change the prepared command's shot count, worker count, or timeout
  without a new approval decision.

## Related documents

- [Team structure](../TEAM_STRUCTURE.md)
- [Responsibility matrix](../TEAM_RESPONSIBILITY_MATRIX.md)
- [Task board](../TEAM_TASK_BOARD.md)
- [DQI execution approval request](../../BASELINE_EXECUTION_APPROVAL_REQUEST.md)
- [Baseline evidence reconciliation](../../BASELINE_EVIDENCE_RECONCILIATION.md)
- [Baseline status matrix](../../BASELINE_STATUS_MATRIX.md)
- [Official verifier API reference](../../OFFICIAL_VERIFIER_API_REFERENCE.md)
- [Score model verification](../../SCORE_MODEL_VERIFICATION.md)
