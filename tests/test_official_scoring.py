import math
import unittest

from tools.official_scoring import global_geometric_mean_speedup


class GlobalMetricAggregationTests(unittest.TestCase):
    def test_geometric_mean_aggregation_matches_formula(self):
        score = global_geometric_mean_speedup((10, 100), (5, 25))
        self.assertTrue(math.isclose(score, math.sqrt(8), rel_tol=1e-14))

    def test_one_benchmark_returns_its_speedup(self):
        self.assertEqual(global_geometric_mean_speedup((12,), (3,)), 4.0)

    def test_rejects_empty_mismatched_nonpositive_and_nonfinite_costs(self):
        cases = (
            ((), ()),
            ((10,), ()),
            ((0,), (1,)),
            ((1,), (-1,)),
            ((math.inf,), (1,)),
            ((1,), (math.nan,)),
            ((True,), (1,)),
            ((1,), (10**1000,)),
        )
        for baseline, costs in cases:
            with self.subTest(baseline=baseline, costs=costs):
                with self.assertRaises(ValueError):
                    global_geometric_mean_speedup(baseline, costs)


if __name__ == "__main__":
    unittest.main()
