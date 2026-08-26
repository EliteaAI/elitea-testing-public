"""UI test — Pipeline Dashboard: Pin to Top (ELITEA-2025).

Verifies that a pipeline card can be pinned to the top of the Pipelines
dashboard (card view) via its list-row "Pin to top" icon button, and that
unpinning reverts the state. Mirrors ``test_credential_pin_unpin.py``
(ELITEA-1974) — same shared ``PinButton.jsx`` widget, same asymmetric
reorder-timing shape (pin re-sorts instantly; unpin needs a fresh
navigate/re-fetch to visually revert, even though its own label flips back
immediately).

Spec: test-specs/pipelines/l2_pipeline-dashboard-pin-to-top_ELITEA-2025.md
"""

import logging
import time

import allure
import pytest
from pages.pipelines_list_page import PipelinesListPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
    "pipelines/ELITEA-2025_pipeline-dashboard-pin-to-top.md",
    "onetest-ai Test Case link",
)
@pytest.mark.p2
def test_pipeline_dashboard_pin_to_top(page, pipeline_api):
    """Pinning a pipeline moves it to the top of the dashboard list; unpinning reverts it."""
    ts = int(time.time())
    pipeline_a_name = f"autotest_pin_pipe_a_{ts}"
    pipeline_b_name = f"autotest_pin_pipe_b_{ts + 5}"
    pipeline_a_id = None
    pipeline_b_id = None

    try:
        with allure.step("Setup — Create Pipeline A and Pipeline B via API"):
            pipeline_a = pipeline_api.create_pipeline(
                name=pipeline_a_name,
                description="Disposable pipeline A for ELITEA-2025 pin/unpin test",
            )
            pipeline_a_id = pipeline_a["id"]

            # Pipeline B is created second so it sorts above A under the
            # dashboard's default created_at-desc order — this is what gives
            # Steps 2/6 a real "position" to move to/from (AFS Test Data).
            pipeline_b = pipeline_api.create_pipeline(
                name=pipeline_b_name,
                description="Disposable pipeline B for ELITEA-2025 pin/unpin test",
            )
            pipeline_b_id = pipeline_b["id"]

            assert pipeline_a_id, "Expected a numeric id for Pipeline A"
            assert pipeline_b_id, "Expected a numeric id for Pipeline B"
            logger.info(
                "Created pipelines — A id=%s name=%s, B id=%s name=%s",
                pipeline_a_id, pipeline_a_name, pipeline_b_id, pipeline_b_name,
            )

        list_page = PipelinesListPage(page)

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

        with allure.step(
            "Step 1/2 — Navigate to the Pipelines dashboard in card view and capture the baseline order"
        ):
            list_page.navigate()
            assert list_page.is_card_view_active(), "Pipelines dashboard should default to card view"

            baseline_order = list_page.get_card_names()
            index_a = baseline_order.index(pipeline_a_name)
            index_b = baseline_order.index(pipeline_b_name)
            assert index_b < index_a, (
                f"Expected Pipeline B above Pipeline A before pinning, got order: {baseline_order}"
            )
            assert list_page.get_pin_toggle_label(pipeline_a_id) == "Pin to top", (
                "Pipeline A's pin button should read 'Pin to top' before pinning"
            )

        with allure.step(
            "Step 3/4 — Click 'Pin to top' on Pipeline A and verify it moves to the top, no reload needed"
        ):
            response = list_page.click_pin_toggle(pipeline_a_id)
            assert response.status == 201, f"Expected 201 Created from the pin request, got {response.status}"

            pinned_order = list_page.get_card_names()
            index_a = pinned_order.index(pipeline_a_name)
            index_b = pinned_order.index(pipeline_b_name)
            assert index_a < index_b, (
                f"Expected Pipeline A above Pipeline B immediately after pinning "
                f"(client-side re-sort, no reload), got order: {pinned_order}"
            )
            assert list_page.get_pin_toggle_label(pipeline_a_id) == "Unpin from top", (
                "Pipeline A's pin button should flip to 'Unpin from top' after pinning"
            )

        with allure.step("Step 5 — Click 'Pin to top' again (unpin) and verify the label flips back immediately"):
            response = list_page.click_pin_toggle(pipeline_a_id)
            assert response.status == 204, f"Expected 204 No Content from the unpin request, got {response.status}"
            assert list_page.get_pin_toggle_label(pipeline_a_id) == "Pin to top", (
                "Pipeline A's pin button should flip back to 'Pin to top' immediately after unpinning"
            )

        with allure.step(
            "Step 6 — Re-navigate to the Pipelines dashboard and verify the order reverts to B above A"
        ):
            # Confirmed live (AFS Step 5 Gotcha): unpinning does NOT re-sort
            # the grid in place — the just-unpinned card stays at the top
            # until a fresh navigate/re-fetch, even though its own button
            # label flips back immediately (asserted above). Do not assert
            # order right after the unpin click — mirrors
            # test_credential_pin_unpin.py's Step 7b exactly.
            list_page.navigate()
            reverted_order = list_page.get_card_names()
            index_a = reverted_order.index(pipeline_a_name)
            index_b = reverted_order.index(pipeline_b_name)
            assert index_b < index_a, (
                f"Expected Pipeline B above Pipeline A again after unpinning + re-navigate, "
                f"got order: {reverted_order}"
            )

        with allure.step("Side-channel check — no console errors across the whole pin -> unpin -> re-navigate flow"):
            assert not console_errors, (
                f"Unexpected console errors: {[m.text for m in console_errors]}"
            )

    finally:
        with allure.step("Cleanup — delete both pipelines created for this test"):
            if pipeline_a_id is not None:
                pipeline_api.delete_pipeline(pipeline_a_id)
                logger.info("Deleted pipeline id=%s", pipeline_a_id)
            if pipeline_b_id is not None:
                pipeline_api.delete_pipeline(pipeline_b_id)
                logger.info("Deleted pipeline id=%s", pipeline_b_id)
