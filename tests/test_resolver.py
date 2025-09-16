import os
import tempfile
from pathlib import Path

from mxm_config.resolver import get_config_root, resolve_environment


def test_get_config_path_env(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    monkeypatch.setenv("MXM_CONFIG_HOME", temp_dir)
    assert get_config_root() == Path(temp_dir)


def test_env_resolver_prefers_arg(monkeypatch):
    monkeypatch.setenv("MXM_ENV", "prod")
    value, source = resolve_environment(env="staging")
    assert value == "staging"
    assert source == "arg"


def test_env_resolver_uses_env_when_no_arg(monkeypatch):
    monkeypatch.setenv("MXM_ENV", "prod")
    value, source = resolve_environment()
    assert value == "prod"
    assert source == "env"


def test_env_resolver_falls_back_to_default(monkeypatch):
    monkeypatch.delenv("MXM_ENV", raising=False)
    value, source = resolve_environment()
    assert value == "dev"
    assert source == "default"


def test_env_resolver_respects_custom_default(monkeypatch):
    monkeypatch.delenv("MXM_ENV", raising=False)
    value, source = resolve_environment(default="staging")
    assert value == "staging"
    assert source == "default"
