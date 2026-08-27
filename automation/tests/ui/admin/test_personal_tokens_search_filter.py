"""UI test — Search field filters tokens by name in real time.

Read-only verification against the logged-in user's existing personal-token
data (`.agents/testing.md` § Test data strategy). This case never creates,
renames, or deletes a token: two of the live rows are irrecoverably `Expired`
and ELITEA-2284's merged test reads its `expired` branch off them.

The search term is DERIVED FROM THE OBSERVED DATA at runtime (a prefix of a
real token name that yields a proper subset), never hardcoded — the token names
are shared, mutable, real leftover data, so a literal `"Lev"` would break the
day anyone renames a token. Every asserted value is read off the live rendered
table; nothing about the system under test is substituted.

Filtering is client-side (`TokensSection.jsx` filters an already-cached
RTK-Query array with `name.toLowerCase().includes(search.toLowerCase())`), so
NO request fires on a keystroke — the assertions wait on rendered rows, never
on a response and never on a sleep. `SimpleSearchBar` filters from the native
`onChange`: per keystroke, no Enter, no submit control, no debounce. Pressing
Enter anywhere in this test would defeat its subject, which is exactly the
"real time" claim.

Test case: ELITEA-2287
AFS: test-specs/settings-personal-tokens/l3_search-field-filters-tokens-by-name-in-real-time_ELITEA-2287.md
"""

import logging

import allure
import pytest
from pages.personal_tokens_page import PersonalTokensPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

MIN_TOKEN_ROWS = 2
EXPECTED_PLACEHOLDER = "Search tokens..."
PROBE_LENGTH = 3
NO_MATCH_SUFFIX = "zzzqqq"
EXPECTED_NO_MATCH_MESSAGE = "No tokens"


def _pick_probe(names: list[str]) -> tuple[str, list[str]]:
    """Return a (probe, expected-matches) pair derived from the observed names.

    Walks the live names and takes the first prefix that filters to a PROPER,
    non-empty subset — so the "filtered count is strictly less than the
    unfiltered count" assertion is achievable against whatever data exists,
    without hardcoding a token name.
    """
    for name in names:
        probe = name[:PROBE_LENGTH]
        matches = [n for n in names if probe.lower() in n.lower()]
        if 0 < len(matches) < len(names):
            return probe, matches
    raise AssertionError(
        "Could not derive a search probe that filters to a proper subset of the "
        f"live token names {names} — every name prefix matches every name. The "
        "case needs at least two tokens with sufficiently different names."
    )


class TestPersonalTokensSearchFilter:
    """ELITEA-2287 — Search field filters tokens by name in real time."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/personal-tokens/ELITEA-2287_search-field-filters-tokens-by-name-in-real-time.md",
        "onetest-ai Test Case link",
    )
    def test_search_field_filters_tokens_by_name_in_real_time(self, page):
        """Typing a partial name filters the table per keystroke, matching is
        case-insensitive, a non-matching term empties the table, and clearing
        the field restores every token."""
        tokens_page = PersonalTokensPage(page)
        console_errors = collect_console_errors(page)

        with allure.step(
            "Step 1 — Navigate to Settings -> Personal Tokens with at least two "
            'differently-named tokens: the table renders and an empty "Search '
            'tokens..." field is present'
        ):
            tokens_page.navigate()

            count_all = tokens_page.token_row.count()
            assert count_all >= MIN_TOKEN_ROWS, (
                f"Case precondition — expected at least {MIN_TOKEN_ROWS} token rows, "
                f"got {count_all}"
            )
            assert tokens_page.search_input.is_visible(), (
                "Expected the token search input to be visible"
            )
            placeholder = tokens_page.search_input.get_attribute("placeholder")
            assert placeholder == EXPECTED_PLACEHOLDER, (
                f"Expected search input placeholder {EXPECTED_PLACEHOLDER!r} (the case "
                f"names the field by it), got {placeholder!r}"
            )
            assert tokens_page.get_search_value() == "", (
                "Expected the search field to start empty, got "
                f"{tokens_page.get_search_value()!r}"
            )

            names_all = tokens_page.get_row_names()
            probe, expected_matches = _pick_probe(names_all)
            logger.info("Derived search probe %r -> expected matches %s", probe, expected_matches)

        with allure.step(
            f"Step 2 — Type the partial name {probe!r} into the search field one "
            "character at a time, without pressing Enter: the field accepts the "
            "input and displays the entered value"
        ):
            tokens_page.type_search(probe)
            assert tokens_page.get_search_value() == probe, (
                f"Expected the search field to display {probe!r}, got "
                f"{tokens_page.get_search_value()!r}"
            )

        with allure.step(
            "Step 3 — Verify the table filtered in real time to only the matching "
            "token names, with strictly fewer rows than before (no Enter pressed, "
            "no submit control clicked)"
        ):
            expect(tokens_page.row_name_cell).to_have_text(expected_matches)
            assert tokens_page.token_row.count() == len(expected_matches), (
                f"Expected exactly {len(expected_matches)} rows for probe {probe!r}, "
                f"got {tokens_page.token_row.count()}"
            )
            assert len(expected_matches) < count_all, (
                "Expected the filter to actually remove rows — equal counts would "
                f"pass even for a no-op filter (probe {probe!r} matched all "
                f"{count_all} rows)"
            )

        with allure.step(
            "Step 4 — Verify the search is case-insensitive: the upper-cased and "
            "lower-cased probe produce the identical filtered list"
        ):
            for variant in (probe.upper(), probe.lower()):
                tokens_page.clear_search()
                tokens_page.type_search(variant)
                assert tokens_page.get_search_value() == variant, (
                    f"Expected the search field to display {variant!r}, got "
                    f"{tokens_page.get_search_value()!r}"
                )
                expect(tokens_page.row_name_cell).to_have_text(expected_matches)

        with allure.step(
            "Step 5 — Verify a deliberately non-matching term empties the table: "
            'zero rows, the "No tokens" message, and the column headers unmount '
            "— while the page header and search box stay (this is the no-match "
            "branch, NOT the zero-tokens-exist empty-state page)"
        ):
            no_match_term = f"{probe}{NO_MATCH_SUFFIX}"
            tokens_page.clear_search()
            tokens_page.type_search(no_match_term)

            expect(tokens_page.token_row).to_have_count(0)
            expect(tokens_page.table_empty_message).to_have_text(EXPECTED_NO_MATCH_MESSAGE)
            expect(tokens_page.column_header_name).to_have_count(0)
            expect(tokens_page.column_header_expires).to_have_count(0)
            assert tokens_page.search_input.is_visible(), (
                "Expected the search box to stay mounted in the no-match state"
            )

        with allure.step(
            "Step 6 — Clear the search field: every token is shown again"
        ):
            tokens_page.clear_search()

            assert tokens_page.get_search_value() == "", (
                f"Expected the search field to be empty after clearing, got "
                f"{tokens_page.get_search_value()!r}"
            )
            expect(tokens_page.token_row).to_have_count(count_all)
            # Compare SETS: the sort order is orthogonal to the search and survives
            # a clear (surface digest), so an ordered comparison would be asserting
            # sort state this case never touched.
            assert sorted(tokens_page.get_row_names()) == sorted(names_all), (
                f"Expected the full token set {sorted(names_all)} to be restored, got "
                f"{sorted(tokens_page.get_row_names())}"
            )

        with allure.step("Step 7 — Verify no unexpected console errors across the flow"):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
