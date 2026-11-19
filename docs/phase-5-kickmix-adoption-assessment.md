# Phase 5: Kickmix Adoption and Compatibility Assessment

**Review date:** 2026-11-19

## Evidence labels

**VERIFIED UPSTREAM** means observed in Qualtran or public PyPI metadata, not
official competition documentation. **VERIFIED LOCAL FACT** describes this
checkout. **UNKNOWN** means no evidence was found. **ENGINEERING PROPOSAL**
is a local recommendation.

## Source identity

| Source | Observed identity | Limits |
|---|---|---|
| Qualtran source | **VERIFIED UPSTREAM:** `google/Qualtran`, commit `f559b12af459e7e97e6c6c382434431c03b903c9`, dated 2026-11-12. | Does not establish project adoption or competition approval. |
| PyPI | **VERIFIED UPSTREAM registry metadata:** package `kickmix` 1.0.0, author `Qualtran Developers`, homepage Qualtran, runtime requirement `numpy`, uploaded 2026-10-27. Registry lists a CPython 3.12 manylinux x86_64 wheel SHA-256 `cc26abcd5efa5e72f373148d5cca2ffa43e158a724e94c213b97622f23c6241a`. | The wheel was not downloaded/installed; the hash was not independently computed. The release's exact source commit is **UNKNOWN**. |
| Project dependency state | **VERIFIED LOCAL FACT:** Kickmix and NumPy are not declared project dependencies; neither is installed in the selected Python environment. | No claim about hidden/private evaluation environments. |

## Upstream API and operation model

**VERIFIED UPSTREAM:** The inspected source provides Kickmix circuit-building,
serialization, operation-statistics, and simulator components, including
`Circuit`, `CircuitBuilder`, circuit file I/O, operation statistics, and a
restricted basis-trajectory simulator. The operation model includes a supported
gate set with tracked phase; the simulator is not a general state-vector
simulator.

**VERIFIED UPSTREAM:** Measurement-based uncomputation is represented within
Kickmix's model. Its allocation/freeing behavior is an upstream circuit-model
concept and is not, by itself, proof that a benchmark's workspace is clean or
that a verifier accepts the result.

The exact symbol/operation inventory and pinned-source excerpts are in
[`docs/kickmix-interface-benchmark-contract-dossier.md`](kickmix-interface-benchmark-contract-dossier.md).
This page records no additional API claims beyond that source-backed dossier.

## Compatibility matrix

| Proposed use | Disposition | Reason |
|---|---|---|
| Replace the missing project compiler | **Not established** | No official source says Kickmix is the competition compiler or the expected compiler API. |
| Generate candidate circuits for research | **Potentially useful upstream tool; not validated here** | Would require a separately approved, pinned environment and benchmark contract. It was not installed or executed in this task. |
| Parse official benchmark fixtures | **UNKNOWN** | No official fixture schema or compatibility test exists in the checkout. |
| Serialize official submissions | **UNKNOWN** | No official format equivalence was established. |
| Simulate the full benchmark semantics | **Not established** | Restricted basis-trajectory behavior is not a general semantics guarantee; benchmark-specific phase, measurement, and cleanup rules need an official verifier. |
| Provide resource scores | **Not sufficient alone** | Operation statistics are upstream measurements, not proof of the official scorer's conventions/version. |
| Serve as a trust boundary | **No** | An in-process library is not a sandbox and does not authenticate compiler output. |

## Adoption decision

**ENGINEERING PROPOSAL:** Do not add Kickmix or NumPy to project dependencies
and do not build a benchmark adapter against it yet. Preserve it as a pinned
upstream research reference. Reconsider adoption only after project-owner
approval, confirmation of the competition's supported source version, official
artifact/verifier contracts, and a fixture-backed compatibility test.

This decision does not assert that Kickmix is incompatible; its official
compatibility is **UNKNOWN**.
