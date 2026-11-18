# Experiment Record Standard

**Date:** 2026-11-18
**Status:** `SPECIFIED — NO EXECUTION RECORDS CREATED`
**Authority:** every `PASS`/`FAIL` record must arise from an authoritative verifier run. No verifier run has occurred, so all current baseline records are `BLOCKED`.

---

## 1. Recording rules

1. One execution → one structured record plus one raw log file.
2. `PASS`, `FAIL`, and `BLOCKED` are the only verdicts. `UNVERIFIED` may be used for local preflight but is not a benchmark verdict.
3. Salt values are never stored; store only `salt_id` and `salt_length`.
4. `shot_divisor` must be `1` for any authoritative record.
5. Measured values and theoretical values live in separate objects; never mix them.
6. A score is recorded only if returned by the authoritative verifier/metric.
7. If execution cannot start, write a `BLOCKED` record with the exact blocker and required action.
8. Records are append-only; corrections append a linked correction record.
9. Raw verifier output is preserved verbatim, including exceptions and tracebacks, with secrets redacted if present.
10. Reproduction instructions must be sufficient to rerun from the recorded commit, environment, artifact hashes, and command.

---

## 2. Required structured schema

```yaml
experiment_id: string              # e.g. BASE-INVSQRT-001
kind: baseline | candidate | regression | preflight
benchmark: invsqrt | dqi | dfthcsos | all
verdict: PASS | FAIL | BLOCKED
created_utc: ISO-8601

git:
  commit: string
  branch: string
  dirty: boolean
  tracked_files_changed: [string]

environment:
  os: string
  python_version: string
  python_executable: string
  conda_env: string | null
  dependency_versions:
    cirq: string | NOT INSTALLED
    qualtran: string | NOT INSTALLED
    pyscf: string | NOT INSTALLED
    openfermion: string | NOT INSTALLED
    numpy: string
    scipy: string
    kaggle_cli: string
  pinned_environment_source: string | NOT FOUND

inputs:
  external_files:
    - name: string
      path: external/...            # gitignored
      sha256: string
      bytes: integer
      origin: string
      version_or_revision: string | NOT FOUND
  verifier_version: string | NOT FOUND
  verifier_sha256: string | NOT FOUND

candidate:
  name: string
  sha256: [string]
  bytes: [integer]
  artifact_paths: [string]          # gitignored or repo-relative

execution:
  command_or_api_call: string       # exact text; wrappers labelled internal
  started_utc: ISO-8601 | null
  finished_utc: ISO-8601 | null
  duration_seconds: float | null
  shot_divisor: integer             # must be 1 for authoritative runs
  salt_id: string                   # opaque id; never the salt value
  salt_length: integer              # must be >=32 for authoritative runs

measured:
  raw_log_path: string
  verifier_output_sha256: string
  resource_metrics: object          # only keys observed in authoritative output
  score: float | null
  failures: integer | null
  rejection_reason: string | null

theoretical:
  formulas_used: [string]
  calculated_values: object
  note: "Not score evidence"

failure_details:
  exception_type: string | null
  message: string | null
  requirement_rows_failed: [string]
  blocker: string | null
  required_user_action: string | null

reproduction:
  steps: [string]
  expected_artifacts: [string]
  clean_checkout_verified: boolean
```

---

## 3. BLOCKED baseline record example (current truthful state)

```yaml
experiment_id: BASE-INVSQRT-001
kind: baseline
benchmark: invsqrt
verdict: BLOCKED
created_utc: 2026-11-18
git:
  commit: 2b5906a
  branch: main
  dirty: true
environment:
  os: Ubuntu 26.04.1 LTS / Linux 6.18.33.2-microsoft-standard-WSL2
  python_version: 3.14.7
  python_executable: /home/yousuf/miniconda3/bin/python3
  conda_env: base
  pinned_environment_source: NOT FOUND
inputs:
  external_files: []
  verifier_version: NOT FOUND
candidate:
  name: official reference baseline
  sha256: []
  bytes: []
execution:
  command_or_api_call: "kaggle competitions download -c google-verifiable-quantum-circuit-compilation -p external"
  started_utc: null
  finished_utc: null
  duration_seconds: null
  shot_divisor: 1
  salt_id: null
  salt_length: null
measured:
  raw_log_path: null
  verifier_output_sha256: null
  resource_metrics: {}
  score: null
  failures: null
  rejection_reason: null
theoretical:
  formulas_used: ["S = Q × C", "C = Toffolis + T/4"]
  calculated_values: {"literature_Q": 260, "literature_C": 7988, "literature_S": 2.08e6}
  note: "Literature values only; not measured."
failure_details:
  exception_type: "Authentication required"
  message: "Kaggle CLI reported authentication required; no verifier source/data available."
  requirement_rows_failed: []
  blocker: "Kaggle credentials and competition data unavailable."
  required_user_action: "Yousuf: run kaggle auth login or configure official API token; then download data."
reproduction:
  steps:
    - "Authenticate with Kaggle."
    - "Run kaggle competitions download -c google-verifiable-quantum-circuit-compilation -p external"
    - "Record checksums, then invoke the documented metric API."
  expected_artifacts: ["external/verifiers/", "external/kickmix/", "sample submission"]
  clean_checkout_verified: false
```

Analogous `BLOCKED` records are required for DQI and DFTHC-SOS; no score field may be populated.

---

## 4. File convention

```text
experiments/specs/<experiment_id>.yaml      # pre-registration before execution
experiments/records/<experiment_id>.json    # structured result, append-only
results/raw/<experiment_id>.log             # raw verifier output
results/raw/<experiment_id>.stdout.txt      # exact stdout if separate
results/raw/<experiment_id>.stderr.txt      # exact stderr if separate
```

These paths are planned, not created.

---

## 5. Acceptance criteria for a valid record

- Git commit and working-tree state recorded.
- Environment and dependency versions recorded; pinned source identified.
- Input checksums recorded; restricted bytes remain outside Git.
- Candidate SHA-256 and byte sizes recorded.
- Exact invocation recorded; no invented CLI flags.
- `shot_divisor=1` and `salt_length>=32` for any authoritative verdict.
- Raw log and verifier output hash present.
- Resource metrics copied from verifier output, not estimated locally.
- Score present only if verifier returned it.
- Failure details and reproduction steps present.
- Theoretical values clearly separated from measured values.
