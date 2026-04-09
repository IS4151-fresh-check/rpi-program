"""
Gas freshness model — loads the trained Decision Tree and predicts.
"""

import os
import json
import numpy as np
import joblib

MODEL_DIR = os.path.join(os.path.dirname(__file__), "gas_models")

STAGE_TO_ACTION = {
    "fresh": "maintain_display",
    "ripe": "promote_for_sale",
    "overripe": "apply_discount",
    "spoiled": "remove_from_shelf",
}

# Load once at import time
_model = joblib.load(os.path.join(MODEL_DIR, "freshcheck_decision_tree.joblib"))
_encoder = joblib.load(os.path.join(MODEL_DIR, "label_encoder.joblib"))
with open(os.path.join(MODEL_DIR, "model_config.json")) as f:
    _config = json.load(f)

WINDOW_SIZE = _config["window_size"]
FEATURE_COLUMNS = _config["feature_columns"]


def predict_gas(features):
    """
    Run the Decision Tree on engineered features.

    Returns:
        dict with gasStage, gasConfidence, action, ppmSlope
        or None if features is None (not enough data yet)
    """
    if features is None:
        return None

    X = np.array([[features.get(col, 0) for col in FEATURE_COLUMNS]])
    prediction = _model.predict(X)[0]
    probabilities = _model.predict_proba(X)[0]

    stage = _encoder.inverse_transform([prediction])[0]

    return {
        "gasStage": stage,
        "gasConfidence": round(float(probabilities[prediction]), 4),
        "action": STAGE_TO_ACTION.get(stage, "unknown"),
        "ppmSlope": round(features.get("ppm_slope", 0), 2),
    }