import shutil
from pathlib import Path

import pytest

from mxm_config.installer import install_all


@pytest.fixture
def demo_pkg() -> str:
    return "mxm_config.examples.demo_config"


def test_install_all_with_path(tmp_path: Path, demo_pkg: str) -> None:
    installed = install_all(demo_pkg, target_root=tmp_path)
    assert (tmp_path / "demo_config" / "default.yaml").exists()
    assert any("default.yaml" in str(p) for p in installed)


def test_install_all_with_str(tmp_path: Path, demo_pkg: str) -> None:
    installed = install_all(demo_pkg, target_root=tmp_path)
    assert (tmp_path / "demo_config" / "default.yaml").exists()
    assert any("default.yaml" in str(p) for p in installed)


def test_install_all_with_target_name(tmp_path: Path, demo_pkg: str) -> None:
    installed = install_all(demo_pkg, target_root=tmp_path, target_name="demo")
    assert (tmp_path / "demo" / "default.yaml").exists()
    assert any("default.yaml" in str(p) for p in installed)


def test_install_all_with_target_root_and_name(tmp_path: Path, demo_pkg: str) -> None:
    custom_root = tmp_path / "custom_configs"
    installed = install_all(demo_pkg, target_root=custom_root, target_name="demo")
    assert (custom_root / "demo" / "default.yaml").exists()
    assert any("default.yaml" in str(p) for p in installed)


def test_install_all_copies_core_files(tmp_path: Path, demo_pkg: str) -> None:
    installed = install_all(demo_pkg, target_root=tmp_path)

    expected_core = {"default.yaml"}  # demo_config only ships default.yaml
    installed_names = {p.name for p in installed}
    assert expected_core.issubset(installed_names)

    for name in expected_core:
        assert (tmp_path / "demo_config" / name).exists()


def test_install_all_respects_overwrite(tmp_path: Path, demo_pkg: str) -> None:
    install_all(demo_pkg, target_root=tmp_path)

    dst = tmp_path / "demo_config" / "default.yaml"
    original = dst.read_text()

    dst.write_text("modified: true\n")

    install_all(demo_pkg, target_root=tmp_path, overwrite=False)
    assert dst.read_text() == "modified: true\n"

    install_all(demo_pkg, target_root=tmp_path, overwrite=True)
    assert dst.read_text() == original


def test_install_all_templates(tmp_path: Path, demo_pkg: str) -> None:
    pkg_path = Path(__file__).parents[1] / "mxm_config" / "examples" / "demo_config"
    templates_dir = pkg_path / "templates"
    templates_dir.mkdir(exist_ok=True)
    fake_yaml = templates_dir / "example.yaml"
    fake_yaml.write_text("fake: true\n")

    installed = install_all(demo_pkg, target_root=tmp_path, overwrite=True)
    tmpl_root = tmp_path / "demo_config" / "templates"
    assert any(p.name == "example.yaml" for p in installed)
    assert (tmpl_root / "example.yaml").exists()

    shutil.rmtree(templates_dir)
