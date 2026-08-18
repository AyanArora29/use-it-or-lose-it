# 20 — Annotated bibliography (synthesis of lit/01–11)

Compiled 2026-08-17 from the eleven domain notes. ★ = must-cite (27 starred). Each entry: citation · URL/DOI · one-line finding · why we cite it. Access flags: [F] read in full by a reader; [A] abstract/summary only; [WP] working-paper version read; [B] blog/practitioner; [R] rule text/primary. Numbers are as reported in the domain notes; re-verify anything that will appear in the paper.

---

## A. Review rights as a decision problem (tennis, DRS, NFL/NBA/NHL, theory)

★ **Abramitzky, R., Einav, L., Kolkowitz, S., & Mill, R. (2012).** "On the Optimality of Line Call Challenges in Professional Tennis." *International Economic Review* 53(3): 939–964. doi:10.1111/j.1468-2354.2012.00706.x. PDF: web.stanford.edu/~leinav/pubs/IER2012.pdf. [F]
Finding: 2,008 ATP challenges 2006–08 (2 unsuccessful/set); challenge iff q > q\*(s,c) = ΔV(token)/(ΔV(token)+stakes); success falls with importance (−3–4 pp per SD) and rises with tokens/points left; players capture 96.8% of optimal value but under-challenge (excess propensity −0.064); no learning 2006–08.
Why: our intellectual anchor — the DP, the "success rate as threshold signature" identification (Assumption 1), and the near-optimality benchmark we test in baseball with a better denominator (every pitch observed).

★ **Nadimpalli, V. K., & Hasenbein, J. J. (2013).** "When to challenge a call in tennis: A Markov decision process approach." *JQAS* 9(3): 229–238. doi:10.1515/jqas-2012-0051. [A; 2010 UT thesis read F]
Finding: multi-chain average-reward MDP over a game with discrete belief levels; optimal policy non-monotone in strength ("very weak or very strong players should not challenge" in some states).
Why: precedent for a discrete-belief MDP and for testing non-monotonicity of the ABS threshold in run differential.

★ **Clarke, S. R., & Norman, J. M. (2012).** "Optimal challenges in tennis." *JORS* 63(12): 1765–1772. doi:10.1057/jors.2011.147. [A]
Finding: DP over game/set; "be more aggressive in the latter stages ... and when their opponent is ahead"; optimal use lifts an even five-set match to 59% (model number).
Why: comparative statics we replicate (late/behind aggressiveness); warn that 59% is model-based.

★ **Mather, G. (2008).** "Perceptual uncertainty and line-call challenges in professional tennis." *Proc. R. Soc. B* 275: 1645–1651. doi:10.1098/rspb.2008.0211. [A + secondary]
Finding: 1,473 challenges fit by a cumulative-Gaussian perceptual model; players and judges both <40 mm positional SD; judges more reliable than players.
Why: template for our role-specific psychometric perception model (P(challenge | true distance)).

**Whitney, D., Wurnitsch, N., Hontiveros, B., & Louie, E. (2008).** "Perceptual mislocalization of bouncing balls by professional tennis referees." *Current Biology* 18(20): R947–R949. [key results]
Finding: 84% of 83 referee errors on 4,457 Wimbledon points were in the direction of ball motion (called "out" on balls that were in).
Why: officials' errors are directional → which call type to challenge; AEKM calibrate p_close = 2% from it.

★ **Almog, D., Gauriot, R., Page, L., & Martin, D. (2024/25).** "AI Oversight and Human Mistakes: Evidence from Centre Court." arXiv:2401.16754 (v3); ext. abstract *ACM EC '24* doi:10.1145/3670865.3673481. [F]
Finding: after Hawk-Eye challenges, umpire error within 100 mm fell ≈8% but calls shifted toward "in" (Type II up 8.6 pp for balls 20–40 mm out); umpires weighted overturnable errors 37% more; effect built over 12–18 months.
Why: the direct template for our umpire-accountability pillar (directional shift toward the less-challenged error type).

**Anbarci, N., Lee, J., & Ulker, A. (2016).** "Win at All Costs or Lose Gracefully...? Gender Differences in Professional Tennis." *J. Sports Economics* 17(5): 536–560. doi:10.1177/1527002514531788. [F]
Finding: adds shame/pride to AEKM; "embarrassing" challenges (>50 mm out) 17% overall, 34% for men in tiebreaks; men's challenges correlate with opponents' (r = 0.16).
Why: a physical "low-quality challenge" metric we port (>1 ball radius outside), tiebreak desperation = 9th-inning analogue, contagion test.

**Kovalchik, S. A., Sackmann, J., & Reid, M. (2017).** "Player, official or machine?: uses of the challenge system in professional tennis." *IJPAS* 17(6): 961–969. doi:10.1080/24748668.2017.1410340. [A]
Finding: AO 2016, 1,037 challenged vs 154,648 unchallenged shots; prior successful challenge raises challenging (OR 1.84); importance OR 1.12.
Why: only tennis paper with the unchallenged denominator; hot-hand-after-success hypothesis.

**Collins, H., & Evans, R. (2008; 2012).** *Public Understanding of Science* 17(3): 283–308; 21(8): 904–921. [A]
Finding: Hawk-Eye reconstructions presented as definitive despite ±3.6 mm error; cricket's "umpire's call" honestly conveys uncertainty, tennis does not.
Why: ABS's "any part touches" rule with no tolerance is the tennis model; frame Hawk-Eye truth as measurement, not fact.

**Bassetti, T., Bonini, S., Pacicco, F., & Pavesi, F. (2019).** "Play it again! A Natural Experiment on Reversibility Bias." Marco Fanno WP 0238, U. Padova. [WP]
Finding: ace ratio +1.35–1.51 pp after challenges introduced (line judges make more definitive calls once reversible).
Why: second evidence that reviewability changes officials; cite cautiously (indirect proxy).

**Sackmann, J. (2013; 2016).** Tennis Abstract blog: "How Much Is a Challenge Worth?" (Mar 9, 2016); "Challenges by Gender" (Sep 1, 2013). [B]
Finding: ATP ≈1 challenge/60 points, ~30% overturned; running out then facing a wrong call ≈ once per 320 sets, costing 12.4 pp set-WP.
Why: only public tennis "value of a challenge" simulation; men 7.5 vs women 3.4 challenges/match.

★ **Shivakumar, R. (2018).** "What Technology Says About Decision-Making: Evidence From Cricket's DRS." *J. Sports Economics* 19(3): 315–331. doi:10.1177/1527002516657218. [A + WP summary]
Finding: 1,201 Test reviews 2009–14, 25.8% reversed; "out" calls reversed more than "not out"; no home bias in third-umpire outcomes.
Why: peer-reviewed DRS baseline; role asymmetry (batter- vs captain-initiated).

**Borooah, V. K. (2016; 2023).** "Upstairs and Downstairs: The Imperfections of Cricket's DRS." *JSE* 17(1): 64–85; "Adjudication in Cricket," MPRA 123268. [F 2023]
Finding: decomposes reversals into umpire error vs Hawk-Eye error (23% of "reversals" may be technology error at 95% specificity); "DRS cannot ... eliminate the howler because players make speculative referrals of marginal decisions."
Why: technology-error decomposition and the howler-vs-marginal tension = our threshold problem; design opinions on tokens/retention.

★ **Chowdhury, S. M., Jewell, S., & Singleton, C. (2024).** "Can awareness reduce (and reverse) identity-driven bias in judgement? Evidence from international cricket." *JEBO* 226: 106697. [WP]
Finding: COVID home-umpire era: home-batter LBW advantage vanished/reversed; umpire's-call outcomes for home batters +123%, overturns −40% — over-correction lives in marginal calls; confounded by 2→3 reviews.
Why: umpires under scrutiny over-correct at the margin — the cricket twin of our accountability tests.

**Sacheti, A., Gregory-Smith, I., & Paton, D. (2015).** "Home bias in officiating: evidence from international cricket." *JRSS-A* 178(3): 741–755. [summary]
Finding: two home umpires → away batters 16% more LBWs; bias gone with two neutrals.
Why: personnel vs technology as accountability remedies.

**Davis, C. (2017).** "The art of the review." *The Cricket Monthly*. — **Bayliss, E. (2020).** "DRS: The story so far," Red Ball Data. — **Date, K. (2021).** A Cricketing View posts. [B]
Finding: batters succeed 34–37% vs fielding sides 20–21%; under the 2013–17 80-over top-up rule, success in overs 60–80 fell to 20% vs 28% ("use it or lose it"); reviews/Test 9.0→14.3 when tokens 2→3.
Why: best descriptive DRS analytics; a documented token-expiry dump and token elasticity.

**ICC Playing Conditions, Appendix D (Player Review)** + ESPNcricinfo Jan 2009 (Lorgat: 3→2 "frivolous"), May 2011 (ODI 2→1 "hunch"), Sept 2017 (retention on umpire's call), July 2020 (Tests 3). [R]
Why: verbatim rule text and the league's own reasoning about token counts.

**Spitz, J., et al. (2021).** "Video assistant referees (VAR)..." *J. Sports Sciences* 39(2): 147–153. [A]
Finding: 2,195 matches; accuracy 92.1→98.3%; 9,732 checks (median 22 s).
Why: referee-initiated, no-token benchmark.

**Holder, U., Ehrmann, T., & König, A. (2022).** "Monitoring experts: insights from the introduction of VAR." *J. Business Economics* 92: 285–308. [A]
Finding: post-VAR, initially awarded penalties fell >25% and reds >30% while season totals stayed flat (referees defer to review); Serie A added-time home bias vanished.
Why: "anticipation effect" — do umpires stop calling edge strikes when the batting team holds tokens?

**NBA Rule 14; NBA release Dec 2020; Sprung (Forbes, Jan 2020); Axios (May 2024); Blazer's Edge (Jan 2025).** [R/B]
Finding: 2019-20: 633 challenges, 44%; success by quarter 65/53/45/39%, 51% of challenges in Q4; after 2023-24 second-token-on-success rule: 1,282 challenges, 59.2%.
Why: closest live structural analogue (1 token, +1 on success); retention-rule natural experiment.

**NHL rule releases 2017/2019 (nhl.com; Scouting the Refs); Chicago Sun-Times (Feb 2020).** [R/B]
Finding: switching failure cost from timeout to 2-min penalty cut goalie-interference challenges ~2/3 and doubled success (24→48%).
Why: cost-of-failure comparative static.

**Krasker, W. S. (2006).** "A Model for Coaches' Challenges." footballcommentary.com. [B]
Finding: backward-induction DP; value of holding two vs one challenge only 0.002 WP; last challenge worth 0.006–0.011 WP; coaches too conservative.
Why: direct ancestor of our DP in a team sport.

**Burke, B. (2014).** "Analyzing Replay Challenges." Advanced Football Analytics. [B]
Finding: break-even B = (N−U)/(R−U) ≈ 3–12% reversal probability.
Why: the one-line threshold rule we generalize with an option-value term.

**Imber, L. (2015).** "Reviewing Instant Replay..." *SABR Baseball Research Journal* 44(1). — **Wolfersberger, J. (2014)** and **Illarionov, K. (2017)**, *The Hardball Times*. [F/B]
Finding: MLB 2014 replay 47.5% overturned; overturn 58.5/49.6/38.8% by game third; Illarionov: challenge whenever p(success) ≳ 20%; "challenge as much as he can."
Why: baseball's pre-ABS renewable-token right and its inning gradient.

**FIFA "Football Video Support" (2024–), IFAB VAR protocol.** [R]
Why: DRS-style coach challenge in soccer (2 per match, retained on success); VAR as no-token contrast.

---

## B. Optimality, learning, expiring budgets

★ **Romer, D. (2006).** "Do Firms Maximize? Evidence from Professional Football." *JPE* 114(2): 340–365. [F]
Finding: teams kicked on 959 of 1,068 fourth downs where going was better; ≈2.1 pp WP/game (~1 win per 3 seasons).
Why: canonical "professionals deviate systematically" template and presentation style (optimal vs observed, priced in WP).

★ **Liebman, J. B., & Mahoney, N. (2017).** "Do Expiring Budgets Lead to Wasteful Year-End Spending?" *AER* 107(11): 3510–3549. doi:10.1257/aer.20131296. [A + WP]
Finding: last-week federal spending 4.9× normal; year-end IT projects 2–6× more likely low quality; rollover fixes it.
Why: theory/vocabulary for the "9th-inning dump" and for retention/extra-inning grants as rollover.

**Pope, D., & Schweitzer, M. (2011).** "Is Tiger Woods Loss Averse?" *AER* 101(1): 129–157. [A]
Why: experts with high stakes remain biased; reference-point tests (protecting a lead; visible wasted challenge).

**Palacios-Huerta, I. (2003).** "Professionals Play Minimax." *REStud* 70(2): 395–415; **Chiappori, Levitt & Groseclose (2002).** *AER* 92(4): 1138–1151. [F]
Why: near-optimality in simple, frequent, fast-feedback decisions; warning that pooled tests across heterogeneous agents mislead (analyze within role).

**Kovash, K., & Levitt, S. (2009).** "Professionals Do Not Play Minimax." NBER WP 15347. [A]
Why: counterweight; ≈2 wins/yr magnitude benchmark.

**Yam, D., & Lopez, M. (2019).** "What was lost? A causal estimate of fourth down behavior in the NFL." *J. Sports Analytics* 5(3): 153–167. [A]
Why: no learning 2004–16 until public tools; ≈0.4 wins/yr forgone; matching template.

**Brill, R., Yurko, R., & Wyner, A. (2025).** "Analytics, have some humility..." *The American Statistician*. arXiv:2311.03490. [A]
Why: bootstrap DP thresholds; classify ambiguous decisions before scoring "errors."

**Sandholtz, N., Wu, L., Puterman, M., & Chan, T. C. Y. (2023).** "Learning Risk Preferences in MDPs: ... Fourth Down." arXiv:2309.00756. [A]
Why: inverse-optimization template — report revealed thresholds as an implied risk/misperception parameter.

**Derman, Lieberman & Ross (1972)** *Mgmt Sci* 18(7); **Weitzman (1979)** *Econometrica* 47(3); **Talluri & van Ryzin (1998)** *Mgmt Sci* 44(11); **Dixit & Pindyck (1994).** [foundations]
Why: sequential stochastic assignment, reservation values, bid prices, option value of waiting — q\*(s,c) is a bid price.

**Gibbs, C., Elmore, R., & Fosdick, B. (2022).** "The causal effect of a timeout at stopping an opposing run in the NBA." *AoAS* 16(3). [A]
Why: timeouts as scarce resource; measured value small ≠ misused.

---

## C. Umpire bias, accuracy, monitoring

★ **Green, E., & Daniels, D. (2014).** "What Does it Take to Call a Strike? Three Biases in Umpire Decision Making." *MIT SSAC 2014*. PDF: homepage.divms.uiowa.edu/~dzimmer/sports-statistics/greenanddaniels.pdf; follow-up "Bayesian Instinct" SSRN 2916929. [F]
Finding: 1.03M calls 2009–11; borderline P(strike) ≈31% at two strikes vs ≈58% at three balls; previous strike −17 pp; average umpire needs 64% certainty to call strike three; "the ring ... from 10% to 90% is a foot wide."
Why: Sloan lineage; count/previous-call thresholds define where challenge value lives; we re-estimate under accountability.

★ **Rosales, J., & Spratt, S. (2015).** "Who Is Responsible For A Called Strike?" *MIT SSAC 2015*. [F]
Finding: Strike Zone Plus/Minus splits credit among catcher/pitcher/batter/umpire; 0.1189 runs/strike; even/odd reliability C 0.86, U 0.77, B 0.50, P 0.46; "the strike zone will likely remain the final stronghold of the umpire's influence."
Why: four-actor template for role-level perception; the quote our paper overturns.

★ **Zhan, J., Gerstner, L., & Polimeni, J. (2020).** "Measuring the Impact of Robotic Umpires." *MIT SSAC 2020*. [F]
Finding: 2.87M Kaggle pitches 2015–18; fixed 18-in zone, constant height; 0.065 runs per missed call; ~3× more strikes miscalled as balls; asks for a height-adjusted zone and a "batter's eye" analysis.
Why: the Sloan predecessor whose two open items we answer; the fixed-zone flaw we fix.

★ **Kim, J. W., & King, B. G. (2014).** "Seeing Stars: Matthew Effects and Status Bias in MLB Umpiring." *Management Science* 60(11): 2619–2644. doi:10.1287/mnsc.2014.1967. [F]
Finding: 756,848 calls 2008–09; each All-Star appearance +4.8% odds of ball-called-strike; base errors 18.8% of strikes called balls, 12.9% of balls called strikes; 0-2 −62% / 3-0 +49% odds.
Why: status effects → challenge value depends on who is pitching; error base rates.

★ **Parsons, C., Sulaeman, J., Yates, M., & Hamermesh, D. (2011).** "Strike Three: Discrimination, Incentives, and Evaluation." *AER* 101(4): 1410–1435. [WP F]
Finding: same-race favoritism +0.27 pp, present only in non-QuesTec parks, poorly attended games, non-terminal counts.
Why: cleanest evidence that scrutiny suppresses discretionary calls; cite with Tainsky–Mills–Winfree (2015) fragility caveat.

★ **Chen, D., Moskowitz, T., & Shue, K. (2016).** "Decision Making Under the Gambler's Fallacy..." *QJE* 131(3): 1181–1242. [F baseball section]
Finding: after a called strike, P(strike) −1.5 pp (−3.5 pp on ambiguous pitches); not make-up calls.
Why: sequence dependence enters the perception model; overturns as a sharper test.

**Moskowitz, T., & Wertheim, L. J. (2011).** *Scorecasting*. [reconstructed]
Why: home bias grows with leverage and reverses in QuesTec parks; cite with Birnbaum/Gentile caveats.

★ **Mills, B. M. (2017).** "Technological innovations in monitoring and evaluation: Evidence of performance impacts among MLB umpires." *Labour Economics* 46: 189–199. doi:10.1016/j.labeco.2016.10.004; also Mills (2014) *MDE* 35(6); Mills (2017) "Umpire Analytics," *SABR Book of Umpires*. [A + F]
Finding: accuracy 85.35% (2008) → 89.9% (2015) with QuesTec/Zone Evaluation feedback, more for younger umpires.
Why: monitoring/feedback improves accuracy — baseline against which adversarial, public review is a stronger treatment.

★ **Flannagan, K., Mills, B., & Goldstone, R. (2024).** "The psychophysics of home plate umpire calls." *Scientific Reports* 14: 2735. doi:10.1038/s41598-024-52402-y. Data: osf.io/hv68j. [F]
Finding: 3.0M pitches 2008–15; per-umpire psychometric threshold α and slope β; consistency +33% while home bias stayed ≈0.2 in ("bias ≠ accuracy").
Why: the α/β language for role-level perception and umpire heterogeneity.

★ **Archsmith, J., Heyes, A., Neidell, M., & Sampat, B. (2025).** "The Dynamics of Inattention in the (Baseball) Field." *Economic Journal* 135(671): 2192–2219. [WP F]
Finding: +1 SD leverage → +0.61 pp accuracy; cumulative past leverage −0.25 pp; attention as depletable budget.
Why: miss rate is leverage-elastic — our DP cannot assume a constant miss rate.

**Hsu (2024)** *JSE* 25(4); **Bradbury (2019)** *JSE* 20(6); **Tainsky, Mills & Winfree (2015)** *JSE* 16(4). [A]
Why: home bias persists; monitoring effects modest; race results fragile.

**Walsh, J. (2010)** THT "The Compassionate Umpire"; **Roegele, J. (2014)** THT Annual; **Andrews, D. (FanGraphs 2024–25)** accuracy series; **Andrews (May 5–6, 2025)** "Strike Zone Update" Parts 1–2; **Axisa (CBS, May 1, 2025)**. [B]
Finding: zone 3.52 sq ft at 3-0 vs 2.42 at 0-2; Statcast accuracy 92.4–92.8% (2022–25), shadow ~81–82%; **2025 umpire CBA cut grading buffer 2 in → 0.75 in**; shadow called-strike rate 42.7% (lowest ever) in early 2025.
Why: accuracy levels; the 2025 grading shock that confounds any 2025→2026 comparison.

**Gasparetto & Loktionov (2023)** PLOS ONE; **Işın & Yi (2024)** BMC SSMR; **Pettersson-Lidbom & Priks (2010)** Econ. Letters; **Dohmen & Sauermann (2016)** J. Econ. Surveys. [A]
Why: officiating bias under VAR/crowd removal — external validity of accountability effects.

---

## D. Catcher framing

★ **Deshpande, S. K., & Wyner, A. J. (2017).** "A hierarchical Bayesian model of pitch framing." *JQAS* 13(3): 95–112. doi:10.1515/jqas-2017-0027; arXiv:1704.00823. [F]
Finding: 308,388 frameable pitches 2014; umpire-specific slopes; count-specific run values 0.062 (0-0) to 0.540 (3-2), mean 0.11; catcher spread ≈50 runs with wide CIs; "cannot discriminate between good framers."
Why: canonical framing model; count-specific run values; interval honesty; umpire heterogeneity to re-estimate.

**Judge, J., Pavlidis, H., & Brooks, D. (2015).** "Moving Beyond WOWY: A Mixed Approach to Measuring Catcher Framing." *Baseball Prospectus*. [via SABR/D&W]
Why: industry-standard CSAA (r = 0.94–0.96 with D&W/FanGraphs).

**Cross, J. (2019)** "FanGraphs Pitch Framing"; **Appelman (2019)** "WAR Update: Catcher Framing!" [B]
Why: 0.135 runs/strike; umpires omitted; McCann +181.9 career.

**Marchi, M. (2011)** THT; **Turkenkopf, D. (2008)** BtBS; **Fast, M. (2011)** BP via **Lindbergh (2013)** Grantland. [B]
Why: origins; framing as an underpriced skill competed away — the dynamic Baumann predicts for challenge skill.

**Sullivan, J. (2017)** FanGraphs; **Vigderman, A. (2025)** SIS; **Andrews (Feb 27, 2023)** FanGraphs. [B]
Why: compression of framing spread (98 runs 2008 → ~half by 2025); bottom disappearing.

★ **Statcast catcher-framing glossary + Baseball Savant ABS metrics documentation (2026).** baseballsavant.mlb.com/abs-metrics-documentation; /leaderboard/catcher-framing. [R]
Finding: 0.125 runs/strike; from 2026 framing is booked on the umpire's *initial* call and overturns as separate "challenge skill"; "Challenge Opportunity" (~50% of pitches), "Reasonable Pitch" (~5%), Confidence Level breakeven = 0.2/(0.2+RV) — a *constant* token cost; 2026 zone redefined (mid-plate, height-based).
Why: MLB's own accounting and the constant-cost convention our DP replaces.

**Petriello, M. (Feb 26, 2026)** MLB.com "There's loads of ABS data..." [B]
Finding: AAA 2025: 9,432 challenges (1.1%), 50% overturned; fielders 55%/batters 45%; batter challenge rate 3.5% (1st) → 8% (9th); framing skill ≈ uncorrelated with challenge skill among 121 catchers.
Why: AAA baseline; framing ⟂ challenge skill hypothesis.

**Andrews, D. (Nov 24, 2025; Jun 10, 2026)** FanGraphs. [B]
Finding: spring 2025 C 56%/B 50%/P 41%; catchers ≈10 pp *less* successful challenging where they frame best (over-confidence).
Why: input to the framing/challenge equilibrium.

**Verducci, T. (Apr 13, 2026)** SI "Eight Early Effects of ABS"; **Cooper, J.J. (Sept 2025/Feb 2026)** BA "11 Things"; **Staph, J. (Mar 20, 2026)** Just Baseball; **CalledThird (Apr 5, 2026)** "Catcher Framing in the ABS Era." [B]
Finding: only 19% of 861 umpire-stolen strikes were challenged (Verducci); >98% of pitches still called by the umpire; framing–challenge correlation ≈0/slightly negative in tiny samples.
Why: "framing did not die"; deterrence hypothesis; credit CalledThird by name for the 2025 borderline strike-rate baseline.

---

## E. ABS rules, trials, 2026 analytics

★ **MLB press release (Sept 23, 2025).** "MLB announces ABS Challenge System coming to the Major Leagues beginning in the 2026 season." mlb.com/press-release/... [R]
Finding: 2 challenges/team, retained if successful, +1 per extra inning if none; pitcher/catcher/batter only, immediately, no help; zone 17 in wide, 53.5%/27% of certified height, mid-plate 2-D, any-part-of-ball; spring 2025: ~4/game, C 56/B 50/P 41%.
Why: authoritative rule and zone text.

**DeRosa, T. (Mar 27, 2025)** MLB.com spring-2025 results; **Blum, R. (AP, Sept 2025).** [B]
Finding: 288 games, 1,182 challenges, 52.2% won; rate 1.9% (inn. 1–3) → 3.6% (9th); full counts 8.2%; success 60/51/43/46% by inning block; 13.8 s per challenge.
Why: pre-rollout stylized facts (leverage gradient already visible).

★ **Baseball America (Norris, Mar 14, 2023; Glaser, May 5, 2023; Cooper, Aug 31, 2023; Mar 28, 2024; Jun 19, 2024; Jun 26, 2025; Sept 23, 2025).** [F]
Finding: Triple-A 2023: first three games of series full ABS, last three challenge; zone 17 in, 27–51%; Sept 2023 stance-based experiment; 2024: Tue–Thu full ABS / Fri–Sun challenge, top raised to 53.5%, all-challenge from Jun 25–26; 3 tokens 2023–24 → 2 in 2025; full-ABS vs challenge splits (2023 BB% 12.30 vs 10.45; 2024 11.78 vs 11.01).
Why: the identification calendar and zone history for the accountability pillar; correct the MLB.com "always 53.5/27" claim.

★ **Baseball-Reference, "2026 MLB ABS Challenge Analysis."** baseball-reference.com/friv/abs-challenges.shtml (Aug 17, 2026 pull). [F]
Finding: 7,975 challenges, 53.6% overturned, 4.27/game; C 58.6%, B 48.5%, P 37.7%; with two tokens in hand success 59.3% (1st) → 35.4% (9th); 3-2 counts 40.2%; usage 3.76 (Mar) → 4.60/game (Aug) with flat success; 9% of team-games use zero challenges.
Why: the 9th-inning dump and within-season volume learning in one public table.

★ **Clemens, B. (Apr 1, 2026).** "An Early, Nerdy Look At The Challenge System." FanGraphs. — ★ **Clemens (Apr 28, 2026).** "The Strike Zone Is Shrinking. Here's How." — **Clemens (May 12, 2026)** "Where Are 2026's Extra Walks Coming From?" [F]
Finding: RE288 pricing (3-2 flip w/ R3, 1 out = 0.84 runs); explicit "a run is a run" (rejects WP); only 29% of egregious called strikes challenged; 2026 called zone 454 → 439 sq in for a 6-footer, driven by umpire behavior not overturns; two-strike contraction "vanishing"; BB% 8.4 → 9.5.
Why: first analytics of challenges; the runs-not-wins position we test; the zone-shift measurement we build on.

★ **Martell, M. (Jun 19, 2026)** "To Challenge, or Not To Challenge"; **Oler, K. (Jun 22, 2026)** "Never Use an ABS Challenge in This One Weird Count"; **Jaffe (May 1, 2026)**. FanGraphs. [F]
Finding: 4,537 challenges/161,859 called pitches (2.8%); 3-2 counts 9.4%; challenged-pitch distance from edge 0.048 → 0.057 ft as leverage rises; team policies (Reds bar pitchers); leverage buckets: rate 2.3/3.4/4.6%, success 56.8/50.7/45.9%.
Why: revealed team policies and the AEKM fingerprint in 2026 data.

★ **Baumann, M. (Aug 11, 2026).** "Who's Getting Their Money's Worth From the ABS Challenge System?" FanGraphs. [F]
Finding: team challenge runs 18.1 (TB) to 33.6 (MIN); ≈1.25 wins best-to-worst; "teams ... could stand to be more aggressive"; concedes no opportunity-cost model.
Why: the claim our DP tests; league-scale stakes.

**Oyster Analytics (Lane & Riley, 2026)** dashboard + "The Oyster Guide to ABS Challenge," Down on the Farm Substack (Feb 25, 2026); Effectively Wild ep. 2444; **Tango (2026)** ABS cost-benefit posts (unread). [B]
Why: closest practitioner break-even tool (runs-based, opaque); state of practice; Hawthorne caveat for learning.

**Sawchik (Apr 3, 2026)**, **Greenspan (Mar 22–23, 2026)**, **Petriello (Feb 26, 2026)** MLB.com; **Boeck (Aug 3, 2026)** Yahoo. [B]
Why: 2026 tracker numbers, player poll (22 yes/41 no on pitcher challenges).

**Rudner, J. (Jul 15, 2026)** BA — NCAA D-I 2027: 3 challenges, 58%/23% zone; SEC tournament 2026: 56.2% overturned. [B]
Why: external anchors for token-count and geometry counterfactuals.

★ **Lee, K., Han, K., & Ko, J. (2025).** "Analyzing the impact of the automatic ball strike system ... KBO." *Scientific Reports* 15: 44459. doi:10.1038/s41598-025-28142-y; arXiv:2407.15779. [F]
Finding: KBO full ABS 2024: 47.18 cm width (2 cm buffer), 56.35/27.64% height, two planes; high-zone strike rate 57.3 → 79.8%; low-outside misjudgments 10.5 → 0.6%; batters not yet adjusting.
Why: what a pure machine zone does; KBO geometry as a rule-design counterfactual.

**Hwang, S., Kim, J., & Lee, S. (2026).** *Proc. IMechE Part P* 240(3): 863–874. doi:10.1177/17543371251395162. [A] — **Song, J., Kang, J. H., & Paulsen, R. J. (2026).** "Technology adoption and bias in officiating: ABS in Korean Baseball." *ESMQ*. doi:10.1080/16184742.2026.2681111. [NOT REACHED]
Why: KBO counterfactual outcomes (walks/WHIP up); Song et al. is the officiating-bias bridge — must retrieve.

**Wang, A. W.-Y., Kamino, W., Mimno, D., Levy, K., & Jung, M. F. (2026).** "Inside Baseball: The ABS as an Object Lesson in Technological Rule Enforcement." *ACM FAccT '26*. arXiv:2605.16237. [F]
Why: design rationale (mid-plate 2-D, height not stance, deference only on challenge); 54% player preference for challenge format.

---

## F. Win probability / run expectancy stack

**Lindsey, G. R. (1959; 1961; 1963).** *Operations Research* 7(2); *JASA* 56(295); *Operations Research* 11(4). [metadata]
Why: origin of RE and score-progress (proto-WP) tables.

★ **Tango, T., Lichtman, M., & Dolphin, A. (2007).** *The Book: Playing the Percentages in Baseball.* Potomac. + **Tango (2006)** THT "Crucial Situations" I–III; FanGraphs Library LI/WPA/WE. [F for THT/Library]
Why: RE24, run values by count, LI recipe (average swing 0.0346 wins) we generalize to pitch level.

**Bukiet, Harold & Palacios (1997)** *Op. Res.* 45(1); **Albert (2015)** *J. Sports Analytics* 1(1). [metadata]
Why: Markov half-inning construction; shrinkage for sparse cells.

**Baumer, Jensen & Matthews (2015).** "openWAR." *JQAS* 11(2): 69–84. doi:10.1515/jqas-2014-0098. [F]
Why: reproducible RE24 and resampling intervals; runs-per-win formula.

**Walsh, J. (2008)** THT "Searching for the game's best pitch." [F]
Why: count-value table (3-0 +.220; 0-2 −.106).

**Singer, E. (2020)** FanGraphs Community "Umpire Runs Created"; **Umpire Scorecards explainers.** [F]
Why: RE288/RED construct; xAcc; 2026 method (no tolerance, mid-plate; >99.5% agreement with ABS on ~1,600 challenged pitches).

**Statcast CSV docs; MLB StatsAPI winProbability endpoint; FanGraphs Guts (R/W 9.4–10.3); Clemens (Feb 24, 2026) $/WAR ≈ $11.2M.** [R]
Why: `delta_run_exp`, per-PA WP only (no public per-pitch WP); conversions.

**Lock & Nettleton (2014)** *JQAS* 10(2); **Deshpande & Jensen (2016)** *JQAS* 12(2). [metadata]
Why: WP-model methodology anchors.

---

## G. Perception by role

★ **Burris, K., et al. (2018).** "Sensorimotor abilities predict on-field performance in professional baseball." *Scientific Reports* 8: 116; SSAC 2018 "Eye on the Ball." [F]
Finding: 252 pros; perception span → OBP (+0.64 SD), K%; eye-hand → BB%; no effect on power.
Why: Sloan-pedigree evidence that zone discrimination is a measurable trait; their pitch-level future work is ours.

**Liu, S., Edmunds, F. R., Burris, K., & Appelbaum, L. G. (2020).** *IJPAS* 20(4): 683–700. [A]
Why: smooth-pursuit accuracy predicts O/Z-swing discipline.

**MacMahon, C., & Starkes, J. L. (2008).** "Contextual influences on baseball ball-strike decisions in umpires, players, and controls." *J. Sports Sciences* 26(7): 751–760. [A]
Why: only controlled umpires-vs-players comparison on identical stimuli; count context biases both.

**Kishita, Ueda & Kashino (2020)** *Front. Sports Act. Living* 2:3; **Mann, Spratford & Abernethy (2013)** *PLoS ONE* 8(3); **Bahill & LaRitz (1984)** *Am. Scientist* 72. [F/F/memory]
Why: batters cannot foveate the ball at the plane they are judging → role-specific perceptual SD motivation.

**Millslagle, Hines & Smith (2013)** *Percept. Mot. Skills* 116(1). [A]
Why: umpire gaze/vantage; optional.

---

## H. Zone geometry and Statcast physics

**Shenk, L. (Feb 5, 2026)** MLB.com "Looking ahead to MLB's new Ball-Strike Challenge System." [F]
Why: "measured at the midpoint," "one-sixth of an inch," certified heights (with the "all years" trap).

**Baseball Savant CSV documentation; Appelman (Mar 16, 2026) FanGraphs.** [F]
Why: plate_x/plate_z front-of-plate through 2025, mid-plate from 2026; sz_top/sz_bot ABS-defined from 2026.

**Kagan, D. (2009).** "The Anatomy of a Pitch: Doing Physics with PITCHf/x Data." *The Physics Teacher* 47(7): 412–416. [F]
Why: peer-reviewed coordinate conventions and 9P model.

**Nathan, A. M. (2008)** "A Statistical Study of PITCHf/x Pitched Baseball Trajectories" + pitchtracker.html; **Pendleton (2011)** Sportvision 9P note. baseball.physics.illinois.edu. [F]
Why: 9P is a fit; plate location derived; 0.55-in rms simulated plate error.

**Jedlovec, B. (Jul 20, 2020).** "Introducing Statcast 2020: Hawk-Eye and Google Cloud." MLB Technology Blog. [F]
Why: 12 cameras, 0.25-in accuracy at front of plate.

**Sievert, C. (2014).** "Taming PITCHf/x Data with XML2R and pitchRx." *R Journal* 6(1): 5–19; **Powers, S.** sabRmetrics (GitHub). [F]
Why: public plane-propagation code.

**Walsh, J. (2007)** THT "Strike zone: fact vs. fiction"; **Freiman, N. (2018)** FanGraphs; **Andrews (Dec 5, 2024)** FanGraphs; **Longenhagen (Sept 29, 2023)** FanGraphs. [F]
Why: any-part width ≈19.9 in; operator zone noise; height-zone area (with radius correction); measured-vs-listed heights.

**Official Baseball Rules (2021 ed.)** Rules 2.02, 3.01; glossary. [R]
Why: 17-in plate depth → 8.5-in midpoint; ball radius 1.43–1.47 in.

---

## I. Prior SSAC winners (form and lineage)

★ **"No More Throwing Darts at the Wall" (SSAC 2024 winner).** [F]
Why: MDP with dynamic credits — first credit most valuable, credits saved for the end, suggests "do-over" credits in other sports; closest structural precedent.

**Penalty-kick paper (SSAC 2025 winner, ID 20251395).** [F]
Why: revealed-vs-optimal wedge quantified as one scalar (3.12×); Romer framing.

**Banchio & Munro (2020 winner)** "A No-Tanking Draft Allocation Policy"; **Chan & Fearing (2013 winner)** roster flexibility; **Guyon (2021)** groups of three; **Melville et al. (2023; 2024)** BYU; **Berry & Fowler (2019)** RIFLE. [F/partial]
Why: rule design under incentive constraints; team-level value tables; enumerated counterfactuals; share-of-optimal-decision statistics (70%/48%); method + software release.

**duBoef et al. (SSAC 2026 finalist)** boxing judging, 7,323 rounds. [web]
Why: one-sentence officiating-measurement neighbor.
