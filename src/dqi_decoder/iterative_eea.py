"""Bounded classical register model for thresholded polynomial EEA."""

from collections.abc import Callable
from dataclasses import dataclass

from .field import validate_element
from .reversible_eea import (
    MAX_EEA_R0_WIDTH,
    MAX_EEA_R1_WIDTH,
    MAX_EEA_S_COEFFICIENT_WIDTH,
    MAX_EEA_T_COEFFICIENT_WIDTH,
    xor_accumulate_capacity_aware_eea_transition,
)
from .reversible_polynomial import (
    PolynomialRegister,
    xor_accumulate_polynomial_add,
    xor_accumulate_polynomial_multiply,
)

EEA_THRESHOLD = 35
EEA_MAX_ROUNDS = 35
_EEA_STEP_RESULT = tuple[PolynomialRegister, ...]
_EEAStep = Callable[..., _EEA_STEP_RESULT]


class EEAInvariantError(RuntimeError):
    """Raised when a state violates a required bounded EEA invariant."""


@dataclass(frozen=True)
class EEAState:
    r0: PolynomialRegister
    r1: PolynomialRegister
    s0: PolynomialRegister
    s1: PolynomialRegister
    t0: PolynomialRegister
    t1: PolynomialRegister

    def as_registers(self) -> tuple[PolynomialRegister, ...]:
        return (self.r0, self.r1, self.s0, self.s1, self.t0, self.t1)


@dataclass(frozen=True)
class EEAAroundTrace:
    round_index: int
    active: bool
    source_state: EEAState
    next_state: EEAState
    quotient: PolynomialRegister | None
    remainder: PolynomialRegister | None
    s2: PolynomialRegister | None
    t2: PolynomialRegister | None
    source_preserved: bool
    high_windows_zero: bool
    temporary_outputs_cleared: bool
    source_destination_registers_distinct: bool
    degree_before: int
    degree_after: int


@dataclass(frozen=True)
class BoundedEEAResult:
    input_syndrome: PolynomialRegister
    initial_state: EEAState
    final_state: EEAState
    threshold: int
    round_limit: int
    active_rounds: int
    termination_reason: str
    trace: tuple[EEAAroundTrace, ...]


def _degree(polynomial: PolynomialRegister) -> int:
    for index in range(len(polynomial) - 1, -1, -1):
        if polynomial[index] != 0:
            return index
    return -1


def _fresh_copy(
    polynomial: PolynomialRegister,
    width: int,
) -> PolynomialRegister:
    if len(polynomial) > width:
        raise EEAInvariantError("polynomial exceeds destination capacity")
    return tuple(
        polynomial[index] if index < len(polynomial) else 0
        for index in range(width)
    )


def _copy_proven_window(
    polynomial: PolynomialRegister,
    width: int,
) -> PolynomialRegister:
    if len(polynomial) < width:
        raise EEAInvariantError("polynomial is narrower than its state window")
    if any(polynomial[width:]):
        raise EEAInvariantError(
            "polynomial has a nonzero coefficient outside its proven window"
        )
    return tuple(polynomial[index] for index in range(width))


def _validate_initial_syndrome(
    syndrome: object,
) -> tuple[PolynomialRegister, PolynomialRegister]:
    if type(syndrome) is not tuple:
        raise TypeError("syndrome must be a tuple of field elements")
    if not syndrome:
        raise ValueError("syndrome must contain at least one coefficient")
    if len(syndrome) > MAX_EEA_R1_WIDTH:
        raise ValueError(
            f"syndrome must contain at most {MAX_EEA_R1_WIDTH} coefficients"
        )
    validated = tuple(validate_element(value) for value in syndrome)
    if _degree(validated) < 0:
        raise ZeroDivisionError("zero syndrome is outside the EEA domain")
    if _degree(validated) > MAX_EEA_R1_WIDTH - 1:
        raise ValueError("syndrome degree exceeds the supported bound")
    return validated, _fresh_copy(validated, MAX_EEA_R1_WIDTH)


def _verify_bezout_state(
    state: EEAState,
    dividend: PolynomialRegister,
    syndrome: PolynomialRegister,
) -> None:
    for remainder, s_coefficient, t_coefficient in (
        (state.r0, state.s0, state.t0),
        (state.r1, state.s1, state.t1),
    ):
        s_product_width = len(s_coefficient) + len(dividend) - 1
        t_product_width = len(t_coefficient) + len(syndrome) - 1
        width = max(len(remainder), s_product_width, t_product_width)
        s_product = (0,) * s_product_width
        t_product = (0,) * t_product_width
        _, _, s_product = xor_accumulate_polynomial_multiply(
            s_coefficient,
            dividend,
            s_product,
        )
        _, _, t_product = xor_accumulate_polynomial_multiply(
            t_coefficient,
            syndrome,
            t_product,
        )
        _, _, reconstructed = xor_accumulate_polynomial_add(
            _fresh_copy(s_product, width),
            _fresh_copy(t_product, width),
            (0,) * width,
        )
        if reconstructed != _fresh_copy(remainder, width):
            raise EEAInvariantError("Bézout state invariant failed")


def _compose_one_round(
    state: EEAState,
    round_index: int,
    threshold: int,
    step: _EEAStep,
) -> tuple[EEAState, EEAAroundTrace]:
    source = state.as_registers()
    quotient_target = (0,) * len(state.r0)
    remainder_target = (0,) * max(1, len(state.r1) - 1)
    s2_width = max(
        len(state.s0),
        len(state.r0) + len(state.s1) - 1,
    )
    t2_width = max(
        len(state.t0),
        len(state.r0) + len(state.t1) - 1,
    )
    s2_target = (0,) * s2_width
    t2_target = (0,) * t2_width

    computed = step(*source, quotient_target, remainder_target, s2_target, t2_target)
    if len(computed) != 10 or tuple(computed[:6]) != source:
        raise EEAInvariantError("EEA transition did not preserve its source")
    quotient, remainder, s2_wide, t2_wide = computed[6:]
    source_preserved = tuple(computed[:6]) == source
    expected_output_widths = (
        len(quotient_target),
        len(remainder_target),
        s2_width,
        t2_width,
    )
    output_widths_match = tuple(
        len(register)
        for register in (quotient, remainder, s2_wide, t2_wide)
    ) == expected_output_widths
    s_capacity = len(state.s0)
    t_capacity = len(state.t0)
    high_windows_zero = (
        not any(s2_wide[s_capacity:])
        and not any(t2_wide[t_capacity:])
    )

    next_state: EEAState | None = None
    try:
        if not output_widths_match:
            raise EEAInvariantError(
                "EEA transition returned an unexpected output width"
            )
        if not high_windows_zero:
            raise EEAInvariantError(
                "Bézout output has a nonzero coefficient outside its proven window"
            )
        next_state = EEAState(
            _fresh_copy(state.r1, len(state.r0)),
            _fresh_copy(remainder, len(state.r1)),
            _fresh_copy(state.s1, len(state.s0)),
            _copy_proven_window(s2_wide, s_capacity),
            _fresh_copy(state.t1, len(state.t0)),
            _copy_proven_window(t2_wide, t_capacity),
        )
    finally:
        cleared = step(
            *source,
            quotient,
            remainder,
            s2_wide,
            t2_wide,
        )
        if tuple(cleared[:6]) != source or any(
            any(register) for register in cleared[6:]
        ):
            raise RuntimeError("EEA transition outputs failed to uncompute")
    if next_state is None:
        raise RuntimeError("EEA next state was not constructed")

    if any(
        destination is source_register
        for source_register, destination in zip(
            source,
            next_state.as_registers(),
        )
    ):
        raise EEAInvariantError("source and destination state banks alias")

    source_preserved = source == state.as_registers()
    degree_before = _degree(state.r1)
    degree_after = _degree(next_state.r1)
    if degree_after >= 0 and degree_after >= degree_before:
        raise EEAInvariantError("EEA remainder degree did not strictly decrease")
    trace = EEAAroundTrace(
        round_index=round_index,
        active=True,
        source_state=state,
        next_state=next_state,
        quotient=_fresh_copy(quotient, len(quotient)),
        remainder=_fresh_copy(remainder, len(remainder)),
        s2=_copy_proven_window(s2_wide, s_capacity),
        t2=_copy_proven_window(t2_wide, t_capacity),
        source_preserved=source_preserved,
        high_windows_zero=high_windows_zero,
        temporary_outputs_cleared=True,
        source_destination_registers_distinct=True,
        degree_before=degree_before,
        degree_after=degree_after,
    )
    return next_state, trace


def _run_bounded_schedule(
    initial_state: EEAState,
    threshold: int,
    round_limit: int,
    step: _EEAStep,
    verify_bezout: bool,
    input_syndrome: PolynomialRegister | None = None,
) -> BoundedEEAResult:
    if type(threshold) is not int or threshold < 1:
        raise ValueError("threshold must be a positive integer")
    if type(round_limit) is not int or round_limit < 0:
        raise ValueError("round_limit must be a nonnegative integer")
    if _degree(initial_state.r0) < _degree(initial_state.r1):
        raise ValueError("initial remainder degrees must be ordered")
    if _degree(initial_state.r1) < 0:
        raise ZeroDivisionError("initial current remainder must be nonzero")
    if verify_bezout:
        _verify_bezout_state(
            initial_state,
            initial_state.r0,
            initial_state.r1,
        )

    current = initial_state
    trace: list[EEAAroundTrace] = []
    active_rounds = 0
    for round_index in range(1, round_limit + 1):
        current_degree = _degree(current.r1)
        if current_degree < 0 or current_degree < threshold:
            trace.append(
                EEAAroundTrace(
                    round_index=round_index,
                    active=False,
                    source_state=current,
                    next_state=current,
                    quotient=None,
                    remainder=None,
                    s2=None,
                    t2=None,
                    source_preserved=True,
                    high_windows_zero=True,
                    temporary_outputs_cleared=True,
                    source_destination_registers_distinct=False,
                    degree_before=current_degree,
                    degree_after=current_degree,
                )
            )
            continue

        next_state, round_trace = _compose_one_round(
            current,
            round_index,
            threshold,
            step,
        )
        if verify_bezout:
            _verify_bezout_state(
                next_state,
                initial_state.r0,
                initial_state.r1,
            )
        trace.append(round_trace)
        current = next_state
        active_rounds += 1

    if _degree(current.r1) >= threshold:
        raise EEAInvariantError("round limit reached before termination")
    termination_reason = (
        "zero_remainder" if _degree(current.r1) < 0 else "below_threshold"
    )
    return BoundedEEAResult(
        input_syndrome=(
            initial_state.r1 if input_syndrome is None else input_syndrome
        ),
        initial_state=initial_state,
        final_state=current,
        threshold=threshold,
        round_limit=round_limit,
        active_rounds=active_rounds,
        termination_reason=termination_reason,
        trace=tuple(trace),
    )


def xor_accumulate_bounded_iterative_eea(
    syndrome: PolynomialRegister,
) -> BoundedEEAResult:
    """Run the bounded P008-shaped, standard-initialized threshold EEA.

    The accepted domain is a nonzero syndrome tuple of at most 70 GF(2^12)
    coefficients, paired with the fixed dividend ``z^70``. The syndrome's
    effective degree is therefore at most 69. Initialization is
    ``(r0,r1,s0,s1,t0,t1)=(z^70,S,1,0,0,1)`` with fixed state widths
    `(71,70,35,35,36,36)`. The threshold and schedule are fixed at 35 rounds.

    The return value is a classical EEA result and retained round trace, not
    an input-preserving XOR map or a quantum circuit. Each active transition
    uses P016's input-preserving relation, transfers only invariant-proven
    low coefficient windows into a fresh state bank, and reapplies P016 to
    clear its full-width temporary output targets.
    """
    original_syndrome, initial_syndrome = _validate_initial_syndrome(syndrome)
    dividend = (0,) * (MAX_EEA_R0_WIDTH - 1) + (1,)
    initial_state = EEAState(
        dividend,
        initial_syndrome,
        (1,) + (0,) * (MAX_EEA_S_COEFFICIENT_WIDTH - 1),
        (0,) * MAX_EEA_S_COEFFICIENT_WIDTH,
        (0,) * MAX_EEA_T_COEFFICIENT_WIDTH,
        (1,) + (0,) * (MAX_EEA_T_COEFFICIENT_WIDTH - 1),
    )
    return _run_bounded_schedule(
        initial_state,
        EEA_THRESHOLD,
        EEA_MAX_ROUNDS,
        xor_accumulate_capacity_aware_eea_transition,
        verify_bezout=True,
        input_syndrome=original_syndrome,
    )
