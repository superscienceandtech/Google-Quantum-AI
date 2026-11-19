# Phase 5: Benchmark Contract Reconciliation

**Review date:** 2026-11-19

## Evidence labels

**VERIFIED LOCAL FACT** describes this checkout. **OFFICIAL SOURCE** applies
only to retrieved official material. **PAPER-DERIVED** describes claims from
arXiv:2610.23832 v2. **VERIFIED UPSTREAM** describes upstream Kickmix.
**PARTICIPANT-MIRROR** is not official. **ENGINEERING PROPOSAL** is proposed
local design. **UNKNOWN** and **BLOCKED** identify missing evidence.

## INVSQRT

| Contract element | Status and evidence |
|---|---|
| Input schema / valid domain | **PAPER-DERIVED:** The paper's experiment uses `n_p=10`, `beta=1`, width `2*n_p+2=22`, with `x` over the stated range up to `3*(2^10-2)^2 = 3,133,452`. Exact official fixture encoding and complete accepted domain are **UNKNOWN**. |
| Circuit/register conventions | **PAPER-DERIVED:** The paper describes a phase oracle and finite-precision arithmetic. An official register naming/order contract is **UNKNOWN**. |
| Phase semantics | **PAPER-DERIVED:** The intended phase is associated with the inverse-square-root function; the paper reports a phase-error target of `2^-24 * beta / sqrt(x)` turns. This does not establish exact official verifier rounding behavior. |
| Numerical tolerance | **PAPER-DERIVED:** The above experimental error target. Official accepted tolerance and boundary comparison are **UNKNOWN**. |
| Output, serialization | **UNKNOWN / BLOCKED:** No official output artifact schema or serialization parser was available. |
| Workspace cleanup | **PAPER-DERIVED:** Algorithm descriptions include reversible arithmetic/uncomputation considerations. An official clean-workspace test is **UNKNOWN**. |
| Resource accounting | **PAPER-DERIVED:** The paper reports circuit cost; exact official scorer implementation/version is **BLOCKED**. |
| Verification | **UNKNOWN / BLOCKED:** No official executable or API was obtained. |

## DQI

| Contract element | Status and evidence |
|---|---|
| Finite field / polynomial / basis | **PAPER-DERIVED:** The paper uses a finite field represented with a specified polynomial-basis construction. Any compiler adapter must transcribe the exact paper definitions from the chosen paper revision; no official serialized field contract was found. |
| Matrix and syndrome | **PAPER-DERIVED:** The paper describes a parity-check/syndrome construction with `q=4096`, `m=4095`, `n=70`, `ell=35`, and the Reed-Solomon distance argument `d=71`, so `2*ell=70<71`. The paper's symbolic conventions do not establish an official byte-level encoding. |
| Error-vector encoding / bit ordering | **PAPER-DERIVED, incomplete:** The paper describes an error vector and phase evaluation; an authoritative bit order and serialized representation are **UNKNOWN**. |
| Phase semantics | **PAPER-DERIVED:** The paper defines the target phase from the code/bit function of the syndrome. The exact executable verifier's convention is **UNKNOWN**. |
| Registers / workspace / reversibility | **PAPER-DERIVED, incomplete:** Algorithmic construction is described; official register order and cleanup acceptance are **UNKNOWN**. |
| Samples / scoring / resources | **PAPER-DERIVED:** The paper reports experiment and Toffoli accounting. An official scoring implementation is **BLOCKED**. The paper-reported `5,725,461` Toffoli count after Step 3 cleanup is not adopted as an official score. Other claimed counts without verified source/accounting are not reconciled here. |
| Serialization / verification | **UNKNOWN / BLOCKED:** No official schema, fixture set, or verifier was obtained. |

## DFTHC-SOS

| Contract element | Status and evidence |
|---|---|
| Input dataset schema | **UNKNOWN / BLOCKED:** No official dataset file/schema was available. Paper-level instance and dimension descriptions do not establish a data-loader contract. |
| Tensor dimensions / axes | **PAPER-DERIVED, incomplete:** The paper describes its DFTHC-SOS construction and reported problem sizes. Axis order and official serialized tensor layout are **UNKNOWN**. |
| Factorization and address encoding | **PAPER-DERIVED, incomplete:** The paper describes factorized coefficient access and address-dependent rotations. Exact official index/address encoding and data fixtures are **UNKNOWN**. |
| Angle oracle | **PAPER-DERIVED:** The paper describes the rotation-angle construction and reversibility constraints. Exact accepted gate encoding and verifier tolerance are **UNKNOWN**. |
| Reversibility / cleanup | **PAPER-DERIVED:** The construction includes uncomputation; official workspace-cleanup checks are **UNKNOWN**. |
| Resource accounting / serialization | **PAPER-DERIVED, incomplete / BLOCKED:** Published resource estimates do not establish scorer implementation; official circuit serialization is unavailable. |
| Verification | **UNKNOWN / BLOCKED:** No official verifier or test fixture was obtained. |

## Kickmix is not a benchmark contract

**VERIFIED UPSTREAM:** The pinned Qualtran source defines a restricted circuit
model and basis-trajectory simulation, including tracked phase and
measurement-based uncomputation. This upstream behavior does not determine the
official benchmark API, and upstream `free`/allocation reuse does not prove
workspace cleanup.

See [`phase-5-kickmix-adoption-assessment.md`](phase-5-kickmix-adoption-assessment.md)
and the pinned source dossier for the exact upstream evidence.

## Integration disposition

**BLOCKED:** None of the three benchmarks has sufficient authoritative
machine-readable input, output, invocation, and verifier contracts to implement
a conformant adapter. No benchmark-specific adapter was created. All equations
and parameter values above remain paper-derived and must not be presented as
official executable requirements.
