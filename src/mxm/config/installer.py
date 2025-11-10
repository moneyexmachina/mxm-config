from __future__ import annotations

from collections.abc import Iterable, Iterator
import importlib
from importlib import resources
from pathlib import Path
import shutil
import warnings

from mxm.config.ids import validate_app_id
from mxm.config.reports import InstalledFile, InstallReport
from mxm.config.resolver import get_config_root
from mxm.config.types import DefaultsMode

# --- Public API constants -----------------------------------------------------

_CORE_FILES: list[str] = [
    "default.yaml",
    "environment.yaml",
    "machine.yaml",
    "profile.yaml",
    "local.yaml",
]


# --- Internal helpers ---------------------------------------------------------


def _ensure_dir(p: Path, records: list[InstalledFile]) -> None:
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)
        records.append(InstalledFile(src=None, dest=p, action="created"))


def _copy_if_needed(
    src: Path, dst: Path, overwrite: bool, records: list[InstalledFile]
) -> None:
    if dst.exists() and not overwrite:
        records.append(InstalledFile(src=src, dest=dst, action="skipped"))
        return
    _ensure_dir(dst.parent, records)
    shutil.copy(str(src), str(dst))
    # Treat both overwrite and first-time as "copied"
    records.append(InstalledFile(src=src, dest=dst, action="copied"))


def _iter_seed_files_from_dir(root: Path) -> Iterable[tuple[Path, Path]]:
    """Yield (src, rel) for core files and templates/*.yaml inside a directory."""
    # core files
    for fname in _CORE_FILES:
        p = root / fname
        if p.is_file():
            yield p, Path(fname)

    # templates
    troot = root / "templates"
    if troot.is_dir():
        for child in troot.iterdir():
            cpath = child
            if cpath.is_file() and cpath.suffix == ".yaml":
                yield cpath, Path("templates") / cpath.name


def _iter_seed_files_from_package(
    shipped_package: str,
    app_id: str,
    resource_subpath: str = "_data/seeds",
) -> Iterator[tuple[Path, Path]]:
    """
    Yield (src_file, rel_path) pairs for YAML seeds under:
        <pkg>/<resource_subpath>/<app_id>/**/*
    This includes nested folders such as `templates/`.

    Parameters
    ----------
    shipped_package
        Python import path of the package that ships the seeds.
    app_id
        The application identifier (subfolder name under resource_subpath).
    resource_subpath
        Relative resource root inside the package (default: 'config/_data/seeds').

    Yields
    ------
    (src_file, rel_path)
        Absolute source file path on disk, and its path relative to the app's seed root.
    """
    pkg = importlib.import_module(shipped_package)
    # Build a traversable resource path to .../seeds/<app_id>
    traversable = resources.files(pkg) / resource_subpath / app_id  # type: ignore[attr-defined]

    # Convert to a real filesystem path (works for wheels/zip installs too)
    with resources.as_file(traversable) as base_path:
        base = Path(base_path)

        if not base.exists() or not base.is_dir():
            raise FileNotFoundError(
                f"No seeds for app_id '{app_id}' under "
                f"'{shipped_package}:{resource_subpath}/{app_id}'."
            )

        # Recurse and yield YAML files; include nested dirs like 'templates/'
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".yaml", ".yml"}:
                rel = p.relative_to(base)
                yield p, rel


# --- API ------------------------------------------------------------------


def install_config(
    app_id: str,
    *,
    mode: DefaultsMode = DefaultsMode.shipped,
    # shipped mode
    shipped_package: str | None = None,
    # seed mode
    seed_root: Path | None = None,
    # destination
    dest_root: Path | None = None,
    overwrite: bool = False,
    create_sentinel: bool = True,
) -> InstallReport:
    """
    Install default configuration into ~/.config/mxm/<app_id>/ by default.

    Modes:
      - shipped: copy from an installed package (provide shipped_package="...")
      - seed:    copy from a filesystem directory (provide seed_root=Path(...))
      - empty:   create the app dir (and optional sentinel) only

    Returns:
      InstallReport with a full action log.
    """
    validate_app_id(app_id)
    config_root: Path = dest_root if dest_root else get_config_root()
    dst_root: Path = config_root / app_id
    records: list[InstalledFile] = []
    _ensure_dir(dst_root, records)  # ensure app dir exists (recorded if created)

    if mode is DefaultsMode.empty:
        if create_sentinel:
            sentinel = dst_root / ".initialized"
            if not sentinel.exists():
                sentinel.touch()
                records.append(InstalledFile(src=None, dest=sentinel, action="created"))
            else:
                records.append(InstalledFile(src=None, dest=sentinel, action="skipped"))
        return InstallReport(
            app_id=app_id, mode=mode, dest_root=config_root, installed=tuple(records)
        )

    if mode is DefaultsMode.seed:
        if seed_root is None:
            raise ValueError("install_config(mode='seed') requires seed_root=Path(...)")
        if not Path(seed_root).exists():
            raise FileNotFoundError(f"Seeds directory not found: {seed_root}")
        iterator = _iter_seed_files_from_dir(seed_root)

    elif mode is DefaultsMode.shipped:
        if shipped_package is None:
            raise ValueError(
                "install_config(mode='shipped') requires shipped_package='package.path'"
            )
        iterator = _iter_seed_files_from_package(shipped_package, app_id)

    else:  # pragma: no cover (exhaustive safeguard)
        raise ValueError(f"Unknown mode: {mode}")

    for src, rel in iterator:
        dst = dst_root / rel
        _copy_if_needed(src, dst, overwrite, records)

    return InstallReport(
        app_id=app_id, mode=mode, dest_root=config_root, installed=tuple(records)
    )


# --- Backward compatibility alias --------------------------------------------


def install_all(
    package: str,
    target_root: Path | None = None,
    target_name: str | None = None,
    overwrite: bool = False,
) -> list[Path]:
    """
    DEPRECATED: install all known config files from a package into ~/.config/mxm/<package>/.

    This function is preserved for compatibility with the original signature and return
    type (list[Path]). It delegates to install_config(mode='shipped') and returns only
    the files that were actually written (created or copied), preserving previous behavior
    where skipped files were not included in the result.

    Args:
        package: Import path to the package providing config files,
                 e.g. "mxm_config.examples.demo_config".
        target_root: Optional override for the mxm config root (defaults to ~/.config/mxm).
        target_name: Optional override for the subdirectory name under the config root.
                     By default, the last component of the package name is used.
        overwrite: Whether to overwrite existing files if they already exist.

    Returns:
        A list of installed file paths (created or copied this run).
    """
    warnings.warn(
        "mxm.config.installer.install_all is deprecated; use install_config(...) instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    app_id = target_name or package.split(".")[-1]
    report = install_config(
        app_id=app_id,
        mode=DefaultsMode.shipped,
        shipped_package=package,
        dest_root=target_root,
        overwrite=overwrite,
    )

    # Match legacy semantics: only return paths that were actually written this run
    written = [
        f.dest
        for f in report.installed
        if f.action in ("created", "copied") and f.dest.is_file()
    ]
    return written
