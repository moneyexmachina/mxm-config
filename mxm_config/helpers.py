"""Lightweight utilities for working with MXM configuration objects.

This module provides small, composable helpers for producing and slicing MXM
configuration objects while keeping consumer-facing APIs clean and type-hinted.

Exports
-------
- `make_subconfig(mapping, *, readonly=True, resolve=False) -> MXMConfig`
    Construct a fresh config object from a plain Python mapping.
- `make_view(cfg, path, *, readonly=True, resolve=False) -> MXMConfig`
    Return a focused, read-only view onto a subtree of an existing config.

Guidance
--------
Use `make_subconfig` when you need to *construct* a new config (e.g. in tests
or bootstrapping). Use `make_view` when you need a *slice* of an existing global
config to pass across a package boundary, preserving immutability and provenance.

Both helpers return objects that behave like your app config (dot *and* item
access), backed by OmegaConf `DictConfig` under the hood and typed as `MXMConfig`.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from omegaconf import DictConfig, OmegaConf

from .types import MXMConfig


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
    - Use `resolve=True` if your subconfig contains `${...}` expressions
      that should be evaluated right away.
    """
    cfg: DictConfig = OmegaConf.create(dict(data))
    if resolve:
        OmegaConf.resolve(cfg)
    if readonly:
        OmegaConf.set_readonly(cfg, True)
    # The returned object satisfies MXMConfig structurally (attr + item access).
    return cfg  # type: ignore[return-value]


def make_view(
    cfg: MXMConfig,
    path: str,
    *,
    readonly: bool = True,
    resolve: bool = False,
) -> MXMConfig:
    """Return a focused, read-only view onto a subtree of an existing config.

    This does not deep copy; it returns a `DictConfig` node referencing the same
    underlying subtree. Optionally resolves interpolations and marks the view
    read-only.

    Parameters
    ----------
    cfg
        The global MXM configuration (OmegaConf `DictConfig` typed as `MXMConfig`).
    path
        Dot-separated path into the config (e.g. `"mxm_dataio"` or
        `"mxm_datakraken.sources.justetf.http"`).
    readonly
        If True (default), mark the returned view as read-only.
    resolve
        If True, resolve interpolations before returning.

    Returns
    -------
    MXMConfig
        A `DictConfig` representing the selected subtree (typed as `MXMConfig`).

    Raises
    ------
    TypeError
        If `cfg` is not a `DictConfig`.
    KeyError
        If the `path` does not exist in `cfg`.

    Notes
    -----
    - Use `make_subconfig(mapping)` to construct a *new* config object.
    - Use `make_view(cfg, path)` to pass a *focused view* to a package boundary.
    """
    if not isinstance(cfg, DictConfig):
        raise TypeError("make_view expects an OmegaConf DictConfig (MXMConfig).")
    selected: Optional[object] = OmegaConf.select(cfg, path)
    if selected is None:
        raise KeyError(f"Config path not found: '{path}'")

    if not isinstance(selected, DictConfig):
        # Enforce sub-config (mapping) semantics, not lists or primitives.
        raise TypeError(
            "make_view expects the path to resolve to a mapping (DictConfig). "
            f"Path '{path}' resolved to {type(selected).__name__}. "
            "Select the parent mapping as a view and access the leaf inside it."
        )

    view: DictConfig = selected
    if resolve:
        OmegaConf.resolve(view)
    if readonly:
        OmegaConf.set_readonly(view, True)
    return view
