# Phase 5: Official Verifier and Scorer Contract Status

**Review date:** 2026-11-19

## Evidence labels

**VERIFIED LOCAL FACT** refers to this checkout and executed local commands.
**OFFICIAL SOURCE** refers only to the retrieved official competition material.
**PAPER-DERIVED** and **VERIFIED UPSTREAM** are not official verifier
contracts. **UNKNOWN** means not established; **BLOCKED** means required
authoritative material is unavailable. **ENGINEERING PROPOSAL** is a local
recommendation, not an official requirement.

## Availability conclusion

**BLOCKED:** No official verifier or scorer implementation, versioned API,
executable, source release, fixture, or exact command was available in the
repository or inspected public materials.

**OFFICIAL SOURCE, limited:** The public Kaggle page exposed title/description
metadata. A request to enumerate competition files returned HTTP 401. No
authentication or access control was bypassed, and no private source was
retrieved.

**PAPER-DERIVED:** The paper describes benchmark algorithms, challenge setup,
and scoring/resource analyses. The paper does not provide sufficient evidence
for an executable verifier contract or the exact current evaluation pipeline.

## Contract matrix

| Contract element | Evidence status | Finding |
|---|---|---|
| Official verifier identity and version | **UNKNOWN / BLOCKED** | No source, package, commit, image, or release identifier was obtained. |
| Invocation command, arguments, working directory | **UNKNOWN / BLOCKED** | No authoritative executable invocation is available. |
| Input fixture schema and validation | **UNKNOWN / BLOCKED** | Paper descriptions do not establish an official machine-readable schema. |
| Compiled artifact format and canonical encoding | **UNKNOWN / BLOCKED** | The official artifact format and parser were not available. |
| Circuit semantic checks | **PAPER-DERIVED, incomplete** | The paper describes benchmark semantics but does not establish exact verifier implementation behavior. |
| Resource accounting and scorer version | **PAPER-DERIVED, incomplete** | Paper tables and formulas are not a substitute for the scoring implementation or its versioned rules. |
| Randomness, seeds, salts, or sample generation | **UNKNOWN / BLOCKED** | Any private or unpublished values remain unknown; none were fabricated. |
| Tolerance, accepted precision, and comparison behavior | **PAPER-DERIVED where specified; otherwise UNKNOWN** | The benchmark dossier records individual paper claims. Official executable comparison rules are unavailable. |
| Exit codes, output messages, failure categories | **UNKNOWN / BLOCKED** | No authoritative behavior was retrieved. |
| Timeout, memory, process, and sandbox limits | **UNKNOWN / BLOCKED** | No official deployment configuration was retrieved. |
| Provenance/authenticity requirements | **UNKNOWN / BLOCKED** | No signature or official provenance contract was found. |

## Local infrastructure distinction

**VERIFIED LOCAL FACT:** The local `CompilerVerifier` protocol and
`VerificationResult` model in [`tools/compiler_infrastructure.py`](../tools/compiler_infrastructure.py)
are engineering interfaces. They do not implement or emulate the official
verifier. The local SHA-256 utility verifies byte integrity relative to a
provided digest; it does not prove that the digest or artifact is official.

## Exact external inputs needed

Before implementing an official verifier/scorer adapter, obtain an authorized,
versioned copy of:

1. Verifier/scorer source or executable with a stable version/commit/hash.
2. Public API or exact invocation and process/environment requirements.
3. Representative, non-sensitive input and expected-output fixtures.
4. Official serialization specification and accepted operations.
5. Exact scoring/resource-accounting rules and their version.
6. Documented failure, timeout, and resource-limit behavior.
7. Any permitted seed/salt inputs and their provenance.

Until these are supplied, official verifier compatibility is **BLOCKED**.
