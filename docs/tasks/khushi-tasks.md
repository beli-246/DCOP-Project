# Tasks for Khushi: CP-SAT reference values (main) and a demo run (optional)

Assigned by Beli on Thursday 19 Nov 2026. **Deadline: Friday 20 Nov, 18:00**, as a pull request, so
there is time to review and recompile the report before we submit on Saturday 21 Nov (final deadline
Sunday 22 Nov).

Both tasks are yours in the project-review proposal ("CP-SAT references; visualisation and demo").
Right now the report's Contribution section says *"Khushi Garg: Partly: CP-SAT references and demo not
fulfilled"*, and Limitations says the CP-SAT reference values "were not carried out". Finishing Task 1
changes both to fulfilled, and adds a real result to the paper.

Read this whole file before starting. If anything here is unclear or turns out wrong, message Beli
before working around it.

---

## The rules that matter most

The graders said: *"We will verify whether the results you put in the paper are actually obtained
through your code."* So:

1. **Every number you add to the paper must be printed by our code.** Add it to
   `vmgm/paper_numbers.py` (it prints every number in the paper with a label saying where it is used).
   Never type a number into the paper by hand from a notebook or a one-off script.
2. **Do not change any existing result.** Do not edit `vmgm/model.py`, `attacks.py`, `protocol.py`,
   `invariants.py`, `metrics.py`, `experiments.py`, or anything in `vmgm_results/full/E1.csv`–`E5.csv`.
   Your work only *adds* files and a few lines.
3. **Use the project's own cost function as the ground truth.** Our cost is `vmgm.model.F_cost(inst, x)`.
   Your CP-SAT model must give *exactly* the same value for the timetable it returns (there is a test
   for this below). If it ever differs, the CP-SAT model is wrong, not `F_cost`.
4. **Work on a branch and open a pull request.** Do not upload files through the GitHub website (it
   puts them in the repository root and breaks the layout). Commands are at the end of this file.

---

## Task 1 (main): CP-SAT reference values

### Why we want this

All our results compare against **honest MGM**, which is a local search, so its result is a local
optimum, not the best possible timetable. We do not know how far MGM itself is from the best timetable.
CP-SAT is an exact solver: given everyone's true preferences (which no distributed algorithm has,
that is the whole point of the project), it finds the minimum total cost F, or a good timetable plus
a proven lower bound. This lets the paper say, for example, *"honest MGM ends X% above the best
timetable, and V-MGM with 3 liars ends Y% above it"*. That puts our ρ values in context.

### What I already checked (so you know it works)

I ran a quick prototype of exactly the skeleton below on seed 100 with OR-Tools 9.15:

| Instance | Status | CP-SAT cost | Lower bound | `F_cost` of the CP-SAT timetable | Time | Honest MGM final F |
|---|---|---|---|---|---|---|
| loose, seed 100 | OPTIMAL | 218 | 218 | 218 (matches) | 0.2 s | 329 (random start), 460 (greedy start) |
| tight, seed 100 | FEASIBLE (not proven optimal) | 833 | 574 | 833 (matches) | 60 s limit | 1399 (random), 1388 (greedy) |

So: **loose instances solve to proven optimality in under a second; tight ones do not finish in 60 s.**
Your plan must handle that (see "Tight instances" below). Your numbers must come from your own run, not
from this table.

### What to build

#### 1. `vmgm/cpsat.py` (new file)

A module with:

* `solve(inst, time_limit=..., workers=8, seed=0, hint=None)` returning a dict:
  `status` (`'OPTIMAL'` or `'FEASIBLE'`), `F_best` (cost of the best timetable found), `F_bound` (the
  solver's proven lower bound), `x` (the timetable: list of slots, one per exam), `time_s`.
* A command-line entry point:

  ```bash
  python -m vmgm.cpsat vmgm_results/full --time-loose 60 --time-tight 300 --workers 8
  ```

  It loops over **families `loose` and `tight` × seeds 100–149** (exactly the E1–E3 instances), builds
  each instance with `M.make_instance(seed, **M.FAMILIES[family])`, solves it, **asserts
  `M.F_cost(inst, x) == F_best`**, and writes `vmgm_results/full/cpsat.csv` with one row per instance:

  | column | meaning |
  |---|---|
  | `family`, `seed` | which instance (same keys as E1–E3) |
  | `status` | `OPTIMAL` or `FEASIBLE` |
  | `F_best` | cost of the best timetable found (always equal to `F_cost` of it) |
  | `F_bound` | proven lower bound on the optimum (equals `F_best` when `OPTIMAL`) |
  | `gap` | `(F_best - F_bound) / F_best` |
  | `time_s` | solve time |
  | `time_limit` | the limit used |
  | `ortools_version` | `ortools.__version__` |

  100 instances. Print progress like `experiments.py` does.

The instance does not depend on the starting timetable, so there is one CP-SAT value per instance
(not per start).

#### 2. The model (this exact skeleton reproduced `F_cost` in my test)

The cost (see `model.py`): each exam `e` gets one slot `a` in `0..S-1`; preference cost `g[e][a]`; for
each pair `(e, f)` in `inst['n']` with `c` shared students, the pair cost is `M.pc(a, a2, c)`:
`10·c` if same slot, `2·c` if consecutive slots **on the same day** (`a // 2 == a2 // 2`, two slots per
day, `M.SESS = 2`), else 0. Always compute pair costs by calling `M.pc`, never by re-typing the rule, so
the model cannot drift from the project's definition.

```python
from ortools.sat.python import cp_model
from . import model as M

def solve(inst, time_limit=60, workers=8, seed=0, hint=None):
    E, S = inst['E'], inst['S']
    m = cp_model.CpModel()
    b = [[m.NewBoolVar(f'b_{e}_{a}') for a in range(S)] for e in range(E)]   # exam e in slot a
    for e in range(E):
        m.AddExactlyOne(b[e])
    terms = [inst['g'][e][a] * b[e][a] for e in range(E) for a in range(S)]
    for (e, f), c in inst['n'].items():
        for a in range(S):
            for a2 in range(S):
                w = M.pc(a, a2, c)
                if w == 0:
                    continue
                y = m.NewBoolVar('')                     # 1 if e in a and f in a2
                m.AddBoolOr([b[e][a].Not(), b[f][a2].Not(), y])
                terms.append(w * y)
    m.Minimize(sum(terms))
    if hint is not None:                                 # optional warm start, see "Tight instances"
        for e in range(E):
            for a in range(S):
                m.AddHint(b[e][a], int(hint[e] == a))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_limit
    s.parameters.num_workers = workers
    s.parameters.random_seed = seed
    st = s.Solve(m)
    x = [next(a for a in range(S) if s.Value(b[e][a])) for e in range(E)]
    return dict(status=s.StatusName(st), F_best=int(round(s.ObjectiveValue())),
                F_bound=int(round(s.BestObjectiveBound())), x=x)   # add time_s yourself
```

(`y` only needs a lower bound: the objective pushes it to 0 unless both slots are chosen. If
`s.StatusName(st)` is neither `OPTIMAL` nor `FEASIBLE`, raise an error; do not write a row.)

#### 3. Tight instances

Tight instances (6 slots, more overlap) do not reach optimality quickly. Do this:

* Use a **300 s** limit for tight and 60 s for loose (on 8 workers that is about 4 h for all 50 tight
  instances in the worst case, so **start the run on Thursday night**). If that is too slow on your
  machine, use 120 s and say so. Whatever you use is recorded in the `time_limit` column.
* **Warm start (recommended):** pass `hint=` the honest MGM final timetable for that instance. To get it,
  run honest MGM yourself: `protocol.run(inst, x0, ['honest'] * inst['N'], 3.0, PROTOCOLS['MGM'], seed=sd).x`
  with `x0 = M.greedy_start(inst)`. CP-SAT then never returns anything worse than MGM.
* Report **both** numbers: `F_best` (a timetable that exists, so the true optimum is at most this) and
  `F_bound` (the optimum is at least this). Any ratio "MGM / optimum" is then reported as a range:
  `F_MGM / F_best` ≤ true ratio ≤ `F_MGM / F_bound`. Never call a FEASIBLE value "optimal".

#### 4. Tests: `vmgm/tests/test_cpsat.py` (new file)

Use stdlib `unittest`, like `test_vmgm.py`. Skip the whole class if ortools is not installed:
`@unittest.skipUnless(importlib.util.find_spec('ortools'), 'ortools not installed')`.

1. **Brute force on a tiny instance.** Build `M.make_instance(seed, N=3, per=2, S=4, p=0.5)` for a few
   seeds (6 exams, 4 slots → 4^6 = 4096 timetables). Enumerate all timetables with `itertools.product`,
   take the minimum `M.F_cost`, and assert CP-SAT returns `OPTIMAL` with exactly that value.
2. **Matches `F_cost` on a real instance.** For `loose` seed 100: `F_cost(inst, result['x']) == result['F_best']`
   and `F_bound <= F_best`.
3. **Never worse than its hint.** With `hint=` the honest MGM timetable, `F_best <= F_cost(inst, hint)`.

All existing tests must still pass: `python -m unittest discover -s vmgm/tests -t . -v`.

#### 5. Numbers for the paper: add to `vmgm/paper_numbers.py`

Add a section `head('CP-SAT reference (Setup, Results RQ2, Limitations)')` that reads
`vmgm_results/full/cpsat.csv` (skip the section with a note if the file does not exist) and prints:

* how many instances are OPTIMAL, per family; the median and largest `gap` of the FEASIBLE ones;
* **honest MGM vs the best timetable**: join E2 rows with `k == 0` and `protocol == 'MGM'` to
  `cpsat.csv` on `family, seed`; report the mean of `F / F_best` and of `F / F_bound`, per family and
  start (random, greedy). For loose, where all should be OPTIMAL, the two are equal;
* **V-MGM (history + quarantine) and MGM under attack vs the best timetable**: E2 rows with `k > 0`,
  protocols `VMGM-hist-quar` and `MGM`, mean `F / F_best` by `k` (1, 2, 3, 6), loose family only (proven
  optima), plus the same pooled over both families as a range using `F_bound`.

Then regenerate: `python -m vmgm.paper_numbers vmgm_results/full`. This writes
`vmgm_results/full/paper_numbers.md`; commit it.

#### 6. Paper changes (`paper/DCOP_v4.tex`): small and exact

The paper is exactly 8 pages + references now. **Add at most about 5 lines in total**, and compile to
check (Overleaf, or `cd paper && tectonic DCOP_v4.tex`); if it spills to a 9th page of text, shorten
your sentences, not other people's.

1. **Experimental setup, "Algorithms:"** after "...and cap only or quarantine." add one sentence like:
   *"As a reference that no distributed algorithm can reach, CP-SAT \citep{ortools} computes the best
   timetable centrally from everyone's true preferences (proven optimal on all loose instances; on tight
   instances a timetable and a lower bound after 300 s)."* Use your actual counts and limit.
2. **Results, RQ2 paragraph**, one sentence after the ρ values, like: *"Against the best timetable
   (CP-SAT, loose instances), honest MGM ends A\% above it and V-MGM with $k=1,3,6$ liars B, C and D\%
   above it."* All of A–D come from `paper_numbers.md`.
3. **Limitations:** change *"The CP-SAT reference values and the pyDCOP agreement check planned in the
   project review were not carried out;"* to *"The pyDCOP agreement check planned in the project review
   was not carried out;"* (keep the rest of the sentence). Remove the `% TODO(team)` comment there only if
   pyDCOP is still dropped (ask Ananya).
4. **Contribution table**, your row: change to *"Partly: demo not fulfilled."* or, if you also finish
   Task 2, *"Fulfilled."*.
5. **`paper/references.bib`**: the entry `ortools` says version 9.15; set it to the version you used
   (`ortools.__version__`).
6. **`requirements.txt`**: add the line `ortools`.
7. **`README.md`**: in the reproduce table, add a row
   `| CP-SAT reference values | python -m vmgm.cpsat vmgm_results/full --time-loose 60 --time-tight 300 --workers 8 | vmgm_results/full/cpsat.csv | about 4 h |`,
   and one line in the Results table with the headline number.

Do not change the meaning of any existing sentence. If the CP-SAT result changes the story (for example,
honest MGM is almost optimal, or very far), tell Beli and we decide together how to phrase it.

#### Definition of done (Task 1)

- [ ] `vmgm/cpsat.py`, `vmgm/tests/test_cpsat.py` added; all tests pass (old and new).
- [ ] `vmgm_results/full/cpsat.csv` has 100 rows; every row satisfied the `F_cost` assertion.
- [ ] `paper_numbers.py` prints the CP-SAT section; `paper_numbers.md` regenerated and committed.
- [ ] Paper edits 1–5 done; the PDF still has 8 pages of text with only References after; no `??`.
- [ ] `requirements.txt` and README updated.
- [ ] Pull request opened, with the headline numbers in its description.

---

## Task 2 (optional, only after Task 1): a demo of one run

### Why

The proposal promised a demo. It also makes the idea easy to see: one blocker freezing plain MGM, and
the same blocker caught and quarantined under V-MGM.

### What to build: `vmgm/demo.py`

```bash
python -m vmgm.demo            # prints the story of one run under MGM and under V-MGM
```

* **Use the real engine, do not re-implement it.** Build one small instance (for example
  `M.make_instance(seed, N=6, S=10, p=0.08)`; try a few seeds and pick one where the story is clear;
  hard-code that seed), choose one department as a blocker with `make_types(inst, {i}, 'block')`
  (from `vmgm/liars.py`), and call `protocol.run(...)` twice: with `PROTOCOLS['MGM']` and with
  `PROTOCOLS['VMGM-hist-quar']`, same start `M.greedy_start(inst)` and same seed.
* Print, from the returned `RunResult`: for each round in `res.trace`, which department moved which exam
  from which slot to which, its claim, the public gain `v`, and whether it was flagged
  (`res.flag_round`); the total cost F after each round (replay the moves on a copy of `res.x0` and call
  `M.F_cost`); and at the end: rounds, finished or not (`not res.capped`), final F, and F for honest MGM
  from the same start (run with all-honest types).
* Optionally save `docs/screenshots/demo_cost.png`: F per round for MGM, V-MGM, and honest MGM (use
  the colours in `figures.py`: V-MGM blue, MGM orange).
* Must run in under 10 seconds and give the same output every time.
* Add a "Demo" section to `README.md` with the command, a screenshot of its output, and two sentences
  explaining what it shows.

#### Definition of done (Task 2)

- [ ] `python -m vmgm.demo` runs in under 10 s, deterministic, uses `protocol.run`.
- [ ] README has a Demo section with a screenshot.
- [ ] Contribution row changed to "Fulfilled."

---

## How to work (git)

```bash
git checkout main
git pull
git checkout -b khushi-cpsat
pip install -r requirements.txt ortools
# ... work, then:
python -m unittest discover -s vmgm/tests -t . -v
python -m vmgm.paper_numbers vmgm_results/full
git add vmgm/cpsat.py vmgm/tests/test_cpsat.py vmgm_results/full/cpsat.csv vmgm_results/full/paper_numbers.md \
        vmgm/paper_numbers.py paper/DCOP_v4.tex paper/references.bib requirements.txt README.md
git commit -m "Add CP-SAT reference values"
git push -u origin khushi-cpsat
# then open a pull request on GitHub into main and tell Beli
```

If you recompile the PDF, also commit `paper/DCOP_v4.pdf`.

## Where things are

* Project overview and status: `README.md`, `PROJECT_CONTEXT.md`
* The report: `paper/DCOP_v4.tex` (Experimental setup is Section 4.5, Results Section 5)
* Cost model: `vmgm/model.py` (`make_instance`, `FAMILIES`, `pc`, `F_cost`, `greedy_start`)
* Running one protocol: `vmgm/protocol.py` (`run`, `PROTOCOLS`, `RunResult`)
* How E2 rows are produced: `vmgm/experiments.py` (`job_E2`); honest MGM rows are `k == 0, protocol == 'MGM'`
* Every number in the paper: `vmgm/paper_numbers.py` → `vmgm_results/full/paper_numbers.md`
