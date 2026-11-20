"""Classical research decoder for the paper-defined DQI syndrome mapping."""

from collections.abc import Sequence
from dataclasses import dataclass

from .field import inverse, multiply, power, validate_element
from .polynomial import (
    Polynomial,
    add_polynomials,
    degree,
    divide_polynomials,
    evaluate_polynomial,
    formal_derivative,
    multiply_polynomials,
    normalize,
    scale_polynomial,
)
from .syndrome import (
    DQI_ERROR_SYMBOL_COUNT,
    DQI_SYNDROME_COUNT,
    compute_dqi_syndrome,
)

DQI_MAX_CORRECTABLE_ERRORS = DQI_SYNDROME_COUNT // 2
_ALPHA = 0b10


class InvalidSyndrome(ValueError):
    """The supplied syndrome does not match the fixed DQI vector contract."""


class NoDecodingSolution(RuntimeError):
    """No valid error vector within the supported radius was established."""


@dataclass(frozen=True)
class DecodedError:
    """A verified low-weight error vector and its algebraic certificates."""

    error_symbols: tuple[int, ...]
    error_positions: tuple[int, ...]
    locator_polynomial: Polynomial
    evaluator_polynomial: Polynomial

    @property
    def weight(self) -> int:
        """Return the number of nonzero error symbols."""
        return len(self.error_positions)


def _validate_syndrome(syndromes: Sequence[int]) -> tuple[int, ...]:
    if isinstance(syndromes, (str, bytes)) or not isinstance(syndromes, Sequence):
        raise InvalidSyndrome("syndromes must be a sequence of field elements")
    if len(syndromes) != DQI_SYNDROME_COUNT:
        raise InvalidSyndrome(
            f"expected {DQI_SYNDROME_COUNT} syndrome symbols, got {len(syndromes)}"
        )
    try:
        return tuple(validate_element(value) for value in syndromes)
    except (TypeError, ValueError) as error:
        raise InvalidSyndrome("syndrome contains an invalid field element") from error


def _key_equation(
    syndromes: tuple[int, ...],
) -> tuple[Polynomial, Polynomial]:
    """Solve sigma*S = omega (mod z^70) by the paper's extended Euclid step."""
    if not any(syndromes):
        return (1,), ()

    modulus = (0,) * DQI_SYNDROME_COUNT + (1,)
    remainder_previous: Polynomial = modulus
    remainder_current = normalize(syndromes)
    coefficient_previous: Polynomial = ()
    coefficient_current: Polynomial = (1,)
    iterations = 0

    while remainder_current and degree(remainder_current) >= DQI_MAX_CORRECTABLE_ERRORS:
        if iterations >= DQI_MAX_CORRECTABLE_ERRORS:
            raise NoDecodingSolution("extended Euclid exceeded its degree bound")
        quotient, remainder = divide_polynomials(
            remainder_previous,
            remainder_current,
        )
        if remainder and degree(remainder) >= degree(remainder_current):
            raise NoDecodingSolution(
                "extended Euclid failed to reduce the remainder degree"
            )
        next_coefficient = add_polynomials(
            coefficient_previous,
            multiply_polynomials(quotient, coefficient_current),
        )
        remainder_previous, remainder_current = remainder_current, remainder
        coefficient_previous, coefficient_current = (
            coefficient_current,
            next_coefficient,
        )
        iterations += 1

    if not coefficient_current or coefficient_current[0] == 0:
        raise NoDecodingSolution(
            "extended Euclid produced no locator with nonzero constant term"
        )
    normalization = inverse(coefficient_current[0])
    locator = scale_polynomial(coefficient_current, normalization)
    evaluator = scale_polynomial(remainder_current, normalization)
    if degree(locator) > DQI_MAX_CORRECTABLE_ERRORS:
        raise NoDecodingSolution(
            "extended Euclid locator exceeds the supported error radius"
        )
    return locator, evaluator


def _find_error_positions(locator: Polynomial) -> tuple[int, ...]:
    locator_degree = degree(locator)
    if locator_degree < 0:
        raise NoDecodingSolution("error locator is the zero polynomial")

    positions = []
    for position in range(DQI_ERROR_SYMBOL_COUNT):
        evaluation_point = power(_ALPHA, position)
        root = inverse(evaluation_point)
        if evaluate_polynomial(locator, root) == 0:
            positions.append(position)

    if len(positions) != locator_degree:
        raise NoDecodingSolution(
            "error locator does not have the expected number of distinct "
            "roots among the DQI evaluation points"
        )
    return tuple(positions)


def _recover_error_symbols(
    locator: Polynomial,
    evaluator: Polynomial,
    positions: tuple[int, ...],
) -> tuple[int, ...]:
    derivative = formal_derivative(locator)
    errors = [0] * DQI_ERROR_SYMBOL_COUNT

    for position in positions:
        point = inverse(power(_ALPHA, position))
        denominator = evaluate_polynomial(derivative, point)
        if denominator == 0:
            raise NoDecodingSolution(
                f"error locator derivative is zero at position {position}"
            )
        # With s_i=sum_j e_j alpha^((i+1)j) and
        # sigma(z)=prod_j(1-alpha^j z), the Forney ratio is Omega/sigma'.
        magnitude = multiply(
            evaluate_polynomial(evaluator, point),
            inverse(denominator),
        )
        if magnitude == 0:
            raise NoDecodingSolution(
                f"zero error magnitude reported at root position {position}"
            )
        errors[position] = magnitude
    return tuple(errors)


def decode_error(syndromes: Sequence[int]) -> DecodedError:
    """Recover and verify an error vector of weight at most 35.

    This is a classical research API for logical field-element tuples, not an
    official circuit-register interface. A failure means no valid candidate
    within the supported radius was established; it does not prove that the
    input is beyond that radius or invalid under an official verifier.
    """
    syndrome = _validate_syndrome(syndromes)
    if not any(syndrome):
        return DecodedError(
            error_symbols=(0,) * DQI_ERROR_SYMBOL_COUNT,
            error_positions=(),
            locator_polynomial=(1,),
            evaluator_polynomial=(),
        )

    locator, evaluator = _key_equation(syndrome)
    positions = _find_error_positions(locator)
    errors = _recover_error_symbols(locator, evaluator, positions)
    if len(positions) > DQI_MAX_CORRECTABLE_ERRORS:
        raise NoDecodingSolution("decoded error exceeds the supported radius")
    if compute_dqi_syndrome(errors) != syndrome:
        raise NoDecodingSolution(
            "candidate error vector does not reproduce the supplied syndrome"
        )
    return DecodedError(
        error_symbols=errors,
        error_positions=positions,
        locator_polynomial=locator,
        evaluator_polynomial=evaluator,
    )
