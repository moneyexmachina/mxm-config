"""
mxm_config.loader

Loads hierarchical YAML config files from ~/.config/mxm/<config_path>.

Config layering (in increasing order of precedence):
1. default.yaml
2. env/<env>.yaml         (e.g., "dev", "prod")
3. machine/<machine>.yaml (e.g., "bridge", "wildling")
4. profile/<profile>.yaml (e.g., "backtest", "live")
5. programmatic overrides (dict passed in)

All configs are merged using OmegaConf and optionally frozen.

Usage:
    from mxm_config.loader import load_config

    cfg = load_config(
        config_path="my_module",
        env="dev",
        machine="bridge",
        profile="backtest",
        overrides={"foo": "bar"},
        freeze=True,
    )
"""

import os
from pathlib import Path
from typing import Optional

from omegaconf import OmegaConf


def load_config(
    config_path: str,
    *,
    env: Optional[str] = None,
    machine: Optional[str] = None,
    profile: Optional[str] = None,
    overrides: Optional[dict] = None,
    freeze: bool = True,
) -> OmegaConf:
    """
    Load a hierarchical configuration from ~/.config/mxm/<config_path>.

    Args:
        config_path: Relative path from ~/.config/mxm/ (e.g., "my_module")
        env: Optional environment (e.g., "dev", "prod")
        machine: Optional machine id (e.g., "bridge", "wildling")
        profile: Optional profile name (e.g., "live", "backtest")
        overrides: Optional dictionary to override any config values
        freeze: Whether to make the resulting config read-only

    Returns:
        A composed OmegaConf config object.
    """
    base_dir = Path.home() / ".config" / "mxm" / config_path
    merged_cfgs = []

    def load_if_exists(path: Path) -> Optional[OmegaConf]:
        if path.exists():
            return OmegaConf.load(path)
        return None

    # 1. Load default.yaml (required)
    default_path = base_dir / "default.yaml"
    if not default_path.exists():
        raise FileNotFoundError(f"Missing required config file: {default_path}")
    merged_cfgs.append(OmegaConf.load(default_path))

    # 2. Optional env/<env>.yaml
    env = env or os.getenv("MXM_ENV")
    if env:
        cfg = load_if_exists(base_dir / "env" / f"{env}.yaml")
        if cfg:
            merged_cfgs.append(cfg)

    # 3. Optional machine/<machine>.yaml
    machine = machine or os.getenv("MXM_MACHINE")
    if machine:
        cfg = load_if_exists(base_dir / "machine" / f"{machine}.yaml")
        if cfg:
            merged_cfgs.append(cfg)

    # 4. Optional profile/<profile>.yaml
    profile = profile or os.getenv("MXM_PROFILE")
    if profile:
        cfg = load_if_exists(base_dir / "profile" / f"{profile}.yaml")
        if cfg:
            merged_cfgs.append(cfg)

    # 5. Optional programmatic overrides
    if overrides:
        merged_cfgs.append(OmegaConf.create(overrides))

    # Merge all layers in order
    config = OmegaConf.merge(*merged_cfgs)

    if freeze:
        OmegaConf.set_readonly(config, True)

    return config
