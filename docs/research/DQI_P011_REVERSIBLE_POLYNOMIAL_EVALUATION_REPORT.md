# DQI-P011 — Reversible Polynomial Evaluation Model

- **Project:** Google Quantum AI — Verifiable Quantum Circuit Compilation
- **Workstream:** DQI Decoder
- **Phase:** 01 — P011
- **Audit date:** 2026-11-20
- **Repository root:** `/mnt/d/PROJECT/Quantum_AI/Google-Quantum-AI`
- **Branch:** `feat/dqi-decoder`
- **HEAD before and after:** `5391b2e7123484efacffc0588f5e761e67b5cb55`
- **Status:** **PASS — scoped mathematical register-model requirements and tests pass**

## 1. Objective and mathematical contract

P011 adds a fixed-width, input-preserving polynomial evaluation relation over
the repository's GF(2^12):

```text
(A, x, T) -> (A, x, T XOR A(x))
```

For low-degree-first coefficients
`A=(a_0,...,a_(m-1))`, the mathematical value is:

```text
A(x) = XOR from i=0 to m-1 of (a_i * x^i)
```

Here field addition is XOR in characteristic two; it is not integer
addition. Field multiplication reduces in the polynomial basis modulo
`0x1053`. The operation preserves both `A` and `x`, and updates only the
one-element target tuple.

This is a classical register model with explicit scratch-value computation
and uncomputation. It is not a quantum circuit or gate-level proof.

## 2. P010 audit and dependency traceability

Before implementation, the current branch/HEAD and worktree were checked.
The P010 handoff, implementation, tests, report, P009 primitives, field,
classical polynomial module, and P008/P009 reports were read directly.

The actual source confirms the P010 contracts used here:

- Polynomial registers are nonempty tuples of GF(2^12) elements.
- Coefficients are low-degree first; index zero is the constant term.
- Trailing zero coefficients remain part of the fixed register width.
- Empty tuples are rejected by P010.
- `field.py` represents elements as integers in `[0, 4095]`, with bit `k`
  denoting the coefficient of `alpha^k`, and uses modulus `0x1053`.
- P009 `xor_accumulate_add(left, right, target)` preserves both operands and
  XORs their field sum into its target.
- P009 `xor_accumulate_multiply(left, right, target)` preserves both
  operands and XORs their field product into its target.

No material contradiction between the P010 source and the P010 handoff was
found. P011 uses the existing P009 add and multiply helpers; it does not
modify P010 or P009.

## 3. Implementation inventory and public API

### Files created

| File | Purpose |
|---|---|
| `src/dqi_decoder/reversible_evaluation.py` | Validated P011 evaluation transformation and internal compute/accumulate/uncompute model |
| `tests/dqi_decoder/test_reversible_evaluation.py` | Independent oracle, bounded exhaustive domains, GF(2^12) vectors, and validation tests |
| `docs/research/DQI_P011_REVERSIBLE_POLYNOMIAL_EVALUATION_REPORT.md` | This implementation and evidence report |

### Public API

```python
PolynomialRegister = tuple[int, ...]
EvaluationTarget = tuple[int, ...]

def xor_accumulate_polynomial_evaluation(
    polynomial: PolynomialRegister,
    point: int,
    target: EvaluationTarget,
) -> tuple[PolynomialRegister, int, EvaluationTarget]: ...
```

`polynomial` must be a nonempty tuple of field elements; `point` must be one
field element; and `target` must be a tuple containing exactly one field
element. The function returns the original validated polynomial tuple,
original point, and updated one-element target tuple. Inputs are not
mutated. The new function is module-level, following P010's module API;
`src/dqi_decoder/__init__.py` was not changed.

Invalid containers/types raise `TypeError`; empty polynomial or incorrect
target width raise `ValueError`; invalid field values are rejected by the
existing `validate_element`. There is no field-value truncation or target
resizing.

## 4. Horner derivation and reversible register sequence

For `m` coefficient slots, Horner's recurrence in the repository's field is:

```text
h_(m-1) = a_(m-1)
h_i     = h_(i+1) * x XOR a_i, for i = m-2,...,0
A(x)    = h_0
```

Expanding the recurrence gives the power-sum definition:

```text
h_0 = a_0 XOR (a_1*x) XOR ... XOR (a_(m-1)*x^(m-1)).
```

The implementation models the recurrence using clean scratch registers and
the existing P009 target-XOR relations:

1. Allocate a dedicated zero scratch register, an initial accumulator, and
   two new scratch registers (product and next accumulator) for each lower
   coefficient. Allocation initializes these scratch values to zero.
2. Compute the initial accumulator with
   `xor_accumulate_add(a_(m-1), zero, accumulator)`.
3. For each next coefficient, compute and retain
   `product XOR (previous_accumulator * x)` using
   `xor_accumulate_multiply`, then compute and retain
   `next_accumulator XOR (product + a_i)` using
   `xor_accumulate_add`.
4. Accumulate the final accumulator into the caller's target with
   `xor_accumulate_add(evaluation, zero, target)`. The zero scratch remains
   zero.
5. In reverse stage order, XOR `product + a_i` out of each next-accumulator
   register, then XOR `previous_accumulator * x` out of its product
   register. Finally XOR the leading coefficient out of the initial
   accumulator.
6. Check that every scratch register, including the dedicated zero
   register, is zero. A nonzero scratch result raises `RuntimeError` rather
   than being silently accepted.

For width `m`, this model allocates `2m` field-valued scratch slots: one
zero register, one initial accumulator, and two per remaining coefficient.
The model retains all Horner intermediates until their dependent reverse
updates have completed. It does not expose scratch as part of the public
output.

## 5. Independent reference oracle

The test oracle computes evaluation by a method separate from production
Horner evaluation:

1. Build `x^i` successively from `x^0=1`.
2. Multiply each coefficient by its power.
3. XOR all coefficient terms.

The oracle's finite-field multiplier is test-local shift/XOR multiplication
followed by polynomial reduction using the established modulus. It does not
call production `field.multiply`, `polynomial.evaluate_polynomial`, P009
helpers, or the P011 production function. Thus the oracle shares the
mathematical field modulus and polynomial-basis encoding, as required, but
not the production evaluation procedure or production arithmetic routine.

Small fields use the same test-local shift/reduce algorithm with separately
declared moduli. The test verifies these moduli are irreducible. The small
field Horner scratch model is separately evaluated and reversed to test its
workspace lifecycle; the independent power-sum oracle supplies expected
evaluation values.

## 6. Exhaustive bounded small-field verification

The exhaustive transformation domain uses exactly **two coefficient
register slots**, one evaluation point, and one target value. For field
size `q`, it enumerates all `q^2` coefficient tuples, all `q` points, and
all `q` target values, giving `q^4` full input states. This is exhaustive
for that fixed width, but bounded with respect to polynomial width and is
not exhaustive over arbitrary-width polynomials.

| Field | Modulus | `q` | Coefficient tuples `q²` | Points `q` | Targets `q` | States `q⁴` |
|---|---:|---:|---:|---:|---:|---:|
| GF(2²) | `0b111` | 4 | 16 | 4 | 4 | 256 |
| GF(2³) | `0b1011` | 8 | 64 | 8 | 8 | 4,096 |
| GF(2⁴) | `0b10011` | 16 | 256 | 16 | 16 | 65,536 |
| **Total** | — | — | **336** | **28** | **28** | **69,888** |

For every enumerated state the test:

- compares the computed target with the independent power-sum oracle;
- verifies polynomial and point preservation;
- applies evaluation again and verifies the original target is restored;
- computes Horner scratch, accumulates the target, reverses the scratch
  updates, and checks every scratch slot is zero; and
- records the full output state and checks no duplicate output state occurs.

The uniqueness check covers all 69,888 input states across the three
fixed-width domains. This is bounded exhaustive testing of the independent
small-field model, not exhaustive execution of GF(2^12) production code.

## 7. GF(2^12) deterministic production coverage

Ten deterministic polynomial/point/target cases are compared against the
independent power-sum oracle. They cover:

- all-zero polynomial and nonempty fixed-width zero representation;
- constant and degree-one polynomials;
- higher-degree, sparse, dense, and trailing-zero-slot polynomials;
- evaluation at zero, one, and selected nonzero points;
- unequal coefficient values and maximum coefficient `0xFFF`;
- multiple nonzero targets and target XOR accumulation;
- input preservation, repeated application, and scratch cleanup.

Additional cases check bijection/involution on selected full states,
empty/wrong-width registers, non-tuple registers, invalid coefficient/point/
target types and values, and rejection rather than truncation for oversized
field values and target widths.

These are deterministic tests, not randomized tests and not exhaustive
GF(2^12) evaluation over all polynomials, points, and targets.

## 8. Reversibility and correctness evidence

### 8.1 Input preservation

The coefficient tuple and point are validated and only read. All Horner
updates target newly initialized scratch values. The P009 helpers return
their operands unchanged. The public function returns the original validated
tuple and point, and the target update is isolated to a fresh one-element
tuple. No input object or field value is overwritten.

### 8.2 Target reversibility

For fixed `(A,x)`, evaluation is a deterministic field value `v=A(x)`.
The target update is `T' = T XOR v`. Applying it again with the same
polynomial and point gives:

```text
T'' = T XOR v XOR v = T.
```

This is a mathematical involution argument. Tests exercise repeated
application; they are not a formal proof assistant or a gate-level proof.

### 8.3 Workspace cleanup

The source computes Horner accumulators and products into separate zero
scratch registers, XORs the final value into the caller's target, and then
replays each target-XOR computation in reverse order using the same P009
primitive and unchanged source values. Each scratch update is therefore
applied twice and returns to zero. The implementation explicitly checks the
complete scratch tuple after uncomputation. Tests check zero scratch in the
production helper and for every small-field exhaustive state.

This establishes cleanup for the modeled classical scratch values only. It
does not establish quantum ancilla separability, phase behavior, or a
circuit decomposition.

### 8.4 Bijectivity

On the valid fixed-width domain, `A` and `x` are retained and `T` is updated
by XOR with the deterministic value `A(x)`. The transformation is its own
inverse, so it is bijective. The exhaustive bounded small-field tests also
check output uniqueness for every state in their enumerated domains.

### 8.5 Horner equivalence

By induction on descending coefficient index, the recurrence
`h_i = h_(i+1)*x XOR a_i` expands to the suffix polynomial
`a_i + a_(i+1)x + ... + a_(m-1)x^(m-1-i)` evaluated at `x`, with the
appropriate power offset in the full polynomial. At `i=0`, this is exactly
the coefficient power sum. Independent power-sum comparisons corroborate
this equivalence in bounded small fields and selected GF(2^12) cases.
The induction is a mathematical argument; the tests provide finite
computational evidence, not a machine-checked proof.

## 9. Test execution results

All commands ran with Python bytecode generation and pytest cache creation
disabled.

| Suite | Exact command | Result |
|---|---|---|
| P011 focused | `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/dqi_decoder/test_reversible_evaluation.py -q` | **7 passed, 27 subtests, 0 failed, 0 skipped, 0.69s** |
| P010 polynomial | `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/dqi_decoder/test_reversible_polynomial.py -q` | **6 passed, 28 subtests, 0 failed, 0 skipped, 0.29s** |
| P009 primitives | `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/dqi_decoder/test_reversible_primitives.py -q` | **9 passed, 33 subtests, 0 failed, 0 skipped, 0.26s** |
| Classical DQI regressions | `PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 python -m pytest -p no:cacheprovider tests/dqi_decoder/test_field.py tests/dqi_decoder/test_polynomial.py tests/dqi_decoder/test_decoder.py tests/dqi_decoder/test_syndrome.py -q` | **37 passed, 5,411 subtests, 0 failed, 0 skipped, 9.44s** |

No warning summary was emitted by these commands.

AST syntax parsing passed for the new source and test modules. `ruff`,
`mypy`, `pylint`, and `pyright` were unavailable. No project build or static
type-check command was configured in the inspected repository; no tools or
dependencies were installed.

## 10. Preservation and Git status

Baseline and final repository identity:

| Item | Result |
|---|---|
| Root | `/mnt/d/PROJECT/Quantum_AI/Google-Quantum-AI` |
| Branch | `feat/dqi-decoder` |
| HEAD | `5391b2e7123484efacffc0588f5e761e67b5cb55` |
| Pre-existing tracked unstaged change | `README.md` line-ending conversion, untouched |
| Staged changes | None |
| Files deleted | None |
| Dependencies added | None |

P001–P010 reports and implementation files, P009/P010 tests, the classical
decoder, field and polynomial conventions, existing unrelated untracked
files, and INVSQRT work were preserved. `src/dqi_decoder/__init__.py` was
not modified. No branch or HEAD operation, commit, push, reset, clean,
merge, or deletion occurred.

P011 adds only the three files listed in §3. They are untracked at this
baseline HEAD, consistent with the existing DQI worktree convention. The
pre-existing README line-ending change was not modified.

## 11. Known limitations

- The supported polynomial width is caller-defined and has no separate
  DQI-specific maximum.
- Empty polynomial tuples are rejected; a zero polynomial is a nonempty
  all-zero coefficient tuple.
- The target is represented as a one-element tuple to align with the fixed
  register convention; no external wire serialization is implied.
- Scratch behavior is an explicit classical register-value model, not
  quantum circuit evidence.
- The small-field enumeration fixes polynomial width at two coefficients.
  It does not exhaust arbitrary polynomial widths or GF(2^12).
- No verifier, official fixture, circuit simulator, gate decomposition,
  resource measurement, or benchmark was run.
- No official verifier compatibility, circuit-level proof, or competition
  readiness is claimed.

## 12. P012 prerequisites

P012 may use P011's evaluation relation as a mathematical component after
reviewing the actual API and this report. Before building a subsequent
primitive, explicitly define its coefficient/register widths, source and
target preservation, scratch allocation, forward computation, target
accumulation, reverse uncomputation, and independent oracle. Preserve the
low-degree-first GF(2^12) convention and distinguish classical model tests
from circuit evidence. Any circuit, verifier, or benchmark work requires
separate authorization and artifacts; none is implied by P011.

## 13. Acceptance criteria

| Requirement | Result |
|---|---|
| Baseline and P010 contracts inspected before implementation | **PASS** |
| Input-preserving evaluation API with a one-element target | **PASS** |
| Horner compute uses P009 field primitives and retains inputs/intermediates | **PASS** |
| Target XOR accumulation followed by reverse scratch uncomputation | **PASS** |
| Scratch-zero checks in implementation model and tests | **PASS** |
| Independent power-sum oracle | **PASS** |
| Bounded exhaustive GF(2²), GF(2³), GF(2⁴) state domains counted exactly | **PASS** |
| Deterministic GF(2^12), invalid-input, and no-truncation tests | **PASS** |
| P010, P009, and classical DQI regression suites pass | **PASS** |
| P001–P010, README state, unrelated files, INVSQRT, branch, and HEAD preserved | **PASS** |
| Circuit, gate decomposition, verifier, decoder, or benchmark introduced | **NO** |
| P012 started | **NO** |

## Final status

**PASS — all scoped implementation and correctness requirements pass.**
P011 delivers a classical reversible-register model and bounded/tested
correctness evidence only. No circuit-level or official compatibility claim
is made. P012 is not started.
