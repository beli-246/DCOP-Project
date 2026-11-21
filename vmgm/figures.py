"""Phase 4: paper figures (PDF + PNG) and LaTeX tables, generated from the E1-E6 CSVs.

Usage (from the repository root):
    python3 -m vmgm.figures vmgm_results/full paper
Reads <csv_dir>/E1-E6.csv (E6 optional) and writes <out_dir>/figures/*.pdf|png and <out_dir>/tables/*.tex.
<out_dir> defaults to <csv_dir>; pass `paper` so LaTeX picks the files up directly.

Every number in a figure or table comes from the CSVs, so re-running the experiments
re-generates everything. Figures are static, light-mode, print-oriented.

Colour follows the entity in every figure (reference palette, fixed slot order):
  V-MGM history+quarantine (our method) = blue      slot 1
  MGM                                   = orange    slot 2
  quarantine control                    = aqua      slot 3
  V-MGM history+cap                     = yellow    slot 4
  RP-MGM, DSA (claim-free baselines)    = neutral greys
Every series also has its own marker / line style (secondary encoding for print and CVD).
"""
import os
import sys

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402,F401
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

# ------------------------------------------------------------------ style
INK, INK2, MUTED, GRID, SURFACE = '#0b0b0b', '#52514e', '#8a8984', '#e4e3df', '#ffffff'
STYLE = {
    'VMGM-hist-quar': dict(color='#2a78d6', marker='o', ls='-', label='V-MGM: history + quarantine'),
    'MGM': dict(color='#eb6834', marker='s', ls='--', label='MGM'),
    'control-quar': dict(color='#1baf7a', marker='^', ls=':', label='Quarantine alone (control)'),
    'VMGM-hist-cap': dict(color='#eda100', marker='D', ls='-.', label='V-MGM: history + cap only'),
    'RP-MGM': dict(color='#52514e', marker='v', ls=(0, (1, 1)), label='RP-MGM'),
    'DSA': dict(color='#a8a7a1', marker='X', ls=(0, (3, 1, 1, 1)), label='DSA'),
    'VMGM-hist-soft': dict(color='#7b3fbf', marker='P', ls='-', label='V-MGM: history + soft quarantine'),
    'control-soft': dict(color='#b48ee0', marker='p', ls=':', label='Soft quarantine alone (control)'),
}
SEQ = ['#86b6ef', '#2a78d6', '#104281']           # sequential blue, ordinal (light -> dark)
ATTACK_LABEL = {
    'block': 'Block (T3a)', 'churn': 'Churn (T3b)', 'hijack': 'Inflate huge (T2a)',
    'maxbound': 'Inflate in scale (T2b)', 'sabotage': 'Sabotage (T4)', 'exag_naive': 'Exaggerate naive (T1a)',
    'exag_consistent': 'Exaggerate consistent (T1b)', 'sabotage_consistent': 'Consistent sabotage (new)',
    'delayed': 'Delayed contradiction (new)', 'mixed': 'Mixed attacks',
}

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 8, 'axes.titlesize': 8.5, 'axes.labelsize': 8,
    'xtick.labelsize': 7.5, 'ytick.labelsize': 7.5, 'legend.fontsize': 7.5,
    'axes.edgecolor': MUTED, 'axes.labelcolor': INK2, 'xtick.color': INK2, 'ytick.color': INK2,
    'text.color': INK, 'axes.titlecolor': INK, 'axes.titleweight': 'bold', 'axes.titlelocation': 'left',
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': GRID,
    'grid.linewidth': 0.6, 'axes.axisbelow': True, 'lines.linewidth': 1.5, 'lines.markersize': 5,
    'legend.frameon': False, 'figure.facecolor': SURFACE, 'axes.facecolor': SURFACE,
    'savefig.bbox': 'tight', 'savefig.pad_inches': 0.03, 'pdf.fonttype': 42,
})
FULL_W = 6.9      # inches, full text width


def ci(x):
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 2:
        return (float(x.mean()) if len(x) else np.nan), 0.0
    return float(x.mean()), float(stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)))


def line(ax, xs, ms, hs, key, **kw):
    st = STYLE[key]
    ax.errorbar(xs, ms, yerr=hs, color=st['color'], marker=st['marker'], ls=st['ls'], capsize=2,
                elinewidth=1, markeredgecolor=SURFACE, markeredgewidth=0.8, label=st['label'], **kw)


def save(fig, d, name):
    os.makedirs(os.path.join(d, 'figures'), exist_ok=True)
    for ext in ('pdf', 'png'):
        # no creation date in the PDF, so regenerating gives byte-identical files
        meta = {'CreationDate': None} if ext == 'pdf' else None
        fig.savefig(os.path.join(d, 'figures', f'{name}.{ext}'), dpi=200, metadata=meta)
    plt.close(fig)


# ------------------------------------------------------------------ figure 1: the three guarantees
def fig_guarantees(d, e2):
    fig, axs = plt.subplots(1, 3, figsize=(FULL_W, 2.4), gridspec_kw=dict(wspace=0.42))
    att = e2[e2.k > 0]

    # (a) direct damage: proven bound
    ax = axs[0]
    hq = att[att.protocol == 'VMGM-hist-quar'].dmg_exam_max.clip(lower=0)
    cap_max = att[att.protocol == 'VMGM-hist-cap'].dmg_exam_max.max()
    ax.hist(hq, bins=np.arange(0, 1.05, 0.05), color=STYLE['VMGM-hist-quar']['color'], edgecolor=SURFACE,
            linewidth=1)
    ax.set_yscale('log')
    ax.axvline(1.0, color=INK, ls='--', lw=1)
    ax.text(1.03, 0.62, 'bound (Result 4)', transform=ax.get_xaxis_transform(), ha='left', va='center',
            rotation=90, fontsize=7, color=INK)
    ax.text(0.80, 0.97, f'max {hq.max():.2f} over\n{len(hq):,} runs;\ncap only: max {cap_max:.0f}',
            transform=ax.transAxes, ha='right', va='top', fontsize=7, color=INK2)   # left of the bound line
    ax.set_xlim(0, 1.2)
    ax.set_xticks([0, 0.5, 1])
    ax.set_xlabel('Cost added by a liar exam\'s own moves\n(× g$_{max}$, history + quarantine)')
    ax.set_ylabel('Runs (log scale)')
    ax.set_title('(a) Direct damage: proven')
    ax.grid(axis='x', visible=False)

    # (b) total damage: measured
    ax = axs[1]
    ks = sorted(att.k.unique())
    has_soft = (att.protocol == 'VMGM-hist-soft').any()
    for p in ('MGM', 'VMGM-hist-cap', 'VMGM-hist-quar', 'control-quar') + (
            ('VMGM-hist-soft', 'control-soft') if has_soft else ()):
        r = [ci(att[(att.protocol == p) & (att.k == k)].rho) for k in ks]
        line(ax, ks, [m for m, _ in r], [h for _, h in r], p)
    ax.axhline(1, color=MUTED, lw=0.8)
    ax.set_xticks(ks)
    ax.set_xlabel('Dishonest departments k')
    ax.set_ylabel('Final cost / honest MGM (ρ)')
    ax.set_title('(b) Total damage: measured')

    # (c) termination
    ax = axs[2]
    for p in ('MGM', 'RP-MGM', 'VMGM-hist-cap', 'VMGM-hist-quar') + (('VMGM-hist-soft',) if has_soft else ()):
        f = [att[(att.protocol == p) & (att.k == k)].finished.mean() * 100 for k in ks]
        st = STYLE[p]
        ax.plot(ks, f, color=st['color'], marker=st['marker'], ls=st['ls'], label=st['label'],
                markeredgecolor=SURFACE, markeredgewidth=0.8)
    ax.set_ylim(0, 105)
    ax.set_xticks(ks)
    ax.set_xlabel('Dishonest departments k')
    ax.set_ylabel('Runs that finished (%)')
    ax.set_title('(c) Termination')

    handles, labels = {}, {}
    for a in axs[1:]:
        for h, l in zip(*a.get_legend_handles_labels()):
            handles[l] = h
    order = [STYLE[p]['label'] for p in ('VMGM-hist-quar', 'VMGM-hist-cap', 'control-quar', 'MGM', 'RP-MGM')
             + (('VMGM-hist-soft', 'control-soft') if has_soft else ())]
    fig.legend([handles[l] for l in order], order, loc='upper center', ncol=3, bbox_to_anchor=(0.5, -0.12))
    save(fig, d, 'fig1_guarantees')


# ------------------------------------------------------------------ figure 2: cost of quarantine
def fig_quarantine(d, e2):
    """Who pays for quarantine. (The per-attack rho at k = 3 is in Table tab_e2_k3, so it is not repeated here.)"""
    fig, ax = plt.subplots(figsize=(FULL_W * 0.48, 1.95))
    att = e2[e2.k > 0]
    ks = sorted(att.k.unique())
    for p in ('VMGM-hist-quar', 'control-quar'):
        r = [ci(att[(att.protocol == p) & (att.k == k)].honest_loss) for k in ks]
        line(ax, ks, [m for m, _ in r], [h for _, h in r], p)
    ax.axhline(0, color=MUTED, lw=0.8)
    ax.set_xticks(ks)
    ax.set_xlabel('Dishonest departments k')
    ax.set_ylabel('Honest departments\' extra burden')
    ax.set_title('Who pays: honest departments')
    ax.legend(loc='upper left', fontsize=7)
    save(fig, d, 'fig2_quarantine_cost')


# ------------------------------------------------------------------ figure 3: H1
def fig_h1(d, e1):
    fig, ax = plt.subplots(figsize=(FULL_W * 0.48, 1.95))
    attacks = ['block', 'churn', 'sabotage', 'hijack', 'maxbound']
    prots = ['MGM', 'RP-MGM', 'DSA', 'VMGM-hist-quar']
    off = dict(zip(prots, (-0.27, -0.09, 0.09, 0.27)))
    for p in prots:
        r = [ci(e1[(e1.protocol == p) & (e1.attack == a)].rho) for a in attacks]
        st = STYLE[p]
        y = np.arange(len(attacks)) + off[p]
        ax.errorbar([m for m, _ in r], y, xerr=[h for _, h in r], fmt=st['marker'], color=st['color'],
                    markeredgecolor=SURFACE, markeredgewidth=0.6, capsize=1.5, elinewidth=1, label=st['label'])
    ax.set_yticks(range(len(attacks)))
    ax.set_yticklabels([ATTACK_LABEL[a] for a in attacks])
    ax.invert_yaxis()
    ax.axvline(1, color=MUTED, lw=0.8)
    ax.set_xlabel('Final cost / honest MGM (ρ), k = 1–3 pooled')
    ax.set_title('Final cost by attack (E1)')
    ax.grid(axis='y', visible=False)
    ax.legend(loc='lower right', fontsize=7)
    save(fig, d, 'fig3_h1_algorithms')


# ------------------------------------------------------------------ figure 4: H3
def fig_h3(d, e3):
    s = e3[(e3.attack == 'exag_stretch') & (e3.k == 1)]
    lams = sorted(s.lam.unique())
    fig, axs = plt.subplots(1, len(lams), figsize=(FULL_W, 2.2), sharey=True, gridspec_kw=dict(wspace=0.12))
    for ax, lam in zip(axs, lams):
        g = s[s.lam == lam]
        for col, (sp, gg) in zip(SEQ, g.groupby('spread')):
            kap = sorted(gg.kappa.round(2).unique())
            r = [ci(gg[gg.gmax == gm].liar_profit) for gm in sorted(gg.gmax.unique())]
            xs = [gg[gg.gmax == gm].kappa.mean() for gm in sorted(gg.gmax.unique())]
            ax.errorbar(xs, [m for m, _ in r], yerr=[h for _, h in r], color=col, marker='o', capsize=2,
                        elinewidth=1, markeredgecolor=SURFACE, markeredgewidth=0.8,
                        label=f'{sp:.0%} of the scale')
        ax.axhline(0, color=MUTED, lw=0.8)
        ax.set_xscale('log')
        ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
        ax.set_xticks([0.25, 0.5, 1, 2, 4])
        ax.set_xticklabels(['0.25', '0.5', '1', '2', '4'])
        ax.set_xlabel('κ = g$_{max}$ / back-to-back cost')
        ax.set_title(f'λ = {lam:g}')
    axs[0].set_ylabel('Undetectable liar\'s profit')
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc='upper center', ncol=3, bbox_to_anchor=(0.5, -0.04),
               title='True preferences span', title_fontsize=7.5)
    fig.suptitle('Undetectable exaggeration pays once preferences outweigh student costs', x=0.06, ha='left',
                 y=1.04, fontsize=8.5, fontweight='bold')
    save(fig, d, 'fig4_h3_undetectable')


# ------------------------------------------------------------------ figure 5: H4
def fig_h4(d, e4):
    """Small multiples by N: the liar's degree grows with N, so pooling across N confounds the two."""
    s = e4[e4.k == 1]
    Ns = sorted(s.N.unique())
    attacks = ('block', 'churn')
    fig, axs = plt.subplots(len(attacks), len(Ns), figsize=(FULL_W, 3.9),
                            gridspec_kw=dict(wspace=0.32, hspace=0.6))
    for i, att in enumerate(attacks):
        for j, N in enumerate(Ns):
            ax = axs[i, j]
            g = s[(s.attack == att) & (s.N == N)]
            edges = np.unique(np.quantile(g.liar_deg, np.linspace(0, 1, 6)))
            g = g.assign(bin=pd.cut(g.liar_deg, edges, include_lowest=True))
            for p in ('MGM', 'VMGM-hist-quar'):
                gp = g[g.protocol == p].groupby('bin', observed=True)
                r = [ci(v.extra) for _, v in gp]
                line(ax, gp.liar_deg.median().values, [m for m, _ in r], [h for _, h in r], p)
            rs = stats.spearmanr(g[g.protocol == 'MGM'].liar_deg, g[g.protocol == 'MGM'].extra)[0]
            # blocking: MGM's line rises from the left, so place the label low on the right, above V-MGM
            ax.text(0.97, 0.2 if att == 'block' else 0.32, f'MGM: Spearman {rs:+.2f}', transform=ax.transAxes,
                    ha='right', va='center', fontsize=7, color=INK2)
            ax.axhline(0, color=MUTED, lw=0.8)
            ax.set_title(f'{ATTACK_LABEL[att]}, N = {N}')
            ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
                lambda v, _: f'{v / 1000:g}k' if abs(v) >= 1000 else f'{v:g}'))
            if i == len(attacks) - 1:
                ax.set_xlabel('Liar\'s neighbouring depts.')
            if j == 0:
                ax.set_ylabel('Extra cost over\nhonest MGM')
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, l, loc='upper center', ncol=2, bbox_to_anchor=(0.5, 0.0))
    fig.suptitle('Within each N, blocking damage grows with the liar\'s neighbours under MGM; churn has no consistent trend',
                 x=0.06, ha='left', y=0.99, fontsize=8.5, fontweight='bold')
    save(fig, d, 'fig5_h4_neighbours')


# ------------------------------------------------------------------ tables
def tex_escape(s):
    return str(s).replace('&', r'\&').replace('%', r'\%').replace('_', r'\_')


def write_table(d, name, header, rows, colspec, caption, label, size=r'\footnotesize', colsep=None):
    os.makedirs(os.path.join(d, 'tables'), exist_ok=True)
    # a colspec with an X column becomes a full-width tabularx (needs \usepackage{tabularx} in the paper)
    env, width = ('tabularx', r'{\linewidth}') if 'X' in colspec else ('tabular', '')
    sep = [rf'\setlength{{\tabcolsep}}{{{colsep}}}'] if colsep else []
    lines = [r'\begin{table}[t]', r'\centering', size] + sep + [rf'\caption{{{caption}}}', rf'\label{{{label}}}',
             rf'\begin{{{env}}}{width}{{{colspec}}}', r'\toprule', ' & '.join(header) + r' \\', r'\midrule']
    lines += [' & '.join(r) + r' \\' for r in rows]
    lines += [r'\bottomrule', rf'\end{{{env}}}', r'\end{table}']
    open(os.path.join(d, 'tables', f'{name}.tex'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')


def pct(v):
    """Percent that never rounds up to 100% or down to 0% (0.998 -> '99.8%')."""
    if 0.995 <= v < 1 or 0 < v < 0.005:
        return f'{v:.1%}'
    return f'{v:.0%}'


def tables(d, e1, e2, e3, e4, e5, e6=None):
    allx = [e1, e2, e3, e4, e5] + ([e6] if e6 is not None else [])      # totals over E1-E6
    att = e2[e2.k > 0]
    hq = att[att.protocol == 'VMGM-hist-quar']
    vm = e2[e2.protocol.str.startswith('VMGM')]
    hq_all = pd.concat([e[e.protocol == 'VMGM-hist-quar'] for e in allx])
    det = lambda a: hq[hq.attack == a].det_rate.mean()  # noqa: E731
    rho_k = {k: hq[hq.k == k].rho.mean() for k in sorted(hq.k.unique())}
    oth_fin = att[att.protocol.isin(['VMGM-hist-cap', 'VMGM-move-cap', 'VMGM-move-quar'])].finished.mean()
    cap_dmg = att[att.protocol == 'VMGM-hist-cap'].dmg_exam_max.max()
    cap_dmg_e5 = e5[e5.protocol == 'VMGM-hist-cap'].dmg_exam_max.max()
    oth_fin_e5 = e5[e5.protocol.isin(['VMGM-hist-cap', 'VMGM-move-cap'])].finished.mean()
    n_checked = sum(int(e.protocol.str.startswith('VMGM').sum()) for e in allx)
    # Result 6 slack: runs that ended above the start, and how much of the allowed 2*gmax*|E_L| they used
    liar_runs = pd.concat([e[(e.protocol == 'VMGM-hist-quar') & (e.k > 0)].assign(
        gm=e['gmax'] if 'gmax' in e else 50) for e in allx])
    allowed = 2 * liar_runs.gm * 4 * liar_runs.k
    above = int((liar_runs.F > liar_runs.F0).sum())
    used = ((liar_runs.F - liar_runs.F0) / allowed).max()

    rows = [
        ['Honest posts never flagged', 'any check', 'Proven (R1, R2)', f'{int(vm.false_flags.sum())} false flags'],
        ['Contradictory histories flagged', 'history check', 'Proven (R2)',
         f'blockers {pct(det("block"))}, churners {pct(det("churn"))} flagged, $k\\le 6$'],
        ['Consistent lies undetectable', 'any public check', 'Proven (R3)',
         f'consistent liars: {pct(max(det("exag_consistent"), det("sabotage_consistent")))} flagged'],
        ['Direct student cost $< g_{max}$ per exam', 'history + quarantine', 'Proven (R4)',
         f'max {hq_all.dmg_exam_max.max():.2f}$\\,g_{{max}}$ (all {len(hq_all):,} runs, E1--E6)'],
        ['', 'history + cap only', 'Not guaranteed',
         f'max {cap_dmg:.0f}$\\,g_{{max}}$ ({cap_dmg_e5:.0f} in E5, 1000 rounds)'],
        ['Run finishes', 'history + quarantine', 'Proven (R5, new)',
         f'{pct(hq_all.finished.mean())} of all {len(hq_all):,} runs, E1--E6'],
        ['', 'cap only / one-post', 'Not guaranteed', f'{pct(oth_fin)} finished (E5: {pct(oth_fin_e5)})'],
        ['$F_{final}\\le F_{start}+2g_{max}|E_L|$', 'history + quarantine', 'Proven (R6, new)',
         f'held in all {len(liar_runs):,} runs with liars, E1--E6; above start in {above}, by '
         f'$\\le${100 * used:.1f}% of the bound'],
        ['Total cost vs honest MGM ($\\rho$)', 'any', 'Measured only (R7)',
         ', '.join(f'{v:.2f}' for v in rho_k.values()) + f' for $k={",".join(map(str, rho_k))}$'],
    ]
    write_table(d, 'tab_guarantees', ['Property', 'Applies to', 'Status', 'Evidence (E2 unless stated)'],
                [[tex_escape(c) if '$' not in c else c.replace('%', r'\%') for c in r] for r in rows],
                r'>{\raggedright\arraybackslash}p{3.5cm}>{\raggedright\arraybackslash}p{2.6cm}'
                r'>{\raggedright\arraybackslash}p{2.3cm}>{\raggedright\arraybackslash}X',
                f'What is proven and what is only measured. All {n_checked:,} V-MGM runs were checked automatically '
                f'against R1, R2 and R4--R6 wherever they apply, with no violation.', 'tab:guarantees')

    # main E2 table at k = 3
    k3 = e2[e2.k == 3]
    attacks = ['block', 'churn', 'mixed', 'delayed', 'sabotage', 'hijack', 'exag_naive', 'maxbound',
               'sabotage_consistent', 'exag_consistent']
    prots = ['MGM', 'RP-MGM', 'VMGM-hist-cap', 'VMGM-hist-quar', 'control-quar']
    heads = ['Attack', 'MGM', 'RP-MGM', 'Hist.+cap', 'Hist.+quar.', 'Quar. only']
    if (k3.protocol == 'VMGM-hist-soft').any():
        prots += ['VMGM-hist-soft', 'control-soft']
        heads += ['Hist.+soft', 'Soft only']
    rows = []
    for a in attacks:
        r = [tex_escape(ATTACK_LABEL[a])]
        for p in prots:
            g = k3[(k3.protocol == p) & (k3.attack == a)]
            m = f'{g.rho.mean():.2f}'
            r.append(m + (r'$^\dagger$' if g.finished.mean() < 0.95 else ''))
        r.append(pct(k3[(k3.protocol == "VMGM-hist-quar") & (k3.attack == a)].det_rate.mean()).replace('%', r'\%'))
        rows.append(r)
    write_table(d, 'tab_e2_k3', heads + ['Flagged'],
                rows, 'l' + 'r' * (len(heads)),
                r'Mean $\rho$ with $k=3$ dishonest departments (E2; 400 runs per cell). $\dagger$: fewer than 95\% '
                r"finished. ``Only'': nobody lies, the liars' departments quarantined from their flag rounds (control). "
                r'Flagged: liars caught by history + quarantine (mixed: the third liar is a consistent saboteur).',
                'tab:e2', colsep='4pt')


def main(d, out=None):
    e1, e2, e3, e4, e5 = (pd.read_csv(os.path.join(d, f'E{i}.csv')) for i in range(1, 6))
    e6 = pd.read_csv(os.path.join(d, 'E6.csv')) if os.path.exists(os.path.join(d, 'E6.csv')) else None
    d = out or d
    fig_guarantees(d, e2)
    fig_quarantine(d, e2)
    fig_h1(d, e1)
    fig_h3(d, e3)
    fig_h4(d, e4)
    tables(d, e1, e2, e3, e4, e5, e6)
    print('figures ->', os.path.join(d, 'figures'), ' tables ->', os.path.join(d, 'tables'))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'vmgm_results/full',
         sys.argv[2] if len(sys.argv) > 2 else None)
