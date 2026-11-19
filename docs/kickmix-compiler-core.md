# Local KMX Compiler Core

- **Status:** **VERIFIED LOCALLY** parser/serializer/CLI behavior;
  compatibility with pinned upstream execution and the competition's Kickmix
  build is **BLOCKED**.
- **Scope:** textual `.kmx` input, validation, one deterministic rewrite pass,
  resource summary, KMX output, and a local CLI.
- **Evidence:** the KMX v2 syntax and instruction set are documented at pinned
  upstream Qualtran commit
  [`f559b12af459e7e97e6c6c382434431c03b903c9`](https://github.com/quantumlib/Qualtran/tree/f559b12af459e7e97e6c6c382434431c03b903c9).
  The competition metric source retrieved in
  [Phase 7B](phase-7b-authoritative-evidence-report.md) allows `.kmx` and
  `.kmb`, but does not identify its exact Kickmix revision.

Evidence labels follow the audit taxonomy: **VERIFIED LOCALLY** describes
executed local source/tests; **VERIFIED UPSTREAM** describes source or docs at
the pinned Qualtran revision; **VERIFIED OFFICIAL** is limited to the visible
metric source; **PAPER-DERIVED**, **ENGINEERING PROPOSAL**, **BLOCKED**, and
**UNKNOWN** retain their distinct meanings.

The upstream comparison uses the immutable
[KMX format](https://github.com/quantumlib/Qualtran/blob/f559b12af459e7e97e6c6c382434431c03b903c9/docs/kickmix/kickmix_format.md),
[instruction reference](https://github.com/quantumlib/Qualtran/blob/f559b12af459e7e97e6c6c382434431c03b903c9/docs/kickmix/kickmix_instructions.md),
[mutable KMX parser](https://github.com/quantumlib/Qualtran/blob/f559b12af459e7e97e6c6c382434431c03b903c9/kickmix/src/kickmix/circuit/mutable_circuit.cc),
[circuit validation and writer](https://github.com/quantumlib/Qualtran/blob/f559b12af459e7e97e6c6c382434431c03b903c9/kickmix/src/kickmix/circuit/circuit.cc),
[ID limits](https://github.com/quantumlib/Qualtran/blob/f559b12af459e7e97e6c6c382434431c03b903c9/kickmix/src/kickmix/id/id_tagging.h),
and [fixed-precision angle API](https://github.com/quantumlib/Qualtran/blob/f559b12af459e7e97e6c6c382434431c03b903c9/kickmix/src/kickmix/util/fixed_precision_angle_128.h).
These paths are **VERIFIED UPSTREAM** references, not local files.

## Implementation

`tools/kickmix_compiler.py` contains immutable `Wire`, `Instruction`, and
`Circuit` values, a KMX v2 parser, a deterministic text serializer, resource
summaries, compilation provenance hashes, and the CLI entry point. It handles
all instruction names in the metric's visible whitelist: `X`, `CX`, `CCX`,
`Z`, `CZ`, `CCZ`, `Z_POW`, `NEG`, `SWAP`, `CSWAP`, `R`, `HMR`, `BIT_INVERT`,
`BIT_STORE0`, `BIT_STORE1`, `PUSH_CONDITION`, `POP_CONDITION`, `INFO_TAG`, and
`DEBUG_PRINT`. It also handles the KMX metadata instructions `REGISTER` and
`APPEND_TO_REGISTER`.

The parser preserves the decimal text of `Z_POW` exponents; it does not
interpret or round them into Kickmix's 2^-128 fixed-precision half-turn
representation (**VERIFIED UPSTREAM** behavior; local numeric interpretation
is **BLOCKED**). It validates opcode/operand kinds, instruction arity,
condition bits, quoted-text escapes, and UTF-8/ASCII constraints
(**VERIFIED LOCALLY**). It accepts unnamed and sparse registers, preserves
repeated declarations of the same ID (whose final name overwrites earlier
names), and rejects duplicate non-empty names on different IDs. These register
rules match the pinned source inspection (**VERIFIED UPSTREAM**); exact
differential execution remains **BLOCKED**.
Non-string parser/compiler inputs raise `TypeError`; malformed KMX syntax and
semantic validation failures are reported as `KmxSyntaxError` by the parser
(a `ValueError` subclass) (**VERIFIED LOCALLY**).

The pinned upstream parser rejects IDs greater than or equal to 500,000,000
for qubits/bits and 1,000,000 for registers (**VERIFIED UPSTREAM**). The local
parser accepts qubit/bit IDs below the pinned upstream bound; the compiler
entry point additionally enforces the visible metric's stricter ID bound of
`2**30 // 1536` (**VERIFIED OFFICIAL** source; local enforcement **VERIFIED
LOCALLY**). The metric also requires each register to have a string name;
`compile_kmx` enforces that requirement, while generic `parse_kmx` accepts
upstream-valid unnamed/sparse registers. The local register span cap is
10,000, stricter than the pinned upstream cap (**ENGINEERING PROPOSAL**), and
input is capped at 16 MiB (**VERIFIED LOCALLY**). The competition's
per-benchmark register-count limits are not implemented because no benchmark
is selected by this CLI (**BLOCKED**).

The parser does not accept KMB, arbitrary binary payloads, or instructions
outside the local supported set. It does not impose benchmark-specific
register layouts, per-benchmark register caps, ancilla-cleanliness
requirements, or semantic verifier checks.

### Upstream behavior comparison

The following source-backed distinctions are important:

| Topic | Pinned upstream evidence | Local behavior / status |
|---|---|---|
| Sparse register IDs | `REGISTER` and `APPEND_TO_REGISTER` grow `register_data` through the referenced ID, creating intermediate unnamed entries. | Accepted by `parse_kmx` within the local 10,000-ID span cap; **VERIFIED LOCALLY**. `compile_kmx` rejects any unnamed register for the visible metric; **VERIFIED OFFICIAL** requirement, locally enforced. |
| Unnamed register names | `REGISTER` has an optional name; empty names are valid. | Accepted by `parse_kmx`; `compile_kmx` rejects an omitted name per the visible metric requirement. An explicit empty string is still a string. |
| Duplicate declarations | A later `REGISTER rN "name"` overwrites that register's current name; contents remain. | Declaration sequence is preserved; resource summary uses the ID span; **VERIFIED LOCALLY**, but not differentially executed. |
| Duplicate register names | Final validation rejects duplicate non-empty names on distinct registers. | Rejected after collecting final names; **VERIFIED LOCALLY**. |
| Repeated qubit operands | `Circuit::validate_and_compute_stats` rejects two- and three-qubit operations that use the same qubit in multiple operand positions. | `Circuit` validation rejects repeated operands; **VERIFIED LOCALLY**. |
| Wire-ID limits | KMX format prose says no format-level maximum; pinned parser implementation enforces IDs below 500,000,000 for qubits/bits and below 1,000,000 for registers. | `parse_kmx` follows the pinned qubit/bit bound but has a stricter 10,000-register local cap. `compile_kmx` applies the official metric's smaller qubit/bit bound. Per-benchmark register caps are **BLOCKED**. |
| Resource counts | `Circuit::compute_num_qubits` and `compute_num_bits` return largest referenced ID plus one, including IDs in register contents; this is an ID span, not a count of distinct allocated wires. | `qubit_count` and `bit_count` use largest locally referenced ID plus one. `register_count` is the maximum register ID plus one, including sparse holes; **VERIFIED LOCALLY**. |
| Conditions | `PUSH_CONDITION` snapshots the current bit value; ordinary operations require the stack and explicit condition to be true. `POP_CONDITION` on an empty stack is a no-op. Register metadata and `INFO_TAG` ignore the stack. | The parser preserves explicit push/pop instructions; the test-only subset interpreter models stack snapshots. No full simulator is implemented. |
| `DEBUG_PRINT rN` | The parser expands the register's contents as they exist at that point in the source. | The local syntax tree retains the register operand and serializes it as text; serialized source order preserves reparsing behavior, but the internal representation is not upstream's normalized circuit. |
| `Z_POW` | Decimal text specifies half-turns; the pinned implementation rounds to 2^-128 fixed precision, with the instruction docs requiring at most 2^-128-turn perturbation. | Lexical validation and text preservation only; numerical equivalence is **BLOCKED**. |
| Serialization | `Circuit::write_kmx_to` serializes final register contents/names before operations and writes the fixed-precision normalized angle. | Local serializer preserves instruction order and original `Z_POW` decimal text while removing comments/formatting. Local parse/serialize round-trip is not byte- or representation-equivalence with upstream; **VERIFIED LOCALLY**, upstream differential **BLOCKED**. |
| Comments and escapes | UTF-8 file; non-ASCII is allowed only in comments. `#`, quote, backslash, LF, and CR use `\\P`, `\\Q`, `\\B`, `\\n`, and `\\r`. | Supported by local parser/serializer tests; **VERIFIED LOCALLY**. |

### Supported opcode operand inventory

The following arities and kinds are **VERIFIED UPSTREAM** against the pinned
instruction reference and are enforced by the local parser (**VERIFIED
LOCALLY**). An optional `if bN` condition is supported for quantum operations,
classical operations, and `DEBUG_PRINT`; it is not supported by the control
flow or metadata declarations.

| Opcode(s) | Required operands | Upstream role |
|---|---|---|
| `X`, `Z`, `R` | one qubit | Bit flip, phase flip, reset |
| `CX`, `CZ`, `SWAP` | two distinct qubits | Controlled bit flip, controlled phase flip, exchange |
| `CCX`, `CCZ`, `CSWAP` | three distinct qubits | Doubly-controlled bit flip, phase flip, or swap |
| `Z_POW` | one qubit and one decimal half-turn exponent | Fine-grained phase |
| `NEG` | none | Tracked global phase negation |
| `HMR` | one qubit and one output bit | X-basis measurement and reset |
| `BIT_INVERT`, `BIT_STORE0`, `BIT_STORE1` | one bit | Classical invert, clear, or set |
| `PUSH_CONDITION` | `if bN` | Snapshot and push a condition value |
| `POP_CONDITION` | none | Pop; empty stack is a no-op |
| `INFO_TAG` | one quoted text value | Debug metadata |
| `REGISTER` | one register and optional quoted name | Declare register; omitted name is allowed by KMX |
| `APPEND_TO_REGISTER` | one qubit/bit and one register | Append a member in significance order |
| `DEBUG_PRINT` | zero or more qubit/bit/register IDs | Debug request; register operands expand against current register contents upstream |

## CLI and artifacts

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.kickmix_compiler input.kmx output.kmx
```

The CLI rejects symlink/non-regular inputs, refuses to overwrite an existing
output, does not create missing parent directories, and prints one compact
JSON record with source/output SHA-256, local compiler version, before/after
instruction/resource counts, and the number of canceled pairs. Resource
summaries are structural counts; they are not the verifier's cost or the
official score. The output is KMX v2 text, not KMB.

The pinned C++ source and documentation were inspected at the immutable
revision, but the upstream parser was not built or executed. `kickmix`,
`qualtran`, `pytest`, and Bazel are unavailable in the checked environment;
dependencies were not installed. Upstream differential execution is therefore
**BLOCKED**. The competition's exact parser/build and canonical-byte rules
remain **UNKNOWN**; this CLI does not establish competition compatibility or
benchmark compilation.

## Tests

`tests/test_kickmix_compiler.py` covers the locally supported instruction families,
quoted escapes, comments and line endings, invalid IDs/syntax, named register
name uniqueness, sparse/unnamed registers, deterministic
output/provenance, CLI output protection, and exhaustive small-state
equivalence for a restricted reversible/phase subset, including condition
stack snapshots. A subprocess test also exercises the `python -m` entry point
so the runtime circuit type stays canonical. These tests are **VERIFIED
LOCALLY** evidence only, not a general quantum-equivalence proof.
