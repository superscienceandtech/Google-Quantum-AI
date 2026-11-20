"""Bounded input-preserving register model for one polynomial EEA step."""

from collections.abc import Callable

from .field import validate_element
from .reversible_division import (
    MAX_DIVISION_DIVIDEND_WIDTH,
    MAX_DIVISION_DIVISOR_WIDTH,
    MAX_POLYNOMIAL_REGISTER_WIDTH,
    xor_accumulate_polynomial_division,
)
from .reversible_polynomial import (
    PolynomialRegister,
    xor_accumulate_polynomial_add,
    xor_accumulate_polynomial_multiply,
)

EEATarget = tuple[int, ...]
MAX_EEA_R0_WIDTH = MAX_DIVISION_DIVIDEND_WIDTH
MAX_EEA_R1_WIDTH = MAX_DIVISION_DIVISOR_WIDTH
MAX_EEA_S_COEFFICIENT_WIDTH = 35
MAX_EEA_T_COEFFICIENT_WIDTH = 36
MAX_EEA_QUOTIENT_TARGET_WIDTH = MAX_EEA_R0_WIDTH
MAX_EEA_REMAINDER_TARGET_WIDTH = MAX_EEA_R1_WIDTH - 1
MAX_EEA_S2_TARGET_WIDTH = (
    MAX_EEA_R0_WIDTH + MAX_EEA_S_COEFFICIENT_WIDTH - 1
)
MAX_EEA_T2_TARGET_WIDTH = (
    MAX_EEA_R0_WIDTH + MAX_EEA_T_COEFFICIENT_WIDTH - 1
)
DivisionOperation = Callable[
    [
        PolynomialRegister,
        PolynomialRegister,
        PolynomialRegister,
        PolynomialRegister,
    ],
    tuple[
        PolynomialRegister,
        PolynomialRegister,
        PolynomialRegister,
        PolynomialRegister,
    ],
]
PolynomialAddOperation = Callable[
    [PolynomialRegister, PolynomialRegister, PolynomialRegister],
    tuple[PolynomialRegister, PolynomialRegister, PolynomialRegister],
]
PolynomialMultiplyOperation = PolynomialAddOperation
_EEAInputs = tuple[
    PolynomialRegister,
    PolynomialRegister,
    PolynomialRegister,
    PolynomialRegister,
    PolynomialRegister,
    PolynomialRegister,
]
_EEATargets = tuple[EEATarget, EEATarget, EEATarget, EEATarget]


def _validate_polynomial(
    register: object,
    name: str,
    maximum_width: int = MAX_POLYNOMIAL_REGISTER_WIDTH,
) -> PolynomialRegister:
    if type(register) is not tuple:
        raise TypeError(f"{name} must be a tuple of field elements")
    if not register:
        raise ValueError(f"{name} must contain at least one coefficient")
    if len(register) > maximum_width:
        raise ValueError(
            f"{name} must contain at most "
            f"{maximum_width} coefficients"
        )
    return tuple(validate_element(value) for value in register)


def _validate_target(
    target: object,
    expected_width: int,
    name: str,
) -> EEATarget:
    if type(target) is not tuple:
        raise TypeError(f"{name} must be a tuple of field elements")
    if len(target) != expected_width:
        raise ValueError(
            f"{name} must contain exactly {expected_width} coefficients"
        )
    return tuple(validate_element(value) for value in target)


def _pad(
    polynomial: PolynomialRegister,
    width: int,
) -> PolynomialRegister:
    if len(polynomial) > width:
        raise ValueError("polynomial does not fit the requested width")
    return polynomial + (0,) * (width - len(polynomial))


def _output_widths(
    inputs: _EEAInputs,
) -> tuple[int, int, int, int]:
    r0, r1, _, s1, _, t1 = inputs
    quotient_width = len(r0)
    remainder_width = max(1, len(r1) - 1)
    s_width = max(len(inputs[2]), quotient_width + len(s1) - 1)
    t_width = max(len(inputs[4]), quotient_width + len(t1) - 1)
    return quotient_width, remainder_width, s_width, t_width


def _compute_accumulate_uncompute(
    inputs: _EEAInputs,
    targets: _EEATargets,
    division_operation: DivisionOperation = xor_accumulate_polynomial_division,
    add_operation: PolynomialAddOperation = xor_accumulate_polynomial_add,
    multiply_operation: PolynomialMultiplyOperation = (
        xor_accumulate_polynomial_multiply
    ),
) -> tuple[_EEATargets, tuple[tuple[str, PolynomialRegister], ...]]:
    """Compute one EEA step, accumulate its outputs, and reverse scratch."""
    r0, r1, s0, s1, t0, t1 = inputs
    scratch: dict[str, PolynomialRegister] = {}

    q_width, r2_width, s2_width, t2_width = _output_widths(inputs)
    scratch["quotient"] = (0,) * q_width
    scratch["remainder"] = (0,) * r2_width
    _, _, scratch["quotient"], scratch["remainder"] = division_operation(
        r0,
        r1,
        scratch["quotient"],
        scratch["remainder"],
    )

    quotient = scratch["quotient"]
    identity_product_width = len(quotient) + len(r1) - 1
    identity_width = max(
        len(r0),
        identity_product_width,
        len(scratch["remainder"]),
    )
    scratch["identity_product"] = (0,) * identity_product_width
    _, _, scratch["identity_product"] = multiply_operation(
        quotient,
        r1,
        scratch["identity_product"],
    )
    scratch["identity_reconstruction"] = (0,) * identity_width
    _, _, scratch["identity_reconstruction"] = add_operation(
        _pad(scratch["identity_product"], identity_width),
        _pad(scratch["remainder"], identity_width),
        scratch["identity_reconstruction"],
    )
    if scratch["identity_reconstruction"] != _pad(r0, identity_width):
        raise ArithmeticError("EEA division outputs do not reconstruct r0")

    scratch["s_product"] = (0,) * (len(quotient) + len(s1) - 1)
    _, _, scratch["s_product"] = multiply_operation(
        quotient,
        s1,
        scratch["s_product"],
    )
    scratch["s_update"] = (0,) * s2_width
    _, _, scratch["s_update"] = add_operation(
        s0,
        scratch["s_product"],
        scratch["s_update"],
    )

    scratch["t_product"] = (0,) * (len(quotient) + len(t1) - 1)
    _, _, scratch["t_product"] = multiply_operation(
        quotient,
        t1,
        scratch["t_product"],
    )
    scratch["t_update"] = (0,) * t2_width
    _, _, scratch["t_update"] = add_operation(
        t0,
        scratch["t_product"],
        scratch["t_update"],
    )

    quotient_target, remainder_target, s_target, t_target = targets

    def accumulate(
        value: PolynomialRegister,
        target: EEATarget,
    ) -> EEATarget:
        zero = (0,) * len(value)
        _, _, updated = add_operation(value, zero, target)
        return updated

    updated_targets = (
        accumulate(quotient, quotient_target),
        accumulate(scratch["remainder"], remainder_target),
        accumulate(scratch["s_update"], s_target),
        accumulate(scratch["t_update"], t_target),
    )

    _, _, scratch["t_update"] = add_operation(
        t0,
        scratch["t_product"],
        scratch["t_update"],
    )
    _, _, scratch["t_product"] = multiply_operation(
        quotient,
        t1,
        scratch["t_product"],
    )
    _, _, scratch["s_update"] = add_operation(
        s0,
        scratch["s_product"],
        scratch["s_update"],
    )
    _, _, scratch["s_product"] = multiply_operation(
        quotient,
        s1,
        scratch["s_product"],
    )

    _, _, scratch["identity_reconstruction"] = add_operation(
        _pad(scratch["identity_product"], identity_width),
        _pad(scratch["remainder"], identity_width),
        scratch["identity_reconstruction"],
    )
    _, _, scratch["identity_product"] = multiply_operation(
        quotient,
        r1,
        scratch["identity_product"],
    )
    _, _, scratch["quotient"], scratch["remainder"] = division_operation(
        r0,
        r1,
        scratch["quotient"],
        scratch["remainder"],
    )

    return updated_targets, tuple(scratch.items())


def xor_accumulate_eea_transition(
    r0: PolynomialRegister,
    r1: PolynomialRegister,
    s0: PolynomialRegister,
    s1: PolynomialRegister,
    t0: PolynomialRegister,
    t1: PolynomialRegister,
    quotient_target: EEATarget,
    remainder_target: EEATarget,
    s2_target: EEATarget,
    t2_target: EEATarget,
) -> tuple[
    PolynomialRegister,
    PolynomialRegister,
    PolynomialRegister,
    PolynomialRegister,
    PolynomialRegister,
    PolynomialRegister,
    EEATarget,
    EEATarget,
    EEATarget,
    EEATarget,
]:
    """XOR-accumulate one quotient/remainder/Bézout EEA transition.

    Each input polynomial is a nonempty low-degree-first GF(2^12) tuple of at
    most eight coefficients. ``r1`` must be nonzero. Target widths are exact:
    quotient ``len(r0)``, remainder ``max(1, len(r1) - 1)``, and Bézout
    updates ``max(len(s0), len(r0) + len(s1) - 1)`` and
    ``max(len(t0), len(r0) + len(t1) - 1)``.

    The transition follows ``r0 = q*r1 + r2``,
    ``s2 = s0 + q*s1``, and ``t2 = t0 + q*t1`` over GF(2^12) polynomials.
    """
    input_registers = (
        _validate_polynomial(r0, "r0"),
        _validate_polynomial(r1, "r1"),
        _validate_polynomial(s0, "s0"),
        _validate_polynomial(s1, "s1"),
        _validate_polynomial(t0, "t0"),
        _validate_polynomial(t1, "t1"),
    )
    target_widths = _output_widths(input_registers)
    output_targets = (
        _validate_target(quotient_target, target_widths[0], "quotient_target"),
        _validate_target(
            remainder_target,
            target_widths[1],
            "remainder_target",
        ),
        _validate_target(s2_target, target_widths[2], "s2_target"),
        _validate_target(t2_target, target_widths[3], "t2_target"),
    )
    if not any(input_registers[1]):
        raise ZeroDivisionError("current remainder r1 must be nonzero")

    updated_targets, scratch = _compute_accumulate_uncompute(
        input_registers,
        output_targets,
    )
    if any(any(register) for _, register in scratch):
        raise RuntimeError("EEA transition left nonzero scratch")

    return (*input_registers, *updated_targets)


def xor_accumulate_capacity_aware_eea_transition(
    r0: PolynomialRegister,
    r1: PolynomialRegister,
    s0: PolynomialRegister,
    s1: PolynomialRegister,
    t0: PolynomialRegister,
    t1: PolynomialRegister,
    quotient_target: EEATarget,
    remainder_target: EEATarget,
    s2_target: EEATarget,
    t2_target: EEATarget,
    *,
    max_r0_width: int = MAX_EEA_R0_WIDTH,
    max_r1_width: int = MAX_EEA_R1_WIDTH,
    max_s_coefficient_width: int = MAX_EEA_S_COEFFICIENT_WIDTH,
    max_t_coefficient_width: int = MAX_EEA_T_COEFFICIENT_WIDTH,
) -> tuple[
    PolynomialRegister,
    PolynomialRegister,
    PolynomialRegister,
    PolynomialRegister,
    PolynomialRegister,
    PolynomialRegister,
    EEATarget,
    EEATarget,
    EEATarget,
    EEATarget,
]:
    """Accumulate one capacity-bounded EEA step into four XOR targets.

    The six nonempty, low-degree-first inputs use the GF(2^12) fixed-width
    representation. Their default maximum widths are ``r0=71``, ``r1=70``,
    ``s0/s1=35``, and ``t0/t1=36``. Lower per-call limits may be supplied,
    but cannot exceed those maxima. These are storage limits, not checks of
    the standard EEA state invariant.

    Target widths follow the underlying P015/P010 APIs exactly:
    ``q=len(r0)``, ``r2=max(1, len(r1)-1)``,
    ``s2=max(len(s0), len(r0)+len(s1)-1)``, and likewise for ``t2``.
    Therefore the Bézout targets retain the full declared-width convolution,
    even when an invariant-valid EEA state would have smaller significant
    support. ``r1`` must be nonzero.
    """
    capacity_limits = (
        ("max_r0_width", max_r0_width, MAX_EEA_R0_WIDTH),
        ("max_r1_width", max_r1_width, MAX_EEA_R1_WIDTH),
        (
            "max_s_coefficient_width",
            max_s_coefficient_width,
            MAX_EEA_S_COEFFICIENT_WIDTH,
        ),
        (
            "max_t_coefficient_width",
            max_t_coefficient_width,
            MAX_EEA_T_COEFFICIENT_WIDTH,
        ),
    )
    for name, value, hard_limit in capacity_limits:
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer")
        if not 1 <= value <= hard_limit:
            raise ValueError(f"{name} must be in [1, {hard_limit}]")

    input_registers = (
        _validate_polynomial(r0, "r0", max_r0_width),
        _validate_polynomial(r1, "r1", max_r1_width),
        _validate_polynomial(
            s0,
            "s0",
            max_s_coefficient_width,
        ),
        _validate_polynomial(
            s1,
            "s1",
            max_s_coefficient_width,
        ),
        _validate_polynomial(
            t0,
            "t0",
            max_t_coefficient_width,
        ),
        _validate_polynomial(
            t1,
            "t1",
            max_t_coefficient_width,
        ),
    )
    target_widths = _output_widths(input_registers)
    if target_widths[0] > MAX_EEA_QUOTIENT_TARGET_WIDTH:
        raise ValueError("quotient target capacity exceeded")
    if target_widths[1] > MAX_EEA_REMAINDER_TARGET_WIDTH:
        raise ValueError("remainder target capacity exceeded")
    if target_widths[2] > MAX_EEA_S2_TARGET_WIDTH:
        raise ValueError("s2 target capacity exceeded")
    if target_widths[3] > MAX_EEA_T2_TARGET_WIDTH:
        raise ValueError("t2 target capacity exceeded")

    output_targets = (
        _validate_target(quotient_target, target_widths[0], "quotient_target"),
        _validate_target(
            remainder_target,
            target_widths[1],
            "remainder_target",
        ),
        _validate_target(s2_target, target_widths[2], "s2_target"),
        _validate_target(t2_target, target_widths[3], "t2_target"),
    )
    if not any(input_registers[1]):
        raise ZeroDivisionError("current remainder r1 must be nonzero")

    updated_targets, scratch = _compute_accumulate_uncompute(
        input_registers,
        output_targets,
    )
    if any(any(register) for _, register in scratch):
        raise RuntimeError("EEA transition left nonzero scratch")

    return (*input_registers, *updated_targets)
