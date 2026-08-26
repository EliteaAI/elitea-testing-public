"""UI test — "Build with AI" generates Project Context content and inserts it
into the editor, where it stays editable until Save.

Walks the real user path: empty state -> Build with AI -> the dialog opens ->
type a project description -> Generate Draft (a LIVE model call) -> the review
form is pre-populated with the draft -> Apply -> the draft lands in the editor
verbatim -> one more character proves it is still editable, and the API confirms
nothing has been saved.

Fidelity (no substitution): the draft is produced by a live
POST /elitea_core/generate_project_context_draft/prompt_lib/{project_id}. Its
response body is the ORACLE -- the review field and the editor are asserted
against the response, never against a hand-written payload, so every asserted
value comes from the product while the assertion stays fully deterministic
(.agents/testing.md, "How to test a NONDETERMINISTIC producer without
substituting it"). No page.route / route.fulfill / monkeypatch / page.evaluate
anywhere in this spec. Precedent: tests/ui/agents/test_agent_build_with_ai.py
(ELITEA-1909/1911), same shared GenerateEntityModal shell.

Case-text divergence (declared, reverse-masking guard): the case calls the
target the "Project Background editor". No section of that name exists in the
product -- it is the Project Context editor at /settings/project-context/edit.
Already filed as clarification #1792 (module-wide, ELITEA-2266 analysis); not
re-filed. Note the review form inside the dialog DOES carry a "Project
Background" field label, which is where the case's wording comes from.

Test case: ELITEA-2269
AFS: test-specs/settings-project-params/l3_project-context-build-with-ai-generates-content_ELITEA-2269.md
"""

import logging

import allure
import pytest
from pages.generate_project_context_modal_page import GenerateProjectContextModalPage
from pages.project_context_page import ProjectContextPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

#: The live generation took ~5-20s in exploration (2026-08-26). Same constant
#: name and value as tests/ui/agents/test_agent_build_with_ai.py's live path.
LIVE_GENERATE_RESPONSE_TIMEOUT = 30_000

#: The project description typed into the dialog (case step 4). Only the INPUT
#: is authored; everything asserted afterwards comes from the model's response.
PROJECT_DESCRIPTION = (
    "Elitea is an AI collaboration platform. The team uses React on the frontend "
    "and Python on the backend. Deployment is via Kubernetes."
)

#: One extra character, typed to prove the inserted draft is still editable
#: (case step 6).
INLINE_EDIT_CHAR = "!"

#: PROJECT_CONTEXT_MAX_LEN in projectContext.constants.js.
MAX_CHARS = 2500


def _normalize(text: str) -> str:
    """Collapse whitespace the way Playwright normalizes actual text.

    ``expect(locator).to_have_text([...])`` trims and collapses whitespace in the
    ACTUAL text only, so a generated line such as ``"  - nested"`` would never
    match an un-normalized expectation. Normalizing the expected side the same
    way keeps the comparison exact in content while tolerant of the rendering's
    own whitespace handling -- it never drops or reorders a line.
    """
    return " ".join(text.split())


class TestProjectContextBuildWithAI:
    """ELITEA-2269 — Build with AI generates project context content."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/project-params/ELITEA-2269_build-with-ai-button-generates-project-context-content.md",
        "onetest-ai Test Case link",
    )
    def test_build_with_ai_generates_content_and_stays_editable(self, page, api, clean_project_context):
        """Build with AI produces a real draft, the UI carries it into the editor
        unchanged, and the generated content is still editable before saving."""
        context_page = ProjectContextPage(page)
        modal = GenerateProjectContextModalPage(page)
        console_errors = collect_console_errors(page)
        api_path = f"/elitea_core/project_context/prompt_lib/{api.project_id}/project-context"

        with allure.step("Step 1 — Navigate to Settings -> Project Context"):
            context_page.navigate()
            expect(context_page.build_with_ai_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 2 — Click the 'Build with AI' button"):
            context_page.click_build_with_ai()
            assert page.url.endswith("/settings/project-context/edit"), (
                f"Build with AI should open the editor route, got {page.url}"
            )

        with allure.step("Step 3 — Verify the AI-assisted input dialog appears"):
            expect(modal.modal).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(modal.modal.locator("h2")).to_have_text("Build with AI")
            expect(modal.prompt_input).to_be_visible()
            expect(modal.prompt_input).to_have_value("")
            expect(modal.generate_button).to_be_disabled()

        with allure.step("Step 4 — Provide a description of the project and generate the draft"):
            modal.fill_prompt(PROJECT_DESCRIPTION)
            expect(modal.generate_button).to_be_enabled()

            response = modal.click_generate_and_wait_for_response(
                timeout=LIVE_GENERATE_RESPONSE_TIMEOUT
            )
            assert response.status == 200, (
                f"Live generate-draft call failed: {response.status} {response.url}"
            )
            draft = response.json()
            generated = draft.get("project_background") or ""
            assert generated.strip(), (
                "The generate-draft response carried no project_background content: "
                f"{list(draft)}"
            )

            modal.wait_for_review_form(timeout=LIVE_GENERATE_RESPONSE_TIMEOUT)
            expect(modal.review_background_input).to_be_visible()
            assert modal.get_review_background() == generated, (
                "The review form's Project Background field does not match the "
                "generated draft the API returned — the UI dropped or mangled it"
            )

        with allure.step("Step 5 — Apply and verify the generated content lands in the editor"):
            modal.click_apply()
            expect(modal.modal).to_have_count(0)

            expected_lines = [_normalize(line) for line in generated.split("\n")]
            expect(context_page.editor_lines()).to_have_text(
                expected_lines, timeout=UI_ELEMENT_TIMEOUT
            )
            expect(context_page.save_button).to_be_enabled()

            unsaved = api.get(api_path)
            assert unsaved.status_code == 200, f"Project Context GET failed: {unsaved.status_code}"
            assert unsaved.json().get("content") == "", (
                "Apply must not persist anything — the server already holds content"
            )

        with allure.step("Step 6 — Verify the generated content is editable before saving"):
            expect(context_page.char_counter).to_have_text(
                f"{MAX_CHARS - len(generated)} characters left.", timeout=UI_ELEMENT_TIMEOUT
            )

            context_page.type_at_end_of_content(INLINE_EDIT_CHAR)
            expect(context_page.editor_lines().last).to_contain_text(INLINE_EDIT_CHAR)
            expect(context_page.char_counter).to_have_text(
                f"{MAX_CHARS - len(generated) - 1} characters left.", timeout=UI_ELEMENT_TIMEOUT
            )

            still_unsaved = api.get(api_path)
            assert still_unsaved.json().get("content") == "", (
                "Everything above must happen BEFORE saving — the server holds content"
            )

        with allure.step("Axis 2 — No console errors during the Build with AI flow"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
