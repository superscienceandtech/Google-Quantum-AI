# INVSQRT P012 Circuit Backend Readiness Report

## 1. Executive summary

**P012 execution:** `IMPLEMENTED`
**Circuit-level audit readiness:** `PARTIALLY_READY` for static inspection of a
hash-pinned public mirror; `BLOCKED` for execution or optimization.
**Overall backend readiness:** `BLOCKED`.

The checkout contains a fail-closed artifact/readiness inventory and backend
interfaces, but no local INVSQRT circuit, sample submission, Kickmix runtime,
resource backend, or official verifier. The active Python environment cannot
import Kickmix. Consequently, no circuit was imported, built, simulated,
measured, or officially verified.

The previously pinned `qarena-ai/invsqrt` mirror was fetched again at its
immutable commit. Its reference-circuit and verifier bytes match the P008/P009
SHA-256 values, and their source was inspected without installing packages or
writing mirror files into the repository. This supports a **mirror-qualified
static source analysis only**. It does not authenticate competition
provenance. No register reduction, arithmetic change, official acceptance,
circuit equivalence, or resource/score result is claimed.

No P007–P011 source, test, or report was changed. P012 adds this report and a
README link only; no dependency or production readiness interface was changed.

## 2. Repository and environment snapshot

| Item | P012 initial observation |
|---|---|
| Repository root | `D:\PROJECT\Quantum_AI\Google-Quantum-AI` |
| Branch | `feat/invsqrt-optimization` |
| HEAD | `5391b2e7123484efacffc0588f5e761e67b5cb55` |
| Staged changes | None |
| Tracked changes | `README.md` was already modified before P012 |
| Ignored data | Existing `.pytest_cache/` was present and preserved |
| Python | CPython 3.14.6, Anaconda build, Windows 11 AMD64 |
| Project Python floor | `>=3.10` in `pyproject.toml` |
| Installed relevant packages | `numpy 2.4.6`; `pytest 9.0.3`; `setuptools` is the declared build dependency |
| Kickmix | Distribution not installed; `find_spec("kickmix")` returned `None`; direct `import kickmix` raised `ModuleNotFoundError` |
| Other checked SDKs | `cirq`, `qiskit`, `pytket`, and `stim` not installed/importable |

The initial `git status --short --untracked-files=all` showed the modified
README and pre-existing untracked P002–P011 work: six research documents
(P006–P011), `pyproject.toml`, the `src/invsqrt_opt/` package and its
`candidates/` implementation, eight test files, and generated `.pyc` files
under `src/invsqrt_opt/`, `src/invsqrt_opt/candidates/`, and `tests/`. The
untracked project files included the P007 reference, P008/P009 fixed-point
implementation, P010 candidate register, and P011 analyzer/report. No
`external/` directory was present. P012 preserved that state and did not stage,
delete, or replace existing work.

Dependency configuration was inspected in `pyproject.toml`: only
`setuptools>=68` is required for builds and `pytest>=7` is an optional test
dependency. Kickmix, NumPy, a compiler, and a simulator are not declared
project dependencies. No package was installed or upgraded.

## 3. P011 findings relevant to circuit-level analysis

P011's full-domain scalar-model scan covered 3,133,452 inputs and recorded no
mismatches in six internal reconstruction checks. Some scalar values had
unused upper bits. P011 explicitly did **not** establish circuit wire ranges,
carry states, modular overflow behavior, physical allocations, uncomputation,
or width savings. Its measured ranges are therefore leads for a later source
audit, not evidence for a circuit edit.

The P011 report and analyzer are unchanged. P012 compares the scalar stages
with declarations visible in the pinned mirror source, but does not equate
scalar register values with quantum-wire or gate-level intermediate states.

## 4. Artifact inventory and provenance

The classifications below distinguish official provenance from the pinned
public mirror. “External” means fetched from the immutable remote reference;
no mirror artifact was copied into or tracked by this checkout.

| Logical role | Exact path / source | Availability and readability | SHA-256 / version | Tracking / provenance | Compatibility and verification |
|---|---|---|---|---|---|
| Canonical official reference circuit | `external/verifiers/invsqrt/nr_reference_circuit.py` | `NOT_AVAILABLE` locally | None | Missing local path; no official source identity established | Import and execution `NOT_TESTED` |
| Pinned-mirror reference circuit | [`nr_reference_circuit.py`](https://github.com/qarena-ai/invsqrt/blob/6ac78ec5ace6dfd5831ccac2547041408f5d8278/verifiers/invsqrt/nr_reference_circuit.py) | `PARTIALLY_READY`; fetched as readable UTF-8 source for static inspection | `bb90330dcf774f7b502de471293facba67f27952cc8808fe4a9970a9b1322e23`; commit `6ac78ec5ace6dfd5831ccac2547041408f5d8278` | External, not Git-tracked here; `PINNED_PUBLIC_MIRROR`, not `OFFICIAL_VERIFIED` | SHA-256 recomputed from raw bytes and matched; import `NOT_AVAILABLE` because Kickmix is missing |
| Canonical official verifier | `external/verifiers/invsqrt/verify_submission_invsqrt.py` | `NOT_AVAILABLE` locally | None | Missing local path; no official source identity established | Execution `NOT_TESTED` |
| Pinned-mirror verifier | [`verify_submission_invsqrt.py`](https://github.com/qarena-ai/invsqrt/blob/6ac78ec5ace6dfd5831ccac2547041408f5d8278/verifiers/invsqrt/verify_submission_invsqrt.py) | `PARTIALLY_READY`; fetched as readable UTF-8 source for static inspection | `ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a`; same commit | External, not Git-tracked here; `PINNED_PUBLIC_MIRROR`, not `OFFICIAL_VERIFIED` | SHA-256 recomputed from raw bytes and matched; verifier execution `NOT_TESTED` |
| Official sample submission | `external/sample_submission/invsqrt.kmb` | `NOT_AVAILABLE`; path absent | None | No local artifact or version | Loading and compatibility `NOT_TESTED` |
| Kickmix distribution/library and source | `external/kickmix/kickmix.so`; Python import name `kickmix` | `NOT_AVAILABLE`; local path absent, distribution absent, module unimportable | No version or hash available | No local package/source provenance | API compatibility `NOT_TESTED` |
| Compiler and simulator | Kickmix API referenced by the mirror source | `NOT_AVAILABLE` in this environment because Kickmix is absent | No version | No installed compiler/simulator package identified | No SDK symbols could be imported or executed |
| Circuit-specific helpers | Helpers embedded in the pinned-mirror reference source | `PARTIALLY_READY` for static source reading only | Covered by reference-source hash above | Mirror-qualified | Actual helper execution `NOT_TESTED` |

The reference source imports `kickmix as km` and `numpy as np` (source lines
33–34). NumPy 2.4.6 is installed, but this does not supply the missing
`CircuitBuilder`, circuit, or simulator API. The verifier likewise imports
Kickmix; its source cannot execute here.

The existing artifact manifest independently reported the expected local
reference-circuit, verifier, sample-submission, and Kickmix paths as `MISSING`,
with no hashes. Its SDK inventory reported `import_available=false`,
`version=null`, and `api_status=UNKNOWN`. These records are local path and
environment evidence, not official provenance evidence.

### Mirror provenance and verification method

P009 established the immutable mirror commit and expected hashes. P012 fetched
only the two exact raw files from that commit, recomputed SHA-256 from response
bytes in memory, and observed exact matches and expected byte lengths:

- Reference circuit: 18,862 bytes; SHA-256
  `bb90330dcf774f7b502de471293facba67f27952cc8808fe4a9970a9b1322e23`.
- Verifier: 17,210 bytes; SHA-256
  `ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a`.

This proves identity with the pinned mirror bytes, not identity with a
competition-distributed artifact. The mirror's competition-origin statement
remains unauthenticated by an official archive, signature, or other
independent primary evidence.

## 5. Kickmix and dependency compatibility

| Check | Result |
|---|---|
| Active Python version | 3.14.6 |
| Kickmix distribution/version | `NOT_AVAILABLE`; no installed distribution/version |
| `find_spec("kickmix")` | No module specification |
| Actual import smoke test | `NOT_AVAILABLE`; `ModuleNotFoundError: No module named 'kickmix'` |
| Circuit builder symbols (`km.CircuitBuilder`, `km.q`, `km.array`) | `NOT_TESTED`; package cannot be imported |
| Circuit simulator (`km.Simulator`) | `NOT_TESTED`; package cannot be imported |
| NumPy dependency | Available as 2.4.6; mirror source model imports NumPy |
| Compiler executable lookup | No `kickmix`, `cmake`, or `qir-compiler` executable found by `shutil.which`; this lookup does not prove that no compiler exists elsewhere |
| Reference source import/construction | `NOT_AVAILABLE`; import is blocked by missing Kickmix |
| Resource extraction | `NOT_TESTED`; no circuit instance or resource counter is available |

No compatibility conclusion is inferred from documentation or the fact that
NumPy is installed. No guessed API adapter, package installation, or substitute
compiler/simulator was used.

## 6. Reference-circuit import and construction results

- Static source retrieval and parsing by line inspection: `PARTIALLY_READY`
  for the pinned public mirror.
- Import of the reference module: `NOT_AVAILABLE` because its top-level
  `import kickmix as km` fails in this environment.
- `build_nr_circuit(...)` invocation: `NOT_TESTED`; construction cannot begin
  without the imported Kickmix API.
- Circuit serialization to `.kmb`/`.kmx`: `NOT_TESTED`.
- Sample-submission loading: `NOT_AVAILABLE`; no sample file is present.
- Resource extraction from a constructed circuit: `NOT_TESTED`.
- Official verifier execution: `NOT_TESTED`; canonical verifier unavailable,
  and the mirror verifier was inspected but deliberately not executed.

The mirror's reference source declares `build_nr_circuit` at lines 351–377.
Its `main` writes the circuit and prints operation statistics at lines
380–397. These are source-level entry points only; neither was called.

## 7. Backend capability assessment

The repository already has an artifact manifest, SDK inventory, adapter
readiness assessment, circuit artifact adapter, fail-closed unavailable
backend, and verifier availability/result interfaces:

- `ArtifactManifest` / `ArtifactRecord` record local availability, readability,
  hash, tracking, provenance, version, and compatibility state.
- `SDKInventory` separates import availability, version, and API status.
- `AdapterReadiness` records artifact availability, SDK import/API state, and
  explicit blockers.
- `UnavailableCircuitArtifactAdapter`, `UnavailableKickmixBackend`, and
  `UnavailableVerifierAdapter` return unavailable/not-started states rather
  than success-shaped measurements or verification.
- Backend operation statuses and verifier execution/verification statuses
  distinguish unavailable, unexecuted, failed, and completed operations.

The current overall `AdapterReadiness.status` is intentionally coarse
(`READY`/`BLOCKED`). The P012 report supplies a per-capability matrix using
`READY`, `PARTIALLY_READY`, `BLOCKED`, `NOT_AVAILABLE`, `NOT_TESTED`, and
`NOT_MEASURED`, while reusing the existing manifest and fail-closed adapter
results as evidence. No production interface extension was necessary for this
documentation-only readiness assessment; adding a duplicate readiness API
would not make the absent SDK or artifacts more testable.

Observed adapter result: `BLOCKED`, `ready=false`; blockers include missing
official verifier, reference circuit, sample submission, non-importable
Kickmix, unconfirmed Kickmix APIs, and no production circuit/resource adapter.
The generic backend reports `available=false`. Circuit construction and
resource measurement are not represented as successful operations.

## 8. Circuit-level arithmetic inspection findings

The following are source-level observations from the pinned mirror only.
They are not authenticated official-artifact facts and were not reproduced by
executing the circuit.

| Stage | Mirror source evidence | Declared widths / behavior visible in source |
|---|---|---|
| Input | `build_nr_circuit`, lines 351–366; verifier register validation, lines 180–194 | `x` has `2*n_p+2 = 22` qubits at `n_p=10`; verifier source expects little-endian distinct qubits |
| Normalization | `_flag_zero_pair`, `_normalize`; `_compute_y1`, lines 297–340 | `flags` has `n_p = 10` bits; pair-zero controls normalize `x` in place |
| Interval selection | `_select_interval`, `_load_coefficients` | Three selector bits; top normalized bits select one of four coefficient cases |
| Coefficients / polynomial | `_load_coefficients`, `_horner`, `_add_row` | Four coefficient arrays of `coef_bits = 17`; `delta_bits = 14`; Horner stages update the coefficient/intermediate arrays |
| Row product / accumulation | `_add_row`, lines 150–167 | Controlled terms are ANDed into shared scratch, added/subtracted into a target slice, then ANDs are deleted by measurement-based uncomputation; fixed-width addition/subtraction API semantics were not run here |
| Square | `_square` | `square_bits = 28`; diagonal bit terms and doubled cross terms form the square |
| Mantissa product | `_multiply_m` | `z` array has `product_bits + 2 = 30` bits |
| Newton correction | `_correct` | In-place complement/constant addition or subtraction on the 30-bit `z` register; actual overflow/wrap behavior not executed |
| Newton product | `_multiply_y0` | Product target is the first 30 bits of `y1` (`p`); `result_bits + 1 = 30` |
| Denormalization | `_denormalize` | `y1` has `output_bits = result_bits + n_p + 1 = 40` bits, controlled by the 10 flags |
| Phase preparation | `_phase_by_bits`, lines 343–349 | One `Z_POW` operation is requested per output bit; no phase gate was executed |
| Scratch | `build_nr_circuit`, lines 365–376 | `scratch` allocation is `max(square_bits, product_bits+2, result_bits+1) = 30` bits |
| Compute/uncompute and cleanup | `_compute_y1`, lines 297–340; `build_nr_circuit`, lines 370–376 | Forward stages are followed by phase and reverse stages; non-`x` registers are freed after inverse computation in the full-circuit path |

The source's reverse path applies denormalization, Newton multiply,
correction, mantissa multiply, square, Horner, coefficient unload, interval
unselection, and normalization in reverse order. `_add_row` describes
measurement-based AND cleanup, and the verifier source checks each simulated
shot for restored `x` and all-zero scratch. These source-level descriptions do
not establish Kickmix execution semantics, every measurement outcome, or
successful restoration in this checkout.

No circuit register declarations were found locally: the widths above belong
to the pinned mirror source. P011's range values remain scalar-model values.
No actual gate-level intermediate states, resource counts, or ancillary
lifetimes were measured.

## 9. Register and ancilla audit readiness matrix

| Audit target | Static mirror evidence | Local execution / width confidence | Status |
|---|---|---|---|
| 22-bit input and endianness | Source plus verifier register checks | No circuit loaded; provenance mirror-qualified | `PARTIALLY_READY` |
| Normalization flags and controlled shifts | 10-bit flag allocation and named stage | No gate/state execution | `PARTIALLY_READY` |
| Interval selector and four-case coefficient table | 3 selector bits; four 17-bit coefficient arrays | Source-readable; no imported module/QROM inspection | `PARTIALLY_READY` |
| Delta/Horner row widths and truncation | 14-bit precision and 17-bit arrays; row helper text | Carry/wrap/API semantics not executed | `PARTIALLY_READY` |
| Square and multiplier intermediates | 28-bit square, 30-bit `z`, 30-bit `p` | No gate-level intermediate or carry trace | `PARTIALLY_READY` |
| Correction and denormalization | 30-bit correction path; 40-bit output | No circuit-state validation | `PARTIALLY_READY` |
| Phase numerator/rotation preparation | 40 output bits and per-bit phase source | No phase simulation or comparator execution | `PARTIALLY_READY` |
| Scratch/ancilla allocation and sharing | 30-bit named scratch allocation; row helper uses it | No actual peak allocation/statistics, lifetime, or ancilla trace | `PARTIALLY_READY` |
| Measurement-based uncomputation | Source calls `init_and` / `del_and`; verifier checks scratch per shot | Kickmix API and branches not executable | `BLOCKED` |
| Input restoration and scratch cleanup | Reverse source sequence and verifier assertions | No circuit or verifier execution | `BLOCKED` |
| Official verifier and acceptance | Pinned mirror source only; canonical path absent | No official provenance or run | `NOT_AVAILABLE` |

The mirror's declared arrays expose a useful *source inspection hypothesis*,
but their bits cannot be substituted for P011's scalar ranges or for measured
qubit/resource counts. No reduction was selected or implemented.

## 10. Exact blockers and missing evidence

1. **Canonical provenance:** the local checkout lacks an official distribution
   archive or authenticated artifact manifest. Mirror hashes establish the
   pinned mirror bytes only. Obtain an official archive/signature or another
   independently authoritative identity to resolve this blocker. It blocks
   official claims and provenance-bound optimization.
2. **Kickmix runtime and version:** no distribution, import, binary, or version
   is available. Provide the project-authorized compatible runtime and
   version/hash, then confirm required APIs. It blocks module import,
   construction, simulation, and resource extraction.
3. **Circuit fixture/sample:** no `.kmb` sample or locally available reference
   circuit exists. Obtain a provenance-bound artifact and inspect it using the
   supported runtime. It blocks reference-circuit loading and direct
   stage/state comparisons.
4. **Official verifier execution:** the canonical verifier is absent and the
   public mirror is not independently authenticated. Obtain the canonical
   verifier and execution dependencies, then run only under the applicable
   authorization. It blocks official acceptance and phase-compliance claims.
5. **Circuit semantics:** actual fixed-width `iadd`/`isub`, `init_and` /
   `del_and`, operation ordering, measurement branches, and cleanup have not
   been executed. Runtime-supported state traces and all required verifier
   outcomes are needed. This blocks circuit equivalence, ancilla-cleanliness,
   and any width change.
6. **Resource counter:** there is no constructed circuit or confirmed
   counter. A provenance-bound circuit plus the official/runtime resource
   extraction path is required. Qubit, Toffoli, T, depth, and score are
   `NOT_MEASURED`.

## 11. Proposed circuit-level audit procedure

This is a future test plan, not work executed in P012.

1. Acquire the canonical reference circuit, verifier, and sample submission
   from an authoritative source. Record origin, version/commit, exact paths,
   file hashes, tracking location, license/source notice, and authentication
   evidence. Keep mirror and canonical files distinct.
2. Obtain approval and the project-supported Kickmix runtime. Record Python,
   distribution/binary hashes, version, import names, required API symbols,
   compiler/simulator versions, and exact environment. Do not install an
   unapproved package.
3. Import the canonical reference in a clean environment and run a minimal
   read-only circuit construction smoke test. Capture construction output and
   register metadata; do not infer a production resource result from a
   smoke-test object.
4. Compare the circuit's actual register declarations with the static
   source-width matrix: `x`, normalization flags, selectors, coefficient and
   Horner registers, square, `z`, `p`, `y1`, scratch, and any unnamed
   ancillas. Identify which widths are declared by source/API and which are
   inferred.
5. Trace each stage on boundary and adversarial inputs: domain endpoints,
   powers of two and neighboring inputs, normalization-pair transitions,
   all interval boundaries and neighboring values, row-truncation
   thresholds, carry boundaries, and maximum scalar-range inputs. Compare
   circuit-stage integers against the unchanged P008 model without altering
   its precision or semantics.
6. Establish fixed-width behavior directly: operand order, target slice,
   carry-out, overflow/wrap, truncation direction, coefficient encoding,
   subtraction representation, and whether intermediate overflow is possible
   on every valid input. A scalar fit result is not a substitute for this
   trace.
7. Exercise compute, phase, and inverse paths, including every relevant
   measurement-based uncompute result supported by the runtime. Check that
   `x` is restored, every scratch/ancilla is `|0>`, and no unwanted relative
   or global phase changes violate the contract.
8. Run the authenticated official verifier on its full required domain and
   shot protocol; retain verifier hash, circuit hash, command, environment,
   logs, seed/salt, and all per-input failure evidence.
9. Only after correctness and cleanup pass, measure actual resources from the
   same circuit artifact using the verified counter. Keep measured output
   separate from source-declared widths and static estimates.
10. Any later single-register-width experiment requires a separate candidate,
    a circuit-level proof of carry/truncation/restoration semantics, complete
    phase verification, and same-artifact resource comparison. P012 does not
    authorize or implement it.

## 12. Safety and correctness requirements

- Preserve the 22-bit input domain and bit ordering; require exact input
  restoration.
- Require every unnamed scratch/work qubit to return to zero for all
  supported measurement outcomes.
- Establish actual QROM/coefficient words, sign handling, selector boundaries,
  row truncation, carry, subtraction, overflow, and fixed-width semantics
  before comparing or changing registers.
- Keep P007's Decimal model, P008's fixed-point model, P009's mirror
  differential result, P011's scalar ranges, and circuit/gate observations as
  distinct evidence types.
- Treat mirror findings as mirror-qualified until canonical provenance is
  established.
- Do not derive physical qubit savings from an unused scalar high bit.
- Do not report unexecuted import, construction, measurement, or verifier
  operations as successful. Do not fabricate resource metrics.
- Do not change widths, arithmetic, coefficients, rounding, or truncation in
  this readiness phase.

## 13. P013 recommendation

**Recommend exactly one next step:** acquire and provenance-bind the canonical
INVSQRT artifact bundle (reference circuit, verifier, and sample submission),
record its authoritative origin and hashes, and preserve it separately from
the public mirror. This addresses the highest-priority evidence gap exposed
by P012. P013 should not start a width experiment or claim circuit
optimization readiness; Kickmix compatibility and executable backend checks
remain subsequent gates.

## 14. Reproduction instructions

From the repository root in PowerShell:

```powershell
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git status --short --untracked-files=all
python --version
python -m pip show kickmix
$env:PYTHONPATH = "src"
python -c "from invsqrt_opt.artifacts import ArtifactManifest, assess_adapter_readiness; from pathlib import Path; m = ArtifactManifest.discover(Path.cwd()); print(m.to_dict()); print(assess_adapter_readiness(m).to_dict())"
```

`python -m pip show kickmix` is expected to report that the package is not
installed in the P012 environment. The pinned mirror bytes were rechecked
without saving files using the immutable raw URLs:

- `https://raw.githubusercontent.com/qarena-ai/invsqrt/6ac78ec5ace6dfd5831ccac2547041408f5d8278/verifiers/invsqrt/nr_reference_circuit.py`
- `https://raw.githubusercontent.com/qarena-ai/invsqrt/6ac78ec5ace6dfd5831ccac2547041408f5d8278/verifiers/invsqrt/verify_submission_invsqrt.py`

Recompute SHA-256 from response bytes and compare with §4. Do not execute the
mirror verifier as though it were canonical. P012 did not install or modify
any dependencies or artifact files.

## 15. Evidence references, hashes, and validation status

### Local evidence hashes recorded before P012 edits

| File | SHA-256 |
|---|---|
| P007 reference model, `src/invsqrt_opt/reference_math.py` | `5c6510f2efedb39f4a4106e122c75ecb83e66cad21ff717b1e985d11dfd92b03` |
| P007 numerical validator, `src/invsqrt_opt/numerical_validation.py` | `b39cf381d74392330eb500bdb7110355c54da3056f4914a390c719a530c1450b` |
| P008 fixed-point model, `src/invsqrt_opt/fixed_point.py` | `734d8fbbccb603d03eaa51e49e98b0a1126d77c2461b4bc4dffe7c4dceabc1ac` |
| P009 differential validator, `src/invsqrt_opt/fixed_point_differential.py` | `0b2eb8420bb386b49e91d223a2b43ed6d50ed92d56227351084cdfae9e93e852` |
| P007 report | `daad44272c3f53eca1e85cad6b6a9f653e0507f68f14b725a8191e96875ef8b0` |
| P008 report | `a82205c95380fe421ba4930741dfdae044d53975d4b74a0f9c4e80aab2f41002` |
| P009 report | `c559bce744d142f08c2a7e4703db89ee4ce9df750d33dab5d47f735225401054` |
| P010 candidate register | `f019220523eaf2bce9a57cf0569ef821f3b1a2ef786b852b7bc7657b1965e662` |
| P011 analyzer | `d8c8ea3c258c5eabe525223cb1bae11f35e5df9e12a4d57e58c78abe1972b4a7` |
| P011 tests | `357d0a7a14b19886fd1d16f68871f6a3914abca3b2ef4d5ffea2224fe1b48c6b` |
| P011 report | `ca5940fd271069b6f60003a7eabf94a7a9f42102e424a2db04b78d82a086c8e8` |
| `pyproject.toml` | `95f056050f2b1df8b1d4c36fe8e63fab620098a6eb10aa4d9ce79290583061c8` |

The above hashes were captured before the P012 report/README edits and are
intended to verify preservation. P007–P011 documents and implementation
outputs remain separate from any P012 source analysis.

### P012 validation

| Check | Result |
|---|---|
| Local artifact manifest and fail-closed adapter assessment | `BLOCKED`, with missing artifacts and unavailable Kickmix explicitly listed |
| Mirror source and verifier hash checks | `READY`; both match the pinned P009 digests |
| Reference module import / circuit construction | `NOT_AVAILABLE` / `NOT_TESTED` |
| Resource extraction | `NOT_TESTED` |
| Official verifier availability / execution | `NOT_AVAILABLE` / `NOT_TESTED` |
| Circuit equivalence, phase acceptance, resources, score | `NOT_MEASURED` |
| P007–P011 preservation | `PASS`; all 12 recorded baseline/report/manifest hashes match, and the complete test suite passes |
| Complete project test suite | `PASS`; `python -m pytest -q` — 310 passed |
| `git diff --check` | `PASS` |
| README report link | `PASS`; target report exists |
| Dependency manifest | `PASS`; `pyproject.toml` hash unchanged |
| Official artifact modifications | None; official artifacts were unavailable locally |
| Dependency changes | None |
| Commit / push | None |

Final tracked diff: `README.md` only. New P012 file: this report. All
pre-existing untracked P002–P011 files and cache files remain present and
untouched.

### Evidence references

1. Local readiness interfaces: `src/invsqrt_opt/artifacts.py`,
   `src/invsqrt_opt/backend.py`, and `src/invsqrt_opt/verifier.py`.
2. Local arithmetic evidence: `src/invsqrt_opt/fixed_point.py`,
   `src/invsqrt_opt/fixed_point_differential.py`, and P007–P011 reports.
3. Pinned mirror reference circuit and verifier at commit
   `6ac78ec5ace6dfd5831ccac2547041408f5d8278`, with hashes in §4.
4. `pyproject.toml` and the P012 Python/import/package checks.
5. `tests/test_artifact_intake.py` for existing fail-closed readiness and
   unavailable-backend behavior.
