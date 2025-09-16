from pathlib import Path

from mxm_config.resolver import get_config_root


def initiate_mxm_configs(
    config_root: Path | None = None,
    create_if_missing: bool = True,
) -> Path:
    """
    Resolve and optionally create the MXM config root directory.

    Args:
        config_root: Optional explicit path to use.
        create_if_missing: Whether to create the directory if it does not exist.

    Returns:
        The resolved config root Path.
    """
    resolved_root = config_root or get_config_root()

    if create_if_missing:
        resolved_root.mkdir(parents=True, exist_ok=True)

    return resolved_root
