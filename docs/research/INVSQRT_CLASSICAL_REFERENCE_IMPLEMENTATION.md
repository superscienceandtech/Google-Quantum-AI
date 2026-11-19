# INVSQRT Classical Reference Implementation

## 1. Purpose and scope

P007 implements and validates a classical, high-precision model of the
paper-described INVSQRT stages. It is a reproducible numerical reference, not
a reproduction of the reference quantum circuit.

The implementation covers input validation, leading-zero-pair normalization,
the paper's two cubic coefficient sets and upper-range rescaling, one
real-arithmetic Newton–Raphson correction, the resulting inverse-square-root
estimate, and a classical phase-in-turns value. It does not emulate QROM,
fixed-point arithmetic, gate synthesis, phase kickback, uncomputation, or the
official verifier.

Labels used in the validation record distinguish `CLASSICAL_REFERENCE`,
`PAPER_REPORTED`, `HIGH_PRECISION_ORACLE`, `SAMPLED_VALIDATION`,
`EXHAUSTIVE_VALIDATION`, and `QUANTUM_VERIFICATION_NOT_PERFORMED`. Numerical
agreement is not official verifier acceptance or a quantum resource result.

## 2. Paper version and source locations

The primary source inspected was *Leveraging verifiable structure in quantum
circuits to find more efficient compilations with agentic AI*,
[arXiv:2610.23832v2](https://arxiv.org/abs/2610.23832v2), including its
[HTML version](https://arxiv.org/html/2610.23832v2).

Relevant locations:

- §III.1.2, Eqs. (14)–(31): leading-zero-pair normalization, the two
  polynomial forms and coefficient values, the Newton step, denormalization,
  and phase/uncompute overview.
- Appendix B.1, Eqs. (102)–(105): polynomial rescaling for the normalized
  input interval \([2,4)\).
- Appendix B.3, Eqs. (106)–(110): interval selection, Horner forms, offsets,
  coefficient selection, and fixed-point circuit register/truncation details.
- §III.1.3: benchmark domain, target phase, and the paper-reported circuit
  result used for the comparison below.

The implementation's source references are embedded in its validation record.
The benchmark constants are read from the existing P003
[`OFFICIAL_INVSQRT_SPEC`](../../src/invsqrt_opt/contract.py), not duplicated.

## 3. Mathematical function and input domain

The target classical value is

\[
f(x)=\frac{1}{\sqrt{x}},\qquad 1\leq x\leq3{,}133{,}452,
\]

for the benchmark's \(n_p=10\), \(\beta=1\), and 22-bit input. The intended
phase in turns is \(\beta f(x)\), modulo one when represented as a phase. The
implementation reports the unwrapped and modulo-one classical values
separately. It does not convert them into a quantum gate.

Inputs are validated by the P003 domain helper. Booleans, non-integers, and
values outside the inclusive domain are rejected; invalid values are never
clipped.

## 4. Normalization algorithm

For integer input \(x\), the number of leading zero pairs in the 22-bit
register is

\[
s=\left\lfloor\frac{22-\operatorname{bit\_length}(x)}{2}\right\rfloor.
\]

The 20-fractional-bit normalized value is represented exactly as the rational

\[
u=x\,2^{2s-20}\in[1,4).
\]

The implementation preserves \(u\) as a `Fraction` for boundary decisions and
converts it to 50-digit `Decimal` arithmetic for polynomial evaluation.
Examples derived from the formula are \(x=3\mapsto(s,u)=(10,3)\) and
\(x=4\mapsto(s,u)=(9,1)\).

The paper writes the post-Newton denormalization as \(y_1=p\,2^s\)
(Eq. (31)). With the 20-fractional-bit normalized input above, this register
scale corresponds to a physical inverse-square-root estimate
\(y_1/2^{n_p}\). The code exposes both `denormalized_register_estimate` and
`final_estimate`; the latter is the value compared to \(1/\sqrt{x}\). This
scale conversion is a mathematical interpretation of the paper's fixed-point
binary-point convention, not a reconstruction of its bit-level circuit.

## 5. Piecewise cubic definition and coefficients

For \(v\in[1,2)\), the paper gives the following coefficient sets and
polynomials (Eqs. (15)–(24)):

\[
P_a(v)=a_0-a_1(v-1)+a_2(v-1)^2-a_3(v-1)^3
\quad (1\leq v<3/2),
\]

\[
P_b(v)=b_0-b_1(v-3/2)+b_2(v-3/2)^2-b_3(v-3/2)^3
\quad (3/2\leq v<2),
\]

| Coefficient | Paper value |
|---|---:|
| \(a_0\) | 0.99994132489119882162 |
| \(a_1\) | 0.49609891915903542303 |
| \(a_2\) | 0.33261112772430493331 |
| \(a_3\) | 0.14876762006038398086 |
| \(b_0\) | 0.81648515205385221995 |
| \(b_1\) | 0.27136515484240234115 |
| \(b_2\) | 0.12756148214815175348 |
| \(b_3\) | 0.044753028579153842218 |

For \(u<2\), the polynomial argument is \(v=u\) and no rescaling is applied.
For \(2\leq u<4\), the argument is \(v=u/2\), and the selected polynomial is
multiplied by \(1/\sqrt{2}\), following Appendix B.1, Eqs. (102)–(105). Thus
the four normalized regions are \([1,1.5)\), \([1.5,2)\), \([2,3)\), and
\([3,4)\). The half-open intervals follow the paper's QROM selection cases in
Appendix B.3.

The implementation evaluates each polynomial in Horner form, with exact
paper-provided decimal coefficient strings. It does not round coefficients to
the reference circuit's QROM format.

## 6. Newton–Raphson correction

For normalized input \(u\) and initial estimate \(y_0\), the code applies
exactly one real-arithmetic inverse-square-root Newton step:

\[
p=\frac{1}{2}y_0(3-u y_0^2).
\]

It then forms the paper-described denormalized intermediate \(p\,2^s\) and
converts that scaled value to the physical estimate by dividing by \(2^{n_p}\).
The initial and corrected normalized estimates and both final-scale values are
available in the immutable `ReferenceResult`.

The paper describes finite-width circuit registers, including 17 fractional
bits for QROM coefficients/Horner intermediates, truncated partial products,
and subsequent 28-, 29-, and 30-bit arithmetic registers (Appendix B.3).
P007 does not emulate those operations. In particular, it does not infer a
coefficient encoding/rounding or overflow convention from the paper's decimal
coefficients.

## 7. Numerical precision assumptions

The model uses Python `Decimal` with a configurable precision of at least 32
decimal digits (default 50). Decimal arithmetic uses the active context's
rounding mode (`ROUND_HALF_EVEN` by default). The coefficient decimals are
loaded from the published strings. The rational normalization itself is exact.

There is no intermediate fixed-point quantization, truncation, saturation,
or additional Newton iteration. This is an idealized real-arithmetic model
with finite Decimal evaluation precision, not the paper's fixed-point circuit.

## 8. Independent high-precision oracle

The oracle is implemented independently as `1 / Decimal(x).sqrt()` at 50
digits. It does not call the normalization, polynomial, or Newton code. The
phase oracle is independently computed as \(\beta/\sqrt{x}\) in turns.

For each input, the report defines:

- absolute error: \(|\hat f(x)-f(x)|\);
- relative error: \(|\hat f(x)-f(x)|/f(x)\);
- signed error: \(\hat f(x)-f(x)\);
- signed relative error: \((\hat f(x)-f(x))/f(x)\).

These are inverse-square-root/phase-in-turns errors. They are not radians;
conversion of a turn difference to radians would multiply by \(2\pi\). No
official modulo-distance comparator is implemented.

## 9. Validation methodology and exhaustive results

The P007 exhaustive run evaluated every integer from 1 through 3,133,452,
inclusive, once, in deterministic ascending order. Each model result was
compared with the independent 50-digit Decimal oracle. In addition, the run
tracks inputs at and immediately around normalization and polynomial interval
boundaries; 118 distinct valid boundary cases were included in the domain
iteration.

| Measurement | Exhaustive local result |
|---|---:|
| Validation mode | `EXHAUSTIVE_VALIDATION` |
| Evaluated inputs | 3,133,452 |
| Oracle/model precision | 50 decimal digits |
| Maximum absolute error | \(5.16405158684016760144785491987692297221484\times10^{-9}\) |
| Input at maximum absolute error | 1 |
| Maximum relative error | \(5.1643545984960819089670834272040066197411095618635\times10^{-9}\) |
| Input at maximum relative error | 1,123,799 |
| Mean signed error | \(-1.732615836942596313214628824\times10^{-12}\) |
| Mean absolute error | \(1.732615836942596313214628824\times10^{-12}\) |
| Mean signed relative error | \(-1.614220050390739466318973632\times10^{-9}\) |
| Mean absolute relative error | \(1.614220050390739466318973632\times10^{-9}\) |
| Maximum boundary relative error | \(5.16405158684016760144785491987692297221484\times10^{-9}\) at \(x=1\) |

Relative-error distribution over the exhaustive domain:

| Absolute relative error | Count |
|---|---:|
| \(\leq10^{-12}\) | 57,157 |
| \((10^{-12},10^{-11}]\) | 124,145 |
| \((10^{-11},10^{-10}]\) | 410,491 |
| \((10^{-10},10^{-9}]\) | 1,108,944 |
| \((10^{-9},10^{-8}]\) | 1,432,715 |
| \(>10^{-8}\) | 0 |

Execution provenance: CPython 3.14.6, Windows 11 (AMD64), 50-digit Decimal
precision, completed at `2026-11-19T17:34:10.625696Z`. These measurements are
local results of the P007 classical model only. The numerical validation
record includes the algorithm and paper versions, source references,
validation mode, domain, evaluation count, precision, errors, environment,
timestamp, the paper-reported error/input and the measured comparison when
that input was evaluated, and `QUANTUM_VERIFICATION_NOT_PERFORMED`. Sampled
records also retain the requested sample count and seed when supplied. It
deliberately contains no qubit or gate metrics.

## 10. Comparison with the paper-reported result

The paper reports a reference-circuit worst-case relative error of
\(2.84\times10^{-8}\) at \(x=2{,}588{,}411\) (§III.1.2, immediately before
§III.1.3). The relative error is the same mathematical quantity as the
classical model's relative inverse-square-root error, so a numerical
comparison is meaningful, but the implementations are not equivalent.

At that input, the idealized P007 model measured relative error
\(4.0227848172749841925464768555553667348467114121761\times10^{-9}\), an
absolute difference of
\(2.4377215182725015807453523144444633265153288587824\times10^{-8}\) from the
paper-reported value. The model's exhaustive worst case instead occurs at
\(x=1{,}123{,}799\). The difference is expected to reflect, among other
things, the model's unquantized Decimal polynomial and real-arithmetic
Newton step versus the paper's finite-width circuit arithmetic. This is a
comparison, not a reproduction of the paper's circuit result; no value was
forced to match the report.

## 11. Tests and deterministic behavior

[`tests/test_reference_math.py`](../../tests/test_reference_math.py) checks
input boundaries and rejection, pair-shift normalization, all four polynomial
regions and exact interval cases, published coefficient values, the Newton
formula, final scaling, independent-oracle behavior, the paper-reported input,
determinism, sampled provenance, and rejection of an incomplete “exhaustive”
range. The full repository suite passed: `python -m pytest` — **94 passed**.

Run exhaustive validation from the repository root in PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m invsqrt_opt.numerical_validation --mode EXHAUSTIVE_VALIDATION
```

For a reproducible uniform sample augmented with all required edge cases, run:

```powershell
$env:PYTHONPATH = "src"
python -m invsqrt_opt.numerical_validation --mode SAMPLED_VALIDATION
```

The sampled mode is clearly labelled and must not be reported as exhaustive.

## 12. Quantum implications and remaining blockers

The classical result provides candidate numeric stages for future investigation;
it does not establish a reversible implementation, cleanup, phase correctness
under the official comparator, or any resource count. A circuit-faithful
reproduction remains **BLOCKED** pending an unambiguous bit-level contract for
QROM coefficient encoding and rounding, signed intermediate/overflow
semantics, and exact fixed-point operation conventions. The paper does state
register widths and truncation of partial products, but this P007 model does
not claim those details are sufficient to establish exact circuit equivalence.

No quantum circuit, `Z_POW` gate, phase kickback, uncomputation, official
verifier, or benchmark was run. No official acceptance, score, or resource
improvement is claimed.

## 13. Dependencies and implementation files

P007 adds no dependencies. The implementation is in
[`reference_math.py`](../../src/invsqrt_opt/reference_math.py) and
[`numerical_validation.py`](../../src/invsqrt_opt/numerical_validation.py).
The P002–P006 work and official artifacts were not modified by the numerical
implementation. The README links this document.
