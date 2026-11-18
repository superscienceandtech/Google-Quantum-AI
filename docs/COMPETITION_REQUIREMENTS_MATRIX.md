# Competition Requirements Matrix

**Date:** 2026-11-18
**Purpose:** Single, source-linked checklist of every authoritative requirement. A submission is valid only if every **MUST** row passes.
**Authority order:** (1) official Kaggle metric code [C3], (2) competition data `verifiers/` [C5], (3) companion paper arXiv:2610.23832 [C4], (4) Kaggle rules/API [C1], (5) this repository's documents. If sources conflict, the verifier's executed behaviour wins; open a ticket rather than guessing.
**Status legend:** `VERIFIED` = primary source cited · `NOT FOUND` = not available from accessible primary sources · `BLOCKED` = cannot be checked locally yet.

Full citations and the NOT FOUND list are in `docs/research/PRIMARY_SOURCE_FINDINGS.md`.

---

## 0. Global / administrative requirements

| ID | Requirement | Source | Status | Current state | Owner (proposed) |
|---|---|---|---|---|---|
| G-01 | Official team size **≤ 5** members | Kaggle API `maxTeamSize: 5` [C1] | VERIFIED | 5 named members nominated; confirmation pending | Yousuf |
| G-02 | **5 submissions/day** maximum | Kaggle API [C1] | VERIFIED | Budget not yet allocated | Yousuf |
| G-03 | Final deadline **2027-01-20T23:59:00Z** | Kaggle API [C1] | VERIFIED | 63 days from audit date | Yousuf |
| G-04 | New-entrant deadline **2027-01-13T23:59:00Z** | Kaggle API [C1] | VERIFIED | 56 days from audit date; registration unconfirmed | Yousuf |
| G-05 | Competition license **Apache 2.0** | Kaggle API [C1], blog [C6] | VERIFIED | Repo has no LICENSE file — add before release | Yousuf / Srijon |
| G-06 | Team registration + rules acceptance | Kaggle rules page [C1] | NOT FOUND (exact text) | Must be done in an authenticated session; anonymous API shows `userHasEntered: false` | Yousuf |
| G-07 | Restricted competition data must not leave the registered team | Kaggle rules page [C1] | NOT FOUND (exact quote) | Treat as binding by default; store data outside git, commit only hashes/sizes | All |
| G-08 | Official metric is "Google Quantum AI Metric" | Kaggle API [C1], metric source [C3] | VERIFIED | No local copy of metric yet | SeyamB |

---

## 1. Submission container (all benchmarks)

| ID | Requirement | Source | Status | Check |
|---|---|---|---|---|
| S-01 | Exactly one `invsqrt.kmx` **or** `invsqrt.kmb` | Metric `find_one()` [C3] | VERIFIED | BLOCKED — file absent |
| S-02 | Exactly one `dqi.kmx` **or** `dqi.kmb` | Metric `find_one()` [C3] | VERIFIED | BLOCKED — file absent |
| S-03 | `dfthcsos/` containing `angle_k_0 … angle_k_{n−1}` as `.kmx`/`.kmb`, exactly one per `k = 0..n−1` | Metric [C3] | VERIFIED | BLOCKED — files absent |
| S-04 | `dfthcsos/submission.npz` with **exactly** the required keys | Metric [C3] | VERIFIED | BLOCKED — file absent |
| S-05 | All registers named; regular files only (no links/FIFOs/devices); `__MACOSX/` ignored | Metric [C3] | VERIFIED | BLOCKED |
| S-06 | Only allowlisted kickmix instructions used | Metric `ALLOWED_INSTRUCTIONS` [C3] | VERIFIED | BLOCKED |
| S-07 | Qubit/bit ids `< MAX_QUBIT_OR_BIT_ID = 2^30 // 1536` | Metric [C3] | VERIFIED | BLOCKED |
| S-08 | `submission.npz` ≤ `MAX_NPZ_BYTES = 2^26` bytes | Metric [C3] | VERIFIED | BLOCKED |
| S-09 | Per-row `seed_salt` is a string of length **≥ 32** | Metric [C3] | VERIFIED | BLOCKED |
| S-10 | `verification_shot_divisor` **must be 1** on Kaggle (local testing only otherwise) | Metric [C3] | VERIFIED | Enforce in harness config |
| S-11 | Verifier-returned `score` must be finite and `> 0` | Metric [C3] | VERIFIED | BLOCKED |

Allowlist (verbatim from [C3]): `X, CX, CCX, Z, CZ, CCZ, Z_POW, NEG, SWAP, CSWAP, R, HMR, BIT_INVERT, BIT_STORE0, BIT_STORE1, PUSH_CONDITION, POP_CONDITION, INFO_TAG, DEBUG_PRINT`. Note `Z_POW` is globally allowlisted but **specifically forbidden inside DFTHC ANGLE circuits** (row D-12).

---

## 2. Benchmark I — INVSQRT

| ID | Requirement / threshold | Source | Status | Check |
|---|---|---|---|---|
| I-01 | Implements `\|x⟩\|0⟩ ↦ exp(2πiβ/√x)\|x⟩\|0⟩` for all `x ∈ [1, 3,133,452]` | Paper §III.1.3 [C4] | VERIFIED | BLOCKED |
| I-02 | Register `"x"`: exactly 1 named register, 22 distinct qubits, restored at output | Paper §III.1.3 [C4]; metric [C3] | VERIFIED | BLOCKED |
| I-03 | Scratch qubits return to `\|0⟩` on every shot | Paper §II.3, §III.1.3 [C4] | VERIFIED | BLOCKED |
| I-04 | `n_p = 10`, `β = 1`; verifier uses `ProblemSpecInvSqrt.for_n_p(10)` | Paper §III.1.3 [C4]; metric [C3] | VERIFIED | Fixed by verifier |
| I-05 | Phase within `tol(x) = 2^−24 β/√x` turns; checked as `⌊2^65 β/√x⌋` in `2^−64`-turn `uint64` units | Paper §III.1.3 [C4] | VERIFIED | BLOCKED |
| I-06 | 64 shots per `x`, 200,540,928 total shots; **every shot must pass** (`k = 0`) | Paper §III.1.3 [C4] | VERIFIED | BLOCKED |
| I-07 | Cost `S = Q × C`, `C = Toffolis + T/4`; lower is better | Paper §III.1.3 [C4] | VERIFIED | Not measured |
| I-08 | Rotation pricing: Clifford `Z_POW` free; `T` = 1; finer rotations `0.56 log₂(1/ε) + 5.3` T | Paper §III.1.3 [C4] | VERIFIED | Must be reproduced by verifier, not by local estimate |
| I-09 | Reference: `Q=260`, 7,735 Toffolis, 11 T, 37 `Z_POW`, `C≈7,988`, `Q×C≈2.08e6` | Paper §III.1.2 [C4] | VERIFIED (literature) | Host baseline may differ — measure, do not assume |
| I-10 | No non-Clifford instruction outside the allowlist | Metric [C3] | VERIFIED | BLOCKED |

---

## 3. Benchmark II — DQI

| ID | Requirement / threshold | Source | Status | Check |
|---|---|---|---|---|
| D-01 | Instance `RS(4095,4025)` over `GF(2^12)`, `(m,n,b,r)=(4095,70,12,2016)` | Paper §III.2.2 Eq. (39) [C4] | VERIFIED | Fixed by verifier |
| D-02 | Contract `U_c\|s⟩\|0⟩_W = (−1)^{c·bin(e(s))}\|s⟩\|0⟩_W`, `s = Bᵀe`, `wt(e) ≤ ℓ` | Paper §III.2.1 Eq. (38) [C4] | VERIFIED | BLOCKED |
| D-03 | Syndrome preserved; workspace `W` clean; target phase correct | Paper §III.2.1, §III.2.3 [C4] | VERIFIED | BLOCKED |
| D-04 | Syndrome width 840 qubits; `c` = 49,140 classical bits | Paper §III.2.2 [C4] | VERIFIED | Fixed by verifier |
| D-05 | Register count limited to `dqi_spec.n + dqi_spec.m` (`S_i` and `E_j`) | Metric [C3] | VERIFIED | BLOCKED |
| D-06 | Verifier samples `e ~ \|a_e\|²`, computes `s`, samples `c` uniformly | Paper §III.2.3 [C4] | VERIFIED | Fixed by verifier |
| D-07 | `N = 102,400` shots; Clopper–Pearson upper bound at `1 − 2^−128` | Paper §III.2.3, §II.3 Eq. (4) [C4] | VERIFIED | Shot divisor must be 1 (S-10) |
| D-08 | `ε⁺ ≥ 1/16` ⇒ **no finite score** (rejection) | Paper §III.2.3 [C4] | VERIFIED | BLOCKED |
| D-09 | Cost `S = R(ε⁺) Q² T`, `R(ε) = ln2/(−ln(1/2 + 2√ε))` | Paper Eq. (43) [C4] | VERIFIED | Not measured |
| D-10 | Zero-failure floor `ε⁺ ≈ 8.7e−4`, `R ≈ 1.19` | Paper §III.2.3 [C4] | VERIFIED | Reference point only |
| D-11 | `Q` includes syndrome **and** workspace; `T` is single-run Toffoli count including cleanup | Paper §III.2.3 [C4] | VERIFIED | Critical for accounting |
| D-12 | Numeric `DEFAULT_NUM_SHOTS`, `DEFAULT_BATCH_SIZE` **NOT FOUND** | Metric [C3], evidence [C8] | NOT FOUND | Read from competition data before claiming exact shot config |

---

## 4. Benchmark III — DFTHC-SOS

| ID | Requirement / threshold | Source | Status | Check |
|---|---|---|---|---|
| D-13 | Cost `S = λ_eff · T_tot · Q_tot`, `λ_eff = √(E_gap(2Λ − E_gap))` | Paper §III.3.2 Eq. (44), §III.3.7 Eq. (78) [C4] | VERIFIED | Not measured |
| D-14 | `ε₁ = ‖h̃⁽¹⁾′ − h⁽¹⁾′‖_F ≤ 0.020 Ha` | Paper Eqs. (74)–(75) [C4] | VERIFIED | BLOCKED |
| D-15 | `ε₂ = ‖Σ_{ρ,c} X^{(ρc)}⊗X^{(ρc)} − h⁽²⁾ − 𝒯(S₀)‖_F ≤ 0.020 Ha` | Paper Eqs. (74)–(75) [C4] | VERIFIED | BLOCKED |
| D-16 | `Λ > 49.0 Ha` (strict; equality rejected) | Paper §III.3.2, Eqs. (76)–(77) [C4] | VERIFIED | BLOCKED |
| D-17 | `E_gap > 3.914898 Ha` (strict) and `0 < E_gap < 2Λ` | Paper §III.3.2, Eqs. (76)–(77) [C4] | VERIFIED | BLOCKED |
| D-18 | `E_upper = −22140.27335 Ha` fixed, core-inclusive; `E_gap = E_upper − E_SOS` | Paper §III.3.2 [C4] | VERIFIED | Fixed by verifier |
| D-19 | **Every** `Angles_k` circuit ≤ 128 qubits (`dfthcsos_verify.QUBIT_CAP`); over-cap ⇒ infinite cost | Paper §III.3.2 [C4]; metric [C3] | VERIFIED | BLOCKED |
| D-20 | `Q_tot` includes persistent + largest workspace; **not** capped at 128 | Paper §III.3.7 [C4] | VERIFIED | Accounting rule |
| D-21 | `T_tot` = forward + reverse `Angles_k` Toffolis + `Outer`, `Inner`, `N−1` Givens heuristics | Paper §III.3.2 [C4] | VERIFIED | Accounting rule |
| D-22 | `selection` register width `⌈log₂(N+RB)⌉`; values `a < N+RB`; first `N` one-body, last `RB` two-body | Paper §III.3.4 [C4] | VERIFIED | BLOCKED |
| D-23 | Each `word_j` register `β` qubits, fixed-point `[0,2)`, 1 integer + `β−1` mantissa bits; consistent across all `k` | Paper §III.3.4 [C4] | VERIFIED | BLOCKED |
| D-24 | Addresses unchanged; workspace clean at start and end; `Z_POW` **forbidden** in ANGLE circuits | Paper §III.3.4 [C4] | VERIFIED | BLOCKED |
| D-25 | Simulation: every valid vector address forward + reverse, 64 samples/address; phases corrected | Paper §III.3.7 [C4] | VERIFIED | Shot divisor = 1 (S-10) |
| D-26 | `npz` keys exactly: `U(R,B,ORBITALS)`, `W(R,B,C)`, `H2_I(R,C)`, `H1_I()`, `Hsym_lower(ORBITALS(ORBITALS+1)/2)`, `tree_edges(ORBITALS−1,2) uint` | Metric [C3] | VERIFIED | BLOCKED |
| D-27 | `ORBITALS = N = 76`; `η = 113`; `S = S₀`, `β₁ = β₁,₀` fixed | Paper §III.3.7 [C4] | VERIFIED | Fixed by verifier |
| D-28 | Factorization, angle words and circuits must be mutually consistent (same `R,B,C`, same angle map, same tree) | Paper §III.3.2–§III.3.7 [C4]; metric [C3] | VERIFIED | BLOCKED |
| D-29 | Any failed check ⇒ infinite score (not clamped); values not clamped to floors | Paper §III.3.7 Eq. (78) [C4] | VERIFIED | Submit-time critical |
| D-30 | Baseline `R,B,C = 65,60,60`; numeric `SHOTS_PER_ADDRESS`, `QUBIT_CAP` | Mixed sources | **UNVERIFIED** | Read from competition data before use as control [C8] |

---

## 5.Verification model requirements (all benchmarks)

| ID | Requirement | Source | Status |
|---|---|---|---|
| V-01 | Fuzz testing over computational-basis inputs with `km.Simulator`; compare bitstrings, phases, cleanliness | Paper §II.3 [C4] | VERIFIED |
| V-02 | Failure probability `ε`; trace distance `≤ 2√ε` under distinct-output assumption | Paper §II.3 Eqs. (2)–(3) [C4] | VERIFIED |
| V-03 | Clopper–Pearson upper bound at `δ = 2^−128`; `ε⁺ ≈ 88.7/N` for `k = 0` | Paper §II.3 Eq. (4) [C4] | VERIFIED |
| V-04 | SHA-256(circuit) + private salt seeds PRNG; deterministic and non-interactive | Paper §II.3 [C4] | VERIFIED |
| V-05 | Fuzz testing is **not** formal proof of equivalence | Blog [C6]; paper §II.3 [C4] | VERIFIED |
| V-06 | Verifications run in random order; per-split secret salts | Metric [C3] | VERIFIED |
| V-07 | Standalone CLI verifier invocation flags | — | **NOT FOUND** [C8] — use metric Python API only until verified |

---

## 6. Authoritative verifier invocations (from metric source [C3])

```python
from dfthcsos import verify as dfthcsos_verify
from dqi import verify_submission_dqi
from invsqrt import verify_submission_invsqrt

verify_submission_invsqrt.verify(invsqrt, verify_submission_invsqrt.ProblemSpecInvSqrt.for_n_p(10), salt=salt)
verify_submission_dqi.verify(dqi, dqi_spec, salt=salt)
dfthcsos_verify.verify(angle_circuits, npz, tree_edges, salt=salt,
                       shots_per_address=max(1, dfthcsos_verify.SHOTS_PER_ADDRESS // shot_divisor))
```

`dqi_spec` construction (same source):

```python
batches = max(1, verify_submission_dqi.DEFAULT_NUM_SHOTS
                 // verify_submission_dqi.DEFAULT_BATCH_SIZE // shot_divisor)
dqi_spec = verify_submission_dqi.ProblemSpecDQI.benchmark_instance(
    num_shots=batches * verify_submission_dqi.DEFAULT_BATCH_SIZE)
```

Do not substitute invented CLI flags for these calls. If a standalone CLI is discovered in competition data, record the exact command in `EXPERIMENT_AND_SCORE_TRACKER.md` before use.

---

## 7. How to use this matrix

1. Before any experiment: copy the relevant row IDs into the experiment record in `EXPERIMENT_AND_SCORE_TRACKER.md`.
2. A candidate is "valid" only when every applicable MUST row is checked by an **authoritative verifier run** with `shot_divisor = 1` and a ≥32-character salt.
3. Rows marked BLOCKED remain BLOCKED until competition data is obtained; a local approximation is not a substitute.
4. Any change to a threshold must be backed by a new primary-source citation and an ADR in `ARCHITECTURE_DECISION_LOG.md`.
