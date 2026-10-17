"""Never run integration tests against the developer's database or AI account."""
import os
import tempfile
from pathlib import Path

_test_directory = tempfile.TemporaryDirectory(prefix="facilityops-tests-", ignore_cleanup_errors=True)
os.environ["DATABASE_URL"] = "sqlite:///" + (Path(_test_directory.name) / "test.db").as_posix()
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "facilityops123"
os.environ["JWT_SECRET_KEY"] = "test-only-key-not-for-deployment-1234567890"
os.environ["AI_PROVIDER"] = "mock"
os.environ.setdefault("ENABLE_TENSORFLOW", "false")


def pytest_sessionstart(session):
    # Existing modules enter their own TestClients during collection. Finish
    # initial seeding once first so those clients cannot race each other.
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app):
        pass


def pytest_collection_modifyitems(items):
    import pytest
    deep_learning_tests = {
        "test_asset_health_uses_lstm_and_returns_valid_prediction",
        "test_cnn_live_inference_on_zone_with_environmental_data",
    }
    if os.environ["ENABLE_TENSORFLOW"].lower() not in {"1", "true", "yes"}:
        for item in items:
            if item.name in deep_learning_tests:
                item.add_marker(pytest.mark.skip(reason="Optional deep-learning suite: run with ENABLE_TENSORFLOW=true and TensorFlow installed"))


def pytest_sessionfinish(session, exitstatus):
    from app.core.database import engine
    engine.dispose()
