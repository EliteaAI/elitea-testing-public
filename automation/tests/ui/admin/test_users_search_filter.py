"""UI test — Users page search filters the table in real time.

Read-only verification against the active project's existing user rows
(`.agents/testing.md` § Test data strategy). This case never creates, edits
or deletes a user; filtering is client-side, so nothing is mutated.

The search probes are DERIVED FROM THE OBSERVED DATA at runtime — a prefix of
a real email and a prefix of a real name, each chosen because it filters to a
proper, non-empty subset — never hardcoded. The user set is shared, mutable,
real data (project 400 currently carries two real users plus two orphaned
invite rows from an earlier ELITEA-2304 run), so a literal "epam" would break
the day anyone invites or removes someone. Every asserted value is read off
the live rendered table; nothing about the system under test is substituted.

`Users.jsx` filters an already-cached RTK-Query array, so NO request fires on
a keystroke — the assertions wait on rendered rows, never on a response and
never on a sleep. `SimpleSearchBar` filters from the native `onChange`: per
keystroke, no Enter, no submit control, no debounce. Pressing Enter anywhere
in this test would defeat its subject, which is exactly the "real time" claim.

The product's matching rule has THREE arms (`Users.jsx:82-92`): a row matches
when the lower-cased term is a substring of its email OR its name OR its
joined roles. The expectation helper below applies the same three arms, so a
probe that happens to also be a substring of "admin"/"editor"/"viewer" is
predicted correctly instead of producing a false red.

Test case: ELITEA-2294
AFS: test-specs/settings-users-and-roles/l3_users-page-search-filters-the-table-in-real-time_ELITEA-2294.md
"""

import logging

import allure
import pytest
from pages.admin_users_page import AdminUsersPage
from playwright.sync_api import expect
from utils.console_errors import (
    TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL,
    collect_console_errors,
    exclude_known_defect_urls,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

MIN_USER_ROWS = 2
EXPECTED_SEARCH_PLACEHOLDER = "Search "
PROBE_LENGTH = 4


def _matches(term: str, row: dict) -> bool:
    """Apply the product's own three-arm match rule (`Users.jsx:82-92`)."""
    lowered = term.lower()
    return (
        lowered in row["email"].lower()
        or lowered in row["name"].lower()
        or lowered in row["roles"].lower()
    )


def _pick_probe(rows: list[dict], field: str) -> tuple[str, list[dict]]:
    """Return a (probe, expected-matching-rows) pair derived from live data.

    Walks the observed rows and takes the first prefix of *field* that filters
    to a PROPER, non-empty subset under the product's three-arm rule — so the
    "filtered count is strictly less than the unfiltered count" assertion is
    achievable against whatever data exists, without hardcoding a value.
    """
    for row in rows:
        probe = row[field][:PROBE_LENGTH].strip()
        if not probe:
            continue
        matches = [candidate for candidate in rows if _matches(probe, candidate)]
        if 0 < len(matches) < len(rows):
            return probe, matches
    raise AssertionError(
        f"Could not derive a {field} search probe that filters to a proper subset of "
        f"the live user rows {rows} — every prefix matches every row. The case needs "
        f"at least two users with sufficiently different {field} values."
    )


class TestUsersSearchFilter:
    """ELITEA-2294 — Users page search filters the table in real time."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/users-and-roles/ELITEA-2294_users-page-search-filters-the-table-in-real-time.md",
        "onetest-ai Test Case link",
    )
    def test_users_page_search_filters_the_table_in_real_time(self, page):
        """Typing a partial email and a partial name each filter the table per
        keystroke to exactly the matching rows, and clearing the field restores
        every user."""
        users_page = AdminUsersPage(page)
        console_errors = collect_console_errors(page)

        with allure.step(
            "Step 1 — Navigate to Settings -> Users with at least two rows: the "
            'table renders and an empty "Search " field is present'
        ):
            users_page.navigate()

            count_all = users_page.user_row.count()
            assert count_all >= MIN_USER_ROWS, (
                f"Case precondition — expected at least {MIN_USER_ROWS} user rows, got "
                f"{count_all}"
            )
            assert users_page.search_input.is_visible(), "Expected the users search input to be visible"
            placeholder = users_page.search_input.get_attribute("placeholder")
            assert placeholder == EXPECTED_SEARCH_PLACEHOLDER, (
                f"Expected search input placeholder {EXPECTED_SEARCH_PLACEHOLDER!r} (the "
                f"case names the field by it), got {placeholder!r}"
            )
            assert users_page.get_search_value() == "", (
                f"Expected the search field to start empty, got {users_page.get_search_value()!r}"
            )

            rows_all = [
                {"name": name, "email": email, "roles": roles}
                for name, email, roles in zip(
                    users_page.get_row_names(),
                    users_page.get_row_emails(),
                    users_page.get_row_roles(),
                    strict=True,
                )
            ]
            email_probe, email_matches = _pick_probe(rows_all, "email")
            name_probe, name_matches = _pick_probe(rows_all, "name")
            logger.info(
                "Derived probes — email %r -> %s, name %r -> %s",
                email_probe,
                email_matches,
                name_probe,
                name_matches,
            )

        with allure.step(
            f"Step 2 — Type the partial email {email_probe!r} into the search field "
            "one character at a time, without pressing Enter: the field accepts the "
            "input and displays the entered value"
        ):
            users_page.type_search(email_probe)
            assert users_page.get_search_value() == email_probe, (
                f"Expected the search field to display {email_probe!r}, got "
                f"{users_page.get_search_value()!r}"
            )

        with allure.step(
            "Step 3 — Verify the table filtered in real time to only the matching "
            "users, with strictly fewer rows than before (no Enter pressed, no "
            "submit control clicked)"
        ):
            expect(users_page.row_email_cell).to_have_text([row["email"] for row in email_matches])
            assert len(email_matches) < count_all, (
                f"Expected the filter to actually remove rows — equal counts would pass "
                f"even for a no-op filter (probe {email_probe!r} matched all {count_all} rows)"
            )

        with allure.step(
            f"Step 4 — Clear the search field and type the partial name "
            f"{name_probe!r}: the field accepts the input and displays it"
        ):
            users_page.clear_search()
            users_page.type_search(name_probe)
            assert users_page.get_search_value() == name_probe, (
                f"Expected the search field to display {name_probe!r}, got "
                f"{users_page.get_search_value()!r}"
            )

        with allure.step(
            "Step 5 — Verify the table filtered to only the matching names, again "
            "with strictly fewer rows than the unfiltered table"
        ):
            expect(users_page.row_email_cell).to_have_text([row["email"] for row in name_matches])
            assert len(name_matches) < count_all, (
                f"Expected the name probe {name_probe!r} to remove rows, but it matched "
                f"all {count_all}"
            )

        with allure.step("Step 6 — Clear the search field: every user is shown again"):
            users_page.clear_search()

            assert users_page.get_search_value() == "", (
                f"Expected the search field to be empty after clearing, got "
                f"{users_page.get_search_value()!r}"
            )
            expect(users_page.user_row).to_have_count(count_all)
            # Compare SETS: the sort order is orthogonal to the search and survives a
            # clear, so an ordered comparison would be asserting sort state this case
            # never touched.
            assert sorted(users_page.get_row_emails()) == sorted(row["email"] for row in rows_all), (
                f"Expected the full user set {sorted(row['email'] for row in rows_all)} to be "
                f"restored, got {sorted(users_page.get_row_emails())}"
            )

        with allure.step("Step 7 — Verify no unexpected console errors across the flow"):
            # Known defect: #1971 (regression of the closed #554) — during the
            # project switch this page object performs, EliteaUI's `toolkitTypes`
            # query can fire before `useSelectedProjectId()` resolves and request
            # a project-id-less `.../toolkits/prompt_lib/`, which 404s. Cosmetic
            # in the product, unrelated to anything this case drives. Excluded by
            # that EXACT URL only — never by status code, which would swallow the
            # next genuine 404. Delete this argument when #1971 is fixed.
            unexpected = exclude_known_defect_urls(
                console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL
            )
            assert not unexpected, f"Unexpected console errors: {unexpected}"
