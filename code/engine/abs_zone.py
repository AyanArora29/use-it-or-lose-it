"""
abs_zone.py — geometry of MLB's 2026 ABS strike zone, from public Statcast fields.

Rule (MLB press release, Sept 2025): the ABS zone is a two-dimensional rectangle set at the middle of
home plate, 17 inches wide, with top = 53.5% and bottom = 27% of the batter's height; a pitch is a
strike if ANY PART of the ball touches the rectangle.

Statcast reports plate_x / plate_z at the FRONT of home plate (y = 17/12 ft from the plate's back point).
The plate's midpoint is 8.5 inches behind the front edge (y = 8.5/12 ft). We propagate the tracked
trajectory from the front to the midpoint using the public constant-acceleration fields
(vx0, vy0, vz0, ax, ay, az, all defined at y0 = 50 ft).

All distances in FEET unless noted. Ball radius: 2.9 in diameter -> r = 1.45 in.
"""
from __future__ import annotations

import math

import numpy as np

Y0 = 50.0                  # ft: reference plane for vx0/vy0/vz0
Y_FRONT = 17.0 / 12.0      # ft: front edge of the plate (where plate_x/plate_z are reported)
Y_MID = 8.5 / 12.0         # ft: midpoint of the plate depth (where ABS judges)
PLATE_HALF_WIDTH = 8.5 / 12.0
BALL_RADIUS = 1.45 / 12.0
TOP_FRAC, BOT_FRAC = 0.535, 0.27


def _time_to_plane(y_start, y_target, vy, ay):
    """Time for the ball to travel from plane y_start to y_target (ball moves toward decreasing y, vy<0)."""
    # y(t) = y_start + vy t + 0.5 ay t^2 = y_target  ->  0.5 ay t^2 + vy t + (y_start - y_target) = 0
    c = y_start - y_target
    disc = vy * vy - 2.0 * ay * c
    disc = np.where(disc < 0, np.nan, disc)
    # smaller positive root (vy negative, ay small positive drag)
    with np.errstate(invalid="ignore", divide="ignore"):
        t = np.where(np.abs(ay) > 1e-9, (-vy - np.sqrt(disc)) / ay, -c / vy)
    return t


def propagate_to_midpoint(plate_x, plate_z, vx0, vy0, vz0, ax, ay, az):
    """Vectorized. Returns (x_mid, z_mid) in feet at the plate midpoint plane."""
    plate_x, plate_z = np.asarray(plate_x, float), np.asarray(plate_z, float)
    vx0, vy0, vz0 = np.asarray(vx0, float), np.asarray(vy0, float), np.asarray(vz0, float)
    ax, ay, az = np.asarray(ax, float), np.asarray(ay, float), np.asarray(az, float)
    t_front = _time_to_plane(Y0, Y_FRONT, vy0, ay)          # 50 ft -> front of plate
    vx_f = vx0 + ax * t_front
    vy_f = vy0 + ay * t_front
    vz_f = vz0 + az * t_front
    dt = _time_to_plane(Y_FRONT, Y_MID, vy_f, ay)             # front -> midpoint (~8.5 in)
    x_mid = plate_x + vx_f * dt + 0.5 * ax * dt * dt
    z_mid = plate_z + vz_f * dt + 0.5 * az * dt * dt
    return x_mid, z_mid


def abs_zone_bounds(height_in):
    """Zone rectangle (ft) for a batter of given height in inches: (x_lo, x_hi, z_lo, z_hi) — ball CENTER
    coordinates, i.e. already expanded by the ball radius per the 'any part of the ball' rule."""
    h = np.asarray(height_in, float) / 12.0
    x_lo = -(PLATE_HALF_WIDTH + BALL_RADIUS)
    x_hi = +(PLATE_HALF_WIDTH + BALL_RADIUS)
    z_lo = BOT_FRAC * h - BALL_RADIUS
    z_hi = TOP_FRAC * h + BALL_RADIUS
    return x_lo, x_hi, z_lo, z_hi


def signed_miss_inches(x, z, height_in, expand_ball=True):
    """Signed distance (inches) from the ball CENTER to the ABS rectangle (expanded by ball radius if
    expand_ball). Negative = inside the zone (a true strike), positive = outside (a true ball).
    Uses the Euclidean distance to the rectangle outside, and minus the inset depth inside."""
    x, z = np.asarray(x, float), np.asarray(z, float)
    x_lo, x_hi, z_lo, z_hi = abs_zone_bounds(height_in)
    if not expand_ball:
        x_lo, x_hi, z_lo, z_hi = x_lo + BALL_RADIUS, x_hi - BALL_RADIUS, z_lo + BALL_RADIUS, z_hi - BALL_RADIUS
    dx = np.maximum(np.maximum(x_lo - x, x - x_hi), 0.0)
    dz = np.maximum(np.maximum(z_lo - z, z - z_hi), 0.0)
    outside = np.sqrt(dx * dx + dz * dz)
    inside = np.minimum(np.minimum(x - x_lo, x_hi - x), np.minimum(z - z_lo, z_hi - z))
    d = np.where(outside > 0, outside, -inside)
    return d * 12.0


def abs_is_strike(x, z, height_in):
    return signed_miss_inches(x, z, height_in) <= 0.0


if __name__ == "__main__":
    # --- self-tests on synthetic pitches ---
    # 1) A pitch thrown straight (no lateral accel) keeps its x when propagated; z drops slightly (gravity).
    x_mid, z_mid = propagate_to_midpoint(plate_x=0.0, plate_z=2.5, vx0=0.0, vy0=-130.0, vz0=-5.0,
                                         ax=0.0, ay=25.0, az=-32.17)
    assert abs(x_mid - 0.0) < 1e-9, x_mid
    assert 2.35 < z_mid < 2.45, z_mid          # falls ~1.2 in over 8.5 in of travel (vz at plate ≈ -18 ft/s)
    # 2) A pitch with lateral acceleration (sweeper): moves horizontally between front and midpoint.
    x_mid2, _ = propagate_to_midpoint(0.70, 2.5, vx0=6.0, vy0=-120.0, vz0=-4.0, ax=-15.0, ay=25.0, az=-30.0)
    assert x_mid2 < 0.70 + 0.05 and x_mid2 > 0.60, x_mid2   # ~4-5 in of horizontal break spread over ~7 ms
    # 3) Zone for a 6'2" batter (74 in): bottom 27% = 19.98 in, top 53.5% = 39.59 in (ball center expanded by 1.45 in)
    x_lo, x_hi, z_lo, z_hi = abs_zone_bounds(74)
    assert abs(x_hi * 12 - 9.95) < 1e-6 and abs(z_lo * 12 - (19.98 - 1.45)) < 1e-6 and abs(z_hi * 12 - (39.59 + 1.45)) < 1e-6
    # 4) Signed miss: dead center is deep inside; a ball 12 in outside is +ish 2 in beyond the expanded edge
    d_center = signed_miss_inches(0.0, 2.5, 74)
    d_out = signed_miss_inches(1.0, 2.5, 74)     # 12 in from center; expanded half-width 9.95 -> +2.05 in
    assert d_center < -8 and abs(d_out - 2.05) < 1e-6, (d_center, d_out)
    # 5) Vertical: pitch at 18.5 in for a 74-in batter -> below expanded bottom (18.53) by 0.03 in -> ball
    d_low = signed_miss_inches(0.0, 18.5 / 12, 74)
    assert 0 < d_low < 0.1, d_low
    print("abs_zone self-tests passed")
    print(f"6'2\" batter zone (ball-center coords, inches): x±{x_hi*12:.2f}, z [{z_lo*12:.2f}, {z_hi*12:.2f}]")
