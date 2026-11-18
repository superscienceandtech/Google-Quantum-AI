# Team Structure

## Purpose and status

This guide describes the proposed six-person team for Google Quantum AI —
Verifiable Quantum Circuit Compilation. Member profiles come from the project
lead's team brief; work ownership is **PROPOSED** until each member explicitly
accepts a defined scope and that acceptance is recorded.

Yousuf is the project lead and approval authority. That role does not mean every
individual work package listed for Yousuf has already been accepted.

## Proposed roster

| Member | Starting profile | Proposed responsibility | Assignment status |
|---|---|---|---|
| Yousuf | Team Lead and Chief Research Architect; AI/ML, quantum research, architecture, and integration | Architecture, research priorities, cross-benchmark integration, approval gates, and final technical review | **PROPOSED** |
| Sonjoy | AI/ML profile | Potential independent AI/ML literature review, algorithm comparison, or bounded research reproduction | **PROPOSED / UNCONFIRMED** — availability and scope require explicit confirmation |
| Srijon | Web engineering and cybersecurity | Infrastructure, developer setup, safe CI/test automation, dependency/security review, and reproducibility | **PROPOSED** |
| SeyamB | Data cleaning, error detection, and validation | Verification strategy, evidence integrity, checksums, input/output validation, and independent result review | **PROPOSED** |
| Mahin | Web development and research | DQI decoder research, mathematical/API analysis, and resource/complexity analysis | **PROPOSED** |
| SeyamR | Rapid prototyping and implementation | Reproducible experiment tooling, isolated prototypes, metadata collection, and reporting | **PROPOSED** |

No member has accepted a task in the repository evidence inspected for this
audit. Do not treat a proposed reviewer or lead as confirmed ownership.

## Acceptance states

- **PROPOSED** — suggested scope; the member has not explicitly accepted it.
- **ACCEPTED** — the member explicitly accepted the scope and the acceptance,
  date, and channel are recorded in the responsibility matrix or task file.
- **DECLINED** — the member declined; the scope must be reassigned only after
  project-lead review.
- **ON HOLD** — the work is blocked by a dependency or approval gate; this does
  not imply acceptance.

Update the acceptance state only from an explicit response. Silence, profile
information, previous branch names, or prior work do not count as acceptance.

## Decision and safety boundaries

- Yousuf retains project-level architecture, baseline/optimization approval,
  cross-benchmark integration, and release decisions.
- The full DQI 102,400-shot baseline remains blocked until Yousuf explicitly
  approves execution. No team document or task assignment grants that approval.
- Optimization must not begin before baseline governance requirements are met.
- Official verifier source, competition artifacts, sample submissions, and raw
  experiment outputs remain read-only.
- No unverified candidate may replace an official baseline or be described as a
  verifier PASS.
- Every assignment and reviewer named elsewhere remains proposed until accepted.

Current benchmark statuses are recorded in the
[baseline status matrix](../BASELINE_STATUS_MATRIX.md): INVSQRT and DFTHC-SOS
have historical full-verifier PASS evidence but strict status **NOT REPRODUCED**;
DQI is **BLOCKED** pending explicit approval.

## Team operating documents

- [Responsibility matrix](./TEAM_RESPONSIBILITY_MATRIX.md)
- [Task board](./TEAM_TASK_BOARD.md)
- Individual proposed scopes:
  - [Yousuf](./INDIVIDUAL_TASKS/YOUSUF.md)
  - [Sonjoy](./INDIVIDUAL_TASKS/SONJOY.md)
  - [Srijon](./INDIVIDUAL_TASKS/SRIJON.md)
  - [SeyamB](./INDIVIDUAL_TASKS/SEYAMB.md)
  - [Mahin](./INDIVIDUAL_TASKS/MAHIN.md)
  - [SeyamR](./INDIVIDUAL_TASKS/SEYAMR.md)
- Benchmark workstreams:
  - [INVSQRT](./BENCHMARKS/INVSQRT.md)
  - [DQI](./BENCHMARKS/DQI.md)
  - [DFTHC-SOS](./BENCHMARKS/DFTHC-SOS.md)
- [GitHub workflow](./GITHUB_WORKFLOW.md)
- [Contribution guidelines](./CONTRIBUTION_GUIDELINES.md)
- [Review and acceptance policy](./REVIEW_AND_ACCEPTANCE_POLICY.md)
- [Onboarding](./ONBOARDING.md)
