"""Tests for the statistics helpers in vmgm/analysis.py.

Issue #11. ci, wilcoxon_p, holm and paired compute every CI and p-value in the paper.
Run from the repository root:

    python -m unittest discover -s vmgm/tests -t . -v
"""
import math
import random
import unittest

import numpy as np
import pandas as pd
from scipy import stats

from vmgm.analysis import ci, holm, paired, wilcoxon_p

try:
    from statsmodels.stats.multitest import multipletests
except ImportError:  # statsmodels is not in requirements.txt; that comparison is optional
    multipletests = None


def naive_holm(pvals):
    """Independent reference: Holm-Bonferroni written from the definition.
    Sort p ascending; the j-th smallest (j = 0..n-1) is multiplied by (n - j), capped at 1,
    then made non-decreasing along the sorted order; results returned in the original order."""
    n = len(pvals)
    order = sorted(range(n), key=lambda i: pvals[i])
    adj = [0.0] * n
    best = 0.0
    for j, i in enumerate(order):
        best = max(best, min(1.0, (n - j) * pvals[i]))
        adj[i] = best
    return adj


class TestHolm(unittest.TestCase):

    def test_holm_known_values(self):
        # sorted: 0.005*4 = 0.02, 0.01*3 = 0.03, 0.03*2 = 0.06, 0.04*1 = 0.04 -> raised to 0.06
        self.assertTrue(np.allclose(holm([0.01, 0.04, 0.03, 0.005]), [0.03, 0.06, 0.06, 0.02]))
        # sorted: 0.01*3 = 0.03, 0.02*2 = 0.04, 0.9*1 = 0.9
        self.assertTrue(np.allclose(holm([0.9, 0.01, 0.02]), [0.9, 0.03, 0.04]))
        # 0.5*2 = 1.0 (capped), then 0.5*1 = 0.5 -> raised to 1.0
        self.assertTrue(np.allclose(holm([0.5, 0.5]), [1.0, 1.0]))

    def test_holm_properties(self):
        rng = random.Random(0)
        for _ in range(200):
            n = rng.randint(1, 20)
            p = [rng.random() for _ in range(n)]
            adj = list(holm(p))
            # every adjusted value >= its raw value, and <= 1
            self.assertTrue(all(a >= rp - 1e-12 for a, rp in zip(adj, p)))
            self.assertTrue(all(0 <= a <= 1 + 1e-12 for a in adj))
            # non-decreasing when sorted by raw p
            adj_sorted = [a for _, a in sorted(zip(p, adj))]
            self.assertTrue(all(adj_sorted[i] <= adj_sorted[i + 1] + 1e-12
                                for i in range(len(adj_sorted) - 1)))
            # agrees with the independent reference
            self.assertTrue(np.allclose(adj, naive_holm(p)))
            if multipletests is not None:
                self.assertTrue(np.allclose(adj, multipletests(p, method='holm')[1]))


class TestCI(unittest.TestCase):

    def test_ci_known_values(self):
        x = [1, 2, 3, 4, 5]
        mean, h, n = ci(x)
        self.assertAlmostEqual(mean, 3.0)
        # t_{0.975, 4} * s / sqrt(5) = 2.7764 * 1.5811 / 2.2361 = 1.9632
        self.assertAlmostEqual(h, 1.9632, places=4)
        lo, hi = stats.t.interval(0.95, 4, loc=3, scale=stats.sem(x))
        self.assertAlmostEqual(h, (hi - lo) / 2, places=10)
        self.assertEqual(n, 5)

    def test_ci_nans_dropped(self):
        mean, h, n = ci([1, float('nan'), 3])
        self.assertAlmostEqual(mean, 2.0)
        self.assertEqual(n, 2)
        self.assertFalse(math.isnan(h))

    def test_ci_single_value(self):
        mean, h, n = ci([7])
        self.assertAlmostEqual(mean, 7.0)
        self.assertTrue(math.isnan(h))
        self.assertEqual(n, 1)

    def test_ci_empty(self):
        mean, h, n = ci([])
        self.assertTrue(math.isnan(mean))
        self.assertTrue(math.isnan(h))
        self.assertEqual(n, 0)


class TestWilcoxon(unittest.TestCase):

    def test_all_zero(self):
        self.assertEqual(wilcoxon_p([0, 0, 0, 0]), 1.0)

    def test_empty(self):
        self.assertEqual(wilcoxon_p([]), 1.0)

    def test_matches_scipy(self):
        rng = random.Random(42)
        d = [rng.gauss(0.3, 1.0) for _ in range(40)]
        expected = float(stats.wilcoxon(d, zero_method='wilcox').pvalue)
        self.assertAlmostEqual(wilcoxon_p(d), expected)

    def test_shifted_sample_significant(self):
        rng = random.Random(0)
        d = [rng.gauss(1.0, 0.5) for _ in range(50)]
        self.assertLess(wilcoxon_p(d), 0.001)


class TestPaired(unittest.TestCase):

    def test_paired_pairs_correctly(self):
        """A and B on 3 seeds with per-seed diffs +0.1, +0.2, +0.3, rows in shuffled order:
        mean_diff = 0.2 only if rows are matched by key, not by position."""
        rows = [
            dict(family='loose', seed=0, start='random', protocol='A', rho=1.1),
            dict(family='loose', seed=2, start='random', protocol='B', rho=1.0),
            dict(family='loose', seed=0, start='random', protocol='B', rho=1.0),
            dict(family='loose', seed=1, start='random', protocol='A', rho=1.2),
            dict(family='loose', seed=2, start='random', protocol='A', rho=1.3),
            dict(family='loose', seed=1, start='random', protocol='B', rho=1.0),
        ]
        out = paired(pd.DataFrame(rows), ['family', 'seed', 'start'], 'A', 'B', 'rho', ['family'])
        self.assertEqual(len(out), 1)
        row = out.iloc[0]
        self.assertAlmostEqual(row['mean_diff'], 0.2)
        self.assertEqual(row['n'], 3)

    def test_paired_holm_across_groups(self):
        """Two groups in `by`: p_holm equals holm() of the two raw p-values."""
        rows = []
        rng = random.Random(0)
        for att in ('block', 'hijack'):
            shift = 1.0 if att == 'block' else 0.0
            for sd in range(30):
                rows.append(dict(family='loose', seed=sd, start='random', attack=att,
                                 protocol='A', rho=rng.gauss(shift, 1.0)))
                rows.append(dict(family='loose', seed=sd, start='random', attack=att,
                                 protocol='B', rho=rng.gauss(0.0, 1.0)))
        out = paired(pd.DataFrame(rows), ['family', 'seed', 'start'], 'A', 'B', 'rho', ['attack'])
        self.assertEqual(len(out), 2)
        self.assertTrue(np.allclose(out['p_holm'], holm(list(out['p']))))


if __name__ == '__main__':
    unittest.main()
