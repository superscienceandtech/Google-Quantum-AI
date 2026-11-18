# GitHub Workflow

## Current remote state

Audit performed 2026-11-19:

- The checked-out branch is `main` at `2b5906a`; only `README.md` is tracked.
- The remote `develop` branch exists at initial commit `5391b2e`. The following
  other remote branch names also exist at that initial commit:
  `docs/research-documentation`, `feat/compiler-infrastructure`,
  `feat/dfthcsos-factorization`, `feat/dqi-decoder`,
  `feat/invsqrt-optimization`, `research/competition-analysis`,
  `research/dfthcsos`, `research/dqi`, `research/invsqrt`, and
  `test/verification-regression`.
- These branch names do not prove active work or accepted ownership. Check the
  live remote and coordinate with Yousuf before reusing or replacing any branch.
- The authenticated account has WRITE permission. The main branch-protection
  endpoint returned 404; protection status is therefore **unconfirmed**.
- The inspected issue and pull-request lists were empty. No `.github` templates
  or CI configuration existed at audit time.

This is an audit snapshot, not a guarantee of current remote state. Recheck before
creating a branch or opening a pull request.

## Recommended branch model

These are recommendations only; no branch is created or configured by this
document.

- `main` — release history. Do not push directly.
- `develop` — proposed integration target, subject to project-lead review and
  confirmation that it is the intended integration branch.
- `docs/<issue-or-topic>` — documentation-only work.
- `feat/<benchmark>/<issue-or-topic>` — candidate implementation after baseline
  and scope approval.
- `research/<benchmark>/<issue-or-topic>` — isolated analysis and hypotheses.
- `test/<area>/<issue-or-topic>` — test and verification tooling.

Before using a branch name, check whether it already exists and who is using it.
Do not treat the currently stale remote branches as ready-to-use workspaces.
Branch protection and naming conventions remain proposed until accepted and
actually configured.

## Proposed pull-request flow

1. Confirm the work item, proposed owner, acceptance state, dependencies, and
   restrictions in the task board or GitHub issue.
2. Create or reuse an issue-scoped branch only after checking the live remote and
   confirming the owner.
3. Keep the change limited to the approved scope. Never push directly to `main`.
4. Open a pull request to `develop` for reviewed integration work, if Yousuf has
   confirmed `develop` as the integration target.
5. Link the work item, provide evidence and validation, request the proposed
   reviewer, and address review comments.
6. Promote from `develop` to `main` only through a separately reviewed release
   pull request after project-lead approval and applicable evidence gates.
7. Do not merge or publish until the project lead has reviewed the final diff and
   explicitly approved publication.

No automatic merge or release action is authorized by this workflow.

## Pull-request requirements

Every pull request should include:

- Linked task or issue and the accepted scope (or clearly marked proposed scope).
- Summary of changed paths and any behavior/evidence impact.
- Tests and documentation checks actually run, including commands and results.
- Evidence links for every verifier, score, or reproducibility claim.
- SHA-256 and byte size for candidate artifacts when their inclusion is
  authorized; never attach or commit restricted official artifacts.
- Reviewer request appropriate to the work; reviewers remain proposed until
  their assignments are accepted.
- Confirmation that official artifacts, raw evidence, and secrets were not
  changed or included.
- Explicit notice if any full benchmark ran, including prior authorization and
  the preserved raw outputs.

`PARTIAL` or `BLOCKED` validation cannot approve a release that requires official
full-verifier acceptance.

## Branch protection and review configuration

Branch protection is not confirmed by the audit. Before enabling rules, Yousuf
must review the proposed policy, inspect the live GitHub settings, and authorize
the change. Recommended controls are pull-request-only changes to `main`,
required independent review, required applicable CI checks, and no bypass for
release evidence gates. Do not describe these as active until verified in
GitHub.

## Remote-side-effect boundary

This file documents local recommendations only. It does not create branches,
issues, pull requests, labels, rulesets, branch protections, or repository
settings. Obtain project-lead approval before any such remote change.

Related: [team structure](./TEAM_STRUCTURE.md),
[task board](./TEAM_TASK_BOARD.md),
[contribution guidelines](./CONTRIBUTION_GUIDELINES.md), and
[review and acceptance policy](./REVIEW_AND_ACCEPTANCE_POLICY.md).
