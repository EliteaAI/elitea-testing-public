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

from urllib.parse import urlparse

import pytest
from pages.pipelines_list_page import PipelinesListPage
from pages.pipeline_form_page import PipelineFormPage
from pages.pipeline_detail_page import PipelineDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.pipelines]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10000
NAVIGATION_TIMEOUT = 15000
FORM_SAVE_TIMEOUT = 15000


class TestPipelineDashboard:
    """PIPE-001: Pipeline dashboard loads and displays pipelines list."""

    @pytest.mark.p0
    @pytest.mark.smoke
    def test_pipeline_dashboard_loads(self, page):
        """PIPE-001: Dashboard loads with header and search input."""
        list_page = PipelinesListPage(page)
        list_page.navigate()

        # Header "Pipelines" should be visible
        assert list_page.page_header.is_visible(), (
            "Pipelines header should be visible"
        )

        # Search input should be present
        assert list_page.search_input.is_visible(), "Search input should be visible"

    @pytest.mark.p1
    def test_pipeline_created_via_api_visible_in_dashboard(self, page, pipeline_id, pipeline_api):
        """Pipeline created via API fixture should appear in the dashboard."""
        pipeline = pipeline_api.get_pipeline(pipeline_id)
        pipeline_name = pipeline.get("name", "")

        list_page = PipelinesListPage(page)
        list_page.navigate()

        assert list_page.pipeline_exists_in_list(pipeline_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"Pipeline '{pipeline_name}' should appear in the dashboard"
        )

    @pytest.mark.p1
    def test_view_toggle_table_and_card(self, page):
        """Dashboard should support switching between table and card views."""
        list_page = PipelinesListPage(page)
        list_page.navigate()

        assert list_page.table_view_button.is_visible(), "Table view button should exist"
        assert list_page.card_view_button.is_visible(), "Card view button should exist"

        # Switch to table view and verify it became active
        list_page.switch_to_table_view()
        assert list_page.is_table_view_active(), (
            "Table view toggle should be active after switching to table view"
        )

        # Switch back to card view and verify it became active
        list_page.switch_to_card_view()
        assert list_page.is_card_view_active(), (
            "Card view toggle should be active after switching to card view"
        )


class TestCreatePipeline:
    """PIPE-002: Create new pipeline via UI."""

    @pytest.mark.p0
    @pytest.mark.smoke
    def test_create_pipeline_via_ui(self, page, pipeline_api):
        """PIPE-002: Create a pipeline through the UI form and verify it appears."""
        pipeline_name = "autotest_create_pipe_ui"
        pipeline_desc = "Created by UI automation test"

        form_page = PipelineFormPage(page)
        form_page.navigate_to_create()

        form_page.fill_form(
            name=pipeline_name,
            description=pipeline_desc,
        )

        # Save should become enabled
        form_page.wait_for_form_validation()
        assert form_page.is_save_enabled(), (
            "Save button should be enabled after filling required fields"
        )
        form_page.click_save(timeout=FORM_SAVE_TIMEOUT)

        # Wait for the SPA to navigate to the pipeline detail page
        detail_page = PipelineDetailPage(page)
        detail_page.wait_for_detail_page_load()
        url_path = urlparse(page.url).path
        assert "/app/pipelines/all/" in url_path and "create" not in url_path, (
            f"Should navigate to pipeline detail page, got: {page.url}"
        )

        # Verify the name on the detail page
        assert detail_page.get_name() == pipeline_name

        # Cleanup via API
        pipeline_id_str = None
        try:
            pipeline_id_str = detail_page.get_pipeline_id()
            pipeline_api.delete_pipeline(int(pipeline_id_str))
        except Exception as cleanup_exc:
            print(f"[WARN] Failed to delete pipeline {pipeline_id_str}: {cleanup_exc}")

    @pytest.mark.p1
    def test_create_pipeline_required_fields_validation(self, page):
        """Save button should be disabled when required fields are empty."""
        form_page = PipelineFormPage(page)
        form_page.navigate_to_create()

        # With empty fields, Save should be disabled
        assert not form_page.is_save_enabled(), (
            "Save should be disabled with empty required fields"
        )

        # Fill only name — still missing description
        form_page.update_name("autotest_partial")
        form_page.wait_for_network(timeout=3000)
        assert not form_page.is_save_enabled(), (
            "Save should be disabled without description"
        )


class TestEditPipeline:
    """PIPE-003: Edit pipeline name and description."""

    @pytest.mark.p1
    def test_edit_pipeline_name(self, page, pipeline_id, pipeline_api):
        """Edit a pipeline's name and verify the change persists."""
        new_name = "autotest_renamed_pipe"

        detail_page = PipelineDetailPage(page)
        detail_page.navigate(pipeline_id)
        detail_page.dismiss_banner_if_present()

        # Use update_name method
        detail_page.update_name(new_name)

        assert detail_page.is_save_enabled(), "Save should be enabled after name change"
        detail_page.click_save(timeout=FORM_SAVE_TIMEOUT)

        # Reload and verify
        detail_page.reload_and_wait()
        assert detail_page.get_name() == new_name, (
            f"Pipeline name should be '{new_name}' after save"
        )

    @pytest.mark.p1
    def test_edit_pipeline_description(self, page, pipeline_id, pipeline_api):
        """Edit a pipeline's description and verify the change persists."""
        new_desc = "Updated by automation"

        detail_page = PipelineDetailPage(page)
        detail_page.navigate(pipeline_id)
        detail_page.dismiss_banner_if_present()

        # Use update_description method
        detail_page.update_description(new_desc)

        detail_page.click_save(timeout=FORM_SAVE_TIMEOUT)

        detail_page.reload_and_wait()
        detail_page.wait_for_detail_page_load()
        assert detail_page.get_description() == new_desc, (
            f"Description should be '{new_desc}' after save and reload"
        )

    @pytest.mark.p1
    def test_pipeline_detail_page_loads(self, page, pipeline_id, pipeline_api):
        """Navigate to a pipeline's detail page and verify form fields match."""
        pipeline = pipeline_api.get_pipeline(pipeline_id)

        detail_page = PipelineDetailPage(page)
        detail_page.navigate(pipeline_id)

        assert detail_page.get_name() == pipeline.get("name", ""), (
            "Name should match API data"
        )
        assert detail_page.get_description() == pipeline.get("description", ""), (
            "Description should match API data"
        )

    @pytest.mark.p1
    def test_pipeline_has_configuration_and_history_tabs(self, page, pipeline_id):
        """Pipeline detail page shows configuration panel and history button.

        Release 2.0.1: tab-based navigation was replaced with an always-visible
        left configuration panel and a 'view run history' icon button.
        """
        detail_page = PipelineDetailPage(page)
        detail_page.navigate(pipeline_id)
        detail_page.dismiss_banner_if_present()

        assert detail_page.configuration_tab.is_visible(), "Configuration panel (General section) should be visible"
        assert detail_page.history_tab.is_visible(), "History icon button should be visible"


class TestDeletePipeline:
    """PIPE-004: Delete pipeline via API and verify in UI."""

    @pytest.mark.p1
    def test_delete_pipeline_via_api(self, page, pipeline_api):
        """Create a pipeline, delete via API, and verify it's gone from the UI."""
        pipeline = pipeline_api.create_pipeline(
            name="autotest_delete_api_pipe",
            description="Will be deleted via API",
        )
        pid = pipeline["id"]
        pipeline_name = "autotest_delete_api_pipe"

        try:
            list_page = PipelinesListPage(page)
            list_page.navigate()

            # Verify it appears in the UI
            assert list_page.pipeline_exists_in_list(pipeline_name, timeout=UI_ELEMENT_TIMEOUT), (
                f"Pipeline '{pipeline_name}' should appear in dashboard before deletion"
            )

            # Delete via API
            pipeline_api.delete_pipeline(pid)

            # Reload and verify gone from UI
            list_page.reload_and_wait()

            assert not list_page.pipeline_exists_in_list(pipeline_name, timeout=3000), (
                f"Pipeline '{pipeline_name}' should be gone after API deletion"
            )
        finally:
            try:
                pipeline_api.delete_pipeline(pid)
            except Exception:
                pass

    @pytest.mark.p1
    def test_delete_pipeline_via_ui_menu(self, page, pipeline_api):
        """Create a pipeline, delete via the UI three-dot menu, and verify removal."""
        pipeline = pipeline_api.create_pipeline(
            name="autotest_delete_ui_pipe",
            description="Will be deleted via UI",
        )
        pid = pipeline["id"]

        try:
            detail_page = PipelineDetailPage(page)
            detail_page.navigate(pid)
            detail_page.dismiss_banner_if_present()

            detail_page.delete_pipeline_via_menu(timeout=NAVIGATION_TIMEOUT)

            # After delete, navigate to pipelines list and verify absence
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

    @pytest.mark.p1
    def test_search_pipeline_by_name(self, page, pipeline_id, pipeline_api):
        """Search for a pipeline by name on the dashboard."""
        pipeline = pipeline_api.get_pipeline(pipeline_id)
        pipeline_name = pipeline.get("name", "")

        list_page = PipelinesListPage(page)
        list_page.navigate()

        # Search for the pipeline
        list_page.search_and_wait_for_results(pipeline_name)

        assert list_page.pipeline_exists_in_list(pipeline_name, timeout=UI_ELEMENT_TIMEOUT), (
            f"Pipeline '{pipeline_name}' should appear in search results"
        )

    @pytest.mark.p1
    def test_search_pipeline_no_results(self, page):
        """Searching for a non-existent pipeline should show no results."""
        list_page = PipelinesListPage(page)
        list_page.navigate()

        list_page.search_and_wait_for_results("zzzz_nonexistent_pipeline_12345")

        assert not list_page.pipeline_exists_in_list(
            "zzzz_nonexistent_pipeline_12345", timeout=3000,
        ), "Non-existent pipeline should not appear in results"


class TestPipelineIsolation:
    """Verify test isolation -- each test gets a clean pipeline."""

    @pytest.mark.p0
    @pytest.mark.smoke
    def test_fixture_creates_fresh_pipeline(self, page, pipeline_id):
        """Verify the pipeline_id fixture produces a valid pipeline.

        Navigates to the pipeline detail page and checks the form loads.
        """
        detail_page = PipelineDetailPage(page)
        detail_page.navigate(pipeline_id)

        assert detail_page.get_name().startswith("autotest_"), (
            "Fixture-created pipeline name should start with 'autotest_'"
        )
        assert detail_page.get_pipeline_id() == str(pipeline_id)

    @pytest.mark.p1
    @pytest.mark.smoke
    def test_fixture_cleanup_cycle(self, pipeline_api):
        """Verify that creating and deleting pipelines via the API works.

        Smoke test for the fixture's create/delete cycle.
        """
        pipeline = pipeline_api.create_pipeline(
            name="autotest_cleanup_cycle_pipe",
            description="Smoke test for cleanup",
        )
        pid = pipeline["id"]

        # Verify it exists
        pipeline = pipeline_api.get_pipeline(pid)
        assert pipeline is not None, f"Pipeline {pid} should exist after creation"

        # Delete it
        pipeline_api.delete_pipeline(pid)

        # Verify it's gone
        try:
            pipeline_api.get_pipeline(pid)
            assert False, f"Pipeline {pid} should have been deleted"
        except Exception:
            pass  # Expected: pipeline no longer exists
