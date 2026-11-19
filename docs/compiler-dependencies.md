# Compiler Infrastructure Dependency Inventory

- **Updated:** 2026-11-19
- **Repository snapshot:** `feat/compiler-infrastructure` at
  `7165220562da2bb34bf2700ee844ad4a312e3b13`

## Project-owned code

There is no dependency manifest or lockfile in the committed project tree.
The SHA-256 utility and compiler-neutral infrastructure proposal import Python
standard-library modules plus the local `tools` module.

| Dependency | Use | Version status |
|---|---|---|
| Python standard library: `argparse`, `errno`, `hashlib`, `stat`, `sys`, `pathlib`, `typing` | SHA-256 CLI, regular-file check, file reading, argument validation and process status. | Comes with Python; no project Python version policy is declared. |
| Python standard library: `unittest`, `subprocess`, `tempfile`, `os` | Utility tests, isolated CLI invocation, and platform-conditional FIFO regression test. | Comes with Python; no third-party test dependency. |
| Python standard library: `json`, `math`, `re`, `dataclasses`, `enum`, `types`, `typing` | Compiler-neutral request validation, protocols, artifact metadata, and deterministic JSON manifests in the current worktree. | Comes with Python; no third-party dependency. |
| Python standard library: `contextlib`, `secrets`, `threading`, `concurrent.futures`, `platform`, `signal`, `subprocess` | Descriptor-backed artifact streams, manifest publication, runtime metadata, concurrency tests, and bounded subprocess execution tests. | Comes with Python; no third-party dependency. |
| Local `tools.verify_sha256` module | Test access to parser and file hashing functions. | Project-owned source, not an external dependency. |

**VERIFIED LOCALLY:** AST inspection of the local Python files found only
standard-library imports and the local `tools` module. The utility and
compiler-neutral infrastructure tests ran with Python 3.12.3 without
installing packages. There is no project dependency manifest; no pinning is
currently justified for standard-library modules.

The use of assignment expressions in `verify_sha256.py` requires Python 3.8
or newer as a syntax matter. This is a compatibility floor implied by the
source, not an approved project support policy.

## Upstream-only dependencies

The following requirements refer to `quantumlib/Qualtran` at immutable commit
`f559b12af459e7e97e6c6c382434431c03b903c9`, as recorded in the
[Kickmix dossier](kickmix-interface-benchmark-contract-dossier.md). They are
not dependencies of the current committed project:

| Upstream item | Pinned/documented evidence | Current project classification |
|---|---|---|
| Bazel | `.bazelversion` selects 7.2.0; upstream CI uses Bazelisk 1.x. | **UPSTREAM-ONLY**, unavailable locally; not project-required. |
| C++ compiler | Kickmix BUILD uses C++20 and `-march=native`; no minimum compiler release is identified in the dossier. | **UPSTREAM-ONLY / UNVERIFIED COMPATIBILITY**; g++ 13.3.0 is present, but no upstream build was run. |
| pybind11 | Upstream package build pins 2.12.0; Bazel metadata also references `pybind11_bazel` 2.11.1. | **UPSTREAM-ONLY**, not installed locally; not required by local Python code. |
| NumPy | Declared as Kickmix wheel runtime dependency without a version pin in the cited BUILD metadata. | **UPSTREAM-ONLY**; not imported by the local checker or tests. |
| pytest | Listed in upstream Kickmix development/wheel-test instructions. | **UPSTREAM DEVELOPMENT TOOL**, not used by local tests and unavailable locally. |
| GoogleTest | Upstream module metadata pins 1.14.0 for C++ tests. | **UPSTREAM-ONLY**, not a project dependency. |
| setuptools / wheel | Upstream Kickmix Python package build requirements. | **UPSTREAM-ONLY**, not required to run the local checker/tests. |

Exact source locations, upstream command examples, and compatibility caveats
are recorded in the pinned-source dossier. Upstream commands have not been
executed here; their presence does not establish a project build contract.

## Public package-registry observation

The public [PyPI `kickmix` release metadata](https://pypi.org/project/kickmix/)
reports version `1.0.0`, author `Qualtran Developers`, homepage
`quantumlib/Qualtran`, and runtime requirement `numpy`; files were uploaded
2026-10-27. PyPI lists a CPython 3.12 manylinux x86_64 wheel with registry
SHA-256 `cc26abcd5efa5e72f373148d5cca2ffa43e158a724e94c213b97622f23c6241a`.
The wheel was not downloaded or installed, so its bytes were not independently
verified here. The release-to-Git-commit mapping was not established. This is
**VERIFIED UPSTREAM registry metadata**, not an official competition compiler,
verifier, or project dependency.

## Local tool availability

Observed on 2026-11-13:

- Available: Python 3.12.3, pip 24.0, g++ 13.3.0, uv 0.12.19, GNU Make
  4.3, Node.js 24.21.0.
- Unavailable: CMake, Bazel, Bazelisk, pytest, pybind11.
- No dependencies were installed.

Tools present on the host are not automatically project dependencies.

## Dependency policy and blockers

- Do not add a package, lockfile, or build tool until a project interface and
  build workflow require it.
- Do not add Qualtran/Kickmix as a runtime dependency merely because the
  competition paper or upstream docs reference it.
- Before any compiler dependency pinning, obtain the approved architecture,
  project-supported Python/compiler versions, build entry point, and policy
  for provenance/hash verification.
- Before benchmark dependencies or optional datasets are added, obtain the
  official verifier and data contracts from the competition owners.

Dependency pinning for the project compiler is **BLOCKED** pending owner
decisions. The current standard-library utility workflow has no third-party
dependency to pin.
