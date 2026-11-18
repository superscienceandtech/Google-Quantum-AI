# Score Model Verification

All formulas below are independently sourced from the official verifier implementations. Existing raw output is kept separate from derived formulas.

## INVSQRT

Source: `external/verifiers/invsqrt/verify_submission_invsqrt.py`

- `Q = circuit.num_qubits` — 330-334.
- Mean Toffoli-like gates: `toffoli_count` — 317.
- Base T and fallback rotation T: `t_count` — 318-323.
- `C = toffoli_count + t_count/4` — 324-325.
- `score = Q*C` — 327.
- Rotation cost: `0.56*log2(1/eps)+5.3` — 148-149.

The official sample run reports `Q=260`, mean Toffoli count `7735`, `C=7987.593206597238`, and score `2076774.233715282` in `results/raw/BASE-INVSQRT-002.stdout.txt`.

## DQI

Source: `external/verifiers/dqi/verify_submission_dqi.py`

- `k = value_errors + phase_errors` — 407.
- `eps_hat=k/N` — 407.
- `eps_plus=clopper_pearson_upper_bound(k,N,log2_delta)` — 139-171 and 408.
- Rejection: `eps_plus >= 1/16` — 410-414.
- `R(eps)=ln(2)/-ln(1/2+2*sqrt(eps))` — 130-136.
- `T=mean Toffoli-like operations per shot` — 416.
- `Q=circuit.num_qubits` — 417.
- `score=R(eps_plus)*Q^2*T` — 420.

Official constants: `N=102400`, batch size `256`, log2 delta `-128`, `m=4095`, `n=70`, `degree=12`, `r=2016` — lines 52-58 and 85-101.

No measured 102,400-shot DQI baseline exists.

## DFTHC-SOS

Source: `external/verifiers/dfthcsos/verify.py`, `reference.py`, and `circuits.py`.

- Residual limits: `error_1 <= 0.020 Ha`, `error_2 <= 0.020 Ha` — verify.py 120-123.
- Strict Lambda floor: `Lambda > 49.0 Ha` — verify.py 125-130.
- Strict gap floor: `E_gap > 3.914898 Ha` and `0<E_gap<2*Lambda` — verify.py 125-130.
- `lambda_eff=sqrt(E_gap*(2*Lambda-E_gap))` — verify.py 546-555.
- ANGLE width cap: 128 qubits — verify.py 132-134.
- ANGLE shots/address: 64 — circuits.py 399.
- `T_total=ANGLE forward+reverse Toffolis + outer prep + inner prep + Givens heuristics` — verify.py 472-516.
- `Q_total=persistent state-prep + ANGLE word + maximum temporary workspace` — verify.py 472-516.
- `score=lambda_eff*T_total*Q_total` — verify.py 546-555.
- Any rejection returns `inf`.

The official sample run reports a finite score of `3355599588.3155365`, `lambda_eff=49.30136925057438`, `T_total=93237`, `Q_total=730`, and 254,464 verified shots in `results/raw/BASE-DFTHCSOS-003.stdout.txt`.
