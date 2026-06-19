"""Unit tests for the @action decorator."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from utils.actions import action, _get_rp_step


class _FakePage:
    def __init__(self):
        self.screenshot_calls = 0

    def screenshot(self, full_page: bool = False) -> bytes:
        self.screenshot_calls += 1
        return b"\x89PNG_fake"


class _FakePageObj:
    def __init__(self):
        self.page = _FakePage()

    @action("Do something")
    def do_something(self, value: str, timeout: int = 5000) -> str:
        return f"done:{value}"

    @action("Raise error")
    def raise_error(self, msg: str) -> None:
        raise ValueError(f"boom:{msg}")

    @action()
    def unnamed(self) -> int:
        return 42


def test_action_returns_value():
    obj = _FakePageObj()
    with patch("utils.actions._get_rp_step", return_value=None):
        assert obj.do_something("hello") == "done:hello"


def test_action_unnamed_uses_func_name(caplog):
    obj = _FakePageObj()
    with patch("utils.actions._get_rp_step", return_value=None):
        with caplog.at_level(logging.INFO, logger="elitea.steps"):
            obj.unnamed()
    assert "unnamed" in caplog.text


def test_action_excludes_timeout_from_log(caplog):
    obj = _FakePageObj()
    with patch("utils.actions._get_rp_step", return_value=None):
        with caplog.at_level(logging.INFO, logger="elitea.steps"):
            obj.do_something("world", timeout=3000)
    assert "timeout" not in caplog.text
    assert "3000" not in caplog.text


def test_action_includes_non_timeout_param(caplog):
    obj = _FakePageObj()
    with patch("utils.actions._get_rp_step", return_value=None):
        with caplog.at_level(logging.INFO, logger="elitea.steps"):
            obj.do_something("my_value")
    assert "my_value" in caplog.text


def test_action_reraises_exception():
    obj = _FakePageObj()
    with patch("utils.actions._get_rp_step", return_value=None):
        with pytest.raises(ValueError, match="boom:oops"):
            obj.raise_error("oops")


def test_action_captures_screenshot_on_failure():
    obj = _FakePageObj()
    with patch("utils.actions._get_rp_step", return_value=None):
        with pytest.raises(ValueError):
            obj.raise_error("oops")
    assert obj.page.screenshot_calls == 1


def test_action_no_screenshot_on_success():
    obj = _FakePageObj()
    with patch("utils.actions._get_rp_step", return_value=None):
        obj.do_something("ok")
    assert obj.page.screenshot_calls == 0


def test_action_uses_rp_step_as_context_manager():
    fake_ctx = MagicMock()
    fake_ctx.__enter__ = MagicMock(return_value=None)
    fake_ctx.__exit__ = MagicMock(return_value=False)
    mock_rp_step = MagicMock(return_value=fake_ctx)

    obj = _FakePageObj()
    with patch("utils.actions._get_rp_step", return_value=mock_rp_step):
        obj.do_something("rp_test")

    mock_rp_step.assert_called_once()
    fake_ctx.__enter__.assert_called_once()
    fake_ctx.__exit__.assert_called_once()


def test_action_passes_params_to_rp_step():
    """Input params (minus timeout) must be passed to rp_step as params=."""
    fake_ctx = MagicMock()
    fake_ctx.__enter__ = MagicMock(return_value=None)
    fake_ctx.__exit__ = MagicMock(return_value=False)
    mock_rp_step = MagicMock(return_value=fake_ctx)

    obj = _FakePageObj()
    with patch("utils.actions._get_rp_step", return_value=mock_rp_step):
        obj.do_something("abc", timeout=9000)

    mock_rp_step.assert_called_once_with("Do something", params={"value": "abc"})


def test_action_passes_none_params_when_no_args():
    """When a method has no non-timeout params, rp_step receives params=None."""
    fake_ctx = MagicMock()
    fake_ctx.__enter__ = MagicMock(return_value=None)
    fake_ctx.__exit__ = MagicMock(return_value=False)
    mock_rp_step = MagicMock(return_value=fake_ctx)

    obj = _FakePageObj()
    with patch("utils.actions._get_rp_step", return_value=mock_rp_step):
        obj.unnamed()

    mock_rp_step.assert_called_once_with("unnamed", params=None)
