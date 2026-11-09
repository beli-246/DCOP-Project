"""Invariant sweep over k dishonest departments (also the skeleton of the E2 runner).

Every run goes through check_all, so the sweep stops with an InvariantError if any proven
property fails. Results go to a CSV, one row per run.

Usage (from the repository root):
    python3 -m vmgm.sweep OUT.csv N_SEEDS [k1,k2,...]
"""
import csv
import sys
import time

from . import model as M
from .attacks import ALL_ATTACKS
from .invariants import check_all
from .liars import liar_adjacency, make_types, place_liars
from .protocol import PROTOCOLS, run

LAM = 3.0
SWEEP_PROTOCOLS = ['MGM', 'VMGM-hist-cap', 'VMGM-hist-quar']
ATTACK_SETS = {a: a for a in ALL_ATTACKS}
ATTACK_SETS['mixed'] = ['block', 'churn', 'sabotage_consistent', 'exag_consistent']


def main(out, n_seeds, ks):
    cols = ['family', 'seed', 'start', 'k', 'placement', 'liar_pairs', 'attack', 'protocol', 'rounds', 'finished',
            'detected', 'false_flags', 'F0', 'F', 'F_mgm_honest', 'rho', 'dmg_unflagged', 'dmg_total',
            'F_bound', 'secs']
    t_start = time.time()
    n = 0
    with open(out, 'w', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for family in ('loose', 'tight'):
            for sd in range(n_seeds):
                inst = M.add_fake_preferences(M.make_instance(sd, **M.FAMILIES[family]), LAM)
                for sname, x0 in (('random', M.random_start(inst, 1000 + sd)), ('greedy', M.greedy_start(inst))):
                    honest = ['honest'] * inst['N']
                    f_ref = M.F_cost(inst, run(inst, x0, honest, LAM, PROTOCOLS['MGM'], seed=sd).x)
                    for k in ks:
                        for placement in (('random',) if k == 0 else ('adjacent', 'spread')):
                            liars = place_liars(inst, k, placement, seed=sd)
                            for aname, att in (ATTACK_SETS.items() if k else [('none', 'honest')]):
                                types = make_types(inst, liars, att)
                                for pname in SWEEP_PROTOCOLS:
                                    prot = PROTOCOLS[pname]
                                    t0 = time.time()
                                    res = run(inst, x0, types, LAM, prot, seed=sd, max_rounds=300)
                                    chk = check_all(inst, res, types, prot)
                                    F = M.F_cost(inst, res.x)
                                    w.writerow(dict(
                                        family=family, seed=sd, start=sname, k=k, placement=placement,
                                        liar_pairs=liar_adjacency(inst, liars), attack=aname, protocol=pname,
                                        rounds=res.rounds, finished=not res.capped,
                                        detected=len(res.flagged & liars), false_flags=len(res.flagged - liars),
                                        F0=M.F_cost(inst, x0), F=F, F_mgm_honest=f_ref, rho=F / f_ref,
                                        dmg_unflagged=chk.get('dmg_unflagged', ''), dmg_total=chk.get('dmg_total', ''),
                                        F_bound=chk.get('F_bound', ''), secs=round(time.time() - t0, 3)))
                                    n += 1
                print(f'{family} seed {sd}: {n} runs, {time.time() - t_start:.0f}s', file=sys.stderr, flush=True)
    print(f'{n} runs, all invariants held. Written to {out}')


if __name__ == '__main__':
    ks = [int(v) for v in sys.argv[3].split(',')] if len(sys.argv) > 3 else [0, 1, 2, 3, 6]
    main(sys.argv[1], int(sys.argv[2]), ks)
