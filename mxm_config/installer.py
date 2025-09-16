import shutil
from importlib.resources import files
from pathlib import Path

from .resolver import get_config_root


def install_default(package: str, force: bool = False) -> Path:
    """
    Install a package's default.yaml into ~/.config/mxm/<package>/default.yaml

    Args:
        package: Dotted import path for the package (e.g. "mxm_config.examples.demo_config")
        force: Whether to overwrite an existing file

    Returns:
        Path to the installed file
    """
    target_root = get_config_root() / package.replace(".", "/")
    target_root.mkdir(parents=True, exist_ok=True)

    source = files(package).joinpath("default.yaml")
    target = target_root / "default.yaml"

    if target.exists() and not force:
        print(f"[mxm-config] Skipping existing default: {target}")
        return target

    shutil.copy(source, target)
    print(f"[mxm-config] Installed default.yaml for {package} -> {target}")
    return target


def install_templates(package: str, force: bool = False) -> list[Path]:
    """
    Install all .yaml files from a package's config_templates/ into
    ~/.config/mxm/<package_name>/templates/
    """
    package_name = package.split(".")[-1]
    source_dir = files(package).joinpath("config_templates")
    target_dir = get_config_root() / package_name / "templates"
    target_dir.mkdir(parents=True, exist_ok=True)

    installed = []
    if not source_dir.is_dir():
        print(f"[mxm-config] No templates found for {package}")
        return installed

    for entry in source_dir.iterdir():
        if entry.suffix == ".yaml":
            target = target_dir / entry.name
            if target.exists() and not force:
                print(f"[mxm-config] Skipping existing template: {target}")
                continue
            shutil.copy(entry, target)
            installed.append(target)
            print(f"[mxm-config] Installed template {entry.name} -> {target}")

    return installed
