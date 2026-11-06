"""Problem model: instances, costs and gains.

Copied from the pilot (DCOP_prelim_code_results/prelim.py) without behavioural changes,
so that the regression test can reproduce the pilot numbers exactly.
"""
import itertools
import random

WH, WS, SESS, HUGE = 10, 2, 2, 10**6   # clash weight, back-to-back weight, slots per day, "huge" claim


# ------------------------------------------------------------------ instances
def make_instance(seed, N=12, per=4, S=10, p=0.08, gmax=50, pref_spread=1.0):
    """pref_spread: true preferences are drawn from {0..round(pref_spread*gmax)}, so a department
    with spread < 1 has room to exaggerate within the public scale. pref_spread=1.0 gives exactly
    the pilot's instances (same random calls)."""
    rng = random.Random(seed)
    gtop = int(round(pref_spread * gmax))
    E = N * per
    owner = [e // per for e in range(E)]
    n = {}
    for e, f in itertools.combinations(range(E), 2):
        if rng.random() < p:
            n[(e, f)] = rng.randint(5, 40)
    g = [[rng.randint(0, gtop) for _ in range(S)] for _ in range(E)]
    adj = {e: [] for e in range(E)}
    for (e, f), c in n.items():
        adj[e].append((f, c))
        adj[f].append((e, c))
    nbr = {i: set() for i in range(N)}
    for (e, f) in n:
        a, b = owner[e], owner[f]
        if a != b:
            nbr[a].add(b)
            nbr[b].add(a)
    exams = {i: list(range(i * per, (i + 1) * per)) for i in range(N)}
    return dict(E=E, S=S, N=N, owner=owner, n=n, g=g, adj=adj, nbr=nbr, exams=exams, gmax=gmax)


FAMILIES = {'loose': dict(S=10, p=0.08), 'tight': dict(S=6, p=0.14)}


def add_fake_preferences(inst, lam):
    """g~ used by the consistent exaggerator (T1b): truthful play for min(gmax, lam*g)."""
    inst['gtilde'] = [[min(inst['gmax'], int(round(lam * v))) for v in row] for row in inst['g']]
    # strongest undetectable exaggeration: stretch each exam's preferences from their minimum by lam,
    # clipped to the public scale (used by 'exag_stretch'; differs from T1b, which clips lam*g)
    inst['gtilde_stretch'] = [[min(inst['gmax'], int(round(lam * (v - min(row))))) for v in row]
                              for row in inst['g']]
    return inst


# ------------------------------------------------------------------ costs
def pc(a, b, c):
    """Pairwise student cost f_ef for slots a, b and c shared students."""
    if a == b:
        return WH * c
    if a // SESS == b // SESS and abs(a - b) == 1:
        return WS * c
    return 0


def H_cost(inst, x):
    return sum(pc(x[e], x[f], c) for (e, f), c in inst['n'].items())


def G_cost(inst, x, gvec=None, exams=None):
    g = inst['g'] if gvec is None else gvec
    rng = range(inst['E']) if exams is None else exams
    return sum(g[e][x[e]] for e in rng)


def F_cost(inst, x):
    return G_cost(inst, x) + H_cost(inst, x)


def clash_students(inst, x):
    return sum(c for (e, f), c in inst['n'].items() if x[e] == x[f])


def burden(inst, x, i):
    """B_i: own preference cost + half of each inter-department term + full intra terms (sum_i B_i = F)."""
    tot = 0.0
    for e in inst['exams'][i]:
        tot += inst['g'][e][x[e]]
        for f, c in inst['adj'][e]:
            w = 1.0 if inst['owner'][f] == i else 0.5
            if inst['owner'][f] == i and f < e:
                continue          # intra pair counted once
            tot += w * pc(x[e], x[f], c)
    return tot


def J(inst, x, i, lam):
    """Selfish objective of department i: lam * own preference cost + student cost touching its exams."""
    tot = lam * sum(inst['g'][e][x[e]] for e in inst['exams'][i])
    seen = set()
    for e in inst['exams'][i]:
        for f, c in inst['adj'][e]:
            k = (min(e, f), max(e, f))
            if k not in seen:
                seen.add(k)
                tot += pc(x[e], x[f], c)
    return tot


# ------------------------------------------------------------------ gains
def V(inst, x, e, a):
    """Public gain: drop in student cost H if exam e moves from x[e] to slot a."""
    return sum(pc(x[e], x[f], c) - pc(a, x[f], c) for f, c in inst['adj'][e])


def moves(inst, x, i):
    for e in inst['exams'][i]:
        for a in range(inst['S']):
            if a != x[e]:
                yield e, a


def best_move(inst, x, i, gvec, lam=1.0):
    """argmax over single-exam moves of V + lam*(g(a)-g(a')); returns (value, e, a) or (0, None, None)."""
    best = (0, None, None)
    for e, a in moves(inst, x, i):
        val = V(inst, x, e, a) + lam * (gvec[e][x[e]] - gvec[e][a])
        if val > best[0] + 1e-9:
            best = (val, e, a)
    return best


# ------------------------------------------------------------------ starts
def random_start(inst, seed):
    rng = random.Random(seed)
    return [rng.randrange(inst['S']) for _ in range(inst['E'])]


def greedy_start(inst):
    """Registrar's draft from public data only: exams by decreasing coupling, min coupling-cost slot."""
    x = [None] * inst['E']
    order = sorted(range(inst['E']), key=lambda e: -sum(c for _, c in inst['adj'][e]))
    for e in order:
        x[e] = min(range(inst['S']),
                   key=lambda a: (sum(pc(a, x[f], c) for f, c in inst['adj'][e] if x[f] is not None), a))
    return x
