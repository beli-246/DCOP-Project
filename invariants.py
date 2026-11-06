"""Automatic checks of the proven results on every run.

Which checks apply depends on the protocol:
  * no_false_flags        - any protocol with an audit (Result 1 / Result 2).
  * direct_damage         - audit == 'hist' (Result 4, unflagged part); with quarantine
                            also over the whole run.
  * potential_decreases   - hist + quarantine (proposed Result 5, termination).
  * global_bound          - hist + quarantine (proposed Result 6:
                            F_final <= F_start + 2 * gmax * (number of liar exams)).
  * finished              - hist + quarantine (follows from Result 5; a failure here with the
                            potential check passing only means the round limit was too small).

`check_all` raises InvariantError with a description on the first failure.
"""
from .model import F_cost, H_cost

EPS = 1e-9


class InvariantError(AssertionError):
    pass


def fake_preferences(scores_by_exam):
    """g~ from history scores: g~(e, s) = score(e, s) - min score of e (so it lies in [0, gmax])."""
    out = {}
    for e, sc in scores_by_exam.items():
        lo = min(sc.values())
        out[e] = {s: v - lo for s, v in sc.items()}
    return out


def no_false_flags(res, types):
    bad = [i for i in res.flagged if types[i] == 'honest']
    if bad:
        raise InvariantError(f'honest departments flagged: {bad}')


def direct_damage(inst, res, liars):
    """Per liar exam: student cost added by its own moves.

    Returns (worst_unflagged, worst_total) as fractions of gmax:
      unflagged: sum of -V over the exam's executed moves while its owner was unflagged,
      total:     the same over all its executed moves.
    """
    gmax = inst['gmax']
    unfl = {e: 0.0 for j in liars for e in inst['exams'][j]}
    tot = dict(unfl)
    for rnd in res.trace:
        for m in rnd:
            if m['e'] in tot:
                tot[m['e']] += -m['v']
                if m['unflagged']:
                    unfl[m['e']] += -m['v']
    if not tot:
        return 0.0, 0.0
    return max(unfl.values()) / gmax, max(tot.values()) / gmax


def potential_series(inst, res, types):
    """Phi_t = H + G_honest + sum over liars unflagged after round t of g~_j(x_t).

    g~_j is fixed once per liar: from its history scores at flag time (or at the end if never
    flagged), so it explains every claim it made while unflagged.
    """
    g = inst['g']
    liars = [i for i, t in enumerate(types) if t != 'honest']
    honest_exams = [e for i, t in enumerate(types) if t == 'honest' for e in inst['exams'][i]]
    gt = {}
    for j in liars:
        sc = res.flag_scores.get(j)
        if sc is None:
            sc = {e: res.end_scores[e] for e in inst['exams'][j]}
        gt[j] = fake_preferences(sc)

    def phi(x, flagged_now):
        val = H_cost(inst, x) + sum(g[e][x[e]] for e in honest_exams)
        for j in liars:
            if j in flagged_now:
                continue
            for e in inst['exams'][j]:
                if x[e] not in gt[j][e]:
                    raise InvariantError(f'unflagged liar {j}: exam {e} in slot {x[e]} with no history score')
                val += gt[j][e][x[e]]
        return val

    x = list(res.x0)
    series = [phi(x, set())]
    for t, rnd in enumerate(res.trace, start=1):
        for m in rnd:
            x[m['e']] = m['to']
        flagged_now = {j for j, r in res.flag_round.items() if r <= t}
        series.append(phi(x, flagged_now))
    return series


def potential_decreases(inst, res, types):
    s = potential_series(inst, res, types)
    for t in range(1, len(s)):
        if not s[t] < s[t - 1] - EPS:
            raise InvariantError(f'potential did not decrease in round {t}: {s[t-1]} -> {s[t]}')
    return s


def global_bound(inst, res, types):
    n_liar_exams = sum(len(inst['exams'][i]) for i, t in enumerate(types) if t != 'honest')
    f0, f1 = F_cost(inst, res.x0), F_cost(inst, res.x)
    bound = f0 + 2 * inst['gmax'] * n_liar_exams
    if f1 > bound + EPS:
        raise InvariantError(f'global bound violated: F_final={f1} > F_start + 2*gmax*{n_liar_exams} = {bound}')
    return f1, bound


def check_all(inst, res, types, protocol):
    """Run every check that applies to this protocol. Returns a dict of measured values."""
    out = {}
    liars = [i for i, t in enumerate(types) if t != 'honest']
    if protocol['audit'] != 'none':
        no_false_flags(res, types)
    if protocol['audit'] == 'hist':
        unfl, tot = direct_damage(inst, res, liars)
        out['dmg_unflagged'], out['dmg_total'] = unfl, tot
        if unfl >= 1.0:
            raise InvariantError(f'Result 4 violated: unflagged direct damage {unfl:.3f} * gmax per exam')
        if protocol['response'] == 'quarantine':
            if tot >= 1.0:
                raise InvariantError(f'Result 4 (quarantine) violated: direct damage {tot:.3f} * gmax per exam')
            potential_decreases(inst, res, types)
            out['F_final'], out['F_bound'] = global_bound(inst, res, types)
            if res.capped:
                raise InvariantError(f'hist+quarantine run did not finish in {res.rounds} rounds '
                                     '(potential decreased every round, so raise max_rounds)')
    return out
