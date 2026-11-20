"""Experiments E1-E6. One CSV per experiment in vmgm_results/

  E1  does lying hurt MGM more than claim-free baselines?             (H1)
  E2  k dishonest departments: detection, finishing, damage split,
      placement, mixed attacks, quarantine control, record mode        (H2a-d)
  E3  does undetectable lying pay, and more as kappa grows?            (H3)
  E4  damage vs problem size N, overlap p and the liar's neighbours    (H4)
  E5  is "did not finish" caused by the 300-round limit? (300 vs 1000)
  E6  do colluding liars hurt honest departments more than independent ones? (H5)

Instances use seeds 100.. so they are disjoint from the pilot's seeds 0..29.
Every run with an audit goes through invariants.check_all, so any violation of a proven
result stops the experiment. Quarantine-control runs are exempt (honest departments are
quarantined on purpose, which no result covers).

Usage (from the repository root):
    python3 -m vmgm.experiments E2 --seeds 50 --workers 7
    python3 -m vmgm.experiments all --seeds 50
    python3 -m vmgm.experiments all --seeds 2 --out vmgm_results/smoke     (quick smoke test)
"""
import argparse
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd

from . import model as M
from .attacks import ALL_ATTACKS, E6_ATTACKS
from .invariants import check_all
from .liars import liar_adjacency, make_types, place_liars
from .metrics import dsa_metrics, run_metrics
from .protocol import PROTOCOLS, run, run_dsa

LAM = 3.0
SEED0 = 100
MIXED = ['block', 'churn', 'sabotage_consistent', 'exag_consistent']


def starts(inst, sd, which=('random', 'greedy')):
    out = []
    if 'random' in which:
        out.append(('random', M.random_start(inst, 1000 + sd)))
    if 'greedy' in which:
        out.append(('greedy', M.greedy_start(inst)))
    return out


def honest_refs(inst, x0, sd, names, lam=LAM, max_rounds=300):
    honest = ['honest'] * inst['N']
    ref = {}
    for n in names:
        if n == 'DSA':
            ref[n] = run_dsa(inst, x0, honest, lam, seed=sd, max_rounds=max_rounds)[0]
        else:
            prot = PROTOCOLS[n.replace('-exec', '')] if n.endswith('-exec') else PROTOCOLS[n]
            ref[n] = run(inst, x0, honest, lam, prot, seed=sd, max_rounds=max_rounds).x
    return ref


def one(inst, x0, sd, types, pname, ref, lam=LAM, max_rounds=300, check=True, **kw):
    """Run protocol pname (or DSA) and return (metrics, RunResult or None)."""
    if pname == 'DSA':
        x, rr, capped = run_dsa(inst, x0, types, lam, seed=sd, max_rounds=max_rounds)
        return dsa_metrics(inst, x, rr, capped, x0, types, lam, ref['MGM'], ref['DSA']), None
    if pname.endswith('-exec'):
        prot = dict(PROTOCOLS[pname[:-5]], record='executed')
        ref_self = ref[pname[:-5]]
    else:
        prot = PROTOCOLS[pname]
        ref_self = ref[pname]
    res = run(inst, x0, types, lam, prot, seed=sd, max_rounds=max_rounds, **kw)
    if check:
        check_all(inst, res, types, prot)
    return run_metrics(inst, res, types, lam, ref['MGM'], ref_self), res


# ------------------------------------------------------------------ E1
E1_PROTOCOLS = ['MGM', 'RP-MGM', 'DSA', 'VMGM-hist-quar']
E1_ATTACKS = ['hijack', 'maxbound', 'block', 'churn', 'sabotage']


def job_E1(family, sd):
    inst = M.add_fake_preferences(M.make_instance(sd, **M.FAMILIES[family]), LAM)
    rows = []
    for sname, x0 in starts(inst, sd):
        ref = honest_refs(inst, x0, sd, E1_PROTOCOLS)
        for k in (1, 2, 3):
            liars = place_liars(inst, k, 'random', seed=sd)
            for att in E1_ATTACKS:
                types = make_types(inst, liars, att)
                for p in E1_PROTOCOLS:
                    m, _ = one(inst, x0, sd, types, p, ref)
                    rows.append(dict(family=family, seed=sd, start=sname, k=k, attack=att, protocol=p, **m))
    return rows


# ------------------------------------------------------------------ E2
E2_PROTOCOLS = list(PROTOCOLS) + ['VMGM-hist-quar-exec']
E2_ATTACKS = {a: a for a in ALL_ATTACKS}
E2_ATTACKS['mixed'] = MIXED


def job_E2(family, sd):
    inst = M.add_fake_preferences(M.make_instance(sd, **M.FAMILIES[family]), LAM)
    rows = []
    for sname, x0 in starts(inst, sd):
        ref = honest_refs(inst, x0, sd, list(PROTOCOLS))
        ref['VMGM-hist-quar-exec'] = ref['VMGM-hist-quar']
        base = dict(family=family, seed=sd, start=sname)
        for p in E2_PROTOCOLS:
            m, _ = one(inst, x0, sd, ['honest'] * inst['N'], p, ref)
            rows.append(dict(base, k=0, placement='none', liar_pairs=0, attack='none', protocol=p, **m))
        for k in (1, 2, 3, 6):
            for pl in ('adjacent', 'spread'):
                liars = place_liars(inst, k, pl, seed=sd)
                lp = liar_adjacency(inst, liars)
                for aname, att in E2_ATTACKS.items():
                    types = make_types(inst, liars, att)
                    flagged_runs = {}
                    for p in E2_PROTOCOLS:
                        m, res = one(inst, x0, sd, types, p, ref)
                        if p in ('VMGM-hist-quar', 'VMGM-hist-soft'):
                            flagged_runs[p] = res
                        rows.append(dict(base, k=k, placement=pl, liar_pairs=lp, attack=aname, protocol=p, **m))
                    # quarantine controls: everyone honest, the departments the liars were flagged in quarantined
                    # (hard, resp. soft) from the same rounds; isolates what each response itself costs
                    for prot, ctl_name in (('VMGM-hist-quar', 'control-quar'), ('VMGM-hist-soft', 'control-soft')):
                        forced = {i: r for i, r in flagged_runs[prot].flag_round.items() if i in liars}
                        honest = ['honest'] * inst['N']
                        m, cres = one(inst, x0, sd, honest, prot, ref, check=False, forced_quarantine=forced)
                        m['liar_profit'] = float('nan')
                        m['honest_loss'] = sum(M.burden(inst, cres.x, i) - M.burden(inst, ref[prot], i)
                                               for i in range(inst['N']) if i not in liars)
                        m['n_forced'] = len(forced)
                        rows.append(dict(base, k=k, placement=pl, liar_pairs=lp, attack=aname,
                                         protocol=ctl_name, **m))
    return rows


# ------------------------------------------------------------------ E3
E3_GMAX = (10, 25, 50, 100, 200)
E3_SPREAD = (0.25, 0.5, 1.0)
E3_LAM = (1.5, 3.0, 6.0)


def job_E3(family, sd):
    """Undetectable liars never get flagged, so V-MGM behaves exactly like MGM for them;
    only V-MGM is run (the invariant checks confirm no liar is ever flagged)."""
    rows = []
    for gmax in E3_GMAX:
        for spread in E3_SPREAD:
            base_inst = M.make_instance(sd, gmax=gmax, pref_spread=spread, **M.FAMILIES[family])
            nbar = sum(base_inst['n'].values()) / len(base_inst['n'])
            kappa = gmax / (M.WS * nbar)
            for lam in E3_LAM:
                inst = M.add_fake_preferences(dict(base_inst), lam)
                for sname, x0 in starts(inst, sd):
                    ref = honest_refs(inst, x0, sd, ['MGM', 'VMGM-hist-quar'], lam=lam)
                    for k in (1, 3):
                        liars = place_liars(inst, k, 'random', seed=sd)
                        for att in ('exag_stretch', 'exag_consistent'):
                            types = make_types(inst, liars, att)
                            m, _ = one(inst, x0, sd, types, 'VMGM-hist-quar', ref, lam=lam)
                            if m['detected']:
                                raise AssertionError(f'undetectable liar flagged: {family} {sd} {att}')
                            rows.append(dict(family=family, seed=sd, start=sname, gmax=gmax, spread=spread,
                                             lam=lam, kappa=kappa, k=k, attack=att, protocol='VMGM-hist-quar', **m))
    return rows


# ------------------------------------------------------------------ E4
E4_N = (12, 24, 48)
E4_P = (0.02, 0.04, 0.08)
E4_ATTACKS = ['block', 'churn', 'sabotage', 'sabotage_consistent']


def job_E4(N, p, sd):
    inst = M.add_fake_preferences(M.make_instance(sd, N=N, S=10, p=p), LAM)
    dens = sum(len(inst['nbr'][i]) for i in range(N)) / N / (N - 1)
    rows = []
    for sname, x0 in starts(inst, sd, which=('random',)):
        ref = honest_refs(inst, x0, sd, ['MGM', 'VMGM-hist-quar'])
        for k in sorted({1, math.ceil(0.25 * N)}):
            liars = place_liars(inst, k, 'random', seed=sd)
            for att in E4_ATTACKS:
                types = make_types(inst, liars, att)
                for prot in ('MGM', 'VMGM-hist-quar'):
                    m, _ = one(inst, x0, sd, types, prot, ref)
                    rows.append(dict(N=N, p=p, S=10, seed=sd, start=sname, density=dens, k=k, k_frac=k / N,
                                     attack=att, protocol=prot, **m))
    return rows


# ------------------------------------------------------------------ E5
def job_E5(family, sd):
    inst = M.add_fake_preferences(M.make_instance(sd, **M.FAMILIES[family]), LAM)
    rows = []
    for sname, x0 in starts(inst, sd, which=('random',)):
        for cap in (300, 1000):
            ref = honest_refs(inst, x0, sd, ['MGM', 'VMGM-move-cap', 'VMGM-hist-cap', 'VMGM-hist-quar', 'RP-MGM'],
                              max_rounds=cap)
            for k in (1, 3):
                liars = place_liars(inst, k, 'random', seed=sd)
                for att in ('block', 'churn', 'sabotage'):
                    types = make_types(inst, liars, att)
                    for p in ('MGM', 'VMGM-move-cap', 'VMGM-hist-cap', 'VMGM-hist-quar', 'RP-MGM'):
                        m, _ = one(inst, x0, sd, types, p, ref, max_rounds=cap)
                        rows.append(dict(family=family, seed=sd, start=sname, max_rounds=cap, k=k, attack=att,
                                         protocol=p, **m))
    return rows


# ------------------------------------------------------------------ E6: collusion (H5)
E6_PROTOCOLS = ['MGM', 'VMGM-hist-quar', 'VMGM-hist-soft']


def job_E6(family, sd):
    """Coordinated vs independent consistent liars (never flagged by Result 3), so the comparison isolates
    coordination. honest_loss is measured against everyone honest under the same protocol."""
    inst = M.add_fake_preferences(M.make_instance(sd, **M.FAMILIES[family]), LAM)
    rows = []
    for sname, x0 in starts(inst, sd):
        ref = honest_refs(inst, x0, sd, E6_PROTOCOLS)
        base = dict(family=family, seed=sd, start=sname)
        for k in (2, 3, 6):
            for pl in ('adjacent', 'spread'):
                liars = place_liars(inst, k, pl, seed=sd)
                lp = liar_adjacency(inst, liars)
                inst['coalition'] = set(liars)
                for att in E6_ATTACKS:
                    types = make_types(inst, liars, att)
                    for p in E6_PROTOCOLS:
                        m, _ = one(inst, x0, sd, types, p, ref)
                        rows.append(dict(base, k=k, placement=pl, liar_pairs=lp, attack=att, protocol=p, **m))
    return rows


JOBS = {'E1': job_E1, 'E2': job_E2, 'E3': job_E3, 'E4': job_E4, 'E5': job_E5, 'E6': job_E6}


def job_list(exp, n_seeds):
    seeds = range(SEED0, SEED0 + n_seeds)
    if exp == 'E4':
        return [(N, p, sd) for N in E4_N for p in E4_P for sd in seeds]
    if exp == 'E5':
        return [(f, sd) for f in M.FAMILIES for sd in seeds[:max(1, n_seeds // 5)]]
    return [(f, sd) for f in M.FAMILIES for sd in seeds]


def _call(exp, args):
    return JOBS[exp](*args)


def run_experiment(exp, n_seeds, workers, outdir):
    jobs = job_list(exp, n_seeds)
    # largest jobs first so the pool finishes evenly
    jobs.sort(key=lambda a: -(a[0] * a[0] * a[1]) if exp == 'E4' else 0)
    t0, rows, done = time.time(), [], 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futs = [pool.submit(_call, exp, a) for a in jobs]
        for f in as_completed(futs):
            rows.extend(f.result())              # re-raises InvariantError from a worker
            done += 1
            if done % max(1, len(jobs) // 10) == 0 or done == len(jobs):
                print(f'{exp}: {done}/{len(jobs)} jobs, {len(rows)} rows, {time.time() - t0:.0f}s',
                      file=sys.stderr, flush=True)
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, f'{exp}.csv')
    pd.DataFrame(rows).to_csv(path, index=False)
    print(f'{exp}: {len(rows)} rows, all invariants held, {time.time() - t0:.0f}s -> {path}', flush=True)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('exp', choices=list(JOBS) + ['all'])
    ap.add_argument('--seeds', type=int, default=50)
    ap.add_argument('--workers', type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument('--out', default='vmgm_results')
    a = ap.parse_args()
    for exp in (list(JOBS) if a.exp == 'all' else [a.exp]):
        run_experiment(exp, a.seeds, a.workers, a.out)


if __name__ == '__main__':
    main()
