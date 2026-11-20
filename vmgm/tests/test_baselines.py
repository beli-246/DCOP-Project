"""Tests of the two comparison algorithms (RP-MGM and DSA) and of the no-freeze step of Result 5.

Run from the repository root:  python -m unittest discover -s vmgm/tests -t . -v
"""
import unittest
from unittest import mock

from vmgm import model as M
from vmgm import protocol as P
from vmgm.attacks import announce as real_announce
from vmgm.liars import make_types
from vmgm.tests.test_vmgm import LAM, small

FAMILIES = ('loose', 'tight')
SEEDS = range(5)
VMGM = ('VMGM-move-cap', 'VMGM-move-quar', 'VMGM-hist-cap', 'VMGM-hist-quar')


def instances():
    """(family, seed, instance, random start) for loose and tight, seeds 0-4."""
    for fam in FAMILIES:
        for sd in SEEDS:
            inst = small(sd, fam)
            yield fam, sd, inst, M.random_start(inst, 1000 + sd)


def no_positive_move(inst, x):
    return all(M.best_move(inst, x, i, inst['g'])[1] is None for i in range(inst['N']))


def blocker_without_move(inst, x, i, kind, lam, **kw):
    """Department 0 posts "no move" with a huge claim; everyone else plays as told."""
    if i == 0:
        return (10**6, None, None)
    return real_announce(inst, x, i, kind, lam, **kw)


def run_with_blocker(inst, x0, name, seed):
    with mock.patch.object(P, 'announce', blocker_without_move):
        return P.run(inst, x0, ['honest'] * inst['N'], LAM, P.PROTOCOLS[name], seed=seed)


class TestRPMGM(unittest.TestCase):
    def test_rp_mgm_honest_finishes_and_never_raises_cost(self):
        for fam, sd, inst, x0 in instances():
            res = P.run(inst, x0, ['honest'] * inst['N'], LAM, P.PROTOCOLS['RP-MGM'], seed=sd)
            with self.subTest(fam=fam, seed=sd):
                self.assertFalse(res.capped)
                self.assertTrue(res.trace)
                x = list(res.x0)
                cost = M.F_cost(inst, x)
                for rnd, moves in enumerate(res.trace, 1):
                    self.assertTrue(moves)
                    for m in moves:
                        self.assertEqual(x[m['e']], m['frm'])
                        x[m['e']] = m['to']
                    new = M.F_cost(inst, x)
                    self.assertLess(new, cost, f'round {rnd}')
                    cost = new
                self.assertEqual(x, res.x)                    # the trace replays to the final timetable
                self.assertTrue(no_positive_move(inst, res.x))

    def test_rp_mgm_moves_are_non_neighbours(self):
        for fam, sd, inst, x0 in instances():
            res = P.run(inst, x0, ['honest'] * inst['N'], LAM, P.PROTOCOLS['RP-MGM'], seed=sd)
            with self.subTest(fam=fam, seed=sd):
                for rnd, moves in enumerate(res.trace, 1):
                    depts = [m['dept'] for m in moves]
                    self.assertEqual(len(depts), len(set(depts)), f'round {rnd}')
                    for i in depts:
                        self.assertFalse(inst['nbr'][i] & set(depts), f'round {rnd}, dept {i}')

    def test_rp_mgm_churn_does_not_finish(self):
        """Known weakness stated in the paper: RP-MGM almost never finishes under churn."""
        capped = []
        for sd in SEEDS:
            inst = small(sd)
            x0 = M.random_start(inst, 1000 + sd)
            types = make_types(inst, {0}, 'churn')
            res = P.run(inst, x0, types, LAM, P.PROTOCOLS['RP-MGM'], seed=sd, max_rounds=300)
            capped.append(res.capped and res.rounds == 300)
        self.assertTrue(any(capped), capped)


class TestDSA(unittest.TestCase):
    def test_dsa_honest_finishes(self):
        for fam, sd, inst, x0 in instances():
            x, rounds, capped = P.run_dsa(inst, x0, ['honest'] * inst['N'], LAM, seed=sd)
            with self.subTest(fam=fam, seed=sd):
                self.assertFalse(capped)
                self.assertLess(rounds, 300)
                self.assertTrue(no_positive_move(inst, x))

    def test_dsa_ignores_claim_only_attacks(self):
        """DSA posts no gains, so attacks that act only through announcements change nothing."""
        for fam, sd, inst, x0 in instances():
            ref = P.run_dsa(inst, x0, ['honest'] * inst['N'], LAM, seed=sd)
            for att in ('block', 'hijack', 'maxbound'):
                for liars in ({0}, {0, 5, 9}):
                    types = make_types(inst, liars, att)
                    with self.subTest(fam=fam, seed=sd, att=att, liars=liars):
                        self.assertEqual(P.run_dsa(inst, x0, types, LAM, seed=sd), ref)

    def test_dsa_sabotage_acts(self):
        self.assertIn('sabotage', P.DSA_ATTACKS)
        differs = []
        for sd in SEEDS:
            inst = small(sd)
            x0 = M.random_start(inst, 1000 + sd)
            ref, _, _ = P.run_dsa(inst, x0, ['honest'] * inst['N'], LAM, seed=sd)
            x, _, _ = P.run_dsa(inst, x0, make_types(inst, {0}, 'sabotage'), LAM, seed=sd)
            differs.append(x != ref)
        self.assertTrue(any(differs), differs)


class TestNoFreeze(unittest.TestCase):
    """Result 5's no-freeze step: "no move" has priority 0, so the highest positive priority always
    wins. Plain MGM has no such rule and a "no move" post with a huge claim freezes it."""

    def test_plain_mgm_can_freeze(self):
        for fam, sd, inst, x0 in instances():
            res = run_with_blocker(inst, x0, 'MGM', sd)
            with self.subTest(fam=fam, seed=sd):
                self.assertTrue(res.capped)
                self.assertLess(res.rounds, 300)          # stopped because nobody could move
                self.assertFalse(no_positive_move(inst, res.x))   # ... although moves were left

    def test_vmgm_cannot_freeze(self):
        for fam, sd, inst, x0 in instances():
            for name in VMGM:
                res = run_with_blocker(inst, x0, name, sd)
                with self.subTest(fam=fam, seed=sd, protocol=name):
                    self.assertEqual(res.flag_round.get(0), 1)
                    self.assertFalse(res.capped)

    def test_no_honest_flag_in_freeze_scenario(self):
        for fam, sd, inst, x0 in instances():
            for name in VMGM:
                res = run_with_blocker(inst, x0, name, sd)
                with self.subTest(fam=fam, seed=sd, protocol=name):
                    self.assertEqual(res.flagged, {0})


if __name__ == '__main__':
    unittest.main()
