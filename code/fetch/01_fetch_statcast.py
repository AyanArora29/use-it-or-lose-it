#!/usr/bin/env python3
"""
01_fetch_statcast.py — pull Statcast pitch-level data season by season via pybaseball.

Output: <repo>/data/raw/statcast/statcast_<season>.parquet   (one file per season)
Resumable: seasons whose parquet already exists are skipped (use --force to redo).

Usage:
    python3 01_fetch_statcast.py                     # 2026, then 2025 ... 2015
    python3 01_fetch_statcast.py --seasons 2026 2025
    python3 01_fetch_statcast.py --force --seasons 2026   # re-pull the current season

Requires: pip install pybaseball pandas pyarrow
"""
import argparse
import datetime as dt
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
def _find_root(start):
    p = start
    for _ in range(4):
        if any(os.path.exists(os.path.join(p, m)) for m in ("requirements.txt", "Instruction", "METHODS.md")):
            return p
        p = os.path.dirname(p)
    return os.path.dirname(start)
ROOT = os.environ.get("ABS_ROOT") or _find_root(HERE)
OUT_DIR = os.path.join(ROOT, "data", "raw", "statcast")

# Season windows: generous bounds; pybaseball returns nothing for off days.
# Spring training is included on purpose (2025 ST had the ABS challenge trial in some parks).
SEASON_WINDOWS = {
    2015: ("2015-03-01", "2015-11-05"),
    2016: ("2016-03-01", "2016-11-05"),
    2017: ("2017-02-20", "2017-11-05"),
    2018: ("2018-02-20", "2018-11-05"),
    2019: ("2019-02-20", "2019-11-05"),
    2020: ("2020-02-20", "2020-11-05"),
    2021: ("2021-02-25", "2021-11-05"),
    2022: ("2022-03-15", "2022-11-08"),
    2023: ("2023-02-24", "2023-11-05"),
    2024: ("2024-02-22", "2024-11-05"),
    2025: ("2025-02-20", "2025-11-05"),
    2026: ("2026-02-20", None),   # None = through yesterday
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", nargs="*", type=int, default=None,
                    help="seasons to pull (default: 2026 down to 2015)")
    ap.add_argument("--force", action="store_true", help="re-pull even if the parquet exists")
    args = ap.parse_args()

    try:
        import pandas as pd
        import pybaseball
        from pybaseball import statcast
    except ImportError as e:
        sys.exit(f"Missing package ({e}). Run: python3 -m pip install pybaseball pandas pyarrow")

    pybaseball.cache.enable()          # lets a killed run resume without re-downloading
    os.makedirs(OUT_DIR, exist_ok=True)

    seasons = args.seasons or sorted(SEASON_WINDOWS, reverse=True)
    yesterday = (dt.date.today() - dt.timedelta(days=1)).isoformat()

    for season in seasons:
        if season not in SEASON_WINDOWS:
            print(f"[skip] no window defined for {season}")
            continue
        out = os.path.join(OUT_DIR, f"statcast_{season}.parquet")
        if os.path.exists(out) and not args.force:
            print(f"[skip] {out} exists ({os.path.getsize(out)/1e6:.0f} MB). Use --force to redo.")
            continue
        start, end = SEASON_WINDOWS[season]
        end = end or yesterday
        print(f"\n=== Season {season}: {start} → {end} ===", flush=True)
        t0 = time.time()
        try:
            df = statcast(start_dt=start, end_dt=end, verbose=True, parallel=True)
        except Exception as e:
            print(f"[error] season {season}: {e!r}. Re-run to resume (cache is on).")
            continue
        if df is None or df.empty:
            print(f"[warn] season {season}: no rows returned")
            continue
        # keep everything Savant gives us; downstream code selects columns
        df["season"] = season
        df.to_parquet(out, index=False)
        n_games = df["game_pk"].nunique() if "game_pk" in df.columns else -1
        print(f"[ok] {season}: {len(df):,} pitches, {n_games:,} games, "
              f"{df.shape[1]} columns → {out} ({os.path.getsize(out)/1e6:.0f} MB) "
              f"in {(time.time()-t0)/60:.1f} min", flush=True)

    # Column manifest (handy for me): union of columns across saved seasons
    try:
        import pyarrow.parquet as pq
        cols = {}
        for f in sorted(os.listdir(OUT_DIR)):
            if f.endswith(".parquet"):
                s = pq.ParquetFile(os.path.join(OUT_DIR, f)).schema.names
                cols[f] = s
        with open(os.path.join(OUT_DIR, "COLUMNS.txt"), "w") as fh:
            for f, s in cols.items():
                fh.write(f"{f}: {len(s)} columns\n  " + ", ".join(s) + "\n")
        print(f"\nWrote {os.path.join(OUT_DIR, 'COLUMNS.txt')}")
    except Exception as e:
        print(f"(manifest skipped: {e})")


if __name__ == "__main__":
    main()
