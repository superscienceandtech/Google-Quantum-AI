# Baseline Reproduction Report

**Date:** 2026-11-18
**Scope:** INVSQRT, DQI, DFTHC-SOS baseline reproduction attempts using only authorized official material.
**Execution status:** reconciled on 2026-11-19.
- INVSQRT and DFTHC-SOS have official full verifier executions recorded in `results/raw/`.
- Under strict baseline-evidence rules, neither is promoted to `BASELINE REPRODUCED` because timestamp, verifier provenance, and/or complete execution metadata are incomplete.
- DQI has no 102,400-shot execution.
**Overall decision:** `BLOCKED`

---

## 0. Attempt summary

| Benchmark | Contract reviewed | Official baseline available locally | Verifier run | Decision |
|---|---|---|---|---|
| INVSQRT | Yes | Yes; official full sample execution | Official full execution | `NOT REPRODUCED` under strict provenance rules |
| DQI | Yes | No 102,400-shot execution | Diagnostic only | `BLOCKED` |
| DFTHC-SOS | Yes | Yes; official full sample execution | Official full execution | `NOT REPRODUCED` under strict provenance rules |

Historical blocker chain: the older 2026-11-18 report assumed official data was unavailable. The reconciled 2026-11-19 audit confirms the data and verifiers are locally present. Missing timestamp and provenance evidence prevents strict baseline promotion.

Evidence: `BASELINE_ENVIRONMENT_AUDIT.md` §6, `BASELINE_ARTIFACT_INVENTORY.md` §1–3, `PRIMARY_SOURCE_FINDINGS.md:317-323`.

---

## D1. INVSQRT

### Contract review (authoritative, not executed)

| Item | Status | Evidence |
|---|---|---|
| Input domain `x ∈ [1, 3,133,452]`, `n_p=10`, `β=1`, 22-bit `x` | `VERIFIED` from paper | `PRIMARY_SOURCE_FINDINGS.md:51,228`, matrix I-01/I-04 |
| Register name `"x"`, exactly 1 named register, 22 distinct qubits, restored | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:228-230`, matrix I-02 |
| Output phase `exp(2πiβ/√x)`; tolerance `2^-24 β/√x` turns; `uint64` phase check | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:153,224-228`, matrix I-05 |
| Scratch restoration / every shot passes (`k=0`) | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:51,122,153`, matrix I-03/I-06 |
| 64 shots per `x`, 200,540,928 total shots | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:51`, matrix I-06 |
| Allowed operations / metric allowlist | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:206-218`; matrix S-06/I-10 |
| Cost `S = Q×C`, `C = Toffolis + T/4`; finer rotations priced `0.56 log₂(1/ε)+5.3` T | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:31-49`, matrix I-07/I-08 |
| Literature reference `Q=260`, Toffolis=7,735, T=11, `Z_POW`=37, `C≈7,988`, `S≈2.08e6` | `VERIFIED (literature only)` | `PRIMARY_SOURCE_FINDINGS.md:53`, matrix I-09 |

### Reproduction record

| Field | Value |
|---|---|
| Official baseline artifact | `external/sample_submission/invsqrt.kmb` |
| Artifact checksum | `e2bf8eb64350a4460a271fc7f1d591ef125b1e276377e9a0f64b96ab3ca321e1` |
| Verifier source / SHA-256 | `external/verifiers/invsqrt/verify_submission_invsqrt.py` / `ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a` |
| Full-shot domain | 200,540,928 shots; 64 shots for each x in `1..3,133,452` |
| Qubit count `Q` | 260 |
| Toffoli count | 7,735 |
| T-equivalent rotation cost / `C` | 7,987.593206597238 |
| Total score | 2,076,774.233715282 |
| Verification result | Official verifier stdout: `PASS` |
| Exit code | 0 |
| Runs | `BASE-INVSQRT-001` and `BASE-INVSQRT-002`, matching PASS metrics |
| Runtime | 001: 11:09.85 / 523,348 KB max RSS; 002: 11:30.13 / 523,844 KB max RSS |
| Raw logs | 001 stdout + stderr/time; 002 stdout + `.time.txt` (stderr empty) |
| Decision | `NOT REPRODUCED` under strict baseline provenance rules |

The raw result is an official full-domain verifier execution, not merely a sample parse or partial diagnostic. It is not promoted to `BASELINE REPRODUCED` because the evidence package lacks start/finish timestamps and a complete independent experiment record.

---

## D2. DQI

### Contract review (authoritative, not executed)

| Item | Status | Evidence |
|---|---|---|
| `RS(4095,4025)` over `GF(2^12)`, `(m,n,b,r)=(4095,70,12,2016)` | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:70`, matrix D-01 |
| Syndrome width 840; classical record `c` 49,140 bits | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:70,243`, matrix D-04 |
| Contract `U_c|s⟩|0⟩_W = (−1)^{c·bin(e(s))}|s⟩|0⟩_W`; syndrome preserved; workspace clean | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:234-245`, matrix D-02/D-03 |
| Register count `dqi_spec.n + dqi_spec.m` | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:245`, matrix D-05 |
| Shots `N=102,400`; one-sided Clopper–Pearson bound at `1−2^-128`; `ε⁺≥1/16` rejects | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:68,131,154`, matrix D-07/D-08 |
| Official implementation only; no approximation substituted | `VERIFIED` requirement | `PRIMARY_SOURCE_FINDINGS.md:124-131`, matrix D-07 |
| Cost `S = R(ε⁺)Q²T`, `R = ln2/(−ln(1/2+2√ε))` | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:57-66`, matrix D-09 |
| `Q` includes syndrome + workspace; `T` includes cleanup | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:66`, matrix D-11 |
| Numeric `DEFAULT_NUM_SHOTS`, `DEFAULT_BATCH_SIZE` | `NOT FOUND` | `PRIMARY_SOURCE_FINDINGS.md:181-185,320`, matrix D-12 |

### Reproduction record

| Field | Value |
|---|---|
| Official baseline artifact | `external/sample_submission/dqi.kmb` |
| Artifact checksum | `959471d05a26373b4f14ca0cae2d8639ea25f18170d9f6532139aa51ccc04995` |
| Verifier source / SHA-256 | `external/verifiers/dqi/verify_submission_dqi.py` / `f14274bc0943fb9769ddb01131be6063191a15009fe1caf1d4bdd9fd25194e65` |
| `Q` | 1,893 qubits in the submitted circuit |
| `T` | Not measured by a 102,400-shot official run |
| Observed failures `k` | 0 in the bounded 256-shot and 1024-shot diagnostics |
| Shot count | 102,400 required; no official 102,400-shot execution |
| Confidence bound `ε⁺` | Not measured from 102,400 shots |
| Score | Not measured |
| Verification result | Diagnostic failures from low-shot confidence bounds |
| Runtime | Diagnostics only |
| Raw log | `results/raw/SMOKE-DQI-256b.*`, `results/raw/SMOKE-DQI-1024b.*` |
| Decision | `BLOCKED` |

No unofficial confidence-bound implementation was used.

---

## D3. DFTHC-SOS

### Contract review (authoritative, not executed)

| Item | Status | Evidence |
|---|---|---|
| Input artifacts: raw integrals, reference factorization, boolean-oracle circuits, address-to-bit-string map, tree | `VERIFIED` as required artifacts; local availability `NOT AVAILABLE` | `PRIMARY_SOURCE_FINDINGS.md:286`, matrix D-26/D-28 |
| `submission.npz` exact keys/shapes: `U(W,B,ORBITALS)`, `W(R,B,C)`, `H2_I(R,C)`, `H1_I()`, `Hsym_lower(...)`, `tree_edges(...)` | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:253-266`, matrix D-26 |
| `N=76`, `η=113`, `S=S₀`, `β₁=β₁,₀` fixed | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:104`, matrix D-27 |
| `Λ>49.0`, `E_gap>3.914898`, `0<E_gap<2Λ`; strict floors | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:102`, matrix D-16/D-17 |
| Residuals `ε₁,ε₂ ≤0.020 Ha`; any failure ⇒ infinite score | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:92-102,155`, matrix D-14/D-15/D-29 |
| ANGLE structure: named `selection`, `word_j`; `Z_POW` forbidden; ≤128 qubits; clean workspace; addresses unchanged | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:249-251`, matrix D-19/D-22/D-23/D-24 |
| Simulation 64 samples/address forward + reverse | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:251`, matrix D-25 |
| Cost `S = λ_eff T_tot Q_tot`, `λ_eff=√(E_gap(2Λ−E_gap))`; `Q_tot` not capped at 128 | `VERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:74-90`, matrix D-13/D-20/D-21 |
| Baseline `R,B,C=65,60,60` | `UNVERIFIED` | `PRIMARY_SOURCE_FINDINGS.md:292,322`, matrix D-30 |
| Numeric `SHOTS_PER_ADDRESS`, `QUBIT_CAP` from source | `NOT FOUND` | `PRIMARY_SOURCE_FINDINGS.md:268,321` |

### Reproduction record

| Field | Value |
|---|---|
| Official baseline submission | `external/sample_submission/dfthcsos/` |
| Submission checksum | `14d5cc25eb3bf82a9ccb87c811db28d127bef6d28697dd190dc1e875de3bfe69` |
| Verifier source / checksum | `external/verifiers/dfthcsos/verify.py` / `0775be7a528922367caebe9e4d051d6199811f1aefeaa4b793eaaa4621b8ec9d` |
| FCIDUMP checksum | `e5a48af746fd075026dec9e8f5df2d363802a121e8c53af9a0b984bde695e1bd` |
| Fixed shifts checksum | `7b7facf63fe35a9d9d3d00787ffdb700c863fa845fe4724d7f7c54778151cd87` |
| `R,B,C` | `(65,60,60)` in the official sample submission |
| `Λ` | 308.4559397330944 Ha |
| `E_gap` | 3.965477244291833 Ha |
| Residuals `ε₁,ε₂` | 0.0031851950317991775 and 0.018639570630974073 Ha |
| Number of ANGLE circuits | 10 |
| Maximum ANGLE qubits | 119 |
| Toffoli count / `T_tot` | 93,237 |
| `Q_tot` | 730 |
| `λ_eff` | 49.30136925057438 |
| Final score | 3,355,599,588.3155365 |
| Verification result | Official verifier stdout: `PASS` |
| Exit code | 0 |
| Runs | `BASE-DFTHCSOS-002` and `BASE-DFTHCSOS-003`, matching PASS metrics |
| Runtime | 002: 1:44.26 / 1,113,308 KB max RSS; 003: 2:13.41 / 1,112,216 KB max RSS |
| Raw logs | 002 stdout + stderr/time; 003 stdout + `.time.txt` (stderr empty) |
| Decision | `NOT REPRODUCED` under strict baseline provenance rules |

No documentation metric was promoted to a measured result.

---

## Final decisions

| Benchmark | Decision |
|---|---|
| INVSQRT | `NOT REPRODUCED` under strict provenance rules; official full execution exists |
| DQI | `BLOCKED`; 102,400-shot execution absent |
| DFTHC-SOS | `NOT REPRODUCED` under strict provenance rules; official full execution exists |
| Overall | `BLOCKED` |

**Optimization is not authorized.**
