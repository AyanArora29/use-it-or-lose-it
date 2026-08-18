# METHODS_REVIEW.md — adversarial design review of METHODS.md v0.1 (2026-08-17)

Five referee personas (academic statistician, sports economist, front-office R&D director, umpire/replay-operations expert, industry-panel judge) attacked v0.1; 47 objections were raised; skeptic verification ran on the majority (the rest were cut off by a compute limit and are treated as surviving). Below: the objections that changed the plan, what changed, and the ones we rejected but will pre-empt in the paper's limitations.

## A. Fatal (plan could not proceed as written)
| # | Objection (persona) | Disposition in v0.2 |
|---|---|---|
| A1 | Statcast `description`/`type`/`delta_*` almost certainly record the **post-challenge (corrected) call**; the umpire's original call is not in the pitch table, so §3 (zone validation), §5 (perception), §8 (umpire behaviour), §9 (framing) are all mis-specified until the original call is recovered. (front office, rules, statistician) | New §2.1 **data-verification protocol** with pass/fail criteria: reconstruct `call_original` from the StatsAPI feed (challenge/review events), keep `call_final`, 200-pitch manual audit, join-key match rate > 99%, reconcile counts/overturn/role split against Baseball-Reference. All umpire/framing/perception outcomes defined on `call_original`. |
| A2 | σ_role and τ(·) are not separately identified from the three-outcome model as written; role ranking is confounded by selection, team eligibility policy, and measurement error in d. (statistician, economist, front office) | §5 rewritten as **two tiers**: Tier 1 descriptive (binned P(challenge | d̂, role, inning, tokens), P(overturn | challenged, d̂, role)) carries the abstract; Tier 2 structural adds a measurement-error term (σ_meas identified from challenged pitches), an eligibility/hurdle component π_role,team, σ estimated within teams that allow both roles, location-region controls, and a pre-registered simulation-recovery test. |
| A3 | Bellman inequality double-counts the flip gain and V is undefined; token state {0,1,2,3} is wrong; opponent tokens and the extras grant need explicit treatment. (statistician, economist, rules) | §6 rewritten with one value function on the full state, correct Bellman comparison, MTV derived, t ∈ {0,1,2}, extras-grant rule cited with both readings pre-registered, own×opponent token DP solved as robustness. |
| A4 | Six questions is a dissertation; nothing is designed to finish by Oct 1; the headline is not identifiable. (judge) | New §0: one headline sentence, a Sept-15 fallback result that needs only the challenge-event table plus a WP lookup, Tier-1/Tier-2 labels on every component, Q4–Q6 demoted to extensions. |

## B. Major (accepted, plan amended)
- **B1 p is a posterior, not a primitive** → p(m) is computed against the empirical prior f(d | call, location region) estimated from all 2026 called pitches; the deliverable is a break-even *probability* card, inches only in an appendix.
- **B2 Capture ratio compares a noisy actor to an oracle and ignores failed-challenge cost** → three benchmarks (oracle / information-constrained optimum / observed); ratio defined against the information-constrained optimum; failed challenges valued at −MTV; shortfall decomposed.
- **B3 The 9th-inning "dump" is partly optimal (expiring token, extras grant)** → dump index redefined as WP-weighted excess Σ max(0,(p*−p̂)(g+MTV)) by score state, plus a model-free test (overturn rate and |d̂| by tokens-remaining at fixed leverage/count).
- **B4 Learning confounded by composition, race status, umpire/framing response** → within-player and within-team event-time regressions of the residual (p̂ − p*) with month FE, playoff-odds controls, arrival prior fixed at April; contract-status heterogeneity as a pre-registered secondary.
- **B5 Umpire designs**: spring DiD underpowered/non-random; 2026 vs 2023–25 confounded by the 2025 evaluation buffer cut (2 in → 0.75 in) and 2026 zone redefinition; within-game event study confounded by regression to the mean; accuracy measured against a zone umpires were never asked to call → primary estimand = change in count-bias contrast on the fitted GAM surface at fixed d grid, 2026 vs 2025, with 2024→2025 placebo; zone-geometry shift reported separately from bias; borderline defined relative to the umpire-season's own 50% contour; within-game design becomes a sharp RD in d among challenged pitches; spring DiD and Triple-A demoted to exploratory and made conditional on a rule-version table.
- **B6 No primary specification / family-wise control; power for reliability and heterogeneity claims** → per-hypothesis primary estimand + spec + numeric threshold; three confirmatory hypotheses, the rest exploratory; hierarchical variance-components (all called pitches) instead of split-half correlations.
- **B7 Uncertainty not propagated; second-half validation leaks** → full-pipeline game-clustered bootstrap (≥200 reps, ε resampled), MC-error check, fit through July 31 / evaluate Aug–Sept.
- **B8 Zone: variant chosen post hoc; roster heights wrong; propagation anchor; measurement error unquantified; go/no-go missing** → primary variant pre-registered (any-part, midpoint, published height rule); anchor on plate_x/plate_z + 9P increment; per-batter effective-height offset with shrinkage; σ_meas estimated; go/no-go at 90% agreement with a probabilistic strike model as fallback.
- **B9 Eligibility over-inclusive** → explicit eligibility definition (exclude automatic ball/strike, pitchouts, intentional balls, HBP; flag check-swing).
- **B10 Rule-design lab unauditable / Lucas critique** → three pre-named counterfactuals, one bar each (miscalls corrected/game vs seconds added), two arrival regimes as bounds, ∞-token as mechanical bound only.
- **B11 Deliverable form** → the "challenge card" (≤8 cells, plain-language confidence rules, WP cost of the simplification vs the full DP); token value reported in WP/game, wins/162, and dollars at a pre-registered $/win.
- **B12 Blowouts, pre-2020 extras, 7-inning doubleheaders, position players pitching contaminate WP-by-count/arrivals** → exclusions added.

## C. Rejected or already handled (pre-empt in the limitations section)
- "WP objective assumes team win maximization" — kept as the normative benchmark; individual-incentive test added as secondary (B4).
- "Arrival process depends on regime" — accepted as a caveat with bounds (B10), not a redesign.
- "Structural MLE is indefensible for a 16-year-old" — Tier 2 only; the abstract rests on Tier 1; the author must be able to explain the toy DP and the descriptive tables, which are the paper's spine.
- "Drop §8 entirely" — reduced, not dropped: the RD around overturns is intuitive, needs only 2026 data, and yields one memorable chart.
- Triple-A geometry changed year to year — handled by the rule-version table; AAA analyses only where documented.

## B. Code review round (2026-08-18, after data contact) — findings and dispositions

Independent adversarial review of the analysis code (wp_count.py, wp_model.py, challenges_extract.py, build_opps_2026.py, perception_fit_2026.py, dp.py, dp_fast.py, tier1_dp_2026.py, decompose_2026.py, counterfactuals_2026.py) against METHODS §2–§7.

| # | severity | finding | disposition |
|---|---|---|---|
| 1 | high | WP cube did not end the game when the top of the 9th+ ended with the home team ahead; game-ending strike-three cell mispriced (65% of such opportunities clipped to g = 0) | fixed in wp_count.build_cube and wp_model.wp_after_pitch; capture 0.815 → 0.817 |
| 2 | high | capture ratio is a mechanical function of σ; σ from the pooled probit is an upper bound on perception noise | stated as conditional; player-fixed-effects σ added to robustness (capture 0.80); paper wording changed |
| 3 | medium | "within-team σ" replaced cell effects instead of adding them (reported σ_within > σ_pooled) | replaced by two-way probit (cell + team; cell + player) |
| 4 | medium | extras grant not applied to the stored V (MTV1 at the top of the 10th reported as 0.88 pp instead of 0) | fixed in dp.py and dp_fast.py |
| 5 | medium | V(2) at first pitch (2.49) and simulated optimum (2.59) are two numbers for one estimand | headline = simulated optimum on actual streams; V(2) reported as ex-ante state value with the reason |
| 6 | medium | unsmoothed count-conditional transitions: walk cells differed by strike count (up to 3.9 pp) | terminal counts pooled; thin cells shrunk toward base-out transitions |
| 7 | medium | g clipped at 0 for 2.7% of opportunities; 256 real challenges on g = 0 | fixed cube reduces to 2.2% / 148; clip justified (first-base-open 3-0 states); dump index excludes g = 0 |
| 8 | medium | in-sample fitting vs the pre-registered leakage-free split | split added to robustness (fit ≤ Jul 31, evaluate August: capture 0.83) |
| 9 | low | per-band "share of gap" not a decomposition when negative | levels reported; wording fixed |
| 10 | low | oracle and "unlimited tokens" rows identical | merged with the explicit statement (with retention a perfect challenger never loses a token) |
| 11 | low | bootstrap pseudo-game id collisions; card cells used per-side terciles | fixed (unique ids; pooled terciles as in build_card) |
| 12 | low | half-innings beyond the 12th collapse into one state (33 opportunities) | documented |
| 13 | low | base/score state from Statcast pre-pitch fields | documented (Statcast fields are pre-pitch; outs cross-checked 100%) |
| 14 | low | numerator scored by ABS verdict, denominator by zone truth | numerator now scored by truth; verdict-scored value reported alongside |
| 15 | low | Savant per-player reconciliation exact for 70–89% of players (snapshots a day apart; a few counts exceed Savant's) | reported as is; attribution to be re-checked once both snapshots align |
