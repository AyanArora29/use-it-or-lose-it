"""
decompose_2026.py — where the observed shortfall vs the information-constrained optimum comes from (METHODS §7):
by side (batting team on called strikes vs fielding team on called balls), inning band, count class, and margin bin;
and the "who should hold the trigger" counterfactual (batters with catcher-level perception).
Input: data/derived/tier1_opps_with_breakeven.parquet (from tier1_dp_2026.py). Output: tier1_decomposition_2026.md/.csv
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DERIVED = os.path.join(ROOT, "data", "derived")


def main():
    op = pd.read_parquet(os.path.join(DERIVED, "tier1_opps_with_breakeven.parquet"))
    n_tg = op.groupby(["game_id", "team_home"]).ngroups
    op["inn_band"] = np.where(op["inning"] <= 3, "1-3", np.where(op["inning"] <= 6, "4-6", np.where(op["inning"] <= 8, "7-8", "9+")))
    op["cnt"] = np.where((op["balls"] == 3) | (op["strikes"] == 2), "PA-ending", "count-changing")
    op["obs_gain"] = op["g"] * op["challenged"] * op["overturned"]
    op["opt_gain"] = op["g"] * op["prop_optimal"] * op["truth"]
    op["obs_used"] = op["challenged"]; op["opt_used"] = op["prop_optimal"]
    op["obs_succ"] = op["challenged"] * op["overturned"]; op["opt_succ"] = op["prop_optimal"] * op["truth"]
    op["oracle_gain"] = op["g"] * op["truth"]
    rep = ["# Shortfall decomposition — 2026 (observed vs information-constrained optimum)", "",
           "Levels per team-game. The optimum is one global policy evaluated on the same streams; a negative per-band gap means the optimum spends fewer tokens there because it spent them earlier, not that teams out-perform it there.", ""]
    rep.append(f"- Per team-game: observed {op['obs_gain'].sum()/n_tg*100:.3f} pp; optimum {op['opt_gain'].sum()/n_tg*100:.3f} pp; oracle {op['oracle_gain'].sum()/n_tg*100:.3f} pp; "
               f"gap {(op['opt_gain'].sum()-op['obs_gain'].sum())/n_tg*100:.3f} pp ({(op['opt_gain'].sum()-op['obs_gain'].sum())/n_tg*162:.2f} wins/162).")
    rows = []
    for keys, name in (["role"], "side"), (["inn_band"], "inning band"), (["role", "inn_band"], "side × inning band"), (["cnt"], "count class"), (["role", "cnt"], "side × count class"), (["tokens_obs"], "tokens in hand (observed)"):
        t = op.groupby(keys).agg(opps=("g", "size"), obs_used=("obs_used", "sum"), opt_used=("opt_used", "sum"), obs_succ=("obs_succ", "sum"), opt_succ=("opt_succ", "sum"),
                                 obs_gain=("obs_gain", "sum"), opt_gain=("opt_gain", "sum"), oracle_gain=("oracle_gain", "sum")).reset_index()
        for c in ["obs_used", "opt_used", "obs_succ", "opt_succ"]:
            t[c] = t[c] / n_tg
        for c in ["obs_gain", "opt_gain", "oracle_gain"]:
            t[c] = t[c] / n_tg * 100
        t["gap_pp"] = t["opt_gain"] - t["obs_gain"]   # levels; the optimum is a global policy, so per-band gaps can be negative (it spends tokens earlier by design)
        t["obs_succ_rate"] = t["obs_succ"] / t["obs_used"]; t["opt_succ_rate"] = t["opt_succ"] / t["opt_used"]
        t.insert(0, "by", name)
        rows.append(t)
        rep.append(f"- By {name} (per team-game; gains in WP points):\n\n" + t.drop(columns=["by"]).round(3).to_string(index=False) + "\n")
    # margin bins: where are the missed opportunities?
    op["xb"] = pd.cut(op["x"], [-30, -1, 0, 0.5, 1, 1.5, 2, 3, 40])
    t = op.groupby("xb", observed=True).agg(opps=("g", "size"), obs_used=("obs_used", "mean"), opt_used=("opt_used", "mean"), obs_gain=("obs_gain", "sum"), opt_gain=("opt_gain", "sum")).reset_index()
    t["obs_gain"] = t["obs_gain"] / n_tg * 100; t["opt_gain"] = t["opt_gain"] / n_tg * 100; t["gap_pp"] = t["opt_gain"] - t["obs_gain"]
    rep.append("- By true margin (challenge propensity observed vs optimal, gains per team-game):\n\n" + t.round(3).to_string(index=False) + "\n")
    # failed challenges: ex-post cost by side/inning
    ch = op[op["challenged"] == 1]
    rep.append(f"- Actual challenges: {len(ch):,}; overturned {ch['overturned'].mean():.3f}; mean g of overturned {ch.loc[ch['overturned']==1,'g'].mean()*100:.3f} pp; "
               f"mean g of failed {ch.loc[ch['overturned']==0,'g'].mean()*100:.3f} pp; mean decision-time MTV at failed challenges {ch.loc[ch['overturned']==0,'mtv_obs'].mean()*100:.3f} pp.")
    pd.concat(rows, ignore_index=True).to_csv(os.path.join(DERIVED, "tier1_decomposition_2026.csv"), index=False)
    with open(os.path.join(DERIVED, "tier1_decomposition_2026.md"), "w") as fh:
        fh.write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
