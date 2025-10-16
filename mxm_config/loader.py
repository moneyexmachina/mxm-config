"""
Configuration loader for MXM apps (layered OmegaConf).

This module composes the final, read-only configuration object for a given
`package` by merging a standard set of YAML layers located under the MXM
config root (e.g., `~/.config/mxm/<package>`). Layering order is stable and
well-defined (low → high precedence):

  1) default.yaml               — always applied if present
  2) environment.yaml[env]      — the block matching the resolved environment
  3) machine.yaml[machine]      — the block matching the resolved machine/host
  4) profile.yaml[profile]      — the block matching the resolved profile
  5) local.yaml                 — optional, for developer overrides
  6) overrides (in-memory)      — explicit dict passed to `load_config(...)`

Resolution helpers in `mxm_config.resolver` normalize `env`, `profile`, and
`machine` (e.g., deriving defaults from environment variables or hostname).

The resulting OmegaConf DictConfig is:
  - fully resolved (interpolations evaluated),
  - merged according to the order above,
  - and set to read-only.

Downstream packages should generally import `load_config` via
`mxm_config.__init__` and type against the `MXMConfig` protocol instead of
depending on OmegaConf directly.
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable, Union, cast

from omegaconf import DictConfig, ListConfig, OmegaConf

from mxm_config.resolver import (
    get_config_root,
    resolve_environment,
    resolve_machine,
    resolve_profile,
)
from mxm_config.types import MXMConfig

Layer = Union[ListConfig, DictConfig]


def load_config(
    package: str,
    env: str,
    profile: str,
    machine: str | None = None,
    root: Path | None = None,
    overrides: Mapping[str, Any] | None = None,
) -> MXMConfig:
    """
    Load the MXM configuration by composing layered YAML files.

    The configuration directory is determined by combining the MXM config root
    (``~/.config/mxm`` by default, or overridden by ``MXM_CONFIG_HOME``) and
    the given ``package`` name (e.g. ``demo``). This directory is populated
    when configs are installed using :func:`install_all`.

    Layers are merged in the following order (lowest → highest precedence):

        1. ``default.yaml``          — always applied if present
        2. ``environment.yaml``      — only the block matching ``env`` is applied
        3. ``machine.yaml``          — only the block matching current hostname
        4. ``profile.yaml``          — only the block matching ``profile``
        5. ``local.yaml``            — applied if present
        6. explicit overrides dict   — passed via ``overrides`` argument

    Args:
        package: Name of the config subdirectory under the MXM config root.
        env: Environment selector (e.g. ``"dev"``, ``"prod"``).
        profile: Profile selector (e.g. ``"default"``, ``"research"``).
        machine: Optional explicit machine name override.
        root: Optional config root path override.
        overrides: Optional dictionary of overrides applied last.

    Returns:
        OmegaConf: A frozen OmegaConf config object with all layers
        merged and interpolated.
    """
    base_root = Path(root) if root is not None else get_config_root()
    cfg_root = base_root / Path(str(package))

    context_cfg = OmegaConf.create(
        {
            "mxm_env": resolve_environment(env),
            "mxm_profile": resolve_profile(profile),
            "mxm_machine": resolve_machine(machine),
        }
    )
    layers: list[Layer] = [context_cfg]

    default_cfg = _load_yaml_if_exists(cfg_root / "default.yaml")
    if default_cfg:
        layers.append(default_cfg)

    env_cfg = _load_block(env, cfg_root / "environment.yaml", resolve_environment)
    if env_cfg:
        layers.append(env_cfg)

    machine_cfg = _load_block(machine, cfg_root / "machine.yaml", resolve_machine)
    if machine_cfg:
        layers.append(machine_cfg)

    profile_cfg = _load_block(
        profile, cfg_root / "profile.yaml", resolve_profile, allow_default_skip=True
    )
    if profile_cfg:
        layers.append(profile_cfg)

    local_cfg = _load_yaml_if_exists(cfg_root / "local.yaml")
    if local_cfg:
        layers.append(local_cfg)

    if overrides is not None:
        overrides_cfg: DictConfig = OmegaConf.create(dict(overrides))
        layers.append(overrides_cfg)

    merged: DictConfig = OmegaConf.merge(*layers)  # type: ignore[assignment]
    OmegaConf.resolve(merged)
    OmegaConf.set_readonly(merged, True)
    return cast(MXMConfig, merged)


def _load_block(
    selector: str | None,
    path: Path,
    resolver: Callable[[str | None], str],
    allow_default_skip: bool = False,
) -> DictConfig | None:
    """
    Resolve and load a configuration block from a YAML file.

    Args:
        selector: Raw selector value (e.g. env, profile, machine).
        path: Path to the YAML file.
        resolver: Function to normalize the selector.
        allow_default_skip: If True, missing "default" selector will return None
            instead of raising KeyError (used for profiles).

    Returns:
        DictConfig block for the selector, or None if skipped.

    Raises:
        KeyError: If YAML exists but selector not defined.
    """
    resolved = resolver(selector)

    if not path.exists():
        return None

    cfg: DictConfig = OmegaConf.load(path)  # type: ignore[assignment]

    if resolved in cfg:
        return cfg[resolved]  # type: ignore[index]
    elif allow_default_skip and resolved == "default":
        return None
    else:
        raise KeyError(
            f"Selector '{resolved}' not found in {path}. Available: {list(cfg.keys())}"
        )


def _load_yaml_if_exists(path: Path):
    """Load a YAML file into an OmegaConf config if it exists, else return None."""
    return OmegaConf.load(path) if path.exists() else None
