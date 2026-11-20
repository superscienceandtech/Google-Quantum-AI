"""Logical DQI syndrome evaluation; no circuit register mapping is implied."""

from collections.abc import Sequence

from .field import add, multiply, power, validate_element

DQI_ERROR_SYMBOL_COUNT = 4095
DQI_SYNDROME_COUNT = 70
_ALPHA = 0b10


def compute_dqi_syndrome(error_symbols: Sequence[int]) -> tuple[int, ...]:
    """Compute the 70 indexed syndromes defined in arXiv:2610.23832v2.

    The input is the mathematical vector (e_0, ..., e_4094), with each
    symbol represented in the field module's polynomial basis. Output index
    i is s_i = sum_j e_j * alpha**((i + 1) * j). This does not define the
    verifier's register names, bit ordering, or serialization.
    """
    if len(error_symbols) != DQI_ERROR_SYMBOL_COUNT:
        raise ValueError(
            f"expected {DQI_ERROR_SYMBOL_COUNT} error symbols, "
            f"got {len(error_symbols)}"
        )
    symbols = tuple(validate_element(symbol) for symbol in error_symbols)

    syndromes: list[int] = []
    for syndrome_index in range(DQI_SYNDROME_COUNT):
        evaluation_point = power(_ALPHA, syndrome_index + 1)
        value = 0
        for coefficient in reversed(symbols):
            value = add(multiply(value, evaluation_point), coefficient)
        syndromes.append(value)
    return tuple(syndromes)
