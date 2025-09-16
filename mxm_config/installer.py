import shutil
from importlib.resources import files
from pathlib import Path

from mxm_config.resolver import get_config_root

_CORE_FILES = [
    "default.yaml",
    "environment.yaml",
    "machine.yaml",
    "profile.yaml",
    "overrides.yaml",
]


def install_all(
    package: str, target_root: Path | None = None, overwrite: bool = False
) -> list[Path]:
    """Install all known config files from a package into ~/.config/mxm/<package>/.

    Args:
        package: The package namespace, e.g. "mxm_config.examples.demo_config".
        target_root: Optional override for the mxm config root.
        overwrite: Whether to overwrite existing files.

    Returns:
        List of installed file paths.
    """
    installed = []
    dst_root = (target_root or get_config_root()) / package.split(".")[-1]
    dst_root.mkdir(parents=True, exist_ok=True)

    for fname in _CORE_FILES:
        src = files(package).joinpath(fname)
        if src.is_file():
            dst = dst_root / fname
            if dst.exists() and not overwrite:
                continue
            shutil.copy(src, dst)
            installed.append(dst)

    # optional templates folder
    src_templates = files(package).joinpath("templates")
    if src_templates.is_dir():
        tmpl_root = dst_root / "templates"
        tmpl_root.mkdir(parents=True, exist_ok=True)
        for src in src_templates.iterdir():
            if src.suffix == ".yaml":
                dst = tmpl_root / src.name
                if dst.exists() and not overwrite:
                    continue
                shutil.copy(src, dst)
                installed.append(dst)

    return installed
