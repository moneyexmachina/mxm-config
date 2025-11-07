from __future__ import annotations

from contextlib import contextmanager
from importlib.resources import as_file, files
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

APP_ID = "demo_config"


@contextmanager
def _shipped_seeds_path():
    """Yield a real filesystem Path to src/mxm/config/_data/seeds/mxm.config without duplicating files."""
    with as_file(files("mxm.config._data") / "seeds" / "mxm.config") as p:
        yield Path(p)


@pytest.fixture()
def dest_root(tmp_path: Path) -> Path:
    # Keep tests isolated from real HOME; pass dest_root explicitly to installer
    return tmp_path / "home" / ".config" / "mxm"


def _app_dir(dest_root: Path) -> Path:
    return dest_root / APP_ID


def test_seed_copies_core_files(dest_root: Path):
    with _shipped_seeds_path() as seed_root:
        report = install_config(
            app_id=APP_ID,
            mode=DefaultsMode.seed,
            seed_root=seed_root,
            dest_root=dest_root,
        )

    app_dir = _app_dir(dest_root)
    assert app_dir.exists()

    for name in CORE_FILES:
        assert (app_dir / name).exists(), f"missing seed core file: {name}"

    # Sanity on report
    assert report.app_id == APP_ID
    assert report.mode is DefaultsMode.seed
    assert report.dest_root == dest_root
    assert report.copied_count >= 1


def test_seed_templates_copied_if_present(dest_root: Path):
    with _shipped_seeds_path() as seed_root:
        templates_dir = seed_root / "templates"
        has_yaml_templates = templates_dir.is_dir() and any(
            p.suffix == ".yaml" for p in templates_dir.iterdir()
        )

        install_config(
            app_id=APP_ID,
            mode=DefaultsMode.seed,
            seed_root=seed_root,
            dest_root=dest_root,
            overwrite=True,
        )

    troot = _app_dir(dest_root) / "templates"
    if has_yaml_templates:
        assert (
            troot.is_dir()
        ), "templates directory should be created when seed templates exist"
        assert any(
            p.suffix == ".yaml" for p in troot.iterdir()
        ), "no YAML templates copied"
    else:
        assert True  # no-op if repo has no templates


def test_seed_idempotent_skips_on_second_run(dest_root: Path):
    with _shipped_seeds_path() as seed_root:
        r1 = install_config(
            app_id=APP_ID,
            mode=DefaultsMode.seed,
            seed_root=seed_root,
            dest_root=dest_root,
            overwrite=False,
        )
        r2 = install_config(
            app_id=APP_ID,
            mode=DefaultsMode.seed,
            seed_root=seed_root,
            dest_root=dest_root,
            overwrite=False,
        )

    assert r1.copied_count >= 1
    assert r2.skipped_count >= r1.copied_count


def test_seed_overwrite_replaces_modified_file(dest_root: Path):
    app_dir = _app_dir(dest_root)

    with _shipped_seeds_path() as seed_root:
        # 1) First install
        install_config(
            app_id=APP_ID,
            mode=DefaultsMode.seed,
            seed_root=seed_root,
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
            mode=DefaultsMode.seed,
            seed_root=seed_root,
            dest_root=dest_root,
            overwrite=True,
        )
        assert r2.copied_count >= 1

        # 4) Compare with seed source content to ensure it was restored
        shipped_default = (seed_root / "default.yaml").read_text(encoding="utf-8")
        current_default = target.read_text(encoding="utf-8")
        assert current_default == shipped_default


def test_seed_destination_control_only_writes_under_dest_root(
    dest_root: Path, tmp_path: Path
):
    with _shipped_seeds_path() as seed_root:
        install_config(
            app_id=APP_ID,
            mode=DefaultsMode.seed,
            seed_root=seed_root,
            dest_root=dest_root,
            overwrite=True,
        )

    app_dir = _app_dir(dest_root)
    assert app_dir.exists()

    # Ensure no accidental writes under an unrelated default path
    unrelated = tmp_path / ".config" / "mxm" / APP_ID
    assert not unrelated.exists() or unrelated == app_dir


def test_seed_report_integrity(dest_root: Path):
    with _shipped_seeds_path() as seed_root:
        report = install_config(
            app_id=APP_ID,
            mode=DefaultsMode.seed,
            seed_root=seed_root,
            dest_root=dest_root,
            overwrite=True,
        )

    app_dir = _app_dir(dest_root)
    allowed = {"copied", "created", "skipped"}
    for item in report.installed:
        assert item.action in allowed
        assert str(item.dest).startswith(
            str(app_dir)
        ), f"dest escaped app dir: {item.dest}"


def test_seed_missing_root_raises(dest_root: Path):
    # Explicitly passing None is handled by signature typing; simulate missing path by
    # providing a non-existent directory.
    bogus = dest_root.parent / "does-not-exist" / "seeds"
    with pytest.raises(ValueError):
        # Our installer requires seed_root to be a Path when mode=seed
        install_config(
            app_id=APP_ID,
            mode=DefaultsMode.seed,
            seed_root=None,  # type: ignore[arg-type]
            dest_root=dest_root,
        )

    with pytest.raises(FileNotFoundError):
        install_config(
            app_id=APP_ID,
            mode=DefaultsMode.seed,
            seed_root=bogus,
            dest_root=dest_root,
        )
