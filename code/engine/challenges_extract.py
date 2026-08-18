"""
challenges_extract.py — build the 2026 ABS challenge-event table and a per-pitch geometry table from StatsAPI feeds.

Encoding (verified on 2026-08-16 feeds, METHODS §2.1): a challenged pitch carries
    playEvent.reviewDetails = {isOverturned, inProgress, reviewType: "MJ", challengeTeamId, player{id, fullName}}
    playEvent.details.call / description / count  = the FINAL (post-challenge) call and post-pitch count
    pitchData.coordinates {pX,pZ (front of plate), x0,y0=50,z0, vX0,vY0,vZ0, aX,aY,aZ}
    pitchData.strikeZoneTop/Bottom = ABS zone edges (0.535H / 0.27H, certified height H), strikeZoneWidth=17, Depth=8.5
    gameData.absChallenges = {away/home: usedSuccessful, usedFailed, remaining}
So call_original = flip(call_final) if isOverturned else call_final; challenger role = pitcher if player == matchup.pitcher,
else catcher if on the fielding team, else batter.

Usage:
    python3 challenges_extract.py --feeds <dir with *.json or *.json.gz> --out <prefix>
Outputs: <prefix>_challenges.parquet, <prefix>_pitches.parquet (all pitches, geometry + d), <prefix>_games.csv
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "code"))
from abs_zone import propagate_to_midpoint, BALL_RADIUS, PLATE_HALF_WIDTH  # noqa: E402

TOP_FRAC, BOT_FRAC = 0.535, 0.27


def load(path):
    if path.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    with open(path) as fh:
        return json.load(fh)


def signed_miss_from_edges(x, z, z_lo, z_hi, expand=True):
    """Signed distance (in) from ball centre to the ABS rectangle given zone edges in feet; negative inside."""
    r = BALL_RADIUS if expand else 0.0
    x_lo, x_hi = -(PLATE_HALF_WIDTH + r), (PLATE_HALF_WIDTH + r)
    zl, zh = z_lo - r, z_hi + r
    dx = np.maximum(np.maximum(x_lo - x, x - x_hi), 0.0)
    dz = np.maximum(np.maximum(zl - z, z - zh), 0.0)
    outside = np.sqrt(dx * dx + dz * dz)
    inside = np.minimum(np.minimum(x - x_lo, x_hi - x), np.minimum(z - zl, zh - z))
    return np.where(outside > 0, outside, -inside) * 12.0


def parse_game(js):
    gd = js.get("gameData", {}) or {}
    gpk = js.get("gamePk") or (gd.get("game") or {}).get("pk")
    date = (gd.get("datetime") or {}).get("officialDate")
    teams = gd.get("teams", {}) or {}
    away_id, home_id = (teams.get("away") or {}).get("id"), (teams.get("home") or {}).get("id")
    absc = gd.get("absChallenges") or {}
    live = js.get("liveData", {}) or {}
    plays = (live.get("plays", {}) or {}).get("allPlays", []) or []
    officials = {o.get("officialType"): (o.get("official") or {}).get("fullName") for o in ((live.get("boxscore", {}) or {}).get("officials", []) or [])}
    pitches, chal = [], []
    for p in plays:
        ab = p.get("about", {}) or {}
        ab_idx = ab.get("atBatIndex"); inning = ab.get("inning"); half = ab.get("halfInning")
        bat_home = 1 if half == "bottom" else 0
        mu = p.get("matchup", {}) or {}
        batter = (mu.get("batter") or {}).get("id"); pitcher = (mu.get("pitcher") or {}).get("id")
        stand = (mu.get("batSide") or {}).get("code"); pthrows = (mu.get("pitchHand") or {}).get("code")
        prev_b = prev_s = 0
        for ev in p.get("playEvents", []) or []:
            if not ev.get("isPitch"):
                continue
            det = ev.get("details", {}) or {}
            cnt = ev.get("count", {}) or {}
            pdata = ev.get("pitchData", {}) or {}
            co = pdata.get("coordinates", {}) or {}
            call_final = (det.get("call") or {}).get("code")
            rv = ev.get("reviewDetails") or None
            overturned = bool(rv and rv.get("isOverturned"))
            if rv and call_final in ("B", "C"):
                call_original = {"B": "C", "C": "B"}[call_final] if overturned else call_final
            else:
                call_original = call_final
            row = dict(gamePk=gpk, game_date=date, atBatIndex=ab_idx, at_bat_number=(ab_idx + 1) if ab_idx is not None else None,
                       pitchNumber=ev.get("pitchNumber"), eventIndex=ev.get("index"), inning=inning, bat_home=bat_home,
                       batter=batter, pitcher=pitcher, stand=stand, p_throws=pthrows,
                       balls_pre=prev_b, strikes_pre=prev_s, outs_pre=None,
                       balls_post=cnt.get("balls"), strikes_post=cnt.get("strikes"), outs_post=cnt.get("outs"),
                       code=det.get("code"), call_final=call_final, call_original=call_original, description=det.get("description"),
                       is_called=int(call_final in ("B", "C") and det.get("code") in ("B", "C", "*B")),
                       pX=co.get("pX"), pZ=co.get("pZ"), x0=co.get("x0"), y0=co.get("y0"), z0=co.get("z0"),
                       vX0=co.get("vX0"), vY0=co.get("vY0"), vZ0=co.get("vZ0"), aX=co.get("aX"), aY=co.get("aY"), aZ=co.get("aZ"),
                       szTop=pdata.get("strikeZoneTop"), szBot=pdata.get("strikeZoneBottom"),
                       szWidth=pdata.get("strikeZoneWidth"), szDepth=pdata.get("strikeZoneDepth"),
                       zone=pdata.get("zone"), startTime=ev.get("startTime"), endTime=ev.get("endTime"),
                       challenged=int(rv is not None), isOverturned=int(overturned),
                       challengeTeamId=(rv or {}).get("challengeTeamId"), challenger_id=((rv or {}).get("player") or {}).get("id"),
                       challenger_name=((rv or {}).get("player") or {}).get("fullName"), reviewType=(rv or {}).get("reviewType"))
            # outs before the pitch: outs_post minus outs made on this pitch is not directly known; use play-level start
            row["outs_pre"] = None
            pitches.append(row)
            prev_b, prev_s = cnt.get("balls", prev_b), cnt.get("strikes", prev_s)
    df = pd.DataFrame(pitches)
    if len(df):
        # outs before the pitch: the play's first pitch starts with the outs at PA start = previous play's outs_post; approximate
        # with the minimum outs_post within the PA (outs cannot decrease within a PA)
        df["outs_pre"] = df.groupby("atBatIndex")["outs_post"].transform("min")
        # challenger role
        fld_team = np.where(df["bat_home"] == 1, away_id, home_id)
        bat_team = np.where(df["bat_home"] == 1, home_id, away_id)
        df["challenger_side"] = np.where(df["challengeTeamId"].isna(), None,
                                         np.where(df["challengeTeamId"] == bat_team, "bat", np.where(df["challengeTeamId"] == fld_team, "fld", "?")))
        df["role"] = np.where(df["challenged"] == 0, None,
                              np.where(df["challenger_side"] == "bat", "batter",
                                       np.where(df["challenger_id"] == df["pitcher"], "pitcher", "catcher")))
        # geometry: propagate front-plate pX/pZ to the plate midpoint; ABS zone from szTop/szBot; implied height
        ok = df[["pX", "pZ", "vX0", "vY0", "vZ0", "aX", "aY", "aZ"]].notna().all(axis=1).values
        xm = np.full(len(df), np.nan); zm = np.full(len(df), np.nan)
        if ok.any():
            xm[ok], zm[ok] = propagate_to_midpoint(*[df.loc[ok, c].values for c in ["pX", "pZ", "vX0", "vY0", "vZ0", "aX", "aY", "aZ"]])
        df["x_mid"] = xm; df["z_mid"] = zm
        df["height_in"] = df["szTop"] * 12 / TOP_FRAC
        df["d_in"] = signed_miss_from_edges(df["x_mid"], df["z_mid"], df["szBot"], df["szTop"], expand=True)
        df["d_in_center"] = signed_miss_from_edges(df["x_mid"], df["z_mid"], df["szBot"], df["szTop"], expand=False)
        df["d_in_front"] = signed_miss_from_edges(df["pX"], df["pZ"], df["szBot"], df["szTop"], expand=True)
        # was the ORIGINAL call wrong under our zone?  strike wrong iff d>0 ; ball wrong iff d<=0
        df["orig_wrong"] = np.where(df["call_original"] == "C", df["d_in"] > 0, np.where(df["call_original"] == "B", df["d_in"] <= 0, np.nan))
        df["hp_umpire"] = officials.get("Home Plate")
        df["away_id"] = away_id; df["home_id"] = home_id
    game_row = dict(gamePk=gpk, game_date=date, away_id=away_id, home_id=home_id, hp_umpire=officials.get("Home Plate"),
                    away_usedSuccessful=(absc.get("away") or {}).get("usedSuccessful"), away_usedFailed=(absc.get("away") or {}).get("usedFailed"),
                    away_remaining=(absc.get("away") or {}).get("remaining"), home_usedSuccessful=(absc.get("home") or {}).get("usedSuccessful"),
                    home_usedFailed=(absc.get("home") or {}).get("usedFailed"), home_remaining=(absc.get("home") or {}).get("remaining"),
                    n_pitches=len(df), n_challenges=int(df["challenged"].sum()) if len(df) else 0)
    return df, game_row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feeds", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    files = sorted(glob.glob(os.path.join(args.feeds, "*.json.gz")) + glob.glob(os.path.join(args.feeds, "*.json")))
    if args.limit:
        files = files[:args.limit]
    P, G = [], []
    for i, f in enumerate(files, 1):
        try:
            df, g = parse_game(load(f)); P.append(df); G.append(g)
        except Exception as e:
            print(f"[warn] {f}: {e!r}")
        if i % 200 == 0:
            print(f"  {i}/{len(files)}", flush=True)
    pitches = pd.concat(P, ignore_index=True); games = pd.DataFrame(G)
    chal = pitches[pitches["challenged"] == 1].copy()
    pitches.to_parquet(args.out + "_pitches.parquet", index=False)
    chal.to_parquet(args.out + "_challenges.parquet", index=False)
    games.to_csv(args.out + "_games.csv", index=False)
    print(f"games {len(games):,} | pitches {len(pitches):,} | called {int(pitches['is_called'].sum()):,} | challenges {len(chal):,} "
          f"| overturned {chal['isOverturned'].mean() if len(chal) else float('nan'):.3f}")
    if len(chal):
        print("by role:", chal.groupby("role")["isOverturned"].agg(["size", "mean"]).round(3).to_dict())
        # zone-reconstruction agreement: an overturn means the ORIGINAL call was wrong; upheld means it was right
        ok = chal["d_in"].notna()
        agree = ((chal.loc[ok, "orig_wrong"].astype(bool)) == (chal.loc[ok, "isOverturned"] == 1)).mean()
        band = chal.loc[ok, "d_in"].abs() >= 0.5
        agree_b = ((chal.loc[ok & band, "orig_wrong"].astype(bool)) == (chal.loc[ok & band, "isOverturned"] == 1)).mean()
        print(f"zone agreement with ABS verdicts: {agree:.3f} (all) / {agree_b:.3f} (|d|>=0.5 in, n={int((ok&band).sum())})")
        # reconciliation with gameData.absChallenges
        s = games[["away_usedSuccessful", "away_usedFailed", "home_usedSuccessful", "home_usedFailed"]].sum().sum()
        print(f"reconciliation: events {len(chal)} vs gameData summary {int(s)}")


if __name__ == "__main__":
    main()
