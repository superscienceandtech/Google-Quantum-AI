# DQI-P005 — Evidence and Authorization Gap Closure Plan

- **Project:** Google Quantum AI — Verifiable Quantum Circuit Compilation
- **Workstream:** DQI Decoder
- **Developer named by directive:** Sonjoy
- **Required branch:** `feat/dqi-decoder`
- **Assessment date:** 2026-11-20
- **Final disposition:** **BLOCKED**

## 1. Executive Summary

P004's reported blockers were checked against the actual P004 report and the
available governance records. They remain open. The official executable
verifier/scorer, reference circuit, sample circuit, official fixtures, and
expected outputs are not present in the inspected worktree or the refs
documented by P004. Repository documents contain summaries and digests, but
not the bytes needed to validate those claims. The arXiv v2 paper supports
research-level mathematics and methodology; it does not establish executable
verifier behavior.

The governance documents still mark the DQI work package proposed, Sonjoy's
availability and acceptance unconfirmed, baseline execution pending explicit
Yousuf approval, and optimization unauthorized. The project-lead approval of
a Sonjoy-defined scope and independent reviewer acceptance are not recorded.
Read-only inspection of named reference paths is permitted; that does not
permit execution or imply permission to acquire through a restricted channel.

This plan identifies the evidence, approvals, and acceptance checks required
to close those gaps. It does not acquire artifacts, perform tests, execute
diagnostics, or modify any authorization state. **Disposition: BLOCKED.**

## 2. Repository and Branch Identity

- Repository root: `D:\PROJECT\Quantum_AI\Google-Quantum-AI`
- Branch: `feat/dqi-decoder`
- Initial HEAD: `5391b2e7123484efacffc0588f5e761e67b5cb55`
- Staged tracked changes at start: none.
- Unstaged tracked changes at start: none.
- Existing untracked files at start:
  - P001, P002, P003, and P004 reports in `docs/research/`.
  - INVSQRT bytecode caches in `src/invsqrt_opt/__pycache__/`,
    `src/invsqrt_opt/candidates/__pycache__/`, and `tests/__pycache__/`.
- P005 destination did not exist at task start.

The complete initial untracked-file list was recorded and will be preserved.
No branch change, staging, commit, push, merge, cherry-pick, reset, or clean
operation is permitted or performed by this phase.

## 3. P001–P004 Continuity Verification

All four reports exist in the worktree and are untracked at initial HEAD.
Their SHA-256 values were checked before this P005 edit:

| Report | Bytes | SHA-256 |
|---|---:|---|
| `docs/research/DQI_P001_DEVELOPMENT_FOUNDATION.md` | 18,717 | `dc44f79bd38e7bd38566fc11e3234b0ece5c8adca52b66ece9823e13634eb0f8` |
| `docs/research/DQI_P002_TECHNICAL_CONTRACT.md` | 23,206 | `48e8772d49425cc50c0694ff7b133a7f58af1f218452a2a6ddece8bcb1eec516` |
| `docs/research/DQI_P003_EVIDENCE_READINESS_REPORT.md` | 31,957 | `0f47d0f4c59cdd040a569e7fc55c7a4127e69147f7a530ef2a16741dc4415163` |
| `docs/research/DQI_P004_AUTHORIZED_VERIFIER_FIXTURE_INTAKE.md` | 35,153 | `5496f8817f6835d2eeaa28a6e9f08f84579588eef1ddaac8d2510f6f96131167` |

These are content-integrity identifiers for the local working-tree reports,
not official artifact hashes or commit IDs. P001–P004 were read for
continuity and remain unmodified.

## 4. P004 Findings Reconciliation

The actual P004 report, especially §§4, 6–10, 11–14, and 20, supports the
following carried-forward findings:

| P004-reported finding | Rechecked status | Basis |
|---|---|---|
| Final status is BLOCKED | **Confirmed** | P004 §20 |
| Official executable verifier/scorer unavailable | **NOT FOUND / NOT VERIFIED** | P004 §§5–7 and §10 |
| Official reference circuit unavailable | **NOT FOUND / NOT VERIFIED** | P004 §8 |
| Official sample circuit unavailable | **NOT FOUND / NOT VERIFIED** | P004 §8 |
| Official fixture bundle and expected outputs unavailable | **NOT FOUND / NOT VERIFIED** | P004 §9 |
| Immutable provenance for unavailable executable artifacts | **NOT VERIFIED** | P004 §§5–10 |
| Sonjoy work-package acceptance | **NOT VERIFIED** | P004 §4; `origin/main:docs/TEAM/INDIVIDUAL_TASKS/SONJOY.md` |
| Project-lead approval of Sonjoy scope | **NOT VERIFIED** | P004 §4; same acceptance record and responsibility matrix |
| Diagnostic execution | **NOT AUTHORIZED** | P004 §15; DQI governance |
| Full baseline execution | **PENDING** | P004 §16; approval request explicitly awaits Yousuf |
| Optimization | **NOT AUTHORIZED** | P004 §17; DQI governance |
| Independent review/final acceptance | **NOT VERIFIED** | P004 §4; assignments remain proposed |

No P004 finding was upgraded based on this plan. No discrepancy was found
between the P004 document and these carried-forward findings.

## 5. Evidence Gap Register

“Owner not identified” means no accepted artifact owner or official publisher
is named in the repository records inspected. Proposed team roles are not
treated as accepted ownership.

| ID | Artifact / contract gap | Expected path or identity | Current evidence and status | Missing evidence / provenance | Closure acceptance criteria | Intake permission |
|---|---|---|---|---|---|---|
| G-01 | Official verifier source | `external/verifiers/dqi/verify_submission_dqi.py` (repository-documented path) | **ABSENT** in P004's inspected local paths and refs | Official source bytes, release/commit, publisher, version, license, runtime/dependencies, SHA-256 | Source is readable; publisher/release and commit are traceable; locally computed digest matches its published digest; entry point is in source | Read-only inspection of listed paths is recorded as allowed; official acquisition channel/permission must be confirmed |
| G-02 | Verifier entry point and invocation | Same verifier; exact CLI/API not established | Repository API/CLI summaries conflict; executable entry point unavailable | Actual callable/CLI, required arguments, environment, exit codes, timeout and failure rules | Invocation can be derived directly from official source/docs and is consistent with official example/test vectors | No execution without separate diagnostic/baseline authorization |
| G-03 | Verifier input schema | Official verifier schema, not located | **ABSENT** as executable contract | Circuit input format/version; register names, widths, ordering, serialization, validation | Schema is directly specified by official source and at least one official valid fixture; malformed cases have expected outcomes | Read-only inspection only |
| G-04 | Verifier output schema | Official verifier result schema, not located | **ABSENT** | Output fields/types, score/result semantics, failure output and exit behavior | Schema is documented in official source and validated against official expected output fixtures | Inspection allowed only through authorized source path; execution remains separately gated |
| G-05 | Validation/rejection conditions | Official verifier checks, not located | **PARTIAL**: summaries describe checks; implementation absent | Exact input rejections, correctness checks, threshold handling, error categories | Each documented rejection/acceptance case has source reference and corresponding official fixture or test vector | Inspection only |
| G-06 | Official scorer | Verifier/scorer release; exact separate filename unknown | **ABSENT** as executable implementation | Official scoring implementation/version and known output vectors | Formula, precision, thresholds, and emitted result are source-traceable and match official expected outputs | Inspection only |
| G-07 | Resource-counting implementation | Official scorer/parser | **ABSENT**; paper-level resource definitions only | Exact `Q`, `T`, gate normalization, cleanup inclusion, aggregation and serialization rules | Independently reproduce counts from official examples/circuit and match expected values | Inspection only; running scorer requires explicit authorization |
| G-08 | Statistical acceptance implementation | Official verifier source | **PARTIAL** at research-paper level; executable behavior absent | Exact confidence-bound implementation, seed/salt derivation, random inputs, defaults, threshold checks | Source and official test vectors pin down `N`, confidence, upper-bound calculation, seed construction, and reject boundary | Inspection only; diagnostics/baseline require separate permission |
| G-09 | Reference circuit | `external/verifiers/dqi/dqi_reference_circuit.py` (documented path) | **ABSENT** | Official source bytes, version, release/commit, digest, algorithm-to-paper mapping | Provenance and digest independently verified; code is readable and its role is stated by official source | Read-only inspection only |
| G-10 | Sample submission | `external/sample_submission/dqi.kmb` (documented path; `.kmx` also appears in summaries) | **ABSENT**; reported hash not matched to bytes | Exact official filename/format/version and bytes; published or independently verifiable digest | Received bytes parse according to official format and SHA-256 matches authoritative manifest | Read-only inspection only |
| G-11 | Circuit serialization format | Official schema/parser | **PARTIAL**: repository summaries mention `.kmb`/`.kmx`; paper describes kickmix | Format specification/version, encoding, canonicalization, compatibility rules | Official parser/schema and fixtures establish accepted format and canonical representation | Inspection only |
| G-12 | Register/wire ordering | Official verifier, circuit schema, fixtures | **CONFLICTING / NOT VERIFIED**: API summary names `S_i`/`E_j`; paper names logical `s`/`c`; later audit says mapping absent | Ordered registers, field-element bits, endian convention, mapping of classical `c`, wire-to-coordinate mapping | Explicit source mapping plus fixtures whose expected inputs/outputs disambiguate each order | Inspection only |
| G-13 | Gate/operation conventions | Official verifier/parser | **PARTIAL**: paper describes instruction families; summary mentions `Z_POW` rejection | Full accepted/rejected operation list and decomposition/counting behavior | Official source and positive/negative fixtures establish legality and resource accounting | Inspection only |
| G-14 | Workspace, initialization, cleanup | Official reference circuit and verifier contract | **PARTIAL** at paper-level transform; circuit artifact absent | Workspace allocation/initial state, ancilla bounds if any, cleanup check and treatment of off-promise inputs | Official contract and fixtures state required initial/final workspace and verifier check; no assumed resource cap | Inspection only |
| G-15 | Official valid fixtures | Official fixture bundle; exact path not identified | **ABSENT** | Valid input bytes, expected result, generator/source, release and digest manifest | Fixtures are attributable to official source and each expected output is independently tied to that fixture | Read-only inspection; no synthetic substitutes |
| G-16 | Official invalid fixtures | Official fixture bundle; exact path not identified | **ABSENT** | Invalid input classes and expected rejection/output/exit status | Official fixtures cover documented validation failures and expected outcomes | Read-only inspection |
| G-17 | Boundary fixtures | Official fixture bundle; exact path not identified | **ABSENT** | Correctable-domain boundary, malformed/minimal/maximal registers, and statistical threshold boundary as applicable | Official expected decisions/outputs cover the boundary conditions declared by source | Read-only inspection |
| G-18 | Expected verifier and score outputs | Fixture manifest or official result corpus | **ABSENT** | Result schema, expected validity, errors, resource counts, confidence fields, score | Each result is linked to immutable input and verifier/scorer version; values match on any separately approved run | Inspection only; execution requires its own gate |
| G-19 | DQI scope ownership | Governance acceptance record | **NOT VERIFIED** | Sonjoy's explicit availability/scope acceptance plus project-lead recording of scope/date/channel | Both records exist in authorized governance process and the scope is bounded | Not an artifact-intake permission |
| G-20 | Independent reviewer | Governance assignment/acceptance record | **NOT VERIFIED**; proposed roles only | Named reviewer acceptance, scope, independence, review output and final authority | Assignment and acceptance recorded; review outcome recorded separately from execution approval | No reviewer name is presumed |

The official competition/verifier artifact owner is **OWNER NOT IDENTIFIED**
in the inspected repository records. The project lead is not presumed to be
the artifact publisher.

## 6. Official Verifier and Scorer Requirements

The following exact requirements must be requested, not inferred from
secondary summaries:

| Requirement | Evidence required to close gap | Current unresolved point |
|---|---|---|
| Source and release identity | Official repository/source URL, immutable commit or release/version, publisher identity, license, dependency/runtime manifest | No executable source or release ID is present |
| Entry point and invocation | Official callable/CLI, exact arguments, input location, output channels, exit codes, timeout and error handling | API and CLI summaries conflict; do not invent a command |
| Input/output schema | Versioned schema with field types, register and serialization rules, result fields, failure representation | No actual parser/schema/output observed |
| Validation/rejection | Official list of accepted and rejected inputs, operation restrictions, correctness checks, statistical rejection behavior | Summary claims cannot establish actual code paths |
| Scoring | Executable score calculation and expected score vectors | Paper Eq. (43) is not the scorer implementation |
| Resource accounting | Exact qubit and Toffoli counting, including workspace and cleanup, operation mapping and aggregation | Paper says `Q` includes workspace and `T` includes cleanup; repository summary wording about `T` conflicts |
| Statistical acceptance | Exact sample construction, shot count, confidence-bound implementation, seed/salt rules, threshold and defaults | Paper specifies a model; executable behavior/defaults remain unverified |
| Integrity | Published artifact hashes plus local SHA-256 of received bytes; provenance chain for every dependency/binary | Summary-recorded hashes are unmatched to bytes |

Repository secondary evidence is versioned at `origin/main` commit
`3861f76f4842f40e70fc59ad69812052c2719f32`: `docs/COMPETITION_REQUIREMENTS_MATRIX.md`,
`docs/OFFICIAL_VERIFIER_API_REFERENCE.md`, and
`docs/SCORE_MODEL_VERIFICATION.md`. P004 §10 records their Git blob IDs and
SHA-256 values. These documents identify claims and requested paths, not the
missing official executable artifacts.

## 7. Reference and Sample Circuit Requirements

The acquisition request must include:

- The official reference circuit and the official sample submission, each
  with exact filename, format/version, publisher/release, commit or release
  ID, size, and authoritative SHA-256.
- An official format/schema description that defines serialization,
  register declarations, register order, wire order, field-element bit order,
  and how logical inputs bind to circuit registers.
- The accepted gate/operation conventions, including any disallowed
  operations and resource-counting normalization.
- The required initial state, workspace/ancilla conditions, cleanup
  requirement, and output interpretation. Do not infer a maximum workspace
  limit from a reference circuit's reported qubit count.
- A source-backed mapping between mathematical coordinates and circuit
  registers/wires, including whether the API summary's classical `E_j`
  registers correspond to the paper's `c`. Equal bit counts are not proof.
- The relation, if any, between the paper's internal-run commitment
  `0701f553a9ac4e8af100f66acfccf2fc82cf5a44c2e5aa765b1d4ace01cbaadb` and
  the repository-reported sample hash
  `959471d05a26373b4f14ca0cae2d8639ea25f18170d9f6532139aa51ccc04995`.
  Do not equate them absent bytes and an authoritative manifest.

Known documented paths are
`external/verifiers/dqi/dqi_reference_circuit.py` and
`external/sample_submission/dqi.kmb`; the alternative `.kmx` extension appears
in repository summaries but is not confirmed as the official sample filename.
The competition artifact owner is not identified. Any delivery must use an
authorized source and remain read-only.

## 8. Fixture and Expected-Output Requirements

Request an official, versioned fixture manifest and the exact fixture files;
do not create replacements. The bundle should identify, where provided by the
official source:

1. Valid fixtures with canonical input bytes and expected verifier decisions.
2. Invalid fixtures with rejection category, expected exit/output behavior,
   and validation rule.
3. Boundary cases for the documented correctable domain, register/schema
   constraints, and score/statistical threshold semantics.
4. Expected resource metrics and score outputs, with the exact verifier and
   scorer release used to produce them.
5. Provenance for each input/output pair: source, release/commit, generator if
   applicable, size, and SHA-256.

The report must label a paper example or locally derived vector as
research-derived, not an official fixture. P004 found no official valid,
invalid, boundary, expected-output, or fixture-provenance bytes in its
inspected paths and refs. No fixture should be copied to protected locations
or executed until its receipt and intended use are separately authorized.

## 9. P002 Technical Contract Gap Matrix

Status definitions for this plan: `RESOLVED_FROM_PRIMARY_SOURCE` means only
the published claim is directly supported by primary research;
`RESOLVED_FROM_EXECUTABLE_ARTIFACT` requires inspected official executable
bytes; `PARTIALLY_RESOLVED` means research details exist but critical
executable mapping remains; `CONFLICTING` means repository summaries disagree;
`ABSENT` means no adequate source was located; `NOT_VERIFIED` means the claim
or provenance cannot currently be confirmed. A paper claim is never proof of
verifier behavior.

| Contract question | Current status | Evidence and remaining closure condition |
|---|---|---|
| Decoder mathematical semantics | `PARTIALLY_RESOLVED` | arXiv v2 §§III.2.1–III.2.2 describes the research target; official executable conformance is unverified. |
| Finite-field polynomial and basis | `RESOLVED_FROM_PRIMARY_SOURCE` | arXiv v2 §III.2.2 states the field polynomial and little-endian polynomial basis. Confirm implementation/serialization against official artifacts. |
| Evaluation-point convention | `RESOLVED_FROM_PRIMARY_SOURCE` | Paper gives `alpha_j=alpha^j`; executable mapping remains unverified. |
| Syndrome ordering and indexing | `RESOLVED_FROM_PRIMARY_SOURCE` | Paper gives the mathematical indexed syndrome equation; register-to-coordinate order is not executable-verified. |
| Decoder input representation | `PARTIALLY_RESOLVED` | Paper's logical inputs are described, but official serialized registers and input schema are absent. |
| Register/bit/wire ordering | `CONFLICTING` | Secondary API summary and later readiness summary do not establish the same mapping; official parser and fixtures are needed. |
| Error-weight and decoding radius | `RESOLVED_FROM_PRIMARY_SOURCE` | Paper specifies its research instance and radius; official executable instance conformance remains to be checked. |
| Reversible output semantics | `RESOLVED_FROM_PRIMARY_SOURCE` | Paper states syndrome preservation, clean workspace, and phase action on the promised domain; executable acceptance behavior is unverified. |
| Workspace initialization and cleanup | `PARTIALLY_RESOLVED` | Paper describes clean output and inverse EEA; actual circuit allocation and verifier checks are absent. |
| Exact verifier input/output schema | `ABSENT` | No executable verifier or official schema was found. |
| Resource metrics and counting | `CONFLICTING` | Paper defines a research score and cleanup accounting; the local summary wording for `T` differs. Obtain scorer source and vectors. |
| Statistical acceptance | `PARTIALLY_RESOLVED` | Paper specifies shot/confidence model and threshold; official code, seed construction, and operational defaults absent. |
| Official verifier/scorer identity | `ABSENT` | No source, immutable release, or independently matched digest. |
| Official fixtures and expected outputs | `ABSENT` | No fixture bytes, expected results, or provenance manifest. |

No row is marked `RESOLVED_FROM_EXECUTABLE_ARTIFACT` because no official
executable artifact was available to inspect.

## 10. Artifact Acquisition Request

The requests below are for a later authorized intake; P005 does not download,
install, execute, or copy any artifact.

| Request | Exact item and reason | Known source/owner | Provenance and integrity required | Acceptance check after receipt | Does receipt authorize execution? |
|---|---|---|---|---|---|
| A-01 | Official verifier/scorer source or immutable release; closes G-01–G-08 and the verifier/API/statistical/resource gaps in P002/P004 | **OWNER NOT IDENTIFIED**; use official competition source through authorized channel | Publisher, source URL, release/commit, version, license, runtime/dependency manifest, published hashes; compute local SHA-256 | Inspect source without running; compare bytes to authoritative manifest; map entry point/schema/scorer functions to docs and official test vectors | **No.** Diagnostic and baseline execution require separate approvals |
| A-02 | Official reference circuit and official sample submission; closes G-09–G-14 and P002 register/circuit gaps | Paths documented in DQI governance; official artifact publisher **OWNER NOT IDENTIFIED** | Exact filenames/formats, release/commit, sizes, digests, provenance, applicable schema version | Verify hashes; inspect declarations/serialization read-only; compare circuit metadata to official schema and paper claims | **No.** Circuit inspection is not verifier/benchmark permission |
| A-03 | Official valid, invalid, and boundary fixture bundle plus expected outputs | **OWNER NOT IDENTIFIED** | Fixture manifest, source/release, generator if applicable, individual hashes, verifier/scorer version and expected-result provenance | Verify manifest/hash correspondence; confirm every fixture's expected decision/output is tied to exact verifier release | **No.** Running fixtures requires a distinct diagnostic authorization |
| A-04 | Versioned input/output and circuit-format specification | Official competition/verifier owner **OWNER NOT IDENTIFIED** | Versioned document or schema, publisher, release/commit, checksum, relation to verifier version | Cross-check all register, bit, wire, output, failure and operation semantics against executable source and fixtures | **No.** |
| A-05 | Official resource and statistical test vectors/results | Official scorer owner **OWNER NOT IDENTIFIED** | Version, input digest, scorer/verifier digest, configuration, expected raw metrics and score | Reproduce documented values only under separate authorization; first inspect values and formulas against source | **No.** |
| A-06 | Explicit Sonjoy scope acceptance and project-lead approval | Sonjoy and project-lead governance process; Yousuf is named project approval authority | Attributable, dated response with scope, date/channel, and project-lead record | Verify both acceptance and approval independently in authorized governance record | Not an artifact execution approval |
| A-07 | Independent reviewer assignment and acceptance | Governance process; proposed names are not accepted assignments | Named reviewer, accepted scope, independence, date/channel, review criteria | Verify assignment and acceptance; record review outcome separately | Does not authorize execution |

If the artifact publisher or authorized acquisition mechanism cannot be
identified, record that blocker and request direction; do not use alternate
accounts, bypass access controls, or infer permission.

## 11. Authorization Request Matrix

Statuses below are unchanged from P004. Each decision is separate; one cannot
satisfy another.

| Approval | Requested decision | Evidence required | Current status | Known authority / owner |
|---|---|---|---|---|
| Work-package acceptance | Sonjoy explicitly accepts bounded DQI scope and deliverables | Attributable written acceptance, date, and scope | **NOT VERIFIED** | Sonjoy for acceptance; project governance records acceptance |
| Project-lead scope approval | Approve the exact accepted work-package scope | Dated, traceable project-lead approval recorded with scope | **NOT VERIFIED** | Yousuf is named project lead/approval authority in repository records |
| Read-only artifact intake | Permission to inspect the named source/artifact paths | Governance statement covering exact paths and access mode | **VERIFIED** for documented paths only; no new access assumed | `origin/main:docs/TEAM/BENCHMARKS/DQI.md` lines 29–47 and responsibility matrix lines 48–55 |
| Diagnostic execution | Permission for specifically named bounded diagnostics | Explicit approval naming purpose, command, inputs, environment, resource/time limits, output handling | **NOT AUTHORIZED** | Project lead/approval process; exact authorization record absent |
| Full baseline execution | Permission for the exact official baseline command/workload and boundary | Separate explicit approval for exact parameters, environment, timeout and recovery/output policy | **PENDING** | Yousuf; `docs/BASELINE_EXECUTION_APPROVAL_REQUEST.md` says awaiting approval |
| Optimization implementation | Permission for defined optimization scope | Separate explicit scope and project-lead authorization after prerequisite gates | **NOT AUTHORIZED** | Project lead; no approval record found |
| Independent review | Assign reviewer and obtain acceptance of review scope | Recorded assignment and reviewer acceptance | **NOT VERIFIED** | Proposed roles only; no accepted reviewer |
| Final acceptance | Accept reviewed implementation/evidence package | Recorded final review decision under policy | **NOT VERIFIED** | Yousuf is documented project-level final reviewer/approval authority |

The baseline request's proposed command, salt, parameters, and resource
estimates are not approvals. The workstream record says the work package is
PROPOSED and optimization is not authorized
(`origin/main:docs/TEAM/BENCHMARKS/DQI.md`, lines 5–8).

## 12. Dependency and Approval Sequence

| Step | Dependency/action | May proceed as documentation-only? | Explicit authorization required? |
|---:|---|---|---|
| 1 | Sonjoy records availability and accepts a bounded DQI scope; project lead records approval | Request and record review can be documented | Yes, for scope acceptance/approval; no work-package approval inferred |
| 2 | Identify official artifact publisher and authorized source; receive verifier, reference/sample, schemas, fixtures and expected outputs | Planning/request can proceed | Yes, if the source is access-controlled or acquisition is otherwise restricted |
| 3 | Verify provenance, release identity, file sizes and hashes | Can proceed read-only after authorized receipt | No execution approval; artifact access permission still applies |
| 4 | Reconcile executable schema and contract against source, fixtures, and primary research | Can proceed by read-only inspection | No execution approval for inspection, but do not execute code |
| 5 | Obtain independent technical review and recorded review decision | Can proceed once evidence is complete | Reviewer must accept assignment; review is not execution approval |
| 6 | Request diagnostic authorization for an exact diagnostic | Proposal/documentation only before approval | Yes, separately and explicitly before execution |
| 7 | Request full baseline authorization for exact official procedure | Proposal/documentation only before approval | Yes, separately and explicitly before full run |
| 8 | Review baseline evidence and record outcome | Documentation only after an authorized run | Run itself requires Step 7 approval; review does not retroactively authorize it |
| 9 | Request optimization scope and permission | Proposal/documentation only | Yes, distinct approval after baseline governance and review prerequisites |
| 10 | Conduct implementation-readiness review against gates below | Readiness assessment can be documented | Does not grant implementation or execution permission; implementation needs its own separate directive/approval |

P005 completes none of these approvals. A later phase must not collapse scope
acceptance, artifact access, diagnostics, baseline, optimization, or
implementation into one implied permission.

## 13. Implementation Readiness Gates

No gate is marked PASS without its specified evidence.

| Gate | Required evidence | Current result |
|---|---|---|
| **GATE-01 — SCOPE** | Sonjoy's explicit bounded work-package acceptance and project-lead approval are traceable and recorded | **BLOCKED** — both NOT VERIFIED |
| **GATE-02 — OFFICIAL ARTIFACTS** | Official verifier/scorer and reference artifacts are available from an identifiable authorized source with verified provenance | **BLOCKED** — artifacts absent; official owner not identified |
| **GATE-03 — FIXTURES** | Official valid/invalid/boundary fixtures and expected outputs are available and provenance-verified | **BLOCKED** — absent |
| **GATE-04 — EXECUTABLE CONTRACT** | Critical P002 contract questions are resolved against primary or executable evidence; executable mapping is explicit | **BLOCKED** — schemas, register/wire mapping, scorer implementation unresolved |
| **GATE-05 — INDEPENDENT REVIEW** | Reviewer assignment/acceptance and technical review outcome are recorded | **BLOCKED** — assignment remains proposed |
| **GATE-06 — EXECUTION AUTHORIZATION** | The diagnostic or baseline has its own explicit approval for its exact scope and boundary | **BLOCKED** — diagnostic NOT AUTHORIZED; baseline PENDING |
| **GATE-07 — OPTIMIZATION AUTHORIZATION** | Defined optimization scope has separate explicit approval | **BLOCKED** — NOT AUTHORIZED |

**Final disposition: `BLOCKED`.** It is not `PARTIALLY_READY_FOR_REVIEW` or
`READY_FOR_SEPARATE_AUTHORIZATION_REVIEW`: scope acceptance and primary
executable artifacts are still absent. A future status change requires new
evidence, not completion of this planning document.

## 14. Risks and Blocking Dependencies

1. **Executable contract risk:** repository summaries may describe an API or
   scorer behavior not present in an official release. Coding against those
   summaries could produce an incompatible circuit or false validation.
2. **Provenance risk:** reported hashes without corresponding bytes cannot
   establish identity. The paper internal-run commitment and repository
   sample hash must remain distinct until verified.
3. **Encoding risk:** mathematical field and syndrome conventions do not
   settle circuit register names, bit ordering, wire layout, or `c` mapping.
4. **Fixture risk:** without official valid/invalid/boundary vectors, expected
   verifier decisions and outputs cannot be independently checked.
5. **Authorization risk:** branch ownership, directive wording, repository
   access, and proposed role assignments are not approvals.
6. **Execution risk:** a diagnostic can be unauthorized even when small; the
   full baseline approval request remains pending; neither the paper's shot
   count nor proposed command permits a run.
7. **Reviewer risk:** proposed reviewer names do not establish accepted
   independence or final acceptance authority.
8. **Resource/statistics risk:** paper formulas and repository summaries do not
   prove the executable count aggregation, seed construction, confidence
   bound, or defaults.

## 15. Exact Next Prerequisites

1. Record Sonjoy's explicit availability and acceptance of a bounded DQI
   work-package, and record project-lead approval of that exact scope and
   deliverables.
2. Identify the official competition/verifier artifact owner and authorized
   acquisition route; request the immutable verifier/scorer, reference and
   sample circuits, format/schema, fixtures, expected outputs, and provenance
   manifest listed in §10.
3. After authorized receipt, verify publisher/release identity, version,
   byte sizes, and SHA-256 without executing artifacts.
4. Reconcile P002 semantics against source and official fixture bytes,
   especially register/bit/wire ordering, input/output schema, rejection
   rules, resource counting, and statistical seed/bound implementation.
5. Record an accepted independent reviewer and complete technical review of
   the source-backed contract and evidence.
6. If needed, obtain a separate diagnostic authorization naming exact scope,
   command, inputs, environment, resource limits, and output handling before
   running any diagnostic.
7. Obtain explicit approval of the exact full-baseline command and boundary
   before any full baseline execution; review baseline evidence separately.
8. Keep optimization authorization separate and blocked until the defined
   prerequisite governance and baseline review are complete.
9. Only after these prerequisites, request a separately reviewed
   implementation-scope decision. P005 does not authorize implementation.

## 16. Acceptance Criteria

- [x] Correct repository root, branch, HEAD, staged/unstaged changes, and
  untracked-file state recorded before editing.
- [x] P001–P004 exist and their initial SHA-256 values are recorded.
- [x] Complete prior reports reviewed for continuity; actual P004 findings
  checked against the P004 document.
- [x] Available governance records read from their documented refs and
  provenance identified.
- [x] Evidence gaps cover verifier/scorer, reference/sample circuits,
  serialization, registers, operations, workspace, fixtures, expected outputs,
  integrity, and P002 technical contract questions.
- [x] Approval matrix keeps work-package acceptance, scope approval,
  read-only intake, diagnostic, baseline, optimization, reviewer assignment,
  and final acceptance separate.
- [x] Artifact acquisition requests specify purpose, provenance, integrity,
  acceptance check, known owner, and execution boundary.
- [x] Readiness gates are explicit and none is marked PASS without evidence.
- [x] No code, tests, diagnostics, verifier, baseline, benchmark, simulation,
  dependency installation, or artifact acquisition performed.
- [x] No authorization or governance record modified.
- [x] P001–P004 and pre-existing untracked files preserved; no other file
  modified or deleted.
- [x] Exactly one new P005 report created.
- [x] UTF-8, final newline, trailing-whitespace, `git diff --check`, branch,
  HEAD, and worktree validations completed after creation.

## 17. Final Disposition

**`BLOCKED`**

The official executable verifier/scorer, reference/sample circuits, fixtures,
expected outputs, and associated immutable provenance remain unavailable.
Sonjoy's work-package acceptance and project-lead scope approval are not
verified; independent review is not recorded; diagnostic execution is not
authorized; full baseline execution is pending; optimization is not
authorized. P005 is a gap-closure plan only and does not authorize artifact
acquisition through restricted channels, implementation, diagnostics,
verifier execution, or baseline/optimization work.

Stop after P005. Do not start P006. Await Sonjoy's review and the required
explicit approvals before preparing an implementation prompt.
