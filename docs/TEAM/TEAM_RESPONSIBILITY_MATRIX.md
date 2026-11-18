# Team Responsibility Matrix

## Status and interpretation

All responsibilities and reviewer assignments in this matrix are **PROPOSED**.
They become active only after the named member explicitly accepts the scope and
the acceptance is recorded. Proposed support or review is not accepted
ownership. See the [team structure](./TEAM_STRUCTURE.md) for role definitions
and status vocabulary.

## Proposed member responsibility matrix

| Member | Proposed responsibility | Proposed collaboration/review | Assignment status |
|---|---|---|---|
| Yousuf | Architecture and research leadership; cross-benchmark integration; baseline and optimization approval gates; final technical review | Proposed independent evidence review by SeyamB; proposed implementation/reproducibility review by Srijon | **PROPOSED** |
| Sonjoy | Potential independent AI/ML literature review, algorithm comparison, or bounded research reproduction | Scope and reviewer to be selected only after Sonjoy confirms availability and accepts a defined scope; Yousuf would review proposed scope | **PROPOSED / UNCONFIRMED** |
| Srijon | Repository setup, infrastructure, safe CI/test automation, dependency/security review, reproducibility | Proposed verification review by SeyamB; proposed architecture review by Yousuf | **PROPOSED** |
| SeyamB | Test inventory, checksum/evidence integrity, input/output validation, independent result review, reproducibility records | Proposed final review by Yousuf; proposed setup/tooling consultation with Srijon | **PROPOSED** |
| Mahin | DQI reversible Reed–Solomon decoder research, verifier/API analysis, mathematical and resource/complexity analysis | Proposed evidence review by SeyamB and approval-gate review by Yousuf | **PROPOSED** |
| SeyamR | Reproducible scripts, benchmark automation, isolated prototypes, metadata collection, and reporting | Proposed tooling review by Srijon and evidence review by SeyamB | **PROPOSED** |

## Proposed benchmark review assignments

| Workstream | Proposed lead | Proposed reviewer | Status and gate |
|---|---|---|---|
| INVSQRT | Yousuf | SeyamB for evidence; Srijon for tooling where applicable | Work assignment PROPOSED; strict baseline status **NOT REPRODUCED** |
| DQI | Mahin | SeyamB for evidence; Yousuf for execution approval | Work assignment PROPOSED; full baseline **BLOCKED** pending explicit Yousuf approval |
| DFTHC-SOS | Yousuf | SeyamB for evidence; Mahin for mathematical analysis where applicable | Work assignment PROPOSED; strict baseline status **NOT REPRODUCED** |

Reviewers are proposed peers, not confirmed task owners. A reviewer must not
approve a full benchmark execution, baseline promotion, or release on Yousuf's
behalf.

## Acceptance register

| Member | Scope accepted? | Date | Evidence/channel | Status |
|---|---|---|---|---|
| Yousuf | No acceptance recorded for these proposed task scopes | — | — | **PROPOSED** |
| Sonjoy | No response recorded; availability and scope unconfirmed | — | — | **PROPOSED / UNCONFIRMED** |
| Srijon | No response recorded | — | — | **PROPOSED** |
| SeyamB | No response recorded | — | — | **PROPOSED** |
| Mahin | No response recorded | — | — | **PROPOSED** |
| SeyamR | No response recorded | — | — | **PROPOSED** |

Update this register only from an explicit response. Do not infer acceptance
from branch names, repository permissions, past contributions, or silence.

## Shared restrictions

- Official verifier source, competition artifacts, shared libraries, and raw
  experiment outputs remain read-only.
- Do not run the DQI 102,400-shot baseline without explicit Yousuf approval.
- Do not begin optimization before baseline governance requirements are met.
- Do not call structural checks or partial diagnostics an official verifier PASS.
- Do not promote or replace an official baseline with an unverified candidate.
- Do not commit credentials or competition artifacts, and do not publish or
  merge without the project lead's approval.

See the [task board](./TEAM_TASK_BOARD.md) and
[individual task files](./INDIVIDUAL_TASKS/) for proposed scope and acceptance
criteria.
