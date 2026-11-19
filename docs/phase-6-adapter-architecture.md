# Phase 6: Adapter Architecture and Implementation Decision

**Status:** No adapter implemented; this document records the minimum future
boundary only.

## Evidence labels

**VERIFIED LOCAL FACT** describes local Python interfaces.
**PAPER-DERIVED** describes benchmark requirements from arXiv:2610.23832v2.
**VERIFIED UPSTREAM** describes Kickmix source at the pinned Qualtran commit.
**ENGINEERING PROPOSAL** is a design suggestion, not an official API.
**BLOCKED** means required official artifacts are unavailable.

## Why there is no real adapter

The current compiler-neutral infrastructure accepts a `CompilationRequest`
and delegates to an in-process `CompilerExecutor`. The actual competition
accepts Kickmix circuits and its paper describes benchmark-specific checks.
However:

- No official optimizer/compiler entry point was identified.
- The competition's `.kmb` files, reference fixtures, and verifier source were
  not available.
- The pinned Kickmix library was not installed or built, and compatibility
  with the competition's runtime was not tested.
- The unaffiliated QArena verifier copies cannot be assumed to match official
  bytes.

Creating an adapter now would require fabricating compilation, data parsing,
or success behavior, so none was added.

## Proposed adapter boundary

This is an **ENGINEERING PROPOSAL**, not a competition contract.

```text
authorized benchmark request
    -> strict benchmark-specific parser/validator
    -> verified compiler or circuit-builder entry point
    -> validated KMB artifact
    -> digest and provenance record
    -> official verifier/scorer invocation
    -> structured passed/failed/blocked result
```

Only verified identities, versions, argument forms, and field semantics may be
mapped into the local infrastructure. Unknown values must remain unknown;
missing verification must return blocked, never success.

## Minimum boundary

1. **Input:** authoritative schema/version, bounded file sizes, complete field
   validation, explicit numerical constraints, and no hidden defaults.
2. **Invocation:** immutable compiler identity, argument vector or typed API,
   controlled environment, and documented working directory.
3. **Output:** allowed artifact paths, KMB version, named registers, circuit
   validation, and no silent rewrites.
4. **Integrity:** digest the exact emitted bytes and recheck after verifier
   handoff; separately establish source authenticity.
5. **Verification:** official verifier identity/version, exact passing
   response, timeout/resource semantics, and authorized fixtures.
6. **Accounting:** exact score implementation/version and the source of each
   counted operation or analytical cost.
7. **Reproducibility:** source revisions, toolchain, dependencies,
   configuration, seeds, and platform.
8. **Failure:** explicit unavailable, timeout, nonzero exit, malformed output,
   verifier failure, and partial-output behavior.

## Benchmark-specific unresolved inputs

- **INVSQRT:** official KMB baseline/fixture, exact KMB version accepted by
  Kaggle, competition Kickmix binary/version, and official verifier runtime.
- **DQI:** official encoded syndrome/record fixtures, actual verifier source,
  and scoring implementation.
- **DFTHC-SOS:** official tensor/data archive with schema and reference
  factorization, angle-oracle fixtures, and verifier/scorer.

No placeholder adapter, no fake verifier, and no test-double success path was
added.
