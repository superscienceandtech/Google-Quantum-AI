from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from invsqrt_opt.backend import (
    BackendOperation,
    BuiltCircuit,
    OperationStatus,
    UnavailableBackend,
)


def _set_mapping_value(mapping: Any, key: str, value: Any) -> None:
    mapping[key] = value
from invsqrt_opt.comparison import (
    CandidateComparisonStatus,
    RankingBasis,
    compare_candidates,
)
from invsqrt_opt.configurations import CandidateConfiguration
from invsqrt_opt.contract import CircuitContract, CircuitValidationLevel
from invsqrt_opt.execution import ExecutionLifecycle, ExecutionStatus
from invsqrt_opt.models import (
    CandidateState,
    MeasurementStatus,
    MetricProvenance,
    ResourceMetrics,
    VerificationStatus,
)
from invsqrt_opt.records import ExperimentRecord, ExperimentStore
from invsqrt_opt.runner import ExperimentRunner
from invsqrt_opt.score import calculate_official_score
from invsqrt_opt.search_space import (
    ParameterDefinition,
    ParameterKind,
    SearchSpace,
)
from invsqrt_opt.strategies import (
    GenerationBatch,
    GridSearch,
    RandomSearch,
)


def example_space() -> SearchSpace:
    return SearchSpace(
        (
            ParameterDefinition(
                "degree", ParameterKind.INTEGER, minimum=0, maximum=4, step=2
            ),
            ParameterDefinition(
                "ratio", ParameterKind.FLOAT, minimum=0.1, maximum=0.3, step=0.1
            ),
            ParameterDefinition(
                "mode",
                ParameterKind.CATEGORICAL,
                choices=("fast", "small"),
            ),
            ParameterDefinition(
                "enabled", ParameterKind.FIXED, fixed_value=True
            ),
        )
    )


def run_arguments(**overrides):
    values = {
        "git_commit": "test-commit",
        "software_version": "test-version",
        "dependency_metadata": {"python": "test-runtime"},
        "run_id": "test-run",
    }
    values.update(overrides)
    return values


def test_search_space_serialization_and_stable_identity():
    space = example_space()
    restored = SearchSpace.from_dict(space.to_dict())
    assert restored == space
    assert restored.search_space_id == space.search_space_id
    assert space.finite_configuration_count == 18


@pytest.mark.parametrize(
    "definition",
    [
        ParameterDefinition(
            "integer", ParameterKind.INTEGER, minimum=1, maximum=4, step=1
        ),
    ],
)
def test_valid_integer_parameter(definition):
    space = SearchSpace((definition,))
    assert space.validate({"integer": 3}) == {"integer": 3}


def test_valid_float_categorical_and_fixed_parameters():
    space = example_space()
    result = space.validate(
        {"degree": 2, "ratio": 0.2, "mode": "small", "enabled": True}
    )
    assert result == {
        "degree": 2,
        "ratio": 0.2,
        "mode": "small",
        "enabled": True,
    }


def test_invalid_parameter_definitions_rejected():
    with pytest.raises(ValueError):
        ParameterDefinition("x", ParameterKind.INTEGER, minimum=5, maximum=1, step=1)
    with pytest.raises(ValueError):
        ParameterDefinition("x", ParameterKind.INTEGER, minimum=0, maximum=2, step=True)
    with pytest.raises(ValueError):
        ParameterDefinition("x", ParameterKind.FLOAT, minimum=0.0, maximum=1.0, step=0.0)
    with pytest.raises(ValueError):
        ParameterDefinition("x", ParameterKind.CATEGORICAL, choices=())
    with pytest.raises(ValueError):
        ParameterDefinition("x", ParameterKind.CATEGORICAL, choices=("same", "same"))


def test_search_space_rejects_duplicate_names_and_invalid_values():
    duplicate = ParameterDefinition(
        "x", ParameterKind.INTEGER, minimum=0, maximum=1, step=1
    )
    with pytest.raises(ValueError):
        SearchSpace((duplicate, duplicate))
    space = SearchSpace((duplicate,))
    for values in (
        {"x": True},
        {"x": 2},
        {"x": 0.5},
        {"x": 0, "unknown": 1},
        {},
    ):
        with pytest.raises(ValueError):
            space.validate(values)


def test_candidate_configuration_fingerprint_and_immutability():
    space = example_space()
    params = {"degree": 2, "ratio": 0.2, "mode": "small", "enabled": True}
    one = CandidateConfiguration.create(
        params,
        space,
        "strategy-v1",
        seed=7,
        created_at="2026-01-01T00:00:00+00:00",
    )
    two = CandidateConfiguration.create(
        params,
        space,
        "strategy-v1",
        seed=7,
        created_at="2026-01-02T00:00:00+00:00",
        creation_metadata={"host": "test"},
    )
    changed = CandidateConfiguration.create(
        {**params, "degree": 4},
        space,
        "strategy-v1",
        seed=7,
        created_at="2026-01-01T00:00:00+00:00",
    )
    assert one.configuration_id == two.configuration_id
    assert one.fingerprint == two.fingerprint
    assert changed.fingerprint != one.fingerprint
    assert CandidateConfiguration.from_json(one.to_json()) == one
    one.validate_against(space)
    with pytest.raises(TypeError):
        _set_mapping_value(one.parameters, "degree", 4)
    with pytest.raises(ValueError):
        CandidateConfiguration(
            **{
                **one.to_dict(),
                "fingerprint": "0" * 64,
                "configuration_id": "candidate-config:" + "0" * 64,
            }
        )


def test_grid_search_order_limit_and_invalid_limits():
    one = GridSearch().generate(example_space(), benchmark_id="INVSQRT")
    two = GridSearch().generate(example_space(), benchmark_id="INVSQRT")
    assert [c.fingerprint for c in one.configurations] == [
        c.fingerprint for c in two.configurations
    ]
    assert one.requested_count == 18
    assert one.generated_count == 18
    assert len({c.fingerprint for c in one.configurations}) == 18

    limited = GridSearch().generate(
        example_space(), benchmark_id="INVSQRT", max_configurations=3
    )
    assert limited.generated_count == 3
    assert limited.limit_applied is True
    assert limited.requested_count == 18
    assert [c.parameters["degree"] for c in limited.configurations] == [0, 0, 0]
    with pytest.raises(ValueError):
        GridSearch().generate(
            example_space(), benchmark_id="INVSQRT", max_configurations=0
        )
    continuous = SearchSpace(
        (
            ParameterDefinition(
                "x", ParameterKind.FLOAT, minimum=0.0, maximum=1.0
            ),
        )
    )
    with pytest.raises(ValueError):
        GridSearch().generate(continuous, benchmark_id="INVSQRT")


def test_random_search_is_seeded_unique_and_reports_counts():
    strategy = RandomSearch()
    first = strategy.generate(
        example_space(), benchmark_id="INVSQRT", seed=102, sample_count=10
    )
    same = strategy.generate(
        example_space(), benchmark_id="INVSQRT", seed=102, sample_count=10
    )
    other = strategy.generate(
        example_space(), benchmark_id="INVSQRT", seed=103, sample_count=10
    )
    assert [c.fingerprint for c in first.configurations] == [
        c.fingerprint for c in same.configurations
    ]
    assert [c.fingerprint for c in first.configurations] != [
        c.fingerprint for c in other.configurations
    ]
    assert first.generated_count == first.requested_count == 10
    assert len({c.fingerprint for c in first.configurations}) == 10
    for config in first.configurations:
        config.validate_against(example_space())

    single = SearchSpace(
        (ParameterDefinition("fixed", ParameterKind.FIXED, fixed_value="only"),)
    )
    exhausted = strategy.generate(
        single, benchmark_id="INVSQRT", seed=0, sample_count=5
    )
    assert exhausted.requested_count == 5
    assert exhausted.generated_count == 1
    assert exhausted.space_exhausted is True
    with pytest.raises(ValueError):
        strategy.generate(single, benchmark_id="INVSQRT", sample_count=2)
    with pytest.raises(ValueError):
        strategy.generate(single, benchmark_id="INVSQRT", seed=0, sample_count=0)


def test_unavailable_backend_fails_closed_and_persists(tmp_path):
    space = SearchSpace(
        (ParameterDefinition("n", ParameterKind.INTEGER, 0, 1, 1),)
    )
    store = ExperimentStore(tmp_path / "experiments.jsonl")
    summary = ExperimentRunner(UnavailableBackend(), store).run(
        space,
        GridSearch(),
        **run_arguments(max_experiments=1),
    )
    assert summary.interrupted is False
    assert summary.generation.limit_applied is True
    assert len(summary.outcomes) == 1
    outcome = summary.outcomes[0]
    assert outcome.execution_status == ExecutionStatus.BACKEND_UNAVAILABLE
    assert outcome.backend_result.resource_metrics is None
    assert outcome.experiment_record.score_result is None
    assert outcome.experiment_record.candidate_state == CandidateState.CREATED
    records = store.load()
    assert len(records) == 2
    assert records[0].resource_metrics is None
    assert records[1].record_type == "RUN_SUMMARY"
    summary_record = records[1].backend_execution
    assert summary_record is not None
    assert summary_record["interrupted"] is False


def test_explicit_verification_request_stays_unavailable_without_verifier(tmp_path):
    space = SearchSpace(
        (ParameterDefinition("n", ParameterKind.INTEGER, 1, 1, 1),)
    )
    store = ExperimentStore(tmp_path / "experiments.jsonl")
    summary = ExperimentRunner(TestDoubleBackend(), store).run(
        space,
        GridSearch(),
        **run_arguments(
            run_id="verify-unavailable",
            max_experiments=1,
            authorization_reference="test-only-authorization",
        ),
    )
    outcome = summary.outcomes[0]
    assert outcome.execution_status == ExecutionStatus.VERIFICATION_UNAVAILABLE
    assert outcome.experiment_record.candidate_state == CandidateState.CREATED
    result = outcome.experiment_record.verification_result
    assert result is not None
    assert result["verification_status"] == "VERIFIER_UNAVAILABLE"
    assert result["execution_status"] == "NOT_STARTED"


class TestDoubleBackend:
    """Unit-test-only backend; resource values are labeled estimates."""

    __test__ = False
    backend_id = "TEST_DOUBLE_BACKEND"
    backend_version = "unit-test"

    @property
    def available(self):
        return True

    def validate_configuration(self, configuration, search_space):
        if configuration.parameters["n"] == 0:
            return BackendOperation(
                OperationStatus.FAILED,
                error="test double injected a candidate-specific failure",
            )
        return BackendOperation(OperationStatus.SUCCEEDED)

    def construct_circuit(self, configuration):
        contract = CircuitContract(
            candidate_id=configuration.configuration_id,
            circuit_artifact="test-double://not-a-real-circuit",
            register_names=("x",),
            register_widths={"x": 22},
            distinct_qubit_ids={"x": tuple(range(22))},
            total_qubit_count=22,
            input_register_restored=True,
            scratch_registers_restored=True,
            validation_level=CircuitValidationLevel.UNKNOWN,
        )
        return BackendOperation(
            OperationStatus.SUCCEEDED,
            value=BuiltCircuit(
                "test-double://not-a-real-circuit",
                circuit=object(),
                metadata=contract,
            ),
        )

    def measure_resources(self, configuration, circuit):
        return BackendOperation(
            OperationStatus.SUCCEEDED,
            value=ResourceMetrics(
                qubit_count=2,
                toffoli_like_count=3.0,
                base_t_count=1.0,
                rotation_fallback_t_contribution=0.0,
                provenance=MetricProvenance.ESTIMATE,
                measurement_status=MeasurementStatus.ESTIMATED,
            ),
            evidence_references=("test-double:estimate",),
        )

    def compile_circuit(self, configuration, circuit):
        return BackendOperation(OperationStatus.SUCCEEDED)


class NoMetricsBackend(TestDoubleBackend):
    __test__ = False

    def measure_resources(self, configuration, circuit):
        return BackendOperation(
            OperationStatus.UNAVAILABLE,
            error="test double has no resource measurement",
        )


class NoMetadataBackend(TestDoubleBackend):
    __test__ = False

    def construct_circuit(self, configuration):
        return BackendOperation(
            OperationStatus.SUCCEEDED,
            value=BuiltCircuit(
                "test-double://metadata-unavailable",
                circuit=object(),
                metadata=None,
            ),
        )


class OverflowMetricsBackend(TestDoubleBackend):
    __test__ = False

    def measure_resources(self, configuration, circuit):
        return BackendOperation(
            OperationStatus.SUCCEEDED,
            value=ResourceMetrics(
                qubit_count=2,
                toffoli_like_count=1e308,
                base_t_count=1e308,
                rotation_fallback_t_contribution=1e308,
                provenance=MetricProvenance.ESTIMATE,
                measurement_status=MeasurementStatus.ESTIMATED,
            ),
        )


def test_missing_metrics_and_metadata_are_explicit(tmp_path):
    space = SearchSpace(
        (ParameterDefinition("n", ParameterKind.FIXED, fixed_value=1),)
    )
    missing_metrics = ExperimentRunner(
        NoMetricsBackend(), ExperimentStore(tmp_path / "metrics.jsonl")
    ).run(
        space,
        GridSearch(),
        **run_arguments(run_id="missing-metrics"),
    )
    assert missing_metrics.outcomes[0].execution_status == (
        ExecutionStatus.RESOURCE_METRICS_UNAVAILABLE
    )

    missing_metadata = ExperimentRunner(
        NoMetadataBackend(), ExperimentStore(tmp_path / "metadata.jsonl")
    ).run(
        space,
        GridSearch(),
        **run_arguments(run_id="missing-metadata"),
    )
    assert missing_metadata.outcomes[0].execution_status == (
        ExecutionStatus.CIRCUIT_METADATA_UNAVAILABLE
    )

    overflow = ExperimentRunner(
        OverflowMetricsBackend(), ExperimentStore(tmp_path / "overflow.jsonl")
    ).run(
        space,
        GridSearch(),
        **run_arguments(run_id="overflow-metrics"),
    )
    assert overflow.outcomes[0].execution_status == ExecutionStatus.EXECUTION_FAILED
    assert overflow.outcomes[0].experiment_record.score_result is None


def test_runner_isolates_failures_and_saves_estimates(tmp_path):
    space = SearchSpace(
        (ParameterDefinition("n", ParameterKind.INTEGER, 0, 1, 1),)
    )
    store = ExperimentStore(tmp_path / "experiments.jsonl")
    summary = ExperimentRunner(TestDoubleBackend(), store).run(
        space,
        GridSearch(),
        **run_arguments(max_experiments=2, run_id="isolation-run"),
    )
    assert [outcome.execution_status for outcome in summary.outcomes] == [
        ExecutionStatus.EXECUTION_FAILED,
        ExecutionStatus.EXECUTION_SUCCEEDED,
    ]
    estimate = summary.outcomes[1].experiment_record.score_result
    assert estimate is not None
    assert estimate.provenance == MetricProvenance.ESTIMATE
    assert summary.outcomes[1].experiment_record.candidate_state == CandidateState.CREATED
    entries = compare_candidates(
        store.load(), ranking_basis=RankingBasis.ALL_SCORED_WITH_PROVENANCE
    )
    candidate_entries = [
        entry for entry in entries if entry.status != CandidateComparisonStatus.RUN_SUMMARY
    ]
    assert [entry.status for entry in candidate_entries] == [
        CandidateComparisonStatus.BACKEND_FAILURE,
        CandidateComparisonStatus.ESTIMATED,
    ]
    assert candidate_entries[0].rank is None
    assert candidate_entries[1].rank == 1
    assert compare_candidates(
        store.load(), ranking_basis=RankingBasis.OFFICIAL_VERIFIED
    )[1].rank is None


class DuplicateStrategy:
    strategy_id = "duplicate-test-strategy"
    version = "1"

    def generate(
        self,
        search_space,
        *,
        benchmark_id,
        seed=None,
        max_configurations=None,
        sample_count=None,
    ):
        config = CandidateConfiguration.create(
            {"n": 0}, search_space, self.strategy_id, seed=seed, benchmark_id=benchmark_id
        )
        return GenerationBatch(
            strategy_id=self.strategy_id,
            seed=seed,
            configurations=(config, config),
            requested_count=2,
            generated_count=2,
            total_possible=1,
            limit_applied=False,
            space_exhausted=True,
        )


class InvalidConfigurationStrategy:
    strategy_id = "invalid-test-strategy"
    version = "1"

    def generate(
        self,
        search_space,
        *,
        benchmark_id,
        seed=None,
        max_configurations=None,
        sample_count=None,
    ):
        other_space = SearchSpace(
            (ParameterDefinition("n", ParameterKind.INTEGER, 1, 2, 1),)
        )
        configuration = CandidateConfiguration.create(
            {"n": 1},
            other_space,
            self.strategy_id,
            seed=seed,
            benchmark_id=benchmark_id,
        )
        return GenerationBatch(
            strategy_id=self.strategy_id,
            seed=seed,
            configurations=(configuration,),
            requested_count=1,
            generated_count=1,
            total_possible=1,
            limit_applied=False,
            space_exhausted=True,
        )


def test_runner_rejects_configuration_from_wrong_search_space(tmp_path):
    space = SearchSpace(
        (ParameterDefinition("n", ParameterKind.INTEGER, 0, 1, 1),)
    )
    summary = ExperimentRunner(
        UnavailableBackend(), ExperimentStore(tmp_path / "invalid.jsonl")
    ).run(
        space,
        InvalidConfigurationStrategy(),
        **run_arguments(run_id="invalid-config"),
    )
    assert summary.outcomes[0].execution_status == (
        ExecutionStatus.CONFIGURATION_INVALID
    )


def test_runner_duplicate_handling_and_duplicate_experiment_ids(tmp_path):
    space = SearchSpace(
        (ParameterDefinition("n", ParameterKind.FIXED, fixed_value=0),)
    )
    store = ExperimentStore(tmp_path / "experiments.jsonl")
    runner = ExperimentRunner(UnavailableBackend(), store)
    first = runner.run(
        space, DuplicateStrategy(), **run_arguments(run_id="duplicate-run")
    )
    assert first.outcomes[1].execution_status == ExecutionStatus.DUPLICATE_CONFIGURATION
    duplicate_id = runner.run(
        space, DuplicateStrategy(), **run_arguments(run_id="duplicate-run")
    )
    assert duplicate_id.outcomes[0].persistence_error is not None
    assert duplicate_id.summary_persistence_error is not None
    assert len(store.load()) == 3


class InterruptingBackend(UnavailableBackend):
    backend_id = "TEST_INTERRUPT_BACKEND"
    backend_version = "unit-test"

    @property
    def available(self):
        return True

    def validate_configuration(self, configuration, search_space):
        raise KeyboardInterrupt


def test_interrupted_run_is_persisted(tmp_path):
    space = SearchSpace(
        (ParameterDefinition("n", ParameterKind.FIXED, fixed_value=0),)
    )
    store = ExperimentStore(tmp_path / "experiments.jsonl")
    summary = ExperimentRunner(InterruptingBackend(), store).run(
        space, GridSearch(), **run_arguments(run_id="interrupted-run")
    )
    assert summary.interrupted is True
    records = store.load()
    assert len(records) == 1
    assert records[0].record_type == "RUN_SUMMARY"
    backend_summary = records[0].backend_execution
    assert backend_summary is not None
    assert backend_summary["interrupted"] is True


def test_execution_lifecycle_rejects_invalid_transitions():
    lifecycle = ExecutionLifecycle()
    with pytest.raises(ValueError):
        lifecycle.transition(ExecutionStatus.OFFICIAL_VERIFICATION_PASSED)
    lifecycle.transition(ExecutionStatus.CONFIGURATION_VALID)
    lifecycle.transition(ExecutionStatus.EXECUTION_PENDING)
    lifecycle.transition(ExecutionStatus.EXECUTION_RUNNING)
    lifecycle.transition(ExecutionStatus.EXECUTION_SUCCEEDED)
    with pytest.raises(ValueError):
        lifecycle.transition(ExecutionStatus.OFFICIAL_VERIFICATION_PASSED)


def test_comparison_distinguishes_measured_unverified_from_official():
    metrics = ResourceMetrics(
        qubit_count=260,
        toffoli_like_count=7735.0,
        base_t_count=1.0,
        rotation_fallback_t_contribution=1009.372826388952,
        provenance=MetricProvenance.OFFICIAL,
        measurement_status=MeasurementStatus.MEASURED,
    )
    record = ExperimentRecord(
        experiment_id="measured-unverified",
        candidate_id="candidate",
        git_commit="test-commit",
        candidate_state=CandidateState.CREATED,
        verification_status=VerificationStatus.NOT_RUN,
        score_result=calculate_official_score(metrics),
        resource_metrics=metrics.to_dict(),
        backend_execution={"execution_status": "EXECUTION_SUCCEEDED"},
    )
    official_basis = compare_candidates(
        [record], ranking_basis=RankingBasis.OFFICIAL_VERIFIED
    )[0]
    measured_basis = compare_candidates(
        [record], ranking_basis=RankingBasis.MEASURED_OFFICIAL_METRICS
    )[0]
    assert official_basis.status == CandidateComparisonStatus.MEASURED_UNVERIFIED
    assert official_basis.rank is None
    assert measured_basis.rank == 1


def test_comparison_rejects_inconsistent_persisted_score():
    metrics = ResourceMetrics(
        qubit_count=2,
        toffoli_like_count=3.0,
        base_t_count=1.0,
        rotation_fallback_t_contribution=0.0,
        provenance=MetricProvenance.ESTIMATE,
        measurement_status=MeasurementStatus.ESTIMATED,
    )
    record = ExperimentRecord(
        experiment_id="tampered-score",
        candidate_id="candidate",
        git_commit="test-commit",
        candidate_state=CandidateState.CREATED,
        verification_status=VerificationStatus.NOT_RUN,
        score_result=calculate_official_score(
            ResourceMetrics(
                qubit_count=260,
                toffoli_like_count=7735.0,
                base_t_count=1.0,
                rotation_fallback_t_contribution=1009.372826388952,
                provenance=MetricProvenance.OFFICIAL,
                measurement_status=MeasurementStatus.MEASURED,
            )
        ),
        resource_metrics=metrics.to_dict(),
        backend_execution={"execution_status": "EXECUTION_SUCCEEDED"},
    )
    result = compare_candidates(
        [record], ranking_basis=RankingBasis.ALL_SCORED_WITH_PROVENANCE
    )[0]
    assert result.status == CandidateComparisonStatus.INCOMPLETE_MEASUREMENTS
    assert result.rank is None


def test_store_reads_legacy_p002_record_shape(tmp_path):
    legacy = ExperimentRecord(
        experiment_id="legacy",
        candidate_id="candidate",
        git_commit="test-commit",
        candidate_state=CandidateState.CREATED,
        verification_status=VerificationStatus.NOT_RUN,
        score_result=None,
    ).to_dict()
    legacy.pop("record_type")
    path = tmp_path / "legacy.jsonl"
    import json

    path.write_text(json.dumps(legacy) + "\n", encoding="utf-8")
    loaded = ExperimentStore(path).load()
    assert len(loaded) == 1
    assert loaded[0].record_type == "CANDIDATE"


def test_experiment_store_rejects_protected_paths():
    repository_root = Path(__file__).resolve().parents[1]
    for protected in (
        repository_root / ".git" / "must-not-write.jsonl",
        repository_root / "external" / "must-not-write.jsonl",
        repository_root / "results" / "raw" / "must-not-write.jsonl",
    ):
        with pytest.raises(ValueError):
            ExperimentStore(protected)
