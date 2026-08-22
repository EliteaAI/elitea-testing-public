"""Test for Credential Dashboard — View Toggle (Table/Card).

Verifies the credentials list's Card/Table view toggle: Card is the default
layout, switching to Table renders the five credential columns plus a
20-per-page pagination footer whose Next/Previous controls move between
disjoint row sets, and switching back restores the card layout.

Test case: ELITEA-1973
AFS: test-specs/toolkits-credentials/l1_credential-dashboard-view-toggle-table-card_ELITEA-1973.md

No substitution of the system under test: credentials are topped up to the
case's own ">20 credentials" precondition through the real REST API purely
as **transit** (the case has no create step). Every asserted observable —
the pressed toggle button, the rendered layout, the column headers, the
page-info string, the rows on each page — is computed and rendered by the
product from its own paged server response. Nothing is mocked, injected or
intercepted.
"""

import logging
import re
import time
from urllib.parse import parse_qs, urlparse

import allure
import pytest
from api.client import CredentialAPI
from pages.credentials_list_page import CredentialsListPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.credentials, pytest.mark.p1, pytest.mark.regression, pytest.mark.new]

#: The table's default page size (DataTable.jsx PAGE_SIZE) — the case's own
#: "Default page size (table view): 20 items per page" test-datum.
DEFAULT_PAGE_SIZE = 20

#: The case's precondition is "more than 20 credentials"; 21 is the cheapest
#: state that satisfies it (a full first page + a non-empty second page).
REQUIRED_CREDENTIAL_COUNT = DEFAULT_PAGE_SIZE + 1

PAGE_INFO_RE = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s+of\s+(\d+)\s*$")


def _is_known_554_warning(msg) -> bool:
    """Filter elitea-testing-public#554 (CLOSED 2026-08-11, product-owner
    verdict: reproducible only against a local UI / test-client artifact,
    not a backend defect, no action items). The right-panel toolkit-types
    query can fire before ``useSelectedProjectId()`` resolves, collapsing
    its URL to ``.../toolkits/prompt_lib/`` (no id) and 404-ing. Filtering
    it is a local-environment allowance, NOT a product-defect waiver — it
    is pinned to that exact URL shape, never a blanket 404 ignore, and it
    can match nothing this case renders or asserts."""
    location_url = (msg.location or {}).get("url", "")
    return "404" in msg.text and location_url.rstrip("/").endswith("/toolkits/prompt_lib")


def _parse_page_info(text: str) -> tuple[int, int, int]:
    """Parse the pagination footer's ``'{start} - {end} of {total}'`` text."""
    match = PAGE_INFO_RE.match(text)
    assert match, f"Pagination info should read '<start> - <end> of <total>', got: {text!r}"
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


class TestCredentialViewToggle:
    """ELITEA-1973 — Credentials dashboard Card/Table view toggle + pagination."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "credentials/ELITEA-1973_credential-dashboard-view-toggle-table-card.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    def test_credential_dashboard_view_toggle_table_card(self, page, credential_api: CredentialAPI):
        """Card view is the default; Table view shows the five credential
        columns and a working 20-per-page pager; Card view is restored."""
        ts = int(time.time())
        seeded_ids: list[int] = []

        console_messages = []

        def _on_console(msg):
            if msg.type in ("error", "warning") and not _is_known_554_warning(msg):
                console_messages.append(msg)

        list_page = CredentialsListPage(page)

        try:
            # Precondition (AFS § Test Data), not a case step: the case
            # requires >20 credentials for pagination to be observable at
            # all — GridTablePagination disables BOTH arrows when
            # total <= pageSize. Existing credentials are reused as page-1
            # content and never touched; only the shortfall is seeded.
            existing_total = credential_api.list_credentials(
                params={"section": ["credentials", "storage"], "limit": 1}
            )["total"]
            for index in range(max(0, REQUIRED_CREDENTIAL_COUNT - existing_total)):
                created = credential_api.create_credential(
                    {
                        "type": "github",
                        "elitea_title": f"github_autotest_view_{ts}_{index:02d}",
                        "label": f"autotest_cred_view_{index:02d}_{ts}",
                        "data": {"base_url": "https://api.github.com"},
                        "shared": False,
                    }
                )
                seeded_ids.append(created["id"])
            logger.info(
                "Credentials precondition: %s existed, seeded %s more", existing_total, len(seeded_ids)
            )

            page.on("console", _on_console)

            with allure.step("Step 1 — Navigate to the Credentials list; verify it loads with no ?view= param"):
                list_page.navigate()
                parsed = urlparse(page.url)
                assert parsed.path.rstrip("/").endswith("/credentials/all"), (
                    f"Expected the credentials list URL, got: {page.url}"
                )
                assert "view" not in parse_qs(parsed.query), (
                    f"A fresh navigation should carry no ?view= param, got: {page.url}"
                )

            with allure.step("Step 2 — Verify the default view is Card (card view button pressed/active)"):
                assert list_page.is_card_view_active(), (
                    "Card view should be the default active layout on a fresh page load"
                )
                assert not list_page.is_table_view_active(), (
                    "Table view should NOT be active while Card view is the default"
                )
                baseline_card_names = list_page.get_card_names()
                assert baseline_card_names, "At least one credential card should be visible by default"
                expect(list_page.pagination_page_info).to_have_count(0)

            with allure.step("Step 3 — Click the Table view button; verify the view switches"):
                list_page.switch_to_table_view()
                assert parse_qs(urlparse(page.url).query).get("view") == ["table"], (
                    f"URL should reflect ?view=table after switching, got: {page.url}"
                )
                assert list_page.is_table_view_active(), "Table view should be active after clicking it"
                assert not list_page.is_card_view_active(), (
                    "Card view should no longer be active once Table view is on"
                )

            with allure.step("Step 4 — Verify credentials display in table format"):
                expect(list_page.entity_card).to_have_count(0)
                expect(list_page.table_row_name.first).to_be_visible()

            with allure.step(
                "Step 5 — Verify the table columns: Name & Description, Type, Authors, Created, Actions"
            ):
                for field, label in CredentialsListPage.TABLE_COLUMNS:
                    header = list_page.get_table_column_header(field)
                    expect(header).to_be_visible()
                    assert (header.text_content() or "").strip() == label, (
                        f"Column header {field!r} should read {label!r}, "
                        f"got: {(header.text_content() or '').strip()!r}"
                    )

            with allure.step(
                "Step 6 — Verify pagination controls are present, defaulting to 20 items per page"
            ):
                expect(list_page.pagination_page_info).to_be_visible()
                start, end, total = _parse_page_info(list_page.get_page_info())
                assert total > DEFAULT_PAGE_SIZE, (
                    f"The case's precondition requires more than {DEFAULT_PAGE_SIZE} credentials "
                    f"for pagination to be exercisable, total is {total}"
                )
                assert (start, end) == (1, DEFAULT_PAGE_SIZE), (
                    f"The first page should show rows 1-{DEFAULT_PAGE_SIZE}, got {start}-{end}"
                )

                first_page_names = list_page.get_table_row_names()
                assert len(first_page_names) == DEFAULT_PAGE_SIZE, (
                    f"The first page should render {DEFAULT_PAGE_SIZE} rows, got {len(first_page_names)}"
                )
                assert list_page.pagination_prev_button.is_disabled(), (
                    "The 'previous page' control should be disabled on the first page"
                )
                assert list_page.pagination_next_button.is_enabled(), (
                    "The 'next page' control should be enabled while further pages exist"
                )

            with allure.step("Step 7 — Click the next page control; verify the next set is displayed"):
                list_page.click_next_page()

                next_start, next_end, next_total = _parse_page_info(list_page.get_page_info())
                assert next_total == total, (
                    f"Paging must not change the total ({total}), got {next_total}"
                )
                expected_end = min(DEFAULT_PAGE_SIZE * 2, total)
                assert (next_start, next_end) == (DEFAULT_PAGE_SIZE + 1, expected_end), (
                    f"The second page should show rows {DEFAULT_PAGE_SIZE + 1}-{expected_end}, "
                    f"got {next_start}-{next_end}"
                )

                second_page_names = list_page.get_table_row_names()
                assert len(second_page_names) == expected_end - DEFAULT_PAGE_SIZE, (
                    f"The second page should render {expected_end - DEFAULT_PAGE_SIZE} rows, "
                    f"got {len(second_page_names)}"
                )
                assert not (set(second_page_names) & set(first_page_names)), (
                    f"The second page must show a DIFFERENT set of credentials — overlap: "
                    f"{sorted(set(second_page_names) & set(first_page_names))}"
                )
                assert list_page.pagination_prev_button.is_enabled(), (
                    "The 'previous page' control should be enabled once past the first page"
                )

            with allure.step("Step 8 — Click the previous page control; verify the previous set is displayed"):
                list_page.click_prev_page()

                back_start, back_end, _back_total = _parse_page_info(list_page.get_page_info())
                assert (back_start, back_end) == (1, DEFAULT_PAGE_SIZE), (
                    f"Going back should return to rows 1-{DEFAULT_PAGE_SIZE}, got {back_start}-{back_end}"
                )
                assert list_page.get_table_row_names() == first_page_names, (
                    "Going back should restore exactly the first page's rows"
                )
                assert list_page.pagination_prev_button.is_disabled(), (
                    "The 'previous page' control should be disabled again on the first page"
                )

            with allure.step("Step 9 — Click the Card view button; verify the view switches back"):
                list_page.switch_to_card_view()
                assert parse_qs(urlparse(page.url).query).get("view") == ["cards"], (
                    f"URL should reflect ?view=cards after switching back, got: {page.url}"
                )
                assert list_page.is_card_view_active(), "Card view should be active again"
                assert not list_page.is_table_view_active(), (
                    "Table view should no longer be active after switching back"
                )

            with allure.step("Step 10 — Verify credentials display in card format again"):
                expect(list_page.table_row_name).to_have_count(0)
                expect(list_page.entity_card.first).to_be_visible()
                restored_card_names = list_page.get_card_names()
                missing = set(baseline_card_names) - set(restored_card_names)
                assert not missing, (
                    f"Card view should show the same credentials as before the round trip; "
                    f"missing: {sorted(missing)}"
                )

            with allure.step("Side channel — no unexpected console errors across the whole flow"):
                assert not console_messages, (
                    "Unexpected console errors/warnings: "
                    f"{[m.text for m in console_messages]}"
                )
        finally:
            page.remove_listener("console", _on_console)
            for credential_id in seeded_ids:
                try:
                    credential_api.delete_credential(credential_id)
                except Exception:
                    logger.warning("Failed to delete seeded credential id=%s", credential_id, exc_info=True)
