"""
Public helpers for working with MXM configuration objects.

This module exposes utilities that produce or transform objects conforming to
the `MXMConfig` protocol without requiring callers to import OmegaConf.

`make_subconfig` is a tiny factory that turns a plain mapping into an object
behaving like your app config (supports both attribute and item access), backed
by OmegaConf `DictConfig` under the hood and typed as `MXMConfig`.

Typical use cases:
- Build a minimal, self-contained config for a subsystem (e.g., DataIO).
- Construct tiny configs in unit tests without loading layered YAML.
- Provide a focused “view” of a larger config tree at a package boundary.
"""

from __future__ import annotations

from typing import Any, Mapping

from .types import MXMConfig

__all__ = ["make_subconfig"]


def make_subconfig(
    data: Mapping[str, Any],
    *,
    readonly: bool = True,
    resolve: bool = False,
) -> MXMConfig:
    """
    Create an `MXMConfig` from a plain mapping.

    Parameters
    ----------
    data
        Plain nested mapping to convert into a config-shaped object.
    readonly
        If True (default), the returned config is set read-only.
    resolve
        If True, resolve `${...}` interpolations immediately.

    Returns
    -------
    MXMConfig
        An object supporting both dot and item access. Internally an
        OmegaConf `DictConfig`, but typed as the protocol to keep OmegaConf
        out of consumer APIs.

    Notes
    -----
    - OmegaConf is imported locally to avoid exposing it to consumers.
    - Use `resolve=True` if your subconfig contains `${...}` expressions
      that should be evaluated right away.
    """
    # Local import to keep OmegaConf out of public type signatures for consumers.
    from omegaconf import OmegaConf  # type: ignore

    cfg = OmegaConf.create(dict(data))
    if resolve:
        OmegaConf.resolve(cfg)
    if readonly:
        OmegaConf.set_readonly(cfg, True)
    # The returned object satisfies MXMConfig structurally (attr + item access).
    return cfg
