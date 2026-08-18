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
- `code/engine/` — `abs_zone.py` (ABS zone reconstruction at the plate midpoint), `challenges_extract.py` (StatsAPI feeds → per-pitch table with the umpire's original call, the ABS zone, the signed miss, and every challenge event), `retro_parse.py` (Retrosheet → pitch states), `wp_count.py` (primary win-probability model: count-composed) and `wp_model.py` (direct fit, robustness), `dp.py` (the renewable-token DP), `perception.py` (structural perception model + threshold-in-inches), `test_dp.py`.
- `code/analysis/` — the nightly pipeline (`build_all.py`): `build_opps_2026.py` (every eligible called pitch with state, tokens in hand, ABS truth, WP flip gain; writes the §2.1 verification report), `perception_fit_2026.py` (challenge-propensity curves and probit fits by side/state), `tier1_dp_2026.py` (DP on the 2026 streams, marginal token values, the challenge card, policy values, capture ratio, dump tests).
- `data/derived/` — WP cubes (versioned); everything else is published nightly to the rolling `data` GitHub Release: `feed_2026_pitches.parquet` / `feed_2026_challenges.parquet` (per-pitch ABS table and challenge events), `opps_2026.parquet` (the opportunity table), `verification_2026.md`, `perception_*`, `tier1_*` (reports, tables, DP arrays).
- `tutorials/` — the toy dynamic program (Python notebook + R script).
- `.github/workflows/nightly.yml` — nightly rebuild: pulls, tests, figures, data release.

## Reproduce
```bash
pip install -r requirements.txt
python code/fetch/01_fetch_statcast.py            # 2015–2026 Statcast (~1 hr)
python code/fetch/02_fetch_statsapi_feeds.py --season 2026
python code/fetch/03_fetch_savant_leaderboards.py
python code/fetch/04_fetch_players_and_transactions.py
python code/engine/challenges_extract.py --feeds data/raw/feeds/2026 --out data/derived/feed_2026
python code/engine/wp_count.py build              # primary WP cube (needs Retrosheet pitch tables from retro_parse.py)
python code/engine/wp_model.py fit                # robustness WP cube
python code/analysis/build_all.py                 # opportunity table -> perception fits -> DP, card, policies
```
Or skip the pulls: download `feeds_2026.tgz`, `statcast_2026.parquet` and the derived tables from the `data` release and run `code/analysis/build_all.py`.
Data sources and terms: Baseball Savant / MLB Advanced Media (Statcast), MLB StatsAPI, Retrosheet (via Chadwick Baseball Bureau; "The information used here was obtained free of charge from and is copyrighted by Retrosheet"), Baseball-Reference/FanGraphs for cross-checks. Code: MIT license.
