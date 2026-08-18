"""
wp_model.py — win-probability model at pitch resolution: P(home wins | game state incl. count).

Features: inning (capped at 10), bat_home, outs, on1/on2/on3, score_diff_home (clipped ±10), balls, strikes,
          ghost (extra innings in the automatic-runner era, 2020+).
Model: sklearn HistGradientBoostingClassifier with a monotone constraint on score_diff_home.
Training data: pitch-level rows from Retrosheet 2015–2025 (regular season) built by retro_parse.py.

Provides:
  fit_wp(...)                     -> trained model, saved to data/wp_hgb.joblib
  WP.predict(states DataFrame)    -> home win prob
  flip_values(states)             -> ΔWP (for the challenging side) of overturning a call, with terminal handling
Also builds a lookup cube for fast DP use: wp_cube[inning, bat_home, outs, bases, sd, balls, strikes].
"""
from __future__ import annotations

import os
import sys
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
MODEL_PATH = os.path.join(DATA, "wp_hgb.joblib")
CUBE_PATH = os.path.join(DATA, "wp_cube.npz")

FEATURES = ["inning_c", "bat_home", "outs", "on1", "on2", "on3", "sd", "balls", "strikes", "ghost"]
SD_CLIP = 10
INN_CAP = 10
BASES = ["___", "1__", "_2_", "12_", "__3", "1_3", "_23", "123"]
BASE_IDX = {b: i for i, b in enumerate(BASES)}


def featurize(df: pd.DataFrame) -> pd.DataFrame:
    X = pd.DataFrame(index=df.index)
    X["inning_c"] = np.minimum(df["inning"].astype(int), INN_CAP)
    X["bat_home"] = df["bat_home"].astype(int)
    X["outs"] = df["outs"].astype(int)
    X["on1"] = df["on1"].astype(int); X["on2"] = df["on2"].astype(int); X["on3"] = df["on3"].astype(int)
    X["sd"] = np.clip(df["score_diff_home"].astype(int), -SD_CLIP, SD_CLIP)
    X["balls"] = df["balls"].astype(int)
    X["strikes"] = df["strikes"].astype(int)
    season = df["season"].astype(int) if "season" in df else pd.Series(2025, index=df.index)
    X["ghost"] = ((df["inning"].astype(int) >= 10) & (season >= 2020)).astype(int)
    return X[FEATURES]


def load_pitches(seasons=range(2015, 2026), cols=None):
    parts = []
    for y in seasons:
        p = os.path.join(DATA, f"pitches_{y}.parquet")
        if os.path.exists(p):
            parts.append(pd.read_parquet(p, columns=cols))
    return pd.concat(parts, ignore_index=True)


def fit_wp(seasons=range(2015, 2026), max_iter=400, save=True):
    cols = ["season", "game_id", "inning", "bat_home", "outs", "on1", "on2", "on3", "score_diff_home", "balls",
            "strikes", "home_win"]
    df = load_pitches(seasons, cols)
    # hold out 10% of GAMES for calibration checks
    games = df["game_id"].unique()
    rng = np.random.default_rng(7)
    test_games = set(rng.choice(games, size=len(games) // 10, replace=False))
    is_test = df["game_id"].isin(test_games).values
    X = featurize(df); y = df["home_win"].values
    mono = [0] * len(FEATURES); mono[FEATURES.index("sd")] = 1
    t0 = time.time()
    clf = HistGradientBoostingClassifier(max_iter=max_iter, learning_rate=0.08, max_leaf_nodes=63, min_samples_leaf=200,
                                         l2_regularization=1.0, monotonic_cst=mono, early_stopping=False, random_state=7)
    clf.fit(X[~is_test], y[~is_test])
    p = clf.predict_proba(X[is_test])[:, 1]
    yt = y[is_test]
    ll = -np.mean(yt * np.log(np.clip(p, 1e-9, 1)) + (1 - yt) * np.log(np.clip(1 - p, 1e-9, 1)))
    brier = np.mean((p - yt) ** 2)
    print(f"fit on {(~is_test).sum():,} pitches; test {is_test.sum():,}: logloss {ll:.4f}, Brier {brier:.4f}, {time.time()-t0:.0f}s")
    # calibration table
    bins = np.clip((p * 10).astype(int), 0, 9)
    cal = pd.DataFrame({"bin": bins, "p": p, "y": yt}).groupby("bin").agg(n=("y", "size"), pred=("p", "mean"), obs=("y", "mean"))
    print(cal.round(3).to_string())
    if save:
        joblib.dump({"model": clf, "features": FEATURES, "seasons": list(seasons)}, MODEL_PATH)
        print(f"saved {MODEL_PATH}")
    return clf


class WP:
    def __init__(self, path=MODEL_PATH):
        obj = joblib.load(path)
        self.model = obj["model"]

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        return self.model.predict_proba(featurize(df))[:, 1]


def build_cube(wp: WP, season=2025):
    """Full lookup: inning 1..10, bat_home 0/1, outs 0-2, bases 0-7, sd -10..10, balls 0-3, strikes 0-2 (+ ghost implied by
    inning==10 & season>=2020)."""
    grid = []
    for inn in range(1, INN_CAP + 1):
        for bh in (0, 1):
            for o in range(3):
                for bi, b in enumerate(BASES):
                    for sd in range(-SD_CLIP, SD_CLIP + 1):
                        for balls in range(4):
                            for strikes in range(3):
                                grid.append((inn, bh, o, b, int(b[0] == "1"), int(b[1] == "2"), int(b[2] == "3"), sd, balls, strikes))
    g = pd.DataFrame(grid, columns=["inning", "bat_home", "outs", "bases", "on1", "on2", "on3", "score_diff_home", "balls", "strikes"])
    g["season"] = season
    p = wp.predict(g)
    cube = np.zeros((INN_CAP + 1, 2, 3, 8, 2 * SD_CLIP + 1, 4, 3), dtype=np.float32)
    idx = (g["inning"].values, g["bat_home"].values, g["outs"].values, g["bases"].map(BASE_IDX).values,
           g["score_diff_home"].values + SD_CLIP, g["balls"].values, g["strikes"].values)
    cube[idx] = p
    np.savez_compressed(CUBE_PATH, cube=cube)
    print(f"cube saved {CUBE_PATH} shape {cube.shape}")
    return cube


class WPCube:
    """Fast WP lookups + flip values from the cube. All arrays are numpy; states are the standard fields."""
    def __init__(self, path=CUBE_PATH):
        self.cube = np.load(path)["cube"]

    def wp_home(self, inning, bat_home, outs, bases_idx, sd, balls, strikes):
        inn = np.minimum(inning, INN_CAP); sdc = np.clip(sd, -SD_CLIP, SD_CLIP) + SD_CLIP
        return self.cube[inn, bat_home, outs, bases_idx, sdc, balls, strikes]

    # --- terminal transitions -------------------------------------------------------------
    @staticmethod
    def walk_state(bases_idx, sd_home, bat_home):
        """Batter walks: forced runners advance; run scores if bases loaded. Returns (bases_idx', sd_home')."""
        on1, on2, on3 = bases_idx & 1, (bases_idx >> 1) & 1, (bases_idx >> 2) & 1
        run = on1 & on2 & on3
        n_on2 = np.where(on1 == 1, 1, on2)               # runner on 1st forced to 2nd
        n_on3 = np.where((on1 == 1) & (on2 == 1), 1, on3)  # runner on 2nd forced to 3rd only if 1st also occupied
        new_idx = 1 + 2 * n_on2 + 4 * n_on3
        sd_new = sd_home + np.where(bat_home == 1, run, -run)
        return new_idx, sd_new

    def wp_after_pitch(self, inning, bat_home, outs, bases_idx, sd, balls, strikes, call):
        """WP(home) after a called pitch with call 'B' or 'S' at count (balls,strikes) — handles walk/strikeout/inning end.
        Simplification: dropped third strikes and inning-ending state transitions beyond 3 outs are handled by moving to
        the next half-inning with the same score."""
        inning = np.asarray(inning); bat_home = np.asarray(bat_home); outs = np.asarray(outs)
        bases_idx = np.asarray(bases_idx); sd = np.asarray(sd); balls = np.asarray(balls); strikes = np.asarray(strikes)
        if call == "B":
            walk = balls + 1 >= 4
            nb_idx, nsd = self.walk_state(bases_idx, sd, bat_home)
            wp_walk = self.wp_home(inning, bat_home, outs, nb_idx, nsd, 0, 0)
            wp_ball = self.wp_home(inning, bat_home, outs, bases_idx, sd, np.minimum(balls + 1, 3), strikes)
            return np.where(walk, wp_walk, wp_ball)
        else:
            k = strikes + 1 >= 3
            new_outs = outs + 1
            inning_over = new_outs >= 3
            # next half-inning: if bottom ends -> next inning top; if top ends -> bottom same inning
            n_inning = np.where(inning_over, np.where(bat_home == 1, inning + 1, inning), inning)
            n_bat_home = np.where(inning_over, 1 - bat_home, bat_home)
            n_outs = np.where(inning_over, 0, new_outs)
            n_bases = np.where(inning_over, 0, bases_idx)
            wp_k = self.wp_home(n_inning, n_bat_home, n_outs, n_bases, sd, 0, 0)
            wp_strike = self.wp_home(inning, bat_home, outs, bases_idx, sd, balls, np.minimum(strikes + 1, 2))
            return np.where(k, wp_k, wp_strike)

    def flip_gain(self, inning, bat_home, outs, bases_idx, sd, balls, strikes, original_call):
        """ΔWP for the CHALLENGING side if the call is overturned. original_call 'S' (called strike; batting team may
        challenge) or 'B' (called ball; fielding team may challenge). Returned from the challenger's perspective (>0 = good)."""
        wp_if_ball = self.wp_after_pitch(inning, bat_home, outs, bases_idx, sd, balls, strikes, "B")
        wp_if_strike = self.wp_after_pitch(inning, bat_home, outs, bases_idx, sd, balls, strikes, "S")
        bat_home = np.asarray(bat_home)
        # home-perspective delta of turning the call the challenger's way
        if original_call == "S":   # batter wants a ball
            d_home = wp_if_ball - wp_if_strike
            challenger_is_home = bat_home == 1
        else:                       # fielders want a strike
            d_home = wp_if_strike - wp_if_ball
            challenger_is_home = bat_home == 0
        return np.where(challenger_is_home, d_home, -d_home)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fit":
        clf = fit_wp()
        build_cube(WP())
    else:
        print("usage: python3 wp_model.py fit")
