"""Shared definitions used in the fit, policy, card, and audit."""
import numpy as np


def count_class(balls, strikes):
    """Either possible ruling can end the PA: three balls OR two strikes.

    This does not assert that the original umpire call itself ended the PA.
    """
    return np.where((np.asarray(balls) == 3) | (np.asarray(strikes) == 2),
                    "PA-ending", "count-changing")


def validate_horizon(op, hi, hmax):
    for name, frame in (("opportunities", op), ("half innings", hi)):
        h = frame["h"].to_numpy()
        if np.any(~np.isfinite(h) | (h < 1) | (h > hmax) | (h != np.floor(h))):
            raise ValueError(f"{name} exceed the supported horizon 1..{hmax}; extend the grid, do not collapse innings")
    if hi.duplicated(["game_id", "h"]).any():
        raise ValueError("Duplicate half-inning paths would replay opportunities")
    covered = set(zip(hi["game_id"], hi["h"]))
    if not set(zip(op["game_id"], op["h"])).issubset(covered):
        raise ValueError("Every opportunity must have a half-inning path")
