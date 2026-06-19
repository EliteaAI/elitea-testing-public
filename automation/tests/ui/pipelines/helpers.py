"""Shared navigation helpers for pipeline UI tests.

Extracted from test_pipeline_advanced.py and test_pipeline_nodes.py to
eliminate duplication and provide a single maintained entry point for
common canvas navigation patterns.
"""

from pages.pipeline_detail_page import PipelineDetailPage


def _navigate_to_detail(page, pipeline_id) -> PipelineDetailPage:
    """Navigate to pipeline detail and wait for it to load.

    Dismisses the new-feature banner if present so tabs and form fields
    are accessible immediately after return.

    Returns:
        PipelineDetailPage instance ready for interaction.
    """
    detail_page = PipelineDetailPage(page)
    detail_page.navigate(pipeline_id)
    detail_page.dismiss_banner_if_present()
    return detail_page


def _navigate_to_canvas(page, pipeline_id) -> PipelineDetailPage:
    """Navigate to pipeline detail, dismiss banner, and wait for canvas.

    Delegates to ``_navigate_to_detail`` then waits for the ReactFlow
    canvas wrapper to become visible.

    Returns:
        PipelineDetailPage instance ready for canvas interaction.
    """
    detail_page = _navigate_to_detail(page, pipeline_id)
    detail_page.wait_for_canvas()
    return detail_page
