"""Tests of the CP-SAT reference solver. Run from the repository root:
    python -m unittest discover -s vmgm/tests -t . -v
Skipped if ortools is not installed."""
import importlib.util
import itertools
import unittest

from vmgm import model as M

HAS_ORTOOLS = importlib.util.find_spec('ortools') is not None


@unittest.skipUnless(HAS_ORTOOLS, 'ortools not installed')
class TestCpSat(unittest.TestCase):
    def test_optimal_on_tiny_instances_by_brute_force(self):
        """6 exams, 4 slots: CP-SAT's optimum equals the minimum of F_cost over all 4^6 timetables."""
        from vmgm.cpsat import solve
        for seed in range(5):
            inst = M.make_instance(seed, N=3, per=2, S=4, p=0.5)
            best = min(M.F_cost(inst, list(x)) for x in itertools.product(range(inst['S']), repeat=inst['E']))
            r = solve(inst, time_limit=30, workers=4)
            self.assertEqual(r['status'], 'OPTIMAL')
            self.assertEqual(r['F_best'], best)
            self.assertEqual(M.F_cost(inst, r['x']), best)

    def test_objective_is_f_cost_on_a_real_instance(self):
        from vmgm.cpsat import solve
        inst = M.make_instance(100, **M.FAMILIES['loose'])
        r = solve(inst, time_limit=60, workers=8)
        self.assertEqual(M.F_cost(inst, r['x']), r['F_best'])
        self.assertLessEqual(r['F_bound'], r['F_best'])

    def test_never_worse_than_its_warm_start(self):
        from vmgm.cpsat import honest_mgm, solve
        inst = M.make_instance(100, **M.FAMILIES['tight'])
        hint = honest_mgm(inst, 100)
        r = solve(inst, time_limit=10, workers=8, hint=hint)
        self.assertLessEqual(r['F_best'], M.F_cost(inst, hint))
        self.assertLessEqual(r['F_bound'], r['F_best'])
        self.assertEqual(M.F_cost(inst, r['x']), r['F_best'])


if __name__ == '__main__':
    unittest.main()
