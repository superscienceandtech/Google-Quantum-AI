# STEP-10 — Team Repository Reconnaissance and Integration Planning

- Document ID: TPR-010
- Status: COMPLETED — READ-ONLY INSPECTION
- Team repository: Google-Quantum-AI
- Independent workspace: separate verification workspace; its contents were not copied wholesale
- Inspection date: 2026-11-19

## 1. Repository Identity and Git Status

### 1.1 Confirmed repository identity

- Repository remote:
  `https://github.com/superscienceandtech/Google-Quantum-AI.git`
- Current local branch: `main`
- Current commit: `3861f76f4842f40e70fc59ad69812052c2719f32`
- Latest commit summary: merge of `docs/team-readiness`
- Working tree: clean
- Git status: `## main...origin/main`
- Local branch at reconnaissance: `main`
- Remote branches present:
  - `origin/main`
  - `origin/develop`
  - `origin/docs/research-documentation`
  - `origin/docs/team-readiness`
  - `origin/feat/compiler-infrastructure`
  - `origin/feat/dfthcsos-factorization`
  - `origin/feat/dqi-decoder`
  - `origin/feat/invsqrt-optimization`
  - `origin/research/competition-analysis`
  - `origin/research/dfthcsos`
  - `origin/research/dqi`
  - `origin/research/invsqrt`
  - `origin/test/verification-regression`

No credentials, tokens or secret values were inspected or exposed.

### 1.2 Refreshed branch evidence

Remote refs were rechecked on 2026-11-19 before this report was integrated.
`origin/main` and `origin/develop` both resolve to
`3861f76f4842f40e70fc59ad69812052c2719f32`; `develop` was fast-forwarded to
`main` under the STEP-13 project-lead authorization.

Other live remote refs at that check:

- `origin/docs/team-readiness`: `7ddcb3df96c52515c21629464351b1b840ae642f`
- `origin/feat/compiler-infrastructure`: `6c63c152972bd2e920ed72514dbb9bb7e4e1d6dd`
- `origin/docs/research-documentation`,
  `origin/feat/dfthcsos-factorization`, `origin/feat/dqi-decoder`,
  `origin/feat/invsqrt-optimization`, `origin/research/competition-analysis`,
  `origin/research/dfthcsos`, `origin/research/dqi`,
  `origin/research/invsqrt`, and `origin/test/verification-regression`:
  `5391b2e7123484efacffc0588f5e761e67b5cb55`

The branch names do not establish active implementation ownership or accepted
work assignments.

## 2. Repository Structure

The checked-out `main` tree contains 29 files. The complete relevant inventory
is documentation and repository templates; no Python source or test source
exists on `main`.

Top-level structure:

- `README.md`
- `.github/ISSUE_TEMPLATE/task.yml`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `docs/`

Documentation areas include:

- baseline status and reconciliation;
- baseline execution approval;
- competition requirements;
- dependency compatibility;
- experiment record standard;
- official verifier API reference;
- score model verification;
- benchmark workstreams;
- team workflow and responsibilities.

Not present on `main`:

- `.github/workflows/`
- `.gitignore`
- `pyproject.toml`
- `pytest.ini`
- `requirements.txt` or equivalent dependency manifest
- Python package directories
- `src/`, `benchmarks/`, `harness/`, `experiments/`, `tests/`
- `external/verifiers/`
- `external/kickmix/`
- `external/sample_submission/`

This is a documentation/workflow repository snapshot, not an implementation
checkout.

## 3. Benchmark Implementation Map

No executable benchmark implementation modules were found in the current
`main` tree or in the inspected remote-tracking implementation branch trees.

### INVSQRT

Repository evidence:

- [`docs/TEAM/BENCHMARKS/INVSQRT.md`](./BENCHMARKS/INVSQRT.md)
- [`docs/OFFICIAL_VERIFIER_API_REFERENCE.md`](../OFFICIAL_VERIFIER_API_REFERENCE.md)
- [`docs/BASELINE_STATUS_MATRIX.md`](../BASELINE_STATUS_MATRIX.md)

Status: documentation and verifier contract preparation only.

No candidate implementation path, generator, test suite or local verifier source
exists on `main`. The workstream is proposed and strict baseline reproduction
is `NOT REPRODUCED`.

Likely future implementation area:

- not found; do not assume `benchmarks/invsqrt/`

### DQI

Repository evidence:

- [`docs/TEAM/BENCHMARKS/DQI.md`](./BENCHMARKS/DQI.md)
- [`docs/BASELINE_EXECUTION_APPROVAL_REQUEST.md`](../BASELINE_EXECUTION_APPROVAL_REQUEST.md)
- [`docs/OFFICIAL_VERIFIER_API_REFERENCE.md`](../OFFICIAL_VERIFIER_API_REFERENCE.md)

Status: documentation and full-run approval preparation only.

No decoder generator, candidate implementation or test suite exists on `main`.
The full 102,400-shot baseline is explicitly blocked pending Yousuf approval.

Likely future implementation area:

- not found; proposed documentation does not establish a source module path

### DFTHC-SOS

Repository evidence:

- [`docs/TEAM/BENCHMARKS/DFTHC-SOS.md`](./BENCHMARKS/DFTHC-SOS.md)
- [`docs/OFFICIAL_VERIFIER_API_REFERENCE.md`](../OFFICIAL_VERIFIER_API_REFERENCE.md)
- [`docs/BASELINE_STATUS_MATRIX.md`](../BASELINE_STATUS_MATRIX.md)

Status: documentation and evidence reconciliation only.

No factorization generator, ANGLE circuit generator or dataset validator exists
on `main`. Strict baseline reproduction remains `NOT REPRODUCED`.

Likely future implementation area:

- not found; do not assume `benchmarks/dfthcsos/`

### Quantum compiler and optimization modules

No compiler or optimization package was found on `main`. The only relevant
documentation is proposed architecture/workflow material.

### Candidate generation

No candidate generator or candidate artifact directory was found on `main`.
Candidate submission restrictions are documented and candidate implementation
remains proposed/blocked rather than present.

### Shared utilities

No team shared utility package was found.

## 4. Existing Test and Validation Architecture

### Team repository

No executable test architecture exists on `main`:

- no Python package;
- no pytest configuration;
- no test directories;
- no unit/integration test modules;
- no fixtures;
- no dependency manifest;
- no CI workflow.

The repository has issue and pull-request templates but no `.github/workflows/`.
It has a pull-request workflow proposal in documentation, but no active CI
configuration.

The team documentation proposes a future:

- harness;
- experiment runner;
- append-only artifact registry;
- one verifier invocation per benchmark;
- preflight checks;
- CI checks.

Those are plans, not existing executable infrastructure.

### Independent workspace

Confirmed test and framework structure:

- `pytest.ini`
- `05_Regression_Engineering/verification_framework/`
- `05_Regression_Engineering/unit/`
- `05_Regression_Engineering/cross_benchmark/`
- `02_INVSQRT_Verification/tests/`
- `03_DQI_Verification/tests/`
- `04_DFTHC_SOS_Data_Validation/tests/`

The independent workspace has 53 INVSQRT tests, 82 DQI tests,
47 DFTHC-SOS tests, 29 framework tests, and 4 cross-benchmark tests,
with one framework symlink test skipped in the latest known run.

## 5. Team Architecture Observations

Current team repository responsibilities are proposed only:

- `Yousuf`: architecture, integration and release gate;
- `Srijon`: infrastructure and tooling;
- `SeyamB`: verification, test and data quality;
- `Mahin`: quantum mathematics;
- `Sonjoy`: proposed optimization support;
- `SeyamR`: proposed automation and reporting.

Documentation assignments and acceptance must not be inferred as current
implementation ownership.

The team distinguishes:

- file integrity;
- schema/register/structural validation;
- partial diagnostics;
- official full-verifier execution;
- official baseline score reproduction.

Structural validation establishes only the checked structure, not official
verifier acceptance. An official full-verifier execution records the verifier's
run and result, but does not by itself establish strict baseline reproduction
when required provenance is incomplete.

This separation is compatible with the independent evidence policy.

## 6. Independent Framework Compatibility

### Direct reuse candidates

- `05_Regression_Engineering/verification_framework/evidence.py`
- `05_Regression_Engineering/verification_framework/models.py`
- `05_Regression_Engineering/verification_framework/paths.py`
- `05_Regression_Engineering/verification_framework/reports.py`
- `05_Regression_Engineering/verification_framework/logging.py`
- `05_Regression_Engineering/verification_framework/traceability.py`
- `05_Regression_Engineering/cross_benchmark/regression.py`
- `05_Regression_Engineering/cross_benchmark/tests/test_cross_benchmark.py`
- benchmark-test fixtures and public-secondary fixture conventions

These components are framework-level and do not implement benchmark math.

### Likely adapters

1. Team package/import-path adapter:
   - add or reuse a team package root;
   - avoid importing benchmark modules solely for test discovery;
   - expose no official-verifier wrapper unless separately reviewed.

2. Evidence adapter:
   - map team experiment paths to the existing append-only evidence manifest;
   - preserve raw stdout/stderr/timing files;
   - never move or rewrite raw evidence.

3. pytest adapter:
   - add verification tests to a dedicated team test namespace;
   - define a verification-only test selection command;
   - avoid merging broad `testpaths` that duplicate discovery.

4. CI adapter:
   - add workflow only after team approval;
   - separate structural/preflight tests from resource-intensive verifier jobs;
   - require explicit approval gates for DQI and official benchmark runs.

### Dependency compatibility

Team documentation records:

- Python 3.13.15 in the observed authoritative environment;
- NumPy 2.5.5;
- SciPy 1.18.1;
- kickmix as an ELF shared library under `external/kickmix/`;
- no pinned manifest in the repository snapshot.

Independent workspace status:

- Python 3.14.5;
- pytest 9.1.1;
- NumPy/SciPy/SymPy available;
- no kickmix/candidate verifier dependency used by the independent suites.

This is a compatibility risk for team CI and any future official-verifier
integration. Python and NumPy versions should be pinned only after team approval
and a clean compatibility reproduction.

### pytest discovery risks

- the team currently has no pytest configuration;
- the independent workspace has explicit `pythonpath` and `testpaths`;
- a team copy of the independent `pytest.ini` could alter discovery;
- the independent package names could conflict with future team package names;
- integration should not add benchmark tests to compiler and optimization
  package directories by broad discovery.

## 7. Integration Risks

1. The repository is documentation-only on `main`.
2. Most feature, research, and test refs remain at the initial commit; the
   compiler-infrastructure ref has advanced, but branch ownership and scope are
   not established by that commit alone.
3. No team CI workflow exists.
4. No dependency manifest or Python package structure exists.
5. Future code ownership and branch names are not accepted assignments.
6. Official verifier/data files are not present on `main`.
7. Exact DQI execution approval is absent.
8. INVSQRT and DFTHC-SOS strict baseline reproduction is incomplete.
9. Candidate or official verifier execution could accidentally occur in CI.
10. Restricted competition data must not enter git.

## 8. Missing Official Sources and Datasets

No official `external/verifiers/`, `external/kickmix/`, sample submissions or
official dataset artifacts are present in the checked-out `main` tree.

Missing or unresolved:

- authoritative competition verifier source checkout;
- exact official metric source;
- official DQI 102,400-shot output;
- authoritative INVSQRT strict baseline provenance;
- authoritative DFTHC-SOS strict baseline provenance;
- exact pinned competition environment;
- exact team CI/dependency policy;
- candidate artifact inventory;
- private competition salt handling.

No restricted file or secret was accessed.

## 9. Recommended Integration Architecture

Recommended future layout after explicit team approval:

```text
team-repository/
├── verification/
│   ├── framework/
│   ├── invsqrt/
│   ├── dqi/
│   └── dfthcsos/
├── tests/
│   └── verification/
├── evidence/
│   └── manifests/
└── .github/workflows/
```

Safer alternatives:

- keep the independent workspace as an evidence-only downstream verification repository;
- first integrate generic framework files under a clearly named `verification/framework/` package;
- add benchmark tests under `tests/verification/<benchmark>/`;
- keep compiler, optimizer and candidate-generation code outside verification directories;
- add separate CI jobs for:
  1. structural/preflight tests;
  2. public-secondary synthetic regression tests;
  3. explicitly authorized official verifier runs.

Do not integrate official verifier or restricted data into normal test discovery.
Do not package submissions or invoke candidate circuits during verification
workflow startup.

## 10. Exact Files and Modules Potentially Needing Integration

Independent workspace components:

- `05_Regression_Engineering/verification_framework/__init__.py`
- `05_Regression_Engineering/verification_framework/evidence.py`
- `05_Regression_Engineering/verification_framework/models.py`
- `05_Regression_Engineering/verification_framework/paths.py`
- `05_Regression_Engineering/verification_framework/reports.py`
- `05_Regression_Engineering/verification_framework/logging.py`
- `05_Regression_Engineering/verification_framework/traceability.py`
- `05_Regression_Engineering/cross_benchmark/regression.py`
- `02_INVSQRT_Verification/tests/`
- `03_DQI_Verification/tests/`
- `04_DFTHC_SOS_Data_Validation/tests/`
- `05_Regression_Engineering/cross_benchmark/tests/`

Team files requiring future reconciliation:

- new team package configuration;
- new team test configuration;
- new team CI workflow;
- future benchmark package directories;
- future evidence manifest location;
- future official-verifier integration boundary.

No exact team target file can be created or selected as confirmed until the team
adds implementation code and confirms its package/test layout.

## 11. Recommended Next Implementation Step

Do not implement integration in this phase.

Recommended first implementation step after repository coordination:

1. Confirm the integration target branch and project lead approval.
2. Confirm whether implementation work exists on another live branch.
3. Add or select a team Python package layout and test configuration.
4. Add generic verification framework only, with no benchmark logic.
5. Run framework and existing synthetic tests in team CI.
6. Add benchmark test namespaces one benchmark at a time.
7. Gate official verifier and candidate execution behind explicit approval records.

No remote fetch, pull, push, merge, branch switch or file edit was performed
during this reconnaissance.
