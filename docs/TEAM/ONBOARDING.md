# Team Onboarding

## Start here

1. Read the [team structure](./TEAM_STRUCTURE.md) and
   [responsibility matrix](./TEAM_RESPONSIBILITY_MATRIX.md).
2. Review the [task board](./TEAM_TASK_BOARD.md) and the task specification
   relevant to your proposed scope.
3. Explicitly accept, decline, or request a revision to the proposed scope.
   Until acceptance is recorded, your assignment remains **PROPOSED**.
4. Read the [contribution guidelines](./CONTRIBUTION_GUIDELINES.md),
   [GitHub workflow](./GITHUB_WORKFLOW.md), and
   [review and acceptance policy](./REVIEW_AND_ACCEPTANCE_POLICY.md).
5. Confirm current branch and remote state before creating or reusing a branch.
   Existing remote names are stale audit observations, not active assignments.

## Repository state and setup limits

At the 2026-11-19 audit:

- Only `README.md` was tracked; the project has no application source, tests,
  Python/package manifest, CI workflow, or developer setup command.
- Audit documents and raw evidence exist locally as untracked files. Preserve
  them; do not assume they are published remotely.
- Official competition data and verifier files are in ignored `external/`.
- The external data directory is approximately 1.7 GB, and Git LFS is unavailable
  in the audited environment.
- Branch protection is unconfirmed; GitHub returned 404 for the main protection
  endpoint.

Do not install packages or create setup tooling merely to onboard. A reproducible
environment proposal must be reviewed and supported by compatibility evidence
before dependencies are installed or upgraded.

## Evidence and benchmark safety

- Treat `external/` and `results/raw/` as read-only.
- Do not run full benchmarks as an onboarding or setup check.
- Do not run the DQI 102,400-shot full baseline without explicit Yousuf approval.
- Do not begin optimization before baseline governance requirements are met.
- Preserve the status distinction: INVSQRT and DFTHC-SOS have historical full
  verifier PASS results but strict status **NOT REPRODUCED**; DQI is **BLOCKED**.
- Use the [baseline status matrix](../BASELINE_STATUS_MATRIX.md) and
  [evidence reconciliation](../BASELINE_EVIDENCE_RECONCILIATION.md) as the
  current evidence references.

## First contribution checklist

- [ ] Confirm scope and acceptance state with the project lead.
- [ ] Identify the issue/task and proposed reviewer.
- [ ] Check the current branch and remote; do not reuse a branch without
  confirming its owner.
- [ ] Work only in approved paths and preserve official artifacts/raw records.
- [ ] Run only the bounded checks required by the accepted task.
- [ ] Record exact commands and outputs for any authorized experiment.
- [ ] Submit a pull request using the repository template once it is available
  on the appropriate branch; do not push directly to `main`.
- [ ] Wait for review and explicit project-lead approval before merge or publish.

For questions about access to restricted data, credentials, or the execution
approval gate, contact Yousuf through the team's agreed private channel. Never
include secrets in an issue, pull request, or repository document.
