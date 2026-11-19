"""Integer-claim rule and the round bound of Result 5 (issue #15).

Run from the repository root:  python -m unittest discover -s vmgm/tests -t . -v
"""
import dataclasses
import unittest
from unittest import mock

from vmgm import model as M
from vmgm import protocol as P
from vmgm.attacks import ALL_ATTACKS
from vmgm.attacks import announce as real_announce
from vmgm.invariants import InvariantError, check_all
from vmgm.liars import make_types, place_liars

LAM = 3.0
HQ = P.PROTOCOLS['VMGM-hist-quar']


def small(seed, family='loose', N=12, lam=LAM, **kw):
    return M.add_fake_preferences(M.make_instance(seed, N=N, **M.FAMILIES[family], **kw), lam)


def run_with_spy(inst, x0, types, prot, seed, lam=LAM, **kw):
    """Run and record every post: (round, dept, claim, exam, slot)."""
    posts = []

    def spy(inst_, x, i, kind, lam_, **k):
        out = real_announce(inst_, x, i, kind, lam_, **k)
        posts.append((k.get('rnd'), i) + tuple(out))
        return out

    with mock.patch.object(P, 'announce', spy):
        res = P.run(inst, x0, types, lam, prot, seed=seed, **kw)
    return res, posts


class TestIntegerRule(unittest.TestCase):
    def _run_with_fractional_claim(self, extra, prot_name):
        """Department 0 posts its honest move but claims V + extra; everyone else is honest."""
        inst = small(0)
        x0 = M.random_start(inst, 1000)

        def fake(inst_, x, i, kind, lam_, **k):
            claim, e, a = real_announce(inst_, x, i, kind, lam_, **k)
            if i == 0 and e is not None:
                return (M.V(inst_, x, e, a) + extra, e, a)
            return (claim, e, a)

        with mock.patch.object(P, 'announce', fake):
            return P.run(inst, x0, ['honest'] * inst['N'], LAM, P.PROTOCOLS[prot_name], seed=0)

    def test_non_integer_claim_is_flagged(self):
        for name in ('VMGM-move-cap', 'VMGM-hist-cap', 'VMGM-hist-quar'):
            res = self._run_with_fractional_claim(10.5, name)
            self.assertIn(0, res.flagged, name)
            self.assertEqual(res.flag_round[0], 1, name)

    def test_integer_claim_is_not_flagged_by_the_rule(self):
        for name in ('VMGM-move-cap', 'VMGM-hist-quar'):
            res = self._run_with_fractional_claim(10, name)        # in scale, whole number
            if 0 in res.flagged:                                  # only a history contradiction may flag it
                self.assertEqual(name, 'VMGM-hist-quar')
                self.assertGreater(res.flag_round[0], 1)

    def test_every_attack_posts_whole_numbers(self):
        """Every (attack, lambda) used in E1-E5 posts only whole numbers, so the rule changes no existing result.
        E1, E2, E4, E5 use lambda = 3 with all attacks; E3 varies lambda but only for exag_consistent and
        exag_stretch (they play truthfully for integer fake preferences)."""
        cases = [(fam, sd, LAM, att) for fam in ('loose', 'tight') for sd in range(4) for att in ALL_ATTACKS]
        cases += [('loose', sd, lam, att) for sd in range(3) for lam in (1.5, 6.0)
                  for att in ('exag_consistent', 'exag_stretch')]
        for fam, sd, lam, att in cases:
            inst = small(sd, fam, lam=lam, pref_spread=0.5 if att == 'exag_stretch' else 1.0)
            x0 = M.random_start(inst, 1000 + sd)
            types = make_types(inst, place_liars(inst, 3, 'random', seed=sd), att)
            res, posts = run_with_spy(inst, x0, types, HQ, sd, lam=lam)
            with self.subTest(fam=fam, sd=sd, lam=lam, att=att):
                for rnd, i, claim, e, a in posts:
                    self.assertTrue(float(claim).is_integer(), (rnd, i, claim))


    def test_naive_exaggeration_with_fractional_lambda_is_caught(self):
        """With lambda = 1.5 a naive exaggerator claims V + 1.5 P, often not a whole number: the rule catches
        it (no experiment uses this combination; this documents the rule's effect)."""
        caught = 0
        for sd in range(3):
            inst = small(sd, lam=1.5)
            x0 = M.random_start(inst, 1000 + sd)
            types = make_types(inst, place_liars(inst, 3, 'random', seed=sd), 'exag_naive')
            res, posts = run_with_spy(inst, x0, types, P.PROTOCOLS['VMGM-move-cap'], sd, lam=1.5)
            fractional = {i for rnd, i, claim, e, a in posts if not float(claim).is_integer()}
            self.assertTrue(fractional <= res.flagged)          # every fractional poster is flagged
            caught += len(fractional)
        self.assertGreater(caught, 0)


class TestRoundBound(unittest.TestCase):
    def test_bound_holds_on_attacked_runs(self):
        for fam in ('loose', 'tight'):
            for sd in range(2):
                inst = small(sd, fam)
                x0 = M.random_start(inst, 1000 + sd)
                for k in (1, 3, 6):
                    liars = place_liars(inst, k, 'adjacent', seed=sd)
                    for att in ALL_ATTACKS + [ALL_ATTACKS]:
                        types = make_types(inst, liars, att)
                        res = P.run(inst, x0, types, LAM, HQ, seed=sd, max_rounds=1000)
                        with self.subTest(fam=fam, sd=sd, k=k, att=att):
                            out = check_all(inst, res, types, HQ)          # raises if the bound fails
                            self.assertLessEqual(res.rounds, out['round_bound'])

    def test_bound_check_can_fail(self):
        inst = small(0)
        x0 = M.random_start(inst, 1000)
        types = make_types(inst, {0}, 'churn')
        res = P.run(inst, x0, types, LAM, HQ, seed=0)
        bound = check_all(inst, res, types, HQ)['round_bound']
        too_long = dataclasses.replace(res, rounds=int(bound) + 1)
        with self.assertRaisesRegex(InvariantError, 'round bound'):
            check_all(inst, too_long, types, HQ)


if __name__ == '__main__':
    unittest.main()
