"""
dp.py — the renewable-token dynamic program for ABS challenges.

Value function V(h, d, t): expected future WP gain (relative to holding no tokens) at the START of half-inning h,
with score-difference bucket d (team perspective, clipped ±DMAX) and t tokens in hand.
Rules encoded: 2 tokens to start; a successful challenge is retained; a failed one is lost; from the 10th inning on,
a team with 0 tokens is granted 1 at the start of each inning (2026 MLB rule).

Opportunities: each called pitch (B or C) is an opportunity for exactly one side (called strike -> batting team;
called ball -> fielding team) with gain g = ΔWP if overturned (wp_model.flip_gain) and success probability p as
perceived by the challenger. Given (g, p) at an opportunity, with V known for the continuation:
    challenge  iff  p * g  >=  (1 - p) * MTV,   MTV = V(t) - V(t-1)  (marginal token value at that point).

Backward induction uses REAL half-inning opportunity streams (states from Retrosheet 2015–2025; p from a perception
model — synthetic until Statcast miss distances are attached) and the real score path for continuation.

Usage (engine test):  python3 dp.py --seasons 2023 2024 --eval 2025
"""
from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from wp_model import WPCube, BASE_IDX  # noqa: E402

DATA = os.path.join(HERE, "data")
DMAX = 6          # score-diff bucket clip (team perspective)
HMAX = 24         # half-innings modeled explicitly (through the 12th); beyond -> treated as HMAX
TOK = 3           # tokens 0,1,2


# ---------------------------------------------------------------------------------------------
# 1. Opportunity streams
# ---------------------------------------------------------------------------------------------
def build_streams(seasons, cube: WPCube, p_model, seed=0):
    """Return a DataFrame of opportunities with columns:
       season, game_id, team_home(0/1 = the challenging team is home), h, d_start(bucket, team persp.), g, p, role
       plus a half-inning table (season, game_id, team_home, h) -> d_start, d_end.
    p_model(df) -> array of perceived success probabilities for the challenger (may be synthetic)."""
    parts = []
    for y in seasons:
        df = pd.read_parquet(os.path.join(DATA, f"pitches_{y}.parquet"))
        parts.append(df)
    df = pd.concat(parts, ignore_index=True)
    df["h"] = (df["inning"] - 1) * 2 + (df["bat_home"] == 1).astype(int) + 1        # top1=1, bot1=2, ...
    df["bases_idx"] = df["bases"].map(BASE_IDX).astype(int)

    # half-inning score path (home perspective) : start diff and end diff of each half-inning
    hi = df.groupby(["season", "game_id", "h"], sort=False).agg(sd_start=("score_diff_home", "first"),
                                                                 pa_last=("pa_idx", "last")).reset_index()
    # end-of-half-inning score = start of next half-inning; for the last half-inning use final score
    hi = hi.sort_values(["season", "game_id", "h"])
    hi["sd_end"] = hi.groupby(["season", "game_id"])["sd_start"].shift(-1)
    # final score for the last half-inning of each game: derive from last PA start score + runs of that PA
    last = df.groupby(["season", "game_id"]).tail(1)[["season", "game_id", "score_diff_home", "bat_home", "pa_runs"]]
    last["sd_final"] = last["score_diff_home"] + np.where(last["bat_home"] == 1, last["pa_runs"], -last["pa_runs"])
    hi = hi.merge(last[["season", "game_id", "sd_final"]], on=["season", "game_id"], how="left")
    hi["sd_end"] = hi["sd_end"].fillna(hi["sd_final"])
    hi = hi.drop(columns=["sd_final", "pa_last"])

    # opportunities: called pitches only
    op = df[df["called"] == 1].copy()
    op["orig"] = np.where(op["pitch_code"] == "C", "S", "B")   # called strike -> 'S', called ball -> 'B'
    # challenging team: called strike -> batting team; called ball -> fielding team
    op["team_home"] = np.where(op["orig"] == "S", op["bat_home"], 1 - op["bat_home"]).astype(int)
    g = np.zeros(len(op))
    for call in ("S", "B"):
        m = (op["orig"] == call).values
        g[m] = cube.flip_gain(op["inning"].values[m], op["bat_home"].values[m], op["outs"].values[m],
                              op["bases_idx"].values[m], op["score_diff_home"].values[m], op["balls"].values[m],
                              op["strikes"].values[m], call)
    op["g"] = np.maximum(g, 0.0)
    op["role"] = np.where(op["orig"] == "S", "batter", "catcher")   # fielding-side challenges attributed to catcher by default
    op["p"] = p_model(op, seed)
    op = op[["season", "game_id", "team_home", "h", "score_diff_home", "g", "p", "role", "orig", "balls", "strikes",
             "inning", "outs", "bases_idx"]].reset_index(drop=True)
    return op, hi


def synthetic_p(op: pd.DataFrame, seed=0):
    """Placeholder perception model until Statcast miss distances are attached.
    ~90% of called pitches are clearly right (p≈0.03), ~7% borderline (p ~ U(0.25,0.75)), ~3% clear misses (p≈0.9)."""
    rng = np.random.default_rng(seed)
    n = len(op)
    u = rng.random(n)
    p = np.where(u < 0.90, rng.beta(1, 25, n), np.where(u < 0.97, rng.uniform(0.25, 0.75, n), rng.beta(18, 2, n)))
    return p


# ---------------------------------------------------------------------------------------------
# 2. Backward induction
# ---------------------------------------------------------------------------------------------
def team_bucket(sd_home, team_home):
    d = np.where(team_home == 1, sd_home, -sd_home)
    return np.clip(d, -DMAX, DMAX).astype(int)


def _index_streams(op: pd.DataFrame, hi: pd.DataFrame):
    hi_rows = []
    for th in (0, 1):
        t = hi.copy(); t["team_home"] = th
        t["d_start"] = team_bucket(t["sd_start"].values, th); t["d_end"] = team_bucket(t["sd_end"].values, th)
        hi_rows.append(t)
    H = pd.concat(hi_rows, ignore_index=True)
    H["h_c"] = np.minimum(H["h"], HMAX)
    H["is_last"] = (H["h"] == H.groupby(["season", "game_id"])["h"].transform("max")).astype(int)   # game over after this half-inning
    op = op.copy(); op["h_c"] = np.minimum(op["h"], HMAX)
    op["d_pitch"] = team_bucket(op["score_diff_home"].values, op["team_home"].values)
    op_groups = {k: (v["g"].values, v["p"].values, v["outs"].values.astype(int), v["d_pitch"].values.astype(int))
                 for k, v in op.groupby(["season", "game_id", "team_home", "h_c"], sort=False)}
    return H, op_groups


def solve_foresight(op: pd.DataFrame, hi: pd.DataFrame, verbose=True):
    """Sample-path backward induction (v0.1): the backward max over each instance's OWN remaining stream — an in-sample
    optimum with perfect foresight of the upcoming opportunities within the half-inning. Upward-biased; kept for reference."""
    V = np.zeros((HMAX + 2, 2 * DMAX + 1, TOK))
    C_sum = np.zeros((HMAX + 2, 2 * DMAX + 1, 3, TOK)); C_n = np.zeros((HMAX + 2, 2 * DMAX + 1, 3))
    H, op_groups = _index_streams(op, hi)
    for h in range(HMAX, 0, -1):
        Hh = H[H["h_c"] == h]
        for dstart in range(-DMAX, DMAX + 1):
            sub = Hh[Hh["d_start"] == dstart]
            if len(sub) == 0:
                V[h, dstart + DMAX, :] = V[h + 1, dstart + DMAX, :]
                continue
            acc = np.zeros(TOK); n = 0
            for r in sub.itertuples(index=False):
                key = (r.season, r.game_id, r.team_home, h)
                cont = np.zeros(TOK) if r.is_last else V[h + 1, r.d_end + DMAX, :].copy()
                nxt = h + 1
                if not r.is_last and nxt >= 19 and nxt % 2 == 1:
                    cont[0] = cont[1]
                W = cont
                if key in op_groups:
                    gs, ps, os_, ds = op_groups[key]
                    for i in range(len(gs) - 1, -1, -1):
                        g, p = gs[i], ps[i]
                        C_sum[h, ds[i] + DMAX, os_[i], :] += W; C_n[h, ds[i] + DMAX, os_[i]] += 1
                        Wn = W.copy()
                        for t in range(1, TOK):
                            chal = p * (g + W[t]) + (1 - p) * W[t - 1]
                            Wn[t] = max(W[t], chal)
                        W = Wn
                acc += W; n += 1
            V[h, dstart + DMAX, :] = acc / n
    C = np.zeros_like(C_sum)
    for h in range(1, HMAX + 1):
        for d in range(2 * DMAX + 1):
            for o in range(3):
                C[h, d, o, :] = C_sum[h, d, o, :] / C_n[h, d, o] if C_n[h, d, o] > 0 else V[h + 1, d, :]
    return V, C


def solve(op: pd.DataFrame, hi: pd.DataFrame, verbose=True, n_iter=12, tol=1e-6, C0=None):
    """State-based value function by policy iteration on the empirical streams (v0.2, primary).

    The decision at an opportunity may use only the STATE (half-inning h, score bucket d at the pitch, outs, tokens t) and
    the opportunity's own (g, p): challenge iff p·g > (1−p)·[C(h,d,outs,t) − C(h,d,outs,t−1)], where C is the expected
    continuation value after an opportunity in that state. Each iteration evaluates that policy on every instance
    (expected value over success ~ Bernoulli(p), continuation = the instance's realized path under the policy — no max, so
    no foresight), then re-averages the continuation values into C and the half-inning start values into V. Iterate to a
    fixed point. Returns V[h, d+DMAX, t] (h = 1..HMAX+1, index HMAX+1 = terminal zeros) and C[h, d+DMAX, outs, t]."""
    H, op_groups = _index_streams(op, hi)
    V = np.zeros((HMAX + 2, 2 * DMAX + 1, TOK))
    C = np.zeros((HMAX + 2, 2 * DMAX + 1, 3, TOK)) if C0 is None else C0.copy()
    if C0 is None:
        # warm start: the sample-path solution (over-optimistic but a good starting policy)
        _, C = solve_foresight(op, hi, verbose=False)
    t0 = time.time()
    for it in range(n_iter):
        V_new = np.zeros_like(V)
        C_sum = np.zeros_like(C); C_n = np.zeros((HMAX + 2, 2 * DMAX + 1, 3))
        for h in range(HMAX, 0, -1):
            Hh = H[H["h_c"] == h]
            for dstart in range(-DMAX, DMAX + 1):
                sub = Hh[Hh["d_start"] == dstart]
                if len(sub) == 0:
                    V_new[h, dstart + DMAX, :] = V_new[h + 1, dstart + DMAX, :]
                    continue
                acc = np.zeros(TOK); n = 0
                for r in sub.itertuples(index=False):
                    key = (r.season, r.game_id, r.team_home, h)
                    cont = np.zeros(TOK) if r.is_last else V_new[h + 1, r.d_end + DMAX, :].copy()   # game over -> 0
                    nxt = h + 1
                    if not r.is_last and nxt >= 19 and nxt % 2 == 1:      # start of an extra inning: a team with 0 tokens receives 1
                        cont[0] = cont[1]
                    W = cont
                    if key in op_groups:
                        gs, ps, os_, ds = op_groups[key]
                        for i in range(len(gs) - 1, -1, -1):
                            g, p = gs[i], ps[i]
                            Cc = C[h, ds[i] + DMAX, os_[i], :]
                            C_sum[h, ds[i] + DMAX, os_[i], :] += W; C_n[h, ds[i] + DMAX, os_[i]] += 1
                            Wn = W.copy()
                            for t in range(1, TOK):
                                if p * g > (1 - p) * (Cc[t] - Cc[t - 1]):
                                    Wn[t] = p * (g + W[t]) + (1 - p) * W[t - 1]
                            W = Wn
                    acc += W; n += 1
                V_new[h, dstart + DMAX, :] = acc / n
        C_new = np.zeros_like(C)
        for h in range(1, HMAX + 1):
            for d in range(2 * DMAX + 1):
                for o in range(3):
                    C_new[h, d, o, :] = C_sum[h, d, o, :] / C_n[h, d, o] if C_n[h, d, o] > 0 else V_new[h + 1, d, :]
        delta = np.max(np.abs(C_new - C)); dV = np.max(np.abs(V_new - V))
        V, C = V_new, C_new
        if verbose:
            print(f"  policy iteration {it+1}: V(2, start, tie) = {V[1, DMAX, 2]*100:.4f} pp, max|ΔC| = {delta:.2e}, max|ΔV| = {dV:.2e} ({time.time()-t0:.0f}s)", flush=True)
        if delta < tol and it > 0:
            break
    return V, C


def mtv(V):
    """Marginal token values MTV[h, d, t] = V[t] - V[t-1] for t=1,2."""
    return V[:, :, 1:] - V[:, :, :-1]


# ---------------------------------------------------------------------------------------------
# 3. Policy evaluation on real streams
# ---------------------------------------------------------------------------------------------
def evaluate(op: pd.DataFrame, hi: pd.DataFrame, V, C, policy: str, thresh=0.5):
    """Simulate each (game, team) through its opportunity stream under a policy; return per-game realized WP gain and
    tokens used/left. Success is Bernoulli(p) (p is the challenger's calibrated success probability)."""
    rng = np.random.default_rng(123)
    out = []
    op = op.sort_values(["season", "game_id", "team_home", "h"]).reset_index(drop=True)
    for (season, gid, th), grp in op.groupby(["season", "game_id", "team_home"], sort=False):
        t = 2; gain = 0.0; used = 0; succ = 0; last_inn = 0
        for r in grp.itertuples(index=False):
            inn = (r.h + 1) // 2
            if inn >= 10 and inn != last_inn and t == 0:
                t = 1
            last_inn = max(last_inn, inn)
            if t == 0:
                continue
            d = int(np.clip(r.score_diff_home if th == 1 else -r.score_diff_home, -DMAX, DMAX))
            hc = min(r.h, HMAX)
            if policy == "optimal":
                m = C[hc, d + DMAX, r.outs, t] - C[hc, d + DMAX, r.outs, t - 1]   # decision-time MTV
                go = r.p * r.g > (1 - r.p) * m
            elif policy == "naive":
                go = r.p >= thresh
            elif policy == "late":       # save for the 7th inning on, then naive
                go = (inn >= 7) and (r.p >= thresh)
            elif policy == "card":
                go = r.p > thresh(inn, r.g, r.balls, r.strikes, t)   # thresh is the card lookup function
            elif policy == "never":
                go = False
            else:
                raise ValueError(policy)
            if go:
                used += 1
                if rng.random() < r.p:
                    gain += r.g; succ += 1
                else:
                    t -= 1
        out.append((season, gid, th, gain, used, succ, t))
    return pd.DataFrame(out, columns=["season", "game_id", "team_home", "gain", "used", "succ", "tokens_left"])


# ---------------------------------------------------------------------------------------------
# 4. The challenge card: break-even success probability by a handful of cells
# ---------------------------------------------------------------------------------------------
INN_BAND = lambda inn: np.where(inn <= 3, "1-3", np.where(inn <= 6, "4-6", np.where(inn <= 8, "7-8", "9+")))
CNT_CLASS = lambda balls, strikes: np.where((balls == 3) | (strikes == 2), "PA-ending", "count-changing")


def add_breakeven(op: pd.DataFrame, C) -> pd.DataFrame:
    """Attach decision-time MTV and break-even p* = MTV/(g+MTV) for tokens t=2 and t=1 to each opportunity."""
    op = op.copy()
    d = np.clip(np.where(op["team_home"] == 1, op["score_diff_home"], -op["score_diff_home"]), -DMAX, DMAX).astype(int) + DMAX
    hc = np.minimum(op["h"].values, HMAX)
    for t in (1, 2):
        m = C[hc, d, op["outs"].values, t] - C[hc, d, op["outs"].values, t - 1]
        op[f"mtv_t{t}"] = m
        op[f"pstar_t{t}"] = np.where(op["g"] > 0, m / (op["g"] + m), 1.0)
    return op


def build_card(op: pd.DataFrame, C, lev_q=(1/3, 2/3)) -> pd.DataFrame:
    """Median break-even probability per cell: inning band × tokens × leverage band (g terciles) × count class."""
    op = add_breakeven(op, C)
    q1, q2 = op["g"].quantile(lev_q)
    op["lev"] = np.where(op["g"] < q1, "low", np.where(op["g"] < q2, "mid", "high"))
    op["inn_band"] = INN_BAND(op["inning"].values); op["cnt"] = CNT_CLASS(op["balls"].values, op["strikes"].values)
    rows = []
    for (ib, lev, cnt), grp in op.groupby(["inn_band", "lev", "cnt"]):
        rows.append(dict(inn_band=ib, lev=lev, cnt=cnt, n=len(grp), g_med=grp["g"].median(),
                         pstar_t2=grp["pstar_t2"].median(), pstar_t1=grp["pstar_t1"].median()))
    card = pd.DataFrame(rows)
    return card, (q1, q2)


def card_lookup(card, q):
    """Return a function (inning, g, balls, strikes, t) -> break-even p from the card."""
    q1, q2 = q
    idx = {(r.inn_band, r.lev, r.cnt): (r.pstar_t1, r.pstar_t2) for r in card.itertuples(index=False)}
    def f(inning, g, balls, strikes, t):
        ib = str(INN_BAND(np.array([inning]))[0]); lev = "low" if g < q1 else ("mid" if g < q2 else "high")
        cnt = str(CNT_CLASS(np.array([balls]), np.array([strikes]))[0])
        p1, p2 = idx.get((ib, lev, cnt), (0.5, 0.5))
        return p2 if t >= 2 else p1
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="*", type=int, default=[2023, 2024])
    ap.add_argument("--eval", nargs="*", type=int, default=[2025])
    args = ap.parse_args()
    cube = WPCube()
    print("building streams (train) ...")
    op, hi = build_streams(args.seasons, cube, synthetic_p, seed=1)
    print(f"  {len(op):,} opportunities, {len(hi):,} half-innings")
    print("solving DP ...")
    V, C = solve(op, hi)
    np.save(os.path.join(DATA, "V_synthetic.npy"), V); np.save(os.path.join(DATA, "C_synthetic.npy"), C)
    M = mtv(V)
    print("\nMarginal value of the 2nd token (t=2) by inning, tie game (WP points):")
    for h in range(1, 19, 2):
        print(f"  inning {(h+1)//2:2d}: MTV2={M[h, DMAX, 1]*100:5.2f} pp   MTV1={M[h, DMAX, 0]*100:5.2f} pp   V(2)={V[h, DMAX, 2]*100:5.2f} pp")
    print("\nMTV of 2nd token at inning 1 / 5 / 9 by score diff (team perspective):")
    for d in range(-DMAX, DMAX + 1):
        print(f"  d={d:+d}: {M[1, d+DMAX, 1]*100:5.2f} / {M[9, d+DMAX, 1]*100:5.2f} / {M[17, d+DMAX, 1]*100:5.2f} pp")
    print("\nevaluating policies on held-out season(s) ...")
    op2, hi2 = build_streams(args.eval, cube, synthetic_p, seed=2)
    card, q = build_card(op, C)
    print("\nChallenge card (median break-even success probability):")
    print(card.pivot_table(index=["inn_band", "cnt"], columns="lev", values="pstar_t2").round(2).to_string())
    look = card_lookup(card, q)
    for pol in ["optimal", "card", "naive", "late", "never"]:
        r = evaluate(op2, hi2, V, C, pol, thresh=look if pol == "card" else 0.5)
        print(f"  {pol:8s}: mean gain/team-game {r['gain'].mean()*100:.3f} pp of WP | challenges/game {r['used'].mean():.2f} "
              f"| success {r['succ'].sum()/max(r['used'].sum(),1):.2f} | tokens left {r['tokens_left'].mean():.2f}")


if __name__ == "__main__":
    main()
