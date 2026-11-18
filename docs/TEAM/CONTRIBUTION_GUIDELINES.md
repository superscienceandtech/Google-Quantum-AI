# Contribution Guidelines

## Before starting

1. Read the [team structure](./TEAM_STRUCTURE.md), [task board](./TEAM_TASK_BOARD.md),
   and relevant [benchmark specification](./BENCHMARKS/).
2. Confirm that the proposed scope is still available and explicitly accept it
   before treating yourself as its owner.
3. Check current repository and remote state; branch names alone do not establish
   active work or ownership.
4. Confirm any experiment, full benchmark, or optimization has the required
   project-lead approval before execution.

## Scope and evidence

- Keep each change limited to its accepted issue/task scope.
- Cite primary sources and repository evidence for technical claims.
- Distinguish derived calculations, estimates, diagnostics, official verifier
  full executions, and strict baseline score reproduction.
- Preserve raw stdout, stderr, timing, and execution records; never rewrite or
  fabricate missing evidence.
- Record unavailable timestamps or metrics as unavailable rather than inferring
  them from filesystem metadata.
- A prototype or partial check must not replace an official baseline or be
  described as an official verifier PASS.

## Files and data handling

- Treat official verifier source, competition artifacts, sample submissions,
  shared libraries, and raw experiment output as read-only unless Yousuf
  explicitly authorizes a narrowly scoped change.
- Never commit credentials, tokens, private keys, `.env` files, Kaggle
  credentials, or restricted competition data.
- Do not add large external artifacts to Git without checking licensing,
  competition rules, repository size, and explicit project-lead approval.
- Keep generated files and temporary outputs outside source paths or in the
  approved ignored results area.
- Do not send sensitive data, credentials, or restricted artifacts to external
  services.

## Branch and pull-request practice

- Use the proposed issue-scoped branch patterns in the
  [GitHub workflow](./GITHUB_WORKFLOW.md) after checking the live remote.
- Do not push directly to `main`; use a reviewed pull request.
- Keep commits small and reviewable. The repository has no established commit
  convention, so the following is a recommendation, not an enforced rule:
  `type(scope): imperative summary`, using `docs`, `feat`, `fix`, `test`,
  `research`, or `chore` as appropriate.
- Do not amend or force-push shared history without explicit project-lead
  approval.
- Do not merge or publish before the final diff has been reviewed and the
  project lead explicitly approves publication.

## Pull-request checklist

- [ ] Linked task/issue and accepted or explicitly proposed ownership.
- [ ] Scope and restrictions match the task specification.
- [ ] Relevant tests/checks ran; commands and results are stated accurately.
- [ ] Evidence claims link to complete official outputs where required.
- [ ] No credential, official artifact, or raw execution output was included.
- [ ] Proposed reviewer was requested; review status is not misrepresented.
- [ ] No full benchmark or optimization ran without explicit approval.
- [ ] `git diff --check` is clean and generated files are understood.

Related: [review and acceptance policy](./REVIEW_AND_ACCEPTANCE_POLICY.md).
