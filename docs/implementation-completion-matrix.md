# Implementation Completion Matrix

This matrix distinguishes local implementation from official integration and
benchmark evidence. Documentation is not treated as proof that a software
component exists.

Evidence labels follow the audit taxonomy: **VERIFIED LOCALLY**,
**VERIFIED UPSTREAM**, **VERIFIED OFFICIAL**, **PAPER-DERIVED**,
**ENGINEERING PROPOSAL**, **BLOCKED**, or **UNKNOWN**.

| Objective | Local implementation | Evidence / tests | Evidence classification and remaining status |
|---|---|---|---|
| Actual circuit compiler | KMX v2 parser, validator, deterministic writer, KMX-to-KMX local CLI | `tools/kickmix_compiler.py`; `tests/test_kickmix_compiler.py` | **VERIFIED LOCALLY**; upstream differential parse **BLOCKED**; official compatibility **UNKNOWN** |
| Participant optimizer | Adjacent identical self-inverse cancellation | `tools/participant_optimizer.py`; restricted finite-state regression tests | **VERIFIED LOCALLY** for tested subset; official optimizer boundary and metric-driven improvement **BLOCKED** |
| INVSQRT adapter | None | Contract and blockers in [Phase 7B](phase-7b-authoritative-evidence-report.md) | No local adapter **VERIFIED LOCALLY**; integration **BLOCKED** |
| DQI adapter | None | Contract and blockers in [Phase 7B](phase-7b-authoritative-evidence-report.md) | No local adapter **VERIFIED LOCALLY**; integration **BLOCKED** |
| DFTHC-SOS adapter | None | Contract and blockers in [Phase 7B](phase-7b-authoritative-evidence-report.md) | No local adapter **VERIFIED LOCALLY**; integration **BLOCKED** |
| Official verifier | None; existing infrastructure supports an injected verifier boundary | [Verifier contract](official-verifier-integration-contract.md) | No local official verifier **VERIFIED LOCALLY**; integration **BLOCKED** |
| Official scoring | Global geometric-mean formula only | `tools/official_scoring.py`; `tests/test_official_scoring.py` | Formula **VERIFIED OFFICIAL** and **VERIFIED LOCALLY**; row alignment, per-benchmark costs, and runtime **BLOCKED** |
| Real benchmark compilation | None demonstrated | No authorized benchmark fixtures in checkout | No local result **VERIFIED LOCALLY**; official outcome **UNKNOWN** |
| Circuit correctness verification | Exact exhaustive small-state check for the pass subset | `tests/test_kickmix_compiler.py` | **VERIFIED LOCALLY** for restricted subset; general quantum or benchmark verification **BLOCKED** |
| Competition end-to-end workflow | None | [Local workflow and limitations](end-to-end-workflow.md) | No local workflow **VERIFIED LOCALLY**; competition workflow **BLOCKED** |

## Documentation map

Avoiding duplicate contract reports, existing authoritative documents remain
the source of benchmark and environment evidence:

- Architecture: [compiler infrastructure architecture](compiler-infrastructure-architecture.md)
- Compiler-neutral infrastructure: [infrastructure core](compiler-infrastructure-core.md)
- Local circuit compiler: [KMX compiler core](kickmix-compiler-core.md)
- Optimizer: [participant optimizer](participant-optimizer.md)
- Benchmark contracts and evidence: [Phase 7B report](phase-7b-authoritative-evidence-report.md)
- Verifier contract: [official verifier integration contract](official-verifier-integration-contract.md)
- Scoring: [official scoring integration](official-scoring-integration.md)
- Correctness limits: [quantum correctness verification](quantum-correctness-verification.md)
- Workflow: [local end-to-end workflow](end-to-end-workflow.md)
- Reproducibility: [Phase 6 reproducibility](phase-6-reproducibility.md)
- Toolchain/dependencies: [toolchain baseline](compiler-toolchain-baseline.md),
  [dependency inventory](compiler-dependencies.md), and
  [environment](compiler-environment.md)
- Security and artifact boundaries: [infrastructure core](compiler-infrastructure-core.md)

The benchmark-specific documents are intentionally not duplicated: no adapter
was implemented, and the Phase 7B report already records the latest
source-backed contract and blockers for all three benchmarks.
