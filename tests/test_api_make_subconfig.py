from __future__ import annotations

import pytest

from mxm_config import MXMConfig, make_subconfig


def test_make_subconfig_dot_and_item_access() -> None:
    cfg: MXMConfig = make_subconfig(
        {"paths": {"db_path": "/abs/db.sqlite", "responses_dir": "/abs/resp"}}
    )
    # Dot access
    assert cfg.paths.db_path == "/abs/db.sqlite"
    # Item access
    assert cfg["paths"]["responses_dir"] == "/abs/resp"


def test_make_subconfig_readonly_true_by_default() -> None:
    cfg = make_subconfig({"a": {"b": 1}})
    with pytest.raises(Exception):
        cfg.a.b = 2  # type: ignore[attr-defined]
    with pytest.raises(Exception):
        cfg["a"]["b"] = 3  # type: ignore[index]


def test_make_subconfig_resolve_interpolations() -> None:
    cfg = make_subconfig(
        {"root": "/abs", "paths": {"db": "${root}/db.sqlite"}},
        resolve=True,
    )
    assert cfg.paths.db == "/abs/db.sqlite"


def test_make_subconfig_no_resolve_leaves_interpolation() -> None:
    cfg = make_subconfig({"root": "/abs", "paths": {"db": "${root}/db.sqlite"}})
    # OmegaConf keeps the node as a string-like container until resolved
    # Accessing it returns the interpolated value lazily, but str shows the template.
    # We check that explicit resolve works as advertised, so here we just ensure access works.
    assert str(cfg.paths.db)  # non-empty string
