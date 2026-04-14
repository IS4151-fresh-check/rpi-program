"""
Gas Feature Engineering
=======================
Computes sliding-window statistics from a buffer of MQ2 sensor readings.
This is the same logic as the v8 training notebook.
"""

import numpy as np
from scipy import stats

# The leaf RPis collect data every ~30 seconds, the fog polls every 60s.
# For feature engineering we treat each polled reading as one timestep.
# Adjust based on actual leaf RPi sampling rate.
READING_INTERVAL_SECONDS = 60


def engineer_gas_features(readings_buffer, window_size=3, recent_window=2):
    """
    Compute features from the most recent readings in the buffer.

    Parameters:
        readings_buffer: list of dicts with keys: timestamp, voltage, ppm
        window_size: number of readings in sliding window (36 = 6 hours)
        recent_window: number of readings for recent trend (6 = 1 hour)

    Returns:
        dict of 18 feature values, or None if not enough data yet
    """
    if len(readings_buffer) < window_size + 1:
        return None

    window = readings_buffer[-window_size:]
    recent = readings_buffer[-recent_window:]
    current = readings_buffer[-1]

    ppm_values = np.array([r["ppm"] for r in window])
    v_values = np.array([r["voltage"] for r in window])
    recent_ppm = np.array([r["ppm"] for r in recent])

    hours_elapsed = len(readings_buffer) * READING_INTERVAL_SECONDS / 3600

    # PPM statistics
    ppm_mean = np.mean(ppm_values)
    ppm_std = np.std(ppm_values)
    ppm_min = np.min(ppm_values)
    ppm_max = np.max(ppm_values)
    ppm_range = ppm_max - ppm_min
    ppm_current = current["ppm"]
    ppm_cv = ppm_std / ppm_mean if ppm_mean > 0 else 0

    # Slope via linear regression
    x_hours = np.arange(len(ppm_values)) * (READING_INTERVAL_SECONDS / 3600)
    slope_result = stats.linregress(x_hours, ppm_values)
    ppm_slope = slope_result.slope
    ppm_r_squared = slope_result.rvalue ** 2

    # Recent trend
    recent_slope = 0
    if len(recent_ppm) >= 3:
        x_recent = np.arange(len(recent_ppm)) * (READING_INTERVAL_SECONDS / 3600)
        recent_slope = stats.linregress(x_recent, recent_ppm).slope

    ppm_acceleration = recent_slope - ppm_slope

    # Voltage features
    v_mean = np.mean(v_values)
    v_std = np.std(v_values)
    v_current = current["voltage"]
    v_slope = stats.linregress(x_hours, v_values).slope

    # Percentiles
    ppm_q25 = np.percentile(ppm_values, 25)
    ppm_q75 = np.percentile(ppm_values, 75)
    ppm_iqr = ppm_q75 - ppm_q25

    return {
        "hours_elapsed": hours_elapsed,
        "ppm_current": ppm_current,
        "ppm_std": ppm_std,
        "ppm_min": ppm_min,
        "ppm_max": ppm_max,
        "ppm_range": ppm_range,
        "ppm_cv": ppm_cv,
        "ppm_slope": ppm_slope,
        "ppm_r_squared": ppm_r_squared,
        "ppm_q25": ppm_q25,
        "ppm_q75": ppm_q75,
        "ppm_iqr": ppm_iqr,
        "recent_slope": recent_slope,
        "ppm_acceleration": ppm_acceleration,
        "v_mean": v_mean,
        "v_std": v_std,
        "v_current": v_current,
        "v_slope": v_slope,
    }
