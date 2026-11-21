"""Property check for Proposition 4: with the history audit, for every dishonest exam the summed public-cost
increase of its moves executed while its owner is unflagged stays below g_max."""
import random, prelim
from prelim import make_instance, announce, V
worst = 0.0; checked = 0
for fam, (S, p) in {'loose': (10, 0.08), 'tight': (6, 0.14)}.items():
    for sd in range(30):
        inst = make_instance(sd, S=S, p=p); lam = 3.0
        inst['gtilde'] = [[min(50, int(round(lam * v))) for v in row] for row in inst['g']]
        rng = random.Random(1000 + sd)
        for x0 in ([rng.randrange(S) for _ in range(inst['E'])], prelim.greedy_start(inst)):
            for att in ['maxbound', 'churn', 'sabotage', 'exag_naive', 'hijack']:
                liars = set(random.Random(2000 + sd).sample(range(inst['N']), 2))
                types = [att if i in liars else 'honest' for i in range(inst['N'])]
                # replay prelim.run with instrumentation (hist audit, quarantine)
                x = list(x0); gmax = inst['gmax']; flagged = set(); phi = {e: {x0[e]: 0} for e in range(inst['E'])}
                dmg = {e: 0.0 for e in range(inst['E'])}
                for r in range(300):
                    ann = {i: announce(inst, x, i, types[i], lam) for i in range(inst['N'])}
                    eff = {}; passed = {}
                    for i, (c, e, a) in ann.items():
                        v = 0 if e is None else V(inst, x, e, a)
                        viol = (c > 0) if e is None else abs(c - v) > gmax
                        if e is not None and not viol:
                            P = phi[e]; cur = P.get(x[e])
                            if cur is not None:
                                new = cur - (c - v)
                                if (a in P and P[a] != new) or max(list(P.values()) + [new]) - min(list(P.values()) + [new]) > gmax:
                                    viol = True
                                else:
                                    P[a] = new
                        if viol: flagged.add(i)
                        eff[i] = 0 if e is None else (min(c, v) if i in flagged else min(c, v + gmax))
                        passed[i] = (i not in flagged, v)
                    el = [i for i in ann if eff[i] > 0]
                    w = [i for i in el if ann[i][1] is not None and all(eff[i] > eff[j] or (eff[i] == eff[j] and i < j) for j in inst['nbr'][i])]
                    if not el or not w: break
                    for i in w:
                        _, e, a = ann[i]
                        if passed[i][0]: dmg[e] += -passed[i][1]
                        x[e] = a
                for i in liars:
                    for e in inst['exams'][i]:
                        worst = max(worst, dmg[e] / gmax); checked += 1
print('checked exam-runs:', checked, ' max (sum of -V over unflagged executed moves)/g_max =', round(worst, 3))
