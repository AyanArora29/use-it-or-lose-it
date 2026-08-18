"""
build_opps_2026.py — the 2026 opportunity table: every eligible called pitch with game state, tokens in hand, ABS truth,
geometry, WP flip gain, and (if challenged) the challenge outcome.   METHODS §2.1 (verification), §4 (pricing), §7 (tokens).

Inputs  (repo-relative):
    data/derived/feed_2026_pitches.parquet      per-pitch table from code/engine/challenges_extract.py (StatsAPI feeds)
    data/derived/feed_2026_games.csv            per-game absChallenges tallies (reconciliation)
    data/raw/statcast/statcast_2026.parquet     Statcast 2026 (pybaseball) — game state, Savant coordinates
    data/derived/wp_count_cube.npz              primary WP cube (count-composed; code/engine/wp_count.py, Retrosheet 2015–2025)
    data/derived/wp_cube.npz                    robustness WP cube (direct HGB with count; code/engine/wp_model.py)
Outputs:
    data/derived/opps_2026.parquet              one row per eligible called pitch
    data/derived/verification_2026.md           the §2.1 verification report (join rate, reconciliation, token audit, geometry)

Conventions: d_in = signed miss (inches) of the ball to the ABS rectangle at the plate midpoint, any-part-of-ball rule
(negative = strike). orig ∈ {'S','B'} is the umpire's ORIGINAL call. The challenging side is the batting team on a called
strike and the fielding team on a called ball; margin x = d_in (orig='S') or −d_in (orig='B') is positive iff a challenge
would succeed. g = ΔWP for the challenging side if the call is overturned (win-probability points, 0–1 scale).
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "code", "engine"))
from wp_model import WPCube  # noqa: E402
from wp_count import WPCountCube  # noqa: E402

DERIVED = os.path.join(ROOT, "data", "derived")
ELIGIBLE_DESC = {"called_strike", "ball", "blocked_ball"}


def replay_tokens(fp: pd.DataFrame, extras_rule="start_of_inning"):
    """Tokens in hand for both teams before every pitch, replaying the game's ABS challenges in order.
    2026 rule: 2 per team; retained on success; lost on failure; from the 10th inning a team with none receives one at the
    start of each extra inning (extras_rule='start_of_inning'); alternative reading 'per_half' grants at the start of the
    team's own half (sensitivity)."""
    fp = fp.sort_values(["gamePk", "atBatIndex", "eventIndex"]).reset_index(drop=True)
    th = np.zeros(len(fp), dtype=np.int8); ta = np.zeros(len(fp), dtype=np.int8)
    final = {}
    for gpk, idx in fp.groupby("gamePk", sort=False).indices.items():
        home = 2; away = 2; last_inning = 0
        inn = fp["inning"].values[idx]; bh = fp["bat_home"].values[idx]
        ch = fp["challenged"].values[idx]; ov = fp["isOverturned"].values[idx]
        side = fp["challenger_side"].values[idx]
        for j, i in enumerate(idx):
            if inn[j] != last_inning:
                if inn[j] >= 10:
                    if extras_rule == "start_of_inning":
                        if home == 0: home = 1
                        if away == 0: away = 1
                last_inning = inn[j]
            if extras_rule == "per_half" and inn[j] >= 10:
                pass  # (implemented in the sensitivity script)
            th[i] = home; ta[i] = away
            if ch[j] == 1 and ov[j] == 0:
                # who lost the token: challenger's team
                if (side[j] == "bat" and bh[j] == 1) or (side[j] == "fld" and bh[j] == 0):
                    home = max(home - 1, 0)
                else:
                    away = max(away - 1, 0)
        final[gpk] = (home, away)
    fp["tokens_home"] = th; fp["tokens_away"] = ta
    return fp, final


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feed", default=os.path.join(DERIVED, "feed_2026_pitches.parquet"))
    ap.add_argument("--games", default=os.path.join(DERIVED, "feed_2026_games.csv"))
    ap.add_argument("--statcast", default=os.path.join(ROOT, "data", "raw", "statcast", "statcast_2026.parquet"))
    ap.add_argument("--out", default=os.path.join(DERIVED, "opps_2026.parquet"))
    ap.add_argument("--report", default=os.path.join(DERIVED, "verification_2026.md"))
    args = ap.parse_args()
    rep = ["# Verification report — 2026 opportunity table (METHODS §2.1)", ""]

    fp = pd.read_parquet(args.feed)
    games = pd.read_csv(args.games)
    sc = pd.read_parquet(args.statcast, columns=["game_pk", "game_type", "game_date", "at_bat_number", "pitch_number", "description",
                                                 "balls", "strikes", "outs_when_up", "inning", "inning_topbot", "on_1b", "on_2b", "on_3b",
                                                 "home_score", "away_score", "home_team", "away_team", "batter", "pitcher", "stand", "p_throws",
                                                 "plate_x", "plate_z", "sz_top", "sz_bot", "pitch_type", "release_speed",
                                                 "home_win_exp", "delta_home_win_exp", "type", "zone"])
    sc = sc[sc["game_type"] == "R"].copy().rename(columns={"description": "sc_description"})
    rep.append(f"- StatsAPI feeds: {fp['gamePk'].nunique():,} games, {len(fp):,} pitches ({fp['game_date'].min()} → {fp['game_date'].max()}).")
    rep.append(f"- Statcast regular season: {sc['game_pk'].nunique():,} games, {len(sc):,} pitches ({sc['game_date'].min()} → {sc['game_date'].max()}).")

    # ---- tokens replay + audit against gameData.absChallenges remaining --------------------------------------------
    fp, final = replay_tokens(fp)
    g = games.set_index("gamePk")
    audit = pd.DataFrame([(k, v[0], v[1]) for k, v in final.items()], columns=["gamePk", "home_final", "away_final"]).set_index("gamePk")
    audit = audit.join(g[["home_remaining", "away_remaining"]])
    max_inn = fp.groupby("gamePk")["inning"].max()
    audit["max_inn"] = max_inn
    nine = audit["max_inn"] <= 9
    ok_tok = ((audit["home_final"] == audit["home_remaining"]) & (audit["away_final"] == audit["away_remaining"]))
    rep.append(f"- Token replay audit (nine-inning games, where gameData.remaining = 2 − failed challenges): final tokens match for both teams in "
               f"{ok_tok[nine & audit['home_remaining'].notna()].mean()*100:.2f}% of {int((nine & audit['home_remaining'].notna()).sum()):,} games. "
               f"gameData.remaining ignores extra-inning grants (it equals max(0, 2 − usedFailed) in {((audit['home_remaining'] == (2 - g['home_usedFailed']).clip(lower=0)).mean())*100:.1f}% of games), "
               f"so extra-inning games are audited by consistency instead: under the pre-registered reading (a team with no challenge receives one at the "
               f"start of each extra inning) every one of the {int(fp['challenged'].sum()):,} observed challenges was made with ≥1 token in hand — "
               f"violations: {int(((fp['challenged']==1) & (np.where(((fp['challenger_side']=='bat')&(fp['bat_home']==1))|((fp['challenger_side']=='fld')&(fp['bat_home']==0)), fp['tokens_home'], fp['tokens_away'])==0)).sum())}.")
    summ = g[["away_usedSuccessful", "away_usedFailed", "home_usedSuccessful", "home_usedFailed"]].sum().sum()
    n_ch = int(fp["challenged"].sum())
    rep.append(f"- Challenge events parsed: {n_ch:,} (event-level {int((fp['review_level']=='event').sum()):,}, play-level "
               f"{int((fp['review_level']=='play').sum()):,}) vs gameData tallies {int(summ):,}; games not reconciling: "
               f"{int((g['n_challenges'] != g[['away_usedSuccessful','away_usedFailed','home_usedSuccessful','home_usedFailed']].sum(axis=1)).sum())}.")

    # ---- game coverage: Statcast regular-season games absent from the feed pull ---------------------------------------
    sc_games = sc.drop_duplicates("game_pk")[["game_pk", "game_date", "home_team", "away_team"]]
    miss_g = sc_games[~sc_games["game_pk"].isin(fp["gamePk"])]
    rep.append(f"- Game coverage: {len(miss_g)} Statcast regular-season games are absent from the feed pull"
               + (f" ({', '.join(str(x) for x in miss_g['game_pk'].head(25))})" if len(miss_g) else "") +
               f"; {int((~fp['gamePk'].isin(sc_games['game_pk'])).sum() and fp.loc[~fp['gamePk'].isin(sc_games['game_pk']), 'gamePk'].nunique())} feed games are not yet in Statcast (usually the latest date).")

    # ---- independent reconciliation with Baseball Savant's ABS leaderboards (per player) ---------------------------------
    sav_dir = os.path.join(ROOT, "data", "raw", "savant")
    if os.path.isdir(sav_dir):
        import unicodedata
        def _norm(x):
            return unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode().lower().replace(".", "").replace(" jr", "").strip()
        chal = fp[fp["challenged"] == 1]
        for role, fn in (("batter", "abs_challenges_batter_mlb_regular_2026.csv"), ("catcher", "abs_challenges_catcher_mlb_regular_2026.csv"),
                         ("pitcher", "abs_challenges_pitcher_mlb_regular_2026.csv")):
            path = os.path.join(sav_dir, fn)
            if not os.path.exists(path):
                continue
            try:
                sv = pd.read_csv(path)
                sv["key"] = sv["entity_name"].map(_norm)
                ours = chal[chal["role"] == role].copy(); ours["key"] = ours["challenger_name"].map(_norm)
                ours = ours.groupby("key").agg(n=("isOverturned", "size"), ov=("isOverturned", "sum")).reset_index()
                mm = sv.merge(ours, on="key", how="outer", indicator=True); both = mm[mm["_merge"] == "both"]
                rep.append(f"- Savant ABS leaderboard reconciliation ({role}s): {len(both)}/{len(sv)} Savant players matched by name "
                           f"({int((mm['_merge']=='left_only').sum())} Savant-only, {int((mm['_merge']=='right_only').sum())} ours-only); "
                           f"challenge counts identical for {(both['n_challenges']==both['n']).mean()*100:.1f}% of players, "
                           f"Σ|difference| = {int((both['n_challenges']-both['n']).abs().sum())} of {int(both['n_challenges'].sum()):,} "
                           f"({(both['n_challenges']-both['n']).abs().sum()/max(both['n_challenges'].sum(),1)*100:.2f}%); overturn counts identical for "
                           f"{(both['n_overturns']==both['ov']).mean()*100:.1f}%; league totals Savant {int(sv['n_challenges'].sum()):,}/{int(sv['n_overturns'].sum()):,} vs ours "
                           f"{int(ours['n'].sum()):,}/{int(ours['ov'].sum()):,} (snapshots may differ by a day of games).")
            except Exception as e:  # never let an audit line sink the build
                rep.append(f"- Savant reconciliation ({role}s) skipped: {e!r}")

    # ---- join to Statcast -----------------------------------------------------------------------------------------
    key = ["game_pk", "at_bat_number", "pitch_number"]
    fp = fp.rename(columns={"gamePk": "game_pk", "pitchNumber": "pitch_number"})
    m = fp.merge(sc.drop(columns=["game_date", "batter", "pitcher", "stand", "p_throws"]), on=key, how="left", suffixes=("", "_sc"))
    m["joined"] = m["sc_description"].notna() & m["balls"].notna()
    called_mask = m["call_original"].isin(["B", "C"]) & m["code"].isin(["B", "C", "*B"])
    common_games = set(fp["game_pk"]).intersection(set(sc["game_pk"]))
    in_common = m["game_pk"].isin(common_games)
    rep.append(f"- Join key (game_pk, at_bat_number = atBatIndex+1, pitch_number): match rate {m.loc[in_common, 'joined'].mean()*100:.3f}% of feed pitches "
               f"in the {len(common_games):,} games present in both sources; {m.loc[in_common & called_mask, 'joined'].mean()*100:.3f}% of called pitches; "
               f"{m.loc[in_common & (m['challenged']==1), 'joined'].mean()*100:.3f}% of challenged pitches.")
    j = m[m["joined"] & called_mask & in_common]
    cnt_ok = ((j["balls_pre"] == j["balls"]) & (j["strikes_pre"] == j["strikes"])).mean()
    outs_ok = (j["outs_pre"] == j["outs_when_up"]).mean()
    rep.append(f"- State agreement on joined called pitches: pre-pitch count identical {cnt_ok*100:.3f}%; outs identical {outs_ok*100:.3f}%.")
    # description vs feed code
    ct = pd.crosstab(j["code"], j["sc_description"])
    rep.append("- Feed code × Statcast description (called pitches):\n\n" + ct.to_string() + "\n")
    # geometry: Savant 2026 plate_x/plate_z (mid-plane) vs our propagated feed coordinates
    dx = (j["x_mid"] - j["plate_x"]) * 12; dz = (j["z_mid"] - j["plate_z"]) * 12
    dtop = (j["szTop"] - j["sz_top"]) * 12; dbot = (j["szBot"] - j["sz_bot"]) * 12
    rep.append(f"- Geometry: our plate-midpoint x/z (feed pX/pZ propagated with the 9-parameter fit) vs Savant plate_x/plate_z: "
               f"median |Δx| {dx.abs().median():.3f} in (95th pct {dx.abs().quantile(.95):.3f}), median |Δz| {dz.abs().median():.3f} in (95th {dz.abs().quantile(.95):.3f}); "
               f"ABS zone edges identical to Savant sz_top/sz_bot in {((dtop.abs()<0.01)&(dbot.abs()<0.01)).mean()*100:.2f}% of pitches.")

    # ---- eligibility --------------------------------------------------------------------------------------------
    no_abs = set(g.index[g["home_usedFailed"].isna() & g["away_usedFailed"].isna()])
    rep.append(f"- Games without an absChallenges block in gameData (ABS not in operation; excluded from all analyses): {len(no_abs)} — {sorted(no_abs)}.")
    elig = (m["joined"] & m["call_original"].isin(["B", "C"]) & m["sc_description"].isin(ELIGIBLE_DESC) & (m["balls"] <= 3) & (m["strikes"] <= 2)
            & m["d_in"].notna() & ~m["game_pk"].isin(no_abs))
    consistent = ((m["call_final"] == "B") & m["sc_description"].isin(["ball", "blocked_ball"])) | ((m["call_final"] == "C") & (m["sc_description"] == "called_strike"))
    rep.append(f"- Feed final call vs Statcast description inconsistent (dropped): {int((elig & ~consistent).sum()):,} pitches.")
    elig = elig & consistent
    o = m[elig].copy()
    # position players pitching: pitcher-game mean release speed < 75 mph (flag; excluded from perception/arrival analyses per METHODS §2)
    pg = sc.groupby(["game_pk", "pitcher"])["release_speed"].mean().rename("pg_speed").reset_index()
    o = o.merge(pg, on=["game_pk", "pitcher"], how="left")
    o["pos_pitcher"] = (o["pg_speed"] < 75).astype(int)
    rep.append(f"- Position players pitching (pitcher-game mean velocity < 75 mph): {int(o['pos_pitcher'].sum()):,} eligible pitches flagged (kept in the table, excluded from perception and arrival analyses).")
    rep.append(f"- Eligible opportunities (original call B/C, Statcast description in {sorted(ELIGIBLE_DESC)}, valid count/geometry, joined): {len(o):,} "
               f"of {int(called_mask.sum()):,} called pitches; excluded automatic balls: {int((m['sc_description']=='automatic_ball').sum()):,}; "
               f"challenged pitches retained: {int(o['challenged'].sum()):,} of {n_ch:,}.")

    # ---- state, side, tokens, truth, gain -------------------------------------------------------------------------
    o["orig"] = np.where(o["call_original"] == "C", "S", "B")
    o["bat_home"] = (o["inning_topbot"] == "Bot").astype(int)
    o["team_home"] = np.where(o["orig"] == "S", o["bat_home"], 1 - o["bat_home"]).astype(int)   # challenging side
    o["outs"] = o["outs_when_up"].astype(int)
    o["on1"] = o["on_1b"].notna().astype(int); o["on2"] = o["on_2b"].notna().astype(int); o["on3"] = o["on_3b"].notna().astype(int)
    o["bases_idx"] = o["on1"] + 2 * o["on2"] + 4 * o["on3"]
    o["sd_home"] = (o["home_score"] - o["away_score"]).astype(int)
    o["sd_team"] = np.where(o["team_home"] == 1, o["sd_home"], -o["sd_home"]).astype(int)
    o["balls"] = o["balls"].astype(int); o["strikes"] = o["strikes"].astype(int)
    o["tokens"] = np.where(o["team_home"] == 1, o["tokens_home"], o["tokens_away"]).astype(int)
    o["tokens_opp"] = np.where(o["team_home"] == 1, o["tokens_away"], o["tokens_home"]).astype(int)
    o["x_margin"] = np.where(o["orig"] == "S", o["d_in"], -o["d_in"])
    o["truth"] = (o["x_margin"] > 0).astype(int)
    o["h"] = (o["inning"] - 1) * 2 + o["bat_home"] + 1
    o["pa_ending"] = ((o["orig"] == "S") & (o["strikes"] == 2)) | ((o["orig"] == "B") & (o["balls"] == 3))
    o["pa_ending"] = o["pa_ending"].astype(int)
    # nearest edge type for the measurement-error model
    r = 1.45 / 12; half_w = 17 / 24
    d_side = np.maximum(np.abs(o["x_mid"]) - (half_w + r), -(np.abs(o["x_mid"]) - (half_w + r)))
    e_top = o["z_mid"] - (o["szTop"] + r); e_bot = (o["szBot"] - r) - o["z_mid"]; e_side = np.abs(o["x_mid"]) - (half_w + r)
    o["edge"] = np.where((np.abs(e_top) <= np.abs(e_bot)) & (np.abs(e_top) <= np.abs(e_side)), "top",
                         np.where(np.abs(e_bot) <= np.abs(e_side), "bottom", "side"))

    # WP flip gains: primary = count-composed WP (wp_count.py, v2); robustness = direct HGB fit with count (wp_model.py, v1)
    cube2 = WPCountCube(os.path.join(DERIVED, "wp_count_cube.npz"))
    cube = WPCube(os.path.join(DERIVED, "wp_cube.npz"))
    gain = np.zeros(len(o)); gain1 = np.zeros(len(o))
    for call in ("S", "B"):
        mk = (o["orig"] == call).values
        args_ = (o["inning"].values[mk], o["bat_home"].values[mk], o["outs"].values[mk], o["bases_idx"].values[mk],
                 o["sd_home"].values[mk], o["balls"].values[mk], o["strikes"].values[mk], call)
        gain[mk] = cube2.flip_gain(*args_)
        gain1[mk] = cube.flip_gain(*args_)
    o["g"] = np.maximum(gain, 0.0); o["g_v1"] = np.maximum(gain1, 0.0)
    o["wp_home_pre_v2"] = cube2.wp_home(o["inning"].values, o["bat_home"].values, o["outs"].values, o["bases_idx"].values, o["sd_home"].values, o["balls"].values, o["strikes"].values)
    wp2_S = cube2.wp_home(o["inning"].values, o["bat_home"].values, o["outs"].values, o["bases_idx"].values, o["sd_home"].values, o["balls"].values, o["strikes"].values + 1)
    wp2_B = cube2.wp_home(o["inning"].values, o["bat_home"].values, o["outs"].values, o["bases_idx"].values, o["sd_home"].values, o["balls"].values + 1, o["strikes"].values)
    o["dwp_home_actual_v2"] = np.where(o["orig"] == "S", wp2_S - o["wp_home_pre_v2"], wp2_B - o["wp_home_pre_v2"])
    # WP before the pitch and the WP change of the actual (original) call — for validation against Savant's delta_home_win_exp
    wp_pre = cube.wp_home(o["inning"].values, o["bat_home"].values, o["outs"].values, o["bases_idx"].values, o["sd_home"].values, o["balls"].values, o["strikes"].values)
    wp_post = cube.wp_after_pitch(o["inning"].values, o["bat_home"].values, o["outs"].values, o["bases_idx"].values, o["sd_home"].values,
                                  o["balls"].values, o["strikes"].values, "S")
    wp_postB = cube.wp_after_pitch(o["inning"].values, o["bat_home"].values, o["outs"].values, o["bases_idx"].values, o["sd_home"].values,
                                   o["balls"].values, o["strikes"].values, "B")
    o["wp_home_pre"] = wp_pre
    o["dwp_home_actual"] = np.where(o["orig"] == "S", wp_post - wp_pre, wp_postB - wp_pre)
    unch = o["challenged"] == 0
    v = o[unch & o["delta_home_win_exp"].notna()]
    corr = np.corrcoef(v["dwp_home_actual"], v["delta_home_win_exp"])[0, 1]
    mae = (v["dwp_home_actual"] - v["delta_home_win_exp"]).abs().mean()
    corr2 = np.corrcoef(v["dwp_home_actual_v2"], v["delta_home_win_exp"])[0, 1]; mae2 = (v["dwp_home_actual_v2"] - v["delta_home_win_exp"]).abs().mean()
    rep.append(f"- WP validation on {len(v):,} unchallenged called pitches vs Savant: ΔWP(home) of the original call — primary count-composed WP (v2): "
               f"r = {corr2:.3f}, MAE = {mae2*100:.3f} pp (mean |Savant Δ| = {v['delta_home_win_exp'].abs().mean()*100:.3f} pp); direct HGB-with-count WP (v1): r = {corr:.3f}, MAE = {mae*100:.3f} pp. "
               f"Pre-pitch WP vs Savant home_win_exp: r = {np.corrcoef(v['wp_home_pre_v2'], v['home_win_exp'])[0,1]:.4f} (v2), {np.corrcoef(v['wp_home_pre'], v['home_win_exp'])[0,1]:.4f} (v1). "
               f"Mean flip gain g: {o['g'].mean()*100:.3f} pp (v2) vs {o['g_v1'].mean()*100:.3f} pp (v1), r = {np.corrcoef(o['g'], o['g_v1'])[0,1]:.3f}.")

    # ---- truth vs ABS verdicts (go/no-go §3.3) --------------------------------------------------------------------
    ch = o[o["challenged"] == 1]
    agree = (ch["truth"] == ch["isOverturned"]).mean()
    band = ch["x_margin"].abs() >= 0.5
    rep.append(f"- Zone go/no-go: our any-part/midpoint classification agrees with the ABS verdict on {agree*100:.2f}% of {len(ch):,} challenged pitches "
               f"({(ch.loc[band,'truth']==ch.loc[band,'isOverturned']).mean()*100:.2f}% outside the ±0.5 in coin-flip band, n={int(band.sum()):,}); "
               f"pre-registered threshold 90%.")
    for edge in ("side", "top", "bottom"):
        s = ch[ch["edge"] == edge]
        rep.append(f"  - edge {edge}: n={len(s):,}, agreement {(s['truth']==s['isOverturned']).mean()*100:.2f}%")
    rr = ch.groupby("role")["isOverturned"].agg(["size", "mean"])
    rep.append("- Role split of challenges (overturn rate): " + "; ".join(f"{i}: n={int(r['size']):,}, {r['mean']*100:.1f}%" for i, r in rr.iterrows()) +
               f"; overall {ch['isOverturned'].mean()*100:.1f}% (public reference mid-Aug 2026: 53.6%; catchers 58.6, batters 48.5, pitchers 37.7).")

    keep = ["game_pk", "game_date", "home_team", "away_team", "at_bat_number", "pitch_number", "atBatIndex", "eventIndex", "inning", "bat_home", "h",
            "outs", "on1", "on2", "on3", "bases_idx", "sd_home", "sd_team", "balls", "strikes", "batter", "pitcher", "stand", "p_throws", "pitch_type",
            "release_speed", "orig", "call_original", "call_final", "description", "team_home", "tokens", "tokens_opp", "tokens_home", "tokens_away",
            "x_mid", "z_mid", "plate_x", "plate_z", "szTop", "szBot", "height_in", "d_in", "d_in_center", "x_margin", "truth", "edge", "pa_ending",
            "g", "g_v1", "wp_home_pre", "wp_home_pre_v2", "dwp_home_actual", "dwp_home_actual_v2", "home_win_exp", "delta_home_win_exp", "pos_pitcher", "pg_speed",
            "challenged", "isOverturned", "role", "challenger_id", "challenger_name", "challengeTeamId", "review_level", "hp_umpire", "startTime"]
    o = o[keep].sort_values(["game_date", "game_pk", "atBatIndex", "eventIndex"]).reset_index(drop=True)
    o.to_parquet(args.out, index=False)
    rep.append(f"- Output: {args.out} — {len(o):,} rows, {o['game_pk'].nunique():,} games; challenges {int(o['challenged'].sum()):,}.")
    with open(args.report, "w") as fh:
        fh.write("\n".join(rep) + "\n")
    print("\n".join(rep))


if __name__ == "__main__":
    main()
