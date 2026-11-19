"""CP-SAT reference values: the best timetable, computed centrally from everyone's true preferences.

No distributed algorithm in this project can reach it (no department knows the others' preferences);
it only puts MGM's and V-MGM's final costs in context. The pair costs are taken from model.pc, so the
objective is exactly model.F_cost (checked on every solve).

Usage (from the repository root):
    python -m vmgm.cpsat vmgm_results/full --time-loose 60 --time-tight 300 --workers 8
Writes <dir>/cpsat.csv: one row per instance (loose and tight families, seeds 100-149, the E1-E3
instances). Tight instances may not be solved to proven optimality within the limit; then F_best is
the best timetable found and F_bound a proven lower bound on the optimum.
"""
import argparse
import os
import sys
import time

import pandas as pd

from . import model as M
from .protocol import PROTOCOLS, run

LAM = 3.0
SEED0 = 100


def solve(inst, time_limit=60, workers=8, seed=0, hint=None):
    """Minimise F = G + H over all timetables. Returns status, F_best, F_bound, x, time_s."""
    from ortools.sat.python import cp_model
    E, S = inst['E'], inst['S']
    m = cp_model.CpModel()
    b = [[m.NewBoolVar(f'b_{e}_{a}') for a in range(S)] for e in range(E)]   # exam e in slot a
    for e in range(E):
        m.AddExactlyOne(b[e])
    terms = [inst['g'][e][a] * b[e][a] for e in range(E) for a in range(S)]
    for (e, f), c in inst['n'].items():
        for a in range(S):
            for a2 in range(S):
                w = M.pc(a, a2, c)
                if w == 0:
                    continue
                y = m.NewBoolVar('')                      # 1 if e in a and f in a2 (objective keeps it 0 otherwise)
                m.AddBoolOr([b[e][a].Not(), b[f][a2].Not(), y])
                terms.append(w * y)
    m.Minimize(sum(terms))
    if hint is not None:
        for e in range(E):
            for a in range(S):
                m.AddHint(b[e][a], int(hint[e] == a))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_limit
    s.parameters.num_workers = workers
    s.parameters.random_seed = seed
    t0 = time.time()
    st = s.Solve(m)
    status = s.StatusName(st)
    if status not in ('OPTIMAL', 'FEASIBLE'):
        raise RuntimeError(f'CP-SAT returned {status}')
    x = [next(a for a in range(S) if s.Value(b[e][a])) for e in range(E)]
    return dict(status=status, F_best=int(round(s.ObjectiveValue())), F_bound=int(round(s.BestObjectiveBound())),
                x=x, time_s=time.time() - t0)


def honest_mgm(inst, sd):
    """Honest MGM's final timetable from the greedy start (used as a warm start)."""
    return run(inst, M.greedy_start(inst), ['honest'] * inst['N'], LAM, PROTOCOLS['MGM'], seed=sd).x


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('outdir', nargs='?', default='vmgm_results/full')
    ap.add_argument('--seeds', type=int, default=50)
    ap.add_argument('--time-loose', type=float, default=60)
    ap.add_argument('--time-tight', type=float, default=300)
    ap.add_argument('--workers', type=int, default=8)
    a = ap.parse_args(argv)
    import ortools
    rows, t0 = [], time.time()
    jobs = [(f, sd) for f in M.FAMILIES for sd in range(SEED0, SEED0 + a.seeds)]
    for n, (fam, sd) in enumerate(jobs, 1):
        inst = M.make_instance(sd, **M.FAMILIES[fam])
        limit = a.time_loose if fam == 'loose' else a.time_tight
        r = solve(inst, time_limit=limit, workers=a.workers, seed=0, hint=honest_mgm(inst, sd))
        F = M.F_cost(inst, r['x'])
        if F != r['F_best']:
            raise AssertionError(f'{fam} {sd}: CP-SAT objective {r["F_best"]} != F_cost {F}')
        rows.append(dict(family=fam, seed=sd, status=r['status'], F_best=r['F_best'], F_bound=r['F_bound'],
                         gap=(r['F_best'] - r['F_bound']) / r['F_best'] if r['F_best'] else 0.0,
                         time_s=round(r['time_s'], 2), time_limit=limit, ortools_version=ortools.__version__))
        print(f'{n}/{len(jobs)} {fam} {sd}: {r["status"]} F_best={r["F_best"]} bound={r["F_bound"]} '
              f'({r["time_s"]:.1f}s, total {time.time() - t0:.0f}s)', flush=True)
        pd.DataFrame(rows).to_csv(os.path.join(a.outdir, 'cpsat.csv'), index=False)   # keep partial results
    print(f'wrote {os.path.join(a.outdir, "cpsat.csv")}: {len(rows)} instances')


if __name__ == '__main__':
    sys.exit(main())
