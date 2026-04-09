"""
Gas Model
=========
Loads the trained chained Decision Tree (v8) and runs predictions.

The chained model takes 21 features as input:
  - 18 sliding-window gas features (from gas_features.py)
  - 3 cascading one-hot CV features (from cv_encoder.py)
"""

import os
import json
import logging
import numpy as np
import joblib

from config import MODEL_PATH, ENCODER_PATH, CONFIG_PATH, STAGE_TO_ACTION

logger = logging.getLogger("fog")

# Load model artifacts once at import time
_model = joblib.load(MODEL_PATH)
_encoder = joblib.load(ENCODER_PATH)
with open(CONFIG_PATH) as f:
    _config = json.load(f)

# Public constants
WINDOW_SIZE = _config["window_size"]
FEATURE_COLUMNS = _config["feature_columns"]  # ordered list of all 21 features

logger.info(f"Chained model loaded: depth={_config['model_depth']}, "
            f"features={len(FEATURE_COLUMNS)}, version={_config['version']}")


def predict_chained(gas_features, cv_encoded):
    """
    Run the chained Decision Tree.

    Parameters:
        gas_features: dict from engineer_gas_features() — 18 features
                      OR None if buffer doesn't have enough data yet
        cv_encoded:   dict from encode_cv_stage() — 3 binary CV features

    Returns:
        dict with stage, confidence, action, ppmSlope
        OR None if gas features are not available
    """
    if gas_features is None:
        return None

    # Combine gas + CV features
    combined = {**gas_features, **cv_encoded}

    # Build feature vector in the correct column order
    X = np.array([[combined.get(col, 0) for col in FEATURE_COLUMNS]])

    # Predict
    prediction = _model.predict(X)[0]
    probabilities = _model.predict_proba(X)[0]

    stage = _encoder.inverse_transform([prediction])[0]
    confidence = float(probabilities[prediction])

    return {
        "gasStage": stage,
        "gasConfidence": round(confidence, 4),
        "action": STAGE_TO_ACTION.get(stage, "unknown"),
        "ppmSlope": round(gas_features.get("ppm_slope", 0), 2),
    }
