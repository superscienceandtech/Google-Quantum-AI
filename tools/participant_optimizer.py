"""Deterministic, semantics-preserving local Kickmix optimization passes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from tools.kickmix_compiler import Circuit, Instruction


_SELF_INVERSE_OPCODES = frozenset(
    {"X", "CX", "CCX", "Z", "CZ", "CCZ", "NEG", "SWAP", "CSWAP"}
)


def _is_cancellable_pair(left: Instruction, right: Instruction) -> bool:
    if left != right or left.opcode not in _SELF_INVERSE_OPCODES | {"BIT_INVERT"}:
        return False
    if left.opcode in {"CX", "CCX", "CZ", "CCZ", "SWAP", "CSWAP"}:
        qubit_ids = [wire.index for wire in left.operands]
        if len(set(qubit_ids)) != len(qubit_ids):
            return False
    if left.opcode == "BIT_INVERT" and left.condition == left.operands[0].index:
        return False
    return True


@dataclass(frozen=True)
class OptimizationResult:
    circuit: Circuit
    canceled_pairs: int


def cancel_adjacent_involutions(circuit: Circuit) -> OptimizationResult:
    from tools.kickmix_compiler import Circuit

    if not isinstance(circuit, Circuit):
        raise TypeError("circuit must be a Circuit")
    stack = []
    canceled_pairs = 0
    for instruction in circuit.instructions:
        if stack and _is_cancellable_pair(stack[-1], instruction):
            stack.pop()
            canceled_pairs += 1
        else:
            stack.append(instruction)
    return OptimizationResult(Circuit(tuple(stack)), canceled_pairs)


def optimize_adjacent_involutions(circuit: Circuit) -> Tuple[Circuit, int]:
    result = cancel_adjacent_involutions(circuit)
    return result.circuit, result.canceled_pairs
