import os
import socket
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


def resolve_environment(env: str | None = None) -> str:
    """Resolve environment (must be explicitly provided).

    Args:
        env: The chosen environment (e.g. "dev", "prod").

    Returns:
        The environment string.

    Raises:
        ValueError: If env is not provided.
    """
    if env is None:
        raise ValueError("Environment must be specified (e.g. 'dev', 'prod').")
    return env


def resolve_profile(profile: str | None = None) -> str:
    """Resolve profile (must be explicitly provided).

    Args:
        profile: The chosen profile (e.g. "research", "trading").

    Returns:
        The profile string.

    Raises:
        ValueError: If profile is not provided.
    """
    if profile is None:
        raise ValueError("Profile must be specified (e.g. 'research', 'trading').")
    return profile


def resolve_machine(machine: str | None = None) -> str:
    """Resolve machine identifier.

    Resolution order:
        1. Explicit argument
        2. Environment variable: MXM_MACHINE
        3. Fallback to system hostname
    """
    if machine is not None:
        return machine

    env_machine = os.getenv("MXM_MACHINE")
    if env_machine:
        return env_machine
    hostname = socket.gethostname().lower()
    if hostname.endswith(".local"):
        hostname = hostname[:-6]
    return hostname
