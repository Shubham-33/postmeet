"""pytest configuration: set env vars before importing app, expose Flask test client."""
import os
import sys
from pathlib import Path

# Set env BEFORE importing app — app.py raises if NVIDIA_API_KEY is missing.
os.environ.setdefault("NVIDIA_API_KEY", "test-key-fixture")

# Make web/ importable as the project root so `import app` works
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

import app as app_module  # noqa: E402


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


@pytest.fixture
def app_mod():
    return app_module
