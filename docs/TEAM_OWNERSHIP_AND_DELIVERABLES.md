> **Historical draft — superseded for current team assignments.** This document
> reflects an earlier five-person proposal and contains roles/attributions that
> are not current acceptance evidence. Use the current
> [six-member team structure](TEAM/TEAM_STRUCTURE.md),
> [responsibility matrix](TEAM/TEAM_RESPONSIBILITY_MATRIX.md), and
> [task board](TEAM/TEAM_TASK_BOARD.md) for all proposed scopes and status.
> Do not use the historical roster, team-size assumptions, or task attributions
> below to infer current membership, ownership, or acceptance. Verify any
> competition eligibility rule against its current official source before use.

# Team Ownership & Deliverables

**Date:** 2026-11-18
**Critical status note:** every assignment below is **PROPOSED**, not confirmed. The MASTER PROMPT names five official members and five responsibility areas, but does not state that any member has accepted an assignment. Only Yousuf's written sign-off in the confirmation table (§6) changes a label to `CONFIRMED` (ADR-009).
**Team-size rule:** Kaggle competition id 161954 has `maxTeamSize: 5` [C1]. All five named members are already counted; **no sixth person may be added**, and no restricted competition data may be transferred to anyone outside the registered five (G-07; exact rules quote `NOT FOUND` [C8], conservative default applied).

---

## 1. Ownership summary

| Member | Proposed responsibility area | Accountable for tasks | Confirmation |
|---|---|---|---|
| **Yousuf** | Overall architecture, research leadership, integration, release | OWN-01, OWN-02, OWN-03 | PROPOSED (role given in brief) |
| **Sonjoy** | Optimisation research and AI/ML support | OWN-04, OWN-05 | PROPOSED |
| **Srijon** | Compiler engineering and infrastructure | OWN-06, OWN-07 | PROPOSED |
| **SeyamB** | Verification, testing and data quality | OWN-08, OWN-09 | PROPOSED |
| **Mahin** | Quantum mathematics and research analysis | OWN-10, OWN-11 | PROPOSED |

Every task below has exactly one accountable owner. "Reviewer" is responsible for review, not for doing the work.

---

## 2. Yousuf — architecture, research leadership, integration, release

### OWN-01 — Unblock authoritative verification and governance
- **Scope:** accept Kaggle rules; confirm team registration before 2027-01-13; authorise credential setup; confirm the data-handling policy; approve submission schedule (5/day).
- **Deliverables:** signed confirmation table §6; Kaggle registration screenshot/metadata (metadata only, no secrets); written data-handling rule; submitted-experiment calendar.
- **Dependencies:** none (critical path start).
- **Acceptance criteria:** authenticated Kaggle view shows team entered and 5 members; rules accepted; `kaggle` CLI authenticated by an authorised member; no restricted data in git.
- **Deadline:** 2026-11-20 (48 h) — risks R-01, R-03, R-07.
- **Review responsibility:** self + all members acknowledge.

### OWN-02 — Architecture, ADRs, risk and roadmap ownership
- **Scope:** maintain the ten master documents; accept/reject ADRs; re-rank research priorities after baseline measurement; chair daily stand-up while R-01 is open.
- **Deliverables:** accepted ADR set; updated risk register; weekly prioritisation note with score evidence.
- **Dependencies:** OWN-01 (for evidence-based re-ranking; documents themselves already drafted).
- **Acceptance criteria:** every external-contract claim has a primary-source citation; no `NOT FOUND` fact promoted to `VERIFIED` without new evidence.
- **Deadline:** continuous; first review 2026-11-21.
- **Review responsibility:** SeyamB reviews citations; Mahin reviews mathematical statements.

### OWN-03 — Integration and final release
- **Scope:** merge gate from `develop` to `main`; assemble the submission container; approve each of the ≤5 daily uploads; final QA.
- **Deliverables:** release checklist sign-off in `MASTER_RELEASE_GOVERNANCE.md`; submission SHA-256 manifest; rollback point.
- **Dependencies:** OWN-06, OWN-08, OWN-10 and all research tasks complete with authoritative PASS.
- **Acceptance criteria:** full three-benchmark verifier PASS on a clean checkout; all S-*, I-*, D-*, V-* rows in `COMPETITION_REQUIREMENTS_MATRIX.md` green; best-known pointers recorded.
- **Deadline:** target 2027-01-10; hard stop 2027-01-20T23:59:00Z [C1].
- **Review responsibility:** SeyamB (verification) + Srijon (build reproducibility).

---

## 3. Sonjoy — optimisation research and AI/ML support

### OWN-04 — INVSQRT optimisation hypotheses H1.1–H1.3
- **Scope:** design and run controlled experiments on `Q`, rotation budget `n_rot`, and Toffoli retuning; use AI/ML search only inside a fixed, recorded hypothesis and variable set.
- **Deliverables:** one experiment record per run in `experiments/records/`; pre-registered PASS/FAIL; resource vector per run; a ranked findings note with verifier evidence.
- **Dependencies:** OWN-01, OWN-08 (baseline reproduction), OWN-06 (harness).
- **Acceptance criteria:** every claim tied to an authoritative verifier `score`; local estimates labelled `UNVERIFIED`; no best-known promotion without a WIN.
- **Deadline:** first results 2026-12-08; research freeze 2027-01-05.
- **Review responsibility:** Mahin (phase-error math), SeyamB (verifier evidence).

### OWN-05 — AI/ML search harness support (cross-benchmark, tooling only)
- **Scope:** build search/surrogate tooling that proposes candidate configurations for the three benchmark generators; **no algorithm sharing** between benchmarks (ADR-002).
- **Deliverables:** search interface with fixed variable schema; seeded, reproducible proposal logs; integration with `experiments/runner`.
- **Dependencies:** OWN-06.
- **Acceptance criteria:** every proposal reproducible from recorded seed; output cannot bypass preflight or registry gates.
- **Deadline:** 2026-12-15.
- **Review responsibility:** Srijon.

---

## 4. Srijon — compiler engineering and infrastructure

### OWN-06 — Harness, preflight, registry, environment pinning (T5)
- **Scope:** implement `harness/*`, `experiments/runner`, `artifacts/registry`, `.gitignore`, pinned environment, Apache-2.0 LICENSE, CI preflight. Adapter must mirror the metric API exactly (ADR-001, ADR-006).
- **Deliverables:** working clean-room build; pinned `environment.yml`; one command per benchmark (`harness.verify`); append-only registry; CI checks.
- **Dependencies:** OWN-01 (data access for signature confirmation; preflight-only mode allowed before that).
- **Acceptance criteria:** hard-fails on `shot_divisor != 1`, salt <32 chars, disallowed instructions, npz schema mismatch; no restricted data committed; `git diff --check` clean.
- **Deadline:** first usable harness 2026-11-25; hardened 2026-12-01.
- **Review responsibility:** SeyamB.

### OWN-07 — DQI circuit engineering (H2.1–H2.2)
- **Scope:** implement the Reed–Solomon syndrome decoder generator; workspace/syndrome accounting; `Q²T` frontier sweep; enforce the trade-off law from `RESEARCH_OPTIMIZATION_STRATEGY.md` §2.1.
- **Deliverables:** generator package under `benchmarks/dqi/`; frontier table `(ΔQ, T, ε⁺, score)`; authoritative experiment records.
- **Dependencies:** OWN-06; OWN-08 for baseline.
- **Acceptance criteria:** workspace clean, syndrome preserved, phase correct; ε⁺ < 1/16; score > control only counts with verifier evidence.
- **Deadline:** first results 2026-12-12; research freeze 2027-01-05.
- **Review responsibility:** Mahin (decoder math), SeyamB (verification).

---

## 5. SeyamB — verification, testing and data quality

### OWN-08 — Baseline reproduction and score audit (T1)
- **Scope:** with data from OWN-01, reproduce the three host baselines at score 1.0 using the metric API calls; record every constant that was `NOT FOUND` (`DEFAULT_NUM_SHOTS`, `DEFAULT_BATCH_SIZE`, `SHOTS_PER_ADDRESS`, `QUBIT_CAP`, DFTHC `R,B,C`).
- **Deliverables:** three baseline records with full verifier output, artifact SHA-256s, resource counts; updated `contracts` constants with source hash.
- **Dependencies:** OWN-01, OWN-06 (preflight/harness).
- **Acceptance criteria:** host baselines return finite score = 1.0 (within metric rounding); all constants sourced from competition data, not literature; any discrepancy escalated as R-01/R-05.
- **Deadline:** 2026-11-27 — gating every research task.
- **Review responsibility:** Yousuf.

### OWN-09 — Verification runs, test suite and data quality (T7, R-06, R-15)
- **Scope:** execute all authoritative verifier runs within the 5/day budget; own experiment/tracker record integrity; multi-salt robustness runs; verifier-version hashes; `tests/` suite using synthetic fixtures.
- **Deliverables:** signed experiment records; tracker aggregate view; regression suite; data-quality checklist; metric/verifier SHA log.
- **Dependencies:** OWN-01, OWN-06.
- **Acceptance criteria:** no `PASS` label without an official run; every record includes salt id (not value), divisor, verifier hash, and PASS/FAIL criteria recorded *before* the run.
- **Deadline:** continuous from 2026-11-27; final audit 2027-01-12.
- **Review responsibility:** Yousuf.

---

## 6. Mahin — quantum mathematics and research analysis

### OWN-10 — DFTHC mathematical analysis and factorization hypotheses H3.1–H3.4
- **Scope:** analyse feasible `(Λ, E_gap, ε₁, ε₂)` region; derive `λ_eff` sensitivity; search factorizations and tree structures; co-design angle-word precision with residual budget.
- **Deliverables:** mathematical note with derivations from [C4] Eqs. (44), (74)–(78); factorization candidates + npz schema validation; authoritative experiment records for H3.x.
- **Dependencies:** OWN-01, OWN-08 (baseline constants), OWN-06.
- **Acceptance criteria:** strict thresholds respected (`Λ>49.0`, `E_gap>3.914898 Ha`, residuals ≤0.020 Ha, ANGLE ≤128); no empirical result described as proof; consistency of npz/angles/tree.
- **Deadline:** first feasibility note 2026-12-04; first verifier results 2026-12-10; research freeze 2027-01-05.
- **Review responsibility:** Yousuf (architecture), SeyamB (verifier evidence).

### OWN-11 — Cross-benchmark mathematical review
- **Scope:** review phase-error/tolerance arguments (INVSQRT), Clopper–Pearson/`R(ε)` reasoning (DQI), and SOS/LCU derivations (DFTHC); verify all equations quoted in docs match [C4].
- **Deliverables:** review notes with equation anchors; corrections logged as ADRs or doc edits.
- **Dependencies:** none (can start immediately from the paper).
- **Acceptance criteria:** every mathematical claim in the master docs has a section/equation citation; derived inequalities (e.g. `∂λ_eff/∂Λ > 0`) shown explicitly.
- **Deadline:** 2026-11-25.
- **Review responsibility:** Yousuf.

---

## 7. RACI summary

| Task | Yousuf | Sonjoy | Srijon | SeyamB | Mahin |
|---|---|---|---|---|---|
| OWN-01 rules/credentials | **A/R** | C | C | C | C |
| OWN-02 architecture/ADRs | **A/R** | C | C | C | C |
| OWN-03 integration/release | **A/R** | C | C | C | C |
| OWN-04 INVSQRT research | A | **R** | C | C | C |
| OWN-05 AI/ML tooling | A | **R** | C | I | I |
| OWN-06 harness/infra | A | C | **R** | C | I |
| OWN-07 DQI circuits | A | C | **R** | C | C |
| OWN-08 baseline reproduction | A | I | C | **R** | C |
| OWN-09 verification/testing | A | C | C | **R** | C |
| OWN-10 DFTHC research | A | I | C | C | **R** |
| OWN-11 math review | A | C | I | C | **R** |

`A` = accountable, `R` = responsible, `C` = consulted, `I` = informed. Each row has exactly one `A` and one `R`.

---

## 8. Confirmation log (edit only with Yousuf's written approval)

| Member | Assignment accepted? | Date | Signature / channel | Status |
|---|---|---|---|---|
| Yousuf | — | — | Brief defines team-lead role | PROPOSED |
| Sonjoy | No response recorded | — | — | PROPOSED |
| Srijon | No response recorded | — | — | PROPOSED |
| SeyamB | No response recorded | — | — | PROPOSED |
| Mahin | No response recorded | — | — | PROPOSED |

Do not report any assignment as confirmed until this table is updated.

---

## 9. Data-sharing rules for all members

1. Only the five registered members may access competition data.
2. Restricted data stays in gitignored `external/`; never commit `*.kmx`, `*.kmb`, `submission.npz`, raw integrals, or `kaggle.json`.
3. Commit only SHA-256, byte sizes, and derived metadata; share verifier output appendices through the experiment tracker.
4. No transfer of restricted data to unauthorized persons, external services, or public artifacts.
5. The exact Kaggle rules-page quote is `NOT FOUND` in the accessible primary sources [C8]; these rules are the conservative default and must be replaced by the exact wording once OWN-01 obtains it.
