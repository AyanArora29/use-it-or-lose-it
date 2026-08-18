#!/usr/bin/env python3
"""
02_fetch_statsapi_feeds.py — download MLB StatsAPI "live feed" JSON for every game of a season.
Standard library only (no pip installs).

Why: the feed carries per-pitch timestamps, umpire assignments, and (in 2026) the ABS challenge
events, none of which are in the Statcast CSV.

Output:
    <repo>/data/raw/feeds/<season>/<gamePk>.json.gz        one gzipped feed per game (resumable)
    <repo>/data/raw/feeds/games_<season>.csv                one row per game (date, teams, umpires, venue,
                                                             #pitch events, #'challenge' mentions, status)
    <repo>/data/raw/feeds/probe/                            (--probe) raw JSON + a text summary of how the
                                                             feed encodes pitches / reviews / challenges

Usage:
    python3 02_fetch_statsapi_feeds.py --probe                    # ~1 min: 3 recent games, uncompressed, + summary
    python3 02_fetch_statsapi_feeds.py --season 2026              # regular season 2026 (default sport 1 = MLB)
    python3 02_fetch_statsapi_feeds.py --season 2025 --game-types S      # 2025 spring training (ABS trial)
    python3 02_fetch_statsapi_feeds.py --season 2025 --sport 11          # Triple-A 2025 (full challenge system)
    python3 02_fetch_statsapi_feeds.py --season 2026 --workers 4         # be gentler on the API
"""
import argparse
import concurrent.futures as cf
import csv
import datetime as dt
import gzip
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
def _find_root(start):
    p = start
    for _ in range(4):
        if any(os.path.exists(os.path.join(p, m)) for m in ("requirements.txt", "Instruction", "METHODS.md")):
            return p
        p = os.path.dirname(p)
    return os.path.dirname(start)
ROOT = os.environ.get("ABS_ROOT") or _find_root(HERE)
FEED_DIR = os.path.join(ROOT, "data", "raw", "feeds")
API = "https://statsapi.mlb.com/api"
UA = {"User-Agent": "Mozilla/5.0 (research; SSAC27 open-data project)"}


def get_json(url, retries=4, timeout=60):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionError) as e:
            last = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"GET failed after {retries} tries: {url} ({last!r})")


def schedule(season, sport, game_types, start=None, end=None):
    """Return list of (gamePk, officialDate, gameType, status, away, home)."""
    start = start or f"{season}-02-15"
    end = end or (f"{season}-11-20" if season < dt.date.today().year else (dt.date.today() - dt.timedelta(days=1)).isoformat())
    games = []
    # StatsAPI caps long ranges; walk month by month.
    d0 = dt.date.fromisoformat(start)
    d1 = dt.date.fromisoformat(end)
    cur = d0
    while cur <= d1:
        nxt = min(cur + dt.timedelta(days=30), d1)
        q = urllib.parse.urlencode({
            "sportId": sport, "startDate": cur.isoformat(), "endDate": nxt.isoformat(),
            "gameTypes": ",".join(game_types), "hydrate": "team",
        })
        js = get_json(f"{API}/v1/schedule?{q}")
        for day in js.get("dates", []):
            for g in day.get("games", []):
                games.append((
                    g["gamePk"], g.get("officialDate", day.get("date")), g.get("gameType"),
                    (g.get("status") or {}).get("detailedState"),
                    (((g.get("teams") or {}).get("away") or {}).get("team") or {}).get("name"),
                    (((g.get("teams") or {}).get("home") or {}).get("team") or {}).get("name"),
                ))
        cur = nxt + dt.timedelta(days=1)
    # de-dup (doubleheaders are distinct gamePks; schedule pages can overlap by a day)
    seen, out = set(), []
    for g in games:
        if g[0] not in seen:
            seen.add(g[0]); out.append(g)
    return out


def summarize_feed(js):
    """Cheap per-game summary: umpires, venue, #pitch events, #challenge mentions."""
    live = js.get("liveData", {}) or {}
    plays = (live.get("plays", {}) or {}).get("allPlays", []) or []
    n_pitch = 0
    n_events = 0
    challenge_mentions = 0
    review_keys = set()
    for p in plays:
        if p.get("reviewDetails"):
            review_keys.add("play.reviewDetails")
        for ev in p.get("playEvents", []) or []:
            n_events += 1
            if ev.get("isPitch"):
                n_pitch += 1
            if ev.get("reviewDetails"):
                review_keys.add("event.reviewDetails")
    text = json.dumps(js)
    challenge_mentions = len(re.findall(r"[Cc]hallenge", text))
    box = (live.get("boxscore", {}) or {})
    umps = {}
    for o in box.get("officials", []) or []:
        umps[o.get("officialType", "?")] = (o.get("official") or {}).get("fullName")
    gd = js.get("gameData", {}) or {}
    venue = (gd.get("venue") or {}).get("name")
    return {
        "n_plays": len(plays), "n_events": n_events, "n_pitch_events": n_pitch,
        "challenge_mentions": challenge_mentions,
        "review_keys": "|".join(sorted(review_keys)),
        "hp_umpire": umps.get("Home Plate"), "ump_1b": umps.get("First Base"),
        "ump_2b": umps.get("Second Base"), "ump_3b": umps.get("Third Base"),
        "venue": venue,
        "abstract_state": ((gd.get("status") or {}).get("abstractGameState")),
    }


def fetch_one(game, season_dir, force=False):
    gpk = game[0]
    out = os.path.join(season_dir, f"{gpk}.json.gz")
    if os.path.exists(out) and not force:
        try:
            with gzip.open(out, "rt", encoding="utf-8") as fh:
                js = json.load(fh)
            return gpk, "cached", summarize_feed(js)
        except Exception:
            pass  # corrupt -> re-download
    js = get_json(f"{API}/v1.1/game/{gpk}/feed/live")
    tmp = out + ".tmp"
    with gzip.open(tmp, "wt", encoding="utf-8") as fh:
        json.dump(js, fh)
    os.replace(tmp, out)
    return gpk, "downloaded", summarize_feed(js)


def probe(sport):
    """Grab 3 recent completed games, save raw JSON, and write a summary of the event structure."""
    pdir = os.path.join(FEED_DIR, "probe")
    os.makedirs(pdir, exist_ok=True)
    today = dt.date.today()
    games = schedule(today.year, sport, ["R"], start=(today - dt.timedelta(days=10)).isoformat(),
                     end=(today - dt.timedelta(days=1)).isoformat())
    games = [g for g in games if (g[3] or "").startswith("Final")][-3:]
    lines = []
    for g in games:
        js = get_json(f"{API}/v1.1/game/{g[0]}/feed/live")
        with open(os.path.join(pdir, f"{g[0]}.json"), "w") as fh:
            json.dump(js, fh, indent=1)
        s = summarize_feed(js)
        lines.append(f"\n### game {g[0]} {g[1]} {g[4]} @ {g[5]} : {s}")
        # enumerate event types / details.event values and any key containing challenge/abs/review
        plays = js["liveData"]["plays"]["allPlays"]
        types, events, calls, keys_hit = {}, {}, {}, {}
        for p in plays:
            for k in p.keys():
                if re.search(r"review|challenge|abs", k, re.I):
                    keys_hit[f"play.{k}"] = keys_hit.get(f"play.{k}", 0) + 1
            for ev in p.get("playEvents", []):
                t = ev.get("type"); types[t] = types.get(t, 0) + 1
                d = ev.get("details", {}) or {}
                e = d.get("event") or d.get("eventType");
                if e: events[e] = events.get(e, 0) + 1
                c = (d.get("call") or {}).get("description")
                if c: calls[c] = calls.get(c, 0) + 1
                for k in list(ev.keys()) + [f"details.{k}" for k in d.keys()]:
                    if re.search(r"review|challenge|abs|overturn|uphold|confirm", k, re.I):
                        keys_hit[f"event.{k}"] = keys_hit.get(f"event.{k}", 0) + 1
                desc = d.get("description") or ""
                if re.search(r"challenge|ABS|overturn|upheld|confirmed", desc, re.I):
                    lines.append(f"  event text: {desc[:200]}")
        lines.append(f"  playEvent types: {types}")
        lines.append(f"  details.event values (top 15): {dict(sorted(events.items(), key=lambda x:-x[1])[:15])}")
        lines.append(f"  call descriptions: {calls}")
        lines.append(f"  keys mentioning review/challenge/abs: {keys_hit}")
        # keys of one pitch event, for reference
        for p in plays:
            for ev in p.get("playEvents", []):
                if ev.get("isPitch"):
                    lines.append(f"  sample pitch event keys: {sorted(ev.keys())}")
                    lines.append(f"  sample pitch details keys: {sorted((ev.get('details') or {}).keys())}")
                    lines.append(f"  sample pitchData keys: {sorted((ev.get('pitchData') or {}).keys())}")
                    break
            else:
                continue
            break
        # any string mentioning 'challenge' anywhere in the doc (first 8)
        hits = re.findall(r'"([^"]{0,60}[Cc]hallenge[^"]{0,120})"', json.dumps(js))
        lines.append(f"  raw 'challenge' strings (up to 8): {hits[:8]}")
    with open(os.path.join(pdir, "probe_summary.txt"), "w") as fh:
        fh.write("\n".join(lines))
    print("\n".join(lines))
    print(f"\nProbe written to {pdir}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--sport", type=int, default=1, help="1=MLB, 11=Triple-A")
    ap.add_argument("--game-types", nargs="*", default=["R"], help="R regular, S spring, P/D/L/W/F postseason")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    os.makedirs(FEED_DIR, exist_ok=True)
    if args.probe:
        probe(args.sport)
        return

    tag = f"{args.season}" if args.sport == 1 else f"{args.season}_sport{args.sport}"
    if args.game_types != ["R"]:
        tag += "_" + "".join(args.game_types)
    season_dir = os.path.join(FEED_DIR, tag)
    os.makedirs(season_dir, exist_ok=True)

    print(f"Fetching schedule: season={args.season} sport={args.sport} types={args.game_types} ...", flush=True)
    games = schedule(args.season, args.sport, args.game_types)
    games = [g for g in games if (g[3] or "").startswith("Final") or (g[3] or "") in ("Completed Early", "Game Over")]
    print(f"{len(games)} completed games. Downloading to {season_dir} with {args.workers} workers ...", flush=True)

    rows, n_dl, n_cached, errs = [], 0, 0, []
    t0 = time.time()
    with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(fetch_one, g, season_dir, args.force): g for g in games}
        for i, fut in enumerate(cf.as_completed(futs), 1):
            g = futs[fut]
            try:
                gpk, how, s = fut.result()
                n_dl += how == "downloaded"; n_cached += how == "cached"
                rows.append({"gamePk": gpk, "date": g[1], "gameType": g[2], "status": g[3],
                             "away": g[4], "home": g[5], **s})
            except Exception as e:
                errs.append((g[0], repr(e)))
            if i % 100 == 0 or i == len(games):
                print(f"  {i}/{len(games)}  downloaded={n_dl} cached={n_cached} errors={len(errs)}  "
                      f"{(time.time()-t0)/60:.1f} min", flush=True)

    rows.sort(key=lambda r: (r["date"], r["gamePk"]))
    out_csv = os.path.join(FEED_DIR, f"games_{tag}.csv")
    if rows:
        with open(out_csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    print(f"\nWrote {out_csv} ({len(rows)} games). Errors: {len(errs)}")
    for e in errs[:10]:
        print("  ", e)
    tot = sum(r["challenge_mentions"] for r in rows)
    print(f"Total 'challenge' mentions across feeds: {tot} (if this is ~0 for 2026, tell me — challenges live elsewhere)")


if __name__ == "__main__":
    main()
