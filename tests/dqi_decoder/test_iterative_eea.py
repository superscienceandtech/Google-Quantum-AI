import unittest

from dqi_decoder.iterative_eea import (
    EEAInvariantError,
    EEAState,
    EEA_THRESHOLD,
    _compose_one_round,
    _run_bounded_schedule,
    xor_accumulate_bounded_iterative_eea,
)
from dqi_decoder.reversible_eea import (
    MAX_EEA_R0_WIDTH,
    MAX_EEA_R1_WIDTH,
    MAX_EEA_S_COEFFICIENT_WIDTH,
    MAX_EEA_T_COEFFICIENT_WIDTH,
)

_GF12_MODULUS = 0x1053
_SMALL_MODULI = {2: 0b111, 3: 0b1011, 4: 0b10011}


def _reference_multiply(
    left: int,
    right: int,
    degree: int,
    modulus: int,
) -> int:
    product = 0
    while right:
        if right & 1:
            product ^= left
        right >>= 1
        left <<= 1
        if left & (1 << degree):
            left ^= modulus
    return product & ((1 << degree) - 1)


def _reference_inverse(value: int, degree: int, modulus: int) -> int:
    if value == 0:
        raise ZeroDivisionError("zero has no inverse")
    result = 1
    factor = value
    exponent = (1 << degree) - 2
    while exponent:
        if exponent & 1:
            result = _reference_multiply(result, factor, degree, modulus)
        factor = _reference_multiply(factor, factor, degree, modulus)
        exponent >>= 1
    return result


def _trim(values: list[int]) -> tuple[int, ...]:
    while values and values[-1] == 0:
        values.pop()
    return tuple(values)


def _degree(polynomial: tuple[int, ...]) -> int:
    for index in range(len(polynomial) - 1, -1, -1):
        if polynomial[index]:
            return index
    return -1


def _reference_add(
    left: tuple[int, ...],
    right: tuple[int, ...],
) -> tuple[int, ...]:
    width = max(len(left), len(right))
    return _trim(
        [
            (left[index] if index < len(left) else 0)
            ^ (right[index] if index < len(right) else 0)
            for index in range(width)
        ]
    )


def _reference_polynomial_multiply(
    left: tuple[int, ...],
    right: tuple[int, ...],
    degree: int,
    modulus: int,
) -> tuple[int, ...]:
    if not left or not right:
        return ()
    result = [0] * (len(left) + len(right) - 1)
    for left_index, left_value in enumerate(left):
        for right_index, right_value in enumerate(right):
            result[left_index + right_index] ^= _reference_multiply(
                left_value,
                right_value,
                degree,
                modulus,
            )
    return _trim(result)


def _reference_division(
    dividend: tuple[int, ...],
    divisor: tuple[int, ...],
    degree: int,
    modulus: int,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    remainder = list(_trim(list(dividend)))
    denominator = _trim(list(divisor))
    if not denominator:
        raise ZeroDivisionError("zero polynomial divisor")
    quotient = [0] * max(0, len(remainder) - len(denominator) + 1)
    inverse_leading = _reference_inverse(denominator[-1], degree, modulus)
    while remainder and len(remainder) >= len(denominator):
        shift = len(remainder) - len(denominator)
        factor = _reference_multiply(
            remainder[-1],
            inverse_leading,
            degree,
            modulus,
        )
        quotient[shift] ^= factor
        for index, coefficient in enumerate(denominator):
            remainder[shift + index] ^= _reference_multiply(
                factor,
                coefficient,
                degree,
                modulus,
            )
        remainder = list(_trim(remainder))
    return _trim(quotient), tuple(remainder)


def _pad(polynomial: tuple[int, ...], width: int) -> tuple[int, ...]:
    if len(polynomial) > width:
        raise AssertionError("oracle polynomial exceeds expected width")
    return polynomial + (0,) * (width - len(polynomial))


def _reference_transition_outputs(
    inputs: tuple[tuple[int, ...], ...],
    degree: int,
    modulus: int,
) -> tuple[tuple[int, ...], ...]:
    r0, r1, s0, s1, t0, t1 = inputs
    quotient, remainder = _reference_division(r0, r1, degree, modulus)
    s2 = _reference_add(
        s0,
        _reference_polynomial_multiply(quotient, s1, degree, modulus),
    )
    t2 = _reference_add(
        t0,
        _reference_polynomial_multiply(quotient, t1, degree, modulus),
    )
    return quotient, remainder, s2, t2


def _reference_step_relation(
    *arguments: tuple[int, ...],
    degree: int,
    modulus: int,
) -> tuple[tuple[int, ...], ...]:
    inputs = arguments[:6]
    targets = arguments[6:]
    outputs = _reference_transition_outputs(inputs, degree, modulus)
    return (
        *inputs,
        *(
            tuple(
                old ^ value
                for old, value in zip(target, _pad(output, len(target)))
            )
            for target, output in zip(targets, outputs)
        ),
    )


def _reference_iterative(
    dividend: tuple[int, ...],
    syndrome: tuple[int, ...],
    threshold: int,
    degree: int,
    modulus: int,
) -> tuple[
    tuple[tuple[tuple[int, ...], ...], ...],
    tuple[tuple[int, ...], ...],
]:
    r0, r1 = _trim(list(dividend)), _trim(list(syndrome))
    s0, s1 = (1,), ()
    t0, t1 = (), (1,)
    rounds: list[tuple[tuple[int, ...], ...]] = []
    while r1 and _degree(r1) >= threshold:
        q, r2 = _reference_division(r0, r1, degree, modulus)
        s2 = _reference_add(
            s0,
            _reference_polynomial_multiply(q, s1, degree, modulus),
        )
        t2 = _reference_add(
            t0,
            _reference_polynomial_multiply(q, t1, degree, modulus),
        )
        rounds.append((q, r2, s2, t2))
        r0, r1, s0, s1, t0, t1 = r1, r2, s1, s2, t1, t2
    return tuple(rounds), (r0, r1, s0, s1, t0, t1)


def _small_field_step(
    degree: int,
    modulus: int,
):
    def step(*arguments: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
        return _reference_step_relation(
            *arguments,
            degree=degree,
            modulus=modulus,
        )

    return step


def _small_initial_state(
    dividend: tuple[int, ...],
    syndrome: tuple[int, ...],
) -> EEAState:
    return EEAState(
        dividend,
        syndrome,
        (1, 0),
        (0, 0),
        (0, 0),
        (1, 0),
    )


class BoundedIterativeEEATests(unittest.TestCase):
    def test_initialization_and_already_below_threshold(self) -> None:
        syndrome = (0x123, 0x456)
        result = xor_accumulate_bounded_iterative_eea(syndrome)
        self.assertEqual(result.initial_state.r0, (0,) * 70 + (1,))
        self.assertEqual(result.initial_state.r1[:2], (0x123, 0x456))
        self.assertEqual(result.input_syndrome, syndrome)
        self.assertEqual(result.initial_state.s0, (1,) + (0,) * 34)
        self.assertEqual(result.initial_state.s1, (0,) * 35)
        self.assertEqual(result.initial_state.t0, (0,) * 36)
        self.assertEqual(result.initial_state.t1, (1,) + (0,) * 35)
        self.assertEqual(result.active_rounds, 0)
        self.assertEqual(result.termination_reason, "below_threshold")
        self.assertEqual(len(result.trace), 35)
        self.assertTrue(all(not entry.active for entry in result.trace))
        self.assertEqual(
            result,
            xor_accumulate_bounded_iterative_eea(syndrome),
        )

    def test_zero_syndrome_and_invalid_inputs_are_rejected(self) -> None:
        for syndrome, error in (
            ((0,), ZeroDivisionError),
            ((0,) * 70, ZeroDivisionError),
            ((1,) * 71, ValueError),
            ((True,), TypeError),
            ((4096,), ValueError),
            ([], TypeError),
            ((), ValueError),
        ):
            with self.subTest(syndrome=syndrome):
                with self.assertRaises(error):
                    xor_accumulate_bounded_iterative_eea(syndrome)

    def test_divisible_input_terminates_with_zero_remainder(self) -> None:
        syndrome = (0,) * 35 + (1,)
        result = xor_accumulate_bounded_iterative_eea(syndrome)
        self.assertEqual(result.active_rounds, 1)
        self.assertEqual(result.termination_reason, "zero_remainder")
        self.assertEqual(_degree(result.final_state.r1), -1)
        self.assertEqual(result.trace[0].quotient[35], 1)
        self.assertTrue(all(not entry.active for entry in result.trace[1:]))

    def test_exhaustive_small_field_multiround_domains(self) -> None:
        pair_counts: dict[int, int] = {}
        active_round_counts: dict[int, int] = {}
        for degree, modulus in _SMALL_MODULI.items():
            field_size = 1 << degree
            pairs = 0
            active_rounds = 0
            for a_value in range(1, field_size**2):
                dividend = (a_value % field_size, a_value // field_size)
                for b_value in range(1, field_size**2):
                    syndrome = (b_value % field_size, b_value // field_size)
                    if _degree(dividend) < _degree(syndrome):
                        continue
                    pairs += 1
                    expected_rounds, expected_final = _reference_iterative(
                        dividend,
                        syndrome,
                        threshold=1,
                        degree=degree,
                        modulus=modulus,
                    )
                    initial = _small_initial_state(dividend, syndrome)
                    schedule_limit = max(0, _degree(syndrome))
                    result = _run_bounded_schedule(
                        initial,
                        threshold=1,
                        round_limit=schedule_limit,
                        step=_small_field_step(degree, modulus),
                        verify_bezout=False,
                    )
                    self.assertEqual(result.active_rounds, len(expected_rounds))
                    self.assertEqual(
                        len([entry for entry in result.trace if entry.active]),
                        len(expected_rounds),
                    )
                    for trace, expected in zip(
                        (entry for entry in result.trace if entry.active),
                        expected_rounds,
                    ):
                        reconstructed_dividend = _reference_add(
                            _reference_polynomial_multiply(
                                expected[0],
                                _trim(list(trace.source_state.r1)),
                                degree,
                                modulus,
                            ),
                            expected[1],
                        )
                        self.assertEqual(
                            reconstructed_dividend,
                            _trim(list(trace.source_state.r0)),
                        )
                        self.assertLess(
                            _degree(expected[1]),
                            _degree(trace.source_state.r1),
                        )
                        self.assertEqual(
                            trace.quotient,
                            _pad(expected[0], len(trace.quotient)),
                        )
                        self.assertEqual(
                            trace.remainder,
                            _pad(expected[1], len(trace.remainder)),
                        )
                        self.assertEqual(
                            trace.s2,
                            _pad(expected[2], len(trace.s2)),
                        )
                        self.assertEqual(
                            trace.t2,
                            _pad(expected[3], len(trace.t2)),
                        )
                        self.assertTrue(trace.high_windows_zero)
                        self.assertTrue(trace.temporary_outputs_cleared)
                        self.assertTrue(trace.source_preserved)
                        self.assertTrue(
                            trace.source_destination_registers_distinct
                        )
                    final = result.final_state.as_registers()
                    self.assertEqual(
                        tuple(_trim(list(poly)) for poly in final),
                        expected_final,
                    )
                    self.assertTrue(
                        result.termination_reason
                        in ("below_threshold", "zero_remainder")
                    )
                    active_rounds += result.active_rounds
            self.assertEqual(
                pairs,
                (field_size - 1) * (field_size**3 - 1),
            )
            pair_counts[degree] = pairs
            active_round_counts[degree] = active_rounds

        self.assertEqual(
            pair_counts,
            {2: 189, 3: 3577, 4: 61425},
        )
        self.assertEqual(
            active_round_counts,
            {2: 144, 3: 3136, 4: 57600},
        )

    def test_transfer_checks_high_windows_and_cleans_before_failure(self) -> None:
        source = _small_initial_state((0, 1), (1, 1))
        calls = 0

        def invalid_step(*arguments: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
            nonlocal calls
            calls += 1
            inputs = arguments[:6]
            targets = arguments[6:]
            outputs = (
                (0, 1),
                (0,),
                (0, 0, 0x123),
                (0, 0, 0),
            )
            return (
                *inputs,
                *(
                    tuple(
                        initial ^ value
                        for initial, value in zip(target, _pad(output, len(target)))
                    )
                    for target, output in zip(targets, outputs)
                ),
            )

        with self.assertRaises(EEAInvariantError):
            _compose_one_round(source, 1, 1, invalid_step)
        self.assertEqual(calls, 2)
        self.assertEqual(source, _small_initial_state((0, 1), (1, 1)))

    def test_maximum_width_and_35_round_boundary(self) -> None:
        dividend = (0,) * (MAX_EEA_R0_WIDTH - 1) + (1,)
        syndrome = tuple(
            ((index * 0x31) ^ 0x17 ^ 0xA57) & 0xFFF
            for index in range(MAX_EEA_R1_WIDTH - 1)
        ) + (1,)
        expected_rounds, expected_final = _reference_iterative(
            dividend,
            syndrome,
            EEA_THRESHOLD,
            12,
            _GF12_MODULUS,
        )
        self.assertEqual(len(expected_rounds), 35)

        result = xor_accumulate_bounded_iterative_eea(syndrome)
        active_trace = tuple(entry for entry in result.trace if entry.active)
        self.assertEqual(result.active_rounds, 35)
        self.assertEqual(len(active_trace), 35)
        self.assertEqual(len(result.trace), 35)
        self.assertEqual(result.termination_reason, "below_threshold")
        self.assertEqual(_degree(result.final_state.r1), 34)
        self.assertEqual(
            tuple(_trim(list(poly)) for poly in result.final_state.as_registers()),
            expected_final,
        )

        for trace, expected in zip(active_trace, expected_rounds):
            reconstructed_dividend = _reference_add(
                _reference_polynomial_multiply(
                    expected[0],
                    _trim(list(trace.source_state.r1)),
                    12,
                    _GF12_MODULUS,
                ),
                expected[1],
            )
            self.assertEqual(
                reconstructed_dividend,
                _trim(list(trace.source_state.r0)),
            )
            self.assertLess(
                _degree(expected[1]),
                _degree(trace.source_state.r1),
            )
            self.assertEqual(trace.quotient, _pad(expected[0], 71))
            self.assertEqual(trace.remainder, _pad(expected[1], 69))
            self.assertEqual(
                trace.s2,
                _pad(expected[2], MAX_EEA_S_COEFFICIENT_WIDTH),
            )
            self.assertEqual(
                trace.t2,
                _pad(expected[3], MAX_EEA_T_COEFFICIENT_WIDTH),
            )
            self.assertTrue(trace.high_windows_zero)
            self.assertTrue(trace.temporary_outputs_cleared)
            self.assertTrue(trace.source_preserved)
            self.assertTrue(trace.source_destination_registers_distinct)
            self.assertLess(trace.degree_after, trace.degree_before)
        self.assertEqual(
            max(_degree(trace.s2) for trace in active_trace),
            MAX_EEA_S_COEFFICIENT_WIDTH - 1,
        )
        self.assertEqual(
            max(_degree(trace.t2) for trace in active_trace),
            MAX_EEA_T_COEFFICIENT_WIDTH - 1,
        )
        self.assertEqual(
            len(result.initial_state.r0),
            MAX_EEA_R0_WIDTH,
        )
        self.assertEqual(
            len(result.initial_state.r1),
            MAX_EEA_R1_WIDTH,
        )


if __name__ == "__main__":
    unittest.main()
