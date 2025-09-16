import os
from pathlib import Path

import pytest

from mxm_config.initializer import initiate_mxm_configs
from mxm_config.installer import install_default, install_templates
from mxm_config.resolver import get_config_root


@pytest.fixture(autouse=True)
def temp_config_root(monkeypatch, tmp_path):
    """
    Redirect MXM_CONFIG_HOME to a temp directory for all installer tests.
    """
    monkeypatch.setenv("MXM_CONFIG_HOME", str(tmp_path))
    # Ensure base dir exists
    initiate_mxm_configs()
    yield tmp_path


def test_install_default_first_time(temp_config_root):
    path = install_default("mxm_config.examples.demo_config")
    assert path.exists()
    assert path.read_text().startswith('project: "mxm-config demo"')


def test_install_default_skip_existing(temp_config_root):
    # First install
    path1 = install_default("mxm_config.examples.demo_config")
    # Modify file to simulate user edit
    path1.write_text("modified: true")
    # Second install without force
    path2 = install_default("mxm_config.examples.demo_config", force=False)
    # Should not overwrite
    assert "modified" in path2.read_text()


def test_install_default_force_overwrites(temp_config_root):
    path = install_default("mxm_config.examples.demo_config")
    path.write_text("modified: true")
    path2 = install_default("mxm_config.examples.demo_config", force=True)
    # Should have original demo contents again
    assert 'project: "mxm-config demo"' in path2.read_text()


def test_install_templates(temp_config_root):
    paths = install_templates("mxm_config.examples.demo_config", force=True)
    # If demo_config has no templates yet, this will be empty
    assert isinstance(paths, list)
    for p in paths:
        assert p.exists()
        assert p.suffix == ".yaml"
        assert str(p).startswith(str(get_config_root()))
