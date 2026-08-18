"""
figures_2026.py — exhibits from the Tier-1 outputs (figures/*.png, *.pdf).
  fig1_value_and_use.png   (a) marginal value of the 1st and 2nd challenge by inning (tie game; ±2 runs dashed)
                           (b) observed vs information-constrained-optimal challenges per team-game by inning band, with success rates
  fig2_perception.png      P(challenge | true margin) by side with the fitted probit; overturn rate given a challenge
  fig3_card.png            the challenge card as a rendered table
"""
from __future__ import annotations

import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import norm  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
DERIVED = os.path.join(ROOT, "data", "derived"); FIG = os.path.join(ROOT, "figures")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 150})
DMAX = 6


def fig1():
    mt = pd.read_csv(os.path.join(DERIVED, "tier1_mtv_2026.csv"))
    dec = pd.read_csv(os.path.join(DERIVED, "tier1_decomposition_2026.csv"))
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9))
    top = mt[(mt["half"] == "top") & (mt["inning"] <= 9)]
    tie = top[top["d_team"] == 0].sort_values("inning")
    pm2 = top[top["d_team"].abs() == 2].groupby("inning")[["MTV1", "MTV2"]].mean().reset_index()
    ax[0].plot(tie["inning"], tie["MTV1"] * 100, "-", color="#1f77b4", label="1st challenge, tie game")
    ax[0].plot(pm2["inning"], pm2["MTV1"] * 100, "--", color="#1f77b4", label="1st challenge, 2-run game")
    ax[0].plot(tie["inning"], tie["MTV2"] * 100, "-", color="#d62728", label="2nd challenge, tie game")
    ax[0].plot(pm2["inning"], pm2["MTV2"] * 100, "--", color="#d62728", label="2nd challenge, 2-run game")
    ax[0].set_xlabel("inning (start of the top)"); ax[0].set_ylabel("marginal value of holding the challenge\n(win-probability points)")
    ax[0].set_xticks(range(1, 10))
    ax[0].legend(frameon=False, fontsize=7, loc="lower left"); ax[0].set_ylim(0, None)
    ax[0].set_title("(a) A challenge is worth more the earlier it is held", fontsize=9, loc="left")
    d1 = dec[dec["by"] == "inning band"].copy()
    d1["inn_band"] = pd.Categorical(d1["inn_band"], ["1-3", "4-6", "7-8", "9+"], ordered=True); d1 = d1.sort_values("inn_band")
    xs = np.arange(len(d1)); w = 0.38
    b1 = ax[1].bar(xs - w / 2, d1["obs_used"], w, color="#7f7f7f", label="observed")
    b2 = ax[1].bar(xs + w / 2, d1["opt_used"], w, color="#2ca02c", label="optimal (same perception)")
    for i, r in enumerate(d1.itertuples(index=False)):
        ax[1].text(xs[i] - w / 2, r.obs_used + 0.02, f"{r.obs_succ_rate*100:.0f}%", ha="center", fontsize=7, color="#555")
        ax[1].text(xs[i] + w / 2, r.opt_used + 0.02, f"{r.opt_succ_rate*100:.0f}%", ha="center", fontsize=7, color="#2ca02c")
    ax[1].set_xticks(xs); ax[1].set_xticklabels([str(v) for v in d1["inn_band"]]); ax[1].set_xlabel("inning")
    ax[1].set_ylabel("challenges per team-game"); ax[1].legend(frameon=False, fontsize=7)
    ax[1].set_title("(b) Use by inning; labels = success rate", fontsize=9, loc="left")
    ax[1].set_ylim(0, max(d1["opt_used"].max(), d1["obs_used"].max()) * 1.25)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig1_value_and_use.png")); fig.savefig(os.path.join(FIG, "fig1_value_and_use.pdf"))
    plt.close(fig)


def fig2():
    cur = pd.read_csv(os.path.join(DERIVED, "perception_curves_2026.csv"))
    fit = json.load(open(os.path.join(DERIVED, "perception_fit_2026.json")))
    opps = pd.read_parquet(os.path.join(DERIVED, "tier1_opps_with_breakeven.parquet"), columns=["role", "cell", "tokens_obs"])
    fig, ax = plt.subplots(1, 2, figsize=(7.2, 3.0))
    mids = {"(-30.0, -6.0]": -7, "(-6.0, -4.0]": -5, "(-4.0, -3.0]": -3.5, "(-3.0, -2.0]": -2.5, "(-2.0, -1.5]": -1.75, "(-1.5, -1.0]": -1.25,
            "(-1.0, -0.5]": -0.75, "(-0.5, 0.0]": -0.25, "(0.0, 0.5]": 0.25, "(0.5, 1.0]": 0.75, "(1.0, 1.5]": 1.25, "(1.5, 2.0]": 1.75,
            "(2.0, 3.0]": 2.5, "(3.0, 4.0]": 3.5, "(4.0, 6.0]": 5, "(6.0, 40.0]": 7}
    xs = np.linspace(-6, 6, 241)
    for side, col, lab in (("bat", "#1f77b4", "batting team (called strike)"), ("fld", "#d62728", "fielding team (called ball)")):
        c2 = cur[cur["side"] == side].copy(); c2["nc"] = c2["p_challenge"] * c2["n"]
        c = c2.groupby("xb").agg(n=("n", "sum"), nc=("nc", "sum")).reset_index(); c["p"] = c["nc"] / c["n"]
        c["x"] = c["xb"].map(mids); c = c[(c["n"] >= 30) & (c["x"].abs() <= 6)]
        ax[0].scatter(c["x"], c["p"], s=np.clip(c["n"] / 150, 10, 90), color=col, alpha=0.85, label=lab, zorder=3)
        f = fit["sides"][side]["pooled"]; sig = f["sigma"]
        cells = opps.loc[(opps["role"] == side) & (opps["tokens_obs"] >= 1), "cell"]
        w = cells.value_counts(normalize=True)
        taus = np.array([f["tau"].get(k, np.nan) for k in w.index]); ww = w.values[np.isfinite(taus)]; taus = taus[np.isfinite(taus)]
        curve = (ww[None, :] * norm.cdf((xs[:, None] - taus[None, :]) / sig)).sum(1) / ww.sum()
        ax[0].plot(xs, curve, color=col, lw=1.2, label=f"fitted model (σ = {sig:.1f} in)")
    ax[0].axvline(0, color="#999", lw=0.6); ax[0].set_xlim(-6, 6); ax[0].set_ylim(0, 0.9)
    ax[0].set_xlabel("true margin in the challenger's favour (in)\n(> 0: the umpire was wrong)")
    ax[0].set_ylabel("share of eligible pitches challenged")
    ax[0].legend(frameon=False, fontsize=6.5, loc="upper left")
    ax[0].set_title("(a) Challenges track the true miss, noisily", fontsize=9, loc="left")
    for side, col, nm in (("bat", "#1f77b4", "batters"), ("fld", "#d62728", "catchers/pitchers")):
        f = fit["sides"][side]["pooled"]
        tau = pd.Series(f["tau"])
        df = pd.DataFrame({"inn": [k.split("|")[0] for k in tau.index], "tok": [k.split("|")[1] for k in tau.index], "tau": tau.values})
        med = df.groupby(["inn", "tok"])["tau"].median().unstack("tok").reindex(["1-3", "4-6", "7-8", "9+"])
        ax[1].plot(range(4), med["2"], "-o", color=col, ms=4, label=f"{nm}, 2 challenges left")
        ax[1].plot(range(4), med["1"], "--s", color=col, ms=4, label=f"{nm}, 1 left")
    ax[1].set_xticks(range(4)); ax[1].set_xticklabels(["1-3", "4-6", "7-8", "9+"]); ax[1].set_xlabel("inning")
    ax[1].set_ylabel("revealed threshold (in of perceived miss)"); ax[1].legend(frameon=False, fontsize=6.5)
    ax[1].set_title("(b) Thresholds fall as the game runs out", fontsize=9, loc="left"); ax[1].set_ylim(0, None)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2_perception.png")); fig.savefig(os.path.join(FIG, "fig2_perception.pdf"))
    plt.close(fig)


def fig3():
    card = pd.read_csv(os.path.join(DERIVED, "tier1_card_2026.csv"))
    piv2 = card.pivot_table(index=["inn_band", "cnt"], columns="lev", values="pstar_t2")[["low", "mid", "high"]]
    piv1 = card.pivot_table(index=["inn_band", "cnt"], columns="lev", values="pstar_t1")[["low", "mid", "high"]]
    piv2 = piv2.reindex(pd.MultiIndex.from_product([["1-3", "4-6", "7-8", "9+"], ["count-changing", "PA-ending"]]))
    piv1 = piv1.reindex(piv2.index)
    fig, ax = plt.subplots(figsize=(7.2, 3.0)); ax.axis("off")
    rows = []
    for (ib, cnt) in piv2.index:
        rows.append([ib, cnt] + [f"{piv2.loc[(ib, cnt), c]*100:.0f}% / {piv1.loc[(ib, cnt), c]*100:.0f}%" for c in ["low", "mid", "high"]])
    tbl = ax.table(cellText=rows, colLabels=["inning", "the call would…", "low stakes", "medium stakes", "high stakes"],
                   loc="center", cellLoc="center")
    tbl.auto_set_font_size(False); tbl.set_fontsize(8); tbl.scale(1, 1.3)
    ax.set_title("Challenge card — minimum confidence to challenge (2 challenges left / 1 left)\n"
                 "stakes = win-probability swing of the call (terciles); PA-ending = strike three / ball four", fontsize=8.5)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig3_card.png")); fig.savefig(os.path.join(FIG, "fig3_card.pdf"))
    plt.close(fig)


if __name__ == "__main__":
    fig1(); fig2(); fig3()
    print("figures written to", FIG)
