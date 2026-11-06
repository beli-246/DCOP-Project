"""Department behaviours: what each department posts each round.

A behaviour returns (claim, e, a): a claimed gain and the move "exam e to slot a",
or (claim, None, None) for "no move".

The pilot attacks are copied unchanged (regression). Two attacks are new:

* sabotage_consistent: the worst liar Result 4 allows. Every round it picks the most
  harmful move (most negative public gain V) for which some claim keeps its history of
  claims consistent and the claim positive, and claims as much as consistency allows.
  It is never flagged, so it spends its whole g_max budget per exam.
* delayed: sabotage_consistent until round `switch_round`, then blocks (huge claims),
  which contradicts its history and gets it flagged. Tests damage done before detection.

Both read the public history scores from the board (assumption A2: the board and every
announcement are public, so any department can recompute them).
"""
from .model import HUGE, V, best_move, moves

PILOT_ATTACKS = ['block', 'hijack', 'maxbound', 'churn', 'sabotage', 'exag_naive', 'exag_consistent']
NEW_ATTACKS = ['sabotage_consistent', 'delayed']
ALL_ATTACKS = PILOT_ATTACKS + NEW_ATTACKS
# exag_stretch: truthful play for g~ = min(gmax, lam*(g - min g)); undetectable by Result 3.
# Only meaningful when true preferences do not fill the scale (make_instance pref_spread < 1), so E3 only.
E3_ATTACKS = ['exag_stretch']


def feasible_r_range(scores, cur_slot, new_slot, gmax):
    """Interval [lo, hi] of private parts r that keep an exam's history consistent, or None.

    scores: slot -> score for this exam (the board's history), with cur_slot in scores.
    Moving cur_slot -> new_slot with private part r sets score(new_slot) = score(cur) - r.
    """
    s_cur = scores[cur_slot]
    if new_slot in scores:
        r = s_cur - scores[new_slot]
        return (r, r) if abs(r) <= gmax else None
    lo_s, hi_s = min(scores.values()), max(scores.values())
    # need max(hi_s, s_new) - min(lo_s, s_new) <= gmax  <=>  hi_s - gmax <= s_new <= lo_s + gmax
    s_lo, s_hi = hi_s - gmax, lo_s + gmax
    if s_lo > s_hi:
        return None
    lo, hi = max(s_cur - s_hi, -gmax), min(s_cur - s_lo, gmax)
    return (lo, hi) if lo <= hi else None


def _sabotage_consistent(inst, x, i, board):
    gmax = inst['gmax']
    best = None
    for e, a in moves(inst, x, i):
        scores = board.scores[e]
        if x[e] not in scores:
            continue
        rr = feasible_r_range(scores, x[e], a, gmax)
        if rr is None:
            continue
        v = V(inst, x, e, a)
        claim = v + rr[1]
        if v < 0 and claim > 0 and (best is None or v < best[0]):
            best = (v, claim, e, a)
    if best is None:
        return (0, None, None)
    return (best[1], best[2], best[3])


def announce(inst, x, i, kind, lam, board=None, rnd=0, switch_round=20):
    """Return (claim, e, a) posted by department i. kind='honest' or an attack name."""
    g, gmax = inst['g'], inst['gmax']
    if kind == 'honest':
        return best_move(inst, x, i, g)
    if kind == 'exag_naive':                      # T1a: post own utility gain V + lam*P
        return best_move(inst, x, i, g, lam)
    if kind == 'exag_consistent':                 # T1b: truthful for fake g~ = min(gmax, lam*g)
        return best_move(inst, x, i, inst['gtilde'])
    if kind == 'exag_stretch':
        return best_move(inst, x, i, inst['gtilde_stretch'])
    if kind == 'hijack':                          # T2a: inflate by HUGE
        v, e, a = best_move(inst, x, i, g, lam)
        return (v + HUGE, e, a) if e is not None else (0, None, None)
    if kind == 'maxbound':                        # T2b: claim V + gmax for own selfish best move
        v, e, a = best_move(inst, x, i, g, lam)
        return (V(inst, x, e, a) + gmax, e, a) if e is not None else (0, None, None)
    if kind == 'block':                           # T3a: always claim HUGE
        v, e, a = best_move(inst, x, i, g, lam)
        return (HUGE, e, a)
    if kind == 'churn':                           # T3b: max-V move every round, claim V + gmax
        best = max(((V(inst, x, e, a), e, a) for e, a in moves(inst, x, i)), key=lambda t: t[0])
        return (best[0] + gmax, best[1], best[2])
    if kind == 'sabotage':                        # T4: most harmful move with -gmax < V < 0
        c = [(V(inst, x, e, a), e, a) for e, a in moves(inst, x, i)]
        c = [t for t in c if -gmax < t[0] < 0]
        if not c:
            return (0, None, None)
        v, e, a = min(c)
        return (v + gmax, e, a)
    if kind == 'sabotage_consistent':
        return _sabotage_consistent(inst, x, i, board)
    if kind == 'delayed':
        if rnd < switch_round:
            return _sabotage_consistent(inst, x, i, board)
        return announce(inst, x, i, 'block', lam)
    raise ValueError(kind)
