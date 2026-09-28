# Shortfall decomposition — 2026 (observed vs information-constrained optimum)

Levels per team-game. The optimum is one global policy evaluated on the same streams; a negative per-band gap means the optimum spends fewer tokens there because it spent them earlier, not that teams out-perform it there.

- Per team-game: observed 2.102 pp; optimum 2.557 pp; oracle 6.356 pp; gap 0.455 pp (fixed-stream model).
- By side (per team-game; gains in WP points):

role   opps  obs_used  opt_used  obs_succ  opt_succ  obs_gain  opt_gain  oracle_gain  gap_pp  obs_succ_rate  opt_succ_rate
 bat 113991     0.981     1.257     0.480     0.479     0.891     1.122        3.201   0.231          0.489          0.381
 fld 240497     1.193     1.457     0.692     0.684     1.212     1.435        3.154   0.223          0.580          0.469

- By inning band (per team-game; gains in WP points):

inn_band   opps  obs_used  opt_used  obs_succ  opt_succ  obs_gain  opt_gain  oracle_gain  gap_pp  obs_succ_rate  opt_succ_rate
     1-3 122157     0.621     0.967     0.378     0.461     0.702     1.054        2.353   0.352          0.608          0.477
     4-6 118417     0.701     0.846     0.388     0.376     0.655     0.802        2.004   0.147          0.554          0.445
     7-8  80751     0.527     0.561     0.272     0.223     0.433     0.444        1.264   0.011          0.515          0.397
      9+  33163     0.325     0.341     0.133     0.103     0.312     0.257        0.735  -0.055          0.410          0.302

- By side × inning band (per team-game; gains in WP points):

role inn_band  opps  obs_used  opt_used  obs_succ  opt_succ  obs_gain  opt_gain  oracle_gain  gap_pp  obs_succ_rate  opt_succ_rate
 bat      1-3 39512     0.258     0.393     0.135     0.157     0.264     0.400        1.074   0.136          0.525          0.400
 bat      4-6 37552     0.314     0.399     0.162     0.165     0.292     0.384        1.080   0.092          0.517          0.414
 bat      7-8 26194     0.252     0.285     0.120     0.103     0.183     0.204        0.655   0.021          0.477          0.362
 bat       9+ 10733     0.158     0.180     0.062     0.053     0.151     0.133        0.392  -0.018          0.392          0.295
 fld      1-3 82645     0.364     0.574     0.243     0.304     0.438     0.654        1.279   0.216          0.667          0.530
 fld      4-6 80865     0.388     0.447     0.226     0.211     0.363     0.418        0.924   0.055          0.584          0.473
 fld      7-8 54557     0.274     0.276     0.151     0.119     0.250     0.240        0.608  -0.010          0.551          0.432
 fld       9+ 22430     0.167     0.161     0.071     0.050     0.161     0.123        0.342  -0.037          0.427          0.309

- By count class (per team-game; gains in WP points):

           cnt   opps  obs_used  opt_used  obs_succ  opt_succ  obs_gain  opt_gain  oracle_gain  gap_pp  obs_succ_rate  opt_succ_rate
     PA-ending  91600     0.820     1.098     0.382     0.392     1.265     1.506        2.752   0.242          0.466          0.357
count-changing 262888     1.354     1.617     0.789     0.770     0.838     1.050        3.604   0.213          0.583          0.477

- By side × count class (per team-game; gains in WP points):

role            cnt   opps  obs_used  opt_used  obs_succ  opt_succ  obs_gain  opt_gain  oracle_gain  gap_pp  obs_succ_rate  opt_succ_rate
 bat      PA-ending  16515     0.389     0.489     0.161     0.161     0.545     0.656        1.276   0.112          0.413          0.330
 bat count-changing  97476     0.592     0.768     0.319     0.317     0.346     0.466        1.925   0.120          0.538          0.413
 fld      PA-ending  75085     0.431     0.609     0.221     0.231     0.720     0.850        1.476   0.130          0.514          0.380
 fld count-changing 165412     0.762     0.849     0.470     0.453     0.492     0.585        1.679   0.093          0.617          0.534

- By tokens in hand (observed) (per team-game; gains in WP points):

 tokens_obs   opps  obs_used  opt_used  obs_succ  opt_succ  obs_gain  opt_gain  oracle_gain  gap_pp  obs_succ_rate  opt_succ_rate
          0  24661     0.000     0.144     0.000     0.055     0.000     0.119        0.455   0.119            NaN          0.380
          1  96676     0.597     0.716     0.312     0.285     0.609     0.649        1.739   0.040          0.522          0.398
          2 233151     1.577     1.855     0.859     0.823     1.493     1.788        4.161   0.295          0.545          0.444

- By true margin (challenge propensity observed vs optimal, gains per team-game):

           xb   opps  obs_used  opt_used  obs_gain  opt_gain  gap_pp
(-30.0, -1.0] 304729     0.008     0.015     0.000     0.000   0.000
  (-1.0, 0.0]  24529     0.099     0.118     0.000     0.000   0.000
   (0.0, 0.5]   8469     0.164     0.173     0.538     0.730   0.192
   (0.5, 1.0]   6127     0.209     0.212     0.509     0.633   0.125
   (1.0, 1.5]   3976     0.260     0.253     0.382     0.451   0.068
   (1.5, 2.0]   2470     0.333     0.305     0.282     0.317   0.035
   (2.0, 3.0]   2142     0.385     0.375     0.280     0.317   0.037
  (3.0, 40.0]    672     0.494     0.462     0.111     0.108  -0.003

- Actual challenges: 10,545; overturned 0.539; mean g of overturned 1.795 pp; mean g of failed 2.280 pp; mean decision-time MTV at failed challenges 0.491 pp.
