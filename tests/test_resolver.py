import os
import tempfile
from pathlib import Path

from mxm_config.resolver import get_config_root


def test_get_config_path_env(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setenv("MXM_CONFIG_HOME", temp_dir)
    assert get_config_root() == Path(temp_dir)
