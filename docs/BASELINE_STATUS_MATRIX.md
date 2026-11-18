# Baseline Status Matrix

| Benchmark | Artifact integrity | Register/schema validation | Official full execution | Baseline evidence complete | Final status |
|---|---|---|---|---|---|
| INVSQRT | VERIFIED | VERIFIED | Yes: runs 001 and 002; 200,540,928 shots, exit 0, PASS | Missing execution timestamps and contemporaneous environment/commit binding | NOT REPRODUCED |
| DQI | VERIFIED | VERIFIED | No: 102,400-shot run absent | Missing full run | BLOCKED |
| DFTHC-SOS | VERIFIED | VERIFIED | Yes: runs 002 and 003; 254,464 shots, exit 0, PASS | Missing execution timestamps and contemporaneous environment/commit/input-file binding | NOT REPRODUCED |

**Overall decision:** BLOCKED

## Recovered execution details

| Benchmark/run | Recorded command | File mtime evidence (not run time) | Elapsed | Peak RSS | Result |
|---|---|---|---:|---:|---|
| INVSQRT-001 | `/home/yousuf/.venvs/gqai/bin/python invsqrt/verify_submission_invsqrt.py ../sample_submission/invsqrt.kmb` | 2026-11-18 21:55:34 +06:00 | 11:09.85 | 523,348 KB | PASS, score 2,076,774.233715282 |
| INVSQRT-002 | Same as 001 | stdout/time mtime 2026-11-19 01:41:42 +06:00 | 11:30.13 | 523,844 KB | PASS, same score |
| DFTHC-SOS-002 | `/home/yousuf/.venvs/gqai/bin/python dfthcsos/verify.py ../sample_submission/dfthcsos` | 2026-11-18 21:43:48 +06:00 | 1:44.26 | 1,113,308 KB | PASS, score 3,355,599,588.3155365 |
| DFTHC-SOS-003 | Same as 002 | stdout/time mtime 2026-11-19 01:29:56 +06:00 | 2:13.41 | 1,112,216 KB | PASS, same score |

Reason:

- DQI has no official full baseline.
- INVSQRT and DFTHC-SOS full verifier executions do not meet strict reproduction provenance requirements.
- No optimization authorization follows from sample parsing or partial diagnostics.
- No start/end execution timestamps are available; file modification times are recorded only as metadata.
