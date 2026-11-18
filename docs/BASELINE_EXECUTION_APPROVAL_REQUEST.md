# DQI Full Baseline Execution Approval Request

**Status:** Awaiting Yousuf's explicit approval.

## Required command

Run from the repository root:

```bash
set +e
{
  date --iso-8601=ns
  /usr/bin/time -v -o results/raw/BASE-DQI-102400-W1.time.txt \
    timeout --signal=TERM --kill-after=5m 16h \
    env PYTHONPATH="$PWD/external:$PWD/external/verifiers:$PWD/external/kickmix" \
    /home/yousuf/.venvs/gqai/bin/python \
      external/verifiers/dqi/verify_submission_dqi.py \
      external/sample_submission/dqi.kmb \
      --num-shots 102400 \
      --batch-size 256 \
      --log2-delta -128 \
      --max-workers 1 \
      --salt codex-dqi-full-baseline-20261119 \
      > results/raw/BASE-DQI-102400-W1.stdout.json \
      2> results/raw/BASE-DQI-102400-W1.stderr.log
  status=$?
  printf 'exit_code=%s\n' "$status"
  date --iso-8601=ns
  exit "$status"
} > results/raw/BASE-DQI-102400-W1.timestamps.txt 2>&1
```

## Official parameters

- Circuit: `external/sample_submission/dqi.kmb`
- Circuit SHA-256: `959471d05a26373b4f14ca0cae2d8639ea25f18170d9f6532139aa51ccc04995`
- Verifier: `external/verifiers/dqi/verify_submission_dqi.py`
- Verifier SHA-256: `f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65`
- Shots: 102,400
- Batch size: 256
- Log2 delta: `-128`
- Workers: 1

## Runtime estimate

Measured diagnostics:

- 256 shots, one worker: 1:52.83 elapsed, 3,482,040 KB max RSS.
- 1024 shots, one worker: 0:45.10 elapsed, 3,496,640 KB max RSS.

Linear scaling of the 1024-shot observation to 102,400 shots gives about 1:15:10. Linear scaling of the 256-shot observation gives about 12:32:12. The spread is large because there are only two observations and process/runtime variability is substantial; these are planning bounds, not a reliable performance model.

The proposed 16-hour timeout allows about 3 hours 28 minutes beyond the slower proportional estimate. It is a recovery boundary, not a performance promise.

## Memory estimate

- Host total: approximately 8,035,968 KB.
- Observed one-worker diagnostic peak: approximately 3.5 GB.
- Estimated full one-worker peak: approximately 3.5–4.0 GB.
- Do not use four workers unless memory feasibility is independently demonstrated.

## Output and recovery

- stdout: `results/raw/BASE-DQI-102400-W1.stdout.json`
- stderr: `results/raw/BASE-DQI-102400-W1.stderr.log`
- GNU time: `results/raw/BASE-DQI-102400-W1.time.txt`
- Start/end timestamp and shell exit-status record: `results/raw/BASE-DQI-102400-W1.timestamps.txt`

On timeout or failure:

1. Preserve all four output files.
2. Do not rerun silently or change shot count.
3. Inspect exit status and peak memory.
4. Record the failure as evidence.
5. Seek explicit Yousuf approval before any subsequent run.

## Approval gate

**No command above has been executed.** Run it only after Yousuf explicitly approves the 102,400-shot single-worker execution and 16-hour timeout.
