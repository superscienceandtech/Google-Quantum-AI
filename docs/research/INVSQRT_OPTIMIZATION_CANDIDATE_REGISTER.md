# INVSQRT Optimization Candidate Register (P010)

> **Research and candidate design only.**
>
> No candidate below is an implemented optimization, verified circuit, or
> measured score improvement. Do not change the P007–P009 baseline or start a
> candidate experiment until its listed evidence gates are met.

## 1. Executive research summary

P010 inspected the fixed-point arithmetic and experiment infrastructure and
turned plausible optimization directions into isolated, falsifiable candidate
specifications. The official workstream objective is to minimize

\[
S=Q\,C,\qquad
Q=\texttt{circuit.num\_qubits},\qquad
C=\text{Toffoli count}+\frac{\text{T count}}4,
\]

subject to the full input, phase, restoration, cleanup, and submission
contract. The formula is the competition objective specified for this
workstream and documented in P006 and `src/invsqrt_opt/score.py`; the official
metric source itself is not present here, so its exact accounting rules remain
`REPOSITORY_VERIFIED`, not independently `OFFICIAL_VERIFIED`.

The strongest safe first numerical study is **P010-C01**, an exhaustive
intermediate-range and truncation-margin audit of the existing fixed-point
baseline. It could identify whether a narrower implementation merits study
without changing the arithmetic or asserting that a narrower register is
equivalent. The first future circuit-level candidate is **P010-C06**,
reversible workspace scheduling and uncomputation, because it can preserve
the computed function while potentially affecting both \(Q\) and \(C\).
Neither candidate is currently circuit-executable.

Top blockers are the missing independently authenticated competition source
archive, Kickmix runtime/API, local reference circuit/sample artifact,
official metric/verifier execution, and a complete stage-to-phase error
budget. As a result, this report gives qualitative potential impact only.
There are no measured P010 resource or score improvements.

## 2. Repository baseline and inspected evidence

Initial P010 inspection found:

| Item | Observed |
|---|---|
| Root | `D:\PROJECT\Quantum_AI\Google-Quantum-AI` |
| Branch | `feat/invsqrt-optimization` |
| HEAD | `5391b2e7123484efacffc0588f5e761e67b5cb55` |
| Worktree | README modified; P002–P009 documents, source, tests, and `pyproject.toml` untracked |
| Ignored data | `.pytest_cache/` was present and ignored; preserved |
| Baseline tests | P009 had recorded 299 passing; P010 makes no code changes |

Inspected the requested implementation modules, tests, README, `pyproject.toml`,
and the P006–P009 research reports. In particular:

- `fixed_point.py` implements the default fixed-point reference arithmetic.
- `fixed_point_differential.py` binds the P009 comparison to the mirror's
  reference/verifier hashes, but not official Kaggle authentication.
- `reference_math.py` and `numerical_validation.py` implement P007's distinct
  real-arithmetic Decimal model and exhaustive error check.
- `score.py`, `models.py`, and `comparison.py` implement local metric storage,
  score calculation, provenance gates, and ranking.
- `search_space.py`, `configurations.py`, and `strategies.py` support finite
  typed parameter spaces and seeded grid/random configuration generation.
- `backend.py`, `execution.py`, `runner.py`, `verifier.py`, and `artifacts.py`
  define experiment interfaces, unavailable fail-closed implementations,
  result persistence, and artifact readiness. These abstractions do not supply
  a production circuit builder, resource counter, or official verifier.
- Existing tests are contract, artifact-intake, search/execution, P007, and
  P008/P009 classical-model tests; there are no real Kickmix integration
  fixtures.

The P008/P009 evidence is preserved as documented:

- P007: 3,133,452 inputs evaluated at 50-digit Decimal precision; maximum
  relative error \(5.1643545984960819089670834272040066197411095618635
  \times10^{-9}\) at \(x=1{,}123{,}799\).
- P009: two full-domain comparisons against the hash-pinned mirror's pure
  Python model, each with 3,133,452 inputs, zero mismatches, and zero maximum
  integer output difference.
- P009 source provenance remains `PARTIALLY_VERIFIED`; mirror origin is not
  independently authenticated. Neither result proves quantum circuit
  equivalence.

No P010 implementation or experiment was executed. `P010` does not modify
P007, P008, or P009 behavior or results.

## 3. Evidence and readiness vocabulary

Evidence labels follow the requested classifications:

- `OFFICIAL_VERIFIED`: directly authenticated official competition source or
  official execution evidence. None of the candidate benefits has this label.
- `PAPER_SUPPORTED`: directly stated or motivated in the cited paper.
- `REPOSITORY_VERIFIED`: directly checked local code, tests, or documentation.
- `MATHEMATICALLY_DERIVED`: follows from the stated equation under explicit
  assumptions.
- `EMPIRICAL_HYPOTHESIS`: requires a numerical result not yet measured.
- `THEORETICAL_CANDIDATE`: plausible circuit/computation direction without an
  implementation or measurement.
- `UNKNOWN`: inspected evidence does not settle it.
- `BLOCKED`: required source/runtime/verification capability is absent.

Readiness labels:

- `READY_FOR_NUMERICAL_EXPERIMENT`: can be evaluated against the current
  classical model without claiming circuit implementation or acceptance.
- `REQUIRES_MATHEMATICAL_PROOF`: exact equivalence or an adequate error bound
  has not been established.
- `REQUIRES_FIXED_POINT_EQUIVALENCE`: must preserve or explicitly revalidate
  finite-width output and phase behavior.
- `REQUIRES_CIRCUIT_BACKEND`: needs a real reversible circuit builder,
  simulator, and resource counter.
- `REQUIRES_OFFICIAL_VERIFIER`: cannot be accepted based only on the local
  model.
- `BLOCKED`: a necessary primary source/capability is unavailable.
- `REJECTED`: not advanced because the current evidence does not justify it.

`READY_FOR_PROTOTYPE` is not assigned to a candidate: no candidate has all the
necessary mathematical and circuit assumptions established.

## 4. Authoritative objective and trade-offs

The objective supplied for this workstream is

\[
S=Q\left(T_{\mathrm{off}}+\frac{T_{\mathrm{total}}}{4}\right),
\]

where \(Q\) is total circuit qubits, \(T_{\mathrm{off}}\) is Toffoli count, and
\(T_{\mathrm{total}}\) is the T-equivalent count under official accounting.
The local `ResourceMetrics` stores qubits, `toffoli_like_count`, base T count,
and rotation-fallback T contribution; `calculate_score` forms
\(C=T_{\mathrm{off}}+T_{\mathrm{total}}/4\) and multiplies by \(Q\).
`calculate_official_score` requires `OFFICIAL` provenance and measured metrics.

Only the measured official pair \((Q,C)\) from the official counter can
establish score improvement. For a candidate:

\[
S'<S\iff Q'C'<QC.
\]

Thus a gate-cost decrease is not enough if qubit count rises. Depth, number of
rotations, compilation time, and simulator runtime can inform engineering
decisions but are not added as score terms without primary metric evidence.
Do not compare estimates as official scores.

The primary metric/verifier source is absent locally. P006 reports the score
formula, rotation pricing, and a historical reference resource point as
repository/literature evidence, not fresh measurements made by P010. The
historical baseline is still not strictly reproduced with contemporaneous
artifact hashes, commit, and environment binding.

## 5. Validated mathematical and fixed-point baseline

For the official instance, the current contract and paper-supported
description use \(n_p=10,\ \beta=1\), 22-bit input, and
\(1\leq x\leq3{,}133{,}452\). The target phase is
\(e^{2\pi i\beta/\sqrt{x}}\); the input must be restored, all scratch cleaned,
and the applicable phase tolerance satisfied on all required tests.
The exact verifier's phase wrap, integer comparison, shot behavior, and
submission parser remain unavailable for independent source verification.

The fixed-point source model uses defaults:

| Component | Baseline |
|---|---:|
| \(\Delta\) terms | `delta_bits=14` |
| Coefficients and Horner registers | `coef_bits=17` |
| Square | `square_bits=28` |
| Mantissa product / correction precision | `product_bits=28` |
| Newton output product | `result_bits=29` |
| Phase numerator width at \(n_p=10\) | `29 + 10 + 1 = 40` |

The mirror's model implements a leading-zero-pair normalization, four
coefficient intervals, three Horner subtractions, a bitwise square
construction, row-aligned products that discard low columns before row
addition, Newton correction \(3-z\), and denormalization by a shift. Coefficient
conversion follows the source's binary64 values and Python `round`. The local
P008 emulator matches this model on the complete valid domain in P009; this
does not validate gate-by-gate behavior.

For the real-arithmetic Newton map

\[
y'=\frac12y(3-xy^2),
\]

let \(y=x^{-1/2}(1+\delta)\). Direct substitution gives

\[
\delta'=-\frac12\delta^2(3+\delta).
\]

This supports quadratic error reduction when the starting estimate is
sufficiently accurate in real arithmetic. It does not bound fixed-point
coefficient quantization, row truncation, finite-width wrap, phase synthesis,
or accumulated stage error. P007's Decimal result is a different numerical
model and must not be used as a bit-exact emulator oracle.

## 6. Research methodology and category analysis

For any candidate, compare against the unchanged default implementation and
require:

1. A precise transform and scope (which registers/operations change).
2. Exact integer equivalence, or a separately derived whole-domain error
   bound that includes every truncation and the official phase comparator.
3. Boundary checks at powers of two, normalization pair transitions, all
   polynomial interval boundaries, and domain endpoints.
4. Input restoration, scratch cleanup, and reverse/uncompute evidence.
5. Same-artifact resource measurement of \(Q\), Toffoli, T, and rotation
   fallback counts, plus the official verifier.
6. Provenance-bound reproducibility and approval under the existing benchmark
   workstream gate.

### 6.1 Fixed-point arithmetic and widths

Potential opportunities include finding exact register value ranges, deriving
minimum required widths with sign/carry included, and identifying fixed-zero
partial-product rows or redundant bits. A narrower register is only exact if
every reachable value fits under the actual circuit's modular semantics and
all removed low columns are already discarded identically. A changed
truncation point changes \(z\), then \(3-z\), then \(p\); output equality is
not implied by a small real-valued difference.

The P009 emulator is deliberately restricted to default precision and checks
integer overflow. It does not support candidate width changes. Exact ranges
can first be audited numerically over all benchmark inputs, but that audit
would be a necessary condition—not proof that a narrower reversible circuit
preserves outputs, phase tolerance, or cleanup.

### 6.2 Polynomial evaluation

The baseline computes \(r_1=c_2-T(c_3\Delta)\),
\(r_2=c_1-T(r_1\Delta)\), and \(y_0=c_0-T(r_2\Delta)\), with
source-defined row truncation. Algebraically equivalent reassociation is not
integer-equivalent in general because truncation occurs per partial-product
row before summation. Potential work is limited to exact row/carry analysis,
fixed zero control elimination with domain proof, or reversible selector/QROM
factoring. No new coefficients or alternative fitted polynomial are proposed.

The paper motivates simpler approximations over broader intervals and
coefficient precision as research directions. It does not supply a new
verified set of coefficients or a complete fixed-point error budget for those
alternatives.

### 6.3 Newton correction

The fixed-point pipeline computes \(z=T(MT(y_0^2))\), then a scaled
\(3-z\), then a truncated product with \(y_0\). Fusing or narrowing these
stages might reduce live qubits or arithmetic, but reassociation across
truncation is unsafe without an exact integer proof. Moving the factor \(1/2\)
as a shift may alter discarded columns and output bit alignment. Removing the
correction changes real arithmetic according to the quadratic error relation,
but does not by itself prove phase tolerance for every input or account for
fixed-point error. No correction stage is removed or altered in this plan.

### 6.4 Normalization and region selection

Normalization is \(x_{\rm norm}=x\,2^{2s}\), where \(s\) counts leading-zero
pairs, followed by \(y_1=p\,2^s\). Candidate logic changes must match both
shifts and exact interval endpoints. The emulator's integer `bit_length`
formulation matches the pinned classical model on the domain; this does not
establish a lower-cost circuit than pair-zero tests and controlled rotations.
Region selection affects the coefficient words and \(\Delta\) rows; sharing
address/control logic is a circuit synthesis question. No branch or shift is
currently shown redundant.

### 6.5 Reversible circuit implications

Any reduction must account for forward and reverse arithmetic, temporary-AND
cleanup, measurement-based uncomputation outcomes, phase corrections,
register lifetimes, and peak qubit allocation. Qubit reuse can lower \(Q\)
while increasing depth; parallelism can lower depth while increasing \(Q\).
Neither effect is measurable in the current repository. Local experiment
interfaces and test doubles cannot provide actual Kickmix gate counts or
official resource metrics.

### 6.6 Search-space and experiment framework

The generic framework has typed integer, float, categorical, and fixed
parameters; canonicalized configurations; seeded grid/random generators;
backend and official-verifier protocols; score provenance validation; and
experiment persistence/ranking. It does not have conditional/dependency
constraints between parameters, a domain-specific INVSQRT builder, or the real
resource/verifier implementation. Do not add P010 parameters to production
search spaces until their domains and constraints are justified.

## 7. Optimization candidate register

Potential impact is qualitative and denotes possible score relevance, not
measured benefit. Priority ranks investigation order, not expected percentage.

### P010-C01 — Exhaustive reachable-range and truncation-margin audit

- **Category:** Fixed-point arithmetic / register widths.
- **Baseline:** Default widths and row truncation listed in §5.
- **Proposed transformation:** First compute exact reachable minima/maxima,
  used-bit ranges, row contribution ranges, and distance to each register
  limit across all valid inputs. Only if margins justify it, specify one
  single-register narrowing candidate for later isolated evaluation.
- **Mathematical justification:** For a nonnegative register value \(v\),
  the minimum unsigned width is \(\lceil\log_2(v_{\max}+1)\rceil\). This
  establishes fit for observed values only if the traversal is complete and
  all control paths are represented. Exact narrowing additionally requires
  proving the circuit uses the same range, carry, and wrap semantics.
- **Fixed-point equivalence requirements:** Pinned source and default
  precision; stage-by-stage full-domain integer equality; no wrap/overflow;
  check all boundaries and final phase error if any width changes.
- **Expected potential benefit:** `UNKNOWN` (could affect workspace qubits and
  arithmetic cost).
- **Correctness risk:** High if narrowing changes carry-out, modular behavior,
  or a rarely reached boundary value.
- **Implementation work:** Numerical range report first; no baseline edit.
  Then one separate prototype only after exact bounds and approval.
- **Tests:** Exhaust all valid inputs; assert stage extrema and first/last
  values attaining each extremum; compare unchanged output; boundary tests.
- **Circuit/backend:** Required to establish actual qubit and gate savings.
- **Verification:** Official full-domain verifier and resource counter after
  a candidate circuit exists.
- **Evidence:** `REPOSITORY_VERIFIED` baseline semantics plus
  `MATHEMATICALLY_DERIVED` width formula; proposed benefit
  `EMPIRICAL_HYPOTHESIS`.
- **Readiness:** `READY_FOR_NUMERICAL_EXPERIMENT` for range audit;
  `REQUIRES_FIXED_POINT_EQUIVALENCE` for any width change.
- **Priority:** 1 — safest next numerical study; does not change semantics.

### P010-C02 — Exact zero-row / constant-row multiplier pruning

- **Category:** Fixed-point arithmetic / reversible multiplier.
- **Baseline:** Row products are accumulated by alignment exponent; zero
  controls contribute zero, and coefficients are constant bit words.
- **Proposed transformation:** Omit only circuit rows proven identically zero
  for every valid input/control path, or specialize constant coefficient
  terms where the current circuit actually materializes them.
- **Mathematical justification:** Removing a row with control identically zero
  or operand identically zero preserves the integer sum. Removing a
  data-dependent row is not justified by observing it is zero on sampled
  inputs.
- **Fixed-point equivalence requirements:** Prove zero controls from
  bit-level logic and valid-domain constraints; preserve per-row low-column
  truncation and carry; compare all output integers.
- **Expected potential benefit:** `LOW` to `MEDIUM`, unknown until circuit
  structure and counters are available.
- **Correctness risk:** Medium; an invalid domain assumption or omitted carry
  changes output bits.
- **Implementation work:** Inspect generated row network and domain proof;
  avoid modifying the scalar oracle.
- **Tests:** Static row identity proof, per-stage exhaustive equality, input
  boundaries, reversible cleanup.
- **Circuit/backend:** Required; the scalar model cannot prove synthesized
  gate savings.
- **Verification:** Full official verifier plus same-artifact \(Q C\)
  measurement.
- **Evidence:** Arithmetic identity `MATHEMATICALLY_DERIVED`;
  circuit benefit `THEORETICAL_CANDIDATE`.
- **Readiness:** `REQUIRES_CIRCUIT_BACKEND`.
- **Priority:** 5.

### P010-C03 — Polynomial selector/QROM factoring

- **Category:** Polynomial evaluation / region selection.
- **Baseline:** Four interval cases select four quantized coefficient words;
  Horner then performs three subtractions and truncated row products.
- **Proposed transformation:** Explore a reversible lookup/address network
  that factors shared selector conditions or coefficient-bit structure while
  producing the identical four words and leaving all selector/work bits
  clean.
- **Mathematical justification:** Lookup outputs must equal the baseline
  table exactly for every normalized input; a Boolean factoring is exact only
  if all four half-open interval boundaries are preserved.
- **Fixed-point equivalence requirements:** Exact coefficient table and
  interval choice, identical \(y_0\) bits after each Horner stage, exact
  uncompute.
- **Expected potential benefit:** `UNKNOWN` (possible Toffoli/T or qubit
  change; could also cost more).
- **Correctness risk:** High at interval endpoints and during lookup
  uncomputation.
- **Implementation work:** Circuit-level truth-table factoring and synthesis;
  no new coefficients.
- **Tests:** Exhaustive four-case address map; every transition \(\pm1\);
  lookup/uncompute state tests; whole-domain model and circuit checks.
- **Circuit/backend:** Required for reversible lookup and resources.
- **Verification:** Official full-domain run and official score comparison.
- **Evidence:** Table and cases `REPOSITORY_VERIFIED` against mirror model;
  optimization `THEORETICAL_CANDIDATE`.
- **Readiness:** `REQUIRES_CIRCUIT_BACKEND`.
- **Priority:** 4.

### P010-C04 — Horner row/carry network specialization

- **Category:** Polynomial evaluation / arithmetic widths.
- **Baseline:** Three Horner stages use `T` with each row shifted/truncated
  before accumulation and 17-bit unsigned intermediate registers.
- **Proposed transformation:** Specialize the reversible implementation of
  the existing row/carry network (e.g. constant or fixed-control rows), without
  changing polynomial order, coefficient values, truncation, or 17-bit
  outputs.
- **Mathematical justification:** Only Boolean rewrites proven to compute the
  identical truncated integer sum are in scope. Reassociating products or
  moving truncation is not presumed valid.
- **Fixed-point equivalence requirements:** Exact register-by-register
  equality for all four coefficient cases and every reachable delta pattern.
- **Expected potential benefit:** `UNKNOWN`.
- **Correctness risk:** High if row truncation occurs after rather than before
  summation, or if carries are omitted.
- **Implementation work:** Derive truth/carry structure; prototype one stage
  first, then all three only if exact.
- **Tests:** Exhaustive legal delta patterns; all domain inputs; boundary
  truncation vectors; inverse/uncompute.
- **Circuit/backend:** Required to measure actual network.
- **Verification:** Official verifier and resource counter.
- **Evidence:** Source semantics `REPOSITORY_VERIFIED` from the pinned mirror;
  gate optimization `THEORETICAL_CANDIDATE`.
- **Readiness:** `REQUIRES_FIXED_POINT_EQUIVALENCE`.
- **Priority:** 3.

### P010-C05 — Newton multiply fusion or fixed-point scaling relocation

- **Category:** Newton correction / arithmetic pipeline.
- **Baseline:** \(z=T(MT(y_0^2))\), \(c=3\cdot2^{28}-z\), then
  \(p=T(y_0c)\), followed by \(y_1=p2^s\).
- **Proposed transformation:** Investigate whether a circuit implementation can
  fuse intermediate storage or relocate an exact power-of-two scale while
  preserving each source-defined truncation point.
- **Mathematical justification:** Real-valued multiplication associates, but
  \(T(T(ab)c)\) need not equal \(T(aT(bc))\). Shifting a register changes
  which product columns survive unless a bit-level identity proves otherwise.
- **Fixed-point equivalence requirements:** Exact \(z,c,p,y_1\) integer
  equality across the full domain; preserve widths, carry, and truncation.
- **Expected potential benefit:** `LOW` to `MEDIUM`, unknown.
- **Correctness risk:** High due accumulated error and scale/truncation
  interaction.
- **Implementation work:** First derive fixed-point identity; then implement
  only a separately versioned circuit candidate.
- **Tests:** Stage-by-stage exhaustive comparisons; paper's worst-case input;
  all normalization boundaries; phase error and cleanup.
- **Circuit/backend:** Required.
- **Verification:** Official full-domain run and measured \(Q C\).
- **Evidence:** Baseline expressions `REPOSITORY_VERIFIED`; proposed fusion
  `THEORETICAL_CANDIDATE`.
- **Readiness:** `REQUIRES_MATHEMATICAL_PROOF`.
- **Priority:** 6.

### P010-C06 — Reversible workspace schedule and uncomputation

- **Category:** Reversible circuit structure / workspace.
- **Baseline:** Reference computes stages, applies phase from output bits, and
  reverses computation; work registers and temporary ANDs must be restored.
- **Proposed transformation:** Explore register lifetime scheduling and legal
  clean-ancilla reuse while keeping the exact arithmetic and phase function.
- **Mathematical justification:** Reuse is valid only after the prior
  register's information has been uncomputed or preserved elsewhere; each
  compute/phase/uncompute sequence must implement the same diagonal unitary.
- **Fixed-point equivalence requirements:** Baseline output bits preserved;
  reversible compute and inverse exact; every possible measurement-based
  uncompute outcome accounted for.
- **Expected potential benefit:** `UNKNOWN` for \(Q C\); potentially affects
  both factors and may trade depth/runtime.
- **Correctness risk:** High for residual entanglement, phase correction,
  measurement branches, and dirty ancillas.
- **Implementation work:** Liveness plan, one transformation, state-level
  tests, actual workspace accounting.
- **Tests:** Basis-state phase tests, input restoration, every scratch bit
  clean, repeated shots/measurement branches, depth/resource profiling.
- **Circuit/backend:** Required and currently absent.
- **Verification:** Official verifier and official resource output.
- **Evidence:** Reverse-compute structure `PAPER_SUPPORTED`;
  savings `THEORETICAL_CANDIDATE`.
- **Readiness:** `REQUIRES_CIRCUIT_BACKEND`.
- **Priority:** 2 — best first circuit-level investigation after blockers.

### P010-C07 — Normalization and interval-control circuit factoring

- **Category:** Normalization / region selection.
- **Baseline:** Count leading zero pairs, normalize by \(2^{2s}\), use
  top normalized bits for four cases, and denormalize by \(2^s\).
- **Proposed transformation:** Factor pair-zero detection, interval control,
  and shift control into a shared reversible Boolean network.
- **Mathematical justification:** Preserve exact \(s\), normalized bits, case
  selector, and output alignment for all valid \(x\); half-open case edges
  must be identical.
- **Fixed-point equivalence requirements:** Exact normalized register, all
  selector bits, and output numerator for every input.
- **Expected potential benefit:** `LOW` to `MEDIUM`, unknown.
- **Correctness risk:** High at power-of-two and pair-shift boundaries.
- **Implementation work:** Truth-table/circuit factoring with clean controls.
- **Tests:** All pair transitions, all region edges, exhaustive domain and
  compute/uncompute.
- **Circuit/backend:** Required for resource/depth evidence.
- **Verification:** Official full-domain verifier.
- **Evidence:** Integer normalization identity `MATHEMATICALLY_DERIVED`;
  lower gate cost `EMPIRICAL_HYPOTHESIS`.
- **Readiness:** `REQUIRES_CIRCUIT_BACKEND`.
- **Priority:** 7.

### P010-C08 — Phase rotation synthesis/error-budget allocation

- **Category:** Phase synthesis.
- **Baseline:** Output register bits induce phase operations; documented
  rotation pricing depends on synthesis precision, but exact local verifier
  and counter are unavailable.
- **Proposed transformation:** After recovering the official comparator,
  assign per-rotation synthesis tolerances from a rigorous residual phase
  error budget and measure the resulting exact T/fallback count.
- **Mathematical justification:** The sum of per-rotation errors must be
  bounded under the verifier's actual modulo/wrap metric and every target
  input. The present P007 relative error is not this synthesis budget.
- **Fixed-point equivalence requirements:** Preserve fixed-point numerator;
  add only phase-synthesis error within a proven total bound.
- **Expected potential benefit:** `UNKNOWN` (could reduce T count, or increase
  it if synthesis becomes stricter).
- **Correctness risk:** High because accumulated angle error can exceed
  tolerance and precise comparator semantics are missing.
- **Implementation work:** Recover verifier/metric, establish exact phase
  convention, derive per-gate allocation, implement real synthesis.
- **Tests:** Exhaustive target-phase comparison with exact integer rounding,
  wrap and equality boundaries, full verifier.
- **Circuit/backend:** Required; runtime, official counter, and verifier all
  required.
- **Verification:** Official full-domain zero-failure run.
- **Evidence:** Pricing `REPOSITORY_DOCUMENTED`; candidate
  `EMPIRICAL_HYPOTHESIS`.
- **Readiness:** `BLOCKED`.
- **Priority:** 8.

### P010-C09 — Broader-interval/lower-degree polynomial

- **Category:** Approximation algorithm / polynomial evaluation.
- **Baseline:** Four source-defined coefficient cases and one Newton step.
- **Proposed transformation:** Search a broader normalized interval or a
  lower-degree approximation without inventing production coefficients in
  P010.
- **Mathematical justification:** A new polynomial requires a uniform error
  bound and fixed-point coefficient quantization analysis; the Newton
  relation only propagates an ideal real-arithmetic starting error.
- **Fixed-point equivalence requirements:** This intentionally changes
  intermediate values; require a separate algorithm version, quantized
  coefficient source, complete phase-error proof/test, and preserved
  restoration/cleanup.
- **Expected potential benefit:** `UNKNOWN` (possibly less selection or
  arithmetic, perhaps higher degree/precision).
- **Correctness risk:** Very high; no candidate coefficients or end-to-end
  error budget exist.
- **Implementation work:** Separate numerical approximation study, then
  fixed-point quantization study, then reversible circuit.
- **Tests:** Rigorous interval maximum error; exhaustive integer-domain
  quantized evaluation; official phase test.
- **Circuit/backend:** Required for score claim; numerical fitting alone is
  insufficient.
- **Verification:** Official full domain and score counter.
- **Evidence:** Broader-polynomial direction `PAPER_SUPPORTED`;
  any coefficients/benefit `EMPIRICAL_HYPOTHESIS`.
- **Readiness:** `REQUIRES_MATHEMATICAL_PROOF`.
- **Priority:** 9; do not implement yet.

### P010-C10 — Remove the Newton correction

- **Category:** Newton correction elimination.
- **Baseline:** One Newton correction is part of the described reference.
- **Proposed transformation:** Omit the correction stage.
- **Mathematical justification:** None sufficient for the fixed-point official
  phase contract. The initial polynomial error and real Newton identity alone
  do not prove the uncorrected phase passes all inputs.
- **Fixed-point equivalence requirements:** Not equivalent by definition;
  would need a new complete error proof and official acceptance.
- **Expected potential benefit:** `UNKNOWN`; fewer operations is not evidence
  of lower official \(Q C\).
- **Correctness risk:** Very high and unbounded from available evidence.
- **Implementation work:** Not authorized.
- **Tests:** No prototype until a rigorous worst-case phase bound establishes
  viability.
- **Circuit/backend:** Required if reconsidered.
- **Verification:** Official full-domain verifier required.
- **Evidence:** Baseline correction `PAPER_SUPPORTED`; safety
  `UNKNOWN`/`BLOCKED`.
- **Readiness:** `REJECTED` for P011 implementation absent new proof.
- **Priority:** Reject/defer.

## 8. Candidate prioritization

| Rank | Candidate | Confidence / feasibility | Potential score impact | Complexity / verification | Decision |
|---:|---|---|---|---|---|
| 1 | C01 exact range and truncation-margin audit | High confidence as an analysis of the current model; exact circuit transfer still unproven | `UNKNOWN` | Numerical full-domain scan feasible; circuit proof later | First numerical prototype; do not narrow widths in this step |
| 2 | C06 workspace schedule/uncomputation | The paper supports reverse computation; circuit capability absent | `UNKNOWN` | High implementation and verifier cost | First circuit investigation after source/runtime/baseline gates |
| 3 | C04 Horner row specialization | Baseline row arithmetic is known from the mirrored model | `UNKNOWN` | Requires exact bit/carry proof and circuit synthesis | One-stage prototype only after backend available |
| 4 | C03 selector/QROM factoring | Four-case table and edges known against mirror model | `UNKNOWN` | Reversible lookup and cleanup complexity | Defer pending backend |
| 5 | C02 zero-row pruning | Exact zero identity is simple; proving controls are identically zero is circuit-specific | `LOW`–`MEDIUM` | Needs circuit and domain proof | Defer |
| 6 | C05 Newton fusion/scaling | Algebra alone insufficient due truncation | `LOW`–`MEDIUM` | Very high equivalence burden | Requires mathematical proof first |
| 7 | C07 normalization/control factoring | Normalization function known; gate cost unknown | `LOW`–`MEDIUM` | Boundary-sensitive and backend-dependent | Defer |
| 8 | C08 phase synthesis budget | Could influence T cost directly | `UNKNOWN` | Exact primary metric/verifier blocked | Blocked |
| 9 | C09 new polynomial | Paper motivates broad-range idea, but no supported coefficients/error bound | `UNKNOWN` | High numerical and circuit cost | Do not implement yet |
| 10 | C10 correction removal | No all-domain phase proof | `UNKNOWN` | Correctness risk dominates | Rejected until compelling proof |

- **Best first numerical prototype:** C01, exhaustive range/bit-use analysis
  using the validated default arithmetic only. It can tell us whether any
  width question merits a separate candidate without changing the model.
- **Best first circuit-level investigation:** C06, workspace scheduling and
  uncomputation, after Kickmix, circuit fixtures, verifier, and baseline
  provenance are closed.
- **Highest risk:** C09, changing the approximation polynomial, because it
  changes algorithmic error and quantized coefficients simultaneously.
- **Do not implement yet:** C05, C08, C09, and any precision narrowing; each
  needs proof, primary semantics, or a live circuit counter first.
- **Rejected for immediate implementation:** C10, due absent evidence that
  the uncorrected estimate meets phase tolerance everywhere.

No candidate has measured impact. All benefits remain qualitative.

## 9. Mathematical correctness obligations

Every serious candidate must retain:

1. The inclusive official input domain and exact target
   \(e^{2\pi i\beta/\sqrt{x}}\).
2. The exact modulo/wrap, rounding, and phase acceptance rule from the
   recovered official verifier; the P006 description is not a substitute.
3. The 22-bit input register's exact bit ordering, distinct-qubit constraint,
   and restoration.
4. Zeroed unnamed scratch/work qubits for every relevant measurement outcome.
5. The source-defined coefficient words, widths, row truncation, addition,
   carry, shifts, and subtraction, unless a separately versioned candidate
   proves/revalidates its changes.
6. A complete stage-wise bound from polynomial and coefficient errors through
   all fixed-point operations and synthesized phase rotations.
7. Boundary coverage: domain endpoints, every leading-zero-pair transition,
   each interval boundary, each truncation/carry threshold, and phase wrap
   edges.
8. A full-domain verifier result and measured \(Q C\) from the same
   provenance-bound circuit artifact before any acceptance or improvement
   claim.

For exact arithmetic rewrites, compare intermediate integer registers—not
only final approximate real values. For approximate rewrites, evaluate phase
error in the official units and comparator. Floating-point/Decimal proximity
or P009 output equality is not proof of reversible circuit equivalence.

## 10. Future experiment specifications

No experiment below was run. Experiments E-01/E-02 can initially be
classical-only; all resource or acceptance conclusions require the live
circuit/backend path.

### E-01 — Baseline reachable ranges and bit-use profile (C01)

- **Hypothesis:** One or more baseline work registers may have unreachable
  high bits or a positive safety margin that justifies later width review.
- **Baseline:** P008 default precision; pinned source model and P009 emulator;
  `n_p=10`; full input domain.
- **Candidate transformation:** None for the first pass. Measure the baseline
  stage registers, maxima/minima, highest set-bit positions, and inputs that
  attain each extreme. A second, separately approved run may emulate a single
  proposed narrower width.
- **Input coverage:** Ascending \(x=1\ldots3{,}133{,}452\), including all
  normalization/interval boundaries in the full pass.
- **Expected output:** A reproducible range table, no expected resource
  result.
- **Correctness checks:** Baseline output unchanged; stage extrema/counts
  repeat; no input omitted; any proposed width checked against source fixed
  widths.
- **Numerical comparison:** Integer-exact comparison against the hash-pinned
  model; phase-vs-target may be reported separately but not treated as
  official verification.
- **Resources:** None in the numerical pass; circuit \(Q\), Toffoli, T,
  rotations, depth (secondary), and peak ancilla only after circuit exists.
- **Official verifier:** Required for any changed width candidate, not for
  collecting baseline integer ranges.
- **Reproducibility:** Pin source hash/commit, code revision, precision,
  Python/NumPy, complete ordered domain, output checksum, and first mismatch.
- **Pass/fail:** Pass analysis only if every input is counted and exact
  baseline stage values agree; a narrow-width proposal passes only with
  stage/output exactness or a full proven phase bound.

### E-02 — Exact Horner row specialization (C04)

- **Hypothesis:** The existing three row accumulators can be implemented with
  fewer reversible operations while preserving exact per-row truncation.
- **Baseline:** Original Horner order, four coefficient cases, 14-bit delta,
  17-bit intermediates.
- **Candidate transformation:** One row/carry-network rewrite in a separate
  candidate branch/configuration; no changed coefficient or precision.
- **Input coverage:** Exhaust legal delta patterns per region, then all valid
  domain inputs and boundary vectors.
- **Expected output:** Every Horner intermediate and final result bit equal.
- **Correctness checks:** Forward/inverse state, control cleanup, exact
  integer equality.
- **Numerical comparison:** Integer bitwise comparison, no approximate
  tolerance.
- **Resources:** Actual qubits, Toffoli, T, rotation contribution; secondary
  depth and compile/runtime.
- **Official verifier:** Required for any submission candidate.
- **Reproducibility:** Candidate/source hashes, compiler/runtime version,
  seed, exact command, inputs, logs.
- **Pass/fail:** Fail on one integer mismatch, dirty work bit, or non-finite
  resource result; advance only if measured \(Q'C'<QC\).

### E-03 — Reversible workspace lifetime study (C06)

- **Hypothesis:** A different legal schedule can reuse clean work registers
  and/or reduce gates without changing the diagonal unitary.
- **Baseline:** Reference compute, phase, reverse-compute order.
- **Candidate transformation:** One named register-lifetime/uncompute
  change; exact arithmetic unchanged.
- **Input coverage:** Boundary basis states, all relevant measurement
  outcomes, then verifier's complete domain and shots.
- **Expected output:** Same tracked phase, original `x`, and all work
  registers restored.
- **Correctness checks:** State-level trajectory comparison and every
  measurement/reset branch supported by the runtime.
- **Numerical comparison:** Official fixed-point phase comparator and
  zero-failure behavior.
- **Resources:** Official \(Q\), Toffoli, T, rotation cost; depth/runtime
  secondary.
- **Official verifier:** Required for promotion and score comparison.
- **Reproducibility:** Pin circuit, verifier, metric, runtime, commit,
  environment, seed/salt where permitted, logs and approval.
- **Pass/fail:** Any phase/restoration/cleanup failure rejects; score advances
  only if official \(Q C\) is lower.

### E-04 — Phase synthesis tolerance allocation (C08)

- **Hypothesis:** Error-budgeted per-rotation synthesis could change the T and
  rotation-fallback contribution.
- **Baseline:** Recovered official reference phase synthesis and verifier.
- **Candidate transformation:** One allocation policy derived from a
  verified bound, no fixed-point output change.
- **Input coverage:** All valid inputs; phase-wrap and comparator thresholds
  explicitly included.
- **Expected output:** Same acceptance contract, with a reported phase error
  bound and actual rotation counts.
- **Correctness checks:** Exact official comparator reproduction and
  accumulated synthesis error proof.
- **Numerical comparison:** Integer/fixed-point phase units; no unverified
  floating-only comparator.
- **Resources:** Official T and fallback T counts, \(Q\), Toffoli, plus
  secondary synthesis depth/runtime.
- **Official verifier:** Required.
- **Reproducibility:** Pin comparator, metric, compiler, per-gate tolerances,
  circuit artifact and input-domain results.
- **Pass/fail:** Fail if any input/shot exceeds verifier tolerance; advance
  only if \(Q C\) improves.

### E-05 — Broader polynomial study (C09), research-only gate

- **Hypothesis:** A lower-degree/broader-range approximation could reduce
  selection/evaluation work.
- **Baseline:** P007 Decimal model for ideal math and P008 fixed-point model
  for the quantized baseline, clearly kept separate.
- **Candidate transformation:** No coefficient is specified in P010. A future
  numerical study must version every fitted coefficient and derive a uniform
  approximation bound before quantization.
- **Input coverage:** Continuous interval proof or certified extremum search,
  then all 3,133,452 integer inputs after quantization.
- **Expected output:** Candidate error curve, worst-case location, quantized
  stage output; no synthetic resources.
- **Correctness checks:** Bound initial estimate and Newton propagated error,
  then include coefficient quantization, row truncation, and phase synthesis.
- **Numerical comparison:** High-precision Decimal or interval arithmetic
  against \(1/\sqrt{x}\); fixed-point exact integer tests after encoding.
- **Resources:** None until a circuit is built; then official measures.
- **Official verifier:** Required before any correctness claim.
- **Reproducibility:** Publish fitting objective, domain, precision, solver,
  coefficients, quantizer and complete validation input/output hashes.
- **Pass/fail:** Stop if a rigorous domain-wide bound cannot be established;
  never select coefficients based on a sparse sample alone.

## 11. Search-space parameter design (not added)

Possible future parameter definitions, all experiment-only until justified:

| Proposed name | Type / candidate domain | Source-supported default | Constraints/dependencies | Algorithm/resource effect | Correctness and verification | Executable now? |
|---|---|---|---|---|---|---|
| `delta_bits_candidate` | Integer; finite values derived after C01 proof | Baseline 14, not a candidate default | Must preserve exact baseline truncation unless separately evaluated; depends on coefficient and product widths | Delta row count/precision | Full stage equality or error proof; official verifier for changed output | No |
| `coef_bits_candidate` | Integer; finite evidence-backed set only | Baseline 17 | Requires regenerated table encoded by source formula; all coefficient words fit | QROM width, Horner arithmetic | Coefficient/address equality and full phase bound | No |
| `square_bits_candidate` | Integer; proof-derived set | Baseline 28 | Depends on `coef_bits_candidate`, product widths, carry and output budget | Square network and ancillas | Full-domain exact-stage or error validation | No |
| `product_bits_candidate` | Integer; proof-derived set | Baseline 28 | Applies to mantissa product/correction; dependent on square width | Multiplier network | Stage-by-stage equality and phase check | No |
| `result_bits_candidate` | Integer; proof-derived set | Baseline 29 | Output phase width and `n_p` scaling coupled | Final multiplier, output qubits/rotations | Exact phase rounding/tolerance via verifier | No |
| `polynomial_form` | Categorical; `baseline_horner` plus future proven forms | `baseline_horner` | Any alternative form changes truncation ordering and needs unique model | Arithmetic depth/gates | Exact integer mapping or full error proof | No |
| `normalization_form` | Categorical; baseline and future truth-table-equivalent forms | `leading_zero_pairs` | Must preserve `s`, normalized bits and interval selector | Comparators/controls/depth | Exhaustive boundary and cleanup checks | No |
| `workspace_schedule` | Categorical; baseline plus explicit schedules | `reference_reverse_order` | Valid only when lifetimes and uncompute are specified | \(Q\), gates, depth | State/cleanup checks plus official metrics | No |
| `rotation_policy` | Categorical or proof-derived finite synthesis policies | `official_reference_policy` once recovered | Depends on exact comparator and per-rotation error bounds | T/fallback gates | Official full-domain phase verification | No |
| `newton_steps` | Integer, candidate values would require proof | Baseline 1 | Do not expose/remove before all-domain phase proof | Arithmetic stage count | Full quantized phase proof and verifier | No |

No parameter, range, or dependency was added to `search_space.py` or a
production search definition. Its current schema supports typed parameter
values but does not encode conditional dependencies or mathematical proofs.
The experiment framework is only partially applicable: configuration
generation and record provenance exist; real construction, measurement, and
official execution do not.

## 12. Implementation-readiness matrix

| Capability | Status | Evidence / blocker |
|---|---|---|
| Paper-level algorithm and target | `PARTIALLY_READY` | P007/P006 paper-derived equations and domain |
| Default classical fixed-point semantics | `PARTIALLY_READY` | P009 full-domain mirror-model match; mirror provenance remains qualified |
| Exact official artifact provenance | `BLOCKED` | Need official competition archive/checksum or other authoritative identity |
| Stage-wise reachable-range report | `READY_FOR_NUMERICAL_EXPERIMENT` | Can scan validated model; no scan performed in P010 |
| Fixed-point width change | `REQUIRES_FIXED_POINT_EQUIVALENCE` | Must prove per-stage results/error; unsupported precision is intentionally rejected |
| Reversible circuit construction | `BLOCKED` | No production backend; Kickmix missing/unavailable |
| Resource counter | `BLOCKED` | Official resource implementation unavailable |
| Official phase comparator/verifier | `BLOCKED` | Source absent; no verifier run |
| Full candidate score improvement | `BLOCKED` | Requires official verifier and same-artifact measured resource counts |
| Search parameter generation | `REPOSITORY_VERIFIED` | Generic typed grid/random strategy exists, but no INVSQRT candidate backend |
| P011 authorization/baseline gate | `BLOCKED` | P006 docs note strict baseline provenance and approval gate are not closed by this report |

## 13. Dependency and capability blockers

1. **Official source identity:** acquire competition-distributed verifier,
   metric, reference source, and sample circuit with authoritative hashes.
   P009's immutable mirror hash match remains not official authentication.
2. **Kickmix runtime/API:** provide supported binary/source and version;
   confirm parsing, construction, simulator, measurement-based uncompute,
   resource, and serialization behavior.
3. **Official verifier/metric:** make the phase comparator, resource counters,
   rotation pricing, and acceptance rules inspectable and executable.
4. **Baseline provenance:** bind a strict baseline run to candidate and
   verifier hashes, commit, environment, exact command, logs, timestamp, and
   authorization.
5. **Error budget:** derive all intermediate arithmetic and phase synthesis
   contributions against the actual official comparison.
6. **Experiment policy:** satisfy the existing explicit authorization gate
   before any optimization circuit work.

## 14. Recommended P011 implementation direction

Do not begin with a new polynomial, changed precision, Newton deletion, or
speculative circuit rewrite. First close source/runtime/baseline provenance.
If the circuit backend remains unavailable, the safest P011 implementation is
a standalone, deterministic **baseline intermediate-range and
truncation-margin analyzer** for C01. It should report exact source/model
identity, domain count, extrema and attaining inputs for each intermediate,
used-bit widths, and no proposed width changes. Keep it separate from
`fixed_point_reference`; then derive a narrowly scoped width candidate only
with a proof and review.

If authoritative artifacts and Kickmix are available, first circuit-level
prototype C06 (one workspace schedule/uncompute change) while keeping
arithmetic unchanged, because correctness can be isolated from approximation
changes. Require restoration, scratch cleanup, official phase acceptance, and
measured \(Q C\) before continuing. P010 itself does not authorize or start
P011.

## 15. Source references and evidence

1. **Companion paper:** arXiv:2610.23832v2, §III.1.2–III.1.3,
   Eqs. (14)–(31), Appendix B.1/B.3 Eqs. (102)–(110):
   [abstract](https://arxiv.org/abs/2610.23832v2),
   [HTML](https://arxiv.org/html/2610.23832v2). Supports the mathematical
   reference method and optimization directions, not this report's circuit
   resource outcomes.
2. **Local scorer:** `src/invsqrt_opt/score.py` and metric model in
   `src/invsqrt_opt/models.py`. Repository implementation; not primary
   official metric source.
3. **P006 report:** [INVSQRT Algorithm and Optimization Strategy](./INVSQRT_ALGORITHM_AND_OPTIMIZATION_STRATEGY.md),
   especially §§5, 8–17. Identifies source hierarchy, score formula,
   blockers, and research hypotheses.
4. **P007 report:** [INVSQRT Classical Reference Implementation](./INVSQRT_CLASSICAL_REFERENCE_IMPLEMENTATION.md),
   §§4–11. Decimal model, oracle, and exhaustive error results.
5. **P008 report:** [INVSQRT Fixed-Point Semantics and Emulator Readiness](./INVSQRT_FIXED_POINT_SEMANTICS_AND_EMULATOR_READINESS.md),
   §§3–15. Mirror-qualified integer semantics and circuit blockers.
6. **P009 report:** [INVSQRT Fixed-Point Emulator Validation](./INVSQRT_FIXED_POINT_EMULATOR_VALIDATION.md),
   §§4–10. Hashes, differential methodology, results, provenance limitation.
7. **P009 mirror reference file:** `qarena-ai/invsqrt` at commit
   `6ac78ec5ace6dfd5831ccac2547041408f5d8278`, path
   `verifiers/invsqrt/nr_reference_circuit.py`, SHA-256
   `bb90330dcf774f7b502de471293facba67f27952cc8808fe4a9970a9b1322e23`.
   Mirror-derived; not independently authenticated official data.
8. **P009 mirror verifier file:** same commit, path
   `verifiers/invsqrt/verify_submission_invsqrt.py`, SHA-256
   `ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a`.
   Hash-verified mirror bytes; verifier not executed.
9. **Framework:** `search_space.py`, `configurations.py`, `strategies.py`,
   `backend.py`, `execution.py`, `runner.py`, `comparison.py`, `verifier.py`,
   `artifacts.py`, and their existing `tests/`.

### Evidence status summary

- **Directly inspected/repository-verified:** P010 repository root, branch,
  HEAD, dirty state; score helper formula; model/search/backend interfaces;
  artifact-readiness structure; P006–P009 reports and test inventory.
- **P009-reported and independently source-hash qualified:** two exact
  full-domain comparisons against the mirror's classical model; the
  official-origin claim remains qualified.
- **Paper-supported:** high-level normalized cubic/Newton method, target
  phase, and research directions described in the cited sections.
- **Mathematically derived:** Newton relative-error recurrence and the
  necessary \(Q'C'<QC\) comparison.
- **Empirical hypotheses:** all candidate resource benefits.
- **Not measured / blocked:** any candidate resource count, depth, score
  improvement, official verifier pass, or circuit-equivalence claim.

## 16. P010 completion status

- Candidate register: created with ten candidates, explicit evidence,
  readiness, priorities, and correctness obligations.
- Future experiments: specified with baselines, coverage, checks, measurements,
  reproducibility, and pass/fail criteria.
- Production search space and baseline behavior: unchanged.
- Official artifacts and verifier: not modified or executed.
- P007/P008/P009 outcomes: preserved without relabeling.
- Circuit equivalence and score improvement: not claimed.
