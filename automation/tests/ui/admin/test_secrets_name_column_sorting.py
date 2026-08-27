"""UI test — Secrets listing: the Name column is sortable.

Read-only verification against the logged-in user's existing project secrets.
Sorting is client-side over the FULL dataset (`useTableSort.sortData`), so no
network request fires on a header click and nothing is written.

The assertions are RELATIONAL, not literal — `observed == sorted(observed,
key=str.lower)` rather than a hardcoded name list. The secret names are shared,
mutable, real project data; a literal expectation would break the day anyone
adds a secret, and worse, would still pass if the product stopped sorting but
the API happened to return that order.

⚠️ Case-text divergence (filed as #1901, `question`; sibling of #1880, the
identical drift on Settings -> Personal Tokens): case steps 2-5 claim the FIRST
Name click sorts ascending and the second descending. The product's default sort
is ALREADY name-ascending (`useTableSort({ defaultField: 'name',
defaultDirection: 'asc' })`), so the first click flips to DESCENDING and the
second returns to ascending. The product is correct and internally consistent;
the case text is stale, so this test asserts the live contract (reverse-masking
guard). Both directions the case asks for ARE asserted — only the click index at
which each occurs differs from the stale text.

Sort DIRECTION is asserted through the rendered row ORDER, never through the
sort icon's inline `transform: rotate(180deg)` style — the row order is the
observable the case actually names.

No substitution of the system under test: every asserted value is read off the
live rendered table.

Test case: ELITEA-2331
AFS: test-specs/settings-secrets/l3_secrets-name-column-sortable_ELITEA-2331.md

Known defect (EliteaAI/elitea-testing-public#1203): see the isolated soft
failure at the end of the flow.
"""

import logging

import allure
import pytest
from pages.secrets_page import SecretsPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

MIN_SECRET_ROWS = 2
SORTABLE_FIELDS = ("name",)
NON_SORTABLE_FIELDS = ("secretValue", "actions")


def _is_known_defect_1203(text: str) -> bool:
    """True for the known, filed, isolated console error EliteaAI/
    elitea-testing-public#1203 ("Maximum update depth exceeded" on mount)."""
    return "Maximum update depth exceeded" in text


class TestSecretsNameColumnSorting:
    """ELITEA-2331 — the Name column exposes the table's only sort control, and
    clicking it toggles the rendered row order between descending and ascending
    over the whole dataset, without adding or dropping rows."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2331_secrets-listing-name-column-is-sortable.md",
        "onetest-ai Test Case link",
    )
    def test_secrets_name_column_is_sortable(self, page):
        secrets_page = SecretsPage(page)
        console_errors = collect_console_errors(page)
        soft_failures: list[str] = []

        with allure.step(
            "Step 1 — Navigate to Settings -> Secrets with at least two secrets: the "
            "Name column is the only one exposing a sort control, and the table "
            "arrives ALREADY sorted name-ascending with no interaction"
        ):
            secrets_page.navigate()

            row_count = secrets_page.secret_row.count()
            assert row_count >= MIN_SECRET_ROWS, (
                f"Case precondition — expected at least {MIN_SECRET_ROWS} secret rows so "
                f"the ordering assertions are meaningful, got {row_count}"
            )
            total_before = secrets_page.get_pagination_total()

            for field in SORTABLE_FIELDS:
                expect(secrets_page.sort_icon(field)).to_be_visible()
            # The case title scopes sortability to Name; without the negative the
            # claim would pass even if all three columns became sortable.
            for field in NON_SORTABLE_FIELDS:
                expect(secrets_page.sort_icon(field)).to_have_count(0)

            names_default = secrets_page.get_row_names()
            assert names_default == sorted(names_default, key=str.lower), (
                "Expected the table to arrive already sorted name-ascending with no "
                "interaction (useTableSort defaultField='name'/'asc') — this is the "
                f"premise the first click's direction follows from, got {names_default}"
            )

        with allure.step(
            "Step 2 — Click the Name column header: the table re-sorts by name "
            "DESCENDING (the default is already ascending, so the first click flips "
            "it — see the case-text divergence filed as #1901)"
        ):
            secrets_page.click_column_header("name")
            # Auto-retrying: this is both the wait for the re-render and the check.
            expect(secrets_page.name_cell).not_to_have_text(names_default)

            names_desc = secrets_page.get_row_names()
            assert names_desc == sorted(names_desc, key=str.lower, reverse=True), (
                f"Expected the rendered page to be name-descending, got {names_desc}"
            )
            # Proves the sort re-sliced the WHOLE dataset rather than only
            # reordering the rows that happened to be on this page.
            assert names_desc[0].lower() > names_default[0].lower(), (
                "Expected descending sort to bring the dataset's LAST names onto page 1 "
                f"(got head {names_desc[0]!r} vs ascending head {names_default[0]!r}) — "
                "a page-local reorder would leave the head unchanged"
            )
            assert secrets_page.secret_row.count() == row_count, (
                "Expected sorting to reorder rows without changing the row count "
                f"({row_count}), got {secrets_page.secret_row.count()}"
            )

        with allure.step(
            "Step 3 — Click the Name column header again: the table returns to name "
            "ASCENDING, matching the load-time order"
        ):
            secrets_page.click_column_header("name")
            expect(secrets_page.name_cell).to_have_text(names_default)

            assert secrets_page.secret_row.count() == row_count, (
                "Expected sorting to reorder rows without changing the row count "
                f"({row_count}), got {secrets_page.secret_row.count()}"
            )
            assert secrets_page.get_pagination_total() == total_before, (
                "Expected the dataset total to be untouched by sorting "
                f"({total_before}), got {secrets_page.get_pagination_total()}"
            )

        with allure.step("Step 4 — Verify no unexpected console errors across the flow"):
            unexpected_errors = [e for e in console_errors if not _is_known_defect_1203(e)]
            assert not unexpected_errors, f"Unexpected console errors: {unexpected_errors}"

            known_defect_errors = [e for e in console_errors if _is_known_defect_1203(e)]
            if known_defect_errors:
                # Known defect: EliteaAI/elitea-testing-public#1203
                soft_failures.append(
                    "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/1203: "
                    f"React 'Maximum update depth exceeded' console error(s) on "
                    f"/settings/secrets mount: {len(known_defect_errors)} occurrence(s)"
                )

        if soft_failures:
            pytest.fail(
                "Test flow completed and all functional assertions passed, but "
                "known-defect soft failures were recorded:\n" + "\n".join(soft_failures)
            )
