# DQI-P011 Post-Execution Audit and P012 Handoff

- **Project:** Google Quantum AI — Verifiable Quantum Circuit Compilation
- **Workstream:** DQI Decoder
- **Phase:** 01 — P011 audit / P012 handoff
- **Audit date:** 2026-11-20
- **Repository root:** `/mnt/d/PROJECT/Quantum_AI/Google-Quantum-AI`
- **Branch:** `feat/dqi-decoder`
- **HEAD:** `5391b2e7123484efacffc0588f5e761e67b5cb55`
- **Disposition:** **PASS — P011 audit passes; mathematical prerequisites for a bounded P012 research model are established.**

## 1. Executive summary

P011 implements an input-preserving polynomial evaluation transformation
over the repository's GF(2^12):

```text
(A, x, T) -> (A, x, T XOR A(x))
```

The implementation accepts a nonempty, low-degree-first coefficient tuple,
a field element `x`, and a one-element tuple target. It computes a Horner
value in dedicated scratch registers using P009's target-XOR addition and
multiplication relations, XOR-accumulates the final value into the caller's
target, and applies the same scratch updates in reverse to restore all
scratch values to zero. The public function checks this cleanup condition.
No material correctness defect was found in the audited source or reproduced
test evidence.

The P011 test's stated **69,888 states** reproduces exactly:
`4^4 + 8^4 + 16^4 = 256 + 4,096 + 65,536`. This is full state enumeration
for two coefficient slots, one point, and one target over each small field.
The enumerated transformation and scratch model are test-local small-field
reference logic; they are not executions of the GF(2^12) production
implementation. Production-field coverage consists of 10 deterministic
value vectors, not exhaustive enumeration.

P012 may use the existing classical division function as a mathematical
behavior reference, but must design its own fixed-width reversible register
contract. The current classical division function normalizes variable-width
polynomials and raises on a zero divisor. It does not provide retained
inputs, XOR-target outputs, a reversible division model, or scratch cleanup.
P012 must not assume these properties carry over automatically.

No P012 implementation was started.

## 2. Repository baseline

| Item | Audit start | Final |
|---|---|---|
| Root | `/mnt/d/PROJECT/Quantum_AI/Google-Quantum-AI` | unchanged |
| Branch | `feat/dqi-decoder` | unchanged |
| HEAD | `5391b2e7123484efacffc0588f5e761e67b5cb55` | unchanged |
| Staged paths | 0 | 0 |
| Tracked unstaged paths | `README.md` only | `README.md` only |
| Existing untracked paths | 59 | 60, including this handoff |

The pre-existing README diff remains a line-ending conversion. Its content
was not edited or reverted. Existing untracked DQI artifacts, classical
implementation/tests, INVSQRT bytecode work, and unrelated work were left
untouched. No branch change, commit, push, reset, clean, merge, or deletion
occurred.

### 2.1 P001–P011 artifact inventory

Present at audit:

- Research reports: P001, P002, P003, P004, P005 core, P005 gap-closure,
  P006, P007, P008, P009, P010, P010–P011 handoff, and P011.
- DQI source: package initializer, field, classical polynomial,
  reversible primitives, reversible polynomial, reversible evaluation,
  syndrome, and decoder modules.
- DQI tests: field, polynomial, reversible primitives, reversible
  polynomial, reversible evaluation, syndrome, and decoder test modules.
- Existing unrelated INVSQRT bytecode paths remained present.

The report inventory has 13 research markdown files because P005 has two
reports and both P010 reports (arithmetic and P010–P011 handoff) are present
in addition to P001–P011 phase reports.

## 3. Files inspected

Read directly during this audit:

- `src/dqi_decoder/reversible_evaluation.py`
- `tests/dqi_decoder/test_reversible_evaluation.py`
- `docs/research/DQI_P011_REVERSIBLE_POLYNOMIAL_EVALUATION_REPORT.md`
- `src/dqi_decoder/reversible_polynomial.py`
- `src/dqi_decoder/reversible_primitives.py`
- `src/dqi_decoder/field.py`
- `src/dqi_decoder/polynomial.py`
- `docs/research/DQI_P010_P011_HANDOFF.md`
- `docs/research/DQI_P008_REVERSIBLE_DECODER_SPECIFICATION.md`
- `docs/research/DQI_P009_REVERSIBLE_FINITE_FIELD_PRIMITIVES_REPORT.md`
- `docs/research/DQI_P010_REVERSIBLE_POLYNOMIAL_ARITHMETIC_REPORT.md`

Repository state and P001–P011 artifact availability were also inspected.
P011 source/tests and pre-existing tracked/untracked material were
fingerprinted before running tests.

## 4. P011 implementation and API inventory

### 4.1 P011 artifacts

| Path | Role |
|---|---|
| `src/dqi_decoder/reversible_evaluation.py` | Evaluation relation, input validation, Horner scratch computation and reverse cleanup |
| `tests/dqi_decoder/test_reversible_evaluation.py` | Independent power-sum oracle, bounded small-field enumeration, production vectors, validation tests |
| `docs/research/DQI_P011_REVERSIBLE_POLYNOMIAL_EVALUATION_REPORT.md` | P011 implementation and evidence report |

### 4.2 Exact public signature

The inspected runtime signature and annotations are:

```python
PolynomialRegister = tuple[int, ...]
EvaluationTarget = tuple[int]

def xor_accumulate_polynomial_evaluation(
    polynomial: tuple[int, ...],
    point: int,
    target: tuple[int],
) -> tuple[tuple[int, ...], int, tuple[int]]: ...
```

The function is exposed from `dqi_decoder.reversible_evaluation`; the
package initializer was not changed. Its actual implementation returns
validated polynomial values and point unchanged plus a newly constructed
one-element target tuple.

## 5. P011 mathematical and register-contract audit

### 5.1 Representation and field arithmetic

- Polynomial register: exact Python tuple, nonempty, of exact integer
  GF(2^12) elements.
- Coefficient ordering: low-degree first; slot `i` is the coefficient of
  `X^i`; slot 0 is constant.
- Width is the tuple length and is retained even when high slots are zero.
- Zero polynomial is a nonempty all-zero tuple. Empty tuple is rejected.
- Point: one exact integer in `[0, 4095]`.
- Target: exact tuple of length one, containing one field element.
- Field values use `field.py`'s polynomial-basis representation with bit
  `k` the coefficient of `alpha^k`, and modulus `0x1053`.
- Field addition is XOR, not integer addition. Multiplication is the
  repository's GF(2^12) multiplication/reduction operation through P009.

The target width is explicitly checked; invalid field values are rejected
and never silently masked or truncated. No input tuple or point is mutated.
This matches P010's fixed-width coefficient convention and P009's
input-preserving target-XOR primitive semantics.

### 5.2 Horner iteration

The source reverses the coefficient tuple and processes it from
`a_(m-1)` down to `a_0`. It initializes the first accumulator by target-XOR
addition of `a_(m-1)` and zero. Each subsequent coefficient computes:

```text
product = previous_accumulator * x
next_accumulator = product XOR a_i
```

using `xor_accumulate_multiply` and `xor_accumulate_add`. Thus the order and
operations implement:

```text
r = a_(m-1)
r = r * x XOR a_i       for i = m-2,...,0
```

Field addition is characteristic-two XOR. The implementation uses
production P009 primitives; it does not call the test oracle.

Reviewed production test cases include nonempty zero polynomials,
constants, degree-one polynomials, higher-degree polynomials, sparse/dense
coefficient patterns, trailing zero slots, `x=0`, `x=1`, selected nonzero
points, nonzero targets, and maximum field coefficient `0xFFF`. These
cases are compared against a separate power-sum oracle.

### 5.3 Forward, target, and reverse register sequence

For coefficient width `m`, the source initializes `2m` field-valued scratch
slots to zero: a dedicated zero slot, one initial accumulator, and one
product plus one next accumulator for each of the remaining `m-1`
coefficients.

The source-level sequence is:

1. **Forward compute:** XOR the highest coefficient into the initial
   accumulator; then, for each lower coefficient, XOR the previous
   accumulator times `x` into a fresh product slot and XOR that product plus
   the coefficient into a fresh accumulator slot.
2. **Target accumulation:** XOR the final accumulator into the caller's
   target using P009 field addition with the dedicated zero slot.
3. **Reverse uncomputation:** in reverse coefficient order, XOR each
   product-plus-coefficient term back out of its next-accumulator slot, then
   XOR each previous-accumulator-times-point term back out of its product
   slot. Finally XOR the leading coefficient back out of the initial
   accumulator.
4. **Clean-workspace check:** the public function checks all scratch values
   are zero and raises `RuntimeError` if any remain nonzero.

The reverse acts on the exact same XOR-target relations as forward
computation, using preserved inputs and still-live previous accumulators.
It does not clear scratch by direct assignment. Public repeated application
preserves the polynomial and point and XORs the same evaluation into the
target again, restoring the original target.

### 5.4 Evidence categories and limits

- **Reversible classical register relation:** mathematically,
  `(A,x,T) -> (A,x,T XOR A(x))` is an involution for fixed `A,x`.
- **Implementation-level cleanup simulation:** source computes values in
  scratch using P009 relations, reverses those relations, and checks zeros.
  The tests exercise this computation in production for a sample and in a
  separate small-field model for every enumerated state.
- **Mathematical bijection:** preserving `A,x` and XORing a deterministic
  value into `T` makes the map its own inverse on each valid fixed-width
  domain.
- **Quantum circuit/gate-level proof:** **not established**. There is no
  circuit, gate decomposition, phase proof, or quantum ancilla proof.

## 6. Independent oracle audit

`_reference_polynomial_evaluate` computes powers of `x` iteratively from
`x^0=1`, multiplies each coefficient by its power using a test-local
shift/XOR/reduce multiplier, and XORs those terms. It does not call the
production evaluation API, production Horner helper, P009 helpers, or
`field.multiply`. This independent evaluation order can detect coefficient
order and Horner-order defects.

The oracle necessarily shares the specified mathematical field modulus and
integer polynomial-basis encoding (`0x1053` for production GF(2^12)). Its
small-field modulus choices are separately declared and checked for
irreducibility. The power-sum oracle does not independently prove that the
repository's chosen GF(2^12) modulus corresponds to an external
serialization; it tests arithmetic under the repository-established field
contract.

The exhaustive small-field scratch evaluator is another test-local Horner
procedure. It is not the independent expected-value oracle; expected values
come from the power-sum computation.

## 7. Exhaustive enumeration audit

The test loop is over:

```python
product(range(q), repeat=4)
```

with coordinates `(a_0, a_1, x, T)`. Thus it enumerates all `q^2`
coefficient tuples, `q` points, and `q` targets for a polynomial register of
exactly two coefficient slots. The state count is `q^4`.

| Field | `q` | Coefficient tuples | Evaluation points | Target values | Enumerated input states | Forward map evaluations | Repeat-map evaluations |
|---|---:|---:|---:|---:|---:|---:|---:|
| GF(2²) | 4 | 16 | 4 | 4 | 256 | 256 | 256 |
| GF(2³) | 8 | 64 | 8 | 8 | 4,096 | 4,096 | 4,096 |
| GF(2⁴) | 16 | 256 | 16 | 16 | 65,536 | 65,536 | 65,536 |
| **Total** | — | **336** | **28** | **28** | **69,888** | **69,888** | **69,888** |

Here a “forward map evaluation” computes the Horner scratch transform and
target result; the “repeat-map evaluation” applies it again to check target
restoration. For each of the 69,888 first applications, the test also
computes an independent power-sum result, checks inputs are preserved,
checks the XOR target result, checks the first workspace is all zero, and
records the output for uniqueness. The repeated application checks that the
target returns to its prior value. Output uniqueness is checked over the
complete `q^4` domain independently for each field.

**Classification:** exhaustive over all valid input states for the
restricted two-slot polynomial domain in each small field; bounded as to
polynomial width and field size. The map checked is the test-local small
field Horner/reference model, not the production GF(2^12) implementation.
Production GF(2^12) coverage is deterministic and selected, not exhaustive
or randomized.

## 8. Reproduced tests and static checks

Exact commands and observed output:

| Suite | Command | Result |
|---|---|---|
| P011 | `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/dqi_decoder/test_reversible_evaluation.py -q` | **7 passed, 27 subtests, 0 failed, 0 skipped, 0.76s** |
| P010 | `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/dqi_decoder/test_reversible_polynomial.py -q` | **6 passed, 28 subtests, 0 failed, 0 skipped, 0.32s** |
| P009 | `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/dqi_decoder/test_reversible_primitives.py -q` | **9 passed, 33 subtests, 0 failed, 0 skipped, 0.26s** |
| Classical field/polynomial/decoder/syndrome | `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/dqi_decoder/test_field.py tests/dqi_decoder/test_polynomial.py tests/dqi_decoder/test_decoder.py tests/dqi_decoder/test_syndrome.py -q` | **37 passed, 5,411 subtests, 0 failed, 0 skipped, 9.39s** |

No warning summary was emitted. AST parsing passed for the P011 source and
test files. `ruff`, `mypy`, `pylint`, and `pyright` were unavailable; no
dependencies were installed.

## 9. Preservation audit

Baseline and final fingerprints matched for P001–P010 reports, P010/P011
handoff/report artifacts, P009/P010/P011 implementation/test files,
classical field/polynomial/decoder/syndrome source and tests, and README.
All 21 files under `src/invsqrt_opt` had matching path/hash inventory.
The pre-existing untracked paths remained present. The only new path from
this audit is this handoff.

No implementation source or test was edited during this audit. No
dependency, quantum SDK, circuit implementation, EEA, decoder feature, or
other out-of-scope component was introduced. The README line-ending
conversion was preserved.

## 10. P012 proposed scope: reversible polynomial division

### 10.1 Mathematical convention and existing repository behavior

The existing classical `polynomial.divide_polynomials(dividend, divisor)`
uses low-degree-first coefficient sequences and first normalizes both
arguments, removing trailing high-degree zero coefficients. It returns a
canonical `(quotient, remainder)` pair. Its long-division step uses the
inverse of the normalized divisor's nonzero leading coefficient:

```text
factor = leading(remainder) * inverse(leading(divisor))
remainder <- remainder XOR (factor * divisor shifted by degree difference)
quotient[degree difference] = factor
```

All coefficients and operations are over the repository's GF(2^12).
Existing source behavior:

- A zero divisor normalizes to `()`, causing `ZeroDivisionError`.
- Zero dividend by nonzero divisor returns zero quotient and remainder,
  represented canonically as `()` and `()`.
- For nonzero divisor, `dividend = divisor * quotient + remainder`.
- A nonzero remainder satisfies `degree(remainder) < degree(divisor)`.
- Exact division has zero remainder `()`.
- If dividend degree is below divisor degree, quotient is `()` and
  remainder is the normalized dividend.
- For nonzero dividend and nonzero divisor with degrees `dA,dB`, quotient
  degree is at most `max(0,dA-dB)` when a nonzero quotient exists; more
  precisely if `dA >= dB`, `degree(Q) <= dA-dB`; if `dA < dB`, `Q=0`.

This is **repository-implemented classical behavior**, not a reversible
division interface. In particular, P010 fixed-width tuples retain trailing
zero slots while the classical division routine normalizes them away.

### 10.2 Interface and register-layout decisions P012 must make

Do not assume the following design choices without explicitly selecting and
testing them:

1. Whether inputs are P010-style fixed-width nonempty tuples, normalized
   classical sequences, or a separately specified boundary conversion.
2. How mathematical degree is represented when input registers retain
   trailing zeros.
3. Whether quotient and remainder are separate XOR-accumulation targets,
   returned output registers, or another relation. A candidate relation is
   `(A,B,Q_T,R_T) -> (A,B,Q_T XOR Q(A,B), R_T XOR R(A,B))`, but P012 must
   define exact target capacities and zero-padding rules before adopting it.
4. Whether fixed capacities derive from input widths or use other explicit
   caller-provided widths. They must accommodate every mathematically
   possible quotient/remainder coefficient without truncation.
5. How a zero divisor is handled in the classical model and what domain the
   claimed reversible bijection covers. Existing classical code raises;
   a circuit cannot raise an exception. No total off-domain extension is
   currently specified.
6. Whether canonical empty zero polynomials at the classical API boundary
   are converted into nonempty fixed-width all-zero registers.

For the conventional polynomial quotient/remainder function, if `B` is
nonzero, the pair is uniquely determined by the identity and degree bound.
If `A` and `B` are preserved and quotient/remainder are XORed into fixed
targets, that deterministic relation is an involution for each fixed valid
`A,B`. This mathematical fact does not specify the target layout or prove a
division algorithm's scratch cleanup.

### 10.3 Leading coefficient, capacity, and edge cases

- Normalize or otherwise identify the highest nonzero divisor coefficient
  before inversion. Never pass zero to the classical field inverse.
- The leading divisor coefficient is nonzero only on the valid-divisor
  domain. The P009 reversible inverse's total convention `inverse(0)=0`
  must not be mistaken for a valid polynomial division by zero.
- For nonzero divisor degree `dB`, remainder has degree `< dB`; a zero
  remainder is represented by the agreed zero convention.
- For nonzero dividend degree `dA >= dB`, quotient has degree `<= dA-dB`.
  When `dA < dB`, quotient is zero and remainder equals dividend.
- Zero dividend gives zero quotient/remainder for nonzero divisor.
- Division by the zero polynomial must be explicitly rejected or separately
  totalized by a future specification; no existing mathematical quotient
  is defined by this repository.
- Fixed-width result registers need enough capacity for quotient and
  remainder under all supported input widths, including trailing-zero input
  slots. P012 must document whether outputs are normalized or retain fixed
  slots.

### 10.4 Reversible compute and cleanup obligations

A future P012 implementation must identify and preserve quotient terms,
remainder states, leading-degree information, leading coefficient inverse,
shift/control values, and any old state overwritten during long division.
It must compute the quotient/remainder into explicit output targets, XOR
those values into targets only after their contract is fixed, then reverse
the computation and verify every scratch register returns to its declared
initial state. Directly assigning zero to overwritten history or scratch
does not establish reversible cleanup.

The exact scratch/register design is **unverified and intentionally left for
P012**. A classical call to `divide_polynomials` or the quotient/remainder
identity alone does not establish a reversible update sequence.

### 10.5 Independent oracle and small-field exhaustive strategy

Use an independent finite-field polynomial long-division oracle that does
not call `divide_polynomials`, production field operations, or a proposed
P012 function to calculate expected results. Possible cross-checks include:

- independent quotient/remainder computation by leading-term cancellation;
- checking `A == B*Q + R` with an independent multiplier;
- checking `R == 0` for exact division;
- checking `R == 0` or `degree(R) < degree(B)` as appropriate;
- input preservation, target XOR accumulation, double application, and
  scratch-zero assertions.

For each small field GF(2²), GF(2³), and GF(2⁴), bound polynomial widths
explicitly and enumerate all coefficient tuples for dividend and nonzero
divisor. Include all quotient/remainder target values if claiming complete
transformation-state enumeration; the full domain grows as
`q^(m+n+q_width+r_width)` times the number of valid divisors for fixed
coefficient widths `m,n`. A smaller exhaustive subset may be used, but label
it as bounded and give exact input/target counts. Include zero dividend,
constant nonzero divisors, lower-degree dividends, exact divisions,
nonzero remainders, and trailing-zero slots at the input boundary.
GF(2^12) cases should be identified as deterministic or randomized unless
the full relevant domain is actually enumerated.

## 11. P012 readiness and unresolved assumptions

**Ready for a bounded specification/model phase; not ready for a
verifier-compatible circuit.** The repository establishes field arithmetic,
low-degree-first polynomial ordering, canonical classical polynomial
normalization, and classical division behavior for nonzero divisors.
P012 still must define fixed-width input/output encodings, target capacities,
zero-divisor treatment, and a reversible update/history scheme. No quantum
circuit, gate model, official verifier mapping, or serialization is
established by P011.

P012 must not implement EEA, decoder stages, or a quantum circuit unless
separately authorized. P012 is not implemented here.

## 12. Acceptance results

| Audit criterion | Result |
|---|---|
| Expected root, branch, and HEAD confirmed | **PASS** |
| Full initial Git status and untracked inventory captured | **PASS** |
| Required P011/P010/P009 sources, tests, and reports inspected | **PASS** |
| P011 coefficient, point, target, and field contracts audited | **PASS** |
| Horner order and arithmetic audited against actual source | **PASS** |
| Forward target accumulation and reverse cleanup audited | **PASS** |
| Independent power-sum oracle boundary documented | **PASS** |
| 69,888 state count reproduced and properly classified | **PASS** |
| All required tests reproduced with actual counts and runtimes | **PASS** |
| P001–P010, P011 implementation, classical files, README, and INVSQRT preserved | **PASS** |
| P012 requirements described without implementing division | **PASS** |
| Files deleted or unrelated files modified | **NONE** |

## Final status

**PASS — P011 audit passes and P012 mathematical prerequisites are
adequately established for a bounded research-model phase.** This does not
establish a quantum circuit, gate-level reversibility, official verifier
compatibility, or competition readiness. P012 is not started.
