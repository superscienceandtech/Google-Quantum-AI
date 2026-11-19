# Compiler Infrastructure Architecture Boundaries

- **Status:** evidence map and boundary proposal; not an approved architecture.
- **Updated:** 2026-11-19
- **Repository snapshot:** `feat/compiler-infrastructure` at
  `6c63c152972bd2e920ed72514dbb9bb7e4e1d6dd`
- **Upstream reference:** `quantumlib/Qualtran` at
  `f559b12af459e7e97e6c6c382434431c03b903c9`

## Evidence classifications

- **VERIFIED LOCALLY:** observed in local source or test execution.
- **VERIFIED UPSTREAM:** observed in the pinned Qualtran/Kickmix source or
  documentation; this does not establish project adoption.
- **VERIFIED OFFICIAL:** observed in the official metric source only.
- **PAPER-DERIVED:** described by the competition paper, not executable
  verifier behavior.
- **ENGINEERING PROPOSAL:** local interface or candidate boundary requiring
  project-owner approval.
- **BLOCKED:** requires an authoritative source or artifact not in this
  checkout.
- **UNKNOWN:** available evidence does not settle the point.

## Current project boundary

**VERIFIED LOCALLY:** The committed project tree has `README.md`,
`tools/verify_sha256.py`, and `tests/test_verify_sha256.py`. The checker
validates a caller-supplied digest, opens and validates a descriptor,
rejects non-regular files, rejects supported symlinks through `O_NOFOLLOW`,
and hashes bytes with SHA-256 in 1 MiB chunks. It does not construct circuits, read benchmark input, serialize
circuits, or call a verifier.

**ENGINEERING PROPOSAL:** The current worktree's `tools/compiler_infrastructure.py` adds
compiler-neutral request/result contracts, injected executor and verifier
protocols, a configured subprocess executor using a local JSON protocol,
root-relative artifact management, and deterministic run manifests.
These are executable infrastructure proposals; they do not define a compiler
IR, circuit format, benchmark adapter, or official verifier API.

**BLOCKED:** No project compiler pipeline, module boundary, IR, circuit
construction API, register/wire model, benchmark adapter, serialization
contract, verifier API, scorer API, or project error taxonomy is declared in
the committed tree. The absence in this checkout does not prove that no
separately distributed or private owner specification exists.

No modules or interfaces below are designated as official project
architecture.

## Verified external reference boundary

The existing [Kickmix interface and benchmark dossier](kickmix-interface-benchmark-contract-dossier.md)
records a source and documentation review pinned to Qualtran commit
`f559b12af459e7e97e6c6c382434431c03b903c9`. The following are upstream APIs,
not APIs declared or adopted by this project:

| Upstream function | Evidence-backed role | Project status |
|---|---|---|
| `km.Circuit` / `Circuit.from_file` / `Circuit.to_file` | Circuit parsing and KMX/KMB file serialization. | Upstream API documented and source-inspected; competition format use must be confirmed for each task. |
| `km.CircuitBuilder` | Register/allocation and circuit construction methods. | Upstream API documented; no project wrapper or chosen builder boundary. |
| Circuit register/count/diagram properties | Circuit inspection, including register data and qubit/bit/register counts. | Upstream API documented; no project inspection interface. |
| `km.Simulator` | Restricted basis-trajectory simulation, tracked phase and state access; supports explicit seed. | Upstream API documented/source-inspected; not a general state-vector simulator or official verifier. |
| `km.OperationStatistics` | Static operation counts; simulator can report shot-dependent counts when enabled. | Upstream API documented/source-inspected; not by itself the competition score. |
| KMX/KMB readers/writers | KMX text and KMB v2 binary format at the pinned upstream revision. | Upstream format; verifier canonicalization/hash rules and cross-benchmark submission requirements remain unconfirmed. |

The source paths below are in the pinned upstream repository, not local
`docs/kickmix/` files:
[KMX format](https://github.com/quantumlib/Qualtran/blob/f559b12af459e7e97e6c6c382434431c03b903c9/docs/kickmix/kickmix_format.md),
[KMX instructions](https://github.com/quantumlib/Qualtran/blob/f559b12af459e7e97e6c6c382434431c03b903c9/docs/kickmix/kickmix_instructions.md),
[KMB format](https://github.com/quantumlib/Qualtran/blob/f559b12af459e7e97e6c6c382434431c03b903c9/docs/kickmix/kickmix_binary_format.md),
[Python circuit bindings](https://github.com/quantumlib/Qualtran/tree/f559b12af459e7e97e6c6c382434431c03b903c9/kickmix/src/kickmix/py/circuit/),
and [C++ circuit source](https://github.com/quantumlib/Qualtran/tree/f559b12af459e7e97e6c6c382434431c03b903c9/kickmix/src/kickmix/circuit/).
Build evidence is likewise upstream-only: the pinned
[`.bazelversion`](https://github.com/quantumlib/Qualtran/blob/f559b12af459e7e97e6c6c382434431c03b903c9/.bazelversion),
[`MODULE.bazel`](https://github.com/quantumlib/Qualtran/blob/f559b12af459e7e97e6c6c382434431c03b903c9/MODULE.bazel),
[`WORKSPACE`](https://github.com/quantumlib/Qualtran/blob/f559b12af459e7e97e6c6c382434431c03b903c9/WORKSPACE),
and [`kickmix/BUILD`](https://github.com/quantumlib/Qualtran/blob/f559b12af459e7e97e6c6c382434431c03b903c9/kickmix/BUILD).

## Candidate integration boundaries (ENGINEERING PROPOSAL only)

The conceptual flow below is only a way to organize future compiler decisions.
The implemented Python protocols are local infrastructure seams, not approved
compiler or competition interfaces.

| Conceptual boundary | Responsibility to settle | Current status |
|---|---|---|
| Benchmark input | Versioned schema, validation rules, ownership, and conversion to mathematical inputs. | **BLOCKED** for official DQI/DFTHC schemas and complete verifier-owned INVSQRT inputs. |
| Circuit construction | Approved circuit API/IR, operation coverage, register naming, allocation and cleanup invariants. | **BLOCKED** on architecture and benchmark register/wire contracts. |
| Serialization | Accepted format/version, canonical bytes, path/stream behavior, and error handling. | Upstream KMX/KMB is known; competition canonical format and hash rules are **BLOCKED** except paper-described INVSQRT `.kmb` submission. |
| Inspection/statistics | Which circuit properties and operation-cost definitions are required. | Upstream inspection/count APIs exist; project scoring mapping is **BLOCKED**. |
| Simulation | Supported circuit subset, deterministic seed source, sampling protocol and phase interpretation. | Upstream simulator is known; official verifier/salt behavior is **BLOCKED**. |
| Verification/scoring | External invocation, outputs, failure semantics, scoring ownership and artifact versions. | **BLOCKED** pending official verifier/scorer release. |

## Benchmark-specific boundary constraints

These are **PAPER-DERIVED** constraints summarized from arXiv
`2610.23832v2`, as recorded in the dossier. They are not a complete adapter
specification.

| Track | Paper-derived information | Blocked information |
|---|---|---|
| INVSQRT | Inverse-square-root phase target, `"x"` register, preservation/cleanup, phase tolerance, sampling and cost model; paper identifies a Qualtran baseline. | Official verifier package/salt, canonical serialization contract, immutable competition fixture, and exact invocation. |
| DQI | Reed–Solomon syndrome/phase semantics, finite-field basis, principal dimensions, sampling and scoring description. | Register names, full bit/wire order, serialized input contract, authoritative executable/reference fixture, and verifier invocation. |
| DFTHC-SOS | Angle-oracle and address semantics, paper-described named registers, tree ordering, cleanup/sampling and cost description. | Data container/schema, tensor axes/dtypes, full address/reference artifacts, submission contract, and verifier invocation. |

Do not infer missing contracts from participant-maintained repositories or
from the fact that an upstream Kickmix API can represent an operation.

## Future adapter contract readiness (ENGINEERING PROPOSAL)

The local `CompilerExecutor` and `CompilerVerifier` protocols are generic
execution seams; the verifier remains in-process, and the subprocess protocol
is a local engineering contract, not a competition API. They are not benchmark
adapters. Any future adapter needs
an authoritative source for each of the following before implementation:

1. Input schema, ownership, validation, and version.
2. Compiler invocation and supported operation contract.
3. Output artifact format, location, and lifecycle.
4. Artifact digest/integrity rules.
5. Verification interface and exact status mapping.
6. Failure and partial-output semantics.
7. Deterministic execution metadata and seed rules.
8. Resource-accounting definitions and units.
9. Compiler, verifier, and source-data version/provenance.

These are readiness gates, not proposed official field names or requirements.

| Integration | Readiness | Evidence and blocker |
|---|---|---|
| INVSQRT | **BLOCKED** | Paper-derived circuit/phase constraints are **PAPER-DERIVED**. Official input fixture, canonical serialization/hash rules, verifier package and invocation remain unavailable. |
| DQI | **BLOCKED** | Mathematical semantics are **PAPER-DERIVED**. Authoritative input schema, register/bit ordering, fixtures and verifier invocation remain unavailable. |
| DFTHC-SOS | **BLOCKED** | Oracle/address semantics are **PAPER-DERIVED**. Data schema, tensor layout, reference artifacts and verifier invocation remain unavailable. |
| Kickmix | **VERIFIED UPSTREAM** | Pinned APIs and formats are source-backed; project adoption, benchmark conversion rules and competition verification remain **UNKNOWN** or **BLOCKED**. |
| Official verifier/scorer | **BLOCKED** | No authoritative implementation, interface, immutable release or fixtures are present in this checkout. |

## Required owner decisions and consequences

| Required source / owner | Missing decision or artifact | Work blocked |
|---|---|---|
| Project architecture owner | Approved module boundaries, pipeline, IR choice, register/wire semantics, error policy, determinism and build/test entry points. | Project API, IR, build orchestration, error conventions and integration layout. |
| Competition/verifier owner | Immutable verifier/scorer release, invocation, submission schemas, canonical serialization/seed rules, and official fixtures. | Adapter acceptance, end-to-end verification, resource-score reproduction and submission validation. |
| DQI benchmark owner | Wire/register encoding, serialized inputs, reference decoder/artifacts and fixtures. | DQI parser/adapter and independent DQI integration tests. |
| DFTHC-SOS data/benchmark owner | Data container, keys, shapes, dtypes, tensor axes, address map, reference tree/oracle artifacts and fixtures. | DFTHC loader, oracle adapter and forward/reverse integration tests. |
| INVSQRT benchmark/verifier owner | Competition reference artifact, verifier invocation, salt and exact canonical KMB/hash contract. | Reproduction of salted verification and competition-compatible submission checks. |

## Safe work currently supported

- Maintain and test the standalone digest checker without claiming
  provenance/authenticity from a digest alone.
- Record environment and dependency evidence without installing tools or
  declaring upstream requirements to be project requirements.
- Prepare tests against official fixtures once authorized inputs and
  verifier APIs are supplied.

Further compiler or benchmark code is **BLOCKED** until the required contracts
arrive. The next implementation milestone is a reproducible baseline for the
approved project entry point, not a speculative IR or adapter.

## Local KMX compiler update — 2026-11-19

The worktree now contains a scoped local KMX v2 compiler core in
`tools/kickmix_compiler.py` and the adjacent-involution optimizer in
`tools/participant_optimizer.py`. This changes the earlier statement that no
local circuit parser/compiler exists: the implementation parses, validates,
optimizes, and serializes KMX text. It does **not** make the local interface an
approved project or competition API.

The CLI and test evidence are documented in the
[KMX compiler core](kickmix-compiler-core.md) and
[completion matrix](implementation-completion-matrix.md). The competition's
exact Kickmix build, benchmark adapters, official verifier, and benchmark
acceptance remain blocked. No architecture decision is inferred from this
local implementation.
