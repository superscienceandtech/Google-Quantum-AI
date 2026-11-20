# DQI-P003 — Authoritative Evidence Intake and Implementation Readiness

**Project:** Google Quantum AI — Verifiable Quantum Circuit Compilation
**Workstream:** DQI Decoder
**Developer named by directive:** Sonjoy
**Target branch:** `feat/dqi-decoder`
**Assessment date:** 2026-11-20
**Final status:** **BLOCKED**

## 1. Executive readiness decision

**BLOCKED for implementation review.** The versioned primary research paper
provides a meaningful mathematical and algorithmic specification for DQI:
the Reed–Solomon dual-code decoding target, field representation, syndrome
equation, error-weight bound, phase-correction contract, reference algorithm,
resource model, and statistical criterion. These are materially stronger
technical sources than the repository summaries reviewed in P001/P002.

However, the official verifier/scorer release and its input/output schema,
reference/sample artifacts and fixtures, reproducible artifact digests, and
recorded Sonjoy/project-lead scope acceptance are not available in the
inspected repository refs. The full baseline remains pending explicit
approval; diagnostic execution is not authorized; optimization is not
authorized. The paper's mathematical contract does not substitute for the
missing executable competition interface or governance decisions.

This phase is documentation-only. No circuit, decoder, test, diagnostic,
verifier run, or benchmark was executed or created.

## 2. P001 and P002 continuity

- Read [DQI_P001_DEVELOPMENT_FOUNDATION.md](./DQI_P001_DEVELOPMENT_FOUNDATION.md)
  and [DQI_P002_TECHNICAL_CONTRACT.md](./DQI_P002_TECHNICAL_CONTRACT.md).
- Both are present in the worktree as untracked files, not in current-branch
  `HEAD`; they were preserved without modification.
- P001 correctly left implementation and execution blocked based on the
  repository evidence then available.
- P002 accurately recorded conflicts and missing sources among the repository
  summaries. P003 supplements that analysis with the versioned arXiv v2 paper,
  now retrieved from the public arXiv HTML page.
- P003 does not treat the paper as an official verifier package or use its
  internal-run hash as proof that any locally available sample circuit matches
  that run.

## 3. Authoritative evidence inventory

Status definitions: **VERIFIED** means the identified source directly supports
the stated research/contract item; it does not imply executable verifier
validation. **PARTIAL** means some requirements are supported but required
artifacts or interface details are missing. **ABSENT** means the artifact was
not found in the inspected refs. **CONFLICTING** means repository records
disagree and the cited executable source is unavailable.

| Evidence ID | Artifact / requirement | Path or external source | Authority and version | Hash / integrity status | Evidence status | Unresolved questions | Required next action |
|---|---|---|---|---|---|---|---|
| E-01 | Competition page / official competition metadata | [Kaggle competition page](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation) | Kaggle-hosted official page; fetched 2026-11-20; visible title: “Google Quantum AI - Verifiable Quantum Circuit Compilation” | Dynamic HTML; no content hash recorded | **PARTIAL** | Public HTML exposes title and short description, but not the DQI executable contract, verifier package, schema, fixtures, or full competition instructions | Obtain an authorized immutable competition specification/release and record its version and digest |
| E-02 | DQI research specification / Reed–Solomon decoder definition | [arXiv:2610.23832v2](https://arxiv.org/abs/2610.23832v2), especially §§II.3, III.2.1–III.2.3, Eqs. (36)–(43); HTML: `https://arxiv.org/html/2610.23832v2` | Primary research paper by Nicholas C. Rubin, Craig Gidney, Michael Broughton, Guang Hao Low, and Ryan Babbush; arXiv version v2 dated 2026-10-21; arXiv-issued DOI `10.48550/arXiv.2610.23832` | Versioned public source identified; downloaded/rendered content digest not computed. Paper states a DQI internal-best-run SHA-256 `0701f553a9ac4e8af100f66acfccf2fc82cf5a44c2e5aa765b1d4ace01cbaadb`; corresponding artifact not present to compare | **VERIFIED** for published mathematical/research claims; not an executable verifier | Paper does not supply the actual competition verifier/scorer binary, complete artifact schema, or test fixture package in this checkout | Preserve an authorized paper copy/digest if required by project evidence policy; obtain executable competition release separately |
| E-03 | Finite-field parameters and representation | arXiv v2 §III.2.2, Eq. (39) and following text | Primary research paper, arXiv v2 | Same provenance as E-02; no raw-content digest | **VERIFIED** as paper-specified representation | Need verify that the competition executable uses this version and same serialization | Cross-check against immutable official verifier and its test vectors before coding |
| E-04 | DQI target semantics and correctness observables | arXiv v2 §III.2.1, Eqs. (36)–(38) | Primary research paper, arXiv v2 | Same provenance as E-02 | **VERIFIED** as research contract | The exact circuit-file register declarations and complete behavior outside promised correctable syndromes are not supplied as fixtures | Obtain official verifier contract and representative authorized inputs |
| E-05 | Reversible reference algorithm / uncomputation description | arXiv v2 §III.2.2; EEA, Chien search, Forney recovery, inverse EEA cleanup; also §III.2.1 MBUC discussion | Primary research paper, arXiv v2 | Same provenance as E-02 | **PARTIAL** | Describes reference method and cleanup, but the actual reference circuit source and exhaustive gate-level mapping are absent | Obtain authorized reference circuit and verify its release/hash |
| E-06 | Official verifier source | `external/verifiers/dqi/verify_submission_dqi.py` (named in repository summaries) | Claimed local source path; not present in `origin/main`, `origin/seyamb/verification-engineering`, or `origin/feat/compiler-infrastructure` | No source file, version, or digest available; summary-recorded hash not independently checked | **ABSENT** | API, CLI, result schema, error behavior, parser semantics, random-seed construction, and actual score computation | Obtain the immutable official verifier/scorer release, provenance, dependency/runtime record, and digest |
| E-07 | Official reference circuit source | `external/verifiers/dqi/dqi_reference_circuit.py` (named by DQI workstream documentation) | Claimed local path; absent in inspected refs | No file or digest available | **ABSENT** as an artifact; algorithm is described in E-05 | Whether the competition’s released reference implementation exactly matches the paper narrative and published metrics | Obtain authorized source and map it to the paper version |
| E-08 | Official sample circuit / baseline input | `external/sample_submission/dqi.kmb` (named in DQI governance records) | Claimed local path; absent in inspected refs | No file available. Repository reports SHA-256 `959471d05a26373b4f14ca0cae2d8639ea25f18170d9f6532139aa51ccc04995`; digest not checked against bytes | **ABSENT** | Whether reported digest is current official baseline, and its relation to the paper’s internal-best-run digest | Obtain the authorized sample and independently compute/record its digest |
| E-09 | Sample inputs, fixtures, expected outputs | `external/`, `docs/evidence/`, `results/raw/` paths named by local documents | No fixture/evidence/raw directories in inspected refs | No bytes, version, or digest to inspect | **ABSENT** | Canonical encodings, reference outputs, permitted fixture use, and coverage | Obtain authorized fixtures and expected results, with provenance and checksums |
| E-10 | Register names, wire layout, bit ordering, serialization | arXiv v2 §III.2.2; `docs/OFFICIAL_VERIFIER_API_REFERENCE.md` lines 60–65; compiler readiness report | Paper directly defines mathematical coordinate/basis conventions; repository API summary reports `S0..S69` and `E0..E4094`; later readiness report says wire mapping/bit order missing | Paper version known; local summary docs have verified Git blob/SHA-256 identities listed in §4; executable source absent | **PARTIAL / CONFLICTING** | Exact circuit register names/widths, `c` serialization and wire order, and relationship of `E` registers to `c` | Resolve from official verifier source, parser, and fixtures; do not infer from matching bit counts |
| E-11 | Reversibility, workspace cleanup, equivalence conditions | arXiv v2 §§III.2.1–III.2.2, Eqs. (36)–(38); local matrix D-02/D-03 | Primary research paper plus secondary repository summary | Paper version known; no circuit artifact digest | **VERIFIED** for stated promised-input transform; implementation-level evidence partial | Full behavior off the promised domain; exact official shot-level checks and measurement/reset behavior | Confirm acceptance checks against official verifier and reference fixtures |
| E-12 | Resource metrics and score implementation | arXiv v2 §III.2.2–III.2.3, Eq. (43); `docs/SCORE_MODEL_VERIFICATION.md` lines 18–33 | Primary paper defines formula; repository summary claims code lines in absent verifier | Paper version known; verifier source and corresponding code hash absent | **PARTIAL** | Executable `T` counting semantics, operation normalization, exact score serialization, and whether paper metrics match official scorer | Obtain scorer source and cross-check formula/counting against official fixtures |
| E-13 | Statistical sampling and confidence bound | arXiv v2 §§II.3, III.2.3, Eqs. (4), (41)–(43) | Primary research paper, arXiv v2 | Paper version known; verifier implementation absent | **VERIFIED** for paper-stated methodology; executable enforcement partial | Exact official RNG/hash preimage, seed/salt rules, CI implementation details, and runtime defaults | Obtain verifier source and test vectors; compare implementation to paper |
| E-14 | Work-package and execution governance | `docs/TEAM/BENCHMARKS/DQI.md`; team and baseline governance paths, `origin/main` commit `3861f76f4842f40e70fc59ad69812052c2719f32` | Repository governance records; latest relevant approval-record history is commit `7ddcb3df96c52515c21629464351b1b840ae642f` (2026-11-19) | Relevant docs’ Git blob IDs and SHA-256 values recorded in §4 | **VERIFIED** as repository-recorded status; no newer approval record found | Whether any approval exists outside available repository records | Obtain attributable, explicit records in the designated governance channel |

### Research contract now established by E-02

The paper specifies:

- The dual Reed–Solomon code parameters `[4095,4025,71]` over
  `GF(2^12)`, with `(m,n,b,r)=(4095,70,12,2016)` and correctable symbol
  weight `ell=n/2=35`.
- The field representation
  `GF(2^12) = GF(2)[alpha]/(alpha^12 + alpha^6 + alpha^4 + alpha + 1)`,
  in the little-endian polynomial basis
  `(1, alpha, ..., alpha^11)`.
- Evaluation points `alpha_j=alpha^j` and syndrome coordinates
  `s_i = sum_{j=0}^{m-1} e_j alpha^((i+1)j)`, for `i=0,...,n-1`.
- A unique correctable error for each promised syndrome: since the dual
  code’s minimum distance is `n+1=71` and `2*ell=70`, two distinct errors
  of weight at most `ell` cannot share a syndrome.
- The target phase correction
  `U_c |s>|0>_W = (-1)^(c dot bin(e(s))) |s>|0>_W`; `c` is the uniformly
  random binary measurement record, field-symbol binary encoding uses the
  selected basis, and the dot product is parity modulo two.
- The paper’s reference route: solve the key equation with EEA, locate errors
  by Chien search, recover error symbols with Forney’s formula, apply the
  phase, and uncompute the EEA to restore syndrome and clear auxiliary
  workspace. Other implementations may compute symbols individually or
  compute the required parity directly; EEA is a reference, not a mandated
  algorithm.
- The paper’s reference circuit figures: 1,893 total qubits and 5,725,461
  Toffolis after cleanup. These are published reference metrics, not
  independently measured local artifacts and not a candidate resource cap.

## 4. Source provenance and integrity

### External sources

- **arXiv paper:** The public arXiv record identifies v2, date 2026-10-21,
  named authors, and DOI. The HTML contains the paper’s sections/equations
  cited above. A raw PDF/HTML byte hash was not calculated; rendered web
  content is not treated as an immutable local artifact.
- **Kaggle page:** Fetched page title and description are visible, but its body
  is client-rendered and does not expose a verifier, schema, or benchmark
  files. Dynamic-page digest/version not recorded.
- **Paper’s DQI internal-run hash:** The paper publishes
  `0701f553a9ac4e8af100f66acfccf2fc82cf5a44c2e5aa765b1d4ace01cbaadb` as
  the authors’ best internal DQI run commitment. Its associated circuit is
  not available in inspected refs, so no integrity match was performed. It is
  not assumed to be the named sample file or verifier.

### Repository records

The following governance/specification documents were read from
`origin/main` at `3861f76f4842f40e70fc59ad69812052c2719f32`. Git blob IDs
identify the exact repository content; SHA-256 is computed from `git show`
bytes. These hashes establish identity of the inspected repository documents,
not authority or truth of every statement in them.

| Repository path | Git blob ID | SHA-256 |
|---|---|---|
| `docs/COMPETITION_REQUIREMENTS_MATRIX.md` | `b47aeeb78bbee583d624d3a5db27146d5987b258` | `07d67c866166ca00eaf1a28b2b363f18ca8eb5aa55a1fae9c3ed2fecf573656c` |
| `docs/OFFICIAL_VERIFIER_API_REFERENCE.md` | `0b9a435c443d251639ea0b434d9fb847a4d12ea3` | `476606e6da718cee1c6239d63ad67dfd43e51416d3a1b896bd00a68a5580cf34` |
| `docs/SCORE_MODEL_VERIFICATION.md` | `c75dbfab51c2c72539c84001856e7ab7f7ff38e0` | `0df7adfd6c36e2e2d2de1138cd6a34695e0afb3075af5f899d94aab3b75d0f20` |
| `docs/BASELINE_REPRODUCTION_REPORT.md` | `b895a64a8fa908ac70354979fa4a9f1156470ef6` | `49643c373ccb8814604c278fe1ada8ee1eee0cf83b5a34fef3472b280f35a91a` |
| `docs/BASELINE_EVIDENCE_RECONCILIATION.md` | `08e09144099060129a8a96ff2cc2215cc254360e` | `7491199b1b70d454ed10cf47d228f0664eb7c219e5d53d82be774b81be173d9f` |
| `docs/BASELINE_EXECUTION_APPROVAL_REQUEST.md` | `d1009bb0a3c89f5a62d50ae03f87369bea6b530c` | `7e2bf6a67b510d44906d8d0275519b9faa03a31365a5f65974c50b7dc825c7c7` |
| `docs/BASELINE_STATUS_MATRIX.md` | `685562b785dcfeef7558091c46b9d2f5e922062e` | `5b120cbf187ba2d250fa13607f2d83b1aaa8b86e150756f6f9a19ab7cab14db9` |
| `docs/TEAM/BENCHMARKS/DQI.md` | `d2319b2877ddf5654ff347d5e175a86862df4342` | `a6245844e1a8c6879a8321e67ccc4e76d3b33145cb28692eee382e85837046cb` |
| `docs/TEAM/TEAM_STRUCTURE.md` | `ba79cbc3e93345d6990b4ef134009bff845b3088` | `ac95cd5fc91c968621f722f032cf56ff99be7c9858b45809d8f708dc869aeab1` |
| `docs/TEAM/TEAM_RESPONSIBILITY_MATRIX.md` | `29b26e10cf96bda0d3e00043c1ab781555c2936b` | `809131b1efdc4cca7e0b0d7f3ac2b3dc27564d8d24015f1336fad46d7372e2d2` |
| `docs/TEAM/TEAM_TASK_BOARD.md` | `c119f2d9e3f2a6b0fc4e3f202440dff7a981028a` | `b158ff5e965b57a2e9a4332309cce3995f40a07f1c575140299a3f975e05a7b4` |
| `docs/TEAM/INDIVIDUAL_TASKS/SONJOY.md` | `47a473a553742c34d82f7a27702c6ff782e01faf` | `8b759a0d5e5ea1499c5f7dc5c12ffb656ff671a7f97613d6f2772e7f92168511` |
| `docs/TEAM/REVIEW_AND_ACCEPTANCE_POLICY.md` | `06548fde5168bb2b06ffcd4d87bdcc460c66f6d9` | `162b882767518ac54270dfd82f207b5bf803959f419509c90574aa32b20904dd` |

Additional later-ref evidence, read-only:

- `origin/feat/compiler-infrastructure` at
  `6bf3ff2b4a97b691764deae45be33e4143a0f93b` contains
  `docs/phase-10-dqi-readiness-report.md` and
  `docs/official-verifier-integration-contract.md`; it does not contain the
  verifier or DQI artifacts.
- `origin/seyamb/verification-engineering` at
  `a982be395d79ffbcae1e5fa0c7699f7b3fd0be1e` contains the governance
  summaries; it does not contain the verifier or DQI artifacts.
- The applicable ownership/approval files in both `origin/main` and
  `origin/seyamb/verification-engineering` trace to the team-readiness commit
  `7ddcb3df96c52515c21629464351b1b840ae642f` (2026-11-19). No later
  commit changing those records was found.
- P001/P002 are worktree documents but untracked/not present in `HEAD`; their
  content is preserved. They are not governance approval records.

## 5. Authorization evidence matrix

Status is assigned only from attributable recorded evidence. “PENDING” denotes
an explicit approval request with no recorded decision; “NOT VERIFIED” means
the required approval record is absent; “NOT AUTHORIZED” means the governing
record explicitly prohibits action absent a gate.

| Decision | Required evidence and inspected source | Status | Finding |
|---|---|---|---|
| Sonjoy's explicit DQI work-package acceptance | `docs/TEAM/INDIVIDUAL_TASKS/SONJOY.md` lines 1–6, 31–48, 70–78; responsibility matrix lines 34–46 | **NOT VERIFIED** | No availability, selected scope, acceptance date, or channel recorded. Sonjoy’s proposed scopes are research-support options, not a DQI decoder assignment. |
| Project-lead approval of the accepted scope | Sonjoy task file lines 31–48 and 53–57; team responsibility matrix acceptance register | **NOT VERIFIED** | No defined Sonjoy DQI scope or Yousuf record of its approval/acceptance was found. |
| Read-only source inspection permissions | `docs/TEAM/BENCHMARKS/DQI.md` lines 29–47; team responsibility matrix lines 48–55 | **VERIFIED** for the listed reference paths | Governance defines official verifier, reference source, sample, and evidence paths as read-only. This is not permission to execute a verifier or to access unavailable artifacts by bypassing controls. |
| Diagnostic execution | DQI workstream lines 60–71 and 122–132 | **NOT AUTHORIZED** | Even bounded diagnostics require specific authorization. No diagnostic-specific authorization record found. |
| Full baseline execution | `docs/BASELINE_EXECUTION_APPROVAL_REQUEST.md` lines 1–3, 77–79; DQI workstream lines 5–8, 98, 105–110 | **PENDING** | Request explicitly awaits Yousuf approval; it states no command has been executed. Parameters in the request are not approval. |
| Optimization implementation | DQI workstream lines 5–8, 83–85, 122–132; review policy lines 60–70 | **NOT AUTHORIZED** | Baseline governance is unmet and explicit project-lead approval of transition is absent. |
| Independent review and final acceptance | `docs/TEAM/TEAM_RESPONSIBILITY_MATRIX.md` lines 22–46; `docs/TEAM/REVIEW_AND_ACCEPTANCE_POLICY.md` lines 30–43, 72–77 | **NOT VERIFIED** | SeyamB and other reviewer assignments remain proposed with no acceptance recorded. No candidate diff/evidence package has final acceptance. Yousuf retains project-level final review/approval authority. |

Task acceptance, change review, official verifier acceptance, and baseline or
release approval are separate decisions under the review policy
(`docs/TEAM/REVIEW_AND_ACCEPTANCE_POLICY.md` lines 3–15). None is inferred
from this directive, prior phase completion, or branch name.

## 6. Technical contract completeness

| Contract item | Evidence currently available | Readiness | Missing evidence / documented owner |
|---|---|---|---|
| Decoder mathematical semantics | Paper §III.2.1 Eqs. (36)–(38), §III.2.2; code [parameters and encoding in E-02/E-03] | Research-level semantics defined | Official executable conformance not established. Proposed DQI research lead is Mahin, but ownership remains proposed/unaccepted. |
| Finite-field representation | Paper §III.2.2 gives modulus and little-endian polynomial basis | Defined in paper | Must be cross-checked against official verifier and fixtures; no accepted implementation owner. |
| Input/output contracts | Paper specifies logical `(s,c)` input and phase-corrected syndrome output on correctable syndromes | Mathematical contract defined | Actual circuit register names/serial layout, CLI/API schema, output JSON, error behavior absent. Proposed DQI lead Mahin; verifier source authority is competition owner. |
| Reversible mapping | Paper specifies preserved syndrome, target sign, zeroed workspace, and describes reference uncomputation | Research contract defined | Complete verifier checks and circuit-file semantics unavailable. |
| Ancilla/workspace | Paper reports reference circuit at 1,893 qubits total and cleanup; Q counts syndrome plus workspace | Reference metric available, not a limit | No candidate workspace bound or official cap found; actual reference circuit absent. |
| Correctness/equivalence conditions | Paper describes computational-basis comparison to classical reference and the three checks referenced in §II.3/III.2.1 | Research-level criteria available | Official exact checker behavior/test fixtures and full result schema unavailable. Proposed evidence reviewer SeyamB, unaccepted. |
| Official verifier invocation/result schema | Local API summaries only; actual source absent; later readiness report says blocked | **Not ready** | Immutable official package, invocation, dependencies, input/output schemas, exit/failure and timeout rules, seed vectors. |
| Resource metrics | Paper Eq. (43) defines `R(eps+) Q^2 T`, Q total qubits, T single-run Toffoli count including cleanup | Paper formula defined | Official executable counting/scoring implementation absent; local score summary conflicts about `T` wording. |
| Statistical acceptance | Paper §§II.3/III.2.3: 102,400 shots, one-sided Clopper–Pearson bound at `1-2^-128`, reject at `eps+ >= 1/16` | Paper requirement defined | Verifier implementation, exact random-seed derivation and operational defaults absent; matrix D-12 conflicts with other local summaries. |

### Evidence classes

- **Primary research:** arXiv v2 supplies the mathematical benchmark definition,
  paper representation, reference-algorithm description, and statistical and
  resource rationale.
- **Repository summaries:** competition matrix, API reference, score report,
  baseline reports, and governance documents are versioned local records.
  Their presence and hashes are verified; claims about absent executable
  sources remain summaries.
- **Research interpretation:** the table above maps the paper’s equations and
  prose into explicit readiness findings; it is not additional official
  behavior.
- **Unverified assumptions:** that the current competition package uses the
  exact paper version/encoding; that the repository’s named verifier/sample
  digests match official releases; that local API defaults/output fields are
  accurate; and that no additional gate, resource cap, or required test exists.

## 7. Conflicting claims and reconciliation

1. **Paper versus absent executable package:** the paper defines a detailed
   mathematical and reference contract, while the later
   `origin/feat/compiler-infrastructure` readiness report says the verifier
   invocation, bit/wire mapping, and executable fixtures were not obtained.
   Reconciliation: treat the paper as authoritative primary research for its
   published sections, but not as evidence of actual executable verifier
   behavior.
2. **Verifier summaries versus verifier absence:** `docs/OFFICIAL_VERIFIER_API_REFERENCE.md`
   and `docs/SCORE_MODEL_VERIFICATION.md` give APIs, defaults, and code-line
   references, but the named source is absent from all inspected refs.
   Reconciliation: repository-record claims only; API and code behavior remain
   unverified.
3. **Run defaults versus matrix D-12:** matrix D-12 marks numeric default
   shots/batch size “NOT FOUND”; other summaries report 102,400/256/four
   workers. A separate approval request proposes 102,400/256/one worker.
   Reconciliation: the paper specifies the 102,400-shot statistical workload;
   the executable’s defaults and worker settings remain unverified. The
   proposed one-worker command is not approved.
4. **Register `E` versus measurement record `c`:** the API summary names
   classical `E_j` registers, while paper Eqs. (37)–(38) define a classical
   measurement record `c`. Equal bit counts do not prove these objects or
   serializations are identical. Keep the executable register mapping
   unresolved.
5. **`T` metric wording:** local score report calls `T` a mean per-shot
   Toffoli-like count; paper Eq. (43) calls `T` the single-run Toffoli count
   including cleanup. The paper is clear for its formula, but the absent
   scorer prevents verification that repository summary implements the same
   semantics. Use neither summary as executable proof.
6. **Paper’s DQI hash versus local baseline hash:** paper §III gives an
   internal-best-run hash; local baseline documents give a named sample
   circuit hash. Neither corresponding file is present for comparison. These
   hashes are for different described roles and must not be equated.
7. **Scope/assignment:** this directive names Sonjoy, but governance records
   list Mahin as proposed DQI lead and Sonjoy as unconfirmed research support.
   Reconciliation: directive/branch names are not recorded acceptance;
   work-package ownership remains NOT VERIFIED.

## 8. Missing artifacts and ownership

The following are absent from the inspected `origin/main`,
`origin/seyamb/verification-engineering`, and
`origin/feat/compiler-infrastructure` refs:

- `external/verifiers/dqi/verify_submission_dqi.py`
- `external/verifiers/dqi/dqi_reference_circuit.py`
- `external/sample_submission/dqi.kmb` and `.kmx`
- `docs/research/PRIMARY_SOURCE_FINDINGS.md`
- `docs/evidence/` and `results/raw/`
- authorized DQI fixtures and expected-output records

Ownership records identify Mahin as **proposed** DQI research lead, SeyamB as
**proposed** evidence reviewer, and Yousuf as project lead/approval authority.
The responsibility matrix acceptance register records no scope acceptance for
these roles. Do not treat any proposed name as an accepted artifact owner.
The official competition/verifier artifact owner is not identified in the
available repository records; the project must obtain these materials from an
authorized competition source.

## 9. Implementation readiness checklist

- [x] Primary research source/version located and reviewed for DQI §§III.2.1–III.2.3.
- [x] Mathematical code parameters, field basis, syndrome formula, correction
  phase, reference algorithm, score model, and paper-level statistical
  requirements extracted.
- [x] Repository summaries and governance records inspected with provenance.
- [x] Current and other refs checked for named verifier, reference, sample,
  evidence, and raw-output artifacts.
- [ ] Official competition executable contract and immutable verifier/scorer obtained.
- [ ] Official verifier/source/sample digests independently matched to bytes.
- [ ] Register declarations, input/output serialization, and expected fixtures verified.
- [ ] Sonjoy’s DQI work-package accepted and Yousuf’s scope approval recorded.
- [ ] Independent reviewer assignment and acceptance recorded.
- [ ] Diagnostic authorization recorded, if a diagnostic is proposed.
- [ ] Full-baseline approval recorded before any baseline run.
- [ ] Optimization explicitly authorized after baseline governance and review.

**Gate result:** prerequisites remain incomplete; implementation review is
blocked.

## 10. Diagnostic execution gate

**Status: NOT AUTHORIZED.** The DQI workstream says not to run even a small
diagnostic without specific authorization (`docs/TEAM/BENCHMARKS/DQI.md`
lines 122–126). No diagnostic-specific approval was found. P003 did not run
tests, diagnostic code, verifier code, or any DQI workload.

## 11. Baseline execution gate

**Status: PENDING.** The baseline approval request is explicitly awaiting
Yousuf’s approval and says the proposed command has not been executed
(`docs/BASELINE_EXECUTION_APPROVAL_REQUEST.md` lines 1–3, 77–79). The
workstream and status matrix mark DQI full execution blocked. The paper’s
102,400-shot statistical specification and the command’s proposed parameters
do not grant execution permission. Do not run until an attributable approval
of the exact workload, environment, and recovery boundary is recorded.

## 12. Optimization authorization gate

**Status: NOT AUTHORIZED.** Governance prohibits optimization before baseline
requirements are met and requires explicit project-lead approval for the
transition (`docs/TEAM/BENCHMARKS/DQI.md` lines 5–8, 83–85, 122–132;
`docs/TEAM/REVIEW_AND_ACCEPTANCE_POLICY.md` lines 60–70). Neither the
baseline nor scope acceptance gate is satisfied. Paper discussion of possible
optimizations is not project authorization.

## 13. Recommended next phase

Do not begin implementation yet. First:

1. Obtain and record Sonjoy’s explicit acceptance of a bounded DQI work-package
   and Yousuf’s approval of that defined scope; resolve proposed DQI ownership
   and reviewer assignments without editing governance records in this phase.
2. Obtain authorized immutable official verifier/scorer source, reference and
   sample circuits, fixture inputs/expected results, schemas, invocation,
   dependency/runtime requirements, error behavior, seed vectors, and hashes.
3. Reconcile the paper’s equations/representation to the actual verifier and
   fixture register/bit ordering. Confirm whether the paper’s internal-run hash
   and repository sample digest describe distinct artifacts.
4. Obtain separate explicit authorization before any diagnostic; obtain
   specific full-run approval before any 102,400-shot execution.
5. Only after these gates, prepare a separately reviewed implementation
   proposal and test/resource plan. Seek optimization authorization in a
   distinct decision after baseline governance.

Recommended next phase: **P004 — Authorized Verifier and Fixture Intake**,
limited to acquiring/recording approved source and artifact provenance. It
must not execute the verifier or benchmark absent the relevant explicit
approval.

## 14. Acceptance criteria

- [x] Inspected current branch, HEAD, worktree, P001/P002, and relevant docs.
- [x] Inspected relevant governance/specification refs read-only and identified
  which records are current-branch versus other-ref evidence.
- [x] Located and reviewed the public versioned primary research paper without
  claiming it is an executable verifier.
- [x] Inventoried official specification, decoder definition, field, verifier,
  reference, samples, register contract, reversibility, metrics, and
  statistics with evidence status, provenance, hash state, unresolved items,
  and next actions.
- [x] Created a separate authorization matrix with only attributable
  repository-record evidence.
- [x] Reconciled paper facts with P001/P002 and explicitly documented conflicts.
- [x] Did not implement code, create circuits, run tests/diagnostics/verifier,
  execute the full workload, install dependencies, or modify protected assets
  or governance records.
- [x] Preserved P001/P002 and unrelated untracked INVSQRT caches.
- [x] Confirmed branch and HEAD remained unchanged and no unrelated files were
  modified.

## 15. Final status

**BLOCKED.** The published mathematical/research contract is substantially
specified, but implementation review is not ready because the executable
verifier and fixtures are absent and ownership, diagnostic, baseline, and
optimization approvals are not established. This report does not authorize
implementation or execution.
