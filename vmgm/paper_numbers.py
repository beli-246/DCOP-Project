"""Every number quoted in the paper text, recomputed from the E1-E5 CSVs.

Usage (from the repository root):
    python -m vmgm.paper_numbers vmgm_results/full
Prints the numbers and writes <dir>/paper_numbers.md. Each line names the place in
paper/DCOP_v4.tex where the number is used. Tables 2 and 5 and the figures are generated
separately by `python -m vmgm.figures vmgm_results/full paper`; the statistics with full
detail are in summary.md (`python -m vmgm.analysis vmgm_results/full`).

Definitions follow analysis.py and figures.py: "attacked runs" are E2 rows with k > 0,
"history + quarantine" is protocol VMGM-hist-quar, rho = F / F(honest MGM, same start).
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

from .analysis import PAIR, holm, paired

CAP_ONE_POST = ['VMGM-hist-cap', 'VMGM-move-cap', 'VMGM-move-quar']
HQ = 'VMGM-hist-quar'


def load(d):
    return [pd.read_csv(os.path.join(d, f'E{i}.csv')) for i in range(1, 6)]


def pct(v, nd=0):
    return f'{100 * v:.{nd}f}%'


def numbers(d):
    e1, e2, e3, e4, e5 = load(d)
    out = []

    def say(where, what, value):
        out.append(f'- **{where}** | {what}: {value}')

    def head(t):
        out.append(f'\n## {t}\n')

    att = e2[e2.k > 0]
    hq = att[att.protocol == HQ]

    head('Run counts (Experimental setup, Table 2 caption, Table 3)')
    for i, e in enumerate((e1, e2, e3, e4, e5), 1):
        say('setup', f'E{i} rows', f'{len(e):,}')
    say('setup', 'total rows', f'{sum(map(len, (e1, e2, e3, e4, e5))):,}')
    say('Table 2', 'V-MGM runs checked automatically',
        f'{sum(int(e.protocol.str.startswith("VMGM").sum()) for e in (e1, e2, e3, e4, e5)):,}')
    hq_all = pd.concat([e[e.protocol == HQ] for e in (e1, e2, e3, e4, e5)])
    say('Table 2', 'history + quarantine runs (all experiments)', f'{len(hq_all):,}')
    say('setup', 'instances per family (E1-E3)', e2.seed.nunique())
    say('setup', 'instances per family (E5)', e5.seed.nunique())
    say('setup', 'instances per (N, p) (E4)', e4.seed.nunique())

    head('Detection and false flags (abstract, Results RQ2, Table 4 H2a)')
    for a in ('block', 'churn', 'delayed', 'mixed', 'sabotage', 'maxbound'):
        by_k = hq[hq.attack == a].groupby('k').det_rate.mean()
        say('RQ2', f'{a}: share of liars flagged by k', ', '.join(f'k={k}: {pct(v, 1)}' for k, v in by_k.items()))
    ch = hq[hq.attack == 'churn']
    miss = ch[ch.det_rate < 1]
    say('RQ2', 'churn runs with an unflagged churner', f'{len(miss)} of {len(ch):,} '
        f'(those runs ended after {int(miss.rounds.min())}-{int(miss.rounds.max())} rounds)')
    dl = hq[hq.attack == 'delayed']
    say('RQ2', 'delayed (all k): runs with an unflagged delayed liar that ended before round 20',
        f'{int(((dl.det_rate < 1) & (dl.rounds < 20)).sum())} of {int((dl.det_rate < 1).sum())}')
    c1 = e1[(e1.protocol == HQ) & (e1.attack == 'churn')]
    say('abstract', 'churn, E1: share of churners flagged by k (E1 and E2 together give the abstract range)',
        ', '.join(f'k={k}: {pct(v, 1)}' for k, v in c1.groupby('k').det_rate.mean().items()))
    vm = e2[e2.protocol.str.startswith('VMGM')]
    say('RQ2', 'false flags in all V-MGM runs of E2', int(vm.false_flags.sum()))

    head('Termination (abstract, RQ2, Table 4 H2b, E5)')
    for p in ('MGM', 'RP-MGM', HQ):
        say('RQ2', f'{p}: attacked runs finished', pct(att[att.protocol == p].finished.mean()))
    co = att[att.protocol.isin(CAP_ONE_POST)]
    by_k = co.groupby('k').finished.mean()
    say('RQ2', 'cap-only and one-post: attacked runs finished',
        f'{pct(co.finished.mean())} (by k: {", ".join(pct(v) for v in by_k)})')
    say('Table 4 H2b', 'range of the pooled finish rate over MGM, RP-MGM, cap-only, one-post',
        f'{pct(att[att.protocol == "MGM"].finished.mean())}-{pct(att[att.protocol == "RP-MGM"].finished.mean())}')
    say('RQ2', 'history + quarantine finished (all experiments)', pct(hq_all.finished.mean(), 1))
    w = e5.pivot_table(index=['family', 'seed', 'start', 'k', 'attack', 'protocol'], columns='max_rounds',
                       values='finished')
    say('RQ2/E5', 'runs whose finished status changes from 300 to 1000 rounds', int((w[300] != w[1000]).sum()))
    say('RQ1', 'RP-MGM under churn, attacked runs finished (E2)',
        pct(att[(att.protocol == 'RP-MGM') & (att.attack == 'churn')].finished.mean()))
    r1 = e1[(e1.protocol == 'RP-MGM') & (e1.attack == 'churn') & (e1.k > 0)]
    say('RQ1', 'RP-MGM under churn, runs finished (E1)', f'{int(r1.finished.sum())} of {len(r1)}')
    for p in ('MGM', 'RP-MGM'):
        say('Table 4 H2b', f'{p}: runs finished (E5, both round limits)', pct(e5[e5.protocol == p].finished.mean()))
    say('Table 2', 'cap-only and one-post: runs finished (E5, both round limits)',
        pct(e5[e5.protocol.isin(CAP_ONE_POST)].finished.mean()))
    big = e4[(e4.protocol == HQ) & (e4.N == 48) & (e4.k == 12)]
    say('RQ4', 'N=48, k=12, history + quarantine finished', f'{pct(big.finished.mean())} of {len(big)} runs')

    head('Direct damage (Result 4, Table 4 H2c, Figure 1a)')
    say('RQ2', 'largest per-exam direct damage, E2 history + quarantine',
        f'{hq.dmg_exam_max.max():.2f} g_max over {len(hq):,} runs')
    say('RQ2', 'largest per-exam direct damage, all history + quarantine',
        f'{hq_all.dmg_exam_max.max():.2f} g_max over {len(hq_all):,} runs')
    say('Figure 1a', 'largest per-exam direct damage, cap only (E2)',
        f'{att[att.protocol == "VMGM-hist-cap"].dmg_exam_max.max():.0f} g_max')
    say('Table 2', 'largest per-exam direct damage, cap only (E5, by round limit)',
        ', '.join(f'{r} rounds: {v:.0f} g_max' for r, v in
                  e5[e5.protocol == 'VMGM-hist-cap'].groupby('max_rounds').dmg_exam_max.max().items()))

    head('Total damage (abstract, RQ2, Table 4 H2d, Figure 1b)')
    rows = []
    for k, g in att.groupby('k'):
        r = {p: g[g.protocol == p].rho.mean() for p in ('MGM', HQ, 'control-quar', 'VMGM-hist-cap', 'RP-MGM')}
        r['k'] = k
        rows.append(r)
    for r in rows:
        share = (r['control-quar'] - 1) / (r[HQ] - 1)
        say('RQ2', f'k={r["k"]}: rho MGM / hist+quar / control / share of hist+quar excess also in control',
            f'{r["MGM"]:.2f} / {r[HQ]:.2f} / {r["control-quar"]:.2f} / {pct(share)}')
    t = paired(att[att.protocol.isin([HQ, 'control-quar'])], PAIR + ['placement', 'attack'], HQ, 'control-quar',
               'honest_loss', ['k'])
    for _, r in t.iterrows():
        say('RQ2', f'k={int(r.k)}: honest loss, hist+quar minus control', f'{r.mean_diff:.1f} +/- {r.ci:.1f}')
    ctl = att[att.protocol == 'control-quar']
    for k, g in ctl.groupby('k'):
        say('Figure 2', f'k={k}: control, honest departments\' share of the extra cost',
            pct(g.honest_loss.mean() / g.extra.mean()))

    head('Quarantine vs cap only (Results)')
    for k, g in att.groupby('k'):
        sel = g[g.attack.isin(['hijack', 'exag_naive'])]
        q, c = sel[sel.protocol == HQ].rho.mean(), sel[sel.protocol == 'VMGM-hist-cap'].rho.mean()
        say('Results', f'k={k}: selfish attacks (T1a, T2a) rho cap-only / quarantine / cost of quarantine',
            f'{c:.2f} / {q:.2f} / {q - c:.2f}')
    k3 = att[att.k == 3]
    for a in ('churn', 'mixed', 'sabotage'):
        g = k3[(k3.attack == a) & (k3.protocol == 'VMGM-hist-cap')]
        say('Results', f'k=3, {a}: cap-only rho / finished', f'{g.rho.mean():.2f} / {pct(g.finished.mean(), 2)}')

    head('Placement and record mode (RQ2, Result 2 footnote)')
    t = paired(hq[hq.k > 1].assign(protocol=hq[hq.k > 1].placement), PAIR + ['k', 'attack'], 'adjacent',
               'spread', 'rho', ['k'])
    say('RQ2', 'adjacent minus spread rho, smallest Holm p', f'{t.p_holm.min():.2f}')
    w = att[att.protocol.isin([HQ, 'VMGM-hist-quar-exec'])].pivot_table(
        index=PAIR + ['k', 'placement', 'attack'], columns='protocol', values='F')
    diff = (w[HQ] - w['VMGM-hist-quar-exec']).abs() > 1e-9
    say('Result 2', 'attacked runs where recording executed instead of posted claims changes F',
        f'{int(diff.sum())} of {len(diff):,}')

    head('Result 6 slack (Result 6, Table 2)')
    lr = pd.concat([e[(e.protocol == HQ) & (e.k > 0)].assign(gm=e['gmax'] if 'gmax' in e else 50)
                    for e in (e1, e2, e3, e4, e5)])
    allowed = 2 * lr.gm * 4 * lr.k
    say('Result 6', 'runs with liars ending above the starting cost',
        f'{int((lr.F > lr.F0).sum())} of {len(lr):,}; at most {pct(((lr.F - lr.F0) / allowed).max(), 1)} of the bound')

    head('Round bound (Result 5 with integer claims)')
    # rounds <= Phi_start + 1 <= F_start + |E_L| * g_max + 1 (the per-run Phi_start version is checked in every run)
    rb = pd.concat([e[e.protocol == HQ].assign(gm=e['gmax'] if 'gmax' in e else 50) for e in (e1, e2, e3, e4, e5)])
    rb = rb.assign(bound=rb.F0 + 4 * rb.k * rb.gm + 1)
    say('Result 5', 'history + quarantine: largest number of rounds, and largest rounds / (F_start + |E_L| g_max + 1)',
        f'{int(rb.rounds.max())} rounds; {pct((rb.rounds / rb.bound).max(), 1)} of the bound')

    head('H1 (RQ1, Table 4, Figure 3)')
    a1 = e1[e1.k > 0]
    for other in ('RP-MGM', 'DSA'):
        t = paired(a1, PAIR, 'MGM', other, 'rho', ['attack', 'k'])
        for att_name, g in t.groupby('attack'):
            say('RQ1', f'MGM minus {other}, {att_name}, k=1..3',
                f'{g.mean_diff.min():+.2f} to {g.mean_diff.max():+.2f} (largest Holm p {g.p_holm.max():.1e})')
    say('RQ1', 'RP-MGM mean rho by attack (E1)',
        ', '.join(f'{a}: {v:.2f}' for a, v in a1[a1.protocol == 'RP-MGM'].groupby('attack').rho.mean().items()))
    for a in ('block', 'churn'):
        g = a1[a1.attack == a]
        say('RQ1', f'{a}: mean rho MGM / history + quarantine',
            f'{g[g.protocol == "MGM"].rho.mean():.2f} / {g[g.protocol == HQ].rho.mean():.2f}')

    head('H3 (RQ3, Table 4, Figure 4)')
    say('RQ3', 'E3 liars flagged', int(e3.detected.sum()))
    for k in (1, 3):
        rows, ps = [], []
        for (a, s, lam), g in e3[e3.k == k].groupby(['attack', 'spread', 'lam']):
            r, p = stats.spearmanr(g.kappa, g.liar_profit)
            rows.append((a, s, lam, r))
            ps.append(p)
        adj = holm(ps)
        for a in ('exag_stretch', 'exag_consistent'):
            sel = [(r, q) for (aa, _, _, r), q in zip(rows, adj) if aa == a]
            n_up = sum(1 for r, q in sel if r > 0 and q < 0.05)
            say('RQ3', f'k={k}, {a}: settings where profit rises with kappa (Holm p<0.05)',
                f'{n_up} of {len(sel)} (Spearman {min(r for r, _ in sel):+.2f} to {max(r for r, _ in sel):+.2f})')
    for k in (1, 3):
        st = e3[(e3.k == k) & (e3.attack == 'exag_stretch')]
        m = st.groupby(['spread', 'lam', 'gmax']).liar_profit.mean()
        low = m[m.index.get_level_values('gmax') <= 25]
        say('RQ3', f'stretched liar, k={k}, mean profit for g_max <= 25 (kappa <= 0.56)',
            f'{low.min():+.1f} to {low.max():+.1f}')
        top = m[m.index.get_level_values('gmax') == 200]
        say('RQ3', f'stretched liar, k={k}, mean profit at g_max=200 (kappa 4.5)',
            f'{top.min():+.1f} to {top.max():+.1f}')
    sp = e3[(e3.k == 1) & (e3.attack == 'exag_stretch') & (e3.gmax == 200)]
    say('Figure 4', 'stretched liar, k=1, g_max=200: mean profit by (lambda, preference spread)',
        ', '.join(f'lam={lam}, spread={s}: {v:+.0f}' for (lam, s), v in
                  sp.groupby(['lam', 'spread']).liar_profit.mean().items()))
    t1b = e3[(e3.attack == 'exag_consistent') & (e3.spread == 1.0)].groupby(['k', 'lam']).liar_profit.mean()
    say('RQ3', 'clipped liar (T1b), preferences fill the scale: mean profit by (k, lambda)',
        ', '.join(f'k={k}, lam={lam}: {v:+.1f}' for (k, lam), v in t1b.items()))
    say('RQ3', 'kappa for g_max = 10, 25, 50, 100, 200',
        ', '.join(f'{v:.2f}' for v in e3.groupby('gmax').kappa.mean()))

    head('H4 (RQ4, Table 4, Figure 5)')
    k1 = e4[e4.k == 1]
    for a in ('block', 'churn', 'sabotage', 'sabotage_consistent'):
        rs = []
        for N, g in k1[(k1.attack == a) & (k1.protocol == 'MGM')].groupby('N'):
            rs.append(f'N={N}: {stats.spearmanr(g.liar_deg, g.extra)[0]:+.2f}')
        say('RQ4', f'{a}, MGM: Spearman(liar degree, extra cost) within N', ', '.join(rs))
        ga = e4[e4.attack == a]
        say('RQ4', f'{a}: reduction by history + quarantine, k=1 and N/4 pooled',
            pct(1 - ga[ga.protocol == HQ].extra.mean() / ga[ga.protocol == 'MGM'].extra.mean()))
        g = k1[k1.attack == a]
        mg, vq = g[g.protocol == 'MGM'].extra.mean(), g[g.protocol == HQ].extra.mean()
        say('RQ4', f'{a}, k=1: mean extra cost MGM / history + quarantine / reduction',
            f'{mg:.0f} / {vq:.0f} / {pct(1 - vq / mg)}')

    head('CP-SAT reference: distance from the best timetable (Setup, Results RQ2, Limitations)')
    path = os.path.join(d, 'cpsat.csv')
    if not os.path.exists(path):
        out.append('_(skipped: cpsat.csv not found; run python -m vmgm.cpsat)_')
    else:
        cp = pd.read_csv(path)
        for fam, g in cp.groupby('family'):
            fe = g[g.status != 'OPTIMAL']
            say('Setup', f'{fam}: instances solved to proven optimality',
                f'{int((g.status == "OPTIMAL").sum())} of {len(g)} (limit {g.time_limit.max():.0f} s)'
                + (f'; gap of the others median {pct(fe.gap.median(), 1)}, largest {pct(fe.gap.max(), 1)}'
                   if len(fe) else ''))
        # F / F_best <= F / optimum <= F / F_bound, reported as % above the best timetable
        j = e2.merge(cp[['family', 'seed', 'F_best', 'F_bound']], on=['family', 'seed'])
        j = j.assign(lo=j.F / j.F_best - 1, hi=j.F / j.F_bound - 1)
        hon = j[(j.k == 0) & (j.protocol == 'MGM')]
        for (fam, start), g in hon.groupby(['family', 'start']):
            say('RQ2', f'honest MGM above the best timetable, {fam}, {start} start',
                f'{pct(g.lo.mean())}' + ('' if (g.lo == g.hi).all() else f' to {pct(g.hi.mean())}'))
        hl = hon[hon.family == 'loose']
        say('RQ2', 'honest MGM above the best timetable, loose, both starts', pct(hl.lo.mean()))
        at = j[(j.k > 0) & j.protocol.isin(['MGM', HQ])]
        for p in ('MGM', HQ):
            g = at[(at.protocol == p) & (at.family == 'loose')]
            say('RQ2', f'{p} under attack above the best timetable, loose, by k',
                ', '.join(f'k={k}: {pct(v)}' for k, v in g.groupby('k').lo.mean().items()))
            g = at[at.protocol == p]
            say('RQ2', f'{p} under attack above the best timetable, both families, by k (range)',
                ', '.join(f'k={k}: {pct(gg.lo.mean())}-{pct(gg.hi.mean())}' for k, gg in g.groupby('k')))
    return '\n'.join(['# Numbers used in the paper', f'Source: `{d}`'] + out) + '\n'


def main(d):
    text = numbers(d)
    open(os.path.join(d, 'paper_numbers.md'), 'w', encoding='utf-8').write(text)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
    print(text)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'vmgm_results/full')
