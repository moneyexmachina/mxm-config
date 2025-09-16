import os
from pathlib import Path


def get_config_root() -> Path:
    """
    Resolve the MXM config root.

    Precedence:
      1) MXM_CONFIG_HOME  -> <dir>
      2) XDG_CONFIG_HOME  -> <dir>/mxm
      3) HOME             -> <HOME>/.config/mxm
    """
    override = os.getenv("MXM_CONFIG_HOME")
    if override:
        return Path(override).expanduser()

    xdg = os.getenv("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg).expanduser() / "mxm"

    return Path.home() / ".config" / "mxm"


def resolve_environment(
    env: str | None = None, *, default: str = "dev"
) -> tuple[str, str]:
    """
    Pick the active deployment environment (e.g., 'dev', 'staging', 'prod').

    Precedence:
      1) explicit function argument (env=...)
      2) environment variable: MXM_ENV
      3) default value (defaults to 'dev')

    Returns:
        (selected_value, source) where source is one of: 'arg', 'env', 'default'.
    """
    if env is not None and env.strip():
        return env.strip(), "arg"

    v = os.getenv("MXM_ENV")
    if v is not None and v.strip():
        return v.strip(), "env"

    return default, "default"
