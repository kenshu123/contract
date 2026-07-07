import logging
import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

_bearer = HTTPBearer()


def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> None:
    expected = os.environ.get("API_KEY")
    received = credentials.credentials

    logger.info("API_KEY set: %s", bool(expected))
    logger.info("received key (first 8): %s", received[:8] if received else "(empty)")
    logger.info("expected key (first 8): %s", expected[:8] if expected else "(not set)")
    logger.info("match: %s", expected == received)

    if not expected or received != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
