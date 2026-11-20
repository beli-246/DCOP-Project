"""Result 2 against an independent oracle: the history check flags exactly the inconsistent histories.

`Board.check` is compared with a linear-programming oracle that shares no code with it: a list of
claims (a, a', r), each meaning "g(a) - g(a') = r", is consistent iff some real g with values in
[0, gmax] satisfies all of them. The two must agree after every single claim, on thousands of random
claim sequences built the way `run()` builds them (posted recording, moves that may or may not run).

Run from the repository root:  python -m unittest discover -s vmgm/tests -t . -v
"""
import random
import sys
import unittest
from unittest import mock

import numpy as np
from scipy.optimize import linprog

from vmgm import model as M
from vmgm.liars import make_types, pilot_liars
from vmgm.protocol import PROTOCOLS, Board, run
from vmgm.tests.test_vmgm import LAM, small

MODES = ('truthful', 'noisy', 'adversarial', 'repeat')


# ------------------------------------------------------------------ the oracle (independent of Board)
def consistent(claims, gmax):
    """claims: list of (from_slot, to_slot, r). True iff some g in [0, gmax] explains all of them."""
    slots = sorted({s for a, b, _ in claims for s in (a, b)})
    if not slots:
        return True
    idx = {s: i for i, s in enumerate(slots)}
    A = np.zeros((len(claims), len(slots)))
    b = np.zeros(len(claims))
    for row, (a, a2, r) in enumerate(claims):
        A[row, idx[a]] += 1
        A[row, idx[a2]] -= 1
        b[row] = r
    res = linprog(np.zeros(len(slots)), A_eq=A, b_eq=b, bounds=[(0, gmax)] * len(slots), method='highs')
    return res.status == 0


# ------------------------------------------------------------------ claim generator
def hidden_preferences(rng, S, gmax):
    """Integer preferences in 0..gmax. Half the time the full range is used (min 0, max gmax), so
    truthful claims sit exactly on the range limit and a +1 of noise pushes them over it."""
    g = [rng.randint(0, gmax) for _ in range(S)]
    if rng.random() < 0.5:
        lo, hi = rng.sample(range(S), 2)
        g[lo], g[hi] = 0, gmax
    return g


def next_claim(rng, mode, g, cur, S, gmax, claims):
    """One claim (cur, a, r) about moving from the current slot `cur`."""
    if mode == 'repeat':
        # re-claim an earlier pair that starts (or ends) at the current slot, same or different r
        old = [(a, r) for f, a, r in claims if f == cur] + [(f, -r) for f, a, r in claims if a == cur]
        if old:
            a, r = rng.choice(old)
            if rng.random() < 0.5:
                r += rng.choice((-2, -1, 1, 2))
            return cur, a, r
        mode = 'truthful'
    a = rng.choice([s for s in range(S) if s != cur])
    truth = g[cur] - g[a]
    if mode == 'truthful':
        return cur, a, truth
    if mode == 'noisy':
        return cur, a, truth + (rng.randint(-3, 3) if rng.random() < 0.3 else 0)
    if mode == 'adversarial':
        return cur, a, rng.randint(-gmax, gmax)
    raise ValueError(mode)


def gen_trial(rng, modes, steps=40):
    """Random parameters and a full claim sequence, built as in run() with posted recording.

    The sequence does not depend on the board's answers (claims start at the current slot, and the
    current slot changes with probability 0.6 whether or not the claim is consistent), so it can be
    replayed both against the board and against the oracle.
    """
    S = rng.randint(4, 10)
    gmax = rng.choice((10, 50))
    g = hidden_preferences(rng, S, gmax)
    s0 = rng.randrange(S)
    mix = len(modes) > 1 and rng.random() < 0.5        # mix modes inside this trial
    trial_mode = rng.choice(modes)
    cur, claims = s0, []
    for _ in range(steps):
        mode = rng.choice(modes) if mix else trial_mode
        claims.append(next_claim(rng, mode, g, cur, S, gmax, claims))
        if rng.random() < 0.6:
            cur = claims[-1][1]
    return gmax, s0, claims


def replay(test, gmax, s0, claims, stats=None):
    """Feed claims one by one to a Board, asserting ok == oracle(prefix) at every step.

    Stops at the first flag, as run() does. Returns the index of the flagging claim or None.
    """
    board = Board([s0])
    for t, (cur, a, r) in enumerate(claims):
        ok, new = board.check(0, cur, a, r, gmax)
        expected = consistent(claims[:t + 1], gmax)
        if stats is not None:
            stats['claims'] += 1
        if ok != expected:
            test.fail(f'board says {ok}, oracle says {expected}; gmax={gmax}, start={s0}, '
                      f'claims={claims[:t + 1]}')
        if not ok:
            if stats is not None:
                stats['contradictions'] += 1
            return t
        board.scores[0][a] = new                        # posted recording
    return None


def first_infeasible(claims, gmax):
    """Oracle only: index of the first prefix with no explaining g, or None."""
    for t in range(len(claims)):
        if not consistent(claims[:t + 1], gmax):
            return t
    return None


class TestHistoryOracle(unittest.TestCase):
    def test_board_matches_oracle_random(self):
        stats = dict(trials=0, claims=0, contradictions=0)
        per_mode = {m: 0 for m in MODES + ('mixed',)}
        rng = random.Random(20261120)
        for _ in range(5000):
            gmax, s0, claims = gen_trial(rng, MODES)
            replay(self, gmax, s0, claims, stats)
            stats['trials'] += 1
        # the generator must produce many contradictions, of every kind, or the test is vacuous
        self.assertGreater(stats['contradictions'], 1000)
        print(f"\n[history oracle] {stats['trials']} trials, {stats['claims']} claims compared, "
              f"{stats['contradictions']} contradictions, 0 mismatches", file=sys.stderr)

    def test_truthful_never_flagged_oracle(self):
        rng = random.Random(7)
        for _ in range(1000):
            gmax, s0, claims = gen_trial(rng, ('truthful',))
            self.assertTrue(consistent(claims, gmax))
            self.assertIsNone(replay(self, gmax, s0, claims))

    def test_first_contradiction_is_caught_immediately(self):
        rng = random.Random(11)
        caught = 0
        for _ in range(1500):
            gmax, s0, claims = gen_trial(rng, ('adversarial', 'noisy', 'repeat'))
            t_oracle = first_infeasible(claims, gmax)
            t_board = replay(self, gmax, s0, claims)
            self.assertEqual(t_board, t_oracle, claims)
            caught += t_board is not None
        self.assertGreater(caught, 1000)

    def test_edge_cases(self):
        """(claims, gmax, start slot, expected consistency of the whole list); the board is fed the
        same claims, so it must flag the last one exactly when the list is inconsistent."""
        cases = [
            ([(0, 1, 0)], 50, 0, True),                                # equal scores, r = 0
            ([(0, 1, 0), (1, 0, 0)], 50, 0, True),                     # r = 0 both ways
            ([(0, 1, 0), (1, 0, 1)], 50, 0, False),                    # equal, then not equal
            ([(0, 1, 50)], 50, 0, True),                               # one claim of exactly gmax
            ([(0, 1, 51)], 50, 0, False),                              # one claim of gmax + 1
            ([(0, 1, -51)], 50, 0, False),
            ([(0, 1, 30), (1, 2, 20)], 50, 0, True),                   # range exactly gmax over 3 slots
            ([(0, 1, 30), (1, 2, 21)], 50, 0, False),                  # range gmax + 1 over 3 slots
            ([(0, 1, -30), (1, 2, -20), (2, 3, 50)], 50, 0, True),     # back to the bottom
            ([(0, 1, 30), (1, 0, -30)], 50, 0, True),                  # revisit start, consistent
            ([(0, 1, 30), (1, 0, -29)], 50, 0, False),                 # revisit start, contradiction
            ([(0, 1, 30), (1, 2, 5), (2, 0, -35)], 50, 0, True),       # cycle back to start
            ([(0, 1, 30), (1, 2, 5), (2, 0, -34)], 50, 0, False),
            ([(0, 1, 10), (0, 1, 10)], 50, 0, True),                   # same pair, same r
            ([(0, 1, 10), (0, 1, 11)], 50, 0, False),                  # same pair, different r
            ([(3, 1, 10), (3, 2, -10)], 10, 3, False),                  # range 20 > gmax 10
            ([(3, 1, 5), (3, 2, -5), (3, 1, 5)], 10, 3, True),         # range exactly gmax 10
        ]
        for claims, gmax, s0, expected in cases:
            with self.subTest(claims=claims, gmax=gmax):
                self.assertEqual(consistent(claims, gmax), expected)
                t = replay(self, gmax, s0, claims)
                self.assertEqual(t, None if expected else len(claims) - 1)

    def test_through_run(self):
        """VMGM-hist-cap with k = 3 liars: every Board.check call made inside run() agrees with the
        oracle, flagged liars' scores at flag time and unflagged liars' final scores are consistent."""
        real_check = Board.check
        flagged_total = 0
        for att in ('churn', 'sabotage', 'maxbound', 'exag_naive'):
            for sd in range(4):
                inst = small(sd)
                gmax = inst['gmax']
                x0 = M.random_start(inst, 1000 + sd)
                liars = pilot_liars(inst, 3, sd)
                types = make_types(inst, liars, att)
                calls = []

                def logged(board, e, cur, a, r, gm, _calls=calls):
                    out = real_check(board, e, cur, a, r, gm)
                    _calls.append((e, cur, a, r, out))
                    return out

                with mock.patch.object(Board, 'check', logged):
                    res = run(inst, x0, types, LAM, PROTOCOLS['VMGM-hist-cap'], seed=sd)

                with self.subTest(att=att, seed=sd):
                    # 1. every check in the run agrees with the oracle on (recorded claims + this claim)
                    recorded = {e: [] for e in range(inst['E'])}
                    for e, cur, a, r, (ok, new) in calls:
                        if new is None:                     # current slot has no score: nothing to check
                            continue
                        self.assertEqual(ok, consistent(recorded[e] + [(cur, a, r)], gmax),
                                         (e, recorded[e], (cur, a, r)))
                        if ok:
                            recorded[e].append((cur, a, r))
                    # 2. the board never recorded anything inconsistent, for flagged and unflagged liars
                    for j in liars:
                        if j in res.flagged:
                            flagged_total += 1
                            scores_by_exam = res.flag_scores[j]
                        else:
                            scores_by_exam = {e: res.end_scores[e] for e in inst['exams'][j]}
                        for e, sc in scores_by_exam.items():
                            claims = [(x0[e], s, sc[x0[e]] - v) for s, v in sc.items() if s != x0[e]]
                            self.assertTrue(consistent(claims, gmax), (j, e, sc))
        self.assertGreater(flagged_total, 0)


if __name__ == '__main__':
    unittest.main()
