# DQI-P014 — EEA State Capacity Analysis and Iteration Contract

## 1. Purpose and disposition

P014 is a specification-only analysis of the P013 bounded single-step
extended-Euclidean algorithm (EEA) model. It resolves which polynomial-width
claims follow from the current APIs, derives degree-based bounds for the
standard EEA state, compares capacity architectures, and defines a bounded
iterative contract for a future implementation.

No source or test code is implemented by this specification. P015 is not
started.

**Recommendation:** use role-separated fixed-capacity state registers whose
widths are justified by the standard EEA degree invariant, a fixed maximum
round schedule, and retained stage history for the reversible classical
model. This is a specification recommendation, not an implementation or
gate-level design. It requires a capacity-aware division/multiplication
contract; the current P012 and P013 public interfaces cannot implement it
unchanged.

The paper-parameter mathematical operands fit the derived per-polynomial
degree capacities, but that does **not** show that this stage-banked design
fits P008's shared two-array schedule. The local paper-level register
assignment, output coefficient normalization, zero-syndrome behavior, and
the circuit's off-promise total extension remain unresolved.

## 2. Scope and repository baseline

The analysis is grounded in the actual P008 specification; P009-P013
reports, source modules, and relevant tests; and the P013-P014 handoff.
Repository baseline at inspection:

| Item | Observed |
|---|---|
| Root | `/mnt/d/PROJECT/Quantum_AI/Google-Quantum-AI` |
| Branch | `feat/dqi-decoder` |
| HEAD | `5391b2e7123484efacffc0588f5e761e67b5cb55` |
| Staged changes | None |
| Tracked modification | Existing `README.md` change only |
| Existing untracked work | 83 paths, including prior DQI artifacts and existing bytecode caches |

The README was not edited. No dependency, source, test, report other than
this authorized P014 document, or unrelated INVSQRT artifact was modified
or deleted. No Git history or branch operation was performed.

## 3. Evidence inspected

### P008 paper-level specification

- `docs/research/DQI_P008_REVERSIBLE_DECODER_SPECIFICATION.md`, especially
  §5.1–§5.3 (EEA algorithm family, synchronized storage, degree pointers,
  iteration and cleanup obligations), §7–§8 (workspace and uncomputation).

### P009–P013 reports and code

- P009: `docs/research/DQI_P009_REVERSIBLE_FINITE_FIELD_PRIMITIVES_REPORT.md`,
  `src/dqi_decoder/reversible_primitives.py`,
  `tests/dqi_decoder/test_reversible_primitives.py`.
- P010: `docs/research/DQI_P010_REVERSIBLE_POLYNOMIAL_ARITHMETIC_REPORT.md`,
  `src/dqi_decoder/reversible_polynomial.py`,
  `tests/dqi_decoder/test_reversible_polynomial.py`.
- P011: `docs/research/DQI_P011_REVERSIBLE_POLYNOMIAL_EVALUATION_REPORT.md`,
  `src/dqi_decoder/reversible_evaluation.py`,
  `tests/dqi_decoder/test_reversible_evaluation.py`.
- P012: `docs/research/DQI_P012_REVERSIBLE_POLYNOMIAL_DIVISION_REPORT.md`,
  `src/dqi_decoder/reversible_division.py`,
  `tests/dqi_decoder/test_reversible_division.py`.
- P013: `docs/research/DQI_P013_REVERSIBLE_EEA_FOUNDATION_REPORT.md`,
  `src/dqi_decoder/reversible_eea.py`,
  `tests/dqi_decoder/test_reversible_eea.py`.
- `docs/research/DQI_P013_P014_HANDOFF.md`.
- Shared arithmetic conventions in `src/dqi_decoder/field.py` and
  `src/dqi_decoder/polynomial.py`.

The tests and reports are evidence for bounded classical models and test
domains; they are not treated as circuit or official-verifier evidence.

## 4. Existing representation and capacity facts

### 4.1 Polynomial and field representation

- A field element is an integer in `[0, 4095]`, polynomial-basis encoded
  over GF(2^12), with modulus `0x1053`.
- Polynomial coefficients are low-degree first; tuple index zero is the
  constant coefficient.
- Classical `polynomial.py` normalizes away high trailing zeroes and uses
  `()` for zero. Reversible register APIs use nonempty fixed-width tuples;
  a nonempty all-zero tuple represents zero and padding is retained.
- Field addition and polynomial coefficient addition are XOR.
- P009 arithmetic functions preserve operands and XOR results into targets.
- P010 multiplication requires a target of exactly
  `len(left)+len(right)-1`; it computes the full convolution of the
  *declared tuple widths*, including padded positions.

### 4.2 P012/P013 API limits

P012 sets `MAX_POLYNOMIAL_REGISTER_WIDTH = 8` for both division operands.
Its quotient target width is exactly the declared dividend width; its
remainder target width is `max(1, len(divisor)-1)`. It rejects a zero
divisor.

P013 applies that same width limit to **all six** input polynomials:
`(r0,r1,s0,s1,t0,t1)`. Its output target widths are:

```text
Q  = len(r0)
R2 = max(1, len(r1)-1)
S2 = max(len(s0), len(r0)+len(s1)-1)
T2 = max(len(t0), len(r0)+len(t1)-1)
```

Consequently, a valid P013 call can return `s2` and `t2` targets as wide
as 15 slots although the next P013 call rejects any input wider than 8.
P013's arbitrary six-register interface does not itself enforce the
conventional EEA initialization or a Bézout-history invariant.

For generic declared widths `R=len(r0)` and `C=len(s1)`, a target coefficient
width can grow to `max(len(s0), R+C-1)`. Repeatedly applying this width
rule at worst-case `R=8`, beginning with one-slot coefficients, yields
declared widths 8 after the first transition and 15 after the second.
Thus two transitions are possible in this worst-case width sequence, but
the second result is not generally a valid next P013 input. Shorter inputs
can allow more calls; P013 gives no uniform iterative bound.

This is a declared-width issue, not a proof that a mathematically
conventional EEA coefficient necessarily has degree 14. Trailing zeroes in
the P013 output may be removable as classical representation padding, but
trimming/repacking is not part of the P013 API and is not by itself a
reversible fixed-register operation.

## 5. Standard EEA state and mathematical bounds

The following bounds apply only to the standard EEA state and its invariant;
they do not apply to arbitrary six-tuples accepted by P013.

Let `A` and `B` be nonzero polynomials over the repository field with
degrees

```text
m = deg(A),  n = deg(B),  m >= n >= 0.
```

Initialize:

```text
r[-1] = A                 r[0] = B
s[-1] = 1                 s[0] = 0
t[-1] = 0                 t[0] = 1
r[i] = s[i]*A + t[i]*B
```

For an active step with `r[k] != 0`, divide:

```text
r[k-1] = q[k]*r[k] + r[k+1]
r[k+1] = 0 or deg(r[k+1]) < deg(r[k])
s[k+1] = s[k-1] + q[k]*s[k]
t[k+1] = t[k-1] + q[k]*t[k]
```

All additions here are over GF(2^12), hence XOR. Require `A` and `B` to
be ordered by degree at initialization; do not silently swap without also
swapping the Bézout initialization.

### 5.1 Full Euclidean run (for comparison)

For the conventional initialization and strictly decreasing nonzero
remainders, the quotient degree is
`deg(q[k]) = deg(r[k-1])-deg(r[k])`. The quotient degrees telescope.
The standard recurrence yields the useful bounds:

```text
deg(s[k+1]) <= n - deg(r[k])
deg(t[k+1]) <= m - deg(r[k])
```

for nonzero coefficient values at an update; zero coefficients require
only the minimum nonempty fixed width. Therefore, through the final
division-to-zero step, conservative fixed coefficient widths are:

```text
S_full = n + 1 slots
T_full = m + 1 slots
```

The final zero remainder is represented by an all-zero fixed-width tuple.
The full-run quotient can have degree `m` in the constant-divisor case,
so `Q_full = m+1` slots. A full Euclidean run is not the P008
degree-threshold procedure and is not selected as the P014 objective.

### 5.2 Bounded run stopping below a threshold

Let `ell >= 1`. Starting with `r[-1]=A`, `r[0]=B`, divide only while
`r[k]` is nonzero and `deg(r[k]) >= ell`. The active divisor degree is
therefore at least `ell`.

The number of divisions is bounded by:

```text
K <= max(0, n - ell + 1) <= max(0, m - ell)
```

because each nonzero remainder degree decreases by at least one, and
`n <= m-1` for the paper's distinct operands. If `deg(B)<ell`, no
division is needed. A zero `B` also satisfies the numeric degree test but
is a separate semantic case; this specification does not silently treat it
as an ordinary nonzero-divisor EEA input.

At every active step:

```text
deg(q[k]) <= m - ell
deg(q[k]*r[k]) = deg(r[k-1]) <= m
deg(q[k]*s[k]) <= n - ell
deg(q[k]*t[k]) <= m - ell
```

The coefficient bounds follow by substituting the preceding coefficient
bounds and the quotient degree difference into the recurrence. The
remainder produced at a step has degree below the active divisor. These
facts give fixed capacities for the *mathematical nonzero support*:

| Register family | Capacity in coefficient slots |
|---|---:|
| Remainder state, including initial `A` | `R = m+1` |
| Active quotient | `Q = max(1, m-ell+1)` |
| `s` coefficient state / `q*s` result | `S = max(1, n-ell+1)` |
| `t` coefficient state / `q*t` result | `T = max(1, m-ell+1)` |
| `q*r` reconstruction product | `R = m+1` |

The `max(1, ...)` convention keeps zero and constant polynomials in a
nonempty fixed-width representation. An addition of `s[k-1]` and
`q*s[k]` fits `S`; an addition of `t[k-1]` and `q*t[k]` fits `T`.
`r[k-1] = q*r[k] + r[k+1]` fits `R`.

These are mathematical degree bounds for the standard initialized EEA.
They do **not** mean P010's full declared-width convolution can be placed
directly into these narrow result arrays. That interface's exact target
width is based on tuple lengths, not active degree.

## 6. P008 parameter comparison

P008 describes `n=70`, `ell=35`, EEA on `z^(2ell)` and `S(z)`.
Thus:

```text
A = z^70:       m=70, 71 coefficient slots
B = S(z):       deg(B)<=69, up to 70 coefficient slots
```

For nonzero `S`, the degree-threshold bound gives at most 35 divisions.
If `deg(S)<35`, it gives zero divisions. For an active step, the
mathematical bounds are:

| Item | Bound | P008 parameter capacity |
|---|---:|---:|
| Uniform remainder state | `m+1` | 71 slots |
| Initial syndrome polynomial | `n+1` | at most 70 slots |
| Quotient significant support | `m-ell+1` | at most 36 slots |
| `s`/`q*s` significant support | `max(1,n-ell+1)` | at most 35 slots |
| `t`/`q*t` significant support | `m-ell+1` | 36 slots |
| `q*r` significant support | `m+1` | 71 slots |
| Maximum active division rounds | `max(0,n-ell+1)` | at most 35 |

The coefficient outputs' exact role as locator/evaluator, any normalization
factor, and which terminal remainder/Bézout member feeds later stages are
not settled by these degree bounds. P008's paper-level key-equation
construction supports the algorithm family and threshold; this document
does not infer an output convention beyond the generic EEA state.

P008 additionally reports two arrays of `n+3=73` field-element registers,
five `O(log n)` degree pointers, temporary quotient storage, and
`3(n+1)+9=222` synchronized EEA steps. Those are facts reported in the
local P008 specification about the paper's architecture. They are **not**
the same as 35 mathematical polynomial-division rounds. P008 does not give
this repository a locally verified register alias map or an executable
schedule. The fact that one polynomial's 71 slots are no more than 73
does not prove that the proposed stage banks, scratch, pointers, or
uncomputation schedule fit in the paper's two shared arrays.

### Unsupported by current implementation

- P012 and P013 reject input tuples wider than 8. They cannot accept the
  71-slot `z^70` operand or a syndrome tuple of up to 70 slots.
- P013's Bézout target sizing is declared-width convolution sizing and can
  produce 15 slots at width-8 input; it is not the degree-aware 35/36-slot
  threshold bound.
- P010 requires full convolution targets based on operand tuple widths.
  P012 requires quotient target width equal to dividend tuple width.
- No P008 paper-parameter implementation, pointer schedule, shared-register
  aliasing, or circuit-level cleanup proof exists in the inspected code.

Therefore, P014 can define a mathematically bounded reference contract for
the paper parameters, but must label paper-parameter execution unsupported
until those API and circuit/architecture gaps are addressed and validated.

## 7. Multiplication and scratch capacities

Two different notions of product width must not be conflated.

### 7.1 Degree-bounded mathematical products

For a thresholded EEA step, the valid-state invariant gives the product
capacities `R`, `S`, and `T` in §5.2. At P008 parameters these are 71
slots for `q*r`, at most 35 for `q*s`, and 36 for `q*t`. Products and
updates must be checked against these bounds; no high coefficient may be
silently discarded.

### 7.2 Full declared-width convolution products

If fixed-width arrays are passed unmodified to P010, its exact full
convolution target lengths are:

| Product | With compact degree-bound operands | With P012-width quotient (71 slots) |
|---|---:|---:|
| `q*r` with remainder capacity 71 | `36+71-1 = 106` | `71+71-1 = 141` |
| `q*s` with `S=35` | `36+35-1 = 70` | `71+35-1 = 105` |
| `q*t` with `T=36` | `36+36-1 = 71` | `71+36-1 = 106` |

These raw targets include high zero padding that the EEA invariant says
cannot be nonzero above the mathematical product bounds. They are the
widths demanded by P010's current API, not the mathematical lower bounds.
For a fixed-capacity iterative implementation, choose explicitly between:

1. retaining the full declared-width product arrays at these larger widths;
   or
2. specifying a new fixed-schedule, degree-bounded multiply relation whose
   active-degree/control state is retained and whose valid-state bounds are
   proved.

It is not acceptable to compute a full product and silently truncate it to
`S`, `T`, or `R`.

### 7.3 Division scratch

P012's current Python scratch structure allocates a dividend-width
remainder copy, a dividend-width quotient copy, one inverse element, and
for every quotient shift one factor plus new quotient and remainder copies.
For a generalized fixed-width version with remainder width `R`, quotient
width `Q`, and `h` shift iterations, that source-shaped scratch count is:

```text
R + Q + 1 + h*(R + Q + 1) = (h+1)*(R+Q+1)
```

This counts field-element slots in the Python scratch vector, not qubits or
a circuit ancilla count. For P008 parameter bounds, if a specialized
division uses `R=71`, quotient output width `Q=71` (preserving P012's
dividend-width quotient contract), and at most 36 fixed shifts for an
active divisor of degree at least 35, the source-shaped upper bound is
`37*(71+71+1)=5,291` field-element scratch slots for that division call.
This is a conservative extension calculation; the current P012 API rejects
these widths and this count is not a P008 paper resource claim.

A more compact `Q=36` quotient target would reduce that bound to
`37*(71+36+1)=3,996`, but it changes P012's target-width contract and
requires an independently specified division implementation. Degree-aware
coefficient-product scratch, active-degree metadata, termination/round
control, and retained stage history are additional to the division scratch.
Their final physical allocation depends on the selected implementation.

## 8. Capacity architecture alternatives

| Architecture | Capacity rule | Advantages | Risks / status |
|---|---|---|---|
| Reuse P013 unchanged | Keep every one of six inputs at width at most 8; require each target output to fit the next call | Reuses existing tested API for small examples | No general iteration guarantee; worst-case coefficient output grows 8 then 15 slots. Cannot run P008 operands. |
| Raise one uniform width and use full declared-width products | For fixed `R`-slot quotient width, coefficient width after `K` rounds is bounded by `C_K = C_0 + K*(R-1)` | Simple conservative sizing for a declared finite `K`; no reliance on correlated EEA degrees | For P008, `R=71`, `C0=1`, `K=35` gives 2,451 coefficient slots. It is very wasteful and does not match P008's reported 73-slot shared arrays. Requires generalized P012/P013 validation and still has large convolution scratch. |
| Role-separated degree bounds, fixed stage banks | Remainders `m+1`; threshold quotient `m-ell+1`; `s` coefficients `n-ell+1`; `t` coefficients `m-ell+1`; retain a finite number of state banks | Mathematically justified under standard EEA initialization; fixed capacity independent of number of rounds up to threshold; explicit history makes the classical model easier to audit | Requires enforcing the EEA invariant, explicit degree/control state, specialized bounded arithmetic, and much more storage than P008's synchronized architecture. Recommended for a bounded reference model, not a circuit claim. |
| Reproduce P008 synchronized/shared arrays | Use paper-described two arrays of `n+3` field registers, degree pointers, and stored quotient information | Closest to paper-level resource architecture | Exact alias map, local reversible schedule, and detailed inverse trace are not established in repository evidence. Not ready to select as an implementation contract without further paper/source review. |

For the recommended stage-bank architecture, a transparent conservative
coefficient-slot accounting for P008 bounds is:

- one state bank contains two remainder arrays of 71 slots, two `s` arrays
  of 35 slots, and two `t` arrays of 36 slots: 284 field-element slots;
- a maximum 35-round schedule with the initial state plus one bank per
  round retains 36 banks: `36*284 = 10,224` slots;
- if all 35 quotients are retained at the P012-compatible 71-slot width,
  quotient history adds `35*71 = 2,485` slots;
- subtotal for state banks and quotient history is 12,709 coefficient
  slots, before reusable arithmetic scratch, degree pointers, flags,
  padding/control, or any circuit decomposition.

This is a simple history-preserving reference architecture, **not** a
lower bound, a qubit estimate, or a claim that P008's implementation uses
this storage. Recomputing quotients during reverse cleanup can change the
history count but adds work and must itself be proven reversible.

## 9. Recommended fixed-width iterative contract

The following is a proposed future mathematical/classical register-model
contract. It is not implemented here.

### 9.1 Valid input domain and initialization

Configuration consists of fixed degree bounds `M`, `N`, and `L`, with
`M>=L>=1` and `0<=N<=M`, where `M` bounds `deg(A)` and `N` bounds the
initial `deg(B)`.
Inputs are nonempty low-degree-first fixed-width tuples over GF(2^12),
with effective degrees computed without changing the declared arrays.
Require:

1. `A` is nonzero and `deg(A)=m<=M`.
2. `B` is nonzero and `deg(B)=n<=min(m,N)`.
3. `L` is the specified stop threshold.
4. Inputs preserve their full declared contents; trailing high zeroes are
   padding, not degree.

Use the conventional state:

```text
(r[-1], r[0]) = (A, B)
(s[-1], s[0]) = (1, 0)
(t[-1], t[0]) = (0, 1)
```

The fixed array widths are selected from the configured `M`, maximum
initial `n`, and `L`, not from unbounded runtime growth. The zero-syndrome
case `B=0` is outside this core domain and must be specified as a separate
branch before any P012/P013 division call. P008/P009–P013 do not establish
the required DQI zero-syndrome output contract. `deg(B)<L` is valid and
terminates with zero division rounds.

### 9.2 Transition and round bound

An active round is permitted only when the current divisor register is
nonzero and its effective degree is at least `L`. It computes:

```text
q = quotient(r_prev, r_cur)
r_next = remainder(r_prev, r_cur)
s_next = s_prev XOR q*s_cur
t_next = t_prev XOR q*t_cur
```

The next state is `(r_cur,r_next,s_cur,s_next,t_cur,t_next)`. Retain the
mathematical invariant `r_i=s_i*A XOR t_i*B`; the transition must check the
division identity and strict remainder-degree decrease in the model.

Configure a fixed maximum number of rounds:

```text
Kmax = max(0, N-L+1)
```

This follows from the per-round strict degree decrease and the configured
bound on the initial current remainder. For the P008 operands, `N=69` and
`L=35`, so `Kmax=35`. A more general domain that allows `deg(B)=M` sets
`N=M` and therefore uses `max(0,M-L+1)` instead. Execute a fixed schedule of
`Kmax` rounds in the reversible
model; once the termination flag is set, later rounds are reversible
no-ops. Do not use an unrecorded classical early exit.

Termination is `current remainder == 0` or
`deg(current remainder)<L`; the zero-remainder condition prevents a later
division-by-zero call. `B=0` at initialization remains a separately
defined/rejected input case, not an active division state.

### 9.3 Capacities and overflow

For valid conventional states, use the §5.2 role capacities. For the
P008-shaped `M=70`, `L=35`, `deg(B)<=69` domain:

```text
remainder state capacity: 71
quotient capacity:        71 if preserving P012 output width;
                          36 only under a new bounded-quotient contract
s state capacity:         at most 35
t state capacity:         36
q*r scratch:              71 mathematically, or full-convolution width
                          if using the unmodified P010 API
q*s scratch:              35 mathematically; full P010 width otherwise
q*t scratch:              36 mathematically; full P010 width otherwise
```

Validate all input widths, effective degrees, target widths, and nonzero
divisors before output accumulation. Check every nonzero high coefficient
against the derived capacity. On the declared classical valid domain, an
overflow is an explicit capacity error before caller-visible target
mutation; it is never silently truncated. A quantum circuit cannot raise
such an exception: a total off-promise reversible extension or a precise
valid-subspace proof remains a separate requirement.

### 9.4 Input preservation and target contract

Preserve `A` and `B` exactly. Do not overwrite the initial seed state if it
is part of the public interface; otherwise keep it in retained history.
Accumulate the selected terminal state into fixed-width targets:

```text
T_j' = T_j XOR F_j(A,B)
```

for every declared output component `F_j`. Target widths and the meaning
of each terminal component must be specified exactly before implementation.
For an abstract reference interface, `F` may be the full terminal EEA
state window `(r_prev,r_cur,s_prev,s_cur,t_prev,t_cur)`, padded to the
chosen role capacities. This is a safe generic specification candidate,
not an established mapping to P008's locator/evaluator outputs.

Targets may contain arbitrary valid initial field coefficients; no target
is assigned or overwritten. Applying the same deterministic input-preserving
XOR relation twice restores the original targets.

### 9.5 Workspace and cleanup

For an auditable bounded classical model:

1. Initialize every scratch, history, pointer, and control register to its
   declared value.
2. Compute each round into a fresh state bank; preserve prior state banks
   until they are no longer needed for reversal.
3. Retain each quotient, or recompute it only through a separately verified
   inverse-safe schedule.
4. Accumulate terminal outputs into caller targets only after the terminal
   state has been validated.
5. Reverse rounds in reverse order, reversing each product/add/division
   dependency in reverse order.
6. Verify all scratch, quotient history, inactive-round flags, and temporary
   degree pointers equal their declared initial values. Do not clear
   computed scratch by assignment.

This defines a classical register-state compute/accumulate/uncompute
obligation. It does not prove a circuit permutation, quantum coherence,
phase behavior, or gate-level uncomputation.

## 10. Independent validation and future test requirements

### Independent mathematical oracle

Use test-local GF(2^k) multiplication and inversion with separately
declared irreducible moduli, then normalized-list polynomial arithmetic and
classically structured long division. Expected iterative EEA states must
not call P009-P013 production functions. Document the shared mathematical
field modulus and polynomial-basis assumption for GF(2^12).

For every round, independently verify:

- `r_prev = q*r_cur + r_next`;
- `r_next=0` or `deg(r_next)<deg(r_cur)`;
- both Bézout identities `r_i=s_i*A+t_i*B`;
- quotient/remainder, both coefficient updates, and exact target XORs;
- unchanged input operands and no output overflow;
- threshold/zero termination and fixed-round no-op behavior;
- second application restores arbitrary tested target values; and
- each forward/reverse step returns all scratch/history to its initial
  state.

### Exhaustive small-field plan

Declare field degrees, irreducible moduli, fixed coefficient widths,
nonzero-divisor restrictions, threshold, valid initial coefficient state,
target seeding, and whether scratch values are enumerated or only checked.
Enumerate every valid bounded `(A,B)` pair for the selected small widths and
every EEA step up to the exact derived round bound. If Bézout input states
are fixed to the conventional initialization, call this exhaustive over
that initialized EEA domain—not exhaustive over arbitrary six P013 inputs.
If targets are selected rather than fully enumerated, publish the exact
target samples and do not claim full-register-state enumeration.

Include cases with equal and unequal degrees, nonmonic divisors, trailing
zero padding, exact division, degree-one drops, threshold reached at the
last allowed round, already-below-threshold input, and zero remainder
termination. Handle the excluded initial `B=0` case with explicit
rejection/branch tests once its contract is approved.

### Deterministic GF(2^12) production checks

Cover P008-shaped maximum widths, `A=z^70`, syndrome degrees from zero
through 69, nonmonic leading coefficients, trailing zero slots, every
termination branch, maximal bounded round count, all derived capacity
boundaries, and an intentionally invalid state that would overflow under
the proposed valid-state invariant. Assert that rejection happens before
target mutation. These are deterministic examples, not exhaustive
GF(2^12) coverage.

### Reversibility evidence boundary

Tested classical identities, involution of XOR targets, and zeroed Python
scratch establish only the stated register-model behavior. A later quantum
implementation would separately need a total reversible map on the full
declared basis, reversible degree/termination control, phase correctness,
and a gate-level cleanup proof.

## 11. Unresolved assumptions and exclusions

The following must remain unresolved until supported by additional
evidence or a separately approved implementation decision:

1. Whether P008's two shared arrays and five degree pointers can realize the
   proposed mathematical role capacities and full reverse schedule.
2. The exact polynomial-to-array alias map, quotient storage positions,
   pointer encodings, and relationship of the reported 222 circuit steps to
   any locally defined iteration count.
3. Whether a future implementation should use P012's 71-slot quotient
   target or a new 36-slot threshold-specific quotient target.
4. The exact terminal coefficient that becomes the paper's locator or
   evaluator, and any required normalization.
5. The DQI behavior when the syndrome polynomial is zero.
6. A total off-promise extension and quantum gate decomposition.
7. Official verifier compatibility and competition readiness.

Do not implement Chien search, root finding, Forney computation, error
correction, phase correction, a complete decoder, quantum circuits, or P015
as part of the future bounded iterative contract without separate scope.

## 12. Acceptance criteria and execution report

| Criterion | Result |
|---|---|
| P008 and P009-P013 evidence inspected | **PASS** |
| P013 declared-width mismatch identified | **PASS** |
| EEA-valid-state degree bounds derived separately from arbitrary P013 states | **PASS** |
| Remainder, quotient, Bézout, product, division-scratch, and history capacities stated | **PASS**, with API/circuit boundaries identified |
| Capacity architectures compared with explicit sizing rationale | **PASS** |
| Fixed-width bounded transition and termination contract specified | **PASS** |
| P008 71-/up-to-70-slot operands compared to current limits | **PASS** |
| Unsupported paper requirements and unresolved assumptions labeled | **PASS** |
| Independent oracle and future testing criteria specified | **PASS** |
| Source/test code or dependencies modified | **NO** |
| P015 started | **NO** |

Only the authorized P014 specification was created:

- `docs/research/DQI_P014_EEA_STATE_CAPACITY_AND_ITERATION_CONTRACT.md`

Files modified: none. Files deleted: none. No tests were run because this
is a documentation-only specification task and no implementation changed.
The new report has no trailing whitespace. `git diff --check` reports only
the pre-existing README BOM/line-ending diff; it was not edited. Final
repository state remains on `feat/dqi-decoder` at
`5391b2e7123484efacffc0588f5e761e67b5cb55`, with no staged paths,
`README.md` as the only tracked modification, and 84 untracked paths
including this new report. The README change and all pre-existing untracked
DQI/INVSQRT paths were preserved. The recommendation is a bounded,
degree-aware classical reference-model contract; paper-parameter
implementation and circuit-level readiness remain
**UNRESOLVED / NOT ESTABLISHED**.
