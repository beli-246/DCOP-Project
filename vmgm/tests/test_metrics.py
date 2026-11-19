"""Tests for vmgm/metrics.py: every metric that appears in the Results section.

Issue #10. Each test pins a metric to a value derived either by hand (arithmetic in
the comments) or from a property that must hold. Run from the repository root:

    python -m unittest discover -s vmgm/tests -t . -v

The hand-computed instance is example_instance() from test_vmgm.py: 3 departments,
each owns one exam, exam 0 (EE/e1) shares 3 students with exam 1 (CSE/c1) and 2
students with exam 2 (maths/m1), 6 slots (2 per day). gmax = 50, lam = 3.
"""
import math
import unittest

from vmgm import model as M
from vmgm.invariants import check_all
from vmgm.liars import make_types, place_liars
from vmgm.metrics import dsa_metrics, run_metrics
from vmgm.protocol import PROTOCOLS, RunResult, run, run_dsa
from vmgm.tests.test_vmgm import example_instance, small

LAM = 3.0


def tiny_inst_with_prefs():
    """example_instance() plus a few non-zero preferences so G, J, liar_profit are not trivial."""
    inst = example_instance()
    # exam 0 dislikes slot 3 (10); exam 2 dislikes slot 1 (20). Everything else 0.
    inst['g'] = [[0, 0, 0, 10, 0, 0], [0, 0, 0, 0, 0, 0], [0, 20, 0, 0, 0, 0]]
    inst['gmax'] = 50
    return M.add_fake_preferences(inst, LAM)


def build_result(x0, x, trace, flagged=None, flag_round=None, rounds=None, capped=False):
    return RunResult(
        x=list(x), rounds=rounds if rounds is not None else len(trace),
        flagged=set(flagged or []), flag_round=dict(flag_round or {}), capped=capped,
        x0=list(x0), trace=trace,
    )


class TestHandComputedMetrics(unittest.TestCase):

    def setUp(self):
        self.inst = tiny_inst_with_prefs()
        # x0 = [0, 0, 1]: e1 clashes with c1 at slot 0 (H = 10*3 = 30),
        #                 e1 next to m1 on same day (H += 2*2 = 4), so H(x0) = 34.
        # G(x0) = g[0][0] + g[1][0] + g[2][1] = 0 + 0 + 20 = 20, F0 = 54.
        self.x0 = [0, 0, 1]
        # res.x = [3, 0, 1]: e1 moved to slot 3, no clash, no back-to-back, H = 0.
        # G = g[0][3] + g[1][0] + g[2][1] = 10 + 0 + 20 = 30, F = 30.
        self.x_final = [3, 0, 1]
        # Both references are the start timetable, F_ref = 54.
        self.ref_mgm_x = [0, 0, 1]
        self.ref_self_x = [0, 0, 1]
        v = M.V(self.inst, self.x0, 0, 3)
        self.assertEqual(v, 34)
        self.trace_one_liar_move = [[dict(dept=0, e=0, frm=0, to=3, claim=v, v=v, eff=v, unflagged=True)]]

    def test_costs_and_rho(self):
        """F, H, G, F0, F_ref, rho, extra, extra_H, extra_G from the arithmetic above."""
        types = ['block', 'honest', 'honest']
        res = build_result(self.x0, self.x_final, self.trace_one_liar_move)
        m = run_metrics(self.inst, res, types, LAM, self.ref_mgm_x, self.ref_self_x)
        self.assertEqual(m['F'], 30)
        self.assertEqual(m['H'], 0)
        self.assertEqual(m['G'], 30)
        self.assertEqual(m['F0'], 54)
        self.assertEqual(m['F_ref'], 54)
        self.assertAlmostEqual(m['rho'], 30 / 54)     # 0.5556
        self.assertEqual(m['extra'], -24)              # 30 - 54
        self.assertEqual(m['extra_H'], -34)            # 0 - 34
        self.assertEqual(m['extra_G'], 10)             # 30 - 20
        self.assertEqual(m['K'], 0)                    # no clashing students in res.x
        self.assertEqual(m['rounds'], 1)
        self.assertTrue(m['finished'])

    def test_direct_damage(self):
        """direct_H counts only liar moves. Two liar moves of same exam (v = -20, v = +5)
        plus an honest move (v = 100) that must not count.
            direct_H = -(-20) + -(+5) = 15
            dmg_exam_max = 15 / 50 = 0.3
        """
        trace = [
            [dict(dept=0, e=0, frm=0, to=1, claim=0, v=-20, eff=0, unflagged=True),
             dict(dept=1, e=1, frm=0, to=2, claim=0, v=100, eff=100, unflagged=True)],
            [dict(dept=0, e=0, frm=1, to=2, claim=0, v=5, eff=0, unflagged=True)],
        ]
        types = ['block', 'honest', 'honest']
        res = build_result(self.x0, self.x_final, trace)
        m = run_metrics(self.inst, res, types, LAM, self.ref_mgm_x, self.ref_self_x)
        self.assertEqual(m['direct_H'], 15)
        self.assertAlmostEqual(m['dmg_exam_max'], 15 / 50)

    def test_detection_fields(self):
        """flagged={0,1} with only 0 a liar: detected=1, false_flags=1, det_rate=1/1=1.0,
        flag_round_mean=3 (dept 1 is honest so its flag round 5 is not in the mean)."""
        types = ['block', 'honest', 'honest']
        res = build_result(self.x0, self.x_final, self.trace_one_liar_move,
                           flagged={0, 1}, flag_round={0: 3, 1: 5})
        m = run_metrics(self.inst, res, types, LAM, self.ref_mgm_x, self.ref_self_x)
        self.assertEqual(m['detected'], 1)
        self.assertEqual(m['false_flags'], 1)
        self.assertAlmostEqual(m['det_rate'], 1.0)
        self.assertAlmostEqual(m['flag_round_mean'], 3.0)

    def test_honest_loss_and_liar_profit(self):
        """
        Dept 0 is the liar (lam = 3); honest = {1, 2}; res.x = [3,0,1], ref_self_x = [0,0,1].
        burden(x, i) = own preference cost + half of each pairwise cost with a neighbour.

        honest_loss:
          burden(res.x, 1):    g=0;  pc(slot 0, slot 3, 3 students) = 0,  half = 0   -> 0
          burden(ref_self, 1): g=0;  pc(0, 0, 3) = 30 (clash),        half = 15  -> 15
          diff for dept 1 = -15
          burden(res.x, 2):    g[2][1]=20; pc(1, 3, 2) = 0,  half = 0  -> 20
          burden(ref_self, 2): g=20;       pc(1, 0, 2) = 4,  half = 2  -> 22
          diff for dept 2 = -2
          honest_loss = -15 + -2 = -17.

        liar_profit (J = lam * own preference + full pairwise cost of own exams):
          J(ref_self=[0,0,1], 0) = 3*g[0][0] + pc(0,0,3) + pc(0,1,2) = 0 + 30 + 4   = 34
          J(res.x=[3,0,1], 0)    = 3*g[0][3] + pc(3,0,3) + pc(3,1,2) = 30 + 0 + 0   = 30
          profit = 34 - 30 = 4.

        liar_deg: dept 0 neighbours {1, 2} -> 2.
        """
        types = ['block', 'honest', 'honest']
        res = build_result(self.x0, self.x_final, self.trace_one_liar_move)
        m = run_metrics(self.inst, res, types, LAM, self.ref_mgm_x, self.ref_self_x)
        self.assertAlmostEqual(m['honest_loss'], -17.0)
        self.assertAlmostEqual(m['liar_profit'], 4.0)
        self.assertAlmostEqual(m['liar_deg'], 2.0)

    def test_no_liars(self):
        """All honest: det_rate NaN, liar_profit 0, direct_H 0, dmg_exam_max 0."""
        types = ['honest'] * 3
        res = build_result(self.x0, self.x_final, self.trace_one_liar_move)
        m = run_metrics(self.inst, res, types, LAM, self.ref_mgm_x, self.ref_self_x)
        self.assertTrue(math.isnan(m['det_rate']))
        self.assertEqual(m['liar_profit'], 0)
        self.assertEqual(m['direct_H'], 0)
        self.assertEqual(m['dmg_exam_max'], 0.0)
        self.assertEqual(m['false_flags'], 0)


class TestPropertiesOnRealRuns(unittest.TestCase):

    def test_rho_one_when_same_as_reference(self):
        """Honest MGM against itself: rho = 1, extra = 0, honest_loss = 0."""
        for sd in range(4):
            for fam in ('loose', 'tight'):
                inst = small(sd, fam)
                x0 = M.random_start(inst, 1000 + sd)
                types = ['honest'] * inst['N']
                res = run(inst, x0, types, LAM, PROTOCOLS['MGM'], seed=sd)
                m = run_metrics(inst, res, types, LAM, res.x, res.x)
                self.assertAlmostEqual(m['rho'], 1.0)
                self.assertEqual(m['extra'], 0)
                self.assertEqual(m['honest_loss'], 0.0)
                self.assertEqual(m['direct_H'], 0)

    def test_parts_add_up(self):
        """F = H + G, extra = extra_H + extra_G, sum of burdens = F; attacked runs
        (churn, k = 3, VMGM-hist-quar)."""
        prot = PROTOCOLS['VMGM-hist-quar']
        for sd in range(4):
            for fam in ('loose', 'tight'):
                inst = small(sd, fam)
                x0 = M.random_start(inst, 1000 + sd)
                liars = place_liars(inst, 3, 'random', seed=sd)
                types = make_types(inst, liars, 'churn')
                honest_types = ['honest'] * inst['N']
                ref_mgm = run(inst, x0, honest_types, LAM, PROTOCOLS['MGM'], seed=sd).x
                ref_self = run(inst, x0, honest_types, LAM, prot, seed=sd).x
                res = run(inst, x0, types, LAM, prot, seed=sd)
                check_all(inst, res, types, prot)
                m = run_metrics(inst, res, types, LAM, ref_mgm, ref_self)
                self.assertEqual(m['F'], m['H'] + m['G'])
                self.assertAlmostEqual(m['extra'], m['extra_H'] + m['extra_G'])
                self.assertAlmostEqual(
                    sum(M.burden(inst, res.x, i) for i in range(inst['N'])), m['F'])

    def test_direct_damage_matches_invariants(self):
        """dmg_exam_max (metrics) vs dmg_total (invariants.check_all).

        Rule: invariants counts a liar exam that never moved as 0, while metrics only
        looks at exams that moved. So if every liar exam moved at least once they are
        equal; otherwise dmg_total == max(dmg_exam_max, 0.0). The paper reports
        dmg_exam_max, whose largest value is positive, so the two agree on every
        number in the paper."""
        prot = PROTOCOLS['VMGM-hist-quar']
        for sd in range(4):
            for fam in ('loose', 'tight'):
                inst = small(sd, fam)
                x0 = M.random_start(inst, 1000 + sd)
                liars = place_liars(inst, 2, 'random', seed=sd)
                types = make_types(inst, liars, 'churn')
                honest_types = ['honest'] * inst['N']
                ref_mgm = run(inst, x0, honest_types, LAM, PROTOCOLS['MGM'], seed=sd).x
                ref_self = run(inst, x0, honest_types, LAM, prot, seed=sd).x
                res = run(inst, x0, types, LAM, prot, seed=sd)
                out = check_all(inst, res, types, prot)
                m = run_metrics(inst, res, types, LAM, ref_mgm, ref_self)
                liar_set = set(liars)
                moved_exams = {mv['e'] for rnd in res.trace for mv in rnd if mv['dept'] in liar_set}
                all_liar_exams = {e for i in liars for e in inst['exams'][i]}
                if moved_exams == all_liar_exams:
                    self.assertAlmostEqual(out['dmg_total'], m['dmg_exam_max'])
                else:
                    self.assertAlmostEqual(out['dmg_total'], max(m['dmg_exam_max'], 0.0))

    def test_dsa_metrics(self):
        """dsa_metrics on an honest DSA run: direct_H/dmg_exam_max NaN, no detection,
        rho = F / F_ref."""
        inst = small(0, 'loose')
        x0 = M.random_start(inst, 1000)
        types = ['honest'] * inst['N']
        x_h, rr_h, capped_h = run_dsa(inst, x0, types, LAM, seed=0)
        ref_mgm = run(inst, x0, types, LAM, PROTOCOLS['MGM'], seed=0).x
        m = dsa_metrics(inst, x_h, rr_h, capped_h, x0, types, LAM, ref_mgm, x_h)
        self.assertTrue(math.isnan(m['direct_H']))
        self.assertTrue(math.isnan(m['dmg_exam_max']))
        self.assertEqual(m['detected'], 0)
        self.assertEqual(m['false_flags'], 0)
        self.assertAlmostEqual(m['rho'], m['F'] / m['F_ref'])


if __name__ == '__main__':
    unittest.main()
