"""
counterfactuals_2026.py — rule-design counterfactuals (METHODS §10) on the 2026 streams with the fitted perception model:
tokens per game × retention × extra-innings grant. For each rule the information-constrained optimum is re-solved and
re-simulated; we report value (WP points per team-game), challenges and corrected miscalls per game (both teams), failed
challenges, and time added at a stated seconds-per-challenge. Output: tier1_counterfactuals_2026.csv/.md
"""
from __future__ import annotations

import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code", "engine")); sys.path.insert(0, HERE)
import dp_fast as F  # noqa: E402
from perception_fit_2026 import add_cells  # noqa: E402
from tier1_dp_2026 import half_inning_paths, load_pm, build_streams_2026  # noqa: E402

DERIVED = os.path.join(ROOT, "data", "derived")
SEC_PER_CHALLENGE = 14.0   # MLB-reported average review time for ABS challenges (~14 s); parameter, not an estimate


def main():
    t0 = time.time()
    o = pd.read_parquet(os.path.join(DERIVED, "opps_2026.parquet"))
    o = o[o["pos_pitcher"] == 0].copy()
    fit = json.load(open(os.path.join(DERIVED, "perception_fit_2026.json")))
    o, _ = add_cells(o, {k: tuple(v) for k, v in fit["lev_q"].items()})
    pm = load_pm(os.path.join(DERIVED, "perception_pm_2026.npz"))
    hi = half_inning_paths(os.path.join(ROOT, "data", "raw", "statcast", "statcast_2026.parquet"), set(o["game_pk"]))
    op = build_streams_2026(o, pm, seed=100)
    A = F.make_arrays(op, hi)
    os_ = A["op_sorted"]
    n_tg = os_.groupby(["game_id", "team_home"]).ngroups
    n_games = os_["game_id"].nunique()
    rows = []
    obs_used = os_["challenged"].sum() / n_games; obs_ov = (os_["challenged"] * os_["overturned"]).sum() / n_games
    obs_gain = (os_["g"] * os_["challenged"] * os_["overturned"]).sum() / n_tg
    rows.append(dict(rule="2026 as played (observed behaviour)", tokens=2, retain=True, grant=True, value_pp=obs_gain * 100,
                     challenges_per_game=obs_used, corrected_per_game=obs_ov, failed_per_game=obs_used - obs_ov,
                     minutes_added=obs_used * SEC_PER_CHALLENGE / 60, corrections_per_minute=obs_ov / (obs_used * SEC_PER_CHALLENGE / 60)))
    variants = [("2 challenges, retained if successful (2026 rule)", 2, True, True),
                ("1 challenge, retained", 1, True, True),
                ("3 challenges, retained", 3, True, True),
                ("4 challenges, retained", 4, True, True),
                ("2 challenges, NOT retained", 2, False, True),
                ("3 challenges, NOT retained", 3, False, True),
                ("2 challenges, retained, no extra-innings grant", 2, True, False)]
    for name, tokens, retain, grant in variants:
        V, C = F.solve_fast(A, n_iter=40, tol=1e-7, tokens=tokens, retain=retain, grant=grant)
        r, _ = F.simulate_fast(os_, C, pm, "optimal", D=60, seed=7, tokens=tokens, retain=retain, grant=grant)
        used = r["used"].sum() / n_games; succ = r["succ"].sum() / n_games
        rows.append(dict(rule=name + " — optimal use, human perception", tokens=tokens, retain=retain, grant=grant,
                         value_pp=r["gain"].mean() * 100, V_start_pp=V[1, F.DMAX, tokens] * 100,
                         challenges_per_game=used, corrected_per_game=succ, failed_per_game=used - succ,
                         minutes_added=used * SEC_PER_CHALLENGE / 60, corrections_per_minute=succ / max(used * SEC_PER_CHALLENGE / 60, 1e-9)))
        print(rows[-1], flush=True)
    # mechanical bounds: oracle with 2 tokens (perfect perception), and 'unlimited' (every miscall corrected)
    V, C = F.solve_fast(A, n_iter=40, tol=1e-7)
    r, _ = F.simulate_fast(os_, C, pm, "oracle", D=1, seed=1)
    used = r["used"].sum() / n_games; succ = r["succ"].sum() / n_games
    rows.append(dict(rule="2 challenges retained — perfect perception (oracle)", tokens=2, retain=True, grant=True, value_pp=r["gain"].mean() * 100,
                     challenges_per_game=used, corrected_per_game=succ, failed_per_game=0.0, minutes_added=used * SEC_PER_CHALLENGE / 60,
                     corrections_per_minute=succ / (used * SEC_PER_CHALLENGE / 60)))
    wrong = os_["truth"].sum() / n_games
    rows.append(dict(rule="every miscall corrected (full ABS; mechanical bound)", tokens=np.inf, retain=True, grant=True,
                     value_pp=(os_["g"] * os_["truth"]).sum() / n_tg * 100, challenges_per_game=wrong, corrected_per_game=wrong, failed_per_game=0.0,
                     minutes_added=np.nan, corrections_per_minute=np.nan))
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(DERIVED, "tier1_counterfactuals_2026.csv"), index=False)
    md = ("# Rule-design counterfactuals — 2026 streams, fitted perception (METHODS §10)\n\n"
          f"Value = WP points per team-game from the challenge system relative to no challenges; per-game counts are for both teams; time at {SEC_PER_CHALLENGE:.0f} s per challenge.\n\n"
          + df.round(3).to_string(index=False) + f"\n\nRuntime {time.time()-t0:.0f}s.\n")
    with open(os.path.join(DERIVED, "tier1_counterfactuals_2026.md"), "w") as fh:
        fh.write(md)
    print(md)


if __name__ == "__main__":
    main()
