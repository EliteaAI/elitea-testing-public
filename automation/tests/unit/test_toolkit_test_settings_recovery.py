"""Unit tests for ToolkitTestSettingsPage.wait_for_tool_result's mid-wait
panel-remount recovery.

Regression coverage for the ELITEA-1979 batch-gate flake (2026-08-02,
tests/batch-approved-top10 round 1): under sustained batch load, the right-
hand Test Settings panel was observed to remount to its empty state WHILE a
RUN TOOL result was still in flight, emptying RESULT_MESSAGE_ITEM and
causing wait_for_tool_result() to time out on an empty list instead of ever
seeing the run's real ✅/❌ outcome. These tests exercise the recovery logic
against fakes (no browser/Playwright infra — see tests/unit/conftest.py) so
the remount-detection/recovery/no-mask contract is pinned independently of
any live-batch timing.
"""

from unittest.mock import MagicMock, patch

import pytest
from pages.toolkit_test_settings_page import ToolkitTestSettingsPage


class _FakeResultLocator:
    """Stands in for `page.locator(RESULT_MESSAGE_ITEM).last`."""

    def __init__(self, text: str):
        self._text = text

    def text_content(self):
        return self._text


class _FakeItemsLocator:
    """Stands in for `page.locator(RESULT_MESSAGE_ITEM)` — supports
    `.count()` (used by `get_result_items().count()`) and `.last`
    (used to build the result locator for `expect(...)`)."""

    def __init__(self, count: int, text: str = ""):
        self._count = count
        self.last = _FakeResultLocator(text)

    def count(self):
        return self._count


class _FakeExpectFailThenPass:
    """Fakes `pages.toolkit_test_settings_page.expect` — its `.to_contain_text()`
    raises `AssertionError` (Playwright's real timeout-assertion type, per the
    documented contract in agent_detail_page.py) on the first *fail_times*
    calls, then succeeds."""

    def __init__(self, fail_times: int):
        self.fail_times = fail_times
        self.calls = 0

    def __call__(self, _locator):
        self.calls += 1
        call_index = self.calls
        outer = self

        class _Assertion:
            def to_contain_text(self, *_args, **_kwargs):
                if call_index <= outer.fail_times:
                    raise AssertionError("Timeout 1000ms exceeded waiting for content")

        return _Assertion()


def _make_page(locator_sequence):
    """`page.locator(...)` returns the next item of *locator_sequence* per call."""
    page = MagicMock()
    it = iter(locator_sequence)
    page.locator.side_effect = lambda *_args, **_kwargs: next(it)
    return page


def _make_settings_page(page) -> ToolkitTestSettingsPage:
    settings_page = ToolkitTestSettingsPage(page)
    # The recovery path drives these via LocatorDescriptor fields that need a
    # real Playwright Page — stub them so only the recovery CONTROL FLOW
    # (whether/how they're called) is under test, not their own internals
    # (already covered live by test_mcp_test_settings_select_and_run_tool.py
    # and test_credential_usage_in_toolkit_flows.py).
    settings_page.select_tool_from_empty_state = MagicMock()
    settings_page.wait_for_panel = MagicMock()
    settings_page.run_tool = MagicMock()
    return settings_page


def test_wait_for_tool_result_no_recovery_without_tool_key():
    """A timeout with tool_key=None (every caller before this fix, and every
    caller that doesn't opt in) re-raises immediately — no recovery attempt,
    no behavior change for the shared page object's other callers."""
    result_item = _FakeItemsLocator(count=0)
    page = _make_page([result_item])
    settings_page = _make_settings_page(page)

    with patch(
        "pages.toolkit_test_settings_page.expect", _FakeExpectFailThenPass(fail_times=99)
    ):
        with pytest.raises(AssertionError):
            settings_page.wait_for_tool_result(timeout=1000)

    settings_page.select_tool_from_empty_state.assert_not_called()
    settings_page.wait_for_panel.assert_not_called()
    settings_page.run_tool.assert_not_called()


def test_wait_for_tool_result_recovers_once_from_panel_remount():
    """RESULT_MESSAGE_ITEM count()==0 at failure time is the remount
    signature (the empty-state panel lost the run) — re-select the tool +
    re-click RUN TOOL exactly once, then succeed on the retried wait."""
    empty_result = _FakeItemsLocator(count=0)
    recovered_result = _FakeItemsLocator(count=1, text="✅ list_branches_in_repo (0.4s)")
    # Call order inside wait_for_tool_result: (1) build the initial result
    # locator, (2) get_result_items().count() to classify the failure,
    # (3) rebuild the result locator after recovery.
    page = _make_page([empty_result, empty_result, recovered_result])
    settings_page = _make_settings_page(page)

    with patch(
        "pages.toolkit_test_settings_page.expect", _FakeExpectFailThenPass(fail_times=1)
    ):
        text = settings_page.wait_for_tool_result(timeout=1000, tool_key="list_branches_in_repo")

    assert "✅" in text, f"Expected the recovered run's success marker in the returned text, got {text!r}"
    settings_page.select_tool_from_empty_state.assert_called_once_with(
        "list_branches_in_repo", timeout=10000
    )
    settings_page.wait_for_panel.assert_called_once()
    settings_page.run_tool.assert_called_once()


def test_wait_for_tool_result_does_not_mask_a_real_failure():
    """RESULT_MESSAGE_ITEM count()>0 at failure time means the result item
    IS present but never got its ✅/❌ marker — a genuine product/timing
    failure, not a remount. Must re-raise, never silently recover (masking a
    real defect is exactly what the no-defect-masking rule forbids)."""
    present_but_unresolved = _FakeItemsLocator(count=1, text="pending…")
    page = _make_page([present_but_unresolved, present_but_unresolved])
    settings_page = _make_settings_page(page)

    with patch(
        "pages.toolkit_test_settings_page.expect", _FakeExpectFailThenPass(fail_times=99)
    ):
        with pytest.raises(AssertionError):
            settings_page.wait_for_tool_result(timeout=1000, tool_key="list_branches_in_repo")

    settings_page.select_tool_from_empty_state.assert_not_called()
    settings_page.wait_for_panel.assert_not_called()
    settings_page.run_tool.assert_not_called()


def test_wait_for_tool_result_reraises_if_second_remount_persists():
    """Exactly one recovery attempt — if the panel remounts a SECOND time,
    the retried wait's own timeout re-raises rather than looping forever."""
    empty_result = _FakeItemsLocator(count=0)
    page = _make_page([empty_result, empty_result, empty_result])
    settings_page = _make_settings_page(page)

    with patch(
        "pages.toolkit_test_settings_page.expect", _FakeExpectFailThenPass(fail_times=99)
    ):
        with pytest.raises(AssertionError):
            settings_page.wait_for_tool_result(timeout=1000, tool_key="list_branches_in_repo")

    settings_page.select_tool_from_empty_state.assert_called_once_with(
        "list_branches_in_repo", timeout=10000
    )
