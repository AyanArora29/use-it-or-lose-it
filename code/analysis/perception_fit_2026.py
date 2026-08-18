"""
perception_fit_2026.py — Tier-1 descriptive perception curves and the reduced-form/structural challenge-propensity fits.
METHODS §5.

Model (per side s ∈ {bat = batting team on a called strike, fld = fielding team on a called ball}):
    P(challenge | x, cell) = Φ((x − τ_cell) / σ_s)                                    [pooled probit]
    P(challenge | x, cell) = π_s · Φ((x − τ_cell) / σ_s)                              [hurdle probit]
where x is the true signed margin in the challenger's favour (inches; > 0 ⇒ the challenge would succeed) and cells are
inning band × tokens in hand × leverage tercile (of g, within side) × count class (PA-ending vs count-changing).
Heterogeneity check: probit with x and challenger-team fixed effects (thresholds by team) — the within-team slope is the
perception noise σ_within; the pooled slope conflates threshold heterogeneity (σ_pooled ≥ σ_within).
Also produces p_s(m): posterior success probability given the perceived signal m = x + ε, ε ~ N(0, σ_s²), with the empirical
prior f_s(x) over all eligible called pitches (this is the p the DP uses).

Outputs (data/derived/): perception_curves_2026.csv, perception_fit_2026.json, perception_pm_2026.npz, perception_report_2026.md
"""
from __future__ import annotations

import argparse
import json
import os

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import norm

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DERIVED = os.path.join(ROOT, "data", "derived")

INN_BAND = lambda inn: np.where(inn <= 3, "1-3", np.where(inn <= 6, "4-6", np.where(inn <= 8, "7-8", "9+")))
BINS = [-30, -6, -4, -3, -2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2, 3, 4, 6, 40]


def add_cells(o: pd.DataFrame, lev_q=None):
    o = o.copy()
    o["side"] = np.where(o["orig"] == "S", "bat", "fld")
    o["inn_band"] = INN_BAND(o["inning"].values)
    o["cnt"] = np.where(o["pa_ending"] == 1, "PA-ending", "count-changing")
    if lev_q is None:
        lev_q = {s: tuple(o.loc[o["side"] == s, "g"].quantile([1 / 3, 2 / 3]).values) for s in ("bat", "fld")}
    lev = np.empty(len(o), dtype=object)
    for s, (q1, q2) in lev_q.items():
        m = (o["side"] == s).values
        lev[m] = np.where(o.loc[m, "g"] < q1, "low", np.where(o.loc[m, "g"] < q2, "mid", "high"))
    o["lev"] = lev
    o["tok"] = np.where(o["tokens"] >= 2, "2", "1")
    o["cell"] = o["inn_band"] + "|" + o["tok"] + "|" + o["lev"] + "|" + o["cnt"]
    return o, lev_q


def fit_probit(x, y, cell_idx, n_cells, hurdle=False):
    """MLE of P(y=1) = [π] Φ((x − τ_c)/σ). Parameterised as Φ(a x + b_c), σ = 1/a, τ_c = −b_c/a; π = expit(h)."""
    def unpack(theta):
        a = np.exp(theta[0]); b = theta[1:1 + n_cells]
        pi = 1 / (1 + np.exp(-theta[-1])) if hurdle else 1.0
        return a, b, pi

    def nll(theta):
        a, b, pi = unpack(theta)
        z = a * x + b[cell_idx]
        P = np.clip(pi * norm.cdf(z), 1e-12, 1 - 1e-12)
        return -(y * np.log(P) + (1 - y) * np.log(1 - P)).sum()

    def grad(theta):
        a, b, pi = unpack(theta)
        z = a * x + b[cell_idx]
        Phi = norm.cdf(z); phi = norm.pdf(z)
        P = np.clip(pi * Phi, 1e-12, 1 - 1e-12)
        dP = (y / P - (1 - y) / (1 - P))            # dℓ/dP
        g_z = dP * pi * phi
        ga = (g_z * x).sum() * a                   # d/d log a
        gb = np.bincount(cell_idx, weights=g_z, minlength=n_cells)
        out = [-ga] + list(-gb)
        if hurdle:
            gpi = (dP * Phi).sum() * pi * (1 - pi)
            out.append(-gpi)
        return np.array(out)

    theta0 = np.concatenate([[np.log(0.4)], np.full(n_cells, -1.5), [1.5] if hurdle else []])
    res = minimize(nll, theta0, jac=grad, method="L-BFGS-B", options={"maxiter": 2000})
    a, b, pi = unpack(res.x)
    return dict(sigma=1 / a, tau=-b / a, pi=pi, nll=res.fun, converged=bool(res.success), n=int(len(x)), k=len(res.x))


def fit_twoway(x, y, c1, n1, c2, n2):
    """Probit P = Φ(a·x + b[c1] + d[c2]); returns (sigma = 1/a, b, d, nll, converged)."""
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


def posterior_pm(x_all, sigma, grid=np.linspace(-12, 12, 481)):
    """p(m) = P(x > 0 | m) under prior = empirical distribution of x (all eligible opportunities of the side) and m = x + ε."""
    hist_edges = np.arange(-30, 30.05, 0.1)
    h, _ = np.histogram(np.clip(x_all, -29.99, 29.99), bins=hist_edges)
    centers = 0.5 * (hist_edges[:-1] + hist_edges[1:])
    f = h / h.sum()
    like = norm.pdf((grid[:, None] - centers[None, :]) / sigma)  # (grid, centers)
    num = (like * (f * (centers > 0))[None, :]).sum(1); den = (like * f[None, :]).sum(1)
    return grid, num / np.maximum(den, 1e-300)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--opps", default=os.path.join(DERIVED, "opps_2026.parquet"))
    args = ap.parse_args()
    o = pd.read_parquet(args.opps)
    o = o[(o["pos_pitcher"] == 0)].copy()
    sc_path = os.path.join(ROOT, "data", "raw", "statcast", "statcast_2026.parquet")
    if os.path.exists(sc_path):
        sc = pd.read_parquet(sc_path, columns=["game_pk", "at_bat_number", "pitch_number", "fielder_2"])
        o = o.merge(sc, on=["game_pk", "at_bat_number", "pitch_number"], how="left")
    o, lev_q = add_cells(o)
    rep = ["# Perception fits — 2026 (METHODS §5)", ""]
    rep.append(f"- Sample: {len(o):,} eligible called pitches (position players pitching excluded); challenges {int(o['challenged'].sum()):,}.")

    # ---- Tier-1 descriptive curves ---------------------------------------------------------------------------
    o["xb"] = pd.cut(o["x_margin"], BINS)
    rows = []
    for (side, tok), s in o[o["tokens"] >= 1].groupby(["side", "tok"]):
        t = s.groupby("xb", observed=True).agg(n=("challenged", "size"), p_challenge=("challenged", "mean"), truth=("truth", "mean"))
        t["p_overturn_given_challenge"] = s[s["challenged"] == 1].groupby("xb", observed=True)["isOverturned"].mean()
        t["n_challenges"] = s[s["challenged"] == 1].groupby("xb", observed=True).size()
        t = t.reset_index(); t["side"] = side; t["tokens"] = tok
        rows.append(t)
    curves = pd.concat(rows, ignore_index=True)
    curves["xb"] = curves["xb"].astype(str)
    curves.to_csv(os.path.join(DERIVED, "perception_curves_2026.csv"), index=False)
    # by role within fielding side (catcher vs pitcher) at large margins
    big = o[(o["x_margin"] > 1.5) & (o["tokens"] >= 1)]
    rep.append("- P(challenge | clear miss, x > 1.5 in, tokens ≥ 1): " + "; ".join(
        f"{s}: {v:.3f} (n={n:,})" for s, v, n in big.groupby("side")["challenged"].agg(["mean", "size"]).reset_index().itertuples(index=False)))
    rep.append("- P(challenge | x > 1.5 in) by tokens: " + "; ".join(
        f"{s}/t={t}: {v:.3f}" for (s, t), v in big.groupby(["side", "tok"])["challenged"].mean().items()))
    rep.append("- P(challenge | x > 1.5 in) by count class: " + "; ".join(
        f"{s}/{c}: {v:.3f}" for (s, c), v in big.groupby(["side", "cnt"])["challenged"].mean().items()))
    rep.append("- P(challenge | x > 1.5 in) by leverage tercile: " + "; ".join(
        f"{s}/{l}: {v:.3f}" for (s, l), v in big.groupby(["side", "lev"])["challenged"].mean().items()))
    rep.append("- P(challenge | x > 1.5 in) by inning band: " + "; ".join(
        f"{s}/{b}: {v:.3f}" for (s, b), v in big.groupby(["side", "inn_band"])["challenged"].mean().items()))
    wrong = o[(o["x_margin"] < -1.5) & (o["tokens"] >= 1)]
    rep.append("- P(challenge | clearly correct call, x < −1.5 in): " + "; ".join(
        f"{s}: {v:.4f}" for s, v in wrong.groupby("side")["challenged"].mean().items()))

    # ---- fits per side -------------------------------------------------------------------------------------------
    fits = {"lev_q": {k: [float(v[0]), float(v[1])] for k, v in lev_q.items()}, "sides": {}}
    pm = {}
    for side in ("bat", "fld"):
        s = o[(o["side"] == side) & (o["tokens"] >= 1)]
        cells = sorted(s["cell"].unique()); cidx = {c: i for i, c in enumerate(cells)}
        ci = s["cell"].map(cidx).values.astype(int)
        x = s["x_margin"].values.astype(float); y = s["challenged"].values.astype(float)
        f0 = fit_probit(x, y, ci, len(cells), hurdle=False)
        f1 = fit_probit(x, y, ci, len(cells), hurdle=True)
        # heterogeneity: two-way probits Φ(a·x + b_cell + c_group) with group = challenging team, and group = player
        # (players with >= 5 challenges; the rest pooled). The within-group slope is the perception noise net of group thresholds.
        team = np.where(s["team_home"] == 1, s["home_team"], s["away_team"])
        teams = sorted(set(team)); ti = pd.Series(team).map({t: i for i, t in enumerate(teams)}).values.astype(int)
        sig_team, _, d_team, nll_team, _ = fit_twoway(x, y, ci, len(cells), ti, len(teams))
        pid = s["batter"].values if side == "bat" else s["fielder_2"].values if "fielder_2" in s else None
        if pid is not None:
            pid = pd.Series(pid).fillna(-9).values
            nch = pd.Series(y).groupby(pid).sum(); keep = set(nch[nch >= 5].index)
            pg = np.array([p_ if p_ in keep else -1 for p_ in pid]); pl = sorted(set(pg)); pi_ = pd.Series(pg).map({p_: i for i, p_ in enumerate(pl)}).values.astype(int)
            sig_pl, _, d_pl, nll_pl, _ = fit_twoway(x, y, ci, len(cells), pi_, len(pl))
        else:
            sig_pl, d_pl, nll_pl, pl = float("nan"), np.zeros(1), float("nan"), []
        lr = 2 * (f0["nll"] - f1["nll"])
        fits["sides"][side] = dict(cells=cells, pooled=dict(sigma=float(f0["sigma"]), tau={c: float(t) for c, t in zip(cells, f0["tau"])}, nll=float(f0["nll"]), n=f0["n"]),
                                   hurdle=dict(sigma=float(f1["sigma"]), pi=float(f1["pi"]), tau={c: float(t) for c, t in zip(cells, f1["tau"])}, nll=float(f1["nll"])),
                                   team_fe=dict(sigma=float(sig_team), sd_team_effect_in=float(np.std(d_team) * sig_team), nll=float(nll_team)),
                                   player_fe=dict(sigma=float(sig_pl), n_players=int(max(len(pl) - 1, 0)), sd_player_effect_in=float(np.std(d_pl[1:]) * sig_pl) if len(pl) > 1 else float("nan"), nll=float(nll_pl)),
                                   lr_hurdle_vs_pooled=float(lr))
        rep.append(f"- **{side}**: pooled probit σ = {f0['sigma']:.2f} in (n={f0['n']:,}); hurdle probit σ = {f1['sigma']:.2f} in, π = {f1['pi']:.3f} "
                   f"(LR vs pooled = {lr:.1f} on 1 df); two-way probit with cell + team thresholds: σ = {sig_team:.2f} in (SD of team effects {np.std(d_team)*sig_team:.2f} in); "
                   f"cell + player thresholds: σ = {sig_pl:.2f} in ({max(len(pl)-1,0)} players with ≥5 challenges; SD of player effects {np.std(d_pl[1:])*sig_pl if len(pl)>1 else float('nan'):.2f} in).")
        tau = pd.Series(f0["tau"], index=cells)
        by = {}
        for part, pos in (("inning band", 0), ("tokens", 1), ("leverage", 2), ("count class", 3)):
            grp = tau.groupby([c.split("|")[pos] for c in cells]).median()
            by[part] = grp.round(2).to_dict()
        rep.append(f"  - median threshold τ (pooled model) by {by}")
        grid, p_m = posterior_pm(o.loc[o["side"] == side, "x_margin"].values, f0["sigma"])
        pm[f"grid_{side}"] = grid; pm[f"p_{side}"] = p_m
        pm[f"sigma_{side}"] = f0["sigma"]
        # implied success probability at the fitted thresholds: p(m = τ) for typical cells
        rep.append(f"  - implied posterior success at the median threshold: p(m=τ̃) = {np.interp(np.median(f0['tau']), grid, p_m):.3f}; "
                   f"p(m=0) = {np.interp(0, grid, p_m):.3f}; p(m=2) = {np.interp(2, grid, p_m):.3f}; p(m=4) = {np.interp(4, grid, p_m):.3f}")
    np.savez(os.path.join(DERIVED, "perception_pm_2026.npz"), **pm)
    with open(os.path.join(DERIVED, "perception_fit_2026.json"), "w") as fh:
        json.dump(fits, fh, indent=1)
    with open(os.path.join(DERIVED, "perception_report_2026.md"), "w") as fh:
        fh.write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
