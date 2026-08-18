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


def fit_twoway(x, y, c1, n1, c2, n2):
    """Probit P = Φ(a·x + b[c1] + d[c2]); returns (sigma = 1/a, b, d, nll, converged)."""
    from scipy.optimize import minimize
    from scipy.stats import norm
    def unpack(th):
        return np.exp(th[0]), th[1:1 + n1], th[1 + n1:1 + n1 + n2]
    def nll(th):
        a, b, d = unpack(th); z = a * x + b[c1] + d[c2]; P = np.clip(norm.cdf(z), 1e-12, 1 - 1e-12)
        return -(y * np.log(P) + (1 - y) * np.log(1 - P)).sum()
    def grad(th):
        a, b, d = unpack(th); z = a * x + b[c1] + d[c2]; Phi = norm.cdf(z); phi = norm.pdf(z); P = np.clip(Phi, 1e-12, 1 - 1e-12)
        gz = (y / P - (1 - y) / (1 - P)) * phi
        return -np.concatenate([[(gz * x).sum() * a], np.bincount(c1, weights=gz, minlength=n1), np.bincount(c2, weights=gz, minlength=n2)])
    th0 = np.concatenate([[np.log(0.4)], np.full(n1, -1.5), np.zeros(n2)])
    r = minimize(nll, th0, jac=grad, method="L-BFGS-B", options={"maxiter": 3000})
    a, b, d = unpack(r.x)
    return 1 / a, b, d, r.fun, bool(r.success)


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
    # ---- within-player perception noise: probit with cell + player fixed effects (players with >= 5 challenges; rest pooled)
    fe_lines = []
    try:
        sc = pd.read_parquet(os.path.join(ROOT, "data", "raw", "statcast", "statcast_2026.parquet"), columns=["game_pk", "at_bat_number", "pitch_number", "fielder_2"])
        for side, who in (("fld", "catchers"), ("bat", "batters")):
            s = o[o["side"] == side].copy()
            if side == "fld":
                s = s.merge(sc, on=["game_pk", "at_bat_number", "pitch_number"], how="left"); s["pid"] = s["fielder_2"]
            else:
                s["pid"] = s["batter"]
            nch = s.groupby("pid")["challenged"].sum(); keep = nch[nch >= 5].index
            s["pgrp"] = np.where(s["pid"].isin(keep), s["pid"], -1)
            cs = cells[side]; cidx = {c: i for i, c in enumerate(cs)}; ci = s["cell"].map(cidx); ok = ci.notna().values
            s = s[ok]; ci = ci[ok].values.astype(int)
            pl = sorted(s["pgrp"].unique()); pidx = {p_: i for i, p_ in enumerate(pl)}; pi_ = s["pgrp"].map(pidx).values.astype(int)
            x = s["x_margin"].values.astype(float); y = s["challenged"].values.astype(float)
            sig0, _, _, nll0, _ = fit_twoway(x, y, ci, len(cs), np.zeros(len(s), dtype=int), 1)
            sig1, _, d1, nll1, _ = fit_twoway(x, y, ci, len(cs), pi_, len(pl))
            fe_lines.append(f"- {who}: σ pooled {sig0:.2f} in vs σ with player fixed effects {sig1:.2f} in (players with ≥5 challenges: {len(keep)} of {s['pid'].nunique()}; "
                            f"LR = {2*(nll0-nll1):.0f} on {len(pl)-1} df; SD of player threshold effects {np.std(d1[1:])*sig1:.2f} in).")
            # reliability of individual differences (players with >= 10 challenges): threshold effects vs their Fisher SEs; overturn rates vs binomial noise
            from scipy.stats import norm as _norm
            keep10 = nch[nch >= 10].index
            s10 = s.copy(); s10["pgrp"] = np.where(s10["pid"].isin(keep10), s10["pid"], -1)
            pl10 = sorted(s10["pgrp"].unique()); pi10 = s10["pgrp"].map({p_: i for i, p_ in enumerate(pl10)}).values.astype(int)
            sig2, b2, d2, _, _ = fit_twoway(x, y, ci, len(cs), pi10, len(pl10))
            a = 1 / sig2; z = a * x + b2[ci] + d2[pi10]; P = np.clip(_norm.cdf(z), 1e-9, 1 - 1e-9); phi = _norm.pdf(z)
            info = np.bincount(pi10, weights=phi ** 2 / (P * (1 - P)), minlength=len(pl10)); se_in = sig2 / np.sqrt(np.maximum(info, 1e-9))
            eff = d2 * sig2; msk = np.arange(len(pl10)) > 0
            var_obs = np.var(eff[msk], ddof=1); mean_se2 = np.mean(se_in[msk] ** 2); var_true = max(var_obs - mean_se2, 0.0)
            chp = s[s["challenged"] == 1].groupby("pid").agg(n=("isOverturned", "size"), r=("isOverturned", "mean")); chp = chp[chp["n"] >= 10]
            vo = chp["r"].var(ddof=1); vs = (chp["r"] * (1 - chp["r"]) / chp["n"]).mean()
            fe_lines.append(f"  - reliability ({who}, ≥10 challenges, n={int(msk.sum())}): threshold (willingness) effects — observed SD {np.sqrt(var_obs):.2f} in, mean SE {np.sqrt(mean_se2):.2f} in, "
                            f"signal share {var_true/max(var_obs,1e-12):.2f}; overturn-rate (accuracy) — SD of player rates {np.sqrt(vo):.3f}, mean binomial SE {np.sqrt(vs):.3f}, signal share {max(vo-vs,0)/max(vo,1e-12):.2f}.")
    except Exception as e:
        fe_lines.append(f"- player fixed-effects fit skipped: {e!r}")
    md = ("# Perception heterogeneity — 2026 (σ, τ by subgroup; cell thresholds held to the same cell structure)\n\n" + df.round(3).to_string(index=False) +
          "\n\n## Challenges by role\n\n" + rr.round(3).to_string() + "\n\n## Within-player perception noise (cell + player fixed effects)\n\n" + "\n".join(fe_lines) + "\n")
    with open(os.path.join(DERIVED, "perception_hetero_2026.md"), "w") as fh:
        fh.write(md)
    print(md)


if __name__ == "__main__":
    main()
