# mxm_config/init_resolvers.py
"""Registration of standard MXM resolvers for OmegaConf interpolation.

Resolvers provided:
  - ${cwd:}                 -> current working directory
  - ${home:}                -> user's home directory
  - ${env:VAR[,default]}    -> environment variable lookup with optional default
  - ${timestamp:}           -> ISO timestamp (seconds precision)
"""

from __future__ import annotations

import datetime as _dt
import os as _os
from typing import Any, Callable, cast

from omegaconf import OmegaConf

# --- Typed resolver functions -------------------------------------------------


def _cwd_resolver() -> str:
    """Return the current working directory."""
    return _os.getcwd()


def _home_resolver() -> str:
    """Return the user's home directory."""
    return _os.path.expanduser("~")


def _env_resolver(key: str, default: str | None = None) -> str | None:
    """Resolve an environment variable.

    Args:
        key: Environment variable name.
        default: Value to return if the variable is unset.

    Returns:
        The env var value if set, otherwise `default`.
    """
    value = _os.getenv(key)
    return value if value is not None else default


def _timestamp_resolver() -> str:
    """Return the current timestamp (ISO 8601, seconds precision)."""
    return _dt.datetime.now().isoformat(timespec="seconds")


# --- Public API ---------------------------------------------------------------


def register_mxm_resolvers() -> None:
    """Register MXM resolvers if not already present.

    Notes:
        We cast the typed callables to `Callable[..., Any]` at registration
        time because OmegaConf's type hints are permissive and do not model
        per-resolver signatures precisely.
    """
    if not OmegaConf.has_resolver("cwd"):
        OmegaConf.register_new_resolver(
            "cwd",
            cast(Callable[..., Any], _cwd_resolver),
        )
    if not OmegaConf.has_resolver("home"):
        OmegaConf.register_new_resolver(
            "home",
            cast(Callable[..., Any], _home_resolver),
        )
    if not OmegaConf.has_resolver("env"):
        OmegaConf.register_new_resolver(
            "env",
            cast(Callable[..., Any], _env_resolver),
        )
    if not OmegaConf.has_resolver("timestamp"):
        OmegaConf.register_new_resolver(
            "timestamp",
            cast(Callable[..., Any], _timestamp_resolver),
        )
