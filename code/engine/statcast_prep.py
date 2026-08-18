"""
statcast_prep.py — turn raw Statcast season parquet files into the per-pitch ABS table used everywhere else.

Input : data/raw/statcast/statcast_<season>.parquet   (pybaseball statcast() columns)
        data/raw/players/players_<season>.csv          (StatsAPI heights; id, height_in)
Output: data/derived/abs_pitches_<season>.parquet with, for every CALLED pitch (description in
        {called_strike, ball, blocked_ball}):
        game_pk, game_date, game_type, at_bat_number, pitch_number, inning, bat_home, outs, bases_idx, sd_home,
        balls, strikes, batter, pitcher, catcher, stand, p_throws, pitch_type, release_speed,
        call ('S'/'B'), plate_x, plate_z, x_mid, z_mid, height_in, d_in (signed miss to ABS zone; <0 inside),
        d_in_center (center-of-ball variant), d_in_front (front-of-plate variant), zone_ok (flag: trajectory available),
        d_fav (signed miss in favour of the eligible challenger: >0 means the call was wrong), eligible ('bat'/'fld'),
        g (ΔWP for the eligible challenger if overturned; from the WP cube), plus Savant's own delta_home_win_exp for checks.

Run:  python3 statcast_prep.py 2026 2025 ...
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "code"))
from abs_zone import propagate_to_midpoint, signed_miss_inches, BALL_RADIUS  # noqa: E402
from wp_model import WPCube  # noqa: E402

ROOT = os.environ.get("ABS_ROOT") or os.path.dirname(HERE)          # sloan/  (raw data staged under data/raw)
RAW = os.path.join(ROOT, "data", "raw")
DER = os.path.join(ROOT, "data", "derived")
os.makedirs(DER, exist_ok=True)

CALLED = {"called_strike": "S", "ball": "B", "blocked_ball": "B"}
BASE_IDX_FROM_FLAGS = lambda on1, on2, on3: (on1.astype(int) + 2 * on2.astype(int) + 4 * on3.astype(int))


def load_heights(season):
    p = os.path.join(RAW, "players", f"players_{season}.csv")
    if not os.path.exists(p):
        return None
    h = pd.read_csv(p, usecols=["id", "height_in"])
    return dict(zip(h["id"].astype(int), h["height_in"]))


def prep_season(season, cube: WPCube):
    src = os.path.join(RAW, "statcast", f"statcast_{season}.parquet")
    df = pd.read_parquet(src)
    n0 = len(df)
    df = df[df["description"].isin(CALLED)].copy()
    df["call"] = df["description"].map(CALLED)
    # ---- state -------------------------------------------------------------------------------
    df["bat_home"] = (df["inning_topbot"].astype(str).str.lower() == "bot").astype(int)
    df["outs"] = df["outs_when_up"].astype(int)
    on1 = df["on_1b"].notna(); on2 = df["on_2b"].notna(); on3 = df["on_3b"].notna()
    df["bases_idx"] = BASE_IDX_FROM_FLAGS(on1, on2, on3)
    df["sd_home"] = (df["home_score"] - df["away_score"]).astype(int)
    df["balls"] = df["balls"].astype(int).clip(0, 3); df["strikes"] = df["strikes"].astype(int).clip(0, 2)
    df["catcher"] = df["fielder_2"] if "fielder_2" in df else np.nan
    # ---- geometry ----------------------------------------------------------------------------
    need = ["plate_x", "plate_z", "vx0", "vy0", "vz0", "ax", "ay", "az"]
    ok = df[need].notna().all(axis=1)
    df["zone_ok"] = ok.astype(int)
    x_mid = np.full(len(df), np.nan); z_mid = np.full(len(df), np.nan)
    if season >= 2026:
        # Savant moved plate_x/plate_z to the PLATE-MIDPOINT plane and made sz_top/sz_bot ABS-defined from 2026
        # (Savant CSV docs, lit/10). No propagation; the ABS-certified height is implied by sz_top = 0.535*H.
        x_mid[:] = df["plate_x"].values; z_mid[:] = df["plate_z"].values
        df["plane_src"] = "savant_midplane_2026"
    else:
        xm, zm = propagate_to_midpoint(*[df.loc[ok, c].values for c in need])
        x_mid[ok.values] = xm; z_mid[ok.values] = zm
        df["plane_src"] = "propagated_9P"
    df["x_mid"] = x_mid; df["z_mid"] = z_mid
    heights = load_heights(season) or {}
    df["height_roster_in"] = df["batter"].astype(int).map(heights)
    if season >= 2026:
        df["height_in"] = (df["sz_top"] * 12 / 0.535)          # ABS-certified height implied by Savant's ABS zone top
        df["height_src"] = "savant_sz_top_2026"
        # cross-check: implied height vs sz_bot (should be 0.27*H) and vs roster height
        df["height_in_from_bot"] = df["sz_bot"] * 12 / 0.27
    else:
        df["height_in"] = df["height_roster_in"]
        fallback = df["height_in"].isna()
        df.loc[fallback, "height_in"] = (df.loc[fallback, "sz_top"] * 12 / 0.535).round()
        df["height_src"] = np.where(fallback, "sz_top_fallback", "statsapi_roster")
    df["d_in"] = signed_miss_inches(df["x_mid"], df["z_mid"], df["height_in"])                    # any-part, midpoint
    df["d_in_center"] = signed_miss_inches(df["x_mid"], df["z_mid"], df["height_in"], expand_ball=False)
    df["d_in_front"] = signed_miss_inches(df["plate_x"], df["plate_z"], df["height_in"])           # any-part, front of plate
    # ---- who may challenge and was the call wrong -----------------------------------------------
    # called strike -> batting side may challenge; wrong iff pitch was outside (d_in > 0)
    # called ball   -> fielding side may challenge; wrong iff pitch was inside (d_in <= 0)
    df["eligible"] = np.where(df["call"] == "S", "bat", "fld")
    df["d_fav"] = np.where(df["call"] == "S", df["d_in"], -df["d_in"])          # >0 means call was wrong (favourable to challenger)
    # ---- ΔWP if overturned, for the eligible challenger ------------------------------------------
    g = np.zeros(len(df))
    for call in ("S", "B"):
        m = (df["call"] == call).values
        g[m] = cube.flip_gain(df["inning"].values[m], df["bat_home"].values[m], df["outs"].values[m],
                              df["bases_idx"].values[m], df["sd_home"].values[m], df["balls"].values[m],
                              df["strikes"].values[m], call)
    df["g"] = np.maximum(g, 0.0)
    keep = ["game_pk", "game_date", "game_type", "at_bat_number", "pitch_number", "inning", "bat_home", "outs", "bases_idx",
            "sd_home", "balls", "strikes", "batter", "pitcher", "catcher", "stand", "p_throws", "pitch_type", "release_speed",
            "call", "plate_x", "plate_z", "x_mid", "z_mid", "plane_src", "height_in", "height_roster_in", "height_src", "d_in", "d_in_center", "d_in_front",
            "zone_ok", "eligible", "d_fav", "g"]
    for extra in ["delta_home_win_exp", "home_win_exp", "delta_run_exp", "umpire", "sz_top", "sz_bot", "zone", "height_in_from_bot"]:
        if extra in df.columns:
            keep.append(extra)
    out = df[keep].sort_values(["game_pk", "at_bat_number", "pitch_number"]).reset_index(drop=True)
    dst = os.path.join(DER, f"abs_pitches_{season}.parquet")
    out.to_parquet(dst, index=False)
    wrong = (out["d_fav"] > 0).mean()
    print(f"[ok] {season}: {n0:,} pitches -> {len(out):,} called; trajectory ok {out['zone_ok'].mean():.3f}; "
          f"heights from StatsAPI {(out['height_src']=='statsapi').mean():.3f}; share of calls wrong vs ABS zone {wrong:.3f}; "
          f"median |d| {out['d_in'].abs().median():.2f} in -> {dst}")
    return out


if __name__ == "__main__":
    cube = WPCube()
    seasons = [int(a) for a in sys.argv[1:]] or [2026]
    for y in seasons:
        prep_season(y, cube)
