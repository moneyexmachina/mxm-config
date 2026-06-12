"""Tests for RuntimeIdentity-driven configuration loading."""

from __future__ import annotations

from pathlib import Path

import pytest
from omegaconf import DictConfig, OmegaConf

from mxm.config.loader import load_config
from mxm.types import (
    RuntimeIdentity,
)


def _identity(
    *,
    app: str = "mxm-moneymachine",
    environment: str = "dev",
    machine: str = "bridge",
    substrate: str = "local-process",
    role: str = "marketdata",
) -> RuntimeIdentity:
    return RuntimeIdentity(
        app=app,
        environment=environment,
        machine=machine,
        substrate=substrate,
        role=role,
    )


def _app_root(store_root: Path, app: str = "mxm-moneymachine") -> Path:
    return store_root / "apps" / app


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_load_config_loads_default_yaml_only(tmp_path: Path) -> None:
    app_root = _app_root(tmp_path)
    _write(
        app_root / "default.yaml",
        """
project: mxm
parameters:
  refresh_interval: 5min
""",
    )

    cfg = load_config(identity=_identity(), store_root=tmp_path)

    assert cfg.project == "mxm"
    assert cfg.parameters.refresh_interval == "5min"


def test_load_config_applies_environment_layer(tmp_path: Path) -> None:
    app_root = _app_root(tmp_path)
    _write(app_root / "default.yaml", "value: default\n")
    _write(
        app_root / "environment.yaml",
        """
dev:
  value: environment
""",
    )

    cfg = load_config(identity=_identity(), store_root=tmp_path)

    assert cfg.value == "environment"


def test_load_config_applies_machine_layer(tmp_path: Path) -> None:
    app_root = _app_root(tmp_path)
    _write(app_root / "default.yaml", "value: default\n")
    _write(
        app_root / "machine.yaml",
        """
bridge:
  value: machine
""",
    )

    cfg = load_config(identity=_identity(), store_root=tmp_path)

    assert cfg.value == "machine"


def test_load_config_applies_substrate_layer(tmp_path: Path) -> None:
    app_root = _app_root(tmp_path)
    _write(app_root / "default.yaml", "value: default\n")
    _write(
        app_root / "substrate.yaml",
        """
local-process:
  value: substrate
""",
    )

    cfg = load_config(identity=_identity(), store_root=tmp_path)

    assert cfg.value == "substrate"


def test_load_config_applies_role_layer(tmp_path: Path) -> None:
    app_root = _app_root(tmp_path)
    _write(app_root / "default.yaml", "value: default\n")
    _write(
        app_root / "role.yaml",
        """
marketdata:
  value: role
""",
    )

    cfg = load_config(identity=_identity(), store_root=tmp_path)

    assert cfg.value == "role"


def test_load_config_layer_precedence(tmp_path: Path) -> None:
    app_root = _app_root(tmp_path)

    _write(app_root / "default.yaml", "value: default\n")
    _write(app_root / "environment.yaml", "dev:\n  value: environment\n")
    _write(app_root / "machine.yaml", "bridge:\n  value: machine\n")
    _write(app_root / "substrate.yaml", "local-process:\n  value: substrate\n")
    _write(app_root / "role.yaml", "marketdata:\n  value: role\n")

    cfg = load_config(identity=_identity(), store_root=tmp_path)

    assert cfg.value == "role"


def test_load_config_merges_nested_mappings(tmp_path: Path) -> None:
    app_root = _app_root(tmp_path)

    _write(
        app_root / "default.yaml",
        """
parameters:
  refresh_interval: 5min
  sample_count: 10
paths:
  output: /tmp/default
""",
    )
    _write(
        app_root / "environment.yaml",
        """
dev:
  parameters:
    refresh_interval: 1min
""",
    )
    _write(
        app_root / "machine.yaml",
        """
bridge:
  paths:
    output: /tmp/bridge
""",
    )

    cfg = load_config(identity=_identity(), store_root=tmp_path)

    assert cfg.parameters.refresh_interval == "1min"
    assert cfg.parameters.sample_count == 10
    assert cfg.paths.output == "/tmp/bridge"


def test_load_config_explicit_overrides_win(tmp_path: Path) -> None:
    app_root = _app_root(tmp_path)

    _write(app_root / "default.yaml", "value: default\n")
    _write(app_root / "role.yaml", "marketdata:\n  value: role\n")

    cfg = load_config(
        identity=_identity(),
        store_root=tmp_path,
        overrides={"value": "override"},
    )

    assert cfg.value == "override"


def test_load_config_missing_app_root_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="Application configuration root"):
        load_config(identity=_identity(), store_root=tmp_path)


def test_load_config_missing_default_yaml_raises(tmp_path: Path) -> None:
    _app_root(tmp_path).mkdir(parents=True)

    with pytest.raises(FileNotFoundError, match=r"default.yaml"):
        load_config(identity=_identity(), store_root=tmp_path)


def test_load_config_missing_selector_in_existing_dimension_file_raises(
    tmp_path: Path,
) -> None:
    app_root = _app_root(tmp_path)

    _write(app_root / "default.yaml", "value: default\n")
    _write(app_root / "environment.yaml", "prod:\n  value: prod\n")

    with pytest.raises(KeyError, match="dev"):
        load_config(identity=_identity(), store_root=tmp_path)


def test_load_config_absent_optional_dimension_files_are_skipped(
    tmp_path: Path,
) -> None:
    app_root = _app_root(tmp_path)

    _write(app_root / "default.yaml", "value: default\n")

    cfg = load_config(identity=_identity(), store_root=tmp_path)

    assert cfg.value == "default"


def test_load_config_returns_read_only_config(tmp_path: Path) -> None:
    app_root = _app_root(tmp_path)

    _write(app_root / "default.yaml", "value: default\n")

    cfg = load_config(identity=_identity(), store_root=tmp_path)
    assert isinstance(cfg, DictConfig)
    assert OmegaConf.is_readonly(cfg)
