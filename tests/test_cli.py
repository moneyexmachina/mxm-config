"""Tests for the mxm-config CLI."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from mxm.config._version import __version__
from mxm.config.cli import app

runner = CliRunner()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_cli_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.output


def test_cli_show_config_prints_resolved_config(tmp_path: Path) -> None:
    app_root = tmp_path / "apps" / "mxm-moneymachine"

    _write(app_root / "default.yaml", "value: default\n")
    _write(app_root / "role.yaml", "marketdata:\n  value: role\n")

    result = runner.invoke(
        app,
        [
            "show-config",
            "--app",
            "mxm-moneymachine",
            "--environment",
            "dev",
            "--machine",
            "bridge",
            "--substrate",
            "local-process",
            "--role",
            "marketdata",
            "--store-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "value: role" in result.output


def test_cli_show_config_applies_full_layer_order(tmp_path: Path) -> None:
    app_root = tmp_path / "apps" / "mxm-moneymachine"

    _write(app_root / "default.yaml", "value: default\n")
    _write(app_root / "environment.yaml", "dev:\n  value: environment\n")
    _write(app_root / "machine.yaml", "bridge:\n  value: machine\n")
    _write(app_root / "substrate.yaml", "local-process:\n  value: substrate\n")
    _write(app_root / "role.yaml", "marketdata:\n  value: role\n")

    result = runner.invoke(
        app,
        [
            "show-config",
            "--app",
            "mxm-moneymachine",
            "--environment",
            "dev",
            "--machine",
            "bridge",
            "--substrate",
            "local-process",
            "--role",
            "marketdata",
            "--store-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    assert "value: role" in result.output


def test_cli_show_config_fails_cleanly_for_missing_app_root(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "show-config",
            "--app",
            "mxm-moneymachine",
            "--environment",
            "dev",
            "--machine",
            "bridge",
            "--substrate",
            "local-process",
            "--role",
            "marketdata",
            "--store-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 1
    assert "Application configuration root" in result.output


def test_cli_show_config_fails_cleanly_for_missing_selector(tmp_path: Path) -> None:
    app_root = tmp_path / "apps" / "mxm-moneymachine"

    _write(app_root / "default.yaml", "value: default\n")
    _write(app_root / "environment.yaml", "prod:\n  value: prod\n")

    result = runner.invoke(
        app,
        [
            "show-config",
            "--app",
            "mxm-moneymachine",
            "--environment",
            "dev",
            "--machine",
            "bridge",
            "--substrate",
            "local-process",
            "--role",
            "marketdata",
            "--store-root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 1
    assert "Selector" in result.output
    assert "dev" in result.output
