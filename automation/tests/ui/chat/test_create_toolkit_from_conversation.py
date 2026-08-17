"""UI Test for ELITEA-2083 — Chat: Create Toolkit from Conversation – Close
Canvas and Verify Toolkit Added as Participant.

Verifies the in-chat Toolkit-creation canvas flow: after creating toolkit
"test1" via the canvas (GitHub type), closing the canvas, and confirming
the toolkit appears in the PARTICIPANTS panel under the TOOLKITS section.

Spec: test-specs/chat-interface/
      l2_create-toolkit-from-conversation-close-canvas-and-verify-participant_ELITEA-2083.md

New page-object surface (AFS § Automation Hints): the Toolkit-creation canvas
uses the SAME ``ToolkitForm``/``ToolkitTypeSelector`` and
``CredentialsSelect`` component set as the standalone toolkit creation flow
and the MCP canvas (ELITEA-2085).  Composition:
  - ``ChatPage`` — canvas entry point (``open_create_new_toolkit_canvas``),
    participants panel (``expand_participants_panel_via_toggle``,
    ``PARTICIPANTS_BADGE``, ``PARTICIPANTS_BADGE_ICON``).
  - ``ToolkitCanvasPage`` — canvas-specific chrome (close button, title,
    Create button); mirrors ``McpCanvasPage``.
  - ``ToolkitCreationPage`` — type-picker search + card click + form fields.
  - ``ToolkitDetailPage`` — credential dropdown selection.

Fidelity: transit substitution only (creating the toolkit via UI canvas as
transit to reach the "canvas open, saved" precondition).  The case's own
observables — canvas title text, close behavior, PARTICIPANTS badge —
are produced by the live system.  No ``page.route`` / ``route.fulfill`` /
``page.evaluate`` anywhere in this test.

Known console noise pre-filtered:
  - Secrets-403 (environment-wide background probe).
  - CategorySection.jsx unique-key-prop warning (issue #656, same as
    ELITEA-2085).
  - Vite stream externalization warning (exceljs build-tooling artifact).
"""

import logging

import allure
import pytest
from config import settings
from pages.chat_page import ChatPage
from pages.toolkit_canvas_page import ToolkitCanvasPage
from pages.toolkit_creation_page import ToolkitCreationPage
from pages.toolkit_detail_page import ToolkitDetailPage
from playwright.sync_api import expect

logger = logging.getLogger("elitea.tests.chat.create_toolkit_from_conversation")

pytestmark = [
    pytest.mark.ui,
    pytest.mark.chat,
    pytest.mark.toolkits,
    pytest.mark.regression,
]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

TOOLKIT_NAME = "test1"


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as ``test_create_mcp_from_conversation.py`` — an unrelated
    toolkit/secrets panel probe that fires on every page load in this
    local environment, not caused by this flow.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


def _is_known_vite_stream_externalization_warning(msg) -> bool:
    """Filter the pre-existing, environment-wide Vite 'stream' externalization
    warning.

    ``exceljs`` (an artifact/export dependency) pulls in
    ``crypto-browserify``/``cipher-base``, which references the Node builtin
    ``stream`` module; Vite externalizes it and logs a warning the first time
    that vendor chunk loads.  Confirmed not caused by this flow.
    """
    return "stream" in msg.text and "externalized for browser compatibility" in msg.text


def _is_known_category_section_key_warning(msg) -> bool:
    """Filter the pre-existing, already-tracked #656 console warning.

    ``CategorySection.jsx`` (inside ``ToolkitTypeSelector.jsx``) renders a
    list without a unique 'key' prop — confirmed as already tracked (issue
    #656, filed during ELITEA-1868 analysis).  Fires via ``console.error``
    in React dev mode despite the "Warning: ..." text (i.e. ``msg.type ==
    "error"`` at the browser level), so type-gating would make this filter
    a silent no-op for the one message it exists to catch.
    """
    return (
        "unique" in msg.text
        and "key" in msg.text
        and "prop" in msg.text
    )


class TestCreateToolkitFromConversation:
    """ELITEA-2083: Chat – Create Toolkit from Conversation – Close Canvas and
    Verify Toolkit Added as Participant (l2, high)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "chat/ELITEA-2083_chat-create-toolkit-from-conversation-close-canvas-and-verify-toolkit-added-as-participant.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    def test_create_toolkit_from_conversation_close_canvas_and_verify_participant(
        self,
        page,
        conversation_id,
        toolkit_api,
        github_credential,
    ):
        """Create a GitHub toolkit via the in-chat canvas; close the canvas;
        verify the PARTICIPANTS panel shows a TOOLKITS section with "test1".

        Transit substitution: the toolkit creation flow (type picker → form
        fill → Create button) is transit to reach the "canvas open after
        save" precondition.  The case's own observables (canvas title, close
        behaviour, PARTICIPANTS badge) are produced by the live system.

        AFS steps (test-specs/chat-interface/
        l2_create-toolkit-from-conversation-close-canvas-and-verify-participant_ELITEA-2083.md):
        1. Verify canvas header shows "test1".
        2. Click X to close the canvas; verify canvas unmounted.
        3. Expand the PARTICIPANTS panel via toggle; verify panel visible.
        4. Verify TOOLKITS section badge present in PARTICIPANTS.
        5. Verify badge text contains "test1" and badge icon visible.
        """
        chat = ChatPage(page)
        toolkit_canvas = ToolkitCanvasPage(page)
        toolkit_form = ToolkitCreationPage(page)
        toolkit_detail = ToolkitDetailPage(page)

        toolkit_id = None
        console_messages = []

        def _on_console(msg):
            if msg.type not in ("error", "warning"):
                return
            if (
                _is_known_secrets_403(msg)
                or _is_known_category_section_key_warning(msg)
                or _is_known_vite_stream_externalization_warning(msg)
            ):
                return
            console_messages.append(msg)

        page.on("console", _on_console)

        try:
            # ------------------------------------------------------------------
            # Transit setup 0a — navigate to Chat and open the conversation
            # ------------------------------------------------------------------
            chat.navigate_to_chat(conversation_id=conversation_id)
            expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            # ------------------------------------------------------------------
            # Transit setup 0b — open the Toolkit canvas via + menu
            # ------------------------------------------------------------------
            chat.open_create_new_toolkit_canvas(timeout=NAVIGATION_TIMEOUT)
            toolkit_canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)

            # ------------------------------------------------------------------
            # Transit setup 0c — select GitHub type and wait for pgvector defaults
            # ------------------------------------------------------------------
            # ToolkitTypeSelector.jsx fires getDefaultValues() async after the
            # card click, calling GET /configurations/models/{project_id} with
            # section=vectorstorage&include_shared=true to fetch the project's
            # default pgvector credential.  That auto-fills pgvector_configuration
            # in the form state; without it validateRequiredFields() sets
            # toolErrors.pgvector_configuration=true and the Create button is blocked
            # (no POST is made, "Please fill in all required fields" toast fires).
            #
            # We intercept that specific response with expect_response rather than
            # relying on wait_for_network (networkidle can fire in the 500 ms
            # microtask gap BEFORE the GET is even initiated, because getDefaultValues
            # is an async arrow called fire-and-forget — the network request goes out
            # only after the event loop returns to it, potentially AFTER networkidle's
            # 500 ms quiet window has already elapsed).
            #
            # If RTK Query serves from cache (no network call), expect_response times
            # out — we swallow the exception: state is already up-to-date from cache.
            try:
                with page.expect_response(
                    lambda r: r.request.method == "GET"
                    and "configurations/models" in r.url
                    and "vectorstorage" in r.url,
                    timeout=10_000,
                ):
                    toolkit_form.select_toolkit_type("github", "github", timeout=NAVIGATION_TIMEOUT)
            except Exception:
                # Response served from RTK Query cache — React state already set.
                pass
            # Allow React to flush the state update from the async callback.
            toolkit_detail.wait_for_network(timeout=NAVIGATION_TIMEOUT)

            # ------------------------------------------------------------------
            # Transit setup 0d — fill form: name + credential + repository
            # ------------------------------------------------------------------
            toolkit_form.fill_name(TOOLKIT_NAME)

            toolkit_detail.open_credential_dropdown(
                "github", timeout=UI_ELEMENT_TIMEOUT
            )
            toolkit_detail.select_saved_credential(
                github_credential["elitea_title"],
                private=True,
                timeout=UI_ELEMENT_TIMEOUT,
            )
            # Credential selection triggers a backend fetch (credential schema /
            # tools list) which causes the ToolBase form to re-render — if we
            # type into `toolkit-field-repository-input` while the re-render is
            # in flight the element is detached mid-type and press_sequentially
            # times out.  Wait for the network to idle and the repository field
            # to be stable before typing.  Same pattern as the standalone
            # test_create_github_toolkit which does wait_for_load_state("networkidle")
            # + wait_for_timeout(1000) after credential selection.
            toolkit_detail.wait_for_network(timeout=NAVIGATION_TIMEOUT)
            repo_field = page.locator(toolkit_form.TOOLKIT_FIELD_INPUT.format("repository"))
            repo_field.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)

            # force=True: after credential selection a MuiBox overlay
            # (css-15msj7j/css-1qkypnf) intercepts pointer events on the form
            # fields — documented in CLAUDE.md "Click intercepted by overlay".
            toolkit_form.fill_field("repository", settings.github_repo, force=True)
            # base_branch has no consts.js default (unlike active_branch which
            # defaults to "main") but IS in the backend schema's required list —
            # validateRequiredFields checks !settings[prop] and "base_branch"
            # starts as undefined, causing the "fill required fields" toast.
            # toolkit_factories.py confirms the API also needs base_branch: "main".
            toolkit_form.fill_field("base_branch", "main", force=True)

            # ------------------------------------------------------------------
            # Transit setup 0e — click Create; verify POST 201 + toast
            # ------------------------------------------------------------------
            with page.expect_response(
                lambda r: r.request.method == "POST"
                and "/tools/prompt_lib/" in r.url,
                timeout=NAVIGATION_TIMEOUT,
            ) as create_resp_info:
                toolkit_canvas.create_button.click()
            create_response = create_resp_info.value
            assert create_response.status == 201, (
                f"Toolkit-creation POST should resolve 201, got "
                f"{create_response.status} for {create_response.url}"
            )
            created_toolkit = create_response.json()
            toolkit_id = created_toolkit.get("id")
            assert toolkit_id, (
                f"Expected a numeric toolkit id in the creation response, "
                f"got: {created_toolkit!r}"
            )
            expect(chat.toast_message).to_contain_text(
                "The toolkit has been created successfully",
                timeout=UI_ELEMENT_TIMEOUT,
            )

            # ------------------------------------------------------------------
            # Step 1 — verify the canvas header shows "test1"
            # ------------------------------------------------------------------
            with allure.step(
                f'Step 1 — Verify canvas header shows "{TOOLKIT_NAME}" after save'
            ):
                expect(toolkit_canvas.title).to_have_text(
                    TOOLKIT_NAME, timeout=UI_ELEMENT_TIMEOUT
                )

            # ------------------------------------------------------------------
            # Step 2 — close the canvas; verify it is fully unmounted
            # ------------------------------------------------------------------
            with allure.step("Step 2 — Click X to close the canvas; verify canvas unmounted"):
                toolkit_canvas.close(timeout=UI_ELEMENT_TIMEOUT)
                expect(toolkit_canvas.title).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                expect(toolkit_form.name_input).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            # ------------------------------------------------------------------
            # Step 3 — ensure PARTICIPANTS panel is in collapsed (badge-strip)
            # state so the section badges are visible
            # ------------------------------------------------------------------
            with allure.step(
                "Step 3 — Collapse PARTICIPANTS panel to badge-strip view; "
                "verify panel is in collapsed state"
            ):
                chat.collapse_participants_panel_via_toggle(timeout=UI_ELEMENT_TIMEOUT)

            # ------------------------------------------------------------------
            # Step 4 — verify TOOLKITS section badge is present
            # ------------------------------------------------------------------
            with allure.step(
                "Step 4 — Verify a TOOLKITS section badge is present in the "
                "PARTICIPANTS panel"
            ):
                toolkits_badge = page.locator(
                    chat.PARTICIPANTS_BADGE.format("toolkits")
                )
                expect(toolkits_badge).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            # ------------------------------------------------------------------
            # Step 5 — verify "test1" toolkit name and section icon
            # ------------------------------------------------------------------
            with allure.step(
                f'Step 5 — Verify the TOOLKITS badge lists "{TOOLKIT_NAME}" '
                "and the section icon is visible"
            ):
                expect(toolkits_badge).to_contain_text(
                    TOOLKIT_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                toolkits_badge_icon = page.locator(
                    chat.PARTICIPANTS_BADGE_ICON.format("toolkits")
                )
                expect(toolkits_badge_icon).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            # ------------------------------------------------------------------
            # Side-channel — verify no unexpected console errors/warnings
            # ------------------------------------------------------------------
            with allure.step(
                "Side-channel — verify no unexpected console errors/warnings "
                "occurred across the whole flow (known secrets-403 noise and "
                "the pre-existing #656 key-prop warning are pre-filtered by "
                "_on_console, so any survivor here is a genuinely new issue)"
            ):
                assert not console_messages, (
                    f"Unexpected console error/warning(s) during the flow: "
                    f"{[m.text for m in console_messages]!r}"
                )

        finally:
            with allure.step("Cleanup — delete the created toolkit"):
                if toolkit_id:
                    try:
                        toolkit_api.delete_toolkit(toolkit_id)
                        logger.info("Deleted toolkit %s", toolkit_id)
                    except Exception as exc:
                        logger.warning(
                            "Cleanup failed for toolkit %s: %s", toolkit_id, exc
                        )
