"""
Public API for mxm-config.

This package loads layered configuration for MXM apps and installs standard
OmegaConf resolvers (e.g., `${cwd:}`, `${env:VAR}`) on import.

Typical usage
-------------
    from mxm_config import MXMConfig, load_config, install_all

    # (Optional) Install package config files into ~/.config/mxm/<package>/
    install_all()

    # Load layered config for your app/package
    cfg: MXMConfig = load_config(
        package="mxm-datakraken",
        env="dev",
        profile="default",
    )

    # Use ergonomic dot-notation
    root = cfg.paths.sources.justetf.root
    # Or mapping-style access
    root2 = cfg["paths"]["sources"]["justetf"]["root"]

Notes
-----
- Downstream packages should import from `mxm_config` (this module) and type
  against the `MXMConfig` protocol rather than importing OmegaConf directly.
- `load_config` returns an object that satisfies `MXMConfig` (backed by
  OmegaConf DictConfig internally).
"""

from __future__ import annotations

from mxm_config.api import make_subconfig
from mxm_config.init_resolvers import register_mxm_resolvers
from mxm_config.installer import install_all
from mxm_config.loader import load_config
from mxm_config.types import MXMConfig

# Register standard MXM resolvers at import time so `${...}` interpolations work globally.
register_mxm_resolvers()

__all__ = [
    "MXMConfig",
    "install_all",
    "load_config",
    "make_subconfig",
]
