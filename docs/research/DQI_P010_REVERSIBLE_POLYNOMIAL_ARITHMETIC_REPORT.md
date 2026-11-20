# DQI-P010 — Reversible Polynomial Arithmetic Models

**Project:** Google Quantum AI — Verifiable Quantum Circuit Compilation
**Workstream:** DQI Decoder
**Phase:** 01 — P010
**Repository:** `D:\PROJECT\Quantum_AI\Google-Quantum-AI`
**Branch before and after:** `feat/dqi-decoder`
**HEAD before and after:** `5391b2e7123484efacffc0588f5e761e67b5cb55`
**Overall status:** **PASS — all P010 acceptance criteria met**

## 1. Executive summary

P010 adds classical input-preserving XOR-accumulation models for fixed-width
polynomial addition and multiplication over the existing `GF(2^12)` field.
The new module preserves both operand tuples, accumulates into an exactly
sized target tuple, validates registers and coefficients, and uses the P009
field primitives for each coefficient operation.

The tests exhaustively enumerate complete one-coefficient transformation
domains over independently implemented `GF(2^2)`, `GF(2^3)`, and `GF(2^4)`
models. They also cover all two-coefficient-by-one-coefficient operand
combinations in each small field for independent reference calculations,
and compare 11 deterministic production-field transformation vectors against
an independent polynomial arithmetic oracle.

These are classical register-permutation models only. They are **not** a
quantum circuit, gate decomposition, ancilla-cleanup proof, reversible
decoder, or official-verifier implementation.

## 2. Repository identity and baseline

| Item | Observed value |
|---|---|
| Repository root | `D:\PROJECT\Quantum_AI\Google-Quantum-AI` |
| Required and actual branch | `feat/dqi-decoder` |
| Expected, initial, and final HEAD | `5391b2e7123484efacffc0588f5e761e67b5cb55` |
| Initial staged paths | 0 |
| Initial tracked unstaged paths | 0 |
| Initial status paths | 52 untracked paths; preserved |
| Dependencies installed or changed | None |
| Branch, HEAD, or commit operations | None |

The initial untracked set included prior DQI reports and code/tests, as well
as INVSQRT bytecode caches and unrelated DQI work. They were preserved.
P010 adds only its new source module, focused test module, and this report;
no existing file was overwritten or deleted.

## 3. P008/P009 traceability

| Evidence | P010 use | Status |
|---|---|---|
| P008, §4 reversible arithmetic discussion | Supports retaining polynomial operands and XOR-accumulating into separate targets as a mathematical register-relation shape; explicitly not a gate implementation | **SPECIFIED** as a model shape; not an executable circuit contract |
| P009 report and `reversible_primitives.py` | Supplies validated field addition and multiplication target-XOR helpers used coefficient by coefficient | **IMPLEMENTED** and audited before P010 |
| `field.py` | Defines GF(2^12), exact integer/range validation, polynomial-basis encoding, addition, and multiplication | **SPECIFIED** by the existing local API and reused |
| `polynomial.py` | Establishes low-degree-first coefficient ordering and canonical classical polynomial operations | Existing convention inspected; variable-length canonical API remains unchanged |

### P009 audit gate

P009's actual source, report, and tests were inspected before implementation.
The following checks were reproduced:

- The four field operations retain their input elements and XOR-accumulate
  into the target; all validate field operands and targets.
- `target_width()` returns 12, and the production backend is the existing
  GF(2^12) representation.
- Inverse-at-zero is explicitly totalized to zero only in the reversible
  tuple model; the classical field inverse still rejects zero.
- The small-field oracle uses its own polynomial multiplication and
  inverse-by-enumeration rather than production field helpers for expected
  values.
- The exhaustive loops cover all input and target states claimed by P009.
- The report distinguishes small-field exhaustiveness from selected
  GF(2^12) tests and its stated count is reproducible.

Audit command and result:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -p no:cacheprovider tests/dqi_decoder/test_reversible_primitives.py -q
# 9 passed, 33 subtests passed
```

No P009 mismatch or critical defect was found. P009 files were not modified.

## 4. Existing polynomial representation

[`polynomial.py`](../../src/dqi_decoder/polynomial.py) uses low-degree-first
coefficient sequences. Its `normalize` function removes trailing
high-degree zero coefficients; the canonical classical zero polynomial is
the empty tuple. Its add and multiply functions return normalized,
variable-length values.

That canonical representation cannot itself retain a declared register
width. P010 therefore defines a separate, fixed-width representation that
reuses the established coefficient ordering and field encoding without
calling `normalize` or changing the classical API. In the new reversible
register API:

- a register is a **nonempty tuple** of exact GF(2^12) integers;
- index 0 is the constant coefficient and index `i` is coefficient of
  `x^i`;
- an all-zero tuple represents the zero polynomial at that declared width;
- an empty tuple is invalid and is not used as a fixed-width register; and
- each target must have the exact operation-specific width.

This distinction avoids silently trimming high-order zero coefficients or
confusing a canonical polynomial object with a fixed-width register.

## 5. Fixed-width polynomial register contract

Let `A=(a_0,...,a_(m-1))` and `B=(b_0,...,b_(n-1))` be nonempty,
low-degree-first tuples of GF(2^12) elements. Let `T` be a separate target
tuple. The input tuples and target are immutable Python tuples; invalid
container types, empty operand registers, wrong target widths, and invalid
field elements are rejected explicitly.

The finite register widths are set by the input tuple lengths. P010 defines
no decoder-specific maximum polynomial width because no such supported
capacity is established by P008/P009. Each call nevertheless has concrete,
finite widths and exact result capacity.

## 6. Reversible polynomial addition semantics

For addition, define `k=max(m,n)` and zero-extend the shorter coefficient
tuple through index `k-1`. The transformation is:

```text
(A, B, T) -> (A, B, T XOR (A + B))
T'_i = T_i XOR a_i XOR b_i,  0 <= i < k
```

The target width must be exactly `k`. Since field addition in characteristic
two is coefficient-wise XOR, this is implemented by P009's
`xor_accumulate_add`. Both inputs are returned unchanged; the output is not
trimmed. Unequal widths use explicit zero padding. All-zero operands are
valid zero polynomials.

## 7. Reversible polynomial multiplication semantics

For multiplication, the exact target capacity is `m+n-1`. The full
low-degree-first product is:

```text
p_k = XOR over i+j=k of GF_MUL(a_i, b_j)
T'_k = T_k XOR p_k,  0 <= k < m+n-1
(A, B, T) -> (A, B, T')
```

Each coefficient contribution is accumulated using P009's
`xor_accumulate_multiply`; characteristic-two field addition XORs all
contributions at the same coefficient index. No coefficient is truncated
and no normalization is performed. A fixed-width all-zero operand produces
an all-zero product at the exact declared product capacity. The target must
have exactly `m+n-1` coefficients.

## 8. Implementation and public API

Created [`reversible_polynomial.py`](../../src/dqi_decoder/reversible_polynomial.py)
with:

- `PolynomialRegister`
- `xor_accumulate_polynomial_add(left, right, target)`
- `xor_accumulate_polynomial_multiply(left, right, target)`

Both functions return `(left_register, right_register, updated_target)`.
They validate tuple shape, nonempty register widths, exact target width, and
every field element. They do not mutate inputs. Product convolution uses the
existing P009 target-XOR multiplication relation; addition uses the
corresponding P009 addition relation.

No existing classical polynomial function or decoder behavior was modified.

## 9. Independent oracle methodology

The new test module implements its own small-field arithmetic:

- GF elements are integer coefficient bitmasks in a polynomial basis.
- Field multiplication is shift/XOR multiplication followed by polynomial
  reduction, independent of production `field.multiply`.
- Polynomial addition zero-pads coefficients and XORs them.
- Polynomial multiplication performs direct coefficient convolution using
  the independent small-field multiplier.
- Proposed small-field moduli are checked for irreducibility by enumerating
  all monic possible divisors of degree at most half the field degree.

The small-field moduli are `0b111` for GF(2^2), `0b1011` for GF(2^3), and
`0b10011` for GF(2^4). In addition to complete one-coefficient transformation
enumeration, all `q^3` choices of a two-coefficient left polynomial and
one-coefficient right polynomial are checked per field for the independent
polynomial-addition and convolution formulas. That wider oracle check uses
the fixed target `(q-1, 0)`; it is **not** an exhaustive transformation-state
enumeration.

Production-field expected values use the same independently coded
shift/reduce field arithmetic with modulus `0x1053`, and direct polynomial
coefficient convolution. They do not use production polynomial operations
to calculate expected outputs.

## 10. Exhaustive small-domain test methodology

For complete transformation-domain enumeration, both operands and the
target are one-coefficient registers. For each operation and each field, the
test enumerates every `(a,b,t)` state and records the output tuple.

| Field | Modulus | Field size `q` | Operand combinations `q²` | Target states `q` | Complete states per operation `q³` |
|---|---:|---:|---:|---:|---:|
| GF(2^2) | `0b111` | 4 | 16 | 4 | 64 |
| GF(2^3) | `0b1011` | 8 | 64 | 8 | 512 |
| GF(2^4) | `0b10011` | 16 | 256 | 16 | 4,096 |
| **Total per operation** | — | — | **336** | **28** | **4,672** |

Addition and multiplication each cover **4,672 complete states**; combined,
they cover **9,344 complete transformation states**. For every state the
tests check unchanged operands, applying the transformation twice restores
the original state, and no two complete states map to the same output.
The independent two-by-one coefficient oracle adds 4,672 operand combinations
per operation across the three fields, with one stated target tuple per
combination; these are oracle formula checks, not complete-state bijection
counts.

The exhaustive tests cover only one-coefficient complete maps. Wider
polynomial-register transformations are not claimed to have been exhaustively
enumerated.

## 11. Production GF(2^12) test methodology

The tests exercise **11 deterministic input/target vectors** against
independently computed results: four addition cases and seven multiplication
cases. They include equal and unequal widths, zero polynomials, all-zero
coefficients, zero padding, constant one, low- and high-degree zero
coefficients, maximum field elements, and nonzero convolution at the final
product coefficient. Each vector checks preserved operands, accumulated
target values, exact output capacity, and round-trip application.

Independent fixed multiplication vectors include:

```text
(0x123, 0x456) * (0x789, 0xABC) = (0xAC1, 0xC31, 0x584)
(0x123, 0x456, 0x789) * (0xABC, 0x053)
    = (0x113, 0xD0E, 0xBBD, 0x5B0)
```

These are deterministic property checks, **not** exhaustive coverage of
polynomial registers over GF(2^12).

## 12. Involution and bijection arguments

For either operation, let `F(A,B)` be the fixed-width sum or product vector.
The implemented register relation is:

```text
G(A,B,T) = (A, B, T XOR F(A,B)).
```

The same input operands are retained, so a second application computes the
same `F(A,B)` and XORs it into the target again:

```text
G(G(A,B,T)) = (A, B, T XOR F(A,B) XOR F(A,B)) = (A, B, T).
```

Thus `G` is its own inverse and is a bijection on the complete fixed-width
register domain for the declared operation. This mathematical argument is
general for any deterministic `F`; executed small-domain tests corroborate
the one-coefficient cases. It does not prove a circuit decomposition or
physical implementation.

## 13. Boundary and invalid-input results

The tests verify rejection of:

- empty operand and target tuples;
- target tuples shorter or longer than the exact required capacity;
- non-tuple register containers;
- field elements below zero or at/above 4096; and
- booleans, floats, and strings as coefficients.

The tests also cover zero-polynomial tuples and maximum valid field
coefficients (`0xFFF`). The target is never silently resized or truncated.

## 14. Exact test commands and outputs

P009 prerequisite audit:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -p no:cacheprovider tests/dqi_decoder/test_reversible_primitives.py -q
# 9 passed, 33 subtests passed
```

P010 focused tests:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -p no:cacheprovider tests/dqi_decoder/test_reversible_polynomial.py -q
# 6 passed, 28 subtests passed in 0.16s
```

Combined prerequisite and P010 run:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -p no:cacheprovider tests/dqi_decoder/test_reversible_primitives.py tests/dqi_decoder/test_reversible_polynomial.py -q
# 15 passed, 61 subtests passed in 0.29s
```

Pylance syntax checks found no syntax errors, and Pylance diagnostics
reported no issues in either new Python file.

These are research tests authored in this repository. No official fixtures,
verifier, DQI decoder, benchmark, or competition workload was executed.

## 15. Files created, modified, and preserved

Created:

- `src/dqi_decoder/reversible_polynomial.py`
- `tests/dqi_decoder/test_reversible_polynomial.py`
- `docs/research/DQI_P010_REVERSIBLE_POLYNOMIAL_ARITHMETIC_REPORT.md`

Modified or deleted: **none**. P001–P009 reports and all existing DQI source
and tests were preserved. The existing classical polynomial module and its
tests were not modified. Existing unrelated untracked work was preserved.

SHA-256 fingerprints of prior reports and relevant pre-existing code were
recorded before and after P010 changes; final values are listed below:

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
| `docs/research/DQI_P009_REVERSIBLE_FINITE_FIELD_PRIMITIVES_REPORT.md` | `7F9B4EDA59A9E5459AA21455FC29C52CC10DB7DF486407E0AE29F1528F090238` |
| `src/dqi_decoder/reversible_primitives.py` | `F4B9FF249BE9FA641468533C4136CC1949D1C3FCFEA0132CB5E5078AF7F4B779` |
| `tests/dqi_decoder/test_reversible_primitives.py` | `813F9D4C118320CDE6E659A22FE71B68ABB7E1AB1FD9B514C2244E5ED8C9D717` |
| `src/dqi_decoder/polynomial.py` | `8BC2DDD8804DD102585D81DD622EC76B0A736741F24D3AACEBB0B4D196F1DACF` |
| `tests/dqi_decoder/test_polynomial.py` | `FFD6AF2F321C81F4499BF65AA7BDA3FA364BCB5287F5361762AEC24ABBDFA693` |

These hashes are preservation fingerprints, not official signatures.

## 16. Dependency changes

No dependency was added, installed, removed, or changed. The implementation
uses only the existing DQI package and Python standard library.

## 17. Limitations and unresolved questions

- The register widths are supplied by the caller; no DQI-specific maximum
  polynomial width is asserted.
- Empty tuples cannot encode a fixed-width register. Zero is represented by
  one or more all-zero coefficients.
- Small-domain complete transformation enumeration uses one coefficient
  per operand. Wider small-field oracle combinations are checked separately
  and are not complete transformation-state enumerations.
- GF(2^12) testing uses 11 deterministic vectors, not exhaustive registers.
- P008/P009 do not establish an official polynomial wire serialization,
  verifier schema, or complete decoder circuit contract.
- No polynomial evaluation, division, EEA, decoder, quantum circuit, gate
  decomposition, ancilla estimate, resource metric, or official verifier
  compatibility is implemented.

## 18. Readiness for reversible polynomial evaluation

The arithmetic relations now provide a testable classical model that a later
evaluation design may use as a mathematical component. Reversible polynomial
evaluation is **NOT IMPLEMENTED** and is **NOT GATE-LEVEL VERIFIED**.
Proceeding to it would require a separately scoped phase defining the
evaluation input/point representation, register capacities, workspace,
uncomputation, complete domain behavior, and relevant authorization. No
evaluation algorithm or circuit is implied by P010.

## 19. Evidence labels and acceptance checklist

| Claim | Evidence label |
|---|---|
| Fixed-width coefficient tuple and target-width rules | **SPECIFIED** |
| Polynomial addition and multiplication functions | **IMPLEMENTED** |
| Complete one-coefficient maps for GF(2²), GF(2³), GF(2⁴) | **EXHAUSTIVELY TESTED ON DECLARED SMALL DOMAIN** |
| Selected production-field transformation vectors | **PROPERTY-TESTED ON GF(2^12)** |
| Input-preserving XOR relation is an involutive bijection | **MATHEMATICALLY JUSTIFIED** |
| Gate decomposition and physical circuit semantics | **NOT GATE-LEVEL VERIFIED** |
| Official fixtures, verifier, or competition behavior | **NOT OFFICIAL-VERIFIER VERIFIED** |

- [x] Correct repository, branch, and HEAD recorded and unchanged.
- [x] P009 implementation, tests, and report audited and preserved.
- [x] Fixed-width register and target contracts documented.
- [x] Addition and multiplication preserve operands and use exact output widths.
- [x] Independent small-field oracle and exhaustive bounded state tests added.
- [x] Production GF(2^12) deterministic checks added.
- [x] Focused tests and static checks pass.
- [x] P001–P009 and existing classical polynomial files preserved.
- [x] No dependencies, official verifier, or benchmark used.
- [x] No unrelated work modified or deleted.

## 20. Final disposition

**PASS — all P010 acceptance criteria met.** P010 implements and validates
input-preserving classical polynomial addition and multiplication models,
with independently checked bounded test domains and explicit limits on the
evidence. It does not establish gate-level or official-verifier correctness.
The work stops at P010; no P011 work is started.
