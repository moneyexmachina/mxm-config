import importlib
import socket
from pathlib import Path

import pytest

from mxm_config import resolver as resolver

# --- get_config_root ------------------------------------------------------


def test_get_config_root_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("MXM_CONFIG_HOME", raising=False)
    monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)

    # Belt-and-braces: set HOME and also override Path.home() for environments that
    # ignore HOME or cache it at import time.
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
    # Ensure any module-level cached paths are recomputed under patched env.
    importlib.reload(resolver)

    expected = tmp_path / "home" / ".config" / "mxm"
    assert resolver.get_config_root() == expected


def test_get_config_root_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    cfg_root = tmp_path / "custom_config"
    monkeypatch.setenv("MXM_CONFIG_HOME", str(cfg_root))

    assert resolver.get_config_root() == cfg_root


# --- resolve_environment --------------------------------------------------


def test_resolve_environment_requires_explicit() -> None:
    with pytest.raises(ValueError, match="Environment must be specified"):
        resolver.resolve_environment(None)


def test_resolve_environment_explicit_ok() -> None:
    assert resolver.resolve_environment("dev") == "dev"
    assert resolver.resolve_environment("prod") == "prod"


# --- resolve_profile ------------------------------------------------------


def test_resolve_profile_requires_explicit() -> None:
    with pytest.raises(ValueError, match="Profile must be specified"):
        resolver.resolve_profile(None)


def test_resolve_profile_explicit_ok() -> None:
    assert resolver.resolve_profile("research") == "research"
    assert resolver.resolve_profile("trading") == "trading"


# --- resolve_machine ------------------------------------------------------


def test_resolve_machine_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MXM_MACHINE", "wildling")
    assert resolver.resolve_machine() == "wildling"


def test_resolve_machine_hostname(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MXM_MACHINE", raising=False)
    fake_hostname = "monolith"
    monkeypatch.setattr(socket, "gethostname", lambda: fake_hostname)
    assert resolver.resolve_machine() == fake_hostname


def test_resolve_machine_explicit() -> None:
    assert resolver.resolve_machine("bridge") == "bridge"
