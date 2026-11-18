# Team Task Board

## How to read this board

This is a proposed allocation, not an assignment record. `PROPOSED` means the
member has not explicitly accepted the scope. A task may be discussed or
prepared without changing that status. Update ownership only after a recorded
acceptance; update benchmark evidence only when supported by the official
records.

Team-wide acceptance rules are in the
[team structure](./TEAM_STRUCTURE.md) and
[responsibility matrix](./TEAM_RESPONSIBILITY_MATRIX.md).

## Individual work packages

| ID | Work package | Proposed lead | Proposed reviewer | Dependencies | Proposed deliverable and acceptance criteria | Risk/restriction | Assignment status |
|---|---|---|---|---|---|---|---|
| TEAM-01 | Architecture and research leadership | Yousuf | SeyamB for evidence; Srijon for reproducibility | Project-lead decisions; member scope confirmation for delegated work | Research priorities, architecture decisions, cross-benchmark integration notes, and explicit baseline/optimization gates; acceptance requires evidence links and no unsupported PASS claims | No optimization before governance gates; no full run without required approval | **PROPOSED** |
| TEAM-02 | Independent research support | Sonjoy (only if confirmed) | Yousuf, proposed | Sonjoy's explicit availability and accepted scope | If accepted: one bounded literature review, algorithm comparison, or research reproduction with sources and reproducible notes; acceptance requires a written scope and review | No assumed ownership; do not transfer Yousuf's past tasks; no full benchmark without approval | **PROPOSED / UNCONFIRMED** |
| TEAM-03 | Infrastructure and security | Srijon | SeyamB for verification; Yousuf for architecture | Approved scope; repository and data-handling constraints | Setup and CI recommendations, dependency/security review, safe test automation, and reproducibility instructions; acceptance requires local checks and no official-artifact changes | No changes to official verifier or protected competition files; remote protections are not confirmed/configured | **PROPOSED** |
| TEAM-04 | Verification and data integrity | SeyamB | Yousuf | Read-only evidence access and agreed validation scope | Test inventory, checksum/input-output review, evidence-integrity checklist, and independent result review; acceptance requires explicit evidence-level classification | A parse, schema, structural, or partial check is not a full PASS or baseline reproduction | **PROPOSED** |
| TEAM-05 | DQI research | Mahin | SeyamB for evidence; Yousuf for approval | Verifier/API analysis; explicit Yousuf approval before any full 102,400-shot execution | Decoder and confidence-bound analysis, resource/complexity note, and authorized small diagnostics; acceptance requires source-backed claims and classified evidence | Full run remains blocked; no optimization before baseline gates | **PROPOSED** |
| TEAM-06 | Prototyping and experiment automation | SeyamR | Srijon for tooling; SeyamB for evidence | Approved experiment specification and isolated candidate path, if later established | Reproducible scripts, metadata capture, prototype, or report; acceptance requires a reproducible record and no baseline replacement | No unverified candidate may replace an official baseline; no unauthorized full run | **PROPOSED** |

Individual scope details: [Yousuf](./INDIVIDUAL_TASKS/YOUSUF.md),
[Sonjoy](./INDIVIDUAL_TASKS/SONJOY.md),
[Srijon](./INDIVIDUAL_TASKS/SRIJON.md),
[SeyamB](./INDIVIDUAL_TASKS/SEYAMB.md),
[Mahin](./INDIVIDUAL_TASKS/MAHIN.md), and
[SeyamR](./INDIVIDUAL_TASKS/SEYAMR.md).

## Benchmark workstreams

| ID | Workstream | Proposed lead | Proposed reviewer | Dependencies | Acceptance criteria | Risk/restriction | Work status | Strict baseline status |
|---|---|---|---|---|---|---|---|---|
| BENCH-INVSQRT | Circuit analysis, resource accounting, phase precision, reversible restoration, optimization hypotheses | Yousuf | SeyamB; Srijon for tooling | Baseline governance; explicit authorization before full execution or optimization | Source-backed analysis and correctly classified verifier evidence; no candidate promoted without authoritative evidence | Preserve two official PASS runs as historical evidence; do not upgrade strict status | **PROPOSED** | **NOT REPRODUCED** |
| BENCH-DQI | Reversible Reed–Solomon decoder, confidence bounds, resource accounting, approved baseline preparation | Mahin | SeyamB; Yousuf approval gate | Explicit Yousuf approval for the 102,400-shot run | Research claims cite verifier/source evidence; diagnostics are not called full acceptance; full run requires written approval | No 102,400-shot execution without explicit approval; no optimization | **BLOCKED** for full baseline | **BLOCKED** |
| BENCH-DFTHC-SOS | Factorization, Givens tree, ANGLE circuits, Lambda/gap constraints, resource analysis | Yousuf | SeyamB; Mahin for math | Baseline governance; explicit authorization before full execution or optimization | Evidence-backed analysis; strict thresholds and official results accurately reported; no candidate promoted without verification | Preserve two official PASS runs as historical evidence; do not upgrade strict status | **PROPOSED** | **NOT REPRODUCED** |

Detailed specifications: [INVSQRT](./BENCHMARKS/INVSQRT.md),
[DQI](./BENCHMARKS/DQI.md), and
[DFTHC-SOS](./BENCHMARKS/DFTHC-SOS.md).

## Evidence and approval gates

- INVSQRT has two raw full-verifier PASS records with score
  `2076774.233715282`; strict status remains **NOT REPRODUCED** because required
  provenance is incomplete.
- DFTHC-SOS has two raw full-verifier PASS records with score
  `3355599588.3155365`; strict status remains **NOT REPRODUCED** because required
  provenance is incomplete.
- DQI's full 102,400-shot execution is absent from the raw records. Its status
  remains **BLOCKED** pending explicit Yousuf approval.
- A partial diagnostic, file integrity result, schema check, or structural
  validation must never be treated as official baseline score reproduction.
- Optimization is not authorized by this board. No benchmark or full workload
  may be run without its required approval.

Source of record:
[baseline status matrix](../BASELINE_STATUS_MATRIX.md),
[baseline evidence reconciliation](../BASELINE_EVIDENCE_RECONCILIATION.md), and
[DQI approval request](../BASELINE_EXECUTION_APPROVAL_REQUEST.md).

## Proposed branch/workflow references

Existing remote branches are not proof that any work package has an owner or is
active. Follow the [GitHub workflow](./GITHUB_WORKFLOW.md); do not create a
duplicate branch or push directly to `main`.
