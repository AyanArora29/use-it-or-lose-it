# METHODS_hedge_pitchclock.md — pre-registered plan for the hedge abstract (v0.1, 2026-08-17)

*"Forced tempo": a dose-response test of the pitch clock on pitcher fatigue and injury.* Author: [withheld during blind review]. Decision point Sep 15: file as a second SSAC27 abstract only if the ABS paper is on track and Tier-1 results below exist.

## Question and hypotheses
The 2023 pitch timer (15 s bases empty / 20 s runners on; 18 s with runners from 2024) forced pitchers who were slow in 2022 to compress their between-pitch rest by far more seconds than fast pitchers. **H1:** within-outing fastball velocity decay (mph per 10 pitches, controlling for pitch count) worsened more, post-2023, for pitchers with larger forced compression. **H2:** the hazard of an arm/forearm IL placement rose more for high-compression pitchers (event-study around 2023, with 2024 as a second step). **H0 is a legitimate headline:** a well-powered null on velocity decay would resolve the contradiction between the clinical literature's pre/post counts.

## Data (public)
- Baseball Savant Pitch Tempo leaderboards 2015–2026 (seconds between pitches, bases empty/occupied, per pitcher-season) — pre-period tempo defines the dose.
- Statcast pitch-level 2015–2026 (release_speed, spin, release point, pitch number within outing, pitcher, game) — within-outing decay outcomes; timestamps from StatsAPI feeds as a check on realized tempo (2026 sample; feeds for other seasons only if cheap).
- StatsAPI transactions 2015–2026 — IL placements with description text classified into arm/forearm/elbow/shoulder vs other; days lost.
- Exclusions: 2020; position players pitching; openers/bulk relievers flagged.

## Design
- Dose D_i = max(0, tempo_2022,i − limit) separately for empty/runners-on states, weighted by 2022 pitch mix; alternative doses: 2021–22 average; rank-based.
- Outcomes: (a) slope of velocity on within-outing pitch number (fastballs only, per outing) → outing-level decay; (b) release-point drift; (c) IL hazard.
- Estimator: pitcher fixed effects; event-study interactions of D_i with season indicators (2015–2026, ref. 2022); clustered SEs by pitcher; placebo: hitters' outcomes; also a "sham" dose from 2019 tempo on 2020–22 outcomes.
- Confounds addressed: velocity trends (season FE), sweeper adoption (pitch-mix controls), age (age×season), workload (pitch counts), 2023 co-rule changes (shift ban does not affect pitcher fatigue; disengagement limits — controlled via runners-on states).
- Power: >1,000 pitcher-seasons; velocity decay has high precision; IL events rare (~150–200 arm IL/yr) — report minimum detectable effects.

## Deliverables (Tier 1 for a Sept-15 decision)
Event-study figure of decay by dose tercile; IL hazard ratios; a one-sentence result with CI; repo with the tempo/velocity/IL tables.
