"""Demo: one churning department, under plain MGM and under V-MGM (history check + quarantine).

Usage (from the repository root):
    python -m vmgm.demo                       # prints the story of the three runs
    python -m vmgm.demo --plot docs/screenshots/demo_cost.png

Uses the real engine (protocol.run) on one small fixed instance: 6 departments, 4 exams each,
10 slots. Department 0 churns (T3b): every round it posts the move with the largest public gain V and
claims V + g_max, the most the one-post check allows. So no single post is ever flagged, but its
claims about the same slots soon contradict each other.
"""
import argparse
import sys

from . import model as M
from .liars import make_types
from .protocol import PROTOCOLS, run

SEED, N, S, P = 9, 6, 10, 0.12        # chosen so the story is typical (see the commit that added this file)
LAM = 3.0
LIAR = 0
MGM_ROUNDS_SHOWN = 6


def setup():
    inst = M.add_fake_preferences(M.make_instance(SEED, N=N, S=S, p=P), LAM)
    return inst, M.greedy_start(inst)


def cost_per_round(inst, res):
    """Total cost F after each round, replaying the executed moves from the start."""
    x = list(res.x0)
    out = [M.F_cost(inst, x)]
    for rnd in res.trace:
        for m in rnd:
            x[m['e']] = m['to']
        out.append(M.F_cost(inst, x))
    return out


def describe(inst, res, name, rounds_shown=None):
    F = cost_per_round(inst, res)
    lines = [f'== {name} ==']
    shown = res.trace if rounds_shown is None else res.trace[:rounds_shown]
    for t, rnd in enumerate(shown, start=1):
        moves = []
        for m in rnd:
            who = f'dept {m["dept"]}' + (' (LIAR)' if m['dept'] == LIAR else '')
            moves.append(f'{who}: exam {m["e"]} slot {m["frm"]}->{m["to"]}, claims {m["claim"]:g}, public gain V={m["v"]:g}')
        flagged = [i for i, r in res.flag_round.items() if r == t]
        lines.append(f'round {t:3d}  F={F[t]:4d}  ' + ('; '.join(moves) if moves else '(no move)')
                     + (f'   <-- dept {flagged[0]} FLAGGED, quarantined from now on' if flagged else ''))
    if rounds_shown is not None and len(res.trace) > rounds_shown:
        lines.append(f'  ... {len(res.trace) - rounds_shown} more rounds of the same')
    status = 'finished' if not res.capped else 'did NOT finish (stopped at the round limit)'
    lines.append(f'result: {status} after {res.rounds} rounds, final cost F = {F[-1]}')
    return lines, F


def main(argv=None):
    ap = argparse.ArgumentParser(description='Demo: one churner under MGM and V-MGM.')
    ap.add_argument('--plot', help='also save a PNG of the cost per round')
    a = ap.parse_args(argv)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
    inst, x0 = setup()
    liar = make_types(inst, {LIAR}, 'churn')
    honest = ['honest'] * inst['N']
    runs = {
        'honest MGM (nobody lies)': run(inst, x0, honest, LAM, PROTOCOLS['MGM'], seed=SEED),
        'plain MGM, dept 0 churns': run(inst, x0, liar, LAM, PROTOCOLS['MGM'], seed=SEED),
        'V-MGM (history check + quarantine), dept 0 churns': run(inst, x0, liar, LAM,
                                                                 PROTOCOLS['VMGM-hist-quar'], seed=SEED),
    }
    print(f'Instance: {inst["N"]} departments x 4 exams, {inst["S"]} slots (2 per day), seed {SEED}. '
          f'Dept {LIAR} has {len(inst["nbr"][LIAR])} neighbouring departments. Start: greedy, F = {M.F_cost(inst, x0)}.\n')
    curves = {}
    for name, res in runs.items():
        lines, curves[name] = describe(inst, res, name,
                                       MGM_ROUNDS_SHOWN if name.startswith('plain') else None)
        print('\n'.join(lines) + '\n')
    v = runs['V-MGM (history check + quarantine), dept 0 churns']
    if LIAR in v.flag_round:
        print(explain_flag(inst, v))
    if a.plot:
        plot(curves, a.plot)
        print(f'\nplot saved to {a.plot}')


def explain_flag(inst, res):
    """Recompute the flagged post from the public board, exactly as every department does."""
    from .attacks import announce
    t = res.flag_round[LIAR]
    x = list(res.x0)
    for rnd in res.trace[:t - 1]:
        for m in rnd:
            x[m['e']] = m['to']
    claim, e, a = announce(inst, x, LIAR, 'churn', LAM)
    r = claim - M.V(inst, x, e, a)
    scores = res.flag_scores[LIAR][e]
    new = scores[x[e]] - r
    lines = [f'Why dept {LIAR} was flagged in round {t}:',
             f'  The board keeps a score per slot for each exam, built from the claims posted so far.',
             f'  Scores of exam {e} before round {t}: '
             + ', '.join(f'slot {s} -> {v:g}' for s, v in sorted(scores.items())),
             f'  In round {t} dept {LIAR} posts: exam {e} slot {x[e]}->{a}, claim {claim:g}, public gain '
             f'V={M.V(inst, x, e, a):g}, so its claimed private part is r = {claim:g} - {M.V(inst, x, e, a):g} = {r:g}.',
             f'  That gives slot {a} the score {scores[x[e]]:g} - {r:g} = {new:g}.']
    if a in scores and scores[a] != new:
        lines.append(f'  But slot {a} already has the score {scores[a]:g}: two claims about the same slots '
                     f'contradict each other, so no real preference can explain them. Flagged.')
    else:
        lines.append(f'  The scores would then spread by more than g_max = {inst["gmax"]}. Flagged.')
    lines.append(f'  Each post alone was within the scale (|r| <= {inst["gmax"]}), so the one-post check alone '
                 f'never flags it; only the history check does.')
    return '\n'.join(lines)


def plot(curves, path):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from .figures import STYLE
    colors = {'honest MGM (nobody lies)': ('#7f7f7f', ':'),
              'plain MGM, dept 0 churns': (STYLE['MGM']['color'], '--'),
              'V-MGM (history check + quarantine), dept 0 churns': (STYLE['VMGM-hist-quar']['color'], '-')}
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    for name, F in curves.items():
        c, ls = colors[name]
        ax.plot(range(len(F))[:41], F[:41], color=c, ls=ls, lw=1.8, label=name)
    ax.set_xlabel('Round')
    ax.set_ylabel('Total cost F')
    ax.set_title('One churning department (first 40 rounds; plain MGM never finishes)')
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)


if __name__ == '__main__':
    main()
