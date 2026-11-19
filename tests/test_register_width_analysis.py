from __future__ import annotations

import pytest
from invsqrt_opt.fixed_point import fixed_point_reference

from invsqrt_opt.register_width_analysis import (
    assess_width_opportunities,
    fixed_point_scaling,
    run_register_width_analysis,
    signed_representation_width,
    signed_width_evidence,
    unsigned_representation_width,
)


def test_unsigned_width_zero_and_positive_values():
    assert unsigned_representation_width(0) == 1
    assert unsigned_representation_width(1) == 1
    assert unsigned_representation_width(2) == 2
    assert unsigned_representation_width(127) == 7
    assert unsigned_representation_width(128) == 8
    assert unsigned_representation_width(255) == 8
    assert unsigned_representation_width(256) == 9


def test_unsigned_width_rejects_negative_and_non_integer():
    with pytest.raises(ValueError, match="negative"):
        unsigned_representation_width(-1)
    with pytest.raises(ValueError, match="integer"):
        unsigned_representation_width(1.0)
    with pytest.raises(ValueError, match="integer"):
        unsigned_representation_width(True)


@pytest.mark.parametrize(
    ("minimum", "maximum", "expected"),
    (
        (0, 0, 1),
        (0, 127, 8),
        (0, 128, 9),
        (1, 127, 8),
        (-128, -128, 8),
        (-127, -1, 8),
        (-128, 127, 8),
        (-129, 128, 9),
    ),
)
def test_signed_width_handles_positive_negative_and_crossing_ranges(
    minimum, maximum, expected
):
    evidence = signed_width_evidence(minimum, maximum)
    assert signed_representation_width(minimum, maximum) == expected
    assert evidence.verify_endpoints(minimum, maximum)
    assert evidence.representable_minimum <= minimum
    assert maximum <= evidence.representable_maximum


@pytest.mark.parametrize(
    ("minimum", "maximum"),
    (
        (2, 1),
        (True, 1),
        (1, False),
        (1.5, 2),
    ),
)
def test_signed_width_rejects_invalid_ranges(minimum, maximum):
    with pytest.raises(ValueError):
        signed_representation_width(minimum, maximum)


def test_fixed_point_scaling_metadata_is_explicit():
    plain = fixed_point_scaling(None)
    coefficient = fixed_point_scaling(17)
    result = fixed_point_scaling(40)

    assert plain.fractional_bits is None
    assert plain.scale_factor is None
    assert coefficient.fractional_bits == 17
    assert coefficient.scale_factor == 1 << 17
    assert result.fractional_bits == 40
    assert result.scale_factor == 1 << 40
    with pytest.raises(ValueError):
        fixed_point_scaling(-1)
    with pytest.raises(ValueError):
        fixed_point_scaling(True)


def test_intermediate_inventory_full_subrange_and_serialization():
    result = run_register_width_analysis(1, 4096)
    payload = result.to_dict()

    assert result.minimum_input == 1
    assert result.maximum_input == 4096
    assert result.inputs_evaluated == 4096
    assert result.mismatches == 0
    assert result.repeated_run_identical is None
    assert len(result.entries) == 16
    assert payload["entries"]

    entries = {entry.intermediate_id: entry for entry in result.entries}
    assert set(entries) == {
        "input",
        "shift_pairs",
        "normalized",
        "interval_case",
        "coefficient_c0",
        "coefficient_c1",
        "coefficient_c2",
        "coefficient_c3",
        "horner_r1",
        "horner_r2",
        "horner_r3",
        "square",
        "mantissa_product",
        "newton_correction",
        "newton_result_before_denormalization",
        "phase_numerator",
    }

    for entry in result.entries:
        assert entry.minimum_observed >= 0
        assert entry.minimum_observed <= entry.maximum_observed
        assert entry.minimum_unsigned_width >= 1
        assert unsigned_representation_width(entry.maximum_observed) == (
            entry.minimum_unsigned_width
        )
        evidence = signed_width_evidence(
            entry.minimum_observed,
            entry.maximum_observed,
        )
        assert evidence.verify_endpoints(
            entry.minimum_observed,
            entry.maximum_observed,
        )
        assert entry.evidence_classification == "EXHAUSTIVELY_OBSERVED"
        assert entry.circuit_mapping_status == "UNMAPPED"


def test_full_domain_inventory_is_reproducible_and_partition_consistent():
    first = run_register_width_analysis(1, 4096)
    second = run_register_width_analysis(1, 4096)

    assert first.inputs_evaluated == 4096
    assert second.inputs_evaluated == 4096
    assert first.mismatches == 0
    assert second.mismatches == 0
    assert tuple(entry.to_dict() for entry in first.entries) == tuple(
        entry.to_dict() for entry in second.entries
    )

    for entry in first.entries:
        assert len(entry.partition_extrema) <= 4
        assert all(
            0 <= partition.interval_case <= 3
            for partition in entry.partition_extrema
        )
        assert all(
            partition.minimum <= partition.maximum
            for partition in entry.partition_extrema
        )


def test_known_p011_p016_extrema_are_regressed():
    result = run_register_width_analysis(1, 4096)
    entries = {entry.intermediate_id: entry for entry in result.entries}
    direct = {}
    for input_value in range(1, 4097):
        fixed = fixed_point_reference(input_value)
        values = {
            "normalized": fixed.normalized_register,
            "coefficient_c0": fixed.coefficient_integers[0],
            "horner_r1": fixed.horner_registers[0],
            "square": fixed.square_register,
            "mantissa_product": fixed.product_register,
            "newton_correction": (
                (3 << 28) - fixed.product_register
            ),
            "phase_numerator": fixed.result_register,
        }
        for name, value in values.items():
            previous = direct.setdefault(
                name,
                [value, value, input_value, input_value],
            )
            if value < previous[0]:
                previous[0] = value
                previous[2] = input_value
            if value > previous[1]:
                previous[1] = value
                previous[3] = input_value

    for name in direct:
        entry = entries[name]
        minimum, maximum, minimum_at, maximum_at = direct[name]
        assert entry.minimum_observed == minimum
        assert entry.maximum_observed == maximum
        assert entry.minimum_at == minimum_at
        assert entry.maximum_at == maximum_at


def test_invalid_analysis_bounds_are_rejected():
    with pytest.raises(ValueError):
        run_register_width_analysis(0, 1)
    with pytest.raises(ValueError):
        run_register_width_analysis(1, 3_133_453)
    with pytest.raises(ValueError):
        run_register_width_analysis(3, 2)


def test_width_opportunities_never_claim_circuit_savings():
    result = run_register_width_analysis(1, 4096)
    opportunities = assess_width_opportunities(result)

    assert len(opportunities) == 16
    for opportunity in opportunities:
        assert opportunity.decision in {
            "SUPPORTED_FOR_CIRCUIT_EXPERIMENT",
            "REQUIRES_SEMANTIC_PROOF",
            "REQUIRES_CANONICAL_CIRCUIT_MAPPING",
            "NO_WIDTH_REDUCTION_IDENTIFIED",
            "REJECTED",
            "INCONCLUSIVE",
        }
        assert opportunity.decision != "SUPPORTED_FOR_CIRCUIT_EXPERIMENT"
