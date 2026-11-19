from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Iterable

from .models import MeasurementStatus, MetricProvenance, ResourceMetrics
from .records import ExperimentRecord
from .score import ScoreResult, calculate_official_score, calculate_score


class RankingBasis(str, Enum):
    OFFICIAL_VERIFIED = "OFFICIAL_VERIFIED"
    MEASURED_OFFICIAL_METRICS = "MEASURED_OFFICIAL_METRICS"
    ALL_SCORED_WITH_PROVENANCE = "ALL_SCORED_WITH_PROVENANCE"


class CandidateComparisonStatus(str, Enum):
    CONFIGURATION_INVALID = "CONFIGURATION_INVALID"
    DUPLICATE_CONFIGURATION = "DUPLICATE_CONFIGURATION"
    BACKEND_FAILURE = "BACKEND_FAILURE"
    COMPILATION_UNAVAILABLE = "COMPILATION_UNAVAILABLE"
    CIRCUIT_METADATA_UNAVAILABLE = "CIRCUIT_METADATA_UNAVAILABLE"
    INCOMPLETE_MEASUREMENTS = "INCOMPLETE_MEASUREMENTS"
    VERIFICATION_UNAVAILABLE = "VERIFICATION_UNAVAILABLE"
    OFFICIAL_VERIFICATION_REJECTED = "OFFICIAL_VERIFICATION_REJECTED"
    RESULT_UNKNOWN = "RESULT_UNKNOWN"
    ESTIMATED = "ESTIMATED"
    MEASURED_UNVERIFIED = "MEASURED_UNVERIFIED"
    OFFICIALLY_VERIFIED = "OFFICIALLY_VERIFIED"
    RUN_SUMMARY = "RUN_SUMMARY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ComparisonEntry:
    experiment_id: str
    candidate_id: str
    status: CandidateComparisonStatus
    ranking_basis: RankingBasis
    score_result: ScoreResult | None
    rank: int | None


def _record_status(
    record: ExperimentRecord,
) -> tuple[CandidateComparisonStatus, ScoreResult | None]:
    if record.record_type == "RUN_SUMMARY":
        return CandidateComparisonStatus.RUN_SUMMARY, None
    if record.backend_execution is None:
        return CandidateComparisonStatus.UNKNOWN, None

    execution_status = record.backend_execution.get("execution_status")
    if execution_status == "CONFIGURATION_INVALID":
        return CandidateComparisonStatus.CONFIGURATION_INVALID, None
    if execution_status == "DUPLICATE_CONFIGURATION":
        return CandidateComparisonStatus.DUPLICATE_CONFIGURATION, None
    if execution_status in ("BACKEND_UNAVAILABLE", "EXECUTION_FAILED"):
        return CandidateComparisonStatus.BACKEND_FAILURE, None
    if execution_status == "COMPILATION_UNAVAILABLE":
        return CandidateComparisonStatus.COMPILATION_UNAVAILABLE, None
    if execution_status == "CIRCUIT_METADATA_UNAVAILABLE":
        return CandidateComparisonStatus.CIRCUIT_METADATA_UNAVAILABLE, None
    if execution_status == "RESOURCE_METRICS_UNAVAILABLE":
        return CandidateComparisonStatus.INCOMPLETE_MEASUREMENTS, None
    if execution_status == "VERIFICATION_UNAVAILABLE":
        return CandidateComparisonStatus.VERIFICATION_UNAVAILABLE, None
    if execution_status == "OFFICIAL_VERIFICATION_REJECTED":
        return CandidateComparisonStatus.OFFICIAL_VERIFICATION_REJECTED, None
    if execution_status == "RESULT_UNKNOWN":
        return CandidateComparisonStatus.RESULT_UNKNOWN, None

    if record.resource_metrics is None:
        return CandidateComparisonStatus.INCOMPLETE_MEASUREMENTS, None
    try:
        metrics = ResourceMetrics.from_dict(record.resource_metrics)
    except (TypeError, ValueError):
        return CandidateComparisonStatus.INCOMPLETE_MEASUREMENTS, None
    if not metrics.is_complete or record.score_result is None:
        return CandidateComparisonStatus.INCOMPLETE_MEASUREMENTS, None

    try:
        if (
            metrics.provenance == MetricProvenance.OFFICIAL
            and metrics.measurement_status == MeasurementStatus.MEASURED
        ):
            calculated = calculate_official_score(metrics)
        elif metrics.provenance == MetricProvenance.ESTIMATE:
            calculated = calculate_score(metrics)
        else:
            return CandidateComparisonStatus.INCOMPLETE_MEASUREMENTS, None
    except ValueError:
        return CandidateComparisonStatus.INCOMPLETE_MEASUREMENTS, None

    if (
        record.score_result.provenance != calculated.provenance
        or not math.isclose(
            record.score_result.cost_c, calculated.cost_c, rel_tol=1e-14
        )
        or not math.isclose(
            record.score_result.score, calculated.score, rel_tol=1e-14
        )
    ):
        return CandidateComparisonStatus.INCOMPLETE_MEASUREMENTS, None

    if metrics.provenance == MetricProvenance.ESTIMATE:
        return CandidateComparisonStatus.ESTIMATED, calculated
    if (
        metrics.provenance == MetricProvenance.OFFICIAL
        and metrics.measurement_status == MeasurementStatus.MEASURED
        and record.is_officially_eligible
    ):
        return CandidateComparisonStatus.OFFICIALLY_VERIFIED, calculated
    if (
        metrics.provenance == MetricProvenance.OFFICIAL
        and metrics.measurement_status == MeasurementStatus.MEASURED
    ):
        return CandidateComparisonStatus.MEASURED_UNVERIFIED, calculated
    return CandidateComparisonStatus.INCOMPLETE_MEASUREMENTS, None


def _eligible_for_basis(
    status: CandidateComparisonStatus,
    record: ExperimentRecord,
    basis: RankingBasis,
) -> bool:
    if record.score_result is None:
        return False
    if basis == RankingBasis.OFFICIAL_VERIFIED:
        return status == CandidateComparisonStatus.OFFICIALLY_VERIFIED
    if basis == RankingBasis.MEASURED_OFFICIAL_METRICS:
        return status in (
            CandidateComparisonStatus.OFFICIALLY_VERIFIED,
            CandidateComparisonStatus.MEASURED_UNVERIFIED,
        )
    return status in (
        CandidateComparisonStatus.OFFICIALLY_VERIFIED,
        CandidateComparisonStatus.MEASURED_UNVERIFIED,
        CandidateComparisonStatus.ESTIMATED,
    )


def compare_candidates(
    records: Iterable[ExperimentRecord],
    *,
    ranking_basis: RankingBasis = RankingBasis.OFFICIAL_VERIFIED,
) -> tuple[ComparisonEntry, ...]:
    if not isinstance(ranking_basis, RankingBasis):
        ranking_basis = RankingBasis(ranking_basis)

    classified = [
        (record, *_record_status(record))
        for record in records
    ]
    ranked = [
        (index, record, status, score)
        for index, (record, status, score) in enumerate(classified)
        if _eligible_for_basis(status, record, ranking_basis)
    ]
    ranked.sort(
        key=lambda item: (
            item[3].score if item[3] is not None else float("inf"),
            item[0],
        )
    )
    rank_by_index = {index: rank for rank, (index, _, _, _) in enumerate(ranked, start=1)}

    return tuple(
        ComparisonEntry(
            experiment_id=record.experiment_id,
            candidate_id=record.candidate_id,
            status=status,
            ranking_basis=ranking_basis,
            score_result=score,
            rank=rank_by_index.get(index),
        )
        for index, (record, status, score) in enumerate(classified)
    )
