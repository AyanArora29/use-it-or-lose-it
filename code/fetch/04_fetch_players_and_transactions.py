#!/usr/bin/env python3
"""
04_fetch_players_and_transactions.py — MLB StatsAPI: player bios (height!) and transactions (IL stints).
Standard library only.

Output:
    <repo>/data/raw/players/players_<season>.csv        every player on an MLB roster that season:
                                                        id, name, height (inches), weight, bats, throws,
                                                        position, birthDate, mlbDebutDate
    <repo>/data/raw/transactions/transactions_<year>.csv  all MLB transactions that year (IL placements,
                                                        activations, options...) — used for the pitch-clock hedge

Usage:  python3 04_fetch_players_and_transactions.py            # 2015..this year
        python3 04_fetch_players_and_transactions.py --years 2026
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import time
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
P_OUT = os.path.join(ROOT, "data", "raw", "players")
T_OUT = os.path.join(ROOT, "data", "raw", "transactions")
API = "https://statsapi.mlb.com/api/v1"
UA = {"User-Agent": "Mozilla/5.0 (research; SSAC27 open-data project)"}


def get_json(url, retries=4):
    last = None
    for i in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            last = e; time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"failed {url}: {last!r}")


def height_to_inches(h):
    """'6\\' 2"' -> 74"""
    if not h:
        return None
    m = re.match(r"\s*(\d+)\s*'\s*(\d+)?", h)
    if not m:
        return None
    return int(m.group(1)) * 12 + int(m.group(2) or 0)


def players(season, sport=1):
    js = get_json(f"{API}/sports/{sport}/players?season={season}&hydrate=currentTeam")
    rows = []
    for p in js.get("people", []):
        rows.append({
            "season": season, "id": p.get("id"), "fullName": p.get("fullName"),
            "height_raw": p.get("height"), "height_in": height_to_inches(p.get("height")),
            "weight": p.get("weight"), "bats": (p.get("batSide") or {}).get("code"),
            "throws": (p.get("pitchHand") or {}).get("code"),
            "position": (p.get("primaryPosition") or {}).get("abbreviation"),
            "birthDate": p.get("birthDate"), "mlbDebutDate": p.get("mlbDebutDate"),
            "currentTeam": (p.get("currentTeam") or {}).get("name"),
            "active": p.get("active"),
        })
    return rows


def transactions(year, sport=1):
    rows = []
    d0, d1 = dt.date(year, 1, 1), min(dt.date(year, 12, 31), dt.date.today())
    cur = d0
    while cur <= d1:
        nxt = min(cur + dt.timedelta(days=45), d1)
        q = urllib.parse.urlencode({"sportId": sport, "startDate": cur.isoformat(), "endDate": nxt.isoformat()})
        js = get_json(f"{API}/transactions?{q}")
        for t in js.get("transactions", []):
            rows.append({
                "id": t.get("id"), "date": t.get("date"), "effectiveDate": t.get("effectiveDate"),
                "resolutionDate": t.get("resolutionDate"), "typeCode": t.get("typeCode"),
                "typeDesc": t.get("typeDesc"),
                "person_id": (t.get("person") or {}).get("id"), "person": (t.get("person") or {}).get("fullName"),
                "fromTeam": (t.get("fromTeam") or {}).get("name"), "toTeam": (t.get("toTeam") or {}).get("name"),
                "description": t.get("description"),
            })
        cur = nxt + dt.timedelta(days=1)
        time.sleep(0.3)
    # de-dup by id
    seen, out = set(), []
    for r in rows:
        if r["id"] not in seen:
            seen.add(r["id"]); out.append(r)
    return out


def write_csv(path, rows):
    if not rows:
        print(f"  [warn] nothing to write for {path}"); return
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="*", type=int, default=list(range(2015, dt.date.today().year + 1)))
    args = ap.parse_args()
    os.makedirs(P_OUT, exist_ok=True); os.makedirs(T_OUT, exist_ok=True)

    print("Players (heights) ...")
    for y in args.years:
        out = os.path.join(P_OUT, f"players_{y}.csv")
        if os.path.exists(out):
            print(f"  [skip] {out}"); continue
        rows = players(y); write_csv(out, rows)
        print(f"  [ok] {y}: {len(rows)} players (missing height: {sum(1 for r in rows if r['height_in'] is None)})")

    print("Transactions (IL etc.) ...")
    for y in args.years:
        out = os.path.join(T_OUT, f"transactions_{y}.csv")
        if os.path.exists(out) and y != dt.date.today().year:
            print(f"  [skip] {out}"); continue
        rows = transactions(y); write_csv(out, rows)
        il = sum(1 for r in rows if re.search(r"injured list|disabled list", (r["description"] or ""), re.I))
        print(f"  [ok] {y}: {len(rows)} transactions ({il} mention IL/DL)")
    print("Done.")


if __name__ == "__main__":
    main()
