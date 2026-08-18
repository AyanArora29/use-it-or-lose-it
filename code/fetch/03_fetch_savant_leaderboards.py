#!/usr/bin/env python3
"""
03_fetch_savant_leaderboards.py — download Baseball Savant leaderboards / pages we need.
Standard library only.

Saves into <repo>/data/raw/savant/:
    abs_challenges_<role>_<level>_<gametype>_<year>.csv   ABS challenge leaderboards (MLB 2026, AAA 2025, ST 2025)
    abs_dashboard_<level>_<year>.html                     ABS dashboard page (I'll mine embedded data/links)
    abs_metrics_documentation.html
    pitch_tempo_<type>_<year>.csv                         Pitch tempo leaderboards 2015–2026 (hedge project)
    catcher_framing_<year>.csv                            Catcher framing 2015–2026
    _download_log.csv                                     what worked / what didn't (send me this if anything fails)

Usage:  python3 03_fetch_savant_leaderboards.py
"""
import csv
import datetime as dt
import os
import time
import urllib.error
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
OUT = os.path.join(ROOT, "data", "raw", "savant")
UA = {"User-Agent": "Mozilla/5.0 (research; SSAC27 open-data project)"}
BASE = "https://baseballsavant.mlb.com"
THIS_YEAR = dt.date.today().year


def fetch(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        ctype = r.headers.get("Content-Type", "")
        return r.read(), ctype


def save(name, url, expect_csv=True, log=None):
    path = os.path.join(OUT, name)
    if os.path.exists(path) and os.path.getsize(path) > 200:
        log.append([name, url, "cached", os.path.getsize(path), ""])
        return True
    try:
        body, ctype = fetch(url)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        log.append([name, url, "error", 0, repr(e)])
        print(f"  [fail] {name}: {e!r}")
        return False
    text = body[:400].decode("utf-8", "ignore")
    looks_csv = ("," in text) and ("<html" not in text.lower())
    if expect_csv and not looks_csv:
        # Savant sometimes returns the HTML page instead of CSV if a param is off — keep it, flag it
        name = name.replace(".csv", ".html")
        path = os.path.join(OUT, name)
    with open(path, "wb") as fh:
        fh.write(body)
    status = "ok" if (looks_csv or not expect_csv) else "html_instead_of_csv"
    log.append([name, url, status, len(body), ctype])
    print(f"  [{status}] {name} ({len(body)/1e3:.0f} KB)")
    time.sleep(0.6)
    return status == "ok"


def main():
    os.makedirs(OUT, exist_ok=True)
    log = []

    print("ABS challenge leaderboards ...")
    roles = ["batter", "catcher", "pitcher", "batting-team", "catching-team", "team", "league"]
    combos = [("mlb", "regular", THIS_YEAR), ("mlb", "spring", THIS_YEAR - 1), ("aaa", "regular", THIS_YEAR - 1),
              ("aaa", "regular", THIS_YEAR)]
    for level, gt, yr in combos:
        for role in roles:
            url = (f"{BASE}/leaderboard/abs-challenges?challengeType={role}&level={level}&gameType={gt}"
                   f"&year={yr}&sort=n_challenges&sortDir=desc&page=0&pageSize=1000&dataMode=for&csv=true")
            save(f"abs_challenges_{role}_{level}_{gt}_{yr}.csv", url, True, log)

    print("ABS dashboard + docs ...")
    for level, yr in [("mlb", THIS_YEAR), ("aaa", THIS_YEAR - 1), ("mlb", THIS_YEAR - 1)]:
        save(f"abs_dashboard_{level}_{yr}.html", f"{BASE}/abs?gameType=regular&year={yr}&level={level}", False, log)
    save("abs_metrics_documentation.html", f"{BASE}/abs-metrics-documentation", False, log)
    # a few plausible JSON endpoints behind the dashboard (harmless if they 404)
    for level, yr in [("mlb", THIS_YEAR)]:
        for ep in ["abs-data", "abs/data", "abs-challenges-data", "leaderboard/abs-challenges-data"]:
            save(f"abs_endpoint_{ep.replace('/', '_')}_{level}_{yr}.json",
                 f"{BASE}/{ep}?gameType=regular&year={yr}&level={level}", False, log)

    print("Pitch tempo leaderboards ...")
    for yr in range(2015, THIS_YEAR + 1):
        for typ in ["Pit", "Bat"]:
            url = f"{BASE}/leaderboard/pitch-tempo?type={typ}&min=q&year={yr}&csv=true"
            save(f"pitch_tempo_{typ}_{yr}.csv", url, True, log)
        # unqualified pitchers too (relievers) — try min=1
        save(f"pitch_tempo_Pit_min1_{yr}.csv", f"{BASE}/leaderboard/pitch-tempo?type=Pit&min=1&year={yr}&csv=true", True, log)

    print("Catcher framing leaderboards ...")
    for yr in range(2015, THIS_YEAR + 1):
        save(f"catcher_framing_{yr}.csv", f"{BASE}/catcher_framing?year={yr}&team=&min=q&sort=4,1&csv=true", True, log)

    with open(os.path.join(OUT, "_download_log.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["file", "url", "status", "bytes", "content_type_or_error"]); w.writerows(log)
    ok = sum(1 for r in log if r[2] in ("ok", "cached"))
    print(f"\nDone: {ok}/{len(log)} succeeded. Log: {os.path.join(OUT, '_download_log.csv')}")


if __name__ == "__main__":
    main()
