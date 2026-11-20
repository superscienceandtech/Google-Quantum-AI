# DQI-P006 — Classical Decoder Implementation Report

## 1. Executive Summary

This phase extends the P005 mathematical foundation with a classical,
research-only syndrome decoder following the EEA/key-equation, Chien-search,
and Forney-recovery conventions described in the primary paper. It recovers a
candidate error vector only when the vector has weight at most 35 and its
syndrome exactly matches the supplied input.

The implementation does not build a reversible quantum circuit, manage
ancillas, apply the DQI phase, correct a received word, or interface with the
official verifier. The official executable verifier and fixtures remain
unavailable. The decoder is not an official submission and has no official
compatibility or benchmark-compliance claim.

The focused DQI suite passed: **28 tests and 4,157 subtests**. Tests use
deterministic locally constructed research vectors, including an independently
implemented polynomial-basis syndrome oracle. They are not official
competition fixtures.

## 2. Repository and Branch Identity

- Repository root: `D:\PROJECT\Quantum_AI\Google-Quantum-AI`
- Branch before and after: `feat/dqi-decoder`
- HEAD before and after: `5391b2e7123484efacffc0588f5e761e67b5cb55`
- Initial staged tracked changes: none.
- Initial unstaged tracked changes: none.
- Initial untracked files included P001–P005 reports, P005 source and tests,
  and existing unrelated INVSQRT bytecode caches.
- The P006 report path did not exist before this task.

All pre-existing untracked paths were preserved. No branch switch, reset,
clean, stage, commit, push, merge, or cherry-pick operation occurred.

## 3. P005 Implementation Audit

P005 provided:

- `src/dqi_decoder/field.py`: integer polynomial-basis symbols,
  characteristic-two addition, multiplication modulo the field polynomial,
  exponentiation, inversion, and strict element validation.
- `src/dqi_decoder/syndrome.py`: the logical 4095-symbol to 70-syndrome
  calculation.
- `tests/dqi_decoder/test_field.py` and
  `tests/dqi_decoder/test_syndrome.py`: field and syndrome research tests.

The P005 constants and conventions remain unchanged. The decoder uses the
existing field arithmetic and syndrome routine; no P001–P005 report was
modified. P005's prior report accurately describes the earlier state and is
not rewritten to reflect this phase.

## 4. Package/API Integrity Audit

The package initializer that exists is
`src/dqi_decoder/__init__.py`; `src/dqi_decoder/init.py` does not exist. The
package imports successfully using `PYTHONPATH=src`. The public exports were
extended without removing the P005 exports.

New public decoder API:

- `decode_error(syndromes: Sequence[int]) -> DecodedError`
- `DecodedError`, an immutable result with the full `error_symbols`,
  ascending `error_positions`, `locator_polynomial`, and
  `evaluator_polynomial`.
- `InvalidSyndrome` for malformed length/type/field-symbol input.
- `NoDecodingSolution` when no candidate satisfying the supported checks is
  established.
- `DQI_MAX_CORRECTABLE_ERRORS`, fixed at the paper's `ell=35`.

Polynomial operations live in `src/dqi_decoder/polynomial.py` and use
low-degree-first coefficient tuples. They are available from that module;
they are not all promoted to top-level package exports.

## 5. Primary Mathematical Sources

Nicholas C. Rubin et al., *Leveraging verifiable structure in quantum circuits
to find more efficient compilations with agentic AI*, arXiv:2610.23832v2,
2026-10-21:

- [arXiv version record](https://arxiv.org/abs/2610.23832v2)
- [Versioned HTML](https://arxiv.org/html/2610.23832v2)
- §III.2.1, Eqs. (37)–(38): syndrome/record context and promised DQI circuit
  action.
- §III.2.2, Eq. (39) and following text: parameters, field, basis,
  evaluation-point order, syndrome equation, and EEA/Chien/Forney reference
  algorithm.
- §III.2.2, Eq. (40): key equation
  `sigma(z) S(z) ≡ Omega(z) (mod z^(2 ell))`.
- §III.2.2 reference implementation prose: `S(z)=sum_j s_j z^j`;
  locator proportional to `product_(i:e_i != 0)(1-alpha_i z)`;
  EEA on `z^(2 ell)` and `S(z)` stops when the remainder degree is below
  `ell`; Chien search evaluates `sigma(alpha_i^-1)`; Forney recovery uses
  `Omega` and `sigma'`; the zero syndrome uses `sigma=1`, `Omega=0`.
- §III.2.1, Eq. (38): the reversible circuit must preserve syndrome, return
  workspace to zero, and apply the specified phase on the promised domain.

P003 and P004 in the worktree were also read. They record that official
verifier/scorer source, reference/sample circuits, and fixtures were not
available in inspected refs. P002/P004 record unresolved executable register
and serialization conventions. These reports do not substitute for the
primary mathematical source or for missing executable artifacts.

## 6. Decoder Mathematical Conventions

- **Field:** `GF(2^12)` represented in the little-endian polynomial basis
  `(1, alpha, ..., alpha^11)` modulo
  `alpha^12+alpha^6+alpha^4+alpha+1` (`0x1053`).
- **Primitive element:** the paper indexes all `m=q-1=4095` nonzero
  evaluation points as `alpha^j`. This implies alpha enumerates the
  multiplicative group. The implementation's field test verifies
  `alpha^4095=1` and that no proper order dividing 4095 is obtained for its
  prime factors 3, 5, 7, and 13.
- **Syndrome:** 70 symbols indexed `i=0,...,69`,
  `s_i=sum_(j=0)^4094 e_j alpha^((i+1)j)`.
- **Error positions:** position `j` has evaluation point `alpha^j`.
- **Polynomial representation:** coefficient arrays are low-degree first:
  entry `k` is the coefficient of `z^k`. This follows the paper's
  `S(z)=sum_j s_j z^j` indexing and is documented in the polynomial module.
- **Locator:** normalized to constant term 1, with roots at `alpha^-j`:
  `sigma(z)=product_(j:e_j != 0)(1-alpha^j z)`. In characteristic two,
  subtraction and addition are identical.
- **Evaluator:** `Omega(z)` is the low-degree remainder in the key equation,
  normalized by the same scalar as the locator.
- **Radius:** fixed `ell=35`; EEA terminates once the remainder degree is
  strictly less than 35, matching the paper.
- **Magnitude:** the paper specifies Forney recovery from `Omega` and
  `sigma'`. From those source conventions and the syndrome starting at
  exponent `i+1`, the implementation uses
  `e_j=Omega(alpha^-j)/sigma'(alpha^-j)`. This formula is the
  source-convention derivation used in code; it is checked against an
  independent syndrome oracle.
- **Output:** the API returns the recovered error vector `e(s)` and
  certificates. The primary paper's classical decoder input is a syndrome,
  not a received word. A corrected received word is therefore not returned;
  the paper does not define a received-word input contract for this API.

No circuit register ordering, bit ordering, or serialization is inferred.

## 7. Classical Decoder Pipeline

`src/dqi_decoder/decoder.py` performs:

1. Validate that the input is a sequence of exactly 70 field elements.
2. Handle the zero syndrome explicitly as zero error, locator 1, evaluator 0.
3. Run polynomial extended Euclid on `z^70` and `S(z)`, tracking the
   coefficient of `S(z)`, until the current remainder has degree below 35.
4. Normalize the resulting locator so its constant coefficient is 1 and
   scale the evaluator consistently.
5. Search each position `j=0,...,4094` at `alpha^-j`; require exactly as many
   distinct roots as the locator degree.
6. Compute the formal derivative in characteristic two and recover each
   symbol with the Forney ratio. A zero denominator or zero recovered
   magnitude at a reported root is rejected.
7. Require the number of roots to be at most 35 and recompute the candidate's
   syndrome with the P005 implementation. Return only if it matches all 70
   supplied symbols exactly.

Invalid input raises `InvalidSyndrome`; inability to establish a valid
candidate raises `NoDecodingSolution`. The latter does not prove that the
input is mathematically beyond radius 35; it means only that this decoder
did not establish a supported solution.

## 8. Error-Locator Implementation

`src/dqi_decoder/polynomial.py` supplies normalized low-degree-first
polynomials, addition, scalar multiplication, polynomial multiplication,
long division, evaluation, and formal derivative over the P005 field API.

The locator path in `decoder.py` follows the paper's EEA convention:

- Initialize remainders with `r0=z^70` and `r1=S(z)`.
- Initialize the tracked `S` coefficients with `t0=0`, `t1=1`.
- Apply ordinary polynomial Euclidean updates until the current remainder
  degree is less than 35.
- The current tracked coefficient gives the locator up to a nonzero scalar;
  normalize its constant coefficient to 1.
- Scale the current remainder by the same factor to produce `Omega`.
- For zero syndrome, return the paper's explicit `sigma=1`, `Omega=0`
  special case.

This is the classical polynomial EEA described by the paper, not the
paper's optimized synchronized quantum circuit construction. A locator with
zero constant coefficient, degree over 35, or an incorrect count of roots
among the 4095 evaluation points is rejected.

## 9. Error-Location Implementation

For each coordinate `j`, code computes `alpha^j`, inverts it, and evaluates
the locator at `alpha^-j`. A zero value marks an error coordinate, matching
the paper's locator product and Chien-search convention.

The error positions are returned in ascending coordinate order. They are
mathematical vector indices only; they do not imply circuit wire or register
ordering.

## 10. Error-Evaluator and Magnitude Implementation

Polynomial division and EEA produce the evaluator satisfying
`sigma*S ≡ Omega mod z^70`. The formal derivative retains only odd-power
coefficients because the field has characteristic two. For a root
`alpha^-j`, the implementation evaluates both `Omega` and `sigma'` and
computes their field quotient. A zero derivative denominator and zero
recovered magnitude at a reported root raise `NoDecodingSolution`.

The test suite independently rebuilds the locator from known positions and
checks the truncated key-equation product against the returned evaluator.
It also verifies the returned magnitudes by recomputing the original
syndrome using a separate direct field-arithmetic oracle.

## 11. Corrected-Word Semantics

The decoder returns a verified error vector, not a received word or corrected
codeword. The paper's DQI decoder contract is syndrome-to-error recovery for
the phase correction; it does not define a received-word API here. Although
addition and subtraction coincide in characteristic two, the code does not
invent an input word, codeword representation, or corrected-word return
contract.

## 12. Source-to-Code Traceability

| Requirement/step | Implementation | Source |
|---|---|---|
| GF parameters and polynomial basis | Existing `field.py` constants and arithmetic | arXiv v2 §III.2.2, Eq. (39) and following text; P005 implementation audit |
| Syndrome length, order and equation | Existing `syndrome.py` | arXiv v2 §III.2.2 syndrome definition |
| Syndrome polynomial `S(z)` | `decoder.py` passes input tuple as low-degree-first `S` to EEA | arXiv v2 §III.2.2, EEA prose |
| Key equation | `_key_equation` in `decoder.py` | arXiv v2 §III.2.2, Eq. (40) |
| EEA start/termination | `_key_equation` uses `z^70`, `S`, stop at remainder degree `<35` | arXiv v2 §III.2.2, EEA prose |
| Locator factors/normalization | `_key_equation`; low-degree-first polynomial operations | arXiv v2 §III.2.2 locator definition; normalization chooses the paper's proportional locator with constant term 1 |
| Zero syndrome special case | `_key_equation` and `decode_error` | arXiv v2 §III.2.2 explicitly states `sigma=1`, `Omega=0` |
| Root map | `_find_error_positions` evaluates at `alpha^-j` | arXiv v2 §III.2.2 Chien-search prose |
| Magnitude recovery | `_recover_error_symbols` evaluates `Omega/sigma'` | arXiv v2 §III.2.2 Forney prose; formula derived from the paper's syndrome and locator conventions |
| Verified result | `decode_error` re-encodes candidate and compares all syndromes | Research correctness guard; official acceptance semantics are unavailable |
| Reversible circuit and phase | Not implemented | arXiv v2 §III.2.1, Eq. (38); future work |

## 13. Test Strategy and Independent Test Oracles

Tests in `tests/dqi_decoder/` are local research tests, not official fixtures.
They include:

- P005 field and syndrome regressions.
- Field polynomial, identity, reduction, exponentiation, inverse, validation,
  and alpha-order tests.
- Polynomial normalization, arithmetic, division reconstruction,
  evaluation, derivative, and zero-divisor rejection.
- Zero, single-error, multiple-error, and exact 35-error decoding.
- A 36-error boundary probe that accepts either an explicit no-solution result
  or a returned candidate only if it is within radius and independently
  reproduces the syndrome. It does not assert a decoder outcome beyond the
  paper's guaranteed radius.
- Malformed syndrome length/symbols and an unmatched syndrome case.
- An independent test oracle using carryless polynomial multiplication with
  explicit long-division reduction and direct evaluation of the paper's
  syndrome sum. The test also independently constructs the expected locator
  and checks the key equation for returned `Omega`.

The test oracle shares the paper's stated field polynomial, but does not call
the production syndrome evaluator or production polynomial operations to
derive expected syndrome values.

## 14. Test Results

Focused command:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -p no:cacheprovider tests\dqi_decoder -q
```

Final observed result: **28 passed, 4,157 subtests passed in 13.94 seconds**.
Pylance syntax checks found no syntax errors in new Python files. Pylance
diagnostics for the final new/modified DQI source and test files were empty.
No unrelated INVSQRT tests or workloads were run.

The deterministic 36-error probe in this run raised `NoDecodingSolution`
because the locator did not have the expected number of distinct roots among
the evaluation points. This result is specific to that research vector; it
does not establish an outcome for every syndrome outside radius 35.

## 15. Complexity and Performance

Let `m=4095`, `n=70`, and `ell=35`.

- EEA uses classical polynomial arithmetic on degree-at-most-70 polynomials;
  with the implemented low-degree-first multiplication and division, its
  algebraic work is bounded by `O(n^2)` field operations for the Euclidean
  sequence.
- Chien search evaluates at all `m` positions using degree-at-most-ell
  polynomials: `O(m*ell)` field operations.
- Candidate validation recomputes 70 syndromes over 4095 positions with
  Horner evaluation: `O(m*n)` field operations.
- The full error vector requires `O(m)` field elements; syndrome and
  polynomial state require `O(n)` field elements.
- The local focused test runtime is reported in §14 only. It is not a
  competition performance metric or official resource measurement.

No quantum qubit count, Toffoli count, depth, official score, or benchmark
performance was measured.

## 16. Unsupported and Unresolved Cases

- This implementation handles only the fixed DQI parameters and field
  representation. It is not a generic Reed–Solomon package.
- It does not prove correctness for arbitrary syndromes or identify whether
  an unmatched syndrome is beyond radius, malformed under a hidden official
  convention, or otherwise invalid.
- The paper guarantees unique decoding for the promised weight-35 domain;
  behavior outside it is not upgraded into a guarantee. A 36-error syndrome
  could potentially coincide with a supported candidate in a boundary case;
  any returned candidate is nevertheless checked for radius and exact
  syndrome agreement.
- Multiple-root/zero-derivative and malformed-locator cases are rejected;
  no official fixture coverage is available for these cases.
- No received-word or corrected-codeword interface is implemented.
- No verifier register/wire/bit ordering, binary serialization, phase-record
  mapping, or output schema is defined.
- No official score, seed construction, confidence-bound implementation, or
  resource-counting behavior is implemented.

## 17. Quantum Reversibility Gap

This phase is a classical algorithm only. It does not show that EEA,
polynomial arithmetic, root search, or magnitude recovery is reversible.
Future circuit work must separately establish reversible arithmetic,
reversible EEA/state handling, root and magnitude computation, input
preservation, ancilla initialization and cleanup, output extraction, and
equivalence to the phase action in arXiv v2 §III.2.1 Eq. (38). Circuit
legality and resource accounting must use the official executable contract
when available.

## 18. Official Verifier Compatibility

**NOT AVAILABLE.** P004 reports that the official verifier/scorer and
fixtures are absent from the inspected refs/worktree. No official verifier
was imported or executed. No compatibility or competition-readiness claim
is made.

## 19. Files Created and Modified

Created:

- `src/dqi_decoder/polynomial.py`
- `src/dqi_decoder/decoder.py`
- `tests/dqi_decoder/test_polynomial.py`
- `tests/dqi_decoder/test_decoder.py`
- `docs/research/DQI_P006_CLASSICAL_DECODER_IMPLEMENTATION_REPORT.md`

Modified:

- `src/dqi_decoder/__init__.py` — exports the decoder API.
- `tests/dqi_decoder/test_field.py` — adds a primitive-element order check
  implied by the paper's `q-1` evaluation-point enumeration.

Unchanged: P001–P005 reports, P005 field/syndrome implementation, P005 tests
other than the noted field-test addition, P005 gap-closure plan, and unrelated
INVSQRT files. No files were deleted.

## 20. Remaining Work

1. Obtain and provenance-check official verifier/scorer source, reference and
   sample circuits, schemas, fixtures, and expected outputs.
2. Cross-check field/register serialization and phase-record mapping against
   those executable artifacts.
3. Add official fixture tests only after authorized receipt; keep them
   separate from local research tests.
4. Define any received-word/codeword API from an authoritative source before
   implementing corrected-word output.
5. Design and prove a reversible circuit separately; classical decoder
   success does not establish clean workspace or target phase.
6. Implement verifier integration and official resource accounting only when
   the executable interface and counting rules are available.
7. Keep verifier execution and the 102,400-shot baseline separate from these
   research tests; no benchmark authorization is inferred from P006.

## 21. Final Status

**PARTIAL — classical research decoder prototype implemented and tested.**
The paper-convention EEA locator/evaluator, Chien root search, and Forney
magnitude recovery recover and verify error vectors through the documented
radius of 35 on deterministic research vectors. P005 functionality remains
available. Quantum reversibility, corrected received-word semantics, official
verifier compatibility, and competition readiness remain unimplemented or
unverified. P006 stops here; no P007 work has started.
