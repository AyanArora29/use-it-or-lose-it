"""
perception.py — the structural perception/decision model and the threshold-in-inches table.

Model (METHODS §5): the eligible challenger perceives m = d + ε, ε ~ N(0, σ_role²), where d is the true signed miss
distance of the call in the challenger's favour (d > 0 means the call was wrong in a way that helps the challenger if
overturned; d < 0 means the call was right). Given m, the posterior probability the call is wrong (flat prior on d) is
        p(m) = Φ(m / σ_role).
The DP decision rule "challenge iff p·g > (1−p)·MTV" then has the closed form
        challenge iff m > m* = σ_role · Φ⁻¹( MTV / (g + MTV) ).
So the deliverable table is m*(inning, tokens, leverage bucket) in inches per role.

Estimation (when 2026 challenge data are attached): maximum likelihood on all called pitches, outcome ∈ {not challenged,
challenged & upheld, challenged & overturned}, with P(challenge | d) = Φ((d − τ)/σ) for the eligible role and
P(overturned | challenged, d) = 1[d > 0] (up to zone-reconstruction error handled by a small classification noise η).
This file provides: the likelihood, a fitter (scipy), the threshold formula, and a synthetic-data self-test.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize
from scipy.stats import norm


def p_success(m, sigma):
    return norm.cdf(np.asarray(m, float) / sigma)


def threshold_inches(g, mtv, sigma):
    """m* such that Φ(m*/σ)·g = (1−Φ(m*/σ))·MTV. Returns +inf if g<=0."""
    g = np.asarray(g, float); mtv = np.asarray(mtv, float)
    q = np.clip(mtv / (g + mtv), 1e-9, 1 - 1e-9)
    out = sigma * norm.ppf(q)
    return np.where(g <= 0, np.inf, out)


# ------------------------------------------------------------------------------------------------
# Likelihood for the (τ, σ, η) model on called pitches
# ------------------------------------------------------------------------------------------------
def negloglik(params, d, y, tau_x=None):
    """params = [log σ, τ0, τ1..τk (if tau_x has k columns), logit η]
       d: true signed miss (in inches, favour of the eligible challenger); y: 0 not challenged, 1 challenged-upheld,
       2 challenged-overturned. tau_x: optional covariates for the threshold (e.g., inning dummies, tokens, leverage)."""
    sigma = np.exp(params[0])
    if tau_x is None:
        tau = params[1]
        eta = 1 / (1 + np.exp(-params[2]))
    else:
        k = tau_x.shape[1]
        tau = params[1] + tau_x @ params[2:2 + k]
        eta = 1 / (1 + np.exp(-params[2 + k]))
    p_ch = norm.cdf((d - tau) / sigma)                       # P(perceived m > τ)
    p_ch = np.clip(p_ch, 1e-12, 1 - 1e-12)
    wrong = (d > 0).astype(float)
    p_ov = np.clip(wrong * (1 - eta) + (1 - wrong) * eta, 1e-12, 1 - 1e-12)   # overturned given challenged
    ll = np.where(y == 0, np.log(1 - p_ch), np.where(y == 1, np.log(p_ch) + np.log(1 - p_ov), np.log(p_ch) + np.log(p_ov)))
    return -ll.sum()


def fit_perception(d, y, tau_x=None, x0=None):
    k = 0 if tau_x is None else tau_x.shape[1]
    if x0 is None:
        x0 = np.r_[np.log(1.5), 1.0, np.zeros(k), -3.0]
    res = minimize(negloglik, x0, args=(d, y, tau_x), method="L-BFGS-B")
    sigma = float(np.exp(res.x[0])); tau0 = float(res.x[1]); beta = res.x[2:2 + k]; eta = float(1 / (1 + np.exp(-res.x[2 + k])))
    return dict(sigma=sigma, tau0=tau0, beta=beta, eta=eta, nll=res.fun, ok=res.success)


if __name__ == "__main__":
    # ---- self-test on synthetic data --------------------------------------------------------
    rng = np.random.default_rng(3)
    n = 200_000
    d = rng.normal(-3.0, 3.0, n)                 # most calls are right (d<0), some wrong (d>0)
    sigma_true, tau_true, eta_true = 1.4, 1.2, 0.03
    m = d + rng.normal(0, sigma_true, n)
    ch = m > tau_true
    ov = np.where(d > 0, rng.random(n) > eta_true, rng.random(n) < eta_true)
    y = np.where(~ch, 0, np.where(ov, 2, 1))
    fit = fit_perception(d, y)
    print("fit:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in fit.items() if k != 'beta'})
    assert abs(fit["sigma"] - sigma_true) < 0.1 and abs(fit["tau0"] - tau_true) < 0.1 and abs(fit["eta"] - eta_true) < 0.01
    # observed success rate among challenges (what leaderboards report) vs the structural quantities
    print(f"observed overturn rate among challenges: {(y==2).sum()/(y>0).sum():.3f}; challenge rate {(y>0).mean():.4f}")
    # threshold table demo: g = 2 pp, MTV from 0.1 pp to 3 pp
    for mtv in [0.001, 0.005, 0.01, 0.02, 0.03]:
        print(f"g=0.02, MTV={mtv:.3f}: challenge if perceived miss > {float(threshold_inches(0.02, mtv, sigma_true)):+.2f} in "
              f"(success prob at threshold {float(p_success(threshold_inches(0.02, mtv, sigma_true), sigma_true)):.2f})")
    print("perception self-test passed")
