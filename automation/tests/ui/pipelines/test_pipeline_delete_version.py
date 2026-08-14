"""UI test — Pipeline: Delete Pipeline Version — Falls Back to Base.

TMS: ELITEA-2003
(test-specs/pipelines/l2_delete-pipeline-version-falls-back-to-base_ELITEA-2003.md)

Saves a non-base pipeline version ("ver_to_delete") via "Save As Version",
deletes it via the three-dot menu's VERSION-group "Delete" item, and
verifies the pipeline automatically falls back to and displays the "base"
version — VERSION selector, URL version-id segment, and Information-panel
Version ID all agree.

Test-data strategy: the pre-existing ``pipeline_id`` fixture (data_fixtures.py)
creates a dedicated, uniquely-named, zero-node pipeline per test and deletes
it afterwards — same precedent as the sibling ``test_pipeline_create_version.py``
/ELITEA-2002. No custom setup/teardown needed (Hard Rule 7 — reuse before
create).

Version-management methods (``open_save_as_version_dialog``,
``confirm_new_version``, ``open_version_selector``,
``is_version_option_visible``, ``get_version_option_count``,
``close_versions_menu``, ``get_version_id``) are reused verbatim from
ELITEA-2002. New ``PipelineDetailPage`` methods added for this case:
``open_delete_version_dialog``, ``confirm_delete_version``,
``wait_for_fallback_to_base`` — drive the three-dot menu's VERSION-group
"Delete" item and its (non-typing) confirm modal, distinct from
``delete_pipeline_via_menu``'s PIPELINE-group "Delete pipeline" flow.

Known defect (non-blocking, does not affect this test's assertions):
confirming the deletion triggers one transient, visible 400 on the
just-deleted version's own endpoint before the fallback to "base" settles
— EliteaAI/elitea-testing-public#1330. The FINAL state (Step 6) is
unaffected in every run; this test asserts final state, not
console/network cleanliness across the whole flow, per
``.agents/testing.md`` § Merge gate's sanctioned-RED guidance for isolated,
non-blocking, ticketed observations.
"""

from urllib.parse import urlparse

import allure
import pytest

from tests.ui.pipelines.helpers import _navigate_to_detail

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
VERSION_NAME = "ver_to_delete"
EXPECTED_CONFIRM_MESSAGE = (
    f"Are you sure to delete the {VERSION_NAME} version? It can't be restored."
)


def _url_version_id(page) -> str:
    """Read the version-id path segment from the current URL (ignoring any
    query string, e.g. the transient ``isFromCreation=true`` param)."""
    return urlparse(page.url).path.rstrip("/").split("/")[-1]


def test_delete_pipeline_version_falls_back_to_base(page, pipeline_id):
    """Deleting a non-base version via the three-dot menu removes it from
    the VERSION dropdown and the pipeline automatically falls back to
    "base" — VERSION selector, URL, and Information panel all agree."""
    with allure.step(
        "Step 1 — Save the current (base) state as a new version "
        f"{VERSION_NAME!r} via 'Save As Version'"
    ):
        pipeline_page = _navigate_to_detail(page, pipeline_id)
        assert pipeline_page.get_version_display() == "base", (
            "A freshly created pipeline should load showing its 'base' version"
        )
        base_version_id = pipeline_page.get_version_id()

        pipeline_page.open_save_as_version_dialog(timeout=UI_ELEMENT_TIMEOUT)
        pipeline_page.confirm_new_version(VERSION_NAME, timeout=NAVIGATION_TIMEOUT)

        assert pipeline_page.get_version_display() == VERSION_NAME, (
            f"VERSION selector should show {VERSION_NAME!r} after Save As Version"
        )
        ver_to_delete_id = pipeline_page.get_version_id()
        assert ver_to_delete_id != base_version_id, (
            "The new version should have gotten its own, distinct version id"
        )

        pipeline_page.open_version_selector()
        assert pipeline_page.is_version_option_visible(VERSION_NAME, timeout=UI_ELEMENT_TIMEOUT), (
            f"VERSION dropdown should list the new {VERSION_NAME!r} version"
        )
        assert pipeline_page.is_version_option_visible("base", timeout=UI_ELEMENT_TIMEOUT), (
            "VERSION dropdown should still list 'base' alongside the new version"
        )
        pipeline_page.close_versions_menu()

    with allure.step(
        f"Step 2 — Confirm the app is now on {VERSION_NAME!r} — selector, "
        "URL, and Information panel all agree on the new version's id"
    ):
        assert pipeline_page.get_version_display() == VERSION_NAME, (
            f"VERSION selector should still read {VERSION_NAME!r}"
        )
        assert pipeline_page.get_version_id() == ver_to_delete_id, (
            "Information panel's Version ID should match the version just created"
        )
        assert _url_version_id(page) == ver_to_delete_id, (
            "URL's version-id path segment should match the version just created"
        )

    with allure.step(
        'Step 3 — Open the three-dot menu and click "Delete" under the '
        "VERSION group; verify the confirmation dialog and its message"
    ):
        pipeline_page.open_delete_version_dialog(timeout=UI_ELEMENT_TIMEOUT)
        assert pipeline_page.delete_confirm_dialog.is_visible(), (
            "Delete confirmation dialog should be visible after clicking "
            "the VERSION-group 'Delete' menu item"
        )
        assert pipeline_page.delete_confirm_message.text_content().strip() == (
            EXPECTED_CONFIRM_MESSAGE
        ), "Confirmation dialog message should name the version being deleted"

    with allure.step(
        "Step 4 — Confirm deletion in the dialog; the DELETE request "
        "returns 200"
        # Known defect #1330: a stale GET on this same version id fires a
        # transient, visible 400 as a side effect of this flow, before the
        # fallback to 'base' settles (Step 6). Non-blocking, ticketed —
        # not asserted against here; see module docstring.
    ):
        with page.expect_response(
            lambda resp: (
                resp.request.method == "DELETE"
                and "/version/prompt_lib/" in resp.url
                and resp.url.rstrip("/").endswith(ver_to_delete_id)
            ),
            timeout=UI_ELEMENT_TIMEOUT,
        ) as response_info:
            pipeline_page.confirm_delete_version(timeout=UI_ELEMENT_TIMEOUT)
        delete_response = response_info.value
        assert delete_response.status == 200, (
            f"Expected the version-delete request ({delete_response.url}) "
            f"to return 200, got {delete_response.status}"
        )

    with allure.step(
        f"Step 5 — Open the VERSION dropdown again; {VERSION_NAME!r} no "
        "longer appears, only 'base' remains"
    ):
        pipeline_page.open_version_selector()
        assert pipeline_page.get_version_option_count(VERSION_NAME) == 0, (
            f"{VERSION_NAME!r} should no longer be an option after deletion"
        )
        assert pipeline_page.is_version_option_visible("base", timeout=UI_ELEMENT_TIMEOUT), (
            "'base' should remain the only option in the VERSION dropdown"
        )
        pipeline_page.close_versions_menu()

    with allure.step(
        "Step 6 — Verify the pipeline has fallen back to 'base' — VERSION "
        "selector, URL, and Information panel all agree on the original "
        "base version's id"
    ):
        settled_base_id = pipeline_page.wait_for_fallback_to_base(timeout=NAVIGATION_TIMEOUT)
        assert pipeline_page.get_version_display() == "base", (
            "VERSION selector should read 'base' after the deleted "
            "version's fallback"
        )
        assert settled_base_id == base_version_id, (
            "The pipeline should fall back to the SAME base version id it "
            "started on, not a new one"
        )
        assert _url_version_id(page) == base_version_id, (
            "URL's version-id path segment should match the original base id"
        )
