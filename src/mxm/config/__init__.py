"""Public API for mxm-config.

`mxm-config` provides RuntimeIdentity-driven configuration resolution for
Money Ex Machina applications.

The package resolves plain YAML configuration from an external configuration
store, merges selected layers in deterministic precedence order, and returns an
OmegaConf-backed configuration object typed against the `MXMConfig` protocol.

Responsibilities
----------------
`mxm-config` owns:

- configuration-store layout semantics
- RuntimeIdentity-based layer selection
- deterministic OmegaConf merging
- lightweight config object helpers

`mxm-config` does not own:

- runtime identity discovery
- runtime context construction
- secret resolution
- configuration installation
- configuration storage authority

Exports
-------
- `MXMConfig`      : Protocol describing the resolved config object shape.
- `load_config`    : Resolve configuration for a `RuntimeIdentity`.
- `make_subconfig` : Construct a config object from a plain mapping.
- `make_view`      : Return a focused read-only subtree of a resolved config.
- `__version__`    : Package version.

Quick start
-----------
    from pathlib import Path

    from mxm.config import MXMConfig, load_config, make_view
    from mxm.types import RuntimeIdentity

    identity = RuntimeIdentity(
        app="mxm-moneymachine",
        environment="dev",
        machine="bridge",
        substrate="local-process",
        role="marketdata",
    )

    cfg: MXMConfig = load_config(
        identity=identity,
        store_root=Path("~/mxm-config-store").expanduser(),
    )

    root = cfg.paths.marketdata.root
    db_cfg = make_view(cfg, "services.database", resolve=True)

Notes
-----
- `load_config` returns an OmegaConf `DictConfig` object typed as `MXMConfig`.
  Consumers should type against `MXMConfig` rather than importing OmegaConf
  directly.
- Configuration selection is driven by `RuntimeIdentity`; discovery of that
  identity belongs to `mxm-runtime`.
- Configuration data lives in an external `mxm-config-store` repository.
- Explicit overrides may be passed to `load_config`; persistent local override
  files are intentionally not part of the configuration-store model.
"""

from __future__ import annotations

from mxm.config._version import __version__
from mxm.config.helpers import make_subconfig, make_view
from mxm.config.loader import load_config
from mxm.config.types import MXMConfig

__all__ = [
    "MXMConfig",
    "__version__",
    "load_config",
    "make_subconfig",
    "make_view",
]
