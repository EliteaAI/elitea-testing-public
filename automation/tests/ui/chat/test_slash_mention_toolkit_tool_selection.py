"""UI Test for ELITEA-2204 — Chat: Slash Commands, Selecting a Toolkit From
'/' Shows Its Available Tools.

Adds an Artifact toolkit configured with exactly 4 ``selected_tools`` as a
conversation participant, then verifies the two-phase slash-mention flow:
typing '/' and clicking the toolkit replaces the composer fragment with
``/{toolkit_name}`` and opens a second list of exactly those 4 tools, in
configuration order; clicking a tool replaces the fragment with
``/{toolkit_name}/{tool_name} `` (confirmed trailing space).

Spec: test-specs/chat-interface/l3_slash-mention-toolkit-tool-selection_ELITEA-2204.md

Case-text deviation (AFS § Test Data / § Known Defects, filed
EliteaAI/elitea-testing-public#1125): the case's expected tool
``list_collections`` is not a valid tool name in this environment (backend
rejects it) — the live, correct tool for the same capability is
``list_indexes``. This test asserts against ``list_indexes``, per the
reverse-masking guard (asserting a stale case-text value here would be
masking in the wrong direction, not honesty).

Testid gaps filled this implementation (``add-data-testid``, pushed to
``automation/testids``, EliteaAI/EliteaUI@34319b30):
- ``slash-mention-list`` / ``slash-mention-item-{project_id}_{toolkit_id}``
  (dynamic) — see ELITEA-2202/2203 test module docstrings; reused here for
  the toolkit-selection phase.
- ``slash-mention-tool-list`` (static — ``ToolList.jsx``'s outer ``Box``;
  NOT shared with any other feature, confirmed via ``git grep -rl
  "ToolList"`` returning only ``SlashSuggestionList.jsx``, so no prop
  threading was needed) and ``slash-mention-tool-item-{tool_name}``
  (dynamic — ``ToolItem.jsx``, threaded via a new ``testId`` prop from
  ``ToolList.jsx``'s per-item call, same ``testId``-prop convention as
  ``AttachmentButton.jsx``).

Implementer-level fix (live race, not an AFS/scope issue): the tools list
container renders immediately on toolkit selection with ``isToolsFetching``'s
loading spinner and ZERO tool-item testids — waiting only on the
container's visibility (as the AFS's Automation Hints literally say: "wait
for slash_mention_tool_list to become visible") races the
``useToolkitsDetailsQuery`` fetch and reads an empty list. Fixed by having
``ChatPage.select_slash_mention_toolkit()`` additionally wait for the first
tool-item row to attach before returning.

New page-object surface (``ChatPage``, all additive):
- ``slash_mention_tool_list`` (LocatorDescriptor)
- ``SLASH_MENTION_TOOL_ITEM`` / ``SLASH_MENTION_TOOL_ITEM_PREFIX``
  (template constants)
- ``select_slash_mention_toolkit()`` / ``select_slash_mention_tool()`` /
  ``get_slash_mention_tool_item()``
- Reuses ELITEA-2203's ``add_toolkit_participant_via_slash_menu()`` (resolves
  the toolkit row directly by testid, no search typing — see that test
  module's docstring for the live race this avoided) /
  ``close_plus_menu_popper()`` / ``open_slash_mention_dropdown()`` /
  ``get_slash_mention_item()``

New fixture: ``artifact_toolkit_four_tools`` (``fixtures/data_fixtures.py``)
— a new, additional fixture (the existing ``artifact_toolkit`` is untouched
except for the additive ``project_id`` key added for ELITEA-2203). Needed
because ``create_artifact_toolkit()``'s factory hardcodes a 16-tool
``selected_tools`` list, which would make this case's "exactly 4 tools"
assertion false.

Known defects: none blocking this case; see the case-text CLARIFICATION
above (filed, not a defect — AFS § Known Defects Found).

Usage:
    cd automation
    pytest tests/ui/chat/test_slash_mention_toolkit_tool_selection.py -v
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

# AFS § Test Data — CLARIFICATION: list_indexes, not the case's stale
# list_collections (issue EliteaAI/elitea-testing-public#1125). Order
# matches the toolkit's configured selected_tools order (AFS-confirmed).
EXPECTED_TOOLS = ["index_data", "list_indexes", "search_index", "stepback_search_index"]


class TestSlashMentionToolkitToolSelection:
    """ELITEA-2204: Chat – Slash Commands – Selecting a Toolkit From '/'
    Shows Its Available Tools (l3, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/chat/ELITEA-2204_chat-slash-commands-verify-selecting-toolkit-from-dropdown-and-viewing-available-tools.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_select_toolkit_from_slash_mention_shows_its_tools(
        self, page, conversation_id, artifact_toolkit_four_tools,
    ):
        """Selecting a toolkit from the '/' dropdown shows exactly its
        configured tools, in order; selecting a tool updates the composer.
        """
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        chat = ChatPage(page)
        toolkit_name = artifact_toolkit_four_tools["name"]
        project_id = artifact_toolkit_four_tools["project_id"]
        toolkit_id = artifact_toolkit_four_tools["id"]

        with allure.step("Setup — navigate to the conversation, add the toolkit as a participant"):
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.add_toolkit_participant_via_slash_menu(
                project_id=project_id, toolkit_id=toolkit_id, timeout=UI_ELEMENT_TIMEOUT,
            )
            chat.close_plus_menu_popper()
            assert chat.is_participants_badge_visible(section="toolkits"), (
                "TOOLKITS participants badge should appear after adding the toolkit"
            )

        with allure.step(
            "Step 1 — Type '/', click the toolkit card; verify the composer "
            "shows '/{toolkit_name}' and the available-tools list appears"
        ):
            chat.open_slash_mention_dropdown(timeout=UI_ELEMENT_TIMEOUT)
            chat.select_slash_mention_toolkit(project_id, toolkit_id, timeout=UI_ELEMENT_TIMEOUT)

            composer_value = chat.message_input.input_value()
            assert composer_value == f"/{toolkit_name}", (
                f"Expected composer value '/{toolkit_name}', got {composer_value!r}"
            )

            tools_header = chat.slash_mention_tool_list.text_content() or ""
            assert f"{toolkit_name} available tools" in tools_header.lower(), (
                f"Expected tools-list header to contain "
                f"'{toolkit_name} available tools', got: {tools_header!r}"
            )

        with allure.step("Step 2 — Verify the tools list shows exactly the 4 configured tools, in order"):
            actual_tools = chat.get_slash_mention_tool_testids()
            expected_testids = [f"slash-mention-tool-item-{name}" for name in EXPECTED_TOOLS]
            assert actual_tools == expected_testids, (
                f"Expected tools in order {expected_testids}, got {actual_tools}"
            )

        with allure.step(
            "Step 3 — Click 'index_data'; verify the composer updates to "
            "'/{toolkit_name}/index_data ' (trailing space)"
        ):
            chat.select_slash_mention_tool("index_data", timeout=UI_ELEMENT_TIMEOUT)
            composer_value = chat.message_input.input_value()
            assert composer_value == f"/{toolkit_name}/index_data ", (
                f"Expected composer value '/{toolkit_name}/index_data ' "
                f"(with trailing space), got {composer_value!r}"
            )

        with allure.step("Side-channel check — no console/JS errors"):
            assert not console_errors and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_errors]}; "
                f"page errors: {page_errors}"
            )
