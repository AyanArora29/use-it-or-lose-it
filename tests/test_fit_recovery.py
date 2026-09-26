"""Recover a known signal scale under the fitted model's actual assumptions."""
import sys
from pathlib import Path
import numpy as np
from scipy.stats import norm
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'code/analysis')]
from perception_fit_2026 import fit_probit

def test_known_probit_scale_and_thresholds_are_recovered():
    rng=np.random.default_rng(4719)
    x=rng.normal(0,4,40000); cells=rng.integers(0,3,len(x))
    sigma=2.; tau=np.array([0.,1.5,3.])
    y=rng.binomial(1,norm.cdf((x-tau[cells])/sigma))
    fit=fit_probit(x,y,cells,3)
    assert abs(fit['sigma']-sigma)<.10
    np.testing.assert_allclose(fit['tau'],tau,atol=.13)
