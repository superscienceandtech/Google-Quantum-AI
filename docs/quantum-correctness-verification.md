# Quantum-Circuit Correctness Verification

- **Status:** local equivalence evidence exists only for the implemented
  adjacent-cancellation pass and its restricted gate subset.
- **Independent test implementation:** the test-only
  `simulate_reversible_phase` helper in `tests/test_kickmix_compiler.py`.
- **Official benchmark verification:** blocked; see
  [official verifier integration contract](official-verifier-integration-contract.md)
  and the [Phase 7B evidence report](phase-7b-authoritative-evidence-report.md).

Evidence labels follow the audit taxonomy: **VERIFIED LOCALLY**,
**VERIFIED UPSTREAM**, **VERIFIED OFFICIAL**, **PAPER-DERIVED**,
**ENGINEERING PROPOSAL**, **BLOCKED**, or **UNKNOWN**.

## Verified relation and domain

The test helper enumerates every three-qubit basis input and every
two-classical-bit input for selected `X`, `CX`, `CCX`, `Z`, `CZ`, `CCZ`,
`NEG`, `SWAP`, `CSWAP`, and `BIT_INVERT` operations with explicit conditions.
It models `PUSH_CONDITION` as a snapshot of the current bit and
`POP_CONDITION` as a stack pop, consistent with the pinned upstream
instruction documentation. It compares output qubits, bits, and the tracked
sign phase before and after optimization. This is **VERIFIED LOCALLY**
test-oracle evidence for the enumerated subset only.

This is exact equality on the enumerated finite basis domain, including the
Kickmix Boolean sign phase. It is not a statevector/unitary proof, a proof for
arbitrary circuit size, a benchmark acceptance test, or evidence about
approximate phase rotations. The helper does not implement reset or
measurement semantics; adjacent `R` and `HMR` regression tests instead verify
that the optimizer leaves those operations unchanged.

## Not verified

- General unitary or operator equivalence.
- Global-phase equivalence beyond the tested explicit Boolean sign.
- `HMR` measurement, phase kickback, random seeds, or reset semantics.
- `R` behavior, `Z_POW` approximation error, and fixed-point tolerances.
- Ancilla restoration, benchmark register mapping, or numerical
  approximation bounds.
- Any INVSQRT, DQI, or DFTHC-SOS reference comparison.

The optimizer is not its own correctness authority: its tests use a separate
small-state interpreter. Upstream semantic details cited above are
**VERIFIED UPSTREAM**, but differential execution is **BLOCKED** because the
pinned implementation is unavailable locally. This evidence does not
substitute for the unavailable benchmark verifier or a formal equivalence
checker; official benchmark correctness remains **BLOCKED**.
