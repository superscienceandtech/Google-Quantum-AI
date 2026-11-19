# INVSQRT Algorithm and Optimization Strategy

> **RESEARCH SPECIFICATION**
>
> **NOT AN IMPLEMENTED OPTIMIZATION**
>
> **NOT AN OFFICIAL VERIFICATION RESULT**

## 1. Executive summary

The INVSQRT benchmark asks a 22-qubit input register to acquire the diagonal
phase \(e^{2\pi i\beta/\sqrt{x}}\) for each valid integer input
\(x\in[1,3{,}133{,}452]\), while restoring the input and cleaning every
unnamed work qubit. The benchmark instance uses \(n_p=10\), \(\beta=1\), and
requires 64 verifier shots for each input, with zero failed shots.

The companion paper describes its reference method: normalize by removing
leading zero pairs, obtain an initial inverse-square-root estimate from a
piecewise cubic approximation, apply one Newton–Raphson correction, apply the
resulting phase, and uncompute. The paper reports a reference-circuit resource
point and worst-case relative error. Those are literature-reported values,
not a measurement made in this checkout.

The mathematical problem and a paper-level reference algorithm can therefore
be specified. The official verifier's exact phase-comparison code, metric
implementation, reference circuit source, sample circuit, and Kickmix runtime
are not present in the current branch or the inspected remote-tracking trees.
Consequently, exact fixed-point comparison semantics, circuit loading,
resource-counter behavior, and candidate verification remain blocked. No
optimization has been implemented or measured.

## 2. Scope and non-goals

This is a source-grounded research and implementation specification only. It
does not add an algorithm, circuit, approximation coefficients, resource
estimates, verifier adapter, or benchmark execution. P003's
`OFFICIAL_INVSQRT_SPEC` remains the package contract; this document does not
replace it or alter benchmark requirements.

The existing P002–P005 package supplies generic candidate, score, search,
execution, verifier-boundary, and artifact-readiness interfaces. Those
interfaces are infrastructure, not evidence that an INVSQRT circuit or
production backend exists.

## 3. Source authority and evidence classification

The source hierarchy stated in the repository's requirements matrix is:
official Kaggle metric code; competition verifier and data; companion paper;
competition rules/API; then repository documentation. The first two source
artifacts are not available in the inspected checkout or remote-tracking trees.
The companion paper was directly inspected at arXiv v2. Repository documents
were inspected on `origin/main`; their claims about absent primary code are
identified as repository documentation, not independently verified source
behavior.

Evidence labels used below:

- **OFFICIAL_VERIFIED** — directly checked against official metric or verifier
  implementation/output available as source evidence.
- **PAPER_SUPPORTED** — stated in, or derived from, the companion paper.
- **REPOSITORY_DOCUMENTED** — asserted in repository documents; the cited
  primary artifact is not available here.
- **MATHEMATICALLY_DERIVED** — follows from the stated mathematical model under
  the assumptions written alongside it.
- **RESEARCH_HYPOTHESIS** — plausible optimization direction, not established
  as correct or beneficial.
- **UNKNOWN** — accessible sources do not settle the claim.
- **BLOCKED** — verification or implementation requires unavailable evidence
  or tooling.

No behavior of the official metric or verifier is labelled
`OFFICIAL_VERIFIED` in this specification: the primary source code is absent.
The repository matrix calls several requirements “VERIFIED,” but that label is
the matrix's own source classification.

## 4. Mathematical problem definition

Let \(x\) be the unsigned integer represented on the named input register, and
let \(\beta\) be the phase parameter. The target operation is the diagonal
unitary

\[
U_\beta\lvert x\rangle\lvert 0\rangle_W
= e^{2\pi i\beta/\sqrt{x}}\lvert x\rangle\lvert 0\rangle_W,
\]

for every valid input \(x\). \(W\) denotes all unnamed scratch/work qubits.
The benchmark subroutine takes the squared-distance integer \(w\) directly;
forming \(w\) from coordinate differences is upstream of the benchmark
subroutine and is not part of this input circuit.

For the official instance, the paper gives

\[
n_p=10,\qquad \beta=1,\qquad
\operatorname{width}(x)=2n_p+2=22,
\]

\[
1\leq x\leq 3(2^{n_p}-2)^2=3{,}133{,}452.
\]

The stated range follows from the paper's benchmark model and its
antisymmetrized-input assumption. The P003 contract stores the same constants.
The number of tested integer values is \(3{,}133{,}452\); at 64 shots per
value, the required workload is \(200{,}540{,}928\) shots.

The source specifies the integer value and register width, but the
bit-to-wire ordering/endianness was not found. The circuit must expose exactly
one named quantum register `"x"` with 22 distinct qubits. All other qubits are
unnamed scratch. The `"x"` value must be restored, and every scratch qubit must
be returned to \(\lvert0\rangle\) on each tested shot.

The operation is diagonal in the computational basis: it must not change
\(x\), but it must apply the correct phase relative to the other basis
components. For \(x=1,\beta=1\), the stated phase is one full turn and the
unitary action is the identity on that basis state. Whether the verifier
allows an arbitrary circuit-wide global phase offset is **UNKNOWN**; the
accessible descriptions specify tracked phase comparison but do not expose the
comparison implementation.

## 5. Target phase function and verifier comparison

The phase in turns before reduction modulo one is

\[
\theta_\beta(x)=\frac{\beta}{\sqrt{x}}.
\]

The target amplitude is \(e^{2\pi i\theta_\beta(x)}\), so radians are
\(2\pi\theta_\beta(x)\). The paper and the repository matrix describe the
allowed phase error in turns as

\[
\operatorname{tol}(x)=2^{-24}\frac{\beta}{\sqrt{x}}.
\]

For positive \(\beta\), this is \(2^{-24}\) times the unwrapped target phase
in turns. This is a mathematical reading of the stated formula; it is not a
replacement for the verifier's fixed-point comparator, especially at phase
wrap boundaries.

The paper describes tracking phase in 64-bit fixed-point units of
\(2^{-64}\) turns and computing the integer target from

\[
\left\lfloor\frac{2^{65}\beta}{\sqrt{x}}\right\rfloor
=
\operatorname{isqrt}\!\left(
\left\lfloor\frac{2^{130}\beta^2}{x}\right\rfloor
\right).
\]

The equality follows by squaring the nonnegative scaled target and taking the
integer square root. The repository matrix reports this target encoding and
that every shot must pass (`k = 0`). However, the actual verifier is absent, so
the exact unsigned wraparound, distance calculation, tie/rounding behavior,
and acceptance inequality cannot be confirmed here. The exact relationship
between the 65-bit target integer and the 64-bit phase accumulator must be
checked against the verifier before implementing a comparator.

The described verification enumerates every valid \(x\) and repeats the
simulation 64 times per value to sample measurement/reset outcomes. It is not
evidence that a randomly sampled subset of \(x\) is accepted, nor does the
zero-failure requirement supply an internal arithmetic error budget. The paper
describes PRNG seeding from the canonical circuit serialization and a
competition salt; precise implementation details remain source-dependent.

## 6. Official benchmark contract

The following consolidates traceable claims; P003 remains the canonical
machine-readable contract.

| Requirement | Finding | Evidence class and source | Confidence | Implementation consequence |
|---|---|---|---:|---|
| Function and input domain | \(e^{2\pi i\beta/\sqrt{x}}\), \(x=1\ldots3{,}133{,}452\) | PAPER_SUPPORTED, [R1] §III.1.2–III.1.3; also REPOSITORY_DOCUMENTED, [R2] I-01 | High | Implement only against the integer domain and phase definition; preserve exact \(x\). |
| Input register | One named `"x"` register, 22 distinct qubits | PAPER_SUPPORTED, [R1] §III.1.3; REPOSITORY_DOCUMENTED, [R2] I-02 and [R3] contract section | High for width/name; UNKNOWN for endianness | Confirm bit ordering from verifier/parser before construction. |
| Work-qubit cleanup | All unnamed scratch returns to \(\lvert0\rangle\) per shot | PAPER_SUPPORTED, [R1] §III.1.3; [R2] I-03 | High | Every compute, measurement-uncompute, and reuse path must prove cleanup. |
| Parameters | \(n_p=10,\beta=1\) | PAPER_SUPPORTED, [R1] §III.1.3; [R2] I-04 | High | Treat as fixed benchmark inputs, not search parameters. |
| Shots | 64 per valid \(x\); 200,540,928 total; all pass | PAPER_SUPPORTED, [R1] §III.1.3; [R2] I-06 | High | No measured or estimated partial run establishes acceptance. |
| Tolerance | \(2^{-24}\beta/\sqrt{x}\) turns | PAPER_SUPPORTED, [R1] §III.1.3; [R2] I-05 | High for stated tolerance; BLOCKED for code-level comparison | Implement no substitute comparator until verifier behavior is available. |
| \(k=0\) | Every verifier shot must pass | REPOSITORY_DOCUMENTED, [R2] I-06 | High as paper/matrix requirement; not rechecked against metric source | Test every requested input/shot in an authorized full run. |
| Input restoration | \(x\) is unchanged | PAPER_SUPPORTED, [R1] §III.1.3; [R3] contract section | High | Check output bitstring for every test trajectory. |
| Global phase convention | Verifier comparison is described as tracked phase | REPOSITORY_DOCUMENTED, [R3] contract/rejection section | Low for exact semantics | Do not assume a global offset is ignored. |

## 7. Reference algorithm investigation

### 7.1 What is identified

The companion paper identifies and describes its reference implementation in
§III.1.2 and gives the verification contract in §III.1.3. Its principal stages
are:

1. **Normalize.** Count leading zero *pairs* in the input \(w\), store the
   count \(s\) in unary work bits, and form
   \(w_{\mathrm{norm}}=w\,2^{2s}\in[1,4)\).
2. **Initial approximation.** Use a piecewise cubic approximation to
   \(1/\sqrt{w_{\mathrm{norm}}}\), split over \([1,3/2]\) and \([3/2,2]\);
   rescale the polynomial coefficients to cover the \([2,4)\) part of the
   normalized range. The paper specifies the coefficient sets in
   Eqs. (17)–(24) and points to Appendix B.1/B.3 for scaling and QROM/fixed-point
   details.
3. **Correction.** Apply one inverse-square-root Newton–Raphson step
   \(y\leftarrow \tfrac12 y(3-wy^2)\). With the paper's normalization,
   \(y_{\mathrm{init}}=2^s y_0\) and
   \(y_1=\tfrac12(2^s y_0)(3-w_{\mathrm{norm}}y_0^2)\). The paper computes
   \(p=\tfrac12y_0(3-w_{\mathrm{norm}}y_0^2)\) before the shift
   \(y_1=p\,2^s\), noting this keeps the final multiplier width independent
   of \(n_p\) in its construction.
4. **Phase and uncompute.** Apply the phase from the bits of the corrected
   fixed-point value using `Z_POW`, then reverse the computation to restore
   \(x\) and clean work qubits.

The paper describes this as a fixed-point implementation; it is not safe to
reconstruct the circuit from real-arithmetic equations alone. Bit widths,
coefficient encoding, truncation/rounding, branch boundaries, and exact
uncomputation must be recovered from the paper's detailed appendix and the
actual reference source before implementation. This document intentionally
does not copy or invent those circuit-level details.

### 7.2 Identification status and limitations

The algorithm is **PAPER_SUPPORTED** as the paper's reference method. The
repository names `external/verifiers/invsqrt/nr_reference_circuit.py` and an
official `.kmb` sample, but neither file exists in the inspected checkout or
remote-tracking trees. Therefore, whether those exact competition artifacts
implement the paper's described circuit without deviations is **BLOCKED**.
The paper's method is not asserted here to be the only correct algorithm or a
proven best implementation.

## 8. Approximation and error analysis

The paper states a 24-bit relative-error requirement for the inverse-square
root, relates it to the phase tolerance, and reports that one Newton–Raphson
step suffices for its initial approximation in double precision. It reports
the reference circuit's worst-case relative error as
\(2.84\times10^{-8}\) (\(2^{-25.07}\)) at \(x=2{,}588{,}411\). These are
paper-reported facts, not values recomputed in this repository.

For exact real arithmetic, write an iterate as
\(y=(1/\sqrt{x})(1+\delta)\). Substituting it into
\(y'=\tfrac12y(3-xy^2)\) gives the derived error relation

\[
\delta'=-\frac12\delta^2(3+\delta).
\]

This explains the quadratic suppression for a sufficiently accurate initial
guess in the real-arithmetic model. It does **not** bound the reference circuit:
fixed-point multiplication, coefficient quantization, truncation, rounding,
and phase synthesis add errors not represented by this relation.

The available material does not supply a complete, independently checkable
error budget allocating the final tolerance among:

- polynomial approximation and QROM coefficient encoding;
- multiplication truncation/rounding and Newton-step arithmetic;
- phase extraction/rotation synthesis; and
- fixed-point accumulator/comparator quantization.

The paper describes pricing finer rotations from the remaining phase-error
margin, but the implementation must reproduce the verifier's exact calculation
and angle units. No intermediate precision, guard-bit count, truncation policy,
or safe per-stage error allocation is specified by this document. Those values
must not be guessed.

## 9. Circuit resource and score analysis

Repository documentation attributes the official INVSQRT score to

\[
Q=\texttt{circuit.num\_qubits},\qquad
C=\text{Toffoli count}+\frac{\text{T count}}{4},\qquad
S=Q\,C,
\]

where the verifier reports per-shot resource costs and `t_count` includes base
T gates and priced fallback contributions for finer rotations. The API/score documents report Clifford
`Z_POW` as free, a T angle as one T, and finer rotations priced by
\(0.56\log_2(1/\epsilon)+5.3\) T. These cost conventions are
**REPOSITORY_DOCUMENTED** here because the cited verifier/metric implementation
is absent. The existing P002 `calculate_score` is the package implementation
reference; no second scorer is introduced.

An exact comparison between two candidate resource pairs is

\[
S'<S\quad\Longleftrightarrow\quad Q'C'<QC.
\]

Thus a gate-cost decrease alone is insufficient if total qubits increase. The
official score has no documented depth or runtime term. Depth, operation
counts, compilation time, and simulator runtime may be tracked as secondary
engineering metrics, not substituted for \(Q C\).

Repository literature/evidence reports a reference point of \(Q=260\),
7,735 Toffolis, 11 T gates, 37 `Z_POW` rotations, and score approximately
\(2.08\times10^6\). The repository's historical raw-evidence documents report
two full verifier PASS runs with the same score and workload. They also
explicitly keep strict baseline status **NOT REPRODUCED** because execution
timestamps and contemporaneous environment/commit binding are missing. These
reports are contextual evidence only; this task did not inspect the raw files
or rerun the verifier.

## 10. Optimization opportunity analysis

All opportunities below are unmeasured. Expected effects are qualitative
hypotheses, not resource claims.

| Area | Mathematical/circuit rationale | Possible resource effect and trade-off | Correctness and precision obligations | Required evidence/capability | Readiness |
|---|---|---|---|---|---|
| Approximation range and degree | The paper explicitly suggests comparing a simpler polynomial over a larger interval with the piecewise cubic on a normalized range. | Could reduce QROM/selection or polynomial-evaluation work; a wider range may require higher degree, wider intermediates, or more error margin. | Prove/measure worst-case approximation across all normalized inputs and all fixed-point boundary cases; carry its error into final phase tolerance. | Exact polynomial/coefficients, reversible evaluator, full-domain phase tests, official counter/verifier. | PARTIALLY_READY as a research direction; implementation BLOCKED. |
| Coefficient/QROM representation | The reference obtains coefficients through QROM; the paper identifies coefficient accuracy as a further optimization direction. | Coefficient width or lookup layout might change Toffolis, T count, and ancillas; more precision may increase qubits/gates. | Prove table values, address ranges, signed/fixed-point interpretation, lookup reversibility, and a complete quantization error bound. | Paper Appendix B.3 plus reference source and Kickmix/QROM/resource APIs. | BLOCKED. |
| Arithmetic widths, truncation, and carry handling | The paper uses normalization and truncation to reduce multiplication cost; its shifted-after-multiply organization has a paper-described width benefit. General paper discussion identifies dropping low-weight carries/truncating intermediates as testable approximate-compilation patterns. | May lower arithmetic Toffoli count and temporary width; can increase approximation failures, cleanup cost, or qubits for parallelism. | Derive an end-to-end fixed-point error bound and preserve all inputs/work bits; specifically test normalization thresholds and truncation boundaries. | Exact arithmetic circuit, simulator, traceable resource counts, full verifier. | PARTIALLY_READY as a theory direction; a specific rewrite is BLOCKED. |
| Reversible structure and workspace schedule | The reference uncomputes stages in reverse; Kickmix documentation/paper describes compute/uncompute and temporary-AND primitives. | Gate-count savings or reduced peak \(Q\) are possible; aggressive reuse can increase depth or complicate cleanup. | Establish bijective/reversible behavior or valid measurement-based uncomputation, phase correction, input restoration, and clean workspace on all shots. | Kickmix builder and simulator, structural fixtures, verified liveness/resource counter. | BLOCKED. |
| Phase synthesis | The score prices non-Clifford rotations and uses an error-dependent fallback cost. | Fewer or cheaper rotations may reduce \(C\); a smaller synthesis error allowance may increase T cost. | Preserve target phase under the actual fixed-point comparator; allocate only rigorously derived residual tolerance. | Official phase counter and implementation, synthesis error semantics, verifier. | BLOCKED. |

Register-width reduction is not an independent entitlement: the input width
is fixed by the contract, while any work-qubit reduction must still satisfy
restoration and resource counting. QROM is relevant to the paper's reference
algorithm but alternative lookup layouts are not assumed relevant until their
exact circuit and cost are established.

## 11. Candidate algorithm comparison

Only one reference algorithm is sufficiently identified in the available
evidence: the paper's normalized piecewise-cubic initial approximation plus
one Newton–Raphson correction. Its input, target, high-level approximation
structure, phase application, and uncomputation are described above.

The paper mentions broader-range polynomials and direct input-domain
polynomial approximation as possible research directions, but it does not
specify a complete circuit, fixed-point implementation, verified error bound,
or measured resource pair for those alternatives. They are hypotheses, not
additional established algorithms. A resource/correctness comparison table
between implemented candidates would therefore be fabricated and is omitted.

## 12. Correctness obligations

No obligation below is proven for a candidate circuit by the P002–P005
infrastructure. Metadata validation and test doubles are not mathematical
proofs or official verifier evidence.

| Obligation | Required statement/evidence | Required test | Official-verifier evidence | Current status |
|---|---|---|---|---|
| Domain | Input integer is within \(1\ldots3{,}133{,}452\); define behavior for every value the verifier may supply. | Domain endpoints and values around normalization/branch boundaries; exhaustive valid-domain coverage where feasible. | Full-domain run, all prescribed shots. | Contract PAPER_SUPPORTED; candidate BLOCKED. |
| Encoding | `"x"` is the exact 22-qubit integer register with the official wire ordering. | Encode/decode known integers and boundary patterns. | Verifier/parser accepts register and tests intended values. | Width/name PAPER_SUPPORTED; ordering UNKNOWN. |
| Mathematical phase | For each legal \(x\), output phase equals \(e^{2\pi i\beta/\sqrt{x}}\) under the benchmark convention. | Compare tracked phase against exact target on basis inputs. | Full official pass. | Specification PAPER_SUPPORTED; candidate BLOCKED. |
| Phase tolerance | Actual fixed-point phase comparison satisfies \(\operatorname{tol}(x)\) for every shot. | Reproduce exact comparator, integer target, wrap, and rounding behavior. | Official verifier output with zero failures. | Tolerance PAPER_SUPPORTED; comparator details BLOCKED. |
| Reversible computation | Each arithmetic/QROM stage has the claimed action and can be reversed with its work state accounted for. | Forward/reverse state equality, including arithmetic boundary patterns. | Official structural and full-run checks. | BLOCKED. |
| Input restoration | Output register equals input \(\lvert x\rangle\). | Compare all output bits on basis trajectories. | Verifier's register-restoration check passes. | Requirement PAPER_SUPPORTED; candidate BLOCKED. |
| Scratch cleanup | Every unnamed work qubit is \(\lvert0\rangle\) on every tested shot. | Inspect all work bits after each trajectory and all measurement outcomes. | Verifier's clean-ancilla check passes. | Requirement PAPER_SUPPORTED; candidate BLOCKED. |
| Ancilla lifetime/reuse | Reused qubits are clean before allocation and remain within counted circuit resources. | State/liveness checks at each allocation boundary. | Official `num_qubits` and structural validation. | BLOCKED. |
| Global phase | Any allowed phase offset is consistent with the verifier's tracked-phase comparison. | Add controlled diagnostic circuits only after comparison semantics are known. | Exact verifier behavior. | UNKNOWN. |
| Verifier compatibility | Submission format, instruction set, register contract, seeded simulation, and output satisfy the official verifier. | Parser/structural tests with real artifacts. | Authorized official run, full input domain. | BLOCKED. |
| Score compatibility | \(Q\), Toffoli, T, and rotation-fallback counts match official accounting. | Independently reconcile operation counts and score from the same circuit artifact. | Official score output with artifact/verifier hashes. | Formula REPOSITORY_DOCUMENTED; counter BLOCKED. |

## 13. Research-hypothesis register

No hypothesis has status `VERIFIED`. Status and priority describe proposed
research sequencing, not authorization to implement or run experiments.

| ID / priority | Hypothesis and evidence | Expected impact / negative trade-off | Required implementation and tests | Official verification and falsification | Status |
|---|---|---|---|---|---|
| H-01 / High | A simpler (possibly lower-degree) polynomial over a broader normalized interval may outperform the paper's two-piece cubic. The paper explicitly identifies the simpler-polynomial direction [R1, §III.1.2]. | Potentially less selection/QROM overhead; broader approximation interval may require a higher degree or more coefficient precision. | Derive candidate coefficients and a uniform error bound; implement an explicitly reversible evaluator; test all domain values and interval boundaries. | Compare official \(Q C\) and require all shots pass. Falsify if no candidate meets tolerance or the official score is not lower. | PROPOSED |
| H-02 / High | The reference coefficient encoding/QROM may use more precision or data movement than necessary. The paper identifies coefficient accuracy as an optimization target [R1, §III.1.2, App. B.3]. | Potentially reduce table/address/arithmetic costs; reduced precision can consume phase margin or increase output correction work. | Recover exact fixed-point table semantics; sweep only mathematically justified encodings; prove lookup cleanup and phase error. | Official full-domain zero-failure run and same-verifier resource comparison. Falsify if valid encodings do not reduce \(Q C\). | PROPOSED |
| H-03 / Medium | Precision can be allocated across multiplication intermediates using proven error bounds instead of uniform widths. The paper motivates normalization/truncation [R1, §III.1.2]; no budget is available here. | May shrink arithmetic and ancillas; risk is a rare boundary input or accumulated error exceeding tolerance. | Derive a stage-wise bound, then change one width/truncation at a time; test normalization and rounding boundaries exhaustively. | Official full-domain run and resource counter. Falsify on any failed shot, invalid cleanup, or non-improving score. | MATHEMATICAL_REVIEW_REQUIRED |
| H-04 / Medium | Reversible arithmetic/uncomputation and workspace scheduling may reduce peak qubits or Toffoli cost without changing the target phase. The reference explicitly reverses its stages [R1, §III.1.2]. | Possible lower \(Q\) or \(C\); more sequential scheduling can increase depth/runtime, and alternate uncomputation may require phase corrections. | Implement a single reviewed transformation with basis-state phase, restoration, and cleanup tests. | Official resource and full verifier evidence. Falsify if phase/cleanup changes or \(Q'C'\ge QC\). | EVIDENCE_PENDING |

## 14. Implementation-readiness matrix

Readiness reflects evidence and working capabilities, not the existence of an
interface alone.

| Capability | Status | Evidence and blocker |
|---|---|---|
| Mathematical specification | PARTIALLY_READY | Paper target, range, parameters, and tolerance are available; exact fixed-point comparison/wrap semantics and bit ordering are not. |
| Reference algorithm definition | PARTIALLY_READY | High-level method and equations are in the paper; exact fixed-point/QROM circuit details and correspondence to competition artifacts need confirmation. |
| Reference circuit/artifact | BLOCKED | P005 manifest found no local verifier, reference source, or sample `.kmb`; inspected remote branch trees have no such files. |
| Quantum SDK/runtime | BLOCKED | The paper and dependency report identify Kickmix; P005's inspected Python environments cannot import it, and version/API are not locally confirmed. |
| Circuit backend | BLOCKED | Only the unavailable backend boundary exists; no production builder/loader is implemented. |
| Resource counter | BLOCKED | Repository docs report verifier metrics and score fields; the underlying verifier/resource implementation is absent. |
| Official verifier | BLOCKED | API documentation exists on `origin/main`; verifier source is missing locally, and P005 did not execute it. |
| Test fixtures | PARTIALLY_READY | P002–P005 have contract tests and explicit test doubles; no official circuit fixture or real SDK integration fixture is available. |
| Reproducibility evidence | PARTIALLY_READY | `origin/main` documents two historical full INVSQRT PASS runs; strict baseline status remains NOT REPRODUCED due missing provenance binding. |

## 15. Missing evidence and blockers

1. **Primary verifier/metric source:** recover the authorized official verifier
   and Kaggle metric implementation, including exact phase-difference,
   unsigned arithmetic, equality, wraparound, and rounding semantics.
2. **Official reference artifacts:** obtain the reference-circuit source,
   sample `.kmb`/`.kmx`, and checksums/provenance from an authorized source.
   The existence of paths in repository docs does not mean files are present.
3. **Kickmix runtime/API:** obtain the supported runtime and version; confirm
   circuit loading/building, simulation, serialization, instruction counting,
   workspace accounting, and rotation-cost APIs from real source/API evidence.
4. **Fixed-point implementation details:** confirm polynomial coefficient
   encoding, lookup table, bit widths, truncation and rounding at every
   intermediate, multiplication semantics, and reverse/uncompute sequence.
5. **Error budget:** derive and independently check a stage-wise bound from
   fixed-point arithmetic and phase synthesis to the final verifier tolerance.
6. **Baseline provenance:** close the documented gaps in execution timestamps
   and contemporaneous commit/environment binding before calling the baseline
   strictly reproduced.
7. **Authorization:** the INVSQRT workstream document gates optimization on
   strict baseline requirements and explicit project-lead approval. Neither
   this specification nor the historical PASS reports waive that gate.

## 16. Prioritized future implementation roadmap

1. **Evidence closure:** obtain authorized primary verifier/metric files and
   circuit artifacts; hash them; document exact revision and SDK version.
2. **Contract reconciliation:** validate P003 constants against the recovered
   source and record discrepancies without silently changing the contract.
   Resolve phase comparison, register ordering, and global-phase questions.
3. **Baseline closure:** bind a full baseline run to candidate/verifier hashes,
   commit, environment, exact command, execution timestamps, complete output,
   and approval. Preserve existing baseline records read-only.
4. **Backend and fixtures:** implement only the verified load/build/measure
   path; add deterministic basis-state tests for phase, input restoration,
   and scratch cleanup before any optimization.
5. **Select one hypothesis:** after the gate is satisfied and authorized, start
   with one narrow change from H-01 or H-02, with a pre-registered error proof,
   score expectation, and falsification condition.
6. **Evaluate:** use the official resource counter and verifier, archive full
   provenance, and compare the official \(Q C\) objective. Do not rank
   estimated metrics as official improvements.

No P006 experiment is authorized or executed.

## 17. References and source locations

- **[R1] Companion paper:** *Leveraging verifiable structure in quantum
  circuits to find more efficient compilations with agentic AI*,
  arXiv:2610.23832v2. [Abstract and paper](https://arxiv.org/abs/2610.23832v2);
  HTML version: https://arxiv.org/html/2610.23832v2. Relevant locations:
  §II.3 (basis-state fuzz testing and error interpretation), §III.1.2
  (reference implementation and Eqs. 13–31), §III.1.3 (benchmark contract,
  phase tolerance, score), Appendix B.1/B.3 (polynomial rescaling and
  fixed-point/QROM details).
- **[R2]** `origin/main:docs/COMPETITION_REQUIREMENTS_MATRIX.md`, authority
  order at lines 4–9; INVSQRT rows I-01–I-09 at lines 47–59; verifier
  invocation at lines 122–129. Repository synopsis, not primary metric code.
- **[R3]** `origin/main:docs/OFFICIAL_VERIFIER_API_REFERENCE.md`, INVSQRT
  sections at lines 3–36. It points to the absent
  `external/verifiers/invsqrt/verify_submission_invsqrt.py` and reports its
  documented API/source line ranges.
- **[R4]** `origin/main:docs/SCORE_MODEL_VERIFICATION.md`, INVSQRT at lines
  5–16; reports verifier source lines 317–334 and 148–149, plus historic
  output. The verifier and raw output are not in the current checkout.
- **[R5]** `origin/main:docs/TEAM/BENCHMARKS/INVSQRT.md`, status and objective
  at lines 3–10, evidence at lines 15–37, acceptance and gates at lines 67–91.
- **[R6]** `origin/main:docs/BASELINE_EVIDENCE_RECONCILIATION.md`, INVSQRT
  evidence and missing provenance at lines 26–62.
- **[R7]** `origin/main:docs/BASELINE_STATUS_MATRIX.md`, INVSQRT status and
  historical run summary at lines 5, 15–16, and 23.
- **[R8]** `origin/main:docs/DEPENDENCY_COMPATIBILITY_REPORT.md`, verifier
  import/runtime claims at lines 3–37. The report describes a supplied
  Kickmix library, not the local environment used for P005.
- **[R9]** Local implementation cross-checks: `src/invsqrt_opt/contract.py`
  lines 134–155 (P003 constants and descriptions), lines 257–317 (metadata
  checks); `src/invsqrt_opt/score.py` lines 16–48 (P002 score calculation);
  `src/invsqrt_opt/artifacts.py` lines 128–214 and 358–451 (P005 manifest
  and unavailable adapter). These establish package behavior only, not
  official benchmark behavior.

The primary findings document referenced by the matrix,
`docs/research/PRIMARY_SOURCE_FINDINGS.md`, is absent from `origin/main`.
Relevant remote-tracking research branches contain only their README files;
they add no algorithm notes or primary implementation evidence.

## 18. Status

**RESEARCH SPECIFICATION — complete for the accessible paper and repository
documentation.** The paper's reference algorithm is identified at a
high-level, and candidate directions are explicitly hypotheses.

**NOT AN IMPLEMENTED OPTIMIZATION.** No algorithm, circuit, source code, or
optimization experiment was added or run.

**NOT AN OFFICIAL VERIFICATION RESULT.** No official artifact or verifier was
executed. The implementation and verifier-specific questions remain blocked as
listed above.
