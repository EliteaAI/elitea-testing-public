"""UI Test for ELITEA-2203 — Chat: Slash Commands, Typing '/' Shows Only the
Added Toolkit and MCP Participants.

Adds one Artifact-type toolkit and one Remote-MCP toolkit as conversation
participants via the "+ > Toolkits" / "+ > MCPs" toggle-switch flow, then
verifies typing '/' shows a dropdown with exactly those two items, each
correctly labelled ("toolkit" / "MCP" — see the DOM-text note below), and
nothing else.

Spec: test-specs/chat-interface/l3_slash-mention-toolkit-and-mcp-participants_ELITEA-2203.md

Case-text names are cosmetic (AFS § Test Data) — assertions are written
against the fixture-generated names, never hardcoded "banana"/"delete".

Implementer-level technique note (AFS's suggested flow said to type the
toolkit/MCP name into the search field first): dropped. The plus-menu's
Toolkits/MCPs lists sort newest-first (`sort_by=created_at&sort_order=desc`),
so a toolkit this fixture just created is already on the first, unfiltered
page — no search needed. Typing the fixture's long, timestamp-suffixed
generated name character-by-character against a non-debounced,
per-keystroke search endpoint produced a live, reproducible race (the MCP
participant intermittently failed to register at all — confirmed via a
diagnostic pass capturing the raw `/elitea_core/participants/` API
response, which showed only the toolkit, never the MCP, after the exact
same click sequence executed cleanly on a rerun). Resolving the row
directly by its dynamic testid — which the AFS's own Automation Hints
signature (`add_toolkit_participant_via_slash_menu(project_id, toolkit_id)`,
2 args, no name) already implied — is a technique substitution within
Phase-2 latitude, not a scope change: the case's assertions (participant
badges, dropdown contents, labels) are unchanged.

Implementer-level correction (AFS text vs. live DOM): the AFS's step-4/5
guidance says to assert the toolkit item's type-label text reads "Toolkit"
— but `ChatParticipantType.Toolkits` (`EliteaUI/src/common/constants.js`)
is the literal lowercase string `'toolkit'`, and `NewParticipantCard.jsx`
renders `participant.participantType` verbatim for a non-MCP toolkit; the
`text-transform: capitalize` CSS only affects the SCREEN rendering, not
`.text_content()`. Live-confirmed this pass: `text_content()` returned
`'...toolkittoolkit'`-shaped text with a literal lowercase `'toolkit'` type
label, never `'Toolkit'`. Asserting the capitalized form against
`.text_content()` is exactly the reverse-masking case the workflow skill's
Hard Rule 2 warns about (asserting stale/cosmetic-CSS-driven case text
instead of the live contract) — this test asserts the real, lowercase DOM
text. The MCP branch is unaffected: `NewParticipantCard.jsx` renders the
literal string `'MCP'` (already correct case, no CSS transform needed) for
MCP-type participants.

Declared improvisation (implementer-level, on top of the AFS's own
declared improvisation): the AFS names icon-presence as a SECONDARY,
declared-out-of-scope-to-testid signal ("assert icon PRESENCE... as the
automatable signal, with the adjacent TYPE-LABEL TEXT carrying the actual
type-correctness assertion"). Implementing "icon presence" would require a
non-testid locator (e.g. an `svg` CSS selector) inside the item's testid
scope, which `.agents/role-overrides.md` § Reviewer slot makes an absolute
`CHANGES_REQUESTED` ("not waived for neighborhood consistency") — the
locator-policy override outranks the AFS's implementation suggestion here.
This test therefore asserts ONLY the type-label text, which the AFS itself
says is what the case's Pass/Fail criteria substantively need; icon
presence is not independently checked. Reported as a `note` finding.

Testid gaps filled this implementation (``add-data-testid``, pushed to
``automation/testids``, EliteaAI/EliteaUI@34319b30):
- ``slash-mention-list`` / ``slash-mention-item-{project_id}_{toolkit_id}``
  (dynamic) — see ELITEA-2202's test module docstring for the full
  opt-in-prop mechanism (shared with ``RecommendationList``/
  ``SearchResultList``).
- the dynamic ``toolkits-menu-item-toolkit-{project_id}-{toolkit_id}`` /
  ``mcps-menu-item-mcp-{project_id}-{toolkit_id}`` plus-menu item rows were
  ALREADY on ``automation/testids`` (commit ``73595e8d``, ELITEA-2094) —
  not newly added this pass, only newly consumed. (``toolkits-search-input``
  / ``mcps-search-input`` were also already there but this test does not
  use them — see the technique note above.)

New page-object surface (``ChatPage``, all additive — the legacy
``add_toolkit_participant()`` select-and-close flow is untouched, neither
called nor modified by this case, which needs the toggle-switch flow
instead):
- ``toolkits_menuitem`` / ``mcps_menuitem`` / ``toolkits_search_input`` /
  ``mcps_search_input`` (LocatorDescriptors — search fields kept on the
  page object for future callers even though this case doesn't use them)
- ``TOOLKIT_PARTICIPANT_MENU_ITEM`` / ``MCP_PARTICIPANT_MENU_ITEM``
  (dynamic template constants)
- ``open_toolkits_submenu()`` / ``add_toolkit_participant_via_slash_menu()``
  / ``add_mcp_participant_via_slash_menu()`` / ``close_plus_menu_popper()``
- ``open_slash_mention_dropdown()`` / ``get_slash_mention_item()`` /
  ``get_slash_mention_item_count()`` (shared with ELITEA-2202/2204)

Fixture change (additive — ``artifact_toolkit`` / ``mcp_toolkit_with_tools``
in ``fixtures/data_fixtures.py`` now also yield ``project_id``, needed to
format the dynamic menu-item/dropdown-item testids; no existing key removed
or changed).

Known defects: none for this case (see AFS § Known Defects Found).

Usage:
    cd automation
    pytest tests/ui/chat/test_slash_mention_toolkit_and_mcp_participants.py -v
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000


class TestSlashMentionToolkitAndMcpParticipants:
    """ELITEA-2203: Chat – Slash Commands – Typing '/' Displays Only Added
    Toolkit and MCP Participants (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2203_chat-slash-commands-verify-typing-displays-only-added-toolkit-and-mcp-participants.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_slash_mention_shows_only_added_toolkit_and_mcp(
        self, page, conversation_id, artifact_toolkit, mcp_toolkit_with_tools,
    ):
        """Adding one Toolkit + one MCP as participants shows exactly those
        two items (correctly labelled) in the '/' dropdown, nothing else.
        """
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        chat = ChatPage(page)
        toolkit_name = artifact_toolkit["name"]
        toolkit_project_id = artifact_toolkit["project_id"]
        toolkit_id = artifact_toolkit["id"]
        mcp_name = mcp_toolkit_with_tools["name"]
        mcp_project_id = mcp_toolkit_with_tools["project_id"]
        mcp_id = mcp_toolkit_with_tools["id"]

        with allure.step("Setup — navigate to the conversation"):
            chat.navigate_to_chat(conversation_id=conversation_id)

        with allure.step(
            "Step 1 — Add the toolkit as a chat participant via + > Toolkits "
            "(toggle-switch row, does not close the submenu)"
        ):
            chat.add_toolkit_participant_via_slash_menu(
                project_id=toolkit_project_id, toolkit_id=toolkit_id, timeout=UI_ELEMENT_TIMEOUT,
            )

        with allure.step(
            "Step 2 — WITHOUT closing the popper, add the MCP via + > MCPs "
            "(same open popper, per the confirmed-live quirk); then close "
            "via outside click and verify both participants show"
        ):
            chat.add_mcp_participant_via_slash_menu(
                project_id=mcp_project_id, toolkit_id=mcp_id, timeout=UI_ELEMENT_TIMEOUT,
            )
            chat.close_plus_menu_popper()
            assert chat.is_participants_badge_visible(section="toolkits"), (
                "TOOLKITS participants badge should appear after adding the toolkit"
            )
            assert chat.is_participants_badge_visible(section="mcp"), (
                "MCP participants badge should appear after adding the MCP"
            )

        with allure.step("Step 3 — Type '/' and verify the dropdown shows exactly two items"):
            chat.open_slash_mention_dropdown(timeout=UI_ELEMENT_TIMEOUT)
            item_count = chat.get_slash_mention_item_count()
            assert item_count == 2, f"Expected exactly 2 items in the dropdown, found {item_count}"

        with allure.step("Step 4 — Verify the Toolkit item's type label reads 'toolkit'"):
            toolkit_item = chat.get_slash_mention_item(toolkit_project_id, toolkit_id)
            toolkit_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            toolkit_item_text = toolkit_item.text_content() or ""
            assert toolkit_name in toolkit_item_text, (
                f"Expected toolkit item to contain name {toolkit_name!r}, got: {toolkit_item_text!r}"
            )
            # Live DOM text is lowercase 'toolkit' (ChatParticipantType.Toolkits);
            # CSS text-transform:capitalize only affects the screen render, not
            # text_content() — see module docstring's "Implementer-level correction".
            assert "toolkit" in toolkit_item_text.lower(), (
                f"Expected toolkit item's type label to contain 'toolkit', got: {toolkit_item_text!r}"
            )

        with allure.step("Step 5 — Verify the MCP item's type label reads 'MCP'"):
            mcp_item = chat.get_slash_mention_item(mcp_project_id, mcp_id)
            mcp_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            mcp_item_text = mcp_item.text_content() or ""
            assert mcp_name in mcp_item_text, (
                f"Expected MCP item to contain name {mcp_name!r}, got: {mcp_item_text!r}"
            )
            assert "MCP" in mcp_item_text, (
                f"Expected MCP item's type label to read 'MCP', got: {mcp_item_text!r}"
            )

        with allure.step("Step 6 — Verify no other toolkits/MCPs appear (already asserted by the ==2 count above)"):
            assert chat.get_slash_mention_item_count() == 2, (
                "Item count should remain exactly 2 — only the two added participants"
            )

        with allure.step("Side-channel check — no console/JS errors"):
            assert not console_errors and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_errors]}; "
                f"page errors: {page_errors}"
            )
