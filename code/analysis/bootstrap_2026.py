"""
bootstrap_2026.py — game-clustered bootstrap of the full Tier-1 pipeline (METHODS §11): resample games with replacement,
refit the perception model (σ_side, τ_cell), rebuild p(m), redraw ε, re-solve the DP (numba), re-simulate the
information-constrained optimum and recompute the observed realized value, capture ratio, V(2), MTV, and card cells.

Usage: python3 bootstrap_2026.py --B 200 --draws 30 --seed 1 --out data/derived/bootstrap_2026.csv
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code", "engine")); sys.path.insert(0, HERE)
import dp_fast as F  # noqa: E402
from dp import INN_BAND, CNT_CLASS  # noqa: E402
from perception_fit_2026 import add_cells, fit_probit, posterior_pm  # noqa: E402
from tier1_dp_2026 import half_inning_paths  # noqa: E402

DERIVED = os.path.join(ROOT, "data", "derived")
DMAX, HMAX = F.DMAX, F.HMAX


def fit_perception(o, cells_by_side):
    """Return pm dict side -> (grid, p, sigma) and tau arrays aligned to o (NaN where cell unseen)."""
    pm = {}; tau_all = np.full(len(o), np.nan); sig_obs = np.zeros(2)
    for si, side in enumerate(("bat", "fld")):
        m = (o["side"] == side).values & (o["tokens"].values >= 1)
        s = o[m]
        cells = cells_by_side[side]; cidx = {c: i for i, c in enumerate(cells)}
        ci = s["cell"].map(cidx)
        ok = ci.notna().values
        f = fit_probit(s["x_margin"].values[ok].astype(float), s["challenged"].values[ok].astype(float), ci.values[ok].astype(int), len(cells))
        grid, p_m = posterior_pm(o.loc[o["side"] == side, "x_margin"].values, f["sigma"])
        pm[side] = (grid, p_m, f["sigma"]); sig_obs[si] = f["sigma"]
        tau_map = dict(zip(cells, f["tau"]))
        idx = np.where((o["side"] == side).values)[0]
        tau_all[idx] = pd.Series(o["cell"].values[idx]).map(tau_map).values.astype(float)
    return pm, tau_all, sig_obs


def card_from(op_sorted, C, gq):
    """Break-even p* per (inn_band, lev, cnt) with two tokens and one token (medians); lev = pooled g terciles gq=(q1,q2),
    the same definition as dp.build_card (held at the full-sample cut points across replicates)."""
    o = op_sorted
    hc = o["h_c"].values; d = o["d_pitch"].values; outs = o["outs"].values
    m2 = C[hc, d, outs, 2] - C[hc, d, outs, 1]; m1 = C[hc, d, outs, 1] - C[hc, d, outs, 0]
    g = o["g"].values
    ok = g > 0
    p2 = np.where(ok, m2 / (g + m2), np.nan); p1 = np.where(ok, m1 / (g + m1), np.nan)
    lev = np.where(g < gq[0], "low", np.where(g < gq[1], "mid", "high"))
    df = pd.DataFrame({"inn_band": INN_BAND(o["inning"].values), "cnt": CNT_CLASS(o["balls"].values, o["strikes"].values),
                       "lev": lev, "p2": p2, "p1": p1})
    return df.groupby(["inn_band", "lev", "cnt"])[["p2", "p1"]].median()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=200)
    ap.add_argument("--draws", type=int, default=30)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", default=os.path.join(DERIVED, "bootstrap_2026.csv"))
    ap.add_argument("--full-only", action="store_true", help="only run the point estimate (replicate 0)")
    args = ap.parse_args()
    t_start = time.time()
    o = pd.read_parquet(os.path.join(DERIVED, "opps_2026.parquet"))
    o = o[o["pos_pitcher"] == 0].copy()
    fit = json.load(open(os.path.join(DERIVED, "perception_fit_2026.json")))
    lev_q = {k: tuple(v) for k, v in fit["lev_q"].items()}
    o, _ = add_cells(o, lev_q)
    cells_by_side = {s: fit["sides"][s]["cells"] for s in ("bat", "fld")}
    hi_all = half_inning_paths(os.path.join(ROOT, "data", "raw", "statcast", "statcast_2026.parquet"), set(o["game_pk"]))
    gq = tuple(o["g"].quantile([1 / 3, 2 / 3]).values)      # pooled leverage terciles for the card (fixed across replicates)
    games = np.array(sorted(o["game_pk"].unique()))
    o_by_game = {g: v for g, v in o.groupby("game_pk", sort=False)}
    hi_by_game = {g: v for g, v in hi_all.groupby("game_id", sort=False)}
    rng = np.random.default_rng(args.seed)
    rows = []
    B = 0 if args.full_only else args.B
    for b in range(0, B + 1):
        t0 = time.time()
        if b == 0:
            sample = games
        else:
            sample = rng.choice(games, size=len(games), replace=True)
        # assemble resampled frames with unique game ids (duplicates get suffixes)
        parts = []; hparts = []
        for j, gk in enumerate(sample):
            og = o_by_game[gk]; hg = hi_by_game[gk]
            gid = 10_000_000 + j if b > 0 else int(gk)      # unique per draw position (a game drawn twice becomes two pseudo-games)
            parts.append(og.assign(game_pk=gid)); hparts.append(hg.assign(game_id=gid))
        ob = pd.concat(parts, ignore_index=True); hb = pd.concat(hparts, ignore_index=True)
        pm, tau_all, sig_obs = fit_perception(ob, cells_by_side)
        # DP streams: one ε draw per opportunity
        sig = np.where(ob["side"] == "bat", pm["bat"][2], pm["fld"][2])
        m = ob["x_margin"].values + rng.normal(0, 1, len(ob)) * sig
        p = np.where(ob["side"] == "bat", np.interp(m, pm["bat"][0], pm["bat"][1]), np.interp(m, pm["fld"][0], pm["fld"][1]))
        op = pd.DataFrame({"game_id": ob["game_pk"].values, "team_home": ob["team_home"].values, "h": ob["h"].values,
                           "score_diff_home": ob["sd_home"].values, "g": ob["g"].values, "p": p, "outs": ob["outs"].values,
                           "x": ob["x_margin"].values, "truth": ob["truth"].values, "role": ob["side"].values,
                           "inning": ob["inning"].values, "balls": ob["balls"].values, "strikes": ob["strikes"].values,
                           "lev": ob["lev"].values, "challenged": ob["challenged"].values, "overturned": ob["isOverturned"].values,
                           "abi": ob["atBatIndex"].values, "evi": ob["eventIndex"].values})
        op = op.sort_values(["game_id", "abi", "evi"]).reset_index(drop=True)
        A = F.make_arrays(op, hb)
        V, C = F.solve_fast(A, n_iter=40, tol=1e-7)
        os_ = A["op_sorted"]
        r_opt, _ = F.simulate_fast(os_, C, pm, "optimal", D=args.draws, seed=1000 + b)
        r_orc, _ = F.simulate_fast(os_, C, pm, "oracle", D=1, seed=1)
        obs_gain = (os_["g"] * os_["challenged"] * os_["overturned"]).sum() / (os_.groupby(["game_id", "team_home"]).ngroups)
        opt_gain = r_opt["gain"].mean(); orc_gain = r_orc["gain"].mean()
        card = card_from(os_, C, gq)
        row = dict(b=b, n_games=len(sample), sigma_bat=pm["bat"][2], sigma_fld=pm["fld"][2],
                   V2_start=V[1, DMAX, 2], MTV2_inn1=V[1, DMAX, 2] - V[1, DMAX, 1], MTV1_inn1=V[1, DMAX, 1] - V[1, DMAX, 0],
                   MTV2_inn5=V[9, DMAX, 2] - V[9, DMAX, 1], MTV2_inn9=V[17, DMAX, 2] - V[17, DMAX, 1],
                   MTV1_inn9=V[17, DMAX, 1] - V[17, DMAX, 0],
                   obs_gain=obs_gain, opt_gain=opt_gain, oracle_gain=orc_gain, capture=obs_gain / opt_gain,
                   perception_cost=opt_gain / orc_gain, gap_wins162=(opt_gain - obs_gain) * 162,
                   opt_used=r_opt["used"].mean(), opt_succ_rate=r_opt["succ"].sum() / max(r_opt["used"].sum(), 1e-9))
        for (ib, lev, cnt), rr in card.iterrows():
            row[f"card2_{ib}_{lev}_{cnt}"] = rr["p2"]; row[f"card1_{ib}_{lev}_{cnt}"] = rr["p1"]
        rows.append(row)
        print(f"b={b:3d} capture={row['capture']:.3f} V2={row['V2_start']*100:.2f}pp opt={opt_gain*100:.3f} obs={obs_gain*100:.3f} "
              f"σ=({pm['bat'][2]:.2f},{pm['fld'][2]:.2f}) [{time.time()-t0:.0f}s, total {time.time()-t_start:.0f}s]", flush=True)
        pd.DataFrame(rows).to_csv(args.out, index=False)
    df = pd.DataFrame(rows)
    if len(df) > 1:
        print(summarize(df, os.path.join(DERIVED, "tier1_bootstrap_2026.md")))


def summarize(df, out_md=None):
    """Percentile intervals from a bootstrap CSV/DataFrame (row b=0 is the full-sample point estimate)."""
    boot = df[df["b"] > 0]
    lines = [f"# Game-clustered bootstrap — {len(boot)} replicates (full pipeline: perception refit, DP re-solve, policy re-simulation)", ""]
    lines.append("| quantity | point estimate | 95% percentile interval | bootstrap SE |")
    lines.append("|---|---|---|---|")
    names = {"capture": "capture ratio (observed ÷ optimum)", "V2_start": "value of two challenges at first pitch, tie (WP)", "MTV2_inn1": "MTV of 2nd token, inning 1 (WP)",
             "MTV1_inn1": "MTV of 1st token, inning 1 (WP)", "MTV2_inn9": "MTV of 2nd token, inning 9 (WP)", "MTV1_inn9": "MTV of 1st token, inning 9 (WP)",
             "obs_gain": "observed realized gain per team-game (WP)", "opt_gain": "information-constrained optimum (WP)", "oracle_gain": "oracle (WP)",
             "perception_cost": "optimum ÷ oracle", "gap_wins162": "gap in wins per 162", "sigma_bat": "σ batters (in)", "sigma_fld": "σ fielding (in)",
             "opt_used": "optimal challenges per team-game", "opt_succ_rate": "optimal success rate"}
    for c, nm in names.items():
        if c not in df:
            continue
        lo, hi_ = np.percentile(boot[c], [2.5, 97.5])
        pt = df.loc[0, c]
        lines.append(f"| {nm} | {pt:.4f} | [{lo:.4f}, {hi_:.4f}] | {boot[c].std():.4f} |")
    card_cols = [c for c in df.columns if c.startswith("card2_")]
    if card_cols:
        lines.append("")
        lines.append("Card cells (break-even p* with two tokens): point [95% interval]")
        lines.append("")
        for c in card_cols:
            lo, hi_ = np.percentile(boot[c], [2.5, 97.5])
            lines.append(f"- {c[6:]}: {df.loc[0, c]:.2f} [{lo:.2f}, {hi_:.2f}]")
    md = "\n".join(lines) + "\n"
    if out_md:
        with open(out_md, "w") as fh:
            fh.write(md)
    return md


if __name__ == "__main__":
    main()
