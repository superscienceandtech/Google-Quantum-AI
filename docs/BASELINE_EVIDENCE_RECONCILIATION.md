# Baseline Evidence Reconciliation

**Date:** 2026-11-19

## Contradiction resolved

The previous report used “baseline reproduced” in two senses:

1. An official verifier fully executed the packaged sample submission.
2. A baseline has a complete reproduction evidence package.

Those meanings must not be merged. This reconciliation requires a complete evidence package before promotion to `BASELINE REPRODUCED`.

## Classification levels

- `FILE_INTEGRITY_CHECK`
- `SCHEMA_VALIDATION`
- `REGISTER_VALIDATION`
- `STRUCTURAL_CIRCUIT_VALIDATION`
- `PARTIAL_DIAGNOSTIC`
- `OFFICIAL_VERIFIER_FULL_EXECUTION`
- `OFFICIAL_BASELINE_SCORE_REPRODUCTION`

Levels 1–6 do not prove level 7.

## INVSQRT

The raw directory contains two independently captured full executions with matching PASS metrics. `BASE-INVSQRT-001` is the primary provenance record because its stderr file contains the GNU `time` report; `BASE-INVSQRT-002` is a second record with the same result and a separate time file.

- Candidate: `external/sample_submission/invsqrt.kmb`
- Candidate SHA-256: `e2bf8eb64350a4460a271fc7f1d591ef125b1e276377e9a0f64b96ab3ca321e1`
- Verifier: `external/verifiers/invsqrt/verify_submission_invsqrt.py`
- Verifier SHA-256: `ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a`
- Exact recorded command: `/home/yousuf/.venvs/gqai/bin/python invsqrt/verify_submission_invsqrt.py ../sample_submission/invsqrt.kmb`
- Recorded working directory is not embedded. Relative paths are consistent with `external/verifiers`; this is an inference, not recovered fact.
- Primary raw stdout: `results/raw/BASE-INVSQRT-001.stdout.txt`
- Primary raw stderr/timing: `results/raw/BASE-INVSQRT-001.stderr.txt`
- Secondary raw stdout: `results/raw/BASE-INVSQRT-002.stdout.txt`
- Secondary raw timing: `results/raw/BASE-INVSQRT-002.time.txt`; its stderr is zero bytes.
- File metadata: primary files have mtime `2026-11-18 21:55:34 +06:00`; this is file mtime, not an execution start or finish timestamp.
- Exit: 0
- Verified shots: 200,540,928
- Status: `PASS`
- Score: `2076774.233715282`
- Resources: 260 qubits, 7,735 Toffolis, 7,987.593206597238 Toffoli equivalent
- Primary timing: 11:09.85 elapsed, 523,348 KB max RSS.
- Secondary timing: 11:30.13 elapsed, 523,844 KB max RSS.
- Full input-domain coverage is established by the verifier's `verified_shots=200540928` result and the source default of 64 shots for each x in `1..3,133,452`.

Classification:

- `OFFICIAL_VERIFIER_FULL_EXECUTION`: confirmed by both raw PASS outputs, matching full verified-shot count, and exit status 0.
- Official baseline score reproduction: **not promoted**.

Missing critical baseline provenance:

- No execution start/finish timestamps. Filesystem mtimes do not substitute for them.
- No contemporaneous experiment record binding the run to the verifier checksum, dependency versions, and Git commit.
- The raw command does not encode the verifier checksum; current source hash is independently verified against the official archive, but not captured by the run record.

Final status: **NOT REPRODUCED** under the strict evidence requirements.

## DQI

Evidence:

- Candidate: `external/sample_submission/dqi.kmb`
- Candidate SHA-256: `959471d05a26373b4f14ca0cae2d8639ea25f18170d9f6532139aa51ccc04995`
- Verifier: `external/verifiers/dqi/verify_submission_dqi.py`
- Required official shots: 102,400.
- 256-shot and 1024-shot diagnostic records exist and fail confidence thresholds.
- 102,400-shot stdout and stderr are absent or 0 bytes.

Final status: **BLOCKED**.

## DFTHC-SOS

Evidence:

- Submission: `external/sample_submission/dfthcsos`
- NPZ SHA-256: `14d5cc25eb3bf82a9ccb87c811db28d127bef6d28697dd190dc1e875de3bfe69`
- Verifier: `external/verifiers/dfthcsos/verify.py`
- Verifier SHA-256: `0775be7a528922367caebe9e4d051d6199811f1aefeaa4b793eaaa4621b8ec9d`
- FCIDUMP SHA-256: `e5a48af746fd075026dec9e8f5df2d363802a121e8c53af9a0b984bde695e1bd`
- Fixed-shift SHA-256: `7b7facf63fe35a9d9d3d00787ffdb700c863fa845fe4724d7f7c54778151cd87`
- All 10 ANGLE circuits are present; the sample verifier output reports the submission digest `276d464ff14da828b6b33e8487d99975494cbdf0c3cb2bd37dd3c3ddc4002695`.
- Primary exact recorded command: `/home/yousuf/.venvs/gqai/bin/python dfthcsos/verify.py ../sample_submission/dfthcsos`
- Recorded working directory is not embedded. Relative paths are consistent with `external/verifiers`; this is an inference, not recovered fact.
- Primary raw stdout: `results/raw/BASE-DFTHCSOS-002.stdout.txt`
- Primary raw stderr/timing: `results/raw/BASE-DFTHCSOS-002.stderr.txt`
- Secondary raw stdout: `results/raw/BASE-DFTHCSOS-003.stdout.txt`
- Secondary raw timing: `results/raw/BASE-DFTHCSOS-003.time.txt`; its stderr is zero bytes.
- File metadata: primary files have mtime `2026-11-18 21:43:48 +06:00`; secondary stdout/time mtime is `2026-11-19 01:29:56 +06:00` and its empty stderr mtime is `2026-11-19 01:27:41.800 +06:00`. These are file mtimes, not execution timestamps.
- Exit: 0
- Status: `PASS`
- Score: `3355599588.3155365`
- Lambda: 308.4559397330944
- E_gap: 3.965477244291833
- Residuals: error_1 `0.0031851950317991775`, error_2 `0.018639570630974073`
- T_total: 93,237
- Q_total: 730
- Verified shots: 254,464
- Primary timing: 1:44.26 elapsed, 1,113,308 KB max RSS.
- Secondary timing: 2:13.41 elapsed, 1,112,216 KB max RSS.

Classification:

- `OFFICIAL_VERIFIER_FULL_EXECUTION`: confirmed by matching PASS outputs, expected 3,976 addresses × 64 shots = 254,464 verified shots, and exit status 0.
- Official baseline score reproduction: **not promoted**.

Missing critical baseline provenance:

- No execution start/finish timestamps. Filesystem mtimes do not substitute for them.
- No contemporaneous experiment record binding the run to the verifier checksum, dependency versions, and Git commit.
- The run record does not list per-file SHA-256 values for every ANGLE circuit; the current archive inventory provides extracted-file hashes, but those were not captured at execution time.

Final status: **NOT REPRODUCED** under the strict evidence requirements.

## Overall contradiction

Calling an official full verifier pass a baseline reproduction is not justified under this audit's evidence requirements. The INVSQRT and DFTHC-SOS raw runs are useful official full-execution evidence, while DQI remains blocked.
