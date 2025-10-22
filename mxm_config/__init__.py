"""
Public API for mxm-config.

This package provides a typed, OmegaConf-backed configuration layer for MXM
applications. On import it registers standard MXM resolvers so `${...}`
interpolations work consistently across packages.

Exports
-------
- MXMConfig     : Protocol describing the config object shape (dot & item access).
- install_all   : Install package-level default config files into the user config root.
- load_config   : Load layered configuration for a package/environment/profile.
- make_subconfig: Construct a new config object from a plain mapping.
- make_view     : Return a focused, read-only sub-tree view of an existing config.

Quick start
-----------
    from mxm_config import MXMConfig, install_all, load_config, make_view

    # (Optional) install package defaults for first-run setups
    install_all()

    # Load layered config for your app/package
    cfg: MXMConfig = load_config(package="mxm-datakraken", env="dev", profile="default")

    # Access values
    root = cfg.paths.sources.justetf.root           # dot access
    root2 = cfg["paths"]["sources"]["justetf"]["root"]  # item access

    # Pass a focused, read-only view across a package boundary
    http_cfg = make_view(cfg, "mxm_datakraken.sources.justetf.http", resolve=True)
    timeout = http_cfg.timeout_s

Notes
-----
- `load_config` and the helpers return OmegaConf `DictConfig` objects that satisfy
  the `MXMConfig` protocol. Consumers should type against `MXMConfig` rather than
  importing OmegaConf directly.
- Resolver registration occurs at import time (`register_mxm_resolvers()`), enabling
  `${env:VAR}`, `${cwd:}`, and other MXM resolvers globally. Importing this module
  early in your program is recommended.
- Use `make_subconfig(mapping)` to *construct* a fresh config (e.g., tests/bootstraps),
  and `make_view(cfg, "path.to.slice")` to *slice* a read-only sub-tree for downstream
  packages while preserving immutability and provenance.
"""

from __future__ import annotations

from mxm_config.helpers import make_subconfig, make_view
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
    "make_view",
]
