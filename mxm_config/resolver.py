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
