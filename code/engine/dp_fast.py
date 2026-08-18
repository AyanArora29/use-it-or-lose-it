"""
dp_fast.py — numba implementation of the renewable-token DP (state-based policy iteration) and of the policy simulator on
actual streams. Independent re-implementation of dp.solve / tier1_dp_2026.simulate for the dual-implementation check
(METHODS §12) and for the game-clustered bootstrap (§11), where speed matters.

Streams are passed as flat arrays:
  instances (one per team × half-inning): h (capped), d_start, d_end (team-perspective buckets, +DMAX), is_last, op_lo, op_hi
  opportunities (sorted by game, team, half-inning, time): g, p, outs, d_pitch (+DMAX), h (capped)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from numba import njit

DMAX = 6
HMAX = 24
TOK = 3
ND = 2 * DMAX + 1


def team_bucket(sd_home, team_home):
    d = np.where(team_home == 1, sd_home, -sd_home)
    return np.clip(d, -DMAX, DMAX).astype(np.int64) + DMAX


def make_arrays(op: pd.DataFrame, hi: pd.DataFrame):
    """op: columns game_id, team_home, h, score_diff_home, g, p, outs (+ anything else); hi: game_id, h, sd_start, sd_end.
    Returns dict of arrays with opportunities re-sorted; keeps op['_pos'] mapping to the sorted order."""
    op = op.copy()
    op["_orig_index"] = np.arange(len(op))
    op = op.sort_values(["game_id", "team_home", "h", "_orig_index"], kind="mergesort").reset_index(drop=True)
    op["h_c"] = np.minimum(op["h"].values, HMAX)
    op["d_pitch"] = team_bucket(op["score_diff_home"].values, op["team_home"].values)
    # instances
    rows = []
    for th in (0, 1):
        t = hi[["game_id", "h", "sd_start", "sd_end"]].copy(); t["team_home"] = th
        t["d_start"] = team_bucket(t["sd_start"].values, th); t["d_end"] = team_bucket(t["sd_end"].values, th)
        rows.append(t)
    inst = pd.concat(rows, ignore_index=True)
    inst["is_last"] = (inst["h"] == inst.groupby("game_id")["h"].transform("max")).astype(np.int64)
    inst["h_c"] = np.minimum(inst["h"].values, HMAX)
    inst = inst.sort_values(["game_id", "team_home", "h"], kind="mergesort").reset_index(drop=True)
    # opp ranges per instance via merge of keys
    key_op = pd.MultiIndex.from_arrays([op["game_id"], op["team_home"], op["h_c"]])
    key_in = pd.MultiIndex.from_arrays([inst["game_id"], inst["team_home"], inst["h_c"]])
    # group boundaries in op
    grp = op.groupby(["game_id", "team_home", "h_c"], sort=False).indices
    lo = np.full(len(inst), 0, dtype=np.int64); hi_ = np.full(len(inst), 0, dtype=np.int64)
    for i, k in enumerate(key_in):
        idx = grp.get(k)
        if idx is not None:
            lo[i] = idx[0]; hi_[i] = idx[-1] + 1
    inst["op_lo"] = lo; inst["op_hi"] = hi_
    # instances not covering some opps (h > HMAX collapse etc.) — opps whose (game, team, h_c) has no instance are ignored
    A = dict(
        inst_h=inst["h_c"].values.astype(np.int64), inst_dstart=inst["d_start"].values.astype(np.int64),
        inst_dend=inst["d_end"].values.astype(np.int64), inst_last=inst["is_last"].values.astype(np.int64),
        inst_lo=lo, inst_hi=hi_, inst_game=inst["game_id"].values, inst_team=inst["team_home"].values.astype(np.int64),
        g=op["g"].values.astype(np.float64), p=op["p"].values.astype(np.float64), outs=op["outs"].values.astype(np.int64),
        d_pitch=op["d_pitch"].values.astype(np.int64), h=op["h_c"].values.astype(np.int64), op_sorted=op,
    )
    return A


@njit(cache=True)
def _solve_kernel(inst_h, inst_dstart, inst_dend, inst_last, inst_lo, inst_hi, g, p, outs, d_pitch, C, n_iter, tol, retain, grant):
    """C has shape (HMAX+2, ND, 3, ntok); ntok-1 = tokens at game start. retain=1: a successful challenge keeps the token
    (2026 rule); retain=0: every challenge consumes a token. grant=1: a team with 0 tokens receives 1 at the start of each
    extra inning (2026 rule)."""
    n_inst = inst_h.shape[0]
    ntok = C.shape[3]
    V = np.zeros((HMAX + 2, ND, ntok))
    for it in range(n_iter):
        V_new = np.zeros((HMAX + 2, ND, ntok))
        C_sum = np.zeros((HMAX + 2, ND, 3, ntok)); C_n = np.zeros((HMAX + 2, ND, 3))
        acc = np.zeros((HMAX + 2, ND, ntok)); cnt = np.zeros((HMAX + 2, ND))
        for h in range(HMAX, 0, -1):
            for k in range(n_inst):
                if inst_h[k] != h:
                    continue
                W = np.zeros(ntok)
                if inst_last[k] == 0:
                    for t in range(ntok):
                        W[t] = V_new[h + 1, inst_dend[k], t]
                    if grant == 1 and (h + 1) >= 19 and ((h + 1) % 2 == 1):
                        W[0] = W[1]
                for i in range(inst_hi[k] - 1, inst_lo[k] - 1, -1):
                    gi = g[i]; pi = p[i]; oi = outs[i]; di = d_pitch[i]
                    for t in range(ntok):
                        C_sum[h, di, oi, t] += W[t]
                    C_n[h, di, oi] += 1.0
                    Wn = W.copy()
                    for t in range(1, ntok):
                        keep = t if retain == 1 else t - 1
                        # state-based rule: challenge iff p*(g + C[keep]) + (1-p)*C[t-1] > C[t]  (with retention: p*g > (1-p)*MTV)
                        if pi * (gi + C[h, di, oi, keep]) + (1.0 - pi) * C[h, di, oi, t - 1] > C[h, di, oi, t]:
                            Wn[t] = pi * (gi + W[keep]) + (1.0 - pi) * W[t - 1]
                    W = Wn
                for t in range(ntok):
                    acc[h, inst_dstart[k], t] += W[t]
                cnt[h, inst_dstart[k]] += 1.0
            for d in range(ND):
                if cnt[h, d] > 0:
                    for t in range(ntok):
                        V_new[h, d, t] = acc[h, d, t] / cnt[h, d]
                else:
                    for t in range(ntok):
                        V_new[h, d, t] = V_new[h + 1, d, t]
        C_new = np.zeros((HMAX + 2, ND, 3, ntok))
        delta = 0.0
        for h in range(1, HMAX + 1):
            for d in range(ND):
                for o in range(3):
                    for t in range(ntok):
                        if C_n[h, d, o] > 0:
                            C_new[h, d, o, t] = C_sum[h, d, o, t] / C_n[h, d, o]
                        else:
                            C_new[h, d, o, t] = V_new[h + 1, d, t]
                        dd = abs(C_new[h, d, o, t] - C[h, d, o, t])
                        if dd > delta:
                            delta = dd
        C = C_new
        V = V_new
        if delta < tol and it > 0:
            break
    return V, C


def solve_fast(A, C0=None, n_iter=30, tol=1e-7, tokens=2, retain=True, grant=True):
    """State-based policy iteration. tokens = challenges per team at game start (2 in 2026); retain = keep on success;
    grant = extra-innings grant. Returns V[h, d, t] and C[h, d, outs, t] for t = 0..tokens."""
    ntok = tokens + 1
    C = np.zeros((HMAX + 2, ND, 3, ntok)) if C0 is None else np.ascontiguousarray(C0, dtype=np.float64)
    V, C = _solve_kernel(A["inst_h"], A["inst_dstart"], A["inst_dend"], A["inst_last"], A["inst_lo"], A["inst_hi"],
                         A["g"], A["p"], A["outs"], A["d_pitch"], C, n_iter, tol, 1 if retain else 0, 1 if grant else 0)
    return V, C


@njit(cache=True)
def _sim_kernel(tg_lo, tg_hi, x, g, truth, side, inn, h, d_pitch, outs, sig_side, grid_b, pm_b, grid_f, pm_f, C,
                policy, D, seed, tau_opp, sig_obs, thr1, thr2, prop_out, tok0, retain, grant):
    """policy: 0 oracle, 1 optimal, 2 card, 3 naive50, 4 late50, 5 observed_model, 6 never. Returns per team-game
    (gain_mean, used_mean, succ_mean, tokens_left_mean, gain_sd)."""
    np.random.seed(seed)
    n_tg = tg_lo.shape[0]
    out = np.zeros((n_tg, 5))
    for k in range(n_tg):
        tok = np.full(D, tok0, dtype=np.int64)
        gain = np.zeros(D); used = np.zeros(D); succ = np.zeros(D)
        last_inn = 0
        for i in range(tg_lo[k], tg_hi[k]):
            if grant == 1 and inn[i] >= 10 and inn[i] != last_inn:
                for dd in range(D):
                    if tok[dd] == 0:
                        tok[dd] = 1
            if inn[i] > last_inn:
                last_inn = inn[i]
            any_alive = False
            for dd in range(D):
                if tok[dd] > 0:
                    any_alive = True
                    break
            if not any_alive:
                continue
            sg = sig_side[side[i]]
            n_go = 0.0
            for dd in range(D):
                if tok[dd] == 0:
                    continue
                go = False
                if policy == 0:
                    go = truth[i] == 1
                elif policy == 6:
                    go = False
                elif policy == 5:
                    if not np.isnan(tau_opp[i]):
                        z = (x[i] - tau_opp[i]) / sig_obs[side[i]]
                        # Φ(z) via erf
                        pc = 0.5 * (1.0 + _erf(z / np.sqrt(2.0)))
                        go = np.random.random() < pc
                else:
                    m = x[i] + sg * np.random.standard_normal()
                    if side[i] == 0:
                        pp = np.interp(m, grid_b, pm_b)
                    else:
                        pp = np.interp(m, grid_f, pm_f)
                    if policy == 1:
                        keep = tok[dd] if retain == 1 else tok[dd] - 1
                        go = pp * (g[i] + C[h[i], d_pitch[i], outs[i], keep]) + (1.0 - pp) * C[h[i], d_pitch[i], outs[i], tok[dd] - 1] > C[h[i], d_pitch[i], outs[i], tok[dd]]
                    elif policy == 2:
                        thr = thr2[i] if tok[dd] >= 2 else thr1[i]
                        go = pp > thr
                    elif policy == 3:
                        go = pp >= 0.5
                    elif policy == 4:
                        go = (inn[i] >= 7) and (pp >= 0.5)
                if go:
                    n_go += 1.0
                    used[dd] += 1.0
                    if truth[i] == 1:
                        gain[dd] += g[i]; succ[dd] += 1.0
                        if retain == 0:
                            tok[dd] -= 1
                    else:
                        tok[dd] -= 1
            prop_out[i] = n_go / D
        gm = gain.mean()
        out[k, 0] = gm; out[k, 1] = used.mean(); out[k, 2] = succ.mean(); out[k, 3] = tok.mean()
        out[k, 4] = np.sqrt(((gain - gm) ** 2).mean())
    return out


@njit(cache=True)
def _erf(x):
    # Abramowitz-Stegun 7.1.26 (max error 1.5e-7)
    s = 1.0 if x >= 0 else -1.0
    ax = abs(x)
    t = 1.0 / (1.0 + 0.3275911 * ax)
    y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * np.exp(-ax * ax)
    return s * y


POLICY_ID = {"oracle": 0, "optimal": 1, "card": 2, "naive50": 3, "late50": 4, "observed_model": 5, "never": 6}


def simulate_fast(op_sorted: pd.DataFrame, C, pm, policy, D=200, seed=1, tau_opp=None, sig_obs=None, thr1=None, thr2=None,
                  tokens=2, retain=True, grant=True):
    """op_sorted: the sorted opportunity frame from make_arrays (must have game_id, team_home, x, g, truth, role, inning, h_c,
    d_pitch, outs). pm: dict side -> (grid, p, sigma). Returns (DataFrame per team-game, prop per opp in sorted order)."""
    o = op_sorted
    tg = o.groupby(["game_id", "team_home"], sort=False).indices
    keys = list(tg.keys())
    lo = np.array([tg[k][0] for k in keys], dtype=np.int64); hi_ = np.array([tg[k][-1] + 1 for k in keys], dtype=np.int64)
    side = (o["role"].values == "fld").astype(np.int64)
    sig_side = np.array([pm["bat"][2], pm["fld"][2]], dtype=np.float64)
    gb, pb, _ = pm["bat"]; gf, pf, _ = pm["fld"]
    n = len(o)
    tau_opp = np.full(n, np.nan) if tau_opp is None else np.asarray(tau_opp, dtype=np.float64)
    sig_obs = sig_side if sig_obs is None else np.asarray(sig_obs, dtype=np.float64)
    thr1 = np.full(n, 0.5) if thr1 is None else np.asarray(thr1, dtype=np.float64)
    thr2 = np.full(n, 0.5) if thr2 is None else np.asarray(thr2, dtype=np.float64)
    prop = np.zeros(n)
    out = _sim_kernel(lo, hi_, o["x"].values.astype(np.float64), o["g"].values.astype(np.float64), o["truth"].values.astype(np.int64),
                      side, o["inning"].values.astype(np.int64), o["h_c"].values.astype(np.int64), o["d_pitch"].values.astype(np.int64),
                      o["outs"].values.astype(np.int64), sig_side, gb.astype(np.float64), pb.astype(np.float64), gf.astype(np.float64), pf.astype(np.float64),
                      np.ascontiguousarray(C, dtype=np.float64), POLICY_ID[policy], int(D), int(seed), tau_opp, sig_obs, thr1, thr2, prop,
                      int(tokens), 1 if retain else 0, 1 if grant else 0)
    res = pd.DataFrame(out, columns=["gain", "used", "succ", "tokens_left", "gain_sd"])
    res["game_id"] = [k[0] for k in keys]; res["team_home"] = [k[1] for k in keys]
    return res, prop
