from __future__ import annotations

import math

import pytest

from invsqrt_opt.models import (
    Candidate,
    CandidateState,
    ExperimentConfig,
    ExperimentStatus,
    MeasurementStatus,
    MetricProvenance,
    ResourceMetrics,
    VerificationStatus,
)
from invsqrt_opt.records import ExperimentRecord, ExperimentStore
from invsqrt_opt.score import calculate_official_score, calculate_score


def historical_metrics() -> ResourceMetrics:
    return ResourceMetrics(
        qubit_count=260,
        toffoli_like_count=7735.0,
        base_t_count=1.0,
        rotation_fallback_t_contribution=1009.372826388952,
        provenance=MetricProvenance.OFFICIAL,
        measurement_status=MeasurementStatus.MEASURED,
    )


def experiment_config(**overrides):
    values = {
        "experiment_id": "exp-sonjoy-001",
        "candidate_id": "candidate-001",
        "strategy_name": "foundation",
        "parameter_configuration": {"degree": 10},
        "random_seed": 2026,
        "software_version": "0.1.0",
        "dependency_metadata": {"python": "3.14"},
        "git_commit": "5391b2e7123484efacffc0588f5e761e67b5cb55",
        "creation_timestamp": "2026-11-19T18:29:23+06:00",
        "execution_status": ExperimentStatus.CREATED,
        "evidence_references": ("none-yet",),
    }
    values.update(overrides)
    return ExperimentConfig(**values)


def test_historical_reference_score_regression():
    result = calculate_official_score(historical_metrics())
    assert math.isclose(result.cost_c, 7987.593206597238, rel_tol=1e-15)
    assert math.isclose(result.score, 2076774.233715282, rel_tol=1e-15)


def test_missing_and_invalid_metrics_rejected():
    missing = ResourceMetrics(None, None, None, None)
    with pytest.raises(ValueError):
        calculate_official_score(missing)
    with pytest.raises(ValueError):
        ResourceMetrics(-1, 1, 1, 1)
    with pytest.raises(ValueError):
        ResourceMetrics(1, math.inf, 1, 1)


def test_score_rejects_non_finite_derived_cost():
    metrics = ResourceMetrics(
        qubit_count=2,
        toffoli_like_count=1e308,
        base_t_count=1e308,
        rotation_fallback_t_contribution=1e308,
        provenance=MetricProvenance.ESTIMATE,
        measurement_status=MeasurementStatus.ESTIMATED,
    )
    with pytest.raises(ValueError):
        calculate_score(metrics)


def test_resource_metrics_complete_and_serializable():
    metrics = historical_metrics()
    data = metrics.to_dict()
    assert ResourceMetrics.from_dict(data) == metrics
    assert metrics.total_t_equivalent_contribution == pytest.approx(1010.372826388952)


def test_experiment_config_validation_and_serialization():
    config = experiment_config()
    assert ExperimentConfig.from_dict(config.to_dict()) == config
    with pytest.raises(ValueError):
        experiment_config(creation_timestamp="not-a-timestamp")


def test_candidate_validation_and_official_state_evidence():
    candidate = Candidate(
        candidate_id="candidate-001",
        candidate_version="v1",
        optimization_strategy="foundation",
        configuration={"degree": 10},
    )
    assert candidate.state == CandidateState.CREATED
    with pytest.raises(ValueError):
        Candidate(
            candidate_id="candidate-002",
            candidate_version="v1",
            optimization_strategy="foundation",
            configuration={},
            state=CandidateState.OFFICIAL_VERIFIER_VALIDATED,
            verification_status=VerificationStatus.PASSED,
        )


def test_candidate_serialization():
    candidate = Candidate(
        candidate_id="candidate-001",
        candidate_version="v1",
        optimization_strategy="foundation",
        configuration={"degree": 10},
        resource_metrics=historical_metrics(),
        evidence_references=("official-verifier:fixture",),
    )
    assert Candidate.from_dict(candidate.to_dict()) == candidate


def test_estimated_metrics_are_not_claimed_official():
    metrics = ResourceMetrics(
        qubit_count=260,
        toffoli_like_count=7735.0,
        base_t_count=1.0,
        rotation_fallback_t_contribution=1009.372826388952,
        provenance=MetricProvenance.ESTIMATE,
        measurement_status=MeasurementStatus.ESTIMATED,
    )
    estimate = calculate_score(metrics)
    assert estimate.provenance == MetricProvenance.ESTIMATE
    with pytest.raises(ValueError):
        calculate_official_score(metrics)


def test_invalid_official_metrics_rejected():
    with pytest.raises(ValueError):
        ResourceMetrics(
            qubit_count=260,
            toffoli_like_count=None,
            base_t_count=1.0,
            rotation_fallback_t_contribution=1009.372826388952,
            provenance=MetricProvenance.OFFICIAL,
            measurement_status=MeasurementStatus.MEASURED,
        )


def test_comparison_excludes_unverified_candidates(tmp_path):
    official_result = calculate_official_score(historical_metrics())
    official = ExperimentRecord(
        experiment_id="exp-1",
        candidate_id="candidate-official",
        git_commit="5391b2e7123484efacffc0588f5e761e67b5cb55",
        candidate_state=CandidateState.OFFICIAL_VERIFIER_VALIDATED,
        verification_status=VerificationStatus.PASSED,
        score_result=official_result,
        evidence_references=("official-verifier:run-1",),
        verification_result={
            "candidate_id": "candidate-official",
            "execution_status": "EXECUTED",
            "verification_status": "PASSED",
            "exit_code": 0,
            "verifier_source_checksum": "official-verifier-checksum",
            "provenance_complete": True,
            "evidence_references": ("official-verifier:run-1",),
        },
    )
    unverified = ExperimentRecord(
        experiment_id="exp-2",
        candidate_id="candidate-unverified",
        git_commit="5391b2e7123484efacffc0588f5e761e67b5cb55",
        candidate_state=CandidateState.BUILT,
        verification_status=VerificationStatus.NOT_RUN,
        score_result=official_result,
        evidence_references=(),
    )
    assert ExperimentStore.compare([unverified, official]) == [official]
    assert ExperimentStore.best([unverified, official]) == official

    store = ExperimentStore(tmp_path / "experiments.jsonl")
    store.append(official)
    store.append(unverified)
    loaded = store.load()
    assert len(loaded) == 2
    assert ExperimentRecord.from_dict(loaded[0].to_dict()) == loaded[0]
    with pytest.raises(ValueError):
        store.append(official)
