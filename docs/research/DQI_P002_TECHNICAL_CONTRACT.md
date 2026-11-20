# DQI-P002 — Technical Contract and Authorization Reconciliation

**Project:** Google Quantum AI — Verifiable Quantum Circuit Compilation
**Workstream:** DQI Decoder
**Developer named by directive:** Sonjoy
**Branch:** `feat/dqi-decoder`
**Phase:** 02 — Technical Contract and Readiness Gate
**Assessment date:** 2026-11-20
**Status:** Contract evidence reconciled; executable contract and required
authorizations NOT VERIFIED

## 1. Problem statement

The repository's DQI workstream describes a reversible Reed–Solomon decoding
benchmark over `GF(2^12)`. The intended operation is documented as a
syndrome-controlled phase transformation: preserve the syndrome, return
workspace to zero, and apply a phase determined by a classical bit string and
the decoded error vector.

This is a documentary statement, not an implementation-ready specification.
The competition matrix cites paper equations, but the cited primary-source
dossier, verifier, reference circuit, and sample circuit are absent from the
available trees. A later DQI readiness report explicitly lists field and
syndrome encoding, register/wire mapping, and record bit order as missing.
Therefore this report records what local documents say and marks the missing
executable semantics as unresolved. It does not choose a decoder algorithm.

## 2. Mathematical notation and decoder semantics

The available competition matrix, `docs/COMPETITION_REQUIREMENTS_MATRIX.md`
§3, rows D-01–D-03 (lines 64–70), records:

- Instance label: `RS(4095,4025)` over `GF(2^12)`.
- Parameter tuple: `(m,n,b,r) = (4095,70,12,2016)`.
- Syndrome relation: `s = B^T e`.
- A weight condition written `wt(e) <= ell`.
- The target action:

  ```text
  U_c |s>|0>_W = (-1)^(c·bin(e(s))) |s>|0>_W
  ```

Here `s` is the syndrome register, `W` is workspace, `c` is described as a
classical bit string, and `e(s)` is the error vector named by the matrix.
These symbols and the equation are copied as documented; no additional
interpretation is assumed.

**Unresolved mathematical semantics:** the accessible documents do not define
the field polynomial/basis, element encoding, matrix `B`, coordinate order,
`ell`, the map selecting `e(s)`, uniqueness or decoding-domain conditions, the
meaning/order of `bin`, or the layout and length convention for the dot
product. Nor do they explain how a 49,140-bit classical value is supplied to
the quantum circuit/verifier. These details must come from the authorized
primary specification and fixtures.

The later `origin/feat/compiler-infrastructure` record
`docs/phase-10-dqi-readiness-report.md` lines 5–12 independently identifies
missing register/wire mapping, field and syndrome encoding, and record bit
order. It also marks verifier invocation, shot/seed semantics, and official
baseline missing.

## 3. Input contract

| Input aspect | Repository-documented statement | Status |
|---|---|---|
| Problem parameters | `RS(4095,4025)`, `GF(2^12)`, `(m,n,b,r)=(4095,70,12,2016)`; competition matrix D-01, line 68 | Paper-cited in a local matrix; primary source not available for verification |
| Syndrome | `s=B^T e`; matrix D-02, line 69 | Paper-cited notation; `B`, encoding, dimension/order, and valid syndrome domain unresolved |
| Decoded vector | `e(s)` with `wt(e)<=ell`; matrix D-02, line 69 | Mapping and `ell` unresolved; do not assume uniqueness or a decoding rule |
| Classical phase input | `c` is reported as 49,140 classical bits; matrix D-04, line 71; baseline reproduction report DQI table, line 72 | Reported dimension only; bit order, binding to circuit, and serialization unresolved |
| Verifier register names | API reference says quantum `S0..S69` and classical `E0..E4094`, all width 12 and pairwise disjoint; `docs/OFFICIAL_VERIFIER_API_REFERENCE.md` lines 60–65 | Unverified summary of an absent source; conflicts in wording with other register descriptions |
| Required circuit artifact | Documents name `external/sample_submission/dqi.kmb`; DQI workstream `docs/TEAM/BENCHMARKS/DQI.md` lines 31–47 | Path is absent in inspected refs; format and official artifact identity cannot be checked |
| Encoding and wire mapping | No accessible executable mapping | Unresolved; implementation blocker |

The 70 width-12 syndrome registers implied by the API-reference summary total
840 qubits, consistent with the number in matrix D-04. The 4,095 width-12
`E` registers total 49,140 bits, consistent with the recorded size for `c`;
however, the API reference calls these `E` registers classical bit registers,
while the mathematical formula separately names `c`. Equality of these
representations is **not established** and must not be inferred from matching
counts.

## 4. Output contract

At the circuit level, the only documented output condition is the state action
in §2: syndrome `s` is preserved, workspace is zero, and the specified phase
is applied. The available documents do not establish:

- behavior for nonzero workspace or inputs outside the stated condition;
- the complete unitary on all basis states;
- a classical decoded-vector output (none is specified by the recorded target
  action);
- exact measurement, phase, or bit serialization conventions; or
- an official verifier JSON schema, exit-code contract, and failure-output
  behavior.

The verifier API reference summarizes returned fields as value/phase failures,
empirical/effective error rates, repetition factor, Toffoli count, `Q`,
operations, and SHA-256 (`docs/OFFICIAL_VERIFIER_API_REFERENCE.md` lines
67–71). This is a local summary of an absent implementation, not a verified
output schema.

## 5. Reversibility requirements

The matrix D-02/D-03 (lines 69–70) and baseline reproduction report DQI contract
review (lines 73–78) document these conditions:

1. The input syndrome is preserved.
2. Workspace `W` is returned to zero.
3. The target phase is `(-1)^(c·bin(e(s)))`.

These are requirements for the stated input subspace `|s>|0>_W`; a complete
reversible extension outside that subspace, a gate-level uncomputation
sequence, ancilla allocation/lifetime, and maximum workspace size are not
specified in accessible sources. “Reversible” alone does not establish an
involution or a particular inverse circuit, so neither is assumed here.

## 6. Correctness and equivalence conditions

The DQI workstream document lists syndrome preservation, clean workspace, and
correct target phase as future decoder tests (`docs/TEAM/BENCHMARKS/DQI.md`
lines 87–101). These are the documented correctness observables, not a complete
formal equivalence contract.

For an eventual candidate to be assessed, authorized sources must define the
reference mapping and domain sufficiently to compare the candidate's phase and
register behavior. The exact wire/register map, field arithmetic convention,
allowed gate set, simulator semantics, test vectors, and verifier acceptance
behavior remain unresolved. No local structural check or paper-derived
calculation can substitute for the unavailable official verifier. No
correctness or equivalence test was performed for P002.

## 7. Verifier interface

Two repository summaries give the following interface claims:

1. `docs/COMPETITION_REQUIREMENTS_MATRIX.md` lines 122–144 shows
   `verify_submission_dqi.verify(dqi, dqi_spec, salt=salt)` and spec
   construction using `DEFAULT_NUM_SHOTS` and `DEFAULT_BATCH_SIZE`. It warns
   against inventing CLI flags.
2. `docs/OFFICIAL_VERIFIER_API_REFERENCE.md` lines 38–71 describes
   `ProblemSpecDQI.benchmark_instance(...)`,
   `clopper_pearson_upper_bound(...)`, `verify(...)`, a CLI, default parameters,
   register checks, returned values, and score calculation.

The named source,
`external/verifiers/dqi/verify_submission_dqi.py`, is absent in both
`origin/main` and `origin/seyamb/verification-engineering`. The later
`origin/feat/compiler-infrastructure` report
`docs/official-verifier-integration-contract.md` lines 3–44 states that no
official verifier/scorer release, invocation, fixtures, or full artifact
contract was obtained. It explicitly distinguishes paper-derived methodology
from executable verifier behavior.

Accordingly, all call signatures, CLI flags, defaults, register checks, output
fields, exception behavior, and scoring details above are **repository-reported,
not independently verified official API requirements**. Do not execute an
invented invocation or implement a substitute verifier.

## 8. Resource metrics

The competition matrix D-09/D-11 (lines 76–78), verifier API reference (lines
67–71), and score model summary (`docs/SCORE_MODEL_VERIFICATION.md` lines
18–33) report:

- `Q = circuit.num_qubits`, including syndrome and workspace.
- `T` is Toffoli-like operation count, with cleanup included in the documented
  benchmark accounting.
- `R(eps) = ln(2) / -ln(1/2 + 2*sqrt(eps))`.
- `score = R(eps_plus) * Q^2 * T`.

The score model summary calls `T` the mean Toffoli-like operations per shot;
the competition matrix describes it as a single-run count including cleanup.
This wording difference is unresolved against the absent verifier. It must not
be silently normalized. No maximum qubit count, depth threshold, or separate
workspace cap is found in the accessible DQI documents. Circuit depth is not
identified as a score input in these records.

These are formulas reported by local documents as verifier-derived or
paper-derived; the formula and implementation were not checked against the
official executable. No candidate resource measurement or score was produced
in P002.

## 9. Statistical requirements

The competition matrix D-07/D-08 (lines 74–75), the baseline reproduction
report DQI table (lines 75–79), and the verifier/score summaries report:

- `N = 102,400` for the full workload.
- A one-sided Clopper–Pearson upper confidence bound `eps_plus`, with
  `log2_delta = -128` as the described parameter.
- `eps_plus >= 1/16` is rejection; a finite score requires the strict
  inequality `eps_plus < 1/16`.
- The verifier summary defines `k = value_errors + phase_errors`,
  `eps_hat = k/N`, and computes `eps_plus` from `k`, `N`, and
  `log2_delta` (`docs/SCORE_MODEL_VERIFICATION.md` lines 18–33).
- The baseline reconciliation reports 256-shot and 1,024-shot diagnostic
  records with zero observed failures but failing confidence thresholds, and
  no full 102,400-shot result (`docs/BASELINE_EVIDENCE_RECONCILIATION.md`
  lines 63–74; `docs/BASELINE_REPRODUCTION_REPORT.md` lines 81–97).

The exact bound implementation and the meaning of its delta parameter are not
independently verified because the referenced verifier and primary-source
dossier are unavailable. Diagnostic outcomes are not full-workload acceptance
or a baseline score.

## 10. Benchmark restrictions

- The DQI workstream says the baseline command has not been executed and awaits
  explicit Yousuf approval (`docs/TEAM/BENCHMARKS/DQI.md` lines 5–27).
- The baseline approval request is explicitly pending, with 102,400 shots,
  batch size 256, `log2_delta=-128`, one worker, a 16-hour timeout, and a
  proposed salt (`docs/BASELINE_EXECUTION_APPROVAL_REQUEST.md` lines 1–3,
  9–30, 33–42, 77–79). These are a proposed run configuration, **not an
  approval**.
- The DQI workstream prohibits even a small diagnostic unless separately
  authorized, prohibits optimization before baseline governance requirements,
  and prohibits changing the prepared command without a new approval decision
  (`docs/TEAM/BENCHMARKS/DQI.md` lines 122–132).
- The team responsibility matrix says official verifier source, competition
  artifacts, shared libraries, and raw outputs are read-only, and prohibits
  the full DQI run without explicit Yousuf approval (`docs/TEAM/TEAM_RESPONSIBILITY_MATRIX.md`
  lines 48–57).
- No verifier, benchmark, diagnostic, dependency install, artifact mutation, or
  raw evidence operation was performed for P002.

## 11. Source-to-requirement traceability

Classification key:

- **Repository-documented:** stated in an available repository record; not
  necessarily verified against its cited primary source.
- **Paper-derived claim:** a repository document attributes the claim to the
  paper. The primary paper text/dossier is not present in the inspected trees.
- **Derived interpretation:** a transparent consequence of documented values,
  not a separately verified official rule.
- **Unresolved assumption:** insufficient evidence to define the requirement.

| Requirement | Exact available source/reference | Evidence class and findings |
|---|---|---|
| Reed–Solomon instance and field size | `docs/COMPETITION_REQUIREMENTS_MATRIX.md` D-01, line 68; cited paper §III.2.2 Eq. (39). Cross-reference: `docs/BASELINE_REPRODUCTION_REPORT.md` lines 69–72. | Paper-derived claim, marked VERIFIED by repository authors; primary source unavailable locally. |
| `s=B^T e`, weight constraint, target phase | `docs/COMPETITION_REQUIREMENTS_MATRIX.md` D-02, line 69; cited paper §III.2.1 Eq. (38). | Paper-derived claim; decoding map, `ell`, encodings, and uniqueness unresolved. |
| Syndrome preservation and clean workspace | `docs/COMPETITION_REQUIREMENTS_MATRIX.md` D-03, line 70; `docs/BASELINE_REPRODUCTION_REPORT.md` lines 73–78. | Paper-derived claim, not executable-verified here. |
| Syndrome and classical-record sizes | `docs/COMPETITION_REQUIREMENTS_MATRIX.md` D-04, line 71; `docs/BASELINE_REPRODUCTION_REPORT.md` lines 71–74. | Paper-derived claim; representation and `c` mapping unresolved. |
| Register count and register names | Matrix D-05, line 72; `docs/OFFICIAL_VERIFIER_API_REFERENCE.md` lines 60–65. | Conflicting/incomplete repository summaries; source verifier absent. |
| Error/syndrome sampling | Matrix D-06, line 73; cited paper §III.2.3. | Paper-derived claim; sampling semantics not executable-verified. |
| Allowed operations | Matrix global requirement S-06, lines 35–43; verifier API summary says `Z_POW` is rejected, lines 60–65. | Repository-documented; exact DQI-specific allowlist and parser behavior unresolved. |
| Shot count and confidence level | Matrix D-07, line 74; `docs/BASELINE_REPRODUCTION_REPORT.md` lines 75–79; `docs/SCORE_MODEL_VERIFICATION.md` lines 18–33. | Repository reports 102,400 and a one-sided bound at `1-2^-128`; paper/verifier source unavailable. |
| Statistical rejection threshold | Matrix D-08, line 75; verifier API summary lines 60–65; DQI workstream lines 77–85. | Repository-documented strict rule `eps_plus < 1/16`; not checked against executable. |
| Score formula and its inputs | Matrix D-09/D-11, lines 76–78; score model lines 18–33. | Repository-reported formula; `T` wording conflicts (single-run vs mean per shot); executable interpretation unresolved. |
| Numeric verifier defaults | Matrix D-12, line 79; API reference lines 44–57; DQI workstream lines 17–19. | Conflict: matrix says numeric defaults NOT FOUND; other summaries state defaults. Treat shot/batch/worker defaults as unverified. |
| Verifier invocation/schema | Matrix lines 122–144; API reference lines 38–71; `docs/official-verifier-integration-contract.md` lines 32–44 on compiler-infrastructure ref. | Conflicting repository evidence; actual source absent; invocation and schemas blocked. |
| Full baseline parameter set | `docs/BASELINE_EXECUTION_APPROVAL_REQUEST.md` lines 9–30, 33–42, 77–79. | Proposed approval request only; no approval and no execution. |
| Diagnostic permissions | `docs/TEAM/BENCHMARKS/DQI.md` lines 60–71 and 122–132. | Each diagnostic requires specific authorization; no permission found. |
| Official full execution status | `docs/BASELINE_STATUS_MATRIX.md` lines 3–9; `docs/BASELINE_EVIDENCE_RECONCILIATION.md` lines 63–74. | Repository records say full run absent and DQI BLOCKED; no verifier run performed here. |
| Project ownership and reviewer | `docs/TEAM/TEAM_RESPONSIBILITY_MATRIX.md` lines 13–43; `docs/TEAM/BENCHMARKS/DQI.md` lines 49–58. | Mahin/SeyamB roles proposed; no assignments accepted in the register. Yousuf is the stated execution approval authority. |
| Sonjoy work-package acceptance | `docs/TEAM/INDIVIDUAL_TASKS/SONJOY.md` lines 1–6, 31–48, 70–78; responsibility matrix lines 34–46. | Not accepted/recorded. Branch and directive do not supply the required acceptance record. |
| Optimization authorization | DQI workstream lines 5–8, 83–85, 122–132; review policy lines 60–70. | Not authorized; baseline governance and explicit project-lead transition approval remain prerequisites. |
| Remaining executable contract blockers | `origin/feat/compiler-infrastructure:docs/phase-10-dqi-readiness-report.md` lines 3–12; `docs/official-verifier-integration-contract.md` lines 32–44, 70–77. | Later readiness audit says mapping, encoding, bit order, invocation, shot/seed semantics, verifier release, fixtures, and schemas are blocked. |

## 12. Conflicts and unresolved assumptions

1. **Primary evidence unavailable:** `external/verifiers/dqi/verify_submission_dqi.py`,
   `external/verifiers/dqi/dqi_reference_circuit.py`,
   `external/sample_submission/dqi.kmb`, `docs/evidence/`, and
   `docs/research/PRIMARY_SOURCE_FINDINGS.md` are absent in the inspected
   `origin/main` and `origin/seyamb/verification-engineering` trees.
2. **Verifier contract conflict:** `docs/OFFICIAL_VERIFIER_API_REFERENCE.md`
   and `docs/SCORE_MODEL_VERIFICATION.md` summarize a detailed API and
   executable behavior. The later
   `origin/feat/compiler-infrastructure:docs/phase-10-dqi-readiness-report.md`
   and `docs/official-verifier-integration-contract.md` state the executable
   contract and fixtures were not obtained. Without the named files and
   provenance, the summaries cannot resolve this conflict.
3. **Shot defaults conflict:** matrix D-12 says numeric defaults were NOT
   FOUND, while the verifier API reference and workstream document state
   numeric defaults. The separate full-run request supplies a proposed
   configuration. Defaults and approved execution parameters must not be
   conflated.
4. **Register semantics conflict/incomplete:** summaries describe `S_i`,
   `E_j`, syndrome `s`, workspace `W`, and classical `c`, but no available
   primary source defines their complete mapping or the relationship between
   `E` and `c`.
5. **Finite-field and decoder definitions missing:** field polynomial/basis,
   coefficient/bit order, `B`, `ell`, the exact decoder map and valid domain
   remain unknown.
6. **Resource `T` wording conflict:** one source calls it a single-run
   Toffoli count including cleanup; another calls it a mean per-shot
   Toffoli-like count. No executable evidence reconciles the definitions.
7. **Statistical implementation unavailable:** the bound function is named in
   an API summary, but the source, exact confidence-bound algorithm, input
   normalization, and failure semantics were not accessible.
8. **No depth or explicit workspace cap found:** absence from the examined
   records is not proof that no such official constraint exists.

No disputed value is elevated to an implementation contract in this report.

## 13. Implementation prerequisites

Before any decoder implementation is considered:

1. Obtain recorded project-lead disposition of the developer's defined DQI
   scope and the developer's explicit acceptance, recorded under the team
   governance process.
2. Obtain authorized immutable official verifier/scorer source or release,
   checksum, license/runtime/dependency requirements, official invocation,
   schemas, exit/failure behavior, and test fixtures.
3. Obtain the authoritative paper/specification and relevant primary-source
   extracts; resolve `B`, field representation, `ell`, register/bit ordering,
   `e(s)`, `c`, phase, and the valid input domain.
4. Resolve the shot/default conflict and document the official statistical
   acceptance rule against the executable verifier.
5. Define approved candidate paths, a reversible correctness test strategy,
   and resource accounting including workspace and cleanup.
6. Keep diagnostic execution, full baseline execution, and optimization as
   separate decisions. Obtain exact, explicit authorization before any
   diagnostic or full workload; optimization remains blocked until baseline
   governance is met and the project lead explicitly approves transition.
7. Obtain an independent, recorded review under the applicable acceptance
   process. Do not treat proposed reviewer assignments or this report as
   approval.

## 14. Authorization status

| Decision | Current evidence | Status |
|---|---|---|
| Sonjoy accepts this DQI work-package | `docs/TEAM/INDIVIDUAL_TASKS/SONJOY.md` says no accepted scope or response is recorded; responsibility matrix acceptance register says no response | **NOT VERIFIED** |
| Project lead accepts/approves Sonjoy's defined DQI scope | Governance makes Yousuf the project lead and says scope must be recorded; no such acceptance record found | **NOT VERIFIED** |
| Full 102,400-shot baseline execution | Baseline request explicitly awaits Yousuf approval; workstream says blocked and command unexecuted | **NOT VERIFIED — NOT APPROVED** |
| Bounded diagnostic execution | DQI restrictions require specific authorization even for small diagnostics; no diagnostic authorization record found | **NOT VERIFIED — NOT APPROVED** |
| Optimization | DQI workstream and acceptance policy explicitly prohibit it before baseline governance and project-lead transition approval | **NOT AUTHORIZED** |
| Reviewer assignment/acceptance authority | SeyamB evidence reviewer and other assignments remain proposed; reviewers cannot approve execution on Yousuf's behalf. Yousuf is the documented project-level approval authority | **Reviewer acceptance NOT VERIFIED; approval role documented** |
| Official verifier acceptance | No candidate/run result is established by this task; local summaries are not the official executable | **NOT APPLICABLE / NOT VERIFIED** |

The project review policy distinguishes task acceptance, change review,
verifier acceptance, and baseline/release approval (`docs/TEAM/REVIEW_AND_ACCEPTANCE_POLICY.md`
lines 3–15). None should be inferred from this directive, branch name, or
documentation artifact.

## Sources inspected

Repository records were inspected at these available revisions:

- `origin/main` — `3861f76f4842f40e70fc59ad69812052c2719f32`.
- `origin/seyamb/verification-engineering` —
  `a982be395d79ffbcae1e5fa0c7699f7b3fd0be1e`.
- `origin/feat/compiler-infrastructure` —
  `6bf3ff2b4a97b691764deae45be33e4143a0f93b`.

Relevant paths are identified with line/section references in the traceability
table. No official verifier, benchmark, diagnostic, or dependency operation was
performed. This artifact defines no decoder algorithm and authorizes no
implementation or execution.
