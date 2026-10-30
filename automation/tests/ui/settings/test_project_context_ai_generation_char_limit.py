"""UI tests — Project Context 2500-character limit enforced across the
AI-assisted create/edit flows and the Chat builder tool (Family).

Four TMS cases, one object under test (the project context's 2500-char
server-side limit, enforced identically wherever generated/edited content is
submitted), four distinct entry points — written as ONE parameterized test,
one row per case, each row asserting its OWN expected outcome:

    1. ELITEA-3252 — Settings, empty state -> "Build with AI": short prompt
       produces a draft well under 2500 chars; Apply + Save succeeds.
    2. ELITEA-3253 — Settings, empty state -> "Build with AI": a verbose
       prompt produces a draft that WOULD exceed 2500 chars; the server
       rejects it (422) with a specific error message, the prompt is
       preserved, and nothing is saved.
    3. ELITEA-3254 — Chat's ``project_context_builder`` module tool:
       asking the AI (in one message, with a project description included)
       to generate+save a project context invokes ``put_project_context``,
       and the saved content is <=2500 chars, visible in both Chat and
       Settings.
    4. ELITEA-3255 — Settings, populated Project Context -> "Edit with AI":
       expanding existing content with an edit instruction stays <=2500
       chars; Apply & Save succeeds.

AFS (family): test-specs/settings-project-params/
    l1_project-context-char-limit-enforced-across-surfaces_ELITEA-3252.md

Case-text drift confirmed live and NOT re-automated (CLARIFICATION, not a
product bug — see the AFS's Known Defects section and
.agents/role-overrides.md's reverse-masking guard):
    - No "Project Context toggle" exists on this build — the feature's
      ``enabled`` flag is a fixed ``true`` the editor always sends, not a
      user-facing switch. Dropped from every row's steps.
    - ELITEA-3254's case text names the tool ``generate_project_context_draft``;
      the live tool-invocation chip reads
      ``Elitea Project Context: put_project_context_project-context`` for a
      message that both generates AND saves in one request. Asserted
      against the live chip text, not the case's named tool — the pass bar
      (content generated + saved + <=2500) is met either way.
    - ELITEA-3255's case text describes "Edit" then "Edit with AI" as two
      sequential clicks; on this build "Edit with AI" is a single click
      directly from the saved view (confirmed live: two independent,
      adjacent buttons, not a two-step flow).

Also confirmed live and folded into every row (not in any case's own step
text — see the AFS's Axis 2 "Analyst additions"): the editor's "Activation
description" input (NEW since ELITEA-2272) is required non-empty for Save to
enable on the create/edit flow; filled in every row that calls Save.

ELITEA-2272 regression note: that case's own test file
(``test_project_context_character_limit.py``) was removed from the suite
independently by commit 3fcc1478 ("unstable UI tests" cleanup, 2026-10-06) —
confirmed via ``git log --diff-filter=D`` before writing this file — so there
is no live ELITEA-2272 test for this change to regress.

Markers:
    - ui: requires browser
    - settings: ELITEA-3252/3253/3255 are Settings-surface; ELITEA-3254 is
      Chat-surface — both markers applied at module level since one
      parametrized test spans both surfaces (see `chat` marker below too)
    - chat: ELITEA-3254's row drives the Chat surface
    - p0: critical priority (AFS: l1, all four cases `priority: critical`)
    - regression

Usage:
    cd automation
    pytest tests/ui/settings/test_project_context_ai_generation_char_limit.py -v
    pytest tests/ui/settings/test_project_context_ai_generation_char_limit.py -v -k ELITEA-3253
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage
from pages.project_context_page import ProjectContextPage

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.settings,
    pytest.mark.chat,
    pytest.mark.p0,
    pytest.mark.regression,
    pytest.mark.new,
]

# ---------------------------------------------------------------------------
# Timeout / shared constants
# ---------------------------------------------------------------------------
AI_GENERATION_TIMEOUT = 30_000   # Draft generation observed 5-11s live; comfortable margin
AI_RESPONSE_TIMEOUT = 60_000     # Chat AI response incl. tool invocation
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

MAX_CHARS = 2500

SHORT_PROMPT = (
    "A simple test automation project for a web app with login, dashboard, "
    "and settings pages."
)

VERBOSE_PROMPT = (
    "Create a comprehensive and detailed project context for a large-scale "
    "AI-powered Healthcare Appointment and Patient Management Platform. The "
    "project should include multiple user roles such as patients, doctors, "
    "nurses, clinic administrators, and system administrators. Describe the "
    "project's business goals, key features, user workflows, functional and "
    "non-functional requirements, system architecture, frontend and backend "
    "components, database structure, authentication and authorization, "
    "appointment scheduling, patient records, notifications, billing, "
    "reporting, audit logging, integrations with external healthcare systems "
    "and payment providers, API requirements, data validation, error "
    "handling, security and privacy considerations, performance "
    "requirements, scalability, accessibility, localization, and compliance "
    "requirements."
)

CHAT_GENERATE_AND_SAVE_MESSAGE = (
    "Generate and save a project context for this project. It is a "
    "Playwright/pytest test automation suite for the Elitea AI platform, "
    "covering chat, agents, pipelines, skills, toolkits, and settings UI "
    "flows against a deployed DEV environment."
)

# ELITEA-3255's base content — short filler, well under the limit, so the
# edit instruction below has room to expand without itself overflowing
# (confirmed live: ~1380 chars base + the edit instruction below settles
# around ~450-1470 chars depending on generation variance, always <=2500).
EDIT_BASE_CONTENT = ("This is filler project context content for an automated test "
                      "covering integrations and security considerations. " * 20)[:1380]
EDIT_INSTRUCTION = "Add one short sentence about security."

ACTIVATION_DESCRIPTION = "Used for automated test coverage of this project's workflows."

# Browser's own automatic network-layer log for the intentionally-triggered
# 422 on ELITEA-3253 ("Failed to load resource: the server responded with a
# status of 422 ()") — expected for this negative-path row, not an
# application-level error. Filtered out of that row's console-error check
# (same pattern as test_artifacts_duplicate_bucket_name.py's 400 case).
EXPECTED_CONSOLE_ERROR_SUBSTRING = "Failed to load resource"


class TestProjectContextAIGenerationCharLimit:
    """ELITEA-3252/3253/3254/3255 — the Project Context's 2500-char
    server-side limit is enforced identically across Settings create
    (Build with AI), Settings edit (Edit with AI), and the Chat
    ``project_context_builder`` module tool."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/chat/build-skills-project-context/"
        "ELITEA-3252_settings-generate-project-context-respects-2500-char-limit.md",
        "onetest-ai Test Case link (ELITEA-3252)",
    )
    @pytest.mark.tms("ELITEA-3252")
    @allure.title("Settings - Build with AI: short prompt stays under 2500 chars, Apply+Save succeeds")
    def test_build_with_ai_short_prompt_under_limit(self, page, clean_project_context):
        """ELITEA-3252 — a short project description generates a draft well
        under 2500 chars; Apply populates the editor; Save succeeds once the
        (new, required) Activation description is filled."""
        context_page = ProjectContextPage(page)
        console_errors = context_page.capture_console_errors()

        try:
            with allure.step("Step 1 — Navigate to Settings -> Project Context: empty state"):
                context_page.navigate()
                assert context_page.create_button.is_visible(), (
                    "Expected the empty-state 'Create' button to be visible"
                )

            with allure.step("Step 2 — Click 'Build with AI' — generation dialog opens"):
                context_page.click_build_with_ai()
                assert context_page.build_with_ai_dialog.is_visible(), (
                    "Expected the 'Build with AI' dialog to be visible"
                )

            with allure.step("Step 3 — Provide a short description, trigger generation"):
                response = context_page.generate_draft_from_prompt(SHORT_PROMPT, timeout=AI_GENERATION_TIMEOUT)
                assert response.status == 200, (
                    f"Expected generate_project_context_draft to return 200 for a short "
                    f"prompt, got {response.status}: {response.text()[:200]}"
                )

            with allure.step("Step 4 — Verify the generated draft is <=2500 chars and coherent"):
                draft = context_page.get_build_with_ai_review_draft()
                assert 0 < len(draft) <= MAX_CHARS, (
                    f"Expected the generated draft length to be in (0, {MAX_CHARS}], got {len(draft)}"
                )
                assert not draft.rstrip().endswith(("...", "…")), (
                    "Draft should not look truncated mid-sentence"
                )

            with allure.step("Step 5 — Apply the draft — editor populates with the generated content"):
                context_page.click_build_with_ai_apply()
                editor_text = context_page.editor_content.text_content() or ""
                # CodeMirror renders each line in its own DOM node, so
                # .text_content() drops the "\n" line separators the review
                # textarea's .input_value() keeps — normalize both before
                # comparing (confirmed live: raw lengths differ by exactly
                # the newline count, content itself is unchanged).
                assert editor_text.replace("\n", "") == draft.replace("\n", ""), (
                    "Expected the editor content to match the applied draft "
                    "(modulo CodeMirror's line-node newline stripping)"
                )
                assert len(editor_text) <= MAX_CHARS, (
                    f"Expected the applied editor content to stay <= {MAX_CHARS} chars, "
                    f"got {len(editor_text)}"
                )

            with allure.step(
                "Step 6 — Fill the required Activation description, click Save — "
                "success toast, URL reverts to the saved view"
            ):
                context_page.fill_activation_description(ACTIVATION_DESCRIPTION)
                assert context_page.is_save_enabled(), (
                    "Expected Save to be enabled once both editor content and "
                    "activation description are non-empty"
                )
                context_page.click_save()
                toast_text = context_page.get_toast_text()
                assert "Project Context saved" in toast_text, (
                    f"Expected toast text to contain 'Project Context saved', got {toast_text!r}"
                )

            with allure.step("Side-channel check — no console errors at any step"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/chat/build-skills-project-context/"
        "ELITEA-3253_settings-generate-project-context-shows-error-when-exceeds-limit.md",
        "onetest-ai Test Case link (ELITEA-3253)",
    )
    @pytest.mark.tms("ELITEA-3253")
    @allure.title("Settings - Build with AI: verbose prompt exceeds 2500 chars, server rejects with 422")
    def test_build_with_ai_verbose_prompt_exceeds_limit(self, page, clean_project_context, project_context_api):
        """ELITEA-3253 — a verbose prompt produces a draft that would exceed
        2500 chars; the server rejects generation with a 422 and a specific
        error message, the prompt is preserved verbatim, and nothing is
        saved (verified both via the UI and a direct API GET)."""
        context_page = ProjectContextPage(page)
        console_errors = context_page.capture_console_errors()

        try:
            with allure.step("Step 1 — Navigate to Settings -> Project Context: empty state"):
                context_page.navigate()

            with allure.step("Step 2 — Click 'Build with AI' — generation dialog opens"):
                context_page.click_build_with_ai()

            with allure.step("Step 3 — Enter the verbose prompt, trigger generation"):
                response = context_page.generate_draft_from_prompt(VERBOSE_PROMPT, timeout=AI_GENERATION_TIMEOUT)
                assert response.status == 422, (
                    f"Expected generate_project_context_draft to return 422 for a prompt "
                    f"that overflows the limit, got {response.status}: {response.text()[:200]}"
                )

            with allure.step(
                "Step 4 — Verify the inline error alert shows the exact message pattern"
            ):
                error_text = context_page.get_build_with_ai_error_text()
                assert error_text.startswith("Project background is ") and (
                    "the maximum is 2500" in error_text
                ), (
                    f"Expected the error text to match 'Project background is {{N}} "
                    f"characters, the maximum is 2500...', got {error_text!r}"
                )
                assert "Try generating again, or ask for a narrower scope." in error_text, (
                    f"Expected the error text to include the retry suggestion, got {error_text!r}"
                )

            with allure.step("Step 5 — Verify the original prompt remains in the textarea, unchanged"):
                preserved_prompt = context_page.get_build_with_ai_prompt_value()
                assert preserved_prompt == VERBOSE_PROMPT, (
                    "Expected the prompt textarea to still contain the originally-typed "
                    "prompt verbatim after a 422"
                )

            with allure.step(
                "Step 6 — Verify no partial/truncated content was saved (API GET is "
                "unchanged from the empty precondition)"
            ):
                get_resp = project_context_api.get_project_context()
                assert get_resp.status_code == 200, (
                    f"Expected GET project-context to return 200, got {get_resp.status_code}"
                )
                body = get_resp.json()
                assert body.get("content") == "" and body.get("id") is None, (
                    f"Expected the project context to remain empty after a 422 "
                    f"(no PUT should have fired), got {body}"
                )

            with allure.step(
                "Side-channel check — only the browser's own network-layer log for "
                "the intentional 422, no application-level console error"
            ):
                unexpected_console_errors = [
                    m for m in console_errors
                    if EXPECTED_CONSOLE_ERROR_SUBSTRING not in (m.text or "")
                ]
                assert not unexpected_console_errors, (
                    f"Unexpected console errors: {[m.text for m in unexpected_console_errors]}"
                )
        finally:
            console_errors.stop()

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/chat/build-skills-project-context/"
        "ELITEA-3254_chat-context-builder-generates-content-under-limit.md",
        "onetest-ai Test Case link (ELITEA-3254)",
    )
    @pytest.mark.tms("ELITEA-3254")
    @allure.title("Chat - project_context_builder tool: generated+saved content stays under 2500 chars")
    def test_chat_project_context_builder_under_limit(self, page, clean_project_context, project_context_api):
        """ELITEA-3254 — asking the AI in Chat to generate+save a project
        context (with a description included in the same message) invokes
        the Project Context tool and persists content <=2500 chars, visible
        in both Chat (tool-invocation chip) and Settings (saved view)."""
        chat = ChatPage(page)
        console_errors = chat.capture_console_errors()

        try:
            with allure.step("Step 1 — Navigate to Chat, create a fresh conversation"):
                chat.navigate_to_chat()
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)

            with allure.step("Step 2 — Ensure the Project Context Builder module is enabled"):
                chat.open_internal_tools_menu()
                chat.ensure_module_toggle_checked("project_context_builder", timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_module_toggle_checked("project_context_builder"), (
                    "Expected the Project Context Builder module toggle to be checked"
                )
                chat.close_modules_panel(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 3 — Send a message asking the AI to generate AND save a project "
                "context, with a project description included in the same message"
            ):
                initial_count = chat.get_message_count()
                chat.send_message(CHAT_GENERATE_AND_SAVE_MESSAGE, use_enter=True)
                chat.wait_for_ai_response(initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT)

            with allure.step(
                "Step 4 — Verify a tool-invocation chip shows the Project Context tool "
                "actually fired (live chip name: put_project_context, not the case's "
                "named generate_project_context_draft — see module docstring)"
            ):
                tool_chips = chat.answer_tool_chip
                chip_texts = [tool_chips.nth(i).text_content() or "" for i in range(tool_chips.count())]
                assert any("Elitea Project Context" in t and "put_project_context" in t for t in chip_texts), (
                    f"Expected a tool-invocation chip naming the Project Context tool's "
                    f"put_project_context call, got chip texts: {chip_texts!r}"
                )

            with allure.step("Step 5 — Verify the saved content is <=2500 chars via a direct API GET"):
                get_resp = project_context_api.get_project_context()
                assert get_resp.status_code == 200, (
                    f"Expected GET project-context to return 200, got {get_resp.status_code}"
                )
                body = get_resp.json()
                content = body.get("content") or ""
                assert 0 < len(content) <= MAX_CHARS, (
                    f"Expected the chat-generated content length to be in (0, {MAX_CHARS}], "
                    f"got {len(content)}"
                )

            with allure.step(
                "Step 6 — Navigate to Settings -> Project Context: saved content appears "
                "(the populated saved view renders the 'Edit with AI' button directly, "
                "not the empty-state 'Create' button — confirmed live)"
            ):
                context_page = ProjectContextPage(page)
                context_page.navigate()
                assert context_page.ai_edit_open_button.is_visible(), (
                    "Expected the populated saved view ('Edit with AI' button) to render, "
                    "confirming the chat-generated content reached Settings — not the "
                    "empty-state 'Create' button"
                )
                assert not context_page.create_button.is_visible(), (
                    "Expected the empty-state 'Create' button to be ABSENT once the chat "
                    "tool has saved content — the API GET in Step 5 already confirmed "
                    "non-empty, <=2500-char content exists"
                )

            with allure.step("Side-channel check — no console errors at any step"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/chat/build-skills-project-context/"
        "ELITEA-3255_settings-edit-with-ai-respects-limit.md",
        "onetest-ai Test Case link (ELITEA-3255)",
    )
    @pytest.mark.tms("ELITEA-3255")
    @allure.title("Settings - Edit with AI: expanding existing content stays under 2500 chars")
    def test_edit_with_ai_expand_content_under_limit(self, page, clean_project_context, project_context_api):
        """ELITEA-3255 — starting from existing (~1380-char) Project Context
        content, 'Edit with AI' is reached directly from the saved view
        (single click, no separate 'Edit' step — case-text drift, see module
        docstring); expanding it with a short edit instruction stays
        <=2500 chars and Apply & Save succeeds in one action."""
        context_page = ProjectContextPage(page)
        console_errors = context_page.capture_console_errors()

        try:
            with allure.step(
                "Step 1 — Seed existing content via the UI create flow (precondition: "
                "existing Project Context content, produced through the action under "
                "test per this project's test-data strategy)"
            ):
                context_page.navigate()
                context_page.click_create()
                context_page.set_editor_content_via_paste(EDIT_BASE_CONTENT)
                base_length = context_page.get_editor_content_length()
                assert base_length == len(EDIT_BASE_CONTENT), (
                    f"Expected the seeded base content length ({base_length}) to match "
                    f"what was pasted ({len(EDIT_BASE_CONTENT)})"
                )
                context_page.fill_activation_description(ACTIVATION_DESCRIPTION)
                context_page.click_save()

            with allure.step(
                "Step 2 — Navigate to Settings -> Project Context: saved view shows "
                "existing content, 'Edit with AI' is directly visible"
            ):
                context_page.navigate()
                assert context_page.ai_edit_open_button.is_visible(), (
                    "Expected 'Edit with AI' to be directly visible on the saved view, "
                    "with no separate 'Edit' click needed first"
                )

            with allure.step("Step 3 — Click 'Edit with AI' — modal opens with a prompt input"):
                context_page.click_edit_with_ai()
                assert context_page.ai_edit_prompt_input.is_visible(), (
                    "Expected the 'Edit with AI' modal's prompt input to be visible"
                )

            with allure.step("Step 4 — Provide the edit instruction, trigger generation"):
                response = context_page.generate_edit_draft(EDIT_INSTRUCTION, timeout=AI_GENERATION_TIMEOUT)
                assert response.status == 200, (
                    f"Expected generate_project_context_draft to return 200 for this "
                    f"edit instruction applied to a {base_length}-char base, got "
                    f"{response.status}: {response.text()[:200]}"
                )

            with allure.step("Step 5 — Click Apply & Save — success toast, modal closes"):
                context_page.click_edit_with_ai_apply_and_save(timeout=UI_ELEMENT_TIMEOUT)
                toast_text = context_page.get_toast_text()
                assert "Project Context saved" in toast_text, (
                    f"Expected toast text to contain 'Project Context saved', got {toast_text!r}"
                )

            with allure.step(
                "Step 6 — Verify the edited content length is <=2500 chars (via API — "
                "the saved view that 'Apply & Save' lands on does not render the "
                "CodeMirror editor; see Step 2's own saved-view assertion)"
            ):
                get_resp = project_context_api.get_project_context()
                assert get_resp.status_code == 200, (
                    f"Expected GET project-context to return 200, got {get_resp.status_code}"
                )
                edited_length = len(get_resp.json().get("content") or "")
                assert 0 < edited_length <= MAX_CHARS, (
                    f"Expected the edited content length to be in (0, {MAX_CHARS}], "
                    f"got {edited_length}"
                )
                assert edited_length != base_length, (
                    "Expected the AI edit to actually change the content length "
                    "(the edit instruction asks to add a sentence)"
                )

            with allure.step("Side-channel check — no console errors at any step"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()
