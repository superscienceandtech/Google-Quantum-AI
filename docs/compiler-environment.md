# Compiler Infrastructure Environment

- **Updated:** 2026-11-19
- **Current project snapshot:** branch `feat/compiler-infrastructure`,
  commit `7165220562da2bb34bf2700ee844ad4a312e3b13`
- **Status:** records verified utility and generic infrastructure workflows.
  It is not a build guide for a competition compiler or benchmarks.

## Evidence and scope

- **VERIFIED LOCALLY:** observations and commands actually run in this
  checkout.
- **UPSTREAM-DOCUMENTED:** requirements found in the pinned Qualtran/Kickmix
  documentation; these are not project requirements.
- **PROPOSED:** a useful workflow not yet approved or validated for a
  compiler/benchmark project entry point.
- **BLOCKED / UNVERIFIED:** unavailable or not established by the current
  repository.

The committed project has a Python SHA-256 utility and a standard-library
`unittest` suite. The current worktree additionally contains a compiler-neutral
infrastructure proposal with injected executor/verifier protocols and a local
subprocess executor; it is not a project compiler, circuit runtime, official
verifier, or benchmark execution entry point (**VERIFIED LOCALLY / PROPOSED
INTERFACE**).

## Observed environment

Environment recorded during the audit:

| Component | Observed value | Status |
|---|---|---|
| OS | Linux x86_64 under WSL2 | **VERIFIED LOCALLY** |
| Python | CPython 3.12.3 | **VERIFIED LOCALLY** |
| pip | 24.0 | **VERIFIED LOCALLY** |
| g++ | 13.3.0 | **VERIFIED LOCALLY**; not used by the local project |
| uv | 0.12.19 | **VERIFIED LOCALLY**; not required by the local project |
| Make | GNU Make 4.3 | **VERIFIED LOCALLY**; no project Makefile |
| Node.js | 24.21.0 | **VERIFIED LOCALLY**; not used by the local project |
| CMake | unavailable | **VERIFIED LOCALLY** |
| Bazel / Bazelisk | unavailable | **VERIFIED LOCALLY** |
| pytest | unavailable | **VERIFIED LOCALLY**; project tests use `unittest` |
| pybind11 | unavailable in the checked Python environment | **VERIFIED LOCALLY**; no local binding code |

These observations describe one environment and do not establish a supported
platform matrix.

## Reproduce the standalone utility tests

From the repository root, using Python 3.8+ on a POSIX platform supporting
`dir_fd`, `O_NOFOLLOW`, and `O_DIRECTORY`:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

The historical Phase 7 observed result in this environment was exit status 0,
`Ran 62 tests`, `OK`. The current Phase 7.2 continuation run on 2026-11-19 observed exit status 0,
`Ran 84 tests`, `OK`, using:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Tests cover the digest utility, compiler-neutral lifecycle, and subprocess
workflows using temporary Python commands and test-double verifiers. These are
not competition compiler, Kickmix, benchmark, official verifier, or scoring
tests. The default process backend requires POSIX process-group support;
alternative lifecycle backends can be injected, but their declared
containment guarantees are not independently validated by this infrastructure.

Check Python syntax without writing bytecode:

```sh
python3 -B -c 'import ast, pathlib; paths=("tools/verify_sha256.py", "tests/test_verify_sha256.py", "tools/compiler_infrastructure.py", "tests/test_compiler_infrastructure.py"); [ast.parse(pathlib.Path(path).read_text(), filename=path) for path in paths]; print("Syntax OK:", ", ".join(paths))'
```

Observed result: exit status 0; all four listed files parsed successfully. The utility
can be invoked from the repository root as:

```sh
python3 tools/verify_sha256.py PATH EXPECTED_SHA256
```

`EXPECTED_SHA256` must be exactly 64 hexadecimal characters. `PATH` must refer
to a regular file according to descriptor-based `fstat` validation after
`os.open`; named pipes and directories are rejected rather than read. Where
`os.O_NOFOLLOW` is supported, symlinks are rejected instead of followed.
Exit status 0 means the bytes read from `PATH` match that supplied digest;
1 means mismatch; 2 indicates file access or non-regular-path failure.
Argparse exits nonzero for invalid CLI arguments. A
successful check does not authenticate the expected digest or the file
publisher.

## Environment safety and limits

- No dependencies were installed during the audit.
- Tests use `tempfile` and clean up their own temporary directories.
- `PYTHONDONTWRITEBYTECODE=1` prevents test bytecode output; the syntax command
  uses `-B`.
- Input files are opened read-only by the utility. It does not create output
  artifacts.
- Permission errors and every platform's path behavior have not been
  comprehensively tested. `O_NOFOLLOW` support is platform-specific. An open
  descriptor is retained for validation and reading, eliminating the prior
  stat/open path replacement window. Platforms that do not provide
  `O_NOFOLLOW` may follow a symlink; descriptor `fstat` then validates the
  opened object but cannot establish that the caller named it directly.
- The project has no documented minimum Python version. The utility syntax
  uses the assignment expression introduced in Python 3.8; compatibility with
  older Python versions is not claimed.

## Upstream-only build notes

The existing dossier records upstream Kickmix build instructions for
Qualtran commit `f559b12af459e7e97e6c6c382434431c03b903c9`, including Bazel
7.2.0, C++20, pybind11 development dependencies, pytest, and upstream build
and test commands. Those commands have **not** been run in this project
checkout and are not project setup instructions.

The infrastructure artifact store currently fails closed if those filesystem
capabilities are missing; it has not been validated on Windows or non-POSIX
filesystems. There is no approved compiler toolchain or project build entry point yet.
Creating project install/build steps before that owner decision would be
speculative. A clean-checkout compiler/benchmark workflow is therefore
**BLOCKED**.
