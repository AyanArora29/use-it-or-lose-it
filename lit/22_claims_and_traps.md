# 22 — Claims we must not make, numbers we can quote, and the twelve likeliest referee objections

Synthesis of the "traps" sections of lit/01–11. Compiled 2026-08-17.

---

## (a) Claims we must NOT make, or must hedge — with the source a referee would cite

| # | Claim to avoid / hedge | Why (contradicting source) | Safe phrasing |
|---|---|---|---|
| 1 | "The 9th-inning success collapse (59% → 35%) shows players are irrational." | Every DP (Abramitzky et al. 2012; Krasker 2006; Illarionov 2017; darts SSAC 2024) predicts thresholds fall as option value → 0; Liebman & Mahoney's dump is wasteful only because rollover is feasible. | "Late aggressiveness is predicted; the behavioral test is *early* hoarding, tokens expiring unused, and thresholds falling *before* option value is gone." |
| 2 | "Catchers perceive the zone best (58% vs 48% vs 38%)." | Rates are conditional on self-selected challenges at different distances/counts/stakes under team policies (Reds bar pitchers; Orioles route to catchers — Martell 2026); AEKM: lower success can mean *better* (more aggressive) challenging. | "Raw success rate"; report role differences only after conditioning on true miss distance and state, with shrinkage. |
| 3 | "Tennis players solve the DP / are optimal." | AEKM's 96.8% is value captured, not threshold accuracy; they find systematic under-challenging and 6–8 pp lower success on high-stakes points; no learning. | "near-optimal in value terms, but too conservative." |
| 4 | "Umpires changed because of the challenge system." | 2025 grading buffer cut 2 in → 0.75 in (Andrews May 2025; Axisa 2025) predates 2026; Statcast plate_x/z moved front→mid-plate and sz_top/bot became ABS-defined in 2026 (Savant CSV docs); accuracy had risen every year to 2023 (Andrews). Clemens (Apr 28, 2026): "the net effect of challenges is quite small." | Identify with AAA 2023–24 rotation and spring-2025 parks; difference out the 2025 grading shock; recompute location on one plane. |
| 5 | "Framing is obsolete under ABS." | >98% of pitches still called by the umpire (Cooper 2025); only 19% of stolen strikes challenged (Verducci 2026); Statcast still books framing on the initial call. | "Compressed" (98 → ~half → ~18 runs spread mid-Aug 2026), with the zone-redefinition caveat. |
| 6 | "A missed call is worth 0.065 runs" (or 0.13, or 0.32) as a universal number. | Four incompatible magnitudes: Zhan 0.065 (per fixed-zone miss, pre-to-post), Turkenkopf/Fast 0.13 (context-neutral flip), Singer mean RED 0.32 (RE288 w/ base-out; internally inconsistent), D&W 0.06–0.54 by count. | Always state population (all/called/missed/challenged), reference (full flip vs half), and base-out inclusion. |
| 7 | "Umpire accuracy is X%." | Levels range 84% (rulebook, Archsmith) → 86.6% (Chen) → 92.5–92.8% (Statcast/FanGraphs) → 96–98.5% (MLB internal, 2-in buffer); BU "34,294 missed calls" is unrefereed with an unstated zone. | State zone definition, ball radius, buffer, plane; quote Statcast ~92.8% (2025) / ~11 misses per game. |
| 8 | "Count effects prove umpire bias." | Green & Daniels themselves moved to a Bayesian-prior interpretation ("Bayesian Instinct" 2021); MacMahon & Starkes show players share the context effect. | "State-dependence"; leave mechanism open. |
| 9 | "Same-race / home / star favoritism motivates our study." | Race results fragile (Tainsky, Mills & Winfree 2015; Hamrick & Rasp 2015); home bias ≈0.2 in / 0.5–2 pp; Scorecasting's "2/3 of HFA" disputed (Birnbaum). | Cite as small, edge-concentrated, and monitoring-sensitive. |
| 10 | "The ABS zone is the rulebook zone / has been the same since 2019." | AAA 2022 width 19 in; 2023 top 51%; Sept 2023 stance-based; 2024+ 53.5/27; KBO buffer + two planes; NCAA 58/23 (BA; Lee et al.). MLB.com's "all years" claim is wrong. | Give the year-by-year geometry table. |
| 11 | "Hawk-Eye gives the truth." | 0.25 in average at front of plate (Jedlovec 2020); "one-sixth of an inch" (Shenk 2026); Collins & Evans on presenting reconstructions as fact; Borooah's technology-error decomposition. | Report a ±0.25–0.5 in coin-flip band; validate ≥99% reproduction of rulings (UmpScorecards got >99.5%). |
| 12 | "Savant's 0.2-run breakeven is MLB's estimate of a token's value." | Documentation gives no justification; it is a convention. | "A constant-cost convention that our DP replaces with a state-dependent value." |
| 13 | "The challenge system is worth $X million / N wins." | Best-to-worst team spread ≈1.25 wins (Baumann 2026); tennis benefit 1.55 pp match-WP; runs/win 9.4–10.3 by year; $/WAR tiered ($7–12M). | Give runs and wins with year-specific conversions; do not oversell. |
| 14 | "First paper on X." | Banchio & Munro; Chan & Fearing hedge. | "To our knowledge." |
| 15 | "Teams should challenge more" as a blanket prescription. | Baumann's "loosen the reins" is a correlation (11.6 challenges ≈ 1 run); Oler shows low-leverage waste; success ≠ value. | Prescribe the state-dependent cutoff; report where teams are above and below it. |
| 16 | "The catcher's 2–3 ft displaced view / batter's truncated tracking explains role gaps." | Physics/psychophysics motivation only (Bahill & LaRitz; Kishita et al.); not measured in baseball. | Motivate σ_role; do not assert magnitudes unless estimated. |
| 17 | "Tennis (or cricket) has public challenge datasets." | None exist (ATP sheets private; Sackmann files carry no challenge flag); Cricsheet has reviews but no `type` field and incomplete pre-2017 coverage. | Say so; use Cricsheet/nflverse for cross-sport pilots only. |
| 18 | "Andrews' 'catchers 10 pp worse where they frame' is established." | ~40 catchers, early season, no CIs, opportunity-quality confound. | Hypothesis we test. |
| 19 | "Learning" from rising challenge volume (3.76 → 4.60/game). | Public dashboards (Savant confidence, Oyster, FanGraphs) may move behavior (Hawthorne); success flat; composition and umpire adaptation confound. | Separate composition, umpire adaptation, and true threshold movement. |
| 20 | Comparing 2025 and 2026 shadow-zone or framing leaderboards. | Savant zone redefinition 2026 (mid-plate, height-based). | Recompute from raw locations with one zone. |

---

## (b) Numbers we can quote as established facts (with source)

**Rules and geometry**
- 2 challenges/team/game; retained if successful; +1 per extra inning if none remaining; pitcher/catcher/batter only, immediately, no help; zone 17 in wide, 27%–53.5% of certified height, 2-D at plate midpoint, strike if any part of the ball touches (MLB press release, Sept 23, 2025).
- Plate depth 17 in → midpoint 8.5 in; ball circumference 9–9.25 in → radius 1.43–1.47 in (Official Baseball Rules 2.02, 3.01). Any-part width ≈19.9 in (Walsh 2007).
- Hawk-Eye: 12 cameras; center-of-ball accuracy 0.25 in on average at front of plate (Jedlovec, MLB Tech Blog 2020); tennis Hawk-Eye 3.6 mm (AEKM 2012).
- Savant plate_x/plate_z front-of-plate through 2025, mid-plate from 2026; sz_top/sz_bot ABS-defined from 2026 (Savant CSV docs). StatsAPI pX/pZ still front-of-plate in 2026 (lit/10 verified).
- Triple-A: 2022 19-in zone; 2023 27–51%, first three games of series full ABS / last three challenge, 3 tokens; 2024 53.5/27, Tue–Thu full / Fri–Sun challenge, all-challenge from Jun 25–26; 2025 2 tokens (Baseball America). KBO 2024: 47.18 cm width, 27.64–56.35%, two planes (Lee et al. 2025). NCAA 2027: 3 tokens, 23–58% (Rudner 2026).

**Trial and 2026 outcomes**
- Spring 2025: 288 games, 1,182 challenges (2.6% of pitches, 4.1/game), 52.2% overturned; C 56%, B 50%, P 41%; rate 1.9% (inn. 1–3) → 3.6% (9th); full counts 8.2%; 13.8 s per challenge (DeRosa, MLB.com Mar 27, 2025).
- AAA 2025: 9,432 challenges, 1.1% of pitches, 50% overturned; fielders 55%, batters 45%; batter rate 3.5% (1st) → 8% (9th) (Petriello 2026). AAA full-ABS vs challenge days: 2023 BB% 12.30 vs 10.45; 2024 11.78 vs 11.01 (Cooper, BA Jun 19, 2024).
- MLB 2026 through Aug 17: 7,975 challenges, 53.6% overturned, 4.27/game; C 58.6%, B 48.5%, P 37.7%; with two tokens: 59.3% (1st) → 35.4% (9th); 3-2 counts 40.2%; monthly usage 3.76 → 4.60/game; 9.0% of team-games zero challenges, 32.7% exactly two (Baseball-Reference).
- 2026 through early June: 4,537 challenges / 161,859 called pitches = 2.8%; 3-2 counts 9.4%; challenged distance from edge 0.048 ft (low LI) → 0.057 ft (high) (Martell 2026). Leverage buckets: rate 2.3/3.4/4.6%, success 56.8/50.7/45.9%, runs per challenge 0.04/0.11/0.23 (Oler 2026).
- 2026 called zone 454 → 439 sq in for a 6-ft batter; fastballs 0–4 in above the top called strikes 54.3% → 40.8% (Clemens Apr 28, 2026). BB% 8.4% → 9.5% (Clemens May 12, 2026).
- Team challenge runs 18.1 (TB) to 33.6 (MIN) through Aug 9 (Baumann 2026).
- Only 29% of called strikes ≥2.5 in outside were challenged in March (Clemens Apr 1, 2026); 19% of 861 stolen strikes challenged (Verducci 2026).

**Umpire literature**
- Green & Daniels 2014: borderline P(strike) ≈31% at two strikes, ≈58% at three balls; prior strike −17 pp; average umpire needs 64% certainty for strike three; 10–90% ring a foot wide.
- Kim & King 2014: 18.8% of true strikes called balls, 12.9% of balls called strikes (2008–09, rulebook zone); +4.8% odds per All-Star appearance.
- Chen–Moskowitz–Shue 2016: −1.5 pp after a called strike (−3.5 pp ambiguous).
- Mills 2017: accuracy 85.35% (2008) → 89.9% (2015). Statcast: 92.44/92.81/92.53/92.83% (2022–25); shadow 81–82% (Andrews).
- Archsmith et al. 2025: +0.61 pp accuracy per SD of leverage.
- Flannagan et al. 2024: consistency +33% 2008–15; home bias ≈0.2 in throughout.
- 2025 umpire CBA: grading buffer 2 in → 0.75 in (Andrews May 2025; The Athletic via CBS).

**Framing**
- Run value of a called strike: 0.1189 (Rosales & Spratt), 0.11 mean / 0.062 (0-0) – 0.540 (3-2) (Deshpande & Wyner), 0.125 (Statcast), 0.135 (FanGraphs), 0.13 (Fast/Turkenkopf).
- Best-minus-worst framer ≈98 runs (2008), ≈half by 2025 (Baumann 2026); Statcast 2025 spread 38, 2026 through Aug 16 ≈18 (Savant CSV pull, lit/05).

**Cross-sport**
- Tennis: 2.6% of points challenged, 38% success (AEKM); 96.8% of optimal value; +1.55 pp match-WP per unilateral right; umpire error 0.61% of bounces, 13.9% within 100 mm (Almog).
- Cricket DRS: 25.8% reversed (Shivakumar); batters 34–37% vs fielders 20–21% (Davis; Bayliss; Date); overs 60–80 success 20% vs 28% under the top-up rule (Bayliss).
- NBA: 2019-20 633 challenges, 44%; Q1–Q4 65/53/45/39%; 2023-24 1,282, 59.2%. NHL GI challenges 24% → 48% after penalty rule. NFL 1999–2024: 8,698 reviews, 42% reversed; coach challenge success 40% (2024) → 60% (2025) with Hawk-Eye feed access.
- MLB replay 2014: 47.5% overturned; 58.5/49.6/38.8% by game third (Imber 2015).
- Romer 2006: ≈2.1 pp WP/game; Liebman & Mahoney: last week 4.9× normal.

---

## (c) Twelve likeliest referee objections, the citation they would wield, and our pre-emptive response

1. **"The ninth-inning dump is exactly what your own DP predicts — where is the inefficiency?"** (Abramitzky et al. 2012; Krasker 2006; darts SSAC 2024.)
Response: We define the behavioral test as (i) WP forgone from *early* thresholds above q\*, (ii) share of team-games ending with unused tokens (9% use zero, 33% exactly two — B-Ref), and (iii) thresholds falling before option value vanishes; we report the value captured (AEKM's 96.8% analogue) with bootstrap CIs, not the raw 9th-inning success drop.

2. **"Success rates are selected — you cannot read perception from 58/48/38."** (AEKM Assumption 1; Chiappori–Levitt–Groseclose on aggregation; Martell on team policies.)
Response: We observe every taken pitch with Hawk-Eye truth, so we estimate P(challenge | true distance, state, role) directly (psychometric σ and criterion c, Mather 2008 / Flannagan et al. 2024 style), test invariance by role, use stakes and tokens as exclusion restrictions, and analyze within role/player with shrinkage.

3. **"Your umpire-accountability effect is the 2025 grading-buffer change and the 2026 coordinate change, not challenges."** (Andrews May 2025; Savant CSV docs; Clemens Apr 28, 2026.)
Response: Identification uses within-week AAA 2023–24 full-ABS vs challenge days (same umpires, same zone), spring-2025 park variation, and 2026 within-game variation in tokens remaining (Holder et al. anticipation test); all locations re-derived from the 9P on the mid-plate plane with legislated zones for every year.

4. **"Runs, not wins: a run is a run."** (Clemens 2026a; Statcast RE288 practice.)
Response: We show where WP- and RE-optimal cutoffs agree (middle innings, close games) and where they diverge (late, lopsided, token-dependent), and quantify the decisions that flip; the token expires at game end, so its shadow price is inherently state-dependent (Talluri & van Ryzin bid prices).

5. **"Your WP model is noisy; declaring decisions sub-optimal overstates certainty."** (Brill, Yurko & Wyner 2025.)
Response: Bootstrap WP288 and the DP; classify decisions as clear-challenge / clear-hold / ambiguous; report results excluding the ambiguous band; validate RE288 against Statcast `delta_run_exp` cell-by-cell.

6. **"Hawk-Eye is not truth; edge cases are coin flips."** (Collins & Evans 2008/2012; Borooah 2016; Jedlovec 0.25 in.)
Response: We treat |d| < 0.25–0.5 in as a measurement band, report robustness excluding it, and reproduce ≥99% of ABS rulings from public 9P + certified heights (UmpScorecards precedent) — disagreements themselves estimate the edge error.

7. **"You have one partial season; effects are small and unstable."** (Deshpande & Wyner on single-season ranks; Pope & Schweitzer; Yam & Lopez slow learning.)
Response: Player/team effects reported with intervals and split-half reliability (Rosales & Spratt benchmarks 0.86/0.77/0.50/0.46); AAA 2025 provides an out-of-sample year for promoted players; magnitudes stated in runs/wins with year-specific conversions and compared to Romer/Kovash–Levitt benchmarks.

8. **"Framing already captures this; you are re-labeling catcher skill."** (Judge et al. 2015; Deshpande & Wyner 2017; Statcast accounting.)
Response: We follow Statcast's initial-call/overturn split, show framing and challenge accuracy are distinct traits (Petriello ≈0 correlation; Andrews' inverse pattern), and model the equilibrium: P(challenge | stolen strike, catcher) and catcher over-confidence by location.

9. **"Umpire count effects are Bayesian, not bias — your 'accountability' story presumes bias."** (Green & Daniels "Bayesian Instinct" 2021; MacMahon & Starkes 2008.)
Response: We do not need the mechanism: we test whether the count-specific *criterion* moves under reviewability (Clemens' early hint that the two-strike contraction is vanishing) and whether the error mix shifts toward the less-challenged type (Almog et al.), which is a prediction about incentives regardless of the prior's rationality.

10. **"Tennis players were near-optimal with fast public feedback; baseball's decision is a team problem — agency, not cognition."** (AEKM contrasting Romer; Anbarci shame costs; Martell interviews.)
Response: That is a feature: we estimate a WP-equivalent "psychic cost of a failed challenge" and test whether it differs by role and by team policy (Reds/Rays/White Sox), the first evidence on agency costs in a shared token.

11. **"Rule counterfactuals are simulations under your model."** (Guyon 2021; Banchio & Munro humility.)
Response: We anchor each counterfactual to a real regime — AAA 3 → 2 tokens (2024 → 2025), NBA second-token rule (44% → 59%), NCAA 3 tokens, KBO buffer/two-plane zone, NHL cost-of-failure — and report directional agreement before quantitative predictions; we say "not globally optimal."

12. **"Public dashboards and media attention contaminate your learning estimates."** (Yam & Lopez regime shift after public tools; Oyster/Savant/FanGraphs.)
Response: Learning is measured on the gap-to-optimal within season with player composition and umpire accuracy held fixed, with a Hawthorne caveat stated; AAA 2025 (no MLB media) is a comparison; we report volume vs. accuracy learning separately (B-Ref: volume +20%, success flat).
