"""UI Tests for ELITEA-2082/2083/2080 — Chat: Create Toolkit from Conversation
Canvas (Save / Close-and-Verify-Participant / Discard).

Family AFS for three flow-variant cases sharing one surface — the in-chat
"+ Create New Toolkit" canvas opened from a conversation's ``+`` menu:

- ELITEA-2080: enter data in the canvas, click Discard, confirm, verify the
  canvas resets all the way back to the "Choose the toolkit type" step with
  nothing persisted.
- ELITEA-2082: select the Artifact type, fill Name/Bucket, click the
  create-mode action button (live label "Create" — case-text-drift
  clarification #1011, the case itself calls it "Save"), verify the
  toolkit-creation POST resolves 201, the success toast, and the canvas
  header updating to the toolkit's name.
- ELITEA-2083: continuing from ELITEA-2082's saved "test1" toolkit (same
  canvas, still open), close the canvas and verify the toolkit now appears
  as a participant under the PARTICIPANTS panel's TOOLKITS section.

ELITEA-2082 and ELITEA-2083 are automated as ONE continuous test
(``test_save_toolkit_and_verify_participant_added``) rather than two
independent tests — ELITEA-2083's own precondition text literally continues
from ELITEA-2082's saved state ("Toolkit 'test1' has been saved and the
canvas is still open"), so splitting them would mean re-deriving that
precondition a second time for no benefit (AFS § Automation Hints).
ELITEA-2080 is fully standalone (``test_discard_clears_new_toolkit_canvas``).

Spec: test-specs/chat-interface/l2_create-toolkit-from-conversation-canvas_ELITEA-2082-2083-2080.md

New page-object surface (this implementation): no existing ``ChatPage``
method drove the in-chat "New Toolkit" canvas before this case.
``ChatPage`` gained ``toolkits_menuitem``/``toolkits_create_new_button`` +
``open_create_new_toolkit_canvas()`` (mirrors the ELITEA-2166
``agents_menuitem``/``open_create_new_agent_canvas()`` precedent 1:1), plus
``chat_participants_panel``/``chat_participants_panel_toggle_button`` +
``expand_participants_panel_via_toggle()``/
``is_participants_panel_expanded_via_testid()`` (testid-only replacements for
the legacy ``expand_participants_panel()``/``is_participants_panel_expanded()``,
left untouched — additive only) + ``get_toolkit_participant_row()`` (reuses
the existing ``PARTICIPANT_ROW`` dynamic-testid template, no new template
needed). New page object ``ToolkitCanvasPage`` (mirrors ``AgentCanvasPage``)
owns ONLY the canvas-specific chrome with no ``ToolkitCreationPage``
equivalent — the type-picker/form fields (``type_search_input``,
``TOOLKIT_TYPE_CARD``, ``name_input``, ``TOOLKIT_FIELD_INPUT``) are reused
directly from ``ToolkitCreationPage(page)``, confirmed live-working as-is in
this chat-canvas context (same underlying components as the standalone
``/toolkits/create`` wizard).

Testid gaps filled this implementation (``add-data-testid``, committed +
pushed to ``automation/testids``, EliteaAI/EliteaUI@4ca95ada) — scoped ONLY
to elements this family's tests touch, never blanket-added to sibling
editors (Agent/Pipeline/Artifact) sharing the same components:
- ``toolkit-form-create-button`` — ``CreateToolkitButton.jsx``'s own
  ``<Button.BaseBtn>``, previously zero testid/props threading.
- ``toolkit-canvas-title`` / ``toolkit-canvas-close-button`` — threaded as
  ``titleTestId``/``closeButtonTestId`` at ``ToolkitEditor.jsx``'s
  ``<BaseEditor>`` call site (``BaseEditor``/``EditorHeader`` already
  support both props — no shared-component change needed, mirrors
  ``AgentEditor.jsx``'s existing usage of the same two props).
- ``toolkit-canvas-discard-button`` / ``toolkit-canvas-discard-confirm-dialog``
  / ``toolkit-canvas-discard-confirm-button`` — required threading 3 NEW
  optional props (``discardButtonTestId``/``discardModalTestId``/
  ``discardConfirmButtonTestId``) through the SHARED ``BaseEditor.jsx`` ->
  ``EditorHeader.jsx`` -> ``Button.DiscardButton`` chain into
  ``DiscardButton.jsx``'s ALREADY-EXISTING ``dataTestId``/``modalDataTestId``/
  ``confirmButtonDataTestId`` props (no change inside ``DiscardButton.jsx``
  itself) — wired ONLY at ``ToolkitEditor.jsx``'s own call site; every other
  editor's Discard button is untouched (no testid, unchanged behavior).

Declared improvisation (canon gap, `.agents/role-overrides.md` §
Declared-improvisation protocol): the AFS's own "needs-adding" table left
the canvas's post-save Save-mode button (``SaveToolkitButton.jsx``, a
DIFFERENT component from the create-mode button) as "not a hard blocker,"
suggesting either a new testid or reuse of an existing one — investigation
during Phase 2 confirmed no existing testid fits (``toolkit-form-save-button``
already belongs to the UNRELATED standalone-wizard's own Save button,
``CreateToolkitToolTabBar.jsx``). Rather than add a 7th testid whose only
use would be a text-content read no case actually needs, this test proves
the create-to-save mode transition via ``expect(create_button).to_have_count(0)``
— a testid-only ABSENCE assertion on the element already added and clicked
(canon ruling #511 extension: absence assertions count as references) —
combined with the persisted toast text, the 201 response, and the header
title update, which is a stronger/more-independent confirmation set than a
single button-label read would have been.

Known defects found: none (Coverage Map's Axis-2 "Known Defects Found"
section is empty). Two CASE-TEXT-DRIFT clarifications were filed during
analysis (reverse-masking guard — live product is correct, case wording is
stale), neither blocking automation and both asserted as the LIVE contract
below:
- ``#1010`` — ELITEA-2080's search text is "Artifact" (singular), not the
  case's literal "Artifacts" (plural), which would filter out the very card
  step 5 needs (the type-picker's search is a plain substring match).
- ``#1011`` — the create-mode button's live label is "Create", not the
  case's "Save" (it flips to "Save" only after a successful create).
"""

import logging

import allure
import pytest
from playwright.sync_api import expect

from pages.chat_page import ChatPage
from pages.toolkit_canvas_page import ToolkitCanvasPage
from pages.toolkit_creation_page import ToolkitCreationPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.toolkits, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds) — same values as the sibling chat/toolkit
# suites (test_create_agent_via_chat_canvas.py / toolkit_creation_page.py callers)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
DIALOG_TIMEOUT = 10_000

# Filed separately, non-gating — fires on every visit to the "Choose the
# toolkit type" step regardless of this flow (already tracked, issue #291;
# AFS § Known Defects Found / § Automation Hints).
KNOWN_NONGATING_CONSOLE_SIGNATURES = (
    'Each child in a list should have a unique "key" prop',
)


def _is_known_nongating_console_error(text: str) -> bool:
    return any(sig in text for sig in KNOWN_NONGATING_CONSOLE_SIGNATURES)


def _is_known_secrets_403(msg) -> bool:
    """Filter the pre-existing, environment-wide ``secrets`` 403 noise.

    Same idiom as ``test_create_agent_via_chat_canvas.py`` — an unrelated
    toolkit/secrets panel probe that fires on every page load in this local
    environment, not caused by this flow.
    """
    text = msg.text
    location_url = (msg.location or {}).get("url", "")
    return "403" in text and "secrets/secrets/default" in (text + location_url)


def _is_gating_console_error(msg) -> bool:
    """Return True for a console message this test should fail on.

    Excludes the pre-existing secrets-403 noise and the already-tracked
    React key-prop warning (#291) — same two-filter idiom as
    ``test_create_agent_via_chat_canvas.py`` / ``test_toolkit_creation_cancel_no_toolkit_no_bucket.py``.
    """
    return (
        msg.type == "error"
        and not _is_known_secrets_403(msg)
        and not _is_known_nongating_console_error(msg.text)
    )


@allure.epic("Chat")
@allure.feature("In-Chat Toolkit Canvas")
class TestCreateToolkitFromConversation:
    """ELITEA-2082/2083/2080: Chat — Create Toolkit from Conversation canvas (l2, high)."""

    @pytest.mark.p1
    @allure.title("Discard on the in-chat New Toolkit canvas clears all entered data")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/chat/canvas/"
        "ELITEA-2080_chat-create-toolkit-from-conversation-enter-data-and-discard-changes.md",
        "onetest-ai Test Case link",
    )
    def test_discard_clears_new_toolkit_canvas(self, page):
        """Enter data into the New Toolkit canvas, Discard, confirm, and verify
        the canvas resets all the way back to the type-picker with nothing
        persisted.

        Steps (AFS
        test-specs/chat-interface/l2_create-toolkit-from-conversation-canvas_ELITEA-2082-2083-2080.md,
        ELITEA-2080 rows):
        1. Navigate to Chats, open a new conversation.
        2. + menu -> Toolkits -> + Create New Toolkit; verify the canvas
           opens on "Choose the toolkit type" with Discard/Create disabled.
        3. Search "Artifact" (singular — clarification #1010); verify
           exactly 2 type cards render, one of them the Artifact card.
        4. Click the Artifact card; verify the canvas heading becomes
           "New Artifact Toolkit".
        5. Fill Name="test"; verify Discard/Create both become enabled.
        6. Fill Bucket="test".
        7. Click Discard; verify the Warning dialog appears.
        8. Confirm Discard.
        9. Verify the canvas resets all the way back to the type-picker
           step (title, search field, Discard/Create disabled again).
        """
        chat = ChatPage(page)
        toolkit_canvas = ToolkitCanvasPage(page)
        toolkit_creation = ToolkitCreationPage(page)

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if _is_gating_console_error(msg) else None,
        )

        with allure.step("Step 1 — Navigate to Chats, open a new conversation"):
            chat.navigate_to_chat()
            chat.wait_for_page_load()
            chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)
            expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            assert chat.get_message_count() == 0, (
                "A freshly-opened conversation should start with zero messages"
            )

        with allure.step(
            "Step 2 — Click + icon -> Toolkits -> + Create New Toolkit; "
            "verify the New Toolkit canvas opens with Discard/Create disabled"
        ):
            chat.open_create_new_toolkit_canvas(timeout=NAVIGATION_TIMEOUT)
            toolkit_canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)
            expect(toolkit_canvas.title).to_have_text("New Toolkit", timeout=UI_ELEMENT_TIMEOUT)
            assert not toolkit_canvas.is_discard_enabled(), (
                "Discard should be disabled before any field is dirty"
            )
            expect(toolkit_canvas.create_button).to_be_disabled(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step(
            'Step 3 — Search "Artifact" (singular — clarification #1010) in '
            "the type-picker; verify exactly 2 type cards render, one of "
            "them the Artifact card"
        ):
            toolkit_creation.search_toolkit_type("Artifact")
            assert toolkit_creation.count_type_cards(timeout=UI_ELEMENT_TIMEOUT) == 2, (
                "Searching 'Artifact' should surface exactly 2 type cards "
                "(the plain Artifact card + the unrelated 'Elitea Artifacts' MCP card)"
            )
            expect(toolkit_creation.get_type_card("artifact")).to_be_visible(
                timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            'Step 4 — Click the Artifact type card; verify the canvas '
            'heading becomes "New Artifact Toolkit"'
        ):
            toolkit_creation.get_type_card("artifact").click()
            expect(toolkit_creation.name_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(toolkit_canvas.title).to_have_text(
                "New Artifact Toolkit", timeout=UI_ELEMENT_TIMEOUT
            )

        with allure.step(
            'Step 5 — Fill Toolkit Name="test"; verify Discard/Create both become enabled'
        ):
            toolkit_creation.fill_name("test")
            assert toolkit_creation.name_input.input_value() == "test"
            assert toolkit_canvas.is_discard_enabled(), (
                "Discard should be enabled once the form is dirty"
            )
            expect(toolkit_canvas.create_button).to_be_enabled(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step('Step 6 — Fill Bucket="test"'):
            toolkit_creation.fill_field("bucket", "test")
            assert toolkit_creation.get_field_value("bucket") == "test"

        with allure.step("Step 7 — Click Discard; verify the Warning dialog appears"):
            toolkit_canvas.discard_button.click()
            expect(toolkit_canvas.discard_confirm_dialog).to_be_visible(timeout=DIALOG_TIMEOUT)
            expect(toolkit_canvas.discard_confirm_dialog).to_contain_text(
                "Are you sure you want to discard changes?"
            )

        with allure.step('Step 8 — Click the dialog\'s "Discard" (confirm) button'):
            toolkit_canvas.discard_confirm_button.click()
            expect(toolkit_canvas.discard_confirm_dialog).to_be_hidden(timeout=DIALOG_TIMEOUT)

        with allure.step(
            "Step 9 — Verify the canvas remains open and resets all the way "
            "back to the 'Choose the toolkit type' step"
        ):
            expect(toolkit_canvas.title).to_have_text("New Toolkit", timeout=UI_ELEMENT_TIMEOUT)
            expect(toolkit_creation.type_search_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            assert toolkit_creation.type_search_input.input_value() == "", (
                "Type-picker search field should be empty after Discard resets the canvas"
            )
            assert not toolkit_canvas.is_discard_enabled(), (
                "Discard should be disabled again after the reset"
            )
            expect(toolkit_canvas.create_button).to_be_disabled(timeout=UI_ELEMENT_TIMEOUT)

        assert not console_errors, f"Unexpected console errors: {[m.text for m in console_errors]!r}"

    @pytest.mark.p1
    @allure.title(
        "Save toolkit from chat canvas, then verify it appears as a PARTICIPANTS TOOLKITS entry"
    )
    @allure.severity(allure.severity_level.NORMAL)
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/chat/canvas/"
        "ELITEA-2082_chat-create-toolkit-from-conversation-save-toolkit-and-verify-creation-success.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/chat/canvas/"
        "ELITEA-2083_chat-create-toolkit-from-conversation-close-canvas-and-verify-toolkit-added-as-part.md",
        "onetest-ai Test Case link",
    )
    def test_save_toolkit_and_verify_participant_added(self, page, toolkit_api):
        """Create an Artifact toolkit via the in-chat canvas, verify creation
        success (ELITEA-2082), then close the canvas and verify the toolkit
        appears under the PARTICIPANTS panel's TOOLKITS section
        (ELITEA-2083 — continues from ELITEA-2082's saved state, same canvas).

        Steps (AFS, ELITEA-2082 then ELITEA-2083 rows):
        1. Navigate to Chats, open a new conversation.
        2. + menu -> Toolkits -> + Create New Toolkit; verify the canvas opens.
        3. Click the Artifact type card directly (no search needed).
        4. Fill Name="test1"; verify header live-updates to "test1".
        5. Fill Bucket="test1".
        6. Click the create-mode action button (live label "Create" —
           clarification #1011); verify the 201 response, the success
           toast, the header showing "test1", the create-mode button
           unmounting (mode-flip evidence), and Discard disabling again.
        7. Re-verify the canvas header still shows "test1".
        --- ELITEA-2083 continues here, same canvas still open ---
        8. Click the canvas's X (close) button; verify the canvas is gone,
           the composer is shown again, and the collapsed TOOLKITS badge
           appears.
        9. Expand the PARTICIPANTS panel.
        10. Verify a TOOLKITS section is present (proven indirectly via the
            row's own presence, AFS § Automation Hints — ParticipantSection
            only renders when its group is non-empty).
        11. Verify "test1" is listed under TOOLKITS with a toolkit icon
            (proven by construction: locating the row via its
            toolkit-flavored composed testid IS the toolkit-icon proof,
            since entityType there is derived directly from entity_name).
        """
        chat = ChatPage(page)
        toolkit_canvas = ToolkitCanvasPage(page)
        toolkit_creation = ToolkitCreationPage(page)

        toolkit_id = None
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if _is_gating_console_error(msg) else None,
        )

        try:
            with allure.step("Step 1 — Navigate to Chats, open a new conversation"):
                chat.navigate_to_chat()
                chat.wait_for_page_load()
                chat.click_create_conversation(timeout=NAVIGATION_TIMEOUT)
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 2 — Click + icon -> Toolkits -> + Create New Toolkit; "
                "verify the New Toolkit canvas opens"
            ):
                chat.open_create_new_toolkit_canvas(timeout=NAVIGATION_TIMEOUT)
                toolkit_canvas.wait_for_open(timeout=UI_ELEMENT_TIMEOUT)
                expect(toolkit_canvas.title).to_have_text("New Toolkit", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                'Step 3 — Click the Artifact type card directly (no search '
                'needed); verify the canvas heading becomes "New Artifact Toolkit"'
            ):
                toolkit_creation.get_type_card("artifact").click()
                expect(toolkit_creation.name_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(toolkit_canvas.title).to_have_text(
                    "New Artifact Toolkit", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                'Step 4 — Fill Toolkit Name="test1"; verify the canvas '
                'header live-updates to "test1"'
            ):
                toolkit_creation.fill_name("test1")
                assert toolkit_creation.name_input.input_value() == "test1"
                expect(toolkit_canvas.title).to_have_text("test1", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step('Step 5 — Fill Bucket="test1"'):
                toolkit_creation.fill_field("bucket", "test1")
                assert toolkit_creation.get_field_value("bucket") == "test1"

            with allure.step(
                "Step 6 — Click the create-mode action button (live label "
                "'Create' — clarification #1011); verify the creation POST "
                "resolves 201, the success toast, the header STILL showing "
                "'test1', the create-mode button unmounting (mode-flip "
                "evidence, declared improvisation — see module docstring), "
                "and Discard disabling again"
            ):
                with page.expect_response(
                    lambda r: r.request.method == "POST"
                    and "/tools/prompt_lib/" in r.url
                ) as resp_info:
                    toolkit_canvas.click_create()
                create_response = resp_info.value
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

                expect(toolkit_canvas.success_toast_message).to_have_text(
                    "The toolkit has been created successfully", timeout=UI_ELEMENT_TIMEOUT
                )
                expect(toolkit_canvas.title).to_have_text("test1", timeout=UI_ELEMENT_TIMEOUT)
                expect(toolkit_canvas.create_button).to_have_count(0, timeout=UI_ELEMENT_TIMEOUT)
                assert not toolkit_canvas.is_discard_enabled(), (
                    "Discard should be disabled again once the form is clean post-save"
                )

            with allure.step('Step 7 — Re-verify the canvas header still shows "test1"'):
                expect(toolkit_canvas.title).to_have_text("test1", timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 8 — Click the canvas's X (close) button; verify the "
                "canvas is gone, the composer is shown again, and the "
                "collapsed TOOLKITS badge count reads '1' (AFS ELITEA-2083 "
                "Axis-2: an earlier, cheaper confirmation that the "
                "participant was actually attached, independent of the "
                "later expanded-panel assertion)"
            ):
                toolkit_canvas.close(timeout=UI_ELEMENT_TIMEOUT)
                expect(toolkit_canvas.title).to_be_hidden(timeout=UI_ELEMENT_TIMEOUT)
                expect(chat.message_input).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                chat.wait_for_participants_badge_count(
                    "1", section="toolkits", timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step("Step 9 — Expand the PARTICIPANTS panel"):
                chat.expand_participants_panel_via_toggle(timeout=UI_ELEMENT_TIMEOUT)
                assert chat.is_participants_panel_expanded_via_testid(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 10/11 — Verify the TOOLKITS section is present and "
                "'test1' is listed with a toolkit icon (the row's own "
                "presence proves the section rendered — AFS § Automation "
                "Hints; the toolkit-flavored composed testid IS the icon "
                "proof, by construction)"
            ):
                row = chat.get_toolkit_participant_row(toolkit_id)
                expect(row).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(row).to_contain_text("test1")

            assert not console_errors, (
                f"Unexpected console errors: {[m.text for m in console_errors]!r}"
            )
        finally:
            with allure.step("Cleanup — delete the created toolkit"):
                if toolkit_id:
                    try:
                        toolkit_api.delete_toolkit(toolkit_id)
                        logger.info("Deleted toolkit %s", toolkit_id)
                    except Exception as exc:
                        logger.warning("Cleanup failed for toolkit %s: %s", toolkit_id, exc)
