# DQI-P016 — Capacity-Generalized Reversible EEA Single-Step

## 1. Execution summary and status

P016 adds a separate capacity-aware single-step EEA register API to
`reversible_eea.py`. It computes the quotient and remainder through the
existing P015 division primitive and computes both Bézout updates using the
existing P010 polynomial add/multiply facilities. It preserves all six
input tuples, XOR-accumulates four outputs, validates every input and target
before computation, and checks that the modeled scratch state is zero after
the compute/accumulate/uncompute sequence.

The existing `xor_accumulate_eea_transition` API and its eight-slot input
limit remain unchanged for P013 callers. The new API has role-specific
limits and does not infer a valid standard-EEA history from arbitrary
registers. Its output widths follow P015/P010 declared-width APIs, not the
narrower significant-support bounds that hold only under P014's standard
EEA initialization and invariants.

**Final status: PASS — for the declared bounded, classical single-step
register contract and its tested arithmetic.** P016 does not implement a
multi-round EEA, enforce the standard EEA invariant, provide P008's shared
array schedule, or establish gate-level quantum reversibility.

## 2. Repository baseline and preservation

| Item | Before | After |
|---|---|---|
| Root | `/mnt/d/PROJECT/Quantum_AI/Google-Quantum-AI` | unchanged |
| Branch | `feat/dqi-decoder` | `feat/dqi-decoder` |
| HEAD | `5391b2e7123484efacffc0588f5e761e67b5cb55` | unchanged |
| Staged paths | 0 | 0 |
| Tracked modifications | Existing `README.md` only | same |
| Existing untracked paths | 85 | 86, adding this report |

The README SHA-256 remained
`6fc9e83d0fb74d8f163fbd1c0fb0d0da246bd33e218e86ee56bd78ec15379027`.
Its existing diff was preserved. P001–P015 artifacts, P015 division
source/tests/report, P009–P011 dependencies, and INVSQRT work were not
modified or deleted. The only files changed or created for P016 are listed
in §13. No dependencies were added, and no branch or Git-history operation
was performed.

## 3. Actual artifacts inspected

Read the live P014 capacity contract; P015 execution report; P015 division
implementation and tests; P013 EEA implementation, tests, and report;
P013→P014 handoff; P009 primitive module/report; P010 polynomial module/
report; P011 evaluation module/report; P008 reversible decoder
specification; and the shared field representation.

The inspection verified these repository conventions:

- Field elements are integers in `[0,4095]`, polynomial-basis encoded for
  GF(2^12), with modulus `0x1053`; field addition is XOR.
- Polynomial tuples are low-degree first; tuple index zero is the constant
  coefficient.
- Reversible polynomial registers are nonempty fixed-width tuples.
  All-zero tuples represent zero; trailing zero padding is retained.
- P009 field operations preserve their operands and XOR the result into the
  target.
- P010 addition uses the maximum declared operand width. P010 multiplication
  requires the full declared convolution width `len(left)+len(right)-1`.
- P013's existing public API validates all six inputs at no more than eight
  coefficients and uses exact, declared-width targets.

## 4. P014/P015 capacity reconciliation

P014 derives mathematical support bounds for the standard EEA state on
`A=z^70`, nonzero syndrome `B=S(z)` of degree at most 69, stopping below
threshold 35:

| EEA role | P014 mathematical capacity |
|---|---:|
| Remainder state, including initial `A` | 71 |
| Active quotient significant support | 36 |
| `s` coefficient state and `q*s` support | 35 |
| `t` coefficient state and `q*t` support | 36 |
| Active divisions | at most 35 |

These are invariant-dependent significant-support and iteration bounds;
they are not generic limits for arbitrary six-tuples or full-width
convolution buffers.

The actual P015 source confirms maximum input widths of 71 dividend slots
and 70 divisor slots. Its quotient target width is exactly the declared
dividend width (up to 71); its remainder target is
`max(1, len(divisor)-1)` (up to 69). P015 does not return a compact
36-coefficient quotient target in the threshold-specific case. The P015
focused tests exercise these boundaries and pass.

Therefore P016 uses:

- 71/70 slots for `r0/r1` to match P015;
- P014's 35/36-slot capacities for input coefficient roles `s0/s1` and
  `t0/t1`;
- full P010/P015 declared-width target sizing, even where this exceeds
  P014's invariant-derived significant support.

For maximum P016 input widths, P015's quotient tuple is 71 slots even if
its significant support is at most 36 in a standard thresholded step.
Consequently, full declared-width products are:

```text
q*r1: 71 + 70 - 1 = 140 slots
q*s1: 71 + 35 - 1 = 105 slots
q*t1: 71 + 36 - 1 = 106 slots
```

The P014 document's comparison includes a 141-slot `q*r` product when both
operands are declared 71 slots. P016's `r1` input is explicitly limited to
70 slots, so its corresponding maximum is 140. Neither bound is silently
truncated. The 105/106 Bézout output targets can contain high zero padding
and are not claims that the mathematical EEA coefficient degree is that
large. Such wide output tuples are not directly acceptable as the next
transition's 35/36-slot coefficient inputs.

## 5. P016 exact register capacities

The new public API is
`xor_accumulate_capacity_aware_eea_transition` in
`src/dqi_decoder/reversible_eea.py`. It accepts optional keyword-only,
per-call limits; each limit must be an exact integer from one through its
hard maximum. A caller may restrict a role's width but cannot raise the
declared maximum.

| Register | Default maximum / target rule | Basis |
|---|---:|---|
| Input `r0` | 71 | P015 dividend maximum |
| Input `r1` | 70 | P015 divisor maximum; must be nonzero |
| Inputs `s0`, `s1` | 35 each | P014 thresholded `s` storage capacity |
| Inputs `t0`, `t1` | 36 each | P014 thresholded `t` storage capacity |
| Quotient target `Tq` | Exactly `len(r0)`, at most 71 | P015 quotient target rule; covers constant-divisor quotient |
| Remainder target `Tr` | Exactly `max(1,len(r1)-1)`, at most 69 | P015 remainder target rule |
| `s2` target | `max(len(s0),len(r0)+len(s1)-1)`, at most 105 | Full declared-width P010 product plus `s0` |
| `t2` target | `max(len(t0),len(r0)+len(t1)-1)`, at most 106 | Full declared-width P010 product plus `t0` |

All six input tuples and four target tuples must be nonempty tuples of valid
GF(2^12) elements. A target with a width other than the exact formula is
rejected. Zero `r1` raises `ZeroDivisionError` after input and target
validation and before any result is returned. Zero `r0`, zero coefficient
tuples, degree-smaller dividends, and leading-zero-padded registers follow
the existing P015/P010 conventions.

The `s2` and `t2` maxima intentionally follow the P010 full declared-width
convolution contract. They are conservative for arbitrary inputs in the
declared domain and do not assume the standard EEA invariant. The output
capacity is exactly the computation's full target width, so it cannot
truncate a valid product.

## 6. Implementation and API changes

`_validate_polynomial` now accepts an optional maximum-width argument whose
default remains `MAX_POLYNOMIAL_REGISTER_WIDTH` (8). This preserves the
legacy P013 public function unchanged. The new API defines role-specific
maximum constants, validates its four width parameters, validates all six
inputs and all four targets, then invokes the existing shared
compute/accumulate/uncompute helper.

The helper uses:

1. P015 `xor_accumulate_polynomial_division` with zero-initialized quotient
   and remainder scratch targets.
2. P010 polynomial multiplication and addition for the `q*r1` reconstruction
   check, `s0+q*s1`, and `t0+q*t1`.
3. XOR accumulation into local target results.
4. The same operations in reverse dependency order to clear the update,
   product, reconstruction, quotient, and remainder scratch registers.
5. A final zero-scratch check at the public entry point.

No P013 target argument meaning or behavior changed. P013 still uses its
existing `xor_accumulate_eea_transition` API and eight-slot inputs; P016
callers must opt into the new function.

## 7. Input preservation, targets, and failure behavior

All input and target objects are tuples and are validated into local tuple
values. P015 and P010 return preserved operand tuples; outputs are new
tuples and caller-owned registers are never mutated. Results are returned
only after computation, reversal, and the zero-scratch check succeed, so an
invalid width, target, element, zero divisor, arithmetic inconsistency, or
scratch failure cannot expose partially updated caller targets.

The independent test helper checks:

```text
r0 = q*r1 + r2
s2 = s0 + q*s1
t2 = t0 + q*t1
```

It also verifies the remainder-degree condition, all six preserved input
tuples, XOR accumulation into nonzero targets, and restoration when the
same transition is applied a second time to the updated targets.

## 8. Independent oracle and bounded exhaustive tests

The test-local oracle implements GF multiplication using carryless
shift/XOR and reduction, field inversion by exponentiation, normalized-list
polynomial long division, coefficient-wise polynomial addition, and
polynomial convolution. It does not call either production EEA transition,
P015 division, P010 polynomial multiplication, or production field
multiplication to produce expected values.

The shared mathematical conventions are GF(2^12) modulus `0x1053`,
polynomial-basis field encoding, low-degree-first coefficients, XOR
addition, and the nonempty fixed-width register zero convention. The small
fields use their corresponding independent test moduli.

For small-field exhaustive runs, the production orchestration helper is
exercised with test-local division/add/multiply operations parameterized
for GF(2²), GF(2³), and GF(2⁴). Expected complete transitions are computed
separately by the test oracle. Each two-coefficient remainder input pair
(`r0` arbitrary, `r1` nonzero) is crossed with two selected Bézout-state
configurations and deterministic target values. The test checks all four
outputs, repeated target accumulation, and scratch cleanup.

| Field | Input pairs | Bézout states per pair | Whole transitions |
|---|---:|---:|---:|
| GF(2²) | 240 | 2 | 480 |
| GF(2³) | 4,032 | 2 | 8,064 |
| GF(2⁴) | 65,280 | 2 | 130,560 |
| **Total** | **69,552** | — | **139,104** |

The input-pair enumeration is exhaustive for the two-coefficient remainder
registers. Bézout states and target registers are selected, not exhaustively
enumerated; this is not complete register-state enumeration. These
small-field tests exercise the orchestration with independent arithmetic
callbacks, not the hard-wired GF(2^12) public API.

## 9. GF(2^12) boundary coverage

The P016 production API tests include:

- Small-width mixed-degree transition with nonzero initial targets.
- Intermediate widths: 35-slot `s` registers, 36-slot `t` registers, and
  35/17-slot remainder operands.
- Maximum inputs: 71-slot `r0`, 70-slot `r1`, 35-slot `s0/s1`, and 36-slot
  `t0/t1`.
- Maximum full-convolution output targets of 105 and 106 slots.
- A P014 threshold case where `r0=z^70` and `deg(r1)=35`; the quotient's
  mathematical degree is 35, while P015's fixed quotient register remains
  71 slots.
- A nonzero constant `r1` case at maximum widths, exercising the maximum
  quotient-shift count and proving the 71-slot quotient target boundary.
- Inputs larger than P013's former eight-slot maximum.
- Zero divisor, invalid target width, over-capacity role inputs, and
  invalid per-call capacity values.

These are deterministic GF(2^12) cases, not exhaustive production-field
coverage.

## 10. Scratch cleanup evidence and limits

The P016 helper's maximum modeled scratch for the declared input limits is
842 field-element slots:

| Scratch value | Maximum slots |
|---|---:|
| Quotient | 71 |
| Remainder | 69 |
| `q*r1` identity product | 140 |
| Identity reconstruction | 140 |
| `q*s1` product | 105 |
| `s2` update | 105 |
| `q*t1` product | 106 |
| `t2` update | 106 |
| **Total** | **842** |

P015 additionally uses its own division scratch. Its source-shaped bound is
10,296 field-element slots at the worst accepted division shape (71-slot
dividend and an effective constant divisor); an EEA step with a 70-slot
divisor has a smaller shift count when that divisor's effective degree is
high. These are counts of Python modeled field-element slots, not qubits or
physical ancillas.

The EEA scratch is cleared by replaying the reversible P009/P010/P015
relations in reverse order; scratch is not cleared by assigning zeros to
nonzero intermediate values. The tests inspect the returned helper scratch
and the public API refuses to return if any scratch register remains
nonzero. This is evidence for the Python register model only. It is not a
gate-level uncomputation, phase, or circuit-resource proof.

## 11. P013/P015 compatibility and test reproduction

Commands were run from the repository root with bytecode and pytest-cache
creation disabled.

| Suite | Exact command | Result | Runtime |
|---|---|---|---:|
| P016 + existing P013 | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q tests/dqi_decoder/test_reversible_eea.py` | 9 passed; 18 subtests; 0 failed; 0 skipped; no warnings | 25.64 s |
| P015 division | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q tests/dqi_decoder/test_reversible_division.py` | 10 passed; 20 subtests; 0 failed; 0 skipped; no warnings | 7.82 s |
| P009 primitives | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q tests/dqi_decoder/test_reversible_primitives.py` | 9 passed; 33 subtests; 0 failed; 0 skipped; no warnings | 0.27 s |
| P010 polynomial arithmetic | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q tests/dqi_decoder/test_reversible_polynomial.py` | 6 passed; 28 subtests; 0 failed; 0 skipped; no warnings | 0.39 s |
| P011 evaluation | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q tests/dqi_decoder/test_reversible_evaluation.py` | 7 passed; 27 subtests; 0 failed; 0 skipped; no warnings | 0.93 s |

The first EEA test run exposed an incorrect test expectation that the fixed
quotient tuple itself would be 71 entries or that the maximum remainder
target always has 69 entries. The test expectations were corrected:
significant quotient output is checked separately from P015's 71-slot
target, and the remainder target is based on the actual declared divisor
width. The reproduced final run is fully passing.

AST parsing passed for the changed source and test modules. `ruff`, `mypy`,
`pylint`, and `pyright` were unavailable; no static analyzer configuration
was found at the repository root or one directory below, and no tooling was
installed. `git diff --check` reports the existing README BOM/line-ending
diff as trailing whitespace. The P016 source, test, and report were checked
separately and contain no trailing whitespace.

## 12. Unsupported P008 requirements and unresolved assumptions

1. P016 is a single transition only. It does not initialize, iterate, or
   terminate EEA.
2. The API accepts arbitrary six-tuples within role capacities; it does not
   validate the standard EEA initialization, Bézout invariant, operand
   degree ordering, threshold stop rule, or round count.
3. P014's 35/36 coefficient support guarantees apply only to the standard
   thresholded EEA state. P016 uses those as maximum input storage widths
   but sizes full-width outputs from P015/P010. The 105/106-slot output
   tuples are therefore not proven to be valid next-step `s`/`t` inputs.
4. P008's shared two-array register assignment, degree pointers, temporary
   quotient lifecycle, synchronized 222-step schedule, and complete
   uncomputation remain unimplemented and unreconciled with these Python
   scratch allocations.
5. P008's paper-level locator/evaluator output convention and
   zero-syndrome behavior remain unresolved in the inspected artifacts.
6. No quantum circuit, gate decomposition, official verifier compatibility,
   or competition readiness has been established.

## 13. Files changed

Modified:

- `src/dqi_decoder/reversible_eea.py`
- `tests/dqi_decoder/test_reversible_eea.py`

Created:

- `docs/research/DQI_P016_CAPACITY_GENERALIZED_REVERSIBLE_EEA_SINGLE_STEP_REPORT.md`

Deleted: none.

P008–P015 historical reports, P015 implementation/tests, README, dependencies,
and unrelated INVSQRT work were preserved.

## 14. Acceptance criteria

| Criterion | Result |
|---|---|
| Explicit, justified per-register capacities | **PASS**, with invariant-dependent versus declared-width bounds distinguished |
| P015 division used within its verified limits | **PASS** |
| Four outputs match independent expected arithmetic | **PASS** |
| Six input registers preserved | **PASS** |
| Four targets XOR-accumulated; no silent truncation | **PASS** |
| Zero divisor and capacity errors rejected before returning results | **PASS** |
| Modeled scratch checked and returned to zero | **PASS** |
| Whole-transition small-field and GF(2^12) tests pass | **PASS** |
| Existing P013 behavior retained | **PASS** |
| P015 regression suite passes | **PASS** |
| Classical register-model evidence distinguished from circuit evidence | **PASS** |
| P017 started | **NO** |

P016 is complete. P017 has not been started.
