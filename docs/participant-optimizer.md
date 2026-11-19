# Participant-Side Optimization

Evidence labels follow the audit taxonomy: **VERIFIED LOCALLY**,
**VERIFIED UPSTREAM**, **VERIFIED OFFICIAL**, **PAPER-DERIVED**,
**ENGINEERING PROPOSAL**, **BLOCKED**, or **UNKNOWN**.

- **Status:** one conservative pass is **VERIFIED LOCALLY**. The competition
  optimizer API and complete official cost model are **BLOCKED**.
- **Implementation:** `tools/participant_optimizer.py`.
- **Correctness evidence:** `tests/test_kickmix_compiler.py` compares the pass
  with an independent test-only basis/phase simulator over all three-qubit,
  two-bit inputs for the tested circuit.

## Implemented pass

`cancel_adjacent_involutions` removes adjacent, exactly equal operations from
the set `X`, `CX`, `CCX`, `Z`, `CZ`, `CCZ`, `NEG`, `SWAP`, `CSWAP`, and
`BIT_INVERT`, provided the operation is safe under the local guard:

- The complete immutable instruction is equal, including operand order and
  any classical condition.
- Multi-qubit gate operands are distinct; the parser rejects repeated operand
  IDs as invalid upstream circuit data.
- A conditional `BIT_INVERT` does not read its own target as the condition.

The pass uses a deterministic stack, which also cancels pairs made adjacent by
earlier cancellations. Metadata and every other instruction are barriers.
It does not reorder, fuse, synthesize, or remove measurement/reset operations.
The result reports the number of canceled pairs; it does not claim an
improvement under any competition cost function.

The pinned instruction reference says `PUSH_CONDITION` snapshots the current
classical bit, nested conditions require all pushed bits plus any explicit
condition, and `POP_CONDITION` on an empty stack is a no-op
(**VERIFIED UPSTREAM** at Qualtran
[`f559b12af459e7e97e6c6c382434431c03b903c9`](https://github.com/quantumlib/Qualtran/blob/f559b12af459e7e97e6c6c382434431c03b903c9/docs/kickmix/kickmix_instructions.md)).
The local pass treats push/pop operations as barriers; identical adjacent
involutions within an unchanged pushed condition remain self-inverse. The
test-only finite-state interpreter models the stack snapshot for the supported
subset (**VERIFIED LOCALLY**), not all Kickmix semantics.

`R` is reset, `HMR` is measurement/reset, and `Z_POW` carries a phase angle
(**VERIFIED UPSTREAM**). None is in the cancellation set. In particular,
reset and measurement instructions are not assumed to be involutions. The
pass does not cross metadata, classical mutation, measurement, or reset
instructions.

## Limitations

This is not a participant optimizer demonstrated on a benchmark. There is no
pass registry, optimization timeout, score-aware search, or verifier-backed
equivalence. The independent small-state test covers only the reversible
classical gates, Boolean phase flips, explicit conditions, and selected
condition-stack snapshots used by the pass. It is not proof of general
quantum-circuit equivalence and does not simulate or validate `HMR`, `R`, or
arbitrary `Z_POW` circuits. Differential execution against upstream and any
official verifier is **BLOCKED**.

The competition cost returned by each verifier remains unavailable. The
global aggregation formula does not define per-benchmark costs, so the pass is
not tuned against an invented score.
