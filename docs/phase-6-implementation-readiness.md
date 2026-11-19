# Phase 6: Implementation Readiness

**Outcome:** External compiler/verifier dependency remains blocked.

## Revalidated position

Phase 5's broad statement that no official competition material was available
needed refinement:

- **OFFICIAL SOURCE:** The exact Kaggle competition page and metric notebook
  are now identified by their official public URLs and page metadata.
- **PAPER-DERIVED:** arXiv:2610.23832v2 supplies substantial logical benchmark
  contracts and explains the salted-hash verifier. The previous Phase 5
  citation to arXiv:2502.07732 was incorrect and has been corrected.
- **VERIFIED UPSTREAM:** Qualtran/Kickmix source is available at an immutable
  commit and exposes circuit-building and KMB serialization APIs.
- **Still BLOCKED:** Kaggle data files, official verifier/scorer implementation
  and its actual invocation, authorized fixtures, and an optimizing compiler
  entry point were not obtained.
- **PARTICIPANT-MIRROR:** QArena publicly hosts files it says were copied from
  Kaggle; its README explicitly disclaims Google/Kaggle sponsorship. The
  claims could not be checked against Kaggle and are not treated as official.

## Acceptance criteria status

| Criterion | Result |
|---|---|
| Repository safety | **PASS:** branch, HEAD, README hash, dossier hash, and unstaged baseline preserved. |
| Compiler contract | **BLOCKED:** Kickmix is a library/API, not an identified benchmark optimizer/compiler. |
| Verifier contract | **PARTIAL:** paper algorithm and official Kaggle metric page metadata are available; executable and exact process contract are not. |
| Benchmark selection | **NO BENCHMARK QUALIFIES FOR REAL ADAPTER IMPLEMENTATION.** |
| First adapter | **Not implemented:** no speculative adapter or fake success path. |
| Compiler execution | **Not run:** no compiler entry point or authorized binary was available. |
| Artifact lifecycle | **VERIFIED LOCAL FACT:** the existing local lifecycle is documented/tested, but has no external compiler process backend. |
| Security/semantics | **PASS for local tests only:** security review found no confirmed vulnerability; no benchmark semantics were executed. |
| Reproducibility | **PARTIAL:** local suite and environment observed; clean-checkout compiler workflow remains unavailable. |
| Test suite | **PASS:** 53 local tests. |
| Git safety | **PASS:** no staging, commit, push, merge, branch switch, or destructive Git action. |

## Exact external blockers

1. Authorized Kaggle data bundle containing the verifier, metric code, Kickmix
   binary/build identity, reference circuit files, and benchmark datasets.
2. Permission/route to retrieve and use those files, or a separately published
   official versioned release with matching hashes.
3. Project-owner decision on the compiler/optimizer to build or integrate:
   the paper specifies circuit-artifact submissions but no central compiler
   service/API. If a distinct official compiler is expected by the project,
   provide its source/version and invocation.
4. Representative official fixtures and expected results for at least one
   benchmark.
5. Official process, timeout, memory, environment, and failure semantics.
6. A verified mapping between the competition's Kickmix binary and the public
   Qualtran commit/package used for local development.

No credentials were available or requested, and no access control was
bypassed.

## Next milestone

Obtain the authorized official data bundle and its release/hash provenance.
Then reconcile INVSQRT first as a narrow candidate because the paper's
logical contract is comparatively explicit. Do not implement its adapter
until the official KMB fixture, compiler/runtime, and verifier can be exercised
locally.
