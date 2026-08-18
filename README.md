# Use It or Lose It — the value and optimal use of MLB's 2026 ABS challenges

Submission to the MIT Sloan Sports Analytics Conference 2027 Research Paper Competition (Baseball track). Author information is withheld from this README during blind review.

**Question.** MLB's 2026 Automated Ball-Strike challenge system gives each team two challenges per game, kept if successful.
What is a challenge worth in win probability, when should it be spent, how far from optimal are teams and players, and did
umpires call the zone differently once their calls could be reviewed on demand?

**Approach.** A finite-horizon dynamic program with a renewable token (the "retained if successful" rule), priced in win
probability from 7.4M pitches (2015–2025); a structural perception model estimated on every 2026 challenge; revealed
thresholds vs optimal; umpire behaviour under review; rule-design counterfactuals. Everything here is public data and
reproducible — see `METHODS.md` (pre-registered analysis plan, dated) and the nightly CI badge.

## Layout
- `METHODS.md` — pre-registered analysis plan with a dated decision log.
- `code/fetch/` — public data pulls (Statcast via pybaseball; MLB StatsAPI feeds; Baseball Savant leaderboards; player heights; transactions).
- `code/engine/` — `abs_zone.py` (ABS zone reconstruction at the plate midpoint), `retro_parse.py` (Retrosheet → pitch states), `wp_model.py` (win-probability model + flip values), `dp.py` (the renewable-token DP), `perception.py` (structural perception model + threshold-in-inches), `test_dp.py`.
- `code/analysis/` — figures and tables for the paper (built by `build_all.py`).
- `data/derived/` — released per-pitch ABS table (zone, midpoint location, signed miss distance) and challenge-event table.
- `tutorials/` — the toy dynamic program (Python notebook + R script).
- `.github/workflows/nightly.yml` — nightly rebuild: pulls, tests, figures, data release.

## Reproduce
```bash
pip install -r requirements.txt
python code/fetch/01_fetch_statcast.py            # 2015–2026 Statcast (~1 hr)
python code/fetch/02_fetch_statsapi_feeds.py --season 2026
python code/fetch/03_fetch_savant_leaderboards.py
python code/fetch/04_fetch_players_and_transactions.py
python code/engine/wp_model.py fit                # win-probability model
python code/engine/dp.py --seasons 2023 2024 --eval 2025
```
Data sources and terms: Baseball Savant / MLB Advanced Media (Statcast), MLB StatsAPI, Retrosheet (via Chadwick Baseball Bureau; "The information used here was obtained free of charge from and is copyrighted by Retrosheet"), Baseball-Reference/FanGraphs for cross-checks. Code: MIT license.
