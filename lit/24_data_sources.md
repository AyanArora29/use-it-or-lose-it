# 24 — Public data sources (consolidated from lit/01–11)

Compiled 2026-08-17. Access notes reflect what readers verified from the sandbox; "blocked here" means proxy 403/JS wall in the container, usually fine locally.

## 1. MLB ABS / challenge data (2025–26)

| Source | URL | Format | Key fields | Access / caveats |
|---|---|---|---|---|
| Baseball Savant ABS dashboard | https://baseballsavant.mlb.com/abs | HTML | totals by role, level (MLB/AAA), season, game type | Aug 17, 2026: 7,974 attempts, 54% overturned |
| Savant ABS challenges leaderboard CSV | `https://baseballsavant.mlb.com/leaderboard/abs-challenges?challengeType={catching-team|batting-team|catcher|batter|pitcher|team-summary}&level={mlb|aaa}&gameType=regular&year={2025|2026}&sort=n_challenges&sortDir=desc&page=0&pageSize=50&dataMode=for&csv=true` | CSV | entity_name, team_abbr, level, n_challenges, n_overturns, n_confirms, rate_overturns, **exp_chal, exp_chal_gained/lost, exp_rate_overturns, exp_rate_challenges**, net_chal_gained/lost, n_strikeouts_flip, n_walks_flip, *_against mirrors, total_vs_expected | Works (verified); AAA 2025–26 rows; filters for confidence bucket, attack zone, pitch type; MLB's own expected-challenge/overturn model included — no run-value column |
| Savant ABS metrics documentation | https://baseballsavant.mlb.com/abs-metrics-documentation | HTML | definitions: Challenge Opportunity, Reasonable Pitch, Confidence Level (0.2/(0.2+RV)), framing vs challenge-skill accounting | Cite verbatim |
| Savant per-game feed | `https://baseballsavant.mlb.com/gf?game_pk={pk}` | JSON | per pitch: px/pz, sz_top/sz_bot, x0,y0,z0,vx0..az, extension, **is_abs_challenge**; MLB and AAA | Reachable via WebFetch; `game_status.hasAbs` unreliable for AAA (code full/challenge days from the calendar) |
| Statcast search CSV | https://baseballsavant.mlb.com/statcast_search/csv?...&type=details (docs https://baseballsavant.mlb.com/csv-docs) | CSV | plate_x/plate_z (**front-of-plate ≤2025, mid-plate ≥2026**), sz_top/sz_bot (**operator ≤2025, ABS-defined ≥2026**), vx0..az at y=50, release_pos, description, zone, delta_run_exp, delta_home_win_exp (per PA), home_win_exp, fielder_2 | Blocked here (403); pull locally via pybaseball `statcast()` / baseballr `statcast_search()`; no challenge column |
| Statcast minors search | https://baseballsavant.mlb.com/statcast-search-minors | CSV | same; AAA 2023+ (mid-plate since 2023), PCL/Charlotte 2022, FSL 2021+ | Needed for AAA 2023–24 identification |
| MLB StatsAPI schedule | `https://statsapi.mlb.com/api/v1/schedule?sportId={1|11}&date=YYYY-MM-DD` | JSON | gamePks (sportId 11 = Triple-A) | Open |
| MLB StatsAPI live feed | `https://statsapi.mlb.com/api/v1.1/game/{pk}/feed/live` | JSON | pitchData.coordinates (x0..aZ, **pX/pZ still front-of-plate in 2026**), strikeZoneTop/Bottom, strikeZoneWidth 17, strikeZoneDepth 17→8.5 (2026), playEvents.details.hasReview, **gameData.absChallenges {usedSuccessful, usedFailed, remaining}**, officials (umpire identity) | Truncated in WebFetch; verify per-pitch reviewDetails locally |
| MLB StatsAPI people | `https://statsapi.mlb.com/api/v1/people?personIds=…` | JSON | height, **strikeZoneTop/strikeZoneBottom** (certified ABS zone → H = 12·szTop/0.535) | Certified heights recoverable to ≈0.1 in |
| MLB StatsAPI winProbability | `https://statsapi.mlb.com/api/v1/game/{pk}/winProbability` | JSON | per-PA homeTeamWinProbability, WPA, leverageIndex, atBatIndex | **No per-pitch WP anywhere public** |
| Baseball-Reference ABS page | https://www.baseball-reference.com/friv/abs-challenges.shtml | HTML tables (daily) | by role, count, inning × tokens remaining, month, leverage, umpire, location 3×3, per team-game distribution | No CSV; scrape |
| Baseball Almanac ABS Challenge Database | (via search) | HTML | game-level challenge log | Not verified |
| FanGraphs "Statcast – ABS" plate-discipline view | (Appelman, Mar 16, 2026) | leaderboard | in-ABS-zone rates by batter/pitcher | JS/API blocked here |
| Jon Becker's compiled challenge log | cited by Martell (FanGraphs Jun 19, 2026) | — | per-challenge | Not located |
| Oyster Analytics dashboard | https://oysteranalytics.com/ | web | break-evens by inning/tokens/score; MiLB ABS | Premium via Down on the Farm Substack |
| Umpire Scorecards | https://umpscorecards.com (data/umpires, data/games; explainers /page/info/explainers/accuracy, /abs) | HTML/JS | per-game accuracy, xAcc, consistency, favor; 2026 uses ABS zone, no tolerance, mid-plate; >99.5% agreement with ABS on ~1,600 challenges | JS-only site |
| MLB press releases / rules | https://www.mlb.com/press-release/press-release-mlb-announces-abs-challenge-system-coming-to-the-major-leagues-beginning-in-the-2026-season ; https://www.mlb.com/news/ball-strike-challenge-system-2026 ; https://www.mlb.com/news/automated-ball-strike-system-results-mlb-spring-training-2025 | HTML | rule text; spring-2025 statistics | Cite MLB numbers; footnote AP discrepancies |

## 2. Framing and umpire data

| Source | URL | Format | Notes |
|---|---|---|---|
| Savant catcher framing CSV | `https://baseballsavant.mlb.com/leaderboard/catcher-framing?gameType=Regular&seasonStart=YYYY&seasonEnd=YYYY&type=catcher&minPitches=q&minResults=1&csv=true` | CSV: id, name, pitches, rv_tot, pct_tot, rv_11..pct_19 | 2018+ only; **2026 zone redefined** — not comparable to ≤2025 |
| Flannagan, Mills & Goldstone replication | https://osf.io/hv68j/ | pitch-level 2008–15 with umpire IDs | Best public umpire-ID pitch file |
| Green & Daniels code/data | https://github.com/etangreen/umpires (+ Dropbox link) | code + data | 2009–11 |
| Kim & King; Chen–Moskowitz–Shue; Archsmith et al. | journal supplement / QJE dataverse / EJ replication | — | Check terms |
| Kaggle "MLB Pitch Data 2015–2018" (Schale) | kaggle.com | CSV, 2.87M pitches | Zhan et al.'s data; pre-ABS baseline |
| Retrosheet | https://www.retrosheet.org | event files, game logs (umpires) | Required attribution notice |
| FanGraphs FRM / Guts / $-WAR | https://www.fangraphs.com/guts.aspx?type=cn | tables | R/W by year 9.4–10.3 |
| Tango RE24 tables | http://www.tangotiger.net/re24.html | HTML | 1950–2015 by era; other Tango pages rate-limited |
| Greg Stoll WE finder | https://gregstoll.com/~gregstoll/baseball/ ; github.com/gregstoll/baseballstats | code (Apache-2.0) | WE tables |
| openWAR; baseball_R | github.com/beanumber/openWAR ; github.com/beanumber/baseball_R | R | RE24 estimation, resampling |
| SIS SZRS; BP CSAA; The Analyst | articles only / paywall | — | cite via articles |

## 3. Zone geometry / physics code

| Source | URL | Notes |
|---|---|---|
| Alan Nathan physics site | https://baseball.physics.illinois.edu (pitchtracker.html; MCAnalysis.pdf; Movement.pdf; PitchFX_9P_Model-4.pdf; KaganPitchfx.pdf; TrajectoryCalculator.xlsx; trajectory-calculator-new3D.html) | 9P model, MC error study, drag/Magnus calculators |
| pitchRx | https://github.com/cpsievert/pitchRx (R/getSnapshots.R) | plane-propagation formula `t = (-vy0 - sqrt(vy0^2 - 2*ay*(y0 - y)))/ay` |
| sabRmetrics (S. Powers) | https://github.com/saberpowers/sabRmetrics (get_quadratic_coef.R, get_trackman_metrics.R; GPL-3) | quadratic trajectory utilities |
| Official Baseball Rules 2021 PDF | https://img.mlbstatic.com/mlb-images/image/upload/mlb/atcjzj9j7wrgvsm8wnjq.pdf | Rules 2.02, 3.01 |
| Baseball America AAA zone history | URLs in lit/10 §2.3 | 2022 19 in; 2023 27–51%; Sept 2023 stance-based; 2024 53.5/27 |
| Verified facts (lit/10) | — | Savant plate_x/z reproduce the 9P to 1e-4 ft; front→mid shift ≈ −0.6 to −1.3 in vertical, 0–0.7 in horizontal |

## 4. Cross-sport data

| Sport | Source | Fields / notes |
|---|---|---|
| **Tennis** | None public per challenge. Sackmann GitHub (CC BY-NC-SA 4.0): tennis_slam_pointbypoint, tennis_pointbypoint, tennis_MatchChartingProject — **no challenge/Hawk-Eye field**; use only for serve-point win rates / point importance | Academic samples (ATP umpire sheets 2006–08; Hawk-Eye tracking) private. Rule text: https://btopen.org/review/ ; ATP rulebook PDFs; ATP ELC release Apr 28, 2023 |
| **Cricket** | Cricsheet https://cricsheet.org/downloads/ (JSON zips: tests 912; ODIs 3,169; T20Is 5,602; IPL 1,243; 22,537 matches 2001–26); format docs https://cricsheet.org/format/json/ | Per-delivery `review` object (JSON 1.0.0+, since Jul 22, 2021): `by`, `umpire`, `batter`, `decision` ∈ {struck down, upheld}, `umpires_call: true`; **no `type` field** (infer LBW/caught from wicket object); "struck down" includes umpire's-call outcomes; pre-2017 back-fill incomplete; `info.officials` for umpires. CSV/"Ashwin" CSV and R `cricketdata` do **not** carry reviews. Licence ODC-By 1.0. Official GitHub org has only archived converters. Also: ESPNcricinfo scorecards "Player Reviews" tables (2017+, scrapeable); private DBs (Samson 6,011 reviews; Ganjoo 3,369; Davis 2,100+) by request |
| **NFL** | nflverse pbp https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{YEAR}.csv.gz (≈18 MB/season; also parquet/rds; open license); dictionary https://raw.githubusercontent.com/nflverse/nflreadr/main/data-raw/dictionary_pbp.csv | `replay_or_challenge` (binary), `replay_or_challenge_result` ∈ {upheld, reversed, confirmed, denied}, `timeout`, `timeout_team`, `posteam/defteam_timeouts_remaining` (post-charge on challenge row), `wp`, `wpa`, `vegas_wp`, `qtr`, `game_seconds_remaining`, `score_differential`, `desc`. **No challenge-team column** — parse `desc` ("<Team> challenged the <ruling> ruling, and the play was (Upheld|REVERSED)"); booth = "Replay Official reviewed"/"Replay Assistant challenged". Local: `/home/claude/sloan/lit/scratch/nfl_coach_challenges_reg_2013_2025.csv` + `nfl_challenge_descriptives.py`; `nfl4th` (CRAN) for 4th-down WP |
| **NBA** | No official dataset; challenges as "Instant Replay – Coach Challenge" events in NBA Stats / `nba_api` / `hoopR` pbp; official.nba.com "Coach's Challenge results" PDFs (2019-20, 2020-21) and Rule 14; github.com/basketballrelativity/challenges (Oct 2019 hand-compiled) | Media tallies: Forbes 2020; Axios 2024; Blazer's Edge 2025 |
| **NHL** | nhl.com Situation Room; Scouting the Refs season logs; The Hockey News 2023 tables | Counts differ across sources — cite one per number |
| **VAR/FVS** | IFAB Laws (VAR protocol); FIFA Inside "What is Football Video Support"; Spitz et al. 2021 | No FVS statistics found |
| **MLB replay 2014–25** | Savant replay page; StatsAPI review feeds; Imber 2015 (MLB counts); Illarionov 2017 (Savant + B-Ref + Retrosheet) | Baseline renewable-token right |
| **KBO** | Naver Sports pitch pages (Lee et al. 2025 scraped 2,515 games) | Full-ABS zone geometry; not public as a file |

## 5. SSAC corpus and rules

- Finalist corpus: `/home/claude/sloan/papers_txt/*.txt` (100 papers 2012–2025); PDFs via sloansportsconference.com/research-papers/<slug> (cdn.prod.website-files.com).
- SSAC27 rules: https://www.sloansportsconference.com/research-paper-competition — abstract <500 words incl. title, ≤2 exhibits, four sections; open-source repository with data required; blind review; abstract Oct 1, 2026; paper Dec 4, 2026.
- Winner code: github.com/evanmunro/draft-policy (2020); github.com/sdsander-syr/soccer_pk_shot_location (2025 — note identity leak); Berry & Fowler RIFLE Stata package.

## 6. Not reached / to retrieve from campus network
Nadimpalli & Hasenbein 2013 full text; Song, Kang & Paulsen 2026 (ESMQ); Clarke & Norman 2012 full text; Mather 2008 full text; Kovalchik et al. 2017 full text; Baseball Prospectus (Judge et al. 2015; Judge 2018; Orr SEAGER); Tango's 2026 ABS posts (tangotiger.com); ESPN ABS tracker; The Athletic (Stark Feb 23, 2026; Blum/Lin Feb 20, 2026); Down on the Farm "Oyster Guide"; Hsu 2024 full text; Bradbury 2019 full text; SSRN "Definitivity Avoidance" abstract.
