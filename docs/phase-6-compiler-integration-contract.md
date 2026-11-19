# Phase 6: Compiler Integration Contract

**Review date:** 2026-11-19
**Repository baseline:** `feat/compiler-infrastructure` at
`7165220562da2bb34bf2700ee844ad4a312e3b13`

## Decision

**Outcome B — external integration blocked.** A real benchmark and verifier
contract is now visible in the Google Quantum AI-authored paper and the
competition's public Kaggle page. However, the actual Kaggle data bundle,
verifier implementation, authorized fixtures, and a compiler invocation
contract are not available in this checkout or through the unauthenticated
public requests made for this review. Kickmix is an upstream circuit builder,
serializer, and simulator, not an identified optimizing compiler entry point.
No adapter was created.

## Evidence inventory

| Source | Classification | Verified contribution | Boundary |
|---|---|---|---|
| [Kaggle competition page](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation) | **OFFICIAL SOURCE** | Page metadata identifies “Google Quantum AI - Verifiable Quantum Circuit Compilation” and describes reducing resources for quantum applications. The public page route exists. | The data/rules routes returned only the Kaggle application shell. They did not expose a file list, executable verifier, or full rules in the retrieved HTML. |
| [Kaggle metric notebook](https://www.kaggle.com/code/metric/google-quantum-ai-metric) | **OFFICIAL SOURCE**, metadata only | Public page metadata identifies “Google Quantum AI Metric” and says it uses data from this competition. | Notebook source and execution contract were not retrieved. |
| Khattar et al., [arXiv:2610.23832v2](https://arxiv.org/abs/2610.23832v2), revised 2026-10-21 | **PAPER-DERIVED** | The paper identifies its authors' Google Quantum AI affiliation and describes Kickmix, the verifier design, and the three benchmark contracts. | It is not the Kaggle verifier executable, full competition data bundle, or an invocable compiler API. |
| [`quantumlib/Qualtran`](https://github.com/quantumlib/Qualtran), commit [`f559b12af459e7e97e6c6c382434431c03b903c9`](https://github.com/quantumlib/Qualtran/tree/f559b12af459e7e97e6c6c382434431c03b903c9) | **VERIFIED UPSTREAM** | Contains the Kickmix C++/Python circuit API, KMX/KMB file support, and circuit-building/simulation source. GitHub reports the current `main` SHA is the same commit. | No benchmark-specific source paths matching `invsqrt`, `dqi`, `dfthc`, `femoco`, `verifiable`, or `competition` were present in the commit tree. This is not a competition compiler release. |
| [`qarena-ai/invsqrt`](https://github.com/qarena-ai/invsqrt) and sibling benchmark repositories | **PARTICIPANT-MIRROR** | The repository describes itself as a QArena export and claims its verifier was copied unchanged from Kaggle data. | Its README explicitly says QArena is independent of Google and Kaggle and neither sponsors nor endorses it. The claims and copied bytes were not compared with official data; the repository is not used as an authoritative dependency. |
| This checkout | **VERIFIED LOCAL FACT** | Contains generic request/result types, in-process executor/verifier protocols, artifact storage, and tests. | Contains no benchmark compiler, circuit IR, benchmark adapter, Kickmix package, or official verifier. |

### Source correction

The Phase 5 reports mistakenly cited arXiv:2502.07732, which is an unrelated
paper. That citation has been corrected in the affected Phase 5 documents.
The relevant paper is arXiv:2610.23832v2.

## Actual Kickmix API boundary

At the pinned upstream commit, the Python binding documents:

- `Circuit.from_file(path, format='auto') -> Circuit`
- `Circuit.to_file(self, path, format='kmx') -> None`
- `CircuitBuilder()` and a `finish_circuit()` result that is a `Circuit`

The `format` choices include `kmx` and `kmb`. The relevant binding source is
[`circuit.pybind.cc`](https://github.com/quantumlib/Qualtran/blob/f559b12af459e7e97e6c6c382434431c03b903c9/kickmix/src/kickmix/py/circuit/circuit.pybind.cc#L302-L413)
and the builder is in
[`circuit_builder.pybind.cc`](https://github.com/quantumlib/Qualtran/blob/f559b12af459e7e97e6c6c382434431c03b903c9/kickmix/src/kickmix/py/circuit/circuit_builder.pybind.cc#L121).
The paper describes Kickmix as a restricted circuit-building and simulation
package. These APIs construct, load, inspect, serialize, and simulate circuits;
the inspected source does not establish a general optimizer that accepts a
benchmark request and compiles it into a lower-cost circuit.

The competition artifact described by the paper is a Kickmix circuit file,
not a source program passed to an identified official compiler. The exact
competition-supplied `kickmix.so`, its build hash, and compatibility with the
upstream commit were not verified.

**PAPER-DERIVED:** The task is framed as optimizing/constructing a constrained
circuit and submitting the resulting artifact. The paper provides reference
circuits as baselines; it does not specify a central compiler service that
participants invoke. Therefore “official compiler unavailable” should not be
read as proof that the competition is missing a required service: a
participant's optimizer may itself be the compiler. This repository currently
contains no such optimizer, and selecting/designing one requires a project
owner decision rather than guessing an official API.

## Local API is not the competition API

**VERIFIED LOCAL FACT:** [`tools/compiler_infrastructure.py`](../tools/compiler_infrastructure.py)
defines `CompilationRequest`, `ArtifactReference`, `CompilationResult`,
`VerificationResult`, `CompilerExecutor`, `CompilerVerifier`, `ArtifactStore`,
and `run_compilation`. The executor and verifier protocols are injected
in-process Python interfaces. They neither invoke Kickmix nor define the
competition's `.kmb` submission contract.

## Compiler contract status

| Item | Status |
|---|---|
| Official compiler identity/version | **Not specified by the paper; no central compiler service identified** |
| Compiler CLI or callable entry point | **Not specified; participant-side optimizer is project scope** |
| Optimizer stages and pass semantics | **UNKNOWN / project-owner decision** |
| Kickmix circuit builder/serializer | **VERIFIED UPSTREAM**, not an optimizer |
| Input and output competition semantics | **PAPER-DERIVED**, with required data artifacts unavailable |
| Official build invocation and supported runtime | **UNKNOWN / BLOCKED** |

No compiler command was run, no upstream package was installed, and no
competition artifact was built. The minimum evidence needed to unblock an
adapter is an authorized, versioned compiler/tool distribution, its exact
invocation/build contract, the official data bundle, and a fixture-backed
verification path.
