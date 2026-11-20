# Numbers used in the paper
Source: `vmgm_results/full`

## Run counts (Experimental setup, Table 2 caption, Table 3)

- **setup** | E1 rows: 9,600
- **setup** | E2 rows: 161,600
- **setup** | E3 rows: 36,000
- **setup** | E4 rows: 7,200
- **setup** | E5 rows: 1,200
- **setup** | total rows: 215,600
- **Table 2** | V-MGM runs checked automatically: 139,920
- **Table 2** | history + quarantine runs (all experiments): 58,440
- **setup** | instances per family (E1-E3): 50
- **setup** | instances per family (E5): 10
- **setup** | instances per (N, p) (E4): 50

## Detection and false flags (abstract, Results RQ2, Table 4 H2a)

- **RQ2** | block: share of liars flagged by k: k=1: 100.0%, k=2: 100.0%, k=3: 100.0%, k=6: 100.0%
- **RQ2** | churn: share of liars flagged by k: k=1: 100.0%, k=2: 100.0%, k=3: 99.9%, k=6: 99.8%
- **RQ2** | delayed: share of liars flagged by k: k=1: 80.5%, k=2: 81.0%, k=3: 81.0%, k=6: 86.5%
- **RQ2** | mixed: share of liars flagged by k: k=1: 100.0%, k=2: 100.0%, k=3: 66.7%, k=6: 66.6%
- **RQ2** | sabotage: share of liars flagged by k: k=1: 78.5%, k=2: 74.5%, k=3: 75.1%, k=6: 74.9%
- **RQ2** | maxbound: share of liars flagged by k: k=1: 33.0%, k=2: 32.9%, k=3: 31.8%, k=6: 31.1%
- **RQ2** | churn runs with an unflagged churner: 5 of 1,600 (those runs ended after 11-32 rounds)
- **RQ2** | delayed (all k): runs with an unflagged delayed liar that ended before round 20: 284 of 284
- **abstract** | churn, E1: share of churners flagged by k (E1 and E2 together give the abstract range): k=1: 99.5%, k=2: 99.8%, k=3: 99.8%
- **RQ2** | false flags in all V-MGM runs of E2: 0

## Termination (abstract, RQ2, Table 4 H2b, E5)

- **RQ2** | MGM: attacked runs finished: 55%
- **RQ2** | RP-MGM: attacked runs finished: 77%
- **RQ2** | VMGM-hist-quar: attacked runs finished: 100%
- **RQ2** | cap-only and one-post: attacked runs finished: 75% (by k: 85%, 73%, 72%, 72%)
- **Table 4 H2b** | range of the pooled finish rate over MGM, RP-MGM, cap-only, one-post: 55%-77%
- **RQ2** | history + quarantine finished (all experiments): 100.0%
- **RQ2/E5** | runs whose finished status changes from 300 to 1000 rounds: 0
- **RQ1** | RP-MGM under churn, attacked runs finished (E2): 0%
- **RQ1** | RP-MGM under churn, runs finished (E1): 4 of 600
- **Table 4 H2b** | MGM: runs finished (E5, both round limits): 12%
- **Table 4 H2b** | RP-MGM: runs finished (E5, both round limits): 48%
- **Table 2** | cap-only and one-post: runs finished (E5, both round limits): 46%
- **RQ4** | N=48, k=12, history + quarantine finished: 100% of 600 runs

## Direct damage (Result 4, Table 4 H2c, Figure 1a)

- **RQ2** | largest per-exam direct damage, E2 history + quarantine: 0.96 g_max over 16,000 runs
- **RQ2** | largest per-exam direct damage, all history + quarantine: 0.99 g_max over 58,440 runs
- **Figure 1a** | largest per-exam direct damage, cap only (E2): 144 g_max
- **Table 2** | largest per-exam direct damage, cap only (E5, by round limit): 300 rounds: 132 g_max, 1000 rounds: 458 g_max

## Total damage (abstract, RQ2, Table 4 H2d, Figure 1b)

- **RQ2** | k=1: rho MGM / hist+quar / control / share of hist+quar excess also in control: 1.91 / 1.10 / 1.06 / 61%
- **RQ2** | k=2: rho MGM / hist+quar / control / share of hist+quar excess also in control: 1.94 / 1.21 / 1.12 / 57%
- **RQ2** | k=3: rho MGM / hist+quar / control / share of hist+quar excess also in control: 2.00 / 1.33 / 1.17 / 51%
- **RQ2** | k=6: rho MGM / hist+quar / control / share of hist+quar excess also in control: 2.28 / 1.71 / 1.33 / 46%
- **RQ2** | k=1: honest loss, hist+quar minus control: -0.2 +/- 1.8
- **RQ2** | k=2: honest loss, hist+quar minus control: 3.5 +/- 2.0
- **RQ2** | k=3: honest loss, hist+quar minus control: 8.4 +/- 2.3
- **RQ2** | k=6: honest loss, hist+quar minus control: 13.6 +/- 2.2
- **Figure 2** | k=1: control, honest departments' share of the extra cost: 6%
- **Figure 2** | k=2: control, honest departments' share of the extra cost: 5%
- **Figure 2** | k=3: control, honest departments' share of the extra cost: 5%
- **Figure 2** | k=6: control, honest departments' share of the extra cost: 4%

## Quarantine vs cap only (Results)

- **Results** | k=1: selfish attacks (T1a, T2a) rho cap-only / quarantine / cost of quarantine: 1.00 / 1.11 / 0.11
- **Results** | k=2: selfish attacks (T1a, T2a) rho cap-only / quarantine / cost of quarantine: 1.00 / 1.23 / 0.23
- **Results** | k=3: selfish attacks (T1a, T2a) rho cap-only / quarantine / cost of quarantine: 1.00 / 1.34 / 0.34
- **Results** | k=6: selfish attacks (T1a, T2a) rho cap-only / quarantine / cost of quarantine: 1.00 / 1.66 / 0.66
- **Results** | k=3, churn: cap-only rho / finished: 2.31 / 0.00%
- **Results** | k=3, mixed: cap-only rho / finished: 2.20 / 0.25%
- **Results** | k=3, sabotage: cap-only rho / finished: 1.68 / 24.25%

## Soft quarantine (Result 8, issue #14)

- **Results** | k=1: rho hard / soft quarantine; control hard / control soft: 1.10 / 1.11; 1.06 / 1.04
- **Results** | k=2: rho hard / soft quarantine; control hard / control soft: 1.21 / 1.22; 1.12 / 1.09
- **Results** | k=3: rho hard / soft quarantine; control hard / control soft: 1.33 / 1.35; 1.17 / 1.12
- **Results** | k=6: rho hard / soft quarantine; control hard / control soft: 1.71 / 1.75; 1.33 / 1.24
- **Results** | k=1: soft minus hard quarantine, paired rho difference: +0.003 +/- 0.001 (Holm p 3.0e-09)
- **Results** | k=2: soft minus hard quarantine, paired rho difference: +0.011 +/- 0.002 (Holm p 2.7e-49)
- **Results** | k=3: soft minus hard quarantine, paired rho difference: +0.018 +/- 0.002 (Holm p 4.4e-82)
- **Results** | k=6: soft minus hard quarantine, paired rho difference: +0.044 +/- 0.003 (Holm p 2.9e-162)
- **Result 8** | soft quarantine: largest per-exam direct damage over the whole run, share finished, false flags: 0.96 g_max, 100.0%, 0
- **Result 8** | soft quarantine: share of liars flagged (same detection as hard quarantine?): soft 65.8% vs hard 65.8%
- **Results** | k=1: selfish attacks (T1a, T2a) rho cap-only / hard / soft quarantine: 1.00 / 1.11 / 1.12
- **Results** | k=2: selfish attacks (T1a, T2a) rho cap-only / hard / soft quarantine: 1.00 / 1.23 / 1.25
- **Results** | k=3: selfish attacks (T1a, T2a) rho cap-only / hard / soft quarantine: 1.00 / 1.34 / 1.37
- **Results** | k=6: selfish attacks (T1a, T2a) rho cap-only / hard / soft quarantine: 1.00 / 1.66 / 1.73
- **Results** | k=1: honest loss, soft quarantine minus its control: -1.8 +/- 2.0
- **Results** | k=2: honest loss, soft quarantine minus its control: 4.5 +/- 2.1
- **Results** | k=3: honest loss, soft quarantine minus its control: 10.5 +/- 2.3
- **Results** | k=6: honest loss, soft quarantine minus its control: 15.7 +/- 2.2

## Placement and record mode (RQ2, Result 2 footnote)

- **RQ2** | adjacent minus spread rho, smallest Holm p: 1.00
- **Result 2** | attacked runs where recording executed instead of posted claims changes F: 3 of 16,000

## Result 6 slack (Result 6, Table 2)

- **Result 6** | runs with liars ending above the starting cost: 124 of 58,240; at most 20.5% of the bound

## Round bound (Result 5 with integer claims)

- **Result 5** | history + quarantine: largest number of rounds, and largest rounds / (F_start + |E_L| g_max + 1): 210 rounds; 33.0% of the bound

## H1 (RQ1, Table 4, Figure 3)

- **RQ1** | MGM minus RP-MGM, block, k=1..3: +3.53 to +3.58 (largest Holm p 1.7e-33)
- **RQ1** | MGM minus RP-MGM, churn, k=1..3: +0.93 to +1.10 (largest Holm p 3.8e-33)
- **RQ1** | MGM minus RP-MGM, hijack, k=1..3: -0.02 to -0.01 (largest Holm p 6.2e-01)
- **RQ1** | MGM minus RP-MGM, maxbound, k=1..3: -0.02 to -0.01 (largest Holm p 6.2e-01)
- **RQ1** | MGM minus DSA, block, k=1..3: +3.52 to +3.58 (largest Holm p 1.7e-33)
- **RQ1** | MGM minus DSA, churn, k=1..3: +1.23 to +1.30 (largest Holm p 3.6e-33)
- **RQ1** | MGM minus DSA, hijack, k=1..3: -0.03 to -0.02 (largest Holm p 2.6e-01)
- **RQ1** | MGM minus DSA, maxbound, k=1..3: -0.02 to -0.01 (largest Holm p 5.3e-01)
- **RQ1** | RP-MGM mean rho by attack (E1): block: 1.01, churn: 1.26, hijack: 1.01, maxbound: 1.01
- **RQ1** | block: mean rho MGM / history + quarantine: 4.57 / 1.23
- **RQ1** | churn: mean rho MGM / history + quarantine: 2.28 / 1.24

## H3 (RQ3, Table 4, Figure 4)

- **RQ3** | E3 liars flagged: 0
- **RQ3** | k=1, exag_stretch: settings where profit rises with kappa (Holm p<0.05): 9 of 9 (Spearman +0.09 to +0.36)
- **RQ3** | k=1, exag_consistent: settings where profit rises with kappa (Holm p<0.05): 7 of 9 (Spearman -0.22 to +0.33)
- **RQ3** | k=3, exag_stretch: settings where profit rises with kappa (Holm p<0.05): 9 of 9 (Spearman +0.13 to +0.57)
- **RQ3** | k=3, exag_consistent: settings where profit rises with kappa (Holm p<0.05): 7 of 9 (Spearman -0.61 to +0.50)
- **RQ3** | stretched liar, k=1, mean profit for g_max <= 25 (kappa <= 0.56): -10.4 to +2.2
- **RQ3** | stretched liar, k=1, mean profit at g_max=200 (kappa 4.5): +2.6 to +114.1
- **RQ3** | stretched liar, k=3, mean profit for g_max <= 25 (kappa <= 0.56): -15.3 to +2.5
- **RQ3** | stretched liar, k=3, mean profit at g_max=200 (kappa 4.5): +2.8 to +121.7
- **Figure 4** | stretched liar, k=1, g_max=200: mean profit by (lambda, preference spread): lam=1.5, spread=0.25: +3, lam=1.5, spread=0.5: +10, lam=1.5, spread=1.0: +16, lam=3.0, spread=0.25: +16, lam=3.0, spread=0.5: +50, lam=3.0, spread=1.0: +63, lam=6.0, spread=0.25: +66, lam=6.0, spread=0.5: +114, lam=6.0, spread=1.0: +83
- **RQ3** | clipped liar (T1b), preferences fill the scale: mean profit by (k, lambda): k=1, lam=1.5: +2.6, k=1, lam=3.0: -11.3, k=1, lam=6.0: -120.8, k=3, lam=1.5: +2.4, k=3, lam=3.0: -17.0, k=3, lam=6.0: -139.4
- **RQ3** | kappa for g_max = 10, 25, 50, 100, 200: 0.22, 0.56, 1.12, 2.23, 4.46

## H4 (RQ4, Table 4, Figure 5)

- **RQ4** | block, MGM: Spearman(liar degree, extra cost) within N: N=12: +0.73, N=24: +0.86, N=48: +0.88
- **RQ4** | block: reduction by history + quarantine, k=1 and N/4 pooled: 98%
- **RQ4** | block, k=1: mean extra cost MGM / history + quarantine / reduction: 10104 / 65 / 99%
- **RQ4** | churn, MGM: Spearman(liar degree, extra cost) within N: N=12: +0.29, N=24: -0.43, N=48: -0.51
- **RQ4** | churn: reduction by history + quarantine, k=1 and N/4 pooled: 82%
- **RQ4** | churn, k=1: mean extra cost MGM / history + quarantine / reduction: 1309 / 74 / 94%
- **RQ4** | sabotage, MGM: Spearman(liar degree, extra cost) within N: N=12: +0.10, N=24: +0.16, N=48: -0.07
- **RQ4** | sabotage: reduction by history + quarantine, k=1 and N/4 pooled: 14%
- **RQ4** | sabotage, k=1: mean extra cost MGM / history + quarantine / reduction: 175 / 97 / 44%
- **RQ4** | sabotage_consistent, MGM: Spearman(liar degree, extra cost) within N: N=12: -0.12, N=24: +0.07, N=48: -0.07
- **RQ4** | sabotage_consistent: reduction by history + quarantine, k=1 and N/4 pooled: 0%
- **RQ4** | sabotage_consistent, k=1: mean extra cost MGM / history + quarantine / reduction: 94 / 94 / 0%

## CP-SAT reference: distance from the best timetable (Setup, Results RQ2, Limitations)

- **Setup** | loose: instances solved to proven optimality: 50 of 50 (limit 60 s)
- **Setup** | tight: instances solved to proven optimality: 4 of 50 (limit 300 s); gap of the others median 25.1%, largest 37.8%
- **RQ2** | honest MGM above the best timetable, loose, greedy start: 33%
- **RQ2** | honest MGM above the best timetable, loose, random start: 36%
- **RQ2** | honest MGM above the best timetable, tight, greedy start: 48% to 92%
- **RQ2** | honest MGM above the best timetable, tight, random start: 58% to 106%
- **RQ2** | honest MGM above the best timetable, loose, both starts: 34%
- **RQ2** | MGM under attack above the best timetable, loose, by k: k=1: 214%, k=2: 222%, k=3: 234%, k=6: 292%
- **RQ2** | MGM under attack above the best timetable, both families, by k (range): k=1: 170%-204%, k=2: 174%-208%, k=3: 183%-217%, k=6: 221%-258%
- **RQ2** | VMGM-hist-quar under attack above the best timetable, loose, by k: k=1: 59%, k=2: 84%, k=3: 112%, k=6: 196%
- **RQ2** | VMGM-hist-quar under attack above the best timetable, both families, by k (range): k=1: 57%-80%, k=2: 72%-95%, k=3: 88%-112%, k=6: 139%-166%
