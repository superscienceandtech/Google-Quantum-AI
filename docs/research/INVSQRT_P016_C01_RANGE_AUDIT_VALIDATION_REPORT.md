# INVSQRT P016 C01 Range-Audit Validation Report

## 1. Executive summary

**P016 status: `IMPLEMENTED — PARTIALLY VALIDATED FOR THE FIXED-POINT MODEL; CIRCUIT VALIDATION BLOCKED`.**

P016 validates and extends P011's C01 range-audit prototype without changing
P011's experiment identity or historical report. The C01 implementation now
exposes exact normalized `interval_case` partition metadata and an exhaustive
partition-vs-fixed-point comparison.

The complete official input domain was checked:

- Inputs: `1..3,133,452`
- Evaluated: `3,133,452`
- Partition mismatches: `0`
- First mismatch: none
- Result: `PASSED`

This is exhaustive agreement between C01's partition description and the
existing P008 integer fixed-point emulator. It is not quantum-circuit
equivalence, official verifier acceptance, a register-width proof, or a
resource/score improvement.

P016 does not modify P005/P015, download artifacts, execute the Kaggle CLI,
build a circuit, measure resources, or run the official verifier.

## 2. P011 C01 baseline and implementation identity

P011 remains the historical range-audit experiment:

- Candidate: `P010-C01`
- P011 candidate version: `P011-range-audit-v1`
- P011 experiment: `P011-C01-E01-BASELINE-RANGE-AUDIT`
- Baseline model: `src/invsqrt_opt/fixed_point.py`
- Algorithm model: P008-independent fixed-point arithmetic
- P011 full-domain result: `3,133,452` inputs, zero stage mismatches
- P011 historical report: not modified

P016 extends the same C01 implementation rather than introducing a second
fixed-point implementation. `audit_interval_partition` obtains every actual
value from `fixed_point_reference`; the partition helper expresses only the
normalized register predicates already implemented by that emulator.

## 3. Mathematical definition of the audited ranges

The fixed-point emulator normalizes an input `x` to:

```text
normalized = x << (2 * shift_pairs)
```

where `shift_pairs` is the leading-zero-pair count for `n_p=10`. The
normalized 22-bit register lies from `1 << 20` through `1 << 22 - 1`,
inclusive. C01's `interval_case` is selected from the normalized top, second,
and third bits:

```text
top    = normalized bit 21
second = normalized bit 20
third  = normalized bit 19
interval_case = third if top == 0 else 2 + second
```

P016 expresses the resulting exact normalized partitions as:

| Case | Normalized integer subrange(s) | Closed/open form |
|---:|---|---|
| 0 | `[1048576, 1572864)` | `[1.0, 1.5) * 2^20` |
| 1 | `[1572864, 2097152)` | `[1.5, 2.0) * 2^20` |
| 2 | `[2097152, 3145728)` | `[2.0, 3.0) * 2^20` |
| 3 | `[3145728, 4194304)` | `[3.0, 4.0) * 2^20` |

These normalized ranges are exact for the fixed-point formula and match P011's
historical coefficient-case shorthand. They are scalar partition semantics,
not register allocation or circuit control-flow evidence.

## 4. Partition completeness and boundary analysis

The P016 partition helper verifies:

- all four interval IDs are present;
- every subrange is non-empty;
- subranges are ordered and adjacent;
- the first subrange starts at `1048576`;
- the final subrange ends at `4194304`;
- no gap or overlap exists;
- the full normalized domain `[1048576, 4194304)` is covered.

Region witnesses found by the full-domain run:

| Case | Minimum observed original input | Maximum observed original input |
|---:|---:|---:|
| 0 | `1` | `1,572,863` |
| 1 | `6` | `2,097,151` |
| 2 | `2` | `3,133,452` |
| 3 | `3` | `1,048,575` |

The full-domain run found 42 transitions in the ascending input stream. The
first three are:

| Input | Previous case | Next case |
|---:|---:|---:|
| `2` | `0` | `2` |
| `3` | `2` | `3` |
| `4` | `3` | `0` |

The transition list is input-sensitive, because normalization changes
`shift_pairs` while preserving the resulting normalized coefficient region.
Values immediately before/after every selected boundary are deterministic test
inputs, rather than a quantum boundary resource result.

## 5. Fixed-point arithmetic semantics relevant to C01

P016 reused:

- `FixedPointPrecision`: delta `14`, coefficient `17`, square `28`,
  product `28`, and result `29` bits;
- `fixed_point_reference` for normalized, interval, Horner, square,
  mantissa, Newton, and denormalized values;
- signedness/range guards already present in the fixed-point emulator;
- source-aligned row reconstruction already present in P011 C01.

No real arithmetic, approximation, binary search, or new coefficient table was
introduced. P016 does not change Horner operations, truncation, square
construction, Newton correction, or denormalization.

The P011 observed extrema remain unchanged:

- coefficient `c1/c2/c3` showed unused modeled upper bits;
- `horner_r1/r2/r3`, square, product, correction, and result ranges were
  measured by C01;
- the correction register had no established physical circuit allocation.

Observed maxima are exhaustive measurements of the P008 scalar model, not
proven circuit-wire maxima.

## 6. Validation methodology

P016 added:

- `IntervalPartitionRegion`;
- `PartitionTransition`;
- `PartitionAuditResult`;
- `get_interval_partition_regions`;
- `audit_interval_partition`.

The audit:

1. validates the existing `RangeAuditConfig`;
2. derives the exact normalized partition from `n_p=10`;
3. calls `fixed_point_reference` for every configured input;
4. derives the expected case from the normalized subranges;
5. compares it with `result.interval_case`;
6. records input witnesses and ascending case transitions;
7. checks partition completeness and first mismatch.

No mirror source, official verifier, Kaggle archive, Kickmix, or circuit
builder was fetched or invoked.

## 7. Exhaustive and boundary results

### Full-domain partition run

| Metric | P016 result |
|---|---:|
| Input minimum | `1` |
| Input maximum | `3,133,452` |
| Inputs checked | `3,133,452` |
| Full-domain | yes |
| Partition mismatches | `0` |
| First mismatch | none |
| Deterministic result | yes across repeated focused execution |

The full-domain result agrees exactly with P011's P008 fixed-point model.
P011's six independent row/reconstruction checks remain the separate stage
audit evidence.

### Boundary-focused tests

P016 tests domain minimum/maximum, power-of-two-adjacent values, normalized
partition edges, invalid inputs, invalid precision, subrange determinism,
partition completeness, non-overlap, and fixed-point case agreement.

The first mismatch in a subrange remains reportable; P016 adds no silent
fallback or approximate partition. Invalid input outside the official domain
raises `ValueError`.

## 8. Reproducibility evidence

P016 source identity and validation can be reproduced using:

```powershell
$env:PYTHONPATH = "src"
python -m pytest tests\test_c01_range_audit.py -q
python -c "from invsqrt_opt.candidates.c01_range_audit import audit_interval_partition; import json; r=audit_interval_partition(); print(json.dumps(r.to_dict(), indent=2, sort_keys=True))"
```

Relevant source hashes:

- P011 C01 implementation before P016: `d8c8ea3c258c5eabe525223cb1bae11f35e5df9e12a4d57e58c78abe1972b4a7`;
- P016 C01 implementation after partition validation: `db3af1329983942d05c2db35003b81168cd98393e920f2868f9d8eb1d2eb18e0`;
- fixed-point implementation hash: `734d8fbbccb603d03eaa51e49e98b0a1126d77c2461b4bc4dffe7c4dceabc1ac`;
- pinned mirror reference hash: `bb90330dcf774f7b502de471293facba67f27952cc8808fe4a9970a9b1322e23`;
- P011 historical report hash: `ca5940fd271069b6f60003a7eabf94a7a9f42102e424a2db04b78d82a086c8e8`;
- P011 report: unchanged.

Repeated partition runs in the focused test suite returned identical serial
structures for the tested subrange.

## 9. Intermediate extrema and witness limitations

P016 adds exact partition witness ranges but does not reimplement P011's
register/result extrema. P011's exhaustive extrema remain the scalar-model
measurement; P016 should not reinterpret their witness inputs as circuit
resource evidence.

The partition witness for each case is the first and last original input
observed by the full scan. It establishes actual fixed-point interval-case
usage across the benchmark domain. It does not establish:

- circuit control wires;
- reversible interval comparators;
- carry or wrap behavior;
- scratch cleanup;
- phase error;
- official tolerance;
- gate count or qubit count.

## 10. Optimization hypothesis register

| Hypothesis | Mathematical rationale | Supporting evidence | Against | Circuit assumptions | Resource impact | Current decision |
|---|---|---|---|---|---|---|
| H16-C01-A: narrow unused coefficient/Horner registers | P011 observed unused modeled upper bits in `c1/c2/c3` and some Horner values | Exhaustive scalar maxima and zero P011 reconstruction mismatches | Unused scalar bits do not establish safe carry/wrap, control, or subtraction widths | Exact reversible arithmetic, fixed-width wrap, cleanup | Unknown; possible register or adder effect, not asserted | `INCONCLUSIVE` |
| H16-C01-B: partition-specific coefficient/control specialization | Four interval cases select fixed coefficient tables | Partition audited over all inputs with zero mismatches | Four selector regions do not identify a circuit implementation or gate savings | Comparator/table factoring and uncomputation are required | Unknown | `SUPPORTED_FOR_FURTHER_TESTING` |
| H16-C01-C: reduce delta precision | P011 reports a 14-bit delta source model | Full-domain scalar row reconstruction agreed | No proof that delta row count/precision can change without phase/model drift | Exact stage output and complete error bound | Unknown | `INCONCLUSIVE` |

All hypotheses remain below the circuit-resource level. A future register or
table experiment must use `SUPPORT`, `PROVEN_ANALYTICALLY`, or
`EXHAUSTIVELY_VERIFIED_AGAINST_FIXED_POINT_MODEL` in the correct category;
it must not turn this scalar evidence into a resource claim.

The evidence ladder is explicit:

1. Mathematical partition coverage: `PROVEN_ANALYTICALLY` for the normalized
   bit formula and exact subranges;
2. Agreement with the fixed-point emulator: `EXHAUSTIVELY_VERIFIED_AGAINST_FIXED_POINT_MODEL`;
3. Potential register-width reduction: `NOT_VERIFIED`;
4. Actual circuit resource reduction: `NOT_VERIFIED`;
5. Verified official score improvement: `NOT_VERIFIED`.

## 11. Resource-impact limitations

No qubit, Toffoli, T, T-depth, circuit-depth, compilation, or score measurement
was made. P016 does not know whether a narrower scalar register decreases
quantum wires or whether selector factoring decreases or increases gates.

The P010 objective `S=Q(C)` remains unmeasured. P016 therefore makes no
resource or official score claim.

## 12. Remaining blockers

- Canonical official artifacts are unavailable.
- Kickmix remains unavailable in the active environment.
- P003/P005 provenance gates remain fail-closed.
- P015 remains unchanged and real acquisition is blocked.
- Quantum carry, modular wrap, scratch cleanup, restoration, and phase behavior
  are not modeled as circuit operations.
- Official tolerance and verified verifier execution are unavailable.
- P011 register extrema do not establish physical register widths.

## 13. Recommended next experiment

If and only if authoritative circuits and a working reversible backend become
available, test one isolated C01 hypothesis in a separately identified
candidate: first prove stage-equivalent fixed-width arithmetic and interval
case behavior, then compare circuit qubits and measured \(C\) on the same
provenance-bound implementation. Do not combine width, coefficient, and
workspace scheduling changes in the first experiment.

P016 does not start that experiment.

## 14. Changed files and test results

P016 changes:

- extended `src/invsqrt_opt/candidates/c01_range_audit.py`;
- extended `tests/test_c01_range_audit.py`;
- added this report;
- updated README with a P016 report link.

P016 does not modify P007/P008/P009/P011/P012/P015 implementation or reports.
P013/P014/P015 provenance and acquisition behavior is unchanged.

Validation state:

- focused C01 tests: **15 passed**;
- full project suite: **359 passed**;
- `git diff --check`: passed;
- README P016 report link: present and resolves;
- P011 report and implementation hashes verified.
