"""Consolidated preliminary study for the revised proposal.

Every number reported in the 'Preliminary results' section of the report is produced
by this script (and summarise.py). Instance generator and cost model follow the original
pilot (pilot.py); attacks, audits and protocols are defined exactly as in the report.
"""
import random, itertools, json, sys, time
import numpy as np

WH, WS, SESS, HUGE = 10, 2, 2, 10**6


# ------------------------------------------------------------------ instances
def make_instance(seed, N=12, per=4, S=10, p=0.08, gmax=50):
    rng = random.Random(seed)
    E = N * per
    owner = [e // per for e in range(E)]
    n = {}
    for e, f in itertools.combinations(range(E), 2):
        if rng.random() < p:
            n[(e, f)] = rng.randint(5, 40)
    g = [[rng.randint(0, gmax) for _ in range(S)] for _ in range(E)]
    adj = {e: [] for e in range(E)}
    for (e, f), c in n.items():
        adj[e].append((f, c)); adj[f].append((e, c))
    nbr = {i: set() for i in range(N)}
    for (e, f) in n:
        a, b = owner[e], owner[f]
        if a != b:
            nbr[a].add(b); nbr[b].add(a)
    exams = {i: list(range(i * per, (i + 1) * per)) for i in range(N)}
    return dict(E=E, S=S, N=N, owner=owner, n=n, g=g, adj=adj, nbr=nbr, exams=exams, gmax=gmax)


def pc(a, b, c):
    if a == b:
        return WH * c
    if a // SESS == b // SESS and abs(a - b) == 1:
        return WS * c
    return 0


def H_cost(inst, x):
    return sum(pc(x[e], x[f], c) for (e, f), c in inst['n'].items())


def G_cost(inst, x, gvec=None):
    g = inst['g'] if gvec is None else gvec
    return sum(g[e][x[e]] for e in range(inst['E']))


def F_cost(inst, x):
    return G_cost(inst, x) + H_cost(inst, x)


def clash_students(inst, x):
    return sum(c for (e, f), c in inst['n'].items() if x[e] == x[f])


def burden(inst, x, i):
    """B_i: own preference cost + half of each inter-department coupling term + full intra terms (sum_i B_i = F)."""
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
    """Strategic objective of department i: lam * own preference cost + coupling terms touching its exams."""
    tot = lam * sum(inst['g'][e][x[e]] for e in inst['exams'][i])
    seen = set()
    for e in inst['exams'][i]:
        for f, c in inst['adj'][e]:
            k = (min(e, f), max(e, f))
            if k not in seen:
                seen.add(k); tot += pc(x[e], x[f], c)
    return tot


def V(inst, x, e, a):
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


# ------------------------------------------------------------------ behaviours
def announce(inst, x, i, kind, lam):
    """Return (claim, e, a) posted by department i. kind='honest' or an attack name."""
    g, gmax = inst['g'], inst['gmax']
    if kind == 'honest':
        return best_move(inst, x, i, g)
    if kind == 'exag_naive':                      # T1 naive: announce own utility gain lam*P + V
        return best_move(inst, x, i, g, lam)
    if kind == 'exag_consistent':                 # T1 consistent: behave truthfully w.r.t. g~ = min(gmax, lam*g)
        return best_move(inst, x, i, inst['gtilde'])
    if kind == 'hijack':                          # T2 naive: inflate by HUGE
        v, e, a = best_move(inst, x, i, g, lam)
        return (v + HUGE, e, a) if e is not None else (0, None, None)
    if kind == 'maxbound':                        # T2 in-bound: claim V+gmax for own selfish best move
        v, e, a = best_move(inst, x, i, g, lam)
        return (V(inst, x, e, a) + gmax, e, a) if e is not None else (0, None, None)
    if kind == 'block':                           # T3 naive: always claim HUGE (null move if nothing to do)
        v, e, a = best_move(inst, x, i, g, lam)
        return (HUGE, e, a)
    if kind == 'churn':                           # T3 in-bound: max-V move every round, claim V+gmax
        best = max(((V(inst, x, e, a), e, a) for e, a in moves(inst, x, i)), key=lambda t: t[0])
        return (best[0] + gmax, best[1], best[2])
    if kind == 'sabotage':                        # action-channel: most harmful move with -gmax < V < 0
        c = [(V(inst, x, e, a), e, a) for e, a in moves(inst, x, i)]
        c = [t for t in c if -gmax < t[0] < 0]
        if not c:
            return (0, None, None)
        v, e, a = min(c)
        return (v + gmax, e, a)
    raise ValueError(kind)


# ------------------------------------------------------------------ protocols
def run(inst, x0, types, lam, protocol, max_rounds=300, seed=0):
    """protocol: dict(priority='gain'|'random', audit='none'|'move'|'hist', response='cap'|'quarantine')"""
    rng = random.Random(seed)
    x = list(x0); gmax = inst['gmax']
    flagged, flag_round = set(), {}
    phi = {e: {x0[e]: 0} for e in range(inst['E'])}
    for r in range(1, max_rounds + 1):
        ann = {i: announce(inst, x, i, types[i], lam) for i in range(inst['N'])}
        eff = {}
        for i, (claim, e, a) in ann.items():
            v = 0 if e is None else V(inst, x, e, a)
            if protocol['audit'] == 'none':
                eff[i] = claim if e is not None or protocol['priority'] == 'gain' else 0
                continue
            viol = (claim > 0) if e is None else (claim - v > gmax or claim - v < -gmax)
            if protocol['audit'] == 'hist' and e is not None and not viol:
                P = phi[e]; cur = P.get(x[e])
                if cur is not None:                     # always true for unflagged histories
                    new = cur - (claim - v)
                    if a in P and P[a] != new:
                        viol = True
                    else:
                        vals = list(P.values()) + [new]
                        if max(vals) - min(vals) > gmax:
                            viol = True
                        else:
                            P[a] = new
            if viol and i not in flagged:
                flagged.add(i); flag_round[i] = r
            if e is None:
                eff[i] = 0
            elif i in flagged and protocol['response'] == 'quarantine':
                eff[i] = min(claim, v)
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
            return x, r, flagged, flag_round, False
        if not winners:                                  # deterministic freeze (gain priority only)
            return x, r, flagged, flag_round, True
        for i in winners:
            _, e, a = ann[i]
            x[e] = a
    return x, max_rounds, flagged, flag_round, True


def run_dsa(inst, x0, types, lam, q=0.6, max_rounds=300, seed=0):
    rng = random.Random(seed); x = list(x0)
    for r in range(1, max_rounds + 1):
        ann = {i: announce(inst, x, i, types[i] if types[i] in ('honest', 'exag_naive', 'exag_consistent', 'sabotage') else 'honest', lam)
               for i in range(inst['N'])}
        act = [i for i, (c, e, a) in ann.items() if e is not None and c > 0]
        if not act:
            return x, r, False
        for i in act:
            if rng.random() < q:
                _, e, a = ann[i]; x[e] = a
    return x, max_rounds, True


# ------------------------------------------------------------------ reference solutions
def cpsat(inst, time_limit=20):
    from ortools.sat.python import cp_model
    m = cp_model.CpModel(); E, S = inst['E'], inst['S']
    y = [[m.NewBoolVar('') for a in range(S)] for e in range(E)]
    for e in range(E):
        m.AddExactlyOne(y[e])
    obj = [inst['g'][e][a] * y[e][a] for e in range(E) for a in range(S)]
    for (e, f), c in inst['n'].items():
        for a in range(S):
            for b in range(S):
                w = pc(a, b, c)
                if w > 0:
                    z = m.NewBoolVar('')
                    m.AddBoolOr([y[e][a].Not(), y[f][b].Not(), z])
                    obj.append(w * z)
    m.Minimize(sum(obj))
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = time_limit; s.parameters.num_workers = 8
    st = s.Solve(m)
    return s.ObjectiveValue(), s.BestObjectiveBound(), s.StatusName(st)


def greedy_start(inst):
    """Registrar's draft from public data only: exams by decreasing coupling degree, min coupling cost slot."""
    x = [None] * inst['E']
    order = sorted(range(inst['E']), key=lambda e: -sum(c for _, c in inst['adj'][e]))
    for e in order:
        best = min(range(inst['S']), key=lambda a: (sum(pc(a, x[f], c) for f, c in inst['adj'][e] if x[f] is not None), a))
        x[e] = best
    return x


# ------------------------------------------------------------------ experiment grid
PROTOCOLS = {
    'MGM':            dict(priority='gain', audit='none', response='cap'),
    'VMGM-move-cap':  dict(priority='gain', audit='move', response='cap'),
    'VMGM-move-quar': dict(priority='gain', audit='move', response='quarantine'),
    'VMGM-hist-cap':  dict(priority='gain', audit='hist', response='cap'),
    'VMGM-hist-quar': dict(priority='gain', audit='hist', response='quarantine'),
    'RP-MGM':         dict(priority='random', audit='none', response='cap'),
}
ATTACKS = ['block', 'hijack', 'maxbound', 'churn', 'sabotage', 'exag_naive', 'exag_consistent']


def main(family, n_inst, ks=(1, 2), lam=3.0):
    S, p = {'loose': (10, 0.08), 'tight': (6, 0.14)}[family]
    rows = []
    for sd in range(n_inst):
        inst = make_instance(sd, S=S, p=p)
        inst['gtilde'] = [[min(inst['gmax'], int(round(lam * v))) for v in row] for row in inst['g']]
        t0 = time.time(); opt, bound, status = cpsat(inst); tcp = time.time() - t0
        rng = random.Random(1000 + sd)
        starts = {'random': [rng.randrange(inst['S']) for _ in range(inst['E'])], 'greedy': greedy_start(inst)}
        for sname, x0 in starts.items():
            honest = ['honest'] * inst['N']
            ref = {}
            for pname, prot in PROTOCOLS.items():
                ref[pname] = run(inst, x0, honest, lam, prot, seed=sd)
            ref['DSA'] = run_dsa(inst, x0, honest, lam, seed=sd)
            F_mgm = F_cost(inst, ref['MGM'][0])
            base = dict(family=family, seed=sd, start=sname, opt=opt, bound=bound, status=status, t_cpsat=tcp,
                        F0=F_cost(inst, x0), K0=clash_students(inst, x0), F_mgm=F_mgm,
                        dens=np.mean([len(inst['nbr'][i]) for i in range(inst['N'])]) / (inst['N'] - 1))
            for pname in list(PROTOCOLS) + ['DSA']:
                xs = ref[pname][0]
                rows.append(dict(base, protocol=pname, attack='none', k=0, F=F_cost(inst, xs), H=H_cost(inst, xs),
                                 K=clash_students(inst, xs), rounds=ref[pname][1],
                                 capped=ref[pname][-1] if pname != 'DSA' else ref[pname][2],
                                 det=0, fp=len(ref[pname][2]) if pname != 'DSA' else 0, profit=0.0, hloss=0.0))
            for k in ks:
                liars = set(random.Random(2000 + sd).sample(range(inst['N']), k))
                types = ['honest'] * inst['N']
                for att in ATTACKS:
                    for i in liars:
                        types[i] = att
                    for pname, prot in list(PROTOCOLS.items()) + [('DSA', None)]:
                        if pname == 'DSA' and att not in ('sabotage', 'exag_naive', 'exag_consistent'):
                            continue
                        if pname == 'DSA':
                            xs, rr, capped = run_dsa(inst, x0, types, lam, seed=sd); fl = set()
                            xref = ref['DSA'][0]
                        else:
                            xs, rr, fl, fr, capped = run(inst, x0, types, lam, prot, seed=sd)
                            xref = ref[pname][0]
                        profit = np.mean([J(inst, xref, i, lam) - J(inst, xs, i, lam) for i in liars])
                        hloss = sum(burden(inst, xs, i) - burden(inst, xref, i) for i in range(inst['N']) if i not in liars)
                        rows.append(dict(base, protocol=pname, attack=att, k=k, F=F_cost(inst, xs), H=H_cost(inst, xs),
                                         K=clash_students(inst, xs), rounds=rr, capped=capped,
                                         det=len(fl & liars), fp=len(fl - liars), profit=profit, hloss=hloss,
                                         liar_deg=np.mean([len(inst['nbr'][i]) for i in liars])))
        print(family, sd, status, round(tcp, 1), file=sys.stderr, flush=True)
    return rows


if __name__ == '__main__':
    fam = sys.argv[1]; n = int(sys.argv[2])
    rows = main(fam, n)
    json.dump(rows, open(f'prelim_{fam}.json', 'w'))
