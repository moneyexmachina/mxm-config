from __future__ import annotations

from typing import Any, Callable, Dict, cast

import pytest
from omegaconf import DictConfig, OmegaConf
from omegaconf.errors import ReadonlyConfigError

from mxm_config.helpers import make_subconfig


def test_constructs_config_from_mapping_attribute_and_item_access() -> None:
    cfg = cast(DictConfig, make_subconfig({"a": {"b": 1}}))
    assert isinstance(cfg, DictConfig)
    # Attribute access
    assert cfg.a.b == 1
    # Item access
    assert cfg["a"]["b"] == 1


# Define typed mutation functions to avoid unknown-typed lambdas
def _set_existing_key(c: DictConfig) -> None:
    c.a.b = 2  # type: ignore[attr-defined]


def _add_new_nested_key(c: DictConfig) -> None:
    c.a.c = 3  # type: ignore[attr-defined]


def _add_top_level_key(c: DictConfig) -> None:
    c["x"] = 1


@pytest.mark.parametrize(
    "mutation",
    cast(
        "list[Callable[[DictConfig], None]]",
        [_set_existing_key, _add_new_nested_key, _add_top_level_key],
    ),
)
def test_readonly_enforced_by_default(mutation: Callable[[DictConfig], None]) -> None:
    cfg = cast(DictConfig, make_subconfig({"a": {"b": 1}}))  # readonly=True by default
    with pytest.raises(ReadonlyConfigError):
        mutation(cfg)


def test_readonly_disabled_allows_mutation() -> None:
    cfg = cast(DictConfig, make_subconfig({"a": {"b": 1}}, readonly=False))
    cfg.a.b = 2  # type: ignore[attr-defined]
    cfg.a.c = 3  # type: ignore[attr-defined]
    cfg["x"] = 4
    assert cfg.a.b == 2  # type: ignore[attr-defined]
    assert cfg.a.c == 3  # type: ignore[attr-defined]
    assert cfg["x"] == 4


def test_interpolation_resolution_off_default_false() -> None:
    cfg = cast(DictConfig, make_subconfig({"a": 7, "b": {"x": "${a}"}}))
    # Access resolves lazily
    assert cfg.b.x == 7  # type: ignore[attr-defined]
    # Container without resolve retains the expression
    raw = cast(Dict[str, Any], OmegaConf.to_container(cfg, resolve=False))
    assert raw["b"]["x"] == "${a}"
    # With resolve=True it's concrete
    resolved = cast(Dict[str, Any], OmegaConf.to_container(cfg, resolve=True))
    assert resolved["b"]["x"] == 7


def test_interpolation_resolution_on_eager_resolve() -> None:
    cfg = cast(DictConfig, make_subconfig({"a": 7, "b": {"x": "${a}"}}, resolve=True))
    # Already resolved
    assert cfg.b.x == 7  # type: ignore[attr-defined]
    # Even with resolve=False in to_container, value is concrete
    raw = cast(Dict[str, Any], OmegaConf.to_container(cfg, resolve=False))
    assert raw["b"]["x"] == 7


def test_empty_mapping_returns_empty_readonly_config() -> None:
    cfg = cast(DictConfig, make_subconfig({}))
    assert isinstance(cfg, DictConfig)
    # Should be empty
    assert list(cfg.keys()) == []
    # Read-only enforced
    with pytest.raises(ReadonlyConfigError):
        cfg["x"] = 1


def test_protocol_shape_dot_and_item_access() -> None:
    cfg = cast(DictConfig, make_subconfig({"root": {"k": "v"}}))
    # Dot access
    assert cfg.root.k == "v"  # type: ignore[attr-defined]
    # Item access
    assert cfg["root"]["k"] == "v"
