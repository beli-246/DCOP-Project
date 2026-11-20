"""pyDCOP agreement check (issue #5). Runs in the separate pyDCOP environment (see README.md):

    conda activate pydcop
    python -m validation.pydcop.check            # reuse saved pyDCOP runs in runs/, if present
    python -m validation.pydcop.check --rerun    # run pyDCOP's MGM again on all 20 instances

pyDCOP's MGM is run twice per instance: 'stock' (the `pydcop` command as installed) and 'fixed'
(`pydcop_fixed.py`: the same command with one fix to MGM's stale current cost, see that file).

It needs the YAML files written by `python -m validation.pydcop.export` (project environment).
vmgm.model and vmgm.protocol use only the standard library, so they import under Python 3.8.

Three checks on the loose family, seeds 100-119:
  1. Same cost model: for 100 random timetables per instance, pyDCOP's DCOP.solution_cost on the
     exported YAML equals our vmgm.model.F_cost (and reports no hard violation).
  2. Same notion of local optimum: pyDCOP's MGM (`pydcop solve --algo mgm`, stop_cycle 500), run with
     agent d<i> hosting department i's exams, ends at x with (a) its reported cost == F_cost(inst, x)
     and (b) no single-exam improving move in our model: best_move(inst, x, i, g)[1] is None for all i.
  3. Similar final quality: final cost of pyDCOP MGM vs our honest MGM from the same start.

Writes validation/pydcop/results.md; every number in it is computed here.
"""
import argparse
import importlib.metadata as md
import json
import os
import platform
import random
import statistics
import subprocess
import sys

from pydcop.dcop.yamldcop import load_dcop_from_file

from vmgm import model as M
from vmgm.protocol import PROTOCOLS, run

from .export import FAMILY, SEEDS, instance, start, var

HERE = os.path.dirname(os.path.abspath(__file__))
INST = os.path.join(HERE, 'instances')
RUNS = os.path.join(HERE, 'runs')
TIMETABLES = 100
STOP_CYCLE = 500
INFINITY = 10**9            # larger than any cost in our instances, so no cost is read as "hard"
VARIANTS = {'stock': ['pydcop'],
            'fixed': [sys.executable, os.path.join(HERE, 'pydcop_fixed.py')]}


def paths(seed, variant='stock'):
    base = os.path.join(INST, f'{FAMILY}_{seed}')
    return base + '.yaml', base + '_dist.yaml', os.path.join(RUNS, variant, f'{FAMILY}_{seed}.json')


def to_assignment(x):
    return {var(e): s for e, s in enumerate(x)}


def from_assignment(inst, asg):
    return [asg[var(e)] for e in range(inst['E'])]


def solve_pydcop(seed, variant):
    dcop_file, dist_file, out = paths(seed, variant)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = VARIANTS[variant] + ['--timeout', '300', '--output', out, 'solve', '--algo', 'mgm',
                               '-p', f'stop_cycle:{STOP_CYCLE}', '-d', dist_file, dcop_file]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def check_cost_model(inst, dcop, seed):
    """Check 1. Returns (number compared, number of mismatches)."""
    rng = random.Random(seed)
    bad = 0
    for _ in range(TIMETABLES):
        x = [rng.randrange(inst['S']) for _ in range(inst['E'])]
        hard, soft = dcop.solution_cost(to_assignment(x), INFINITY)
        bad += hard != 0 or soft != M.F_cost(inst, x)
    return TIMETABLES, bad


def check_local_optimum(inst, dcop, result):
    """Check 2. Returns a dict with the pyDCOP final x and the outcome of (a) and (b)."""
    x = from_assignment(inst, result['assignment'])
    hard, soft = dcop.solution_cost(result['assignment'], INFINITY)
    improving = [i for i in range(inst['N']) if M.best_move(inst, x, i, inst['g'])[1] is not None]
    return dict(x=x, reported=result['cost'], F=M.F_cost(inst, x), api=soft, hard=hard,
                cost_ok=result['cost'] == M.F_cost(inst, x) == soft and hard == 0,
                improving=improving, status=result['status'], cycle=result['cycle'])


def our_mgm(inst, seed):
    n = inst['N']
    return run(inst, start(inst, seed), ['honest'] * n, 3.0, PROTOCOLS['MGM'], seed=seed)


def versions():
    out = {'python': platform.python_version(), 'platform': platform.platform()}
    for pkg in ('pydcop', 'pulp', 'networkx', 'numpy', 'pyyaml'):
        try:
            out[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            out[pkg] = 'not installed'
    try:
        direct = json.loads(md.distribution('pydcop').read_text('direct_url.json') or '{}')
        out['pydcop source'] = f"{direct['url']} @ {direct['vcs_info']['commit_id']}"
    except (KeyError, TypeError, ValueError):
        out['pydcop source'] = 'PyPI'
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--rerun', action='store_true', help='run pyDCOP MGM again even if runs/ exists')
    args = ap.parse_args(argv)

    rows = []
    for seed in SEEDS:
        inst = instance(seed)
        dcop_file = paths(seed)[0]
        dcop = load_dcop_from_file([dcop_file])
        n1, bad1 = check_cost_model(inst, dcop, seed)
        ours = our_mgm(inst, seed)
        row = dict(seed=seed, n1=n1, bad1=bad1, start=M.F_cost(inst, start(inst, seed)),
                   ours=M.F_cost(inst, ours.x), ours_rounds=ours.rounds, ours_capped=ours.capped,
                   ours_local=all(M.best_move(inst, ours.x, i, inst['g'])[1] is None
                                  for i in range(inst['N'])))
        for variant in VARIANTS:
            out = paths(seed, variant)[2]
            if args.rerun or not os.path.exists(out):
                solve_pydcop(seed, variant)
                print(f'seed {seed}: pyDCOP MGM ({variant}) saved to {os.path.relpath(out, HERE)}',
                      file=sys.stderr)
            with open(out) as fh:
                row[variant] = check_local_optimum(inst, dcop, json.load(fh))
        rows.append(row)

    write_results(rows)
    ok1 = all(r['bad1'] == 0 for r in rows)
    ok2 = {v: all(r[v]['cost_ok'] and not r[v]['improving'] for r in rows) for v in VARIANTS}
    print(f'check 1 {"PASS" if ok1 else "FAIL"}; check 2 stock pyDCOP {"PASS" if ok2["stock"] else "FAIL"}, '
          f'fixed pyDCOP {"PASS" if ok2["fixed"] else "FAIL"}; see validation/pydcop/results.md')
    return 0 if ok1 and ok2['fixed'] else 1


def write_results(rows):
    n = len(rows)
    tot1 = sum(r['n1'] for r in rows)
    bad1 = sum(r['bad1'] for r in rows)
    ours = [r['ours'] for r in rows]
    lines = [
        '# pyDCOP agreement check (issue #5)',
        '',
        'Generated by `python -m validation.pydcop.check`; do not edit by hand. Raw pyDCOP outputs: '
        '`runs/stock/`, `runs/fixed/`.',
        '',
        '## Versions',
        '',
    ]
    lines += [f'* {k}: `{val}`' for k, val in versions().items()]
    lines += [
        '',
        f'pyDCOP MGM command (per instance): `pydcop --timeout 300 --output runs/stock/{FAMILY}_<seed>.json '
        f'solve --algo mgm -p stop_cycle:{STOP_CYCLE} -d instances/{FAMILY}_<seed>_dist.yaml '
        f'instances/{FAMILY}_<seed>.yaml` (default `break_mode: lexic`, thread mode). The "fixed" runs use '
        '`python pydcop_fixed.py` in place of `pydcop`, with the same arguments.',
        '',
        '## Mapping',
        '',
        '* exam `e` -> pyDCOP variable `x_e`, domain = slots `0..S-1`; `g[e]` -> unary extensional '
        'constraint `g_e`;',
        '* pair `(e, f)` with `c` students -> binary extensional constraint `n_e_f` whose table is '
        'generated by calling `vmgm.model.pc(a, b, c)`;',
        '* an exam that shares no students gets an all-zero constraint `link_e_f` with the next exam of '
        'its department (it changes no cost; it makes pyDCOP treat the exam like any other, see README.md);',
        '* department `i` -> pyDCOP agent `d<i>`, hosting the computations of its own 4 exams '
        '(distribution file `instances/<name>_dist.yaml`);',
        '* objective `min`; every variable starts at our random start `M.random_start(inst, 1000 + seed)`.',
        '',
        "pyDCOP's MGM runs one computation per **variable**: a variable moves when its gain beats the gains "
        'of all variables it shares a constraint with. Its local cost for exam `e` is `g_e` plus every '
        'binary term containing `e`, so its gain for a move of `e` is exactly the drop of our `F_cost` '
        'for that single-exam move. A pyDCOP fixed point (no variable can lower its local cost) is '
        'therefore the same as our local optimum (for every department `i`, '
        '`best_move(inst, x, i, g)[1] is None`: no single-exam move lowers `F`). The two algorithms differ '
        'in who moves in a round (pyDCOP: any number of non-adjacent exams, possibly several of one '
        'department; ours: at most one exam per department, departments compared with neighbouring '
        'departments), so their runs differ, but not what they stop at.',
        '',
        '## Check 1: same cost model',
        '',
        f'{tot1} random timetables ({TIMETABLES} per instance, {n} instances): pyDCOP '
        f'`DCOP.solution_cost` == `vmgm.model.F_cost` on **{tot1 - bad1} / {tot1}** '
        f'({"PASS" if bad1 == 0 else "FAIL"}).',
        '',
        "## Check 2: pyDCOP MGM's final assignment is a local optimum of our model",
        '',
        '| pyDCOP MGM | (a) reported cost == `F_cost` == `solution_cost` | (b) no improving single-exam move | '
        'departments with an improving move (total) |',
        '|---|---|---|---|',
    ]
    for v in VARIANTS:
        a = sum(r[v]['cost_ok'] for r in rows)
        b = sum(not r[v]['improving'] for r in rows)
        lines.append(f'| {v} | {a} / {n} | {b} / {n} | {sum(len(r[v]["improving"]) for r in rows)} |')
    lines += [
        '',
        "The stock failures come from pyDCOP's MGM, not from the cost model (check 1 and 2(a) agree "
        'exactly): a variable computes its current local cost only in its first cycle and afterwards only '
        'subtracts its own gains, so when a neighbour moves, the cost it compares against is stale and an '
        'improving move can be missed (the stock run stops at cycle 500 although improving moves are '
        'left). `pydcop_fixed.py` recomputes the cost at the start of every cycle and changes nothing '
        'else; see README.md.',
        '',
        '## Check 3: final quality, pyDCOP MGM vs our honest MGM (same start)',
        '',
        f'* mean starting cost: {statistics.mean(r["start"] for r in rows):.2f}',
        f'* our MGM: mean final cost **{statistics.mean(ours):.2f}**; finished on '
        f'{sum(not r["ours_capped"] for r in rows)} / {n}, local optimum on {sum(r["ours_local"] for r in rows)} / {n}.',
    ]
    for v in VARIANTS:
        theirs = [r[v]['F'] for r in rows]
        diff = [t - o for t, o in zip(theirs, ours)]
        lines.append(f'* pyDCOP MGM ({v}): mean final cost **{statistics.mean(theirs):.2f}**; paired difference '
                     f'(pyDCOP - ours) mean **{statistics.mean(diff):.2f}**, sd {statistics.stdev(diff):.2f}, '
                     f'min {min(diff)}, max {max(diff)}; pyDCOP lower on {sum(d < 0 for d in diff)}, equal on '
                     f'{sum(d == 0 for d in diff)}, higher on {sum(d > 0 for d in diff)} of {n}.')
    lines += [
        '',
        'Our MGM and the fixed pyDCOP MGM both end at local optima of the same cost function from the '
        'same start, but the runs take different paths (different movers per round, random tie-breaking '
        'among equally good slots in pyDCOP, thread timing), so the end points differ, and a re-run of '
        'pyDCOP can give slightly different values. We claim only how close the means are, not that the '
        'runs are the same.',
        '',
        '## Per instance',
        '',
        '| seed | start F | our MGM F (rounds) | stock pyDCOP F | stock improving depts | fixed pyDCOP F | '
        'fixed improving depts | check 1 mismatches |',
        '|---|---|---|---|---|---|---|---|',
    ]
    for r in rows:
        st, fx = r['stock'], r['fixed']
        lines.append(f"| {r['seed']} | {r['start']} | {r['ours']} ({r['ours_rounds']}) | {st['F']} | "
                     f"{len(st['improving'])} | {fx['F']} | {len(fx['improving'])} | {r['bad1']} |")
    lines.append('')
    with open(os.path.join(HERE, 'results.md'), 'w') as fh:
        fh.write('\n'.join(lines))


if __name__ == '__main__':
    sys.exit(main())
