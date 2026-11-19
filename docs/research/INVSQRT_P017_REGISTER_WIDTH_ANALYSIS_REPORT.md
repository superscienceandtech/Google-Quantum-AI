# INVSQRT P017 Fixed-Point Intermediate Register-Width Analysis

## 1. Executive summary

**P017 status: `IMPLEMENTED — VALIDATED AGAINST THE FIXED-POINT MODEL; CIRCUIT CORRESPONDENCE BLOCKED`.**

P017 adds a reusable register-width analyzer that derives unsigned and
two's-complement signed widths from observed fixed-point ranges and exposes
fixed-point scaling metadata. It reuses P008's `fixed_point_reference` and
P016's normalized-partition helpers; it does not introduce a competing
fixed-point implementation.

One exhaustive run evaluated `3,133,452` valid inputs with `0` partition or
inventory mismatches. The run completed in `718.619` seconds. The measured
width reductions are scalar/model observations only. Every narrower candidate
is marked `REQUIRES_CANONICAL_CIRCUIT_MAPPING`; no circuit register, qubit,
gate, depth, or score reduction is claimed.

## 2. Scope and P016 evidence

P017 inspected P011/P016 C01 extrema, P008/P009 fixed-point semantics, P012
backend readiness, P015 acquisition safeguards, and the active C01
implementation/tests. P016 established complete normalized interval coverage
and zero mismatch against the fixed-point emulator over the same domain.

P016 partition cases are:

| Case | Normalized range |
|---:|---|
| 0 | `[1048576, 1572864)` |
| 1 | `[1572864, 2097152)` |
| 2 | `[2097152, 3145728)` |
| 3 | `[3145728, 4194304)` |

P017 uses those cases to report the input partition producing each intermediate
extremum. P011's historical report and P016's report remain unchanged.

## 3. Intermediate inventory

P017 inventories only fields or arithmetic values exposed by `FixedPointResult`
or directly derived from its exposed P008/P017 arithmetic:

| Intermediate | Model field or operation | Signedness | Fractional scale |
|---|---|---|---:|
| `input` | `FixedPointResult.input_value` | unsigned | none |
| `shift_pairs` | `FixedPointResult.shift_pairs` | unsigned | none |
| `normalized` | `FixedPointResult.normalized_register` | unsigned | 0 |
| `interval_case` | `FixedPointResult.interval_case` | unsigned | none |
| `coefficient_c0` | `coefficient_integers[0]` | unsigned | 17 |
| `coefficient_c1` | `coefficient_integers[1]` | unsigned | 17 |
| `coefficient_c2` | `coefficient_integers[2]` | unsigned | 17 |
| `coefficient_c3` | `coefficient_integers[3]` | unsigned | 17 |
| `horner_r1` | `horner_registers[0]` | unsigned | 17 |
| `horner_r2` | `horner_registers[1]` | unsigned | 17 |
| `horner_r3` | `horner_registers[2]` | unsigned | 17 |
| `square` | `square_register` | unsigned | 28 |
| `mantissa_product` | `product_register` | unsigned | 28 |
| `newton_correction` | `3 << product_bits - product_register` | unsigned | 28 |
| `newton_result_before_denormalization` | `result_register >> shift_pairs` | unsigned | 29 |
| `phase_numerator` | `result_register` | unsigned | 40 |

The inventory does not infer signedness or fractional scaling from magnitude.
All fields used here are nonnegative in the valid-domain P008 model.

## 4. Width derivation

For a nonnegative maximum `m`, unsigned width is:

\[
w_u=\max(1,\operatorname{bit\_length}(m)).
\]

Zero is represented in one bit. This width is a storage-range fact, not a
circuit-width result.

For a signed inclusive range `[minimum, maximum]`, P017 searches the minimum
two's-complement width `w` satisfying:

\[
-2^{w-1}\leq \text{minimum}
\quad\text{and}\quad
\text{maximum}\leq 2^{w-1}-1.
\]

The helper verifies both endpoints before reporting a width. Signed widths are
included for completeness even though P017's observed fixed-point intermediates
are unsigned.

Fixed-point integer width remains separate from fractional scaling:
the coefficient and Horner values use 17 fractional bits, the square uses 28,
the mantissa uses 28, the pre-denormalized result uses 29, and the phase
numerator uses 40. Real-number ranges are not inferred where the representation
scale is ambiguous.

## 5. Exhaustive extrema

The exhaustive P017 run used one ascending pass from `1` through `3,133,452`.
It reported `3,133,452` evaluated inputs and `0` mismatches.

| Intermediate | Min | Min input | Max | Max input | Unsigned width | Signed width | Existing model width |
|---|---:|---:|---:|---:|---:|---:|---:|
| `input` | 1 | 1 | 3,133,452 | 3,133,452 | 22 | 23 | 22 |
| `shift_pairs` | 0 | 1,048,576 | 10 | 1 | 4 | 5 | not declared |
| `normalized` | 1,048,576 | 1 | 4,194,300 | 1,048,575 | 22 | 23 | 22 |
| `interval_case` | 0 | 1 | 3 | 3 | 2 | 3 | not declared |
| `coefficient_c0` | 75,673 | 3 | 131,064 | 1 | 17 | 18 | 17 |
| `coefficient_c1` | 12,575 | 3 | 65,025 | 1 | 16 | 17 | 17 |
| `coefficient_c2` | 2,956 | 3 | 43,596 | 1 | 16 | 17 | 17 |
| `coefficient_c3` | 518 | 3 | 19,499 | 1 | 15 | 16 | 17 |
| `horner_r1` | 2,441 | 4,094 | 43,596 | 1 | 16 | 17 | 17 |
| `horner_r2` | 10,139 | 16,382 | 65,025 | 1 | 16 | 17 | 17 |
| `horner_r3` | 65,543 | 65,534 | 131,064 | 1 | 17 | 18 | 17 |
| `square` | 67,123,200 | 65,534 | 268,402,689 | 1 | 28 | 29 | 28 |
| `mantissa_product` | 268,399,587 | 49,063 | 268,513,234 | 3,012,415 | 29 | 30 | 30 |
| `newton_correction` | 536,793,134 | 3,012,415 | 536,906,781 | 49,063 | 30 | 31 | not declared |
| `newton_result_before_denormalization` | 536,871,164 | 1,048,575 | 1,073,741,806 | 1 | 30 | 31 | 30 |
| `phase_numerator` | 621,138,295 | 3,133,452 | 1,099,511,609,344 | 1 | 40 | 41 | 40 |

The `minimum_signed_width` for positive-only ranges includes the sign bit.
It is not evidence of a smaller signed circuit register.

## 6. Per-partition extrema

P017 compares every intermediate within C01's four partition cases. The
partition witness table is available through `partition_extrema` in the
serialized `WidthAnalysisResult`.

Selected extrema:

- `coefficient_c0/c1/c2/c3` maxima occur in case `0`, at input `1`.
- `coefficient_c3` minimum occurs in case `3`, at input `3`.
- `horner_r1` maximum occurs in case `0`, at input `1`.
- `horner_r2` maximum occurs in case `0`, at input `1`.
- `horner_r3` maximum occurs in case `0`, at input `1`.
- `square` maximum occurs in case `0`, at input `1`.
- `mantissa_product` minimum occurs in case `2`, at input `49,063`; its maximum
  occurs in case `2`, at input `3,012,415`.
- `newton_correction` extrema occur in cases `2` and `0`, respectively.
- `newton_result_before_denormalization` minimum occurs in case `0`, at
  input `1,048,575`; maximum occurs in case `0`, at input `1`.
- `phase_numerator` minimum occurs in case `2`, at input `3,133,452`; maximum
  occurs in case `0`, at input `1`.

These are partition observations against P008. They do not establish
case-specific quantum comparators or circuit register maps.

## 7. Analytical proof versus exhaustive evidence

The width formula is `PROVEN_ANALYTICALLY` for the observed range abstraction:
unsigned and signed widths represent exactly the supplied integer endpoints.

The extrema are `EXHAUSTIVELY_OBSERVED` over `1..3,133,452`. They are strong
domain-specific evidence but do not mathematically prove a bound for inputs
outside the benchmark domain or prove circuit behavior.

The P017 module does not claim `PROVEN_ANALYTICALLY` for any circuit register
width or for arbitrary out-of-domain integer values.

## 8. Circuit correspondence

No canonical official circuit artifacts or Kickmix source declaration are
available in this checkout. P017 therefore marks all possible emulator
intermediate mappings `UNMAPPED`.

The public mirror is retained only as P008/P009 historical static evidence.
Matching names or similar ranges do not establish exact, partial, or official
circuit correspondence.

No mapping is claimed for coefficient words, Horner accumulators, square,
mantissa product, Newton correction, or phase numerator.

## 9. Optimization opportunities

P017 exposes `assess_width_opportunities`, which never reports
`SUPPORTED_FOR_CIRCUIT_EXPERIMENT`.

| Intermediate | Mathematical range narrower than declared model width? | P017 decision |
|---|---|---|
| `coefficient_c1/c2/c3` | yes: 16/16/15 versus 17 | `REQUIRES_CANONICAL_CIRCUIT_MAPPING` |
| `horner_r1/r2` | yes: 16 versus 17 | `REQUIRES_CANONICAL_CIRCUIT_MAPPING` |
| `mantissa_product` | yes: 29 versus 30 | `REQUIRES_CANONICAL_CIRCUIT_MAPPING` |
| `shift_pairs/interval_case/newton_correction` | no authoritative declared model width | `REQUIRES_CANONICAL_CIRCUIT_MAPPING` |
| `input/normalized/coefficient_c0/horner_r3/square/newton_result/phase_numerator` | no | `NO_WIDTH_REDUCTION_IDENTIFIED` |

Possible arithmetic width changes require:

- exact reversible representation and carry/wrap correspondence;
- fixed-width equivalence on all valid inputs;
- downstream overflow and phase-tolerance evidence;
- verified scratch cleanup and restoration;
- circuit construction and resource measurement;
- official verifier acceptance.

## 10. API and implementation

P017 adds:

- `src/invsqrt_opt/register_width_analysis.py`;
- `tests/test_register_width_analysis.py`;
- package exports in `src/invsqrt_opt/__init__.py`;
- this report;
- a README report link.

It reuses P008 `fixed_point_reference` and P016 partition helpers. It does not
modify P011/P016 reports or P007/P008/P009 implementation.

## 11. Tests and validation

Focused tests cover unsigned widths, signed widths, two's-complement
boundaries, fixed-point scaling, inventory structure, bounded reproducibility,
P017/P011/P016 extrema regressions, partition consistency, unmapped circuit
handling, and refusal to claim circuit savings.

P017's full-domain run was executed separately over `3,133,452` inputs.
It completed in `718.619` seconds with `0` mismatches.

Focused P017/P016 tests: **35 passed**.

Full project suite: **379 passed**.

`git diff --check` passed. The README P017 report link resolves to this report.

## 12. Resource and security impact

P017 makes no qubit, Toffoli, T-count, T-depth, depth, compilation, or score
claim. It does not run Kickmix, construct circuits, download data, execute a
verifier, or modify artifact provenance. P003/P005/P015 remain unchanged.

## 13. Remaining blockers

- canonical circuit source/register declarations;
- reversible arithmetic and carry/wrap proof;
- scratch cleanup/restoration proof;
- official phase tolerance/shot behavior;
- Kickmix and official verifier;
- circuit-level resource measurement.

## 14. Recommended next experiment

If canonical circuit evidence becomes available, isolate one width candidate,
starting with `coefficient_c1/c2/c3`, `horner_r1/r2`, or
`mantissa_product`. Prove exact stage or product-register equivalence against
P008, map reversible controls and carry/wrap semantics, then construct and
measure the candidate before any resource or score claim.
