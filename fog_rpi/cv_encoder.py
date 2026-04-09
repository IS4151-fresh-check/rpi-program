"""
CV Stage Encoder
================
Cascading one-hot encoding for the CV model's ordinal stage prediction.

For ordinal stages fresh < ripe < overripe < spoiled, this encoding
preserves the ordering relationship by encoding "is at least X":

    fresh    -> [0, 0, 0]
    ripe     -> [1, 0, 0]
    overripe -> [1, 1, 0]
    spoiled  -> [1, 1, 1]

Returns: [cv_at_least_ripe, cv_at_least_overripe, cv_at_least_spoiled]
"""

from config import STAGE_ORDER


def encode_cv_stage(cv_stage):
    """
    Convert a CV stage string into 3 cascading binary features.

    Parameters:
        cv_stage: one of 'fresh', 'ripe', 'overripe', 'spoiled'
                  (or None / unknown — defaults to fresh)

    Returns:
        dict with three binary features ready for the chained model
    """
    if cv_stage is None or cv_stage not in STAGE_ORDER:
        # Fallback: treat unknown as fresh (most conservative)
        idx = 0
    else:
        idx = STAGE_ORDER.index(cv_stage)

    return {
        "cv_at_least_ripe": 1 if idx >= 1 else 0,
        "cv_at_least_overripe": 1 if idx >= 2 else 0,
        "cv_at_least_spoiled": 1 if idx >= 3 else 0,
    }
