"""
Fog RPi Configuration
=====================
All constants for the fog processor in one place.
"""

import os

# ── Model paths ──────────────────────────────────────────────
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models_v8")
MODEL_PATH = os.path.join(MODEL_DIR, "freshcheck_chained_tree.joblib")
ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.joblib")
CONFIG_PATH = os.path.join(MODEL_DIR, "model_config.json")

# ── Worker (leaf) RPi nodes ──────────────────────────────────
# Map: section_id (MongoDB ObjectId string) -> leaf RPi endpoint
# NEED TO UPDATE: replace with actual ObjectIds and IP addresses of your leaf RPis
# WORKER_NODES = {
#     # "69d707b8d45b6e355fbcad4a": "http://192.168.137.224:5000/sensors/fetch/latest",
#     "69d27be66dfc8dac776fa9ce": "http://192.168.1.101:5000/sensors/fetch/latest",
#     "69d27be66dfc8dac776fa9cf": "http://192.168.1.102:5000/sensors/fetch/latest",
#     "69d27be66dfc8dac776fa9d0": "http://192.168.1.103:5000/sensors/fetch/latest",
# }
WORKER_NODES = {"test-section-001": "http://localhost:9999/fake"} # for testing without real leaf RPis


# ── Backend cloud API ────────────────────────────────────────
# NEED TO UPDATE: replace with your actual backend API endpoint for saving predictions
# BACKEND_URL = "https://192.168.137.224:3000/api/save"
BACKEND_URL = "https://httpbin.org/post" # for testing without a real backend


# ── Polling intervals ────────────────────────────────────────
POLL_INTERVAL_SECONDS = 60      # how often fog polls each leaf RPi
# POLL_INTERVAL_SECONDS = 5       # for testing with httpbin.org (no real leaf RPis)
LEAF_REQUEST_TIMEOUT = 15       # HTTP timeout for leaf requests
BACKEND_REQUEST_TIMEOUT = 30    # HTTP timeout for backend POST

# For testing without a real backend, you can use httpbin.org which will echo the POST data
# WORKER_NODES = {"test-section-001": "http://localhost:9999/fake"}
# BACKEND_URL = "https://httpbin.org/post"
# POLL_INTERVAL_SECONDS = 5

# ── Stage definitions ────────────────────────────────────────
# Must match the order used during training (see model_config.json)
STAGE_ORDER = ["fresh", "ripe", "overripe", "spoiled"]

STAGE_TO_ACTION = {
    "fresh": "maintain_display",
    "ripe": "promote_for_sale",
    "overripe": "apply_discount",
    "spoiled": "remove_from_shelf",
}
