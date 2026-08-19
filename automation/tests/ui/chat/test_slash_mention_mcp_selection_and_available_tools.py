"""UI Test for ELITEA-2205 / ELITEA-2468 — Chat: Slash Commands, Selecting an
MCP From '/' Shows Its Available Tools (or Correctly Doesn't).

**Family AFS** (both TMS cases share one spec): ELITEA-2205 and ELITEA-2468
test the exact same flow — add an MCP as a participant, type '/', click its
card, verify composer + tools-list behavior — with the SAME steps in the
SAME order; ELITEA-2468 merely spells the same 2 assertions ELITEA-2205
states tersely into 4 explicit steps. Neither case's Test Data supplies
distinct expected values (both just want "tools shown if it has tools, no
list otherwise") — this is a textbook "merge cases that differ only in
data" (AFS § Family note), not a variance family with per-row differing
expected values. Both TMS cases are therefore tagged via stacked
``@allure.issue`` onto EACH test below (precedent:
``test_attach_unsupported_file_format_error.py`` stacks two
``@allure.issue`` decorators on one test), so either case failing this
scenario is independently traceable without duplicating an identical run.

Spec: test-specs/chat-interface/l2_slash-mention-mcp-selection-and-available-tools_ELITEA-2205_ELITEA-2468.md

Two tests, one per MCP state (the AFS's actual parameter-table axis):

1. ``test_select_mcp_from_slash_mention_shows_its_tools`` — has-tools MCP
   (reuses the existing ``mcp_toolkit_with_tools`` fixture, 3 real tools).
   Covers both cases' "tools shown" branch, plus the AFS Axis-2 addition of
   the tool-selection composer trailing space (source-confirmed generic
   mechanism, already live-verified for the Toolkit path in ELITEA-2204).

2. ``test_select_mcp_from_slash_mention_no_tools_shows_empty_panel`` —
   zero-tools MCP (new ``mcp_toolkit_no_tools`` fixture). Covers both
   cases' "no tools/disconnected -> no tools list" branch. **Live product
   does NOT satisfy this** — filed
   https://github.com/EliteaAI/elitea-testing-public/issues/1596 (a
   zero-tools toolkit still opens an empty, header-only "available tools"
   panel instead of showing nothing). Deterministic, single-cause,
   tail-isolable per ``.agents/testing.md`` § Merge gate "Analysis-time
   entry" -- the one no-tools-panel assertion is soft-asserted (this
   project's Python ``soft_failures`` list + trailing ``pytest.fail()``
   pattern -- Playwright JS's ``expect.soft()`` isn't available here, same
   substitution as ``test_agent_build_with_ai.py``'s Known-defect-#1317
   test) with ``# Known defect: #1596``, and this test is RED BY DESIGN
   (sanctioned-RED) until the product fix ships. Declared in
   ``expected_red[]`` in the Run Report.

New page-object surface used (all pre-existing, added by ELITEA-2202/2203/
2204 -- see those test modules' docstrings for testid provenance; no new
testids needed for this case):
- ``ChatPage.add_mcp_participant_via_slash_menu()``,
  ``open_slash_mention_dropdown()``, ``select_slash_mention_toolkit()``,
  ``select_slash_mention_tool()``, ``get_slash_mention_tool_testids()``,
  ``close_plus_menu_popper()``, ``slash_mention_tool_list``,
  ``message_input``.

Implementation-time additive change (AFS § Concrete Handles caution): added
an optional ``wait_for_first_tool: bool = True`` parameter to
``ChatPage.select_slash_mention_toolkit()`` (default preserves ELITEA-2204's
existing behavior byte-for-byte). The zero-tools test passes
``wait_for_first_tool=False`` -- the method's original unconditional wait
for the first ``slash-mention-tool-item-*`` row to attach would time out
here, since no row ever attaches for a zero-tools MCP.

Implementation-time drift found (not anticipated by the AFS's Concrete
Handles / Automation Hints, which named ``add_mcp_participant_via_slash_menu()``
as fully reusable as-is): that method's docstring already says "call this
directly after ``add_toolkit_participant_via_slash_menu``" -- it does NOT
open the plus menu itself, only waits for ``mcps_menuitem`` to already be
visible in an already-open popper. ELITEA-2203/2204 (its only prior
callers) always call ``add_toolkit_participant_via_slash_menu()`` first,
which opens the popper. This case is MCP-only (never adds a Toolkit
participant), so the popper was never open and every run timed out waiting
for ``mcps_menuitem``. Fixed additively: a new ``open_plus_menu: bool =
False`` parameter on ``add_mcp_participant_via_slash_menu()`` that clicks
``plus_menu_button`` first when set; default ``False`` leaves ELITEA-2203's
existing call sites byte-identical. Both tests below pass
``open_plus_menu=True``.

New fixture (additive, ``fixtures/data_fixtures.py``): ``mcp_toolkit_no_tools``
-- mirrors ``mcp_toolkit_with_tools``'s shape/cleanup, but calls
``create_remote_mcp_toolkit(..., tools=[])`` directly (no ``sync_mcp_tools``
probe needed -- nothing to sync).

Known defects: #1596 (see above). No other defects -- both cases' remaining
Objective/Pass-Fail criteria match live product behavior exactly (AFS §
Known Defects Found).

Usage:
    cd automation
    pytest tests/ui/chat/test_slash_mention_mcp_selection_and_available_tools.py -v
"""

import logging

import allure
import pytest
from pages.chat_page import ChatPage

logger = logging.getLogger("elitea.tests.chat")

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

ELITEA_2205_LINK = (
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
    "chat/ELITEA-2205_chat-slash-commands-selecting-mcp-from-slash-dropdown.md"
)
ELITEA_2468_LINK = (
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
    "chat/ELITEA-2468_chat-select-mcp-from-dropdown.md"
)


class TestSlashMentionMcpSelectionAndAvailableTools:
    """ELITEA-2205 (l2, medium) / ELITEA-2468 (l2, high) — Chat – Slash
    Commands – Selecting an MCP From '/' Shows Its Available Tools (or
    Correctly Doesn't)."""

    @allure.issue(ELITEA_2205_LINK, "onetest-ai Test Case link — ELITEA-2205")
    @allure.issue(ELITEA_2468_LINK, "onetest-ai Test Case link — ELITEA-2468")
    @pytest.mark.p2
    def test_select_mcp_from_slash_mention_shows_its_tools(
        self, page, conversation_id, mcp_toolkit_with_tools,
    ):
        """Selecting a has-tools MCP from the '/' dropdown replaces the
        composer with '/{mcp_name}', opens its available-tools list (all 3
        tools, each individually clickable), and selecting a tool appends
        '/{tool_name} ' (trailing space) to the composer.
        """
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        chat = ChatPage(page)
        mcp_name = mcp_toolkit_with_tools["name"]
        project_id = mcp_toolkit_with_tools["project_id"]
        toolkit_id = mcp_toolkit_with_tools["id"]
        expected_tools = sorted(mcp_toolkit_with_tools["tools"])

        with allure.step(
            "Setup — navigate to the conversation, add the MCP as a "
            "participant via + > MCPs"
        ):
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.add_mcp_participant_via_slash_menu(
                project_id=project_id, toolkit_id=toolkit_id, timeout=UI_ELEMENT_TIMEOUT,
                open_plus_menu=True,
            )
            chat.close_plus_menu_popper()
            assert chat.is_participants_badge_visible(section="mcp"), (
                "MCP participants badge should appear after adding the MCP"
            )

        with allure.step("Step 1 — Type '/' and verify the dropdown shows the MCP, labelled 'MCP'"):
            chat.open_slash_mention_dropdown(timeout=UI_ELEMENT_TIMEOUT)
            mcp_item = chat.get_slash_mention_item(project_id, toolkit_id)
            mcp_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            mcp_item_text = mcp_item.text_content() or ""
            assert mcp_name in mcp_item_text, (
                f"Expected MCP item to contain name {mcp_name!r}, got: {mcp_item_text!r}"
            )
            assert "MCP" in mcp_item_text, (
                f"Expected MCP item's type label to read 'MCP', got: {mcp_item_text!r}"
            )

        with allure.step(
            "Step 2 — Click the MCP's card; verify the composer shows "
            "'/{mcp_name}' and the available-tools list shows exactly its 3 tools"
        ):
            chat.select_slash_mention_toolkit(project_id, toolkit_id, timeout=UI_ELEMENT_TIMEOUT)

            composer_value = chat.message_input.input_value()
            assert composer_value == f"/{mcp_name}", (
                f"Expected composer value '/{mcp_name}', got {composer_value!r}"
            )

            tools_header = chat.slash_mention_tool_list.text_content() or ""
            assert f"{mcp_name} available tools" in tools_header.lower(), (
                f"Expected tools-list header to contain "
                f"'{mcp_name} available tools', got: {tools_header!r}"
            )

            actual_testids = sorted(chat.get_slash_mention_tool_testids())
            expected_testids = sorted(f"slash-mention-tool-item-{name}" for name in expected_tools)
            assert actual_testids == expected_testids, (
                f"Expected tool rows {expected_testids}, got {actual_testids}"
            )

        with allure.step(
            "Step 3 — Click one tool ('ask_question'); verify the composer "
            "updates to '/{mcp_name}/ask_question ' (trailing space)"
        ):
            chat.select_slash_mention_tool("ask_question", timeout=UI_ELEMENT_TIMEOUT)
            composer_value = chat.message_input.input_value()
            assert composer_value == f"/{mcp_name}/ask_question ", (
                f"Expected composer value '/{mcp_name}/ask_question ' "
                f"(with trailing space), got {composer_value!r}"
            )

        with allure.step("Side-channel check — no console/JS errors"):
            assert not console_errors and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_errors]}; "
                f"page errors: {page_errors}"
            )

    @allure.issue(ELITEA_2205_LINK, "onetest-ai Test Case link — ELITEA-2205")
    @allure.issue(ELITEA_2468_LINK, "onetest-ai Test Case link — ELITEA-2468")
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1596",
        "Known defect — zero-tools MCP still opens an empty 'available tools' panel",
    )
    @pytest.mark.p2
    def test_select_mcp_from_slash_mention_no_tools_shows_empty_panel(
        self, page, conversation_id, mcp_toolkit_no_tools,
    ):
        """Selecting a zero-tools MCP from the '/' dropdown replaces the
        composer with '/{mcp_name}'; per the case text, no tools list should
        appear at all. Live product diverges (# Known defect: #1596) — the
        no-tools-panel assertion is soft and this test is sanctioned-RED
        until the product fix ships.
        """
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg) if msg.type == "error" else None)
        page_errors = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        chat = ChatPage(page)
        mcp_name = mcp_toolkit_no_tools["name"]
        project_id = mcp_toolkit_no_tools["project_id"]
        toolkit_id = mcp_toolkit_no_tools["id"]
        # pytest-native soft-assertion equivalent (matches this suite's
        # existing `soft_failures` + trailing `pytest.fail()` pattern —
        # see test_agent_build_with_ai.py / Known defect #1317 — not
        # Playwright JS's `expect.soft()`, unavailable in this Python project).
        soft_failures: list[str] = []

        with allure.step(
            "Setup — navigate to the conversation, add the zero-tools MCP "
            "as a participant via + > MCPs"
        ):
            chat.navigate_to_chat(conversation_id=conversation_id)
            chat.add_mcp_participant_via_slash_menu(
                project_id=project_id, toolkit_id=toolkit_id, timeout=UI_ELEMENT_TIMEOUT,
                open_plus_menu=True,
            )
            chat.close_plus_menu_popper()
            assert chat.is_participants_badge_visible(section="mcp"), (
                "MCP participants badge should appear after adding the MCP"
            )

        with allure.step("Step 1 — Type '/' and verify the dropdown shows the MCP, labelled 'MCP'"):
            chat.open_slash_mention_dropdown(timeout=UI_ELEMENT_TIMEOUT)
            mcp_item = chat.get_slash_mention_item(project_id, toolkit_id)
            mcp_item.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            mcp_item_text = mcp_item.text_content() or ""
            assert mcp_name in mcp_item_text, (
                f"Expected MCP item to contain name {mcp_name!r}, got: {mcp_item_text!r}"
            )
            assert "MCP" in mcp_item_text, (
                f"Expected MCP item's type label to read 'MCP', got: {mcp_item_text!r}"
            )

        with allure.step(
            "Step 2 — Click the MCP's card; verify the composer shows "
            "'/{mcp_name}'; verify NO tools list appears (# Known defect: #1596)"
        ):
            # wait_for_first_tool=False -- a zero-tools MCP never attaches a
            # tool-item row, so the default wait would time out (see module
            # docstring's "Implementation-time additive change").
            chat.select_slash_mention_toolkit(
                project_id, toolkit_id, timeout=UI_ELEMENT_TIMEOUT, wait_for_first_tool=False,
            )

            composer_value = chat.message_input.input_value()
            assert composer_value == f"/{mcp_name}", (
                f"Expected composer value '/{mcp_name}', got {composer_value!r}"
            )

            # Per the case's OWN stated expected result: "if no tools/
            # disconnected, no tools list appears". Live product instead
            # renders a header-only, zero-row panel -- soft-asserted below,
            # sanctioned-RED per .agents/testing.md § Merge gate
            # "Analysis-time entry" until the product fix ships.
            panel_visible = chat.slash_mention_tool_list.is_visible()
            tool_item_count = (
                chat.slash_mention_tool_list.locator(chat.SLASH_MENTION_TOOL_ITEM_PREFIX).count()
                if panel_visible
                else 0
            )
            # Known defect: https://github.com/EliteaAI/elitea-testing-public/issues/1596
            if panel_visible:
                soft_failures.append(
                    "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1596: "
                    "a zero-tools MCP should show no available-tools panel at all, but the "
                    f"panel still renders (header-only, {tool_item_count} tool rows)."
                )
            # Hard guard regardless of the defect above: if the panel DOES
            # render, it must never show stray tool rows for a genuinely
            # zero-tools MCP -- that would be a worse, separate regression.
            assert tool_item_count == 0, (
                f"Zero-tools MCP's available-tools panel should never show tool "
                f"rows, got {tool_item_count}"
            )

        with allure.step("Side-channel check — no console/JS errors"):
            assert not console_errors and not page_errors, (
                f"Unexpected console errors: {[m.text for m in console_errors]}; "
                f"page errors: {page_errors}"
            )

        if soft_failures:
            pytest.fail(
                "Soft assertion(s) failed (known isolated product defect, "
                "not test/infrastructure — remaining steps above passed "
                "cleanly):\n" + "\n".join(soft_failures)
            )
