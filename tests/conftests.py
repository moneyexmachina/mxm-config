# tests/conftest.py
import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_config_dir(monkeypatch):
    tmpdir = Path(tempfile.mkdtemp())
    monkeypatch.setenv("MXM_CONFIG_HOME", str(tmpdir))  # Use env var override
    yield tmpdir
    shutil.rmtree(tmpdir)
