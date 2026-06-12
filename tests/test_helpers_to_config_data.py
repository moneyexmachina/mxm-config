"""Tests for converting MXMConfig objects into plain config data."""

from __future__ import annotations

from typing import cast

import pytest
from omegaconf import DictConfig

from mxm.config import MXMConfig, make_subconfig, to_config_data


def test_to_config_data_returns_plain_mapping() -> None:
    """to_config_data should return a plain Python mapping."""
    cfg = make_subconfig(
        {
            "foo": "bar",
            "answer": 42,
        }
    )

    data = to_config_data(cfg)

    assert isinstance(data, dict)
    assert not isinstance(data, DictConfig)
    assert data["foo"] == "bar"
    assert data["answer"] == 42


def test_to_config_data_preserves_nested_structures() -> None:
    """to_config_data should preserve nested JSON-shaped structures."""
    cfg = make_subconfig(
        {
            "outer": {
                "inner": {
                    "values": [1, 2, 3],
                    "enabled": True,
                },
            },
        }
    )

    data = to_config_data(cfg)

    assert data == {
        "outer": {
            "inner": {
                "values": [1, 2, 3],
                "enabled": True,
            },
        },
    }


def test_to_config_data_resolves_interpolations() -> None:
    """to_config_data should resolve OmegaConf interpolations."""
    cfg = make_subconfig(
        {
            "base": "/tmp/mxm",
            "data_root": "${base}/data",
        },
        resolve=False,
    )

    data = to_config_data(cfg)

    assert data["data_root"] == "/tmp/mxm/data"


def test_to_config_data_rejects_non_dictconfig() -> None:
    """to_config_data should reject non-OmegaConf-backed config objects."""
    cfg = cast(MXMConfig, object())

    with pytest.raises(TypeError, match="OmegaConf DictConfig"):
        to_config_data(cfg)
