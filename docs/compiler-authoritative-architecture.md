# Compiler Architecture and Authority Discovery

- **Updated:** 2026-11-19
- **Repository:** `superscienceandtech/Google-Quantum-AI`
- **Branch / HEAD:** `feat/compiler-infrastructure` /
  `7165220562da2bb34bf2700ee844ad4a312e3b13`
- **Decision:** project compiler architecture is **BLOCKED**; no project
  compiler or approved architecture was found in the checkout.

## Evidence labels

- **VERIFIED OFFICIAL** — direct evidence from an official competition page or
  release; the claim is limited to the content actually observed.
- **VERIFIED UPSTREAM** — source or documentation at an immutable upstream
  revision. This does not imply project adoption.
- **LOCAL OBSERVATION** — repository state or response observed during this
  investigation.
- **PAPER-DERIVED** — claim stated in the cited paper, not proof of executable
  verifier behavior.
- **PARTICIPANT-MIRROR** — participant-maintained source; not authoritative.
- **ENGINEERING PROPOSAL** — local infrastructure interface or suggested
  boundary, not a competition contract.
- **UNVERIFIED ASSUMPTION** — not established by inspected evidence.
- **BLOCKED** — requires an authoritative project or competition source that
  is unavailable here.

## Repository inventory

The tracked tree at HEAD contains only:

- `README.md`
- `tests/test_verify_sha256.py`
- `tools/verify_sha256.py`

The worktree additionally contains a compiler-neutral infrastructure proposal,
its test doubles, and research documents. There are no tracked or untracked
project C++ sources, build files, dependency manifests, lockfiles, CI
workflows, submodules, circuit IRs, compiler passes, or benchmark adapters.
The complete current worktree file inventory is recorded by `git ls-files`
and `git ls-files --others --exclude-standard`; no vendored source tree is
present.

`tools/compiler_infrastructure.py` defines local request/result data models,
an injected executor protocol, an injected verifier protocol, artifact
handling, and `run_compilation`. These are **ENGINEERING PROPOSALS**. The
executor and verifier used by `tests/test_compiler_infrastructure.py` are test
doubles. They are not the competition compiler or verifier.

The only standalone command-line program found is the SHA-256 checker in
`tools/verify_sha256.py`. It does not construct, optimize, serialize, or
verify quantum circuits.

## Source register

| Source | Evidence class | Supported claims and limits |
|---|---|---|
| [Kaggle competition page](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation) | **VERIFIED OFFICIAL**, page identity/title metadata only | The fetched page exposes the competition title and short description. Its body is a client-rendered shell; no verifier, data schema, compiler command, or scoring interface was obtained from it. |
| Khattar et al., [arXiv:2610.23832v2](https://arxiv.org/abs/2610.23832), revised 2026-10-21 | **PAPER-DERIVED** | Describes Kickmix and three benchmark mathematical contracts, sampling, and resource formulas. It is not an executable competition API or complete artifact schema. |
| [`quantumlib/Qualtran`](https://github.com/quantumlib/Qualtran/tree/f559b12af459e7e97e6c6c382434431c03b903c9) at `f559b12af459e7e97e6c6c382434431c03b903c9` | **VERIFIED UPSTREAM** | Provides pinned Kickmix documentation and implementation. No evidence found that this project imports or builds it. |
| Participant repositories returned by public GitHub search | **PARTICIPANT-MIRROR / UNVERIFIED** | Search results include repositories describing competition entries and verifier-like tooling. Their authority is not established; they were not used as contracts or executed. |
| Local infrastructure protocols | **ENGINEERING PROPOSAL** | Compiler-neutral orchestration and artifact handling exist in the worktree, but do not identify the actual compiler or official verifier. |

Public GitHub repository searches on 2026-11-19 found participant-namespaced
title matches, no exact-title result under `org:google`, and no `Kickmix`
repository under `org:google`. Search results are not exhaustive proof that
no official repository exists elsewhere. The prior
[Kickmix dossier](kickmix-interface-benchmark-contract-dossier.md) records
the public Kaggle file-list request's HTTP 401 as an access limitation; no
authentication was bypassed.

## Architecture findings

| Component | Finding | Status |
|---|---|---|
| Compiler implementation / entry point | None in the repository. | **BLOCKED** |
| Intermediate representation / circuit model | None project-owned. | **BLOCKED** |
| Optimization passes | None project-owned. | **BLOCKED** |
| Circuit construction / serialization | No project API. Upstream Kickmix supports circuit construction and KMX/KMB I/O at the pinned revision. | Project use **BLOCKED**; upstream **VERIFIED UPSTREAM** |
| Resource accounting | No project scorer. Kickmix offers operation statistics; the paper defines benchmark-specific formulas. | Official accounting **BLOCKED** |
| Verification / scoring | No local or retrieved official verifier/scorer package or invocation. | **BLOCKED** |
| Build and runtime | No project build system or supported toolchain declaration. | **BLOCKED** |

The pinned Kickmix API reference, source paths, format notes, and benchmark
contracts are detailed in the [dossier](kickmix-interface-benchmark-contract-dossier.md)
and [infrastructure architecture map](compiler-infrastructure-architecture.md).
Neither upstream source nor paper-derived semantics establish project
architecture. No project module names or quantum semantics are inferred here.

## Owner evidence required

The project owner must provide or identify the approved compiler architecture,
module boundaries, entry point, IR/circuit representation, toolchain, and
build/test workflow. The competition owner must provide the immutable
verifier/scorer and authorized benchmark artifacts described in
[phase-4-implementation-readiness.md](phase-4-implementation-readiness.md).
