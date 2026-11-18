# Official Verifier API Reference

## INVSQRT

**Source:** `external/verifiers/invsqrt/verify_submission_invsqrt.py`

### Public API

- `ProblemSpecInvSqrt.for_n_p(...)` — lines 78-106.
- `verify(circuit, spec, *, seed=None, salt='', batch_size=256, max_workers=None)` — lines 235-327.
- CLI entry: `main()` — lines 347-401.

**Defaults:** `N_P=10`, `ETA=218`, `DEFAULT_BATCH_SIZE=256`, `DEFAULT_SHOTS_PER_X=64`, beta `1`, precision 24 bits. Full shots: `64 * 3,133,452 = 200,540,928`.

### CLI

```text
python external/verifiers/invsqrt/verify_submission_invsqrt.py CIRCUIT.kmb
  [--format auto|kmb|kmx] [--n-p 10] [--beta 1] [--precision-bits 24]
  [--shots-per-x 64] [--eta 218] [--width WIDTH] [--max-x MAX_X]
  [--system-qubits SYSTEM_QUBITS] [--salt SALT] [--seed SEED]
  [--batch-size 256] [--max-workers N]
```

### Contract and rejection

- Exactly one register named `x`; 22 qubits for the default instance; distinct qubits only — lines 178-194.
- All scratch qubits return to zero; `x` must be restored — lines 270-282.
- Tracked phase must remain within the 64-bit tolerance — lines 284-295.
- Failed checks raise `AssertionError` or `ValueError`.

### Output and cost

`verify()` returns `status`, `score`, `toffoli_equivalent`, `toffoli_count`, `t_count`, `rotation_count`, `rotation_eps`, `num_qubits`, reaction depth, operations, verified shots, worst error, worst x, and circuit SHA-256 — lines 317-337.

Cost: `score = circuit.num_qubits * (toffoli_count + t_count/4)`; finer rotations cost `0.56 log2(1/eps) + 5.3` T — lines 148-149 and 317-327.

## DQI

**Source:** `external/verifiers/dqi/verify_submission_dqi.py`

### Public API

- `ProblemSpecDQI.benchmark_instance(...)` — lines 65-101.
- `clopper_pearson_upper_bound(k,n,log2_delta=-128)` — lines 139-171.
- `verify(circuit, spec, *, seed=None, salt='', batch_size=256, log2_delta=-128, max_workers=None, shots=None)` — lines 334-439.
- CLI entry: `main()` — lines 447-500.

**Defaults:** `m=4095`, `n=70`, `degree=12`, `r=2016`, `num_shots=102400`, `batch_size=256`, `log2_delta=-128`, `max_workers=4`.

### CLI

```text
python external/verifiers/dqi/verify_submission_dqi.py CIRCUIT.kmb
  [--format auto|kmb|kmx] [--m 4095] [--n 70] [--degree 12] [--r 2016]
  [--num-shots 102400] [--batch-size 256] [--log2-delta -128]
  [--salt SALT] [--seed SEED] [--max-workers 4]
```

### Contract and rejection

- Exactly `S0..S69` quantum registers and `E0..E4094` classical bit registers; all width 12, pairwise disjoint — lines 205-230.
- `Z_POW` is rejected — lines 334-351.
- Syndrome restoration and ancilla cleanliness are checked across shots — lines 377-392.
- `eps_plus >= 1/16` rejects with `AssertionError` — lines 407-414.

### Output and cost

Returns value/phase failures, empirical and effective error rates, repetition factor, toffoli count, `Q=circuit.num_qubits`, operations, and SHA-256 — lines 416-438.

Cost: `R(eps_plus) * Q^2 * T`, with `R(eps)=ln(2)/-ln(1/2+2*sqrt(eps))` — lines 130-136 and 416-420.

## DFTHC-SOS

**Source:** `external/verifiers/dfthcsos/verify.py`

### Public API

- `verify(circuits, factorization=None, tree_edges=None, *, format='auto', shots_per_address=64, seed=None, salt='')` — lines 606-674.
- `evaluate_circuits(...)` — lines 558-604.
- `resource_costs(...)`, `score_from_metrics(...)`, `passes_accuracy(...)` — lines 363-555.
- CLI entry: `main()` — lines 679-743.

### CLI

```text
python external/verifiers/dfthcsos/verify.py RUN_DIR [--format auto|kmb|kmx]
  [--shots-per-address 64] [--salt SALT] [--seed SEED]

python external/verifiers/dfthcsos/verify.py FACTORIZATION.npz CIRCUIT_OR_DIR
  [--tree-edges EDGES.npy|EDGES.npz]
```

### Input and rejection

- The factorization NPZ requires `U`, `W`, `H2_I`, `H1_I`, `Hsym_lower`; submitted `H1_I` and `Hsym_lower` are replaced by fixed baseline shifts — `reference.py` 54-68 and `verify.py` 200-230.
- ANGLE circuits require consistent `selection` and `word_0..word_J-1` qubit registers — `circuits.py` 308-360.
- `Z_POW` is rejected — `circuits.py` 419-429.
- Every address and reverse traversal must restore state and clear workspace — `circuits.py` 438-555.
- Strict residual, gap, Lambda, and qubit checks are in `verify.py` 363-555.

### Output and cost

Cost: `lambda_eff * T_total * Q_total`, where `lambda_eff=sqrt(E_gap*(2*Lambda-E_gap))`. Rejections return infinite score; a successful result is a finite JSON summary — `verify.py` 546-555 and 656-674.
