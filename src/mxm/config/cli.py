"""
mxm-config CLI

Thin, dependable CLI for installing *app-owned* MXM configuration
into the user's config root (default: ~/.config/mxm).

Commands
--------
- mxm-config --version
- mxm-config install-config --app-id <APP_ID> [--mode shipped|seed|empty]
    [--pkg <PKG>] [--seed-root <PATH>] [--dest-root <PATH>] [--overwrite] [--json]
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from mxm.config._version import __version__
from mxm.config.ids import validate_app_id
from mxm.config.installer import DefaultsMode, install_config

app = typer.Typer(
    add_completion=False,
    help="mxm-config — app-owned configuration installer",
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def _main(  # pyright: ignore[reportUnusedFunction]
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        is_flag=True,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Top-level flags (currently just --version)."""
    if version:
        typer.echo(__version__)
        raise typer.Exit(0)


def _echo_err(msg: str) -> None:
    typer.echo(msg, err=True)


@app.command("install-config")
def cmd_install_config(
    app_id: str = typer.Option(
        ...,
        "--app-id",
        help="Application identifier; installs under ~/.config/mxm/<app_id>/",
        metavar="APP_ID",
    ),
    mode: str = typer.Option(
        "shipped",
        "--mode",
        help="Installation mode: shipped | seed | empty",
        metavar="MODE",
    ),
    pkg: str | None = typer.Option(
        None,
        "--pkg",
        help="Python package that ships defaults (required for --mode shipped).",
        metavar="PKG",
    ),
    seed_root: str | None = typer.Option(
        None,
        "--seed-root",
        help="Path to the *per-app* seeds folder (…/_data/seeds/<app_id>/) for --mode seed.",
        metavar="PATH",
    ),
    dest_root: str | None = typer.Option(
        None,
        "--dest-root",
        help="Override config root (defaults to ~/.config/mxm).",
        metavar="PATH",
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite existing files."
    ),
    no_sentinel: bool = typer.Option(
        False, "--no-sentinel", help="Skip creating '.initialized' in empty mode."
    ),
    json_out: bool = typer.Option(False, "--json", help="Print InstallReport as JSON."),
) -> None:
    """Install default configuration into ~/.config/mxm/<app_id>/."""
    # Validate app_id early
    try:
        validate_app_id(app_id)
    except ValueError as e:
        _echo_err(f"error: {e}")
        raise typer.Exit(1) from None

    # Map mode (string) -> enum
    key = mode.lower().strip()
    mode_map = {
        "shipped": DefaultsMode.shipped,
        "seed": DefaultsMode.seed,
        "empty": DefaultsMode.empty,
    }
    if key not in mode_map:
        _echo_err("error: --mode must be one of: shipped, seed, empty")
        raise typer.Exit(1)
    mode_enum = mode_map[key]

    # Cross-flag validation
    if mode_enum is DefaultsMode.seed and seed_root is None:
        _echo_err("error: --seed-root is required when --mode seed")
        raise typer.Exit(1)
    if mode_enum is DefaultsMode.shipped and not pkg:
        _echo_err("error: --pkg is required when --mode shipped")
        raise typer.Exit(1)

    # Convert paths from strings (keep CLI surface plain strings to avoid Click type quirks)
    seed_root_path = Path(seed_root) if seed_root else None
    dest_root_path = Path(dest_root) if dest_root else None

    # Execute
    try:
        report = install_config(
            app_id=app_id,
            mode=mode_enum,
            shipped_package=pkg,
            seed_root=seed_root_path,
            dest_root=dest_root_path,
            overwrite=overwrite,
            create_sentinel=not no_sentinel,
        )
    except Exception as exc:
        _echo_err(f"error: {exc}")
        raise typer.Exit(2) from None

    # Output
    if json_out:
        typer.echo(json.dumps(report.to_dict(), indent=2))
    else:
        pretty = getattr(report, "pretty", None)
        typer.echo(pretty() if callable(pretty) else str(report))

    raise typer.Exit(0)


if __name__ == "__main__":
    app()
