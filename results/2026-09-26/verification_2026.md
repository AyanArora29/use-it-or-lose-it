# Verification report — 2026 opportunity table (METHODS §2.1)

- StatsAPI feeds: 2,402 games, 706,633 pitches (2026-03-25 → 2026-09-25).
- Statcast regular season: 2,402 games, 708,912 pitches (2026-03-25 → 2026-09-25).
- Token replay audit (nine-inning games, where gameData.remaining = 2 − failed challenges): final tokens match for both teams in 100.00% of 2,190 games. gameData.remaining ignores extra-inning grants (it equals max(0, 2 − usedFailed) in 99.8% of games), so extra-inning games are audited by consistency instead: under the documented rule (a team with no challenge receives one at the start of each extra inning) every one of the 10,438 observed challenges was made with ≥1 token in hand — violations: 0.
- Challenge events parsed: 10,438 (event-level 7,806, play-level 2,632) vs gameData tallies 10,438; games not reconciling: 0.
- Game coverage: 0 Statcast regular-season games are absent from the feed pull; 0 feed games are not yet in Statcast (usually the latest date).
- Join key (game_pk, at_bat_number = atBatIndex+1, pitch_number): match rate 100.000% of feed pitches in the 2,402 games present in both sources; 100.000% of called pitches; 100.000% of challenged pitches.
- State agreement on joined called pitches: pre-pitch count identical 99.887%; outs identical 100.000%.
- Feed code × Statcast description (called pitches):

sc_description  automatic_ball  automatic_strike    ball  blocked_ball  called_strike  foul  foul_bunt  swinging_strike
code                                                                                                                   
B                           86                28  238108             3             37    59          1               13
C                           59                 8      42             3         114333     7          0                3

- Geometry: our plate-midpoint x/z (feed pX/pZ propagated with the 9-parameter fit) vs Savant plate_x/plate_z: median |Δx| 0.001 in (95th pct 0.003), median |Δz| 0.002 in (95th 0.007); ABS zone edges identical to Savant sz_top/sz_bot in 99.96% of pitches.
- Games without an absChallenges block in gameData (ABS not in operation; excluded from all analyses): 4 — [823669, 823745, 825093, 825094].
- Feed final call vs Statcast description inconsistent (dropped): 82 pitches.
- Position players pitching (pitcher-game mean velocity < 75 mph): 1,067 eligible pitches flagged (kept in the table, excluded from perception and arrival analyses).
- Eligible opportunities (original call B/C, Statcast description in ['ball', 'blocked_ball', 'called_strike'], valid count/geometry, joined): 351,655 of 352,790 called pitches; excluded automatic balls: 270; challenged pitches retained: 10,425 of 10,438.
- Negative estimated flip gains: 7,737; signed values preserved in g_raw, primary policy reward clipped at zero.
- WP validation on 341,230 unchallenged called pitches vs Savant: ΔWP(home) of the original call — primary count-composed WP (v2): r = 0.838, MAE = 0.215 pp (mean |Savant Δ| = 0.552 pp); direct HGB-with-count WP (v1): r = 0.703, MAE = 0.429 pp. Pre-pitch WP vs Savant home_win_exp: r = 0.9981 (v2), 0.9970 (v1). Mean flip gain g: 1.335 pp (v2) vs 1.537 pp (v1), r = 0.881.
- Zone go/no-go: our any-part/midpoint classification agrees with the ABS verdict on 99.97% of 10,425 challenged pitches (99.99% outside the ±0.5 in coin-flip band, n=7,760); documented validation threshold 90%.
  - edge side: n=5,184, agreement 99.98%
  - edge top: n=1,709, agreement 100.00%
  - edge bottom: n=3,532, agreement 99.94%
- Role split of challenges (overturn rate): batter: n=4,706, 49.0%; catcher: n=5,542, 58.7%; pitcher: n=177, 39.0%; overall 54.0% (public reference mid-Aug 2026: 53.6%; catchers 58.6, batters 48.5, pitchers 37.7).
- Output: /Users/admin/Documents/MIT_Sloan_2026/audit/2026-09-26/corrected/data/derived/opps_2026.parquet — 351,655 rows, 2,398 games; challenges 10,425.
