"""Every automatic check must be able to fail (issue #6). Otherwise "all runs checked, no violation"
would prove nothing. (A) hand-made runs that break exactly one property; (B) real runs of protocols
where the property is not guaranteed.

Run from the repository root:  python -m unittest discover -s vmgm/tests -t . -v
"""
import dataclasses
import unittest

from vmgm import model as M
from vmgm.invariants import InvariantError, check_all, global_bound, potential_decreases
from vmgm.liars import make_types
from vmgm.protocol import PROTOCOLS, RunResult, run

LAM = 3.0


def small(seed, family='loose'):
    return M.add_fake_preferences(M.make_instance(seed, **M.FAMILIES[family]), LAM)


def move(dept, e, frm, to, v, unflagged=True, claim=None):
    return dict(dept=dept, e=e, frm=frm, to=to, claim=v + 50 if claim is None else claim, v=v,
                eff=v + 50, unflagged=unflagged)


class TestSyntheticViolations(unittest.TestCase):
    def setUp(self):
        self.inst = small(0)
        self.x0 = M.greedy_start(self.inst)
        self.types = make_types(self.inst, {0}, 'churn')
        self.e = self.inst['exams'][0][0]                 # department 0's first exam

    def _res(self, trace, flagged=(), flag_round=None, x=None, capped=False):
        x = list(self.x0) if x is None else x
        return RunResult(x=x, rounds=len(trace) + 1, flagged=set(flagged), flag_round=flag_round or {},
                         capped=capped, x0=list(self.x0), trace=trace, flag_scores={}, end_scores={})

    def test_direct_damage_check_fires(self):
        e = self.e
        over = self._res([[move(0, e, 0, 1, -30)], [move(0, e, 1, 2, -25)]])        # 55 >= gmax = 50
        with self.assertRaisesRegex(InvariantError, 'Result 4 violated'):
            check_all(self.inst, over, self.types, PROTOCOLS['VMGM-hist-cap'])
        under = self._res([[move(0, e, 0, 1, -30)], [move(0, e, 1, 2, -15)]])       # 45 < 50: no damage error
        out = check_all(self.inst, under, self.types, PROTOCOLS['VMGM-hist-cap'])
        self.assertAlmostEqual(out['dmg_unflagged'], 45 / 50)

    def test_direct_damage_after_flag_fires_under_quarantine(self):
        e = self.e
        res = self._res([[move(0, e, 0, 1, -30, unflagged=False)], [move(0, e, 1, 2, -25, unflagged=False)]],
                        flagged={0}, flag_round={0: 1})
        out = check_all(self.inst, res, self.types, PROTOCOLS['VMGM-hist-cap'])   # cap only: not covered
        self.assertAlmostEqual(out['dmg_total'], 55 / 50)
        with self.assertRaisesRegex(InvariantError, r'Result 4 \(quarantine\) violated'):
            check_all(self.inst, res, self.types, PROTOCOLS['VMGM-hist-quar'])

    def test_global_bound_check_fires(self):
        honest = ['honest'] * self.inst['N']
        all_in_slot0 = [0] * self.inst['E']                                        # every exam in one slot
        self.assertGreater(M.F_cost(self.inst, all_in_slot0), M.F_cost(self.inst, self.x0))
        res = self._res([], x=all_in_slot0)
        with self.assertRaisesRegex(InvariantError, 'global bound violated'):
            global_bound(self.inst, res, honest)

    def test_finished_check_fires(self):
        x0 = M.random_start(self.inst, 1000)
        res = run(self.inst, x0, self.types, LAM, PROTOCOLS['VMGM-hist-quar'], seed=0)
        check_all(self.inst, res, self.types, PROTOCOLS['VMGM-hist-quar'])          # the real run passes
        with self.assertRaisesRegex(InvariantError, 'did not finish'):
            check_all(self.inst, dataclasses.replace(res, capped=True), self.types, PROTOCOLS['VMGM-hist-quar'])

    def test_false_flag_through_check_all(self):
        res = self._res([], flagged={3})                                            # department 3 is honest
        for name in ('VMGM-move-cap', 'VMGM-hist-cap', 'VMGM-hist-quar', 'VMGM-hist-soft'):
            with self.subTest(name=name), self.assertRaisesRegex(InvariantError, 'honest departments flagged'):
                check_all(self.inst, res, self.types, PROTOCOLS[name])

    def test_potential_check_fires_synthetic(self):
        honest = ['honest'] * self.inst['N']
        x = list(self.x0)
        # find a single move that raises the total cost
        for e in range(self.inst['E']):
            for a in range(self.inst['S']):
                y = list(x)
                y[e] = a
                if M.F_cost(self.inst, y) > M.F_cost(self.inst, x):
                    bad = [[move(self.inst['owner'][e], e, x[e], a, M.V(self.inst, x, e, a))]]
                    with self.assertRaisesRegex(InvariantError, 'potential did not decrease'):
                        potential_decreases(self.inst, self._res(bad, x=y), honest)
                    return
        self.fail('no cost-raising move found')


class TestRealRunsWithoutTheGuarantee(unittest.TestCase):
    """The README says the potential check is not vacuous: it fails on plain MGM and cap-only under churn."""

    def _fails_on_some_seed(self, name, k):
        failures = 0
        for sd in range(4):
            inst = small(sd)
            x0 = M.random_start(inst, 1000 + sd)
            types = make_types(inst, set(range(k)), 'churn')
            res = run(inst, x0, types, LAM, PROTOCOLS[name], seed=sd)
            try:
                potential_decreases(inst, res, types)
            except InvariantError:
                failures += 1
        return failures

    def test_potential_fails_on_plain_mgm_under_churn(self):
        self.assertGreater(self._fails_on_some_seed('MGM', 1) + self._fails_on_some_seed('MGM', 3), 0)

    def test_potential_fails_on_cap_only_under_churn(self):
        self.assertGreater(self._fails_on_some_seed('VMGM-hist-cap', 1) + self._fails_on_some_seed('VMGM-hist-cap', 3), 0)

    def test_checks_pass_on_the_main_method(self):
        for sd in range(4):
            inst = small(sd)
            x0 = M.random_start(inst, 1000 + sd)
            for k in (1, 3):
                types = make_types(inst, set(range(k)), 'churn')
                for name in ('VMGM-hist-quar', 'VMGM-hist-soft'):
                    res = run(inst, x0, types, LAM, PROTOCOLS[name], seed=sd)
                    check_all(inst, res, types, PROTOCOLS[name])


if __name__ == '__main__':
    unittest.main()
