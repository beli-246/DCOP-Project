# pyDCOP agreement check (issue #5)

This folder checks our simulator against [pyDCOP](https://github.com/Orange-OpenSource/pyDcop), an
independent DCOP library (Rust, Picard, Ramparany, OptMAS 2019) with its own MGM. It checks three
things: that both compute the same cost, that they agree on what an MGM local optimum is, and how
close the final costs are. The results are in [`results.md`](results.md).

| File | What it is |
|---|---|
| `export.py` | Writes our loose instances (seeds 100–119) to pyDCOP YAML in `instances/`. Runs in the **project** environment. |
| `check.py` | Runs pyDCOP's MGM, performs the three checks and writes `results.md`. Runs in the **pyDCOP** environment. |
| `pydcop_fixed.py` | The `pydcop` command with a one-line fix to pyDCOP's MGM (see below). |
| `instances/` | The exported DCOPs (`loose_<seed>.yaml`) and distributions (`loose_<seed>_dist.yaml`, department = agent). |
| `runs/stock/`, `runs/fixed/` | Raw pyDCOP outputs (JSON) that `results.md` was computed from. |

## How to re-run

```bash
# 1. pyDCOP environment (once). The PyPI release (0.1.1) has a broken `pydcop` launcher, so install
#    from GitHub. PuLP must be 2.0: pyDCOP imports `pulp.solvers`, which PuLP removed in 2.1, and PuLP
#    1.x uses time.clock, which Python 3.8 removed. Conda has no Python 3.7 for Apple Silicon.
conda create -y -n pydcop python=3.8
conda activate pydcop
pip install git+https://github.com/Orange-OpenSource/pyDcop.git@a51cc3f7d8ef9ee1f863beeca4ad60490862d2ed
pip install pulp==2.0
pydcop --help

# 2. Export (project environment, from the repository root)
python -m validation.pydcop.export

# 3. Check (pyDCOP environment, from the repository root)
conda activate pydcop
python -m validation.pydcop.check            # uses the saved runs in runs/ (a few seconds)
python -m validation.pydcop.check --rerun    # runs pyDCOP's MGM again, 2 x 20 runs (about 5 min)
```

`vmgm.model` and `vmgm.protocol` use only the standard library, so `check.py` imports them under
Python 3.8 directly. It exits with 0 if check 1 passes and check 2 passes for the fixed pyDCOP MGM.

## What we found in pyDCOP's MGM

The cost model agrees exactly: check 1 matches on 2,000 / 2,000 timetables, and check 2(a) matches the
reported cost on 20 / 20 runs. pyDCOP's MGM (`pydcop/algorithms/mgm.py` at commit `a51cc3f`) has three
problems. Two of them we avoid in how we write the YAML. One needs the fix in `pydcop_fixed.py`:

1. **A variable with no neighbours ignores its unary constraints.** In `on_start`, such a variable
   takes `optimal_cost_value(variable)`, which looks only at the variable's own `cost_function`. With
   none, that is a random value. Some of our exams share no students. *Workaround (export):* each such
   exam gets an all-zero constraint `link_e_f` with another exam of its own department. The constraint
   costs nothing, so check 1 is unaffected, and it puts the exam through the normal MGM rounds.
2. **A variable's `cost_function` is ignored when MGM chooses a value.** `_compute_best_value` calls
   `find_arg_optimal` on the constraints only, then adds the cost function at the *current* value.
   *Workaround (export):* preferences are written as one-variable extensional constraints `g_e`, not as
   cost functions. We tried cost functions first: pyDCOP's MGM then ignored the preferences and ended
   far above our MGM.
3. **The current cost goes stale.** A variable computes its current local cost only in its first cycle
   (`if self.current_cost is None`). After that it only subtracts its own gains when it moves; when a
   neighbour moves, the cost is not recomputed. Gains are then measured against a wrong baseline, and
   a variable can miss an improving move. *Fix:* `pydcop_fixed.py` resets the stored cost at the start
   of every cycle, so the existing first-cycle code recomputes it. Nothing else changes. With stock
   pyDCOP, check 2(b) holds on 13 / 20 instances; with the fix it holds on 20 / 20.
   A second, independent run of the fixed version also gave 20 / 20.

We report both versions in `results.md`. The fix is applied at run time and pyDCOP's installed files
are not edited.

## Agent/variable mapping and why "local optimum" means the same thing

* Exam `e` → variable `x_e`. Department `i` → agent `d<i>`, which hosts the variables of its own 4 exams.
* pyDCOP's MGM runs one computation per variable. A variable moves when its gain beats every variable
  it shares a constraint with. Its local cost is `g_e` plus each binary term containing `e`, so its
  gain for a move is exactly the drop in our `F_cost` for that single-exam move.
* So pyDCOP has nothing left to do exactly when, for every department `i`,
  `vmgm.model.best_move(inst, x, i, inst['g'])[1] is None`. That is our definition of a local optimum.
* The runs themselves differ. In pyDCOP several exams of one department can move in the same round.
  In ours, each department moves at most one exam, and departments compete with neighbouring
  departments. That is why check 3 compares only mean final costs.
