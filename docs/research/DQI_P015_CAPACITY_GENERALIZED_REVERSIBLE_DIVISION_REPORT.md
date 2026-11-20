# DQI-P015 — Capacity-Generalized Reversible Polynomial Division

## 1. Execution summary and status

P015 extends the existing classical reversible-register model for polynomial
division from its former eight-slot input bound to explicit bounded
capacities of 71 dividend coefficients and 70 divisor coefficients. The
operation continues to preserve its input tuples and XOR-accumulate quotient
and remainder into exact-width targets. The small-field oracle and the
compute/accumulate/uncompute implementation remain separate.

The P012 division behavior for all previously supported valid inputs is
preserved. The old `MAX_POLYNOMIAL_REGISTER_WIDTH = 8` constant remains
available for P013's independent eight-slot input contract; the division API
uses new explicit capacity constants and optional lower per-call limits.

All required tests and regressions passed. The added domain remains a
classical Python register model. This phase does not implement iterative
EEA, a quantum circuit, P008's synchronized register architecture, an
official verifier, or competition behavior.

**Final status: PASS — for the declared capacity-bounded polynomial division
contract and the tested classical register model.** This does not claim
complete P008 compatibility or circuit-level reversibility.

## 2. P014 assumptions inspected and verified

Inspected the actual P014 capacity specification, P013→P014 handoff,
P012 division source/tests/report, P013 source/tests/reports, P009–P011
source/tests/reports, `field.py`, `polynomial.py`, and P008's EEA
specification.

The following P014 facts were verified against those artifacts:

- The P008 key-equation operands described by P014 are `A=z^70` (71
  coefficient slots) and syndrome polynomial `S(z)` of degree at most 69
  (at most 70 coefficient slots).
- For general polynomial division, the quotient significant-support bound
  of 36 is **not** valid for arbitrary accepted operands. It follows only
  for the stated thresholded EEA domain and active divisor degree at least
  35. A constant divisor can produce a quotient with as many coefficients
  as the dividend has declared slots.
- A nonzero remainder has degree below the effective divisor degree. The
  output target still has an exact capacity derived from the declared
  divisor width, including any retained high zero padding.
- P012's existing scratch model retains a dividend-width quotient and
  remainder at each long-division shift. A capacity extension must account
  for that dynamic scratch growth; the P014 scratch figures are arithmetic
  bounds on this Python model, not qubit or circuit resource claims.
- P013 independently restricts its six inputs to eight slots. Widening P012
  does not implement or widen P013, nor does it complete P014's iterative
  EEA contract.

## 3. Repository baseline and preservation

| Item | Before | After |
|---|---|---|
| Repository root | `/mnt/d/PROJECT/Quantum_AI/Google-Quantum-AI` | unchanged |
| Branch | `feat/dqi-decoder` | `feat/dqi-decoder` |
| HEAD | `5391b2e7123484efacffc0588f5e761e67b5cb55` | unchanged |
| Staged changes | none | none |
| Tracked modifications | Existing `README.md` change only | same |
| Untracked paths | 83 recorded at start | 85 at final check, including this report |

The README SHA-256 remained
`6fc9e83d0fb74d8f163fbd1c0fb0d0da246bd33e218e86ee56bd78ec15379027`;
its existing BOM/line-ending change was not edited. The final untracked count is two higher than the recorded starting count.
The report is one known addition; a per-path fingerprint inventory was not
captured at the start, so the remaining count difference is not attributed
to a particular path. No untracked path was deleted or overwritten. P001–P014 evidence,
P009/P010/P011 source and tests, P012/P013 code and reports, classical
decoder/field/polynomial/syndrome files, and unrelated INVSQRT work were not
modified or deleted. No dependencies were added. No branch or Git history
operation was performed.

## 4. Accepted capacity and register contract

### 4.1 Capacity constants and parameters

The division module defines:

```python
MAX_POLYNOMIAL_REGISTER_WIDTH = 8
MAX_DIVISION_DIVIDEND_WIDTH = 71
MAX_DIVISION_DIVISOR_WIDTH = 70
```

The first constant is retained for P013's existing input validation. The
division function has keyword-only capacity limits, defaulting to the latter
two constants:

```python
def xor_accumulate_polynomial_division(
    dividend: PolynomialRegister,
    divisor: PolynomialRegister,
    quotient_target: DivisionTarget,
    remainder_target: DivisionTarget,
    *,
    max_dividend_width: int = MAX_DIVISION_DIVIDEND_WIDTH,
    max_divisor_width: int = MAX_DIVISION_DIVISOR_WIDTH,
) -> tuple[
    PolynomialRegister,
    PolynomialRegister,
    DivisionTarget,
    DivisionTarget,
]: ...
```

Each per-call maximum must be an exact integer (booleans are rejected),
at least one, and no greater than its corresponding module maximum.
Inputs wider than the per-call maximum are rejected before scratch
computation. Callers may select smaller bounds but cannot raise the declared
hard limits through these parameters.

### 4.2 Exact accepted input/output widths

| Register | Accepted capacity |
|---|---:|
| Dividend | Nonempty tuple, width `1..max_dividend_width`, at most 71 |
| Divisor | Nonempty tuple, width `1..max_divisor_width`, at most 70; effective polynomial must be nonzero |
| Quotient target | Exactly `len(dividend)` field coefficients, at most 71 |
| Remainder target | Exactly `max(1, len(divisor)-1)` field coefficients, at most 69 |

Inputs and targets contain GF(2^12) elements in `[0,4095]`. The
representation is low-degree-first and preserves tuple width. A nonempty
all-zero input tuple denotes zero; an empty polynomial register is invalid.
High trailing zero slots are retained and do not determine effective degree.

### 4.3 Width justification

For dividend width `a`, a nonzero constant divisor permits quotient degree
at most `a-1`. Thus `a` quotient slots are necessary and sufficient for
every valid dividend of that width. The implementation uses exactly that
target width; it does not apply the P014 36-slot thresholded-EEA quotient
bound to general division.

For divisor width `b`, its effective degree is at most `b-1`. A valid
nonzero remainder has degree strictly less than that, so at most `b-1`
coefficients are required. The exact target width is `max(1,b-1)`:
the one-slot minimum preserves the repository's nonempty register
convention and represents the necessarily zero remainder for a constant
divisor. High zero padding in the divisor may make this target wider than
the minimum for its effective degree; that is intentional and never causes
truncation.

Therefore the default `71/70` input capacities are mathematically
sufficient for every accepted pair, not only P008-shaped pairs. They cover
the two operand widths identified by P014 without claiming support for
unbounded polynomial inputs.

## 5. P014 relationship and limits of the claim

The new defaults admit the P014 mathematical operand widths:

- `z^70` as a 71-slot dividend;
- any 70-slot-or-shorter syndrome polynomial as divisor, provided it is
  nonzero for division.

For a P008-threshold EEA active divisor with degree at least 35, the
quotient significant support can be at most 36 coefficients. This
primitive deliberately retains the more general quotient target width of
71 because it accepts general nonzero divisors, including constants. It
does not implement a 36-slot threshold-specific quotient interface.

The accepted input widths do not establish P008 compatibility:

- Current P010 still defines full declared-width convolution targets, and
  P012 still uses its existing source-shaped division scratch schedule.
- P013 still validates each of its six input polynomials at width at most
  eight. Its Bézout target sizing and iterative capacity problem are
  unchanged.
- P008's two shared arrays, five degree pointers, quotient storage,
  synchronized schedule and 222 reported steps are not implemented here.
- No local register alias map, circuit schedule, phase behavior, or
  gate-level cleanup proof is established.

## 6. Implementation design and changed API behavior

`_validate_register` now receives an explicit maximum width. The public
division entry point validates both capacity arguments, then validates
input tuple type, nonempty shape, input width, and every field element.
Targets are validated as exact-width tuples of field elements. A zero
effective divisor raises `ZeroDivisionError` before the computation or any
caller-visible result is produced.

The existing long-division scratch algorithm is retained. It computes the
effective leading divisor coefficient, accumulates its inverse into a
zero-initialized scratch target, then processes quotient shifts from high to
low. Each step computes a factor, a fresh quotient copy/update, and a fresh
remainder copy/update. It validates that the final remainder fits the
declared remainder target before creating the updated target tuples.

The observable output remains:

```text
(A, B, TQ, TR)
  -> (A, B, TQ XOR Q(A,B), TR XOR R(A,B))
```

No P009–P014 source or report was changed. P013 continues to import the
legacy eight-slot constant and enforce its own eight-slot input contract.
The P012 division operation now accepts the larger domain by default;
previously supported valid inputs retain the same result and target-width
rules.

## 7. Compute, accumulation, and scratch reversal

The scratch helper:

1. Starts with an empty scratch list and allocates zero-valued quotient and
   remainder registers, each the dividend width.
2. Copies dividend coefficients into an initial remainder using the
   XOR-accumulating field-add primitive.
3. Computes the inverse of the nonzero effective leading divisor
   coefficient into a one-element scratch target.
4. For each quotient shift, computes the factor, copies prior quotient and
   remainder into fresh zeroed registers, and XORs the quotient factor and
   shifted factor-times-divisor terms into those new registers.
5. XOR-accumulates the final quotient and remainder into local copies of the
   validated caller targets.
6. Visits recorded shifts in reverse order, removes the divisor product,
   clears the copied remainder and quotient, and clears the factor product.
7. Clears the copied dividend and leading-coefficient inverse by replaying
   their XOR-target relations.
8. Returns the scratch tuple; the public function checks every element is
   zero before returning the new target tuples.

No computed scratch value is silently assigned zero as a substitute for
reversal. Inputs and targets are immutable tuples, and updated target
tuples remain local until successful completion. Invalid input/capacity
errors therefore cannot partially mutate caller-owned targets.

For dividend width `a`, effective divisor degree `d`, and
`h=max(0,a-d)` shift iterations, the source-shaped scratch allocation is:

```text
(h+1) * (a + a + 1) = (h+1)*(2a+1) field-element slots
```

The base `2a+1` is the initial dividend remainder, initial quotient, and
leading inverse. Every shift adds one factor and fresh quotient/remainder
registers of width `a`. Across the default domain, the maximum occurs for
`a=71` and a constant divisor (`d=0`): `h=71`, for
`72*143 = 10,296` field-element scratch slots. If the divisor degree is
at least 35 as in an active P008 threshold step, the maximum is 36 shifts,
for `37*143 = 5,291` slots.

These are field-element slots in the Python scratch model. The step-history
list also stores Python indices/references and is not included in that
field-element count. Neither number is a qubit count, ancilla estimate, or
P008 resource claim.

## 8. Independent oracle and mathematical checks

The test module's expected polynomial division uses test-local field
multiplication implemented by carryless shift/XOR followed by reduction,
test-local inversion by exponentiation, and normalized-list long division.
It does not call the production reversible division function, its scratch
helper for expected values, or `polynomial.divide_polynomials`. The
production scratch sequencing helper is separately driven with test-local
small-field callbacks in the bounded exhaustive tests.

The oracle and production implementation necessarily share the GF(2^12)
polynomial modulus `0x1053`, the polynomial-basis coefficient encoding,
and the mathematical definition of inversion for nonzero elements. The
oracle multiplication is structurally separate from `field.multiply`;
these shared mathematical conventions remain correlated assumptions.

The helper assertions verify the independent quotient/remainder, full
reconstruction `A = BQ + R`, remainder degree bound, unchanged input
tuples, exact target XOR accumulation, target restoration on repeated
application, and clean scratch.

## 9. Exhaustive small-field enumeration

The added one-coefficient suite enumerates the **complete valid
target-inclusive register domain** for one-slot dividend and divisor
registers in each small field:

- all `q` dividend elements;
- all `q-1` nonzero divisor elements;
- all `q` quotient target values; and
- all `q` remainder target values.

The exact count is `q^3(q-1)` states. For each state, it checks oracle
output, input preservation, scratch cleanup, and uniqueness of the output
state over the enumerated domain.

| Field | Size `q` | Dividend values | Nonzero divisors | Target pairs | Full states |
|---|---:|---:|---:|---:|---:|
| GF(2²) | 4 | 4 | 3 | 16 | 192 |
| GF(2³) | 8 | 8 | 7 | 64 | 3,584 |
| GF(2⁴) | 16 | 16 | 15 | 256 | 61,440 |
| **Total** | — | — | — | — | **65,216** |

The pre-existing two-coefficient small-field suite is retained. It covers
every two-slot dividend and nonzero divisor pair but uses two deterministic
target seeds per pair, not every target value:

| Field | Input pairs | Selected target cases | Second-map applications |
|---|---:|---:|---:|
| GF(2²) | 240 | 480 | 960 |
| GF(2³) | 4,032 | 8,064 | 16,128 |
| GF(2⁴) | 65,280 | 130,560 | 261,120 |
| **Total** | **69,552** | **139,104** | **278,208** |

It independently checks each selected case's quotient/remainder,
reconstruction, degree condition, input preservation, target accumulation,
second-application restoration, and scratch cleanup. This is exhaustive
over the two-slot input pairs, but not all target pairs or full register
states. The report does not call those selected target cases full-state
exhaustion.

## 10. GF(2^12) production coverage

The focused suite covers:

- Existing P012 cases: zero dividend, constant and nonconstant divisors,
  dividend degree less/equal/greater than divisor degree, nonmonic
  divisors, sparse/dense inputs, trailing zero padding, and arbitrary
  nonzero initial targets.
- Repeated XOR application and preservation of both inputs.
- Zero divisor rejection and invalid containers, field values, target
  widths, and capacities.
- Maximum prior P012 width-eight cases.
- Maximum new dividend width 71 with maximum divisor width 70, checked
  against the independent oracle and target widths.
- Maximum dividend width 71 with a nonzero constant divisor, exercising
  the 71-coefficient quotient boundary and maximum scratch schedule.
- Direct assertion that the maximum-width scratch helper returns all-zero
  scratch.

These GF(2^12) cases are deterministic vectors, not exhaustive field
coverage.

## 11. Test reproduction and static checks

All tests were run from the repository root with bytecode and pytest cache
creation disabled, preserving existing cache paths.

| Suite | Exact command | Result | Runtime |
|---|---|---|---:|
| P015/P012 division | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q tests/dqi_decoder/test_reversible_division.py` | 10 passed; 20 subtests; 0 failed; 0 skipped; no warnings | 9.64 s |
| P013 compatibility | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q tests/dqi_decoder/test_reversible_eea.py` | 5 passed; 11 subtests; 0 failed; 0 skipped; no warnings | 14.94 s |
| P011 | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q tests/dqi_decoder/test_reversible_evaluation.py` | 7 passed; 27 subtests; 0 failed; 0 skipped; no warnings | 0.86 s |
| P010 | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q tests/dqi_decoder/test_reversible_polynomial.py` | 6 passed; 28 subtests; 0 failed; 0 skipped; no warnings | 0.48 s |
| P009 | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q tests/dqi_decoder/test_reversible_primitives.py` | 9 passed; 33 subtests; 0 failed; 0 skipped; no warnings | 0.30 s |
| Classical field/polynomial/decoder/syndrome | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q tests/dqi_decoder/test_field.py tests/dqi_decoder/test_polynomial.py tests/dqi_decoder/test_decoder.py tests/dqi_decoder/test_syndrome.py` | 37 passed; 5,411 subtests; 0 failed; 0 skipped; no warnings | 11.93 s |

AST parsing passed for the changed source and test modules. `ruff`, `mypy`,
`pylint`, and `pyright` were unavailable; none were installed. `git diff
--check` reported the pre-existing README BOM/line-ending diff as
trailing whitespace; no README changes were made. The changed Python files
and this report were checked separately for trailing whitespace.

## 12. Files changed

Modified:

- `src/dqi_decoder/reversible_division.py`
- `tests/dqi_decoder/test_reversible_division.py`

Created:

- `docs/research/DQI_P015_CAPACITY_GENERALIZED_REVERSIBLE_DIVISION_REPORT.md`

Deleted: none.

No P009–P014 report or implementation, classical field/polynomial/decoder/
syndrome code, README, dependency manifest, or INVSQRT artifact was changed.

## 13. Limitations and unresolved requirements

1. The default input capacities are finite: dividend width 71 and divisor
   width 70. Wider tuples are rejected; this is not arbitrary-width
   polynomial division.
2. The API's quotient target remains dividend-width, even in a thresholded
   EEA subdomain where a 36-slot quotient could be mathematically
   sufficient. This intentionally supports general division within the
   declared limits and preserves the former width contract.
3. P013 still uses an eight-slot input limit. This primitive alone does not
   provide a capacity-generalized EEA transition or iterative composition.
4. The P008 synchronized two-array layout, degree pointers, 222-step
   schedule, and paper resource accounting have not been implemented or
   independently reconciled against this Python scratch model.
5. Python-level scratch reversal is not a quantum gate-level
   uncomputation or phase proof.
6. Zero polynomial divisor is rejected. P008 zero-syndrome EEA/output
   semantics remain unresolved; the primitive does not define them.
7. Official verifier compatibility and competition readiness are not
   established.

## 14. Acceptance criteria

| Criterion | Result |
|---|---|
| Supports declared larger capacities without silent truncation | **PASS** |
| Capacity bounds are mathematically justified for every accepted input | **PASS** |
| Division identity and remainder-degree condition verified | **PASS** in independent tests |
| Inputs preserved; quotient/remainder targets XOR-accumulated | **PASS** |
| Zero divisor and capacity errors rejected before visible mutation | **PASS** |
| Modeled scratch reverses and returns to zero | **PASS** |
| Independent oracle and bounded exhaustive small-field tests pass | **PASS** |
| Existing P012 valid-domain tests and P013 compatibility pass | **PASS** |
| P008 limitations and circuit evidence boundary reported | **PASS** |
| Unrelated work and repository state preserved | **PASS** |
| P016 started | **NO** |

P015 is complete. P016 has not been started.
