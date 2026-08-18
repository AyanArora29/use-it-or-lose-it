"""
challenges_extract.py — build the 2026 ABS challenge-event table and a per-pitch geometry table from StatsAPI feeds.

Encoding (verified on 1,855 feeds through 2026-08-17; METHODS §2.1). An ABS ball/strike challenge is a review record with
reviewType == "MJ" ("challenged (pitch result)"); every other reviewType (MA tag play, MF play at 1st, MI hit-by-pitch,
NH umpire home-run review, ...) is a replay review, not an ABS challenge. The record lives in one of three places:
  (1) on the pitch event:  playEvent.reviewDetails = {isOverturned, inProgress, reviewType, challengeTeamId, player{id,fullName}}
      — used when the plate appearance continues after the challenge;
  (2) on the play:  play.reviewDetails (same shape) — used when the challenged pitch ENDS the plate appearance
      (strikeout / walk, overturned or confirmed); the challenge belongs to the LAST pitch of the play; the play's
      result.description reads "<name> challenged (pitch result), call on the field was overturned|confirmed: ...";
  (3) inside reviewDetails.additionalReviews[] (either level) when a play carries more than one review.
Sum of MJ records over the three places reconciles with gameData.absChallenges {away/home: usedSuccessful, usedFailed}.
details.call on the pitch = the FINAL (post-challenge) call, so call_original = flip(call_final) if isOverturned.
pitchData.strikeZoneTop/Bottom = ABS zone edges (0.535H / 0.27H of certified height H); coordinates pX,pZ are at the
front of the plate (y = 17/12 ft) with the full 9-parameter trajectory (x0, y0=50, z0, vX0, vY0, vZ0, aX, aY, aZ).
Challenger role = pitcher if player == matchup.pitcher, else catcher if the challenging team is fielding, else batter.

Usage:
    python3 challenges_extract.py --feeds <dir with *.json or *.json.gz> --out <prefix> [--limit N]
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
ABS_TYPE = "MJ"


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


def _reviews(rd):
    """Flatten a reviewDetails object (+ additionalReviews) into a list of review dicts."""
    out = []
    if not rd:
        return out
    base = {k: v for k, v in rd.items() if k != "additionalReviews"}
    out.append(base)
    for extra in rd.get("additionalReviews") or []:
        out.extend(_reviews(extra))
    return out


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
    pitches = []
    warn = []
    prev_half_key = None
    outs_at_play_start = 0
    for p in plays:
        ab = p.get("about", {}) or {}
        ab_idx = ab.get("atBatIndex"); inning = ab.get("inning"); half = ab.get("halfInning")
        half_key = (inning, half)
        if half_key != prev_half_key:
            outs_at_play_start = 0
            prev_half_key = half_key
        bat_home = 1 if half == "bottom" else 0
        mu = p.get("matchup", {}) or {}
        batter = (mu.get("batter") or {}).get("id"); pitcher = (mu.get("pitcher") or {}).get("id")
        stand = (mu.get("batSide") or {}).get("code"); pthrows = (mu.get("pitchHand") or {}).get("code")
        res = p.get("result", {}) or {}
        # ABS challenges recorded at the play level belong to the last pitch of the play
        play_abs = [r for r in _reviews(p.get("reviewDetails")) if r.get("reviewType") == ABS_TYPE]
        evs = p.get("playEvents", []) or []
        pitch_events = [ev for ev in evs if ev.get("isPitch")]
        last_pitch_idx = pitch_events[-1].get("index") if pitch_events else None
        prev_b = prev_s = 0
        cur_outs = outs_at_play_start
        rows_this_play = []
        for ev in evs:
            cnt = ev.get("count", {}) or {}
            if not ev.get("isPitch"):
                if cnt.get("outs") is not None:
                    cur_outs = cnt.get("outs")
                if cnt.get("balls") is not None:
                    prev_b, prev_s = cnt.get("balls", prev_b), cnt.get("strikes", prev_s)
                continue
            det = ev.get("details", {}) or {}
            pdata = ev.get("pitchData", {}) or {}
            co = pdata.get("coordinates", {}) or {}
            call_final = (det.get("call") or {}).get("code")
            ev_abs = [r for r in _reviews(ev.get("reviewDetails")) if r.get("reviewType") == ABS_TYPE]
            other_types = [r.get("reviewType") for r in _reviews(ev.get("reviewDetails")) if r.get("reviewType") != ABS_TYPE]
            level = None
            rv = None
            if ev_abs:
                rv, level = ev_abs[0], "event"
                if len(ev_abs) > 1:
                    warn.append(f"{gpk}: pitch event {ab_idx}/{ev.get('index')} has {len(ev_abs)} ABS reviews")
            elif play_abs and ev.get("index") == last_pitch_idx:
                rv, level = play_abs[0], "play"
                if len(play_abs) > 1:
                    warn.append(f"{gpk}: play {ab_idx} has {len(play_abs)} play-level ABS reviews")
                if call_final not in ("B", "C"):
                    warn.append(f"{gpk}: play-level ABS review on play {ab_idx} but last pitch call={call_final}")
            overturned = bool(rv and rv.get("isOverturned"))
            if rv and call_final in ("B", "C"):
                call_original = {"B": "C", "C": "B"}[call_final] if overturned else call_final
            else:
                call_original = call_final
            row = dict(gamePk=gpk, game_date=date, atBatIndex=ab_idx, at_bat_number=(ab_idx + 1) if ab_idx is not None else None,
                       pitchNumber=ev.get("pitchNumber"), eventIndex=ev.get("index"), inning=inning, bat_home=bat_home,
                       batter=batter, pitcher=pitcher, stand=stand, p_throws=pthrows,
                       balls_pre=prev_b, strikes_pre=prev_s, outs_pre=cur_outs,
                       balls_post=cnt.get("balls"), strikes_post=cnt.get("strikes"), outs_post=cnt.get("outs"),
                       code=det.get("code"), call_final=call_final, call_original=call_original, description=det.get("description"),
                       is_called=int(call_final in ("B", "C") and det.get("code") in ("B", "C", "*B")),
                       pX=co.get("pX"), pZ=co.get("pZ"), x0=co.get("x0"), y0=co.get("y0"), z0=co.get("z0"),
                       vX0=co.get("vX0"), vY0=co.get("vY0"), vZ0=co.get("vZ0"), aX=co.get("aX"), aY=co.get("aY"), aZ=co.get("aZ"),
                       szTop=pdata.get("strikeZoneTop"), szBot=pdata.get("strikeZoneBottom"),
                       szWidth=pdata.get("strikeZoneWidth"), szDepth=pdata.get("strikeZoneDepth"),
                       zone=pdata.get("zone"), startTime=ev.get("startTime"), endTime=ev.get("endTime"),
                       pa_event=res.get("event"), pa_last_pitch=int(ev.get("index") == last_pitch_idx),
                       challenged=int(rv is not None), review_level=level, isOverturned=int(overturned),
                       challengeTeamId=(rv or {}).get("challengeTeamId"), challenger_id=((rv or {}).get("player") or {}).get("id"),
                       challenger_name=((rv or {}).get("player") or {}).get("fullName"), reviewType=(rv or {}).get("reviewType"),
                       other_reviews=",".join(other_types) if other_types else None, hasReview=det.get("hasReview"))
            rows_this_play.append(row)
            if cnt.get("balls") is not None:
                prev_b, prev_s = cnt.get("balls", prev_b), cnt.get("strikes", prev_s)
            if cnt.get("outs") is not None:
                cur_outs = cnt.get("outs")
        if play_abs and last_pitch_idx is None:
            warn.append(f"{gpk}: play-level ABS review on play {ab_idx} with no pitch events")
        pitches.extend(rows_this_play)
        pc = p.get("count", {}) or {}
        outs_at_play_start = pc.get("outs", cur_outs) if pc.get("outs") is not None else cur_outs
    df = pd.DataFrame(pitches)
    if len(df):
        fld_team = np.where(df["bat_home"] == 1, away_id, home_id)
        bat_team = np.where(df["bat_home"] == 1, home_id, away_id)
        df["challenger_side"] = np.where(df["challengeTeamId"].isna(), None,
                                         np.where(df["challengeTeamId"] == bat_team, "bat", np.where(df["challengeTeamId"] == fld_team, "fld", "?")))
        df["role"] = np.where(df["challenged"] == 0, None,
                              np.where(df["challenger_side"] == "bat", "batter",
                                       np.where(df["challenger_id"] == df["pitcher"], "pitcher", "catcher")))
        ok = df[["pX", "pZ", "vX0", "vY0", "vZ0", "aX", "aY", "aZ"]].notna().all(axis=1).values
        xm = np.full(len(df), np.nan); zm = np.full(len(df), np.nan)
        if ok.any():
            xm[ok], zm[ok] = propagate_to_midpoint(*[df.loc[ok, c].values.astype(float) for c in ["pX", "pZ", "vX0", "vY0", "vZ0", "aX", "aY", "aZ"]])
        df["x_mid"] = xm; df["z_mid"] = zm
        df["height_in"] = df["szTop"] * 12 / TOP_FRAC
        df["d_in"] = signed_miss_from_edges(df["x_mid"], df["z_mid"], df["szBot"], df["szTop"], expand=True)
        df["d_in_center"] = signed_miss_from_edges(df["x_mid"], df["z_mid"], df["szBot"], df["szTop"], expand=False)
        df["d_in_front"] = signed_miss_from_edges(df["pX"], df["pZ"], df["szBot"], df["szTop"], expand=True)
        df["orig_wrong"] = np.where(df["call_original"] == "C", df["d_in"] > 0, np.where(df["call_original"] == "B", df["d_in"] <= 0, np.nan))
        df["hp_umpire"] = officials.get("Home Plate")
        df["away_id"] = away_id; df["home_id"] = home_id
    n_ch = int(df["challenged"].sum()) if len(df) else 0
    game_row = dict(gamePk=gpk, game_date=date, away_id=away_id, home_id=home_id, hp_umpire=officials.get("Home Plate"),
                    away_usedSuccessful=(absc.get("away") or {}).get("usedSuccessful"), away_usedFailed=(absc.get("away") or {}).get("usedFailed"),
                    away_remaining=(absc.get("away") or {}).get("remaining"), home_usedSuccessful=(absc.get("home") or {}).get("usedSuccessful"),
                    home_usedFailed=(absc.get("home") or {}).get("usedFailed"), home_remaining=(absc.get("home") or {}).get("remaining"),
                    n_pitches=len(df), n_challenges=n_ch,
                    n_challenges_event=int((df["review_level"] == "event").sum()) if len(df) else 0,
                    n_challenges_play=int((df["review_level"] == "play").sum()) if len(df) else 0,
                    game_status=((gd.get("status") or {}).get("detailedState")))
    return df, game_row, warn


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feeds", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    files = sorted(glob.glob(os.path.join(args.feeds, "*.json.gz")) + glob.glob(os.path.join(args.feeds, "*.json")))
    if args.limit:
        files = files[:args.limit]
    P, G, W = [], [], []
    for i, f in enumerate(files, 1):
        try:
            df, g, w = parse_game(load(f)); P.append(df); G.append(g); W.extend(w)
        except Exception as e:
            print(f"[warn] {f}: {e!r}")
        if i % 200 == 0:
            print(f"  {i}/{len(files)}", flush=True)
    pitches = pd.concat(P, ignore_index=True); games = pd.DataFrame(G)
    chal = pitches[pitches["challenged"] == 1].copy()
    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    pitches.to_parquet(args.out + "_pitches.parquet", index=False)
    chal.to_parquet(args.out + "_challenges.parquet", index=False)
    games.to_csv(args.out + "_games.csv", index=False)
    for w in W[:20]:
        print("[note]", w)
    if len(W) > 20:
        print(f"[note] ... {len(W)} notes total")
    print(f"games {len(games):,} | pitches {len(pitches):,} | called {int(pitches['is_called'].sum()):,} | challenges {len(chal):,} "
          f"(event-level {int((chal['review_level']=='event').sum()):,}, play-level {int((chal['review_level']=='play').sum()):,}) "
          f"| overturned {chal['isOverturned'].mean() if len(chal) else float('nan'):.3f}")
    if len(chal):
        print("by role:", chal.groupby("role")["isOverturned"].agg(["size", "mean"]).round(3).to_dict())
        ok = chal["d_in"].notna()
        agree = ((chal.loc[ok, "orig_wrong"].astype(bool)) == (chal.loc[ok, "isOverturned"] == 1)).mean()
        band = chal.loc[ok, "d_in"].abs() >= 0.5
        agree_b = ((chal.loc[ok & band, "orig_wrong"].astype(bool)) == (chal.loc[ok & band, "isOverturned"] == 1)).mean()
        print(f"zone agreement with ABS verdicts: {agree:.4f} (all, n={int(ok.sum())}) / {agree_b:.4f} (|d|>=0.5 in, n={int((ok&band).sum())})")
        s = games[["away_usedSuccessful", "away_usedFailed", "home_usedSuccessful", "home_usedFailed"]].sum().sum()
        summ = games[["away_usedSuccessful", "away_usedFailed", "home_usedSuccessful", "home_usedFailed"]].sum(axis=1)
        bad = games[games["n_challenges"] != summ]
        print(f"reconciliation: events {len(chal)} vs gameData summary {int(s)}; games not reconciling: {len(bad)}")
        if len(bad):
            print(bad[["gamePk", "game_date", "n_challenges", "n_challenges_event", "n_challenges_play"]].head(10).to_string())


if __name__ == "__main__":
    main()
