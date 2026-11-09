# Who Is Gaming the Timetable?

Catching dishonest departments in distributed exam scheduling.
Multi-Agent Systems course project, IIT Gandhinagar.
Beli Dedhia, Khushi Garg, Ananya Patel, Poojan Soni.

In MGM, the department that announces the biggest improvement moves first, so a liar can grab turns
or stop progress. V-MGM checks each department's history of claims against public data, quarantines
departments that contradict themselves, and provably bounds direct damage, guarantees termination,
and bounds the final cost relative to the start.

## Layout

```
.
├── PROJECT_CONTEXT.md     handoff note: decisions, results, open to-dos (start here)
├── vmgm/                  Python package: simulator, attacks, checks, experiments, analysis, figures
│   ├── README.md          details: files, commands, invariants, attacks, open decisions
│   └── tests/             unit tests (stdlib unittest)
├── vmgm_results/
│   ├── full/              E1–E5.csv, summary.md, full_run.log  (main experiments)
│   └── sweep_k.csv/.log   k-sweep with invariant checks
└── paper/
    ├── DCOP_v4.tex        revised paper (needs arxiv.sty + references.bib from Overleaf)
    ├── figures/           fig1–fig5 (generated)
    ├── tables/            LaTeX tables (generated)
    ├── response_to_reviewer.md
    └── archive/           earlier submitted version (v3)
```

## Quick start

All commands run from the repository root. Needs Python 3.10+.

```bash
pip install -r requirements.txt

python -m unittest discover -s vmgm/tests -t . -v                         # tests
python -m vmgm.experiments all --seeds 50 --workers 7 --out vmgm_results/full   # ~1 h on 7 cores
python -m vmgm.analysis vmgm_results/full                                # -> vmgm_results/full/summary.md
python -m vmgm.figures vmgm_results/full paper                           # -> paper/figures, paper/tables
```

The simulator itself needs only numpy; pandas, scipy and matplotlib are for the experiments,
statistics and figures. See [vmgm/README.md](vmgm/README.md) for the experiment grid and metrics.
