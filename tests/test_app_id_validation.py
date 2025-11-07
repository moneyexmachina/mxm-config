import pytest

from mxm.config.ids import is_valid_app_id, validate_app_id


@pytest.mark.parametrize(
    "app_id",
    [
        # canonical vendor-prefixed
        "mxm.config",
        "mxm.datakraken",
        "mxm.pipeline",
        # multi-segment, underscores, hyphens
        "mxm.data_kraken",
        "mxm.data-kraken",
        "iic.profile",
        "user.alpha_1.beta-2",
        # minimal and short
        "a",
        "mxm",
        "mxm.a",
        "a.b",
    ],
)
def test_is_valid_app_id_accepts_good_cases(app_id: str) -> None:
    assert is_valid_app_id(app_id) is True
    # validate_app_id should not raise
    validate_app_id(app_id)


@pytest.mark.parametrize(
    "app_id",
    [
        # uppercase not allowed
        "MxM.config",
        "mxm.Config",
        "MXM",
        # leading/trailing separators
        ".mxm",
        "mxm.",
        "-mxm",
        "mxm-",
        "_mxm",
        "mxm_",
        # spaces / whitespace
        "mxm config",
        " mxm.config",
        "mxm.config ",
        "mxm.\tconfig",
        # consecutive dots (disallowed by regex)
        "mxm..config",
        "a..b",
        # empty or only separators
        "",
        ".",
        "-",
        "_",
        # non-ascii characters
        "mxm.cönfig",
        "mxm.confíg",
    ],
)
def test_is_valid_app_id_rejects_bad_cases(app_id: str) -> None:
    assert is_valid_app_id(app_id) is False
    with pytest.raises(ValueError):
        validate_app_id(app_id)


def test_leading_and_trailing_separators_systematically() -> None:
    base = "mxm"
    seps = [".", "_", "-"]
    for s in seps:
        assert not is_valid_app_id(s + base)
        assert not is_valid_app_id(base + s)
        with pytest.raises(ValueError):
            validate_app_id(s + base)
        with pytest.raises(ValueError):
            validate_app_id(base + s)


def test_consecutive_dots_are_rejected() -> None:
    assert not is_valid_app_id("a..b")
    with pytest.raises(ValueError):
        validate_app_id("a..b")


def test_underscore_and_hyphen_inside_are_allowed() -> None:
    ok = "mxm.alpha_beta-gamma"
    assert is_valid_app_id(ok) is True
    validate_app_id(ok)  # should not raise


def test_single_character_id_is_allowed() -> None:
    assert is_valid_app_id("a") is True
    validate_app_id("a")  # should not raise
