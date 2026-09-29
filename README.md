# Use It or Lose It — MLB's 2026 ball-strike challenges

Research for the MIT Sloan Sports Analytics Conference 2027 Baseball track. This repository evaluates when teams should spend retained-on-success challenges under an explicit model of the information available to players.

## September 28 full-season snapshot

On 354,488 eligible called pitches and 10,545 challenges from 2,425 games covering the complete 2026 regular season (March 25 to September 27; 2,429 games played, four without ABS), observed challenges capture **82.2%** of an approximate model benchmark. A 200-replicate game-clustered refit bootstrap gives a **79.9%–84.9%** conditional interval. The benchmark produces 2.557 percentage points of cumulative reversal value per team-game, observed use 2.102, and the 48-threshold card 2.376. The card recovers 60.3% of the modeled gap in simulation. Reconstructed outcomes agree with recorded verdicts on 99.97% of challenged pitches. The tables in `results/2026-09-28/` are copied verbatim from the nightly workflow's rolling `data` release (run completed 2026-09-28 18:13 UTC on commit cf4ae86); the folder's manifest records the run's source and input hashes. The September 25 snapshot below is retained as the audited reference; every headline moved by less than 0.1 percentage points of value or 1.5 points of ratio.

## September 26 audit revision

On 350,588 eligible called pitches and 10,425 challenges from 2,398 games through September 25, observed challenges capture **82.3%** of an approximate model benchmark. A 200-replicate game-clustered refit bootstrap gives a **79.4%–84.8%** conditional interval. The benchmark produces 2.565 percentage points of cumulative reversal value per team-game, observed use 2.110, and the 48-threshold card 2.378. The card recovers 58.8% of the modeled gap in simulation.

These values sum estimated nonnegative call-reversal gains along recorded game paths; they are not causal wins gained. The fitted signal scale may absorb attention and threshold heterogeneity and does not identify eyesight. The numerical policy iteration can cycle slightly; see the sensitivity record and current methods. These qualifications are part of the result.

**Current reference:** [CURRENT_METHODS.md](CURRENT_METHODS.md). [METHODS.md](METHODS.md) is a historical plan, not proof that every proposed analysis or validation was completed. Umpire-response and framing-equilibrium studies remain proposed work.

The audit corrected round-ball corner geometry, aligned count classifications and outcome scoring, removed extra-inning state collisions, repaired a walk-off terminal transition, used simulated inventory in observed-policy evaluation, and removed time-holdout preprocessing leakage. The workflow now fails on incomplete required pulls, parsing errors, or failed analyses. Historical WP training data/model provenance and the planned independent 200-pitch manual check remain outstanding.

## Layout

- `code/fetch/`: public Statcast, StatsAPI and ancillary data downloads.
- `code/engine/`: original-call extraction, zone geometry, historical WP pricing and approximate challenge-allocation solvers.
- `code/analysis/`: opportunity building, propensity fitting, policy evaluation, bootstrap and sensitivity analyses.
- `tests/`: regression tests for geometry, terminal states, extra innings, inventory-dependent decisions, scoring and estimator recovery.
- `data/derived/wp_count_cube.npz`, `wp_cube.npz`: versioned historical WP cubes used by the analysis.
- `results/2026-09-26/`: compact corrected result tables and audit metrics prepared locally; see their manifest.
- `results/2026-09-28/`: full-season result tables copied from the rolling release; see `manifest.json` and `metrics.json`.
- `tutorials/`: introductory examples; these are not independent validation of the full empirical study.
- `.github/workflows/nightly.yml`: current-data rebuild and rolling-release workflow.

## Reproduce from a frozen snapshot

Install `requirements.txt` in an isolated Python environment. Place a matched snapshot's `feed_2026_pitches.parquet` and `feed_2026_games.csv` in `data/derived/`, and its `statcast_2026.parquet` in `data/raw/statcast/`. Retain the versioned WP cubes.

```bash
python -m pytest tests -q
python code/engine/test_dp.py
BOOTSTRAP_B=200 python code/analysis/build_all.py
```

`build_all.py` stops if required inputs or analyses fail and writes `run_manifest.json` after a successful run. Bootstrap intervals hold historical WP, geometry, and leverage cut points fixed. A raw-feed rebuild additionally runs `challenges_extract.py` before the analysis. A complete rebuild of the historical WP cubes requires the Retrosheet inputs described in `CURRENT_METHODS.md`; they are not included in the current release.

For a new current-season pull:

```bash
python code/fetch/01_fetch_statcast.py --seasons 2026 --force
python code/fetch/02_fetch_statsapi_feeds.py --season 2026
python code/engine/challenges_extract.py --feeds data/raw/feeds/2026 --out data/derived/feed_2026
BOOTSTRAP_B=200 python code/analysis/build_all.py
```

The `data` GitHub release is rolling: its URL alone does not identify an immutable experiment. Archive exact files and hashes before making submission claims. A successful action is not evidence that future dates or the entire season are complete; check actual source coverage.

Data sources: Baseball Savant / MLB Advanced Media (Statcast), MLB StatsAPI, and Retrosheet. The information used here was obtained free of charge from and is copyrighted by Retrosheet. Code: MIT license. The MLB application builds on prior challenge-allocation research, including [Abramitzky et al. (2012), professional tennis](https://web.stanford.edu/~leinav/pubs/IER2012.pdf).
