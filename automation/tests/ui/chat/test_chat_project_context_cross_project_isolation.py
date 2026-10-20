"""UI test — Project Context Builder creates context in the current project
only; a second project the user belongs to is unaffected (ELITEA-3315).

Verifies that:
    1. Sending the case's own literal creation message with the Project
       Context Builder module enabled produces a DIRECT creation response —
       the assistant never asks the user to specify a project or a user id
       (the backend resolves ``runtime_context``'s ``user_id``/``project_id``
       server-side from the authenticated session).
    2. The created content is present, non-empty, and enabled when viewed
       via Project A's own Settings -> Project Context UI, confirmed both
       at the API layer and the Settings-UI layer.
    3. Project B — a DIFFERENT project the same user belongs to — remains
       completely unaffected: no content, no entity, confirmed via both its
       own Settings UI empty-state AND a direct API GET scoped to Project
       B's id.

AFS: test-specs/chat-interface/l1_project-context-isolated-to-current-project_ELITEA-3315.md

Case-text clarifications (not product defects — see the AFS's Known Defects
section and ``.agents/role-overrides.md``'s reverse-masking guard):
    - The case's "Project Context Builder is enabled in Chat Modules"
      precondition is a PER-CONVERSATION toggle, not an ambient project
      setting — identical finding to ELITEA-3368's AFS for this exact
      module toggle. This test enables it explicitly via the Modules
      submenu before sending the creation message (Step 2).
    - The case's step 6 "Project B's context is unchanged (empty or
      previous content)" names two possible starting states; this
      environment's Project B starts empty, so only that branch is
      exercised (the assertion shape, before == after, is identical either
      way — see the AFS's Known Defects item 2).

Project B discovery — **declared**: resolved at runtime from the acting
user's real project memberships via ``ProjectAPI.list_projects()``, the
same precondition-discovery pattern
``test_pipeline_fork_to_different_project.py``'s
``_resolve_source_project_id()`` already establishes (excludes the active
project id and the public project id; never hardcoded, since a different
CI matrix cell's acting user may have a different second membership).

Markers:
    - ui: requires browser
    - chat: Chat-surface feature
    - p0: critical priority (AFS: l1, case priority: critical)
    - regression

Usage:
    cd automation
    pytest tests/ui/chat/test_chat_project_context_cross_project_isolation.py -v
"""

import logging

import allure
import pytest
from api import ProjectAPI, ProjectContextAPI
from config import settings
from pages.chat_page import ChatPage
from pages.project_context_page import ProjectContextPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [
    pytest.mark.ui,
    pytest.mark.chat,
    pytest.mark.p0,
    pytest.mark.regression,
    pytest.mark.new,
]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 60_000  # tool invocation + generation observed 8-12s live

CREATE_MESSAGE = (
    "Create project context: This is a QA automation project using Python "
    "and Playwright"
)

PROJECT_CONTEXT_ENTITY_LABEL = "Project Context"

# Project A — the active project at test start, the TMS case's own
# precondition ("User is in Project A"). ELITEA_PROJECT_ID is that project
# on every environment (locally 575, "Private"; TEST_USER_PROJECT_<n> in CI).
PROJECT_A_ID = settings.elitea_project_id


def _resolve_second_project_id(browser_cookies: list[dict]) -> int:
    """Return a project the acting user belongs to, other than Project A.

    Reads the acting user's REAL project memberships from the product's own
    projects-list endpoint (same one the UI's project selector renders
    from — ``ProjectAPI.list_projects()``), then excludes Project A
    (``PROJECT_A_ID``) and the public project (``settings.public_project_id``)
    from the candidate list, matching
    ``test_pipeline_fork_to_different_project.py``'s
    ``_resolve_source_project_id()`` pattern. The lowest remaining id is
    chosen, so the pick is deterministic run-to-run.

    Fails loudly (never skips) if either precondition is unmet — a silent
    skip would drop this case's cross-project-isolation coverage without
    anyone noticing.
    """
    if PROJECT_A_ID <= 0:
        pytest.fail(
            "ELITEA-3315 precondition unmet: Project A's id resolved to "
            f"{PROJECT_A_ID!r}. ELITEA_PROJECT_ID is unset or invalid — set "
            "it in automation/.env.test (or the CI env) and re-run."
        )

    project_api = ProjectAPI(browser_cookies=browser_cookies)
    try:
        projects = project_api.list_projects()
    finally:
        project_api.close()

    member_ids = [int(p["id"]) for p in projects]
    candidates = [
        p for p in projects
        if int(p["id"]) not in (PROJECT_A_ID, settings.public_project_id)
    ]
    if not candidates:
        pytest.fail(
            "ELITEA-3315 precondition unmet: the acting user belongs to no "
            "second, non-public project usable as Project B — every "
            f"membership is either Project A ({PROJECT_A_ID}, "
            f"ELITEA_PROJECT_ID) or the public project "
            f"({settings.public_project_id}, both excluded). The case "
            f"requires a second project. Memberships read from the "
            f"projects-list endpoint: {member_ids}"
        )

    chosen = sorted(candidates, key=lambda p: int(p["id"]))[0]
    return int(chosen["id"])


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/chat/build-skills-project-context/"
    "ELITEA-3315_project-context-isolated-to-current-project.md",
    "onetest-ai Test Case link (ELITEA-3315)",
)
@pytest.mark.tms("ELITEA-3315")
class TestChatProjectContextCrossProjectIsolation:
    """ELITEA-3315 — Project Context Builder receives runtime_context and
    creates context in the current project only; a second project the user
    belongs to is unaffected."""

    @allure.title(
        "Chat Project Context builder: creates in current project only, "
        "a second project is unaffected"
    )
    def test_project_context_isolated_to_current_project(
        self,
        page,
        conversation_id,
        clean_project_context,
        project_context_api,
        _browser_cookies,
    ):
        chat = ChatPage(page)
        console_errors = chat.capture_console_errors()

        project_b_id = _resolve_second_project_id(_browser_cookies)
        logger.info(
            "ELITEA-3315: Project A=%s, Project B=%s", PROJECT_A_ID, project_b_id
        )
        project_context_api_b = ProjectContextAPI(
            browser_cookies=_browser_cookies, project_id=str(project_b_id)
        )

        try:
            with allure.step(
                "Step 1 — Confirm the active project is Project A via the "
                "sidebar project selector"
            ):
                chat.navigate_to_chat(conversation_id=conversation_id)
                selected_text = chat.get_selected_project_text()
                assert "Private" in selected_text or str(PROJECT_A_ID) in selected_text, (
                    f"Expected the sidebar project selector to show Project A "
                    f"before the test's own steps run, got: {selected_text!r}"
                )

            with allure.step(
                "Step 2 — Open a fresh conversation in Project A, enable the "
                "Project Context Builder module for it via the Modules submenu"
            ):
                chat.open_internal_tools_menu(timeout=NAVIGATION_TIMEOUT)
                chat.ensure_module_toggle_checked(
                    "project_context_builder", timeout=UI_ELEMENT_TIMEOUT
                )
                assert chat.is_module_toggle_checked("project_context_builder"), (
                    "Expected the Project Context Builder module toggle to be "
                    "checked before sending the creation message"
                )
                chat.close_modules_panel(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 3 — Send the case's own literal creation message; "
                "assistant proceeds without asking for project specification"
            ):
                initial_count = chat.get_message_count()
                chat.send_message(CREATE_MESSAGE, use_enter=True)
                chat.wait_for_ai_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT
                )
                response_text = chat.get_message_text_at(initial_count + 1)
                assert "?" not in response_text, (
                    f"Expected a direct creation response with no clarifying "
                    f"question (no project/user specification requested), got: "
                    f"{response_text!r}"
                )

            with allure.step(
                "Step 4 — Verify the Project Context chip/link appears in the "
                "chat response"
            ):
                chat.generated_entity_chip.wait_for(
                    state="visible", timeout=UI_ELEMENT_TIMEOUT
                )
                chip_label = (chat.generated_entity_chip.text_content() or "").strip()
                assert PROJECT_CONTEXT_ENTITY_LABEL in chip_label, (
                    f"Expected the generated-entity-chip to be labeled "
                    f"'{PROJECT_CONTEXT_ENTITY_LABEL}', got {chip_label!r}"
                )

            with allure.step(
                "Step 5 — Verify via a direct API GET that Project A now has "
                "non-empty, topically consistent content"
            ):
                get_resp_a = project_context_api.get_project_context()
                assert get_resp_a.status_code == 200, (
                    f"Expected GET project-context (Project A) to return 200, "
                    f"got {get_resp_a.status_code}"
                )
                body_a = get_resp_a.json()
                content_a = body_a.get("content") or ""
                assert content_a.strip(), (
                    "Expected Project A's Project Context content to be "
                    "non-empty after creation"
                )
                lowered_a = content_a.lower()
                assert any(kw in lowered_a for kw in ("python", "playwright", "qa")), (
                    f"Expected the generated content to be topically "
                    f"consistent with the prompt (mentioning python/"
                    f"playwright/qa), got: {content_a[:200]!r}"
                )
                assert body_a.get("id") is not None, (
                    f"Expected a non-null id for Project A's created context, "
                    f"got body: {body_a}"
                )
                assert body_a.get("enabled") is True, (
                    f"Expected Project A's Project Context to be enabled "
                    f"(enabled: true) after creation, got "
                    f"enabled={body_a.get('enabled')!r}; body keys: "
                    f"{sorted(body_a.keys())}"
                )

            with allure.step(
                "Step 6 — Navigate to Project A's Settings > Project Context: "
                "the created content is present and enabled"
            ):
                context_page = ProjectContextPage(page)
                context_page.navigate()
                assert context_page.create_button.count() == 0, (
                    "Expected the empty-state 'Create' button to be absent on "
                    "Project A's Settings > Project Context — content already "
                    "exists"
                )
                # Content already exists, so navigate() lands on the
                # read-only SAVED view (edit_button visible), not the
                # CodeMirror editor (editor_content only renders after
                # clicking Edit/Create — see ProjectContextPage.wait_for_page_load
                # docstring, amended this session per live exploration).
                assert context_page.is_saved_view_showing(), (
                    "Expected Project A's Settings > Project Context to show "
                    "the read-only saved view (existing content, not the "
                    "create/edit flow)"
                )
                saved_text_a = context_page.get_saved_content_text()
                assert saved_text_a.strip(), (
                    "Expected Project A's Settings > Project Context saved "
                    "view to show non-empty content"
                )

            with allure.step(
                "Step 7 — Switch the active project to Project B via the "
                "sidebar selector"
            ):
                chat.switch_project(project_b_id, timeout=NAVIGATION_TIMEOUT)
                selected_text_b = chat.get_selected_project_text()
                assert selected_text_b != selected_text, (
                    f"Expected the sidebar project selector text to change "
                    f"after switching to Project B, got the same text as "
                    f"Project A: {selected_text_b!r}"
                )

            with allure.step(
                "Step 8 — Verify Project B's Settings > Project Context is "
                "unaffected by Project A's creation — empty state in the UI "
                "AND via a direct API GET scoped to Project B's id"
            ):
                context_page.navigate()
                assert context_page.create_button.count() == 1, (
                    "Expected Project B's Settings > Project Context to show "
                    "the empty-state 'Create' button — isolated from Project "
                    "A's creation"
                )
                assert context_page.editor_content.count() == 0, (
                    "Expected Project B's Settings > Project Context to show "
                    "no saved editor content — isolated from Project A's "
                    "creation"
                )

                get_resp_b = project_context_api_b.get_project_context()
                assert get_resp_b.status_code == 200, (
                    f"Expected GET project-context (Project B) to return 200, "
                    f"got {get_resp_b.status_code}"
                )
                body_b = get_resp_b.json()
                assert body_b.get("content") == "", (
                    f"Expected Project B's content to remain empty, got: "
                    f"{body_b.get('content')!r}"
                )
                assert body_b.get("id") is None, (
                    f"Expected Project B's Project Context id to remain null "
                    f"(no entity created), got: {body_b.get('id')!r}"
                )

            with allure.step("Side-channel check — no console errors at any step"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()
            project_context_api_b.close()
            # Restore the active project to Project A so the shared
            # project_context_api/clean_project_context fixtures (scoped to
            # Project A) run their teardown DELETE against the right project.
            try:
                chat.switch_project(PROJECT_A_ID, timeout=NAVIGATION_TIMEOUT)
            except Exception as exc:
                logger.warning(
                    "Failed to switch back to Project A during teardown: %s", exc
                )
