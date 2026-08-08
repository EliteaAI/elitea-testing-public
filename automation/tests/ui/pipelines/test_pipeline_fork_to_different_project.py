"""Fork pipeline to a different project (ELITEA-2051).

Creates a source Pipeline via the API in a project OTHER than the fork
target (project 400, "UI Testing"), navigates to it via the sidebar
project switcher + Pipelines dashboard card (Card list view) — matching
the case's "pipeline from another project" framing — forks it via the
pipeline-actions overflow menu's "Fork" item into the target project
(399, "Private", the user's own/default project — the INVERSE project-pair
direction from the sibling Agent case ELITEA-1893, but the same underlying
mechanic: Fork always operates from whichever project is currently
selected into a user-chosen target — see AFS § Preconditions), and
verifies:

1. The Fork wizard shows only a "Main entity" card (no "Nested entities"
   section) for a dependency-free source pipeline.
2. The Fork POST returns 201 Created.
3. "Got it" navigates into the target project, onto the newly forked
   Pipeline.
4. The forked pipeline has a new unique Pipeline ID + Version ID, and its
   Name/Description/Step Limit match the source exactly.
5. The forked pipeline's card on the Pipelines dashboard (Card list view,
   target project) shows a "Forked from" attribution icon-link (case step
   6 — the dashboard-card surface; see AFS for the CLARIFICATION on why
   this is the LIST page's card, not the detail page).
6. Cleanup (case step 9 equivalent) deletes the forked pipeline via the
   UI's type-to-confirm dialog, and the DELETE call returns 204 No
   Content; the read-only source pipeline is deleted via the API.

One MINOR, isolated, already-filed product defect (React
``validateDOMNesting`` ``<p>``-in-``<p>`` console warning on the Fork/Import
"Complete" dialog, https://github.com/EliteaAI/elitea-testing-public/issues/570
— shared ``IWModalSucceedContent.jsx`` component, previously confirmed for
the Agent entity by ELITEA-1893) reproduces here too for the Pipeline
entity. Handled via the same pytest-native soft-assertion pattern
(``soft_failures`` list + a final ``pytest.fail()``, mirroring
``test_fork_agent_to_different_project.py``'s known-defect #570 handling)
so it doesn't mask any *other* console error and never demotes the failure
to a log-only signal.

Spec: test-specs/pipelines/l2_pipeline-fork-to-different-project_ELITEA-2051.md
"""

import logging
import uuid

import allure
import pytest
from api import PipelineAPI
from pages.pipeline_detail_page import PipelineDetailPage
from pages.pipelines_list_page import PipelinesListPage

pytestmark = [pytest.mark.ui, pytest.mark.pipelines]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORK_TIMEOUT = 15_000

logger = logging.getLogger("elitea.tests.pipelines")

# Source project — "UI Testing" (400): the AFS's chosen "pipeline from
# another project", also exercised via the project switcher per case Step 1.
SOURCE_PROJECT_ID = 400
# Target/fork-into project — "Private" (399): the suite default project,
# i.e. the user's own/home project (case's "user's own project").
TARGET_PROJECT_ID = 399


class TestPipelineForkToDifferentProject:
    """Fork pipeline to a different project (ELITEA-2051, l2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/pipelines/ELITEA-2051_pipeline-fork.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_pipeline_fork_to_different_project(self, page, _browser_cookies):
        """Fork a Pipeline into a different project and verify the forked
        pipeline's configuration + attribution, then clean up.

        Steps (AFS
        test-specs/pipelines/l2_pipeline-fork-to-different-project_ELITEA-2051.md):
        1. Create the source Pipeline via API in project 400 ("UI
           Testing"); navigate to it via the sidebar project switcher +
           Pipelines dashboard card (precondition — a pipeline from
           another project, accessible to the user).
        2. Open the pipeline-actions overflow menu; verify the VERSION
           group shows "Fork" enabled.
        3. Click "Fork"; verify the Fork wizard dialog opens showing the
           Project selector and Main-entity preview card.
        4. Select a target project DIFFERENT from the source (399,
           "Private"); verify the Fork button becomes enabled.
        5. Verify the entity-preview card shows the Main entity only (no
           "Nested entities" section, since the source has no attached
           toolkits/skills/nested agents).
        6. Click "Fork"; verify the fork POST returns 201 Created and the
           dialog re-renders as "Fork Complete".
        7. Click "Got it"; verify navigation into the target project, onto
           the new forked Pipeline.
        8. Verify the forked pipeline's ID/Version ID are new and unique,
           and its Name/Description/Step Limit match the source exactly.
        9. Verify the forked pipeline's dashboard card (Card list view,
           target project) shows a "Forked from" attribution icon-link.
        10. Clean up: delete the forked pipeline via the UI; verify the
            DELETE call returns 204 No Content.
        """
        unique_suffix = uuid.uuid4().hex[:8]
        source_pipeline_name = f"el-2051-pipeline-{unique_suffix}"
        source_pipeline_description = "Pipeline for ELITEA-2051 fork-to-project verification."

        # Project-scoped PipelineAPI instances — the suite-default
        # `pipeline_api` fixture is scoped to project 399 (the FORK
        # TARGET here), so both the source-project (400) and target-project
        # (399) clients are built explicitly, mirroring
        # test_fork_agent_to_different_project.py's `target_project_agent_api`.
        source_project_pipeline_api = PipelineAPI(
            browser_cookies=_browser_cookies, project_id=str(SOURCE_PROJECT_ID),
        )
        target_project_pipeline_api = PipelineAPI(
            browser_cookies=_browser_cookies, project_id=str(TARGET_PROJECT_ID),
        )

        source_pipeline_id = None
        forked_pipeline_id = None
        # pytest has no built-in expect.soft() for a raw console-message list
        # (Playwright's Python expect.soft() only supports Page/Locator/
        # APIResponse). This list is the pytest-native equivalent — see
        # test_fork_agent_to_different_project.py's identical mechanism.
        soft_failures = []

        try:
            with allure.step(
                "Step 1 — Create the source Pipeline via API in project "
                "'UI Testing' (400); navigate to it via the sidebar "
                "project switcher + Pipelines dashboard card"
            ):
                created = source_project_pipeline_api.create_pipeline(
                    name=source_pipeline_name,
                    description=source_pipeline_description,
                )
                source_pipeline_id = int(created["id"])
                logger.info(
                    "Created source pipeline %r id=%d in project %d",
                    source_pipeline_name, source_pipeline_id, SOURCE_PROJECT_ID,
                )

                list_page = PipelinesListPage(page)
                list_page.navigate()
                list_page.switch_project(SOURCE_PROJECT_ID, timeout=NAVIGATION_TIMEOUT)
                list_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                if not list_page.is_card_view_active():
                    list_page.switch_to_card_view()
                list_page.open_pipeline_by_name(source_pipeline_name, timeout=UI_ELEMENT_TIMEOUT)

                detail_page = PipelineDetailPage(page)
                detail_page.wait_for_detail_page_load(timeout=NAVIGATION_TIMEOUT)
                assert detail_page.get_name() == source_pipeline_name, (
                    "Should have navigated onto the source pipeline's own detail page"
                )
                assert detail_page.get_pipeline_id() == str(source_pipeline_id), (
                    "Pipeline ID shown on the detail page should match the created source"
                )
                source_version_id = detail_page.get_version_id()

            with allure.step(
                "Step 2 — Open the pipeline-actions overflow menu; verify "
                "the VERSION group shows 'Fork' enabled"
            ):
                detail_page.open_fork_wizard_menu(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.fork_menuitem.is_visible(), (
                    "Actions menu should show a 'Fork' menuitem in the VERSION group"
                )
                assert detail_page.fork_menuitem.is_enabled(), (
                    "'Fork' menuitem should be enabled"
                )

            with allure.step(
                "Step 3 — Click 'Fork'; verify the Fork wizard dialog "
                "opens showing the Project selector and Main-entity "
                "preview card"
            ):
                detail_page.open_fork_wizard(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.fork_wizard_dialog.is_visible(), (
                    "Fork wizard dialog should be visible after clicking Fork"
                )
                assert detail_page.fork_project_select_trigger.is_visible(), (
                    "Fork wizard should show the target Project selector"
                )
                assert detail_page.fork_main_entity_name.text_content() == source_pipeline_name, (
                    "Fork wizard's Main-entity name preview should show the "
                    "source pipeline's name verbatim"
                )
                assert not detail_page.fork_confirm_button.is_enabled(), (
                    "Fork confirm button should be disabled before a target "
                    "project is selected"
                )

            with allure.step(
                "Step 4 — Select a target project DIFFERENT from the "
                "source (399, 'Private'); verify the Fork button becomes "
                "enabled"
            ):
                detail_page.select_fork_target_project(
                    TARGET_PROJECT_ID, timeout=UI_ELEMENT_TIMEOUT,
                )
                assert detail_page.fork_confirm_button.is_enabled(), (
                    "Fork confirm button should become enabled once a "
                    "target project is selected"
                )

            with allure.step(
                "Step 5 — Verify the entity-preview card shows the Main "
                "entity only (no 'Nested entities' section, since the "
                "source pipeline has no attached toolkits/skills/nested "
                "agents)"
            ):
                assert detail_page.fork_entity_card_toggle.count() == 1, (
                    "Fork wizard should render exactly one entity-preview "
                    "card (Main entity only) for a dependency-free source "
                    "pipeline — a count > 1 would indicate an unexpected "
                    "'Nested entities' section"
                )

            with allure.step(
                "Step 6 — Click 'Fork'; verify the fork POST returns 201 "
                "Created and the dialog re-renders as 'Fork Complete'"
            ):
                # Console messages are captured starting BEFORE the fork
                # click so the listener observes the "Fork Complete"
                # dialog's own render — Playwright console listeners are
                # forward-looking only, no backfill.
                console_messages = []
                page.on(
                    "console",
                    lambda msg: console_messages.append(msg) if msg.type == "error" else None,
                )

                with page.expect_response(
                    lambda r: (
                        f"/elitea_core/fork/prompt_lib/{TARGET_PROJECT_ID}" in r.url
                        and r.request.method == "POST"
                    ),
                    timeout=FORK_TIMEOUT,
                ) as fork_response_info:
                    detail_page.confirm_fork(timeout=FORK_TIMEOUT)

                fork_response = fork_response_info.value
                assert fork_response.status == 201, (
                    f"Fork POST to project {TARGET_PROJECT_ID} should "
                    f"return 201 Created, got {fork_response.status}"
                )
                assert detail_page.fork_complete_dialog.is_visible(), (
                    "Fork Complete dialog should be visible after a "
                    "successful fork"
                )
                assert source_pipeline_name in detail_page.fork_complete_pipelines_list.text_content(), (
                    "Fork Complete dialog's Pipelines list should include "
                    "the source pipeline's name — confirming a new forked "
                    "entity was created"
                )
                page.wait_for_timeout(500)  # let any deferred console errors surface

            with allure.step(
                "Step 6b — Console-cleanliness check around the Fork "
                "Complete dialog (a known, isolated, non-blocking defect "
                "fires a validateDOMNesting warning here — soft-asserted "
                "via the pytest-native soft_failures/pytest.fail() "
                "mechanism, not a demoted log-only check)"
            ):
                unexpected_errors = [
                    m.text for m in console_messages
                    if "validateDOMNesting" not in m.text
                ]
                assert not unexpected_errors, (
                    "Expected no UNEXPECTED console errors around the Fork "
                    f"Complete dialog, got: {unexpected_errors!r}"
                )
                # Known defect: #570 — React validateDOMNesting <p>-in-<p>
                # warning on IWModalSucceedContent.jsx's "Forked:" label.
                # Does not block the functional flow. Recorded in
                # soft_failures (real soft-assertion equivalent) rather
                # than only logged, so a regression here still fails the
                # test instead of silently passing.
                known_defect_errors = [
                    m.text for m in console_messages if "validateDOMNesting" in m.text
                ]
                if known_defect_errors:
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/570: "
                        f"validateDOMNesting console error(s) on the Fork Complete "
                        f"dialog: {known_defect_errors!r}"
                    )

            with allure.step(
                "Step 7 — Click 'Got it'; verify navigation into the "
                "target project, onto the new forked Pipeline"
            ):
                forked_pipeline_id = detail_page.confirm_fork_complete(
                    timeout=NAVIGATION_TIMEOUT,
                )
                assert forked_pipeline_id != source_pipeline_id, (
                    f"Forked Pipeline ID should differ from source: "
                    f"forked={forked_pipeline_id}, source={source_pipeline_id}"
                )
                assert f"/pipelines/all/{forked_pipeline_id}" in page.url, (
                    "Should navigate to the forked Pipeline's own detail page URL"
                )
                logger.info(
                    "Forked pipeline created — id=%d in project %d",
                    forked_pipeline_id, TARGET_PROJECT_ID,
                )

            with allure.step(
                "Step 8 — Verify the forked pipeline has a new unique "
                "Pipeline ID and Version ID, and its Name/Description/"
                "Step Limit match the source exactly"
            ):
                assert detail_page.get_pipeline_id() == str(forked_pipeline_id), (
                    "Detail page's own Pipeline ID display should match "
                    "the URL's forked id"
                )
                forked_version_id = detail_page.get_version_id()
                assert forked_version_id != source_version_id, (
                    f"Forked Version ID should differ from source: "
                    f"forked={forked_version_id}, source={source_version_id}"
                )
                assert detail_page.get_name() == source_pipeline_name, (
                    "Forked pipeline's Name should match the source verbatim"
                )
                assert detail_page.get_description() == source_pipeline_description, (
                    "Forked pipeline's Description should match the source verbatim"
                )
                assert detail_page.get_step_limit() == "25", (
                    "Forked pipeline's Step Limit should match the "
                    "source's default (25)"
                )

            with allure.step(
                "Step 9 — Verify the forked pipeline's dashboard card "
                "(Card list view, target project) shows a 'Forked from' "
                "attribution link"
            ):
                list_page.navigate()
                if not list_page.is_card_view_active():
                    list_page.switch_to_card_view()
                forked_card_name = list_page.entity_card_name.filter(has_text=source_pipeline_name)
                forked_card_name.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                forked_from_links = list_page.entity_card_forked_from_link
                assert forked_from_links.count() >= 1, (
                    "Pipelines dashboard should show at least one 'Forked "
                    "from' attribution icon-link (the forked pipeline's card)"
                )
                assert forked_from_links.first.get_attribute("aria-label") == (
                    "Forked from - Original pipeline"
                ), "'Forked from' link should carry the expected aria-label"

            with allure.step(
                "Step 10 — Clean up: delete the forked pipeline via the "
                "UI; verify the DELETE call returns 204 No Content"
            ):
                detail_page.navigate(forked_pipeline_id)
                with page.expect_response(
                    lambda r: (
                        f"/elitea_core/application/prompt_lib/{TARGET_PROJECT_ID}/{forked_pipeline_id}"
                        in r.url
                        and r.request.method == "DELETE"
                    ),
                    timeout=NAVIGATION_TIMEOUT,
                ) as delete_response_info:
                    detail_page.delete_pipeline_via_menu(timeout=NAVIGATION_TIMEOUT)

                delete_response = delete_response_info.value
                assert delete_response.status == 204, (
                    "Deleting the forked pipeline from project "
                    f"{TARGET_PROJECT_ID} should return 204 No Content, "
                    f"got {delete_response.status}"
                )
                # UI-driven delete already succeeded — clear the fallback
                # cleanup marker so the finally block doesn't attempt a
                # redundant (and now-404) API delete.
                forked_pipeline_id = None

            if soft_failures:
                pytest.fail(
                    "Soft assertion(s) failed (known isolated product defect, "
                    "not test/infrastructure — rest of the flow, steps 7-10, "
                    "passed cleanly):\n" + "\n".join(soft_failures)
                )

        finally:
            # Cleanup per AFS: source pipeline (project 400, read-only
            # throughout Fork) always; forked pipeline (project 399) ONLY
            # as a fallback if the UI-driven Step 10 delete above did not
            # run/succeed (forked_pipeline_id is cleared to None on success).
            if source_pipeline_id is not None:
                try:
                    source_project_pipeline_api.delete_pipeline(source_pipeline_id)
                    logger.info("Cleanup: deleted source pipeline id=%d", source_pipeline_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete source pipeline id=%s: %s",
                        source_pipeline_id, exc,
                    )
            if forked_pipeline_id is not None:
                try:
                    target_project_pipeline_api.delete_pipeline(forked_pipeline_id)
                    logger.info(
                        "Fallback cleanup: deleted forked pipeline id=%d in "
                        "project %d", forked_pipeline_id, TARGET_PROJECT_ID,
                    )
                except Exception as exc:
                    logger.warning(
                        "Fallback cleanup: failed to delete forked pipeline "
                        "id=%s in project %d: %s",
                        forked_pipeline_id, TARGET_PROJECT_ID, exc,
                    )
