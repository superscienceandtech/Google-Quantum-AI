"""Input-preserving XOR-accumulation models for polynomial evaluation."""

from .field import validate_element
from .reversible_polynomial import PolynomialRegister
from .reversible_primitives import xor_accumulate_add, xor_accumulate_multiply

EvaluationTarget = tuple[int]


def _validate_polynomial_register(
    register: object,
) -> PolynomialRegister:
    if type(register) is not tuple:
        raise TypeError("polynomial must be a tuple of field elements")
    if not register:
        raise ValueError("polynomial must contain at least one coefficient")
    return tuple(validate_element(value) for value in register)


def _evaluate_and_uncompute(
    polynomial: PolynomialRegister,
    point: int,
    target: EvaluationTarget,
) -> tuple[EvaluationTarget, tuple[int, ...]]:
    """Run Horner compute, target accumulation, and reverse uncomputation."""
    scratch = [0]
    coefficients = tuple(reversed(polynomial))
    accumulator_indices: list[int] = []
    product_steps: list[tuple[int, int, int, int]] = []

    initial_accumulator_index = len(scratch)
    scratch.append(0)
    _, _, scratch[initial_accumulator_index] = xor_accumulate_add(
        coefficients[0],
        scratch[0],
        scratch[initial_accumulator_index],
    )
    accumulator_indices.append(initial_accumulator_index)

    for coefficient in coefficients[1:]:
        previous_accumulator_index = accumulator_indices[-1]

        product_index = len(scratch)
        scratch.append(0)
        _, _, scratch[product_index] = xor_accumulate_multiply(
            scratch[previous_accumulator_index],
            point,
            scratch[product_index],
        )

        accumulator_index = len(scratch)
        scratch.append(0)
        _, _, scratch[accumulator_index] = xor_accumulate_add(
            scratch[product_index],
            coefficient,
            scratch[accumulator_index],
        )
        accumulator_indices.append(accumulator_index)
        product_steps.append(
            (
                previous_accumulator_index,
                product_index,
                accumulator_index,
                coefficient,
            )
        )

    evaluation = scratch[accumulator_indices[-1]]
    _, _, updated_target = xor_accumulate_add(
        evaluation,
        scratch[0],
        target[0],
    )
    result_target = (updated_target,)

    for previous_index, product_index, accumulator_index, coefficient in reversed(
        product_steps
    ):
        _, _, scratch[accumulator_index] = xor_accumulate_add(
            scratch[product_index],
            coefficient,
            scratch[accumulator_index],
        )
        _, _, scratch[product_index] = xor_accumulate_multiply(
            scratch[previous_index],
            point,
            scratch[product_index],
        )

    _, _, scratch[initial_accumulator_index] = xor_accumulate_add(
        coefficients[0],
        scratch[0],
        scratch[initial_accumulator_index],
    )

    return result_target, tuple(scratch)


def xor_accumulate_polynomial_evaluation(
    polynomial: PolynomialRegister,
    point: int,
    target: EvaluationTarget,
) -> tuple[PolynomialRegister, int, EvaluationTarget]:
    """Accumulate a polynomial's value into a one-element target register.

    ``polynomial`` is a nonempty, low-degree-first tuple over GF(2^12);
    ``point`` is one GF(2^12) element; and ``target`` must be a one-element
    tuple of GF(2^12). The polynomial and point are preserved. Horner
    intermediates are stored in scratch registers, the evaluation is XORed
    into the target, and the computation is reversed to clear the scratch.
    """
    polynomial_register = _validate_polynomial_register(polynomial)
    evaluation_point = validate_element(point)
    if type(target) is not tuple:
        raise TypeError("target must be a one-element tuple of field elements")
    if len(target) != 1:
        raise ValueError("target must contain exactly one field element")
    target_register = (validate_element(target[0]),)

    updated_target, scratch = _evaluate_and_uncompute(
        polynomial_register,
        evaluation_point,
        target_register,
    )
    if any(scratch):
        raise RuntimeError("polynomial evaluation left nonzero scratch")

    return polynomial_register, evaluation_point, updated_target
