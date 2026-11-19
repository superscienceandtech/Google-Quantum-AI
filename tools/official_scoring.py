"""Local implementation of the published global geometric-mean aggregation."""

from __future__ import annotations

import math
from typing import Sequence


def global_geometric_mean_speedup(
    baseline_costs: Sequence[int | float], costs: Sequence[int | float]
) -> float:
    """Return exp(mean(log(baseline_cost / cost))) for positive finite inputs.

    This computes only the metric notebook's global aggregation formula. It
    does not implement its row matching, verifier calls, or benchmark costs.
    """
    if len(baseline_costs) != len(costs):
        raise ValueError("baseline and submission costs must have equal lengths")
    if not baseline_costs:
        raise ValueError("at least one benchmark cost is required")

    log_ratios = []
    for index, (baseline, cost) in enumerate(zip(baseline_costs, costs)):
        if type(baseline) not in (int, float) or type(cost) not in (int, float):
            raise ValueError(f"cost pair {index} must contain numeric values")
        if baseline <= 0 or cost <= 0:
            raise ValueError(f"cost pair {index} must contain positive values")
        try:
            baseline_log = math.log(baseline)
            cost_log = math.log(cost)
        except (OverflowError, ValueError) as error:
            raise ValueError(f"cost pair {index} is not finite and positive") from error
        if not math.isfinite(baseline_log) or not math.isfinite(cost_log):
            raise ValueError(f"cost pair {index} is not finite and positive")
        log_ratios.append(baseline_log - cost_log)

    try:
        score = math.exp(math.fsum(log_ratios) / len(log_ratios))
    except OverflowError as error:
        raise ValueError("global geometric-mean score exceeds finite float range") from error
    if score == 0.0:
        raise ValueError("global geometric-mean score is below finite float range")
    return score
