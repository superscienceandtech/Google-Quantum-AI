# Local Compilation Workflow

- **Status:** a deterministic local KMX-to-KMX validation/optimization CLI is
  **VERIFIED LOCALLY**. The competition end-to-end workflow is **BLOCKED**.
- **Entry point:** `python3 -m tools.kickmix_compiler INPUT.kmx OUTPUT.kmx`.

Evidence labels follow the audit taxonomy: **VERIFIED LOCALLY**,
**VERIFIED UPSTREAM**, **VERIFIED OFFICIAL**, **PAPER-DERIVED**,
**ENGINEERING PROPOSAL**, **BLOCKED**, or **UNKNOWN**.

## Local path

```text
KMX text input
  -> bounded UTF-8 and KMX v2 parsing
  -> KMX syntax/ID/condition validation
  -> visible-metric ID and register-name validation
  -> adjacent-involution cancellation (unless --no-optimize)
  -> deterministic KMX text serialization
  -> exclusive output publication and JSON provenance/resource summary
```

Example:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m tools.kickmix_compiler \
  candidate.kmx candidate-optimized.kmx
```

The output file must not already exist. The input must be a regular,
non-symlink file no larger than 16 MiB. Missing output parents are not created.
The CLI returns status 0 on success, 2 for input/compile failures, and 3 for
output publication failures. The output JSON contains content hashes and
structural resource counts, but no timestamps, absolute paths, salts, or
benchmark score.

`parse_kmx` accepts upstream-valid unnamed/sparse register metadata subject to
local resource bounds; the `compile_kmx` entry point enforces the visible
metric's named-register and qubit/bit-ID rules. The pinned upstream parser has
different ID limits; differential execution remains **BLOCKED**.

## Missing official stages

This local flow does not acquire benchmark inputs, identify a benchmark,
construct an INVSQRT/DQI/DFTHC-SOS circuit, read the DFTHC tensor archive,
emit KMB, run an official verifier, or reproduce the Kaggle scorer. It must
not be described as a successful benchmark compilation or competition-ready
workflow. Those stages remain **BLOCKED** on the artifacts and contracts
recorded in [Phase 7B](phase-7b-authoritative-evidence-report.md).
