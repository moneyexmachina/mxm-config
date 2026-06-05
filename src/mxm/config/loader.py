"""RuntimeIdentity-driven configuration loading for MXM applications.

`mxm-config` resolves application configuration from an external configuration
store. The store contains configuration data; this module owns the resolution
semantics.

The public loader takes a `RuntimeIdentity`, selects the corresponding
configuration layers from the store, merges them in deterministic precedence
order, resolves OmegaConf interpolations, and returns a read-only configuration
object.

Resolution order, lowest to highest precedence:

1. `default.yaml`
2. `environment.yaml[identity.environment]`
3. `machine.yaml[identity.machine]`
4. `substrate.yaml[identity.substrate]`
5. `role.yaml[identity.role]`
6. explicit overrides

The default configuration store root is:

```text
~/mxm-config-store
```

`mxm-config` does not discover runtime identity and does not manage secrets.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from omegaconf import DictConfig, ListConfig, OmegaConf

from mxm.config.types import MXMConfig
from mxm.types import RuntimeIdentity

DEFAULT_CONFIG_STORE_ROOT = Path.home() / "mxm-config-store"
"""Default local path to the authoritative MXM configuration store."""

Layer = DictConfig | ListConfig
"""OmegaConf layer type accepted by `OmegaConf.merge`."""


def load_config(
    *,
    identity: RuntimeIdentity,
    store_root: Path = DEFAULT_CONFIG_STORE_ROOT,
    overrides: Mapping[str, Any] | None = None,
) -> MXMConfig:
    """Load and resolve configuration for a runtime identity.

    Parameters
    ----------
    identity
        Runtime identity selecting the application and identity-specific layers.
    store_root
        Root directory of the configuration store. Defaults to
        `~/mxm-config-store`.
    overrides
        Optional explicit override mapping applied after all store layers.

    Returns
    -------
    MXMConfig
        A read-only OmegaConf-backed configuration object typed against the
        lightweight `MXMConfig` protocol.

    Raises
    ------
    FileNotFoundError
        If the application configuration root or `default.yaml` is missing.
    KeyError
        If a dimension file exists but does not contain the selected identity
        value.
    """
    app_root = _app_config_root(identity=identity, store_root=store_root)

    layers: list[Layer] = []

    default_cfg = _load_required_yaml(app_root / "default.yaml")
    layers.append(default_cfg)

    environment_cfg = _load_selected_block(
        path=app_root / "environment.yaml",
        selector=str(identity.environment),
        dimension="environment",
    )
    if environment_cfg is not None:
        layers.append(environment_cfg)

    machine_cfg = _load_selected_block(
        path=app_root / "machine.yaml",
        selector=str(identity.machine),
        dimension="machine",
    )
    if machine_cfg is not None:
        layers.append(machine_cfg)

    substrate_cfg = _load_selected_block(
        path=app_root / "substrate.yaml",
        selector=str(identity.substrate),
        dimension="substrate",
    )
    if substrate_cfg is not None:
        layers.append(substrate_cfg)

    role_cfg = _load_selected_block(
        path=app_root / "role.yaml",
        selector=str(identity.role),
        dimension="role",
    )
    if role_cfg is not None:
        layers.append(role_cfg)

    if overrides is not None:
        overrides_cfg: DictConfig = OmegaConf.create(dict(overrides))
        layers.append(overrides_cfg)

    merged: DictConfig = OmegaConf.merge(
        *layers
    )  # pyright: ignore[reportAssignmentType]
    OmegaConf.resolve(merged)
    OmegaConf.set_readonly(merged, True)

    return cast(MXMConfig, merged)


def _app_config_root(*, identity: RuntimeIdentity, store_root: Path) -> Path:
    """Return and validate the app-specific configuration root.

    The config store is organized as:

    ```text
    <store_root>/apps/<identity.app>/
    ```

    Parameters
    ----------
    identity
        Runtime identity whose app field selects the app configuration root.
    store_root
        Root directory of the external configuration store.

    Returns
    -------
    Path
        App-specific configuration directory.

    Raises
    ------
    FileNotFoundError
        If the app-specific configuration directory does not exist.
    """
    app_root = store_root.expanduser() / "apps" / str(identity.app)
    if not app_root.is_dir():
        raise FileNotFoundError(
            "Application configuration root not found: "
            f"{app_root}. Expected <store_root>/apps/{identity.app}/."
        )

    return app_root


def _load_required_yaml(path: Path) -> DictConfig:
    """Load a required YAML file as an OmegaConf DictConfig.

    Parameters
    ----------
    path
        YAML file path.

    Returns
    -------
    DictConfig
        Loaded YAML configuration.

    Raises
    ------
    FileNotFoundError
        If `path` does not exist.
    TypeError
        If the YAML root is not a mapping.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Required configuration file not found: {path}")

    cfg = OmegaConf.load(path)
    if not isinstance(cfg, DictConfig):
        raise TypeError(f"Configuration file must contain a mapping: {path}")

    return cfg


def _load_optional_yaml(path: Path) -> DictConfig | None:
    """Load an optional YAML mapping file if present.

    Parameters
    ----------
    path
        YAML file path.

    Returns
    -------
    DictConfig | None
        Loaded mapping config, or `None` if the file does not exist.

    Raises
    ------
    TypeError
        If the YAML file exists but its root is not a mapping.
    """
    if not path.exists():
        return None

    cfg = OmegaConf.load(path)
    if not isinstance(cfg, DictConfig):
        raise TypeError(f"Configuration file must contain a mapping: {path}")

    return cfg


def _load_selected_block(
    *,
    path: Path,
    selector: str,
    dimension: str,
) -> DictConfig | None:
    """Load a selected block from a dimension configuration file.

    Dimension files are optional. If the file is absent, the layer is skipped.

    If a dimension file exists, it must contain a top-level key matching the
    selected identity value. The selected block must be a mapping.

    Example
    -------

    For:

    ```text
    identity.environment = "dev"
    ```

    `environment.yaml` is expected to contain:

    ```yaml
    dev:
      ...
    ```

    Parameters
    ----------
    path
        Dimension YAML file path.
    selector
        Selected RuntimeIdentity value for the dimension.
    dimension
        Human-readable dimension name used in error messages.

    Returns
    -------
    DictConfig | None
        Selected configuration block, or `None` if the file is absent.

    Raises
    ------
    KeyError
        If the file exists but does not contain the selector.
    TypeError
        If the file or selected block is not a mapping.
    """
    cfg = _load_optional_yaml(path)
    if cfg is None:
        return None

    if selector not in cfg:
        available = ", ".join(str(key) for key in cfg.keys())
        raise KeyError(
            f"Selector {selector!r} for dimension {dimension!r} not found in "
            f"{path}. Available selectors: {available}"
        )

    selected = cfg[selector]
    if not isinstance(selected, DictConfig):
        raise TypeError(
            f"Selected block for dimension {dimension!r} and selector "
            f"{selector!r} in {path} must be a mapping."
        )

    return selected
