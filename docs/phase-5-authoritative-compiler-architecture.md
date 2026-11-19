# Phase 5: Compiler Architecture and Source Inventory

**Review date:** 2026-11-19
**Repository:** `superscienceandtech/Google-Quantum-AI`
**Branch / HEAD at review start:** `feat/compiler-infrastructure` /
`7165220562da2bb34bf2700ee844ad4a312e3b13`

## Evidence labels

- **VERIFIED LOCAL FACT**: directly observed in this checkout or a command run
  against it.
- **OFFICIAL SOURCE**: directly published by the competition owner; the label
  applies only to the specific material retrieved.
- **VERIFIED UPSTREAM**: directly observed in the named upstream project or
  package registry, not a competition contract.
- **PAPER-DERIVED**: stated or derived from the cited research paper.
- **PARTICIPANT-MIRROR**: participant-provided material; not official.
- **ENGINEERING PROPOSAL**: a suggested local design, not an external
  requirement.
- **UNKNOWN**: not established from available evidence.
- **BLOCKED**: cannot be implemented without missing authoritative input.

## Executive finding

**VERIFIED LOCAL FACT:** The checkout contains compiler-neutral orchestration,
artifact-integrity, and verifier/executor protocols. It does not contain a
benchmark compiler implementation, a compiler adapter, a quantum-circuit IR, an
official scorer, or an official verifier. The existing generic executor is an
in-process extension point; it is not evidence of an actual competition
compiler or a security boundary.

**BLOCKED:** No authoritative competition compiler architecture or executable
compiler API was found in the repository or the inspected public sources.
Benchmark-specific implementation should not begin from these local protocols
alone.

## Local module inventory

| Area | Evidence and actual boundary |
|---|---|
| Local orchestration | **VERIFIED LOCAL FACT:** [`tools/compiler_infrastructure.py`](../tools/compiler_infrastructure.py) defines request/result models, the executor and verifier protocols, artifact storage, manifest handling, and `run_compilation`. These are local infrastructure contracts. |
| Artifact verification utility | **VERIFIED LOCAL FACT:** [`tools/verify_sha256.py`](../tools/verify_sha256.py) and [`tests/test_verify_sha256.py`](../tests/test_verify_sha256.py) cover a standalone SHA-256 file-checking utility; this is not a circuit verifier. |
| Infrastructure tests | **VERIFIED LOCAL FACT:** [`tests/test_compiler_infrastructure.py`](../tests/test_compiler_infrastructure.py) covers local orchestration and artifact-store behavior. |
| Documentation | **VERIFIED LOCAL FACT:** `docs/compiler-infrastructure-*.md`, `docs/compiler-environment.md`, and `docs/compiler-dependencies.md` describe the local proposal and its limits. The Kickmix evidence is separately recorded in [`docs/kickmix-interface-benchmark-contract-dossier.md`](kickmix-interface-benchmark-contract-dossier.md). |
| Project compiler / IR / adapters | **UNKNOWN / BLOCKED:** No source-backed compiler entry point, intermediate representation, benchmark adapter, or project build target was found. |
| Official verifier / scorer | **UNKNOWN / BLOCKED:** No executable, API, package, fixture set, or scoring interface was supplied or retrieved. |

## Source inventory

| Source | Classification | What it supports | What it does not support |
|---|---|---|---|
| Current checkout, HEAD `7165220562da2bb34bf2700ee844ad4a312e3b13` | **VERIFIED LOCAL FACT** | The local modules and tests listed above; current implementation behavior. | Official compiler, benchmark, verifier, or scoring semantics. |
| Kaggle competition page, <https://www.kaggle.com/competitions/quantum-ai> | **OFFICIAL SOURCE**, limited | Public competition title/description metadata was retrievable. | The attempted file-list request returned HTTP 401. No private content was accessed; compiler instructions, verifier, scoring details, fixtures, and downloadable contract remain unavailable. |
| Paper, “Leveraging verifiable structure in quantum circuits to find more efficient compilations with agentic AI,” arXiv:2610.23832v2, <https://arxiv.org/abs/2610.23832v2> | **PAPER-DERIVED** | Kickmix description, benchmark semantics, verifier procedure, sampling, and resource/scoring formulas. The article identifies the authors' affiliation as Google Quantum AI. | The paper is not the executable verifier or the competition's complete serialized data package; Kaggle-salted verifier execution and authorized fixtures remain unavailable here. |
| `quantumlib/Qualtran`, pinned upstream commit `f559b12af459e7e97e6c6c382434431c03b903c9` | **VERIFIED UPSTREAM** | The inspected Kickmix source, its circuit/simulator API, operation model, and source revision. | Proof that this revision is adopted by the competition or by this project; an official compiler or verifier. |
| PyPI `kickmix` 1.0.0, <https://pypi.org/project/kickmix/> | **VERIFIED UPSTREAM registry metadata** | Registry lists author `Qualtran Developers`, homepage `quantumlib/Qualtran`, runtime requirement `numpy`, upload date 2026-10-27, and a CPython 3.12 manylinux x86_64 wheel. | The wheel's downloaded bytes, mapping of this release to the later pinned Git commit, project adoption, or competition compatibility. |
| Participant-labelled public repositories discovered during search | **PARTICIPANT-MIRROR** | Potential research leads only. | Officialness, correctness, or permission to substitute their behavior for the official contract. |

The discovery procedure and source limits are also summarized in
[`phase-5-implementation-readiness.md`](phase-5-implementation-readiness.md).

## Local call boundary

**VERIFIED LOCAL FACT:** `run_compilation` accepts a local
`CompilationRequest`, `CompilerExecutor`, optional `CompilerVerifier`, and an
`ArtifactStore`. The executor produces the expected local artifact result; the
store validates and hashes artifacts; the verifier returns a local
`VerificationResult`. This establishes only the boundary encoded and tested by
the local Python module.

**VERIFIED LOCAL FACT:** Executor and verifier protocols execute in process.
They do not isolate untrusted compiler/verifier code. SHA-256 is an integrity
check against a known digest, not a signature, provenance proof, or authenticity
check.

## Recommendation

**ENGINEERING PROPOSAL:** Keep the infrastructure compiler-neutral. Add a
benchmark adapter only after its authoritative input format, invocation,
output format, resource-accounting rules, and verifier interface are available
and inspected. Do not infer the competition architecture from the paper,
Kickmix, or participant mirrors.
