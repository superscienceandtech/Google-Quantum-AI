# Official Verifier and Scorer Discovery

- **Updated:** 2026-11-19
- **Status:** **BLOCKED** — no official verifier/scorer package, immutable
  release, invocation, or fixture bundle was obtained.

## Evidence labels

**VERIFIED OFFICIAL** is limited to observed official competition-page
metadata. **PAPER-DERIVED** describes published methodology and benchmark
semantics, not executable behavior. **VERIFIED UPSTREAM** describes
Qualtran/Kickmix only. **PARTICIPANT-MIRROR** is not authority.
**LOCAL OBSERVATION** describes observed page metadata or repository state.
**ENGINEERING PROPOSAL** describes local protocols. Unresolved matters are
**UNVERIFIED ASSUMPTION** or **BLOCKED**.

## Discovery results

| Evidence source | Result |
|---|---|
| [Kaggle competition page](https://www.kaggle.com/competitions/google-verifiable-quantum-circuit-compilation) | The fetched HTML exposes title and short description metadata but a client-rendered body. No verifier/scorer package, API, invocation, or schemas were obtained. |
| Public Kaggle file listing | The dossier records a public request returning HTTP 401. This is only an access limitation; no credentials were used and no restrictions were bypassed. |
| [Competition paper, arXiv:2610.23832v2](https://arxiv.org/abs/2610.23832) | **PAPER-DERIVED:** salted-hash seeding, benchmark sampling, correctness checks, and resource formulas are described. The salt, executable verifier, exact command/API, and full artifact contracts are not supplied by this paper source. |
| Pinned Qualtran/Kickmix source | **VERIFIED UPSTREAM:** circuit parser, serializer, simulator, and operation statistics exist at commit `f559b12af459e7e97e6c6c382434431c03b903c9`. This is not an official competition verifier. |
| Participant-maintained verifier-like repositories | **PARTICIPANT-MIRROR / UNVERIFIED:** public search results exist, but no official relationship was established; these were not used or run. |
| Local `CompilerVerifier` / `VerificationResult` | **ENGINEERING PROPOSAL:** local dependency-injection seam and status model only; no official mapping is verified. |

The paper must not be presented as an official executable verifier. The
full paper-versus-upstream distinction is recorded in the
[Kickmix dossier](kickmix-interface-benchmark-contract-dossier.md).

## Official contract fields still required

| Contract field | Status | Required authority |
|---|---|---|
| Verifier/scorer identity, immutable release, digest, license | **BLOCKED** | Competition owner or authorized official release |
| Dependencies, supported runtime/OS, installation | **BLOCKED** | Release metadata and official documentation |
| Input and output schemas, formats, and size limits | **BLOCKED** | Verifier package/specification and authorized fixtures |
| CLI/API invocation, working directory, environment | **BLOCKED** | Official invocation contract |
| Exit codes, diagnostics, failure and partial-output behavior | **BLOCKED** | Official implementation/specification |
| Timeout, cancellation, memory/CPU, concurrency limits | **BLOCKED** | Official runtime contract |
| Seed, salt, hash preimage, and canonical serialization | **BLOCKED** | Official verifier source/specification and test vectors |
| Independent verification and acceptance rules | **BLOCKED** | Official verifier/scorer, sample inputs and expected results |
| Resource accounting and score calculation | **PAPER-DERIVED** formulas exist; official executable interpretation is **BLOCKED** | Official scorer and benchmark fixtures |

## Paper-derived benchmark notes (not verifier instructions)

- **INVSQRT:** the paper describes phase checks across the valid integer
  domain, 64 shots per input, and seed derivation from canonical KMB bytes
  combined with a competition salt. The salt, canonical preimage, and exact
  verifier are unavailable.
- **DQI:** the paper describes syndrome/error sampling, phase checks, and
  102,400 shots. Exact register/input encoding and executable implementation
  are unavailable.
- **DFTHC-SOS:** the paper describes forward/reverse angle-oracle checks,
  address/workspace checks, and 64 samples per valid address. The data bundle,
  verifier, and exact invocation are unavailable.

For detailed mathematical statements and caveats, refer to the benchmark
matrix in the [Kickmix dossier](kickmix-interface-benchmark-contract-dossier.md).

## Integration safety rule

The local verifier protocol must not be used to claim competition acceptance.
No missing verifier means “passed.” Do not implement imitation scoring or
infer status from a paper formula. A future adapter may wrap an authorized
official process/API, but must preserve its verified exit/result semantics,
timeouts, output artifacts, and provenance.

## Authorized unblock request

Request the immutable official verifier/scorer release, digest, dependencies,
invocation/API, input/output schemas, failure/timeout rules, resource
accounting, canonical serialization/seed test vectors, and authorized
benchmark fixtures. Do not access private artifacts through credentials or
bypass controls. Until supplied, official verifier integration remains
**BLOCKED**.
