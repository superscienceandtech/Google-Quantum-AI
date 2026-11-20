# DQI-P001 — Development Foundation

**Project:** Google Quantum AI — Verifiable Quantum Circuit Compilation
**Workstream:** DQI Decoder
**Developer named by this directive:** Sonjoy
**Target branch:** `feat/dqi-decoder`
**Phase:** 01 — DQI Development Foundation
**Assessment date:** 2026-11-20
**Status:** Foundation documented; implementation and benchmark execution remain blocked

## 1. Development objective

Establish an evidence-based foundation for future work on the reversible
Reed–Solomon decoder used by the DQI benchmark. Future work may include a
correctness-preserving circuit, independent verification, and resource analysis
only after the decoder contract, authorized scope, and official verifier
requirements are established.

This report is an inspection and planning artifact. It does not specify a
decoder algorithm, authorize optimization, or authorize any verifier or
benchmark execution.

## 2. Branch and repository state

- Repository root: `D:\PROJECT\Quantum_AI\Google-Quantum-AI`
- Active branch: `feat/dqi-decoder`
- HEAD: `5391b2e7123484efacffc0588f5e761e67b5cb55`
- This branch and `origin/feat/dqi-decoder` point to the initial repository
  commit. Its only tracked file is `README.md`; no DQI implementation, tests,
  configuration, or research report existed before this document.
- Tracked worktree changes before this report: none.
- The worktree contained untracked Python bytecode caches under
  `src/invsqrt_opt/__pycache__/` and `tests/__pycache__/`. These are INVSQRT
  leftovers, not DQI assets. They were not read as DQI source, modified, or
  deleted.
- The requested report path did not exist before this change.

No branch switch, merge, cherry-pick, reset, rebase, staging, commit, push,
dependency installation, or file deletion was performed.

## 3. DQI technical specification summary

The available repository documents describe the benchmark as a reversible
Reed–Solomon decoding task. Their claims are **documentary, not independently
verified against primary sources in this checkout**:

- The competition matrix describes an `RS(4095,4025)` instance over
  `GF(2^12)`, with `(m,n,b,r) = (4095,70,12,2016)`.
- It gives a target operation of the form
  `U_c |s>|0>_W = (-1)^(c·bin(e(s))) |s>|0>_W`, where `s = B^T e` and
  `wt(e) <= ℓ`. The intended invariants are syndrome preservation, clean
  workspace, and the correct target phase.
- The same matrix records 840 syndrome qubits and 49,140 classical bits for
  `c`, and describes quantum registers `S_i` and `E_j`. The verifier API
  reference separately describes `S0..S69` and `E0..E4094` as width-12,
  pairwise-disjoint registers.
- The documented verifier defaults are 102,400 shots, batch size 256,
  `log2_delta=-128`, and four workers. A separate baseline approval request
  proposes a single-worker run. The documented score uses an upper confidence
  bound and rejects when `eps_plus >= 1/16`.
- The documentation states that `Q` includes syndrome and workspace qubits
  and that `T` includes cleanup. Its stated score formula is
  `R(eps_plus) Q^2 T`, with `R(eps) = ln(2) / -ln(1/2 + 2 sqrt(eps))`.

The register descriptions, bit/wire mapping, field and syndrome encoding,
record bit order, exact phase convention, and executable meaning of the
parameters have not been reconciled to an accessible official verifier or
fixture. The numerical and API details above must not be used as an
implementation contract until verified against primary, authorized materials.

### Confirmed versus unresolved

| Topic | Evidence status for P001 |
|---|---|
| Work concerns a reversible Reed–Solomon decoder | Stated in DQI workstream documentation; primary algorithm source not available in the checkout |
| Syndrome preservation, clean workspace, target phase | Stated as required invariants in repository documentation; circuit-level contract not executable or independently confirmed |
| Field parameters, register dimensions, bit order, register/wire mapping | Conflicting or incomplete repository descriptions; unresolved |
| Arithmetic operation set and decoder algorithm | No verified algorithm or official encoding available; unresolved |
| Uncomputation strategy and ancilla lifetime | Required in principle by the stated clean-workspace invariant; concrete method and workspace bound unresolved |
| Circuit instruction/gate allowlist and decomposition rules | No DQI executable contract or target circuit fixture available in the active branch; unresolved |
| Verifier API, seeds, salts, sampling, confidence-bound implementation | Described by repository documents, but the referenced official source is absent and a later readiness report says invocation and shot/seed semantics are missing |
| Resource limits and score interpretation | Formula and accounting notes appear in repository documents; official executable interpretation and candidate measurements are unverified |

## 4. Authoritative requirement references

The following available records were inspected. Branch names and document
statements are recorded so that their authority is not overstated:

- `origin/main` at
  `3861f76f4842f40e70fc59ad69812052c2719f32`:
  - `docs/TEAM/BENCHMARKS/DQI.md` — workstream status, restrictions, proposed
    deliverables, and acceptance criteria.
  - `docs/COMPETITION_REQUIREMENTS_MATRIX.md` — DQI rows D-01 through D-12;
    its requirement claims cite the competition metric and paper.
  - `docs/OFFICIAL_VERIFIER_API_REFERENCE.md` — records an expected API,
    defaults, register checks, output fields, and score formula by source-line
    references.
  - `docs/BASELINE_EXECUTION_APPROVAL_REQUEST.md`,
    `docs/BASELINE_STATUS_MATRIX.md`,
    `docs/BASELINE_REPRODUCTION_REPORT.md`, and
    `docs/BASELINE_EVIDENCE_RECONCILIATION.md` — approval request and baseline
    evidence status.
  - `docs/TEAM/TEAM_STRUCTURE.md`,
    `docs/TEAM/TEAM_RESPONSIBILITY_MATRIX.md`,
    `docs/TEAM/TEAM_TASK_BOARD.md`, and
    `docs/TEAM/INDIVIDUAL_TASKS/SONJOY.md` — ownership, acceptance, and review
    governance.
  - `docs/TEAM/CONTRIBUTION_GUIDELINES.md` and
    `docs/TEAM/REVIEW_AND_ACCEPTANCE_POLICY.md` — contribution and acceptance
    expectations.
- `origin/feat/compiler-infrastructure` at
  `6bf3ff2b4a97b691764deae45be33e4143a0f93b`:
  - `docs/phase-10-dqi-readiness-report.md` — marks DQI readiness blocked and
    lists missing register/wire mapping, field and syndrome encoding, record
    bit order, verifier invocation, shot/seed semantics, and official baseline.
  - `docs/official-verifier-integration-contract.md` — states that no official
    verifier/scorer package, immutable release, invocation, or fixture bundle
    was obtained; paper-derived and local interfaces are not official verifier
    behavior.
  - `tools/compiler_infrastructure.py` — contains a local `CompilerVerifier`
    protocol and `VerificationResult`, explicitly not a statement of official
    acceptance.

These are repository records, not substitutes for the official verifier,
competition artifact, or primary research material. The later compiler
readiness report conflicts with the detailed verifier claims in `origin/main`.
The referenced `external/` verifier, sample, and primary-source research files
were not present in the inspected trees. Consequently, this report treats
executable requirements as unresolved and does not choose between conflicting
documentation.

## 5. Verified approval and scope

- **Developer ownership:** Not verified. The team responsibility matrix and
  Sonjoy individual task record both mark Sonjoy’s availability and accepted
  scope as unconfirmed; no acceptance is recorded. The DQI workstream and task
  board list Mahin as the proposed DQI lead. A branch name or this directive’s
  developer label does not change those approval records.
- **Baseline execution:** Not approved. The baseline request says it is awaiting
  explicit Yousuf approval and that its command has not been executed. The
  status matrix marks DQI blocked because no 102,400-shot run exists.
- **Optimization:** Not authorized. The DQI workstream and baseline records say
  optimization is not authorized until baseline governance requirements are
  met.
- **Verifier and artifacts:** Not available for direct inspection in the
  examined refs. Although repository documents name a DQI verifier and sample
  circuit and record digests, the files are absent from those trees; those
  details were not checksum-verified.
- **P001 scope:** This directive requests a documentation-only foundation
  report. It does not grant baseline execution, optimization, artifact
  modification, or verifier modification authority.

No DQI diagnostic or full workload was run. In particular, the 102,400-shot
workload was not run.

## 6. Existing assets and reusable interfaces

### In the active branch

- `README.md` contains only the general repository purpose and workflow.
- No DQI source, classical reference decoder, finite-field primitive, reversible
  polynomial utility, circuit-construction helper, official verifier, sample
  circuit, test suite, dependency manifest, or build/test configuration exists.
- The untracked INVSQRT bytecode caches are unrelated and are not reusable
  implementation assets.

### In other inspected refs

- `origin/main` provides DQI and governance documentation but not the referenced
  `external/verifiers/dqi/` source, sample circuit, raw results, or
  `docs/research/PRIMARY_SOURCE_FINDINGS.md`.
- `origin/feat/compiler-infrastructure` provides a generic local compilation
  lifecycle and a `CompilerVerifier` protocol. That interface is explicitly
  not an official competition verifier and has no verified DQI adapter. It is
  a possible future integration reference only, not an accepted DQI API.
- No DQI decoder implementation or candidate-specific test structure was found
  in the inspected available refs.

## 7. Proposed module boundaries

Do not create all possible components by default. Once scope and the executable
contract are approved, use only boundaries justified by that contract:

1. **Contract and register mapping** — capture verified encodings, dimensions,
   input/output registers, gate constraints, and acceptance conditions. This
   is a prerequisite, not an invented decoder specification.
2. **Decoder circuit** — isolate reversible decoder construction from the
   benchmark adapter. Add it only after the algorithm and allowed operation
   set are source-verified.
3. **Finite-field and polynomial primitives** — factor into modules only if
   decoder construction requires project-owned operations not already provided
   by an approved compiler/library.
4. **Workspace/uncomputation support** — record ancilla ownership and cleanup
   where not already enforced by the circuit representation. Avoid a separate
   manager abstraction unless concrete reuse or correctness checks require it.
5. **Classical reference** — add an independent, small-domain reference only
   if it can be derived from an authorized specification and is needed for
   differential correctness tests. It must not impersonate the official
   verifier.
6. **Verifier adapter and resource extraction** — keep the official process/API
   boundary and resource reporting separate from circuit generation, and add
   them only after the immutable official interface is available.
7. **Experiment record** — capture source/input digests, exact configuration,
   environment, outputs, and evidence classification for any separately
   approved experiment.

## 8. Proposed source and test directory structure

The active branch has no established Python layout. A minimal, conditional
starting point—subject to project conventions and approval—is:

```text
src/dqi_decoder/
    __init__.py
    contract.py             # only after the official contract is verified
    decoder.py              # only after an algorithm is authorized
    reference.py            # optional independent classical oracle
    resources.py            # only after resource semantics are verified
tests/dqi_decoder/
    test_contract.py
    test_reversible_properties.py
    test_reference_differential.py  # only if a reference is justified
    test_resources.py              # only after metric semantics are verified
```

These are proposals, not existing assets or approved paths. Finite-field,
polynomial, workspace, circuit-decomposition, and verifier-adapter modules
should be split out only when a verified requirement and actual reuse warrant
them. Keep official verifier code, competition artifacts, and raw evidence
outside candidate-owned write paths.

## 9. Correctness and verification strategy

After requirements and scope are approved:

1. Freeze the official input/output contract, wire ordering, field encoding,
   phase convention, allowed gates, and clean-workspace condition with source
   citations and fixture digests.
2. Test field and polynomial primitives independently against transparent,
   small, hand-checkable cases. Do not assume that a familiar Reed–Solomon
   convention matches the benchmark encoding.
3. For small instances, check that the candidate preserves the input syndrome,
   restores all designated workspace to zero, and produces the specified
   phase for every in-scope basis input. Use an implementation independent
   from the circuit builder where feasible.
4. Add reversibility/involution or inverse-composition checks only where
   implied by the verified operation contract; do not infer them from the word
   “reversible.”
5. Check gate legality, register identity/order, and decomposition using the
   official contract or verifier fixtures when available.
6. Validate the official adapter independently from unit tests. Keep structural,
   exhaustive-small-domain, randomized, diagnostic, and official full-run
   evidence clearly distinguished.
7. Require independent review of correctness evidence before optimization
   evaluation. Any full benchmark execution remains separately gated by
   explicit approval of the exact command and prerequisites.

No correctness test was run in P001 because no DQI candidate or DQI test suite
exists in the active branch.

## 10. Resource evaluation strategy

After official resource definitions are available, report at minimum circuit
qubits including required workspace, gate counts by verified instruction
category, depth if the official toolchain measures it, and all cleanup costs.
For DQI specifically, the repository’s stated `Q`, `T`, confidence-bound, and
score definitions must first be reconciled with the official verifier/scorer.
Record both raw counts and calculated score inputs, exact tool/version,
configuration, and artifact digest. Separate analytical estimates from
measured results and from official acceptance.

Do not claim savings based on a classical operation count, an unverified score
formula, or a candidate whose qubit and cleanup costs are omitted. No resource
estimate or benchmark score was computed in P001.

## 11. Risks and limitations

- Governance does not currently record Sonjoy’s accepted DQI scope.
- The baseline approval request remains pending; executing the full workload
  would violate the documented gate.
- Optimization is explicitly unauthorized.
- There is a material mismatch between one repository snapshot’s detailed
  verifier API reference and a later readiness audit stating the official
  executable contract and fixtures are unavailable.
- Primary sources, official verifier code, fixtures, and sample circuit were
  absent from the inspected available refs, so technical parameters and
  recorded hashes could not be independently checked.
- Register, field, bit-order, syndrome, seed, and phase details remain
  insufficient to implement a correct decoder safely.
- There is no active-branch Python package, test framework configuration, or
  dependency manifest on which to base implementation choices.
- The proposal is limited by the refs available locally; it does not assert
  that no additional authoritative material exists elsewhere.

## 12. Next-phase implementation plan

1. Obtain a recorded ownership/scope decision for Sonjoy and confirmation from
   the applicable project lead; otherwise do not treat Sonjoy as the DQI owner.
2. Obtain and preserve authorized, immutable primary specification, official
   verifier/scorer release, sample/fixture artifacts, license/runtime
   requirements, and checksums. Reconcile the conflicting repository
   descriptions before using any API or parameter.
3. Record an explicit baseline execution decision. Do not execute the
   102,400-shot run until the exact command, resources, environment, and
   prerequisites have explicit approval.
4. Establish and review the DQI contract and minimal test plan before selecting
   algorithm or package structure.
5. Only under a separate implementation directive, create the approved
   candidate path and implement the smallest justified reversible components.
6. Validate small cases and invariants independently, then resource-account
   against verified definitions.
7. Seek separate optimization authorization only after required baseline
   governance and review criteria are met.

P001 stops here. It does not begin P002 or implement a decoder.

## 13. P001 acceptance checklist

- [x] Inspected the active branch, HEAD, tracked tree, worktree status, and
  available DQI-related refs without switching branches.
- [x] Distinguished INVSQRT cache files from DQI assets; preserved them.
- [x] Reviewed available DQI, ownership, approval, baseline, verifier, and
  compiler-readiness records.
- [x] Reported developer ownership, baseline approval, and optimization status
  without inferring authorization.
- [x] Separated repository-document claims from requirements verified against
  primary executable sources.
- [x] Proposed conditional module boundaries and directory structure without
  creating source code or a decoder algorithm.
- [x] Recorded correctness, verification, resource evaluation, risks, and
  next-phase gates.
- [x] Did not run the official verifier, a diagnostic, or the 102,400-shot
  workload.
- [x] Did not modify verifier code, competition artifacts, raw evidence, or
  dependencies; did not stage, commit, or push.
- [x] Created this report only; no existing document was overwritten.
