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
from pages.pipeline_detail_page import PipelineDetailPage
from pages.pipeline_form_page import PipelineFormPage
from pages.pipelines_list_page import PipelinesListPage

pytestmark = [pytest.mark.ui, pytest.mark.pipelines]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
NAVIGATION_TIMEOUT = 15000
FORM_SAVE_TIMEOUT = 15000


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
    @pytest.mark.p1
    def test_view_toggle_table_and_card(self, page):
        """Dashboard should support switching between table and card views."""
        with allure.step("Step 1 — Navigate to pipelines dashboard"):
            list_page = PipelinesListPage(page)
            list_page.navigate()

        with allure.step("Step 2 — Verify view toggle buttons exist"):
            assert list_page.table_view_button.is_visible(), "Table view button should exist"
            assert list_page.card_view_button.is_visible(), "Card view button should exist"

        with allure.step("Step 3 — Switch to table view"):
            list_page.switch_to_table_view()
            assert list_page.is_table_view_active(), (
                "Table view toggle should be active after switching to table view"
            )

        with allure.step("Step 4 — Switch back to card view"):
            list_page.switch_to_card_view()
            assert list_page.is_card_view_active(), (
                "Card view toggle should be active after switching to card view"
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
            assert url_path == "/pipelines/create", (
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
            match = re.match(r"^/pipelines/all/(\d+)$", url_path)
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
            detail_page.dismiss_banner_if_present()

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
            detail_page.dismiss_banner_if_present()

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
            detail_page.dismiss_banner_if_present()

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
    @pytest.mark.p1
    def test_delete_pipeline_via_ui_menu(self, page, pipeline_api):
        """Create a pipeline, delete via the UI three-dot menu, and verify removal."""
        with allure.step("Step 1 — Create pipeline via API"):
            pipeline = pipeline_api.create_pipeline(
                name="autotest_delete_ui_pipe",
                description="Will be deleted via UI",
            )
            pid = pipeline["id"]

        try:
            with allure.step("Step 2 — Navigate to pipeline detail page"):
                detail_page = PipelineDetailPage(page)
                detail_page.navigate(pid)
                detail_page.dismiss_banner_if_present()

            with allure.step("Step 3 — Delete pipeline via three-dot menu"):
                detail_page.delete_pipeline_via_menu(timeout=NAVIGATION_TIMEOUT)

            with allure.step("Step 4 — Verify pipeline removed from dashboard"):
                list_page = PipelinesListPage(page)
                list_page.navigate()
                assert not list_page.pipeline_exists_in_list("autotest_delete_ui_pipe", timeout=3000), (
                    "Pipeline 'autotest_delete_ui_pipe' should be gone after UI deletion"
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
        """
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)

        with allure.step("Step 1 — Create a pipeline whose name contains 'YAML' via API"):
            yaml_pipeline_name = f"autotest_YAML_search_{uuid.uuid4().hex[:6]}"
            pipeline = pipeline_api.create_pipeline(
                name=yaml_pipeline_name,
                description="ELITEA-2023 dashboard search filter/clear test",
            )
            pipeline_id = pipeline["id"]

        try:
            with allure.step(
                "Step 2 — Navigate to Pipelines dashboard; verify full list loads "
                "including the 'YAML' pipeline and a non-matching pipeline"
            ):
                existing_rows = pipeline_api.list_pipelines().get("rows", [])
                non_matching_name = next(
                    row["name"]
                    for row in existing_rows
                    if "yaml" not in row.get("name", "").lower()
                )

                list_page = PipelinesListPage(page)
                list_page.navigate()

                assert list_page.pipeline_exists_in_list(yaml_pipeline_name, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Newly created pipeline '{yaml_pipeline_name}' should be visible on the dashboard"
                )
                assert list_page.pipeline_exists_in_list(non_matching_name, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Pre-existing pipeline '{non_matching_name}' should be visible on the dashboard"
                )

            with allure.step(
                "Step 3 — Verify the search textbox placeholder reads "
                "\"Let's find something amazing!\""
            ):
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
                filtered_names = list_page.get_card_names(timeout=UI_ELEMENT_TIMEOUT)
                assert yaml_pipeline_name in filtered_names, (
                    f"Filtered grid should still show matching pipeline '{yaml_pipeline_name}', "
                    f"got {filtered_names}"
                )
                assert non_matching_name not in filtered_names, (
                    f"Filtered grid should hide non-matching pipeline '{non_matching_name}', "
                    f"got {filtered_names}"
                )

            with allure.step("Step 6 — Click the search Clear (X) icon"):
                list_page.clear_search()
                assert list_page.search_input.input_value() == "", (
                    "Search input should be empty after clicking Clear"
                )

            with allure.step(
                "Step 7 — Verify the full pipeline list is restored and the "
                "URL stays on /pipelines/all"
            ):
                assert list_page.pipeline_exists_in_list(yaml_pipeline_name, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Cleared grid should show '{yaml_pipeline_name}' again"
                )
                assert list_page.pipeline_exists_in_list(non_matching_name, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Cleared grid should show previously-hidden '{non_matching_name}' again"
                )
                parsed_url = urlparse(page.url)
                assert parsed_url.path.endswith("/pipelines/all"), (
                    f"Page should stay on /pipelines/all after Clear, got {page.url!r}"
                )

            with allure.step("Side-channel check (Axis 2) — no console errors across the flow"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            pipeline_api.delete_pipeline(pipeline_id)


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
