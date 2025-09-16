import os
import shutil
from pathlib import Path

import pytest

from mxm_config.installer import install_all


def test_install_all_copies_core_files(tmp_path):
    package = "mxm_config.examples.demo_config"

    installed = install_all(package, target_root=tmp_path)

    # All 5 core YAMLs may not exist in demo_config,
    # but default.yaml definitely should
    expected_core = {"default.yaml"}
    installed_names = {p.name for p in installed}
    assert expected_core.issubset(installed_names)

    # Verify files exist at target location
    for name in expected_core:
        assert (tmp_path / "demo_config" / name).exists()


def test_install_all_respects_overwrite(tmp_path):
    package = "mxm_config.examples.demo_config"

    # First install
    install_all(package, target_root=tmp_path)

    dst = tmp_path / "demo_config" / "default.yaml"
    original = dst.read_text()

    # Change the file locally
    dst.write_text("modified: true\n")

    # Run install again with overwrite=False (default)
    install_all(package, target_root=tmp_path, overwrite=False)
    assert dst.read_text() == "modified: true\n"

    # Run install with overwrite=True
    install_all(package, target_root=tmp_path, overwrite=True)
    assert dst.read_text() == original


def test_install_all_templates(tmp_path):
    """If demo_config ever ships templates/, they should be installed."""
    package = "mxm_config.examples.demo_config"

    # Manually create a fake templates dir in package resources
    # For test isolation, copy it into tmp_path
    # Simulating what a real package would ship
    pkg_path = Path(__file__).parents[1] / "mxm_config" / "examples" / "demo_config"
    templates_dir = pkg_path / "templates"
    templates_dir.mkdir(exist_ok=True)
    fake_yaml = templates_dir / "example.yaml"
    fake_yaml.write_text("fake: true\n")

    installed = install_all(package, target_root=tmp_path, overwrite=True)
    tmpl_root = tmp_path / "demo_config" / "templates"
    assert any(p.name == "example.yaml" for p in installed)
    assert (tmpl_root / "example.yaml").exists()

    # Cleanup (so we don’t pollute repo)
    shutil.rmtree(templates_dir)
