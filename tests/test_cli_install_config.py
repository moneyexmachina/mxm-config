from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

import pytest
from typer.testing import CliRunner

from mxm.config.cli import app
from mxm.config.installer import DefaultsMode
from mxm.config.reports import InstalledFile, InstallReport

runner = CliRunner()

_ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")


def _deansi(s: str) -> str:
    return _ANSI_RE.sub("", s)


# ------------------------------------------------------------------------------
# Subprocess helper for clean stdout/stderr separation
# ------------------------------------------------------------------------------


def run_cli(args: list[str]) -> tuple[int, str, str]:
    """
    Run the CLI as a separate process to get clean stdout/stderr separation.

    Returns
    -------
    (returncode, stdout, stderr)
    """
    env = os.environ.copy()
    # Disable colors/styling across ecosystems
    env.update(
        {
            "NO_COLOR": "1",  # generic no-color convention
            "CLICOLOR": "0",  # many tools honor this
            "PY_COLORS": "0",  # pytest/rich honor this
            "FORCE_COLOR": "0",  # some CLIs honor this
            "RICH_NO_COLOR": "1",  # rich-specific
            "TERM": "dumb",  # makes many libs avoid fancy TTY features
        }
    )
    proc = subprocess.run(
        [sys.executable, "-m", "mxm.config.cli", *args],
        text=True,
        capture_output=True,
        env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


# ------------------------------------------------------------------------------
# Test helpers: real report factory + spy
# ------------------------------------------------------------------------------


def make_fake_report(
    dest_root: Path,
    *,
    app_id: str = "mxm.config",
    mode: DefaultsMode = DefaultsMode.shipped,
    files: tuple[InstalledFile, ...] = (),
) -> InstallReport:
    """Build a real InstallReport for tests (no TypedDicts, fully typed)."""
    return InstallReport(
        app_id=app_id,
        mode=mode,
        dest_root=dest_root,
        installed=files,
    )


class _Spy:
    """Callable spy that records calls and returns a preconfigured InstallReport."""

    _fake_report: InstallReport
    calls: list[dict[str, Any]]

    def __init__(self) -> None:
        self.calls = []
        # Default report matches common assertions (app_id shown in JSON, etc.)
        self._fake_report = InstallReport(
            app_id="mxm.config",
            mode=DefaultsMode.empty,
            dest_root=Path("/tmp/.config/mxm"),
            installed=(),
        )

    def __call__(self, *args: Any, **kwargs: Any) -> InstallReport:
        self.calls.append({"args": args, "kwargs": kwargs})
        return self._fake_report


# ------------------------------------------------------------------------------
# Help / version / validation (subprocess: clean stdout/stderr)
# ------------------------------------------------------------------------------


def test_help_shows_command_and_options() -> None:
    code, out, _ = run_cli(["--help"])
    assert code == 0
    assert "install-config" in _deansi(out)

    code2, out2, _ = run_cli(["install-config", "--help"])
    assert code2 == 0
    clean = _deansi(out2)
    assert "--app-id" in clean
    assert "--mode" in clean


def test_version_flag_prints_version() -> None:
    code, out, _ = run_cli(["--version"])
    assert code == 0
    assert out.strip()  # something like 0.5.0.dev0


def test_missing_app_id_errors() -> None:
    code, _, _ = run_cli(["install-config"])
    # Typer usage error (non-zero). We don't assert message text here.
    assert code != 0


def test_seed_requires_seed_root() -> None:
    code, out, err = run_cli(
        ["install-config", "--app-id", "mxm.config", "--mode", "seed"]
    )
    assert code == 1
    assert "seed-root" in err.lower() or "seed-root" in out.lower()


def test_shipped_requires_pkg() -> None:
    code, out, err = run_cli(
        ["install-config", "--app-id", "mxm.config", "--mode", "shipped"]
    )
    assert code == 1
    assert "pkg" in err.lower() or "pkg" in out.lower()


def test_invalid_app_id_is_rejected() -> None:
    code, out, err = run_cli(["install-config", "--app-id", "mxm.", "--mode", "empty"])
    assert code == 1
    msg = (err or out).lower()
    assert "invalid app_id" in msg or "error:" in msg


# ------------------------------------------------------------------------------
# Plumbing / happy paths (in-process: monkeypatch install_config)
# ------------------------------------------------------------------------------


def test_shipped_happy_path_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    spy = _Spy()
    monkeypatch.setattr("mxm.config.cli.install_config", spy)

    r = runner.invoke(
        app,
        [
            "install-config",
            "--app-id",
            "mxm.config",
            "--mode",
            "shipped",
            "--pkg",
            "mxm.config",
            "--dest-root",
            str(tmp_path),
            "--overwrite",
            "--json",
        ],
    )
    assert r.exit_code == 0

    # install_config called once with expected kwargs
    assert len(spy.calls) == 1
    kwargs = spy.calls[0]["kwargs"]
    assert kwargs["app_id"] == "mxm.config"
    assert kwargs["mode"] == DefaultsMode.shipped
    assert kwargs["shipped_package"] == "mxm.config"
    assert kwargs["seed_root"] is None
    assert kwargs["dest_root"] == tmp_path
    assert kwargs["overwrite"] is True
    assert kwargs["create_sentinel"] is True  # default (not --no-sentinel)

    # JSON printed
    data = json.loads(r.output)
    assert data["app_id"] == "mxm.config"
    assert "installed" in data


def test_seed_happy_path_pretty(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    spy = _Spy()
    spy._fake_report = make_fake_report(
        dest_root=tmp_path,
        app_id="mxm.config",
        mode=DefaultsMode.seed,
        files=(InstalledFile(src=None, dest=tmp_path / "cfg.yaml", action="created"),),
    )

    monkeypatch.setattr("mxm.config.cli.install_config", spy)

    seed_root = tmp_path / "seeds" / "mxm.config"
    seed_root.mkdir(parents=True, exist_ok=True)

    r = runner.invoke(
        app,
        [
            "install-config",
            "--app-id",
            "mxm.config",
            "--mode",
            "seed",
            "--seed-root",
            str(seed_root),
            "--dest-root",
            str(tmp_path),
        ],
    )
    assert r.exit_code == 0
    assert "InstallReport(" in r.output  # pretty() output

    kwargs = spy.calls[0]["kwargs"]
    assert kwargs["mode"] == DefaultsMode.seed
    assert kwargs["seed_root"] == seed_root
    assert kwargs["shipped_package"] is None


def test_empty_mode_no_sentinel(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    spy = _Spy()
    monkeypatch.setattr("mxm.config.cli.install_config", spy)
    r = runner.invoke(
        app,
        [
            "install-config",
            "--app-id",
            "mxm.config",
            "--mode",
            "empty",
            "--no-sentinel",
            "--dest-root",
            str(tmp_path),
        ],
    )
    assert r.exit_code == 0
    kwargs = spy.calls[0]["kwargs"]
    assert kwargs["mode"] == DefaultsMode.empty
    assert kwargs["create_sentinel"] is False


def test_underlying_error_maps_to_exit_2(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(**_: Any) -> Any:
        raise RuntimeError("kaboom")

    monkeypatch.setattr("mxm.config.cli.install_config", boom)
    r = runner.invoke(
        app,
        ["install-config", "--app-id", "mxm.config", "--mode", "empty"],
    )
    assert r.exit_code == 2
    assert "kaboom" in r.output.lower()
