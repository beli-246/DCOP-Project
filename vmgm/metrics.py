"""Metrics for one run, all computed the same way in every experiment.

References (same instance, same start, same seed):
  ref_mgm  - honest MGM: the system reference for rho and extra cost.
  ref_self - the same protocol with everyone honest: reference for liar profit and honest loss,
             so lying is compared with honest play under the same algorithm.

Damage, kept apart as the reviewer asked:
  direct_H     = sum of -V over moves made by liars: net student cost added by their own moves.
                 This is what Result 4 bounds (per exam: dmg_exam_max < 1 in units of g_max).
                 It can be negative, since liars also make moves that lower student cost.
  extra        = F - F_ref (total damage vs honest MGM; measured, no bound against honest MGM)
  extra_H, extra_G = the student-cost and preference-cost parts of extra.
"""
import numpy as np

from . import model as M


def run_metrics(inst, res, types, lam, ref_mgm_x, ref_self_x):
    liars = {i for i, t in enumerate(types) if t != 'honest'}
    honest = [i for i in range(inst['N']) if i not in liars]
    F, H = M.F_cost(inst, res.x), M.H_cost(inst, res.x)
    F_mgm, H_mgm = M.F_cost(inst, ref_mgm_x), M.H_cost(inst, ref_mgm_x)
    direct = sum(-m['v'] for rnd in res.trace for m in rnd if m['dept'] in liars)
    per_exam = {}
    for rnd in res.trace:
        for m in rnd:
            if m['dept'] in liars:
                per_exam[m['e']] = per_exam.get(m['e'], 0.0) - m['v']
    fr = [res.flag_round[i] for i in liars if i in res.flag_round]
    return dict(
        F=F, H=H, G=F - H, K=M.clash_students(inst, res.x),
        F0=M.F_cost(inst, res.x0), F_ref=F_mgm, rho=F / F_mgm if F_mgm else float('nan'),
        extra=F - F_mgm, extra_H=H - H_mgm, extra_G=(F - H) - (F_mgm - H_mgm), direct_H=direct,
        dmg_exam_max=(max(per_exam.values()) / inst['gmax']) if per_exam else 0.0,
        rounds=res.rounds, finished=not res.capped,
        detected=len(res.flagged & liars), false_flags=len(res.flagged - liars),
        det_rate=(len(res.flagged & liars) / len(liars)) if liars else float('nan'),
        flag_round_mean=float(np.mean(fr)) if fr else float('nan'),
        liar_profit=float(np.mean([M.J(inst, ref_self_x, i, lam) - M.J(inst, res.x, i, lam) for i in liars]))
        if liars else 0.0,
        honest_loss=sum(M.burden(inst, res.x, i) - M.burden(inst, ref_self_x, i) for i in honest),
        liar_deg=float(np.mean([len(inst['nbr'][i]) for i in liars])) if liars else float('nan'),
    )


def dsa_metrics(inst, x, rounds, capped, x0, types, lam, ref_mgm_x, ref_self_x):
    """DSA has no trace or flags; same fields where they make sense."""
    liars = {i for i, t in enumerate(types) if t != 'honest'}
    honest = [i for i in range(inst['N']) if i not in liars]
    F, H = M.F_cost(inst, x), M.H_cost(inst, x)
    F_mgm, H_mgm = M.F_cost(inst, ref_mgm_x), M.H_cost(inst, ref_mgm_x)
    return dict(
        F=F, H=H, G=F - H, K=M.clash_students(inst, x), F0=M.F_cost(inst, x0), F_ref=F_mgm,
        rho=F / F_mgm if F_mgm else float('nan'), extra=F - F_mgm, extra_H=H - H_mgm,
        extra_G=(F - H) - (F_mgm - H_mgm), direct_H=float('nan'),
        dmg_exam_max=float('nan'), rounds=rounds, finished=not capped, detected=0, false_flags=0,
        det_rate=float('nan'), flag_round_mean=float('nan'),
        liar_profit=float(np.mean([M.J(inst, ref_self_x, i, lam) - M.J(inst, x, i, lam) for i in liars]))
        if liars else 0.0,
        honest_loss=sum(M.burden(inst, x, i) - M.burden(inst, ref_self_x, i) for i in honest),
        liar_deg=float(np.mean([len(inst['nbr'][i]) for i in liars])) if liars else float('nan'),
    )
