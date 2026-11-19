from decimal import Decimal, localcontext
from fractions import Fraction

import pytest

from invsqrt_opt.contract import OFFICIAL_INVSQRT_SPEC
from invsqrt_opt.numerical_validation import (
    deterministic_sample_inputs,
    run_numerical_validation,
)
from invsqrt_opt.reference_math import (
    ALGORITHM_VERSION,
    DECIMAL_PRECISION,
    PAPER_VERSION,
    boundary_inputs,
    inverse_sqrt_oracle,
    paper_reference,
    phase_turns_oracle,
)


def test_normalization_matches_pair_shift_definition():
    assert paper_reference(3).leading_zero_pairs == 10
    assert paper_reference(3).normalized_input == Fraction(3)
    assert paper_reference(4).leading_zero_pairs == 9
    assert paper_reference(4).normalized_input == Fraction(1)
    assert paper_reference(3_133_452).leading_zero_pairs == 0
    assert paper_reference(3_133_452).normalized_input == Fraction(
        3_133_452, 1 << 20
    )


@pytest.mark.parametrize(
    ("value", "region", "argument", "scaled", "expected_initial"),
    [
        (1, "A", Fraction(1), False, "0.99994132489119882162"),
        (6, "B", Fraction(3, 2), False, "0.81648515205385221995"),
        (8, "A", Fraction(1), True, None),
        (12, "B", Fraction(3, 2), True, None),
    ],
)
def test_piecewise_polynomials_and_interval_boundaries(
    value, region, argument, scaled, expected_initial
):
    result = paper_reference(value)
    assert result.polynomial_region == region
    assert result.polynomial_argument == argument
    assert (result.polynomial_rescaling != 1) is scaled
    if expected_initial is not None:
        assert result.initial_estimate == Decimal(expected_initial)
    else:
        with localcontext() as context:
            context.prec = DECIMAL_PRECISION
            unscaled = (
                Decimal("0.99994132489119882162")
                if region == "A"
                else Decimal("0.81648515205385221995")
            )
            expected = unscaled * (
                Decimal(1) / Decimal(2).sqrt()
            )
        assert result.initial_estimate == expected


@pytest.mark.parametrize(
    ("value", "coefficients", "offset"),
    [
        (
            5,
            (
                "0.99994132489119882162",
                "0.49609891915903542303",
                "0.33261112772430493331",
                "0.14876762006038398086",
            ),
            Decimal(1),
        ),
        (
            7,
            (
                "0.81648515205385221995",
                "0.27136515484240234115",
                "0.12756148214815175348",
                "0.044753028579153842218",
            ),
            Decimal("1.5"),
        ),
    ],
)
def test_published_coefficients_match_direct_polynomial(value, coefficients, offset):
    result = paper_reference(value)
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        x = (
            Decimal(result.polynomial_argument.numerator)
            / Decimal(result.polynomial_argument.denominator)
        )
        a0, a1, a2, a3 = (Decimal(coefficient) for coefficient in coefficients)
        delta = x - offset
        expected = a0 - a1 * delta + a2 * delta**2 - a3 * delta**3
    assert result.initial_estimate == expected


def test_newton_step_and_final_denormalization_are_observable():
    result = paper_reference(5)
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        normalized = Decimal(result.normalized_input.numerator) / Decimal(
            result.normalized_input.denominator
        )
        independently_derived_correction = (
            result.initial_estimate
            * (Decimal(3) - normalized * result.initial_estimate**2)
            / Decimal(2)
        )
        expected_register_value = (
            independently_derived_correction
            * Decimal(2) ** result.leading_zero_pairs
        )
        expected_final = expected_register_value / Decimal(
            2
        ) ** OFFICIAL_INVSQRT_SPEC.np
    assert result.corrected_normalized_estimate == independently_derived_correction
    assert result.denormalized_register_estimate == expected_register_value
    assert result.final_estimate == expected_final


@pytest.mark.parametrize("value", [1, 2, 4, 6, 8, 12, 2_588_411, 3_133_452])
def test_independent_oracle_and_phase_relationship(value):
    reference = paper_reference(value)
    oracle = inverse_sqrt_oracle(value)
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        expected_oracle = Decimal(1) / Decimal(value).sqrt()
    assert oracle == expected_oracle
    assert phase_turns_oracle(value) == oracle
    assert reference.phase_turns_unwrapped == reference.final_estimate
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        expected_phase_modulo_one = (
            reference.phase_turns_unwrapped % Decimal(1)
        )
    assert reference.phase_turns_modulo_one == expected_phase_modulo_one


def test_paper_reported_worst_case_input_regression():
    value = 2_588_411
    first = paper_reference(value)
    second = paper_reference(value)
    oracle = inverse_sqrt_oracle(value)
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        relative_error = abs(first.final_estimate - oracle) / oracle
    assert first == second
    assert Decimal(0) < relative_error < Decimal("2.84e-8")


def test_domain_rejects_invalid_values_without_clipping():
    for value in (0, -1, 3_133_453, True, 1.0, "1"):
        with pytest.raises(ValueError):
            paper_reference(value)


def test_precision_must_be_explicitly_sufficient():
    with pytest.raises(ValueError):
        paper_reference(1, precision=31)
    with pytest.raises(ValueError):
        inverse_sqrt_oracle(1, precision=True)


def test_boundary_inputs_cover_normalization_and_polynomial_edges():
    inputs = set(boundary_inputs())
    assert {3, 4, 5, 5, 6, 7, 7, 8, 9, 11, 12, 13} <= inputs
    assert 2_588_411 not in inputs


def test_sampled_validation_records_classical_provenance_only():
    inputs = (1, 3, 4, 6, 8, 12, 2_588_411, 3_133_452)
    result = run_numerical_validation(
        inputs,
        validation_mode="SAMPLED_VALIDATION",
        sample_count_requested=8,
        sample_seed=1337,
    )
    assert result.algorithm_version == ALGORITHM_VERSION
    assert result.paper_version == PAPER_VERSION
    assert result.validation_mode == "SAMPLED_VALIDATION"
    assert result.evaluation_count == len(inputs)
    assert result.sample_count_requested == len(inputs)
    assert result.sample_seed == 1337
    assert result.decimal_precision == DECIMAL_PRECISION
    assert result.boundary_evaluation_count > 0
    assert result.quantum_verification == "NOT_PERFORMED"
    assert result.maximum_relative_error_input in inputs
    assert result.to_dict()["evaluation_count"] == len(inputs)
    assert "PAPER_REPORTED" in result.provenance_labels
    assert "HIGH_PRECISION_ORACLE" in result.provenance_labels
    assert "QUANTUM_VERIFICATION_NOT_PERFORMED" in result.provenance_labels
    assert not hasattr(result, "qubit_count")
    assert result.paper_reported_relative_error == "2.84E-8"
    assert result.paper_reported_error_input == 2_588_411
    with localcontext() as context:
        context.prec = DECIMAL_PRECISION
        paper_input_error = abs(
            paper_reference(2_588_411).final_estimate
            - inverse_sqrt_oracle(2_588_411)
        ) / inverse_sqrt_oracle(2_588_411)
    assert Decimal(result.measured_relative_error_at_paper_input) == paper_input_error
    assert result.absolute_difference_from_paper_report is not None


def test_uniform_sample_is_deterministic_and_includes_required_cases():
    first = deterministic_sample_inputs(sample_count=32, seed=7)
    second = deterministic_sample_inputs(sample_count=32, seed=7)
    assert first == second
    assert 1 in first
    assert 2_588_411 in first
    assert 3_133_452 in first


def test_exhaustive_mode_rejects_a_partial_domain():
    with pytest.raises(ValueError, match="complete official input-domain"):
        run_numerical_validation(
            range(1, 10), validation_mode="EXHAUSTIVE_VALIDATION"
        )
