"""Regression checks for errors found in the September 26 scientific audit."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'code/engine'), str(ROOT / 'code/analysis')]
from abs_zone import signed_miss_from_bounds, BALL_RADIUS, PLATE_HALF_WIDTH
from decision_state import count_class
from dp import solve, DMAX, HMAX
from dp_fast import make_arrays, solve_fast, simulate_fast
from wp_model import WPCube
from tier1_dp_2026 import simulate, realized_observed
from perception_fit_2026 import add_cells
import build_all


def test_round_ball_does_not_fill_square_corners():
    r, w = BALL_RADIUS, PLATE_HALF_WIDTH
    # Square expansion incorrectly calls this diagonal pitch a strike.
    assert signed_miss_from_bounds(w + .8*r, 3 + .8*r, 1.5, 3) > 0
    assert signed_miss_from_bounds(w + .6*r, 3 + .6*r, 1.5, 3) < 0
    assert signed_miss_from_bounds(w + r, 2, 1.5, 3) == pytest.approx(0, abs=1e-12)
    assert signed_miss_from_bounds(0, 2, 1.5, 3) < 0


def streams(last=26):
    hi = pd.DataFrame(dict(season=2026, game_id=1, h=np.arange(1, last+1), sd_start=0, sd_end=0))
    op = pd.DataFrame([dict(season=2026, game_id=1, team_home=t, h=h, score_diff_home=0,
                             g=.1, p=1., outs=0) for t in (0,1) for h in (24,25,26)])
    return op, hi


def test_thirteenth_inning_is_not_collapsed_or_replayed():
    op, hi = streams()
    A = make_arrays(op, hi)
    assert sum(A['inst_hi'] - A['inst_lo']) == len(op)
    v, c = solve(op, hi, verbose=False)
    vf, cf = solve_fast(A)
    assert v[24, DMAX, 2] == pytest.approx(.3)
    assert v[25, DMAX, 2] == pytest.approx(.2)
    assert v[26, DMAX, 2] == pytest.approx(.1)
    np.testing.assert_allclose(v, vf, atol=1e-12)
    np.testing.assert_allclose(c, cf, atol=1e-12)


@pytest.mark.parametrize('error', ['long', 'duplicate', 'uncovered'])
def test_invalid_paths_fail_in_both_solvers(error):
    op, hi = streams()
    if error == 'long':
        op.loc[0, 'h'] = HMAX + 1
    elif error == 'duplicate':
        hi = pd.concat([hi, hi.iloc[:1]])
    else:
        hi = hi[hi.h != 26]
    with pytest.raises(ValueError):
        solve(op, hi, verbose=False)
    with pytest.raises(ValueError):
        make_arrays(op, hi)


def test_walk_forces_only_occupied_chain_and_walkoff_is_terminal():
    bases, score = WPCube.walk_state(np.arange(8), np.zeros(8), np.ones(8))
    np.testing.assert_array_equal(bases, [1,3,3,7,5,7,7,7])
    np.testing.assert_array_equal(score, [0,0,0,0,0,0,0,1])
    cube = WPCube.__new__(WPCube)
    cube.cube = np.full((11,2,3,8,21,4,3), .5)
    assert cube.wp_after_pitch(9,1,0,7,0,3,0,'B') == 1
    assert cube.wp_after_pitch(8,1,0,7,0,3,0,'B') == .5
    assert cube.wp_after_pitch(9,0,2,0,1,0,2,'S') == 1
    assert cube.wp_after_pitch(9,1,2,0,-1,0,2,'S') == 0


def test_perception_and_card_use_same_count_definition():
    o = pd.DataFrame(dict(orig=['S','B','S','B'], balls=[3,0,0,0], strikes=[0,2,0,0],
                          inning=[1]*4, g=[.01,.02,.03,.04], tokens=[2]*4))
    # Deliberately stale source flag must not control classification.
    o['pa_ending'] = 0
    result, _ = add_cells(o)
    np.testing.assert_array_equal(result.cnt, count_class(o.balls,o.strikes))
    assert list(result.cnt[:2]) == ['PA-ending','PA-ending']


def test_observed_simulator_switches_threshold_after_lost_token():
    # First pitch certainly challenged and lost; second would be challenged only with 2 tokens.
    op = pd.DataFrame(dict(game_id=[1,1], team_home=[1,1], x=[0.,0.], g=[.1,.1], truth=[0,1],
         role=['bat','bat'], inning=[9,9], h=[18,18], score_diff_home=[0,0], outs=[0,1],
         balls=[0,0], strikes=[0,0], cell=['9+|2|high|count-changing']*2, challenged=[1,0], overturned=[0,0]))
    pm = {s:(np.array([-1.,1.]),np.array([0.,1.]),1.) for s in ('bat','fld')}
    tau = {'9+|2|high|count-changing':-100., '9+|1|high|count-changing':100.}
    fit = {'sides':{'bat':{'pooled':{'tau':tau,'sigma':1.}}}}
    C = np.zeros((HMAX+2,13,3,3))
    result, prop = simulate(op,C,pm,'observed_model',D=10,fit=fit)
    assert list(prop) == [1.,0.]
    assert result.gain.iloc[0] == 0
    hi = pd.DataFrame(dict(game_id=[1],h=[18],sd_start=[0],sd_end=[0]))
    A = make_arrays(op.assign(p=.5),hi)
    fast, prop_fast = simulate_fast(A['op_sorted'],C,pm,'observed_model',D=10,
                                   tau_opp=np.array([[100.,-100.],[100.,-100.]]))
    assert list(prop_fast) == [1.,0.]
    assert fast.gain.iloc[0] == 0


def test_recorded_verdict_is_an_explicit_sensitivity():
    op = pd.DataFrame(dict(game_id=[1],team_home=[0],challenged=[1],truth=[1],overturned=[0],g=[.1]))
    assert realized_observed(op).gain.iloc[0] == .1
    assert realized_observed(op,'overturned').gain.iloc[0] == 0


def test_core_failure_stops_pipeline(monkeypatch):
    calls = []
    def failed(script, **kwargs):
        calls.append(script)
        return False
    monkeypatch.setattr(build_all,'run',failed)
    with pytest.raises(SystemExit,match='Core analysis failed'):
        build_all.main()
    assert calls == ['build_opps_2026.py']
