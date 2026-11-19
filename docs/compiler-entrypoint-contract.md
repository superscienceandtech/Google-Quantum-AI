# Compiler Entry-Point Contract Discovery

- **Updated:** 2026-11-19
- **Status:** **BLOCKED** — no actual project compiler entry point or
  invocation contract is present in the checkout.

## Evidence labels

**VERIFIED OFFICIAL** is limited to observed official page/release content;
**VERIFIED UPSTREAM** is pinned upstream behavior, not project adoption;
**PAPER-DERIVED** is paper text, not an executable contract;
**PARTICIPANT-MIRROR** is not authority; **LOCAL OBSERVATION** is evidence
from this checkout or a public response; **ENGINEERING PROPOSAL** denotes
local infrastructure interfaces; **UNVERIFIED ASSUMPTION** and **BLOCKED**
mark unresolved claims and missing authoritative evidence.

## Discovered executable surfaces

| Surface | Inputs / outputs | Invocation | Evidence and scope |
|---|---|---|---|
| `tools.verify_sha256.main(argv)` | File path and expected SHA-256; returns CLI status 0/1/2 for match/mismatch/read error. | `python3 tools/verify_sha256.py PATH EXPECTED_SHA256` | **VERIFIED LOCALLY**. Integrity utility only; not a compiler. |
| `tools.compiler_infrastructure.run_compilation(...)` | `CompilationRequest`, injected executor, injected verifier, `ArtifactStore`; returns `ExecutionReport`. | Python function call, no CLI or standalone command. | **ENGINEERING PROPOSAL**. Used by infrastructure tests with test doubles. |
| `CompilerExecutor.compile(request, context)` | Local request/context; returns local `CompilationResult`. | In-process protocol call. | **ENGINEERING PROPOSAL**; not discovered competition API. |
| `SubprocessCompilerExecutor` | Versioned local JSON envelope on stdin; `CompilationResult`-shaped JSON on stdout; artifacts beneath the per-run output directory. | Configure an argv sequence, then pass the executor to `run_compilation`. | **ENGINEERING PROPOSAL, EXECUTED LOCALLY** with a temporary Python test command; not a competition protocol. |
| `CompilerVerifier.verify(request, context)` | Local verification request/context; returns local `VerificationResult`. | In-process protocol call. | **ENGINEERING PROPOSAL**; not an official verifier. |
| Kickmix APIs | Upstream circuit/build/simulation APIs, including file I/O. | Upstream Python/C++ APIs and Bazel targets. | **VERIFIED UPSTREAM** at Qualtran commit `f559b12af459e7e97e6c6c382434431c03b903c9`; no project invocation or dependency declaration. |

No authoritative competition compiler command, input schema, output contract,
resource policy, or verifier/scorer invocation is available. The new local
process protocol does not fill those gaps or establish an executable
competition compiler.

## Required entry-point contract (BLOCKED, not a proposed API)

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

Do not treat the paper's Kickmix descriptions, upstream Qualtran commands, or
the local `run_compilation` / `SubprocessCompilerExecutor` protocols as
satisfying these requirements.

## Safe local commands

These are confirmed utility/infrastructure checks, not a compiler workflow:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 tools/verify_sha256.py PATH EXPECTED_SHA256
```

The first runs utility and infrastructure tests; the second verifies one
file's bytes against a caller-supplied digest. Neither builds or invokes a
competition compiler.

## Evidence references

- Project tree: `git ls-files`, `git ls-files --others --exclude-standard`.
- Local proposal: `tools/compiler_infrastructure.py` and
  `tests/test_compiler_infrastructure.py`.
- Utility: `tools/verify_sha256.py` and `tests/test_verify_sha256.py`.
- Upstream-only API and build details:
  [Kickmix dossier](kickmix-interface-benchmark-contract-dossier.md).
- Missing architecture and owner inputs:
  [compiler-authoritative-architecture.md](compiler-authoritative-architecture.md).
