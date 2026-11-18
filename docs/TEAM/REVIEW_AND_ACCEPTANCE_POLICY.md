# Review and Acceptance Policy

## Four separate decisions

Do not collapse these into one status:

1. **Task acceptance:** a member explicitly accepts the defined work scope.
2. **Change review:** a reviewer assesses a particular diff and its evidence.
3. **Verifier acceptance:** the official verifier reports acceptance for the
   candidate and workload.
4. **Baseline/release approval:** the required provenance is complete and Yousuf
   approves the next governance step.

A task being assigned, a pull request being approved, a file parsing
successfully, or a partial diagnostic passing does not prove the next decision.

## Assignment acceptance

- Every assignment begins **PROPOSED**.
- Acceptance requires an explicit response from the member naming or confirming
  the scope, recorded with date and channel in the
  [responsibility matrix](./TEAM_RESPONSIBILITY_MATRIX.md) or individual task
  file.
- Do not infer acceptance from historical branch names, repository permissions,
  prior task descriptions, silence, or project-lead status.
- Sonjoy's availability and scope remain unconfirmed until he explicitly accepts
  an option and Yousuf records it. Do not transfer Yousuf's past work to Sonjoy.
- A declined or blocked task requires project-lead review before reassignment.

## Change review

- A change author should not approve their own pull request.
- Request a reviewer with relevant expertise: proposed verification review by
  SeyamB, proposed infrastructure review by Srijon, proposed mathematical
  review by Mahin, or project-level review by Yousuf. These roles remain
  proposals until accepted.
- Reviewers should check task scope, source/evidence references, safety
  restrictions, tests, and whether the diff changes official artifacts or raw
  records.
- A review approval applies to the reviewed diff only. New commits or material
  changes require renewed review.
- Branch protection and required-review settings are not confirmed as active.
  Do not rely on an unverified GitHub setting.

## Evidence and verifier acceptance

Use the evidence categories in the
[baseline evidence reconciliation](../BASELINE_EVIDENCE_RECONCILIATION.md):

- File integrity, schema, register, structural, and partial diagnostic checks
  are not full-verifier acceptance.
- An official full-verifier PASS must be supported by raw output, exit status,
  workload coverage, resource record, and the relevant candidate/input identity.
- Strict baseline reproduction also requires the provenance items in the
  [baseline status matrix](../BASELINE_STATUS_MATRIX.md). A full-verifier PASS
  with missing provenance remains insufficient for that status.
- Do not invent a score or claim a result that is absent from the raw official
  output.

## Baseline and optimization gates

- INVSQRT and DFTHC-SOS currently have historical official full-verifier PASS
  records, but strict status remains **NOT REPRODUCED**.
- DQI's 102,400-shot full baseline is **BLOCKED** pending explicit Yousuf approval.
- No full benchmark run is authorized by task acceptance or pull-request review
  alone.
- Do not begin optimization before baseline governance requirements are met and
  Yousuf explicitly approves the transition.
- A sample parse, structural check, or small diagnostic cannot authorize
  optimization or release.

## Release approval

Yousuf must review the final diff, evidence, remaining risks, and applicable
benchmark acceptance before approving a release. No unreviewed change may be
merged into `main`; no publication, merge, or push is authorized until the
project lead explicitly approves it.
