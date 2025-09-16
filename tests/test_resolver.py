import os
import socket
import tempfile
from pathlib import Path

import pytest

from mxm_config.resolver import (
    get_config_root,
    resolve_environment,
    resolve_machine,
    resolve_profile,
)

# --- get_config_root ------------------------------------------------------


def test_get_config_root_default(tmp_path, monkeypatch):
    monkeypatch.delenv("MXM_CONFIG_HOME", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    expected = tmp_path / "home" / ".config" / "mxm"
    assert get_config_root() == expected


def test_get_config_root_env(monkeypatch, tmp_path):
    cfg_root = tmp_path / "custom_config"
    monkeypatch.setenv("MXM_CONFIG_HOME", str(cfg_root))
    assert get_config_root() == cfg_root


# --- resolve_environment --------------------------------------------------


def test_resolve_environment_requires_explicit():
    with pytest.raises(ValueError, match="Environment must be specified"):
        resolve_environment(None)


def test_resolve_environment_explicit_ok():
    assert resolve_environment("dev") == "dev"
    assert resolve_environment("prod") == "prod"


# --- resolve_profile ------------------------------------------------------


def test_resolve_profile_requires_explicit():
    with pytest.raises(ValueError, match="Profile must be specified"):
        resolve_profile(None)


def test_resolve_profile_explicit_ok():
    assert resolve_profile("research") == "research"
    assert resolve_profile("trading") == "trading"


# --- resolve_machine ------------------------------------------------------


def test_resolve_machine_explicit():
    assert resolve_machine("bridge") == "bridge"


def test_resolve_machine_env(monkeypatch):
    monkeypatch.setenv("MXM_MACHINE", "wildling")
    assert resolve_machine() == "wildling"


def test_resolve_machine_hostname(monkeypatch):
    monkeypatch.delenv("MXM_MACHINE", raising=False)
    fake_hostname = "monolith"
    monkeypatch.setattr(socket, "gethostname", lambda: fake_hostname)
    assert resolve_machine() == fake_hostname
