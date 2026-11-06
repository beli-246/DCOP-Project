"""Unit tests. Run from the FAI folder:  python3 -m unittest discover -s vmgm/tests -t . -v"""
import random
import unittest

from vmgm import model as M
from vmgm.attacks import ALL_ATTACKS, announce, feasible_r_range
from vmgm.invariants import InvariantError, check_all, fake_preferences, no_false_flags
from vmgm.liars import liar_adjacency, make_types, place_liars
from vmgm.protocol import PROTOCOLS, Board, RunResult, run

LAM = 3.0
HQ = PROTOCOLS['VMGM-hist-quar']


def example_instance():
    """The proposal's worked example: e1 (EE) clashes with c1 (3 students) and is
    back-to-back with m1 (2 students). Exams: 0 = e1, 1 = c1, 2 = m1. Slots 0..5, 2 per day."""
    n = {(0, 1): 3, (0, 2): 2}
    E, S = 3, 6
    adj = {0: [(1, 3), (2, 2)], 1: [(0, 3)], 2: [(0, 2)]}
    return dict(E=E, S=S, N=3, owner=[0, 1, 2], n=n, g=[[0] * S for _ in range(E)], adj=adj,
                nbr={0: {1, 2}, 1: {0}, 2: {0}}, exams={0: [0], 1: [1], 2: [2]}, gmax=50)


def small(seed, family='loose', N=12):
    return M.add_fake_preferences(M.make_instance(seed, N=N, **M.FAMILIES[family]), LAM)


class TestCosts(unittest.TestCase):
    def test_pairwise_cost(self):
        self.assertEqual(M.pc(3, 3, 4), 40)          # clash: 10 per student
        self.assertEqual(M.pc(2, 3, 4), 8)           # same day, consecutive: 2 per student
        self.assertEqual(M.pc(1, 2, 4), 0)           # consecutive but different days
        self.assertEqual(M.pc(0, 5, 4), 0)

    def test_worked_example_public_gain(self):
        inst = example_instance()
        x = [0, 0, 1]                                 # e1 with c1 (clash), m1 next to it
        self.assertEqual(M.H_cost(inst, x), 30 + 4)
        self.assertEqual(M.V(inst, x, 0, 3), 34)      # moving e1 to slot 3 removes both

    def test_burdens_sum_to_total(self):
        inst = small(0)
        x = M.random_start(inst, 1)
        self.assertAlmostEqual(sum(M.burden(inst, x, i) for i in range(inst['N'])), M.F_cost(inst, x))


class TestHistoryCheck(unittest.TestCase):
    def test_worked_example_contradiction(self):
        b = Board([3])
        ok, new = b.check(0, 3, 4, 40, 50)            # "slot 4 is better by 40"
        self.assertTrue(ok)
        b.scores[0][4] = new
        ok, _ = b.check(0, 4, 3, 40, 50)              # "slot 3 is better by 40": contradiction
        self.assertFalse(ok)

    def test_range_violation(self):
        b = Board([0])
        b.scores[0][1] = -30                          # slot 1 claimed 30 better than slot 0
        ok, _ = b.check(0, 1, 2, 30, 50)              # slot 2 another 30 better: range 60 > 50
        self.assertFalse(ok)

    def test_truthful_history_never_flagged(self):
        rng = random.Random(0)
        for _ in range(200):
            g = [rng.randint(0, 50) for _ in range(6)]
            b = Board([0])
            cur = 0
            for _ in range(30):
                a = rng.randrange(6)
                if a == cur:
                    continue
                ok, new = b.check(0, cur, a, g[cur] - g[a], 50)
                self.assertTrue(ok)
                b.scores[0][a] = new
                cur = a

    def test_feasible_r_range(self):
        self.assertEqual(feasible_r_range({0: 0}, 0, 1, 50), (-50, 50))
        self.assertEqual(feasible_r_range({0: 0, 1: -20}, 0, 1, 50), (20, 20))
        self.assertEqual(feasible_r_range({0: 0, 1: -20}, 1, 2, 50), (-50, 30))
        self.assertEqual(feasible_r_range({0: 0, 1: 30}, 0, 1, 20), None)

    def test_fake_preferences_in_scale(self):
        gt = fake_preferences({0: {0: 0, 3: -40, 5: 10}})
        self.assertEqual(gt[0], {0: 40, 3: 0, 5: 50})


class TestHonest(unittest.TestCase):
    def test_result1_truthful_claims_within_scale(self):
        for sd in range(5):
            inst = small(sd)
            x = M.random_start(inst, sd)
            for i in range(inst['N']):
                claim, e, a = announce(inst, x, i, 'honest', LAM)
                if e is None:
                    self.assertEqual(claim, 0)
                else:
                    self.assertLessEqual(abs(claim - M.V(inst, x, e, a)), inst['gmax'])

    def test_vmgm_equals_mgm_when_all_honest(self):
        for fam in ('loose', 'tight'):
            for sd in range(4):
                inst = small(sd, fam)
                x0 = M.random_start(inst, 1000 + sd)
                types = ['honest'] * inst['N']
                ref = run(inst, x0, types, LAM, PROTOCOLS['MGM'], seed=sd)
                for name in ('VMGM-move-cap', 'VMGM-move-quar', 'VMGM-hist-cap', 'VMGM-hist-quar'):
                    res = run(inst, x0, types, LAM, PROTOCOLS[name], seed=sd)
                    self.assertEqual(res.x, ref.x, name)
                    self.assertEqual(res.rounds, ref.rounds, name)
                    self.assertFalse(res.flagged, name)
                    check_all(inst, res, types, PROTOCOLS[name])


class TestInvariantsWithLiars(unittest.TestCase):
    def test_every_attack_every_k(self):
        """Every proven property holds for all attacks, k in {1,2,3,6}, both placements, both record modes."""
        for fam in ('loose', 'tight'):
            for sd in range(2):
                inst = small(sd, fam)
                x0 = M.random_start(inst, 1000 + sd)
                for k in (1, 2, 3, 6):
                    for placement in ('adjacent', 'spread'):
                        liars = place_liars(inst, k, placement, seed=sd)
                        for att in ALL_ATTACKS + [ALL_ATTACKS]:          # last entry: mixed attacks
                            types = make_types(inst, liars, att)
                            for record in ('posted', 'executed'):
                                for name in ('VMGM-hist-cap', 'VMGM-hist-quar', 'VMGM-move-cap'):
                                    prot = dict(PROTOCOLS[name], record=record)
                                    res = run(inst, x0, types, LAM, prot, seed=sd, max_rounds=1000)
                                    with self.subTest(fam=fam, sd=sd, k=k, pl=placement, att=att,
                                                      rec=record, prot=name):
                                        check_all(inst, res, types, prot)

    def test_consistent_saboteur_never_flagged_and_spends_budget(self):
        worst = 0.0
        for sd in range(4):
            inst = small(sd)
            x0 = M.random_start(inst, 1000 + sd)
            liars = place_liars(inst, 2, 'random', seed=sd)
            types = make_types(inst, liars, 'sabotage_consistent')
            res = run(inst, x0, types, LAM, HQ, seed=sd)
            self.assertFalse(res.flagged & liars)
            worst = max(worst, check_all(inst, res, types, HQ)['dmg_unflagged'])
        self.assertGreater(worst, 0.5)        # it really uses its budget, so the test is not vacuous

    def test_delayed_attacker_flagged_after_switch(self):
        inst = small(0)
        x0 = M.random_start(inst, 1000)
        liars = place_liars(inst, 3, 'random', seed=0)
        types = make_types(inst, liars, 'delayed')
        res = run(inst, x0, types, LAM, HQ, seed=0, switch_round=5)
        for j in liars:
            if j in res.flagged:
                self.assertGreaterEqual(res.flag_round[j], 5)
        check_all(inst, res, types, HQ)

    def test_checks_detect_a_false_flag(self):
        res = RunResult(x=[0], rounds=1, flagged={0}, flag_round={0: 1}, capped=False, x0=[0])
        with self.assertRaises(InvariantError):
            no_false_flags(res, ['honest'])


class TestPhase3Additions(unittest.TestCase):
    def test_pref_spread_one_is_pilot_instance(self):
        a = M.make_instance(7, **M.FAMILIES['tight'])
        b = M.make_instance(7, pref_spread=1.0, **M.FAMILIES['tight'])
        self.assertEqual(a['g'], b['g'])
        self.assertEqual(a['n'], b['n'])
        c = M.make_instance(7, pref_spread=0.25, **M.FAMILIES['tight'])
        self.assertEqual(c['n'], a['n'])                       # same student overlaps
        self.assertLessEqual(max(max(r) for r in c['g']), 13)

    def test_stretch_liar_undetected_and_checked(self):
        for sd in range(3):
            inst = M.add_fake_preferences(M.make_instance(sd, pref_spread=0.25), LAM)
            for row, st in zip(inst['g'], inst['gtilde_stretch']):
                self.assertTrue(all(0 <= v <= inst['gmax'] for v in st))
                self.assertEqual(min(st), 0)
            x0 = M.random_start(inst, sd)
            liars = place_liars(inst, 3, 'random', seed=sd)
            types = make_types(inst, liars, 'exag_stretch')
            res = run(inst, x0, types, LAM, HQ, seed=sd)
            self.assertFalse(res.flagged)
            check_all(inst, res, types, HQ)

    def test_forced_quarantine_only_restricts(self):
        inst = small(0)
        x0 = M.random_start(inst, 1000)
        honest = ['honest'] * inst['N']
        free = run(inst, x0, honest, LAM, HQ, seed=0)
        ctl = run(inst, x0, honest, LAM, HQ, seed=0, forced_quarantine={0: 1, 5: 1})
        self.assertFalse(ctl.flagged)                          # forced departments are not "flagged"
        for rnd in ctl.trace:                                  # quarantined moves only lower student cost
            for m in rnd:
                if m['dept'] in (0, 5):
                    self.assertGreater(m['v'], 0)
        self.assertNotEqual(free.x, ctl.x)


class TestLiarPlacement(unittest.TestCase):
    def test_sizes_and_adjacency(self):
        adj_total = spr_total = 0
        for sd in range(10):
            inst = small(sd, 'loose')
            for k in (0, 1, 3, 6, 12):
                for pl in ('random', 'adjacent', 'spread'):
                    self.assertEqual(len(place_liars(inst, k, pl, seed=sd)), k)
            adj_total += liar_adjacency(inst, place_liars(inst, 4, 'adjacent', seed=sd))
            spr_total += liar_adjacency(inst, place_liars(inst, 4, 'spread', seed=sd))
        self.assertGreater(adj_total, spr_total)

    def test_mixed_types(self):
        inst = small(0)
        t = make_types(inst, {1, 5, 7}, ['block', 'churn'])
        self.assertEqual([t[1], t[5], t[7]], ['block', 'churn', 'block'])
        self.assertEqual(t.count('honest'), inst['N'] - 3)


if __name__ == '__main__':
    unittest.main()
