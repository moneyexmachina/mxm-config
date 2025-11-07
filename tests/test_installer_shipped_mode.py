from __future__ import annotations

from importlib import resources
from pathlib import Path

import pytest

from mxm.config import DefaultsMode, install_config

CORE_FILES = [
    "default.yaml",
    "environment.yaml",
    "machine.yaml",
    "profile.yaml",
    "local.yaml",
]

APP_ID = "mxm.config"
SHIPPED_PKG = "mxm.config"


@pytest.fixture()
def dest_root(tmp_path: Path) -> Path:
    # Keep tests isolated from real HOME; pass dest_root explicitly to installer
    return tmp_path / "home" / ".config" / "mxm"


def _app_dir(dest_root: Path) -> Path:
    return dest_root / APP_ID


def test_shipped_copies_core_files(dest_root: Path):
    report = install_config(
        app_id=APP_ID,
        mode=DefaultsMode.shipped,
        shipped_package=SHIPPED_PKG,
        dest_root=dest_root,
    )
    app_dir = _app_dir(dest_root)
    assert app_dir.exists()

    for name in CORE_FILES:
        assert (app_dir / name).exists(), f"missing shipped core file: {name}"

    # Sanity on report
    assert report.app_id == APP_ID
    assert report.mode is DefaultsMode.shipped
    assert report.dest_root == dest_root
    assert report.copied_count >= 1


def test_shipped_templates_copied_if_present(dest_root: Path):
    """Only asserts templates if the shipped seeds actually include them."""
    seeds_root = resources.files("mxm.config._data") / "seeds" / "mxm.config"
    templates_dir = seeds_root / "templates"

    # If the package has no templates dir (or no *.yaml), this becomes a no-op
    has_yaml_templates = False
    if templates_dir.is_dir():
        for entry in templates_dir.iterdir():
            if entry.name.endswith(".yaml"):
                has_yaml_templates = True
                break

    install_config(
        app_id=APP_ID,
        mode=DefaultsMode.shipped,
        shipped_package=SHIPPED_PKG,
        dest_root=dest_root,
        overwrite=True,
    )
    troot = _app_dir(dest_root) / "templates"

    if has_yaml_templates:
        assert (
            troot.is_dir()
        ), "templates directory should be created when shipped templates exist"
        assert any(
            p.suffix == ".yaml" for p in troot.iterdir()
        ), "no YAML templates copied"
    else:
        # Nothing to assert strictly; absence is acceptable
        assert True


def test_shipped_idempotent_skips_on_second_run(dest_root: Path):
    r1 = install_config(
        app_id=APP_ID,
        mode=DefaultsMode.shipped,
        shipped_package=SHIPPED_PKG,
        dest_root=dest_root,
        overwrite=False,
    )
    r2 = install_config(
        app_id=APP_ID,
        mode=DefaultsMode.shipped,
        shipped_package=SHIPPED_PKG,
        dest_root=dest_root,
        overwrite=False,
    )

    # Second run should mostly skip already-installed files
    assert r1.copied_count >= 1
    assert r2.skipped_count >= r1.copied_count


def test_shipped_overwrite_replaces_modified_file(dest_root: Path):
    app_dir = _app_dir(dest_root)

    # 1) First install
    install_config(
        app_id=APP_ID,
        mode=DefaultsMode.shipped,
        shipped_package=SHIPPED_PKG,
        dest_root=dest_root,
        overwrite=False,
    )

    # 2) Mutate one core file locally
    target = app_dir / "default.yaml"
    assert target.exists()
    target.write_text("# mutated\nx: 123\n", encoding="utf-8")

    # 3) Re-install with overwrite=True
    r2 = install_config(
        app_id=APP_ID,
        mode=DefaultsMode.shipped,
        shipped_package=SHIPPED_PKG,
        dest_root=dest_root,
        overwrite=True,
    )
    assert r2.copied_count >= 1

    # 4) Compare with shipped source content to ensure it was restored
    shipped_default = (
        resources.files("mxm.config._data") / "seeds" / "mxm.config" / "default.yaml"
    ).read_text(encoding="utf-8")
    current_default = target.read_text(encoding="utf-8")
    assert current_default == shipped_default


def test_shipped_destination_control_only_writes_under_dest_root(
    dest_root: Path, tmp_path: Path
):
    install_config(
        app_id=APP_ID,
        mode=DefaultsMode.shipped,
        shipped_package=SHIPPED_PKG,
        dest_root=dest_root,
        overwrite=True,
    )
    app_dir = _app_dir(dest_root)
    assert app_dir.exists()

    # Ensure no accidental writes under an unrelated default path
    unrelated = tmp_path / ".config" / "mxm" / APP_ID
    assert not unrelated.exists() or unrelated == app_dir


def test_shipped_report_integrity(dest_root: Path):
    report = install_config(
        app_id=APP_ID,
        mode=DefaultsMode.shipped,
        shipped_package=SHIPPED_PKG,
        dest_root=dest_root,
        overwrite=True,
    )
    app_dir = _app_dir(dest_root)

    # All dest paths should live under the app directory; actions in allowed set
    allowed = {"copied", "created", "skipped"}
    for item in report.installed:
        assert item.action in allowed
        assert str(item.dest).startswith(
            str(app_dir)
        ), f"dest escaped app dir: {item.dest}"


def test_shipped_missing_package_raises(dest_root: Path):
    with pytest.raises(ModuleNotFoundError):
        install_config(
            app_id=APP_ID,
            mode=DefaultsMode.shipped,
            shipped_package="mxm.config._data.NOT_A_REAL_PACKAGE",
            dest_root=dest_root,
        )
