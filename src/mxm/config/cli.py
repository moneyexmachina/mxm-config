"""Command-line interface for mxm-config.

The CLI exposes configuration resolution and inspection utilities.

It does not install configuration, discover runtime identity, construct runtime
context, or manage secrets.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from omegaconf import DictConfig, OmegaConf

from mxm.config._version import __version__
from mxm.config.loader import DEFAULT_CONFIG_STORE_ROOT, load_config
from mxm.types import (
    RuntimeIdentity,
)

app = typer.Typer(
    add_completion=False,
    help="mxm-config — RuntimeIdentity-driven configuration resolver",
    no_args_is_help=True,
)


@app.callback(invoke_without_command=True)
def _main(  # pyright: ignore[reportUnusedFunction]
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Handle top-level CLI flags."""
    if version:
        typer.echo(__version__)
        raise typer.Exit(0)


def _echo_err(message: str) -> None:
    """Write an error message to stderr."""
    typer.echo(message, err=True)


@app.command("show-config")
def cmd_show_config(
    app_id: str = typer.Option(
        ...,
        "--app",
        help="Application identifier.",
        metavar="APP_ID",
    ),
    environment: str = typer.Option(
        ...,
        "--environment",
        "--env",
        help="Runtime environment selector.",
        metavar="ENVIRONMENT",
    ),
    machine: str = typer.Option(
        ...,
        "--machine",
        help="Machine identifier selector.",
        metavar="MACHINE",
    ),
    substrate: str = typer.Option(
        ...,
        "--substrate",
        help="Runtime substrate selector.",
        metavar="SUBSTRATE",
    ),
    role: str = typer.Option(
        ...,
        "--role",
        help="Runtime role selector.",
        metavar="ROLE",
    ),
    store_root: Annotated[
        Path,
        typer.Option(
            "--store-root",
            help="Configuration store root.",
            metavar="PATH",
        ),
    ] = DEFAULT_CONFIG_STORE_ROOT,
    resolve: bool = typer.Option(
        True,
        "--resolve/--no-resolve",
        help="Print resolved OmegaConf output.",
    ),
) -> None:
    """Resolve and print configuration for an explicit RuntimeIdentity."""
    identity = RuntimeIdentity(
        app=app_id,
        environment=environment,
        machine=machine,
        substrate=substrate,
        role=role,
    )

    try:
        cfg = load_config(
            identity=identity,
            store_root=store_root.expanduser(),
        )
    except Exception as exc:
        _echo_err(f"error: {exc}")
        raise typer.Exit(1) from None

    if not isinstance(cfg, DictConfig):
        _echo_err("error: resolved configuration is not an OmegaConf DictConfig")
        raise typer.Exit(2)

    output = OmegaConf.to_yaml(cfg, resolve=resolve)
    typer.echo(output)


if __name__ == "__main__":
    app()
