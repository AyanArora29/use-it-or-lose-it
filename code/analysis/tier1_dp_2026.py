"""
tier1_dp_2026.py — Tier-1 results on the real 2026 streams (METHODS §6–§7):
  * the renewable-token DP solved on 2026 arrival streams with the fitted perception model (p = posterior success given m = x + ε);
  * marginal token values (MTV) by inning × tokens × score state; the challenge card (break-even success probability);
  * policy evaluation on the ACTUAL 2026 opportunity streams with TRUE outcomes (x known): oracle, information-constrained
    optimum (perceives m with the fitted σ_side, applies the DP rule; averaged over ε draws), model-based observed policy
    (fitted P(challenge | x, cell)), realized observed use, and named heuristics; capture ratio;
  * the model-free dump test and the WP-weighted dump index.

Inputs : data/derived/opps_2026.parquet, data/raw/statcast/statcast_2026.parquet, data/derived/perception_fit_2026.json,
         data/derived/perception_pm_2026.npz
Outputs: data/derived/tier1_results_2026.json, tier1_mtv_2026.csv, tier1_card_2026.csv, tier1_policies_2026.csv,
         tier1_report_2026.md, tier1_dump_2026.csv, dp_V_2026.npy, dp_C_2026.npy
"""
from __future__ import annotations

import argparse
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
from dp import solve, mtv, build_card, card_lookup, add_breakeven, DMAX, HMAX, TOK, INN_BAND, CNT_CLASS  # noqa: E402
from perception_fit_2026 import add_cells  # noqa: E402

DERIVED = os.path.join(ROOT, "data", "derived")


# ---------------------------------------------------------------------------------------------
# streams
# ---------------------------------------------------------------------------------------------
def half_inning_paths(statcast_path, game_pks):
    sc = pd.read_parquet(statcast_path, columns=["game_pk", "game_type", "inning", "inning_topbot", "at_bat_number", "pitch_number",
                                                 "home_score", "away_score", "post_home_score", "post_away_score"])
    sc = sc[(sc["game_type"] == "R") & sc["game_pk"].isin(game_pks)].copy()
    sc["bat_home"] = (sc["inning_topbot"] == "Bot").astype(int)
    sc["h"] = (sc["inning"] - 1) * 2 + sc["bat_home"] + 1
    sc = sc.sort_values(["game_pk", "at_bat_number", "pitch_number"])
    hi = sc.groupby(["game_pk", "h"], sort=True).agg(sd_start=("home_score", "first"), away_start=("away_score", "first")).reset_index()
    hi["sd_start"] = hi["sd_start"] - hi["away_start"]; hi = hi.drop(columns=["away_start"])
    hi["sd_end"] = hi.groupby("game_pk")["sd_start"].shift(-1)
    last = sc.groupby("game_pk").tail(1)
    fin = (last["post_home_score"] - last["post_away_score"]).values
    hi = hi.merge(pd.DataFrame({"game_pk": last["game_pk"].values, "sd_final": fin}), on="game_pk", how="left")
    hi["sd_end"] = hi["sd_end"].fillna(hi["sd_final"]); hi = hi.drop(columns=["sd_final"])
    hi["season"] = 2026; hi = hi.rename(columns={"game_pk": "game_id"})
    return hi[["season", "game_id", "h", "sd_start", "sd_end"]]


def load_pm(npz_path):
    z = np.load(npz_path)
    return {s: (z[f"grid_{s}"], z[f"p_{s}"], float(z[f"sigma_{s}"])) for s in ("bat", "fld")}


def p_of_m(pm, side, m):
    grid, p, _ = pm[side]
    return np.interp(m, grid, p)


def build_streams_2026(o: pd.DataFrame, pm, seed=0):
    """Opportunity stream for the DP: one ε draw per opportunity -> perceived m -> calibrated p."""
    rng = np.random.default_rng(seed)
    op = pd.DataFrame({
        "season": 2026, "game_id": o["game_pk"].values, "team_home": o["team_home"].values, "h": o["h"].values,
        "score_diff_home": o["sd_home"].values, "g": o["g"].values, "role": o["side"].values, "orig": o["orig"].values,
        "balls": o["balls"].values, "strikes": o["strikes"].values, "inning": o["inning"].values, "outs": o["outs"].values,
        "bases_idx": o["bases_idx"].values, "x": o["x_margin"].values, "truth": o["truth"].values,
        "tokens_obs": o["tokens"].values, "challenged": o["challenged"].values, "overturned": o["isOverturned"].values,
        "cell": o["cell"].values, "abi": o["atBatIndex"].values, "evi": o["eventIndex"].values,
    })
    sig = np.where(op["role"] == "bat", pm["bat"][2], pm["fld"][2])
    m = op["x"].values + rng.normal(0, 1, len(op)) * sig
    p = np.where(op["role"] == "bat", p_of_m(pm, "bat", m), p_of_m(pm, "fld", m))
    op["p"] = p; op["m"] = m
    op = op.sort_values(["game_id", "abi", "evi"]).reset_index(drop=True)
    return op


# ---------------------------------------------------------------------------------------------
# policy evaluation on the actual streams with true outcomes, vectorised over ε draws
# ---------------------------------------------------------------------------------------------
def simulate(op: pd.DataFrame, C, pm, policy, D=200, seed=1, card_fn=None, fit=None):
    """Return per (game, team) arrays: realized WP gain (mean over draws), challenges used, successes, tokens left, and the
    per-opportunity mean challenge propensity. Outcome of a challenge is the TRUTH (x > 0). Perception: m = x + ε per draw."""
    rng = np.random.default_rng(seed)
    out = []; prop = np.zeros(len(op))
    sig_b, sig_f = pm["bat"][2], pm["fld"][2]
    for (gid, th), grp in op.groupby(["game_id", "team_home"], sort=False):
        idx = grp.index.values
        n = len(grp)
        tok = np.full(D, 2, dtype=np.int8)
        gain = np.zeros(D); used = np.zeros(D); succ = np.zeros(D)
        last_inn = 0
        x = grp["x"].values; g = grp["g"].values; truth = grp["truth"].values.astype(bool)
        role = grp["role"].values; inn = grp["inning"].values; h = np.minimum(grp["h"].values, HMAX)
        d = (np.clip(np.where(th == 1, grp["score_diff_home"].values, -grp["score_diff_home"].values), -DMAX, DMAX) + DMAX).astype(int)
        outs = grp["outs"].values; balls = grp["balls"].values; strikes = grp["strikes"].values
        cells = grp["cell"].values
        for i in range(n):
            if inn[i] >= 10 and inn[i] != last_inn:
                tok = np.where(tok == 0, 1, tok)
            last_inn = max(last_inn, inn[i])
            alive = tok > 0
            if not alive.any():
                continue
            sig = sig_b if role[i] == "bat" else sig_f
            if policy == "oracle":
                go = np.full(D, truth[i])
            elif policy == "observed_model":
                # fitted P(challenge | x, cell) — the model-based observed policy (Bernoulli)
                tau = fit["sides"][role[i]]["pooled"]["tau"].get(cells[i], np.nan)
                s_ = fit["sides"][role[i]]["pooled"]["sigma"]
                pc = norm.cdf((x[i] - tau) / s_) if np.isfinite(tau) else 0.0
                go = rng.random(D) < pc
            else:
                m = x[i] + rng.normal(0, sig, D)
                p = p_of_m(pm, role[i], m)
                if policy == "optimal":
                    mtv_t = C[h[i], d[i], outs[i], tok] - C[h[i], d[i], outs[i], np.maximum(tok - 1, 0)]
                    go = p * g[i] > (1 - p) * mtv_t
                elif policy == "naive50":
                    go = p >= 0.5
                elif policy == "late50":
                    go = (inn[i] >= 7) & (p >= 0.5)
                elif policy == "card":
                    thr = np.array([card_fn(inn[i], g[i], balls[i], strikes[i], t) for t in (1, 2)])
                    go = p > thr[np.maximum(tok - 1, 0)]
                elif policy == "never":
                    go = np.zeros(D, dtype=bool)
                else:
                    raise ValueError(policy)
            go = go & alive
            prop[idx[i]] = go.mean()
            used += go
            win = go & truth[i]
            gain += np.where(win, g[i], 0.0); succ += win
            tok = np.where(go & ~truth[i], tok - 1, tok)
        out.append((gid, th, gain.mean(), used.mean(), succ.mean(), tok.mean(), gain.std()))
    res = pd.DataFrame(out, columns=["game_id", "team_home", "gain", "used", "succ", "tokens_left", "gain_sd"])
    return res, prop


def realized_observed(op: pd.DataFrame, outcome="truth"):
    """Realized value of the actual challenges per team-game. outcome='truth' scores a challenge by our zone truth (the same
    outcome the simulated policies use, so numerator and denominator of the capture ratio share one zone); 'overturned' uses
    the ABS verdict as recorded (99.7% identical)."""
    r = op.groupby(["game_id", "team_home"]).size().rename("n").reset_index()
    ch = op[op["challenged"] == 1].copy()
    ch["succ_"] = ch[outcome].astype(float)
    ch["gain_"] = ch["g"] * ch["succ_"]
    agg = ch.groupby(["game_id", "team_home"]).agg(gain=("gain_", "sum"), used=("succ_", "size"), succ=("succ_", "sum")).reset_index()
    r = r.drop(columns=["n"]).merge(agg, on=["game_id", "team_home"], how="left").fillna({"gain": 0.0, "used": 0, "succ": 0})
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--reps", type=int, default=2, help="stream replications with independent ε draws for the DP solve")
    args = ap.parse_args()
    t0 = time.time()
    o = pd.read_parquet(os.path.join(DERIVED, "opps_2026.parquet"))
    o = o[o["pos_pitcher"] == 0].copy()
    fit = json.load(open(os.path.join(DERIVED, "perception_fit_2026.json")))
    o, lev_q = add_cells(o, {k: tuple(v) for k, v in fit["lev_q"].items()})
    pm = load_pm(os.path.join(DERIVED, "perception_pm_2026.npz"))
    hi = half_inning_paths(os.path.join(ROOT, "data", "raw", "statcast", "statcast_2026.parquet"), set(o["game_pk"]))
    rep = ["# Tier-1 results — 2026 (METHODS §6–§7)", ""]
    rep.append(f"- Streams: {o['game_pk'].nunique():,} games, {len(o):,} opportunities, {len(hi):,} half-innings; σ_bat = {pm['bat'][2]:.2f} in, σ_fld = {pm['fld'][2]:.2f} in.")

    # ---- DP solve on replicated streams -------------------------------------------------------------------------
    ops = []
    for r in range(args.reps):
        op_r = build_streams_2026(o, pm, seed=100 + r)
        op_r["game_id"] = op_r["game_id"] * 10 + r
        ops.append(op_r)
    op_all = pd.concat(ops, ignore_index=True)
    hi_all = pd.concat([hi.assign(game_id=hi["game_id"] * 10 + r) for r in range(args.reps)], ignore_index=True)
    print(f"solving DP on {len(op_all):,} opportunities ({args.reps} replications) ...", flush=True)
    V, C = solve(op_all, hi_all, verbose=True)
    np.save(os.path.join(DERIVED, "dp_V_2026.npy"), V); np.save(os.path.join(DERIVED, "dp_C_2026.npy"), C)
    M = mtv(V)
    rows = []
    for h in range(1, HMAX + 1):
        for d in range(-DMAX, DMAX + 1):
            rows.append(dict(h=h, inning=(h + 1) // 2, half="top" if h % 2 == 1 else "bottom", d_team=d,
                             V1=V[h, d + DMAX, 1], V2=V[h, d + DMAX, 2], MTV1=M[h, d + DMAX, 0], MTV2=M[h, d + DMAX, 1]))
    mt = pd.DataFrame(rows); mt.to_csv(os.path.join(DERIVED, "tier1_mtv_2026.csv"), index=False)
    rep.append("- Value of holding tokens at the start of the top of the inning, tie game (WP points, ×100): " + "; ".join(
        f"inn {(h+1)//2}: V(2)={V[h, DMAX, 2]*100:.2f}, MTV2={M[h, DMAX, 1]*100:.2f}, MTV1={M[h, DMAX, 0]*100:.2f}" for h in (1, 5, 9, 13, 15, 17)))
    rep.append("- MTV of the 2nd token at the start of inning 1 / 5 / 9 by score (team perspective, pp): " + "; ".join(
        f"{d:+d}: {M[1, d+DMAX, 1]*100:.2f}/{M[9, d+DMAX, 1]*100:.2f}/{M[17, d+DMAX, 1]*100:.2f}" for d in (-4, -2, -1, 0, 1, 2, 4)))
    # DP ex-ante state value at first pitch (tie): V(2). The headline value of the two challenges is the simulated optimum on
    # the actual streams (reported below); V(2) is a few % lower because the DP aggregates continuation values by state.
    v0 = V[1, DMAX, 2]
    rep.append(f"- DP ex-ante value of holding two challenges at first pitch (tie game): V(2) = {v0*100:.2f} WP points; MTV1 = {M[1, DMAX, 0]*100:.2f}, MTV2 = {M[1, DMAX, 1]*100:.2f}.")

    # ---- card ---------------------------------------------------------------------------------------------------
    op1 = ops[0].copy(); op1["game_id"] = op1["game_id"] // 10
    card, q = build_card(op1, C)
    card.to_csv(os.path.join(DERIVED, "tier1_card_2026.csv"), index=False)
    look = card_lookup(card, q)
    piv = card.pivot_table(index=["inn_band", "cnt"], columns="lev", values="pstar_t2").round(2)
    rep.append("- Challenge card, break-even success probability with two tokens (median by cell):\n\n" + piv.to_string() + "\n")
    piv1 = card.pivot_table(index=["inn_band", "cnt"], columns="lev", values="pstar_t1").round(2)
    rep.append("- ... with one token:\n\n" + piv1.to_string() + "\n")

    # ---- policies on the actual streams with true outcomes ------------------------------------------------------
    op = op1
    results = {}
    pol_rows = []
    obs = realized_observed(op, "truth")
    obs_v = realized_observed(op, "overturned")
    results["observed_realized"] = dict(gain=obs["gain"].mean(), used=obs["used"].mean(), succ=obs["succ"].mean(),
                                        succ_rate=obs["succ"].sum() / max(obs["used"].sum(), 1))
    results["observed_realized_abs_verdict"] = dict(gain=obs_v["gain"].mean(), used=obs_v["used"].mean(), succ=obs_v["succ"].mean(),
                                                    succ_rate=obs_v["succ"].sum() / max(obs_v["used"].sum(), 1))
    for pol in ["oracle", "optimal", "card", "naive50", "late50", "observed_model", "never"]:
        t1 = time.time()
        r, prop = simulate(op, C, pm, pol, D=args.draws if pol not in ("oracle", "never") else 1, seed=7, card_fn=look, fit=fit)
        results[pol] = dict(gain=r["gain"].mean(), used=r["used"].mean(), succ=r["succ"].mean(),
                            succ_rate=r["succ"].sum() / max(r["used"].sum(), 1e-9), tokens_left=r["tokens_left"].mean())
        r.to_parquet(os.path.join(DERIVED, f"tier1_sim_{pol}.parquet"), index=False)
        if pol == "optimal":
            op["prop_optimal"] = prop
        if pol == "observed_model":
            op["prop_obsmodel"] = prop
        print(f"  {pol}: {time.time()-t1:.0f}s", flush=True)
    for pol, v in results.items():
        pol_rows.append(dict(policy=pol, **v))
    pols = pd.DataFrame(pol_rows); pols.to_csv(os.path.join(DERIVED, "tier1_policies_2026.csv"), index=False)
    rep.append("- Policy values on the actual 2026 streams (per team-game; challenge outcomes = ABS truth; perception draws where applicable):\n\n" +
               pols.assign(gain_pp=lambda d: (d["gain"] * 100).round(3)).drop(columns=["gain"]).round(3).to_string(index=False) + "\n")
    cap = results["observed_realized"]["gain"] / results["optimal"]["gain"]
    cap_model = results["observed_model"]["gain"] / results["optimal"]["gain"]
    perc_cost = results["optimal"]["gain"] / results["oracle"]["gain"]
    rep.append(f"- **Value of the two challenges (information-constrained optimum on the actual 2026 streams): {results['optimal']['gain']*100:.2f} WP points per team-game "
               f"≈ {results['optimal']['gain']*162:.2f} wins per 162 games; teams realized {results['observed_realized']['gain']*100:.2f} pp ≈ {results['observed_realized']['gain']*162:.2f} wins "
               f"(scored by the ABS verdict as recorded: {results['observed_realized_abs_verdict']['gain']*100:.2f} pp).**")
    rep.append(f"- **Capture ratio (observed realized ÷ information-constrained optimum): {cap:.3f}**; model-based observed ÷ optimum: {cap_model:.3f}; "
               f"information-constrained optimum ÷ oracle: {perc_cost:.3f} (the perception cost). Gap = "
               f"{(results['optimal']['gain']-results['observed_realized']['gain'])*100:.3f} pp per team-game = {(results['optimal']['gain']-results['observed_realized']['gain'])*162:.2f} wins per 162 games. "
               f"The capture ratio is conditional on the fitted perception noise σ (all decision variance not explained by the state cells is treated as perceptual); "
               f"see tier1_robustness_2026 for σ from player fixed effects and other variants.")
    # game-clustered bootstrap for the capture ratio (policy simulations fixed)
    ropt = pd.read_parquet(os.path.join(DERIVED, "tier1_sim_optimal.parquet"))
    mm = obs.merge(ropt[["game_id", "team_home", "gain"]], on=["game_id", "team_home"], suffixes=("_obs", "_opt"))
    games = mm["game_id"].unique(); rng = np.random.default_rng(3)
    G = mm.groupby("game_id")[["gain_obs", "gain_opt"]].sum()
    boots = []
    for b in range(1000):
        smp = G.sample(len(G), replace=True, random_state=int(rng.integers(1e9)))
        boots.append(smp["gain_obs"].sum() / smp["gain_opt"].sum())
    lo, hi_ = np.percentile(boots, [2.5, 97.5])
    results["capture_ratio"] = dict(point=cap, ci95=[lo, hi_], n_games=len(G))
    rep.append(f"- Capture ratio game-clustered bootstrap 95% CI: [{lo:.3f}, {hi_:.3f}] ({len(G):,} games; DP and policy draws held fixed).")

    # ---- where does the shortfall come from? -----------------------------------------------------------------------
    op = add_breakeven(op, C)
    op["mtv_obs"] = np.where(op["tokens_obs"] >= 2, op["mtv_t2"], op["mtv_t1"])
    op["pstar_obs"] = np.where(op["tokens_obs"] >= 2, op["pstar_t2"], op["pstar_t1"])
    ch = op[op["challenged"] == 1].copy()
    ch["ex_post"] = np.where(ch["overturned"] == 1, ch["g"], -ch["mtv_obs"])
    rep.append(f"- Ex-post value of actual challenges (successful: +g; failed: −MTV at decision time): mean {ch['ex_post'].mean()*100:.3f} pp per challenge; "
               f"share with negative ex-post value {(ch['ex_post']<0).mean():.3f}; by side: " +
               "; ".join(f"{s}: {v*100:.3f} pp" for s, v in ch.groupby("role")["ex_post"].mean().items()))
    # missed clear misses: unchallenged with x > 2 in and tokens >= 1
    miss = op[(op["challenged"] == 0) & (op["x"] > 2) & (op["tokens_obs"] >= 1)]
    rep.append(f"- Missed clear misses (unchallenged, true margin > 2 in, tokens in hand): {len(miss):,} pitches worth {miss['g'].sum()*100/ (o['game_pk'].nunique()*2):.3f} pp per team-game in WP "
               f"({miss['g'].sum()*162/(o['game_pk'].nunique()*2):.2f} wins per 162 games at face value).")

    # ---- model-free dump test + WP-weighted dump index --------------------------------------------------------------
    late = op[(op["inning"] >= 9)]
    dump_rows = []
    for (side, tokens), s in op[op["challenged"] == 1].groupby(["role", "tokens_obs"]):
        pass
    ch["inn9"] = ch["inning"] >= 9
    ch["state"] = np.where(ch["score_diff_home"].abs() == 0, "tie", np.where(ch["score_diff_home"].abs() == 1, "one-run",
                           np.where(ch["score_diff_home"].abs() <= 3, "2-3", "4+")))
    ch["abs_x"] = ch["x"].abs()
    tab = ch.groupby(["inn9", "tokens_obs"]).agg(n=("overturned", "size"), overturn=("overturned", "mean"), mean_abs_x=("abs_x", "mean"),
                                                 mean_x=("x", "mean"), g=("g", "mean")).reset_index()
    tab.to_csv(os.path.join(DERIVED, "tier1_dump_2026.csv"), index=False)
    rep.append("- Model-free dump test — overturn rate and mean true margin of actual challenges by inning ≥ 9 × tokens in hand:\n\n" + tab.round(3).to_string(index=False) + "\n")
    tab2 = ch[ch["inn9"]].groupby(["state", "tokens_obs"]).agg(n=("overturned", "size"), overturn=("overturned", "mean"), mean_x=("x", "mean")).reset_index()
    rep.append("- 9th+ inning challenges by score state × tokens:\n\n" + tab2.round(3).to_string(index=False) + "\n")
    # WP-weighted dump index: sum over 9th+ challenges of max(0, (p* - p̂)(g + MTV)) with p̂ = fitted posterior at the OBSERVED margin?
    # p̂ is unobserved (depends on m); use the model's expected p given challenge at x: E[p(m) | m > τ_cell]. Approximate with p(x + E[ε | ε > τ − x]).
    def exp_p_given_challenge(row):
        side = row["role"]; sig = pm[side][2]; tau = fit["sides"][side]["pooled"]["tau"].get(row["cell"], np.nan)
        if not np.isfinite(tau):
            return np.nan
        a = (tau - row["x"]) / sig
        m_exp = row["x"] + sig * norm.pdf(a) / max(1 - norm.cdf(a), 1e-12)
        return p_of_m(pm, side, m_exp)
    ch["p_hat"] = ch.apply(exp_p_given_challenge, axis=1)
    ch["dump"] = np.where(ch["g"] > 0, np.maximum(0, (ch["pstar_obs"] - ch["p_hat"]) * (ch["g"] + ch["mtv_obs"])), 0.0)   # g = 0: no break-even defined
    di = ch[ch["inn9"]].groupby("state")["dump"].agg(["size", "sum", "mean"])
    n_tg = o["game_pk"].nunique() * 2
    rep.append("- WP-weighted dump index (9th+ challenges; Σ max(0,(p*−p̂)(g+MTV)) per team-game, pp): " + "; ".join(
        f"{i}: {r['sum']*100/n_tg:.4f} (n={int(r['size'])}, mean per challenge {r['mean']*100:.3f} pp)" for i, r in di.iterrows()))
    late_thr = ch[ch["inn9"]]; early_thr = ch[~ch["inn9"]]
    rep.append(f"- Mean (p̂ − p*) of actual challenges: innings 1–8: {(early_thr['p_hat']-early_thr['pstar_obs']).mean():.3f}; 9th+: {(late_thr['p_hat']-late_thr['pstar_obs']).mean():.3f} "
               f"(negative = challenges made below the break-even probability).")

    results["dp"] = dict(V2_start_tie=v0, wins_per_162=v0 * 162)
    with open(os.path.join(DERIVED, "tier1_results_2026.json"), "w") as fh:
        json.dump(results, fh, indent=1, default=float)
    op.to_parquet(os.path.join(DERIVED, "tier1_opps_with_breakeven.parquet"), index=False)
    rep.append(f"- Runtime {time.time()-t0:.0f}s.")
    with open(os.path.join(DERIVED, "tier1_report_2026.md"), "w") as fh:
        fh.write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
