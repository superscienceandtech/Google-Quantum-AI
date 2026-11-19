# INVSQRT Fixed-Point Emulator Validation (P009)

## 1. Purpose and scope

P009 audits the P008 classical fixed-point emulator, independently verifies
the identity of the source mirror files, reproduces the full input-domain
differential comparison, and hardens arithmetic/API regression coverage.
Results are explicitly limited to the hash-pinned mirror's **Python model**.
No quantum circuit was simulated, no official verifier was run, and the
mirror's claim that its files are unchanged competition artifacts is not
independently authenticated here.

## 2. Repository and initial state

| Property | Observed value |
|---|---|
| Repository root | `D:\PROJECT\Quantum_AI\Google-Quantum-AI` |
| Branch | `feat/invsqrt-optimization` |
| HEAD | `5391b2e7123484efacffc0588f5e761e67b5cb55` |
| Initial tracked status | `README.md` modified |
| Initial untracked work | P002–P008 `docs/`, `pyproject.toml`, `src/`, and `tests/` files |
| Initial generated Python cache candidates | None reported by `git status` |

No branch switch, reset, clean, commit, or push was performed. P002–P008
uncommitted work was preserved. P007 source and its historical report were
left unchanged.

## 3. P008 implementation inventory

| Path | P008 role | P009 audit |
|---|---|---|
| `src/invsqrt_opt/fixed_point.py` | Independent scalar fixed-point reference | Audited and hardened; default benchmark outputs preserved |
| `tests/test_fixed_point.py` | P008 arithmetic and input tests | Extended with primitive/adversarial and unsupported-configuration tests |
| `src/invsqrt_opt/__init__.py` | Public API exports | Inspected; exports preserved |
| `README.md` | P008 status and research link | P009 status and validation link added |
| `docs/research/INVSQRT_FIXED_POINT_SEMANTICS_AND_EMULATOR_READINESS.md` | P008 evidence and semantics | Preserved unchanged |
| `src/invsqrt_opt/contract.py` | Benchmark input domain and `n_p` contract | Inspected; P009 model now rejects unsupported `n_p` |
| `src/invsqrt_opt/reference_math.py` and `tests/test_reference_math.py` | P007 real-arithmetic model | Regressed exhaustively; unchanged |
| `docs/research/INVSQRT_CLASSICAL_REFERENCE_IMPLEMENTATION.md` | P007 historical results | Preserved unchanged |

P009 adds:

- `src/invsqrt_opt/fixed_point_differential.py`: opt-in, hash-pinned,
  full-domain differential runner; it extracts and executes only the mirror's
  pure-model definitions in memory and does not save or vendor source files.
- `tests/test_fixed_point_differential.py`: 132 static source-model boundary
  vectors for stable offline regression.
- `docs/research/INVSQRT_FIXED_POINT_EMULATOR_VALIDATION.md`: this audit.

## 4. Reference identity, hashes, and provenance

The source repository is [`qarena-ai/invsqrt`](https://github.com/qarena-ai/invsqrt).
GitHub's commit API returned the requested immutable commit
`6ac78ec5ace6dfd5831ccac2547041408f5d8278`, with parent
`6a6684babc6204b44c04391f0416e3ad61cbaa37` and message
`QArena export of invsqrt (hub a17af8de17e3)`. Each raw file was fetched from
the commit-addressed URL and SHA-256 was recomputed from the returned bytes.
The mirror README's listed sizes and checksums agree.

| File at pinned commit | Bytes | P009-computed SHA-256 | P008 recorded SHA-256 | Result |
|---|---:|---|---|---|
| `verifiers/invsqrt/nr_reference_circuit.py` | 18,862 | `bb90330dcf774f7b502de471293facba67f27952cc8808fe4a9970a9b1322e23` | Same | Match |
| `verifiers/invsqrt/verify_submission_invsqrt.py` | 17,210 | `ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a` | Same | Match |

P008 records the reference commit and reference-file hash in
`fixed_point.py`; P009 additionally pins and checks the verifier hash in the
reproducible differential tool. The validation tool checks file hashes before
parsing source. It executes only the AST definitions `POLY_A`, `POLY_B`,
`Precision`, and `fixed_point_model`; it does not execute the verifier, circuit
builder, Kickmix imports, or source module top-level imports.

The P008 report did not preserve a runnable comparison command or machine
result record tying its earlier in-memory execution to fetched source bytes.
Therefore that historical process's source identity cannot be independently
audited from the checkout alone. P009 closes that reproducibility gap: its own
comparison fetches the immutable commit, verifies both hashes, and includes
them in each result.

**Provenance classification: `PARTIALLY_VERIFIED`.** Raw bytes and the
immutable mirror commit are verified. The mirror README and NOTICE assert the
verifier files are competition files unchanged, and identify the Kaggle
competition data as their origin. Those are mirror-authored statements, not an
official Kaggle signature or an independently obtained competition archive.
Accordingly, the source is not classified `OFFICIAL_VERIFIED`, and no official
acceptance is claimed.

## 5. Source-to-implementation arithmetic audit

Source line numbers below refer to the fixed-commit
[`nr_reference_circuit.py`](https://github.com/qarena-ai/invsqrt/blob/6ac78ec5ace6dfd5831ccac2547041408f5d8278/verifiers/invsqrt/nr_reference_circuit.py).
“Matched” means matched against that file's classical `fixed_point_model` for
valid benchmark inputs; it does not mean circuit execution was verified.

| Operation | Pinned source location | Local implementation | Arithmetic rule | Audit |
|---|---|---|---|---|
| Precision defaults | `Precision`, lines 42–68 | `FixedPointPrecision` | `delta=14`, `coef=17`, `square=28`, `product=28`, `result=29` | `MATCHED` |
| Coefficient table | `Precision.coefficient_table`, lines 55–65 | `_coefficient_table` / `coefficient_table` | Binary64 source constants; upper cases divide coefficient \(j\) by \(2^j\sqrt2\); Python ties-to-even `round` after scaling | `MATCHED` |
| Input normalization | `fixed_point_model`, lines 99–102 | `fixed_point_reference` | Count leading zero pairs; normalize \(x\) by `2 * shift_pairs`; source uses `floor(log2(x))`, local uses integer `bit_length()` | `MATCHED` on full valid domain |
| Interval selection | Lines 102–107 | Top-bit selection in `fixed_point_reference` | Four cases selected from normalized top bits | `MATCHED` |
| Delta rows / Horner | Lines 104–112 | `delta` and three Horner passes | Source row list and truncating product; unsigned 17-bit accumulators with range checks | `MATCHED` |
| Row multiplication | Lines 88–97 | `_truncated_product` | Exponent `output_bits - operand_bits + row_weight`; left shift or low-bit-discarding right shift, then row sum | `MATCHED` |
| Square | Lines 114–122 | `square` loop | Diagonal bits copied; cross terms doubled; columns below target LSB omitted | `MATCHED` |
| Mantissa product | Lines 123–124 | normalized rows and `_truncated_product` | Row truncation into product register with two integer bits | `MATCHED` |
| Newton correction | Lines 124–126 | Direct integer `3 * 2**product_bits - product` | Source model uses same scalar difference; circuit's complement/add implementation is not simulated | `MATCHED` to source model; circuit `NOT_TESTED` |
| Newton product | Lines 125–126 | `_truncated_product` | Truncating row product into the result register | `MATCHED` |
| Denormalization | Line 127 | `result << shift_pairs` | Integer shift by leading-zero-pair count | `MATCHED` to source model |
| Fixed-width overflow | Lines 95–97, 111–112 | `_truncated_product` and Horner guards | Model raises on overflow; source circuit comments describe fixed-width wrap | `PARTIALLY_MATCHED` outside valid-domain behavior |
| Phase / circuit behavior | Source phase helper and verifier | No circuit code in emulator | Integer numerator returned; no phase gate, restoration, or scratch cleanup simulated | `NOT_VERIFIABLE` |

The local model imports no functions from the mirror. Both implementations
derive coefficient values from the same published coefficient constants and
documented formulas, but compute them separately. Normalization, interval
selection, products, square, and stages are also separately implemented;
expected full-domain outputs are produced by the pinned reference model, not
by the local emulator. No local result is transformed before comparison.

The only bypass is extraction of the source's pure-Python model to avoid
importing its unavailable `kickmix` circuit dependency. This does not alter the
model's arithmetic: the extracted function uses NumPy array operations and its
own nested `product` implementation. It does mean the comparison provides no
evidence about gate execution or Kickmix runtime semantics.

## 6. Full-domain differential validation

**Classification: `FULL_DOMAIN_EXACT_MATCH` (two P009 runs).**

The opt-in runner fetches both pinned files, checks both hashes, creates the
source `Precision` and `fixed_point_model` definitions from the verified
reference bytes in memory, then compares local scalar results with source
model outputs in ascending contiguous chunks. There is no random sampling,
input skipping, expected-value transformation, or circuit execution. The
reference precision is checked against the local supported defaults.

| Measurement | P009 result |
|---|---:|
| Input domain | 1 through 3,133,452 inclusive |
| Precision (`n_p`, delta, coefficient, square, product, result) | `10`, `14`, `17`, `28`, `28`, `29` |
| Inputs compared per run | 3,133,452 |
| Mismatch count per run | 0 |
| Maximum integer output difference per run | 0 |
| First mismatch | None |
| Completion | `COMPLETED` |
| Order | Ascending contiguous chunks |
| Repeated aggregate fields | Identical across both completed runs |
| Elapsed time | 381.253 s and 341.424 s (runtime only; excluded from stable fields) |

The run report includes source commit and hashes, local algorithm version,
precision, bounds, order, count, mismatch count, maximum difference, first
mismatch, up to 20 mismatch examples, completion status, Python/NumPy versions,
and elapsed time. The validator exits nonzero if the count is incomplete or
any mismatch occurs.

Reproduce one full run from the repository root in PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m invsqrt_opt.fixed_point_differential --mode FULL_DOMAIN_VALIDATION
```

For repeatability, run the command twice and compare the reported fields other
than elapsed time. The tool requires network access to the pinned raw GitHub
files and NumPy for the mirror's model. P009 used NumPy 2.4.6; NumPy was not
added to project dependencies. The emulator itself uses only the standard
library and repository code.

## 7. Boundary and arithmetic regression coverage

`tests/test_fixed_point_differential.py` contains 132 independently generated
source-model integer output vectors. They cover:

- Inputs 1–33 and values immediately around powers of two.
- Normalization and polynomial interval edges across the supported pair shifts.
- The paper-reported input 2,588,411.
- The upper-domain neighbors 3,133,451 and 3,133,452.

The expected integers are static source-model values, not calculated by the
local function under test. Other focused tests verify:

- Exact coefficient table, stable repeated construction, and 17-bit range.
- Zero, identity, maximum-fitting, left-shift, and fractional right-shift
  products, including floor truncation.
- Row accumulation/carry and register overflow.
- Rejection of negative operands, invalid controls/weights/row shapes, and
  invalid widths.
- Every coefficient interval, intermediate vectors, and final golden outputs.
- Invalid inputs: booleans, floats, decimals, strings, zero, negatives, and
  values above the domain.
- Rejection of non-default `n_p` and valid-but-unsupported precision widths.
- Repeated identical-input and input-order-independent deterministic outputs.

The emulator now explicitly supports only the reference benchmark's `n_p=10`
and default precision. Positive but different precision fields are rejected
by `fixed_point_reference`; no unsupported width configuration is silently
treated as source-equivalent.

Focused command:

```powershell
python -m pytest tests/test_fixed_point.py tests/test_fixed_point_differential.py -q
```

P009 result: **205 passed**.

## 8. P007 classical model regression

**Classification: reproduced; P007 remains unchanged.**

Command:

```powershell
$env:PYTHONPATH = "src"
python -m invsqrt_opt.numerical_validation --mode EXHAUSTIVE_VALIDATION
```

The run evaluated all **3,133,452** inputs at 50-digit Decimal precision.
Measured results agree with the historical P007 report:

| Measurement | P009 reproduction |
|---|---:|
| Maximum absolute error | `5.16405158684016760144785491987692297221484E-9` at `x=1` |
| Maximum relative error | `5.1643545984960819089670834272040066197411095618635E-9` at `x=1,123,799` |
| Boundary cases | 118 |
| Relative error at paper-reported `x=2,588,411` | `4.0227848172749841925464768555553667348467114121761E-9` |
| Difference from paper-reported `2.84E-8` | `2.4377215182725015807453523144444633265153288587824E-8` |
| Quantum verification | `NOT_PERFORMED` |

P007 uses real-arithmetic Decimal polynomial/Newton evaluation and an
independent inverse-square-root oracle. P008/P009 use finite-width integer
arithmetic and row truncation. Different values between these models are
expected; no values were altered to make them agree.

## 9. Test suite, dependency, and tooling results

- Full suite: `python -m pytest` — **299 passed**.
- Focused fixed-point suite: **205 passed**.
- Pylance syntax checks: no syntax errors in the modified/new Python files.
- Pylance diagnostics: no diagnostics in the fixed-point implementation or
  differential runner. The selected Pylance environment did not resolve the
  existing optional `pytest` package in the test file; the configured terminal
  Python ran the tests successfully.
- Project dependency manifests: unchanged. No package was installed and no
  dependency was added.
- `numpy` is required by the opt-in mirror-model differential command, not by
  the scalar emulator or ordinary test suite. Version used in P009: `2.4.6`.
- `git diff --check`: passed.

## 10. Readiness and remaining limitations

| Area | P009 status | Basis |
|---|---|---|
| Fixed-point arithmetic on valid official-domain inputs | `PASS` | Audited source-to-code mapping, two exact full-domain comparisons, source-derived regression vectors |
| Reference provenance | `PARTIALLY_VERIFIED` | Immutable mirror commit and both hashes verified; competition origin remains mirror-asserted |
| Differential comparison | `FULL_DOMAIN_EXACT_MATCH` | Two completed ascending runs; 3,133,452 inputs each, zero mismatch, zero maximum difference |
| Circuit equivalence | `BLOCKED` / `NOT_TESTED` | Kickmix runtime, official circuit fixture, and direct circuit simulation unavailable |
| Official verifier / acceptance | `NOT_TESTED` | Not run; no official acceptance claim |

The scalar emulator is ready as a deterministic classical reference for the
default benchmark model. It is not a circuit-faithful simulator, verifier, or
resource estimator. Source-model overflow behavior beyond benchmark inputs and
custom precision configurations remain unsupported.

## 11. Recommended P010 objective

Before optimization, close the provenance/runtime gap: obtain the competition
archive or another authoritative source identity, provide the supported
Kickmix runtime and reference circuit, then compare basis-state outputs,
input restoration, scratch cleanup, and phase tolerance on stage-focused
vectors. Only after those checks should a circuit-level optimization
experiment begin. P009 did not start P010.

## 12. References and evidence classification

1. [Pinned mirror commit](https://github.com/qarena-ai/invsqrt/commit/6ac78ec5ace6dfd5831ccac2547041408f5d8278) — commit identity from GitHub API.
2. [Reference model source](https://github.com/qarena-ai/invsqrt/blob/6ac78ec5ace6dfd5831ccac2547041408f5d8278/verifiers/invsqrt/nr_reference_circuit.py) — bytes and SHA-256 independently verified.
3. [Verifier source](https://github.com/qarena-ai/invsqrt/blob/6ac78ec5ace6dfd5831ccac2547041408f5d8278/verifiers/invsqrt/verify_submission_invsqrt.py) — bytes and SHA-256 independently verified; not executed.
4. [Mirror README](https://github.com/qarena-ai/invsqrt/blob/6ac78ec5ace6dfd5831ccac2547041408f5d8278/README.md) and [NOTICE](https://github.com/qarena-ai/invsqrt/blob/6ac78ec5ace6dfd5831ccac2547041408f5d8278/NOTICE) — mirror-authored provenance claims, not official authentication.
5. [P007 classical reference report](./INVSQRT_CLASSICAL_REFERENCE_IMPLEMENTATION.md) — historical real-arithmetic results; preserved.
6. [P008 fixed-point semantics report](./INVSQRT_FIXED_POINT_SEMANTICS_AND_EMULATOR_READINESS.md) — prior fixed-point analysis; preserved.

Evidence labels in this report:

- **Directly measured / independently reproduced:** source hashes, full-domain
  comparisons, test results, P007 exhaustive metrics.
- **Derived from source:** arithmetic mapping and finite-width rules.
- **Inferred:** none used as a passing verification result.
- **Not tested / blocked:** official source authenticity, Kickmix circuit
  execution, verifier acceptance, and quantum circuit equivalence.
