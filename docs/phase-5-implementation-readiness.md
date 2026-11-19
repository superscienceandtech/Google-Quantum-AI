# Phase 5: Implementation Readiness and External Blockers

**Review date:** 2026-11-19

## Decision

**VERIFIED LOCAL FACT:** The compiler-neutral local infrastructure can be
tested and hardened independently. The 53-test local suite passes.

**BLOCKED:** Benchmark-specific integration is not independently safe or
evidence-supported. No authoritative compiler invocation, benchmark input and
output schema, official verifier/scorer, or conformance fixtures were
available. No adapter or placeholder success path was added.

## Implemented bounded correction

During the source re-audit, a concrete artifact-store root-escape defect was
reproduced. `ArtifactStore.verify` accepted an object that merely resembled an
artifact reference, allowing an unvalidated `../outside.bin` path to reach
filesystem verification.

- **Root cause:** Python type annotations were not runtime validation at the
  `ArtifactStore._open_artifact` trust boundary.
- **Correction:** `_open_artifact` now requires an `ArtifactReference` and
  revalidates its path before descriptor-relative traversal.
- **Regression test:** `test_artifact_store_rejects_unvalidated_reference_type`
  in [`tests/test_compiler_infrastructure.py`](../tests/test_compiler_infrastructure.py).
- **Verification:** The focused infrastructure suite passed (40 tests), and the
  full suite passed (53 tests) after the correction.

This fix closes that reproduced invalid-reference path. It is not a claim of
production security or universal filesystem-race immunity.

## Integration readiness

| Integration | Status | Reason |
|---|---|---|
| INVSQRT adapter | **BLOCKED** | Paper-derived algorithm details exist, but authoritative input/output serialization, exact compiler invocation, and official verifier are unavailable. |
| DQI adapter | **BLOCKED** | Paper-derived finite-field and code construction do not establish authoritative bit/byte order, fixtures, scoring implementation, or verifier. |
| DFTHC-SOS adapter | **BLOCKED** | Dataset schema, axis/address encoding, official angle-oracle interface, and verifier are unavailable. |
| Kickmix integration | **PARTIAL / BLOCKED** | Upstream source and registry release are inspectable, but project adoption and official competition compatibility are unknown. |
| Official verifier/scorer adapter | **BLOCKED** | No official implementation or versioned API was available. |

## Minimum future adapter contract

The following is an **ENGINEERING PROPOSAL**, not an official interface:

1. Versioned input contract and benchmark-specific validation.
2. Explicit compiler executable/API and normalized invocation parameters.
3. Output artifact format, canonicalization, and bounded size.
4. Integrity check tied to a known artifact digest.
5. Independent verifier API and exact passing response semantics.
6. Resource-accounting source, units, and scorer version.
7. Deterministic execution metadata and declared nondeterministic inputs.
8. Failure, timeout, cleanup, and partial-output semantics.
9. Compiler, adapter, verifier, and source provenance identifiers.

The local protocol may be used as an outer orchestration shell only after
mapping the official contracts to it without changing their meaning.

## External inputs that unblock implementation

1. An authorized, versioned compiler/reference source or executable and exact
   invocation/build instructions.
2. Official machine-readable schemas and representative fixtures for each
   benchmark.
3. Official output serialization specification and accepted operation set.
4. Official verifier/scorer source or executable, version/hash, and exact
   invocation.
5. Resource limits, timeout behavior, and cleanup requirements.
6. Kickmix adoption decision and source/package mapping, if Kickmix is intended
   to be in the execution path.
7. Clarification of the DQI resource-accounting discrepancy only if an
   authoritative scoring contract requires resolving it.

## Recommended next milestone

Obtain and verify the external inputs above, beginning with the official
verifier/scorer package and representative fixtures. Record source identity and
hashes without installing or executing untrusted artifacts. Then select one
benchmark for a narrow contract-reconciliation spike; keep other adapters
blocked until their own contracts are verified.
