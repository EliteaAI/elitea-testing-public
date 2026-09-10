"""UI Tests for Elitea Pipeline Management — Phase 1A.

Tests pipeline dashboard, creation, editing, deletion, and search.

Each test that modifies pipelines uses the ``pipeline_id`` fixture so it
gets a fresh, isolated pipeline that is cleaned up automatically.

Test IDs:
    PIPE-001: Dashboard loads and displays pipelines list
    PIPE-002: Create new pipeline via UI
    PIPE-003: Edit pipeline name and description
    PIPE-004: Delete pipeline via API and verify in UI
    PIPE-005: Search and filter pipelines by name

Markers:
    - ui: requires browser
    - pipelines: pipeline-related tests
    - p0/p1: priority markers

Usage:
    cd automation
    pytest test_pipeline_management.py -v
    pytest test_pipeline_management.py -v -m p0
"""

import re
import uuid
from urllib.parse import urlparse

import allure
import pytest
from config import settings
from pages.pipeline_detail_page import PipelineDetailPage
from pages.pipeline_form_page import PipelineFormPage
from pages.pipelines_list_page import PipelinesListPage
from utils.console_errors import collect_console_errors

pytestmark = [pytest.mark.ui, pytest.mark.pipelines, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
NAVIGATION_TIMEOUT = 15000
FORM_SAVE_TIMEOUT = 15000
#: The post-delete redirect fires on the success toast's CLOSE (EliteaUI's
#: ``onCloseToast`` -> ``navigate(-1)``), not on the DELETE response, so it can
#: land several seconds after ``delete_pipeline_via_menu()`` has returned.
#: Measured on dev.elitea.ai across three in-app runs: 0.0 s / 7.1 s / 6.6 s.
#: Budget generously — an 8 s budget against a 7 s reality is a flake generator.
POST_DELETE_REDIRECT_TIMEOUT = 25000
#: How long the dashboard may take to drop a just-deleted card. The redirect
#: is a history-back, so the dashboard repaints its CACHED list first and only
#: drops the card once the list refetch lands — absence is a state it arrives
#: at, not one it starts in.
DASHBOARD_REFRESH_TIMEOUT = 15000


class TestPipelineDashboard:
    """PIPE-001: Pipeline dashboard loads and displays pipelines list."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0855_pipeline-dashboard-view-and-search.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    @pytest.mark.smoke
    def test_pipeline_dashboard_loads(self, page):
        """PIPE-001: Dashboard loads with header and search input."""
        with allure.step("Step 1 — Navigate to pipelines dashboard"):
            list_page = PipelinesListPage(page)
            list_page.navigate()

        with allure.step("Step 2 — Verify header is visible"):
            assert list_page.page_header.is_visible(), (
                "Pipelines header should be visible"
            )

        with allure.step("Step 3 — Verify search input is visible"):
            assert list_page.search_input.is_visible(), "Search input should be visible"

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0855_pipeline-dashboard-view-and-search.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0864_pipeline-creation-ui-and-api.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_pipeline_created_via_api_visible_in_dashboard(self, page, pipeline_id, pipeline_api):
        """Pipeline created via API fixture should appear in the dashboard."""
        with allure.step("Step 1 — Get pipeline name from API"):
            pipeline = pipeline_api.get_pipeline(pipeline_id)
            pipeline_name = pipeline.get("name", "")

        with allure.step("Step 2 — Navigate to pipelines dashboard"):
            list_page = PipelinesListPage(page)
            list_page.navigate()

        with allure.step("Step 3 — Verify pipeline appears in dashboard"):
            assert list_page.pipeline_exists_in_list(pipeline_name, timeout=UI_ELEMENT_TIMEOUT), (
                f"Pipeline '{pipeline_name}' should appear in the dashboard"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0855_pipeline-dashboard-view-and-search.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/pipelines/ELITEA-2024_pipeline-dashboard-view-toggle-card-vs-table.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_view_toggle_table_and_card(self, page, pipeline_id, pipeline_api):
        """Dashboard should support switching between table and card views.

        Extended for ELITEA-2024 (AFS:
        test-specs/pipelines/lextend_pipeline-dashboard-view-toggle-default-and-layout_ELITEA-2024.md)
        with default-state (Step 3) and actual-rendered-layout (Steps 5 & 7)
        assertions — the original ELITEA-0855 coverage (button visibility +
        button aria-pressed state) is unchanged.

        REPAIR 2026-09-09 (board #2118, CI run 34331579791): the test used to
        ASSUME the ambient project held at least one pipeline. The CI matrix
        project holds none, so Step 7 failed and — worse — Step 5 passed
        vacuously, because CardList.jsx's ``showEmptyOrError`` short-circuits
        BOTH the table and the card branch, making "zero cards" true of an
        empty state that mounted no table at all. The test now establishes the
        case's declared precondition itself and asserts it at Step 1.

        Fidelity — transit substitution (AFS § Fidelity Declaration): the
        precondition pipeline is created through the API (``pipeline_id``
        fixture) instead of through the UI create form, purely so the
        dashboard has content to lay out. Every value this test asserts on —
        the toggles' ``aria-pressed`` state, the ``view`` URL parameter, and
        which layout component the dashboard mounts — is produced by the live
        application in response to real clicks. The case does not specify how
        the pipeline gets there.
        """
        with allure.step("Step 1 — Navigate to pipelines dashboard with a known pipeline present"):
            pipeline_name = pipeline_api.get_pipeline(pipeline_id).get("name", "")
            list_page = PipelinesListPage(page)
            list_page.navigate()
            # Waiting, POSITIVE assertion — during the dashboard's loading
            # window both entity-card-name and empty-state-title read 0, so a
            # bare count here would be as vacuous as the Step 5 bug this
            # repair closes. 10 s, not get_card_names()'s 5 s default: 5 s is
            # exactly what expired in CI.
            assert pipeline_name in list_page.get_card_names(timeout=UI_ELEMENT_TIMEOUT), (
                f"Precondition: pipeline {pipeline_name!r} should be on the dashboard "
                "before the view toggle is exercised"
            )

        with allure.step("Step 2 — Verify view toggle buttons exist"):
            assert list_page.table_view_button.is_visible(), "Table view button should exist"
            assert list_page.card_view_button.is_visible(), "Card view button should exist"

        with allure.step("Step 3 — Verify default view is Card list view"):
            assert list_page.is_card_view_active(), (
                "Card list view should be the active/default view on fresh load"
            )
            assert not list_page.is_table_view_active(), (
                "Table view should NOT be active on fresh load"
            )

        with allure.step("Step 4 — Switch to table view"):
            list_page.switch_to_table_view()
            assert list_page.is_table_view_active(), (
                "Table view toggle should be active after switching to table view"
            )

        with allure.step("Step 5 — Verify layout actually changed to table format"):
            assert "view=table" in page.url, f"Expected ?view=table in URL, got {page.url!r}"
            assert list_page.empty_state_title.count() == 0, (
                "Dashboard must not be showing the empty state — a zero card count "
                "would then prove nothing about the table layout"
            )
            assert list_page.entity_card_name.count() == 0, (
                "No card elements (entity-card-name) should render while in table view"
            )

        with allure.step("Step 6 — Switch back to card view"):
            list_page.switch_to_card_view()
            assert list_page.is_card_view_active(), (
                "Card view toggle should be active after switching to card view"
            )

        with allure.step("Step 7 — Verify layout returned to card grid format"):
            assert "view=cards" in page.url, f"Expected ?view=cards in URL, got {page.url!r}"
            assert pipeline_name in list_page.get_card_names(timeout=UI_ELEMENT_TIMEOUT), (
                f"Pipeline {pipeline_name!r} should render as a card again after "
                "switching back to card view"
            )


class TestCreatePipeline:
    """PIPE-002: Create new pipeline via UI."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0864_pipeline-creation-ui-and-api.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    @pytest.mark.smoke
    def test_create_pipeline_via_ui(self, page, pipeline_api):
        """PIPE-002: Create a pipeline through the UI form and verify it appears."""
        pipeline_name = "autotest_create_pipe_ui"
        pipeline_desc = "Created by UI automation test"

        with allure.step("Step 1 — Navigate to create pipeline form"):
            form_page = PipelineFormPage(page)
            form_page.navigate_to_create()

        with allure.step("Step 2 — Fill pipeline name and description"):
            form_page.fill_form(
                name=pipeline_name,
                description=pipeline_desc,
            )

        with allure.step("Step 3 — Verify Save button enabled and click Save"):
            form_page.wait_for_form_validation()
            assert form_page.is_save_enabled(), (
                "Save button should be enabled after filling required fields"
            )
            form_page.click_save(timeout=FORM_SAVE_TIMEOUT)

        with allure.step("Step 4 — Verify navigation to detail page"):
            detail_page = PipelineDetailPage(page)
            detail_page.wait_for_detail_page_load()
            url_path = urlparse(page.url).path
            assert "/pipelines/all/" in url_path and "create" not in url_path, (
                f"Should navigate to pipeline detail page, got: {page.url}"
            )

        with allure.step("Step 5 — Verify pipeline name on detail page"):
            assert detail_page.get_name() == pipeline_name

        with allure.step("Step 6 — Cleanup via API"):
            pipeline_id_str = None
            try:
                pipeline_id_str = detail_page.get_pipeline_id()
                pipeline_api.delete_pipeline(int(pipeline_id_str))
            except Exception as cleanup_exc:
                print(f"[WARN] Failed to delete pipeline {pipeline_id_str}: {cleanup_exc}")

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0864_pipeline-creation-ui-and-api.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_create_pipeline_required_fields_validation(self, page):
        """Save button should be disabled when required fields are empty."""
        with allure.step("Step 1 — Navigate to create pipeline form"):
            form_page = PipelineFormPage(page)
            form_page.navigate_to_create()

        with allure.step("Step 2 — Verify Save disabled with empty fields"):
            assert not form_page.is_save_enabled(), (
                "Save should be disabled with empty required fields"
            )

        with allure.step("Step 3 — Fill only name and verify Save still disabled"):
            form_page.update_name("autotest_partial")
            form_page.wait_for_network(timeout=3000)
            assert not form_page.is_save_enabled(), (
                "Save should be disabled without description"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/pipelines/ELITEA-2020_create-pipeline-minimal.md", "onetest-ai Test Case link")
    @pytest.mark.p0
    def test_create_pipeline_minimal_via_sidebar_button(self, page, pipeline_api):
        """ELITEA-2020: Create a pipeline via the sidebar '+' control, with only
        the required Name + Description fields, and verify the resulting
        pipeline gets a unique numeric ID (URL + Information section) and
        defaults to the "base" VERSION.

        Extends TestCreatePipeline (test-specs/pipelines/lextend_create-
        pipeline-minimal-sidebar_ELITEA-2020.md) — additive to
        test_create_pipeline_via_ui, which navigates via a direct URL instead
        of the sidebar control and never asserts the Information section or
        VERSION selector.
        """
        # Name field has a 32-char cap (MAX_NAME_LENGTH, ApplicationEditForm.jsx) —
        # confirmed live: a longer name silently truncates rather than erroring.
        pipeline_name = f"autotest_pipe_min_{uuid.uuid4().hex[:8]}"
        pipeline_desc = "Automated test pipeline"

        with allure.step("Step 1 — Navigate to Pipelines dashboard"):
            list_page = PipelinesListPage(page)
            list_page.navigate()

        with allure.step("Step 2 — Click the sidebar '+' next to 'Pipeline' and verify the create form opens"):
            list_page.click_create_pipeline()
            url_path = urlparse(page.url).path
            # APP_PREFIX is "" on localhost and "/app" on deployed envs (config.py) —
            # the assertion stays exact-equality on both.
            assert url_path == f"{settings.app_prefix}/pipelines/create", (
                f"Sidebar '+' should navigate to the create form, got: {page.url}"
            )
            form_page = PipelineFormPage(page)
            form_page.wait_for_page_load()

        with allure.step("Step 3 — Fill Name field"):
            form_page.name_input.click()
            form_page.name_input.type(pipeline_name)
            assert form_page.get_name() == pipeline_name, (
                "Name field should hold the typed value"
            )

        with allure.step("Step 4 — Fill Description field"):
            form_page.description_input.click()
            form_page.description_input.type(pipeline_desc)
            assert form_page.get_description() == pipeline_desc, (
                "Description field should hold the typed value"
            )

        with allure.step("Step 5 — Verify Save button is enabled"):
            form_page.wait_for_form_validation()
            assert form_page.is_save_enabled(), (
                "Save button should be enabled once Name and Description are filled"
            )

        with allure.step("Step 6 — Click Save"):
            form_page.click_save(timeout=FORM_SAVE_TIMEOUT)

        with allure.step("Step 7 — Verify URL includes the new numeric pipeline ID"):
            detail_page = PipelineDetailPage(page)
            detail_page.wait_for_detail_page_load()
            url_path = urlparse(page.url).path
            # Anchored on both ends, with APP_PREFIX ("" locally, "/app" deployed).
            match = re.match(
                rf"^{re.escape(settings.app_prefix)}/pipelines/all/(\d+)$", url_path
            )
            assert match, f"URL should include a numeric pipeline ID, got: {page.url}"
            url_pipeline_id = match.group(1)

        pipeline_id_str = None
        try:
            with allure.step("Step 8 — Verify 'Pipeline ID:' in the Information section, numeric, matching the URL"):
                detail_page.information_section.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                pipeline_id_str = detail_page.get_pipeline_id()
                assert pipeline_id_str.isdigit(), (
                    f"Pipeline ID in the Information section should be numeric, got: {pipeline_id_str!r}"
                )
                assert pipeline_id_str == url_pipeline_id, (
                    f"Information section Pipeline ID ({pipeline_id_str}) should match "
                    f"the URL's pipeline ID ({url_pipeline_id})"
                )

            with allure.step("Step 9 — Verify VERSION selector defaults to 'base'"):
                assert detail_page.get_version_display() == "base", (
                    "VERSION selector should default to 'base' on a freshly created pipeline"
                )
        finally:
            if pipeline_id_str:
                try:
                    pipeline_api.delete_pipeline(int(pipeline_id_str))
                except Exception as cleanup_exc:
                    print(f"[WARN] Failed to delete pipeline {pipeline_id_str}: {cleanup_exc}")


class TestEditPipeline:
    """PIPE-003: Edit pipeline name and description."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0850_pipeline-edit-and-delete-operations.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_edit_pipeline_name(self, page, pipeline_id, pipeline_api):
        """Edit a pipeline's name and verify the change persists."""
        new_name = "autotest_renamed_pipe"

        with allure.step("Step 1 — Navigate to pipeline detail page"):
            detail_page = PipelineDetailPage(page)
            detail_page.navigate(pipeline_id)

        with allure.step("Step 2 — Update pipeline name"):
            detail_page.update_name(new_name)

        with allure.step("Step 3 — Save changes"):
            assert detail_page.is_save_enabled(), "Save should be enabled after name change"
            detail_page.click_save(timeout=FORM_SAVE_TIMEOUT)

        with allure.step("Step 4 — Reload and verify name persisted"):
            detail_page.reload_and_wait()
            assert detail_page.get_name() == new_name, (
                f"Pipeline name should be '{new_name}' after save"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0850_pipeline-edit-and-delete-operations.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_edit_pipeline_description(self, page, pipeline_id, pipeline_api):
        """Edit a pipeline's description and verify the change persists."""
        new_desc = "Updated by automation"

        with allure.step("Step 1 — Navigate to pipeline detail page"):
            detail_page = PipelineDetailPage(page)
            detail_page.navigate(pipeline_id)

        with allure.step("Step 2 — Update pipeline description"):
            detail_page.update_description(new_desc)

        with allure.step("Step 3 — Save changes"):
            detail_page.click_save(timeout=FORM_SAVE_TIMEOUT)

        with allure.step("Step 4 — Reload and verify description persisted"):
            detail_page.reload_and_wait()
            detail_page.wait_for_detail_page_load()
            assert detail_page.get_description() == new_desc, (
                f"Description should be '{new_desc}' after save and reload"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0851_pipeline-detail-page-configuration-and-tabs.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_pipeline_detail_page_loads(self, page, pipeline_id, pipeline_api):
        """Navigate to a pipeline's detail page and verify form fields match."""
        with allure.step("Step 1 — Get pipeline data from API"):
            pipeline = pipeline_api.get_pipeline(pipeline_id)

        with allure.step("Step 2 — Navigate to pipeline detail page"):
            detail_page = PipelineDetailPage(page)
            detail_page.navigate(pipeline_id)

        with allure.step("Step 3 — Verify form fields match API data"):
            assert detail_page.get_name() == pipeline.get("name", ""), (
                "Name should match API data"
            )
            assert detail_page.get_description() == pipeline.get("description", ""), (
                "Description should match API data"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0851_pipeline-detail-page-configuration-and-tabs.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_pipeline_has_configuration_and_history_tabs(self, page, pipeline_id):
        """Pipeline detail page shows configuration panel and history button."""
        with allure.step("Step 1 — Navigate to pipeline detail page"):
            detail_page = PipelineDetailPage(page)
            detail_page.navigate(pipeline_id)

        with allure.step("Step 2 — Verify configuration panel is visible"):
            assert detail_page.configuration_tab.is_visible(), "Configuration panel (General section) should be visible"

        with allure.step("Step 3 — Verify history button is visible"):
            assert detail_page.history_tab.is_visible(), "History icon button should be visible"


class TestDeletePipeline:
    """PIPE-004: Delete pipeline via API and verify in UI."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0850_pipeline-edit-and-delete-operations.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_delete_pipeline_via_api(self, page, pipeline_api):
        """Create a pipeline, delete via API, and verify it's gone from the UI."""
        with allure.step("Step 1 — Create pipeline via API"):
            pipeline = pipeline_api.create_pipeline(
                name="autotest_delete_api_pipe",
                description="Will be deleted via API",
            )
            pid = pipeline["id"]
            pipeline_name = "autotest_delete_api_pipe"

        try:
            with allure.step("Step 2 — Navigate to pipelines dashboard"):
                list_page = PipelinesListPage(page)
                list_page.navigate()

            with allure.step("Step 3 — Verify pipeline appears in dashboard"):
                assert list_page.pipeline_exists_in_list(pipeline_name, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Pipeline '{pipeline_name}' should appear in dashboard before deletion"
                )

            with allure.step("Step 4 — Delete pipeline via API"):
                pipeline_api.delete_pipeline(pid)

            with allure.step("Step 5 — Reload and verify pipeline removed"):
                list_page.reload_and_wait()
                assert not list_page.pipeline_exists_in_list(pipeline_name, timeout=3000), (
                    f"Pipeline '{pipeline_name}' should be gone after API deletion"
                )
        finally:
            try:
                pipeline_api.delete_pipeline(pid)
            except Exception:
                pass

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0850_pipeline-edit-and-delete-operations.md", "onetest-ai Test Case link")
    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/pipelines/ELITEA-2022_delete-pipeline.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_delete_pipeline_via_ui_menu(self, page, pipeline_api):
        """Open a pipeline from the dashboard, delete it via the three-dot
        menu, and verify the automatic redirect plus its removal.

        Extends coverage for ELITEA-2022 (test-specs/pipelines/lextend_delete-
        pipeline-via-actions-menu_ELITEA-2022.md) — Step 4 asserts that the app
        auto-redirects to the Pipelines dashboard as a direct consequence of
        the delete action.

        **The arrival path is load-bearing — do not swap Step 2 for a deep
        link.** EliteaUI's post-delete redirect is `navigate(-1)` (React Router
        history-back, fired from the success toast's close), so whether it
        fires is decided entirely by how the detail page was reached. The case
        has no navigation step between "Save" (Step 2) and "open the three-dot
        menu" (Step 3), i.e. the user it describes arrives in-app — so this
        test opens the pipeline by clicking its dashboard card. Reaching it via
        `page.goto()` instead manufactures a failure the case never describes
        (measured on dev.elitea.ai: in-app arrival redirects 3/3, deep-link
        arrival 0/3).

        Substitution declared (transit only): the pipeline itself is seeded via
        `pipeline_api.create_pipeline()`, because the case lists the pipeline's
        existence as a *precondition* and UI creation is covered by ELITEA-2020
        / ELITEA-2021. The case's own observable — the redirect — is still
        produced by the system through the real UI delete flow.

        `EliteaAI/elitea-testing-public#1332` stays a real, OPEN product bug:
        the redirect genuinely no-ops for a deep-link arrival (bookmarks,
        shared links, browser-restored tabs). It is simply not this case's
        scenario, so it is neither asserted nor masked here.
        """
        pipeline_name = f"autotest_delete_ui_pipe_{uuid.uuid4().hex[:8]}"

        with allure.step("Step 1 — Create pipeline via API (precondition)"):
            pipeline = pipeline_api.create_pipeline(
                name=pipeline_name,
                description="Will be deleted via UI",
            )
            pid = pipeline["id"]

        try:
            with allure.step(
                "Step 2 — Open the pipeline from the Pipelines dashboard (in-app arrival)"
            ):
                list_page = PipelinesListPage(page)
                list_page.navigate()
                list_page.open_pipeline_by_name(pipeline_name)
                detail_page = PipelineDetailPage(page)
                detail_page.wait_for_detail_page_load()

            with allure.step("Step 3 — Delete pipeline via three-dot menu"):
                detail_page.delete_pipeline_via_menu(timeout=NAVIGATION_TIMEOUT)

            with allure.step(
                "Step 4 — Verify the app auto-redirects to the Pipelines dashboard"
            ):
                page.wait_for_url(
                    lambda url: urlparse(url).path.rstrip("/").endswith("/pipelines/all"),
                    timeout=POST_DELETE_REDIRECT_TIMEOUT,
                )

            with allure.step("Step 5 — Verify pipeline removed from dashboard"):
                # Waiting, non-vacuous absence check — see
                # PipelinesListPage.wait_for_pipeline_absent(). It is scoped to
                # the rendered grid on purpose: the case's Step 7 observable is
                # the LIST, and `pipeline_exists_in_list()`'s page-wide
                # `text="…"` match cannot express it here, because the delete
                # success toast ("The <name> pipeline has been successfully
                # deleted.") also carries the name and is still on screen at
                # this point (evidenced live on dev.elitea.ai, board #2139).
                list_page.wait_for_pipeline_absent(
                    pipeline_name, timeout=DASHBOARD_REFRESH_TIMEOUT
                )
        finally:
            try:
                pipeline_api.delete_pipeline(pid)
            except Exception:
                pass


class TestSearchPipeline:
    """PIPE-005: Search and filter pipelines by name."""

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0855_pipeline-dashboard-view-and-search.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_search_pipeline_by_name(self, page, pipeline_id, pipeline_api):
        """Search for a pipeline by name on the dashboard."""
        with allure.step("Step 1 — Get pipeline name from API"):
            pipeline = pipeline_api.get_pipeline(pipeline_id)
            pipeline_name = pipeline.get("name", "")

        with allure.step("Step 2 — Navigate to pipelines dashboard"):
            list_page = PipelinesListPage(page)
            list_page.navigate()

        with allure.step("Step 3 — Search for pipeline by name"):
            list_page.search_and_wait_for_results(pipeline_name)

        with allure.step("Step 4 — Verify pipeline appears in search results"):
            assert list_page.pipeline_exists_in_list(pipeline_name, timeout=UI_ELEMENT_TIMEOUT), (
                f"Pipeline '{pipeline_name}' should appear in search results"
            )

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/elitea-platform/pipelines/ELITEA-0855_pipeline-dashboard-view-and-search.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_search_pipeline_no_results(self, page):
        """Searching for a non-existent pipeline should show no results."""
        with allure.step("Step 1 — Navigate to pipelines dashboard"):
            list_page = PipelinesListPage(page)
            list_page.navigate()

        with allure.step("Step 2 — Search for non-existent pipeline"):
            list_page.search_and_wait_for_results("zzzz_nonexistent_pipeline_12345")

        with allure.step("Step 3 — Verify no results found"):
            assert not list_page.pipeline_exists_in_list(
                "zzzz_nonexistent_pipeline_12345", timeout=3000,
            ), "Non-existent pipeline should not appear in results"

    @allure.issue("https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/pipelines/ELITEA-2023_pipeline-dashboard-search.md", "onetest-ai Test Case link")
    @pytest.mark.p1
    def test_search_placeholder_and_dashboard_grid_filters_and_clears(self, page, pipeline_api):
        """ELITEA-2023: search filters the dashboard grid (not just the
        suggestions popover) and Clear restores the full, unfiltered list.

        Unlike ``test_search_pipeline_by_name``/``test_search_pipeline_no_results``
        above (which exercise the suggestions popover via the old fill-only
        ``search()``), this asserts the actual grid-narrowing filter, which
        activates only on Enter — see ``PipelinesListPage.search()`` docstring.

        REPAIR 2026-09-10 (board #2119, CI run 34331579791 / DEV Stable #114):
        the test used to ESTABLISH its matching ("YAML") pipeline via the API
        but HARVEST the non-matching one out of ambient project state with
        ``next(row for row in pipeline_api.list_pipelines() ...)``. The CI
        matrix project holds no pipeline of its own, so the generator was
        empty and the test died ``StopIteration`` three steps before anything
        about search was asserted. Both halves of the precondition are now
        created by the test itself, and Step 2 asserts them on the rendered
        grid — so this class of failure now reports AT the precondition,
        naming it. Nothing in the product changed; the spec is correct on a
        project holding only these two pipelines and on one holding hundreds.
        (Same class as the sibling ELITEA-2024 repair, board #2118.)

        Fidelity — transit substitution (AFS § Fidelity Declaration): both
        precondition pipelines are created through ``pipeline_api`` instead of
        the UI create form, purely so the dashboard has known content to
        filter. The case's Preconditions section states only that the
        dashboard *contains* a "YAML" pipeline, not how it got there, and
        pipeline creation is not this case's subject. Every value asserted on
        — which cards the grid renders after Enter and after Clear, whether
        the empty state mounts, the input's value and placeholder, the URL —
        is produced by the live application in response to real typing, a real
        Enter keypress and a real click. Nothing is fabricated or injected.
        """
        console_errors = collect_console_errors(page)

        # ONE suffix for both, so a pair leaked by a crashed run is greppable
        # as a unit. Neither NAME nor DESCRIPTION of the non-matching pipeline
        # may contain "yaml": the backend `query` matches description as well
        # as name (live-proven 2026-09-10, AFS § Live Findings F3), so a
        # "YAML" description would put it back in the filtered grid and break
        # the Step 5 absence assertion.
        suffix = uuid.uuid4().hex[:6]
        yaml_pipeline_name = f"autotest_YAML_search_{suffix}"
        non_matching_name = f"autotest_nomatch_srch_{suffix}"
        precondition_description = "ELITEA-2023 dashboard search filter and clear"
        yaml_pipeline_id = None
        non_matching_id = None

        try:
            with allure.step(
                "Step 1 — Create both search preconditions via the API: one "
                "pipeline whose name contains 'YAML' and one that matches "
                "neither by name nor by description"
            ):
                yaml_pipeline_id = pipeline_api.create_pipeline(
                    name=yaml_pipeline_name,
                    description=precondition_description,
                )["id"]
                non_matching_id = pipeline_api.create_pipeline(
                    name=non_matching_name,
                    description=precondition_description,
                )["id"]

            with allure.step(
                "Step 2 — Navigate to Pipelines dashboard; verify the full list "
                "loads with BOTH created pipelines present"
            ):
                list_page = PipelinesListPage(page)
                list_page.navigate()

                # Waiting, POSITIVE assertion, and the first thing the browser
                # is asked — during the dashboard's loading window both
                # entity-card-name and empty-state-title read 0, so a bare
                # count here would be vacuous. 10 s, not get_card_names()'s
                # 5 s default: 5 s is exactly what expired in CI. The grid
                # sorts created_at desc and pages at 20, so the two
                # just-created pipelines are always on page 1.
                baseline_names = list_page.get_card_names(timeout=UI_ELEMENT_TIMEOUT)
                assert yaml_pipeline_name in baseline_names, (
                    f"Precondition: matching pipeline '{yaml_pipeline_name}' should be "
                    f"on the dashboard before the search is exercised, got {baseline_names}"
                )
                assert non_matching_name in baseline_names, (
                    f"Precondition: non-matching pipeline '{non_matching_name}' should be "
                    f"on the dashboard before the search is exercised, got {baseline_names}"
                )

            with allure.step(
                "Step 3 — Verify the search textbox is visible and its placeholder "
                "reads \"Let's find something amazing!\""
            ):
                assert list_page.search_input.is_visible(), (
                    "Search textbox should be visible on the Pipelines dashboard"
                )
                placeholder = list_page.search_input.get_attribute("placeholder")
                assert placeholder == "Let's find something amazing!", (
                    f"Search placeholder should read \"Let's find something amazing!\", got {placeholder!r}"
                )

            with allure.step("Step 4 — Type 'YAML' into the search box and press Enter"):
                list_page.search("YAML")
                assert list_page.search_input.input_value() == "YAML", (
                    "Search input should contain 'YAML' after typing"
                )

            with allure.step(
                "Step 5 — Verify the dashboard grid narrows to only pipelines "
                "matching 'YAML' (both directions)"
            ):
                # get_card_names(), not pipeline_exists_in_list(): the active
                # search highlights "YAML" by splitting the card name across
                # nested <span> fragments, and Playwright's exact text="..."
                # locator (used by pipeline_exists_in_list) does not match
                # the parent's concatenated text in that split-node case
                # (confirmed live, ELITEA-2023 implementer Phase 2 — see
                # PipelinesListPage.get_card_names() docstring).
                #
                # Ordering is load-bearing: the waiting POSITIVE assertion
                # first, so the absence assertion below cannot pass on a grid
                # that simply never rendered.
                filtered_names = list_page.get_card_names(timeout=UI_ELEMENT_TIMEOUT)
                assert yaml_pipeline_name in filtered_names, (
                    f"Filtered grid should still show matching pipeline '{yaml_pipeline_name}', "
                    f"got {filtered_names}"
                )
                # Explicit empty-state guard: CardList.jsx's showEmptyOrError
                # short-circuits BOTH the table and the card branch, so "no
                # card matched" and "nothing mounted" are the same DOM. This
                # names the real failure mode instead of reporting a missing
                # pipeline (#2118 precedent).
                assert list_page.empty_state_title.count() == 0, (
                    "Dashboard must not be showing the empty state while a match is expected"
                )
                assert non_matching_name not in filtered_names, (
                    f"Filtered grid should hide non-matching pipeline '{non_matching_name}', "
                    f"got {filtered_names}"
                )
                # ⚠️ Do NOT strengthen this into "every visible card name
                # contains 'yaml'". It looks like the case's wording and it is
                # wrong: the backend matches DESCRIPTION too, so a pipeline
                # with a "YAML"-free name and a "YAML" description
                # legitimately appears — that universal is a false-red
                # generator on any project with ambient data (AFS § Vacuity
                # Audit V4).

            with allure.step("Step 6 — Click the search Clear (X) icon"):
                list_page.clear_search()
                assert list_page.search_input.input_value() == "", (
                    "Search input should be empty after clicking Clear"
                )

            with allure.step(
                "Step 7 — Verify the full pipeline list is restored and the "
                "URL stays on /pipelines/all"
            ):
                restored_names = list_page.get_card_names(timeout=UI_ELEMENT_TIMEOUT)
                assert yaml_pipeline_name in restored_names, (
                    f"Cleared grid should show '{yaml_pipeline_name}' again, got {restored_names}"
                )
                # The assertion that proves the filter was actually RELEASED:
                # this name was provably absent from the grid one step ago.
                assert non_matching_name in restored_names, (
                    f"Cleared grid should show previously-hidden '{non_matching_name}' again, "
                    f"got {restored_names}"
                )
                assert list_page.empty_state_title.count() == 0, (
                    "Dashboard must not be showing the empty state after clearing the search"
                )
                # Strictly ">" rather than "== baseline": this runs against a
                # shared DEV project, where strict equality would flake on any
                # concurrent create/delete (#1082 class). "restored ⊋ filtered"
                # holds by construction on ANY project, because the
                # non-matching pipeline is in one and not the other.
                assert len(restored_names) > len(filtered_names), (
                    f"Cleared grid should hold more cards than the filtered grid: "
                    f"restored={len(restored_names)} filtered={len(filtered_names)} "
                    f"baseline={len(baseline_names)}"
                )
                parsed_url = urlparse(page.url)
                assert parsed_url.path.endswith("/pipelines/all"), (
                    f"Page should stay on /pipelines/all after Clear, got {page.url!r}"
                )

            with allure.step("Step 8 — Side-channel check (Axis 2): no console errors across the flow"):
                # No URL filter is applied: this flow performs no project
                # switch, so #1971 is not expected. collect_console_errors()
                # annotates each message with the failing resource's URL, so a
                # background-noise occurrence arrives diagnosable rather than
                # anonymous (.agents/testing.md § Unconfirmed).
                assert not console_errors, f"Unexpected console errors: {console_errors}"
        finally:
            with allure.step("Cleanup — delete both precondition pipelines"):
                # Guarded so the second delete still runs if the first raises.
                try:
                    if yaml_pipeline_id is not None:
                        pipeline_api.delete_pipeline(yaml_pipeline_id)
                finally:
                    if non_matching_id is not None:
                        pipeline_api.delete_pipeline(non_matching_id)


class TestPipelineIsolation:
    """Verify test isolation -- each test gets a clean pipeline."""

    @pytest.mark.p0
    @pytest.mark.smoke
    def test_fixture_creates_fresh_pipeline(self, page, pipeline_id):
        """Verify the pipeline_id fixture produces a valid pipeline."""
        with allure.step("Step 1 — Navigate to pipeline detail page"):
            detail_page = PipelineDetailPage(page)
            detail_page.navigate(pipeline_id)

        with allure.step("Step 2 — Verify pipeline name starts with 'autotest_'"):
            assert detail_page.get_name().startswith("autotest_"), (
                "Fixture-created pipeline name should start with 'autotest_'"
            )

        with allure.step("Step 3 — Verify pipeline ID matches"):
            assert detail_page.get_pipeline_id() == str(pipeline_id)

    @pytest.mark.p1
    @pytest.mark.smoke
    def test_fixture_cleanup_cycle(self, pipeline_api):
        """Verify that creating and deleting pipelines via the API works."""
        with allure.step("Step 1 — Create pipeline via API"):
            pipeline = pipeline_api.create_pipeline(
                name="autotest_cleanup_cycle_pipe",
                description="Smoke test for cleanup",
            )
            pid = pipeline["id"]

        with allure.step("Step 2 — Verify pipeline exists"):
            pipeline = pipeline_api.get_pipeline(pid)
            assert pipeline is not None, f"Pipeline {pid} should exist after creation"

        with allure.step("Step 3 — Delete pipeline via API"):
            pipeline_api.delete_pipeline(pid)

        with allure.step("Step 4 — Verify pipeline is deleted"):
            try:
                pipeline_api.get_pipeline(pid)
                assert False, f"Pipeline {pid} should have been deleted"
            except Exception:
                pass  # Expected: pipeline no longer exists
