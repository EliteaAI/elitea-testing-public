"""UI test — MCP list page search box filters by name.

TMS: ELITEA-1941 (test-specs/mcp/l1_mcp-dashboard-search-by-name_ELITEA-1941.md)

Verifies the MCP list page's search box (shared ``SearchBar.jsx`` component,
same mechanics as ``CredentialsListPage`` — ELITEA-1965): a matching term
filters the visible card list to only matching MCPs, a non-matching term
shows the empty state, and clearing after a match restores the full list.

Search is explicit-activation (Enter, not live-filter-as-you-type) — typing
alone does not dispatch the filter; confirmed live in
``EliteaUI/src/components/SearchBar.jsx``. Filtering itself is client-side
against an already-fetched MCP list (no new XHR observed on Enter — AFS
§ Network Behavior).

Test data note (case-text drift, CLARIFICATION, reverse-masking guard): the
case's literal match term "Web"/"Web Search" does not exist in the live
``Private`` test project (6 pre-existing MCPs, none named/containing "Web").
The match term was adapted to "github" (matches exactly one existing MCP,
"Remote Github") for this AFS/test — see AFS § Preconditions and § Test
Data.

Known defect (github.com/EliteaAI/elitea-testing-public#585): clearing the
search box after a **zero-results** search redirects to ``/mcps/create``
instead of restoring the list. Scoped to the zero-results path only —
clearing after a non-empty-result search works correctly (asserted as a
control check below, mirroring #551's control check in
``test_credential_search_by_name.py``). Asserted with ``expect.soft()`` per
this project's no-masking policy — the assertion stays RED until #585 is
fixed.
"""

import logging
import re

import allure
import pytest
from playwright.sync_api import expect

from pages.mcp_list_page import McpListPage

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.toolkits, pytest.mark.p1, pytest.mark.regression]

SEARCH_TERM_MATCH = "github"
SEARCH_TERM_MATCH_EXPECTED_NAME = "Remote Github"
SEARCH_TERM_NO_MATCH = "nonexistent_xyz_mcp"
EXPECTED_SEARCH_PLACEHOLDER = "Let's find something amazing!"


class TestMcpSearchByName:
    """ELITEA-1941 — MCP list search box filters by name."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "mcp/ELITEA-1941_mcp-dashboard-search-by-name.md",
        "onetest-ai Test Case link",
    )
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/585", "Known defect #585")
    @pytest.mark.mcp
    def test_mcp_search_by_name(self, page):
        """Search filters MCPs client-side; clearing restores the list (known
        defect: not after a zero-results search — #585)."""
        list_page = McpListPage(page)

        # Console listener — same pre-existing #291 "missing key" dev warning
        # already tracked by test_credential_search_by_name.py (confirmed
        # firing on /mcps/all too, via the shared ToolkitTypeSelector render
        # path) — filtered out so a real regression in this case's own
        # search flow isn't masked by an unrelated, already-filed warning.
        def _is_known_291_warning(msg) -> bool:
            text = msg.text
            return (
                'unique "key" prop' in text
                or ("validateDOMNesting" in text and "<p>" in text)
                or ("validateDOMNesting" in text and "%s" in text)
            )

        def _on_console(msg):
            if msg.type in ("error", "warning") and not _is_known_291_warning(msg):
                console_messages.append(msg)

        console_messages = []
        page.on("console", _on_console)

        with allure.step("Step 1 — Navigate to MCP list page: it loads with all MCPs visible as cards"):
            list_page.navigate()
            baseline_names = set(list_page.get_card_names())
            assert len(baseline_names) >= 1, (
                "Expected at least one pre-existing MCP card on a fresh list load, got none"
            )
            assert SEARCH_TERM_MATCH_EXPECTED_NAME in baseline_names, (
                f"Expected {SEARCH_TERM_MATCH_EXPECTED_NAME!r} among the pre-existing MCPs, "
                f"got {baseline_names}"
            )

        with allure.step(
            "Step 2 — Verify the search textbox is visible with the expected placeholder"
        ):
            expect(list_page.search_input).to_be_visible()
            assert list_page.search_input.get_attribute("placeholder") == EXPECTED_SEARCH_PLACEHOLDER, (
                f"Expected search placeholder {EXPECTED_SEARCH_PLACEHOLDER!r}, "
                f"got {list_page.search_input.get_attribute('placeholder')!r}"
            )

        with allure.step(
            f"Step 3 — Click the search box, type {SEARCH_TERM_MATCH!r}, press Enter: filter is applied"
        ):
            list_page.search(SEARCH_TERM_MATCH)
            # Auto-retrying count assertion — filtering is client-side with no
            # response to await, so the render must be polled rather than
            # trusted immediately after search() returns.
            expect(list_page.mcp_card_name).to_have_count(1)

        with allure.step(
            f"Step 4 — Verify only the MCP matching {SEARCH_TERM_MATCH!r} is shown "
            f"({SEARCH_TERM_MATCH_EXPECTED_NAME!r})"
        ):
            filtered_names = set(list_page.get_card_names())
            assert filtered_names == {SEARCH_TERM_MATCH_EXPECTED_NAME}, (
                f"Expected only {SEARCH_TERM_MATCH_EXPECTED_NAME!r} after searching "
                f"{SEARCH_TERM_MATCH!r}, got {filtered_names}"
            )

        with allure.step(
            f"Step 5 — Clear search and type {SEARCH_TERM_NO_MATCH!r}, press Enter: filter is updated"
        ):
            list_page.clear_search()
            list_page.search(SEARCH_TERM_NO_MATCH)

        with allure.step("Step 6 — Verify no results are shown (empty state)"):
            expect(list_page.empty_state_title).to_be_visible()
            assert list_page.get_card_count() == 0, (
                "Expected zero MCP cards visible while the zero-match empty state is shown"
            )

        with allure.step(
            "Step 7 — Clear search: expect all MCPs to reappear "
            "(Known defect: #585 — redirects to /mcps/create instead)"
        ):
            list_page.clear_search()
            # Known defect: EliteaAI/elitea-testing-public#585 — clearing a
            # zero-match search redirects away from /mcps/all instead of
            # restoring the list. Soft assertions so the control check below
            # still runs; stays RED until #585 ships a fix, per
            # .agents/testing.md's no-masking policy.
            expect.soft(page).to_have_url(re.compile(r".*/mcps/all$"))
            expect.soft(list_page.mcp_card_name).to_have_count(len(baseline_names))
            if "/mcps/all" in page.url and list_page.mcp_card_name.count() == len(baseline_names):
                restored_names = set(list_page.get_card_names())
                assert baseline_names <= restored_names, (
                    f"Expected the full MCP list restored after Clear, got {restored_names}"
                )

        with allure.step(
            "Control check (Axis 2) — clearing after a NON-empty-result search restores the "
            "list correctly (defect #585 is scoped to the zero-results path only)"
        ):
            # Recover to a clean /mcps/all regardless of whether the known
            # defect fired above — a real client-side navigation resets the
            # search state.
            list_page.navigate()
            list_page.search(SEARCH_TERM_MATCH)
            expect(list_page.mcp_card_name).to_have_count(1)
            filtered_names = set(list_page.get_card_names())
            assert filtered_names == {SEARCH_TERM_MATCH_EXPECTED_NAME}, (
                f"Expected only {SEARCH_TERM_MATCH_EXPECTED_NAME!r} after re-searching "
                f"{SEARCH_TERM_MATCH!r}, got {filtered_names}"
            )

            list_page.clear_search()
            assert "/mcps/all" in page.url, (
                "Clearing after a non-empty-result search must NOT navigate away from "
                f"/mcps/all, got {page.url}"
            )
            expect(list_page.mcp_card_name).to_have_count(len(baseline_names))
            restored_names = set(list_page.get_card_names())
            assert baseline_names <= restored_names, (
                f"Expected the full MCP list restored after clearing a non-empty-result search, "
                f"got {restored_names}"
            )

        with allure.step("Side-channel check — no console errors/warnings across the flow"):
            assert not console_messages, (
                f"Unexpected console errors/warnings: {[m.text for m in console_messages]}"
            )
