"""
Backend Client
==============
Sends processed sensor + prediction data to the cloud backend.

The backend endpoint expects one POST per section with the format
defined in the team's REST API spec (POST /api/save).
"""

import logging
import requests

from config import BACKEND_URL, BACKEND_REQUEST_TIMEOUT

logger = logging.getLogger("fog")


def send_to_backend(payload):
    """
    POST a processed reading to the backend.

    Parameters:
        payload: dict matching the team's /api/save schema

    Returns:
        True on success (HTTP 2xx), False otherwise
    """
    try:
        response = requests.post(
            BACKEND_URL,
            json=payload,
            timeout=BACKEND_REQUEST_TIMEOUT,
            headers={"Content-Type": "application/json"},
        )
        if 200 <= response.status_code < 300:
            logger.debug(f"Backend OK: {response.status_code}")
            return True
        else:
            logger.warning(
                f"Backend returned {response.status_code}: {response.text[:200]}"
            )
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Backend unreachable: {e}")
        return False
