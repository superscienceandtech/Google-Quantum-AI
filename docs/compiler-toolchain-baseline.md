# Compiler Toolchain Baseline Discovery

- **Updated:** 2026-11-19
- **Status:** no project compiler toolchain or build baseline is defined.

## Evidence labels

- **VERIFIED OFFICIAL** — direct official source, only for the content
  actually observed.
- **VERIFIED UPSTREAM** — pinned Qualtran/Kickmix documentation only.
- **PAPER-DERIVED** — paper statements, not project toolchain requirements.
- **PARTICIPANT-MIRROR** — participant source, not a project authority.
- **LOCAL OBSERVATION** — observed tool or command in this environment.
- **ENGINEERING PROPOSAL** — local infrastructure/test workflow.
- **UNVERIFIED ASSUMPTION / BLOCKED** — not established for this project.

## Project-owned requirements

The tracked project contains no `pyproject.toml`, requirements file, lockfile,
Makefile, CMake project, Bazel configuration, CI workflow, or native source.
No project-supported OS, Python version, compiler version, build command, or
runtime command is declared. The utility's assignment expression implies
Python 3.8+ syntax compatibility, but this is not an approved support policy.

The local Python utility and compiler-neutral proposal use the standard
library plus the local `tools` package; no third-party dependency is declared.
No package was installed during this discovery.

## Observed environment (2026-11-19)

| Tool / environment | Observed value | Project requirement? |
|---|---|---|
| OS | Linux x86_64 under WSL | No support matrix is declared. |
| Python | CPython 3.12.3 | Used for local tests only; supported project version is **BLOCKED**. |
| pip | 24.0 | Not required by the local test command. |
| g++ | 13.3.0 | Present but unused by project code. |
| Bazel / Bazelisk | Unavailable | No project Bazel files. |
| CMake | Unavailable | No project CMake files. |
| Make | Available | No project Makefile. |
| pytest | Unavailable | Local tests use `unittest`. |
| pybind11 | Not installed | No local binding source. |
| Node.js / uv | Available | No local project use or requirement. |

These observations describe one host, not a supported platform matrix.

## Confirmed local validation

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Observed on 2026-11-19: exit 0, 52 tests passed. These are checksum utility
tests and infrastructure tests using explicit test doubles.

```sh
python3 -B -c 'import ast, pathlib; paths=("tools/verify_sha256.py", "tests/test_verify_sha256.py", "tools/compiler_infrastructure.py", "tests/test_compiler_infrastructure.py"); [ast.parse(pathlib.Path(path).read_text(), filename=path) for path in paths]; print("Syntax OK:", ", ".join(paths))'
```

Observed: exit 0. No project build or compiler execution command exists to run.

## Upstream-only Kickmix requirements

At pinned upstream Qualtran commit
`f559b12af459e7e97e6c6c382434431c03b903c9`, Kickmix documentation/configuration
records Bazel 7.2.0, C++20, pybind11 2.12.0 in package build requirements,
`pybind11_bazel` 2.11.1 in Bazel metadata, NumPy as a runtime dependency
without a pin in the cited build metadata, and pytest for upstream tests. The
broader Qualtran documentation and Kickmix CI provide differing Python
support signals. These are **VERIFIED UPSTREAM**, not project requirements.
No upstream build was run here.

Upstream `-march=native` is a portability/reproducibility consideration. It
does not establish the compiler flags or reproducibility policy for this
project.

## Blockers

The project owner must provide the actual compiler source/package, supported
toolchain, dependency policy, reproducible build instructions, and test
fixtures. Do not copy upstream dependency pins or build commands into project
configuration without approval. See the [dependency inventory](compiler-dependencies.md)
and [entry-point discovery](compiler-entrypoint-contract.md).
