"""Toy tests for the Bellman logic in dp.py. Run: python3 test_dp.py"""
import sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dp import solve, evaluate, DMAX


def toy(opps, h=18, extra_h=None):
    """Both teams get identical opportunity streams (so V equals the single-team value)."""
    rows = []
    for th in (0, 1):
        for g, p, o in opps:
            rows.append(dict(season=2099, game_id="G1", team_home=th, h=h, score_diff_home=0, g=g, p=p, role="batter",
                             orig="S", balls=0, strikes=0, inning=(h + 1) // 2, outs=o, bases_idx=0))
    op = pd.DataFrame(rows)
    hs = list(range(1, 19)) + (list(range(19, extra_h + 1)) if extra_h else [])
    hi = pd.DataFrame([dict(season=2099, game_id="G1", h=hh, sd_start=0, sd_end=0) for hh in hs])
    return op, hi


# 1. single opportunity in the last half-inning: V(t>=1) = p*g
op, hi = toy([(0.1, 0.6, 0)])
V, C = solve(op, hi, verbose=False)
assert np.allclose(V[18, DMAX], [0, 0.06, 0.06]), V[18, DMAX]
assert np.allclose(V[1, DMAX], [0, 0.06, 0.06]), V[1, DMAX]          # value propagates back unchanged (no other opps)

# 2. two opportunities: (0.1, 0.3) then (0.2, 0.9)
#    t=1: skip first (0.03 < 0.7*0.18) -> 0.18 ; t=2: MTV after first is 0 -> challenge: 0.3*0.28+0.7*0.18 = 0.21
op, hi = toy([(0.1, 0.3, 0), (0.2, 0.9, 1)])
V, C = solve(op, hi, verbose=False)
assert np.allclose(V[18, DMAX], [0, 0.18, 0.21]), V[18, DMAX]
assert np.allclose(C[18, DMAX, 0], [0, 0.18, 0.18]), C[18, DMAX, 0]   # continuation after the outs=0 opportunity
assert np.allclose(C[18, DMAX, 1], [0, 0, 0]), C[18, DMAX, 1]         # after the last opportunity: nothing left

# 3. extra-innings grant: opportunity in the top of the 10th (h=19) with p=1, g=0.5; a team with 0 tokens entering
#    the 10th gets one -> V[18, d, 0] = 0.5
op, hi = toy([(0.5, 1.0, 0)], h=19, extra_h=20)
V, C = solve(op, hi, verbose=False)
assert np.allclose(V[18, DMAX], [0.5, 0.5, 0.5]), V[18, DMAX]

# 4. evaluate() follows the DP decision: p in {0,1} makes it deterministic
op, hi = toy([(0.1, 0.0, 0), (0.2, 1.0, 1)])
V, C = solve(op, hi, verbose=False)
r = evaluate(op, hi, V, C, "optimal")
assert np.allclose(r["gain"], 0.2) and (r["used"] == 1).all(), r
r = evaluate(op, hi, V, C, "naive")   # naive at 0.5: challenges the second only
assert np.allclose(r["gain"], 0.2) and (r["used"] == 1).all(), r

# 5. retention makes optimal more aggressive: with 2 tokens, a 40% shot at 0.1 in the top of the 9th is taken when
#    a sure 0.05 remains later (MTV small); with 1 token it is not.
op, hi = toy([(0.1, 0.4, 0), (0.05, 1.0, 2)], h=17)
V, C = solve(op, hi, verbose=False)
assert V[17, DMAX, 2] > V[17, DMAX, 1] + 0.02, V[17, DMAX]      # 2nd token adds real value here
print("dp toy tests passed:", V[17, DMAX])
