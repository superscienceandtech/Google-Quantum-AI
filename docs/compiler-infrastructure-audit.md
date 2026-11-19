# Compiler Infrastructure Repository Audit

- **Audit date:** 2026-11-13
- **Repository:** `superscienceandtech/Google-Quantum-AI`
- **Branch / HEAD:** `feat/compiler-infrastructure` /
  `7165220562da2bb34bf2700ee844ad4a312e3b13`
- **Scope:** current checkout, committed implementation, existing Kickmix and
  benchmark dossier, and locally available toolchain.
- **Non-goal:** this audit does not define project architecture, implement
  benchmark adapters, or claim that the official verifier or scorer has been
  tested.

## Evidence labels

- **SOURCE-VERIFIED:** directly observed in this checkout or in the cited
  immutable upstream source.
- **UPSTREAM-DOCUMENTED:** stated in documentation/build metadata for the
  pinned upstream revision; not thereby a project API.
- **PAPER-DERIVED:** stated in the cited competition paper, but not confirmed
  against an executable official verifier.
- **PROPOSED:** a recommendation, not an approved interface or implementation.
- **UNVERIFIED:** evidence is insufficient to confirm the claim.
- **BLOCKED:** requires an authoritative project or competition artifact that
  is not available in this checkout.

## 1. Repository identity and inventory

| Item | Finding |
|---|---|
| Root | `/mnt/d/Google-Quantum-AI` (**SOURCE-VERIFIED**) |
| Branch | `feat/compiler-infrastructure` (**SOURCE-VERIFIED**) |
| HEAD | `7165220562da2bb34bf2700ee844ad4a312e3b13` (**SOURCE-VERIFIED**) |
| Relationship to origin | Local branch is ahead of `origin/feat/compiler-infrastructure` by one commit; no push was performed (**SOURCE-VERIFIED**) |
| Tracked files at HEAD | `README.md`, `tests/test_verify_sha256.py`, `tools/verify_sha256.py` (**SOURCE-VERIFIED**) |
| Worktree changes | `README.md` has its preserved pre-existing unstaged modification. The checker and tests have unstaged Part 2 changes; the dossier and five reports under `docs/` are untracked (**SOURCE-VERIFIED**) |
| README | Modified but not staged; SHA-256 `1cebe91857b4aa99a3121fc41746d7e833e6a98f16f9ed926a42b80134fafc10`. Its pre-existing diff is preserved (**SOURCE-VERIFIED**) |
| Compiler implementation | No compiler, IR, optimizer, benchmark adapter, verifier, or scorer source exists in the committed tree (**SOURCE-VERIFIED**) |

The committed utility was added by commit
`7165220562da2bb34bf2700ee844ad4a312e3b13`, titled
`feat(infrastructure): add SHA-256 artifact verification utility`. Its exact
manifest is `tools/verify_sha256.py` and `tests/test_verify_sha256.py`.

## 2. Source and API inventory

### Local project surfaces

| Surface | Evidence and state |
|---|---|
| `tools/verify_sha256.py` | **SOURCE-VERIFIED / IMPLEMENTED.** A standalone Python CLI validates a supplied SHA-256 digest and hashes regular files in 1 MiB chunks. It does not retrieve artifacts, establish provenance, or parse a circuit. |
| `tests/test_verify_sha256.py` | **SOURCE-VERIFIED / IMPLEMENTED.** Thirteen standard-library `unittest` cases cover known digests, empty and multi-chunk files, digest syntax, CLI outcomes, missing paths, directory/FIFO/symlink rejection, deterministic output, input non-mutation, and path-safe diagnostics. |
| Project compiler API / IR | **BLOCKED.** No project declarations, source, or approved architecture are present in the committed tree. |
| Project serialization / data API | **BLOCKED.** No project serialization code or benchmark data loader is present. |
| Project verification / scoring API | **BLOCKED.** No project or official verifier/scorer implementation is present in the committed tree. |

### Pinned external reference: Qualtran / Kickmix

The existing [Kickmix dossier](kickmix-interface-benchmark-contract-dossier.md)
records the upstream reference as `quantumlib/Qualtran` commit
[`f559b12af459e7e97e6c6c382434431c03b903c9`](https://github.com/quantumlib/Qualtran/tree/f559b12af459e7e97e6c6c382434431c03b903c9).
These are **UPSTREAM-DOCUMENTED** and **SOURCE-VERIFIED** upstream surfaces,
not APIs declared by this project:

| Upstream boundary | Recorded API or source |
|---|---|
| Circuit creation and parsing | `km.Circuit`; `km.Circuit.from_file`; `CircuitBuilder` register/allocation methods; pinned Python binding sources under `kickmix/src/kickmix/py/circuit/` |
| Serialization | `Circuit.to_file` and `Circuit.from_file`; KMX/KMB formats described by `docs/kickmix/kickmix_format.md` and `docs/kickmix/kickmix_binary_format.md`; implementation in `kickmix/src/kickmix/circuit/circuit.cc` and `mutable_circuit.cc` |
| Circuit inspection | `register_data`, `num_qubits`, `num_bits`, `num_registers`, diagrams, and static `operation_statistics` |
| Simulation | `km.Simulator`, `do`, register reads/writes, phase reads/writes, and optional shot-dependent operation statistics |
| Resource statistics | `km.OperationStatistics`; counts are not themselves a complete benchmark score |

The upstream documentation and corresponding source paths, signatures,
serialization behavior, and error notes are detailed in the existing dossier.
Do not treat these upstream APIs as project interfaces or assume every
Kickmix circuit is accepted by the competition verifier.

## 3. Benchmark contract and integration map

The paper cited in the dossier is arXiv `2610.23832v2`. The paper is
**PAPER-DERIVED** semantic evidence, not an executable verifier or complete
data schema. Participant-maintained code is not substituted for official
contracts.

| Track | Available contract evidence | Missing before implementation |
|---|---|---|
| INVSQRT | **PAPER-DERIVED:** inverse-square-root phase, named `"x"` register, preservation/cleanup expectations, phase tolerance, sampling and scoring description. Paper identifies a Qualtran baseline. | Official verifier and salt, immutable competition `.kmb` fixture, canonical serialization/hash rules, and complete verifier invocation are **BLOCKED**. |
| DQI | **PAPER-DERIVED:** Reed–Solomon syndrome/phase semantics, finite-field basis, widths and sampling/resource descriptions. | Official register names, exact wire/bit ordering, input encoding, executable reference package, fixtures and verifier interface are **BLOCKED**. |
| DFTHC-SOS | **PAPER-DERIVED:** address/angle-oracle semantics, register names described by the paper, tree order and verifier sampling description. | Official dataset/container, keys/shapes/dtypes/axes, address data, reference artifacts and verifier interface are **BLOCKED**; an NPZ schema is **UNVERIFIED**. |

No benchmark mathematics, register order, data layout, score, or verifier
behavior is implemented locally.

## 4. Architecture and module boundary assessment

No authoritative project architecture, module map, compiler pipeline,
intermediate representation, register/wire model, build contract, or
integration specification is in the committed tree. This is
**SOURCE-VERIFIED** for the visible checkout and **BLOCKED** as a statement
about any private or separately distributed owner material.

| Boundary | Current status |
|---|---|
| Compiler pipeline and IR | **BLOCKED**; none is declared in this repository. |
| Circuit construction and transformation | **BLOCKED** on approved project API/IR and benchmark semantics. |
| Input/output and register/wire interpretation | **BLOCKED** on authoritative verifier and per-benchmark contracts. |
| Serialization | Upstream KMX/KMB is documented, but its project/competition role beyond paper-described cases is **UNVERIFIED / BLOCKED**. |
| Resource accounting | Kickmix statistics are available upstream; project scoring mapping is **BLOCKED**. |
| Verification/scoring | **BLOCKED** on official implementation and invocation. |
| Error conventions | The utility has its own explicit CLI errors; a project-wide error model is **BLOCKED**. |

The interface map in the Kickmix dossier is explicitly **PROPOSED**. No module
names or IR should be inferred from it.

## 5. Build, dependency, and toolchain findings

### Local project

| Finding | Evidence |
|---|---|
| Build configuration | No `pyproject.toml`, requirements manifest, Makefile, CMake project, Bazel files, or CI workflow exists in the tracked tree (**SOURCE-VERIFIED**). |
| Project dependencies | No project dependency manifest exists. The committed checker and tests import only Python standard-library modules (**SOURCE-VERIFIED**). |
| Project language | The local executable source is Python. No local C++ source is present (**SOURCE-VERIFIED**). |
| Project build command | **BLOCKED / NOT DEFINED**; there is no project build entry point. |
| Test command | `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` is locally executable and covers only the digest utility (**SOURCE-VERIFIED**). |

### Observed local environment

- OS: Linux x86_64 under WSL2.
- Python: 3.12.3; pip: 24.0.
- g++: 13.3.0.
- Available: `uv`, Node.js 24.21.0, Make.
- Not available: CMake, Bazel, Bazelisk, pytest, pybind11.
- No dependencies were installed during this audit.

These are **LOCALLY-OBSERVED** environment facts, not project support
requirements.

### Upstream Kickmix, not this project

The dossier records that the pinned upstream tree selects Bazel 7.2.0, uses
C++20, includes `-march=native`, uses pybind11 2.12.0 in package build
metadata, and declares NumPy as a runtime dependency without a version pin
there. The upstream Python support signals differ between Qualtran
documentation and Kickmix CI; a single explicit Kickmix minimum is
**UNVERIFIED**. None of the upstream build commands was run in this
project checkout.

## 6. Test and reproducibility findings

- **SOURCE-VERIFIED:** the repository has a focused `unittest` suite for the
  checker, not a project-wide compiler/benchmark test framework.
- **LOCALLY-OBSERVED:** the utility suite ran on 2026-11-19 and reported
  `Ran 12 tests` / `OK` (exit 0), including named-pipe and symlink regression
  cases.
- **LOCALLY-OBSERVED:** Python syntax validation using `ast.parse` passed.
- **NOT TESTED:** project build, Kickmix build, circuit simulation,
  serialization round trips, benchmark integration, official verifier, and
  competition scoring.
- The checker reads in bounded chunks and is deterministic for the bytes it
  reads. It does not create artifact outputs.
- A digest match proves equality with the caller-supplied digest only; it does
  not authenticate publisher identity or source provenance.
- The test suite checks a 1.28 MB file, covering multiple 1 MiB reads. The
  implementation opens the path with `O_RDONLY`, `O_CLOEXEC`, `O_NONBLOCK`,
  and, where available, `O_NOFOLLOW`, then validates the retained descriptor
  with `fstat`. This eliminates the prior stat/open replacement window and
  prevents an ordinary FIFO open from waiting indefinitely. Symlinks are
  rejected where `O_NOFOLLOW` is supported. Platform support and
  permission-denied behavior remain platform-dependent.
- The dossier reports upstream `-march=native` and simulator `seed=None` as
  sources of host/environment dependence. The official verifier's salted seed
  cannot be reproduced without the authorized salt and verifier.

## 7. Security and reliability assessment

| Area | Finding |
|---|---|
| Digest input | Exact 64-character hexadecimal validation; uppercase is normalized. Invalid CLI input fails through `argparse`. **SOURCE-VERIFIED.** |
| File access | Binary, read-only open; bounded 1 MiB reads; `OSError` yields an explicit diagnostic and exit code 2. **SOURCE-VERIFIED.** |
| Digest mismatch | Explicit error to stderr and exit code 1; success message is emitted only on match. **SOURCE-VERIFIED.** |
| Input mutation | Tests verify bytes are unchanged after repeated reads. The implementation opens the input read-only. **SOURCE-VERIFIED.** |
| Path semantics | The checker opens with descriptor flags and validates the opened object with `fstat`; platforms supporting `O_NOFOLLOW` reject symlinks. `O_NONBLOCK` prevents ordinary FIFO open from blocking. FIFO and symlink behavior are covered where platform capabilities exist. |
| Integrity limits | The supplied expected hash is not independently authenticated. This checker is not a signature verifier or provenance system. |
| Benchmark inputs | No benchmark loader exists, so no benchmark-specific validation or deserialization claim is made. |
| Shared state | The utility uses local digest state; no mutable global state or random behavior is present. |

The FIFO probe demonstrated one concrete reliability issue and the checker
now rejects ordinary non-regular paths before reading. Full defense against
adversarial path replacement remains outside the utility's documented
contract. Trusted digest acquisition remains a provenance requirement.

### Phase 5/6 worktree implementation snapshot — 2026-11-19

The compiler-neutral proposal in
[`compiler-infrastructure-core.md`](compiler-infrastructure-core.md) adds
descriptor-relative root traversal, exclusive run ID creation, post-execution
input/output integrity checks, and atomic no-overwrite manifest publication.
Its adversarial suite covers concurrent run creation and concurrent manifest
publication. These are local infrastructure contracts, not approved compiler
or competition APIs. The proposal requires POSIX `dir_fd`, `O_NOFOLLOW`, and
`O_DIRECTORY` support and fails closed where unavailable. At this snapshot,
executors and verifiers were in-process and were not sandboxed.

The Phase 5/6 suite contained 53 tests: 13 checksum utility tests and 40
compiler-neutral infrastructure tests. This is utility/infrastructure
coverage only; no competition compiler or benchmark behavior was tested.

### Phase 7 implementation update — 2026-11-19

`SubprocessCompilerExecutor` now runs an explicitly configured argv using a
bounded local JSON protocol, timeout, and structured process failure results.
The new end-to-end workflow test uses a temporary Python test command; it does
not validate a competition compiler or verifier. The suite now contains 62
tests (13 utility and 49 infrastructure tests). This executor is not a
sandbox, and the official compiler, verifier, fixtures, and benchmark
contracts remain unavailable.

## 8. Implementation gaps and priorities

| Priority | Task | Status / prerequisite |
|---|---|---|
| P0 | Obtain the approved technical architecture (module boundaries, pipeline, IR, register/wire semantics, error policy, determinism and integration contracts) from the project owner. | **BLOCKED**; do not infer architecture from Kickmix or the paper. |
| P0 | Obtain immutable official verifier/scorer release, invocation, submission format, fixtures, and authorized benchmark data. | **BLOCKED**; the dossier records a public Kaggle file-list HTTP 401 as an access limitation, not evidence that artifacts do not exist. |
| P1 | Establish and reproduce the project baseline build/test workflow using the approved architecture and toolchain. | **BLOCKED** until a real project build entry point and dependency choices are supplied. |
| P1 | Document and pin dependencies/toolchain with provenance after owner/toolchain approval. | **PROPOSED / BLOCKED**; do not add dependencies speculatively. |
| P2 | Implement serialization and integration tests against confirmed project/competition interfaces. | **BLOCKED** on submission and verifier contracts. |
| P2 | Implement benchmark-specific loaders/adapters independently for INVSQRT, DQI and DFTHC-SOS. | **BLOCKED** on authoritative schemas, register semantics, fixtures, and verifier. |
| Complete | Preserve and maintain the standalone SHA-256 checker with its focused tests. | Implemented and utility-tested; not a compiler or competition artifact workflow. |

### First safe implementation task

The architecture-independent artifact digest checker was implemented in
commit `7165220562da2bb34bf2700ee844ad4a312e3b13`. During this audit a bounded
FIFO probe found that opening a named pipe could wait indefinitely; the
checker now rejects non-regular paths and the 11-test suite covers this case.
This was a focused safe-file-handling improvement. At the end of Phase 5, no
additional compiler-facing implementation was justified by the available
project contracts. Phase 7 later added a generic subprocess executor without
claiming a competition compiler; the remaining integration tasks are blocked
until the owner supplies the project entry point, architecture, and toolchain
decision.

## 9. Commands executed for this audit

```text
pwd
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short --branch
git ls-files
git ls-files --others --exclude-standard
git show --stat --oneline --decorate --no-renames HEAD
git diff -- README.md
sha256sum README.md
python3 --version
python3 -m pip --version
g++ --version | sed -n '1p'
command -v uv
command -v cmake
command -v bazel
command -v bazelisk
command -v pytest
python3 -m pip show pybind11
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 -B -c 'import ast, pathlib; paths=("tools/verify_sha256.py", "tests/test_verify_sha256.py"); [ast.parse(pathlib.Path(path).read_text()) for path in paths]; print("Syntax OK:", ", ".join(paths))'
git ls-tree -r --name-only HEAD
```

Test result: 12 tests passed; the unittest command exited 0. Syntax validation
exited 0. The FIFO regression test was run as part of the suite. No
dependencies were installed. No commit, push, merge, or staging was performed
as part of this audit.
