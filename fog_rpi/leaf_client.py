"""
Leaf RPi Client
===============
Polls each leaf RPi's /sensors/fetch/latest endpoint to retrieve
the latest sensor snapshot.
"""

import logging
import requests

from config import LEAF_REQUEST_TIMEOUT

logger = logging.getLogger("fog")


def fetch_leaf_data(section_id, url):
    """
    Fetch the latest sensor snapshot from a leaf RPi.

    Parameters:
        section_id: identifier for logging
        url: full HTTP endpoint URL

    Returns:
        dict with sensor data on success, or None on failure
    """
    try:
        response = requests.get(url, timeout=LEAF_REQUEST_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            logger.debug(f"Fetched {section_id}: {len(data)} fields")
            return data
        else:
            logger.warning(f"{section_id}: HTTP {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"{section_id} unreachable ({url}): {e}")
        return None
    except ValueError as e:
        logger.error(f"{section_id} returned invalid JSON: {e}")
        return None


# _counter = [0]
# def fetch_leaf_data(section_id, url):
#     _counter[0] += 1
#     ppm = 200 + _counter[0] * 80
#     return {
#         "ppm": ppm, "voltage": 0.3 + (ppm/9000)*2,
#         "cvStage": "fresh" if ppm<500 else "ripe" if ppm<2000 else "overripe" if ppm<5000 else "spoiled",
#         "cvConfidence": 0.92, "temperature": 24.5, "humidity": 65.0, "imageBase64": "x"
#     }