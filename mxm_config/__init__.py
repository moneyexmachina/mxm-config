"""MXM Config package.

Provides configuration loading, environment setup, and resolver registration
for all MXM packages.

Importing this package automatically registers standard MXM resolvers so that
interpolations like `${cwd:}` and `${env:VAR}` are available globally.

Typical usage:
    from mxm_config import load_config, install_all

    install_all()              # optional: install package config files into ~/.config/mxm/...
    cfg = load_config("mxm-packagename")  # load the layered MXM configuration
"""

from mxm_config.init_resolvers import register_mxm_resolvers
from mxm_config.installer import install_all
from mxm_config.loader import load_config

register_mxm_resolvers()

__all__ = ["install_all", "load_config"]
