# Phase 6: First Benchmark Selection

**Decision:** `NO BENCHMARK QUALIFIES FOR REAL ADAPTER IMPLEMENTATION`

**Review date:** 2026-11-19

## Evidence labels

Benchmark equations, parameters, and paper-described verifier procedures below
are **PAPER-DERIVED** from arXiv:2610.23832v2. Kaggle page title/metric
metadata are **OFFICIAL SOURCE**, but the data bundle and executable metric
were not retrieved. Kickmix API claims are **VERIFIED UPSTREAM**.
**ENGINEERING PROPOSAL** labels a future design only.

## Selection matrix

All seven criteria in the Phase 6 selection rule are required.

| Criterion | INVSQRT | DQI | DFTHC-SOS |
|---|---|---|---|
| Authoritative input schema | **PARTIAL:** paper specifies the logical input register and domain; official fixture encoding is unavailable. | **PARTIAL:** paper specifies field, basis, syndrome and record widths; official data/fixture bundle is unavailable. | **PARTIAL:** paper describes logical tensors and oracle interface; official serialized dataset/schema is unavailable. |
| Authoritative circuit semantics | **PAPER-DERIVED:** `1/sqrt(x)` phase, preservation, cleanup, precision and shot checks are described. | **PAPER-DERIVED:** syndrome-to-sign function and clean/preserve conditions are described. | **PAPER-DERIVED:** angle-oracle and block-encoding checks are described. |
| Compiler supports required operations | **PARTIAL:** upstream Kickmix has the restricted gate/build model; no competition compiler or runtime compatibility test was performed. | **PARTIAL:** same; no compiler/decoder adapter was run. | **PARTIAL:** same; no data-backed oracle circuit was run. |
| Serialization contract | **PARTIAL:** paper names KMB; upstream source supports KMB. The competition's exact binary/version pair was not verified. | **PARTIAL:** Kickmix representation is described, but no official fixture/parser was tested. | **PARTIAL:** no official data/circuit fixture was retrieved. |
| Authorized fixtures available | **NO** | **NO** | **NO** |
| Verification path available | **PARTIAL:** verifier algorithm is paper-described and an official Kaggle metric page exists; executable source/data unavailable. | **PARTIAL:** same, including statistical scoring in the paper. | **PARTIAL:** same, with data and executable verification unavailable. |
| Reproducible toolchain | **NO:** no project compiler/runtime pin or official integration run. | **NO** | **NO** |
| Qualifies | **NO** | **NO** | **NO** |

## Benchmark facts and semantic boundaries

### INVSQRT

**PAPER-DERIVED:** The operation is `|x>|0> -> exp(2*pi*i*beta/sqrt(x))|x>|0>`,
not `1/x`. The paper's competition instance uses `beta=1`, a 22-qubit named
register `x`, and the inclusive range `1 <= x <= 3,133,452`. It specifies
workspace restoration, 64 samples for each input, a phase tolerance, and a
resource score. Those facts make this the most completely described logical
contract, but not an authorized executable fixture.

### DQI

**PAPER-DERIVED:** The paper specifies `q=2^12`, `m=4095`, `n=70`,
`ell=35`, and the field
`F_2[alpha]/(alpha^12 + alpha^6 + alpha^4 + alpha + 1)` in the little-endian
polynomial basis `(1, alpha, ..., alpha^11)`. It defines evaluation points
`alpha^j`, syndrome components, an 840-qubit syndrome, and a 49,140-bit
classical record. The target phase is a record/error-vector parity computed
from the unique correctable error. The paper reports 5,725,461 Toffolis after
cleanup for its reference circuit; that number is not an official score
verified by this project.

These details correct Phase 5's overly broad claim that field basis and bit
ordering were wholly unknown. The paper describes them; the official encoded
fixtures and executable verifier remain unavailable.

### DFTHC-SOS

**PAPER-DERIVED:** The paper describes the FeMo-co instance (`N=76`,
`eta=113`), factorization quantities, Boolean angle oracles, and checks for
angle words, address preservation, workspace, forward/reverse behavior,
resource limits, and numerical residuals. The text does not provide the
Kaggle file bundle or an executable loader. No tensor axes, dtypes, or dataset
schema are inferred from array shapes.

## Selection result

No benchmark passes the mandatory fixture, verification, and reproducible
toolchain gates. INVSQRT is a sensible **ENGINEERING PROPOSAL** for the first
contract-reconciliation spike only after authorized files and verifier access
are obtained; it is not selected for implementation now.
