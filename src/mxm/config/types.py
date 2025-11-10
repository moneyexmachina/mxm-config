"""
Lightweight protocol(s) for application configuration objects.

`MXMConfig` is a runtime-agnostic interface that downstream packages can
type against without importing OmegaConf. It models the two access styles
we support post-load:

- Attribute access (dot-notation): `cfg.paths.sources.justetf.root`
- Item access (mapping-style):     `cfg["paths"]["sources"]["justetf"]["root"]`

Any object that implements these (e.g., OmegaConf DictConfig, SimpleNamespace
with __getitem__ shim, or a small wrapper) will satisfy this protocol.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class MXMConfig(Protocol):
    """Opaque app config supporting attribute and item access.

    Notes
    -----
    - This is intentionally minimal. Do not add OmegaConf-specific methods.
    - Keep it broad so tests can pass lightweight stand-ins.
    """

    # Attribute access: cfg.foo
    def __getattr__(self, key: str) -> Any: ...

    # Item access: cfg["foo"]
    def __getitem__(self, key: str) -> Any: ...


class DefaultsMode(str, Enum):
    seed = "seed"  # copy from a source directory (repo seeds)
    shipped = "shipped"  # copy from an installed package (importlib.resources)
    empty = "empty"  # create dirs/sentinels only
