from pathlib import Path

import pytest

from mxm_config.installer import install_all
from mxm_config.loader import load_config
from mxm_config.types import MXMConfig


@pytest.fixture
def setup_demo(tmp_path: Path) -> Path:
    """Install demo config into a temporary root and return its path."""
    install_all(
        "mxm_config.examples.demo_config",
        target_root=tmp_path,
        target_name="demo",
    )
    return tmp_path


def test_load_defaults_only(setup_demo: Path) -> None:
    cfg: MXMConfig = load_config("demo", env="dev", profile="default", root=setup_demo)

    # From defaults.yaml
    assert cfg.project == "mxm-config demo"

    # environment.yaml[dev] overrides -> 1min
    assert cfg.parameters.refresh_interval == "1min"

    # local.yaml overrides -> 42
    assert cfg.parameters.sample_count == 42

    # Always present
    assert cfg.get("paths") is not None


def test_environment_layer(setup_demo: Path) -> None:
    cfg: MXMConfig = load_config("demo", env="prod", profile="default", root=setup_demo)

    # prod env overrides default.yaml
    assert cfg.parameters.refresh_interval == "10min"

    # local.yaml still wins for sample_count
    assert cfg.parameters.sample_count == 42


def test_machine_layer(setup_demo: Path) -> None:
    cfg: MXMConfig = load_config(
        "demo", env="dev", profile="default", root=setup_demo, machine="wildling"
    )

    # Machine layer affects paths.base_output (value depends on demo_config/machine.yaml)
    assert cfg.paths.base_output.endswith("wildling/demo_output")


def test_profile_layer(setup_demo: Path) -> None:
    cfg: MXMConfig = load_config("demo", env="dev", profile="research", root=setup_demo)

    # profile.yaml["research"] overrides refresh_interval
    assert cfg.parameters.refresh_interval == "30min"

    # environment.yaml[dev] + local.yaml → sample_count overridden to 42
    assert cfg.parameters.sample_count == 42


def test_overrides_file_and_dict(setup_demo: Path) -> None:
    cfg: MXMConfig = load_config(
        "demo",
        env="dev",
        profile="default",
        root=setup_demo,
        overrides={"parameters": {"sample_count": 777}},
    )

    # Explicit overrides always win
    assert cfg.parameters.sample_count == 777
