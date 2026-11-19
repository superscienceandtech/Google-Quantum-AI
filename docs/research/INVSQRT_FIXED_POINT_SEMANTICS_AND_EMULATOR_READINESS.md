# INVSQRT Fixed-Point Semantics and Emulator Readiness

## 1. Purpose and scope

P008 investigates the finite-width arithmetic of the INVSQRT reference and
implements an independent integer model where an inspectable reference source
provides explicit semantics. This is a classical fixed-point model, not a
quantum-circuit simulator and not an official verifier run.

**Status:** `PARTIALLY IMPLEMENTED` for the integer arithmetic model;
`BLOCKED` for independent quantum-circuit equivalence. The P007
real-arithmetic reference remains unchanged.

## 2. Repository state and inspection summary

Initial repository state before P008 edits:

- Root: `D:\PROJECT\Quantum_AI\Google-Quantum-AI`
- Branch: `feat/invsqrt-optimization`
- HEAD: `5391b2e7123484efacffc0588f5e761e67b5cb55`
- `git status --short`: `README.md` modified; `docs/`, `pyproject.toml`,
  `src/`, and `tests/` untracked from the P002–P007 work.

Inspected the P002–P007 package, the P005 artifact-intake/readiness
implementation, existing tests, README and `pyproject.toml`, the P006 strategy
document, the P007 classical model/report, the paper, and the public mirror
inventory and source files described below. No source artifact was copied into
the repository. P008 adds `fixed_point.py`, its tests, and this report; it also
updates the package exports in `__init__.py` and adds README status and links.
Other P002–P007 files were preserved.

## 3. Source authority and evidence methodology

Evidence labels:

- `OFFICIAL_VERIFIED`: directly verified from an official competition artifact
  or verifier. Not assigned to mirror provenance claims alone.
- `REFERENCE_IMPLEMENTATION_VERIFIED`: source bytes match the source
  repository's published SHA-256 manifest, and the source explicitly states
  the behavior.
- `PAPER_EXPLICIT`: stated in the cited paper section/equation.
- `REPOSITORY_DOCUMENTED`: stated by the local repository or source mirror;
  not independently verified against the originating competition artifact.
- `MATHEMATICALLY_DERIVED`: follows from explicitly sourced integer operations.
- `INFERENCE_UNCONFIRMED`: plausible but not proven by accessible primary
  execution evidence.
- `UNKNOWN`: not settled by inspected evidence.
- `BLOCKED`: needs unavailable runtime or primary artifact evidence.

The local checkout and all inspected `origin/*` Git trees do not contain the
verifier, reference circuit, sample submission, or Kickmix library. P005's
artifact intake confirms those local paths are missing.

The GitHub code search led to
[qarena-ai/invsqrt](https://github.com/qarena-ai/invsqrt), a public mirror.
Its README and NOTICE state that its verifier and reference-circuit files are
the competition files unchanged, and identify Apache-2.0 provenance; this
origin statement is `REPOSITORY_DOCUMENTED`, not a direct fetch from Kaggle.
The mirror's `main` commit inspected was
[`6ac78ec5ace6dfd5831ccac2547041408f5d8278`](https://github.com/qarena-ai/invsqrt/commit/6ac78ec5ace6dfd5831ccac2547041408f5d8278).
The README lists SHA-256 digests for the two files. Fetching their raw bytes
independently yielded matching hashes:

| Artifact | Mirror path | Status / version / integrity | Authority and evidence |
|---|---|---|---|
| Reference circuit and integer model | [`nr_reference_circuit.py`](https://github.com/qarena-ai/invsqrt/blob/6ac78ec5ace6dfd5831ccac2547041408f5d8278/verifiers/invsqrt/nr_reference_circuit.py) | Available in mirror; 18,862 bytes; SHA-256 `bb90330dcf774f7b502de471293facba67f27952cc8808fe4a9970a9b1322e23`; exact hash verified | `REFERENCE_IMPLEMENTATION_VERIFIED` for the inspected bytes; unchanged competition origin is `REPOSITORY_DOCUMENTED` by mirror README/NOTICE |
| INVSQRT verifier | [`verify_submission_invsqrt.py`](https://github.com/qarena-ai/invsqrt/blob/6ac78ec5ace6dfd5831ccac2547041408f5d8278/verifiers/invsqrt/verify_submission_invsqrt.py) | Available in mirror; 17,210 bytes; SHA-256 `ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a`; exact hash verified | Same evidence qualification as above |
| Mirror README and provenance notice | [`README.md`](https://github.com/qarena-ai/invsqrt/blob/6ac78ec5ace6dfd5831ccac2547041408f5d8278/README.md), [`NOTICE`](https://github.com/qarena-ai/invsqrt/blob/6ac78ec5ace6dfd5831ccac2547041408f5d8278/NOTICE) | Available at inspected commit; README lists artifacts and declared hashes; NOTICE states verifier files are competition files | `REPOSITORY_DOCUMENTED`; self-asserted origin is not an official Kaggle signature |
| Official verifier in this checkout | `external/verifiers/invsqrt/verify_submission_invsqrt.py` | Missing locally and in inspected branch trees; no local digest/version | `BLOCKED` |
| Official reference circuit in this checkout | `external/verifiers/invsqrt/nr_reference_circuit.py` | Missing locally and in inspected branch trees; no local digest/version | `BLOCKED` |
| Official sample circuit | `external/sample_submission/invsqrt.kmb` | Missing locally and in inspected branch trees; no local digest/version | `BLOCKED` |
| Kickmix runtime | `external/kickmix/kickmix.so` | Missing locally and in inspected branch trees; `kickmix` is not importable in the active environment | `BLOCKED` |
| Paper | [arXiv:2610.23832v2](https://arxiv.org/abs/2610.23832v2) | Available; §§III.1.2–III.1.3, Appendix B.1/B.3 | `PAPER_EXPLICIT` for the facts cited below |

The two source files were executed in memory only to obtain comparison vectors;
they were not written to the checkout or modified. Their source model was
compared against the independent implementation on the full valid domain.
Kickmix was stubbed only to permit importing the pure-Python model; no circuit
builder, verifier, circuit, or simulation was run.

## 4. Paper sections and equations investigated

- §III.1.2, Eqs. (14)–(31): leading-zero-pair normalization, real polynomial
  definitions, coefficient decimals, Newton step, denormalization, and
  phase/uncomputation overview (`PAPER_EXPLICIT`).
- Appendix B.1, Eqs. (102)–(105): upper normalized-range polynomial rescaling
  (`PAPER_EXPLICIT`).
- Appendix B.3, Eqs. (106)–(110): Horner evaluation and range/offset logic;
  remaining circuit-level details (`PAPER_EXPLICIT`).
- The paper does not itself specify every register encoding and row operation
  required for a bit-exact emulator (`PAPER_EXPLICIT` limitation).

The mirrored reference source adds executable details beyond the paper:
`Precision`/coefficient conversion and `fixed_point_model` at lines 42–134;
circuit arithmetic helpers and stage builders at lines 150–321; construction
and output-register allocation at lines 350–384. Its verifier specifies
little-endian input, fixed-point target/tolerance, and modulo-one phase
comparison at lines 9–20 and 116–140. These line locations refer to the
source file at the immutable mirror commit above
(`REFERENCE_IMPLEMENTATION_VERIFIED`, subject to the mirror provenance
qualification).

## 5. Coefficient representation analysis

The paper's decimal coefficients are not themselves the reference QROM words.
The mirrored source defines four coefficient cases and converts each
coefficient to a 17-fractional-bit integer. For upper-range cases it first
scales coefficient \(j\) by \(1/(2^j\sqrt{2})\), then applies Python's
`round(coefficient * 2**coef_bits)`. This is binary64 arithmetic followed by
Python round-to-nearest/ties-to-even, not truncation (`REFERENCE_IMPLEMENTATION_VERIFIED`).

The resulting exact QROM magnitudes are:

| Case | Interval | Coefficient integers \((c_0,c_1,c_2,c_3)\) |
|---:|---|---|
| 0 | \([1,1.5)\) | \((131064,65025,43596,19499)\) |
| 1 | \([1.5,2)\) | \((107018,35568,16720,5866)\) |
| 2 | \([2,3)\) | \((92676,22990,7707,1724)\) |
| 3 | \([3,4)\) | \((75673,12575,2956,518)\) |

These are source-defined integers, not newly guessed encodings. Tests assert
the exact table. The QROM loads the unsigned magnitudes into 17-bit registers;
alternating signs arise from Horner subtractions (`REFERENCE_IMPLEMENTATION_VERIFIED`).

## 6. Register-width analysis

Widths below are for the reference defaults and are fractional bits unless
called out. Input is a 22-bit unsigned little-endian register. The `M` value
is \(x_\mathrm{norm}/2^{20}\), with two integer bits and 20 fractional bits.
The `y1` output has \(F=29+n_p+1=40\) fractional bits at \(n_p=10\).
These allocations are explicit in source (`REFERENCE_IMPLEMENTATION_VERIFIED`).

| Role | Total width at \(n_p=10\) | Fractional / integer allocation | Source status |
|---|---:|---|---|
| Input \(x\) | 22 | Unsigned integer | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| Normalized \(x_\mathrm{norm}\) / \(M\) | 22 | \(M\): 20 fractional + 2 integer | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| Unary normalization flags | 10 | Unary shift count \(s\) | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| Interval selectors | 3 | Boolean selector bits | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| Coefficients and Horner intermediates | 17 each | 17 fractional; no signed magnitude encoding | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| \(\Delta x\) terms | Up to 14 fractional positions | Row weights \(2^{-m}\), \(m=1\ldots14\) | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| \(T(y_0^2)\) | 28 | 28 fractional | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| \(z=T(MT(y_0^2))\), \(3-z\) | 30 | 28 fractional + 2 integer | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| \(p=T(y_0(3-z))\) | 30 | 29 fractional + 1 integer | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| \(y_1=p2^s\) | 40 | 40 fractional phase-turn units | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| Shared partial-product scratch | 30 | Width is max of square, \(z\), and \(p\) stages | `REFERENCE_IMPLEMENTATION_VERIFIED` |

The source's parameter fields independently specify `delta_bits=14`,
`coef_bits=17`, `square_bits=28`, `product_bits=28`, and `result_bits=29`.
The 30-bit \(z\) and \(p\) arrays include the documented integer bits.

## 7. Signedness analysis

- Input, normalized mantissa, coefficient magnitudes, Horner registers,
  square, product, correction, and final output are manipulated as unsigned
  bit registers in the source model (`REFERENCE_IMPLEMENTATION_VERIFIED`).
- The gate builder implements \(3-z\) using bitwise complement plus a
  constant in a fixed-width register, and identifies the operation as
  two's-complement correction (`REFERENCE_IMPLEMENTATION_VERIFIED`).
- The model's scalar formula is `correction = (3 << product_bits) - z`.
  For the tested benchmark domain this value remains nonnegative and fits the
  intended 30-bit register (`MATHEMATICALLY_DERIVED` and exhaustively
  source-model checked).
- Horner intermediates are checked to satisfy \(0<r<2^{17}\) in the model.
  Negative coefficient signs are represented by subtraction, not signed
  coefficient words (`REFERENCE_IMPLEMENTATION_VERIFIED`).

## 8. Multiplication and truncation analysis

The source defines a row product with output fractional width \(f_o\),
operand fractional width \(f_a\), and row weight \(2^w\). Each controlled row
is aligned by exponent \(e=f_o-f_a+w\). If \(e\ge0\), the integer operand is
shifted left by \(e\); if \(e<0\), it is shifted right by \(-e\), discarding
low bits before rows are summed. For nonnegative row operands, Python's
right-shift is floor division by the corresponding power of two. There is no
round-to-nearest in these product rows (`REFERENCE_IMPLEMENTATION_VERIFIED`).

The circuit helper constructs the same aligned row into scratch, applies
fixed-width `iadd`/`isub`, then measurement-uncomputes the row ANDs
(`REFERENCE_IMPLEMENTATION_VERIFIED`). The independent model additionally
raises on documented register-fit violations instead of letting an intermediate
wrap silently; every valid benchmark input fits, as the full-domain comparison
below establishes.

The square is also explicitly constructed: diagonal bit terms are copied, and
off-diagonal AND terms are doubled into the 28-bit fractional target. Terms
below the target least-significant bit are omitted. No floating-point
multiplication is used in the P008 emulator.

## 9. Addition, subtraction, shifts, rounding, overflow

- **Horner subtracts:** `c2 -= T(c3*delta)`, `c1 -= T(r1*delta)`,
  `c0 -= T(r2*delta)`; each result must fit the 17-bit register. Exact
  bitwise low-level `isub` semantics are implemented by Kickmix and are
  unavailable locally; source says a fixed-width overflow would silently wrap
  (`REFERENCE_IMPLEMENTATION_VERIFIED` by source statement).
- **Newton correction:** The gate helper computes \(3-z\) as complement plus
  \((3\ll28)+1\) on the 30-bit `z` register. The source's classical model
  computes the equivalent integer difference directly. For valid inputs the
  exhaustive output match establishes no observable difference in this stage
  (`REFERENCE_IMPLEMENTATION_VERIFIED` against source model).
- **Shifts:** normalization detects leading zero pairs and performs controlled
  lane rotations to form \(x2^{2s}\); denormalization performs controlled
  rotations of the output slice, equivalent to \(p2^s\) for the valid
  initialized register state. The source model computes the same mathematical
  left shifts (`REFERENCE_IMPLEMENTATION_VERIFIED`).
- **Rounding:** coefficient conversion alone uses Python `round` (ties to
  even). Multiplication rows discard low bits via right shift; no rounding
  compensation is applied (`REFERENCE_IMPLEMENTATION_VERIFIED`).
- **Overflow:** the source model explicitly raises on out-of-register
  intermediate values, while its source comment says the circuit would wrap.
  No overflow occurred in the valid benchmark-domain source-model comparison.
  Thus valid-input results are verified against the source model; behavior
  outside the benchmark domain or with alternate precision settings is not
  asserted (`BLOCKED` / `UNKNOWN`).

## 10. Stage-by-stage algorithm mapping

| Stage | Mathematical / circuit behavior | Finite-width semantics and status |
|---|---|---|
| Input interpretation | Integer \(x\) in the domain | 22-bit, unsigned, little-endian; domain helper rejects invalid values (`REFERENCE_IMPLEMENTATION_VERIFIED`) |
| Leading-zero detection | Count leading zero pairs \(s\) | Sequential top-pair zero flags in unary register; pair-controlled lane rotations (`REFERENCE_IMPLEMENTATION_VERIFIED`) |
| Normalization | \(x_\mathrm{norm}=x2^{2s}\), \(M=x_\mathrm{norm}/2^{20}\) | Exact integer bit relocation; \(M\in[1,4)\) (`REFERENCE_IMPLEMENTATION_VERIFIED`) |
| Interval selection | Four cases \([1,1.5),[1.5,2),[2,3),[3,4)\) | Top three normalized mantissa bits select coefficient table and \(\Delta x\) special half bit (`REFERENCE_IMPLEMENTATION_VERIFIED`) |
| Coefficient retrieval | Select four magnitudes | Source-defined integer coefficient table XOR-loaded from selector controls (`REFERENCE_IMPLEMENTATION_VERIFIED`) |
| Polynomial | Three Horner multiplications/subtractions | 14-bit \(\Delta x\) row set, 17-bit coefficients/intermediates, rowwise low-bit truncation (`REFERENCE_IMPLEMENTATION_VERIFIED`) |
| Square | \(T(y_0^2)\) | 28 fractional bits; diagonal copies and doubled cross terms (`REFERENCE_IMPLEMENTATION_VERIFIED`) |
| Mantissa multiply | \(z=T(MT(y_0^2))\) | 28 fractional + 2 integer bits (`REFERENCE_IMPLEMENTATION_VERIFIED`) |
| Newton subtraction | \(3-z\) | 30-bit two's-complement complement-plus-constant circuit operation (`REFERENCE_IMPLEMENTATION_VERIFIED`) |
| Newton multiply | \(p=T(y_0(3-z))\) | 29 fractional + 1 integer bits (`REFERENCE_IMPLEMENTATION_VERIFIED`) |
| Denormalization | \(y_1=p2^s\) | Unary-controlled output-slice rotation; output has 40 fractional phase-turn bits (`REFERENCE_IMPLEMENTATION_VERIFIED`) |
| Phase preparation | Apply phase from output bits | Verifier maps rotations to 64-bit modulo-one phase units; P008 does not emulate or execute a `Z_POW` circuit (`REFERENCE_IMPLEMENTATION_VERIFIED`; circuit check `BLOCKED`) |

## 11. Fixed-point semantics matrix

| Operation | Input format | Output format | Exact sourced behavior | Evidence status |
|---|---|---|---|---|
| Coefficient encoding | Published decimal binary64 values | Unsigned 17-bit integers | Upper cases scaled by \(1/(2^j\sqrt2)\), then Python `round(c*2^17)` | `REFERENCE_IMPLEMENTATION_VERIFIED`; mirror-origin caveat |
| Normalization | Unsigned 22-bit little-endian \(x\) | 22-bit \(x_\mathrm{norm}\), unary \(s\) | Count leading zero pairs; rotate bit lanes, equivalent to \(x2^{2s}\) | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| Interval selection | Top three bits of normalized input | Boolean selectors | Cases selected from top/second/third bits | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| QROM retrieval | Selector bits | Four 17-bit coefficient magnitudes | XOR controlled constant words | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| Polynomial multiplication | 17-bit coefficient/intermediate; 14-bit fractional \(\Delta\) rows | 17-bit accumulator | Each row shifts left or arithmetic-value right/floor before summation; no rounding | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| Polynomial accumulation | 17-bit unsigned words | 17-bit unsigned words | Three successive subtractions; valid model result must be \(0<r<2^{17}\) | `REFERENCE_IMPLEMENTATION_VERIFIED`; out-of-domain wrap not tested |
| Squaring | 17 fractional-bit \(y_0\) | 28 fractional-bit square | Diagonal bits copied, cross products doubled; lower product columns omitted | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| Mantissa multiply | 22-bit \(x_\mathrm{norm}\), 28-bit square | 30-bit \(z\) | Row alignment and truncation; 28 fractional + 2 integer bits | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| Newton subtraction | 30-bit \(z\) | 30-bit \(3-z\) | Complement then add \((3\ll28)+1\); model direct integer difference | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| Newton multiplication | 17-bit \(y_0\), 30-bit correction | 30-bit \(p\) | Rowwise truncating product; 29 fractional + 1 integer bits | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| Denormalization | 30-bit \(p\), unary flags | 40-bit \(y_1\) | Controlled cyclic shift; model returns \(p\ll s\) | `REFERENCE_IMPLEMENTATION_VERIFIED` |
| Final phase scaling | 40-bit \(y_1\) | Phase fraction \(y_1/2^{40}\) turns | Source assigns one phase operation per output bit; no gate emitted here | `REFERENCE_IMPLEMENTATION_VERIFIED`; independent circuit run `BLOCKED` |
| Addition/subtraction overflow | Fixed-width circuit arrays | Same-width arrays | Source says circuit wraps; model checks fit and raises | `REFERENCE_IMPLEMENTATION_VERIFIED` for source statement; no overflow on valid domain |
| Other precision settings | Caller-supplied widths | Caller-supplied widths | Source allows parameter variations, but this P008 validation covers default benchmark settings | `UNKNOWN` / `BLOCKED` |

## 12. Confirmed and unknown semantics

**Confirmed for the default benchmark model** (`REFERENCE_IMPLEMENTATION_VERIFIED`):

- Exact coefficient integers and Python conversion rule.
- Default widths and fractional-bit positions.
- Unsigned input and source verifier's little-endian register convention.
- Four interval cases and selector behavior.
- Per-row shift/truncation formula and accumulation order.
- Square diagonal/cross-term construction.
- Newton correction constant and register scaling.
- Denormalization and 40-bit phase numerator.
- The independent implementation's final integer output matches the
  mirrored source model for every valid benchmark input.

**Still unknown or unverified**:

- Whether the public mirror's self-described unchanged files are byte-for-byte
  identical to the competition data as served to this specific project
  (`REPOSITORY_DOCUMENTED`, not `OFFICIAL_VERIFIED`).
- Actual Kickmix `iadd`, `isub`, rotation, and circuit serialization behavior
  in an executable local runtime (`BLOCKED`; library missing).
- Independent source-circuit simulation and stage-by-stage circuit output
  comparison (`BLOCKED`; no Kickmix runtime or sample `.kmb`).
- Behavior of source arithmetic on overflow inputs and arbitrary nondefault
  precision settings (`UNKNOWN`; outside the validated benchmark domain).
- Exact relationship of phase-bit gate convention to a simulated circuit in
  this checkout (`BLOCKED`), despite the mirrored verifier describing the
  comparison.

## 13. Implemented primitives and validation

Added [`fixed_point.py`](../../src/invsqrt_opt/fixed_point.py), an independent
integer implementation of coefficient construction, row-truncated products,
polynomial evaluation, square, Newton correction, denormalization, and the
fixed-point phase numerator. It contains no NumPy or floating point in the
pipeline except source-faithful binary64 coefficient construction. It is not
connected to a circuit builder or verifier. The existing P007 real-arithmetic
implementation was not modified.

Added [`test_fixed_point.py`](../../tests/test_fixed_point.py), covering:

- Source-derived coefficient integer table.
- Right-shift truncation, row accumulation, and register overflow.
- Stage vectors for all four coefficient intervals.
- Golden results at domain minima/maxima, powers-of-two neighborhoods,
  interval-region values, and the paper-reported input.
- Invalid inputs, precision objects, width values, and deterministic output.

Additionally, an in-memory execution of the hash-verified mirror's
`fixed_point_model` was compared with this independent implementation for
**all 3,133,452 valid inputs** in bounded chunks. Result: exact integer output
match on every input; no mismatch. This is a comparison to the mirror's
classical source model, not to an executed quantum circuit or official
verifier.

The complete repository test suite was run after implementation:
`python -m pytest` — **140 passed**.

## 14. Emulator readiness decision

- **Integer implementation:** `PARTIALLY IMPLEMENTED` — independent model of
  the inspected fixed-point reference source exists and matches its source
  model exhaustively for the official domain.
- **Full circuit-faithful emulator readiness:** `BLOCKED` — no local Kickmix
  runtime/circuit fixture was available to independently establish the
  source model's equivalence to execution of the circuit.
- **Official verifier / benchmark readiness:** `BLOCKED` — neither was run;
  no official acceptance or score claim is made.

The source is detailed enough to implement its classical integer model. P008
does not overstate that result as a proven circuit simulation.

## 15. Exact blockers and required evidence

1. **Primary artifact provenance:** provide or obtain the official competition
   data archive or a signed/checksummed artifact reference to confirm the
   mirror's source files against the originating Kaggle distribution.
2. **Kickmix runtime:** install/provide the supported Kickmix library and
   confirm version and APIs from package/artifact metadata.
3. **Circuit fixture and execution:** generate or obtain the reference `.kmb`
   and compare circuit-emitted `y1` values with the independent emulator over
   stage-focused vectors; then run the source's circuit tests if available.
4. **Overflow behavior:** use the real runtime to test arithmetic overflow
   outside valid inputs only if needed for a generalized emulator; benchmark
   inputs showed no overflow in the exhaustive model comparison.
5. **Nondefault precision:** validate separately before claiming support for
   arbitrary widths.

## 16. Impact on future circuit construction

The P008 implementation can provide independently coded integer test vectors
for the default reference model. It does not construct an optimized circuit,
prove reversible cleanup, execute phase kickback, or establish official
acceptance. P009 should first close primary-artifact provenance and obtain the
Kickmix runtime/reference circuit; then compare basis-state `y1`, phase,
input-restoration, and scratch-cleanup behavior before any optimization.

## 17. Tests, dependencies, and safety

No dependency was added. No official artifact was added to or modified in the
checkout. No official verifier, benchmark, circuit, or resource count was
executed. No DQI or DFTHC-SOS work was performed.

The full suite result is **140 passed**. `git diff --check` completed
successfully.

## 18. References

1. [Companion paper arXiv:2610.23832v2](https://arxiv.org/abs/2610.23832v2),
   §III.1.2–III.1.3, Appendix B.1/B.3.
2. [Public mirror reference circuit at inspected commit](https://github.com/qarena-ai/invsqrt/blob/6ac78ec5ace6dfd5831ccac2547041408f5d8278/verifiers/invsqrt/nr_reference_circuit.py),
   SHA-256 verified as listed above.
3. [Public mirror verifier at inspected commit](https://github.com/qarena-ai/invsqrt/blob/6ac78ec5ace6dfd5831ccac2547041408f5d8278/verifiers/invsqrt/verify_submission_invsqrt.py),
   SHA-256 verified as listed above.
4. [Public mirror README](https://github.com/qarena-ai/invsqrt/blob/6ac78ec5ace6dfd5831ccac2547041408f5d8278/README.md)
   and [NOTICE](https://github.com/qarena-ai/invsqrt/blob/6ac78ec5ace6dfd5831ccac2547041408f5d8278/NOTICE):
   declared provenance and artifact inventory (`REPOSITORY_DOCUMENTED`).
5. Local P005 `ArtifactManifest.discover` and P005 readiness inspection:
   local verifier, reference circuit, sample submission, and Kickmix are
   `MISSING`; SDK import and API are unavailable/unknown.
