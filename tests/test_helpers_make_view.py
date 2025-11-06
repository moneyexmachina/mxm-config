from __future__ import annotations

from typing import Any, cast

from omegaconf import DictConfig, OmegaConf
from omegaconf.errors import ReadonlyConfigError
import pytest

from mxm.config.helpers import make_subconfig, make_view


def _mk_cfg() -> DictConfig:
    """Build a representative config tree for tests."""
    return OmegaConf.create(
        {
            "mxm_dataio": {
                "paths": {"db_path": "/var/mxm/dataio/db.sqlite"},
                "http": {"timeout_s": 10, "headers": {"User-Agent": "mxm/1"}},
                "lists": {"numbers": [1, 2, 3]},
            },
            "mxm_datakraken": {
                "sources": {
                    "justetf": {
                        "http": {
                            "base_url": "https://www.justetf.com",
                            "timeout_s": "${mxm_dataio.http.timeout_s}",
                        }
                    }
                }
            },
            "a": {"b": {"timeout_s": 7}},
        }
    )


def test_basic_nested_selection_and_readonly() -> None:
    cfg = _mk_cfg()
    view = cast(DictConfig, make_view(cfg, "mxm_dataio"))  # subtree → DictConfig
    assert isinstance(view, DictConfig)
    assert view.paths.db_path == "/var/mxm/dataio/db.sqlite"  # type: ignore[attr-defined]
    # default readonly=True
    with pytest.raises(ReadonlyConfigError):
        view.paths.db_path = "/tmp/other.sqlite"  # type: ignore[attr-defined]


def test_deep_nested_selection_with_resolve() -> None:
    cfg = _mk_cfg()
    http = cast(
        DictConfig,
        make_view(cfg, "mxm_datakraken.sources.justetf.http", resolve=True),
    )
    assert http.base_url == "https://www.justetf.com"  # type: ignore[attr-defined]
    assert http.timeout_s == 10  # type: ignore[attr-defined]


def test_readonly_false_allows_mutation_and_reflects_in_global() -> None:
    cfg = _mk_cfg()
    http = cast(
        DictConfig,
        make_view(cfg, "mxm_dataio.http", readonly=False, resolve=False),
    )
    # Mutate through the view
    http.timeout_s = 15  # type: ignore[attr-defined]
    http.headers["X-Test"] = "1"  # type: ignore[index]
    # Reflected in global cfg (proves this is a view, not a deep copy)
    assert cfg.mxm_dataio.http.timeout_s == 15  # type: ignore[attr-defined]
    assert cfg.mxm_dataio.http.headers["X-Test"] == "1"  # type: ignore[attr-defined]


def test_missing_path_raises_keyerror() -> None:
    cfg = _mk_cfg()
    with pytest.raises(KeyError):
        _ = make_view(cfg, "does.not.exist")


def test_non_dictconfig_input_raises_typeerror() -> None:
    # Passing a plain dict should raise, since make_view expects DictConfig
    plain: dict[str, Any] = {"a": {"b": 1}}
    with pytest.raises(TypeError):
        _ = make_view(cast(Any, plain), "a")


def test_identity_same_object_for_subtree() -> None:
    cfg = _mk_cfg()
    view = cast(DictConfig, make_view(cfg, "mxm_dataio"))
    # Selecting a DictConfig subtree should return the same underlying node
    assert view is cfg.mxm_dataio  # type: ignore[attr-defined]


def test_primitive_leaf_selection_errors() -> None:
    cfg = _mk_cfg()
    with pytest.raises(TypeError):
        _ = make_view(cfg, "a.b.timeout_s")


def test_list_selection_errors() -> None:
    cfg = _mk_cfg()
    with pytest.raises(TypeError):
        _ = make_view(cfg, "mxm_dataio.lists.numbers")


def test_resolve_flag_semantics() -> None:
    cfg = _mk_cfg()
    http_unresolved = cast(
        DictConfig,
        make_view(cfg, "mxm_datakraken.sources.justetf.http", resolve=False),
    )
    raw = cast(dict[str, Any], OmegaConf.to_container(http_unresolved, resolve=False))
    assert raw["timeout_s"] == "${mxm_dataio.http.timeout_s}"

    cfg2 = _mk_cfg()
    http_resolved = cast(
        DictConfig,
        make_view(cfg2, "mxm_datakraken.sources.justetf.http", resolve=True),
    )
    raw2 = cast(dict[str, Any], OmegaConf.to_container(http_resolved, resolve=False))
    assert raw2["timeout_s"] == 10


def test_isolation_via_copy_from_view() -> None:
    cfg = _mk_cfg()
    view = cast(DictConfig, make_view(cfg, "mxm_dataio.http", resolve=True))
    # Make a local, regular dict copy that we can mutate freely
    local = cast(dict[str, Any], OmegaConf.to_container(view, resolve=True))
    local["timeout_s"] = 999
    # Original global config remains unchanged
    assert cfg.mxm_dataio.http.timeout_s == 10  # type: ignore[attr-defined]


def test_public_import_surface_still_works_for_helpers() -> None:
    # Convenience: ensure make_view is importable from package root via re-export
    from mxm.config import make_view as make_view_public  # type: ignore

    cfg = _mk_cfg()
    v = cast(DictConfig, make_view_public(cfg, "mxm_dataio"))
    assert v.paths.db_path == "/var/mxm/dataio/db.sqlite"  # type: ignore[attr-defined]


def test_make_view_accepts_config_built_by_make_subconfig() -> None:
    # Interop: view on top of a config created by make_subconfig
    root = cast(
        DictConfig,
        make_subconfig(
            {
                "mxm_dataio": {
                    "paths": {"db_path": "/x.sqlite"},
                    "http": {"timeout_s": 5},
                }
            },
            resolve=True,
        ),
    )
    v = cast(DictConfig, make_view(root, "mxm_dataio"))
    assert v.http.timeout_s == 5  # type: ignore[attr-defined]
