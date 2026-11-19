from __future__ import annotations

from dataclasses import dataclass
import math

from .models import MetricProvenance, ResourceMetrics


@dataclass(frozen=True)
class ScoreResult:
    cost_c: float
    score: float
    provenance: MetricProvenance


def calculate_score(metrics: ResourceMetrics) -> ScoreResult:
    if not metrics.is_complete:
        raise ValueError("Cannot calculate score from incomplete resource metrics")
    if metrics.provenance not in (
        MetricProvenance.OFFICIAL,
        MetricProvenance.ESTIMATE,
    ):
        raise ValueError(
            "Metric provenance must be OFFICIAL or ESTIMATE before score calculation"
        )

    assert metrics.qubit_count is not None
    assert metrics.toffoli_like_count is not None
    assert metrics.total_t_equivalent_contribution is not None

    cost_c = (
        metrics.toffoli_like_count
        + metrics.total_t_equivalent_contribution / 4.0
    )
    score = float(metrics.qubit_count) * cost_c
    if not math.isfinite(cost_c) or not math.isfinite(score):
        raise ValueError("Calculated resource cost and score must be finite")
    return ScoreResult(
        cost_c=cost_c,
        score=score,
        provenance=metrics.provenance,
    )


def calculate_official_score(metrics: ResourceMetrics) -> ScoreResult:
    if metrics.provenance != MetricProvenance.OFFICIAL:
        raise ValueError("Official score requires OFFICIAL metric provenance")
    if metrics.measurement_status.value != "MEASURED":
        raise ValueError("Official score requires measured resource metrics")
    return calculate_score(metrics)
