# Project context: "Who Is Gaming the Timetable?"

Handoff note for anyone joining the project (team member, TA, or another AI session).
Team: Beli Dedhia, Khushi Garg, Ananya Patel, Poojan Soni (IIT Gandhinagar, multi-agent systems course).
Last updated: 8 Nov 2026 (after Phase 5 draft).

---

## 1. The idea in one paragraph

Exam timetabling can be solved by the departments themselves, as a **distributed constraint
optimisation problem (DCOP)**: each department sets the slots of its own exams, and a standard local-search
algorithm, **MGM**, lets the department that announces the largest improvement ("gain") move first.
MGM trusts those announcements, so a dishonest department can lie to grab turns, freeze its
neighbours, or keep the search from ever finishing. Our key observation: in exam timetabling, most of a
gain (the student clash and back-to-back costs) can be **recomputed by anyone from public data**. Only
the department's own preference part is private, and it lies on a fixed scale 0..g_max. So posted gains
can be checked. We build **V-MGM** (verified MGM): MGM plus checks on every announcement, plus a response
to departments caught lying, and we show what the checks can and cannot catch and how much damage liars
can still do.

## 2. Model and method (short)

* **Costs.** Total cost F = H + G. H is the student cost: 10 per student per clash, 2 per student per
  back-to-back pair on the same day. G is the sum of each department's private preference costs
  g_e(slot) ∈ {0..g_max}.
* **Gain of a move.** It splits as V (public, recomputable from the board) + P (private, |P| ≤ g_max).
  A department posts a move and a claimed gain Γ. Anyone can compute the claimed private part r = Γ − V.
* **Two checks:**
  * **One-post check:** flag if |r| > g_max (Result 1: truthful posts always pass).
  * **History check:** each claim says "slot a costs me r more than slot a′". Keep a running score per
    slot for each exam. Flag if a slot gets two different scores, or if the scores spread more than
    g_max (Result 2: this flags exactly the inconsistent histories and never a truthful one).
* **Priority** is capped at min(Γ, V + g_max), so even unflagged lies can only claim the scale's maximum.
* **Responses to a flagged department:**
  * **cap-only:** keep the capped priority.
  * **quarantine:** priority = V, so it can only make moves that lower student cost.
* **Main method: history check + quarantine.** The other combinations are baselines, together with
  plain MGM, RP-MGM (random priority, ignores claims) and DSA (posts no gains).
* **Attacks** (fixed threat model, not equilibrium play):

  | Attack | What the liar does |
  |---|---|
  | T1a/b exaggerate | posts its selfish gain (naive) / plays truthfully for a fake preference (consistent) |
  | T2a/b inflate | huge claim / V + g_max |
  | T3a block | always a huge claim |
  | T3b churn | best-V move every round, claim V + g_max |
  | T4 sabotage | harmful move, claim V + g_max |

* **Results in the proposal:**
  * **Result 1:** the one-post check is safe; honest posts are never flagged.
  * **Result 2:** the history check catches every contradiction.
  * **Result 3:** consistent lies cannot be detected from public data.
  * **Result 4:** damage limit. Each exam's own moves add < g_max student cost while its owner is
    unflagged, and < |E_i|·g_max per department under quarantine.

## 3. The reviewer's feedback and what we decided

> "The claimed damage bound limits the increase in student cost caused directly by a dishonest
> department's own moves, it does not establish a bound on total system cost or guarantee termination.
> The experiments should distinguish these guarantees and test whether the history-check mechanism
> remains effective when several departments behave dishonestly."

The comment is fair: the abstract over-claimed ("limits its damage"). Decisions:

1. **Reword Result 4** as a *direct student-cost bound*. Say explicitly what it does not bound: total
   cost, indirect effects, lost improvements, termination, cap-only.
2. **Add new theory** (see section 4): termination, a global bound relative to the *starting* timetable,
   and a negative result showing that no bound relative to *honest MGM's result* is possible.
3. **Experiments report three things separately:**
   * direct damage (proven);
   * total damage ρ = F_final / F(honest MGM) (measured only);
   * termination (proven and checked).
4. **k independent dishonest departments** (k = 0, 1, 2, 3, 6; placed next to each other or spread out;
   one attack type or mixed).
5. **Out of scope:** collusion, any bound against honest MGM, adaptive attackers. Collusion is only
   mentioned: the checks and the proven bounds work one department at a time, so they still hold under
   collusion; only total damage would change.
6. **Guiding principle:** fewest errors and most useful concepts, not extra complexity.

## 4. New theory (proposed; not yet written up as proofs)

These have been tested in code over 183k runs without a single violation, but **the written proofs still
need doing and checking** (Phase 1, owner Beli).

* **Result 5: termination (history check + quarantine only).**
  * Define the potential Φ = H + G_honest + Σ g̃_j. The sum runs over liars not yet flagged.
  * g̃_j is a fake preference explaining liar j's whole history up to its flag. It exists because the
    history check passed.
  * Pick g̃_j **once per liar**, not per phase; re-picking breaks the argument.
  * Every executed move lowers Φ:
    * honest moves, by their true gain;
    * unflagged liars, by their claimed gain, which is > 0;
    * quarantined liars need V > 0 and their G is not in Φ.
  * Flagging removes a term that is ≥ 0.
  * So Φ strictly decreases. With finitely many timetables and at most k flags, the run always finishes.
  * This does **not** hold for cap-only or the one-post check. A flagged liar can churn forever there,
    and the experiments show it does.
* **Result 6: global bound.** From Φ_final ≤ Φ_start:
  **F_final ≤ F_start + 2·g_max·(number of liar exams).**
  Honest MGM satisfies F_final ≤ F_start. Same scope as Result 5. Loose from a random start.
* **Result 7: negative.** The draft uses a simple example: one exam, and a department playing truthfully
  for a reversed fake preference. Honest MGM ends at F = 0 and the liar at F = g_max, so no bound of the
  form F ≤ c·F(honest MGM) can hold. Optional: a stronger example where the gap is in student cost and
  grows with the number of students.

## 5. Code (`vmgm/`)

The original pilot is in `DCOP_prelim_code_results/` (untouched). The new package reproduces it exactly
(regression: **11,640 pilot rows, 0 mismatches**) and adds automatic checks. It needs only Python 3 +
numpy, plus scipy/pandas for the analysis. See `vmgm/README.md` for details.

| File | Purpose |
|---|---|
| `model.py` | instances, costs, public gain V, starts. `pref_spread` lets true preferences use only part of the scale (1.0 = pilot instances). |
| `attacks.py` | pilot attacks plus the new ones below |
| `protocol.py` | MGM / V-MGM / RP-MGM / DSA with full trace; `record` mode; `forced_quarantine` for the control experiment |
| `invariants.py` | checks run on every experiment run; any failure stops the experiment |
| `liars.py` | placing k liars (random / adjacent / spread), mixed attacks |
| `metrics.py` | ρ, extra, extra_H/extra_G, direct_H, dmg_exam_max, honest_loss, liar_profit, detection, finished |
| `experiments.py` | E1–E5 runner (parallel) |
| `analysis.py` | statistics: paired 95% CIs, Wilcoxon, Holm, Spearman → `summary.md` |
| `regression.py` | reproduces the pilot's saved JSON |
| `sweep.py` | earlier invariant sweep over k |
| `figures.py` | paper figures (PDF/PNG) and LaTeX tables from the CSVs |
| `tests/test_vmgm.py` | 19 unit tests, all passing |

**New attacks:**
* `sabotage_consistent`: the worst liar Result 4 allows. It makes harmful moves while keeping its history
  consistent, so it is never flagged and spends its whole budget.
* `delayed`: the same, then blocks from round 20, so it gets flagged late.
* `exag_stretch`: the strongest undetectable exaggeration. It plays truthfully for
  g̃ = min(g_max, λ·(g − min g)).

**Automatic checks on every run:**
* no honest department flagged;
* per-exam direct damage < g_max (Result 4);
* Φ strictly falls every round (Result 5);
* F_final ≤ F_start + 2·g_max·(number of liar exams) (Result 6);
* the run finishes.

The Φ check is not vacuous: it fails on plain MGM, cap-only and one-post runs under attack.

**Commands** (from the repository root):

```bash
python3 -m unittest discover -s vmgm/tests -t .
```

```bash
python3 -m vmgm.regression DCOP_prelim_code_results 30
```

```bash
python3 -m vmgm.experiments all --seeds 50 --workers 7 --out vmgm_results/full
```

```bash
python3 -m vmgm.analysis vmgm_results/full
```

The full experiment run takes about 1 hour on 7 cores. Experiment instances use seeds 100–149, disjoint
from the pilot's 0–29.

## 6. Experiments and results (`vmgm_results/full/`, summary in `summary.md`)

183,400 runs, 50 instances per setting, loose (10 slots, p = 0.08) and tight (6 slots, p = 0.14)
families, random and greedy starts. **Every proven check held in every run.**

| Hypothesis | Experiment | Outcome |
|---|---|---|
| H1: lying hurts MGM more than RP-MGM / DSA | E1 | **Partly supported.** Block and churn: ρ higher by 3.6 and 1.0 (p < 1e-32). Selfish inflation (T2): no measurable harm. |
| H2a: blockers and churners flagged | E2 | **Supported.** 100% at k = 1, 2, 3, 6. |
| H2b: every run finishes | E2, E5 | **Supported** for history + quarantine (100%). Others 53–86% under attack, and they stay stuck at 1000 rounds too. |
| H2c: direct damage < g_max | E2 | **Supported.** Worst 0.96·g_max over 16,000 runs; 0 false flags. |
| H2d: total damage | E2 | **Measured.** History + quarantine ρ = 1.10, 1.21, 1.33, 1.71 for k = 1, 2, 3, 6. Quarantine alone (control) = 1.06 → 1.33, so it causes most of the cost. Honest departments lose ≤ ~14 burden units beyond quarantine. |
| H3: undetectable lying pays, more as κ grows | E3 | **Supported** for `exag_stretch`: profit ≈ 0 at κ ≤ 0.6, +16 to +114 at κ = 4.5, rising with κ. The pilot's clipped T1b liar often loses. |
| H4: damage grows with neighbours and overlap | E4 | **Supported only for blocking under plain MGM:** within each N, Spearman +0.73 to +0.88 with liar degree. Churn: the pooled correlation was confounded by N (within N it is +0.29, −0.43, −0.51). Sabotage: no effect. Under V-MGM damage stays near zero. At N = 48 with 12 liars, every run still finished. |

Other findings:
* **Liar placement:** next to each other vs spread out makes no significant difference.
* **Record mode:** posted vs executed gives identical results in 100% of runs.
* **Trade-off:**
  * For selfish attacks, cap-only already gives ρ = 1.00 while quarantine costs 1.33.
  * For churn and mixed attacks, cap-only fails (ρ ≈ 2.2–2.3) and quarantine is needed (≈ 1.36).
  * A graded response (cap oversized claims, quarantine contradictions) would help, but it loses the
    termination proof. Suggestion: keep quarantine as the main method, report its cost, and list the
    graded response as future work.

## 7. Status by phase

| Phase | What | Status |
|---|---|---|
| 0 | Freeze scope | Done (section 3) |
| 1 | Theory: reword Result 4, write Results 5–7, second-person check | **Written in the draft** (`paper/DCOP_v4.tex`, Section 4). The line-by-line check by a second person is still needed. |
| 2 | Code cleanup + automatic checks | **Done** |
| 3 | Experiments E1–E5 | **Done** |
| 4 | Figures, proven-vs-measured tables | **Done**: `paper/figures/` (fig1–fig5) and `paper/tables/` (2 LaTeX tables), regenerated by `python3 -m vmgm.figures vmgm_results/full paper` |
| 5 | Paper revision + response to reviewer | **Drafted**: `paper/DCOP_v4.tex` + `paper/response_to_reviewer.md`. Not compiled (no LaTeX here; needs `arxiv.sty` + `references.bib` from Overleaf). Over 4 pages; see TODOs. |

## 8. Open decisions and to-dos

1. **Record mode.** The pilot records claims when posted; the proposal says "after each move". Results
   are identical, so switch the default to `'executed'` and make the text match.
2. **Check the proofs** of Results 5–6 in the draft line by line (second person). Optionally strengthen the Result 7 example.
3. **CP-SAT reference values and the pyDCOP agreement check** are not reconnected (ortools and pyDCOP not
   installed).
4. **Phase 4 is done.** Choose which figures fit the 4-page limit; Figure 1 plus `tab_guarantees` answer the reviewer directly.
5. **Paper (drafted in `paper/`; still to do):** compile in Overleaf, cut to the page limit, resolve the `% TODO(team)` lines, check the proofs of Results 5–6 line by line. The original list of edits, now all in the draft:
   * abstract: "limits its damage" → "limits the student cost its own moves add"; "every run finished"
     → measured, now also proven;
   * reword Result 4 and add Results 5–7;
   * split H2 into a–d in Table 2;
   * H1: say it holds for malicious attacks only;
   * E3: explain the preference-spread redesign;
   * Limitations: total damage and the cost of quarantine.
6. **Response to reviewer:** drafted in `paper/response_to_reviewer.md`.

## 9. Things that are easy to get wrong

* **ρ counts the liars' own preference cost too.** Use `honest_loss` when the question is "were honest
  departments hurt?".
* **`direct_H` can be negative,** because liars also make good moves. Result 4 bounds the per-exam net
  sum; `dmg_exam_max` is the quantity to compare against 1.
* **The liar's number of neighbours grows with N,** so pooled correlations with degree are confounded. Compare within each N (Figure 5, `summary.md`).
* **Instance density doesn't change with N.** With p fixed, about 73% of department pairs are neighbours
  regardless of N, so E4 varies p to get variation in the liar's degree.
* **Uniform preferences fill the whole scale,** leaving no room for undetectable exaggeration. That is
  why E3 uses `pref_spread` < 1.
* **The global bound (Result 6) is loose from a random start,** because F_start is large. It is
  informative from the greedy start.
* **Quarantine-control runs are exempt from the checks,** because they quarantine honest departments on
  purpose.

## 10. File map (this repository)

```
DCOP-Project/
├── README.md                          overview + quick-start commands
├── PROJECT_CONTEXT.md                 this file
├── requirements.txt
├── vmgm/                              Python package (README.md inside)
│   └── tests/                         19 unit tests
├── vmgm_results/
│   ├── sweep_k.csv, sweep_k.log       first invariant sweep over k
│   └── full/                          E1–E5 CSVs + summary.md + full_run.log (the real results)
└── paper/
    ├── DCOP_v4.tex                    revised paper draft
    ├── response_to_reviewer.md
    ├── figures/                       fig1–fig5 (.pdf)
    ├── tables/                        tab_guarantees.tex, tab_e2_k3.tex
    └── archive/
        └── DCOP_Idea_Review_v3final4pg.pdf   proposal the reviewer commented on
```

Not in this repository (only on Poojan's machine): the pilot `DCOP_prelim_code_results/` (needed by
`vmgm.regression`), the v3 LaTeX source, the `smoke/` outputs, the `.png` figures and `CAPTIONS.md`.
