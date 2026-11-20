import unittest

from dqi_decoder.reversible_division import (
    MAX_POLYNOMIAL_REGISTER_WIDTH,
)
from dqi_decoder.reversible_eea import (
    MAX_EEA_R0_WIDTH,
    MAX_EEA_R1_WIDTH,
    MAX_EEA_S2_TARGET_WIDTH,
    MAX_EEA_S_COEFFICIENT_WIDTH,
    MAX_EEA_T2_TARGET_WIDTH,
    MAX_EEA_T_COEFFICIENT_WIDTH,
    _compute_accumulate_uncompute,
    xor_accumulate_capacity_aware_eea_transition,
    xor_accumulate_eea_transition,
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


def _reference_inverse(
    value: int,
    degree: int,
    modulus: int,
) -> int:
    if value == 0:
        raise ZeroDivisionError("zero has no field inverse")
    result = 1
    factor = value
    exponent = (1 << degree) - 2
    while exponent:
        if exponent & 1:
            result = _reference_multiply(result, factor, degree, modulus)
        factor = _reference_multiply(factor, factor, degree, modulus)
        exponent >>= 1
    return result


def _trim(polynomial: list[int]) -> tuple[int, ...]:
    while polynomial and polynomial[-1] == 0:
        polynomial.pop()
    return tuple(polynomial)


def _degree(polynomial: tuple[int, ...]) -> int:
    return len(_trim(list(polynomial))) - 1


def _reference_division(
    dividend: tuple[int, ...],
    divisor: tuple[int, ...],
    degree: int = 12,
    modulus: int = _GF12_MODULUS,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    remainder = list(_trim(list(dividend)))
    denominator = _trim(list(divisor))
    if not denominator:
        raise ZeroDivisionError("zero polynomial divisor")
    quotient = [0] * max(0, len(remainder) - len(denominator) + 1)
    inverse_leading = _reference_inverse(denominator[-1], degree, modulus)

    while remainder and len(remainder) >= len(denominator):
        shift = len(remainder) - len(denominator)
        scale = _reference_multiply(
            remainder[-1],
            inverse_leading,
            degree,
            modulus,
        )
        quotient[shift] ^= scale
        for index, coefficient in enumerate(denominator):
            remainder[shift + index] ^= _reference_multiply(
                scale,
                coefficient,
                degree,
                modulus,
            )
        remainder = list(_trim(remainder))

    return _trim(quotient), tuple(remainder)


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
    degree: int = 12,
    modulus: int = _GF12_MODULUS,
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


def _pad(polynomial: tuple[int, ...], width: int) -> tuple[int, ...]:
    return polynomial + (0,) * (width - len(polynomial))


def _reference_transition(
    inputs: tuple[tuple[int, ...], ...],
    degree: int = 12,
    modulus: int = _GF12_MODULUS,
) -> tuple[tuple[int, ...], ...]:
    r0, r1, s0, s1, t0, t1 = inputs
    quotient, remainder = _reference_division(
        r0,
        r1,
        degree,
        modulus,
    )
    s_update = _reference_add(
        s0,
        _reference_polynomial_multiply(quotient, s1, degree, modulus),
    )
    t_update = _reference_add(
        t0,
        _reference_polynomial_multiply(quotient, t1, degree, modulus),
    )
    return quotient, remainder, s_update, t_update


def _small_add_operation(
    left: tuple[int, ...],
    right: tuple[int, ...],
    target: tuple[int, ...],
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    width = max(len(left), len(right))
    output = tuple(
        target[index] ^ (left[index] if index < len(left) else 0)
        ^ (right[index] if index < len(right) else 0)
        for index in range(width)
    )
    return left, right, output


def _small_multiply_operation(
    left: tuple[int, ...],
    right: tuple[int, ...],
    target: tuple[int, ...],
    degree: int,
    modulus: int,
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    product = _reference_polynomial_multiply(left, right, degree, modulus)
    output = tuple(
        target[index] ^ (product[index] if index < len(product) else 0)
        for index in range(len(target))
    )
    return left, right, output


def _small_division_operation(
    dividend: tuple[int, ...],
    divisor: tuple[int, ...],
    quotient_target: tuple[int, ...],
    remainder_target: tuple[int, ...],
    degree: int,
    modulus: int,
) -> tuple[
    tuple[int, ...],
    tuple[int, ...],
    tuple[int, ...],
    tuple[int, ...],
]:
    quotient, remainder = _reference_division(
        dividend,
        divisor,
        degree,
        modulus,
    )
    quotient_padded = _pad(quotient, len(quotient_target))
    remainder_padded = _pad(remainder, len(remainder_target))
    return (
        dividend,
        divisor,
        tuple(
            target ^ value
            for target, value in zip(quotient_target, quotient_padded)
        ),
        tuple(
            target ^ value
            for target, value in zip(remainder_target, remainder_padded)
        ),
    )


class ReversibleEEATests(unittest.TestCase):
    def assert_transition(
        self,
        inputs: tuple[tuple[int, ...], ...],
        targets: tuple[tuple[int, ...], ...],
    ) -> tuple[tuple[int, ...], ...]:
        expected = _reference_transition(inputs)
        widths = (
            len(inputs[0]),
            max(1, len(inputs[1]) - 1),
            max(len(inputs[2]), len(inputs[0]) + len(inputs[3]) - 1),
            max(len(inputs[4]), len(inputs[0]) + len(inputs[5]) - 1),
        )
        expected_targets = tuple(
            tuple(
                target ^ value
                for target, value in zip(
                    initial_target,
                    _pad(expected_value, width),
                )
            )
            for initial_target, expected_value, width in zip(
                targets,
                expected,
                widths,
            )
        )
        result = xor_accumulate_eea_transition(*inputs, *targets)
        self.assertEqual(result[:6], inputs)
        self.assertEqual(result[6:], expected_targets)
        quotient, remainder, s_update, t_update = expected
        self.assertEqual(
            _reference_add(
                _reference_polynomial_multiply(quotient, inputs[1]),
                remainder,
            ),
            _trim(list(inputs[0])),
        )
        self.assertEqual(
            _reference_add(
                inputs[2],
                _reference_polynomial_multiply(quotient, inputs[3]),
            ),
            s_update,
        )
        self.assertEqual(
            _reference_add(
                inputs[4],
                _reference_polynomial_multiply(quotient, inputs[5]),
            ),
            t_update,
        )
        self.assertTrue(
            not remainder or _degree(remainder) < _degree(inputs[1])
        )
        self.assertEqual(
            xor_accumulate_eea_transition(*result),
            (*inputs, *targets),
        )
        return expected

    def test_conventional_initial_state_and_bezout_invariant(self) -> None:
        dividend = (0x123, 0x456, 0x789, 0xABC)
        divisor = (0x00F, 0x101)
        inputs = (
            dividend,
            divisor,
            (1,),
            (0,),
            (0,),
            (1,),
        )
        targets = ((0x111,) * 4, (0x222,), (0x333, 0x444, 0x555, 0x666), (0x777, 0x888, 0x999, 0xAAA))
        quotient, remainder, s2, t2 = self.assert_transition(inputs, targets)
        self.assertGreater(_degree(quotient), 0)
        self.assertEqual(
            _reference_add(
                _reference_polynomial_multiply(s2, dividend),
                _reference_polynomial_multiply(t2, divisor),
            ),
            remainder,
        )
        self.assertFalse(quotient == ())

    def test_degree_boundaries_zero_and_nonmonic_remainders(self) -> None:
        cases = (
            ((0, 0, 0), (0x003, 0x005), (1,), (0,), (0,), (1,)),
            ((0x123,), (0, 0x789), (1,), (0,), (0,), (1,)),
            ((0x123, 0x456, 0x789), (0x003,), (0x111,), (0x222,), (0x333,), (0x444,)),
            ((0x123, 0x456), (0x789, 0xABC), (0,), (0,), (0,), (0,)),
            ((0x123, 0x456, 0x789), (0x00F, 0x101), (0x111,), (0x222,), (0x333,), (0x444,)),
            ((0x123, 0x456, 0x789), (0x00F, 0x101), (0,), (0,), (0,), (0,)),
        )
        for inputs in cases:
            widths = (
                len(inputs[0]),
                max(1, len(inputs[1]) - 1),
                max(len(inputs[2]), len(inputs[0]) + len(inputs[3]) - 1),
                max(len(inputs[4]), len(inputs[0]) + len(inputs[5]) - 1),
            )
            targets = tuple(
                tuple((index + 1) * 0x101 for index in range(width))
                for width in widths
            )
            with self.subTest(inputs=inputs):
                quotient, remainder, _, _ = self.assert_transition(
                    inputs,
                    targets,
                )
                self.assertEqual(
                    _reference_add(
                        _reference_polynomial_multiply(
                            quotient,
                            inputs[1],
                        ),
                        remainder,
                    ),
                    _trim(list(inputs[0])),
                )

    def test_maximum_input_width_and_output_capacity(self) -> None:
        width = MAX_POLYNOMIAL_REGISTER_WIDTH
        inputs = (
            (0x123, 0x456, 0x789, 0xABC, 0x111, 0x222, 0x333, 0xFFF),
            (0x00F, 0x101, 0x303, 0x505, 0x707, 0x909, 0xB0B, 0xD0D),
            (0x123, 0x456, 0x789, 0xABC, 0x111, 0x222, 0x333, 0x444),
            (0x001, 0x002, 0x003, 0x004, 0x005, 0x006, 0x007, 0x008),
            (0xFFF, 0xEEE, 0xDDD, 0xCCC, 0xBBB, 0xAAA, 0x999, 0x888),
            (0x008, 0x007, 0x006, 0x005, 0x004, 0x003, 0x002, 0x001),
        )
        output_widths = (
            width,
            width - 1,
            2 * width - 1,
            2 * width - 1,
        )
        targets = tuple(
            tuple([0x321] * output_width)
            for output_width in output_widths
        )
        self.assert_transition(inputs, targets)

    def test_invalid_inputs_targets_and_zero_remainder_are_rejected(self) -> None:
        valid = (
            (1, 2),
            (3, 4),
            (1,),
            (0,),
            (0,),
            (1,),
        )
        widths = (2, 1, 2, 2)
        valid_targets = tuple((0,) * width for width in widths)
        with self.assertRaises(ZeroDivisionError):
            xor_accumulate_eea_transition(
                valid[0],
                (0, 0),
                *valid[2:],
                *valid_targets,
            )

        invalid_calls = (
            (((), *valid[1:]), valid_targets),
            ((valid[0], (1, 2, 3, 4, 5, 6, 7, 8, 9), *valid[2:]), valid_targets),
            ((valid[0], valid[1], (True,), *valid[3:]), valid_targets),
            ((valid[0], valid[1], *valid[2:]), ((0,), *valid_targets[1:])),
            ((valid[0], valid[1], *valid[2:]), (*valid_targets[:1], (0, 0), *valid_targets[2:])),
        )
        for inputs, targets in invalid_calls:
            with self.subTest(inputs=inputs, targets=targets):
                with self.assertRaises((TypeError, ValueError)):
                    xor_accumulate_eea_transition(*inputs, *targets)

    def test_exhaustive_remainder_pairs_and_bounded_bezout_states(self) -> None:
        bezout_states = (
            ((0,), (0,), (0,), (0,)),
            ((1,), (0,), (0,), (1,)),
        )
        counts: dict[int, tuple[int, int]] = {}
        for degree, modulus in _SMALL_MODULI.items():
            field_size = 1 << degree
            pair_count = 0
            case_count = 0
            for r0_value in range(field_size**2):
                r0 = (r0_value % field_size, r0_value // field_size)
                for r1_value in range(1, field_size**2):
                    r1 = (r1_value % field_size, r1_value // field_size)
                    pair_count += 1
                    for s0, s1, t0, t1 in bezout_states:
                        inputs = (r0, r1, s0, s1, t0, t1)
                        quotient_target = (r0[0] ^ r1[0], r0[1] ^ r1[1])
                        remainder_target = (r0[0] ^ r1[1],)
                        s_target = (r0[1], r1[0])
                        t_target = (r0[0], r1[1])
                        targets = (
                            quotient_target,
                            remainder_target,
                            s_target,
                            t_target,
                        )
                        expected = _reference_transition(
                            inputs,
                            degree,
                            modulus,
                        )
                        add_operation = _small_add_operation

                        def multiply_operation(
                            left: tuple[int, ...],
                            right: tuple[int, ...],
                            target: tuple[int, ...],
                            *,
                            _degree: int = degree,
                            _modulus: int = modulus,
                        ) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
                            return _small_multiply_operation(
                                left,
                                right,
                                target,
                                _degree,
                                _modulus,
                            )

                        def division_operation(
                            dividend: tuple[int, ...],
                            divisor: tuple[int, ...],
                            quotient: tuple[int, ...],
                            remainder: tuple[int, ...],
                            *,
                            _degree: int = degree,
                            _modulus: int = modulus,
                        ) -> tuple[
                            tuple[int, ...],
                            tuple[int, ...],
                            tuple[int, ...],
                            tuple[int, ...],
                        ]:
                            return _small_division_operation(
                                dividend,
                                divisor,
                                quotient,
                                remainder,
                                _degree,
                                _modulus,
                            )

                        updated, scratch = _compute_accumulate_uncompute(
                            inputs,
                            targets,
                            division_operation,
                            add_operation,
                            multiply_operation,
                        )
                        expected_targets = tuple(
                            tuple(
                                target ^ value
                                for target, value in zip(
                                    initial_target,
                                    _pad(value, len(initial_target)),
                                )
                            )
                            for initial_target, value in zip(targets, expected)
                        )
                        self.assertEqual(updated, expected_targets)
                        self.assertFalse(
                            any(any(register) for _, register in scratch)
                        )
                        repeated, repeated_scratch = (
                            _compute_accumulate_uncompute(
                                inputs,
                                updated,
                                division_operation,
                                add_operation,
                                multiply_operation,
                            )
                        )
                        self.assertEqual(repeated, targets)
                        self.assertFalse(
                            any(any(register) for _, register in repeated_scratch)
                        )
                        case_count += 1
            self.assertEqual(pair_count, field_size**2 * (field_size**2 - 1))
            self.assertEqual(case_count, pair_count * len(bezout_states))
            counts[degree] = pair_count, case_count

        self.assertEqual(
            counts,
            {
                2: (240, 480),
                3: (4032, 8064),
                4: (65280, 130560),
            },
        )


class CapacityAwareReversibleEEATests(unittest.TestCase):
    def assert_capacity_aware_transition(
        self,
        inputs: tuple[tuple[int, ...], ...],
        target_seed: int,
    ) -> tuple[tuple[int, ...], ...]:
        r0, r1, s0, s1, t0, t1 = inputs
        expected = _reference_transition(inputs)
        widths = (
            len(r0),
            max(1, len(r1) - 1),
            max(len(s0), len(r0) + len(s1) - 1),
            max(len(t0), len(r0) + len(t1) - 1),
        )
        targets = tuple(
            tuple(target_seed + index for _ in range(width))
            for index, width in enumerate(widths)
        )
        expected_targets = tuple(
            tuple(
                initial ^ value
                for initial, value in zip(
                    target,
                    _pad(output, len(target)),
                )
            )
            for target, output in zip(targets, expected)
        )

        result = xor_accumulate_capacity_aware_eea_transition(
            *inputs,
            *targets,
        )
        self.assertEqual(result[:6], inputs)
        self.assertEqual(result[6:], expected_targets)
        quotient, remainder, s2, t2 = expected
        self.assertEqual(
            _reference_add(
                _reference_polynomial_multiply(quotient, r1),
                remainder,
            ),
            _trim(list(r0)),
        )
        self.assertTrue(not remainder or _degree(remainder) < _degree(r1))
        self.assertEqual(
            s2,
            _reference_add(
                s0,
                _reference_polynomial_multiply(quotient, s1),
            ),
        )
        self.assertEqual(
            t2,
            _reference_add(
                t0,
                _reference_polynomial_multiply(quotient, t1),
            ),
        )
        repeated = xor_accumulate_capacity_aware_eea_transition(
            *result,
        )
        self.assertEqual(repeated, (*inputs, *targets))
        return expected

    def test_p014_quotient_support_and_full_convolution_targets(self) -> None:
        r0 = (0,) * 70 + (1,)
        r1 = (0,) * 35 + (0x123,)
        inputs = (
            r0,
            r1,
            (0x321,) * MAX_EEA_S_COEFFICIENT_WIDTH,
            (0x456,) * MAX_EEA_S_COEFFICIENT_WIDTH,
            (0x789,) * MAX_EEA_T_COEFFICIENT_WIDTH,
            (0xABC,) * MAX_EEA_T_COEFFICIENT_WIDTH,
        )
        quotient, _, _, _ = self.assert_capacity_aware_transition(inputs, 0x111)
        self.assertEqual(len(quotient), 36)
        self.assertEqual(_degree(quotient), 35)

        self.assertEqual(MAX_EEA_S2_TARGET_WIDTH, 105)
        self.assertEqual(MAX_EEA_T2_TARGET_WIDTH, 106)
        result = xor_accumulate_capacity_aware_eea_transition(
            *inputs,
            (0,) * MAX_EEA_R0_WIDTH,
            (0,) * (len(r1) - 1),
            (0,) * MAX_EEA_S2_TARGET_WIDTH,
            (0,) * MAX_EEA_T2_TARGET_WIDTH,
        )
        self.assertEqual(len(result[6]), MAX_EEA_R0_WIDTH)
        self.assertEqual(len(result[8]), MAX_EEA_S2_TARGET_WIDTH)
        self.assertEqual(len(result[9]), MAX_EEA_T2_TARGET_WIDTH)

    def test_small_intermediate_and_maximum_width_transitions(self) -> None:
        small = (
            (0x123, 0x456, 0x789, 0xABC),
            (0x00F, 0x101),
            (1,),
            (0x222, 0x333),
            (0,),
            (0x444, 0x555, 0x666),
        )
        self.assert_capacity_aware_transition(small, 0x111)

        intermediate = (
            tuple((index * 0x31 + 1) & 0xFFF for index in range(35)),
            tuple((index * 0x17 + 3) & 0xFFF for index in range(17)),
            (0x123,) * 35,
            (0x456,) * 35,
            (0x789,) * 36,
            (0xABC,) * 36,
        )
        self.assert_capacity_aware_transition(intermediate, 0x211)

        maximum = (
            (0,) * 70 + (0x321,),
            (0x111,) * 69 + (0x222,),
            (0x123,) * MAX_EEA_S_COEFFICIENT_WIDTH,
            (0x456,) * MAX_EEA_S_COEFFICIENT_WIDTH,
            (0x789,) * MAX_EEA_T_COEFFICIENT_WIDTH,
            (0xABC,) * MAX_EEA_T_COEFFICIENT_WIDTH,
        )
        self.assert_capacity_aware_transition(maximum, 0x311)
        self.assertGreater(len(maximum[0]), MAX_POLYNOMIAL_REGISTER_WIDTH)
        self.assertGreater(len(maximum[1]), MAX_POLYNOMIAL_REGISTER_WIDTH)

        maximum_shift_count = (
            maximum[0],
            (0x111,) + (0,) * (MAX_EEA_R1_WIDTH - 1),
            maximum[2],
            maximum[3],
            maximum[4],
            maximum[5],
        )
        quotient, remainder, _, _ = self.assert_capacity_aware_transition(
            maximum_shift_count,
            0x411,
        )
        self.assertEqual(len(quotient), MAX_EEA_R0_WIDTH)
        self.assertFalse(any(remainder))

    def test_capacity_limits_target_validation_and_zero_divisor(self) -> None:
        valid = (
            (1, 2),
            (3, 4),
            (1,),
            (0,),
            (0,),
            (1,),
        )
        widths = (2, 1, 2, 2)
        targets = tuple((0,) * width for width in widths)

        with self.assertRaises(ZeroDivisionError):
            xor_accumulate_capacity_aware_eea_transition(
                valid[0],
                (0, 0),
                *valid[2:],
                *targets,
            )
        for invalid_width in (0, MAX_EEA_R0_WIDTH + 1, True):
            with self.subTest(max_r0_width=invalid_width):
                with self.assertRaises((TypeError, ValueError)):
                    xor_accumulate_capacity_aware_eea_transition(
                        *valid,
                        *targets,
                        max_r0_width=invalid_width,
                    )

        invalid_calls = (
            ((valid[0],) * (MAX_EEA_R0_WIDTH + 1), *valid[1:]),
            (valid[0], (1,) * (MAX_EEA_R1_WIDTH + 1), *valid[2:]),
            (*valid[:2], (1,) * (MAX_EEA_S_COEFFICIENT_WIDTH + 1), *valid[3:]),
            (*valid[:4], (1,) * (MAX_EEA_T_COEFFICIENT_WIDTH + 1), valid[5]),
        )
        for inputs in invalid_calls:
            with self.subTest(input_widths=tuple(map(len, inputs))):
                with self.assertRaises(ValueError):
                    xor_accumulate_capacity_aware_eea_transition(
                        *inputs,
                        *targets,
                    )

        with self.assertRaises(ValueError):
            xor_accumulate_capacity_aware_eea_transition(
                *valid,
                (0,),
                *targets[1:],
            )

    def test_exhaustive_bounded_small_field_full_transitions(self) -> None:
        bezout_states = (
            ((0,), (0,), (0,), (0,)),
            ((1,), (0,), (0,), (1,)),
        )
        counts: dict[int, tuple[int, int]] = {}
        for degree, modulus in _SMALL_MODULI.items():
            field_size = 1 << degree
            pair_count = 0
            transition_count = 0
            for r0_value in range(field_size**2):
                r0 = (r0_value % field_size, r0_value // field_size)
                for r1_value in range(1, field_size**2):
                    r1 = (r1_value % field_size, r1_value // field_size)
                    pair_count += 1
                    for s0, s1, t0, t1 in bezout_states:
                        inputs = (r0, r1, s0, s1, t0, t1)
                        quotient, remainder, s2, t2 = _reference_transition(
                            inputs,
                            degree,
                            modulus,
                        )
                        widths = (
                            2,
                            1,
                            max(len(s0), 2 + len(s1) - 1),
                            max(len(t0), 2 + len(t1) - 1),
                        )
                        targets = tuple(
                            tuple(
                                (r0[0] ^ r1[0] ^ state_index) & (field_size - 1)
                                for _ in range(width)
                            )
                            for state_index, width in enumerate(widths)
                        )
                        add_operation = _small_add_operation

                        def multiply_operation(
                            left: tuple[int, ...],
                            right: tuple[int, ...],
                            target: tuple[int, ...],
                            *,
                            _degree: int = degree,
                            _modulus: int = modulus,
                        ) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
                            return _small_multiply_operation(
                                left,
                                right,
                                target,
                                _degree,
                                _modulus,
                            )

                        def division_operation(
                            dividend: tuple[int, ...],
                            divisor: tuple[int, ...],
                            quotient_target: tuple[int, ...],
                            remainder_target: tuple[int, ...],
                            *,
                            _degree: int = degree,
                            _modulus: int = modulus,
                        ) -> tuple[
                            tuple[int, ...],
                            tuple[int, ...],
                            tuple[int, ...],
                            tuple[int, ...],
                        ]:
                            return _small_division_operation(
                                dividend,
                                divisor,
                                quotient_target,
                                remainder_target,
                                _degree,
                                _modulus,
                            )

                        updated, scratch = _compute_accumulate_uncompute(
                            inputs,
                            targets,
                            division_operation,
                            add_operation,
                            multiply_operation,
                        )
                        expected_outputs = (quotient, remainder, s2, t2)
                        expected_targets = tuple(
                            tuple(
                                initial ^ value
                                for initial, value in zip(
                                    target,
                                    _pad(output, len(target)),
                                )
                            )
                            for target, output in zip(targets, expected_outputs)
                        )
                        self.assertEqual(updated, expected_targets)
                        self.assertFalse(
                            any(any(register) for _, register in scratch)
                        )
                        repeated, repeated_scratch = (
                            _compute_accumulate_uncompute(
                                inputs,
                                updated,
                                division_operation,
                                add_operation,
                                multiply_operation,
                            )
                        )
                        self.assertEqual(repeated, targets)
                        self.assertFalse(
                            any(
                                any(register)
                                for _, register in repeated_scratch
                            )
                        )
                        transition_count += 1

            expected_pairs = field_size**2 * (field_size**2 - 1)
            self.assertEqual(pair_count, expected_pairs)
            self.assertEqual(transition_count, pair_count * len(bezout_states))
            counts[degree] = pair_count, transition_count

        self.assertEqual(
            counts,
            {
                2: (240, 480),
                3: (4032, 8064),
                4: (65280, 130560),
            },
        )


if __name__ == "__main__":
    unittest.main()
