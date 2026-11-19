# Phase 4 Implementation Readiness

- **Updated:** 2026-11-19
- **Decision:** **NO BENCHMARK IMPLEMENTATION READY**. The safe outcome for
  this phase is to preserve compiler-neutral code and document authoritative
  blockers.

## Evidence labels

This report uses **VERIFIED OFFICIAL**, **VERIFIED UPSTREAM**,
**PAPER-DERIVED**, **PARTICIPANT-MIRROR**, **LOCAL OBSERVATION**,
**ENGINEERING PROPOSAL**, **UNVERIFIED ASSUMPTION**, and **BLOCKED** exactly
within their evidence limits. See
[compiler-authoritative-architecture.md](compiler-authoritative-architecture.md)
for the source register.

## Integration readiness

| Integration | Readiness | Verified evidence | Unresolved gate |
|---|---|---|---|
| INVSQRT | **PARTIAL / implementation BLOCKED** | Paper-derived domain, `"x"` register, phase tolerance, cleanup, sampling, KMB submission mention, and resource formula. | Official input fixture, wire mapping, canonical KMB/hash/salt rules, verifier/scorer release and invocation. |
| DQI | **PARTIAL / implementation BLOCKED** | Paper-derived finite field, basis, syndrome and phase equations, widths, cleanup, sampling, and score formula. | Official input/error serialization, register names/order, fixtures, verifier and scorer. |
| DFTHC-SOS | **PARTIAL / implementation BLOCKED** | Paper-derived oracle/address/register constraints, reversibility, sampling and cost model. | Official dataset schema/container, tensor axes/dtypes, address map, reference tree/artifacts, verifier/scorer. |
| Kickmix | **PARTIAL / project adoption BLOCKED** | Upstream API and formats pinned to Qualtran commit `f559b12af459e7e97e6c6c382434431c03b903c9`. | Project owner approval, dependency/toolchain decision, adapter semantics, and official acceptance contract. |
| Official verifier/scorer | **BLOCKED** | Kaggle page metadata and paper methodology only. | Immutable official package/API, dependencies, fixtures, invocation, exit/failure/resource semantics. |

## Infrastructure gap analysis

| Existing infrastructure | Reusable capability | Required evidence before adapting |
|---|---|---|
| `CompilationRequest` | Versioned generic request, input refs, immutable JSON options, seed | Benchmark-specific schemas and input validation; do not guess fields. |
| `ArtifactReference` / `ArtifactStore` | Root-relative paths, SHA-256 integrity, safe access | Official formats, canonicalization, provenance/authenticity and data schema. Hash integrity alone is not authenticity. |
| `CompilationResult` | Success/failure, output refs, diagnostics | Official output shape, serialization and partial-output rules. |
| `VerificationResult` | Passed/failed/unavailable/not-executed/error states | Official invocation and exact result/exit-code mapping. |
| `ExecutionReport` / manifest | Structured status, component labels, digest and basic runtime metadata | Required compiler/verifier versions, flags, seeds, resource metrics, timeout semantics. |
| `CompilerExecutor` | Synchronous in-process extension protocol | Actual compiler executable/API and resource/process controls. |
| `CompilerVerifier` | In-process verification seam | Official verifier package/API and trust boundary. |

No concrete authoritative mismatch supports changing these interfaces now.
Keep benchmark-specific validation in adapters when real schemas are supplied.
Do not add success fallbacks, fake compiler/verifier implementations, or
benchmark fields based only on paper semantics.

## Proposed adapter lifecycle (ENGINEERING PROPOSAL)

For each benchmark, after authoritative contracts arrive:

1. Pin compiler/verifier releases and fixture hashes.
2. Parse and validate benchmark inputs against their exact schema/version.
3. Invoke the approved compiler through a benchmark adapter and capture
   process status, timeouts, diagnostics, and partial artifacts.
4. Validate output format and integrity independently of semantic
   verification.
5. Invoke the unchanged official verifier/scorer; map its result explicitly.
6. Compute resource metrics only using official formulas and required inputs.
7. Record source versions, compiler/verifier versions, seed, artifact digests,
   toolchain, and resource values only where their semantics are defined.
8. Return success only when compilation, artifact validation, and official
   verification all succeed.

### Benchmark-specific proposal gates

- **INVSQRT:** validate the official input representation, then enforce
  confirmed phase/register/cleanup requirements; produce only the official
  serialization and reproduce canonical bytes/salt handling from verified
  test vectors.
- **DQI:** implement the official finite-field and syndrome mapping only
  after wire ordering and record/error encoding are supplied; check syndrome
  preservation, cleanup, and phase using the official verifier.
- **DFTHC-SOS:** load only the official dataset schema; validate its tensor
  axes and address/reference artifacts before implementing forward/reverse
  oracle behavior.

These are integration gates, not official APIs or field names.

## Exact external blockers and owners

1. **Project architecture owner:** approved module boundaries, compiler
   entry point, IR/circuit representation, supported toolchain, build/test
   workflow, and dependency policy.
2. **Competition/verifier owner:** immutable verifier/scorer release and
   digest, dependencies, invocation/API, input/output schemas, exit/failure
   and timeout behavior, resource accounting, and canonical
   serialization/seed test vectors.
3. **Benchmark owners:** authorized input artifacts, schemas, fixtures, and
   expected verifier outcomes for each benchmark.
4. **INVSQRT owner:** official wire mapping, KMB canonicalization/hash/salt
   contract and verifier-compatible fixtures.
5. **DQI owner:** register/wire order, serialized syndrome and
   error/record encodings, fixtures, and reference decoder/verifier.
6. **DFTHC-SOS data/benchmark owner:** dataset container, keys, shapes,
   dtypes, axes, address map, reference tree/oracle artifacts and fixtures.
7. **Project owner:** explicit approval or rejection of Kickmix as a project
   dependency and the selected immutable version.

## Phase 5 execution sequence

1. Obtain and pin the architecture, compiler entry point, and official
   verifier/artifact bundle.
2. Reproduce the actual project build/test baseline in the approved
   environment.
3. Validate each official schema and fixture independently before writing
   adapters.
4. Implement one smallest benchmark adapter against official fixtures; keep
   verifier/scorer logic unchanged.
5. Add integration, determinism, resource-accounting, and failure tests
   grounded in authoritative outputs.
6. Expand to other benchmarks only after their owner-provided contracts pass
   the same review.

## Validation and status

The existing suite is infrastructure-only and uses explicit test doubles:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Observed 2026-11-19: exit 0, 52 tests passed. No compiler, benchmark, or
official verifier test ran. The full validation and protected Git baseline
are recorded in the Phase 4 execution report.
