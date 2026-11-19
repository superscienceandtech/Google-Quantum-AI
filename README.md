# Google Quantum AI

Collaborative research and development repository for the
Google Quantum AI — Verifiable Quantum Circuit Compilation competition.

## Team Workflow

- main: Verified releases only
- develop: Main integration branch
- research/: Research and algorithm analysis
- feat/: Feature development
- test/: Verification and regression testing
- docs/: Research documentation

## Development Principles

- Reproducible experiments
- Verified compiler transformations
- Automated testing
- Documented research
- Collaborative code review

## INVSQRT optimization foundation

The `src/invsqrt_opt` package provides P002's repository-independent
experiment foundation:

- `models`: candidate, experiment configuration, verification, provenance,
  and resource metric types.
- `score`: official/estimated cost and score calculation.
- `records`: append-only JSON Lines experiment storage and eligibility-aware
  candidate comparison.

Candidate correctness states are evidence-based. A candidate can only reach
`OFFICIAL_VERIFIER_VALIDATED` with a `PASSED` verification status and an
evidence reference.

Run the deterministic test foundation from the repository root:

```powershell
python -m pytest
```

The historical score regression is a fixture check only; it does not claim that
the official benchmark was re-executed. No official verifier, SDK, reference
circuit, or official sample submission is present in this checkout.

## INVSQRT contract and verifier boundary

P003 adds immutable benchmark-contract models and a fail-closed verifier
boundary in `src/invsqrt_opt/contract.py` and
`src/invsqrt_opt/verifier.py`.

- `OFFICIAL_INVSQRT_SPEC` is the single source of P003 benchmark constants.
- `validate_input` and `validate_inputs` validate the official integer domain.
- `CircuitContract` performs metadata-only structural validation.
- `discover_artifacts` reports documented official artifact availability
  without modifying or executing artifacts.
- `OfficialVerifierAdapter` is an integration protocol; production execution
  remains unavailable until the official verifier is present.
- `UnavailableVerifierAdapter` returns an unavailable, not-passed result.
- `TestDoubleVerifierAdapter` is explicitly a unit-test double and can never
  establish an official pass.

No official verifier or full benchmark is executed by this package or its tests.

## P004 search and experiment framework

The P004 framework is backend-independent and accepts parameter definitions
from a future strategy; it does not prescribe INVSQRT algorithm parameters.

```python
from invsqrt_opt import (
    GridSearch,
    ParameterDefinition,
    ParameterKind,
    SearchSpace,
)

space = SearchSpace(
    (
        ParameterDefinition(
            name="example_integer",
            kind=ParameterKind.INTEGER,
            minimum=1,
            maximum=5,
            step=2,
        ),
    )
)
batch = GridSearch().generate(space, benchmark_id="INVSQRT", max_configurations=2)
```

`RandomSearch` requires an explicit seed and reports requested/generated counts
finite-space exhaustion, and whether the generation completed. Candidate
configuration fingerprints depend only
on their benchmark, parameters, space, strategy, seed, and schema version;
timestamps and creation metadata are retained separately.

An `ExperimentBackend` separates configuration validation, circuit
construction, resource measurement, and compilation. `UnavailableBackend` is
the default-safe implementation; it never creates a circuit or supplies
metrics. The `ExperimentRunner` persists candidate and run-summary records
through the append-only P002 `ExperimentStore`. Explicit backend test doubles
are confined to unit tests.

Run provenance must be supplied by the caller rather than inferred:
`ExperimentRunner.run` requires the repository commit, software version, and
dependency metadata. It executes configurations sequentially, records
per-candidate failures, and persists an interrupted-run summary when interrupted.

Configuration validation only establishes that parameters meet their
declaration. It is not circuit construction, structural proof, or official
verification. Official verification remains behind the P003 adapter and is
attempted only when an authorization reference is explicitly supplied. The
official verifier and quantum SDK are not present in this checkout, so no
production circuit backend or verified optimization is available.

`compare_candidates` requires callers to select an eligibility basis:
officially verified results, measured official metrics, or all scored records
with their provenance distinguished. Estimates are never eligible as official
competition improvements.

Run all deterministic regression tests from the repository root:

```powershell
python -m pytest
```

## P005 artifact intake and runtime readiness

`ArtifactManifest.discover(repository_root)` creates a serializable intake
manifest for the documented INVSQRT verifier, reference circuit, sample
submission, and Kickmix shared library. An external artifact root can be
provided explicitly; only relative artifact paths are accepted. Intake reports
availability, file type, SHA-256, Git tracking status, declared provenance,
and compatibility status without modifying or executing artifacts.
The manifest intentionally omits absolute machine-specific paths.

The current branch has no external payload files. The documentation on
`origin/main` identifies Kickmix as the verifier runtime and documents an
official `external/kickmix/kickmix.so` library, but that report does not supply
the verifier source, circuit files, or a confirmed adapter API in this
checkout. Kickmix is not importable in the inspected local Python environments,
and its version and circuit/resource APIs are therefore unknown here.

`assess_adapter_readiness` reports these blockers explicitly.
`UnavailableCircuitArtifactAdapter` and `UnavailableKickmixBackend` fail
closed: they do not load circuits, fabricate resource metrics, or claim
official-verifier readiness. No SDK, verifier, circuit, or benchmark was
executed. Re-run discovery after authorized artifacts are placed in the
documented paths or supplied through an external artifact root.

The source-grounded mathematical analysis, reference-algorithm findings,
optimization hypotheses, correctness obligations, and readiness blockers are
documented in
[INVSQRT Algorithm and Optimization Strategy](docs/research/INVSQRT_ALGORITHM_AND_OPTIMIZATION_STRATEGY.md).

## P007 classical numerical reference

P007 adds a deterministic, high-precision classical model of the paper's
normalization, piecewise cubic estimate, and one Newton correction in
`src/invsqrt_opt/reference_math.py`. It does not emulate the reference
circuit's fixed-point truncation or implement a quantum phase gate.

Run the reproducible exhaustive validation over the official input domain:

```powershell
$env:PYTHONPATH = "src"
python -m invsqrt_opt.numerical_validation --mode EXHAUSTIVE_VALIDATION
```

Use `--mode SAMPLED_VALIDATION` for a deterministic 1,024-point uniform sample
plus domain, normalization, polynomial-boundary, and paper-reported cases.
Results identify their validation mode and explicitly mark quantum
verification as not performed. The method, coefficient citations, error
definitions, measured results, and remaining fixed-point limitations are in
[INVSQRT Classical Reference Implementation](docs/research/INVSQRT_CLASSICAL_REFERENCE_IMPLEMENTATION.md).

## P008 fixed-point semantics

P008 is **PARTIALLY IMPLEMENTED**: `src/invsqrt_opt/fixed_point.py` provides
an independent integer model of the public reference implementation's
fixed-point pipeline, and it matches that source model over the complete
benchmark input domain. Full quantum-circuit equivalence remains **BLOCKED**:
the source is available through a public mirror that claims its verifier and
reference circuit are unchanged competition artifacts, but this checkout does
not contain Kickmix for an independent circuit-simulation comparison.

See
[INVSQRT Fixed-Point Semantics and Emulator Readiness](docs/research/INVSQRT_FIXED_POINT_SEMANTICS_AND_EMULATOR_READINESS.md)
for the source integrity evidence, arithmetic semantics matrix, exhaustive
comparison, and remaining blockers. This does not claim official verifier
acceptance or quantum resource improvement.

## P009 fixed-point emulator validation

P009 independently rechecked the pinned public-mirror source hashes and
reproduced the emulator comparison twice over all 3,133,452 valid inputs:
**zero mismatches** and **zero maximum integer output difference** on each
completed run. It adds 132 source-model boundary regression vectors, rejects
unsupported precision settings, and re-runs P007's exhaustive classical
regression without changing P007; its historical maximum relative error was
reproduced. The full suite passes **299 tests**.

Source provenance is **PARTIALLY VERIFIED**: the immutable mirror commit and
file hashes match, but the mirror's competition-origin claim is not
independently authenticated. Quantum circuit equivalence and official
acceptance remain **NOT TESTED/BLOCKED** because Kickmix and the circuit
fixture are unavailable. The opt-in differential command requires network
access and NumPy; NumPy was not added to project dependencies.

Run the complete differential comparison from PowerShell:

```powershell
$env:PYTHONPATH = "src"
python -m invsqrt_opt.fixed_point_differential --mode FULL_DOMAIN_VALIDATION
```

See
[INVSQRT Fixed-Point Emulator Validation](docs/research/INVSQRT_FIXED_POINT_EMULATOR_VALIDATION.md)
for the source-to-implementation audit, repeated-run metrics, P007 regression,
test results, and remaining blockers.

## P010 optimization candidate research

P010 documents ten evidence-classified optimization candidates, their
fixed-point and reversibility obligations, qualitative priorities, and
reproducible future experiment designs. It makes no circuit changes and reports
no resource or score improvement. The first proposed step is an exhaustive
baseline intermediate-range audit; circuit experiments remain blocked on
authoritative artifacts, Kickmix, and the official verifier/resource counter.

See
[INVSQRT Optimization Candidate Register](docs/research/INVSQRT_OPTIMIZATION_CANDIDATE_REGISTER.md)
for the candidate register and P011 recommendation.

## P011 C01 baseline range audit

P011 adds an isolated, deterministic analyzer for the P010-C01 baseline range
and truncation-margin study. It observes the validated default fixed-point
model without changing its precision, output, or production behavior. The
exhaustive results and limitations are documented in
[INVSQRT P011 Candidate Prototype Report](docs/research/INVSQRT_P011_CANDIDATE_PROTOTYPE_REPORT.md).

## P012 circuit backend readiness

P012 checks local artifact provenance, Kickmix and SDK availability, and
circuit-level audit readiness. Static findings from the pinned public mirror
are kept separate from official provenance; no circuit was constructed,
measured, or verified.

See
[INVSQRT P012 Circuit Backend Readiness Report](docs/research/INVSQRT_P012_CIRCUIT_BACKEND_READINESS_REPORT.md)
for the artifact inventory, compatibility checks, source-level register
evidence, blockers, and the proposed circuit audit procedure.

## P013 canonical artifact provenance

P013 investigated official artifact acquisition and extended the P005
readiness manifest to keep source authentication distinct from file integrity.
Canonical artifacts remain unavailable because no verified official source
identifier or authenticated acquisition route is configured; the historical
public mirror remains unauthenticated.

See
[INVSQRT P013 Canonical Artifact Provenance Report](docs/research/INVSQRT_P013_CANONICAL_ARTIFACT_PROVENANCE_REPORT.md)
for the acquisition outcome, mirror separation, readiness matrix, and
remaining blockers.

## P014 authoritative competition identity

P014 recovered the competition title and slug from the official Kaggle page
and confirmed the repository-documented download command. Authenticated
Kaggle access is not available in this environment, so canonical artifacts
remain unacquired; the existing provenance gate remains in force.

See
[INVSQRT P014 Authoritative Competition Identity and Acquisition Report](docs/research/INVSQRT_P014_AUTHORITATIVE_COMPETITION_IDENTITY_AND_ACQUISITION_REPORT.md)
for Git-reference evidence, identity confidence, acquisition status, and
remaining blockers.

## P015 Kaggle acquisition adapter

P015 adds a fail-closed Kaggle CLI adapter that validates the P014 slug,
requires explicit authentication verification, stages downloads in an
isolated area, inventories archives without extracting them, and hands
explicitly mapped files to the existing P005 manifest. Authentication
configuration alone is not treated as proof of access. The current environment
has no Kaggle CLI, so no download was attempted and canonical artifact
readiness remains blocked.

See
[INVSQRT P015 Kaggle Acquisition Adapter Report](docs/research/INVSQRT_P015_KAGGLE_ACQUISITION_ADAPTER_REPORT.md)
for the API, security controls, tests, environment status, and future
authorized acquisition procedure.

## P016 C01 range-audit validation

P016 validates and analytically extends C01 against the existing P008 fixed-point
emulator. It confirms complete, non-overlapping normalized interval partitions
and exhaustive agreement over all 3,133,452 valid inputs. It makes no
circuit-register, resource, or official-score claim.

See
[INVSQRT P016 C01 Range-Audit Validation Report](docs/research/INVSQRT_P016_C01_RANGE_AUDIT_VALIDATION_REPORT.md)
for partition boundaries, fixed-point witnesses, hypotheses, limitations, and
the recommended next circuit-level experiment.

## P017 fixed-point intermediate register-width analysis

P017 adds signed and unsigned width helpers, an exhaustive fixed-point
intermediate inventory, partition-to-extrema consistency, and circuit-mapping
guardrails. It does not claim an actual circuit register reduction.

See
[INVSQRT P017 Register-Width Analysis Report](docs/research/INVSQRT_P017_REGISTER_WIDTH_ANALYSIS_REPORT.md)
for exact extrema, mathematical widths, evidence classes, circuit-unmapped
findings, and the next circuit-level validation requirement.
