"""Colluding liars (issue #8, attack T7, experiment E6).

Run from the repository root:  python -m unittest discover -s vmgm/tests -t . -v
"""
import random
import unittest
from unittest import mock

from vmgm import model as M
from vmgm import protocol as P
from vmgm.attacks import announce as real_announce
from vmgm.attacks import honest_harm
from vmgm.invariants import check_all
from vmgm.liars import make_types, place_liars

LAM = 3.0


def small(seed, family='loose'):
    return M.add_fake_preferences(M.make_instance(seed, **M.FAMILIES[family]), LAM)


class TestCollusion(unittest.TestCase):
    def test_honest_harm_matches_burden(self):
        """honest_harm = change of the total burden of the departments outside the coalition."""
        rng = random.Random(0)
        for sd in range(3):
            inst = small(sd)
            x = M.random_start(inst, 1000 + sd)
            coalition = place_liars(inst, 3, 'adjacent', seed=sd)
            outside = [i for i in range(inst['N']) if i not in coalition]
            for _ in range(60):
                j = rng.choice(sorted(coalition))
                e = rng.choice(inst['exams'][j])
                a = rng.randrange(inst['S'])
                y = list(x)
                y[e] = a
                before = sum(M.burden(inst, x, i) for i in outside)
                after = sum(M.burden(inst, y, i) for i in outside)
                self.assertAlmostEqual(honest_harm(inst, x, e, a, coalition), after - before)

    def test_colluding_neighbours_never_both_post(self):
        for sd in range(3):
            inst = small(sd)
            x0 = M.random_start(inst, 1000 + sd)
            liars = place_liars(inst, 3, 'adjacent', seed=sd)
            inst['coalition'] = set(liars)
            types = make_types(inst, liars, 'collude')
            posts = {}

            def spy(inst_, x, i, kind, lam, **k):
                out = real_announce(inst_, x, i, kind, lam, **k)
                if out[1] is not None and i in liars:
                    posts.setdefault(k.get('rnd'), []).append(i)
                return out

            with mock.patch.object(P, 'announce', spy):
                P.run(inst, x0, types, LAM, P.PROTOCOLS['VMGM-hist-quar'], seed=sd)
            self.assertTrue(posts)                                  # they do act
            for rnd, movers in posts.items():
                for a in movers:
                    for b in movers:
                        self.assertFalse(a != b and b in inst['nbr'][a], (rnd, a, b))

    def test_consistent_colluders_never_flagged_and_checks_hold(self):
        for name in ('VMGM-hist-quar', 'VMGM-hist-soft'):
            for sd in range(3):
                inst = small(sd)
                x0 = M.random_start(inst, 1000 + sd)
                for k in (2, 3, 6):
                    liars = place_liars(inst, k, 'adjacent', seed=sd)
                    inst['coalition'] = set(liars)
                    for att in ('collude', 'spite_consistent'):
                        types = make_types(inst, liars, att)
                        res = P.run(inst, x0, types, LAM, P.PROTOCOLS[name], seed=sd)
                        with self.subTest(name=name, sd=sd, k=k, att=att):
                            self.assertFalse(res.flagged)
                            out = check_all(inst, res, types, P.PROTOCOLS[name])
                            self.assertLess(out['dmg_total'], 1.0)

    def test_deterministic(self):
        inst = small(1)
        x0 = M.random_start(inst, 1001)
        liars = place_liars(inst, 3, 'adjacent', seed=1)
        inst['coalition'] = set(liars)
        types = make_types(inst, liars, 'collude')
        a = P.run(inst, x0, types, LAM, P.PROTOCOLS['MGM'], seed=1)
        b = P.run(inst, x0, types, LAM, P.PROTOCOLS['MGM'], seed=1)
        self.assertEqual(a.x, b.x)
        self.assertEqual(a.trace, b.trace)


if __name__ == '__main__':
    unittest.main()
