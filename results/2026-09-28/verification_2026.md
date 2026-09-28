# Verification report — 2026 opportunity table (METHODS §2.1)

- StatsAPI feeds: 2,429 games, 714,483 pitches (2026-03-25 → 2026-09-27).
- Statcast regular season: 2,429 games, 716,792 pitches (2026-03-25 → 2026-09-27).
- Token replay audit (nine-inning games, where gameData.remaining = 2 − failed challenges): final tokens match for both teams in 100.00% of 2,216 games. gameData.remaining ignores extra-inning grants (it equals max(0, 2 − usedFailed) in 99.8% of games), so extra-inning games are audited by consistency instead: under the documented rule (a team with no challenge receives one at the start of each extra inning) every one of the 10,558 observed challenges was made with ≥1 token in hand — violations: 0.
- Challenge events parsed: 10,558 (event-level 7,896, play-level 2,662) vs gameData tallies 10,558; games not reconciling: 0.
- Game coverage: 0 Statcast regular-season games are absent from the feed pull; 0 feed games are not yet in Statcast (usually the latest date).
- Savant ABS leaderboard reconciliation (batters): 526/526 Savant players matched by name (0 Savant-only, 0 ours-only); challenge counts identical for 99.4% of players, Σ|difference| = 13 of 4,765 (0.27%); overturn counts identical for 99.6%; league totals Savant 4,765/2,328 vs ours 4,766/2,328 (snapshots may differ by a day of games).
- Savant ABS leaderboard reconciliation (catchers): 107/107 Savant players matched by name (0 Savant-only, 0 ours-only); challenge counts identical for 100.0% of players, Σ|difference| = 0 of 5,613 (0.00%); overturn counts identical for 100.0%; league totals Savant 5,613/3,287 vs ours 5,613/3,287 (snapshots may differ by a day of games).
- Savant ABS leaderboard reconciliation (pitchers): 109/109 Savant players matched by name (0 Savant-only, 0 ours-only); challenge counts identical for 100.0% of players, Σ|difference| = 0 of 179 (0.00%); overturn counts identical for 100.0%; league totals Savant 179/71 vs ours 179/71 (snapshots may differ by a day of games).
- Join key (game_pk, at_bat_number = atBatIndex+1, pitch_number): match rate 100.000% of feed pitches in the 2,429 games present in both sources; 100.000% of called pitches; 100.000% of challenged pitches.
- State agreement on joined called pitches: pre-pitch count identical 99.888%; outs identical 100.000%.
- Feed code × Statcast description (called pitches):

sc_description  automatic_ball  automatic_strike    ball  blocked_ball  called_strike  foul  foul_bunt  swinging_strike
code                                                                                                                   
B                           86                28  240765             3             37    59          1               13
C                           59                 8      42             3         115576     7          0                3

- Geometry: our plate-midpoint x/z (feed pX/pZ propagated with the 9-parameter fit) vs Savant plate_x/plate_z: median |Δx| 0.001 in (95th pct 0.003), median |Δz| 0.002 in (95th 0.007); ABS zone edges identical to Savant sz_top/sz_bot in 99.96% of pitches.
- Games without an absChallenges block in gameData (ABS not in operation; excluded from all analyses): 4 — [823669, 823745, 825093, 825094].
- Feed final call vs Statcast description inconsistent (dropped): 82 pitches.
- Position players pitching (pitcher-game mean velocity < 75 mph): 1,067 eligible pitches flagged (kept in the table, excluded from perception and arrival analyses).
- Eligible opportunities (original call B/C, Statcast description in ['ball', 'blocked_ball', 'called_strike'], valid count/geometry, joined): 355,555 of 356,690 called pitches; excluded automatic balls: 271; challenged pitches retained: 10,545 of 10,558.
- Negative estimated flip gains: 7,794; signed values preserved in g_raw, primary policy reward clipped at zero.
- WP validation on 345,010 unchallenged called pitches vs Savant: ΔWP(home) of the original call — primary count-composed WP (v2): r = 0.838, MAE = 0.215 pp (mean |Savant Δ| = 0.551 pp); direct HGB-with-count WP (v1): r = 0.703, MAE = 0.429 pp. Pre-pitch WP vs Savant home_win_exp: r = 0.9981 (v2), 0.9970 (v1). Mean flip gain g: 1.333 pp (v2) vs 1.535 pp (v1), r = 0.881.
- Zone go/no-go: our any-part/midpoint classification agrees with the ABS verdict on 99.97% of 10,545 challenged pitches (99.99% outside the ±0.5 in coin-flip band, n=7,846); documented validation threshold 90%.
  - edge side: n=5,240, agreement 99.98%
  - edge top: n=1,727, agreement 100.00%
  - edge bottom: n=3,578, agreement 99.94%
- Role split of challenges (overturn rate): batter: n=4,759, 48.9%; catcher: n=5,607, 58.6%; pitcher: n=179, 39.7%; overall 53.9% (public reference mid-Aug 2026: 53.6%; catchers 58.6, batters 48.5, pitchers 37.7).
- Output: /home/runner/work/use-it-or-lose-it/use-it-or-lose-it/data/derived/opps_2026.parquet — 355,555 rows, 2,425 games; challenges 10,545.
