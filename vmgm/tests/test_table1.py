"""Every claim in Table 1 of the report (issue #7): which check flags which attack, and when.

| ID  | attack (code name)                 | one-post check  | history check  |
| T1a | exag_naive                         | if |lam P| > gmax | if incons.   |
| T1b | exag_consistent                    | never           | never          |
| T1c | exag_stretch                       | never           | never          |
| T2a | hijack                             | yes             | yes            |
| T2b | maxbound                           | never           | if incons.     |
| T3a | block                              | yes             | yes            |
| T3b | churn                              | never           | if incons.     |
| T4  | sabotage                           | never           | if incons.     |
| T5  | sabotage_consistent                | never           | never          |
| T6  | delayed                            | from round 20   | from round 20  |

Run from the repository root:  python -m unittest discover -s vmgm/tests -t . -v
"""
import unittest
from unittest import mock

from vmgm import model as M
from vmgm import protocol as P
from vmgm.attacks import announce as real_announce
from vmgm.liars import make_types
from vmgm.tests.test_history_oracle import consistent

LAM = 3.0
MOVE_CAP, HIST_CAP, HIST_QUAR = (P.PROTOCOLS[n] for n in ('VMGM-move-cap', 'VMGM-hist-cap', 'VMGM-hist-quar'))
CASES = [(fam, sd) for fam in ('loose', 'tight') for sd in range(5)]


def instance(att, fam, sd):
    if att == 'exag_stretch':                       # needs room on the scale (E3 setting)
        return M.add_fake_preferences(M.make_instance(sd, pref_spread=0.25, **M.FAMILIES[fam]), LAM)
    return M.add_fake_preferences(M.make_instance(sd, **M.FAMILIES[fam]), LAM)


def run_with_spy(att, fam, sd, prot, liar=0, **kw):
    """Run with one liar (department `liar`) and record its posts: (round, claim, exam, from, to, V)."""
    inst = instance(att, fam, sd)
    x0 = M.random_start(inst, 1000 + sd)
    types = make_types(inst, {liar}, att)
    posts = []

    def spy(inst_, x, i, kind, lam, **k):
        out = real_announce(inst_, x, i, kind, lam, **k)
        if i == liar:
            claim, e, a = out
            posts.append((k.get('rnd'), claim, e, None if e is None else x[e], a,
                          None if e is None else M.V(inst_, x, e, a)))
        return out

    with mock.patch.object(P, 'announce', spy):
        res = P.run(inst, x0, types, LAM, prot, seed=sd, **kw)
    return inst, res, posts


class TestOnePostCheck(unittest.TestCase):
    def test_one_post_never(self):
        for att in ('exag_consistent', 'exag_stretch', 'maxbound', 'churn', 'sabotage', 'sabotage_consistent'):
            for fam, sd in CASES:
                inst, res, posts = run_with_spy(att, fam, sd, MOVE_CAP)
                with self.subTest(att=att, fam=fam, sd=sd):
                    self.assertNotIn(0, res.flagged)
                    for rnd, claim, e, frm, to, v in posts:
                        if e is not None:
                            self.assertLessEqual(abs(claim - v), inst['gmax'])

    def test_one_post_yes_block(self):
        for fam, sd in CASES:
            _, res, _ = run_with_spy('block', fam, sd, MOVE_CAP)
            self.assertEqual(res.flag_round.get(0), 1, (fam, sd))

    def test_one_post_yes_hijack(self):
        """Flagged in the first round in which it posts a move; never if it never posts one."""
        for fam, sd in CASES:
            _, res, posts = run_with_spy('hijack', fam, sd, MOVE_CAP)
            first = next((rnd for rnd, claim, e, *_ in posts if e is not None), None)
            self.assertEqual(res.flag_round.get(0), first, (fam, sd))

    def test_one_post_naive_exaggeration(self):
        """Flagged in the first round with |claim - V| = |lam P| > gmax; never if there is none."""
        seen = 0
        for fam, sd in CASES:
            inst, res, posts = run_with_spy('exag_naive', fam, sd, MOVE_CAP)
            first = next((rnd for rnd, claim, e, frm, to, v in posts
                          if e is not None and abs(claim - v) > inst['gmax']), None)
            self.assertEqual(res.flag_round.get(0), first, (fam, sd))
            seen += first is not None
        self.assertGreater(seen, 0)                       # some runs do exaggerate beyond the scale


class TestHistoryCheck(unittest.TestCase):
    def test_history_never(self):
        for att in ('exag_consistent', 'exag_stretch', 'sabotage_consistent'):
            for prot in (HIST_CAP, HIST_QUAR):
                for fam, sd in CASES:
                    _, res, _ = run_with_spy(att, fam, sd, prot)
                    with self.subTest(att=att, prot=prot['response'], fam=fam, sd=sd):
                        self.assertNotIn(0, res.flagged)

    def test_history_if_inconsistent(self):
        """When T1a, T2b, T3b or T4 is flagged in round t only by the history check, its claims about that
        exam up to round t - 1 are consistent and adding the round-t claim makes them inconsistent (checked
        with the independent oracle). Flags from the one-post check are classified separately."""
        reasons = {'history': 0, 'one-post': 0, 'no-move claim': 0}
        for att in ('exag_naive', 'maxbound', 'churn', 'sabotage'):
            for fam, sd in CASES:
                inst, res, posts = run_with_spy(att, fam, sd, HIST_CAP)
                if 0 not in res.flag_round:
                    continue
                t = res.flag_round[0]
                rnd, claim, e, frm, to, v = next(p for p in posts if p[0] == t)
                if e is None:
                    reasons['no-move claim'] += 1
                    continue
                if abs(claim - v) > inst['gmax']:
                    reasons['one-post'] += 1
                    continue
                before = [(f, a, c - vv) for r_, c, ee, f, a, vv in posts if r_ < t and ee == e]
                with self.subTest(att=att, fam=fam, sd=sd, round=t):
                    self.assertTrue(consistent(before, inst['gmax']))
                    self.assertFalse(consistent(before + [(frm, to, claim - v)], inst['gmax']))
                reasons['history'] += 1
        self.assertGreater(reasons['history'], 10)

    def test_history_flags_churn_under_quarantine(self):
        flagged = total = 0
        for fam in ('loose', 'tight'):
            for sd in range(10):
                _, res, _ = run_with_spy('churn', fam, sd, HIST_QUAR)
                total += 1
                flagged += 0 in res.flagged
        self.assertGreaterEqual(flagged / total, 0.95)


class TestDelayed(unittest.TestCase):
    def test_delayed_from_round_20(self):
        reached = 0
        for prot in (MOVE_CAP, HIST_QUAR):
            for fam, sd in CASES:
                _, res, _ = run_with_spy('delayed', fam, sd, prot)
                with self.subTest(prot=prot['audit'], fam=fam, sd=sd):
                    if 0 in res.flag_round:
                        self.assertEqual(res.flag_round[0], 20)
                    if res.rounds >= 20:
                        self.assertEqual(res.flag_round.get(0), 20)
                        reached += 1
        self.assertGreater(reached, 0)


if __name__ == '__main__':
    unittest.main()
