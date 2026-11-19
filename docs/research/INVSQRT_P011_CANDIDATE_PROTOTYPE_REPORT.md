# INVSQRT P011 Candidate Prototype Report

## 1. Executive summary

P011 executed the first numerical study recommended by P010: **P010-C01,
Exhaustive reachable-range and truncation-margin audit**. The isolated
analyzer observes the unchanged P008 fixed-point model over the complete
benchmark input domain. It does not change arithmetic, precision, output,
production behavior, or any P007-P009 file.

The full-domain run completed for all **3,133,452** inputs. Its six stage
reconstruction checks had **zero mismatches**. This is a successful numerical
audit of the local scalar model, not a width-equivalence proof: the mirror's
competition origin remains unauthenticated, and no circuit, Kickmix runtime,
resource counter, or official verifier was available. No qubit/gate/score
improvement is claimed.

The candidate found one-bit unused upper capacity in some baseline model
registers and two in others, while several registers use every modeled bit.
Those are measured classical value ranges only. No register narrowing is
implemented or recommended from this result alone.

## 2. P010 candidate selection

P010 explicitly ranks **P010-C01** first for a numerical prototype and marks
only its range audit `READY_FOR_NUMERICAL_EXPERIMENT`. P010 separately marks
any fixed-point width change `REQUIRES_FIXED_POINT_EQUIVALENCE`. Its §14
recommends a standalone deterministic baseline analyzer when the circuit
backend remains unavailable.

| Selection item | P010 decision |
|---|---|
| Candidate | P010-C01 |
| Title | Exhaustive reachable-range and truncation-margin audit |
| Category | Fixed-point arithmetic / register widths |
| Proposed step | Measure the unchanged baseline's stage values, used bits, row contributions, and register-limit margins |
| Evidence | Baseline semantics `REPOSITORY_VERIFIED`; unsigned-width formula `MATHEMATICALLY_DERIVED`; any resource benefit `EMPIRICAL_HYPOTHESIS` |
| Readiness | `READY_FOR_NUMERICAL_EXPERIMENT` for the audit only |
| Correctness gate for a later width candidate | Full-domain stage equality and no overflow; validate boundary cases and phase behavior; then circuit and official verification |
| Risks/blockers | Scalar ranges do not prove circuit wire ranges, modular/carry behavior, reversible cleanup, phase tolerance, or resource savings |

No other P010 candidate was combined with C01. In particular, P010-C06
workspace scheduling was not implemented: its required circuit backend is
unavailable.

## 3. Repository baseline and preserved work

| Property | P011 initial observation |
|---|---|
| Root | `D:\PROJECT\Quantum_AI\Google-Quantum-AI` |
| Branch | `feat/invsqrt-optimization` |
| HEAD | `5391b2e7123484efacffc0588f5e761e67b5cb55` |
| Initial tracked status | `README.md` modified |
| Initial untracked work | P002-P010 research documents, `pyproject.toml`, `src/invsqrt_opt/`, and `tests/`; generated Python bytecode files were present |
| Ignored data | Existing `.pytest_cache/` was preserved |

All existing uncommitted P002-P010 work was preserved. The README's prior
content was retained; P011 adds only a new section and report link. No reset,
stash, checkout, clean, commit, or push was performed.

The following validated baseline files were inspected and left unchanged:

- P007: `src/invsqrt_opt/reference_math.py`,
  `src/invsqrt_opt/numerical_validation.py`.
- P008: `src/invsqrt_opt/fixed_point.py` and
  `docs/research/INVSQRT_FIXED_POINT_SEMANTICS_AND_EMULATOR_READINESS.md`.
- P009: `src/invsqrt_opt/fixed_point_differential.py` and
  `docs/research/INVSQRT_FIXED_POINT_EMULATOR_VALIDATION.md`.
- P010: `docs/research/INVSQRT_OPTIMIZATION_CANDIDATE_REGISTER.md`.

The P009 qualification remains explicit: the pinned public-mirror commit and
file hashes were checked, but the mirror's competition-origin claim was not
independently authenticated. Agreement with the mirror model is not proof of
quantum-circuit equivalence.

## 4. Baseline behavior and mathematical scope

The baseline function evaluated by the analyzer is the P008 scalar fixed-point
reference for `n_p=10` and the default precision:

| Stage/configuration | Baseline |
|---|---:|
| Input domain | Inclusive integers 1 through 3,133,452 |
| Input width | 22 bits |
| Delta rows | 14-bit precision |
| Coefficients and Horner registers | 17 bits |
| Square register | 28 bits |
| Mantissa product precision | 28 bits; scalar product limit is 30 bits |
| Newton result precision | 29 bits; scalar result-product limit is 30 bits |
| Phase numerator width | 40 bits |

The underlying computation remains unchanged: leading-zero-pair
normalization, four source-defined coefficient cases, three Horner
subtractions, bitwise square construction, row-wise truncated products,
Newton correction, and shift-based denormalization. For each row the baseline
uses the control times a shifted operand; right shifts discard low bits before
the row contributions are summed. The analyzer records those contribution
ranges and discarded remainders without moving or changing any truncation.

For a nonnegative integer register value \(v\), the observed minimum unsigned
width is \(\max(1,\operatorname{bit\_length}(v_{\max}))\), equivalent to
\(\lceil\log_2(v_{\max}+1)\rceil\) when \(v_{\max}>0\). A positive observed
margin is only a necessary numerical fact. It does not establish that a
reversible circuit can use fewer wires or preserve carry, wrap, phase, or
uncomputation semantics.

The audit makes no new inverse-square-root approximation. Therefore no new
absolute/relative approximation error, phase error, or official tolerance
result is applicable. The unchanged model represents the returned phase as
an integer numerator over \(2^{40}\) turns; no phase gate or official phase
comparator was evaluated.

## 5. Fixed-point and circuit implications

Every reported data value is nonnegative in the scalar model. Horner stages
use subtraction, but the model checks that each resulting value is positive
and fits its baseline width. The analyzer reports known source/model width
limits only. It does **not** assign a physical width to the observed
`newton_correction`, `shift_pairs`, or `interval_case`, whose allocated
circuit register widths are not established by the available artifacts.

The implementation tracks the baseline `FixedPointResult` values and
independently recomputes each Horner row sum, the mantissa-product row sum, the
Newton-result row sum, and denormalization. The bitwise square's final
register range is measured; its internal reversible-adder/circuit carry
states are not modeled. A successful scan means the local scalar model raised
no overflow and the listed reconstruction checks matched on every scanned
input. It does not prove circuit behavior outside that model.

## 6. Isolated prototype implementation

Created `src/invsqrt_opt/candidates/c01_range_audit.py`, with candidate ID
`P010-C01` and version `P011-range-audit-v1`. It provides:

- Frozen `RangeAuditConfig` with explicit inclusive bounds, `n_p`, and
  precision; only the validated baseline precision is accepted.
- Full-domain scan by default, with explicitly labeled valid subrange mode
  available for focused tests.
- Per-register minima/maxima, first attaining input, observed/minimum
  unsigned bits, and headroom to known baseline limits.
- Per-row contribution ranges and maximum discarded low-bit remainder for
  the three Horner products, mantissa product, and Newton result product.
- Coverage, deterministic output checksum, source and implementation hashes,
  environment, timestamps, runtime, and per-stage consistency counts as
  machine-readable JSON.
- Fail-explicit behavior for invalid bounds, unsupported `n_p`, precision,
  and configuration types.

The analyzer is observational. It does not return a transformed numerical
candidate and does not change the production/reference APIs. No generic
candidate/search configuration or P004 framework schema was changed.

P004's `ExperimentRecord` and `ExperimentRunner` represent constructed circuit
candidates, resource measurements, and verifier outcomes. Using them for this
baseline-only range result would imply candidate/resource/verification
semantics the experiment does not have. The isolated analyzer therefore emits
a dedicated JSON record and this report; no historical experiment record was
overwritten.

## 7. Test and experiment methodology

The experiment scans inputs in ascending order, inclusive, using the
unchanged `fixed_point_reference`. It records the baseline numerator digest
over the complete ordered input stream. Critical values include the domain
endpoints, normalization-pair transitions, and polynomial interval edges and
their adjacent integers; the full contiguous pass also necessarily covers
every other power of two and neighboring input.

For each input it checks:

1. Each of three Horner accumulators equals its coefficient minus the sum of
   the source-aligned row contributions.
2. The mantissa-product row sum equals the baseline product register.
3. The Newton-result row sum equals the pre-denormalized result.
4. The baseline denormalization shift reconstructs the phase numerator.

This is not a candidate-vs-baseline comparison because C01's first step
introduces no transformed output. The historical P009 full-domain comparison
to the hash-pinned mirror model remains the relevant independent baseline
comparison; P009 reported two complete runs with zero output mismatches,
subject to its provenance qualification.

Validation results:

| Test selection | Result |
|---|---:|
| C01 candidate tests | 11 passed |
| P007-P009 regression tests | 228 passed |
| Complete test suite | 310 passed |

Candidate tests exercise the minimum and maximum inputs against pinned
baseline vectors, the 6-8 power-of-two boundary subrange, exact row/stage
checks, deterministic repeated results, default configuration, invalid and
unsupported configurations, and the explicit "no declared correction width"
guard.

Pylance found no syntax errors or source diagnostics in the candidate module.
Its `pytest` import warning on the new test file also appears on existing test
files; the configured terminal environment resolves `pytest` and the test
runs pass.

## 8. Experiment record and full-domain results

**Experiment ID:** `P011-C01-E01-BASELINE-RANGE-AUDIT`
**Candidate/version:** `P010-C01` / `P011-range-audit-v1`
**Configuration:** `n_p=10`; precision `{delta_bits:14, coef_bits:17, square_bits:28, product_bits:28, result_bits:29}`; ascending inclusive domain `1..3,133,452`.
**Coverage:** 3,133,452 of 3,133,452 inputs; full domain. All 118 enumerated critical inputs were visited.
**Execution:** `COMPLETED` / passed; started `2026-11-19T19:55:32.945595Z`, completed `2026-11-19T20:05:36.473505Z`; measured in-process runtime **603.5279051 s**.
**Candidate-vs-baseline output metrics:** Not applicable; this audit has no transformed candidate output. The baseline output checksum and the six consistency checks are recorded below.

| Check | Inputs checked | Mismatches | First mismatch |
|---|---:|---:|---|
| Horner `r1` reconstruction | 3,133,452 | 0 | None |
| Horner `r2` reconstruction | 3,133,452 | 0 | None |
| Horner `r3` reconstruction | 3,133,452 | 0 | None |
| Mantissa-product row sum | 3,133,452 | 0 | None |
| Newton-result row sum | 3,133,452 | 0 | None |
| Denormalized phase numerator | 3,133,452 | 0 | None |

### 8.1 Register ranges

`Distance to exclusive limit` is \(2^w-\max\); `headroom` is
\(2^w-1-\max\). `-` means no physical/baseline width was established, so no
register-limit margin is asserted.

| Value/register | Min (input) | Max (input) | Observed bits | Baseline bits | Unused high bits | Distance to limit | Headroom |
|---|---:|---:|---:|---:|---:|---:|---:|
| Input | 1 (1) | 3,133,452 (3,133,452) | 22 | 22 | 0 | 1,060,852 | 1,060,851 |
| Normalized | 1,048,576 (1) | 4,194,300 (1,048,575) | 22 | 22 | 0 | 4 | 3 |
| Coefficient `c0` | 75,673 (3) | 131,064 (1) | 17 | 17 | 0 | 8 | 7 |
| Coefficient `c1` | 12,575 (3) | 65,025 (1) | 16 | 17 | 1 | 66,047 | 66,046 |
| Coefficient `c2` | 2,956 (3) | 43,596 (1) | 16 | 17 | 1 | 87,476 | 87,475 |
| Coefficient `c3` | 518 (3) | 19,499 (1) | 15 | 17 | 2 | 111,573 | 111,572 |
| Horner `r1` | 2,441 (4,094) | 43,596 (1) | 16 | 17 | 1 | 87,476 | 87,475 |
| Horner `r2` | 10,139 (16,382) | 65,025 (1) | 16 | 17 | 1 | 66,047 | 66,046 |
| Horner `r3` | 65,543 (65,534) | 131,064 (1) | 17 | 17 | 0 | 8 | 7 |
| Square | 67,123,200 (65,534) | 268,402,689 (1) | 28 | 28 | 0 | 32,767 | 32,766 |
| Mantissa product | 268,399,587 (49,063) | 268,513,234 (3,012,415) | 29 | 30 | 1 | 805,228,590 | 805,228,589 |
| Newton correction | 536,793,134 (3,012,415) | 536,906,781 (49,063) | 30 | - | - | - | - |
| Newton result before denormalization | 536,871,164 (1,048,575) | 1,073,741,806 (1) | 30 | 30 | 0 | 18 | 17 |
| Phase numerator | 621,138,295 (3,133,452) | 1,099,511,609,344 (1) | 40 | 40 | 0 | 18,432 | 18,431 |
| `shift_pairs` (control value) | 0 (1,048,576) | 10 (1) | 4 | - | - | - | - |
| `interval_case` (selector value) | 0 (1) | 3 (3) | 2 | - | - | - | - |

These are observed scalar-model ranges only. The one/two unused high bits in
some model values do not authorize any width change. In particular, coefficient
encoding, circuit control flow, modular behavior, and uncomputation still
require circuit-level proof and official validation.

### 8.2 Per-row contributions and truncation

For each row below, `min..max` is the observed contribution range, `min@x` and
`max@x` give the first input attaining each endpoint, and `active` counts inputs
where that row's control is 1. `remainder@x` is the maximum low-bit remainder
among active rows for that row's right-shift truncation; `-` means the row has
no right-shift-discarded bits or no nonzero remainder was observed.

| Operator | Row | Weight | Exponent | Discarded bits | Min | Max | Min @ x | Max @ x | Active inputs | Max remainder @ x |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| horner_r1 | 0 | -1 | -1 | 1 | 0 | 862 | 1 | 10 | 861,537 | 0 @ - |
| horner_r1 | 1 | -2 | -2 | 2 | 0 | 4,874 | 1 | 5 | 1,560,587 | 3 @ 5 |
| horner_r1 | 2 | -3 | -3 | 3 | 0 | 2,437 | 1 | 18 | 1,560,581 | 6 @ 50 |
| horner_r1 | 3 | -4 | -4 | 4 | 0 | 1,218 | 1 | 17 | 1,560,581 | 12 @ 33 |
| horner_r1 | 4 | -5 | -5 | 5 | 0 | 609 | 1 | 66 | 1,560,557 | 28 @ 130 |
| horner_r1 | 5 | -6 | -6 | 6 | 0 | 304 | 1 | 65 | 1,560,557 | 60 @ 129 |
| horner_r1 | 6 | -7 | -7 | 7 | 0 | 152 | 1 | 258 | 1,564,544 | 106 @ 386 |
| horner_r1 | 7 | -8 | -8 | 8 | 0 | 76 | 1 | 257 | 1,564,557 | 234 @ 385 |
| horner_r1 | 8 | -9 | -9 | 9 | 0 | 38 | 1 | 1,026 | 1,566,208 | 234 @ 1,538 |
| horner_r1 | 9 | -10 | -10 | 10 | 0 | 19 | 1 | 1,025 | 1,566,208 | 746 @ 1,537 |
| horner_r1 | 10 | -11 | -11 | 11 | 0 | 9 | 1 | 4,098 | 1,564,672 | 1,770 @ 6,146 |
| horner_r1 | 11 | -12 | -12 | 12 | 0 | 4 | 1 | 4,097 | 1,564,672 | 3,115 @ 4,097 |
| horner_r1 | 12 | -13 | -13 | 13 | 0 | 2 | 1 | 16,386 | 1,558,528 | 5,866 @ 24,578 |
| horner_r1 | 13 | -14 | -14 | 14 | 0 | 1 | 1 | 16,385 | 1,558,528 | 5,866 @ 24,577 |
| horner_r2 | 0 | -1 | -1 | 1 | 0 | 3,422 | 1 | 10 | 861,537 | 1 @ 10 |
| horner_r2 | 1 | -2 | -2 | 2 | 0 | 9,680 | 1 | 5 | 1,560,587 | 3 @ 13 |
| horner_r2 | 2 | -3 | -3 | 3 | 0 | 5,144 | 1 | 18 | 1,560,581 | 7 @ 18 |
| horner_r2 | 3 | -4 | -4 | 4 | 0 | 2,648 | 1 | 17 | 1,560,581 | 15 @ 86 |
| horner_r2 | 4 | -5 | -5 | 5 | 0 | 1,343 | 1 | 66 | 1,560,557 | 31 @ 86 |
| horner_r2 | 5 | -6 | -6 | 6 | 0 | 676 | 1 | 65 | 1,560,557 | 63 @ 141 |
| horner_r2 | 6 | -7 | -7 | 7 | 0 | 339 | 1 | 258 | 1,564,544 | 127 @ 294 |
| horner_r2 | 7 | -8 | -8 | 8 | 0 | 170 | 1 | 257 | 1,564,557 | 255 @ 1,055 |
| horner_r2 | 8 | -9 | -9 | 9 | 0 | 85 | 1 | 1,026 | 1,566,208 | 511 @ 1,055 |
| horner_r2 | 9 | -10 | -10 | 10 | 0 | 42 | 1 | 1,025 | 1,566,208 | 1,023 @ 1,055 |
| horner_r2 | 10 | -11 | -11 | 11 | 0 | 21 | 1 | 4,098 | 1,564,672 | 2,047 @ 5,511 |
| horner_r2 | 11 | -12 | -12 | 12 | 0 | 10 | 1 | 4,097 | 1,564,672 | 4,095 @ 5,511 |
| horner_r2 | 12 | -13 | -13 | 13 | 0 | 5 | 1 | 16,386 | 1,558,528 | 8,191 @ 25,530 |
| horner_r2 | 13 | -14 | -14 | 14 | 0 | 2 | 1 | 16,385 | 1,558,528 | 16,383 @ 25,529 |
| horner_r3 | 0 | -1 | -1 | 1 | 0 | 9,784 | 1 | 10 | 861,537 | 1 @ 14 |
| horner_r3 | 1 | -2 | -2 | 2 | 0 | 13,836 | 1 | 5 | 1,560,587 | 3 @ 7 |
| horner_r3 | 2 | -3 | -3 | 3 | 0 | 7,485 | 1 | 18 | 1,560,581 | 7 @ 38 |
| horner_r3 | 3 | -4 | -4 | 4 | 0 | 3,898 | 1 | 17 | 1,560,581 | 15 @ 77 |
| horner_r3 | 4 | -5 | -5 | 5 | 0 | 1,990 | 1 | 66 | 1,560,557 | 31 @ 130 |
| horner_r3 | 5 | -6 | -6 | 6 | 0 | 1,005 | 1 | 65 | 1,560,557 | 63 @ 133 |
| horner_r3 | 6 | -7 | -7 | 7 | 0 | 505 | 1 | 258 | 1,564,544 | 127 @ 282 |
| horner_r3 | 7 | -8 | -8 | 8 | 0 | 253 | 1 | 257 | 1,564,557 | 255 @ 519 |
| horner_r3 | 8 | -9 | -9 | 9 | 0 | 126 | 1 | 1,026 | 1,566,208 | 511 @ 1,138 |
| horner_r3 | 9 | -10 | -10 | 10 | 0 | 63 | 1 | 1,025 | 1,566,208 | 1,023 @ 1,535 |
| horner_r3 | 10 | -11 | -11 | 11 | 0 | 31 | 1 | 4,098 | 1,564,672 | 2,047 @ 7,487 |
| horner_r3 | 11 | -12 | -12 | 12 | 0 | 15 | 1 | 4,097 | 1,564,672 | 4,095 @ 6,877 |
| horner_r3 | 12 | -13 | -13 | 13 | 0 | 7 | 1 | 16,386 | 1,558,528 | 8,190 @ 27,510 |
| horner_r3 | 13 | -14 | -14 | 14 | 0 | 3 | 1 | 16,385 | 1,558,528 | 16,383 @ 27,509 |
| mantissa_product | 0 | -20 | -20 | 20 | 0 | 255 | 1 | 1,048,577 | 1,042,438 | 1,048,521 @ 2,556,353 |
| mantissa_product | 1 | -19 | -19 | 19 | 0 | 511 | 1 | 1,048,578 | 1,042,438 | 524,283 @ 2,025,986 |
| mantissa_product | 2 | -18 | -18 | 18 | 0 | 1,023 | 1 | 262,145 | 1,435,653 | 262,140 @ 374,433 |
| mantissa_product | 3 | -17 | -17 | 17 | 0 | 2,047 | 1 | 262,146 | 1,435,653 | 131,068 @ 374,434 |
| mantissa_product | 4 | -16 | -16 | 16 | 0 | 4,095 | 1 | 65,537 | 1,533,952 | 65,535 @ 115,661 |
| mantissa_product | 5 | -15 | -15 | 15 | 0 | 8,191 | 1 | 65,538 | 1,533,952 | 32,767 @ 115,662 |
| mantissa_product | 6 | -14 | -14 | 14 | 0 | 16,381 | 1 | 16,385 | 1,558,528 | 16,383 @ 28,915 |
| mantissa_product | 7 | -13 | -13 | 13 | 0 | 32,760 | 1 | 16,386 | 1,558,528 | 8,191 @ 28,915 |
| mantissa_product | 8 | -12 | -12 | 12 | 0 | 65,513 | 1 | 4,097 | 1,564,672 | 4,095 @ 5,401 |
| mantissa_product | 9 | -11 | -11 | 11 | 0 | 130,994 | 1 | 4,098 | 1,564,672 | 2,047 @ 7,282 |
| mantissa_product | 10 | -10 | -10 | 10 | 0 | 261,860 | 1 | 1,025 | 1,566,208 | 1,023 @ 2,547 |
| mantissa_product | 11 | -9 | -9 | 9 | 0 | 523,216 | 1 | 1,026 | 1,566,208 | 511 @ 2,547 |
| mantissa_product | 12 | -8 | -8 | 8 | 0 | 1,044,404 | 1 | 257 | 1,564,557 | 255 @ 569 |
| mantissa_product | 13 | -7 | -7 | 7 | 0 | 2,080,768 | 1 | 258 | 1,564,544 | 127 @ 766 |
| mantissa_product | 14 | -6 | -6 | 6 | 0 | 4,129,722 | 1 | 65 | 1,560,557 | 63 @ 245 |
| mantissa_product | 15 | -5 | -5 | 5 | 0 | 8,134,813 | 1 | 66 | 1,560,557 | 31 @ 67 |
| mantissa_product | 16 | -4 | -4 | 4 | 0 | 15,792,179 | 1 | 17 | 1,560,581 | 15 @ 207 |
| mantissa_product | 17 | -3 | -3 | 3 | 0 | 29,827,674 | 1 | 18 | 1,560,581 | 7 @ 35 |
| mantissa_product | 18 | -2 | -2 | 2 | 0 | 53,681,265 | 1 | 5 | 1,560,587 | 3 @ 22 |
| mantissa_product | 19 | -1 | -1 | 1 | 0 | 89,475,408 | 1 | 6 | 1,560,587 | 1 @ 6 |
| mantissa_product | 20 | 0 | 0 | 0 | 0 | 268,402,689 | 2 | 1 | 1,747,626 | 0 @ - |
| mantissa_product | 21 | 1 | 1 | 0 | 0 | 268,401,280 | 1 | 2 | 1,735,351 | 0 @ - |
| newton_result_before_denormalization | 0 | -1 | 0 | 0 | 536,793,134 | 536,906,781 | 3,012,415 | 49,063 | 3,133,452 | 0 @ - |
| newton_result_before_denormalization | 1 | -2 | -1 | 1 | 0 | 268,451,839 | 2 | 1 | 1,087,491 | 1 @ 1 |
| newton_result_before_denormalization | 2 | -3 | -2 | 2 | 0 | 134,226,320 | 3 | 2,579 | 1,521,411 | 3 @ 1 |
| newton_result_before_denormalization | 3 | -4 | -3 | 3 | 0 | 67,113,347 | 5 | 49,063 | 1,617,083 | 7 @ 1 |
| newton_result_before_denormalization | 4 | -5 | -4 | 4 | 0 | 33,556,479 | 2 | 1 | 1,544,109 | 15 @ 1 |
| newton_result_before_denormalization | 5 | -6 | -5 | 5 | 0 | 16,778,284 | 3 | 2 | 1,596,127 | 31 @ 1 |
| newton_result_before_denormalization | 6 | -7 | -6 | 6 | 0 | 8,389,168 | 2 | 49,063 | 1,542,247 | 63 @ 1 |
| newton_result_before_denormalization | 7 | -8 | -7 | 7 | 0 | 4,194,584 | 5 | 49,063 | 1,555,621 | 127 @ 1 |
| newton_result_before_denormalization | 8 | -9 | -8 | 8 | 0 | 2,097,292 | 2 | 49,063 | 1,563,097 | 255 @ 1 |
| newton_result_before_denormalization | 9 | -10 | -9 | 9 | 0 | 1,048,646 | 2 | 49,063 | 1,563,499 | 511 @ 1 |
| newton_result_before_denormalization | 10 | -11 | -10 | 10 | 0 | 524,323 | 2 | 49,063 | 1,565,948 | 1,023 @ 1 |
| newton_result_before_denormalization | 11 | -12 | -11 | 11 | 0 | 262,159 | 2 | 1 | 1,567,403 | 2,047 @ 1 |
| newton_result_before_denormalization | 12 | -13 | -12 | 12 | 0 | 131,080 | 2 | 2,567 | 1,566,770 | 4,095 @ 1 |
| newton_result_before_denormalization | 13 | -14 | -13 | 13 | 0 | 65,540 | 2 | 10 | 1,564,313 | 8,191 @ 1 |
| newton_result_before_denormalization | 14 | -15 | -14 | 14 | 0 | 32,770 | 1 | 2 | 1,557,471 | 16,383 @ 65,955 |
| newton_result_before_denormalization | 15 | -16 | -15 | 15 | 0 | 16,385 | 1 | 2,567 | 1,564,420 | 32,767 @ 57,610 |
| newton_result_before_denormalization | 16 | -17 | -16 | 16 | 0 | 8,192 | 1 | 3 | 1,554,473 | 65,535 @ 57,610 |

## 9. Error and runtime analysis

The scan changed no numerical approximation and introduced no output variant,
so candidate-vs-baseline maximum absolute/relative output differences and
inverse-square-root or phase-error distributions are **not applicable**.
The six row/stage reconstruction checks above are exact integer checks. The
baseline output checksum is
`d65ca0a2df966d27d6e4f1294541dc7a1f6d2097c18763ffdef6a51915599984`.

The measured final full scan took **603.5279051 seconds** (10 minutes
3.5279051 seconds of in-process wall time) on Windows 11, Python 3.14.6 /
Anaconda, ascending full domain. This is analyzer runtime including baseline
evaluation and range instrumentation, not a speed comparison between two
algorithms. Startup, console serialization, and circuit compilation were not
included. Candidate and baseline classical runtimes are therefore **not
compared**.

## 10. Resource and score implications

Quantum resources are `NOT_MEASURED`. No circuit was built, compiled, or
simulated, and there is no Kickmix/resource-counter/verifier run. The score
objective is \(Q\,(\text{Toffoli}+\text{T}/4)\), but neither factor nor the
official metric accounting was measured in this experiment. A narrower
classical register bound cannot be converted into a qubit/gate reduction or
score improvement. Potential impact remains `UNKNOWN` / `THEORETICAL`.

## 11. Reproducibility and experiment identity

The final run's candidate and baseline implementation hashes, exact timestamps,
runtime, platform, Python version, mirror source identifier/hash, critical
input-set hash, and output checksum are recorded here and emitted in the
machine-readable JSON:

| Identity/measurement | Value |
|---|---|
| Candidate implementation SHA-256 | `d8c8ea3c258c5eabe525223cb1bae11f35e5df9e12a4d57e58c78abe1972b4a7` |
| Baseline implementation SHA-256 | `734d8fbbccb603d03eaa51e49e98b0a1126d77c2461b4bc4dffe7c4dceabc1ac` |
| Baseline ordered output SHA-256 | `d65ca0a2df966d27d6e4f1294541dc7a1f6d2097c18763ffdef6a51915599984` |
| Critical input-set SHA-256 | `1c8b58d13b24549883160cf667d25cdd0c02ce72e53fa840ae25a89227a080bf` |
| Mirror reference SHA-256 | `bb90330dcf774f7b502de471293facba67f27952cc8808fe4a9970a9b1322e23` |
| Python | `3.14.6 \| packaged by Anaconda, Inc. \| (main, Jul 9 2026, 14:29:05) [MSC v.1942 64 bit (AMD64)]` |
| Platform | `Windows-11-10.0.26300-SP0` |

The final identity-bound scan reproduced the prior scan's coverage, all
register/row ranges, six consistency checks, and baseline output digest. The
final version correctly leaves correction-register width unspecified because
the available model does not establish a physical allocation for it.

The complete record is reproducible with:

```powershell
$env:PYTHONPATH = "src"
python -m invsqrt_opt.candidates.c01_range_audit
```

The command emits the full JSON record to standard output. To retain a local
copy, redirect it to a new result file; do not overwrite historical experiment
records. An initial direct Python launch without `PYTHONPATH=src` failed before
starting the scan with `ModuleNotFoundError`; it evaluated zero inputs. The
environment was corrected and the recorded CLI run above completed.

The pinned mirror model identity in the run was commit
`6ac78ec5ace6dfd5831ccac2547041408f5d8278`, reference SHA-256
`bb90330dcf774f7b502de471293facba67f27952cc8808fe4a9970a9b1322e23`.
This remains mirror-qualified, not independently authenticated official
provenance.

## 12. Correctness limitations and remaining blockers

- The scan proves observed ranges only for the P008 scalar model and complete
  valid input domain. It does not prove quantum circuit reachable-state
  ranges, partial-adder carries, modular wrap, restoration, scratch cleanup,
  or measurement-based uncomputation.
- It does not measure the individual internal carry states of the square
  implementation; only the square register value and source-aligned
  multiplication rows are audited.
- The mirror's competition-origin claim is not independently authenticated.
- The official reference circuit, verifier, resource counter, and Kickmix API
  remain unavailable. Official phase tolerance, circuit equivalence, and
  resource/score impact are untested.
- The P004 generic runner's official-verification/resource semantics were
  intentionally not fabricated for this numerical-only study.
- A width change still requires a separately approved candidate, exact
  stage-by-stage circuit/model equivalence or a complete phase-error proof,
  boundary validation, and official verification.

## 13. Recommendation for P012

Do not narrow a register based only on the unused-bit counts in §8. If
authoritative artifacts and the circuit backend become available, select one
register at a time for a separately identified candidate. First prove that the
source circuit's carry, wrap, and control semantics match the proposed width;
then compare all stage integers on the full domain, verify phase tolerance,
restoration and cleanup, and measure \(Q C\) from the same provenance-bound
circuit. If those prerequisites remain unavailable, keep C01 as a numerical
range result and make no circuit optimization claim.

## 14. P011 completion status

- One P010-approved candidate was investigated: C01 numerical range audit.
- P007-P009 baseline implementations and P010's candidate register were left
  unchanged.
- Candidate-specific, P007-P009 regression, and full test suites passed.
- No official verifier, circuit, or resource backend was run.
- No optimization benefit, fixed-point width equivalence, circuit
  equivalence, official acceptance, or score improvement is claimed.
- No commit or push occurred.
