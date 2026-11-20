# DQI-P009 — Reversible Finite-Field Primitive Models

**Project:** Google Quantum AI — Verifiable Quantum Circuit Compilation  
**Workstream:** DQI Decoder  
**Phase:** 01 — P009  
**Branch:** `feat/dqi-decoder`  
**Repository:** `D:\PROJECT\Quantum_AI\Google-Quantum-AI`  
**HEAD before and after:** `5391b2e7123484efacffc0588f5e761e67b5cb55`  
**Status:** **COMPLETE — CLASSICAL REVERSIBLE-SEMANTICS MODELS ONLY**

## 1. Executive summary

P009 adds four deterministic Python functions modeling input-preserving,
XOR-accumulating transformations over the repository's `GF(2^12)` field:
addition, multiplication, squaring, and a totalized inverse. Operands are
returned unchanged and the operation result is XORed into a target field
element. The functions validate every field element and return immutable
tuples.

The test suite exhaustively checked every input/target state over independently
modeled `GF(2^2)`, `GF(2^3)`, and `GF(2^4)` for all four transformations. It
also compared selected `GF(2^12)` behavior with an independent polynomial
arithmetic oracle and checked input preservation and involution properties.
The final focused run passed: **9 tests and 33 subtests**.

These are classical functions that express reversible register relations.
They do **not** construct quantum gates or circuits, establish a gate
decomposition, prove ancilla cleanup for a circuit, implement the DQI decoder,
or demonstrate compatibility with an official verifier. No verifier,
diagnostic, benchmark, or 102,400-shot workload was run.

## 2. Repository and branch identity

| Item | Result |
|---|---|
| Repository root | `D:\PROJECT\Quantum_AI\Google-Quantum-AI` |
| Branch before and after | `feat/dqi-decoder` |
| HEAD before and after | `5391b2e7123484efacffc0588f5e761e67b5cb55` |
| Initial staged changes | None |
| Initial tracked unstaged changes | None |
| Existing untracked work | Preserved; no existing paths were overwritten or deleted |
| Dependency/configuration changes | None |

Existing DQI and unrelated INVSQRT untracked paths were left in place. The
new implementation and test files were also untracked at final inspection;
no files were staged or committed.

## 3. Evidence used

1. **P008 reversible-decoder specification** —
   [`DQI_P008_REVERSIBLE_DECODER_SPECIFICATION.md`](./DQI_P008_REVERSIBLE_DECODER_SPECIFICATION.md),
   especially its reversible-operation and field-arithmetic discussion. It
   separates paper-level mathematical behavior from incomplete circuit and
   verifier details and identifies target-XOR mappings as a reversible
   arithmetic contract/model, not a local executable circuit.
2. **Existing field implementation** — [`field.py`](../../src/dqi_decoder/field.py).
   It defines `GF(2^12)`, polynomial-basis encoding, modulus `0x1053`,
   strict element validation, addition, multiplication, and nonzero inverse.
3. **Primary research claims as summarized and source-traced in P008** —
   Rubin et al., arXiv:2610.23832v2, §III.2.2, as cited in P008. Those claims
   support mathematical context, but do not supply a verifier, circuit
   serialization contract, or the implementation in this phase.

No new external source was downloaded or treated as executable evidence.
P009's four tuple transformations are explicit research-model definitions
implemented for this task; they are not asserted to be an official
competition interface.

## 4. Mathematical components implemented

Let `a`, `b`, and `t` be 12-bit polynomial-basis field elements, `+` be field
addition, `·` be field multiplication, and `ι(a)` be the field inverse for
nonzero `a`. The module implements:

| Function | Returned tuple | Semantics |
|---|---|---|
| `xor_accumulate_add(a, b, t)` | `(a, b, t XOR (a + b))` | Keeps both inputs; XORs their field sum into the target |
| `xor_accumulate_multiply(a, b, t)` | `(a, b, t XOR (a · b))` | Keeps both inputs; XORs their field product into the target |
| `xor_accumulate_square(a, t)` | `(a, t XOR (a · a))` | Keeps the input; XORs its square into the target |
| `xor_accumulate_inverse(a, t)` | `(a, t XOR ι₀(a))` | Keeps the input; XORs the inverse into the target |
| `target_width()` | `12` | Reports the width of a field-element target |

Here `ι₀(0)=0` and `ι₀(a)=ι(a)` for nonzero `a`. This total extension is
specific to the reversible transformation model: zero has no multiplicative
inverse. The existing classical `field.inverse(0)` behavior remains unchanged
and raises `ValueError`.

All four transformations have the abstract form
`(x, t) -> (x, t XOR f(x))`. Applying the same transformation twice restores
the original tuple because the input is retained and `y XOR f(x) XOR f(x)=y`.
This is a property of the returned-value functions, not evidence that any
particular circuit decomposition is available or clean.

## 5. Source-to-code traceability

| Implemented behavior | Source / support | Qualification |
|---|---|---|
| Field elements are integers in `[0, 4095]` | `src/dqi_decoder/field.py`: `FIELD_DEGREE`, `FIELD_SIZE`, `validate_element` | Existing local mathematical representation; not a wire serialization |
| Field addition is coefficient-wise XOR | `src/dqi_decoder/field.py`: `add`; P008 field-arithmetic discussion | Implemented through the existing field helper |
| Product and square use the existing polynomial-basis field | `src/dqi_decoder/field.py`: `multiply`; P008 field-arithmetic discussion | Squaring is computed as `multiply(value, value)` |
| Nonzero inverse uses the existing field inverse | `src/dqi_decoder/field.py`: `inverse`; P008 field contract | Zero is explicitly totalized to zero only in the new model |
| Operands are retained and result XORed into target | P008 reversible-operation discussion; P009 model contract | A classical tuple relation; not an official circuit requirement |
| Target width is 12 bits | Existing `FIELD_SIZE = 1 << 12` | Computed by `target_width()`; not a serialization promise |

No new syndrome, polynomial, decoder, wire-order, or circuit semantics were
implemented.

## 6. Architecture and module responsibilities

- [`reversible_primitives.py`](../../src/dqi_decoder/reversible_primitives.py)
  contains only the four transformations and the target-width helper. Each
  function validates operands and target with the existing
  `validate_element`, then delegates field arithmetic to the existing
  implementation.
- [`test_reversible_primitives.py`](../../tests/dqi_decoder/test_reversible_primitives.py)
  contains a separate small-field arithmetic oracle, irreducibility checks,
  exhaustive transformation tests, and selected `GF(2^12)` comparisons.
- The package initializer, field implementation, classical decoder, and
  prior phase reports were not modified.

## 7. Public API

The module-level API is:

```python
from dqi_decoder.reversible_primitives import (
    target_width,
    xor_accumulate_add,
    xor_accumulate_multiply,
    xor_accumulate_square,
    xor_accumulate_inverse,
)

result = xor_accumulate_multiply(0x123, 0x456, 0x135)
# (0x123, 0x456, 0x61B)
```

Inputs and target must each be exact Python integers in `[0, 4095]`; invalid
types raise `TypeError`, and out-of-range values raise `ValueError`. As with
the existing field validator, booleans are rejected. The functions do not
mutate caller data. The API does not provide a circuit object, gate list,
measurement behavior, verifier serialization, or decoder entry point.

## 8. Reversibility considerations

The returned tuple functions preserve all declared input elements and update
only the target by XOR. Their involution property establishes that the
mathematical tuple mapping is bijective for each fixed operation, including
the explicitly totalized inverse mapping.

This does not establish:

- a reversible gate implementation or gate decomposition;
- ancilla count, initialization, peak workspace, or cleanup;
- coherent control or phase semantics for the DQI decoder;
- behavior matching the official verifier on serialized input; or
- a complete reversible computation for the decoder.

The P008 circuit-level gaps therefore remain open.

## 9. Tests created and execution results

### Test model

The tests independently check that the proposed small-field moduli are
irreducible by enumerating monic possible divisors up to half the field degree.
Small-field multiplication uses shift/XOR polynomial multiplication followed
by reduction modulo the chosen polynomial; inversion searches candidates
directly. The small-field oracle does not call production `field.multiply`,
`field.inverse`, or the new transformation functions to derive expected
outputs. Addition is independently defined as XOR in characteristic two.

For each operation and each small field, every combination of operand(s) and
target was enumerated. The total checked input-state counts are:

| Operation | `GF(2^2)` | `GF(2^3)` | `GF(2^4)` | Total |
|---|---:|---:|---:|---:|
| Addition | 64 | 512 | 4,096 | 4,672 |
| Multiplication | 64 | 512 | 4,096 | 4,672 |
| Squaring | 16 | 64 | 256 | 336 |
| Totalized inverse | 16 | 64 | 256 | 336 |
| **All operations** | **160** | **1,152** | **8,704** | **10,016** |

For every enumerated state, tests checked input preservation, output shape,
round-trip application, and uniqueness of the output mapping over the entire
state space.

The production-field checks use seven selected elements (`0`, `1`, `2`,
`0x53`, `0x123`, `0xABC`, `0xFFF`): 49 cases each for addition and
multiplication and 7 each for square and inverse. An independent reference
oracle also checks nonzero inverse identities and fixed vectors, including
`0x123 * 0x456 = 0x72E`, `0x123² = 0x135`, and
`inverse(0x123) = 0x94A`. Additional tests cover boundaries, rejected
invalid inputs, malformed call shapes, tuple immutability, and repeated
application.

### Actual validation

Focused command:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -p no:cacheprovider tests/dqi_decoder/test_reversible_primitives.py -q
```

Final result: **9 passed, 33 subtests passed in 0.12s**.

Pylance diagnostics on both new Python files: **no diagnostics**. Pylance
syntax checks on both files: **no syntax errors**. `git diff --check` passed
before adding this report; the report is checked again after creation.

These are locally authored research tests, not official DQI fixtures,
verifier tests, or benchmark validation.

## 10. Unsupported and unresolved semantics

- No quantum circuit or gate implementation exists in this phase.
- No circuit resource, ancilla, depth, gate-count, or cleanup claim is made.
- The official verifier, scorer, reference circuit, fixtures, and serialized
  register/bit ordering remain unavailable as recorded in P003/P004.
- Decoder-level promised-domain and off-promise behavior remains outside this
  phase.
- `inverse(0)=0` is a model extension, not a field inverse and not a
  verifier-established convention.
- Small-field exhaustive verification does not prove a 12-bit gate
  implementation; selected production-field checks are not exhaustive over
  `GF(2^12)`.

## 11. Official verifier compatibility status

**NOT ESTABLISHED.** The new functions are local classical models and are not
an official submission format. The official verifier was not run and no
compatibility claim is made.

## 12. Resource and performance limitations

The model relies on the existing Python `GF(2^12)` arithmetic and allocates
ordinary Python tuples. It has no quantum resource metrics, gate-level
complexity measurement, circuit depth, or ancilla usage. Test exhaustiveness
applies only to the 2-, 3-, and 4-bit fields; production-field tests are
selected deterministic cases.

## 13. Security and correctness considerations

Argument validation is explicit and uses the existing exact-integer and
range checks. No external input, dependency, file, network operation,
benchmark, or verifier is involved. The inverse-zero extension is documented
at the API and report levels to avoid confusing it with the mathematical
inverse. The independent small-field oracle reduces the risk of merely
retesting production arithmetic against itself, but does not constitute a
formal proof of a quantum implementation.

## 14. Files created and modified

Created in P009:

- `src/dqi_decoder/reversible_primitives.py`
- `tests/dqi_decoder/test_reversible_primitives.py`
- `docs/research/DQI_P009_REVERSIBLE_FINITE_FIELD_PRIMITIVES_REPORT.md`

No existing files were modified or deleted. P001–P008 reports, the existing
field implementation and tests, other DQI modules, and unrelated INVSQRT
work were preserved. No files were staged or committed.

SHA-256 preservation fingerprints recorded for prior reports and existing
field files:

| File | SHA-256 |
|---|---|
| `docs/research/DQI_P001_DEVELOPMENT_FOUNDATION.md` | `DC44F79BD38E7BD38566FC11E3234B0ECE5C8ADCA52B66ECE9823E13634EB0F8` |
| `docs/research/DQI_P002_TECHNICAL_CONTRACT.md` | `48E8772D49425CC50C0694FF7B133A7F58AF1F218452A2A6DDECE8BCB1EEC516` |
| `docs/research/DQI_P003_EVIDENCE_READINESS_REPORT.md` | `0F47D0F4C59CDD040A569E7FC55C7A4127E69147F7A530EF2A16741DC4415163` |
| `docs/research/DQI_P004_AUTHORIZED_VERIFIER_FIXTURE_INTAKE.md` | `5496F8817F6835D2EEAA28A6E9F08F84579588EEF1DDAAC8D2510F6F96131167` |
| `docs/research/DQI_P005_CORE_IMPLEMENTATION_REPORT.md` | `FA937C40436C41751962B86CBC60BDD99B12024240694648F707F5846A763D97` |
| `docs/research/DQI_P006_CLASSICAL_DECODER_IMPLEMENTATION_REPORT.md` | `9D179E6328FA889A83A76FAE7D21E8D051E0D96948A80297FD588939C5C42084` |
| `docs/research/DQI_P007_INDEPENDENT_CORRECTNESS_AUDIT.md` | `8E2FD36E3896A1F6482CB8A720EA76DF6460422C4238A44A8A09215787C8D6A7` |
| `docs/research/DQI_P008_REVERSIBLE_DECODER_SPECIFICATION.md` | `CF91478C935819939C86CC8FE4D23D2B7FA513F8A384A5EED927F321D228CB41` |
| `src/dqi_decoder/field.py` | `DE6653A968FDDBED701E04706CE61A92A97D7F3C8DAA502E40A3DB1922A7BB94` |
| `tests/dqi_decoder/test_field.py` | `CB11C79F0ACF6DF602AB51FA93C094376E4DE7776E93071C9AA287E971BCF5AF` |

These fingerprints identify the bytes observed at final verification; they
are not official artifact signatures.

## 15. Remaining development work

Any later phase that implements a circuit must separately establish the
gate-level arithmetic decomposition, reversible workspace lifecycle, and
cleanup proof. Verifier and fixture acquisition and authorization gaps
recorded in P003/P004 also remain. None of that work is part of P009.

## 16. Final implementation status

**P009 COMPLETE — RESEARCH MODEL ONLY.** The four field transformations,
validation, independent small-field exhaustive tests, selected production
field checks, and this report are complete. No quantum circuit, decoder
implementation, verifier compatibility, or benchmark result is claimed.
The task stops at P009.
