# Srijon — Infrastructure and Security (Proposed)

**Assignment status:** PROPOSED
**Starting profile:** Web engineering and cybersecurity
**Member acceptance:** Not recorded

## Objective

Propose a safe, reproducible repository workflow and identify infrastructure
and security gaps without changing official competition files or claiming
unimplemented controls are active.

## Proposed scope

- Document repository structure and a safe developer setup path.
- Recommend CI configuration and bounded, non-benchmark test automation.
- Review dependencies and security risks using the actual verifier/runtime
  requirements as evidence.
- Recommend reproducible environment pinning and safe handling of generated data.
- Document branch-protection recommendations for project-lead review.

No CI, branch protection, dependency lock, or setup manifest was found in the
audited repository. These tasks are proposed work, not implemented controls.

## Context and evidence

The repository currently tracks only `README.md`; there is no project source,
test suite, setup manifest, or `.github` configuration. The ignored `external/`
tree contains official competition artifacts. Git LFS is unavailable in the
audited environment. GitHub reports WRITE access, but the main branch protection
endpoint returned 404, so protection status is unconfirmed.

The [baseline status matrix](../../BASELINE_STATUS_MATRIX.md) and raw records
must remain distinct: INVSQRT and DFTHC-SOS have historical full-verifier PASS
results but strict status **NOT REPRODUCED**; DQI is **BLOCKED** pending explicit
approval.

## Expected deliverables

- A reviewed repository/setup recommendation that distinguishes current state
  from proposed configuration.
- Safe CI/test recommendations that do not trigger full benchmarks.
- A dependency/security report with source versions and compatibility evidence.
- Branch-protection and review recommendations for Yousuf to accept or reject.
- A protected-file and secret-handling checklist for future pull requests.

## Acceptance criteria

- Every recommendation is labeled proposed until implemented and verified.
- No documentation says that CI, branch protection, or dependency pinning is
  already active unless new direct evidence confirms it.
- Automation is bounded and cannot launch full benchmark jobs by default.
- Security findings disclose no credential values and do not modify official
  verifier or artifact files.
- The final change list contains no official competition artifacts or raw
  execution outputs.

## Dependencies

- Project-lead approval of any remote branch-protection or GitHub setting change.
- A separately accepted scope and a documented authorization gate for any
  benchmark automation.
- Read-only reference to the dependency compatibility and verifier API reports.

## Risks

- A suggested protection rule could be mistaken for an already active control.
- CI defaults could accidentally start a high-resource benchmark.
- Dependency changes could alter verifier behavior or invalidate historical
  evidence.

## Proposed reviewers

- SeyamB — proposed review of safety checks and evidence-handling criteria.
- Yousuf — proposed review of repository policy and any remote-setting request.

Both reviewer assignments are **PROPOSED**.

## Status and acceptance record

| Field | Value |
|---|---|
| Work-package status | **PROPOSED** |
| Member acceptance | Not recorded |
| Acceptance date/channel | — |
| Proposed reviewer acceptance | Not recorded |

## Restrictions

- Do not modify official verifier logic, official competition artifacts, shared
  libraries, or raw execution evidence.
- Do not run full benchmarks or start optimization as part of setup or CI work.
- Do not configure branch protection or other remote settings without explicit
  project-lead approval.
- Do not install or upgrade packages without a verified compatibility reason.
- Do not commit credentials or publish restricted competition files.

## Related documents

- [Team structure](../TEAM_STRUCTURE.md)
- [Responsibility matrix](../TEAM_RESPONSIBILITY_MATRIX.md)
- [Task board](../TEAM_TASK_BOARD.md)
- [GitHub workflow](../GITHUB_WORKFLOW.md)
- [Dependency compatibility report](../../DEPENDENCY_COMPATIBILITY_REPORT.md)
- [Official verifier API reference](../../OFFICIAL_VERIFIER_API_REFERENCE.md)
