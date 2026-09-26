"""
build_all.py — the analysis pipeline, run nightly after the data pulls (see .github/workflows/nightly.yml).

Order (missing required inputs or failed analysis stops publication):
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
import json
from datetime import datetime, timezone

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
    started = datetime.now(timezone.utc).isoformat()
    ok = run("build_opps_2026.py", needs=["data/derived/feed_2026_pitches.parquet", "data/derived/feed_2026_games.csv",
                                          "data/raw/statcast/statcast_2026.parquet", "data/derived/wp_count_cube.npz", "data/derived/wp_cube.npz"])
    ok = ok and run("perception_fit_2026.py", needs=["data/derived/opps_2026.parquet"])
    ok = ok and run("tier1_dp_2026.py", args=("--draws", "200", "--reps", "2"), needs=["data/derived/perception_pm_2026.npz"])
    if not ok:
        raise SystemExit("Core analysis failed or has missing inputs; downstream outputs must not be published")
    # Evaluate all secondary steps, but surface any failure to the workflow.
    secondary = [run("decompose_2026.py", needs=["data/derived/tier1_opps_with_breakeven.parquet"]),
                 run("teams_learning_2026.py", needs=["data/derived/tier1_opps_with_breakeven.parquet"]),
                 run("perception_extra_2026.py", needs=["data/derived/opps_2026.parquet"]),
                 run("robustness_2026.py", needs=["data/derived/perception_fit_2026.json"]),
                 run("counterfactuals_2026.py", needs=["data/derived/perception_pm_2026.npz"])]
    B = os.environ.get("BOOTSTRAP_B", "0")
    if B not in ("", "0"):
        secondary.append(run("bootstrap_2026.py", args=("--B", B, "--draws", "30"), needs=["data/derived/perception_fit_2026.json"]))
    secondary.append(run("figures_2026.py", needs=["data/derived/tier1_mtv_2026.csv", "data/derived/tier1_decomposition_2026.csv"]))
    if not all(secondary):
        raise SystemExit("One or more analyses failed; outputs must not be published")
    import hashlib
    source_hashes = {}
    for directory, _, names in os.walk(os.path.join(ROOT, "code")):
        for name in names:
            if name.endswith(".py"):
                path = os.path.join(directory, name)
                with open(path, "rb") as fh:
                    source_hashes[os.path.relpath(path, ROOT)] = hashlib.sha256(fh.read()).hexdigest()
    input_hashes = {}
    for relative in ("data/derived/feed_2026_pitches.parquet", "data/derived/feed_2026_games.csv",
                     "data/raw/statcast/statcast_2026.parquet", "data/derived/wp_count_cube.npz", "data/derived/wp_cube.npz"):
        digest = hashlib.sha256()
        with open(os.path.join(ROOT, relative), "rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
        input_hashes[relative] = digest.hexdigest()
    with open(os.path.join(D, "run_manifest.json"), "w") as fh:
        json.dump({"started_utc": started, "completed_utc": datetime.now(timezone.utc).isoformat(),
                   "bootstrap_replicates": int(B or 0), "source_sha256": source_hashes,
                   "input_sha256": input_hashes}, fh, indent=2)
    print("pipeline complete")


if __name__ == "__main__":
    main()
