"""
feed_extract.py — parse MLB StatsAPI live-feed JSON (gzipped, one per game) into
  (a) a per-pitch event table with the feed's own call codes/timestamps/coordinates, and
  (b) a challenge/review event table, detected generically (any playEvent or play with keys/text mentioning
      challenge/review/ABS/overturn/upheld/confirmed), so the exact 2026 encoding can be learned from the probe.
Then joins (a) to the Statcast per-pitch table on (game_pk, at_bat_number = atBatIndex+1, pitch_number = pitchNumber)
to produce `call_original` (feed pitch code before any review) vs `call_final` (Statcast description) — METHODS §2.1.

Usage:
    python3 feed_extract.py --feeds ../data/raw/feeds/2026 --out ../data/derived/feed_2026 [--limit 50]
    python3 feed_extract.py --probe-json ../data/raw/feeds/probe/778123.json      # inspect one game

Outputs: <out>_pitches.parquet, <out>_reviews.parquet, <out>_officials.csv, and a printed field census.
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import os
import re
from collections import Counter

import pandas as pd

KEYPAT = re.compile(r"review|challenge|abs|overturn|uphold|upheld|confirm", re.I)
TXTPAT = re.compile(r"challeng|overturn|upheld|confirmed|ABS", re.I)


def load(path):
    if path.endswith(".gz"):
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            return json.load(fh)
    with open(path) as fh:
        return json.load(fh)


def flatten(d, prefix="", out=None, depth=0):
    """Flatten nested dict (depth-limited) into dotted keys."""
    out = {} if out is None else out
    if depth > 4:
        return out
    for k, v in (d or {}).items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            flatten(v, key + ".", out, depth + 1)
        elif isinstance(v, list):
            out[key] = json.dumps(v)[:500]
        else:
            out[key] = v
    return out


def parse_game(js, keep_all_keys=False):
    gd = js.get("gameData", {}) or {}
    gpk = (js.get("gamePk") or (gd.get("game") or {}).get("pk"))
    live = js.get("liveData", {}) or {}
    plays = (live.get("plays", {}) or {}).get("allPlays", []) or []
    pitches, reviews = [], []
    for p in plays:
        ab = p.get("about", {}) or {}
        ab_idx = ab.get("atBatIndex")
        matchup = p.get("matchup", {}) or {}
        # play-level review objects
        for k, v in p.items():
            if KEYPAT.search(k) and v:
                reviews.append(dict(gamePk=gpk, atBatIndex=ab_idx, level="play", key=k, value=json.dumps(v)[:800],
                                    inning=ab.get("inning"), halfInning=ab.get("halfInning")))
        for ev in p.get("playEvents", []) or []:
            det = ev.get("details", {}) or {}
            cnt = ev.get("count", {}) or {}
            pdata = ev.get("pitchData", {}) or {}
            coords = pdata.get("coordinates", {}) or {}
            row = dict(gamePk=gpk, atBatIndex=ab_idx, at_bat_number=(ab_idx + 1) if ab_idx is not None else None,
                       eventIndex=ev.get("index"), pitchNumber=ev.get("pitchNumber"), isPitch=ev.get("isPitch"),
                       type=ev.get("type"), code=det.get("code"), call_code=(det.get("call") or {}).get("code"),
                       call_desc=(det.get("call") or {}).get("description"), description=det.get("description"),
                       event=det.get("event"), eventType=det.get("eventType"), isInPlay=det.get("isInPlay"),
                       isStrike=det.get("isStrike"), isBall=det.get("isBall"), hasReview=det.get("hasReview"),
                       balls=cnt.get("balls"), strikes=cnt.get("strikes"), outs=cnt.get("outs"),
                       startTime=ev.get("startTime"), endTime=ev.get("endTime"), playId=ev.get("playId"),
                       pX=coords.get("pX"), pZ=coords.get("pZ"), szTop=pdata.get("strikeZoneTop"), szBot=pdata.get("strikeZoneBottom"),
                       zone=pdata.get("zone"), inning=ab.get("inning"), halfInning=ab.get("halfInning"),
                       batter=(matchup.get("batter") or {}).get("id"), pitcher=(matchup.get("pitcher") or {}).get("id"))
            # generic detection of review/challenge material on the event
            hits = {k: v for k, v in flatten(ev).items() if KEYPAT.search(k)}
            txt = " ".join(str(x) for x in [det.get("description"), det.get("event"), det.get("eventType")] if x)
            if hits or TXTPAT.search(txt):
                reviews.append(dict(gamePk=gpk, atBatIndex=ab_idx, level="event", eventIndex=ev.get("index"),
                                    pitchNumber=ev.get("pitchNumber"), type=ev.get("type"), code=det.get("code"),
                                    description=det.get("description"), event=det.get("event"),
                                    inning=ab.get("inning"), halfInning=ab.get("halfInning"), keys=json.dumps(hits)[:1500],
                                    startTime=ev.get("startTime")))
            if keep_all_keys:
                row["_keys"] = ",".join(sorted(ev.keys()))
            pitches.append(row)
    officials = [(gpk, o.get("officialType"), (o.get("official") or {}).get("fullName"), (o.get("official") or {}).get("id"))
                 for o in ((live.get("boxscore", {}) or {}).get("officials", []) or [])]
    return pitches, reviews, officials


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feeds", default=None, help="directory of <gamePk>.json.gz")
    ap.add_argument("--out", default="feed_out")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--probe-json", default=None)
    args = ap.parse_args()

    if args.probe_json:
        js = load(args.probe_json)
        p, r, o = parse_game(js, keep_all_keys=True)
        dp_ = pd.DataFrame(p); dr = pd.DataFrame(r)
        print(f"{len(dp_)} events, {int(dp_['isPitch'].fillna(False).sum())} pitches, {len(dr)} review/challenge hits, officials={o}")
        print("event types:", Counter(dp_["type"]).most_common(8))
        print("pitch codes:", Counter(dp_.loc[dp_['isPitch'] == True, 'code']).most_common(12))
        print("call codes:", Counter(dp_["call_code"].dropna()).most_common(12))
        print("distinct event keys:", Counter(k for ks in dp_["_keys"].dropna() for k in ks.split(",")).most_common(40))
        if len(dr):
            print(dr.head(20).to_string()[:4000])
        return

    files = sorted(glob.glob(os.path.join(args.feeds, "*.json.gz")))
    if args.limit:
        files = files[:args.limit]
    P, R, O = [], [], []
    for i, f in enumerate(files, 1):
        try:
            p, r, o = parse_game(load(f))
            P.extend(p); R.extend(r); O.extend(o)
        except Exception as e:
            print(f"[warn] {f}: {e!r}")
        if i % 200 == 0:
            print(f"  {i}/{len(files)}")
    dp_ = pd.DataFrame(P); dr = pd.DataFrame(R); do = pd.DataFrame(O, columns=["gamePk", "officialType", "name", "id"])
    dp_.to_parquet(args.out + "_pitches.parquet", index=False); dr.to_parquet(args.out + "_reviews.parquet", index=False)
    do.to_csv(args.out + "_officials.csv", index=False)
    print(f"pitch events {len(dp_):,} (pitches {int(dp_['isPitch'].fillna(False).sum()):,}); review/challenge hits {len(dr):,}; games {dp_['gamePk'].nunique():,}")
    print("review hit types:", Counter(dr["type"].fillna("play")).most_common(10) if len(dr) else "none")
    print("top review descriptions:", Counter(dr["description"].dropna().str[:80]).most_common(8) if len(dr) else "none")


if __name__ == "__main__":
    main()
