"""
wp_count.py — count-aware win probability by PA-outcome composition (METHODS §4, primary WP variant v2).

    WP(S, b, s) = Σ_T  P(T | b, s, bases, outs) · WP_base(S ⊕ T)

S = (inning, half, outs, bases, score diff) is the base-out-score state at the pitch; (b, s) the count BEFORE the pitch;
T = (Δouts, bases after the PA, runs scored by the batting team during the rest of the PA) is the plate-appearance
transition; P(T | b, s, bases, outs) is the empirical distribution of PA transitions among Retrosheet 2021–2025 plate
appearances that passed through count (b, s) from base-out state (bases, outs); WP_base(S) is a count-free WP model
(HistGradientBoosting on Retrosheet 2015–2025 PA-start states, 2020 excluded, monotone in score difference).
Terminal counts are part of the grid: (4, s) = the PA ended in a walk on that pitch; (b, 3) = strikeout. So the value of
flipping a called strike at (b, s) is WP(S, b+1, s) − WP(S, b, s+1), including ball-four walks and strike-three outs, with the
inning-ending transition and the extra-innings automatic runner handled inside S ⊕ T.

Why not a direct WP(S, b, s) fit? Count effects are ~0.1–1 WP point and a flexible learner estimates them noisily; the
composition pins the count effect to the (well-measured) shift in where the PA ends. The direct fit (wp_model.py) is kept as
the robustness variant.

Usage:  python3 wp_count.py build     -> data/wp_count_cube.npz (+ data/wp_base_hgb.joblib), prints validation
"""
from __future__ import annotations

import os
import sys
import time

import joblib
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
DATA = os.path.join(HERE, "data")
CUBE_PATH = os.path.join(DATA, "wp_count_cube.npz")
BASE_PATH = os.path.join(DATA, "wp_base_hgb.joblib")

INN_CAP = 10
SD_CLIP = 10
BASES = ["___", "1__", "_2_", "12_", "__3", "1_3", "_23", "123"]
BASE_IDX = {b: i for i, b in enumerate(BASES)}
NB, NS = 5, 4          # balls 0..4 (4 = walk), strikes 0..3 (3 = strikeout)


def _load(seasons, cols=None):
    parts = []
    for y in seasons:
        p = os.path.join(DATA, f"pitches_{y}.parquet")
        if os.path.exists(p):
            parts.append(pd.read_parquet(p, columns=cols))
    return pd.concat(parts, ignore_index=True)


# ---------------------------------------------------------------------------------------------
# 1. PA table with transitions
# ---------------------------------------------------------------------------------------------
def pa_transitions(seasons):
    cols = ["season", "game_id", "inning", "bat_home", "outs", "bases", "home_score", "away_score", "balls", "strikes",
            "pitch_code", "pa_idx", "pitch_idx", "pa_event_cd", "pa_runs", "home_win"]
    df = _load(seasons, cols)
    df = df.sort_values(["season", "game_id", "pa_idx", "pitch_idx"]).reset_index(drop=True)
    df["bases_idx"] = df["bases"].map(BASE_IDX).astype(int)
    first = df.groupby(["season", "game_id", "pa_idx"], sort=False).first().reset_index()
    last = df.groupby(["season", "game_id", "pa_idx"], sort=False).last().reset_index()
    pa = first[["season", "game_id", "pa_idx", "inning", "bat_home", "outs", "bases_idx", "home_score", "away_score", "home_win"]].copy()
    pa["last_balls"] = last["balls"].values; pa["last_strikes"] = last["strikes"].values
    pa["last_code"] = last["pitch_code"].values; pa["event_cd"] = last["pa_event_cd"].values; pa["pa_runs"] = last["pa_runs"].values
    # next PA (same game)
    nxt = pa.groupby(["season", "game_id"])[["inning", "bat_home", "outs", "bases_idx", "home_score", "away_score"]].shift(-1)
    nxt.columns = ["n_inning", "n_bat_home", "n_outs", "n_bases_idx", "n_home_score", "n_away_score"]
    pa = pd.concat([pa, nxt], axis=1)
    same_half = (pa["n_inning"] == pa["inning"]) & (pa["n_bat_home"] == pa["bat_home"])
    bat_score = np.where(pa["bat_home"] == 1, pa["home_score"], pa["away_score"])
    n_bat_score = np.where(pa["bat_home"] == 1, pa["n_home_score"], pa["n_away_score"])
    runs = np.where(pa["n_inning"].notna(), n_bat_score - bat_score, pa["pa_runs"])   # last PA of the game: pa_runs
    pa["runs"] = np.clip(np.nan_to_num(runs, nan=0.0), 0, 4).astype(int)
    pa["d_outs"] = np.where(same_half, pa["n_outs"] - pa["outs"], 3 - pa["outs"]).astype(int)
    pa["end_bases"] = np.where(same_half, pa["n_bases_idx"], 0).astype(int)
    pa["inning_over"] = (~same_half).astype(int)
    pa = pa[(pa["d_outs"] >= 0) & (pa["d_outs"] <= 3)].copy()
    return df, pa


def count_paths(df, pa):
    """Rows (season, game_id, pa_idx, b, s) for every count passed through, plus terminal counts for walks/strikeouts."""
    pre = df[["season", "game_id", "pa_idx", "balls", "strikes"]].drop_duplicates()
    pre = pre[(pre["balls"] <= 3) & (pre["strikes"] <= 2)]
    walk = pa[pa["event_cd"].isin([14, 15]) & (pa["last_balls"] == 3)][["season", "game_id", "pa_idx", "last_strikes"]].copy()
    walk = walk.rename(columns={"last_strikes": "strikes"}); walk["balls"] = 4
    k = pa[(pa["event_cd"] == 3) & (pa["last_strikes"] == 2)][["season", "game_id", "pa_idx", "last_balls"]].copy()
    k = k.rename(columns={"last_balls": "balls"}); k["strikes"] = 3
    paths = pd.concat([pre, walk[["season", "game_id", "pa_idx", "balls", "strikes"]], k[["season", "game_id", "pa_idx", "balls", "strikes"]]], ignore_index=True)
    return paths


def transition_table(seasons=range(2021, 2026)):
    df, pa = pa_transitions(seasons)
    paths = count_paths(df, pa)
    m = paths.merge(pa[["season", "game_id", "pa_idx", "outs", "bases_idx", "d_outs", "end_bases", "runs", "inning_over"]],
                    on=["season", "game_id", "pa_idx"], how="inner")
    m["T"] = m["d_outs"] * 100 + m["end_bases"] * 10 + m["runs"]     # transition key
    tab = m.groupby(["balls", "strikes", "outs", "bases_idx", "T"]).size().rename("n").reset_index()
    tab["p"] = tab["n"] / tab.groupby(["balls", "strikes", "outs", "bases_idx"])["n"].transform("sum")
    tab["d_outs"] = tab["T"] // 100; tab["end_bases"] = (tab["T"] // 10) % 10; tab["runs"] = tab["T"] % 10
    return tab, pa


# ---------------------------------------------------------------------------------------------
# 2. Base WP model (count-free), fit on PA-start states
# ---------------------------------------------------------------------------------------------
BASE_FEATURES = ["inning_c", "bat_home", "outs", "on1", "on2", "on3", "sd", "ghost"]


def base_features(inning, bat_home, outs, bases_idx, sd_home, season=None):
    X = pd.DataFrame({"inning_c": np.minimum(np.asarray(inning), INN_CAP), "bat_home": np.asarray(bat_home).astype(int),
                      "outs": np.asarray(outs).astype(int)})
    b = np.asarray(bases_idx).astype(int)
    X["on1"] = b & 1; X["on2"] = (b >> 1) & 1; X["on3"] = (b >> 2) & 1
    X["sd"] = np.clip(np.asarray(sd_home).astype(int), -SD_CLIP, SD_CLIP)
    seas = np.asarray(season) if season is not None else np.full(len(X), 2025)
    X["ghost"] = ((np.asarray(inning) >= 10) & (seas >= 2020)).astype(int)
    return X[BASE_FEATURES]


def fit_base(seasons=(2015, 2016, 2017, 2018, 2019, 2021, 2022, 2023, 2024, 2025), max_iter=300):
    from sklearn.ensemble import HistGradientBoostingClassifier
    cols = ["season", "game_id", "inning", "bat_home", "outs", "bases", "score_diff_home", "pa_idx", "pitch_idx", "home_win"]
    df = _load(seasons, cols)
    df = df[df["pitch_idx"] == 0]                                  # PA-start states
    X = base_features(df["inning"], df["bat_home"], df["outs"], df["bases"].map(BASE_IDX), df["score_diff_home"], df["season"])
    y = df["home_win"].values
    games = df["game_id"].unique(); rng = np.random.default_rng(11)
    test_games = set(rng.choice(games, size=len(games) // 10, replace=False)); is_test = df["game_id"].isin(test_games).values
    mono = [0] * len(BASE_FEATURES); mono[BASE_FEATURES.index("sd")] = 1
    clf = HistGradientBoostingClassifier(max_iter=max_iter, learning_rate=0.08, max_leaf_nodes=63, min_samples_leaf=300,
                                         l2_regularization=1.0, monotonic_cst=mono, early_stopping=False, random_state=11)
    t0 = time.time(); clf.fit(X[~is_test], y[~is_test])
    p = clf.predict_proba(X[is_test])[:, 1]; yt = y[is_test]
    ll = -np.mean(yt * np.log(np.clip(p, 1e-9, 1)) + (1 - yt) * np.log(np.clip(1 - p, 1e-9, 1)))
    print(f"base WP fit on {(~is_test).sum():,} PA starts; test logloss {ll:.4f}, Brier {np.mean((p-yt)**2):.4f} ({time.time()-t0:.0f}s)")
    joblib.dump({"model": clf, "features": BASE_FEATURES}, BASE_PATH)
    return clf


# ---------------------------------------------------------------------------------------------
# 3. Cube by composition
# ---------------------------------------------------------------------------------------------
def build_cube(tab, base_model, season=2025):
    """cube[inning 0..10, bat_home, outs, bases, sd+10, balls 0..4, strikes 0..3] = WP(home)."""
    inn = np.arange(1, INN_CAP + 1); sds = np.arange(-SD_CLIP, SD_CLIP + 1)
    # all base states S
    S = pd.MultiIndex.from_product([inn, [0, 1], [0, 1, 2], range(8), sds], names=["inning", "bat_home", "outs", "bases", "sd"]).to_frame(index=False)
    cube = np.full((INN_CAP + 1, 2, 3, 8, 2 * SD_CLIP + 1, NB, NS), np.nan, dtype=np.float32)
    # transitions grouped by (balls, strikes, outs, bases)
    groups = {k: v for k, v in tab.groupby(["balls", "strikes", "outs", "bases_idx"])}
    # precompute WP_base for all successor states via one big predict: build the successor table lazily with a cache
    def wp_base_vec(inning, bat_home, outs, bases, sd):
        X = base_features(inning, bat_home, outs, bases, sd, np.full(len(inning), season))
        return base_model.predict_proba(X)[:, 1]
    rows = []
    for (b, s, o, bi), tr in groups.items():
        Ss = S[(S["outs"] == o) & (S["bases"] == bi)]
        n_s = len(Ss)
        acc = np.zeros(n_s)
        for t in tr.itertuples(index=False):
            new_outs = o + t.d_outs
            over = new_outs >= 3
            runs_home = np.where(Ss["bat_home"].values == 1, t.runs, -t.runs)
            sd2 = Ss["sd"].values + runs_home
            if over:
                inn2 = np.where(Ss["bat_home"].values == 1, Ss["inning"].values + 1, Ss["inning"].values)
                bh2 = 1 - Ss["bat_home"].values
                o2 = np.zeros(n_s, dtype=int)
                b2 = np.where(inn2 >= 10, 2, 0)                     # automatic runner on second from the 10th
            else:
                inn2 = Ss["inning"].values; bh2 = Ss["bat_home"].values; o2 = np.full(n_s, new_outs); b2 = np.full(n_s, t.end_bases)
            # game over? bottom of 9th+ with home ahead after the runs; or top of 9th+ over with home ahead; walk-off handled by WP_base
            # (WP_base at the start of a half-inning that never happens is not exact; handle end-of-game states explicitly)
            wp = wp_base_vec(inn2, bh2, o2, b2, sd2)
            # explicit terminal handling: if the half-inning that ended was the bottom of inning>=9 and home leads -> home won;
            # if top of inning>=9 ended (or later) and home leads -> home wins without batting (WP_base handles: bh2=1 with sd>0 at inn>=9 → ~1)
            if over:
                bottom_ended = Ss["bat_home"].values == 1
                home_won = bottom_ended & (Ss["inning"].values >= 9) & (sd2 > 0)
                away_won = bottom_ended & (Ss["inning"].values >= 9) & (sd2 < 0)
                wp = np.where(home_won, 1.0, np.where(away_won, 0.0, wp))
            else:
                # walk-off during the bottom of 9th+ (home takes the lead) -> game over
                walkoff = (Ss["bat_home"].values == 1) & (Ss["inning"].values >= 9) & (sd2 > 0)
                wp = np.where(walkoff, 1.0, wp)
            acc += t.p * wp
        cube[Ss["inning"].values, Ss["bat_home"].values, Ss["outs"].values, Ss["bases"].values, Ss["sd"].values + SD_CLIP, b, s] = acc
    return cube


class WPCountCube:
    def __init__(self, path=CUBE_PATH):
        self.cube = np.load(path)["cube"]

    def wp_home(self, inning, bat_home, outs, bases_idx, sd, balls, strikes):
        inn = np.minimum(np.asarray(inning), INN_CAP); sdc = np.clip(np.asarray(sd), -SD_CLIP, SD_CLIP) + SD_CLIP
        return self.cube[inn, np.asarray(bat_home), np.asarray(outs), np.asarray(bases_idx), sdc, np.asarray(balls), np.asarray(strikes)]

    def flip_gain(self, inning, bat_home, outs, bases_idx, sd, balls, strikes, original_call):
        """ΔWP for the CHALLENGING side if the call is overturned. original_call 'S' (called strike; batting team challenges)
        or 'B' (called ball; fielding team challenges). Uses the terminal counts (4,s) walk and (b,3) strikeout."""
        balls = np.asarray(balls); strikes = np.asarray(strikes); bat_home = np.asarray(bat_home)
        wp_ball = self.wp_home(inning, bat_home, outs, bases_idx, sd, balls + 1, strikes)
        wp_strike = self.wp_home(inning, bat_home, outs, bases_idx, sd, balls, strikes + 1)
        if original_call == "S":
            d_home = wp_ball - wp_strike; challenger_is_home = bat_home == 1
        else:
            d_home = wp_strike - wp_ball; challenger_is_home = bat_home == 0
        return np.where(challenger_is_home, d_home, -d_home)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        t0 = time.time()
        if os.path.exists(BASE_PATH):
            base = joblib.load(BASE_PATH)["model"]; print("loaded base WP model")
        else:
            base = fit_base()
        tab, pa = transition_table()
        print(f"transition table: {len(tab):,} rows over {tab.groupby(['balls','strikes','outs','bases_idx']).ngroups} count×base-out cells; PAs {len(pa):,} ({time.time()-t0:.0f}s)")
        cube = build_cube(tab, base)
        np.savez_compressed(CUBE_PATH, cube=cube)
        print(f"cube saved {CUBE_PATH} shape {cube.shape}; nan cells {int(np.isnan(cube).sum())} ({time.time()-t0:.0f}s)")
        c = WPCountCube()
        # validation 1: implied count values in a neutral state (top 1st, 0 outs, none on, tie), home perspective → batting-team runs
        print("WP(home) top 1st, none on, 0 out, tie, by count (pp):")
        for b in range(4):
            print("  ", [f"{c.wp_home(1, 0, 0, 0, 0, b, s)*100:.2f}" for s in range(3)])
        base_wp = c.wp_home(1, 0, 0, 0, 0, 0, 0)
        print(f"  walk (4,0): {c.wp_home(1,0,0,0,0,4,0)*100:.2f}; K (0,3): {c.wp_home(1,0,0,0,0,0,3)*100:.2f}; PA start {base_wp*100:.2f}")
        # a run's WP value in that state ≈ WP(home) change when the away team is +1: use sd=-1 at the same state
        run_val = c.wp_home(1, 0, 0, 0, 0, 0, 0) - c.wp_home(1, 0, 0, 0, -1, 0, 0)
        print(f"  WP value of one away run in that state: {run_val*100:.2f} pp; implied run value of a 0-0 called strike: "
              f"{(c.wp_home(1,0,0,0,0,0,1)-c.wp_home(1,0,0,0,0,0,0))/run_val:.3f} runs (literature ≈ −0.04 for the batter);"
              f" 0-0 ball: {(c.wp_home(1,0,0,0,0,1,0)-c.wp_home(1,0,0,0,0,0,0))/run_val:.3f} runs")
    else:
        print("usage: python3 wp_count.py build")


if __name__ == "__main__":
    main()
