"""
robustness_2026.py — multiverse / sensitivity for the Tier-1 headline (METHODS §11): WP variant, coin-flip band in the
perception fit, hurdle (attention) perception model, perception-improvement counterfactual (batters with catcher-level σ),
and the DP ε-draw seed. Each variant re-fits what it must and re-runs the DP + optimal-policy simulation (numba).
Output: data/derived/tier1_robustness_2026.csv / .md
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd
from scipy.stats import norm

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code", "engine")); sys.path.insert(0, HERE)
import dp_fast as F  # noqa: E402
from perception_fit_2026 import add_cells, fit_probit, posterior_pm  # noqa: E402
from tier1_dp_2026 import half_inning_paths  # noqa: E402

DERIVED = os.path.join(ROOT, "data", "derived")
DMAX = F.DMAX


def fit_side(o, side, cells, hurdle=False, band=0.0):
    m = (o["side"] == side).values & (o["tokens"].values >= 1)
    if band > 0:
        m &= np.abs(o["x_margin"].values) >= band
    s = o[m]
    cidx = {c: i for i, c in enumerate(cells)}
    ci = s["cell"].map(cidx); ok = ci.notna().values
    return fit_probit(s["x_margin"].values[ok].astype(float), s["challenged"].values[ok].astype(float), ci.values[ok].astype(int), len(cells), hurdle=hurdle)


def run_variant(o, hi, gcol, pm, name, seed=100, D=60, pi=None, notes=""):
    rng = np.random.default_rng(seed)
    sig = np.where(o["side"] == "bat", pm["bat"][2], pm["fld"][2])
    m = o["x_margin"].values + rng.normal(0, 1, len(o)) * sig
    p = np.where(o["side"] == "bat", np.interp(m, pm["bat"][0], pm["bat"][1]), np.interp(m, pm["fld"][0], pm["fld"][1]))
    if pi is not None:   # hurdle: an opportunity is considered with probability π_side; unconsidered -> p = 0 (never challenged)
        consider = rng.random(len(o)) < np.where(o["side"] == "bat", pi["bat"], pi["fld"])
        p = np.where(consider, p, 0.0)
    op = pd.DataFrame({"game_id": o["game_pk"].values, "team_home": o["team_home"].values, "h": o["h"].values,
                       "score_diff_home": o["sd_home"].values, "g": o[gcol].values, "p": p, "outs": o["outs"].values,
                       "x": o["x_margin"].values, "truth": o["truth"].values, "role": o["side"].values,
                       "inning": o["inning"].values, "balls": o["balls"].values, "strikes": o["strikes"].values,
                       "challenged": o["challenged"].values, "overturned": o["isOverturned"].values,
                       "abi": o["atBatIndex"].values, "evi": o["eventIndex"].values})
    op = op.sort_values(["game_id", "abi", "evi"]).reset_index(drop=True)
    A = F.make_arrays(op, hi)
    V, C = F.solve_fast(A, n_iter=40, tol=1e-7)
    os_ = A["op_sorted"]
    if pi is not None:
        # simulate with attention: mask x so that unconsidered opps are never challenged -> emulate by setting truth/x? simplest:
        # run the simulator on the considered subset only (unconsidered opportunities carry no decision)
        keep = os_["p"].values > 0
        os_sim = os_[keep].reset_index(drop=True)
    else:
        os_sim = os_
    r_opt, _ = F.simulate_fast(os_sim, C, pm, "optimal", D=D, seed=7)
    r_orc, _ = F.simulate_fast(os_, C, pm, "oracle", D=1, seed=1)
    n_tg = os_.groupby(["game_id", "team_home"]).ngroups
    obs = (os_["g"] * os_["challenged"] * os_["truth"]).sum() / n_tg
    opt = r_opt["gain"].sum() / n_tg; orc = r_orc["gain"].mean()
    return dict(variant=name, sigma_bat=pm["bat"][2], sigma_fld=pm["fld"][2], V2_start_pp=V[1, DMAX, 2] * 100,
                MTV2_inn1_pp=(V[1, DMAX, 2] - V[1, DMAX, 1]) * 100, MTV1_inn1_pp=(V[1, DMAX, 1] - V[1, DMAX, 0]) * 100,
                MTV2_inn9_pp=(V[17, DMAX, 2] - V[17, DMAX, 1]) * 100, obs_pp=obs * 100, opt_pp=opt * 100, oracle_pp=orc * 100,
                capture=obs / opt, perception_cost=opt / orc, gap_wins162=(opt - obs) * 162, opt_used=r_opt["used"].sum() / n_tg,
                notes=notes)


def main():
    t0 = time.time()
    o = pd.read_parquet(os.path.join(DERIVED, "opps_2026.parquet"))
    o = o[o["pos_pitcher"] == 0].copy()
    fit = json.load(open(os.path.join(DERIVED, "perception_fit_2026.json")))
    lev_q = {k: tuple(v) for k, v in fit["lev_q"].items()}
    o, _ = add_cells(o, lev_q)
    cells = {s: fit["sides"][s]["cells"] for s in ("bat", "fld")}
    hi = half_inning_paths(os.path.join(ROOT, "data", "raw", "statcast", "statcast_2026.parquet"), set(o["game_pk"]))
    rows = []

    def pm_from(fb, ff, sig_override=None):
        pm = {}
        for side, f in (("bat", fb), ("fld", ff)):
            sg = f["sigma"] if sig_override is None else sig_override[side]
            grid, p_m = posterior_pm(o.loc[o["side"] == side, "x_margin"].values, sg)
            pm[side] = (grid, p_m, sg)
        return pm

    fb = fit_side(o, "bat", cells["bat"]); ff = fit_side(o, "fld", cells["fld"])
    pm0 = pm_from(fb, ff)
    rows.append(run_variant(o, hi, "g", pm0, "primary (WP v2, pooled probit, all pitches)", seed=100)); print(rows[-1], flush=True)
    rows.append(run_variant(o, hi, "g", pm0, "primary, second ε seed", seed=200)); print(rows[-1], flush=True)
    rows.append(run_variant(o, hi, "g", pm0, "primary, third ε seed", seed=300)); print(rows[-1], flush=True)
    # WP v1
    o_v1 = o.copy()
    ov1, lev_q1 = add_cells(o_v1.assign(g=o_v1["g_v1"]).drop(columns=["side", "inn_band", "cnt", "lev", "tok", "cell"]))
    fb1 = fit_side(ov1, "bat", cells["bat"]); ff1 = fit_side(ov1, "fld", cells["fld"])
    pm1 = {}
    for side, f in (("bat", fb1), ("fld", ff1)):
        grid, p_m = posterior_pm(ov1.loc[ov1["side"] == side, "x_margin"].values, f["sigma"]); pm1[side] = (grid, p_m, f["sigma"])
    rows.append(run_variant(ov1, hi, "g", pm1, "WP variant v1 (direct HGB fit with count)", seed=100)); print(rows[-1], flush=True)
    # coin-flip band excluded from the perception fit
    for band in (0.3, 0.5, 0.75):
        fbb = fit_side(o, "bat", cells["bat"], band=band); ffb = fit_side(o, "fld", cells["fld"], band=band)
        rows.append(run_variant(o, hi, "g", pm_from(fbb, ffb), f"perception fit excluding |x| < {band} in", seed=100)); print(rows[-1], flush=True)
    # hurdle model
    fbh = fit_side(o, "bat", cells["bat"], hurdle=True); ffh = fit_side(o, "fld", cells["fld"], hurdle=True)
    pmh = pm_from(fbh, ffh)
    rows.append(run_variant(o, hi, "g", pmh, "hurdle probit: optimum limited to considered opportunities", seed=100,
                            pi={"bat": fbh["pi"], "fld": ffh["pi"]}, notes=f"π_bat={fbh['pi']:.3f}, π_fld={ffh['pi']:.3f}")); print(rows[-1], flush=True)
    rows.append(run_variant(o, hi, "g", pmh, "hurdle probit σ, no attention limit", seed=100)); print(rows[-1], flush=True)
    # perception counterfactuals
    rows.append(run_variant(o, hi, "g", pm_from(fb, ff, {"bat": ff["sigma"], "fld": ff["sigma"]}), "counterfactual: batters perceive at catcher-level σ", seed=100)); print(rows[-1], flush=True)
    rows.append(run_variant(o, hi, "g", pm_from(fb, ff, {"bat": 1.0, "fld": 1.0}), "counterfactual: σ = 1.0 in both sides", seed=100)); print(rows[-1], flush=True)
    rows.append(run_variant(o, hi, "g", pm_from(fb, ff, {"bat": 0.5, "fld": 0.5}), "counterfactual: σ = 0.5 in both sides", seed=100)); print(rows[-1], flush=True)
    # σ net of player thresholds (two-way probit, cell + player fixed effects) — perception noise lower bound in the pre-registered family
    pf = {sd: fit["sides"][sd].get("player_fe", {}).get("sigma", np.nan) for sd in ("bat", "fld")}
    if all(np.isfinite(v) for v in pf.values()):
        rows.append(run_variant(o, hi, "g", pm_from(fb, ff, pf), "σ from cell + player fixed effects (within-player noise)", seed=100,
                                notes=f"σ_bat={pf['bat']:.2f}, σ_fld={pf['fld']:.2f}")); print(rows[-1], flush=True)
    # leakage-free split (METHODS §11): perception + DP on games through July 31, evaluated on August games
    o_tr = o[o["game_date"] <= "2026-07-31"]; o_te = o[o["game_date"] > "2026-07-31"]
    if len(o_te) > 1000:
        fbt = fit_side(o_tr, "bat", cells["bat"]); fft = fit_side(o_tr, "fld", cells["fld"])
        pmt = {}
        for side, f in (("bat", fbt), ("fld", fft)):
            grid, p_m = posterior_pm(o_tr.loc[o_tr["side"] == side, "x_margin"].values, f["sigma"]); pmt[side] = (grid, p_m, f["sigma"])
        # DP on the training streams
        rng = np.random.default_rng(100)
        def streams(oo, seed):
            r_ = np.random.default_rng(seed)
            sig = np.where(oo["side"] == "bat", pmt["bat"][2], pmt["fld"][2])
            m = oo["x_margin"].values + r_.normal(0, 1, len(oo)) * sig
            p = np.where(oo["side"] == "bat", np.interp(m, pmt["bat"][0], pmt["bat"][1]), np.interp(m, pmt["fld"][0], pmt["fld"][1]))
            op = pd.DataFrame({"game_id": oo["game_pk"].values, "team_home": oo["team_home"].values, "h": oo["h"].values,
                               "score_diff_home": oo["sd_home"].values, "g": oo["g"].values, "p": p, "outs": oo["outs"].values,
                               "x": oo["x_margin"].values, "truth": oo["truth"].values, "role": oo["side"].values,
                               "inning": oo["inning"].values, "balls": oo["balls"].values, "strikes": oo["strikes"].values,
                               "challenged": oo["challenged"].values, "overturned": oo["isOverturned"].values,
                               "abi": oo["atBatIndex"].values, "evi": oo["eventIndex"].values})
            return op.sort_values(["game_id", "abi", "evi"]).reset_index(drop=True)
        A_tr = F.make_arrays(streams(o_tr, 100), hi[hi["game_id"].isin(set(o_tr["game_pk"]))])
        V_tr, C_tr = F.solve_fast(A_tr, n_iter=40, tol=1e-7)
        A_te = F.make_arrays(streams(o_te, 101), hi[hi["game_id"].isin(set(o_te["game_pk"]))])
        os_te = A_te["op_sorted"]
        r_opt, _ = F.simulate_fast(os_te, C_tr, pmt, "optimal", D=60, seed=7)
        r_orc, _ = F.simulate_fast(os_te, C_tr, pmt, "oracle", D=1, seed=1)
        n_tg = os_te.groupby(["game_id", "team_home"]).ngroups
        obs = (os_te["g"] * os_te["challenged"] * os_te["truth"]).sum() / n_tg
        opt = r_opt["gain"].sum() / n_tg; orc = r_orc["gain"].mean()
        rows.append(dict(variant="leakage-free split: perception + DP fit through Jul 31, evaluated on Aug games", sigma_bat=pmt["bat"][2], sigma_fld=pmt["fld"][2],
                         V2_start_pp=V_tr[1, DMAX, 2] * 100, MTV2_inn1_pp=(V_tr[1, DMAX, 2] - V_tr[1, DMAX, 1]) * 100, MTV1_inn1_pp=(V_tr[1, DMAX, 1] - V_tr[1, DMAX, 0]) * 100,
                         MTV2_inn9_pp=(V_tr[17, DMAX, 2] - V_tr[17, DMAX, 1]) * 100, obs_pp=obs * 100, opt_pp=opt * 100, oracle_pp=orc * 100,
                         capture=obs / opt, perception_cost=opt / orc, gap_wins162=(opt - obs) * 162, opt_used=r_opt["used"].sum() / n_tg,
                         notes=f"train {o_tr['game_pk'].nunique()} games, test {o_te['game_pk'].nunique()} games"))
        print(rows[-1], flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DERIVED, "tier1_robustness_2026.csv"), index=False)
    md = "# Tier-1 robustness / multiverse — 2026\n\n" + df.round(3).to_string(index=False) + f"\n\nRuntime {time.time()-t0:.0f}s.\n"
    with open(os.path.join(DERIVED, "tier1_robustness_2026.md"), "w") as fh:
        fh.write(md)
    print(md)


if __name__ == "__main__":
    main()
