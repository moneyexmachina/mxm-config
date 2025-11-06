from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from importlib.resources import files
from pathlib import Path
import shutil
import warnings

from mxm.config.resolver import get_config_root

# --- Public API constants -----------------------------------------------------

_CORE_FILES: list[str] = [
    "default.yaml",
    "environment.yaml",
    "machine.yaml",
    "profile.yaml",
    "local.yaml",
]


# --- Types --------------------------------------------------------------------


class DefaultsMode(str, Enum):
    seed = "seed"  # copy from a source directory (repo seeds)
    shipped = "shipped"  # copy from an installed package (importlib.resources)
    empty = "empty"  # create dirs/sentinels only


@dataclass(frozen=True)
class InstalledFile:
    src: Path | None  # None for "empty" created items
    dest: Path
    action: str  # "copied" | "created" | "skipped"


@dataclass(frozen=True)
class InstallReport:
    app_id: str
    mode: DefaultsMode
    dest_root: Path
    installed: tuple[InstalledFile, ...] = field(default_factory=tuple)

    @property
    def copied_count(self) -> int:
        return sum(1 for i in self.installed if i.action == "copied")

    @property
    def created_count(self) -> int:
        return sum(1 for i in self.installed if i.action == "created")

    @property
    def skipped_count(self) -> int:
        return sum(1 for i in self.installed if i.action == "skipped")


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


def _iter_seed_files_from_package(pkg: str) -> Iterable[tuple[Path, Path]]:
    """Yield (src, rel) for core files and templates/*.yaml from a package."""
    pkg_root = files(pkg)

    # core files
    for fname in _CORE_FILES:
        src = pkg_root.joinpath(fname)
        if src.is_file():
            yield Path(str(src)), Path(fname)

    # templates
    troot = pkg_root.joinpath("templates")
    if troot.is_dir():
        for child in troot.iterdir():
            cpath = Path(str(child))
            if cpath.is_file() and cpath.suffix == ".yaml":
                yield cpath, Path("templates") / cpath.name


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
        iterator = _iter_seed_files_from_dir(seed_root)

    elif mode is DefaultsMode.shipped:
        if shipped_package is None:
            raise ValueError(
                "install_config(mode='shipped') requires shipped_package='package.path'"
            )
        iterator = _iter_seed_files_from_package(shipped_package)

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
