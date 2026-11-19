# Official Scoring Integration

- **Status:** the global geometric-mean formula is **VERIFIED OFFICIAL** in the
  inspected metric source and **VERIFIED LOCALLY** in this helper. Full scorer
  equivalence and runtime integration are **BLOCKED**.
- **Implementation:** `tools/official_scoring.py`.
- **Source evidence:** the Kaggle metric notebook rendered for version
  `361213439`, inspected without execution and recorded in
  [Phase 7B](phase-7b-authoritative-evidence-report.md), defines the global
  score from `baseline_cost / cost` across benchmark rows. Verifier-produced
  positive costs are required by the notebook.

Evidence labels follow the audit taxonomy: **VERIFIED LOCALLY**,
**VERIFIED UPSTREAM**, **VERIFIED OFFICIAL**, **PAPER-DERIVED**,
**ENGINEERING PROPOSAL**, **BLOCKED**, or **UNKNOWN**.

## Local implementation

`global_geometric_mean_speedup(baseline_costs, costs)` computes

```text
exp(mean(log(baseline_cost / cost)))
```

It requires equally sized, non-empty sequences of positive finite built-in
`int` or `float` values (booleans and non-built-in numeric types are rejected)
and reports underflow/overflow rather than returning a success-shaped zero or
infinity. Log differences avoid forming a potentially overflowing
`baseline_cost / cost` intermediate. It uses standard-library `math` only.

This helper calculates only the documented aggregation. It does not align
`solution` and `submission` rows, parse Kaggle files, call a verifier, calculate
benchmark costs, reproduce pandas-specific behavior, handle Kaggle salts, or
claim bit-for-bit equivalence with the notebook runtime. No official score is
fabricated or reported.

## Validation

`tests/test_official_scoring.py` provides **VERIFIED LOCALLY** evidence: it
checks the formula on known values and rejects
empty, mismatched, non-positive, non-finite, boolean, underflowing, and
otherwise invalid costs. Running the official notebook and reproducing a
leaderboard score remain blocked on authorized verifier/data/runtime access.
