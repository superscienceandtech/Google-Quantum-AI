# P018 — Bounded Iterative Reversible EEA Controller Report

## 1. Executive Result

**Result: PASS for the implemented bounded classical register controller and its declared domain.**

The P018 controller composes the P016 single-step transition for the standard
P014 initialization
`(r0,r1,s0,s1,t0,t1) = (z^70,S,1,0,0,1)`, with nonzero
`deg(S) <= 69`, and stops at zero remainder or when the current remainder has
degree below 35. It maintains fixed-width state banks, verifies the bounded
Bézout windows before transfer, and reapplies P016 to clear each round's
wide output targets. An independent test-local arithmetic oracle agrees on
the whole transition and on the iterative final state for the tested domains.

This PASS is not a claim of gate-level quantum reversibility, a quantum
circuit, full P008 compatibility, or official verifier compatibility. The
controller returns a classical result and retained round trace; it is not
itself a single input-preserving XOR transformation.

## 2. Artifacts Inspected

Implementation dependencies and historical contracts inspected for the
proof gate and implementation:

- `docs/research/DQI_P014_EEA_STATE_CAPACITY_AND_ITERATION_CONTRACT.md`
- `docs/research/DQI_P015_CAPACITY_GENERALIZED_REVERSIBLE_DIVISION_REPORT.md`
- `docs/research/DQI_P016_CAPACITY_GENERALIZED_REVERSIBLE_EEA_SINGLE_STEP_REPORT.md`
- `docs/research/DQI_P017_ITERATIVE_EEA_STATE_CLOSURE_AND_COMPOSITION_FEASIBILITY.md`
- `docs/research/DQI_P008_REVERSIBLE_DECODER_SPECIFICATION.md`
- P012/P013 handoff reports
- `src/dqi_decoder/reversible_division.py`
- `tests/dqi_decoder/test_reversible_division.py`
- `src/dqi_decoder/reversible_eea.py`
- `tests/dqi_decoder/test_reversible_eea.py`
- `src/dqi_decoder/reversible_primitives.py`
- `tests/dqi_decoder/test_reversible_primitives.py`
- `src/dqi_decoder/reversible_polynomial.py`
- `tests/dqi_decoder/test_reversible_polynomial.py`
- `src/dqi_decoder/reversible_evaluation.py`
- `tests/dqi_decoder/test_reversible_evaluation.py`

P018 additions:

- `src/dqi_decoder/iterative_eea.py`
- `tests/dqi_decoder/test_iterative_eea.py`
- `docs/research/DQI_P018_BOUNDED_ITERATIVE_REVERSIBLE_EEA_CONTROLLER_REPORT.md`

No P014–P017 artifact was modified.

## 3. P017 Proof Gate and Capacity Contract

The implementation is restricted to the P014 standard initialization and
threshold domain; it does not accept arbitrary P016 state tuples as its public
input.

| Register | Fixed P018 state width | Per-round P016 output/target width | Contract |
|---|---:|---:|---|
| `r0` | 71 | — | Dividend state; initialized to `z^70` |
| `r1` | 70 | — | Nonzero syndrome, then padded remainder |
| `s0`, `s1` | 35 each | `s2`: 105 | Low 35 coefficients transferred only after high-window proof |
| `t0`, `t1` | 36 each | `t2`: 106 | Low 36 coefficients transferred only after high-window proof |
| `q` | — | 71 | P015/P016 quotient target |
| `r2` | — | 69 | P015/P016 remainder target for the fixed 70-slot divisor |

The state bank contains 283 coefficient slots. The 105- and 106-slot
coefficient outputs are full declared-width convolution targets required by
P016. They are not truncated in place: P018 first checks that coefficients
above slots 34 and 35 are zero, respectively, copies the proven low windows
into a distinct next-state bank, and then reapplies P016 to XOR-clear the
entire wide outputs.

The proof gate confirmed the assumptions needed for that transfer:

1. `A=z^70` has degree 70 and the accepted nonzero `S` has degree at most 69.
2. The standard coefficient initialization is `(s0,s1)=(1,0)` and
   `(t0,t1)=(0,1)`.
3. Active divisions occur only while `deg(r1) >= 35`. Remainder degree
   strictly decreases after each active division, so the initial maximum
   degree 69 permits at most 35 active rounds before the degree is below 35.
4. On these initialized, invariant-valid states, P014/P017's Bézout degree
   bounds imply the next `s` coefficient has degree at most 34 and the next
   `t` coefficient degree at most 35. Thus the 35- and 36-slot state windows
   contain all significant coefficients. This bound is not asserted for
   arbitrary P016 inputs.
5. P015 supports the required 71-slot dividend and 70-slot divisor; the
   transition uses P016's full-width targets at those fixed state widths.

The standard initialization, threshold, and bounded-window lemma are
prerequisites, not optional runtime modes. P018 rejects zero syndromes,
syndromes wider than 70 coefficients, and coefficients outside the field.
Every active step additionally enforces its observed transition widths,
source preservation, high-window zero conditions, decreasing remainder
degree, Bézout state invariant, and output cleanup.

## 4. Implementation and API

The public entry point is:

```python
xor_accumulate_bounded_iterative_eea(
    syndrome: PolynomialRegister,
) -> BoundedEEAResult
```

It accepts a nonempty tuple containing 1–70 GF(2^12) elements and rejects
the all-zero polynomial. It records the exact input tuple and initializes
fixed-width state as follows:

```text
r0 = (0, ..., 0, 1)  # 71 slots, z^70
r1 = syndrome padded to 70 slots
s0 = 1 padded to 35 slots; s1 = 0 padded to 35 slots
t0 = 0 padded to 36 slots; t1 = 1 padded to 36 slots
```

The public result types are `EEAState`, `EEAAroundTrace`, and
`BoundedEEAResult`; `EEAInvariantError` reports violations of the bounded
state assumptions. `EEA_THRESHOLD` and `EEA_MAX_ROUNDS` are both 35.

For each active round the controller:

1. Calls `xor_accumulate_capacity_aware_eea_transition` with six source
   registers and zeroed targets sized for quotient, remainder, and the full
   width `s2`/`t2` outputs.
2. Checks P016's six returned inputs equal the source, checks output widths,
   and verifies the high Bézout tails are zero.
3. Creates a fresh next-state bank by shifting `(r0,r1)` to `(r1,r2)`,
   `(s0,s1)` to `(s1,s2)`, and `(t0,t1)` to `(t1,t2)`. Polynomials are
   represented low-degree-first, and leading zero padding is retained in
   state registers.
4. Reapplies P016 with its computed outputs as XOR targets and verifies the
   four complete output targets return to zero while all six sources remain
   unchanged.
5. Checks the Bézout reconstruction invariants using the repository's
   polynomial arithmetic and checks strict remainder-degree decrease.

The full trace has exactly 35 entries. Once the remainder is zero or below
threshold, remaining schedule entries are explicit inactive no-ops. The
result retains the original syndrome, initial and final states, active-round
count, termination reason, and per-round source/next-state and cleanup
metadata.

No P009/P010/P015/P016 arithmetic implementation was changed. The controller
uses the existing P016 API, which in turn uses the established P015 division
and P009/P010 arithmetic contracts. The field representation is GF(2^12)
with polynomial basis and modulus `0x1053`; addition is XOR.

## 5. Correctness Evidence and Independent Oracle

The test-local oracle does not call the production P016 transition or the
production controller to calculate expected results. It independently
implements field multiplication/reduction, inversion by finite-field
exponentiation, polynomial multiplication by convolution, polynomial
division by leading-term cancellation, and the EEA coefficient recurrences.
It trims only in the mathematical oracle; expected values are padded to the
production register widths for comparison.

Tests check:

- Each complete transition's quotient, remainder, `s2`, and `t2`.
- The division identity and remainder degree through independent polynomial
  division.
- Bézout recurrence and reconstruction in the controller, with independent
  final-state/round comparisons in tests.
- Source preservation and distinct source/destination state tuples.
- Full-width temporary-target XOR accumulation and subsequent cleanup.
- High-window validation before a bounded transfer.
- Deterministic output and exact original syndrome retention.
- Zero syndrome, invalid width/type/field values, divisible input, already
  below-threshold input, leading zeros, and the 35-round boundary.

### Exhaustive bounded small-field domain

For each field GF(2^m), `m=2,3,4`, the harness enumerates every ordered pair
of nonzero two-coefficient polynomials `(A,B)` for which `deg(A) >= deg(B)`.
The threshold is 1, and the complete iterative state and all transition
outputs are compared with the independent oracle.

| Field | Enumerated input pairs | Active rounds across pairs |
|---|---:|---:|
| GF(2^2) | 189 | 144 |
| GF(2^3) | 3,577 | 3,136 |
| GF(2^4) | 61,425 | 57,600 |
| **Total** | **65,191** | **60,880** |

These are exhaustive bounded input-pair enumerations for the stated
two-slot domain, not exhaustive enumeration of all register targets or all
possible EEA states.

### Deterministic GF(2^12) boundary

A deterministic nonzero 70-slot syndrome with degree 69 was tested against
the independent oracle. It exercised the maximum 35 active rounds, the 71-,
70-, 35-, and 36-slot state widths, full 105-/106-slot P016 outputs, and
remainder degrees decreasing from 69 to 34 across active steps. In this case
the observed `s2` and `t2` supports reached degrees 34 and 35, respectively.
This is a deterministic boundary test, not exhaustive GF(2^12) coverage.

## 6. Test Reproduction

Final combined command:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q \
  tests/dqi_decoder/test_iterative_eea.py \
  tests/dqi_decoder/test_reversible_primitives.py \
  tests/dqi_decoder/test_reversible_polynomial.py \
  tests/dqi_decoder/test_reversible_evaluation.py \
  tests/dqi_decoder/test_reversible_division.py \
  tests/dqi_decoder/test_reversible_eea.py
```

**Result:** 47 passed, 133 subtests passed, 0 failed, 0 skipped; 39.52 seconds.
The run covers P018 and the P009, P010, P011, P015, and P016 focused regression
suites. P013's existing behavior is covered in the P016/P013 EEA test module.

The P018-only command was also run:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -p no:cacheprovider -q \
  tests/dqi_decoder/test_iterative_eea.py
```

**Result:** 6 passed, 7 subtests passed, 0 failed, 0 skipped; 6.27 seconds.

Python AST parsing passed for the new implementation and test files. `ruff`
was not installed (`No module named ruff`), and no dependency was installed.
The new files have no trailing whitespace. `git diff --check` reports
pre-existing trailing-whitespace diagnostics in the modified `README.md`;
that file was not edited as part of P018 and its SHA-256 remained unchanged
from the recorded starting value.

## 7. Limitations and P008 Gaps

- The public controller implements only the fixed P008-shaped initialization
  and threshold 35 domain. It is not a general iterative EEA API.
- It returns a classical state/result/trace and retains history. Its external
  operation is not an in-place, input-preserving XOR map over the entire
  multi-round history.
- The modeled P016 uncompute establishes classical-register target cleanup
  for the transition outputs. It does not provide gate decompositions,
  quantum ancilla lifecycle proofs, or a compiled reversible circuit.
- P008's shared 73-register mapping, pointer/control encoding, synchronized
  222-step schedule, wire serialization, official verifier/scorer integration,
  and official compatibility evidence remain unimplemented or unavailable.
- No complete decoder, locator/evaluator construction, Chien search, Forney
  computation, or quantum SDK integration is included.

Accordingly, P018 demonstrates bounded multi-round composition under the
specific proved standard initialization, but does not establish full P008
compatibility or competition readiness.

## 8. Repository Preservation

| Item | Result |
|---|---|
| Repository | `/mnt/d/PROJECT/Quantum_AI/Google-Quantum-AI` |
| Branch | `feat/dqi-decoder` (unchanged) |
| HEAD | `5391b2e7123484efacffc0588f5e761e67b5cb55` (unchanged) |
| Staged paths | None |
| Existing tracked modification | `README.md` preserved |
| README SHA-256 | `6fc9e83d0fb74d8f163fbd1c0fb0d0da246bd33e218e86ee56bd78ec15379027` |
| Untracked paths | 86 observed at baseline; 90 at final check, including the three P018 additions; unrelated untracked paths were left untouched |
| Dependencies | None added |
| Commits, pushes, branch changes, resets, or cleanups | None |

Only the two authorized P018 implementation/test files and this execution
report were created for the phase. No prior P008–P017 report, INVSQRT work,
or unrelated file was changed. No P019 work has been started.
