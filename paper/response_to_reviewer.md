# Response to the review of "Who Is Gaming the Timetable?"

Beli Dedhia, Khushi Garg, Ananya Patel, Poojan Soni

> *"The claimed damage bound limits the increase in student cost caused directly by a dishonest
> department's own moves, it does not establish a bound on total system cost or guarantee termination.
> The experiments should distinguish these guarantees and test whether the history-check mechanism
> remains effective when several departments behave dishonestly."*

Thank you; we agree with all three points. The abstract over-claimed ("limits its damage"). Below, each
part of the comment is matched to what we changed. Section, table and result numbers refer to the final
report (paper/DCOP_v4.pdf), which also summarises these changes in its introduction. Every number below is
printed by `python -m vmgm.paper_numbers vmgm_results/full`.

## 1. "The bound limits only the student cost caused directly by the liar's own moves"

* **Result 4 is renamed "Direct damage limit"** and followed by a sentence listing what it does *not*
  bound: total cost, honest departments' reactions, blocked improvements, and the cap-only response.
* **The abstract and introduction** now name three separate guarantees instead of "limits its damage".
* **A new table (Table 2)** lists every property, what it applies to, whether it is *proven*,
  *not guaranteed* or *measured only*, and the evidence from the experiments.

## 2. "It does not establish a bound on total system cost"

We added two results and found that one kind of bound is impossible.

* **Result 6 (new): a global bound relative to the starting timetable.** With the history check and
  quarantine, F_final ≤ F_start + 2·g_max·|E_L|, where E_L are the dishonest departments' exams. Honest
  MGM satisfies F_final ≤ F_start, so liars can make the result worse than the start only by a fixed
  amount.
  It is a worst case: in our runs with liars the final cost was above the start in only 124 of 58,240
  runs, by at most 20% of the allowed amount.
* **Result 7 (new): no bound relative to honest MGM's result is possible.** A one-exam example shows that
  a department playing truthfully for a fake preference (undetectable by Result 3) can make the ratio to
  honest MGM unbounded. So the ratio ρ to honest MGM is reported as a *measured* quantity, and the paper
  says so explicitly. In that example the gap is the liar's own preference cost, so the experiments also
  report the honest departments' loss separately.

## 3. "...or guarantee termination"

* **Result 5 (new): termination.** With the history check and quarantine, every run finishes, for any
  number of dishonest departments. The proof uses a potential: student cost + honest departments'
  preference cost + each unflagged liar's cost under a fake preference that explains its claims. It
  strictly falls in every round in which anything moves, and the run cannot freeze, because "no move"
  has priority 0.
* **We also state where termination fails:** with cap-only or the one-post check, a flagged department
  can churn forever. The experiments confirm it: those variants finish only 75% of runs under attack
  (plain MGM 55%, RP-MGM 77%), and raising the round limit from 300 to 1000 changes nothing.

## 4. "The experiments should distinguish these guarantees"

The main experiment (E2, Figure 1) reports the three quantities separately, and Table 2 gives the evidence
for each across E1–E5:

| Quantity | Status | Result (history check + quarantine) |
|---|---|---|
| Direct damage per exam | proven (Result 4) | largest 0.99·g_max over all 58,440 runs in E1–E5 (0.96·g_max in E2); cap-only reaches 144·g_max |
| Termination | proven (Result 5) | 100% of runs finished |
| Total cost vs honest MGM, ρ | measured only (Result 7) | 1.10 / 1.21 / 1.33 / 1.71 for k = 1 / 2 / 3 / 6 |

We also added a **control experiment**: everyone honest, with the same departments quarantined at the same
rounds. It shows that about half of the remaining excess cost is the price of quarantine itself
(ρ = 1.06–1.33; 61% of the excess at k = 1, 46% at k = 6), paid mainly by the quarantined departments
(honest departments carry 4–6% of it). Lying adds about 14 burden units to the honest departments' loss
beyond quarantine alone, at k = 6.

Every proven property is also **checked automatically on every run** of the simulator, including that
the potential of Result 5 falls in every round. 123,720 V-MGM runs, no violation.

## 5. "Test whether the history check remains effective when several departments behave dishonestly"

* **k = 1, 2, 3 and 6 dishonest departments out of 12**, placed next to each other or spread out, with
  the same or mixed attack types. We added two attacks built to stress the guarantees: a consistent
  saboteur that spends its whole budget without ever being caught, and a delayed attacker that
  contradicts itself only after 20 rounds.
* **Result:** the history check flagged every blocker and 99.8–100% of churners at every k (the 5
  unflagged churners in 1,600 runs had not contradicted themselves before their runs ended), never
  flagged an honest department, and every run finished. Placing liars next to each other made no
  significant difference.
* **Scale:** with N = 48 and 12 dishonest departments, every run still finished and the direct-damage
  bound held.

## Other changes

* **H1** now holds for malicious attacks only: selfish inflation does no measurable harm to MGM.
* **H3:** the original design could not show anything, because generated preferences filled the whole
  scale. We now vary how much of the scale true preferences use. The strongest undetectable liar's
  profit rises with κ in all 18 settings.
* **H4:** the liar's number of neighbours grows with N, so we now compare within each N. Blocking damage
  grows with neighbours under MGM; churn has no consistent trend.
* **Collusion** stays out of scope. The checks and Results 2–6 work one department at a time, so the
  proven guarantees hold under collusion; only total damage could change, and we have not measured that
  (Limitations).
