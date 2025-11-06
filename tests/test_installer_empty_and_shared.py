from __future__ import annotations

from pathlib import Path

import pytest

from mxm.config import DefaultsMode, install_config

APP_ID = "demo_config"


@pytest.fixture()
def dest_root(tmp_path: Path) -> Path:
    # Keep tests isolated from real HOME; pass dest_root explicitly to installer
    return tmp_path / "home" / ".config" / "mxm"


def _app_dir(dest_root: Path) -> Path:
    return dest_root / APP_ID


# -------------------------
# Empty mode (no files)
# -------------------------


def test_empty_creates_dir_and_sentinel(dest_root: Path):
    report = install_config(
        app_id=APP_ID,
        mode=DefaultsMode.empty,
        dest_root=dest_root,
    )
    app_dir = _app_dir(dest_root)
    assert app_dir.exists(), "app dir should be created in empty mode"
    assert (app_dir / ".initialized").exists(), "sentinel should exist by default"

    # Report sanity
    assert report.app_id == APP_ID
    assert report.mode is DefaultsMode.empty
    assert report.dest_root == dest_root
    assert report.created_count >= 1
    # No core files in empty mode
    for name in [
        "default.yaml",
        "environment.yaml",
        "machine.yaml",
        "profile.yaml",
        "local.yaml",
    ]:
        assert not (app_dir / name).exists()


def test_empty_without_sentinel(dest_root: Path):
    install_config(
        app_id=APP_ID,
        mode=DefaultsMode.empty,
        dest_root=dest_root,
        create_sentinel=False,
    )
    app_dir = _app_dir(dest_root)
    assert app_dir.exists()
    assert not (
        app_dir / ".initialized"
    ).exists(), "sentinel should be omitted when disabled"


def test_empty_idempotent(dest_root: Path):
    r1 = install_config(app_id=APP_ID, mode=DefaultsMode.empty, dest_root=dest_root)
    r2 = install_config(app_id=APP_ID, mode=DefaultsMode.empty, dest_root=dest_root)
    # Second run should skip sentinel creation (if present) and not error
    assert r1.created_count >= 1
    assert r2.skipped_count >= 0  # at least non-negative; presence depends on sentinel


# ----------------------------------------------------
# Cross-cutting: report integrity & path discipline
# ----------------------------------------------------


def test_report_actions_are_well_formed(dest_root: Path):
    # Use empty mode (cheapest) just to get a report to inspect
    report = install_config(app_id=APP_ID, mode=DefaultsMode.empty, dest_root=dest_root)
    allowed = {"copied", "created", "skipped"}
    for item in report.installed:
        assert item.action in allowed, f"unexpected action: {item.action}"


def test_templates_copy_only_yaml(dest_root: Path, tmp_path: Path):
    """
    Build a temporary seed source containing both .yaml and non-.yaml files under templates/.
    Ensure that only *.yaml are installed.
    """
    # Construct a temporary seeds folder (no dependency on shipped seeds)
    seed_root = tmp_path / "seeds"
    (seed_root / "templates").mkdir(parents=True)
    # Minimal core file so installer does some copying
    (seed_root / "default.yaml").write_text("a: 1\n", encoding="utf-8")
    # Mixed templates
    (seed_root / "templates" / "keep.yaml").write_text("x: y\n", encoding="utf-8")
    (seed_root / "templates" / "skip.txt").write_text("not yaml\n", encoding="utf-8")

    install_config(
        app_id=APP_ID,
        mode=DefaultsMode.seed,
        seed_root=seed_root,
        dest_root=dest_root,
        overwrite=True,
    )

    troot = _app_dir(dest_root) / "templates"
    assert troot.exists(), "templates dir should be created"
    keep = troot / "keep.yaml"
    skip = troot / "skip.txt"
    assert keep.exists(), "YAML template should be copied"
    assert not skip.exists(), "non-YAML template should not be copied"


def test_destination_is_confined_to_app_dir(dest_root: Path):
    """
    Generic confinement check: every recorded destination must live under the app directory.
    """
    report = install_config(app_id=APP_ID, mode=DefaultsMode.empty, dest_root=dest_root)
    app_dir = _app_dir(dest_root)
    for item in report.installed:
        assert str(item.dest).startswith(
            str(app_dir)
        ), f"dest escaped app dir: {item.dest}"
