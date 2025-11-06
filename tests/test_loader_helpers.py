from pathlib import Path
from typing import Any

from omegaconf import DictConfig, OmegaConf
import pytest

from mxm.config.loader import _load_block  # pyright: ignore[reportPrivateUsage]
from mxm.config.resolver import resolve_environment, resolve_machine, resolve_profile


def write_yaml(path: Path, content: dict[str, Any]) -> None:
    """Helper to write a dict into a YAML file via OmegaConf."""
    cfg: DictConfig = OmegaConf.create(content)
    path.write_text(OmegaConf.to_yaml(cfg))


# ------------------------
# Profile
# ------------------------
def test_load_profile_missing(tmp_path: Path) -> None:
    cfg = _load_block(
        "default", tmp_path / "profile.yaml", resolve_profile, allow_default_skip=True
    )
    assert cfg is None


def test_load_profile_existing(tmp_path: Path) -> None:
    profile_file = tmp_path / "profile.yaml"
    write_yaml(profile_file, {"research": {"param": 1}})
    cfg = _load_block(
        "research", profile_file, resolve_profile, allow_default_skip=True
    )
    assert cfg is not None
    assert cfg.param == 1


def test_load_profile_default_fallback(tmp_path: Path) -> None:
    profile_file = tmp_path / "profile.yaml"
    write_yaml(profile_file, {"research": {"param": 1}})
    cfg = _load_block("default", profile_file, resolve_profile, allow_default_skip=True)
    assert cfg is None  # graceful fallback


def test_load_profile_unknown_raises(tmp_path: Path) -> None:
    profile_file = tmp_path / "profile.yaml"
    write_yaml(profile_file, {"research": {"param": 1}})
    with pytest.raises(KeyError):
        _load_block("trading", profile_file, resolve_profile, allow_default_skip=True)


# ------------------------
# Environment
# ------------------------
def test_load_environment_missing(tmp_path: Path) -> None:
    cfg = _load_block("dev", tmp_path / "environment.yaml", resolve_environment)
    assert cfg is None


def test_load_environment_existing(tmp_path: Path) -> None:
    env_file = tmp_path / "environment.yaml"
    write_yaml(env_file, {"dev": {"param": 42}})
    cfg = _load_block("dev", env_file, resolve_environment)
    assert cfg is not None
    assert cfg.param == 42


def test_load_environment_unknown_raises(tmp_path: Path) -> None:
    env_file = tmp_path / "environment.yaml"
    write_yaml(env_file, {"dev": {"param": 42}})
    with pytest.raises(KeyError):
        _load_block("prod", env_file, resolve_environment)


# ------------------------
# Machine
# ------------------------
def test_load_machine_missing_file(tmp_path: Path) -> None:
    cfg = _load_block("bridge", tmp_path / "machine.yaml", resolve_machine)
    assert cfg is None


def test_load_machine_existing(tmp_path: Path) -> None:
    machine_file = tmp_path / "machine.yaml"
    write_yaml(machine_file, {"bridge": {"param": "ok"}})
    cfg = _load_block("bridge", machine_file, resolve_machine)
    assert cfg is not None
    assert cfg.param == "ok"


def test_load_machine_unknown_raises(tmp_path: Path) -> None:
    machine_file = tmp_path / "machine.yaml"
    write_yaml(machine_file, {"bridge": {"param": "ok"}})
    with pytest.raises(KeyError):
        _load_block("wildling", machine_file, resolve_machine)
