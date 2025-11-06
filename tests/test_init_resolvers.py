# tests/test_init_resolvers.py
"""Tests for mxm_config.init_resolvers."""

from __future__ import annotations

from collections.abc import Iterator
import re
from typing import Any, Final, cast

from omegaconf import OmegaConf
import pytest

# Import only the public API.
# We test private helpers indirectly via behaviour.
from mxm.config.init_resolvers import register_mxm_resolvers

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_RESOLVERS: Final[tuple[str, ...]] = ("cwd", "home", "env", "timestamp")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def cleanup_resolvers() -> Iterator[None]:
    """Ensure MXM resolvers are unregistered before and after each test."""
    for name in DEFAULT_RESOLVERS:
        if OmegaConf.has_resolver(name):
            OmegaConf.clear_resolver(name)
    yield
    for name in DEFAULT_RESOLVERS:
        if OmegaConf.has_resolver(name):
            OmegaConf.clear_resolver(name)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_register_mxm_resolvers_registers_all() -> None:
    """Ensure all resolvers are registered and callable."""
    register_mxm_resolvers()

    for name in DEFAULT_RESOLVERS:
        assert OmegaConf.has_resolver(name)

    cfg = OmegaConf.create(
        {
            "a": "${cwd:}",
            "b": "${home:}",
            "c": "${env:PATH}",
            "d": "${timestamp:}",
        }
    )

    resolved = cast(dict[str, Any], OmegaConf.to_container(cfg, resolve=True))
    assert isinstance(resolved["a"], str)
    assert isinstance(resolved["b"], str)
    assert isinstance(resolved["c"], (str, type(None)))
    assert re.match(r"^\d{4}-\d{2}-\d{2}T", str(resolved["d"]))


def test_register_mxm_resolvers_idempotent() -> None:
    """Calling register twice should not change resolver state."""
    register_mxm_resolvers()
    first_state = {k for k in DEFAULT_RESOLVERS if OmegaConf.has_resolver(k)}
    register_mxm_resolvers()
    second_state = {k for k in DEFAULT_RESOLVERS if OmegaConf.has_resolver(k)}
    assert first_state == second_state


def test_env_resolver_behaviour(monkeypatch: pytest.MonkeyPatch) -> None:
    """Check that the env resolver behaves correctly."""
    register_mxm_resolvers()

    monkeypatch.setenv("MXM_TEST_VAR", "42")

    cfg = OmegaConf.create(
        {
            "exists": "${env:MXM_TEST_VAR}",
            "missing": "${env:DOES_NOT_EXIST,default}",
        }
    )

    resolved = cast(dict[str, Any], OmegaConf.to_container(cfg, resolve=True))

    assert resolved["exists"] == "42"
    assert resolved["missing"] == "default"
