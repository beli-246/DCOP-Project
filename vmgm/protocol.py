"""MGM, V-MGM variants, RP-MGM and DSA, with a full trace of every run.

The round logic in `run` is the pilot's (prelim.run) with three additions:
  1. a Board that keeps each exam's history scores (always maintained, since the board
     is public; it is used for flagging only when audit == 'hist'),
  2. a trace (executed moves, flags, the history scores at flag time) for the invariant checks,
  3. protocol['record']: 'posted' (pilot behaviour: every consistent claim is recorded,
     even if its move does not run) or 'executed' (only claims whose move runs are recorded,
     which is how Result 2 is worded in the proposal). The team must pick one; both keep
     Results 1, 2 and 4 true.
"""
import copy
import random
from dataclasses import dataclass, field

from .attacks import announce
from .model import V

PROTOCOLS = {
    'MGM':            dict(priority='gain', audit='none', response='cap'),
    'VMGM-move-cap':  dict(priority='gain', audit='move', response='cap'),
    'VMGM-move-quar': dict(priority='gain', audit='move', response='quarantine'),
    'VMGM-hist-cap':  dict(priority='gain', audit='hist', response='cap'),
    'VMGM-hist-quar': dict(priority='gain', audit='hist', response='quarantine'),
    'VMGM-hist-soft': dict(priority='gain', audit='hist', response='soft'),
    'RP-MGM':         dict(priority='random', audit='none', response='cap'),
}


def frozen_preferences(scores_by_exam, gmax):
    """Soft quarantine: each exam's preference implied by its consistent history, frozen when flagged.
    Slot s with a score: score(s) - min score (in [0, gmax]); slots never claimed about: gmax (the worst)."""
    out = {}
    for e, sc in scores_by_exam.items():
        lo = min(sc.values())
        out[e] = {s: v - lo for s, v in sc.items()}
    return out


class Board:
    """Public history scores: scores[e][slot], starting with score 0 at the starting slot."""

    def __init__(self, x0):
        self.scores = {e: {x0[e]: 0} for e in range(len(x0))}

    def check(self, e, cur, a, r, gmax):
        """Consistency of one more claim 'moving e from cur to a has private part r'.

        Returns (ok, new_score). If cur has no score (only possible after the owner was
        flagged and quarantined moves ran), returns (True, None): nothing can be checked.
        """
        P = self.scores[e]
        s = P.get(cur)
        if s is None:
            return True, None
        new = s - r
        if a in P:
            return P[a] == new, new
        vals = list(P.values()) + [new]
        return max(vals) - min(vals) <= gmax, new


@dataclass
class RunResult:
    x: list
    rounds: int
    flagged: set
    flag_round: dict
    capped: bool                         # True = did not finish (round limit or freeze)
    x0: list = None
    trace: list = field(default_factory=list)          # per round: list of executed moves
    flag_scores: dict = field(default_factory=dict)    # dept -> {e: scores at flag time}
    end_scores: dict = field(default_factory=dict)     # e -> scores at end of run

    def as_pilot_tuple(self):
        return self.x, self.rounds, self.flagged, self.flag_round, self.capped


def run(inst, x0, types, lam, protocol, max_rounds=300, seed=0, switch_round=20, forced_quarantine=None):
    """Run one protocol. types[i] is 'honest' or an attack name.

    forced_quarantine: {dept: round} for the quarantine control experiment. From that round on
    the department is treated as quarantined (priority capped at V, or the soft-quarantine priority
    with response 'soft') although it was never flagged. Used with all-honest types to measure the
    cost of quarantine itself. Forced departments are not added to `flagged`, and the invariant
    checks do not apply to such runs.

    Responses to a flagged department: 'cap' (keep the capped priority min(claim, V + gmax)),
    'quarantine' (min(claim, V): only moves that lower the student cost), 'soft' (min(claim,
    V + g~(from) - g~(to)) with g~ its preferences frozen at flag time, see frozen_preferences).
    """
    rng = random.Random(seed)
    x = list(x0)
    gmax = inst['gmax']
    record = protocol.get('record', 'posted')
    forced = forced_quarantine or {}
    board = Board(x0)
    flagged, flag_round, flag_scores = set(), {}, {}
    soft_g = {}                          # dept -> {exam: {slot: frozen preference}} (response 'soft')
    trace = []

    def flag(i, r):
        if i not in flagged:
            flagged.add(i)
            flag_round[i] = r
            flag_scores[i] = {e: dict(board.scores[e]) for e in inst['exams'][i]}
            soft_g[i] = frozen_preferences(flag_scores[i], gmax)

    for r in range(1, max_rounds + 1):
        ann = {i: announce(inst, x, i, types[i], lam, board=board, rnd=r, switch_round=switch_round)
               for i in range(inst['N'])}
        eff, vals, pending = {}, {}, {}
        for i, (claim, e, a) in ann.items():
            v = 0 if e is None else V(inst, x, e, a)
            vals[i] = v
            viol = (claim > 0) if e is None else (claim - v > gmax or claim - v < -gmax)
            # Claims must be whole numbers: honest claims always are (V and g are integers), and integer
            # claims keep the potential Phi an integer, which bounds the number of rounds (Result 5).
            viol = viol or not float(claim).is_integer()
            if e is not None and not viol:
                ok, new = board.check(e, x[e], a, claim - v, gmax)
                if protocol['audit'] == 'hist' and not ok:
                    viol = True
                if ok and new is not None:
                    if record == 'posted':
                        board.scores[e][a] = new
                    else:
                        pending[i] = (e, a, new)
            if protocol['audit'] == 'none':
                eff[i] = claim if e is not None or protocol['priority'] == 'gain' else 0
                continue
            if viol:
                flag(i, r)
            quarantined = i in flagged or (i in forced and r >= forced[i])
            if quarantined and i not in soft_g:          # forced (control): freeze from the board now
                soft_g[i] = frozen_preferences({ex: dict(board.scores[ex]) for ex in inst['exams'][i]}, gmax)
            if e is None:
                eff[i] = 0
            elif quarantined and protocol['response'] == 'quarantine':
                eff[i] = min(claim, v)
            elif quarantined and protocol['response'] == 'soft':
                g = soft_g[i][e]
                eff[i] = min(claim, v + g.get(x[e], gmax) - g.get(a, gmax))
            else:
                eff[i] = min(claim, v + gmax)
        if protocol['priority'] == 'gain':
            eligible = [i for i in ann if eff[i] > 0]
            winners = [i for i in eligible if ann[i][1] is not None and
                       all(eff[i] > eff[j] or (eff[i] == eff[j] and i < j) for j in inst['nbr'][i])]
        else:
            eligible = [i for i in ann if ann[i][1] is not None and eff[i] > 0]
            tok = {i: rng.random() for i in eligible}
            winners = [i for i in eligible if all(tok[i] > tok[j] for j in inst['nbr'][i] if j in tok)]
        if not eligible:
            return _result(x, r, flagged, flag_round, False, x0, trace, flag_scores, board)
        if not winners:                                  # deterministic freeze
            return _result(x, r, flagged, flag_round, True, x0, trace, flag_scores, board)
        executed = []
        for i in winners:
            claim, e, a = ann[i]
            executed.append(dict(dept=i, e=e, frm=x[e], to=a, claim=claim, v=vals[i],
                                 eff=eff[i], unflagged=i not in flagged))
            if i in pending:
                pe, pa, new = pending[i]
                board.scores[pe][pa] = new
            x[e] = a
        trace.append(executed)
    return _result(x, max_rounds, flagged, flag_round, True, x0, trace, flag_scores, board)


def _result(x, r, flagged, flag_round, capped, x0, trace, flag_scores, board):
    return RunResult(x=x, rounds=r, flagged=flagged, flag_round=flag_round, capped=capped, x0=list(x0),
                     trace=trace, flag_scores=flag_scores, end_scores=copy.deepcopy(board.scores))


DSA_ATTACKS = ('honest', 'exag_naive', 'exag_consistent', 'sabotage')


def run_dsa(inst, x0, types, lam, q=0.6, max_rounds=300, seed=0):
    """DSA: no gains are posted, so attacks on the gain channel act like honest play."""
    rng = random.Random(seed)
    x = list(x0)
    for r in range(1, max_rounds + 1):
        ann = {i: announce(inst, x, i, types[i] if types[i] in DSA_ATTACKS else 'honest', lam)
               for i in range(inst['N'])}
        act = [i for i, (c, e, a) in ann.items() if e is not None and c > 0]
        if not act:
            return x, r, False
        for i in act:
            if rng.random() < q:
                _, e, a = ann[i]
                x[e] = a
    return x, max_rounds, True
