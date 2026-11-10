# V-MGM experiments: summary
Source: `vmgm_results/full`

## H1 (E1): lying about gains hurts MGM more than RP-MGM and DSA
Paired difference in rho. H1 is proven wrong for an attack if the MGM − RP-MGM interval includes 0.

### MGM vs RP-MGM
| attack | k | MGM − RP-MGM | includes 0 | p (Holm) | n |
|---|---|---|---|---|---|
| block | 1 | 3.58 ± 0.43 | False | 1.7e-33 | 200 |
| block | 2 | 3.58 ± 0.42 | False | 1.7e-33 | 200 |
| block | 3 | 3.53 ± 0.41 | False | 1.7e-33 | 200 |
| churn | 1 | 1.10 ± 0.14 | False | 1.9e-33 | 200 |
| churn | 2 | 1.03 ± 0.13 | False | 1.7e-33 | 200 |
| churn | 3 | 0.93 ± 0.11 | False | 3.8e-33 | 200 |
| hijack | 1 | -0.02 ± 0.01 | False | 1.1e-01 | 200 |
| hijack | 2 | -0.02 ± 0.02 | False | 1.7e-01 | 200 |
| hijack | 3 | -0.01 ± 0.02 | True | 6.2e-01 | 200 |
| maxbound | 1 | -0.02 ± 0.01 | False | 1.6e-01 | 200 |
| maxbound | 2 | -0.01 ± 0.01 | True | 3.6e-01 | 200 |
| maxbound | 3 | -0.01 ± 0.01 | True | 6.2e-01 | 200 |

### MGM vs DSA
| attack | k | MGM − DSA | includes 0 | p (Holm) | n |
|---|---|---|---|---|---|
| block | 1 | 3.58 ± 0.43 | False | 1.7e-33 | 200 |
| block | 2 | 3.57 ± 0.42 | False | 1.7e-33 | 200 |
| block | 3 | 3.52 ± 0.41 | False | 1.7e-33 | 200 |
| churn | 1 | 1.23 ± 0.15 | False | 3.6e-33 | 200 |
| churn | 2 | 1.27 ± 0.16 | False | 1.7e-33 | 200 |
| churn | 3 | 1.30 ± 0.16 | False | 1.7e-33 | 200 |
| hijack | 1 | -0.02 ± 0.01 | False | 2.6e-01 | 200 |
| hijack | 2 | -0.03 ± 0.01 | False | 2.3e-02 | 200 |
| hijack | 3 | -0.02 ± 0.02 | False | 2.6e-01 | 200 |
| maxbound | 1 | -0.02 ± 0.01 | False | 2.6e-01 | 200 |
| maxbound | 2 | -0.02 ± 0.02 | False | 2.6e-01 | 200 |
| maxbound | 3 | -0.01 ± 0.02 | True | 5.3e-01 | 200 |

### Mean rho by attack (all k)
| attack | DSA | MGM | RP-MGM | VMGM-hist-quar |
|---|---|---|---|---|
| block | 1.02 | 4.57 | 1.01 | 1.23 |
| churn | 1.02 | 2.28 | 1.26 | 1.24 |
| hijack | 1.02 | 0.99 | 1.01 | 1.23 |
| maxbound | 1.02 | 1.0 | 1.01 | 1.02 |

## H2 (E2): k dishonest departments, history check + quarantine

### H2a: fraction of liars flagged (H2a proven wrong if < 0.95 for block or churn)
| attack | 1 | 2 | 3 | 6 |
|---|---|---|---|---|
| block | 1.0 | 1.0 | 1.0 | 1.0 |
| churn | 1.0 | 1.0 | 1.0 | 1.0 |
| delayed | 0.8 | 0.81 | 0.81 | 0.86 |
| exag_consistent | 0.0 | 0.0 | 0.0 | 0.0 |
| exag_naive | 0.88 | 0.88 | 0.87 | 0.87 |
| hijack | 0.98 | 0.98 | 0.97 | 0.97 |
| maxbound | 0.33 | 0.33 | 0.32 | 0.31 |
| mixed | 1.0 | 1.0 | 0.67 | 0.67 |
| sabotage | 0.78 | 0.74 | 0.75 | 0.75 |
| sabotage_consistent | 0.0 | 0.0 | 0.0 | 0.0 |

### H2b: fraction of runs that finished within 300 rounds
| protocol | 1 | 2 | 3 | 6 |
|---|---|---|---|---|
| MGM | 0.565 | 0.548 | 0.543 | 0.528 |
| RP-MGM | 0.86 | 0.743 | 0.74 | 0.734 |
| VMGM-hist-cap | 0.846 | 0.729 | 0.724 | 0.715 |
| VMGM-hist-quar | 1.0 | 1.0 | 1.0 | 1.0 |
| VMGM-hist-quar-exec | 1.0 | 1.0 | 1.0 | 1.0 |
| VMGM-move-cap | 0.846 | 0.729 | 0.724 | 0.715 |
| VMGM-move-quar | 0.846 | 0.729 | 0.724 | 0.715 |
| control-quar | 1.0 | 1.0 | 1.0 | 1.0 |

### H2c: direct damage (Result 4)
Largest student cost added by one liar exam's own moves: **0.960 · g_max** over 16000 runs (bound: < 1). False flags in all V-MGM runs: **0**.
Over all 58,440 history + quarantine runs in E1-E5: **0.990 · g_max** (worst run in E3). This is the number in the paper's Table 2.

### H2d: total damage, rho (all attacks pooled) and the quarantine control
`control-quar`: everyone honest, the flagged liars' departments quarantined at the same rounds. It measures what quarantine itself costs.
| k | MGM | VMGM-hist-cap | VMGM-hist-quar | control-quar | RP-MGM |
|---|---|---|---|---|---|
| 1 | 1.91 ± 0.06 | 1.17 ± 0.02 | 1.10 ± 0.00 | 1.06 ± 0.00 | 1.07 ± 0.01 |
| 2 | 1.94 ± 0.06 | 1.32 ± 0.02 | 1.21 ± 0.01 | 1.12 ± 0.01 | 1.13 ± 0.01 |
| 3 | 2.00 ± 0.06 | 1.38 ± 0.02 | 1.33 ± 0.01 | 1.17 ± 0.01 | 1.21 ± 0.01 |
| 6 | 2.28 ± 0.06 | 1.57 ± 0.03 | 1.71 ± 0.03 | 1.33 ± 0.01 | 1.49 ± 0.03 |

Honest departments' loss: lying + quarantine vs quarantine alone (positive = lying hurts honest departments beyond what quarantine costs):
| k | hist-quar − control (honest loss) | p (Holm) | n |
|---|---|---|---|
| 1 | -0.2 ± 1.8 | 4.7e-06 | 4000 |
| 2 | 3.5 ± 2.0 | 8.1e-15 | 4000 |
| 3 | 8.4 ± 2.3 | 4.9e-31 | 4000 |
| 6 | 13.6 ± 2.2 | 1.4e-55 | 4000 |

### rho by attack and protocol, k = 3
| attack | MGM | RP-MGM | VMGM-hist-cap | VMGM-hist-quar | VMGM-hist-quar-exec | VMGM-move-cap | VMGM-move-quar | control-quar |
|---|---|---|---|---|---|---|---|---|
| block | 4.43 | 1.01 | 1.0 | 1.34 | 1.34 | 1.0 | 1.34 | 1.33 |
| churn | 2.31 | 1.36 | 2.31 | 1.36 | 1.36 | 2.31 | 2.31 | 1.29 |
| delayed | 1.49 | 1.02 | 1.01 | 1.35 | 1.35 | 1.01 | 1.35 | 1.1 |
| exag_consistent | 1.03 | 1.05 | 1.03 | 1.03 | 1.03 | 1.03 | 1.03 | 1.0 |
| exag_naive | 0.98 | 1.01 | 1.0 | 1.33 | 1.33 | 1.0 | 1.33 | 1.33 |
| hijack | 0.99 | 1.01 | 1.0 | 1.34 | 1.34 | 1.0 | 1.34 | 1.33 |
| maxbound | 1.0 | 1.01 | 1.0 | 1.03 | 1.03 | 1.0 | 1.0 | 1.05 |
| mixed | 4.55 | 1.3 | 2.2 | 1.39 | 1.39 | 2.2 | 2.29 | 1.21 |
| sabotage | 1.68 | 1.74 | 1.68 | 1.57 | 1.57 | 1.68 | 1.68 | 1.06 |
| sabotage_consistent | 1.55 | 1.58 | 1.55 | 1.55 | 1.55 | 1.55 | 1.55 | 1.0 |

### Placement (hist-quar): rho, liars adjacent − spread
| k | adjacent − spread | p (Holm) | n |
|---|---|---|---|
| 2 | 0.004 ± 0.006 | 1.0e+00 | 2000 |
| 3 | 0.011 ± 0.009 | 1.0e+00 | 2000 |
| 6 | 0.020 ± 0.015 | 1.0e+00 | 2000 |

### Record mode: posted vs executed claims give the same final cost in **100.0%** of runs.

## H3 (E3): undetectable lying still pays, more as kappa grows
Liar profit = drop in the liar's own objective J vs honest play (positive = lying pays). No liar was flagged in any E3 run. H3 is proven wrong if the profit interval includes 0 at every kappa, or profit does not rise with kappa.

### k = 1
| attack | spread | lam | g_max=10 (kappa 0.22) | g_max=25 (kappa 0.56) | g_max=50 (kappa 1.12) | g_max=100 (kappa 2.23) | g_max=200 (kappa 4.46) | Spearman(kappa, profit) | p (Holm) |
|---|---|---|---|---|---|---|---|---|---|
| exag_consistent | 0.25 | 1.5 | 0.1 ± 0.0 | 0.1 ± 0.8 | -0.2 ± 0.7 | 0.9 ± 0.7 | 2.6 ± 2.7 | 0.09 | 9.5e-03 |
| exag_consistent | 0.25 | 3.0 | -0.2 ± 0.8 | 0.2 ± 1.2 | 2.2 ± 1.5 | 6.3 ± 3.2 | 15.8 ± 6.2 | 0.21 | 4.5e-10 |
| exag_consistent | 0.25 | 6.0 | -0.2 ± 1.1 | 1.2 ± 1.7 | 4.9 ± 2.9 | 20.7 ± 6.7 | 56.3 ± 12.5 | 0.33 | 3.7e-26 |
| exag_consistent | 0.5 | 1.5 | -0.2 ± 0.5 | -0.2 ± 0.7 | 0.9 ± 0.7 | 2.6 ± 2.7 | 9.2 ± 4.5 | 0.14 | 2.1e-05 |
| exag_consistent | 0.5 | 3.0 | 0.0 ± 0.8 | 1.9 ± 1.4 | 4.2 ± 2.8 | 11.2 ± 5.7 | 44.2 ± 10.6 | 0.27 | 8.3e-17 |
| exag_consistent | 0.5 | 6.0 | -3.9 ± 1.8 | -3.0 ± 2.6 | -2.0 ± 5.6 | 7.4 ± 11.5 | 52.6 ± 24.3 | 0.20 | 9.9e-10 |
| exag_consistent | 1.0 | 1.5 | -0.1 ± 0.2 | -0.1 ± 0.8 | 0.3 ± 1.7 | 4.2 ± 4.4 | 8.6 ± 7.5 | 0.15 | 1.6e-05 |
| exag_consistent | 1.0 | 3.0 | -0.8 ± 2.1 | -6.0 ± 2.5 | -13.5 ± 5.1 | -10.6 ± 11.9 | -25.3 ± 22.5 | 0.06 | 5.2e-02 |
| exag_consistent | 1.0 | 6.0 | -14.4 ± 4.1 | -34.0 ± 7.3 | -94.4 ± 16.6 | -144.9 ± 33.8 | -316.2 ± 68.6 | -0.22 | 3.6e-11 |
| exag_stretch | 0.25 | 1.5 | 0.1 ± 0.0 | 0.1 ± 0.8 | -0.2 ± 0.7 | 0.6 ± 0.9 | 2.6 ± 2.7 | 0.09 | 1.2e-02 |
| exag_stretch | 0.25 | 3.0 | -0.2 ± 0.8 | 0.2 ± 1.2 | 2.2 ± 1.5 | 6.3 ± 3.2 | 15.8 ± 6.2 | 0.21 | 4.5e-10 |
| exag_stretch | 0.25 | 6.0 | 0.3 ± 1.4 | 2.0 ± 1.9 | 5.8 ± 2.9 | 24.0 ± 7.1 | 66.2 ± 14.2 | 0.36 | 2.7e-30 |
| exag_stretch | 0.5 | 1.5 | -0.2 ± 0.5 | -0.2 ± 0.7 | 0.6 ± 0.9 | 2.6 ± 2.7 | 9.5 ± 4.5 | 0.13 | 1.9e-04 |
| exag_stretch | 0.5 | 3.0 | 0.1 ± 0.8 | 2.2 ± 1.4 | 4.8 ± 2.8 | 14.6 ± 6.0 | 50.5 ± 11.5 | 0.29 | 1.2e-19 |
| exag_stretch | 0.5 | 6.0 | -1.9 ± 1.5 | 0.8 ± 2.7 | 11.7 ± 5.8 | 38.5 ± 11.4 | 114.1 ± 24.9 | 0.36 | 1.5e-30 |
| exag_stretch | 1.0 | 1.5 | 0.0 ± 0.3 | 0.5 ± 0.7 | 1.9 ± 1.9 | 8.0 ± 4.3 | 16.0 ± 6.5 | 0.18 | 9.0e-08 |
| exag_stretch | 1.0 | 3.0 | 0.7 ± 2.1 | -0.2 ± 2.0 | 0.8 ± 4.1 | 20.9 ± 10.2 | 62.7 ± 18.3 | 0.28 | 7.1e-18 |
| exag_stretch | 1.0 | 6.0 | -4.1 ± 3.4 | -10.4 ± 5.0 | -18.7 ± 11.3 | 25.1 ± 25.6 | 83.1 ± 39.4 | 0.27 | 2.2e-17 |

### Mean profit by k and spread (all g_max, lam)
| attack | k | 0.25 | 0.5 | 1.0 |
|---|---|---|---|---|
| exag_consistent | 1 | 7.4 | 8.3 | -43.1 |
| exag_consistent | 3 | 7.9 | 7.8 | -51.4 |
| exag_stretch | 1 | 8.4 | 16.5 | 12.4 |
| exag_stretch | 3 | 8.6 | 17.3 | 9.1 |

## H4 (E4): damage grows with the liar's neighbours and with overlap p
Different N and p are different instances, so Spearman correlation is used instead of paired tests. Damage = extra cost over honest MGM, per liar.

### k = 1, pooled over N (confounded: the liar's degree grows with N)
| attack | protocol | Spearman(degree, damage) | Spearman(p, damage) | p deg (Holm) | p p (Holm) |
|---|---|---|---|---|---|
| block | MGM | 0.93 | 0.39 | 5.1e-199 | 7.5e-17 |
| block | VMGM-hist-quar | -0.34 | -0.22 | 7.8e-13 | 2.7e-05 |
| churn | MGM | 0.65 | -0.15 | 1.3e-53 | 1.5e-02 |
| churn | VMGM-hist-quar | -0.27 | -0.13 | 3.9e-08 | 5.3e-02 |
| sabotage | MGM | 0.12 | 0.04 | 1.1e-01 | 1.0e+00 |
| sabotage | VMGM-hist-quar | -0.10 | 0.03 | 2.3e-01 | 1.0e+00 |
| sabotage_consistent | MGM | -0.08 | 0.00 | 4.9e-01 | 1.0e+00 |
| sabotage_consistent | VMGM-hist-quar | -0.08 | 0.00 | 4.9e-01 | 1.0e+00 |

### k = 1, within each N (use this one)
| attack | protocol | N | Spearman(degree, damage) | p (Holm) |
|---|---|---|---|---|
| block | MGM | 12 | +0.73 | 1.6e-24 |
| block | MGM | 24 | +0.86 | 1.2e-44 |
| block | MGM | 48 | +0.88 | 7.1e-49 |
| block | VMGM-hist-quar | 12 | -0.30 | 3.2e-03 |
| block | VMGM-hist-quar | 24 | -0.26 | 1.7e-02 |
| block | VMGM-hist-quar | 48 | -0.38 | 3.8e-05 |
| churn | MGM | 12 | +0.29 | 4.8e-03 |
| churn | MGM | 24 | -0.43 | 6.9e-07 |
| churn | MGM | 48 | -0.51 | 8.7e-10 |
| churn | VMGM-hist-quar | 12 | -0.13 | 1.0e+00 |
| churn | VMGM-hist-quar | 24 | -0.21 | 1.3e-01 |
| churn | VMGM-hist-quar | 48 | -0.17 | 5.2e-01 |
| sabotage | MGM | 12 | +0.10 | 1.0e+00 |
| sabotage | MGM | 24 | +0.16 | 7.6e-01 |
| sabotage | MGM | 48 | -0.07 | 1.0e+00 |
| sabotage | VMGM-hist-quar | 12 | -0.13 | 1.0e+00 |
| sabotage | VMGM-hist-quar | 24 | +0.06 | 1.0e+00 |
| sabotage | VMGM-hist-quar | 48 | -0.08 | 1.0e+00 |
| sabotage_consistent | MGM | 12 | -0.12 | 1.0e+00 |
| sabotage_consistent | MGM | 24 | +0.07 | 1.0e+00 |
| sabotage_consistent | MGM | 48 | -0.07 | 1.0e+00 |
| sabotage_consistent | VMGM-hist-quar | 12 | -0.12 | 1.0e+00 |
| sabotage_consistent | VMGM-hist-quar | 24 | +0.07 | 1.0e+00 |
| sabotage_consistent | VMGM-hist-quar | 48 | -0.07 | 1.0e+00 |

### Mean rho by N and p (k = 1 and k = 25% of N pooled)
| protocol | attack | N | 0.02 | 0.04 | 0.08 |
|---|---|---|---|---|---|
| MGM | block | 12 | 5.14 | 7.28 | 8.72 |
| MGM | block | 24 | 6.75 | 8.63 | 9.56 |
| MGM | block | 48 | 9.18 | 9.72 | 7.93 |
| MGM | churn | 12 | 4.13 | 4.0 | 3.08 |
| MGM | churn | 24 | 3.86 | 2.93 | 1.95 |
| MGM | churn | 48 | 2.91 | 1.93 | 1.34 |
| MGM | sabotage | 12 | 2.08 | 2.12 | 1.86 |
| MGM | sabotage | 24 | 1.88 | 1.76 | 1.48 |
| MGM | sabotage | 48 | 1.75 | 1.5 | 1.22 |
| MGM | sabotage_consistent | 12 | 1.91 | 1.84 | 1.61 |
| MGM | sabotage_consistent | 24 | 1.7 | 1.54 | 1.36 |
| MGM | sabotage_consistent | 48 | 1.54 | 1.31 | 1.15 |
| VMGM-hist-quar | block | 12 | 1.72 | 1.59 | 1.39 |
| VMGM-hist-quar | block | 24 | 1.49 | 1.32 | 1.15 |
| VMGM-hist-quar | block | 48 | 1.3 | 1.13 | 1.05 |
| VMGM-hist-quar | churn | 12 | 1.75 | 1.63 | 1.46 |
| VMGM-hist-quar | churn | 24 | 1.53 | 1.38 | 1.18 |
| VMGM-hist-quar | churn | 48 | 1.34 | 1.16 | 1.05 |
| VMGM-hist-quar | sabotage | 12 | 1.88 | 1.84 | 1.65 |
| VMGM-hist-quar | sabotage | 24 | 1.68 | 1.6 | 1.43 |
| VMGM-hist-quar | sabotage | 48 | 1.6 | 1.41 | 1.23 |
| VMGM-hist-quar | sabotage_consistent | 12 | 1.91 | 1.84 | 1.61 |
| VMGM-hist-quar | sabotage_consistent | 24 | 1.7 | 1.54 | 1.36 |
| VMGM-hist-quar | sabotage_consistent | 48 | 1.54 | 1.31 | 1.15 |

### hist-quar at scale
| N | k | finished | det | dmg_max |
|---|---|---|---|---|
| 12.0 | 1.0 | 1.0 | 0.732 | 0.96 |
| 12.0 | 3.0 | 1.0 | 0.715 | 0.96 |
| 24.0 | 1.0 | 1.0 | 0.747 | 0.96 |
| 24.0 | 6.0 | 1.0 | 0.74 | 0.96 |
| 48.0 | 1.0 | 1.0 | 0.725 | 0.96 |
| 48.0 | 12.0 | 1.0 | 0.735 | 0.96 |

## E5: is "did not finish" caused by the 300-round limit?
Fraction finished with a 300 vs 1000 round limit. If a protocol does not finish at 300 but does at 1000, the limit was the problem; if it does not finish at either, it is genuinely stuck.
| protocol | attack | 300 | 1000 |
|---|---|---|---|
| MGM | block | 0.0 | 0.0 |
| MGM | churn | 0.0 | 0.0 |
| MGM | sabotage | 0.38 | 0.38 |
| RP-MGM | block | 1.0 | 1.0 |
| RP-MGM | churn | 0.0 | 0.0 |
| RP-MGM | sabotage | 0.45 | 0.45 |
| VMGM-hist-cap | block | 1.0 | 1.0 |
| VMGM-hist-cap | churn | 0.0 | 0.0 |
| VMGM-hist-cap | sabotage | 0.38 | 0.38 |
| VMGM-hist-quar | block | 1.0 | 1.0 |
| VMGM-hist-quar | churn | 1.0 | 1.0 |
| VMGM-hist-quar | sabotage | 1.0 | 1.0 |
| VMGM-move-cap | block | 1.0 | 1.0 |
| VMGM-move-cap | churn | 0.0 | 0.0 |
| VMGM-move-cap | sabotage | 0.38 | 0.38 |
