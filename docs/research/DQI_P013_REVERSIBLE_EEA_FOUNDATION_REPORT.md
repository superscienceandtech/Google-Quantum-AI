# P013 — Reversible EEA Single-Step Foundation

## 1. Executive summary and status

P013 adds one bounded, input-preserving polynomial extended-Euclidean
transition over the repository's GF(2^12). Given six polynomial registers
`(r0, r1, s0, s1, t0, t1)`, it computes the quotient `q`, next remainder
`r2`, and updated Bézout coefficients `s2,t2`, XOR-accumulating them into
four separate targets. It preserves all six input registers, validates
capacities, rejects a zero current remainder, checks the division identity,
and reverses its modeled scratch computations.

The P013 focused suite and all required P012-P009 and classical regression
suites pass. This is a bounded Python register-state model, not an EEA
iteration loop, quantum circuit, gate sequence, or circuit-level reversibility
proof.

**P013 status: PASS for the bounded single-transition mathematical and
classical register-model scope.** The paper-parameter EEA width remains
unsupported.

## 2. Repository baseline

| Item | Audit-start value |
|---|---|
| Repository root | `/mnt/d/PROJECT/Quantum_AI/Google-Quantum-AI` |
| Branch | `feat/dqi-decoder` |
| HEAD | `5391b2e7123484efacffc0588f5e761e67b5cb55` |
| Staged changes | None |
| Tracked modifications | Pre-existing `README.md` only |
| Existing untracked work | P001-P012 artifacts, DQI source/tests, INVSQRT bytecode caches, and other DQI work |

No branch, commit, index, or existing project file was changed.

## 3. Inspected artifacts and actual APIs

Inspected the P012→P013 handoff, P012 division source/tests/report, P011
evaluation source/tests/report, P010 polynomial source/tests/report, P009
primitive source/tests/report, P008 reversible decoder specification,
`field.py`, `polynomial.py`, `decoder.py`, and the classical field and
polynomial tests.

Relevant contracts observed in source:

- `xor_accumulate_polynomial_division(dividend, divisor, quotient_target,
  remainder_target)` returns both unchanged input registers and both updated
  targets. Its inputs are nonempty tuples, each at most 8 coefficients.
  Quotient width is `len(dividend)` and remainder width is
  `max(1, len(divisor) - 1)`.
- `xor_accumulate_polynomial_add(left, right, target)` preserves its operands,
  pads the shorter input with zeros, and requires target width equal to the
  larger operand width.
- `xor_accumulate_polynomial_multiply(left, right, target)` preserves its
  operands, requires target width `len(left) + len(right) - 1`, and does not
  truncate product coefficients.
- P009 field helpers preserve field operands and XOR-accumulate results into
  a target. Field addition is bitwise XOR in characteristic two.
- The field representation is polynomial-basis integers in `[0, 4095]` with
  modulus `0x1053`.
- Classical `polynomial.py` normalizes away trailing high-degree zeroes and
  represents zero by `()`. Reversible register APIs instead require nonempty
  fixed-width tuples; an all-zero tuple is the zero polynomial.

New public API:

```python
def xor_accumulate_eea_transition(
    r0: PolynomialRegister,
    r1: PolynomialRegister,
    s0: PolynomialRegister,
    s1: PolynomialRegister,
    t0: PolynomialRegister,
    t1: PolynomialRegister,
    quotient_target: EEATarget,
    remainder_target: EEATarget,
    s2_target: EEATarget,
    t2_target: EEATarget,
) -> tuple[
    PolynomialRegister,
    PolynomialRegister,
    PolynomialRegister,
    PolynomialRegister,
    PolynomialRegister,
    PolynomialRegister,
    EEATarget,
    EEATarget,
    EEATarget,
    EEATarget,
]: ...
```

`PolynomialRegister` is P010's `tuple[int, ...]` alias. `EEATarget` is
`tuple[int, ...]`. The package `__init__.py` was not changed; prior reversible
P009-P012 APIs are module-level imports as well.

## 4. Mathematical recurrence and initialization

The single transition uses the standard polynomial EEA relation over
GF(2^12):

```text
r0 = q*r1 + r2
r2 = r0 + q*r1
s2 = s0 + q*s1
t2 = t0 + q*t1
```

The plus signs are polynomial addition over a characteristic-two field:
coefficient-wise GF(2^12) addition is XOR. P012 computes `q` and `r2`; P010
computes the polynomial products and sums for the Bézout updates.

The conventional generic EEA initialization is:

```text
r0=A, r1=B
s0=1, s1=0
t0=0, t1=1
```

It establishes the invariant `r_i = s_i*A + t_i*B`; the transition preserves
that invariant because the same quotient recurrence is applied to the
remainder and both coefficient sequences. The public function accepts any
six valid registers; it does not assert that they came from this initialization
or satisfy a Bézout invariant. The conventional-state test independently
checks the invariant.

The P008 specification describes the EEA key equation using the polynomial
`z^(2ell)` and syndrome polynomial `S(z)`, terminating when the remainder
degree falls below `ell`. Its report describes synchronized remainder and
Bézout storage, temporary quotient values, degree pointers, and later EEA
uncomputation. P008 does not establish a local reversible step API or complete
register-level recurrence schedule. P013 implements the generic recurrence
above; it does not claim to implement that synchronized circuit architecture,
its initialization details as a paper-specific requirement, its iteration
schedule, or its termination logic.

## 5. Input/output register contract

The transformation is:

```text
|r0>|r1>|s0>|s1>|t0>|t1>|Tq>|Tr>|Ts>|Tt>
  ->
|r0>|r1>|s0>|s1>|t0>|t1>
|Tq XOR q>|Tr XOR r2>|Ts XOR s2>|Tt XOR t2>
```

All six input tuples are returned with the same values and declared widths.
All output targets are validated before any computation. Updated targets are
computed locally as new immutable tuples and XOR-accumulated; caller-owned
tuples are never mutated or overwritten.

Invalid containers raise `TypeError`; empty or over-width inputs, incorrect
target widths, and invalid field values are rejected. Zero `r1` raises
`ZeroDivisionError` before computation. Zero `r0` is valid and produces zero
quotient and remainder. If `degree(r0) < degree(r1)`, the quotient is zero and
the remainder is `r0` padded to its required fixed target width. Equal-degree
and nonmonic `r1` cases are supported through leading-coefficient
normalization in P012. Zero `s`/`t` registers are valid.

## 6. Fixed-width representation and capacities

All six input polynomial registers are nonempty low-degree-first tuples of
GF(2^12) elements and each has a maximum width of 8. This follows P012's
public input limitation and does not modify or bypass that limit.

Target capacities are derived as follows:

| Register | Exact capacity | Maximum |
|---|---:|---:|
| Quotient target `Tq` | `len(r0)` (P012 division contract) | 8 |
| Remainder target `Tr` | `max(1, len(r1)-1)` (P012 division contract) | 7 |
| First Bézout target `Ts` | `max(len(s0), len(r0)+len(s1)-1)` | 15 |
| Second Bézout target `Tt` | `max(len(t0), len(r0)+len(t1)-1)` | 15 |

The Bézout widths cover the full P010 product width of the padded quotient
and an input coefficient register. Addition uses the larger of that product
and the prior coefficient width. The operation rejects wrong target widths;
no coefficient is silently truncated.

P008's cited parameterization uses `n=70, ell=35`; `z^(2ell)` needs 71
coefficient slots, and `S(z)` can use up to 70. Both exceed P012's width-8
input bound. P013 is a bounded prototype and does not support or claim the
paper-parameter instance.

## 7. Zero and invalid-input semantics

- `r1` must be a nonzero polynomial. An all-zero `r1` tuple raises
  `ZeroDivisionError`.
- `r0` may be zero. A valid zero dividend yields zero quotient and remainder.
- Empty tuples are invalid fixed-width registers; nonempty all-zero tuples
  represent zero.
- Trailing zero coefficients are retained; effective degree is determined
  by P012's highest nonzero coefficient search.
- Bézout inputs may be zero and are not required to satisfy a supplied
  history/invariant.
- All field elements and all four targets are validated before output
  accumulation. No invalid input can produce externally visible partial
  target mutation.

## 8. Forward computation, accumulation, and reverse cleanup

The internal helper starts named scratch registers at zero:

1. `quotient` and `remainder`: P012's reversible division relation computes
   `q` and `r2`. P012 itself reverses and verifies its internal workspace.
2. `identity_product`: P010 computes `q*r1`.
3. `identity_reconstruction`: P010 adds that product and `r2`; P013 compares
   it with padded `r0` and raises `ArithmeticError` if the relation fails.
4. `s_product` and `s_update`: P010 computes `q*s1`, then adds `s0`.
5. `t_product` and `t_update`: P010 computes `q*t1`, then adds `t0`.
6. Four caller targets XOR-accumulate the corresponding scratch outputs.

Reverse cleanup applies those XOR-accumulating operations in reverse
dependency order: clear `t_update`, `t_product`, `s_update`, `s_product`,
`identity_reconstruction`, and `identity_product`, then call the same P012
division transformation again to clear `quotient` and `remainder`. The helper
returns the named scratch registers for inspection; the public function
verifies each is all zero and raises `RuntimeError` if cleanup fails.
Computed scratch is not assigned zero as a substitute for reverse operations.

This is a Python-level simulation using ordinary calls, tuples, dictionaries,
and control flow. P012 performs its own scratch lifecycle internally. The
returned clean scratch evidence does not establish a quantum circuit,
reversible gate sequence, phase behavior, or gate-level proof.

## 9. Independent oracle and limitations

The test module independently implements field multiplication by carryless
shift/XOR followed by polynomial reduction, field inversion by exponentiation,
normalized-list polynomial long division, polynomial multiplication, and
coefficient addition. Expected quotient, remainder, and Bézout updates are
computed without calling the production P013 transition, P012 division,
P010 polynomial helpers, or production field functions.

The oracle shares the mathematical field modulus `0x1053` and the established
polynomial-basis interpretation with production. Its multiplication procedure
is test-local and structurally distinct from the production shift-and-reduce
field loop, but inversion uses the standard finite-field exponent
`2^k-2`. Small-field register-sequence callbacks reuse the test-local
reference arithmetic; they test sequence logic separately from GF(2^12)
production operations, not via a second independent small-field arithmetic
implementation.

## 10. Small-field test domain and exact counts

For each field GF(2²), GF(2³), GF(2⁴), both `r0` and `r1` are all tuples of
width two. The test enumerates every `r0` and every nonzero `r1`; thus it
exhausts the declared remainder-pair domain, including all-zero `r0`, all
nonzero divisor coefficient combinations, nonmonic leading coefficients,
and every effective degree. Bézout states are the explicitly bounded
two-element set:

1. `s0=s1=t0=t1=(0,)`.
2. Conventional initialization coefficients `(s0,s1,t0,t1)=((1,),(0,),(0,),(1,))`.

There is one deterministic target initialization per remainder-pair /
Bézout-state case. The map is then applied again to check XOR restoration.
The targets are selected, not exhaustively enumerated.

| Field | Size `q` | `r0` tuples | Nonzero `r1` tuples | Remainder pairs | Bézout states | Target initializations per combination | Transition cases |
|---|---:|---:|---:|---:|---:|---:|---:|
| GF(2²) | 4 | 16 | 15 | 240 | 2 | 1 | 480 |
| GF(2³) | 8 | 64 | 63 | 4,032 | 2 | 1 | 8,064 |
| GF(2⁴) | 16 | 256 | 255 | 65,280 | 2 | 1 | 130,560 |
| **Total** | — | — | — | **69,552** | — | — | **139,104** |

The suite performs 278,208 transition applications including the second
application for restoration. It checks oracle equality and scratch cleanup
for every selected case. This is exhaustive over the stated remainder-pair
domain and the declared two-state Bézout subset, but not exhaustive over all
possible Bézout coefficient registers, target values, or complete scratch
states.

## 11. GF(2^12) deterministic production coverage

The focused tests include:

- Conventional initialization and independent Bézout invariant check.
- Zero `r0`, zero `r2`, nonzero remainder, lower-degree, equal-degree, and
  nonmonic divisor cases.
- Multiple quotient coefficients and nonzero Bézout updates.
- All-zero Bézout coefficient state.
- Arbitrary nonzero values in all four targets and repeated target
  restoration.
- All six inputs at maximum width 8, Bézout targets at width 15, and
  quotient/remainder targets at their maximum widths.
- Zero `r1`, empty and over-width inputs, invalid field values, and
  incompatible target capacities.

These are deterministic examples, not exhaustive GF(2^12) coverage.

## 12. Test commands and results

Commands ran from the repository root with bytecode and pytest cache creation
disabled to preserve existing untracked artifacts.

| Scope | Command | Result | Runtime |
|---|---|---|---:|
| P013 | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q tests/dqi_decoder/test_reversible_eea.py` | 5 passed; 11 subtests; 0 failed / skipped | 12.48 s |
| P012 | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q tests/dqi_decoder/test_reversible_division.py` | 7 passed; 17 subtests; 0 failed / skipped | 8.12 s |
| P011 | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q tests/dqi_decoder/test_reversible_evaluation.py` | 7 passed; 27 subtests; 0 failed / skipped | 1.00 s |
| P010 | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q tests/dqi_decoder/test_reversible_polynomial.py` | 6 passed; 28 subtests; 0 failed / skipped | 0.36 s |
| P009 | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q tests/dqi_decoder/test_reversible_primitives.py` | 9 passed; 33 subtests; 0 failed / skipped | 0.33 s |
| Classical regressions | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q tests/dqi_decoder/test_field.py tests/dqi_decoder/test_polynomial.py tests/dqi_decoder/test_decoder.py tests/dqi_decoder/test_syndrome.py` | 37 passed; 5,411 subtests; 0 failed / skipped | 11.95 s |

No pytest warnings were emitted. A Python AST syntax check passed for the new
source and test modules. `ruff`, `mypy`, `pylint`, and `pyright` are
unavailable; none were installed.

`git diff --check` reports trailing whitespace only on the pre-existing
README BOM/line-ending diff. No trailing whitespace was found in the new
P013 source, test, or report.

## 13. P008 relationship

| Requirement | P008 paper/report evidence | P013 implementation | Status |
|---|---|---|---|
| EEA state convention | P008 describes EEA on `z^(2ell)` and `S(z)`, and its Bézout/locator relationship; no exact local one-step API is supplied | Generic `(r0,r1,s0,s1,t0,t1)` transition; conventional `(A,B,1,0,0,1)` initialization is tested | Generic recurrence implemented; paper-specific state mapping remains unestablished |
| Polynomial operand widths | P008 reports `z^(2ell)` and `S(z)` at `n=70, ell=35` | P012 dependency caps every input at width 8 | **Incompatible** with 71-/up-to-70-slot paper operands |
| Quotient/remainder semantics | P008 cites EEA and quotient storage; local classical division defines standard quotient/remainder | Reuses P012's nonzero-divisor polynomial division contract | Bounded mathematical step supported |
| Bézout tracking | P008 describes synchronized remainder/Bézout registers | Computes `s0+q*s1`, `t0+q*t1` in separate targets | Generic update implemented; synchronized register aliasing not implemented |
| Iteration/termination | P008 identifies degree threshold `deg(r)<ell` and reports a 222-step synchronized schedule for its stated parameters | One step only; no loop or stop condition | No complete EEA termination claim |
| Scratch/history | P008 describes temporary quotient storage and degree pointers | Named Python scratch for q, r2, products, updates, and identity check | Local simulation only; paper pointer/history schedule not implemented |
| Cleanup | P008 requires later EEA uncomputation and syndrome restoration | Reverses this one-step scratch and checks zeros | Single-step model evidence only |
| Paper-parameter readiness | Paper source describes the `n=70` instance | Width 8 P012 public dependency rejects its operands | Not supported |

P008 is evidence for algorithmic motivation and cleanup requirements, not
for P013's exact schedule or a local circuit. The single-step prototype does
not validate P008's full synchronized EEA architecture.

## 14. Files and preservation evidence

Created:

- `src/dqi_decoder/reversible_eea.py`
- `tests/dqi_decoder/test_reversible_eea.py`
- `docs/research/DQI_P013_REVERSIBLE_EEA_FOUNDATION_REPORT.md`

Modified existing files: none. Deleted files: none. No package export,
dependency, P009-P012 artifact, classical decoder behavior, README, or
INVSQRT artifact was changed.

At final verification, repository root, branch, and HEAD matched baseline.
No staged changes were present; the pre-existing README remained the only
tracked modification. P009-P012 source, tests, reports, classical DQI source
and tests, P008-P011 reports, and INVSQRT fingerprints matched their
audit-start fingerprints. Existing untracked paths were preserved.

## 15. Limitations and next prerequisites

- Input polynomial width is capped at 8, inherited from P012.
- Bézout outputs can be up to 15 coefficients because they use full P010
  product width.
- The API does not enforce that input coefficients correspond to an EEA
  history; the Bézout invariant is conditional on valid initialization.
- The API performs one transition only. It has no iteration loop, variable
  termination record, normalized locator/evaluator output, or paper-specific
  synchronized register schedule.
- P008's 71-/up-to-70-slot operands cannot pass the current P012 validator.
- No quantum circuit, gate decomposition, circuit-level reversibility,
  official verifier compatibility, or competition readiness is established.

Further work would need an explicitly bounded iteration/state contract,
capacity strategy, history/control-state design, termination semantics, and
an independent audit before a full EEA implementation is considered.

## 16. Acceptance criteria

| Criterion | Result |
|---|---|
| Recurrence is consistent with the declared generic EEA state convention | **PASS** |
| Independent quotient/remainder and Bézout oracle agrees | **PASS** |
| Division identity and remainder-degree condition are checked | **PASS** |
| Six input registers are preserved | **PASS** |
| Four output targets use XOR accumulation | **PASS** |
| Invalid inputs and zero `r1` reject before caller-visible mutation | **PASS** |
| Scratch updates are reversed and zero state is checked | **PASS** |
| Small-field domains and 139,104 transition count are reproducible | **PASS** |
| GF(2^12) deterministic cases pass | **PASS** |
| P009-P012 and classical regression suites pass | **PASS** |
| P008 differences and paper-width incompatibility documented | **PASS** |
| Existing user work and baseline preserved | **PASS** |
| Circuit-level reversibility and verifier compatibility established | **NOT ESTABLISHED** |

## Final status

**PASS — the bounded single-step EEA mathematical and classical
register-model acceptance criteria pass.** This does not establish
circuit-level reversibility, gate decomposition, the P008 paper-parameter
instance, official verifier compatibility, or competition readiness. P014
and the full iterative EEA were not started.
