"""
retro_parse.py — turn Chadwick cwevent CSVs (Retrosheet 2015–2025) into a pitch-level state table.

Each output row = one pitch (or terminal event) with the game state BEFORE the pitch:
  season, game_id, home_team, away_team, inning, bat_home (1 = home batting), outs, bases (3-char '1_3'),
  on1, on2, on3, home_score, away_score, score_diff_home, balls, strikes, pitch_code (Retrosheet char),
  called (1 if 'B' or 'C'), pa_idx (PA index within game), pitch_idx (within PA), bat_id, pit_id, cat_id,
  bat_hand, pit_hand, pa_event_cd (Retrosheet EVENT_CD of the PA), pa_runs, home_win (game outcome).

Count rules (Retrosheet pitch codes):
  balls   += 1 : B (called ball), I (intentional ball), P (pitchout), V (automatic ball)
  strikes += 1 : C (called), S (swinging), K (unknown strike), M (missed bunt), Q (swing on pitchout),
                 A (automatic strike), T (foul tip), O (foul tip on bunt), L (foul bunt — strike even at 2)
  foul F / R   : strike only if strikes < 2
  X / Y        : ball in play (PA ends);  H : hit by pitch (PA ends)
  ignored      : N (no pitch), U (unknown), and modifiers + * . > 1 2 3
Only batter-event rows (BAT_EVENT_FL == 'T') carry the full PA pitch sequence, so those are used.
Base-out state is taken at PA start (mid-PA steals/pickoffs are ignored — documented limitation).
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
RETRO = os.path.join(HERE, "retro")
OUT = os.path.join(HERE, "data")
os.makedirs(OUT, exist_ok=True)

BALL_CODES = set("BIPV")
STRIKE_ALWAYS = set("CSKMQATOL")
FOUL_CODES = set("FR")
END_CODES = set("XYH")
IGNORE = set("NU+*.>123")

BASES_MAP = {0: "___", 1: "1__", 2: "_2_", 3: "12_", 4: "__3", 5: "1_3", 6: "_23", 7: "123"}


def load_header():
    with open(os.path.join(RETRO, "header.csv")) as fh:
        return [c.strip().strip('"') for c in fh.read().strip().split(",")]


def parse_season(season: int, header) -> pd.DataFrame:
    path = os.path.join(RETRO, f"events_{season}.csv")
    use = ["GAME_ID", "AWAY_TEAM_ID", "HOME_TEAM_ID", "INN_CT", "BAT_HOME_ID", "OUTS_CT", "PITCH_SEQ_TX",
           "AWAY_SCORE_CT", "HOME_SCORE_CT", "BAT_ID", "BAT_HAND_CD", "PIT_ID", "PIT_HAND_CD", "POS2_FLD_ID",
           "EVENT_CD", "BAT_EVENT_FL", "GAME_END_FL", "EVENT_RUNS_CT", "START_BASES_CD", "GAME_PA_CT",
           "PA_NEW_FL", "PA_TRUNC_FL"]
    df = pd.read_csv(path, header=None, names=header, usecols=use, dtype=str, keep_default_na=False)
    for c in ["INN_CT", "BAT_HOME_ID", "OUTS_CT", "AWAY_SCORE_CT", "HOME_SCORE_CT", "EVENT_CD", "EVENT_RUNS_CT",
              "START_BASES_CD", "GAME_PA_CT"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    # ---- game outcomes -------------------------------------------------------------------
    last = df[df["GAME_END_FL"] == "T"].copy()
    last["home_final"] = np.where(last["BAT_HOME_ID"] == 1, last["HOME_SCORE_CT"] + last["EVENT_RUNS_CT"], last["HOME_SCORE_CT"])
    last["away_final"] = np.where(last["BAT_HOME_ID"] == 0, last["AWAY_SCORE_CT"] + last["EVENT_RUNS_CT"], last["AWAY_SCORE_CT"])
    last = last[last["home_final"] != last["away_final"]]
    outcome = dict(zip(last["GAME_ID"], (last["home_final"] > last["away_final"]).astype(int)))

    # ---- batter events only (full pitch sequence for the PA) --------------------------------
    pa = df[(df["BAT_EVENT_FL"] == "T")].copy()
    pa = pa[pa["GAME_ID"].isin(outcome)]
    pa["home_win"] = pa["GAME_ID"].map(outcome).astype(int)
    pa = pa[~pa["GAME_ID"].str.startswith("ALS")]  # All-Star game
    pa = pa.reset_index(drop=True)
    pa["pa_idx"] = pa.groupby("GAME_ID").cumcount()

    rows = []
    for r in pa.itertuples(index=False):
        seq = r.PITCH_SEQ_TX
        b = s = 0
        k = 0
        bases = BASES_MAP.get(int(r.START_BASES_CD), "___")
        base = (season, r.GAME_ID, r.HOME_TEAM_ID, r.AWAY_TEAM_ID, r.INN_CT, r.BAT_HOME_ID, r.OUTS_CT, bases,
                int(bases[0] == "1"), int(bases[1] == "2"), int(bases[2] == "3"), r.HOME_SCORE_CT, r.AWAY_SCORE_CT,
                r.HOME_SCORE_CT - r.AWAY_SCORE_CT)
        tail = (r.pa_idx, r.BAT_ID, r.PIT_ID, r.POS2_FLD_ID, r.BAT_HAND_CD, r.PIT_HAND_CD, r.EVENT_CD, r.EVENT_RUNS_CT, r.home_win)
        for ch in seq:
            if ch in IGNORE:
                continue
            called = 1 if ch in ("B", "C") else 0
            rows.append(base + (b, s, ch, called, k) + tail)
            k += 1
            if ch in BALL_CODES:
                b += 1
                if b >= 4:
                    break
            elif ch in STRIKE_ALWAYS:
                s += 1
                if s >= 3:
                    break
            elif ch in FOUL_CODES:
                if s < 2:
                    s += 1
            elif ch in END_CODES:
                break
            # guard against malformed sequences
            if b > 3 or s > 2:
                break
    cols = ["season", "game_id", "home_team", "away_team", "inning", "bat_home", "outs", "bases", "on1", "on2", "on3",
            "home_score", "away_score", "score_diff_home", "balls", "strikes", "pitch_code", "called", "pitch_idx",
            "pa_idx", "bat_id", "pit_id", "cat_id", "bat_hand", "pit_hand", "pa_event_cd", "pa_runs", "home_win"]
    out = pd.DataFrame.from_records(rows, columns=cols)
    return out


def main(seasons=None):
    header = load_header()
    seasons = seasons or list(range(2015, 2026))
    for y in seasons:
        out = os.path.join(OUT, f"pitches_{y}.parquet")
        if os.path.exists(out):
            print(f"[skip] {out}")
            continue
        df = parse_season(y, header)
        df.to_parquet(out, index=False)
        print(f"[ok] {y}: {len(df):,} pitch rows, {df['game_id'].nunique():,} games, "
              f"called share {df['called'].mean():.3f}, home win rate {df.groupby('game_id')['home_win'].first().mean():.3f}")


if __name__ == "__main__":
    ys = [int(a) for a in sys.argv[1:]] or None
    main(ys)
