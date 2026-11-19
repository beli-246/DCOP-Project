"""Tests for which attacks act on DSA (issue #12).

DSA posts no gains, so attacks that act only through announcements (block, hijack,
maxbound) have nothing to act on there. Attacks that act through the moves themselves
(churn, sabotage) are in DSA_ATTACKS and must change the run. Run from the repository root:

    python -m unittest discover -s vmgm/tests -t . -v
"""
import unittest

from vmgm import model as M
from vmgm.liars import make_types, place_liars
from vmgm.protocol import DSA_ATTACKS, run_dsa
from vmgm.tests.test_vmgm import small

LAM = 3.0
SEEDS = range(5)


def honest_and_attacked(seed, family, attack):
    """(inst, honest DSA result, DSA result with one liar of `attack`), same start and seed."""
    inst = small(seed, family)
    x0 = M.random_start(inst, 1000 + seed)
    honest = run_dsa(inst, x0, ['honest'] * inst['N'], LAM, seed=seed)
    types = make_types(inst, place_liars(inst, 1, 'random', seed=seed), attack)
    attacked = run_dsa(inst, x0, types, LAM, seed=seed)
    return inst, honest, attacked


class TestDSAAttacks(unittest.TestCase):

    def test_move_attacks_in_dsa_attacks(self):
        self.assertIn('churn', DSA_ATTACKS)
        self.assertIn('sabotage', DSA_ATTACKS)
        for att in ('block', 'hijack', 'maxbound'):
            self.assertNotIn(att, DSA_ATTACKS)

    def test_churn_acts_on_dsa(self):
        """One churner: the run differs from honest DSA on every seed 0-4, and at least one
        run does not finish (the churner always posts V + gmax > 0, so it keeps moving)."""
        capped = []
        for sd in SEEDS:
            _, honest, attacked = honest_and_attacked(sd, 'loose', 'churn')
            self.assertNotEqual(attacked, honest)
            capped.append(attacked[2])
        self.assertTrue(any(capped))

    def test_sabotage_hurts_dsa(self):
        """One saboteur (moves with -gmax < V < 0): final cost higher than honest DSA on
        most of seeds 0-4 (loose family)."""
        worse = 0
        for sd in SEEDS:
            inst, honest, attacked = honest_and_attacked(sd, 'loose', 'sabotage')
            self.assertNotEqual(attacked[0], honest[0])
            if M.F_cost(inst, attacked[0]) > M.F_cost(inst, honest[0]):
                worse += 1
        self.assertGreaterEqual(worse, 4)

    def test_claim_only_attacks_identical_to_honest(self):
        """block, hijack, maxbound: same final timetable, rounds and capped as honest DSA."""
        for att in ('block', 'hijack', 'maxbound'):
            for fam in ('loose', 'tight'):
                for sd in SEEDS:
                    _, honest, attacked = honest_and_attacked(sd, fam, att)
                    self.assertEqual(attacked, honest, msg=f'{att} {fam} seed {sd}')


if __name__ == '__main__':
    unittest.main()
