# Phase 5: Toolchain and Build Baseline

**Review date:** 2026-11-19
**Repository HEAD at review start:** `7165220562da2bb34bf2700ee844ad4a312e3b13`

## Evidence labels

**VERIFIED LOCAL FACT** means observed in this checkout/environment.
**VERIFIED UPSTREAM** means observed in the named upstream source or registry,
not adopted here. **UNKNOWN** and **BLOCKED** mark missing evidence.
**ENGINEERING PROPOSAL** is not an external requirement.

## Project toolchain and build

| Item | Observed result |
|---|---|
| Python runtime used for validation | **VERIFIED LOCAL FACT:** CPython 3.12.3, invoked as `python3`. Pylance's workspace interpreter is `/usr/bin/python3`; no other Pylance environment was listed. |
| Project language/build definition | **VERIFIED LOCAL FACT:** The present infrastructure is Python. No project `pyproject.toml`, `setup.py`, `setup.cfg`, Makefile target, or benchmark compiler build definition was found during the audit. |
| Project runtime dependencies | **VERIFIED LOCAL FACT:** The infrastructure uses Python standard-library modules; no project runtime dependency was identified in the inspected dependency inventory. This is not a claim about unavailable official tooling. |
| NumPy in the Pylance-selected environment | **VERIFIED LOCAL FACT:** Not importable/installed in the selected environment according to the terminal probe and Pylance installed-module list. |
| Kickmix PyPI package | **VERIFIED UPSTREAM:** PyPI lists `kickmix` 1.0.0, runtime requirement `numpy`, uploaded 2026-10-27. It is not installed or declared as a project dependency. |
| Kickmix source pin | **VERIFIED UPSTREAM:** The inspected Qualtran commit is `f559b12af459e7e97e6c6c382434431c03b903c9`, dated 2026-11-12. Its exact mapping to the earlier PyPI release is **UNKNOWN**. |
| Compiler/build tools | **VERIFIED LOCAL FACT:** GNU Make 4.3, uv 0.12.19, Node.js v24.22.0, g++ 13.3.0 were observed. Bazel, Bazelisk, CMake, pytest, and pybind11 were not available in the initial environment audit. No project build uses these tools. |
| Benchmark compiler build | **BLOCKED:** No actual competition compiler source or supported build command is present. |

## Commands and results

The current full unit suite passed after the Phase 5 artifact-reference fix:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
Ran 53 tests
OK
```

The focused infrastructure suite also passed after that fix:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p test_compiler_infrastructure.py -v
Ran 40 tests
OK
```

These are local tests only; neither command builds or runs a competition
compiler.

## Reproducibility boundary

**VERIFIED LOCAL FACT:** The tests run with the system CPython and do not install
dependencies. The repository has no declared Python support range, lockfile,
or compiler toolchain pin establishing a cross-machine build.

**ENGINEERING PROPOSAL:** If the project adopts an external compiler or
Kickmix, first obtain owner approval and an authoritative version mapping;
then pin the exact source/package and transitive dependencies, document the
supported interpreter/platform matrix, and add an offline or controlled
integration test. Do not add Kickmix or NumPy to the project dependency set
merely because PyPI publishes the package.

## Import audit limitation

Pylance's `pylanceImports` query returned “No import data” for this workspace.
Its selected interpreter and installed top-level modules were available. The
test suite completed with the project's current imports, but a Pylance-wide
unresolved-import report could not be established. This tooling limitation is
not represented as a clean Pylance audit.

The repo-wide `git diff --check` flags the CRLF line ending on the final bullet
of the pre-existing `README.md` working-tree delta as trailing whitespace.
That protected file's required baseline SHA-256 is unchanged. A targeted scan
of the 14 Phase 5 task files reported no trailing whitespace.
