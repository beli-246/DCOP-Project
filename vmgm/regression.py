"""Regression: the new package must reproduce the pilot's saved results exactly.

Usage (from the repository root):
    python3 -m vmgm.regression DCOP_prelim_code_results 30
The second argument is how many seeds per family to check (pilot has 30).
CP-SAT fields are not compared (ortools is optional).
"""
import json
import os
import sys

import numpy as np

from . import model as M
from .liars import pilot_liars
from .attacks import PILOT_ATTACKS
from .protocol import PROTOCOLS, run, run_dsa

FIELDS = ['F', 'H', 'K', 'rounds', 'capped', 'det', 'fp', 'profit', 'hloss']
LAM = 3.0


def recompute(family, sd, ks=(1, 2)):
    inst = M.add_fake_preferences(M.make_instance(sd, **M.FAMILIES[family]), LAM)
    starts = {'random': M.random_start(inst, 1000 + sd), 'greedy': M.greedy_start(inst)}
    rows = {}
    for sname, x0 in starts.items():
        honest = ['honest'] * inst['N']
        ref = {p: run(inst, x0, honest, LAM, prot, seed=sd).as_pilot_tuple() for p, prot in PROTOCOLS.items()}
        ref['DSA'] = run_dsa(inst, x0, honest, LAM, seed=sd)
        for p in list(PROTOCOLS) + ['DSA']:
            xs = ref[p][0]
            rows[(sd, sname, p, 'none', 0)] = dict(
                F=M.F_cost(inst, xs), H=M.H_cost(inst, xs), K=M.clash_students(inst, xs), rounds=ref[p][1],
                capped=ref[p][-1] if p != 'DSA' else ref[p][2], det=0,
                fp=len(ref[p][2]) if p != 'DSA' else 0, profit=0.0, hloss=0.0)
        for k in ks:
            liars = pilot_liars(inst, k, sd)
            for att in PILOT_ATTACKS:
                types = ['honest' if i not in liars else att for i in range(inst['N'])]
                for p, prot in list(PROTOCOLS.items()) + [('DSA', None)]:
                    if p == 'DSA' and att not in ('sabotage', 'exag_naive', 'exag_consistent'):
                        continue
                    if p == 'DSA':
                        xs, rr, capped = run_dsa(inst, x0, types, LAM, seed=sd)
                        fl, xref = set(), ref['DSA'][0]
                    else:
                        xs, rr, fl, _, capped = run(inst, x0, types, LAM, prot, seed=sd).as_pilot_tuple()
                        xref = ref[p][0]
                    rows[(sd, sname, p, att, k)] = dict(
                        F=M.F_cost(inst, xs), H=M.H_cost(inst, xs), K=M.clash_students(inst, xs),
                        rounds=rr, capped=capped, det=len(fl & liars), fp=len(fl - liars),
                        profit=float(np.mean([M.J(inst, xref, i, LAM) - M.J(inst, xs, i, LAM) for i in liars])),
                        hloss=sum(M.burden(inst, xs, i) - M.burden(inst, xref, i)
                                  for i in range(inst['N']) if i not in liars))
    return rows


def main(pilot_dir, n_seeds):
    total, bad = 0, []
    for family in ('loose', 'tight'):
        saved = json.load(open(os.path.join(pilot_dir, f'prelim_{family}.json')))
        saved = {(r['seed'], r['start'], r['protocol'], r['attack'], r['k']): r for r in saved}
        for sd in range(n_seeds):
            new = recompute(family, sd)
            for key, row in new.items():
                old = saved.get(key)
                if old is None:
                    bad.append((family, key, 'missing in pilot JSON'))
                    continue
                total += 1
                for f in FIELDS:
                    a, b = row[f], old[f]
                    same = abs(a - b) <= 1e-6 if isinstance(a, float) or isinstance(b, float) else a == b
                    if not same:
                        bad.append((family, key, f, b, a))
            print(f'{family} seed {sd}: {len(new)} rows', file=sys.stderr, flush=True)
    print(f'compared {total} rows, {len(bad)} mismatches')
    for b in bad[:20]:
        print('  ', b)
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 30))
