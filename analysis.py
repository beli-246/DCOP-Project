"""Statistics and summary tables for E1-E5, one section per hypothesis (H1-H4, H2 split a-d).

Usage (from the FAI folder):
    python3 -m vmgm.analysis vmgm_results/full
Writes vmgm_results/full/summary.md and prints it.

Statistics, as in the proposal: paired runs (same instance, start, seed), 95% confidence intervals
(t-based), Wilcoxon signed-rank tests, Holm correction within each hypothesis family.
Where runs cannot be paired (E4 across p or N: different instances), Spearman correlation is used.
"""
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

PAIR = ['family', 'seed', 'start']


# ------------------------------------------------------------------ helpers
def ci(x):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 2:
        return (float(x.mean()) if len(x) else float('nan')), float('nan'), len(x)
    h = stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))
    return float(x.mean()), float(h), len(x)


def wilcoxon_p(d):
    d = np.asarray(d, dtype=float)
    d = d[~np.isnan(d)]
    if len(d) == 0 or np.all(d == 0):
        return 1.0
    return float(stats.wilcoxon(d, zero_method='wilcox').pvalue)


def holm(pvals):
    p = np.asarray(pvals, dtype=float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, min(1.0, (len(p) - rank) * p[i]))
        adj[i] = run
    return adj


def fmt(m, h, nd=2):
    return f'{m:.{nd}f} ± {h:.{nd}f}' if not np.isnan(h) else f'{m:.{nd}f}'


def md_table(df):
    cols = list(df.columns)
    out = ['| ' + ' | '.join(map(str, cols)) + ' |', '|' + '---|' * len(cols)]
    for _, r in df.iterrows():
        out.append('| ' + ' | '.join(str(r[c]) for c in cols) + ' |')
    return '\n'.join(out)


def paired(df, key_cols, a, b, metric, by):
    """Paired difference metric(protocol a) - metric(protocol b), grouped by `by`."""
    rows = []
    for keys, g in df[df.protocol.isin([a, b])].groupby(by):
        w = g.pivot_table(index=key_cols, columns='protocol', values=metric)
        if a not in w or b not in w:
            continue
        d = (w[a] - w[b]).dropna()
        m, h, n = ci(d)
        rows.append(dict(zip(by, keys if isinstance(keys, tuple) else (keys,)), mean_diff=m, ci=h, n=n,
                         p=wilcoxon_p(d)))
    out = pd.DataFrame(rows)
    if len(out):
        out['p_holm'] = holm(out.p)
    return out


# ------------------------------------------------------------------ sections
def h1(d):
    e = pd.read_csv(os.path.join(d, 'E1.csv'))
    s = ['## H1 (E1): lying about gains hurts MGM more than RP-MGM and DSA',
         'Paired difference in rho. H1 is proven wrong for an attack if the MGM − RP-MGM interval includes 0.', '']
    for other in ('RP-MGM', 'DSA'):
        t = paired(e, PAIR, 'MGM', other, 'rho', ['attack', 'k'])
        t['MGM − ' + other] = [fmt(m, h) for m, h in zip(t.mean_diff, t.ci)]
        t['includes 0'] = (t.mean_diff - t.ci <= 0) & (t.mean_diff + t.ci >= 0)
        t['p (Holm)'] = t.p_holm.map(lambda v: f'{v:.1e}')
        s += [f'### MGM vs {other}', md_table(t[['attack', 'k', 'MGM − ' + other, 'includes 0', 'p (Holm)', 'n']]), '']
    m = e.groupby(['attack', 'protocol']).rho.mean().unstack().round(2).reset_index()
    s += ['### Mean rho by attack (all k)', md_table(m), '']
    return s


def h2(d):
    e = pd.read_csv(os.path.join(d, 'E2.csv'))
    hq = e[e.protocol == 'VMGM-hist-quar']
    s = ['## H2 (E2): k dishonest departments, history check + quarantine', '']
    # H2a detection
    det = hq[hq.k > 0].groupby(['attack', 'k']).det_rate.mean().unstack().round(2).reset_index()
    s += ['### H2a: fraction of liars flagged (H2a proven wrong if < 0.95 for block or churn)', md_table(det), '']
    # H2b finishing, all protocols
    fin = e[e.k > 0].groupby(['protocol', 'k']).finished.mean().unstack().round(3).reset_index()
    s += ['### H2b: fraction of runs that finished within 300 rounds', md_table(fin), '']
    # H2c bound
    c = hq[hq.k > 0]
    s += ['### H2c: direct damage (Result 4)',
          f'Largest student cost added by one liar exam\'s own moves: **{c.dmg_exam_max.max():.3f} · g_max** '
          f'over {len(c)} runs (bound: < 1). False flags in all V-MGM runs: '
          f'**{int(e[e.protocol.str.startswith("VMGM")].false_flags.sum())}**.', '']
    # H2d total damage, with quarantine control
    rows = []
    for k, g in e[e.k > 0].groupby('k'):
        r = {'k': k}
        for p in ('MGM', 'VMGM-hist-cap', 'VMGM-hist-quar', 'control-quar', 'RP-MGM'):
            r[p] = fmt(*ci(g[g.protocol == p].rho)[:2])
        rows.append(r)
    s += ['### H2d: total damage, rho (all attacks pooled) and the quarantine control',
          '`control-quar`: everyone honest, the flagged liars\' departments quarantined at the same rounds. '
          'It measures what quarantine itself costs.', md_table(pd.DataFrame(rows)), '']
    keys = PAIR + ['k', 'placement', 'attack']
    t = paired(e[e.k > 0], keys, 'VMGM-hist-quar', 'control-quar', 'honest_loss', ['k'])
    t['hist-quar − control (honest loss)'] = [fmt(m, h, 1) for m, h in zip(t.mean_diff, t.ci)]
    t['p (Holm)'] = t.p_holm.map(lambda v: f'{v:.1e}')
    s += ['Honest departments\' loss: lying + quarantine vs quarantine alone (positive = lying hurts honest '
          'departments beyond what quarantine costs):', md_table(t[['k', 'hist-quar − control (honest loss)', 'p (Holm)', 'n']]), '']
    # per attack table at k = 3
    k3 = e[e.k == 3].groupby(['attack', 'protocol']).rho.mean().unstack().round(2).reset_index()
    s += ['### rho by attack and protocol, k = 3', md_table(k3), '']
    # placement
    t = paired(hq[hq.k > 1].assign(protocol=hq[hq.k > 1].placement), PAIR + ['k', 'attack'], 'adjacent', 'spread',
               'rho', ['k'])
    t['adjacent − spread'] = [fmt(m, h, 3) for m, h in zip(t.mean_diff, t.ci)]
    t['p (Holm)'] = t.p_holm.map(lambda v: f'{v:.1e}')
    s += ['### Placement (hist-quar): rho, liars adjacent − spread', md_table(t[['k', 'adjacent − spread', 'p (Holm)', 'n']]), '']
    # record mode
    w = e[e.protocol.isin(['VMGM-hist-quar', 'VMGM-hist-quar-exec'])].pivot_table(
        index=PAIR + ['k', 'placement', 'attack'], columns='protocol', values='F')
    same = (w['VMGM-hist-quar'] == w['VMGM-hist-quar-exec']).mean()
    s += [f'### Record mode: posted vs executed claims give the same final cost in **{same:.1%}** of runs.', '']
    return s


def h3(d):
    e = pd.read_csv(os.path.join(d, 'E3.csv'))
    s = ['## H3 (E3): undetectable lying still pays, more as kappa grows',
         'Liar profit = drop in the liar\'s own objective J vs honest play (positive = lying pays). '
         'No liar was flagged in any E3 run. H3 is proven wrong if the profit interval includes 0 at every '
         'kappa, or profit does not rise with kappa.', '']
    rows, ps = [], []
    for (att, spread, lam), g in e[e.k == 1].groupby(['attack', 'spread', 'lam']):
        r = dict(attack=att, spread=spread, lam=lam)
        for gm, gg in g.groupby('gmax'):
            m, h, _ = ci(gg.liar_profit)
            r[f'g_max={gm} (kappa {gg.kappa.mean():.2f})'] = fmt(m, h, 1)
        rho_s, p = stats.spearmanr(g.kappa, g.liar_profit)
        r['Spearman(kappa, profit)'] = f'{rho_s:.2f}'
        ps.append(p)
        rows.append(r)
    t = pd.DataFrame(rows)
    t['p (Holm)'] = [f'{v:.1e}' for v in holm(ps)]
    s += ['### k = 1', md_table(t), '']
    k3 = e.groupby(['attack', 'k', 'spread']).liar_profit.mean().unstack().round(1).reset_index()
    s += ['### Mean profit by k and spread (all g_max, lam)', md_table(k3), '']
    return s


def h4(d):
    e = pd.read_csv(os.path.join(d, 'E4.csv'))
    s = ['## H4 (E4): damage grows with the liar\'s neighbours and with overlap p',
         'Different N and p are different instances, so Spearman correlation is used instead of paired tests. '
         'Damage = extra cost over honest MGM, per liar.', '']
    e = e.assign(extra_per_liar=e.extra / e.k)
    rows, ps = [], []
    for (att, prot), g in e[e.k == 1].groupby(['attack', 'protocol']):
        r1, p1 = stats.spearmanr(g.liar_deg, g.extra_per_liar)
        r2, p2 = stats.spearmanr(g.p, g.extra_per_liar)
        rows.append(dict(attack=att, protocol=prot, **{'Spearman(degree, damage)': f'{r1:.2f}',
                                                       'Spearman(p, damage)': f'{r2:.2f}'}))
        ps += [p1, p2]
    t = pd.DataFrame(rows)
    adj = holm(ps)
    t['p deg (Holm)'] = [f'{v:.1e}' for v in adj[0::2]]
    t['p p (Holm)'] = [f'{v:.1e}' for v in adj[1::2]]
    s += ['### k = 1', md_table(t), '']
    m = e.groupby(['protocol', 'attack', 'N', 'p']).rho.mean().unstack().round(2).reset_index()
    s += ['### Mean rho by N and p (k = 1 and k = 25% of N pooled)', md_table(m), '']
    f = e[e.protocol == 'VMGM-hist-quar'].groupby(['N', 'k']).agg(
        finished=('finished', 'mean'), det=('det_rate', 'mean'), dmg_max=('dmg_exam_max', 'max')).round(3).reset_index()
    s += ['### hist-quar at scale', md_table(f), '']
    return s


def e5(d):
    e = pd.read_csv(os.path.join(d, 'E5.csv'))
    t = e.groupby(['protocol', 'attack', 'max_rounds']).finished.mean().unstack().round(2).reset_index()
    return ['## E5: is "did not finish" caused by the 300-round limit?',
            'Fraction finished with a 300 vs 1000 round limit. If a protocol does not finish at 300 but does at '
            '1000, the limit was the problem; if it does not finish at either, it is genuinely stuck.',
            md_table(t), '']


def main(d):
    out = ['# V-MGM experiments: summary', f'Source: `{d}`', '']
    for f in (h1, h2, h3, h4, e5):
        try:
            out += f(d)
        except FileNotFoundError as err:
            out += [f'_(skipped: {err.filename} not found)_', '']
    text = '\n'.join(out)
    open(os.path.join(d, 'summary.md'), 'w').write(text)
    print(text)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'vmgm_results/full')
