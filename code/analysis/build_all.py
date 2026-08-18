"""
build_all.py — the analysis pipeline, run nightly after the data pulls (see .github/workflows/nightly.yml).

Order (each step is skipped with a note if its inputs are missing, so a partial data day never fails the job):
  1. code/analysis/build_opps_2026.py      feed pitches + Statcast state + WP flip gains + tokens  -> opps_2026.parquet, verification_2026.md
  2. code/analysis/perception_fit_2026.py  Tier-1 perception curves and probit fits               -> perception_*.{csv,json,npz,md}
  3. code/analysis/tier1_dp_2026.py        DP on 2026 streams, card, policy values, capture ratio -> tier1_*.{csv,json,md}, dp_*.npy
  4. decompose / teams_learning / perception_extra / robustness / counterfactuals / (bootstrap if BOOTSTRAP_B is set) / figures
The WP cubes (data/derived/wp_count_cube.npz primary, wp_cube.npz robustness) are built offline from Retrosheet 2015–2025 by
code/engine/wp_count.py and code/engine/wp_model.py and are versioned in the repo.
"""
from __future__ import annotations

import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
D = os.path.join(ROOT, "data", "derived")


def run(script, args=(), needs=()):
    missing = [p for p in needs if not os.path.exists(os.path.join(ROOT, p))]
    if missing:
        print(f"[skip] {script}: missing {missing}")
        return False
    t0 = time.time()
    print(f"[run ] {script} {' '.join(args)}", flush=True)
    r = subprocess.run([sys.executable, os.path.join(HERE, script), *args], cwd=ROOT)
    print(f"[done] {script} rc={r.returncode} ({time.time()-t0:.0f}s)", flush=True)
    return r.returncode == 0


def main():
    ok = run("build_opps_2026.py", needs=["data/derived/feed_2026_pitches.parquet", "data/derived/feed_2026_games.csv",
                                          "data/raw/statcast/statcast_2026.parquet", "data/derived/wp_count_cube.npz", "data/derived/wp_cube.npz"])
    ok = ok and run("perception_fit_2026.py", needs=["data/derived/opps_2026.parquet"])
    ok = ok and run("tier1_dp_2026.py", args=("--draws", "200", "--reps", "2"), needs=["data/derived/perception_pm_2026.npz"])
    # secondary analyses (each independent; failures don't stop the others)
    run("decompose_2026.py", needs=["data/derived/tier1_opps_with_breakeven.parquet"])
    run("teams_learning_2026.py", needs=["data/derived/tier1_opps_with_breakeven.parquet"])
    run("perception_extra_2026.py", needs=["data/derived/opps_2026.parquet"])
    run("robustness_2026.py", needs=["data/derived/perception_fit_2026.json"])
    run("counterfactuals_2026.py", needs=["data/derived/perception_pm_2026.npz"])
    B = os.environ.get("BOOTSTRAP_B", "0")
    if B not in ("", "0"):
        run("bootstrap_2026.py", args=("--B", B, "--draws", "30"), needs=["data/derived/perception_fit_2026.json"])
    run("figures_2026.py", needs=["data/derived/tier1_mtv_2026.csv", "data/derived/tier1_decomposition_2026.csv"])
    print("pipeline", "complete" if ok else "incomplete")


if __name__ == "__main__":
    main()
