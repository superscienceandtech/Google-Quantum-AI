# Phase 6: Verification Integration Contract

**Review date:** 2026-11-19

## Evidence labels

**OFFICIAL SOURCE** applies only to the official Kaggle page and metric
metadata retrieved. **PAPER-DERIVED** describes arXiv:2610.23832v2.
**PARTICIPANT-MIRROR** describes unaffiliated copies or claims.
**VERIFIED LOCAL FACT** describes this checkout. **UNKNOWN / BLOCKED** marks
unavailable executable details.

## What is established

**OFFICIAL SOURCE, metadata only:** The Kaggle competition page identifies
“Google Quantum AI - Verifiable Quantum Circuit Compilation.” The public metric
page identifies “Google Quantum AI Metric” and says it uses the competition's
data. The HTML data and rules routes did not expose file contents or full
rules. Public API attempts did not retrieve the competition data listing or
metric source. No authentication or access-control bypass was attempted.

**PAPER-DERIVED:** Section II.3 of arXiv:2610.23832v2 describes a
non-interactive verifier for serialized Kickmix circuits:

1. Hash the raw serialized circuit bytes with SHA-256 and derive deterministic
   test inputs; in the competition setting a private salt is combined with
   the circuit digest to prevent seed grinding.
2. Initialize the benchmark inputs and simulate each shot, including
   measurement-based uncomputation outcomes.
3. Check expected input/output bitstrings, clean scratch, and output phase
   within the benchmark tolerance.
4. Estimate a one-sided Clopper-Pearson upper bound on the failure probability
   at confidence `1 - 2^-128`; benchmark scoring uses this bound where
   approximate correctness is permitted.

The paper does not disclose the private salt or an executable/API contract.
It is a substantive algorithmic description, not a byte-for-byte substitute
for the official metric/verifier.

## Benchmark-specific verifier facts

| Benchmark | Paper-described checks | Still unavailable |
|---|---|---|
| INVSQRT | A single KMB circuit; named 22-qubit `x` register; `x` preserved; scratch returned to zero; phase for `1/sqrt(x)`; every integer in the stated input range tested 64 times; every shot must pass within the specified phase tolerance. | Official KMB reference fixture, exact competition binary/runtime, private salt, and executable metric behavior. |
| DQI | Circuit preserves the 840-qubit syndrome, cleans workspace, and applies the record-dependent sign. The paper describes a 102,400-shot distribution and a score accounting for a bounded failure probability. | Authorized input/reference files, salt, verifier executable, exact process/API behavior, and official acceptance run. |
| DFTHC-SOS | Paper specifies Boolean angle-oracle checks, forward/reverse behavior, workspace cleanup, address and angle-word conditions, and resource/error constraints. | Official dataset files, schemas as serialized by Kaggle, reference artifacts, verifier executable, and exact metric behavior. |

Values above are **PAPER-DERIVED**, not validated by executing the official
verifier.

## Candidate verifier mirror

The public [`qarena-ai/invsqrt`](https://github.com/qarena-ai/invsqrt) README
claims its files are the Kaggle verifier unchanged and lists hashes. The same
README states that QArena is independent of Google and Kaggle and neither is a
sponsor or endorser. Its repositories are therefore classified as
**PARTICIPANT-MIRROR**. The claimed bytes could not be compared to Kaggle's
official data and were not executed.

## Contract gaps

| Element | Status |
|---|---|
| Official verifier/scorer identity and immutable version | **UNKNOWN / BLOCKED** |
| Official verifier source/binary and trusted digest | **BLOCKED** |
| Invocation arguments, working directory, environment, and return values | **UNKNOWN / BLOCKED** |
| Official fixture files and expected results | **BLOCKED** |
| Private salt and exact seed derivation encoding | **UNKNOWN / BLOCKED** |
| Error codes, diagnostics, timeouts, memory limits | **UNKNOWN / BLOCKED** |
| Reproducible local acceptance command | **UNKNOWN / BLOCKED** |
| Paper-level verifier method | **PAPER-DERIVED**, described but not executable here |

## Local behavior

**VERIFIED LOCAL FACT:** `run_compilation` fails closed: missing verification
returns `BLOCKED`, and only a configured verifier that returns
`VerificationStatus.PASSED` can yield local success. Test-double acceptance
does not establish official circuit correctness. SHA-256 verifies byte
integrity relative to a supplied digest; it does not authenticate the digest's
publisher or prove the verifier's provenance.
