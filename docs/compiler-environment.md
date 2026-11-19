# Compiler Infrastructure Environment

- **Updated:** 2026-11-19
- **Current project snapshot:** branch `feat/compiler-infrastructure`,
  commit `6c63c152972bd2e920ed72514dbb9bb7e4e1d6dd`
- **Status:** records verified utility, generic infrastructure, and local KMX
  workflows.
  It is not a build guide for a competition compiler or benchmarks.

## Evidence and scope

This document uses the audit taxonomy: **VERIFIED LOCALLY**,
**VERIFIED UPSTREAM**, **VERIFIED OFFICIAL**, **PAPER-DERIVED**,
**ENGINEERING PROPOSAL**, **BLOCKED**, and **UNKNOWN**. Upstream requirements
do not establish project requirements.

The committed project has a Python SHA-256 utility and a standard-library
`unittest` suite. The current worktree additionally contains a locally
implemented KMX parser/optimizer and a global score aggregation helper; these
do not establish official benchmark behavior. It also contains a
compiler-neutral infrastructure proposal with injected executor/verifier
protocols and a local subprocess executor (**VERIFIED LOCALLY**;
**ENGINEERING PROPOSAL** interface). No official verifier or benchmark
execution entry point is available (**BLOCKED**).

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

From the repository root, using Python 3.10+ for the full local worktree on a
POSIX platform supporting `dir_fd`, `O_NOFOLLOW`, and `O_DIRECTORY`:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

The historical Phase 7 observed result in this environment was exit status 0,
`Ran 62 tests`, `OK`. The current Phase 7.2 continuation run on 2026-11-19 observed exit status 0,
`Ran 84 tests`, `OK`, using:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

The final infrastructure/KMX audit run on 2026-11-19 observed exit status 0,
`Ran 111 tests`, `OK`. Focused runs also passed: KMX compiler/optimizer
(`19` tests), artifact lifecycle/security (`76` tests), and scoring aggregation
(`3` tests). These results are **VERIFIED LOCALLY**, not upstream differential
or official benchmark validation.

Tests cover the digest utility, compiler-neutral lifecycle, local KMX parser
and optimizer, score aggregation, and subprocess workflows using temporary
Python commands and test-double verifiers. These are not upstream differential
Kickmix, benchmark, official verifier, or full scorer tests. The default
process backend requires POSIX process-group support;
alternative lifecycle backends can be injected, but their declared
containment guarantees are not independently validated by this infrastructure.
The KMX module CLI help and a representative compile in temporary files also
completed successfully; output was verified byte-for-byte and its JSON
provenance parsed successfully (**VERIFIED LOCALLY**).

Check Python syntax without writing bytecode:

```sh
python3 -B -c 'import ast,pathlib; paths=sorted(pathlib.Path("tools").glob("*.py"))+sorted(pathlib.Path("tests").glob("*.py")); [ast.parse(path.read_text(encoding="utf-8"), filename=str(path)) for path in paths]; print(f"AST syntax OK: {len(paths)} Python files")'
```

Observed result: exit status 0; all nine local Python source/test files parsed
successfully. The utility
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
- The full local worktree uses Python 3.10+ annotation syntax. This is a local
  syntax requirement, not an approved project support matrix; the supported
  project interpreter remains **UNKNOWN**.
- Input files are opened read-only by the utility. It does not create output
  artifacts.
- Permission errors and every platform's path behavior have not been
  comprehensively tested. `O_NOFOLLOW` support is platform-specific. An open
  descriptor is retained for validation and reading, eliminating the prior
  stat/open path replacement window. Platforms that do not provide
  `O_NOFOLLOW` may follow a symlink; descriptor `fstat` then validates the
  opened object but cannot establish that the caller named it directly.
The project has no approved minimum Python version. Compatibility with
interpreters older than Python 3.10 is not claimed for the current full
worktree.

Print the observed interpreter and platform metadata:

```sh
python3 -c 'import platform,sys; print("executable="+sys.executable); print("implementation="+platform.python_implementation()); print("python_version="+platform.python_version()); print("platform="+sys.platform); print("architecture="+platform.machine())'
```

Observed result in this audit: `/usr/bin/python3`, CPython 3.12.3, `linux`,
`x86_64` (**VERIFIED LOCALLY**). This reports the current process environment;
it does not certify a supported runtime matrix.

## VERIFIED UPSTREAM build notes

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
