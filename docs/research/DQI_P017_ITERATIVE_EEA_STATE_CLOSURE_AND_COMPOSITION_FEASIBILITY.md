# DQI-P017 — Iterative EEA State Closure and Composition Feasibility

## 1. Executive result

**P017 result: PASS for a bounded mathematical/classical composition
architecture; direct composition of the P016 API is not closed.**

The P016 raw Bézout output targets (up to 105 `s2` slots and 106 `t2`
slots) do not fit its 35/36-slot next-step coefficient inputs. Calling the
same P016 API repeatedly with those raw output tuples is therefore rejected
and is not a valid composition.

The mismatch can be resolved without ordinary trimming or discarding
information, but only on the standard initialized, thresholded EEA domain
covered by P014's degree invariants. Compute P016 outputs into zeroed
full-width scratch targets; use the invariant to establish that the high
`s2` and `t2` coefficients are zero; XOR-copy only the low 35/36 slots into
a fresh next-state bank while retaining the full source outputs; then apply
the same P016 XOR relation again to clear its full-width output scratch.
The low-width next-state coefficients remain, and the zero high region is
not lost. This is a reversible bounded-window transfer, not unproved
normalization.

The resulting proposed state uses remainder capacities 71/70, `s`
capacities 35/35, and `t` capacities 36/36. It supports at most 35
threshold-active rounds for the P008-shaped nonzero-syndrome domain
(`A=z^70`, `deg(S)<=69`, threshold 35). Prior state banks must be retained
or otherwise reversibly reconstructible. This architecture is not
implemented in P016, does not verify its invariant at runtime, and does not
establish P008's shared-array circuit schedule. Thus the PASS is a
feasibility result and proposed register model, **not** implementation or
P008 compatibility certification.

## 2. Scope, evidence, and exact artifacts inspected

This was a specification and source-audit task. The following live files
were inspected:

- `docs/research/DQI_P014_EEA_STATE_CAPACITY_AND_ITERATION_CONTRACT.md`
- `docs/research/DQI_P015_CAPACITY_GENERALIZED_REVERSIBLE_DIVISION_REPORT.md`
- `docs/research/DQI_P016_CAPACITY_GENERALIZED_REVERSIBLE_EEA_SINGLE_STEP_REPORT.md`
- `src/dqi_decoder/reversible_division.py`
- `tests/dqi_decoder/test_reversible_division.py`
- `src/dqi_decoder/reversible_eea.py`
- `tests/dqi_decoder/test_reversible_eea.py`
- `src/dqi_decoder/reversible_primitives.py` and
  `docs/research/DQI_P009_REVERSIBLE_FINITE_FIELD_PRIMITIVES_REPORT.md`
- `src/dqi_decoder/reversible_polynomial.py` and
  `docs/research/DQI_P010_REVERSIBLE_POLYNOMIAL_ARITHMETIC_REPORT.md`
- `src/dqi_decoder/reversible_evaluation.py` and
  `docs/research/DQI_P011_REVERSIBLE_POLYNOMIAL_EVALUATION_REPORT.md`
- `src/dqi_decoder/field.py`
- `docs/research/DQI_P008_REVERSIBLE_DECODER_SPECIFICATION.md`
- `docs/research/DQI_P012_P013_HANDOFF.md`
- `docs/research/DQI_P013_P014_HANDOFF.md`
- `docs/research/DQI_P013_REVERSIBLE_EEA_FOUNDATION_REPORT.md`
- `src/dqi_decoder/polynomial.py` for the canonical versus fixed-width
  representation distinction

No P017 tests or program code were run. No source or test was edited.

## 3. Repository baseline and preservation

| Item | Audit start | Final |
|---|---|---|
| Root | `/mnt/d/PROJECT/Quantum_AI/Google-Quantum-AI` | unchanged |
| Branch | `feat/dqi-decoder` | `feat/dqi-decoder` |
| HEAD | `5391b2e7123484efacffc0588f5e761e67b5cb55` | unchanged |
| Staged paths | 0 | 0 |
| Tracked modifications | Existing `README.md` only | unchanged |
| Untracked paths | 86 | 87, adding this report |

The pre-existing README SHA-256 is
`6fc9e83d0fb74d8f163fbd1c0fb0d0da246bd33e218e86ee56bd78ec15379027`;
it is unchanged. P001–P016 artifacts and INVSQRT work were preserved. No
dependencies, branches, commits, or other worktree files were changed.
Only the authorized P017 report was created.

## 4. Representation and current implementation facts

The repository field is GF(2^12), with polynomial-basis field elements in
`[0,4095]` and modulus `0x1053`. Coefficient addition is XOR. Polynomial
tuples are low-degree first; index zero is the constant coefficient.
Reversible register APIs use nonempty fixed-width tuples; all-zero tuples
represent zero and trailing high zeroes are retained. The classical
polynomial module instead normalizes high zeroes and uses `()` for zero.

Relevant current APIs and behavior:

- P015 division accepts dividend width at most 71 and divisor width at most
  70. It requires a nonzero divisor, returns a quotient target exactly the
  dividend's declared width, and uses a remainder target of
  `max(1, len(divisor)-1)`. It preserves inputs and XOR-accumulates results.
- P010 polynomial multiplication requires the **full declared-width**
  target `len(left)+len(right)-1`; it neither trims nor truncates.
- P016 `xor_accumulate_capacity_aware_eea_transition` accepts `r0<=71`,
  `r1<=70`, `s0/s1<=35`, and `t0/t1<=36`. Its target formulas yield
  `q=len(r0)`, `r2=max(1,len(r1)-1)`,
  `s2=max(len(s0),len(r0)+len(s1)-1)`, and
  `t2=max(len(t0),len(r0)+len(t1)-1)`. The function accepts arbitrary
  inputs within these capacities; it does not enforce the conventional
  EEA initialization, threshold, degree order, or Bézout invariant.
- P016 computes and checks one transition, returns its four full-width
  target tuples, reverses its own local modeled scratch, and checks that
  scratch is zero. It has no controller or inter-round state transfer.
- P009/P010/P011 expose classical target-XOR relations. P011 polynomial
  evaluation is not a polynomial normalization or EEA state-transfer API.

P014 is a mathematical capacity analysis, not a capacity-aware
multiplication API. P015/P016 implement the larger single-step input
widths, but P016's raw Bézout outputs retain P010's full convolution widths.

## 5. EEA state, recurrence, and domain

Use the conventional state:

```text
(r[-1], r[0], s[-1], s[0], t[-1], t[0])
  = (A, B, 1, 0, 0, 1)

r[i] = s[i]*A + t[i]*B
```

For an active state `(r[k-1],r[k],s[k-1],s[k],t[k-1],t[k])`, require
`r[k] != 0` and compute:

```text
r[k-1] = q[k]*r[k] + r[k+1]
r[k+1] = 0 or deg(r[k+1]) < deg(r[k])
s[k+1] = s[k-1] + q[k]*s[k]
t[k+1] = t[k-1] + q[k]*t[k]
```

The next mathematical state is
`(r[k],r[k+1],s[k],s[k+1],t[k],t[k+1])`. Addition is in characteristic
two. Do not silently swap `A,B`; the initial Bézout coefficients are tied
to their order.

For this report's bounded P008-shaped domain:

- `A=z^70`, so `m=70`, `A` uses 71 coefficients, and `A` is nonzero.
- `B=S(z)` is nonzero, has `n=deg(B)<=69`, and is represented in at most
  70 coefficients. Zero `B` is excluded from this EEA core; its DQI
  zero-syndrome output branch remains unresolved.
- Stop when the current divisor is zero or its degree is below
  `ell=35`. A zero remainder produced by a step is terminal and must not be
  supplied as the next divisor.
- If `deg(B)<35`, the state is already terminal and executes zero
  divisions.

## 6. Per-register and per-round capacity derivation

Let `d=deg(r[k])` be the active divisor degree and `p=deg(r[k-1])`.
On an active threshold round, `35<=d<p<=70`. Polynomial division gives:

```text
deg(q[k]) = p-d <= 70-35 = 35
```

Thus quotient *significant support* is at most 36 coefficients. P015's
quotient register nevertheless has 71 declared slots when `r0` is
71-slots wide; its coefficients above the mathematical quotient degree are
zero padding.

P014's standard-initialization invariant yields, for the coefficient
updates made at this active divisor:

```text
deg(s[k+1]) <= n-d <= 69-35 = 34  -> at most 35 slots
deg(t[k+1]) <= m-d <= 70-35 = 35  -> at most 36 slots
```

These are bounds on meaningful support for invariant-valid EEA states, not
on the full P010 target buffers. The same capacities cover coefficient
state carried into any later active round. The proof does not cover
arbitrary six-tuples accepted by P016.

| State/output role | Allocated width in proposed state | Mathematical significant-support bound | Transition/API width |
|---|---:|---:|---:|
| `r0` dividend | 71 | at most 71 | P015 dividend max 71 |
| `r1` divisor | 70 | at most 70 | P015 divisor max 70 |
| `q` | 71 scratch slots | at most 36 on active threshold rounds | P015 target is `len(r0)` |
| `r2` | 69 target slots when `r1` is stored at width 70 | at most 69; degree `<deg(r1)` | P015 rule `max(1,len(r1)-1)` |
| `s0`, `s1`, `s2` compact state | 35 each | at most 35 for threshold-valid states | P016 inputs accept 35; P016 raw `s2` target is 105 |
| `t0`, `t1`, `t2` compact state | 36 each | at most 36 for threshold-valid states | P016 inputs accept 36; P016 raw `t2` target is 106 |
| `q*r1` reconstruction product | 140 scratch slots for declared widths 71 and 70 | at most 71 by `q*r1=r0-r2` | P010 requires full 140-slot product |
| `q*s1` product | 105 scratch slots | at most 35 under P014 invariant | P010 requires full 105-slot product |
| `q*t1` product | 106 scratch slots | at most 36 under P014 invariant | P010 requires full 106-slot product |

For `q*r1`, the full raw convolution size is `71+70-1=140`; P014's
comparison uses 141 when both operands are declared 71 slots. In the valid
division result, `q*r1=r0-r2` has support within the 71-slot remainder
capacity. The full 140 slots remain necessary scratch for the current P010
API. Similarly, current P016 target widths are 105/106 even though P014
proves that valid state outputs have support within 35/36 slots.

### Remainder round closure

Use fixed physical/logical role widths:

```text
r0 bank: 71 slots
r1 bank: 70 slots
```

Initialize `r0` from `A` and pad `S` to 70 slots for `r1`. After each
transition, copy old `r1` into a fresh 71-slot next `r0`; copy the 69-slot
`r2` target into a fresh 70-slot next `r1`, padding its final slot with
zero. This is sufficient because if the divisor's declared width is `b`,
its effective degree is at most `b-1`, and a nonzero remainder has degree
strictly below that; therefore it fits `max(1,b-1)` slots.

No quotient, remainder, or input coefficient is discarded. P015's exact
target-width rule is honored each round, and padded remainder state remains
within the P015 divisor limit.

### Round count and final state

Remainder degrees strictly decrease. Starting from `n<=69`, active divisors
can have degrees `69,68,...,35`; there are at most
`max(0,n-35+1)<=35` divisions. The 35-round limit is valid only for the
thresholded domain. It is not a bound for a full Euclidean run to zero,
which may include active divisors below degree 35.

At termination, retain the current six-role state with the same capacities.
The mathematical terminal predicate is `r1=0` or `deg(r1)<35`. A terminal
output selection or normalization for locator/evaluator use is not
established by P008/P014 and is not specified here. An initial zero
syndrome needs a separately defined branch rather than division by zero.

## 7. P016 output/input mismatch and reversible closure protocol

### Direct composition is disproven

At maximum declared P016 input widths:

```text
len(s2_target) = max(35, 71+35-1) = 105
len(t2_target) = max(36, 71+36-1) = 106
```

Those raw result tuples exceed next-step coefficient input capacities 35
and 36. Passing them directly is invalid. The fact that high coefficients
are zero on the standard EEA domain does not make the API's fixed-width
tuples shorter. Direct repeated P016 calls are therefore **not** closed.

### Reversible bounded-window transfer that closes the valid domain

For a valid initialized state and an active threshold round, the following
is a reversible register-level composition design:

1. Keep the entire old six-register state bank unchanged.
2. Invoke P016 with zeroed output targets of exact widths `71`, `69`,
   `105`, and `106`.
3. Use the P014 invariant proof to establish that output `s2` slots
   `[35:105]` and `t2` slots `[36:106]` are zero. This fact is a
   precondition/theorem for the promised state domain, not an assumption
   that may be applied to arbitrary P016 inputs.
4. XOR-copy the necessary outputs into a fresh fixed-width next state:
   - `old r1` padded to next `r0` width 71;
   - `r2` padded from 69 to next `r1` width 70;
   - `old s1` to next `s0` width 35 and low 35 slots of `s2` to next
     `s1` width 35;
   - `old t1` to next `t0` width 36 and low 36 slots of `t2` to next
     `t1` width 36.
5. Keep the P016 output scratch intact while making the copies. Then invoke
   the same input-preserving P016 XOR relation again with the same old
   inputs and the now-populated output targets. Since the relation XORs
   the same deterministic outputs, all four wide P016 targets return to
   zero. The compact next-state bank remains.
6. Preserve the old bank as history. For reverse cleanup, recompute P016
   from that old bank, XOR-copy the same values out of the next bank, then
   invoke P016 again to clear its output scratch.

The operation on compact next-state targets is not ordinary destructive
trimming. The full result remains available until copied; the omitted
coefficients are proven zero on the declared valid-state domain; the wide
source is then uncomputed from the still-preserved inputs. The XOR copies
are self-inverse. This yields a bounded mathematical reversible embedding
and avoids carrying 105/106-slot coefficient arrays into the next round.

The transfer currently exists only as a specification. P016 does not
provide an invariant-restricted compact-output API, output-window helper,
or a controller that enforces the valid-state preconditions.

## 8. Multi-round state capacity and workspace

One proposed fixed-capacity state bank contains:

```text
71 + 70 + 35 + 35 + 36 + 36 = 283 field-element slots.
```

Retaining the initial bank and one bank per each of at most 35 rounds
requires `36*283 = 10,188` state coefficient slots. This uses the
role-specific P015 divisor width of 70. P014's earlier conservative
illustration used two 71-slot remainder arrays and counted 284 slots per
bank (`10,224` across 36 banks); this report specializes that count to
P015/P016's actual 71/70 roles.

The bank count excludes termination/degree metadata and reusable
arithmetic scratch. P016's own scratch tuple has a maximum of 842 slots for
the declared maximum input widths (products/reconstruction included).
P015 division uses additional scratch; with a 71-slot dividend and
effective divisor degree at least 35, its source-shaped upper bound is
`37*(71+71+1)=5,291` field-element slots. These are Python modeled
field-element counts, not qubits or P008 resource counts.

This history-bank architecture can avoid persistent quotient history by
retaining prior state banks and recomputing the same P016 outputs during
reverse traversal. That is a model-level option, not a proven optimal
schedule. A fixed 35-round controller must represent active/terminal
control so later rounds are reversible no-ops; it cannot erase the
branch/round information by ordinary early exit.

## 9. Alternatives A–E

| Alternative | Mathematical assumptions and capacities | Reversibility and compatibility | Complexity and proof obligations | Assessment |
|---|---|---|---|---|
| **A. Round-specific capacities** | Use `deg(q)=deg(r_prev)-deg(r_cur)`, `deg(s_next)<=n-deg(r_cur)`, and `deg(t_next)<=m-deg(r_cur)`. At active threshold 35, maxima are q support 36, s 35, t 36; remainders fit 71/70 roles. | Compatible with P014 valid-state bounds. P016 still returns a 71-slot quotient and 105/106-slot Bézout targets; use the reversible bounded-window protocol above. | Needs degree metadata or an invariant proof for each round, full-width temporary products, overflow proof, retained old state and inverse traversal. | **Recommended as the capacity policy**, with fixed maximum banks and proven windows. |
| **B. Significant-support representation** | Store degree/support separately from allocated coefficients; logical coefficient values have at most 35/36 support on valid threshold states. | Ordinary `trim()` is many-to-one over arbitrary fixed-width registers and is not reversible. A known-zero window can be copied into a compact next bank only while the wide source and old inputs remain available, then uncomputed. | Must prove high coefficients zero for every allowed initialized state and every active round; handle zero polynomials and terminal states. | **Useful metadata, not a standalone reversible solution.** |
| **C. Reversible bounded normalization** | Keep a full-width temporary output, prove high slots zero on the promised EEA subdomain, XOR-copy the low fixed window, then uncompute the original wide output. | Reversible because the source is preserved through copy and erased by applying the P016 XOR map again. Not valid for arbitrary P016 inputs or nonzero high output targets. | Requires zero-initialized scratch targets, unchanged old state, an invariant-restricted theorem, and a complete inverse trace. Runtime rejection is only a classical guard, not a circuit proof. | **Feasible and chosen transfer mechanism**, not implemented. |
| **D. Conservative uniform capacities** | Without EEA invariant constraints, a P016-like 71-slot quotient and coefficient width `C` can produce `C' = max(C,71+C-1)=C+70`. From `C0=1`, 35 rounds require 2,451 coefficient slots; from P016 maxima, bounds are 2,485 for `s` and 2,486 for `t`. | No trimming or correlated degree assumption is needed if every full product is retained. Current P016 does not accept such widths; a new wide API would be required. | Finite but storage- and arithmetic-heavy, with much larger state banks and full product scratch. Not comparable to P008's two shared arrays without an explicit allocation proof. | **Mathematically conservative but not selected.** |
| **E. Alternative reversible state encoding** | Fixed 71/70/35/36 coefficient banks plus degree/control metadata and an explicit historical bank stack. Quotient need not persist if recomputed from retained old states in reverse. | Preserves prior states; compact windows are valid only under the P014 invariant. A reversible stage transfer must retain old inputs and all control information. | Requires an explicit encoding for degree, active/terminal flags, state-bank routing, and reverse schedule. P008's actual alias map is unavailable. | **Recommended reference-model encoding**, not evidence of P008's shared-array implementation. |

## 10. Composition feasibility argument and remaining gap

### Mathematical/capacity closure argument

Assume the bounded initial domain in §5 and standard EEA initialization.
Inductively, at each active round:

1. Remainder degrees strictly decrease, so `r2` fits the P015 remainder
   target and the next 70-slot divisor bank.
2. `r0` and `r1` remain within the 71/70 P015 operand limits after the
   specified padding.
3. Because the current divisor degree is at least 35, the quotient's
   significant support is at most 36, although its P015 tuple has width 71.
4. P014's coefficient invariant bounds the next `s` and `t` values by
   35/36 slots. The reversible bounded-window transfer copies those values
   into exactly those capacities and clears the full-width P016 target
   scratch without discarding high information.
5. The same bounds apply to the next active state. If the remainder is zero
   or below threshold, the controller terminates instead of calling P016
   with a zero or inactive divisor.
6. Strict degree descent gives at most 35 active transitions.

Thus every **compact transferred** state fits the next P016 input
capacities, every product is first represented at its full required P010
width, and no coefficient is silently truncated. The output/input mismatch
is resolved for this restricted composition architecture, but not by
repeated direct use of P016's raw tuples.

### Reversibility of composition

Each P016 map preserves its six inputs and XORs fixed outputs into targets;
it is its own inverse for fixed inputs. XOR-copy into a fresh next bank is
also self-inverse. Retaining each prior state bank allows the reverse pass
to recompute the P016 outputs, clear the next bank, and uncompute the
temporary outputs. Internal P016/P015 scratch is checked/cleared within
each modeled invocation.

This is a reversible relation/state-history design at the mathematical and
classical register-model level. Degree-dependent round selection, fixed
schedule control, P008 degree pointers, circuit-level phase preservation,
and physical gate uncomputation still require implementation and proof.

### Exact missing lemmas and assumptions

The composition proof depends on P014's standard initialized EEA
invariants. It does **not** apply to every arbitrary six-tuple accepted by
P016. Before implementation, the independent proof/test gate must establish:

- the coefficient degree bounds for every active round under the exact
  initialization, ordered degrees, and threshold;
- the full polynomial division reconstruction and remainder-degree bound
  for the declared padded registers;
- the invariant that all coefficients above positions 34 in `s2` and 35
  in `t2` are zero on every active promised state;
- the zero-syndrome branch and terminal output convention if P008 requires
  them;
- a reversible encoding/update of degree, round, and no-op control;
- an inverse schedule for state-bank copies and terminal target
  accumulation;
- the relation between the generic terminal EEA state and P008's
  locator/evaluator output convention.

The first three are mathematical obligations that can be proved and
independently tested on the restricted state domain. The latter four are
not established by the current P008 specification or P016 implementation.

## 11. Independent mathematical validation plan

No tests or code were executed in P017. The following is a **proposed**
validation plan, not completed evidence.

### Independent reference

Use test-local finite-field carryless multiplication/reduction, inverse by
exponentiation, normalized-list polynomial multiplication, and independent
leading-term long division. Initialize `(A,B,1,0,0,1)` and run a classical
reference EEA controller with independently computed degree and terminal
state. Do not call P016 for expected values.

After every round, independently check:

- `r_prev = q*r_cur + r_next`;
- `r_next=0` or `deg(r_next)<deg(r_cur)`;
- both Bézout recurrences;
- `r_i = s_i*A + t_i*B`;
- quotient/remainder/product significant support and allocated-width fit;
- high-zero windows required by bounded transfer;
- exact next-bank padding, state-copy reversibility, and reverse clearing;
- termination flag and round limit;
- no zero divisor call.

### Exhaustive small-field domain proposal

For each `q=4,8,16` (GF(2²), GF(2³), GF(2⁴)), enumerate all two-slot
coefficient tuples `A,B` where `A!=0`, `B!=0`, and `deg(A)>=deg(B)`.
Use conventional Bézout initialization, run full classical EEA to zero
and separately apply a threshold of one for the bounded-stop variant.
The exact initial-pair count is:

```text
count(q) = (q-1)(q^3-1)
```

| Field | q | Exhaustive ordered nonzero `(A,B)` pairs |
|---|---:|---:|
| GF(2²) | 4 | 189 |
| GF(2³) | 8 | 3,577 |
| GF(2⁴) | 16 | 61,425 |
| **Total** | — | **65,191** |

This is exhaustive over the stated input-pair domain only. Bézout target
initial values, scratch states, capacity encodings, and arbitrary
nonstandard EEA tuples would not be exhaustively enumerated by this plan.
Additional selected nonzero target seeds should check XOR accumulation and
repeated application.

### Deterministic GF(2^12) proposal

Test the exact maximum P008 input widths (`A` 71 slots, `S` 70 slots),
including effective degrees 69, 35, and 34; nonmonic leading coefficients;
dense/sparse operands; retained leading zero padding; and a generated
degree-decrease staircase reaching the 35-round bound. For each executed
round, compare against the independent oracle, inspect every output
capacity, and verify compact-window high-zero conditions. Separately test
`S=0` as a rejected/unresolved branch and ensure no division is invoked.
These are deterministic GF(2^12) vectors, not exhaustive field coverage.

## 12. P008 compatibility matrix

| P008 requirement | Classification | Evidence / gap |
|---|---|---|
| `z^70` 71-slot dividend and up-to-70-slot nonzero syndrome divisor for a single step | **SUPPORTED BY CURRENT MODEL** | P015 division and P016 role limits accept these widths. |
| Quotient significant support at most 36 on an active degree-35 threshold round | **MATHEMATICALLY JUSTIFIED BUT NOT IMPLEMENTED** | Follows `deg(q)=deg(r_prev)-deg(r_cur)` and valid operand degrees. P015 still returns a 71-slot quotient target. |
| Remainder degree decrease and 71/70 role state | **SUPPORTED BY CURRENT MODEL** | P015 full division handles declared capacities; multi-round fixed-bank transfer is proposed, not implemented. |
| Bézout significant capacities 35/36 under standard initialization | **MATHEMATICALLY JUSTIFIED BUT NOT IMPLEMENTED** | P014 invariant bounds; P016 accepts these input capacities but emits 105/106-slot raw outputs. |
| Full-width `q*s`/`q*t` outputs | **SUPPORTED BY CURRENT MODEL** | P016/P010 compute exact 105/106-slot targets without truncation. Compact bounded-window transfer is not implemented. |
| At most 35 thresholded divisions | **MATHEMATICALLY JUSTIFIED BUT NOT IMPLEMENTED** | Strict degree descent from `deg(S)<=69` to below 35. No controller exists. |
| Zero-syndrome behavior, terminal locator/evaluator selection or normalization | **REQUIRES ADDITIONAL PROOF** | P008/P014 do not establish this local output convention. |
| Prior-state retention, degree pointers, fixed schedule, and complete EEA cleanup | **REQUIRES ADDITIONAL PROOF** | P016 cleans per-call Python scratch only. No composed schedule or circuit trace exists. |
| P008 two shared arrays of 73 field registers, quotient storage, pointer schedule, and reported 222 synchronized steps | **REQUIRES ADDITIONAL PROOF** | Capacity arithmetic does not supply a local alias map, allocation, or schedule equivalence. |
| Official verifier schema, wire serialization, and accepted circuit artifact | **BLOCKED BY MISSING OFFICIAL ARTIFACT** | P008 and P012/P013 handoffs record these artifacts/contracts as unavailable or unresolved. |
| Gate-level quantum reversibility and phase-preserving uncomputation | **REQUIRES ADDITIONAL PROOF** | Current source is a classical Python register model only. |

No full P008 compatibility claim follows from the mathematical closure
argument.

## 13. Reversibility, test boundary, and final disposition

The exact P016 function is reversible as an input-preserving XOR-target
relation for each fixed input state. Its raw outputs are not a closed
iterative state representation. The proposed composition adds fresh state
banks, preserves old banks, copies only invariant-proven support into
fixed-width next banks, and uncomputes full-width outputs. This avoids
irreversible trimming. A multi-round controller must also retain or
recompute enough active/termination and degree information to reverse every
round; a classical variable-length loop alone does not establish that.

The test counts in §11 are planned counts, not executed results. No test,
build, static analyzer, or implementation code was run. No implementation
or test files were modified.

**Final result: PASS for the stated composition-feasibility architecture
over nonzero, conventionally initialized P008-shaped EEA states under the
P014 threshold invariants.** Direct P016 output chaining is rejected. The
architecture remains a proposal requiring independent implementation
verification and circuit-level proof.

P017 is complete. P018 has not been started.
