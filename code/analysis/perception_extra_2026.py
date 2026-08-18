"""
perception_extra_2026.py — heterogeneity of perceptual noise (σ) and thresholds (τ) by edge of the zone, pitch type,
velocity, count class, and challenger role; and a hurdle-vs-pooled comparison by subgroup.  METHODS §5 (Tier 2 preview).
Output: perception_hetero_2026.csv / .md
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
from perception_fit_2026 import add_cells, fit_probit  # noqa: E402

DERIVED = os.path.join(ROOT, "data", "derived")


def fit_group(s, cells):
    cidx = {c: i for i, c in enumerate(cells)}
    ci = s["cell"].map(cidx); ok = ci.notna().values
    if ok.sum() < 3000 or s.loc[ok, "challenged"].sum() < 40:
        return None
    f = fit_probit(s["x_margin"].values[ok].astype(float), s["challenged"].values[ok].astype(float), ci.values[ok].astype(int), len(cells))
    tau = np.array(f["tau"]); w = ci[ok].value_counts().reindex(range(len(cells))).fillna(0).values
    return dict(n=int(ok.sum()), challenges=int(s.loc[ok, "challenged"].sum()), sigma=float(f["sigma"]),
                tau_w=float(np.average(tau[w > 0], weights=w[w > 0])), p_clear=float(s.loc[ok & (s["x_margin"].values > 1.5), "challenged"].mean()),
                overturn=float(s.loc[ok & (s["challenged"] == 1), "isOverturned"].mean()))


def main():
    o = pd.read_parquet(os.path.join(DERIVED, "opps_2026.parquet"))
    o = o[(o["pos_pitcher"] == 0) & (o["tokens"] >= 1)].copy()
    fit = json.load(open(os.path.join(DERIVED, "perception_fit_2026.json")))
    o, _ = add_cells(o, {k: tuple(v) for k, v in fit["lev_q"].items()})
    cells = {s: fit["sides"][s]["cells"] for s in ("bat", "fld")}
    o["ptype"] = np.where(o["pitch_type"].isin(["FF", "SI", "FC", "FA"]), "fastball", np.where(o["pitch_type"].isin(["SL", "ST", "CU", "KC", "SV", "CS"]), "breaking", np.where(o["pitch_type"].isin(["CH", "FS", "FO", "SC"]), "offspeed", "other")))
    o["velo"] = pd.cut(o["release_speed"], [0, 85, 92, 110], labels=["<85", "85-92", "92+"])
    o["same_hand"] = np.where(o["stand"] == o["p_throws"], "same", "opposite")
    o["cnt"] = np.where(o["pa_ending"] == 1, "PA-ending", "count-changing")
    o["low_high"] = np.where(o["edge"] == "side", "side", "top/bottom")
    o["role_c"] = np.where(o["side"] == "bat", "batter", "fielding")
    rows = []
    for side in ("bat", "fld"):
        s0 = o[o["side"] == side]
        for by in ("edge", "low_high", "ptype", "velo", "same_hand", "cnt", "stand"):
            for k, s in s0.groupby(by, observed=True):
                r = fit_group(s, cells[side])
                if r:
                    rows.append(dict(side=side, by=by, group=str(k), **r))
    # fielding side by challenger role: pitcher-challenged vs catcher — role only known for challenged pitches; compare
    # the SUBSET of teams/games where pitchers challenge at all is not identifiable here; report overturn rates by role instead
    ch = o[o["challenged"] == 1]
    rr = ch.groupby("role").agg(n=("isOverturned", "size"), overturn=("isOverturned", "mean"), mean_x=("x_margin", "mean"), mean_g=("g", "mean"))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DERIVED, "perception_hetero_2026.csv"), index=False)
    md = ("# Perception heterogeneity — 2026 (σ, τ by subgroup; cell thresholds held to the same cell structure)\n\n" + df.round(3).to_string(index=False) +
          "\n\n## Challenges by role\n\n" + rr.round(3).to_string() + "\n")
    with open(os.path.join(DERIVED, "perception_hetero_2026.md"), "w") as fh:
        fh.write(md)
    print(md)


if __name__ == "__main__":
    main()
