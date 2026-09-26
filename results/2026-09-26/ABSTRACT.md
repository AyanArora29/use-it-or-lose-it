**Use It or Lose It: The Value and Limits of MLB's Ball-Strike Challenges**

**Introduction.** MLB's 2026 challenge system gives each team two challenges, retained on success. A high overturn rate need not mean good allocation: a cautious team can forgo valuable opportunities. We estimate when to challenge and how much modeled value observed decisions capture.

**Methods.** We combine MLB StatsAPI reviews with Statcast through September 25, recovering original umpire calls and reconstructing the ball's intersection with the ABS zone. The analysis includes 350,588 eligible pitches and 10,425 challenges across 2,398 games; reconstructed outcomes agree with recorded verdicts on 99.97% of challenged pitches. Historical count-dependent win probabilities price reversals. A fitted Gaussian signal-and-threshold model describes challenge propensity. An approximate dynamic program prices the opportunity cost of losing a challenge, including retention and extra-inning replenishment. We evaluate policies along recorded game sequences and estimate conditional uncertainty with 200 game-clustered bootstrap refits.

**Results.** The benchmark produces 2.57 win-probability percentage points of cumulative reversal value per team-game; observed challenges produce 2.11, capturing 82% (95% bootstrap interval, 79-85%). The second challenge's value declines from about 0.9 points in the first inning to 0.4 in the ninth. The largest shortfall occurs in innings 1-3: observed use is 0.62 challenges per team-game at 61% success, versus 0.97 at 48% under the benchmark. Thus lower success can accompany greater value. A decision card recovers 59% of the modeled gap in simulation. Perfect-information value is 6.37 points, illustrating sensitivity to the assumed information available to players.

**Conclusion.** The model favors earlier use of two challenges and greater willingness to risk failure as remaining opportunities diminish. These results support a testable decision aid. Values are sums along fixed game paths, not causal wins gained. Fitted signal noise may absorb attention and threshold heterogeneity; it does not isolate eyesight. Prospective validation should test confidence calibration and the card's benefit.

**Figure 1.** Challenge value and use. Bar labels show success rates.

**Table 1.** Minimum modeled confidence (%), two/one challenges. PA-ending: three balls or two strikes. Stakes are reversal-value terciles.
