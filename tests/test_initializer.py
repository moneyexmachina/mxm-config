import os
from pathlib import Path

import pytest

from mxm_config.initializer import initiate_mxm_configs
from mxm_config.resolver import get_config_root


def test_initiate_with_argument_creates(tmp_path):
    target = tmp_path / "explicit"
    assert not target.exists()
    result = initiate_mxm_configs(config_root=target, create_if_missing=True)
    assert result == target
    assert target.exists()


def test_initiate_with_envvar(monkeypatch, tmp_path):
    env_target = tmp_path / "envroot"
    monkeypatch.setenv("MXM_CONFIG_HOME", str(env_target))
    # Ensure other fallbacks don’t interfere
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
    monkeypatch.delenv("HOME", raising=False)

    result = initiate_mxm_configs()
    assert result == env_target
    assert env_target.exists()


def test_initiate_with_default_home(monkeypatch, tmp_path):
    # Clear explicit overrides so we hit the default branch
    monkeypatch.delenv("MXM_CONFIG_HOME", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    fake_home = tmp_path / "home"
    fake_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(fake_home))

    expected = fake_home / ".config" / "mxm"
    result = initiate_mxm_configs()
    assert result == expected
    assert expected.exists()


def test_initiate_without_creation(tmp_path, monkeypatch):
    # Ensure no overrides in play
    monkeypatch.delenv("MXM_CONFIG_HOME", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    target = tmp_path / "no_create"
    result = initiate_mxm_configs(config_root=target, create_if_missing=False)
    assert result == target
    assert not target.exists()
