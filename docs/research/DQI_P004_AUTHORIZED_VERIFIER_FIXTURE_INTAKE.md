# DQI-P004 — Authorized Verifier and Fixture Intake

- **Project:** Google Quantum AI — Verifiable Quantum Circuit Compilation
- **Workstream:** DQI Decoder
- **Developer named by directive:** Sonjoy
- **Target branch:** `feat/dqi-decoder`
- **Assessment date:** 2026-11-20
- **Disposition:** **BLOCKED**

## 1. Executive summary

This read-only intake found no official DQI verifier/scorer source, reference
circuit file, sample circuit file, fixture bundle, expected-output record, or
executable release provenance in the current branch or any of the 21 available
local and remote Git refs inspected. The named artifacts are absent from the
local worktree as well. Repository documentation names those files and
summarizes APIs, score rules, and hashes, but those summaries are not the
artifacts and their cited executable behavior could not be independently
verified.

The versioned primary research paper, arXiv:2610.23832v2, is available as
external literature and defines the published mathematical problem, field
representation, syndrome convention, reference decoder narrative, reversible
target, paper resource metric, and statistical criterion. It is not the
official executable verifier or the competition fixture package. Its DQI
internal-run commitment cannot be matched to local circuit bytes.

No newer, attributable authorization was found. Read-only inspection of named
reference paths is permitted by the repository governance records.
Sonjoy's DQI work-package acceptance and project-lead scope approval remain
**NOT VERIFIED**; diagnostics remain **NOT AUTHORIZED**; the full baseline
request remains **PENDING**; optimization remains **NOT AUTHORIZED**; reviewer
acceptance/final review remains **NOT VERIFIED**.

**Readiness: BLOCKED.** The missing executable verifier and fixtures, together
with missing scope and execution approvals, prevent an implementation-readiness
review. This report does not authorize implementation or execution.

## 2. Repository and branch identity

### Initial state

- Repository root: `D:\PROJECT\Quantum_AI\Google-Quantum-AI`
- Branch: `feat/dqi-decoder` (verified exactly as requested; no branch switch).
- HEAD: `5391b2e7123484efacffc0588f5e761e67b5cb55`.
- Staged tracked changes: none.
- Unstaged tracked changes: none.
- Untracked files before this task:
  - P001, P002, and P003 reports in `docs/research/`.
  - Existing INVSQRT `.pyc` cache files in `src/invsqrt_opt/__pycache__/`,
    `src/invsqrt_opt/candidates/__pycache__/`, and `tests/__pycache__/`.
- The P004 target did not exist before this task.

All existing untracked files were preserved. No staging, commit, push, branch
change, deletion, reset, clean, merge, rebase, or cherry-pick was performed.

### Prior phase report identity

The three reports exist, are UTF-8 readable, and are not tracked in current
`HEAD`. SHA-256 values were recorded before and after the P004 edit to verify
they remained unchanged:

| Report | Worktree status | Size | SHA-256 |
|---|---|---:|---|
| `docs/research/DQI_P001_DEVELOPMENT_FOUNDATION.md` | Untracked; preserved | 18,717 bytes | `dc44f79bd38e7bd38566fc11e3234b0ece5c8adca52b66ece9823e13634eb0f8` |
| `docs/research/DQI_P002_TECHNICAL_CONTRACT.md` | Untracked; preserved | 23,206 bytes | `48e8772d49425cc50c0694ff7b133a7f58af1f218452a2a6ddece8bcb1eec516` |
| `docs/research/DQI_P003_EVIDENCE_READINESS_REPORT.md` | Untracked; preserved | 31,957 bytes | `0f47d0f4c59cdd040a569e7fc55c7a4127e69147f7a530ef2a16741dc4415163` |

These are working-tree documentation hashes, not commit or official-source
identifiers. The reports' contents were inspected for continuity; P001–P003
were not edited.

## 3. P001–P003 continuity

- P001 established the DQI foundation and documented that the active feature
  branch had no implementation assets, while distinguishing unrelated
  INVSQRT caches.
- P002 captured the repository-summary conflicts and correctly left verifier
  behavior and authorization unresolved.
- P003 added the versioned arXiv v2 research paper and concluded that the
  mathematical research contract is substantially specified but that
  executable artifacts and governance approvals block implementation review.
- P004 confirms the P003 artifact-availability and authorization findings
  against the current worktree and all available refs. It adds a precise
  read-only search scope and inventory, but does not upgrade any repository
  summary into an executable artifact.
- P003's earlier paper-level account now has more detail available from the
  arXiv HTML for field and syndrome conventions. P004 records those as
  primary-research claims only; no official verifier was thereby verified.

## 4. Authorization status and evidence

The applicable governance documents are on `origin/main` at
`3861f76f4842f40e70fc59ad69812052c2719f32`. The latest commit touching the
relevant ownership, DQI, and baseline-approval records is
`7ddcb3df96c52515c21629464351b1b840ae642f` (2026-11-19). The same content is
present in `origin/seyamb/verification-engineering`; no later authorization
record was found in the inspected refs.

| Activity / decision | Evidence inspected | Status | P004 finding |
|---|---|---|---|
| Read-only inspection of documented reference paths | `origin/main:docs/TEAM/BENCHMARKS/DQI.md` lines 29–47 and `origin/main:docs/TEAM/TEAM_RESPONSIBILITY_MATRIX.md` lines 48–55 | **VERIFIED** | Listed verifier, reference, sample, and evidence locations are documented as read-only reference paths. This does not authorize execution or access through bypasses. |
| Sonjoy's explicit DQI work-package acceptance | `origin/main:docs/TEAM/INDIVIDUAL_TASKS/SONJOY.md` lines 1–6, 31–48, 70–78; responsibility matrix lines 34–46 | **NOT VERIFIED** | No accepted DQI scope, date, channel, or recorded availability. The optional research-support choices do not establish decoder ownership. |
| Project-lead approval of Sonjoy's defined scope | Same Sonjoy task file and acceptance register | **NOT VERIFIED** | No accepted bounded DQI scope and Yousuf approval record were found. |
| Diagnostic execution | DQI workstream lines 60–71 and 122–132 | **NOT AUTHORIZED** | Workstream explicitly requires specific authorization even for bounded diagnostics; no such record found. |
| Full baseline execution | `origin/main:docs/BASELINE_EXECUTION_APPROVAL_REQUEST.md` lines 1–3, 77–79; DQI workstream lines 5–8, 98, 105–110 | **PENDING** | Explicit approval request is awaiting Yousuf; the request states the command has not been executed. A prepared command and its parameters are not approval. |
| Optimization implementation | DQI workstream lines 5–8, 83–85, 122–132; review policy lines 60–70 | **NOT AUTHORIZED** | Baseline governance is unmet and no explicit transition approval exists. |
| Independent review and final acceptance | `origin/main:docs/TEAM/TEAM_RESPONSIBILITY_MATRIX.md` lines 22–46; review policy lines 30–43, 72–77 | **NOT VERIFIED** | Proposed reviewer roles are not recorded as accepted. No candidate/evidence package has final acceptance. Yousuf is the project-level final review/approval authority in the policy. |

Task acceptance, change review, official verifier acceptance, and baseline or
release approval are separate decisions (`origin/main:docs/TEAM/REVIEW_AND_ACCEPTANCE_POLICY.md`
lines 3–15). None is inferred from this task, branch name, prior work, or
completion of P001–P003.

## 5. Official source inventory

| Evidence ID | Source | Location / version | Authority and inspected evidence | Integrity / completeness | Status and next action |
|---|---|---|---|---|---|
| S-01 | Competition information page | [Kaggle competition page](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation) | Official competition-hosted page; P003 recorded a read-only fetch on 2026-11-20. Visible page title/description only; page body is client-rendered. | Dynamic HTML; no immutable release, snapshot hash, verifier, schemas, or DQI files obtained | **PARTIAL**. Obtain the authorized competition specification and artifact release via approved access; record version and digest. |
| S-02 | Primary research paper | [arXiv:2610.23832v2](https://arxiv.org/abs/2610.23832v2); HTML `https://arxiv.org/html/2610.23832v2` | Primary literature; v2 dated 2026-10-21; authors and DOI are identified by arXiv. P003 inspected §§II.3 and III.2.1–III.2.3, Eqs. (36)–(43). | No local PDF/HTML copy or raw-byte digest in this task. Paper publishes DQI internal-run hash `0701f553a9ac4e8af100f66acfccf2fc82cf5a44c2e5aa765b1d4ace01cbaadb`; run bytes unavailable to verify it. | **VERIFIED_FROM_PRIMARY_SOURCE** for claims in the cited paper sections only. Not official executable interface evidence; compare against released verifier/fixtures when available. |
| S-03 | Repository competition-requirements summary | `origin/main:docs/COMPETITION_REQUIREMENTS_MATRIX.md`, commit `3861f76f4842f40e70fc59ad69812052c2719f32`, DQI §3 / D-01–D-12 | Secondary repository summary with paper/metric citations; inspected in earlier P001–P003 work and referenced here. | Exact repo blob/hash in §10; not the cited executable source | **PARTIAL** as a summary; its claims require source/fixture confirmation. |
| S-04 | Repository verifier API summary | `origin/main:docs/OFFICIAL_VERIFIER_API_REFERENCE.md`, same commit, DQI section lines 38–71 | Secondary repository API notes cite an expected verifier path and source lines. | Exact repo blob/hash in §10; underlying verifier absent | **CONFLICTING** with later readiness records reporting no official package/invocation/fixtures. Obtain actual released source. |
| S-05 | Later verifier-discovery/readiness summary | `origin/feat/compiler-infrastructure:docs/phase-10-dqi-readiness-report.md` and `docs/official-verifier-integration-contract.md`, commit `6bf3ff2b4a97b691764deae45be33e4143a0f93b` | Secondary engineering audit; says register/wire mapping, field/syndrome encoding, bit order, invocation, shot/seed semantics, verifier release, and fixtures are missing. | Git-tracked documents; no official package attached to that ref | **PARTIAL** as evidence of prior discovery limits; it does not prove no official source exists outside the inspected refs. |
| S-06 | Paper-internal DQI best-run commitment | DQI hash printed in arXiv v2 §III | Primary paper statement that authors committed an internal best run | No corresponding file/release locally; cannot hash or map to named sample circuit | **NOT VERIFIED** as a local artifact; obtain the referenced run only from an authorized release if relevant. |

The arXiv paper is primary research, not a competition-owner verifier release.
The Kaggle page observation establishes public metadata only, not the contents
of a gated or client-rendered competition package.

## 6. Verifier artifact inventory

| Item | Exact documented path / source | Availability in inspected worktree and refs | Provenance, version, size, hash | Completeness / status |
|---|---|---|---|---|
| DQI submission verifier source | `external/verifiers/dqi/verify_submission_dqi.py` | Absent locally and from every inspected Git ref | No source commit/version/size/hash available. Repository baseline report names digest `f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65`, not matched to bytes. | **ABSENT**. Verifier source and independently verifiable release provenance required. |
| Verifier entry point | Same path; repository API summary also gives `main()` | Actual file unavailable | API reference summarizes a function and CLI; cannot verify entry-point implementation, flags, exit statuses, or parser | **ABSENT** as executable evidence. |
| Required invocation | `origin/main:docs/COMPETITION_REQUIREMENTS_MATRIX.md` lines 122–144 and `docs/OFFICIAL_VERIFIER_API_REFERENCE.md` lines 42–57 | Summaries only; named verifier absent | Repository-recorded call/CLI claims have Git provenance in §10; no executable confirmation | **CONFLICTING**: matrix shows Python API and cautions against invented CLI flags; API summary documents a CLI; later readiness report says invocation was not obtained. |
| Input schema | API summary lines 60–65 describes registers; paper defines logical `s,c` | No parser/source or fixture available | No executable schema, serialization, byte order, or digest | **ABSENT** as executable schema; paper-level logical input is recorded in §11. |
| Output schema | API summary lines 67–71 describes return fields | No verifier output or expected-result fixture available | No JSON schema, exit/failure behavior, or recorded raw DQI output in inspected refs | **ABSENT**. |
| Validation/rejection conditions | API summary says `Z_POW` rejection, syndrome restoration, clean ancilla, and `eps_plus` threshold | Summary only | Conditions also described at mathematical level in paper; executable checks not inspected | **PARTIAL**. Require verifier source and fixtures. |

No verifier code was imported, run, or otherwise executed.

## 7. Scorer artifact inventory

| Item | Source/path | Availability and provenance | Status / next action |
|---|---|---|---|
| DQI score implementation | Claimed in `external/verifiers/dqi/verify_submission_dqi.py`; summarized by `origin/main:docs/SCORE_MODEL_VERIFICATION.md` lines 18–33 | Executable scorer absent; summary is repository-authored and hash-identified in §10 | **ABSENT** as implementation. Obtain verifier/scorer release and verify metric behavior against fixtures. |
| Paper metric | arXiv v2 §III.2.3 Eq. (43) | Primary research defines `S = R(eps+) Q^2 T`, with `Q` total qubits (syndrome plus workspace) and `T` single-run Toffoli count including cleanup | **VERIFIED_FROM_PRIMARY_SOURCE** for paper formula; not executable score output. |
| Resource counting implementation | Same claimed verifier path; secondary score summary | No code or circuit file available | **ABSENT**. Exact operation parser/counting, inclusion rules, and output semantics remain unknown. |
| Statistical acceptance implementation | Paper §§II.3/III.2.3 Eqs. (4), (41)–(43); secondary verifier/score summaries | Paper defines a one-sided Clopper–Pearson upper bound; executable function is absent | **PARTIALLY_VERIFIED** at paper level; executable implementation and seed construction unavailable. |
| Rejection threshold | Paper §III.2.3; local DQI docs | Paper states `eps+ >= 1/16` receives no finite score | **VERIFIED_FROM_PRIMARY_SOURCE** as paper condition. Executable rejection behavior remains unverified. |

The local score summary calls `T` a mean Toffoli-like count per shot, while
paper Eq. (43) describes a single-run Toffoli count including cleanup. The
paper definition is clear for its equation; whether the summary faithfully
describes the executable scorer cannot be established without the source.

## 8. Reference and sample circuit inventory

| Item | Documented location | Availability/provenance | Status and unresolved details |
|---|---|---|---|
| Official DQI reference circuit source | `external/verifiers/dqi/dqi_reference_circuit.py` | Absent locally and in all inspected refs; no version, size, or digest | **ABSENT** as file. Paper §III.2.2 describes EEA, Chien search, Forney recovery, and cleanup, but that is not the reference circuit artifact. |
| Official DQI sample submission | `external/sample_submission/dqi.kmb` (or `.kmx` in general requirement summaries) | Absent locally and in all inspected refs. Local baseline summary reports SHA-256 `959471d05a26373b4f14ca0cae2d8639ea25f18170d9f6532139aa51ccc04995`; digest cannot be verified without bytes. | **ABSENT**. Obtain authorized bytes and independently verify hash. |
| Paper internal-best-run circuit | arXiv v2 §III commitment `0701f553a9ac4e8af100f66acfccf2fc82cf5a44c2e5aa765b1d4ace01cbaadb` | Paper gives a commitment, not an available circuit file in inspected refs | **NOT VERIFIED** as a circuit artifact; do not assume it equals the repository-named sample. |
| Circuit format | Repository summaries name `.kmb`/`.kmx`; paper describes a kickmix circuit | No local DQI file or parser/verifier | **PARTIALLY_VERIFIED** at paper/repository-summary level; exact accepted format/version unknown. |
| Register declarations and ordering | Paper §III.2.2 defines field basis, coordinates and mathematical `s,c`; API summary reports `S0..S69` and `E0..E4094` | No executable artifact to inspect; summary calls `E` registers classical bit registers, while paper names a classical measurement record `c` | **CONFLICTING** for executable representation. Exact register names, widths, wire order, and serialization require official source and fixture. |
| Gate/operation conventions | Paper §II.1 defines kickmix instruction categories; repository API summary says DQI rejects `Z_POW` | No DQI circuit/parser/source locally | **PARTIALLY_VERIFIED** from research plus secondary summary; exact DQI allowlist/rejection implementation unverified. |
| Workspace/cleanup | Paper Eqs. (36)–(38) requires output workspace zero and §III.2.2 describes inverse EEA; local summary says verifier checks syndrome restoration and ancilla cleanliness | No circuit bytes or executable checks available | **PARTIALLY_VERIFIED** at research level; actual implementation/circuit behavior not verified. |

## 9. Fixture and expected-output inventory

| Fixture class | Search scope and result | Provenance/hash | Status |
|---|---|---|---|
| Official valid inputs | DQI fixture/evidence paths in workstream docs; all available refs and local named paths | No input bytes or expected output found | **ABSENT** |
| Official invalid inputs | Same search | No rejected circuit/input fixture found | **ABSENT** |
| Expected verifier outputs | `docs/evidence/`, `results/raw/`, and references to DQI raw runs | Directories and DQI output records absent in inspected refs/local path checks | **ABSENT**. Repository baseline summaries report no full run and diagnostic records, but those records themselves are not present in the refs inspected. |
| Expected score outputs | Same plus `docs/SCORE_MODEL_VERIFICATION.md` summary | No DQI raw JSON output or fixture-linked score expected value | **ABSENT** as executable fixture. Formula is paper-level only. |
| Boundary cases | No DQI test/fixture directories in refs | No valid-zero-syndrome, max-weight, malformed-register, or threshold-boundary fixture bytes | **ABSENT** |
| Fixture provenance/version | No fixture manifest or immutable release found | No commit, release, size, or digest | **ABSENT** |

No replacement fixtures were created, and no diagnostic was run to generate
expected outputs.

## 10. SHA-256 and provenance manifest

Repository summaries below are secondary evidence. Git blob IDs and SHA-256
values identify the exact `origin/main` document bytes; they do not prove the
summaries' cited verifier source exists or is authoritative.

`origin/main` is `3861f76f4842f40e70fc59ad69812052c2719f32`. Governance records
were last changed in `7ddcb3df96c52515c21629464351b1b840ae642f`. The
verification-engineering ref contains identical blob IDs for the listed
authorization files.

| Artifact | Repository version/path | Blob ID | SHA-256 / file integrity |
|---|---|---|---|
| DQI requirements summary | `origin/main:docs/COMPETITION_REQUIREMENTS_MATRIX.md` | `b47aeeb78bbee583d624d3a5db27146d5987b258` | `07d67c866166ca00eaf1a28b2b363f18ca8eb5aa55a1fae9c3ed2fecf573656c` |
| Verifier API summary | `origin/main:docs/OFFICIAL_VERIFIER_API_REFERENCE.md` | `0b9a435c443d251639ea0b434d9fb847a4d12ea3` | `476606e6da718cee1c6239d63ad67dfd43e51416d3a1b896bd00a68a5580cf34` |
| Score-model summary | `origin/main:docs/SCORE_MODEL_VERIFICATION.md` | `c75dbfab51c2c72539c84001856e7ab7f7ff38e0` | `0df7adfd6c36e2e2d2de1138cd6a34695e0afb3075af5f899d94aab3b75d0f20` |
| DQI workstream record | `origin/main:docs/TEAM/BENCHMARKS/DQI.md` | `d2319b2877ddf5654ff347d5e175a86862df4342` | `a6245844e1a8c6879a8321e67ccc4e76d3b33145cb28692eee382e85837046cb` |
| Baseline execution request | `origin/main:docs/BASELINE_EXECUTION_APPROVAL_REQUEST.md` | `d1009bb0a3c89f5a62d50ae03f87369bea6b530c` | `7e2bf6a67b510d44906d8d0275519b9faa03a31365a5f65974c50b7dc825c7c7` |
| Baseline status | `origin/main:docs/BASELINE_STATUS_MATRIX.md` | `685562b785dcfeef7558091c46b9d2f5e922062e` | `5b120cbf187ba2d250fa13607f2d83b1aaa8b86e150756f6f9a19ab7cab14db9` |
| Sonjoy task/acceptance proposal | `origin/main:docs/TEAM/INDIVIDUAL_TASKS/SONJOY.md` | `47a473a553742c34d82f7a27702c6ff782e01faf` | `8b759a0d5e5ea1499c5f7dc5c12ffb656ff671a7f97613d6f2772e7f92168511` |
| Responsibility matrix | `origin/main:docs/TEAM/TEAM_RESPONSIBILITY_MATRIX.md` | `29b26e10cf96bda0d3e00043c1ab781555c2936b` | `809131b1efdc4cca7e0b0d7f3ac2b3dc27564d8d24015f1336fad46d7372e2d2` |
| Review and acceptance policy | `origin/main:docs/TEAM/REVIEW_AND_ACCEPTANCE_POLICY.md` | `06548fde5168bb2b06ffcd4d87bdcc460c66f6d9` | `162b882767518ac54270dfd82f207b5bf803959f419509c90574aa32b20904dd` |
| P001 report | Current worktree, untracked | Not committed | `dc44f79bd38e7bd38566fc11e3234b0ece5c8adca52b66ece9823e13634eb0f8`; unchanged |
| P002 report | Current worktree, untracked | Not committed | `48e8772d49425cc50c0694ff7b133a7f58af1f218452a2a6ddece8bcb1eec516`; unchanged |
| P003 report | Current worktree, untracked | Not committed | `0f47d0f4c59cdd040a569e7fc55c7a4127e69147f7a530ef2a16741dc4415163`; unchanged |
| Official verifier/reference/sample/fixtures | Named external paths in repository docs | Not found in refs or local worktree | No size or SHA-256 can be reported; repository-reported digests are unverified against bytes |
| arXiv v2 HTML/PDF | `https://arxiv.org/html/2610.23832v2`, `https://arxiv.org/pdf/2610.23832` | External version v2 | No file downloaded or local raw-byte hash computed in P004 |
| Kaggle page | Official URL in §5 | Dynamic page | No immutable version or content hash recorded |

### Exact ref search scope

Read-only path and tree inspection covered all 21 refs listed by the local
`git for-each-ref` inventory: local heads `feat/dqi-decoder`,
`feat/invsqrt-optimization`, `main`, `research/dqi`, `research/invsqrt`, and
all listed `origin/*` refs including `origin/main`,
`origin/seyamb/verification-engineering`, and
`origin/feat/compiler-infrastructure`. In each ref, the following exact paths
were absent: DQI verifier source, DQI reference-circuit source, `.kmb` and
`.kmx` sample circuits, and `docs/research/PRIMARY_SOURCE_FINDINGS.md`.
No DQI fixture-like tracked files were found outside governance/readiness
documentation.

This establishes absence from the inspected local refs and local paths, not
absence from the competition owner's systems or other uninspected locations.

## 11. P002 contract reconciliation

The following status labels are used as requested. “Verified” for a paper
claim is explicitly not executable-artifact verification.

| Contract item | Status | Primary/repository evidence and reconciliation |
|---|---|---|
| Finite-field representation and polynomial | `VERIFIED_FROM_PRIMARY_SOURCE` | arXiv v2 §III.2.2 specifies `GF(2^12) = GF(2)[alpha]/(alpha^12+alpha^6+alpha^4+alpha+1)` and little-endian polynomial basis `(1,alpha,...,alpha^11)`. No executable cross-check. |
| Field element bit encoding | `VERIFIED_FROM_PRIMARY_SOURCE` | Paper §III.2.1 Eq. (37) states `bin(e)` is binary encoding of field symbols in the chosen basis; does not define circuit-file wire serialization. |
| Evaluation-point convention | `VERIFIED_FROM_PRIMARY_SOURCE` | Paper §III.2.2 specifies `alpha_j=alpha^j`, `j=0,...,m-1`. No executable cross-check. |
| Syndrome ordering/indexing | `VERIFIED_FROM_PRIMARY_SOURCE` | Paper §III.2.2 defines `s_i = sum_j e_j alpha^((i+1)j)` for `i=0,...,n-1`; executable register-to-coordinate order remains unverified. |
| Decoder input representation | `PARTIALLY_VERIFIED` | Paper Eqs. (37)–(38) say the circuit receives syndrome `s` and uniformly random classical record `c`, not hidden error vector `e`; actual input serialization/register schema absent. |
| Register and bit ordering | `CONFLICTING` | Paper gives logical field basis and coordinate conventions. Secondary API summary reports `S0..S69`, `E0..E4094`; later readiness says register/wire mapping and bit order were not obtained. No executable source or fixtures to resolve. |
| Error-weight/decoding radius | `VERIFIED_FROM_PRIMARY_SOURCE` | Paper §III.2.2 gives dual RS code `[4095,4025,71]`, `ell=n/2=35`, and uniqueness because `2ell=70<71`. Executable instance conformance not checked. |
| Reversible output semantics | `VERIFIED_FROM_PRIMARY_SOURCE` | Paper Eq. (38): preserve `s`, return `W` to zero, apply `(-1)^(c dot bin(e(s)))` on promised correctable syndromes. Complete behavior outside the promise and executable checks absent. |
| Workspace initialization/cleanup | `PARTIALLY_VERIFIED` | Paper Eq. (38) requires zero workspace on output; §III.2.2 describes inverse EEA cleanup and reports the reference total after cleanup. Candidate ancilla layout, complete workspace allocation, and verifier checks require artifacts. |
| Exact verifier input/output schema | `ABSENT` | API summary exists, but verifier source, actual invocation, schema, output, failure behavior, and fixtures absent; later readiness report says blocked. |
| Resource metrics/counting | `PARTIALLY_VERIFIED` | Paper Eq. (43) defines `S=R(eps+)Q^2T`, with `Q` total qubits and `T` single-run Toffolis including cleanup. Executable count/scorer absent; local score summary wording for `T` conflicts. |
| Statistical acceptance | `PARTIALLY_VERIFIED` | Paper §§II.3/III.2.3 gives `N=102,400`, one-sided Clopper–Pearson bound at confidence `1-2^-128`, and no finite score for `eps+ >= 1/16`. Exact RNG/seed and executable calculation remain unverified. |
| Circuit format/gate convention | `PARTIALLY_VERIFIED` | Paper §II describes kickmix instruction families; repository API summary says DQI rejects `Z_POW`. Actual parser, supported format version, and DQI gate acceptance cannot be inspected. |
| Valid/invalid fixtures and expected results | `ABSENT` | No fixture bytes, expected-output files, or provenance manifest in inspected refs/local paths. |
| Official verifier release/version | `ABSENT` | No package, release ID, commit, or source hash available. |

No conflict is silently reconciled. The paper establishes paper-level
mathematics; the missing executable contract remains a separate blocker.

## 12. Conflicts and unresolved questions

1. **Paper versus executable contract:** the paper defines mathematics and
   describes a verifier strategy, but the later engineering readiness report
   says no executable verifier release, invocation, fixtures, or full artifact
   contract was obtained. Needed: authorized official release and fixtures.
2. **Verifier API versus absence:** `docs/OFFICIAL_VERIFIER_API_REFERENCE.md`
   summarizes a Python API and CLI, while the DQI matrix shows an API invocation
   and warns against inventing CLI flags; a later readiness report says
   invocation remains missing. Needed: inspect actual verifier entry point.
3. **Register mapping:** mathematical coordinates are defined by the paper,
   but secondary `S_i`/`E_j` declarations and wire/bit order are unverified.
   The names and equal bit counts do not prove that `E` and paper record `c`
   have identical semantics. Needed: verifier/parser source plus canonical
   valid fixtures.
4. **Operational defaults:** the matrix says numeric `DEFAULT_NUM_SHOTS` and
   `DEFAULT_BATCH_SIZE` were not found, while other summaries report 102,400,
   256, and four workers. The baseline request proposes one worker. The paper
   establishes the 102,400-shot statistical analysis, not every executable
   default. Needed: source and exact approved run configuration.
5. **Resource `T`:** paper Eq. (43) describes single-run Toffoli count
   including cleanup; local score summary calls it mean per-shot
   Toffoli-like count. Needed: actual scorer implementation and output
   semantics.
6. **Circuit commitments:** the paper's internal-best-run digest and
   repository's reported sample digest have no corresponding bytes in the
   inspected refs. They must not be equated. Needed: authorized artifact
   release and digest comparison.
7. **Statistical execution behavior:** paper supplies the upper-bound model
   but the verifier's seed/salt derivation, canonical serialization, exact
   confidence-bound code, errors, and result schema are unavailable. Needed:
   verifier source and published/authorized test vectors.
8. **Governance:** directive names Sonjoy, but governance records call Sonjoy
   unconfirmed research support and Mahin proposed DQI lead. Needed: explicit
   scope acceptance and project-lead record; do not edit the governance
   record as part of this intake.

## 13. Missing artifacts and responsible source/owner

| Missing item | Known source/owner in available evidence | Needed |
|---|---|---|
| Immutable official verifier and scorer release | Official competition/verifier owner is not identified in repository records; Yousuf is project approval authority, not evidenced as artifact publisher | Authorized release/source URL, version/commit, license, dependencies, digest, invocation/schema |
| Reference circuit and sample submission | Paths are named in `docs/TEAM/BENCHMARKS/DQI.md`; no accepted artifact owner recorded | Authorized bytes and independent digest |
| Valid/invalid fixtures and expected outputs | No owner or fixture manifest identified | Authorized fixture bundle, expected outputs, boundaries, and provenance |
| Canonical register/bit-order contract | Paper defines mathematical convention; executable owner/source missing | Exact circuit schema and golden encodings |
| Diagnostic permission | Yousuf/project lead is governance approval authority for benchmark execution; no diagnostic record | Separate explicit authorization naming diagnostic scope, command, environment, and evidence handling |
| Full baseline approval | Approval request is awaiting explicit Yousuf approval | Attributable approval of exact workload and execution boundary |
| Sonjoy DQI scope acceptance | Sonjoy must explicitly accept and Yousuf must record per governance | Written acceptance and recorded scope approval |
| Reviewer/final acceptance | Proposed SeyamB reviewer and project-lead review roles; acceptance unrecorded | Accepted independent reviewer and later final project-lead decision |

## 14. Implementation-readiness assessment

The paper provides sufficient evidence to discuss the mathematical research
problem and the published reference strategy. It is not enough to establish
the current executable submission contract. Required verifier, reference,
sample, and fixture artifacts are absent across all searched refs, and scope
acceptance is not recorded.

**Decision: BLOCKED; not ready for implementation review.** No new source or
test structure should be initiated under P004. In particular, paper formulas,
repository API summaries, and recorded but unmatched hashes must not be used
to fabricate an executable adapter or replacement fixture.

## 15. Diagnostic execution authorization status

**NOT AUTHORIZED.** The DQI workstream requires specific authorization even
for a bounded diagnostic (`origin/main:docs/TEAM/BENCHMARKS/DQI.md` lines
122–126). No attributable diagnostic approval was found. No test, simulator,
diagnostic, verifier, or DQI code was executed for P004.

## 16. Baseline execution authorization status

**PENDING.** The approval request explicitly says it awaits Yousuf's approval
and that its prepared command has not been executed
(`origin/main:docs/BASELINE_EXECUTION_APPROVAL_REQUEST.md` lines 1–3,
77–79). The 102,400-shot statistical target in the paper and the proposed
single-worker command are not permission. P004 did not execute any baseline
workload.

## 17. Optimization authorization status

**NOT AUTHORIZED.** The DQI workstream prohibits optimization before baseline
governance requirements and explicit transition approval
(`origin/main:docs/TEAM/BENCHMARKS/DQI.md` lines 5–8, 83–85, 122–132).
Neither condition is verified.

## 18. Exact next prerequisites

1. Obtain the official verifier/scorer, reference circuit, sample circuit,
   valid/invalid fixtures, expected outputs, and exact schemas from an
   authorized competition source; record immutable provenance and hashes.
2. Establish Sonjoy's explicit bounded DQI work-package acceptance and
   project-lead approval in the authorized governance channel.
3. Reconcile mathematical field/register conventions to actual verifier
   parsing and fixture bytes; record disagreements rather than guessing.
4. Obtain an accepted independent reviewer and define review/acceptance
   evidence.
5. Obtain separate explicit diagnostic authorization before any diagnostic.
   Obtain the exact full-run approval before any 102,400-shot execution.
6. Keep optimization separately gated until baseline governance is complete
   and explicit project-lead optimization approval is recorded.

## 19. Acceptance criteria

- [x] Correct repository root, exact target branch, HEAD, full untracked
  status, and staged/unstaged changes recorded.
- [x] P001, P002, and P003 confirmed present; their content hashes remained
  unchanged.
- [x] Relevant governance records and available refs inspected read-only.
- [x] All available refs searched for the named verifier, reference circuit,
  sample circuits, primary-source dossier, and fixture-like files.
- [x] Actual inspected evidence distinguished from unavailable sources and
  secondary summaries.
- [x] Authorization states supported by dated, traceable governance records;
  no approval inferred.
- [x] P002 contract items reconciled or explicitly left conflicting/absent.
- [x] Missing artifacts, known proposed owners, and required next evidence
  recorded.
- [x] No code, tests, diagnostics, verifier, benchmark, dependency, or
  protected artifact operations performed.
- [x] Exactly one new report created; P001–P003 and unrelated untracked files
  preserved.
- [x] Documentation validation passed as reported below.

## 20. Final disposition

**BLOCKED.** The primary paper is inspectable and supports research-level DQI
semantics, but the official executable verifier/scorer and fixtures are absent
from the inspected worktree and every available ref. Sonjoy's work-package
acceptance and project-lead scope approval are not verified; diagnostics are
not authorized; the full baseline remains pending; optimization is not
authorized. This artifact grants no implementation or execution permission.

P004 stops here. No P005 or implementation work has started.
