import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


def make_client():
    with patch("storage.get_db_connection"), \
         patch("service.run_db"), \
         patch("app.auth.verify_api_key", return_value=None):
        from server import app
        return TestClient(app)


def test_health():
    client = make_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_mask_sensitive():
    from server import mask
    result = mask("API_KEY", "supersecretvalue")
    assert result.endswith("...")
    assert "supersecretvalue" not in result


def test_mask_non_sensitive():
    from server import mask
    result = mask("USERNAME", "alice")
    assert result == "alice"
