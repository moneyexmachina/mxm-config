import shutil
from importlib.resources import files
from pathlib import Path
from typing import List, Optional, cast

from mxm_config.resolver import get_config_root

_CORE_FILES: list[str] = [
    "default.yaml",
    "environment.yaml",
    "machine.yaml",
    "profile.yaml",
    "local.yaml",
]


def install_all(
    package: str,
    target_root: Optional[Path] = None,
    target_name: Optional[str] = None,
    overwrite: bool = False,
) -> List[Path]:
    """Install all known config files from a package into ~/.config/mxm/<package>/.

    Args:
        package: Import path to the package providing config files,
            e.g. ``"mxm_config.examples.demo_config"``.
        target_root: Optional override for the mxm config root.
            Defaults to ``~/.config/mxm``.
        target_name: Optional override for the subdirectory name under the config root.
            By default, the last component of the package name is used.
        overwrite: Whether to overwrite existing files if they already exist.

    Returns:
        A list of installed file paths.
    """
    config_root: Path = target_root if target_root else get_config_root()
    package_dir: str = target_name or package.split(".")[-1]
    dst_root: Path = config_root / package_dir
    dst_root.mkdir(parents=True, exist_ok=True)

    installed: List[Path] = []

    for fname in _CORE_FILES:
        src = files(package).joinpath(fname)
        if src.is_file():
            dst = dst_root / fname
            if dst.exists() and not overwrite:
                continue
            shutil.copy(str(src), str(dst))
            installed.append(dst)

    src_templates = files(package).joinpath("templates")
    if src_templates.is_dir():
        tmpl_root = dst_root / "templates"
        tmpl_root.mkdir(parents=True, exist_ok=True)
        for src in src_templates.iterdir():
            src_path = cast(Path, src)
            if src_path.suffix == ".yaml":
                dst = tmpl_root / src_path.name
                if dst.exists() and not overwrite:
                    continue
                shutil.copy(str(src), str(dst))
                installed.append(dst)

    return installed
