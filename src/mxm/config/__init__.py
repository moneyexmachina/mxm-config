"""
Public API for mxm-config.

This package provides a typed, OmegaConf-backed configuration layer for MXM
applications. On import it registers standard MXM resolvers so `${...}`
interpolations work consistently across packages.

Exports
-------
- MXMConfig      : Protocol describing the config object shape (dot & item access).
- install_config : Install package/app default config into the user config root with
                   selectable defaults mode (`seed | shipped | empty`), returning an
                   InstallReport for auditing.
- install_all    : (Deprecated) Legacy installer alias that delegates to
                   `install_config(mode='shipped')`.
- DefaultsMode   : Enum of available install modes (`seed`, `shipped`, `empty`).
- InstallReport  : Dataclass summarising what was created/copied/skipped.
- load_config    : Load layered configuration for a package/environment/profile.
- make_subconfig : Construct a new config object from a plain mapping.
- make_view      : Return a focused, read-only sub-tree view of an existing config.

Quick start
-----------
    from mxm.config import (
        MXMConfig, install_config, DefaultsMode, load_config, make_view
    )

    # (Optional) first-run setup: create an app-owned config directory
    # - empty mode: scaffold directory and a sentinel only
    install_config(app_id="mxm-datakraken", mode=DefaultsMode.empty)

    # Or install shipped defaults packaged with a module (resources under mxm.config._data.seeds)
    # install_config(
    #     app_id="mxm-datakraken",
    #     mode=DefaultsMode.shipped,
    #     shipped_package="mxm.config._data.seeds",
    # )

    # Load layered config for your app/package
    cfg: MXMConfig = load_config(package="mxm-datakraken", env="dev", profile="default")

    # Access values
    root = cfg.paths.sources.justetf.root                 # dot access
    root2 = cfg["paths"]["sources"]["justetf"]["root"]    # item access

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
- `install_config` supports three modes:
    * seed    — copy from a filesystem directory (e.g., a repo `seeds/` folder)
    * shipped — copy from packaged resources (e.g., `mxm.config._data.seeds`)
    * empty   — create the app directory (and a sentinel) without files
  It returns an `InstallReport` detailing every action for deterministic installs.
- `install_all(...)` is deprecated and will be removed in a future release; use
  `install_config(...)` instead.
- Use `make_subconfig(mapping)` to *construct* a fresh config (e.g., tests/bootstraps),
  and `make_view(cfg, "path.to.slice")` to *slice* a read-only sub-tree for downstream
  packages while preserving immutability and provenance.
"""

from __future__ import annotations

from mxm.config._version import __version__
from mxm.config.helpers import make_subconfig, make_view
from mxm.config.init_resolvers import register_mxm_resolvers
from mxm.config.installer import (
    DefaultsMode,
    InstallReport,
    install_config,
)
from mxm.config.installer import install_all  # deprecated alias, still exported for now
from mxm.config.loader import load_config
from mxm.config.types import MXMConfig

# Register standard MXM resolvers at import time so `${...}` interpolations work globally.
register_mxm_resolvers()

__all__ = [
    "DefaultsMode",
    "InstallReport",
    "MXMConfig",
    "__version__",
    "install_all",  # deprecated
    "install_config",
    "load_config",
    "make_subconfig",
    "make_view",
]
