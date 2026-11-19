"""Soft quarantine (issue #14, Result 8): a flagged department keeps the preferences its consistent
history implied at flag time (gmax on slots it never claimed about) instead of losing them.

Run from the repository root:  python -m unittest discover -s vmgm/tests -t . -v
"""
import unittest
from unittest import mock

from vmgm import model as M
from vmgm import protocol as P
from vmgm.attacks import ALL_ATTACKS
from vmgm.attacks import announce as real_announce
from vmgm.invariants import check_all, fake_preferences
from vmgm.liars import make_types, place_liars

LAM = 3.0
SOFT = P.PROTOCOLS['VMGM-hist-soft']
HARD = P.PROTOCOLS['VMGM-hist-quar']


def small(seed, family='loose'):
    return M.add_fake_preferences(M.make_instance(seed, **M.FAMILIES[family]), LAM)


class TestSoftQuarantine(unittest.TestCase):
    def test_equals_mgm_when_all_honest(self):
        for fam in ('loose', 'tight'):
            for sd in range(3):
                inst = small(sd, fam)
                x0 = M.random_start(inst, 1000 + sd)
                honest = ['honest'] * inst['N']
                ref = P.run(inst, x0, honest, LAM, P.PROTOCOLS['MGM'], seed=sd)
                res = P.run(inst, x0, honest, LAM, SOFT, seed=sd)
                self.assertEqual(res.x, ref.x)
                self.assertEqual(res.rounds, ref.rounds)
                self.assertFalse(res.flagged)

    def test_every_proven_property_holds(self):
        """Result 8: termination, per-exam direct damage < gmax over the whole run, global bound, round
        bound, no false flags; every attack, k in {1,2,3,6}, both placements, both record modes."""
        for fam in ('loose', 'tight'):
            for sd in range(2):
                inst = small(sd, fam)
                x0 = M.random_start(inst, 1000 + sd)
                for k in (1, 2, 3, 6):
                    for placement in ('adjacent', 'spread'):
                        liars = place_liars(inst, k, placement, seed=sd)
                        for att in ALL_ATTACKS + [ALL_ATTACKS]:
                            types = make_types(inst, liars, att)
                            for record in ('posted', 'executed'):
                                prot = dict(SOFT, record=record)
                                res = P.run(inst, x0, types, LAM, prot, seed=sd, max_rounds=1000)
                                with self.subTest(fam=fam, sd=sd, k=k, pl=placement, att=att, rec=record):
                                    out = check_all(inst, res, types, prot)
                                    self.assertLess(out['dmg_total'], 1.0)
                                    self.assertFalse(res.capped)

    def test_priority_uses_frozen_preferences(self):
        """A flagged department's priority is min(claim, V + g~(from) - g~(to)), with g~ rebuilt here
        independently from the flag-time scores (gmax on slots without a score)."""
        checked = 0
        # (a flagged churner never moves again: its frozen preferences make going back cost gmax; the
        # attacks below do keep moving after the flag, so the priority formula is exercised)
        for sd, att in [(sd, att) for sd in range(4) for att in ('exag_naive', 'maxbound', 'sabotage', 'hijack')]:
            inst = small(sd)
            x0 = M.random_start(inst, 1000 + sd)
            types = make_types(inst, place_liars(inst, 3, 'random', seed=sd), att)
            res = P.run(inst, x0, types, LAM, SOFT, seed=sd)
            for t, rnd in enumerate(res.trace, start=1):
                for m in rnd:
                    i = m['dept']
                    if i in res.flag_round and res.flag_round[i] <= t:
                        g = fake_preferences({m['e']: res.flag_scores[i][m['e']]})[m['e']]
                        expected = min(m['claim'], m['v'] + g.get(m['frm'], inst['gmax']) - g.get(m['to'], inst['gmax']))
                        self.assertEqual(m['eff'], expected)
                        self.assertGreater(m['eff'], 0)
                        checked += 1
        self.assertGreater(checked, 0)                      # the test is not vacuous

    def test_soft_cheaper_than_hard_for_wrongly_quarantined_honest(self):
        """Control: honest departments forced into quarantine lose less under soft than under hard
        quarantine on most instances (their frozen preferences are their real ones)."""
        better = total = 0
        for fam in ('loose', 'tight'):
            for sd in range(5):
                inst = small(sd, fam)
                x0 = M.random_start(inst, 1000 + sd)
                honest = ['honest'] * inst['N']
                forced = {0: 2, 5: 2}
                hard = P.run(inst, x0, honest, LAM, HARD, seed=sd, forced_quarantine=forced)
                soft = P.run(inst, x0, honest, LAM, SOFT, seed=sd, forced_quarantine=forced)
                total += 1
                better += M.F_cost(inst, soft.x) <= M.F_cost(inst, hard.x)
        self.assertGreaterEqual(better, 0.7 * total)

    def test_hard_quarantine_ignores_frozen_preferences(self):
        """The frozen preferences only enter the soft response: replacing them with nothing must not change
        a hard-quarantine run. (The E2 re-run additionally checks every old row is unchanged.)"""
        inst = small(0)
        x0 = M.random_start(inst, 1000)
        for att in ('churn', 'sabotage', 'exag_naive'):
            types = make_types(inst, place_liars(inst, 3, 'adjacent', seed=0), att)
            a = P.run(inst, x0, types, LAM, HARD, seed=0)
            with mock.patch.object(P, 'frozen_preferences', return_value={}):
                b = P.run(inst, x0, types, LAM, HARD, seed=0)
            self.assertEqual(a.x, b.x, att)
            self.assertEqual(a.trace, b.trace, att)


if __name__ == '__main__':
    unittest.main()
