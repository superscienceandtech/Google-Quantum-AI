# DQI-P007 — Independent Classical Decoder Correctness Audit

**Project:** Google Quantum AI — Verifiable Quantum Circuit Compilation
**Workstream:** DQI Decoder
**Phase:** 01 — P007
**Branch:** `feat/dqi-decoder`
**HEAD before and after:** `5391b2e7123484efacffc0588f5e761e67b5cb55`
**Assessment date:** 2026-11-20
**Final disposition:** **PASS — scoped classical correctness audit**

## 1. Executive summary

P005–P006’s classical finite-field, syndrome, polynomial, and decoder code was
audited against the mathematical conventions attributed to Rubin et al.,
arXiv:2610.23832v2, §III.2.2. The package import, public result contract,
failure paths, and research tests were also checked. Independent test oracles
use carryless polynomial multiplication with separate long-division
reduction, direct syndrome summation, direct polynomial evaluation, and
independently computed locator, evaluator, derivative, and Forney values.

The audit found no disagreement between the production decoder and the
independent oracles on the tested vectors, including exact weights 34 and 35.
The decoder now also checks that each EEA remainder strictly decreases and
fails closed if that invariant is violated. It uses an explicit maximum of 35
iterations, justified by the initial syndrome degree being at most 69 and the
loop stopping below degree 35.

P006’s package-initializer discrepancy is a naming error in the reported
completion summary, not a package defect: importing `dqi_decoder` resolves to
`src/dqi_decoder/__init__.py`; no `init.py` exists. No duplicate initializer
was created.

**PASS applies only to this paper-convention classical research prototype and
the inspected test domain.** The Forney ratio is a derivation from the
paper’s syndrome and locator conventions, not an independently specified
official API formula. The official verifier, scorer, fixtures, and serialized
register contract remain unavailable. This audit makes no claim of official
compatibility, benchmark compliance, or quantum reversibility.

## 2. Repository identity and worktree baseline

- Repository root: `D:\PROJECT\Quantum_AI\Google-Quantum-AI`
- Branch: `feat/dqi-decoder`
- HEAD: `5391b2e7123484efacffc0588f5e761e67b5cb55`
- Initial staged changes: none.
- Initial tracked unstaged changes: none.
- Initial worktree had 47 untracked paths: P001–P006 reports and prior DQI
  implementation/tests, plus unrelated INVSQRT bytecode caches.
- All prior untracked work was retained. No branch switch, stage, commit,
  push, merge, cherry-pick, reset, clean, or deletion occurred.

## 3. P005–P006 implementation inventory

| Component | Implementation | Audited responsibility |
|---|---|---|
| Finite field | `src/dqi_decoder/field.py` | GF(2^12) element validation, characteristic-two addition, polynomial-basis multiplication/reduction, power, inverse |
| Syndrome | `src/dqi_decoder/syndrome.py` | 4095-symbol logical error vector to 70 indexed syndromes |
| Polynomial operations | `src/dqi_decoder/polynomial.py` | Low-degree-first normalization, arithmetic, division with explicit remainder, evaluation, formal derivative |
| Decoder | `src/dqi_decoder/decoder.py` | Key-equation EEA, Chien root search, Forney magnitude recovery, radius and full-syndrome checks |
| Public API | `src/dqi_decoder/__init__.py` | Re-exports P005 operations and P006 decoder API |
| Research tests | `tests/dqi_decoder/` | Field, syndrome, polynomial, decoder, independent-oracle and failure-path checks |

These are classical mathematical modules. They do not build a reversible
circuit or implement verifier, benchmark, or competition serialization logic.

## 4. Package initializer discrepancy investigation

The complete `src/dqi_decoder/` directory contains `__init__.py`,
`decoder.py`, `field.py`, `polynomial.py`, and `syndrome.py`; it contains no
`init.py`.

With `PYTHONPATH=src`, importing `dqi_decoder` reported:

```text
dqi_decoder.__file__ =
D:\PROJECT\Quantum_AI\Google-Quantum-AI\src\dqi_decoder\__init__.py
decode_error = (syndromes: collections.abc.Sequence[int]) -> dqi_decoder.decoder.DecodedError
public_imports = OK
```

The public imports `decode_error`, `compute_dqi_syndrome`, `DecodedError`,
`InvalidSyndrome`, and `NoDecodingSolution` resolve from the package exports.
The P006 report itself identifies `__init__.py`; the conflicting
`src/dqi_decoder/init.py` wording was an erroneous completion-summary
reference. No source correction or API change was needed.

## 5. Mathematical convention traceability

Primary mathematical source: Nicholas C. Rubin et al., *Leveraging verifiable
structure in quantum circuits to find more efficient compilations with
agentic AI*, [arXiv:2610.23832v2](https://arxiv.org/abs/2610.23832v2),
§III.2.2, Eq. (39), Eq. (40), and the accompanying reference-implementation
prose. P005 and P006 recorded those sources. The classes below describe
mathematical agreement with the paper, not agreement with an unavailable
verifier executable.

| Convention | Paper statement | Implementation location | Independent test | Mapping |
|---|---|---|---|---|
| Field and element basis | §III.2.2, Eq. (39) and following text: GF(2^12), modulus `alpha^12+alpha^6+alpha^4+alpha+1`, little-endian polynomial basis | `field.py`: `FIELD_DEGREE`, `FIELD_MODULUS_POLYNOMIAL`, `validate_element` | `test_field.py`: parameters, independent carryless multiplication, reduction, inverse oracle | Exact for the paper’s mathematical field; integer encoding is direct coefficient encoding, not circuit serialization |
| Generator / evaluation points | §III.2.2: evaluation points `alpha^j`, `j=0..4094`, enumerate the nonzero field elements | `syndrome.py` and `decoder.py`: `_ALPHA = 0b10`, powers and inverses | `test_field.py`: alpha has order 4095, checking each prime factor of 4095 | Exact paper enumeration; primitivity is implied by listing all 4095 nonzero points and independently confirmed for this modulus |
| Syndrome indexing | §III.2.2: `s_i = sum_j e_j alpha^((i+1)j)`, `i=0..69` | `syndrome.py`: `compute_dqi_syndrome` | `test_syndrome.py`; `test_decoder.py`: `_independent_syndrome` directly sums every contribution | Exact mathematical equation; no wire/register ordering implied |
| Syndrome polynomial | §III.2.2 reference prose: `S(z)=sum_j s_j z^j` | `decoder.py`: syndrome tuple passed as low-degree-first coefficients | `test_decoder.py`: independent key-equation product for `Omega` | Exact coefficient mapping; polynomial arrays are low-degree first |
| Locator factors | §III.2.2: locator proportional to `product_(j:e_j != 0)(1-alpha^j z)` | `decoder.py`: `_key_equation`; `polynomial.py` low-degree-first arithmetic | `test_decoder.py`: independently constructs expected factors and checks roots | Exact; in characteristic two each factor has coefficients `(1, alpha^j)` |
| EEA start and stop | §III.2.2: EEA on `z^(2ell)` and `S(z)`, stopping once the remainder degree is below `ell`; `ell=35` | `decoder.py`: `_key_equation`, `z^70`, threshold 35 | Exact-radius tests and `test_key_equation_rejects_a_non_decreasing_remainder` | Exact paper convention; extra degree-progress and 35-iteration guards are fail-closed hardening |
| Evaluator `Omega` | Eq. (40): `sigma(z) S(z) ≡ Omega(z) mod z^(2ell)` | `decoder.py`: EEA remainder scaled with locator normalization | `test_decoder.py`: independently multiplies returned locator by input syndrome and truncates modulo `z^70` | Exact key-equation relation |
| Root search | §III.2.2: search at inverse error locations `alpha_i^-1` | `decoder.py`: `_find_error_positions` evaluates `sigma(alpha^-j)` | Decoder oracle checks expected factor polynomial and returned position set; repeated-root locator is rejected | Exact inverse-location convention |
| Formal derivative | §III.2.2: Forney recovery uses `sigma'` | `polynomial.py`: `formal_derivative` | `test_polynomial.py`; decoder tests compute derivative independently | Exact formal derivative in characteristic two |
| Forney magnitude | Paper says recover magnitudes from `Omega` and `sigma'`; the explicit ratio follows from its syndrome and locator conventions | `decoder.py`: `_recover_error_symbols` computes `Omega(alpha^-j)/sigma'(alpha^-j)` | `test_decoder.py`: independent polynomial evaluation, derivative, inversion, and magnitude checks | **Derived:** at `x=alpha^-j`, `Omega(x)=e_j alpha^j product_(k!=j)(1-alpha^(k-j))` and `sigma'(x)=alpha^j product_(k!=j)(1-alpha^(k-j))`; their ratio is `e_j`. This derivation is locally tested, not verifier-verified |
| Coordinate contribution | Syndrome equation assigns coordinate `j` contribution `e_j alpha^((i+1)j)` | `syndrome.py`; decoder’s position-to-symbol vector assignment | Independent direct summation compared for all 70 syndromes | Exact paper mapping |
| Result semantics | Paper’s classical reference procedure takes syndrome and recovers error; no received-word API is established by the cited equations | `decode_error(syndromes)` returns `DecodedError.error_symbols`, `error_positions`, locator and evaluator | API tests and full independent syndrome reconstruction | Exact for this research API; it returns an error vector, not a corrected received word |
| Executable register/bit representation | No verified executable register contract or fixture in P003/P004 | Not implemented | Not applicable | **Unresolved:** paper-level mathematical tuples do not define verifier serialization, bit order, or register mapping |

## 6. Independent oracle methodology

The tests distinguish production code from reference calculations:

| Oracle | Method independent of production path | Used to verify |
|---|---|---|
| Field multiplication | Carryless integer polynomial product followed by explicit long-division reduction modulo `0x1053` | Production multiplication across a deterministic grid, seeded sample, and edge pairs |
| Field inverse | Independent reference exponentiation and multiplication, including all 4095 nonzero elements | Production inverse values and multiplicative identity |
| Polynomial evaluation | Direct low-degree polynomial Horner evaluation using the test-only field oracle | Production evaluation at zero, one, small, and high field elements |
| Polynomial division | Separate test-only long division and field inversion | Exact quotient and remainder; confirms nonzero remainders are retained |
| Syndrome reconstruction | Direct sum over all coordinates and all 70 syndrome exponents | Input vectors and every returned candidate |
| Locator | Independent product of `(1, alpha^j)` factors and oracle evaluation at inverse locations | Returned locator polynomial, root positions, and repeated-root rejection |
| Evaluator | Independent product of locator and syndrome followed by truncation modulo `z^70` | Returned `Omega` |
| Forney magnitude | Independent derivative, polynomial evaluation, field inverse, and ratio | Every tested recovered error magnitude |

Expected decoder outputs are generated from locally constructed
position/magnitude vectors, not by calling the production decoder. These
vectors are research tests, not official fixtures.

## 7. Test matrix and boundary results

| Area | Cases added or strengthened | Result |
|---|---|---|
| Zero | Zero syndrome returns the all-zero 4095-symbol vector, empty positions, weight zero, locator 1, evaluator 0; independent reconstruction is zero | Pass |
| Single errors | Positions 0, 1, 137, and 4094; distinct nonzero magnitudes including 1, `0xABC`, and `0xFFF` | Pass |
| Multiple errors | Non-consecutive positions, both endpoints, distinct and repeated magnitudes | Pass |
| Radius boundary | Exact recovery and independent reconstruction for weight 34 and weight 35; verifies complete error-symbol vector and position list | Pass |
| Invalid input | Wrong syndrome length, out-of-field element, `None`, string, and boolean element | Pass: `InvalidSyndrome` |
| Polynomial degeneracy | Zero and constant polynomial behavior; zero locator rejected; constant locator has no roots; repeated-root locator fails expected root count | Pass |
| Forney degeneracy | Repeated locator produces zero derivative denominator; zero evaluator produces zero magnitude at a reported root | Pass: `NoDecodingSolution` |
| EEA/division failures | Non-decreasing remainder fault injection fails closed; independent polynomial division preserves a nonzero remainder | Pass |
| Unmatched syndrome | Selected syndrome with no supported candidate | Pass: `NoDecodingSolution` |
| Beyond radius | Two selected deterministic weight-36 inputs | Both rejected for incorrect number of distinct locator roots; this is only an observation about these vectors |

The weight-36 results do not prove that every out-of-radius syndrome must be
rejected. If a candidate is returned for another syndrome, the implementation
still requires weight at most 35 and exact reconstruction of all 70 syndrome
symbols; the syndrome alone does not establish the original error weight.

## 8. API and result-contract audit

- `decode_error(syndromes: Sequence[int]) -> DecodedError` accepts a
  70-element mathematical syndrome sequence, not a received codeword.
- Invalid sequence shape or field elements raise `InvalidSyndrome`, a
  `ValueError` subclass. Booleans are rejected as field elements.
- A candidate that cannot be established, has invalid roots/magnitudes, or
  fails full syndrome reconstruction raises `NoDecodingSolution`.
- `DecodedError` is frozen. `error_symbols` is a full 4095-entry tuple;
  `error_positions` is strictly ascending from the position scan; `weight`
  is the number of returned positions. Locator and evaluator are
  low-degree-first coefficient tuples.
- Zero syndrome returns a deterministic zero-weight result. Repeated calls
  on the same input are deterministic.
- Public P005 imports remain exported from `__init__.py`; no API change was
  needed.

## 9. Failure-handling and algebraic safety audit

- Field and syndrome inputs are explicitly validated; invalid values are not
  truncated or coerced.
- Polynomial division returns quotient and remainder and rejects the zero
  divisor. The independent division oracle confirms that nonzero remainder
  terms are not discarded.
- EEA begins with degree-70 modulus and a syndrome polynomial of degree at
  most 69. Each nonzero Euclidean remainder must have strictly lower degree
  than the current remainder. Since processing stops below degree 35, at
  most 35 divisions are possible. The implementation enforces strict degree
  progress and a 35-iteration upper bound; injected non-progress raises
  `NoDecodingSolution`.
- Locator normalization rejects zero constant term; root search requires
  exactly `degree(locator)` distinct roots among all 4095 evaluation points.
- Forney recovery rejects zero derivative denominators and zero magnitudes at
  reported roots. Recovered symbols are produced by field operations and
  therefore remain field elements.
- The candidate is returned only after its full syndrome matches all 70
  supplied symbols.
- No broad exception handling or success-shaped fallback was added.

## 10. Defects discovered and changes

1. **Initializer summary typo:** the package was correctly structured; actual
   import resolves to `__init__.py`, and no `init.py` exists. No code change.
2. **EEA progress invariant was implicit:** Euclidean division already
   decreases degree, but `_key_equation` had no explicit guard against a
   broken division result. Added strict remainder-degree validation and a
   35-iteration cap; added a fault-injection test. This is fail-closed
   hardening, not a demonstrated incorrect decode on valid inputs.
3. **Test coverage gaps:** independent multiplication/inverse and polynomial
   evaluation/division oracles were added. Decoder coverage now includes
   explicit weight 34, repeated magnitudes, edge positions, independent
   Forney checks, malformed inputs, and algebraic degeneracies.
4. **Intermediate test-oracle defects:** the first expanded run exposed
   defects in the new tests, not production output: the independent derivative
   helper omitted zero coefficient slots between odd powers, and a field test
   accidentally used `0x1052` (outside `[0,4095]`). Both test defects were
   corrected. Full details are in §13.

No P005–P006 mathematical output mismatch was found by the final independent
test set. This statement is limited to tested vectors and paper-derived
semantics.

## 11. Files changed and reasons

Modified:

- `src/dqi_decoder/decoder.py` — explicit EEA degree-progress and iteration
  guards.
- `tests/dqi_decoder/test_field.py` — independent multiplication/inverse
  oracles.
- `tests/dqi_decoder/test_polynomial.py` — independent evaluation and
  division oracles; zero/constant cases.
- `tests/dqi_decoder/test_decoder.py` — independent root, evaluator,
  derivative, Forney, syndrome checks; boundary/API/invalid/failure cases.

Created:

- `docs/research/DQI_P007_INDEPENDENT_CORRECTNESS_AUDIT.md` — this report.

No files were deleted. P001–P006 reports and unrelated INVSQRT files were not
modified.

## 12. Regression results

All commands ran with `PYTHONPATH=src` and
`PYTHONDONTWRITEBYTECODE=1`; pytest cache was disabled.

| Run | Command | Result |
|---|---|---|
| Pre-edit baseline | `python -m pytest -p no:cacheprovider tests/dqi_decoder -q` | Exit 0; 28 passed, 4,157 subtests passed in 14.37 s |
| First expanded run | Same focused command | Exit 1; 5 failed, 34 passed, 5,408 subtests passed in 24.63 s. The failures were the weight-34 and weight-35 subtests of `test_exact_recovery_at_weights_34_and_35`, `test_multiple_errors_include_repeated_magnitudes_and_both_boundaries`, and `test_multiple_errors_within_radius`; their Forney assertions exposed the test helper’s incorrectly packed derivative coefficients. `test_multiplication_matches_independent_carryless_reference` also failed for `(4178, 4095)` because `4178` (`0x1052`) is outside the valid field-element range. No production mismatch was identified. |
| Corrected oracle rerun | Same focused command | Exit 0; 36 passed, 5,411 subtests passed in 23.21 s |
| Final run after EEA guard test | Same focused command | Exit 0; 37 passed, 5,411 subtests passed in 23.64 s |

Pylance diagnostics were empty for all four modified Python files. Pylance
syntax checks reported no syntax errors in those files. No official verifier,
diagnostic, benchmark, 102,400-shot workload, or unrelated INVSQRT test was
run; no dependencies were installed.

## 13. P001–P006 preservation evidence

SHA-256 values captured before P007 changes were rechecked after the audit.
All prior reports and the P005 files not in P007’s change list remained
unchanged:

| Preserved file | SHA-256 |
|---|---|
| `docs/research/DQI_P001_DEVELOPMENT_FOUNDATION.md` | `dc44f79bd38e7bd38566fc11e3234b0ece5c8adca52b66ece9823e13634eb0f8` |
| `docs/research/DQI_P002_TECHNICAL_CONTRACT.md` | `48e8772d49425cc50c0694ff7b133a7f58af1f218452a2a6ddece8bcb1eec516` |
| `docs/research/DQI_P003_EVIDENCE_READINESS_REPORT.md` | `0f47d0f4c59cdd040a569e7fc55c7a4127e69147f7a530ef2a16741dc4415163` |
| `docs/research/DQI_P004_AUTHORIZED_VERIFIER_FIXTURE_INTAKE.md` | `5496f8817f6835d2eeaa28a6e9f08f84579588eef1ddaac8d2510f6f96131167` |
| `docs/research/DQI_P005_CORE_IMPLEMENTATION_REPORT.md` | `fa937c40436c41751962b86cbc60bdd99b12024240694648f707f5846a763d97` |
| `docs/research/DQI_P005_EVIDENCE_AUTHORIZATION_GAP_CLOSURE_PLAN.md` | `a91d056176782675788c920c2b8e715c28606d538ede4515c911448214c7f4ff` |
| `docs/research/DQI_P006_CLASSICAL_DECODER_IMPLEMENTATION_REPORT.md` | `9d179e6328fa889a83a76fae7d21e8d051e0d96948a80297fd588939c5c42084` |
| `src/dqi_decoder/__init__.py` | `b6d6d3edfb7c48834e25aeadac70239c0b9aca966225025233f4f2f8b66dbc2c` |
| `src/dqi_decoder/field.py` | `de6653a968fddbed701e04706ce61a92a97d7f3c8daa502e40a3db1922a7bb94` |
| `src/dqi_decoder/polynomial.py` | `8bc2ddd8804dd102585d81dd622ec76b0a736741f24d3aacebb0b4d196f1dacf` |
| `src/dqi_decoder/syndrome.py` | `418a48dd94ff7e6a8abcd3bc6d9ce1969dadcead43dad2656f722713a098cfde` |
| `tests/dqi_decoder/test_syndrome.py` | `8b799bb745c84d5631b72f0e4ecfc47929c6ac84ba1d18ee513f970d23434db6` |

The decoder source and three tests listed as modified in §11 were untracked
before and after this phase, so the changes did not overwrite tracked user
work. The original 47 untracked paths remain present; this report adds one
new path. No unrelated file was modified or deleted.

## 14. Remaining mathematical uncertainties

- The Forney ratio is derived from the paper’s explicit syndrome exponent
  convention, locator factors, and use of `Omega` and `sigma'`. The paper
  wording cited by P006 does not provide an independently verified official
  executable formula or test fixture.
- The polynomial-basis integer representation is the direct coefficient
  representation of the paper’s little-endian basis. It is not a verified
  bit-to-wire or serialized field-element convention.
- Decoder behavior is guaranteed/tested only for the paper-defined
  correctable domain and selected malformed/out-of-radius inputs. A syndrome
  does not, by itself, reveal the original error weight.
- No official source was obtained to confirm verifier behavior or whether its
  released implementation exactly matches arXiv v2.

These limitations do not prevent the scoped classical mathematical audit;
they do prevent claims about official executable conformance.

## 15. Official verifier and benchmark limitations

P003–P004 record the official verifier/scorer, reference/sample circuit,
fixtures, and expected outputs as unavailable in the inspected repository
references. This phase did not obtain or execute them. The audit’s locally
generated vectors are not official fixtures. No verifier compatibility,
score, resource count, statistical acceptance, or benchmark compliance is
claimed.

## 16. Quantum reversibility limitations

The audited implementation is classical Python. It does not preserve quantum
input registers, allocate or clean ancillas, uncompute intermediate state,
apply the paper’s target phase, or prove circuit equivalence. Passing these
classical tests is not evidence of reversibility or quantum-circuit
correctness.

## 17. P008 prerequisites

Before any later phase claims executable or circuit readiness:

1. Obtain the authorized official verifier/scorer, reference and sample
   circuits, fixtures, expected outputs, schemas, and immutable provenance.
2. Reconcile field/register serialization and bit ordering against those
   actual artifacts; keep unresolved differences explicit.
3. Independently review this audit and the classical decoder’s scope and
   correctness evidence.
4. Define the quantum operation contract, input-preservation conditions,
   workspace/ancilla requirements, cleanup, and phase semantics from
   authoritative evidence before circuit design.
5. Keep verifier diagnostics, full baseline execution, and optimization
   separately gated. This P007 work does not grant those permissions.

## 18. Final disposition

**PASS — scoped classical decoder correctness audit.** The package/API
behavior is consistent, the paper-derived conventions are implemented
consistently on the tested domain, independent oracles agree, exact
weight-34/35 recovery passes, and malformed or degenerate cases fail
explicitly. This is not a pass for official verifier compatibility, benchmark
readiness, or quantum reversibility.

P007 stops here. No P008 work has started.
