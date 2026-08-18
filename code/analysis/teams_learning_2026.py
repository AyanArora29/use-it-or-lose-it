"""
teams_learning_2026.py — team heterogeneity in challenge use (H2: between-team SD of capture ratio after shrinkage) and
learning over the season (thresholds / residuals by month).  METHODS §7 (Q2).
Inputs: tier1_opps_with_breakeven.parquet, tier1_sim_optimal.parquet. Output: tier1_teams_2026.csv/.md
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from perception_fit_2026 import fit_probit  # noqa: E402

DERIVED = os.path.join(ROOT, "data", "derived")


def main():
    op = pd.read_parquet(os.path.join(DERIVED, "tier1_opps_with_breakeven.parquet"))
    o = pd.read_parquet(os.path.join(DERIVED, "opps_2026.parquet"), columns=["game_pk", "atBatIndex", "eventIndex", "home_team", "away_team", "game_date"])
    op = op.merge(o.rename(columns={"game_pk": "game_id", "atBatIndex": "abi", "eventIndex": "evi"}), on=["game_id", "abi", "evi"], how="left")
    op["team"] = np.where(op["team_home"] == 1, op["home_team"], op["away_team"])
    op["obs_gain"] = op["g"] * op["challenged"] * op["overturned"]
    op["opt_gain"] = op["g"] * op["prop_optimal"] * op["truth"]
    rep = ["# Teams and learning — 2026", ""]
    # ---- team table -----------------------------------------------------------------------------------------------
    tg = op.groupby(["team", "game_id"]).agg(obs=("obs_gain", "sum"), opt=("opt_gain", "sum"), used=("challenged", "sum"),
                                              succ=("overturned", lambda v: 0)).reset_index()
    ch = op[op["challenged"] == 1].groupby(["team", "game_id"]).agg(succ=("overturned", "sum")).reset_index()
    tg = tg.drop(columns=["succ"]).merge(ch, on=["team", "game_id"], how="left").fillna({"succ": 0})
    t = tg.groupby("team").agg(games=("game_id", "nunique"), obs=("obs", "mean"), opt=("opt", "mean"), used=("used", "mean"), succ=("succ", "mean"),
                               obs_sd=("obs", "std")).reset_index()
    t["capture_raw"] = t["obs"] / t["opt"]
    t["succ_rate"] = t["succ"] / t["used"]
    # shrinkage of the per-team gain difference (obs - opt) toward the league mean: empirical Bayes with within-team variance
    t["diff"] = t["obs"] - t["opt"]
    within_var = (tg.assign(d=tg["obs"] - tg["opt"]).groupby("team")["d"].var() / t.set_index("team")["games"]).reindex(t["team"]).values
    grand = np.average(t["diff"], weights=t["games"])
    between_var = max(np.var(t["diff"], ddof=1) - np.mean(within_var), 1e-12)
    shrink = between_var / (between_var + within_var)
    t["diff_shrunk"] = grand + shrink * (t["diff"] - grand)
    t["capture_shrunk"] = (t["opt"] + t["diff_shrunk"]) / t["opt"]
    t = t.sort_values("capture_shrunk", ascending=False)
    rep.append(f"- Between-team SD of the raw capture ratio: {t['capture_raw'].std():.3f}; after empirical-Bayes shrinkage: {t['capture_shrunk'].std():.3f} "
               f"(pre-registered threshold for 'material heterogeneity': 0.10). Reliability (between / (between + mean within) variance of obs−opt): {between_var/(between_var+np.mean(within_var)):.2f}.")
    rep.append("- Teams (per team-game WP points; capture = observed ÷ optimal for that team's own streams):\n\n" +
               t[["team", "games", "used", "succ_rate", "obs", "opt", "capture_raw", "capture_shrunk"]].assign(obs=lambda d: d["obs"] * 100, opt=lambda d: d["opt"] * 100).round(3).to_string(index=False) + "\n")
    # ---- learning: thresholds by month, by side --------------------------------------------------------------------
    op["month"] = pd.to_datetime(op["game_date"]).dt.month
    rows = []
    for side in ("bat", "fld"):
        s = op[(op["role"] == side) & (op["tokens_obs"] >= 1)]
        cells = sorted(s["cell"].unique()); cidx = {c: i for i, c in enumerate(cells)}
        for mth, sm in s.groupby("month"):
            if len(sm) < 5000:
                continue
            f = fit_probit(sm["x"].values.astype(float), sm["challenged"].values.astype(float), sm["cell"].map(cidx).values.astype(int), len(cells))
            tau = np.array(f["tau"]); w = sm["cell"].map(cidx).value_counts().reindex(range(len(cells))).fillna(0).values
            rows.append(dict(side=side, month=int(mth), n=len(sm), challenges=int(sm["challenged"].sum()), sigma=f["sigma"],
                             tau_weighted=float(np.average(tau[w > 0], weights=w[w > 0])),
                             p_challenge_clear=float(sm.loc[sm["x"] > 1.5, "challenged"].mean()),
                             overturn=float(sm.loc[sm["challenged"] == 1, "overturned"].mean()),
                             gap_pp=float((sm["opt_gain"].sum() - sm["obs_gain"].sum()) / sm["game_id"].nunique() * 100)))
    L = pd.DataFrame(rows)
    rep.append("- Learning: perception fits and use by month (τ weighted by cell frequency; gap = optimal − observed per game in that month's games, pp):\n\n" + L.round(3).to_string(index=False) + "\n")
    t.to_csv(os.path.join(DERIVED, "tier1_teams_2026.csv"), index=False); L.to_csv(os.path.join(DERIVED, "tier1_learning_2026.csv"), index=False)
    with open(os.path.join(DERIVED, "tier1_teams_2026.md"), "w") as fh:
        fh.write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
