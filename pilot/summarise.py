import json, sys, numpy as np, pandas as pd
from scipy import stats

def ci(x):
    x = np.asarray(x, float); n = len(x)
    if n < 2: return np.nan
    return stats.t.ppf(0.975, n - 1) * x.std(ddof=1) / np.sqrt(n)

frames = [pd.DataFrame(json.load(open(f'prelim_{f}.json'))) for f in sys.argv[1:]]
r = pd.concat(frames)
r['rho_hon'] = r.F / r.F_mgm
r['rho_lb'] = r.F / r.bound
r['delta'] = (r.F - r.F_mgm) / (r.F0 - r.F_mgm)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)

print('=== instance statistics')
h = r[(r.protocol == 'MGM') & (r.attack == 'none')]
for (fam, st), d in h.groupby(['family', 'start']):
    print(fam, st, 'n=%d' % len(d), 'opt-proven %d' % (d.status == 'OPTIMAL').sum(),
          'MGM/LB %.3f±%.3f' % ((d.F / d.bound).mean(), ci(d.F / d.bound)),
          'F0/LB %.2f' % (d.F0 / d.bound).mean(), 'K0 %.1f' % d.K0.mean(), 'K_mgm %.1f' % d.K.mean(),
          'coupling share %.2f' % (d.H / d.F).mean(), 'dens %.2f' % d.dens.mean(),
          'gap(opt-bound)/bound %.3f' % ((d.opt - d.bound) / d.bound).mean())

print('\n=== honest protocols (rho_hon = F / F_MGM)')
hh = r[r.attack == 'none']
print(hh.groupby(['family', 'start', 'protocol']).agg(rho=('rho_hon', 'mean'), ci=('rho_hon', ci), rounds=('rounds', 'mean'),
                                                     capped=('capped', 'mean'), fp=('fp', 'sum')).round(3))

print('\n=== attacks')
a = r[r.attack != 'none']
g = a.groupby(['family', 'start', 'k', 'attack', 'protocol']).agg(
    rho=('rho_hon', 'mean'), ci=('rho_hon', ci), K=('K', 'mean'), delta=('delta', 'mean'),
    det=('det', 'mean'), fp=('fp', 'sum'), rounds=('rounds', 'mean'), capped=('capped', 'mean'),
    profit=('profit', 'mean'), pci=('profit', ci), hloss=('hloss', 'mean'), hci=('hloss', ci), n=('seed', 'count'))
print(g.round(3).to_string())
g.round(4).to_csv('summary_attacks.csv')
print('\nTOTAL false positives over all runs:', int(r.fp.sum()), 'runs:', len(r))
