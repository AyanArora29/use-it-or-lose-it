# Scientific and submission audit — September 26, 2026

The core allocation result survives correction. The strongest paper is an MLB challenge-allocation study with transparent model assumptions, a pitch-level data contribution, and a decision aid to test prospectively. It should not be sold as a causal estimate of season wins, an identified study of eyesight, or a completed set of umpire/framing causal studies.

This audit made local code/document changes and built a revised abstract. It did not submit an application, change the already-submitted CMSAC abstract, or push any repository changes. The GitHub rolling release still reflects the earlier code/results until a reviewed revision is published.

## Scope and evidence

Reviewed the supplied competition rules, submission form and prior-research materials; the active repository's extraction, geometry, WP, perception, policy, bootstrap, robustness and workflow code; the current abstract/PDF/build script; methods/review logs, submission notes, literature positioning, and stage talk. Earlier duplicates/archives were treated as historical context rather than alternate active implementations. The complete bibliography has not been independently verified citation by citation; current novelty claims were checked against the primary tennis paper and MLB documentation.

Baseline code: `a4f2c831c063560164222e3e3b9027aa617f2903` (local and remote matched before edits). The September 26 rolling release was downloaded into `audit/2026-09-26/release/`; exact asset IDs, times and SHA-256 hashes are in `snapshot_manifest.json`. The baseline code and a separate corrected working snapshot are retained. The dataset ends September 25, not season end. Live official MLB rules and SSAC guidelines were checked, and the three remaining challenged-pitch geometry disagreements were re-read against official StatsAPI game feeds.

## Result ledger

| Quantity | Published snapshot | Audited rebuild |
|---|---:|---:|
| Eligible games | 2,398 | 2,398 |
| Analysis opportunities after position-player proxy exclusion | 350,588 | 350,588 |
| Parsed / eligible challenges | 10,438 / 10,425 | 10,438 / 10,425 |
| Geometry/verdict agreement on eligible challenges | 99.7314% | 99.9712% |
| Observed nonnegative reversal value, pp/team-game | 2.1140 | 2.1100 |
| Approximate information-model policy, pp/team-game | 2.5543 | 2.5653 |
| Capture ratio | 82.7607% | 82.2514% |
| Card value, pp/team-game | 2.3687 | 2.3778 |
| Share of modeled gap recovered by card | 57.8% | 58.8% |
| Perfect-information value, pp/team-game | 6.4205 | 6.3680 |
| Refit bootstrap replicates | 100 | 200 |
| Refit-bootstrap conditional capture interval | 80.03%–85.33% | 79.45%–84.83% |

The revised abstract uses 82% [79–85%], 2.57 / 2.11 points, and 59% card gap recovery. Its two exhibits were regenerated from the same corrected snapshot. The refit-bootstrap point is 82.52%, slightly different from the 82.25% headline because it uses one policy stream and 30 evaluation draws rather than two and 200. The interval is conditional on fixed WP cubes, geometry, leverage cut points and model family.

The first three innings remain the largest component of the allocation gap: observed 0.619 challenges per team-game at 60.8% success; benchmark 0.968 at 47.7%. The benchmark corrects more calls in those innings (0.462 versus 0.377/team-game), although total corrections over all innings are slightly lower. The earlier abstract's claim that greater early value came without more calls corrected was misleading.

## Findings and actions

| Finding | Why it matters | Action / status |
|---|---|---|
| Square expansion of strike-zone corners | Overstated strikes where the round ball does not touch the rectangle; altered miss distances for both challenged and unchallenged pitches. | Fixed shared signed-distance geometry; recomputed every pitch's distance before fitting. Agreement improves by 25 challenged pitches, leaving three disagreements. |
| Different count classes across fit/card/bootstrap | 67,080 analysis pitches changed class relative to the old propensity fit; the policy and its simpler card did not share a consistent state definition. | Unified “either ruling can end PA” (three balls OR two strikes), refitted and rebuilt all results. Logged as a post-data correction. |
| Half-innings after 12 collapsed | The same opportunity block could be replayed in multiple late half-innings. There are 42 opportunities after inning 12 in this snapshot. | Distinct states through inning 20; explicit failure beyond supported horizon and for duplicate/uncovered half-inning paths. |
| Numerator changed between outputs | Main results used geometric truth while bootstrap/decomposition/counterfactuals used recorded verdicts. | Aligned primary scoring; preserved recorded verdict as an explicit sensitivity. |
| Observed-policy simulation used historical inventory | A simulated policy could lose a challenge but continue using a two-challenge fitted threshold. | Python and fast simulators now use simulated inventory; deterministic regression test reproduces this failure mode. |
| Missing direct-WP walk-off transition | A bases-loaded ball-four walk-off could retain a sub-100% home WP. | Fixed the terminal rule and tested all eight walk occupancy states, walk-offs and game-ending strikeouts. The existing primary cube was not rebuilt. |
| Out-of-time preprocessing leakage | Full-season cut points/cell support entered the training specification. | Refit cut points/cells on training games only; relabeled test period August–September. Corrected holdout capture is 85.6% over 748 games. It remains retrospective model validation. |
| Silent failures could publish incomplete output | Fetch, extraction and analysis errors could be converted to warnings/success; required `.npz` posterior was omitted from rolling publication. | Required pulls/parsing/analyses now fail visibly; add source/shape gates, optimizer checks, `.npz` publication, tests and a successful-run manifest. New workflow was checked locally, not executed on GitHub. |
| Solvers had different initializations | Python's foresight warm start and Numba's zero start could select different finite-iteration policies. | Aligned zero initialization; independent arrays agree below 6e-17 on 104 real games, including every 13-inning game. |
| Policy iteration does not always converge | The current full-sample continuation map cycles rather than meeting 1e-7. Agreement between two implementations is not proof of convergence. | Added numerical diagnostics/warnings and measured cycle sensitivity. Maximum continuation change 0.00013574 WP; adjacent phase policy values 2.56645 versus 2.56839 pp/team-game with identical draws. Revised claims say approximate benchmark. Exact numerical convergence remains unresolved. |
| Fixed-path cumulative value called “wins” | Reversing a call changes future play, but simulation retains recorded future opportunities and scores. | Removed season-win conversions from the active headline/report and documented the actual estimand. Archived stage talk is marked superseded. |
| Signal scale interpreted as eyesight / formal upper bound | Threshold heterogeneity, attention and misspecification can affect fitted scale; fielding is not exclusively catchers. | Qualified the model and removed the “binding limit is perception” claim. Formal identification/bounds remain unestablished. |
| “Eight-cell” card | There are 48 thresholds (eight display rows), not eight cells. Real-world users also need reliable confidence and stakes estimates. | Corrected the description; kept the result as simulated gap recovery and prospective decision-aid evidence. |
| Historical training and methods claims exceed evidence | Raw Retrosheet/trained-model provenance is incomplete; the seven-inning exclusion is not implemented. A dated plan is not external registration, and prespecification alone does not control family-wise error. | Fixed repository-relative historical paths and future direct-fit 2020 exclusion; added current methods and history notices. Raw historical rebuild / exclusion sensitivity remains open. |
| Planned manual audit lacks completion evidence | Automated join/reconciliation/geometry agreement cannot establish that a promised independent 200-pitch manual review occurred. | Prepared fixed-seed `manual_audit_sample_200.csv`; status explicitly pending. Checked all three residual geometry disagreements against official feeds. |
| PDF builder could mix old text with new rolling data | Silent download, Linux-only browser path, and no enforcing word-limit check weakened reproducibility. | Replaced with a portable local-input builder, headline assertions, conservative word/page checks and SHA-256 manifest. Original builder preserved in the audit folder. |
| Novelty and completed-work overclaims | Retained-on-success DP thresholds already exist in tennis; framing equilibrium and umpire causal designs are not implemented. | Scoped contribution to MLB integration/data/application, added primary citation, marked historical related-work/talk claims superseded. |

## Validation performed

- Eleven regression tests pass, covering corner geometry, distinct 13th innings, invalid/duplicate/missing paths, walk and terminal transitions, count consistency, both simulators' inventory switching, outcome scoring, pipeline failure propagation, and synthetic recovery of known probit parameters.
- Existing geometry, DP and perception self-tests pass.
- Rebuilt the full opportunity table from the frozen feed-pitch and Statcast inputs; no duplicated join keys, missing required coverage, nonfinite rewards, or observed challenges with zero tokens.
- Refit perception; reran the primary two-stream / 200-draw analysis, decomposition, team/learning summaries, heterogeneity, all existing robustness/counterfactual variants, and figures.
- Completed 200 independently seeded game-clustered refit bootstrap replicates in four shards; combined output checks unique replicate IDs 0–200.
- Verified decomposition sums equal the primary numerator and denominator, both solver arrays agree on 104 games, and marginal continuation values are nonnegative.
- Preserved raw signed gains: scoring observed challenges without clipping yields 2.10791 rather than 2.10999 pp/team-game, a 0.00209-point difference. This small sensitivity does not remove the need to label the metric honestly.
- Varied finite-iteration caps and evaluated both cycle phases; reported the unmet convergence tolerance.
- Rendered and visually inspected the revised PDF. One page, four sections, one composite figure plus one table, no author information, 437 conservatively counted words.

Scientific specification uncertainty is larger than the numerical cycle: direct-WP capture is 78.6%, player-effects capture 80.7%, and the alternative attention interpretations span roughly 78.2%–88.5%. These are sensitivity scenarios, not a confidence interval. No “82% is the true efficiency of MLB” claim is warranted.

## Before filing and before a full paper

For the abstract: use the audited text/PDF; retain the September 25 data cutoff unless a verified later snapshot is rebuilt; publish a reviewed code revision plus an immutable data/result snapshot so the submitted repository link matches the claims. The current local files have not been pushed. Check form entries and retain submission confirmation when the author submits.

For a stronger full paper: recover and document the historical WP training inputs and exact exclusions; complete the independent 200-pitch check; formalize or stabilize the approximate policy iteration; evaluate the card and confidence calibration out of time; assess how counterfactual changes to game paths affect the value scale. These strengthen the central paper more directly than adding the proposed umpire-response/framing studies before their identification is established.

## Suggested explanation for Ayan

“We ask whether teams get as much value as they could from their challenges, given a model of the information available to players. A high success rate can mean teams wait too long. In our data through September 25, observed challenges capture about 82% of our approximate benchmark; the largest modeled shortfall is early in the game. A simplified card closes about 59% of that gap in simulation. These are cumulative call-reversal values on recorded games, not a claim that adopting the card would win a certain number of extra games. The information model includes decision noise, so it does not measure eyesight alone.”

For “What is new?”: the recovered original-call data and MLB-specific integration of geometry, call value, challenge rules and observed allocation. Credit the tennis literature for the underlying challenge/opportunity-cost framework.

For “What could overturn the conclusion?”: better out-of-time confidence calibration or a game-transition model could change the benchmark and the gap. Alternative specifications already move the exact capture percentage. That is why the paper reports assumptions, sensitivity, and a testable aid rather than a guaranteed causal improvement.

## Main deliverables

- `paper/ABSTRACT_AUDITED_2026-09-26.md` and `output/pdf/SSAC27_Abstract_Audited_2026-09-26.pdf`.
- `repo/CURRENT_METHODS.md` and revised `repo/README.md`.
- `paper/SUBMISSION_PACKAGE_AUDITED_2026-09-26.md`.
- `audit/2026-09-26/audit_metrics.json`, `audit_checks.py`, cycle-phase check, bootstrap logs/results, source snapshots, and manifests.
- `repo/tests/` and the corrected local analysis/workflow code.

Official sources: [SSAC competition guidelines](https://www.sloansportsconference.com/research-paper-competition), [MLB ABS adoption notice](https://img.mlbstatic.com/opprops-images/image/upload/opprops/jgdgj1bak2bgiskwpdnm.pdf), [Statcast field definitions](https://baseballsavant.mlb.com/csv-docs), [Savant ABS](https://baseballsavant.mlb.com/abs), [Abramitzky et al. (2012)](https://web.stanford.edu/~leinav/pubs/IER2012.pdf).
