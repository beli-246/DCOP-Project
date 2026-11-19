# vmgm: V-MGM with k dishonest departments (Phase 2 code)

Cleaned-up version of the pilot (`DCOP_prelim_code_results/prelim.py`). It reproduces the pilot's
numbers exactly and adds automatic checks of every proven result. The pilot folder is untouched.

The simulator needs only Python 3 + numpy (pandas, scipy, matplotlib for the analysis and figures).
CP-SAT (ortools) and pyDCOP are not used; the report says so.

## Files

| File | What it does |
|---|---|
| `model.py` | instances, costs (H, G, F), public gain V, best move, starts. Unchanged from the pilot. |
| `attacks.py` | what each department posts. Pilot attacks T1-T4, plus two new ones (below). |
| `protocol.py` | MGM / V-MGM variants / RP-MGM / DSA. Same round logic as the pilot, plus a trace and a public `Board` of history scores. |
| `invariants.py` | checks of the proven results; raises `InvariantError` on any failure. |
| `liars.py` | choosing k liars: `random`, `adjacent` (liars share students), `spread`; mixed attacks. |
| `regression.py` | recomputes the pilot's rows and compares with `prelim_*.json`. |
| `sweep.py` | runs every attack for k in {0,1,2,3,6} with checks on; skeleton of the E2 runner. |
| `tests/test_vmgm.py` | unit tests (stdlib `unittest`). |

## How to run (from the repository root)

```bash
python3 -m unittest discover -s vmgm/tests -t . -v
```

```bash
python3 -m vmgm.regression DCOP_prelim_code_results 30   # needs the pilot folder, not in this repo
```

```bash
python3 -m vmgm.sweep vmgm_results/sweep_k.csv 10
```

## Phase 3: experiments (`experiments.py`, `metrics.py`, `analysis.py`)

```bash
python3 -m vmgm.experiments all --seeds 50 --workers 7 --out vmgm_results/full
```

```bash
python3 -m vmgm.analysis vmgm_results/full
```

The full run takes about 1 hour on 7 cores and writes `E1.csv`–`E5.csv` plus `summary.md`.
Instances use seeds 100–149, disjoint from the pilot's 0–29. Every run with an audit goes through
`check_all`, except the quarantine-control runs.

| Exp | Tests | Grid |
|---|---|---|
| E1 | H1 | MGM, RP-MGM, DSA, hist-quar × hijack, maxbound, block, churn × k 1–3 |
| E2 | H2a–d | all protocols + record='executed' + quarantine control × 10 attacks (incl. mixed) × k 1,2,3,6 × adjacent/spread |
| E3 | H3 | g_max (kappa) × preference spread × lambda × exag_stretch / exag_consistent × k 1,3 |
| E4 | H4 | N 12/24/48 × p 0.02/0.04/0.08 × 4 attacks × k = 1 and 25% of N |
| E5 | round limit | 300 vs 1000 rounds |

Metrics (`metrics.py`): `rho`, `extra` (total, vs honest MGM), `extra_H`/`extra_G`, `direct_H`
(student cost from liars' own moves: what Result 4 bounds), `dmg_exam_max`, `honest_loss`,
`liar_profit`, `det_rate`, `false_flags`, `finished`.

`control-quar` rows: everyone honest, the departments that were flagged in the matching hist-quar run
quarantined from the same rounds. It isolates what quarantine itself costs.

`make_instance(pref_spread=s)`: true preferences use only `s·g_max` of the scale (s = 1 is the pilot's
instances). `exag_stretch` is the strongest undetectable exaggeration, used in E3.

## Phase 4: figures and tables (`figures.py`)

```bash
python3 -m vmgm.figures vmgm_results/full paper
```

This writes `paper/figures/fig1–fig5` (`.pdf` for LaTeX, `.png` for the README) and `paper/tables/tab_guarantees.tex`
and `paper/tables/tab_e2_k3.tex`, all from the CSVs.

## Every number in the report (`paper_numbers.py`)

```bash
python3 -m vmgm.paper_numbers vmgm_results/full
```

Prints every number quoted in the report text, each labelled with where it is used, and writes
`vmgm_results/full/paper_numbers.md`. Definitions match `analysis.py` and `figures.py`.

Colours follow the protocol in every figure: history + quarantine = blue, MGM = orange,
quarantine control = aqua, cap only = yellow, RP-MGM/DSA = greys. Every series also has its own
marker and line style, so the figures survive grayscale printing.

## Checks (`invariants.check_all`)

| Check | Applies to | Result it tests |
|---|---|---|
| no honest department flagged | any audit | Results 1, 2 |
| per-exam student cost added by the liar's own moves while unflagged < g_max | history check | Result 4 |
| same over the whole run < g_max | history + quarantine | Result 4 (quarantine part) |
| potential Phi = H + G_honest + sum of g~_j over unflagged liars strictly falls every round | history + quarantine | proposed Result 5 (termination) |
| F_final <= F_start + 2 g_max (number of liar exams) | history + quarantine | proposed Result 6 (global bound) |
| run finishes | history + quarantine | follows from Result 5 |

g~_j is fixed once per liar from its history scores at flag time (or at the end if it is never flagged).
The potential check is not vacuous: it fails on plain MGM, the one-post check and cap-only runs under attack.

## New attacks

* `sabotage_consistent`: the worst liar Result 4 allows. Each round it makes the most harmful move
  whose claim keeps its history consistent, and claims the most consistency allows. It is never flagged
  and really spends its budget (worst per-exam damage above 0.5 g_max in the tests).
* `delayed`: `sabotage_consistent` until round `switch_round` (default 20), then blocks, so it gets
  flagged at exactly that round. Measures damage done before detection.

## When is a claim recorded? (decided: when posted)

The history check records every consistent claim when it is posted, even if that department does not
win the round. `protocol['record']` selects either:

* `'posted'` (default, used for every result in the report): stricter, catches contradictions in
  claims about moves that never ran. The report (Result 2, Algorithm 1) describes this.
* `'executed'`: only claims whose move runs are recorded. E2 runs it as `VMGM-hist-quar-exec`; it gives
  the same final cost in 16,197 of 16,200 runs.

All checks pass under both.

## Known limits

* The global bound is loose from a random start (F_start is large); it is informative from the greedy start.
* `check_prop4.py` in the pilot folder duplicated the run loop by hand. It is replaced by
  `invariants.direct_damage`, which reads the real trace.
* CP-SAT reference values and the pyDCOP agreement check from the project review were not done.
