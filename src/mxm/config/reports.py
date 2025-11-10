"""Reporting structures for mxm-config installs.

This module defines lightweight, serializable records used to report the results
of a configuration installation. It is intentionally independent of the
installer logic to avoid circular imports and to keep the data model small and
portable across CLI, tests, and external tooling.

Public API
----------
- `InstalledFile`: per-file action record
- `InstallReport`: aggregate report with counters, `to_dict()`, and `pretty()`
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, cast

from mxm.config.types import DefaultsMode

# ---- Per-file record ---------------------------------------------------------

Action = Literal["created", "copied", "skipped"]
"""Action taken for a single destination path during installation."""


@dataclass(frozen=True)
class InstalledFile:
    """A single file-level action taken by the installer.

    Attributes
    ----------
    src
        Source file path (if any). `None` for synthetic files such as sentinels.
    dest
        Destination path under the app's config directory.
    action
        One of: "created" (new file), "copied" (overwritten), "skipped" (left as-is).
    """

    src: Path | None
    dest: Path
    action: Action

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable representation of this record."""
        return {
            "src": str(self.src) if self.src is not None else None,
            "dest": str(self.dest),
            "action": self.action,
        }

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> InstalledFile:
        """Reconstruct an InstalledFile from a dict produced by to_dict()."""
        src_raw = d.get("src")
        action = cast(Action, d["action"])
        return cls(
            src=Path(src_raw) if src_raw is not None else None,
            dest=Path(d["dest"]),
            action=action,
        )


# ---- Aggregate install report -----------------------------------------------


@dataclass(frozen=True)
class InstallReport:
    """Aggregate result of a configuration installation.

    Attributes
    ----------
    app_id
        Identifier of the application whose config was installed.
    mode
        Installation mode used (e.g., DefaultsMode.shipped / seed / empty).
    dest_root
        The config root directory (e.g., ``~/.config/mxm``). The app's files
        were written under ``dest_root / app_id``.
    installed
        Tuple of file-level records in the order they were processed.
    """

    app_id: str
    mode: DefaultsMode
    dest_root: Path
    installed: tuple[InstalledFile, ...]

    # ---- Counters ------------------------------------------------------------

    @property
    def created_count(self) -> int:
        """Number of 'created' actions."""
        return sum(1 for r in self.installed if r.action == "created")

    @property
    def copied_count(self) -> int:
        """Number of 'copied' (overwritten) actions."""
        return sum(1 for r in self.installed if r.action == "copied")

    @property
    def skipped_count(self) -> int:
        """Number of 'skipped' actions."""
        return sum(1 for r in self.installed if r.action == "skipped")

    # ---- Serialization & display --------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary of this report."""
        return {
            "app_id": self.app_id,
            "mode": str(self.mode),
            "dest_root": str(self.dest_root),
            "installed": [r.to_dict() for r in self.installed],
            "created_count": self.created_count,
            "copied_count": self.copied_count,
            "skipped_count": self.skipped_count,
        }

    @classmethod
    def from_dict(cls, d: Mapping[str, Any]) -> InstallReport:
        """Reconstruct an InstallReport from a dict produced by to_dict()."""
        return cls(
            app_id=str(d["app_id"]),
            mode=DefaultsMode(d["mode"]),
            dest_root=Path(d["dest_root"]),
            installed=tuple(InstalledFile.from_dict(x) for x in d.get("installed", [])),
        )

    def pretty(self) -> str:
        """Return a human-friendly multi-line summary of the report."""
        lines: list[str] = []
        lines.append(f"InstallReport(app_id={self.app_id}, mode={self.mode})")
        lines.append(f"  dest_root: {self.dest_root}")
        lines.append(
            f"  summary: created={self.created_count}, "
            f"copied={self.copied_count}, skipped={self.skipped_count}"
        )

        if self.installed:
            lines.append("  files:")
            for r in self.installed:
                src_display = str(r.src) if r.src is not None else "-"
                # fixed-width action for nicer alignment
                lines.append(
                    f"    - [{r.action:7}] {r.dest}  \N{LEFTWARDS ARROW}  {src_display}"
                )
        else:
            lines.append("  files: (none)")

        return "\n".join(lines)

    def __str__(self) -> str:
        """Alias for `pretty()` so printing the object is pleasant by default."""
        return self.pretty()


__all__ = ["Action", "InstallReport", "InstalledFile"]
