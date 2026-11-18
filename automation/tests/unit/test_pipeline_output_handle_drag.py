"""Regression: output-handle drag must read a STABLE box, prime the handle, and retry a missed drag once."""
from unittest.mock import MagicMock

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from pages.pipeline_detail_page import PipelineDetailPage


def _page_obj(boxes, dropdown_results):
    pp = PipelineDetailPage.__new__(PipelineDetailPage)
    pp.__dict__["page"] = MagicMock()
    pp.page.viewport_size = {"width": 1280, "height": 720}
    handle = MagicMock()
    handle.bounding_box.side_effect = list(boxes)
    pp.page.locator.return_value = handle
    dd = MagicMock()
    dd.wait_for.side_effect = dropdown_results
    return pp, handle, dd


def _patch_dropdown(monkeypatch, dd):
    monkeypatch.setattr(PipelineDetailPage, "connection_dropdown_menu", dd, raising=False)


A = {"x": 10, "y": 10, "width": 16, "height": 16}
B = {"x": 40, "y": 30, "width": 16, "height": 16}


def test_waits_for_two_consecutive_equal_boxes_and_hovers_before_down(monkeypatch):
    pp, handle, dd = _page_obj([B, A, A], [None])
    _patch_dropdown(monkeypatch, dd)
    pp.drag_output_handle_to_empty_canvas("Agent 1")
    assert handle.bounding_box.call_count == 3  # moving box rejected
    names = [c[0] for c in pp.page.mouse.method_calls]
    assert names.count("down") == 1 and names.count("up") == 1
    first_move = pp.page.mouse.method_calls[0]
    assert first_move.args == (18.0, 18.0)  # stable centre, not the stale one
    handle.hover.assert_called_once()


def test_missed_drag_is_retried_once(monkeypatch):
    pp, handle, dd = _page_obj([A, A, A, A], [PlaywrightTimeoutError("x"), None])
    _patch_dropdown(monkeypatch, dd)
    pp.drag_output_handle_to_empty_canvas("Agent 1")
    assert [c[0] for c in pp.page.mouse.method_calls].count("down") == 2


def test_second_miss_fails_loudly(monkeypatch):
    pp, handle, dd = _page_obj([A, A, A, A], [PlaywrightTimeoutError("x")] * 2)
    _patch_dropdown(monkeypatch, dd)
    with pytest.raises(PlaywrightTimeoutError):
        pp.drag_output_handle_to_empty_canvas("Agent 1")
