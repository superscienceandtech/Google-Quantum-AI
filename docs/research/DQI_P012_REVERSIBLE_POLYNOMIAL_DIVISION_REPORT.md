# P012 — Reversible Polynomial Division & Correctness Harness

## Objective and status

P012 adds a bounded mathematical register model for polynomial quotient and
remainder over the repository's GF(2^12). It preserves the input registers,
XOR-accumulates both outputs into separate caller-owned targets, and reverses
its modeled scratch computation. This is a classical register-model
implementation; it is not a quantum circuit or a gate-level reversibility
proof.

The implementation was validated with focused P012 tests and the P011, P010,
P009, and classical DQI regression suites. See the reproduced results below.
No EEA, decoder stage, quantum circuit, verifier integration, or competition
claim is included.

## Mathematical contract

For nonempty low-degree-first coefficient tuples `A` and nonzero `B`, the
classical division identity is:

`A = B × Q + R`, with `R = 0` or `degree(R) < degree(B)`.

The register transformation is:

`|A>|B>|TQ>|TR> → |A>|B>|TQ XOR Q>|TR XOR R>`.

Addition and output accumulation are coefficient-wise GF(2^12) addition, which
is XOR in the repository's polynomial-basis representation. Integer addition
is not used for field arithmetic. A zero divisor raises `ZeroDivisionError`
before the computation or output accumulation begins.

## Register representation and capacities

- Polynomial registers are nonempty tuples of GF(2^12) elements in
  low-degree-first order. Trailing zero coefficients are retained.
- Each input register is limited to 8 coefficient slots by the P012 API.
  This is a phase-local resource bound, not a limit established by P010.
- The zero polynomial is represented by a nonempty all-zero tuple.
- The quotient target has exactly `len(dividend)` elements. A nonzero
  constant divisor is the worst case: a dividend with `m` slots can produce a
  quotient of degree `m - 1`, requiring `m` slots.
- The remainder target has exactly `max(1, len(divisor) - 1)` elements. A
  divisor with `n` slots has degree at most `n - 1`, so a valid nonzero
  remainder requires at most `n - 1` slots. The minimum width of one preserves
  the repository's nonempty fixed-register convention and represents the
  necessarily zero remainder for a constant divisor.
- These capacities are based on declared register widths, so high trailing
  zeros in either input do not change output target widths.

## Source, tests, and public API

Added files:

- `src/dqi_decoder/reversible_division.py`
- `tests/dqi_decoder/test_reversible_division.py`
- `docs/research/DQI_P012_REVERSIBLE_POLYNOMIAL_DIVISION_REPORT.md`

Public API:

```python
MAX_POLYNOMIAL_REGISTER_WIDTH = 8

def xor_accumulate_polynomial_division(
    dividend: PolynomialRegister,
    divisor: PolynomialRegister,
    quotient_target: DivisionTarget,
    remainder_target: DivisionTarget,
) -> tuple[
    PolynomialRegister,
    PolynomialRegister,
    DivisionTarget,
    DivisionTarget,
]:
    ...
```

`PolynomialRegister` is the existing P010 tuple type; `DivisionTarget` is
`tuple[int, ...]`. The returned tuple contains the unchanged dividend and
divisor followed by updated quotient and remainder targets.

The API rejects non-tuples, empty inputs, widths greater than 8, invalid field
elements, and targets with incorrect widths. It does not silently truncate
inputs, outputs, or field values. It is not exported through
`dqi_decoder.__init__`; existing reversible P009–P011 functions follow the
same module-level import pattern.

## Algorithm and reversible register sequence

The implementation scans the divisor for its effective leading nonzero
coefficient without modifying it. It copies the dividend into an initial
remainder scratch register, obtains the leading-coefficient inverse in a
zeroed scratch target using the P009 inverse primitive, then processes quotient
shifts from high to low. At each shift it:

1. Computes the quotient factor by multiplying the current remainder's
   coefficient at the shifted leading position by the divisor-leading
   inverse.
2. Copies the prior quotient and remainder scratch registers into fresh,
   initially zero registers.
3. XOR-accumulates the factor into the new quotient slot.
4. XOR-accumulates each factor-times-divisor coefficient into the new
   remainder register.

The leading coefficient of the divisor is nonzero, so its inverse is defined.
Characteristic two makes subtraction equal to addition. Each fixed shift
cancels the current coefficient at that shift without changing higher
coefficients already processed. The final quotient is padded to the dividend
width; the remainder is checked to fit the target derived above before any
output is accumulated.

After XOR-accumulating the final scratch quotient and remainder into the
caller targets, the implementation reverses the recorded steps in reverse
order: remove divisor-product contributions, clear the remainder copy, remove
the quotient factor, clear the quotient copy, and clear the factor product.
It then clears the initial dividend copy and the leading-coefficient inverse
using the same P009 XOR-target operations. The public API verifies that every
scratch element is zero and raises `RuntimeError` if an invariant fails; it
does not assign zero to computed scratch as a substitute for reversal.

The internal step history and scratch allocations are Python-level
simulation. Their degree-dependent schedule and dynamic storage are not a
fixed-layout circuit or a demonstrated gate decomposition.

## P009/P010 dependency traceability

- P010 establishes the nonempty, fixed-width, low-degree-first tuple
  convention and zero-padding behavior.
- P009 supplies `xor_accumulate_add`, `xor_accumulate_multiply`, and
  `xor_accumulate_inverse`. The implementation uses each with a scratch or
  output target, retaining all operands.
- The inverse primitive is applied only to the nonzero effective leading
  divisor coefficient. The P009 totalized zero-input inverse behavior is not
  used to model division by zero.
- The existing classical polynomial division contract is preserved:
  division by zero is invalid, and valid division satisfies the quotient /
  remainder identity and strict remainder-degree bound. The reversible
  function is separate from the classical API and does not alter it.

## Independent correctness oracle

The test module contains independent field multiplication and exponentiation
for inversion, followed by normalized-list polynomial long division. It does
not call the production reversible division function, its scratch helper, or
the existing classical `divide_polynomials`. It computes the quotient and
remainder independently and checks both the polynomial identity and remainder
degree bound.

The oracle and the P012 arithmetic necessarily share the GF(2^12) field
definition: both use the repository modulus `0x1053` and the polynomial-basis
element encoding. The oracle's multiplication and exponentiation are expressed
in test code rather than delegated to production field helpers. Small-field
tests supply test-local GF(2^k) arithmetic callbacks to the same scratch
sequencing helper; this verifies generic register sequencing, not the public
GF(2^12) validator or P009 circuit behavior.

## Small-field bounded exhaustive verification

The tests cover all fixed-width two-coefficient dividend and nonzero divisor
register pairs in each field. For each pair, two deterministic target
initializations are exercised. The dividend and divisor coefficient domains are therefore exhaustive for the
stated two-slot input domain, but target
register states are sampled rather than fully enumerated. The complete
valid-register state space is not claimed to have been exhaustively tested.

| Field | Size | Dividend registers | Nonzero divisor registers | Input pairs | Target cases per pair | Reversible-map cases | Map applications including second pass |
|---|---:|---:|---:|---:|---:|---:|---:|
| GF(2²) | 4 | 16 | 15 | 240 | 2 | 480 | 960 |
| GF(2³) | 8 | 64 | 63 | 4,032 | 2 | 8,064 | 16,128 |
| GF(2⁴) | 16 | 256 | 255 | 65,280 | 2 | 130,560 | 261,120 |
| **Total** | — | — | — | **69,552** | — | **139,104** | **278,208** |

For field size `q`, the complete target-inclusive valid state domain with
these widths has `(q^4 - q^2) × q^3` states: 15,360 for GF(2²), 2,064,384
for GF(2³), and 267,386,880 for GF(2⁴). The harness does not enumerate those
complete state domains. Its two deterministic target seeds are `t ∈ {0, 1}`,
`TQ = (a0 XOR b0 XOR t, a1 XOR b1 XOR t)`, and
`TR = (a0 XOR b1 XOR t)`.

For each reversible-map case the harness checks the independently computed
quotient and remainder, input preservation, XOR target accumulation,
`A = BQ + R`, the remainder-degree condition, zeroed scratch after forward /
reverse cleanup, and a second application returning both targets to their
initial values. It also checks output-state uniqueness over the enumerated
subset. This is bounded exhaustive enumeration, not exhaustive enumeration of
all target values or all full register states.

## GF(2^12) deterministic coverage

The production API tests cover zero dividend, constant and nonconstant
divisors, dividend degree below / equal to / above divisor degree, exact and
nonzero-remainder divisions, sparse and dense inputs, nonmonic divisors,
trailing zero coefficients, maximum valid field values, arbitrary target
contents, repeated accumulation, input preservation, and maximum supported
register widths (8). Invalid cases cover empty and oversized inputs, wrong
target widths, non-tuple registers, booleans, negative values, and values
outside GF(2^12). The zero-divisor case confirms rejection before output
targets can be changed.

These are deterministic examples; they are not exhaustive over GF(2^12).

## Reproduced tests and checks

All commands ran from the repository root. `PYTHONPATH=src` is required in
this checkout to import the package.

| Scope | Command | Result | Runtime |
|---|---|---|---:|
| P012 focused | `PYTHONPATH=src python -m pytest -q tests/dqi_decoder/test_reversible_division.py` | 7 passed; 17 subtests passed; 0 failed / skipped | 6.70 s |
| P011 | `PYTHONPATH=src python -m pytest -q tests/dqi_decoder/test_reversible_evaluation.py` | 7 passed; 27 subtests passed; 0 failed / skipped | 1.35 s |
| P010 | `PYTHONPATH=src python -m pytest -q tests/dqi_decoder/test_reversible_polynomial.py` | 6 passed; 28 subtests passed; 0 failed / skipped | 0.74 s |
| P009 | `PYTHONPATH=src python -m pytest -q tests/dqi_decoder/test_reversible_primitives.py` | 9 passed; 33 subtests passed; 0 failed / skipped | 0.62 s |
| Classical regressions | `PYTHONPATH=src python -m pytest -q tests/dqi_decoder/test_field.py tests/dqi_decoder/test_polynomial.py tests/dqi_decoder/test_decoder.py tests/dqi_decoder/test_syndrome.py` | 37 passed; 5,411 subtests passed; 0 failed / skipped | 10.46 s |

`python -m py_compile` succeeded for the new source and test modules. `git diff
--check` was attempted, but reports the pre-existing README line-ending/BOM
diff as trailing whitespace; that README was not edited. No new dependency or
static-analysis tool was added. `ruff`, `mypy`, `pylint`, and `pyright` are not
available in this environment.

## Preservation and limitations

- No P009, P010, P011, classical decoder, field, polynomial, syndrome,
  `__init__.py`, or INVSQRT source was edited.
- Fingerprints for the pre-existing P011, P010, field, polynomial, and README
  files matched the previously recorded audit baseline.
- Branch and HEAD remained `feat/dqi-decoder` and
  `5391b2e7123484efacffc0588f5e761e67b5cb55`.
- The existing README working-tree change remains present. P001–P011 reports,
  source/tests, and unrelated untracked artifacts remain in the worktree.
- This model has a deliberately bounded maximum input width of 8. Increasing
  that limit requires reconsidering scratch growth and runtime.
- The small-field test callbacks exercise the shared register-sequencing
  implementation; GF(2^12) public behavior is validated separately against
  the independent polynomial oracle.
- No quantum circuit, gate-level reversibility, official verifier
  compatibility, or competition readiness is established.

## P013 prerequisites

Before any next polynomial algorithm phase, retain the fixed-width,
low-degree-first input convention and explicitly choose its output capacities
and invalid-input behavior. A subsequent reversible Euclidean algorithm
should specify:

1. How quotient and remainder registers are sized per iteration.
2. How the nonzero-divisor invariant is maintained and how zero divisors are
   rejected.
3. Which prior remainders and quotient factors must be retained for reverse
   cleanup.
4. Whether the width-eight P012 cap is retained, changed, or replaced by a
   bounded iteration contract.
5. An independent reference oracle and bounded exhaustive small-field domains
   that distinguish sampled target values from full-state enumeration.

P012 does not implement EEA or any later decoder operation.
