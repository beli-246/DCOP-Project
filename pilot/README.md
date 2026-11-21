# Pilot (first version of the simulator)

This folder is the original pilot study: the first version of the simulator, which produced the
numbers in Table 3 of the project review (`paper/archive/DCOP_Idea_Review_v3final4pg.pdf`).
It is kept **unchanged** (copied as is from `DCOP_prelim_code_results/`) so that anyone can check that the
cleaned-up package `vmgm/` reproduces it exactly.

| File | What it is |
|---|---|
| `prelim.py` | pilot simulator: instances, MGM, V-MGM variants, RP-MGM, DSA, pilot attacks |
| `prelim_loose.json`, `prelim_tight.json` | saved pilot results, 30 seeds per family (read by the regression) |
| `summarise.py`, `summary.txt`, `summary_attacks.csv` | the pilot's summary script and its output |
| `check_prop4.py` | the pilot's property check for the damage bound (Proposition 4 at the time) |
| `regression.log` | output of the regression below |

## Regression

From the repository root:

```bash
python -m vmgm.regression pilot 30
```

It recomputes every pilot row with `vmgm/` (both families, 30 seeds, random and greedy starts, every pilot
protocol and attack, k = 1, 2) and compares F, H, K, rounds, capped, detections, false positives, liar
profit and honest loss with the saved JSON. Result (`regression.log`): **11,640 rows compared, 0 mismatches**
(about 6 minutes on one core).

Only the protocols the pilot ran are compared. Soft quarantine (`VMGM-hist-soft`, #14) and the newer attacks
(T1c, T5–T7) were added after the pilot and have no pilot rows. CP-SAT fields are not compared.

To re-run the pilot itself (not needed for the regression; it overwrites the JSON files), from this folder:

```bash
python prelim.py loose 30
```
