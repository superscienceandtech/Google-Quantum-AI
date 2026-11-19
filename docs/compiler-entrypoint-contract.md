# Compiler Entry-Point Contract Discovery

- **Updated:** 2026-11-19
- **Status:** a local KMX v2 compiler CLI now exists; the official competition
  compiler/runtime contract remains **BLOCKED**.

## Evidence labels

**VERIFIED LOCALLY**, **VERIFIED UPSTREAM**, **VERIFIED OFFICIAL**,
**PAPER-DERIVED**, **ENGINEERING PROPOSAL**, **BLOCKED**, and **UNKNOWN** are
the only evidence labels used below. Local implementation is not evidence of
official compatibility; upstream source is not evidence of project adoption.

## Discovered executable surfaces

| Surface | Inputs / outputs | Invocation | Evidence and scope |
|---|---|---|---|
| `tools.verify_sha256.main(argv)` | File path and expected SHA-256; returns CLI status 0/1/2 for match/mismatch/read error. | `python3 tools/verify_sha256.py PATH EXPECTED_SHA256` | **VERIFIED LOCALLY**. Integrity utility only; not a compiler. |
| `tools.kickmix_compiler.main(argv)` | Bounded KMX v2 text to deterministic KMX v2 output; emits a JSON summary and returns 0/2/3 for success/compile/output failure. | `python3 -m tools.kickmix_compiler INPUT.kmx OUTPUT.kmx` | **VERIFIED LOCALLY**. One conservative optimization pass; upstream differential execution is **BLOCKED** and official compatibility is **UNKNOWN**. |
| `tools.compiler_infrastructure.run_compilation(...)` | `CompilationRequest`, injected executor, injected verifier, `ArtifactStore`; returns `ExecutionReport`. | Python function call, no CLI or standalone command. | **ENGINEERING PROPOSAL**. Used by infrastructure tests with test doubles. |
| `CompilerExecutor.compile(request, context)` | Local request/context; returns local `CompilationResult`. | In-process protocol call. | **ENGINEERING PROPOSAL**; not discovered competition API. |
| `SubprocessCompilerExecutor` | Versioned local JSON envelope on stdin; `CompilationResult`-shaped JSON on stdout; artifacts beneath the per-run output directory. | Configure an argv sequence, then pass the executor to `run_compilation`. | **ENGINEERING PROPOSAL**, with test execution **VERIFIED LOCALLY**; not a competition protocol. |
| `CompilerVerifier.verify(request, context)` | Local verification request/context; returns local `VerificationResult`. | In-process protocol call. | **ENGINEERING PROPOSAL**; not an official verifier. |
| Kickmix APIs | Upstream circuit/build/simulation APIs, including file I/O. | Upstream Python/C++ APIs and Bazel targets. | **VERIFIED UPSTREAM** at Qualtran commit `f559b12af459e7e97e6c6c382434431c03b903c9`; no project invocation or dependency declaration. |

The competition compiler command, complete benchmark input schema, resource
policy, and verifier/scorer invocation are **BLOCKED** on authoritative
artifacts not present in this checkout. The local KMX CLI is a functioning
project-owned entry point (**VERIFIED LOCALLY**), but it does not establish
benchmark compilation or competition compatibility.

## Required official entry-point contract (BLOCKED)

Before documenting an actual compiler command, obtain an authoritative source
for each item below:

1. Executable/package identity, immutable version, and integrity digest.
2. Supported OS, language/runtime, native toolchain, and dependency versions.
3. Exact command or callable signature, including working directory and
   environment variables.
4. Input schema, version negotiation, and validation rules.
5. Output artifact schema, format, serialization, and publication behavior.
6. Exit-code/result mapping, diagnostics, partial-output behavior, and cleanup.
7. Timeout, cancellation, CPU/memory, and other resource limits.
8. Reproducibility inputs, seed derivation, compiler flags, and metadata.
9. Independent verifier/scorer invocation and required output.

Do not treat the paper's Kickmix descriptions, upstream Qualtran commands,
the local `run_compilation` / `SubprocessCompilerExecutor` protocols, or the
local KMX CLI as satisfying these official requirements.

## Safe local commands

These commands cover local utilities and KMX-to-KMX compilation
(**VERIFIED LOCALLY**). They do not run a benchmark adapter, official verifier,
or competition scorer:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 tools/verify_sha256.py PATH EXPECTED_SHA256
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.kickmix_compiler INPUT.kmx OUTPUT.kmx
```

The first runs utility and infrastructure tests; the second verifies one
file's bytes against a caller-supplied digest. The third validates and
optimizes KMX v2 text using the local implementation; it does not build or
invoke a competition compiler.

## Evidence references

- Project tree: `git ls-files`, `git ls-files --others --exclude-standard`.
- Local proposal: `tools/compiler_infrastructure.py` and
  `tests/test_compiler_infrastructure.py`.
- Local KMX pipeline: `tools/kickmix_compiler.py`,
  `tools/participant_optimizer.py`, and `tests/test_kickmix_compiler.py`.
- Utility: `tools/verify_sha256.py` and `tests/test_verify_sha256.py`.
- Upstream-only API and build details:
  [Kickmix dossier](kickmix-interface-benchmark-contract-dossier.md).
- Missing architecture and owner inputs:
  [compiler-authoritative-architecture.md](compiler-authoritative-architecture.md).
