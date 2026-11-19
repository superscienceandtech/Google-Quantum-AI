# Phase 10 — Compiler Integration Architecture

## Existing public surfaces

- `tools/compiler_infrastructure.py`
  - `CompilationRequest`
  - `CompilationResult`
  - `CompilerExecutor`
  - `CompilerVerifier`
  - `ArtifactStore`
  - `run_compilation`
- `tools/kickmix_compiler.py`
  - `parse_kmx`
  - `serialize_kmx`
  - `compile_kmx`
  - CLI `main`
- `tools/participant_optimizer.py`
  - conservative adjacent-involution cancellation
- `tools/official_scoring.py`
  - global geometric-mean aggregation helper

## Boundary

The compiler infrastructure injects executors/verifiers and verifies artifacts;
it does not define official benchmark semantics. The KMX compiler emits local
KMX text only. Benchmark adapters require authoritative schemas and fixtures.
