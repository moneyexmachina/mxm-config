from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from pathlib import Path
from typing import Any, cast

import pytest

from mxm.config.reports import InstalledFile, InstallReport
from mxm.config.types import DefaultsMode


def test_installedfile_to_dict_stringifies_paths(tmp_path: Path) -> None:
    src = tmp_path / "src.yaml"
    dest = tmp_path / "dest.yaml"
    src.write_text("x: 1\n", encoding="utf-8")

    rec = InstalledFile(src=src, dest=dest, action="copied")
    d: dict[str, Any] = rec.to_dict()

    assert d["src"] == str(src)
    assert d["dest"] == str(dest)
    assert d["action"] == "copied"


def test_installedfile_to_dict_with_none_src(tmp_path: Path) -> None:
    dest = tmp_path / "sentinel"
    rec = InstalledFile(src=None, dest=dest, action="created")
    d = rec.to_dict()
    assert d["src"] is None
    assert d["dest"] == str(dest)
    assert d["action"] == "created"


def test_installedfile_is_frozen(tmp_path: Path) -> None:
    rec = InstalledFile(src=None, dest=tmp_path / "a", action="created")
    with pytest.raises(FrozenInstanceError):
        # Suppress static "read-only" check so we can test the runtime error.
        cast(Any, rec).action = "skipped"  # pyright: ignore[reportAttributeAccessIssue]


def test_installreport_counters() -> None:
    a = InstalledFile(src=None, dest=Path("/x/a.yaml"), action="created")
    b = InstalledFile(src=Path("/s/b.yaml"), dest=Path("/x/b.yaml"), action="copied")
    c = InstalledFile(src=Path("/s/c.yaml"), dest=Path("/x/c.yaml"), action="skipped")

    r = InstallReport(
        app_id="mxm.config",
        mode=DefaultsMode.shipped,
        dest_root=Path("/home/user/.config/mxm"),
        installed=(a, b, c),
    )

    assert r.created_count == 1
    assert r.copied_count == 1
    assert r.skipped_count == 1


def test_installreport_to_dict_is_json_serializable(tmp_path: Path) -> None:
    rec = InstalledFile(src=None, dest=tmp_path / "f.yaml", action="created")
    r = InstallReport(
        app_id="iic.profile",
        mode=DefaultsMode.seed,
        dest_root=tmp_path,
        installed=(rec,),
    )

    d = r.to_dict()
    # basic shape
    assert d["app_id"] == "iic.profile"
    assert isinstance(d["mode"], str)
    m = d["mode"]
    assert isinstance(m, str)
    ml = m.lower()
    assert ml == "seed" or ml.endswith(".seed")
    assert d["dest_root"] == str(tmp_path)
    assert isinstance(d["installed"], list)
    assert (
        d["created_count"] == 1 and d["copied_count"] == 0 and d["skipped_count"] == 0
    )

    # must be JSON serializable
    json.dumps(d)


def test_installreport_pretty_and_str_match(tmp_path: Path) -> None:
    a = InstalledFile(src=None, dest=tmp_path / "default.yaml", action="created")
    b = InstalledFile(
        src=tmp_path / "templates" / "t.yaml",
        dest=tmp_path / "templates" / "t.yaml",
        action="copied",
    )

    r = InstallReport(
        app_id="mxm.config",
        mode=DefaultsMode.shipped,
        dest_root=tmp_path,
        installed=(a, b),
    )

    pretty = r.pretty()
    s = str(r)
    assert s == pretty  # __str__ proxies pretty()

    # contains key lines
    assert f"InstallReport(app_id={r.app_id}, mode={r.mode})" in pretty
    assert f"dest_root: {tmp_path}" in pretty
    assert "summary: created=1, copied=1, skipped=0" in pretty

    # file lines; includes leftwards arrow and src display
    assert "[created]" in pretty or "[created " in pretty  # padded width may vary
    assert "[copied]" in pretty or "[copied " in pretty
    assert "\u2190" in pretty  # LEFTWARDS ARROW


def test_installreport_pretty_empty_list(tmp_path: Path) -> None:
    r = InstallReport(
        app_id="mxm.empty",
        mode=DefaultsMode.empty,
        dest_root=tmp_path,
        installed=(),
    )
    pretty = r.pretty()
    assert "files: (none)" in pretty
