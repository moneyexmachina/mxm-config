from __future__ import annotations

from pathlib import Path
import warnings

import pytest

from mxm.config import install_all

SHIPPED_PKG: str = "mxm.config"
APP_ID: str = "mxm.config"


def _dest_root(tmp_path: Path) -> Path:
    return tmp_path / "home" / ".config" / "mxm"


@pytest.mark.filterwarnings("always:.*install_all is deprecated.*:DeprecationWarning")
def test_install_all_emits_deprecation_and_writes_files(tmp_path: Path) -> None:
    dest: Path = _dest_root(tmp_path)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", DeprecationWarning)
        written: list[Path] = install_all(
            package=SHIPPED_PKG,
            target_root=dest,
            target_name=APP_ID,
            overwrite=True,
        )
        assert any(
            isinstance(m.message, DeprecationWarning) for m in w
        ), "no DeprecationWarning emitted"

    assert len(written) > 0, "expected some files to be written"
    assert all(p.exists() for p in written), "returned paths should exist"


def test_install_all_returns_only_new_writes_and_respects_overwrite(
    tmp_path: Path,
) -> None:
    dest: Path = _dest_root(tmp_path)

    first: list[Path] = install_all(
        package=SHIPPED_PKG,
        target_root=dest,
        target_name=APP_ID,
        overwrite=False,
    )
    assert len(first) > 0, "first run should write files"

    second: list[Path] = install_all(
        package=SHIPPED_PKG,
        target_root=dest,
        target_name=APP_ID,
        overwrite=False,
    )
    assert (
        second == []
    ), "second run without overwrite should return no newly written files"

    third: list[Path] = install_all(
        package=SHIPPED_PKG,
        target_root=dest,
        target_name=APP_ID,
        overwrite=True,
    )
    assert len(third) > 0, "overwrite run should rewrite files and return paths"
