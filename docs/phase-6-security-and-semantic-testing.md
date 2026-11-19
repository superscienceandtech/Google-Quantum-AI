# Phase 6: Security and Semantic Testing

**Review date:** 2026-11-19

## Security review findings

The required read-only security review found **no confirmed security
vulnerabilities** in the reviewed local infrastructure. Residual concerns
below are trust-boundary and portability limitations, not confirmed
exploitable defects.

| # | Severity | File | Lines | Vulnerability | Confidence |
|---|----------|------|-------|---------------|------------|
| — | — | — | — | No confirmed security vulnerabilities identified by the read-only review. | — |

## Residual risks

- **In-process trust:** `CompilerExecutor` and `CompilerVerifier` run with
  process permissions and can affect any accessible file or spawn processes.
  The local protocol is not isolation.
- **Platform limits:** Artifact descriptor defenses require POSIX
  `dir_fd`, `O_NOFOLLOW`, and `O_DIRECTORY`; unsupported platforms fail
  closed.
- **Reproducibility:** Manifests include Python and platform metadata, so
  identical compilation results in different environments need not have
  identical manifest bytes.
- **Integrity versus authenticity:** SHA-256 detects byte differences relative
  to a supplied digest; it does not authenticate the publisher or source.
- **Concurrent content changes:** Descriptor anchoring and revalidation detect
  ordinary mutations, but are not an immutable snapshot against an adversary
  able to modify file contents while preserving observable metadata.

These points are also recorded in
[`compiler-infrastructure-core.md`](compiler-infrastructure-core.md). No
security changes were necessary in Phase 6.

## Existing test coverage

Baseline and Phase 6 baseline suite: **53 tests passed** (13 SHA-256 utility
tests and 40 infrastructure tests).

| Category | Existing coverage |
|---|---|
| Unit/input validation | Request schema/version, JSON bounds and unsupported values, safe identifiers/paths/digests, immutable options, malformed outputs and verifier responses. |
| Filesystem regressions | Traversal and absolute paths, symlink files/directories/root, FIFO/non-regular rejection, missing files, digest mismatch, descriptor anchoring, mutation during use, concurrent run creation, manifest collision/corruption. |
| Lifecycle/failure | Missing executor/verifier, executor/verifier exception, partial output, invalid result, failure status, input/output mutation, verifier handoff integrity. |
| Determinism | Canonical JSON, mapping insertion-order independence, repeated manifests and checksum CLI results. |
| Compiler integration | **Not run:** no official compiler executable/API was found. |
| Benchmark fixtures | **Not run:** no authorized fixtures were retrieved. |
| Official verifier/acceptance | **Not run:** the verifier source and metric execution path were unavailable. |

All executor/verifier cases use local test doubles. Their passing tests establish
only the local orchestration behavior.

## Semantic correctness boundary

The paper provides reference semantics and sampling strategies, but no local
test here compares a real circuit against those semantics. Basis-state tests
alone would not establish universal unitary equivalence. No circuit phase,
register ordering, workspace, measurement, or score result is claimed as
verified by this repository's suite.
