#!/usr/bin/env python3
"""
Fog RPi Processor — Main Entry Point
=====================================
Polls each leaf RPi every 60 seconds, runs the chained gas model
on the collected readings, and POSTs the processed result to the backend.

Architecture:

  Leaf RPi 1 (sensors + CV)  --\\
                                 \\
  Leaf RPi 2 (sensors + CV)  ----+--->  Fog RPi (this script)  --->  Backend  --->  MongoDB
                                 /                |
  Leaf RPi 3 (sensors + CV)  --/                  |
                                                  +--> Chained gas model
                                                      (gas features + CV stage)

Usage:
    python main.py
"""

import time
import logging
from datetime import datetime

from config import (
    WORKER_NODES, POLL_INTERVAL_SECONDS, STAGE_TO_ACTION
)
from leaf_client import fetch_leaf_data
from gas_features import engineer_gas_features
from cv_encoder import encode_cv_stage
from gas_model import predict_chained, WINDOW_SIZE
from section_buffers import SectionBuffers
from backend_client import send_to_backend

# ── Logging ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("fog")


def build_payload(section_id, leaf_data, gas_prediction):
    """
    Build the payload for POST /api/save based on the team's schema.

    Combines:
      - Section identification
      - Raw sensor data from leaf RPi
      - CV model output from leaf RPi
      - Gas model output from our chained model (or fallback if buffering)
    """
    payload = {
        "sectionId": section_id,
        # ── Environmental sensors (BME280, from leaf) ──
        "temperature": leaf_data.get("temperature"),
        "humidity": leaf_data.get("humidity"),
        # ── Raw gas reading (MQ2, from leaf) ──
        "ppm": leaf_data.get("ppm"),
        # ── CV model output (from leaf) ──
        "cvStage": leaf_data.get("cvStage"),
        "cvConfidence": leaf_data.get("cvConfidence"),
        "imageBase64": leaf_data.get("imageBase64"),
    }

    # Gas model output — populated if model has enough data, else nulls
    if gas_prediction:
        payload["gasStage"] = gas_prediction["gasStage"]
        payload["gasConfidence"] = gas_prediction["gasConfidence"]
        payload["ppmSlope"] = gas_prediction["ppmSlope"]
        payload["action"] = gas_prediction["action"]
    else:
        payload["gasStage"] = None
        payload["gasConfidence"] = None
        payload["ppmSlope"] = None
        payload["action"] = None

    return payload


def process_section(section_id, url, buffers):
    """
    Process one leaf RPi:
      1. Fetch latest sensor data
      2. Append gas reading to this section's buffer
      3. Compute gas features (if enough data)
      4. Encode CV prediction
      5. Run chained model
      6. POST to backend
    """
    # Step 1: fetch
    leaf_data = fetch_leaf_data(section_id, url)
    if leaf_data is None:
        return False

    # Step 2: append to buffer
    gas_reading = {
        "timestamp": datetime.now(),
        "ppm": leaf_data.get("ppm", 0),
        "voltage": leaf_data.get("voltage", 0),
    }
    buffers.append(section_id, gas_reading)

    # Step 3: feature engineering
    gas_features = engineer_gas_features(buffers.get(section_id))

    # Step 4: encode CV stage
    cv_encoded = encode_cv_stage(leaf_data.get("cvStage"))

    # Step 5: chained prediction
    gas_prediction = predict_chained(gas_features, cv_encoded)

    # Logging
    if gas_prediction:
        logger.info(
            f"{section_id[:8]}... | "
            f"PPM={leaf_data.get('ppm', 0):.0f} | "
            f"CV={leaf_data.get('cvStage', 'none')} | "
            f"Gas Prediction={gas_prediction['gasStage']} ({gas_prediction['gasConfidence']:.0%}) | "
            f"Action={gas_prediction['action']}"
        )
    else:
        buffered = buffers.size(section_id)
        logger.info(
            f"{section_id[:8]}... | "
            f"PPM={leaf_data.get('ppm', 0):.0f} | "
            f"CV={leaf_data.get('cvStage', 'none')} | "
            f"buffering {buffered}/{WINDOW_SIZE}"
        )

    # Step 6: POST to backend
    payload = build_payload(section_id, leaf_data, gas_prediction)
    send_to_backend(payload)
    return True


def main():
    logger.info("=" * 60)
    logger.info("Fog Processor started")
    logger.info(f"Polling {len(WORKER_NODES)} leaf RPis every {POLL_INTERVAL_SECONDS}s")
    logger.info("=" * 60)

    buffers = SectionBuffers()

    while True:
        cycle_start = time.time()
        logger.info(f"--- Polling cycle at {datetime.now().isoformat()} ---")

        for section_id, url in WORKER_NODES.items():
            try:
                process_section(section_id, url, buffers)
            except Exception as e:
                logger.error(f"Error processing {section_id}: {e}")

        # Sleep until next cycle
        elapsed = time.time() - cycle_start
        sleep_time = max(0, POLL_INTERVAL_SECONDS - elapsed)
        logger.info(f"Cycle complete in {elapsed:.1f}s, sleeping {sleep_time:.1f}s\n")
        time.sleep(sleep_time)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nFog processor stopped by user")
