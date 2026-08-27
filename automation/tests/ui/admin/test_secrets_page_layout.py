"""UI test — Secrets page loads with correct layout and components.

Read-only verification against the logged-in user's existing project secrets
(`.agents/testing.md` § Test data strategy). This case creates nothing and
deletes nothing.

The assertions are RELATIONAL, not literal — per-row `value == "{{secret." +
name + "}}"` computed from the name the product itself rendered, and control
counts compared against the observed row count. A hardcoded name list would
break the day anyone adds a secret, and worse, would still pass if the product
stopped rendering the reference format for new rows.

No substitution of the system under test: every asserted value is read off the
live rendered page.

Test case: ELITEA-2330
AFS: test-specs/settings-secrets/l3_secrets-page-layout-and-components_ELITEA-2330.md

Known defect (EliteaAI/elitea-testing-public#1203): `/settings/secrets` may fire
a React "Maximum update depth exceeded" console error on mount. Recorded as an
isolated soft failure (sanctioned-RED per `.agents/testing.md` § Merge gate)
with the same `soft_failures`/`pytest.fail()` idiom the sibling secrets specs
use — never filtered away.
"""

import logging
import re

import allure
import pytest
from pages.secrets_page import SecretsPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

EXPECTED_TITLE = "Secrets"
EXPECTED_SEARCH_PLACEHOLDER = "Search"
EXPECTED_COLUMNS = (("name", "Name"), ("secretValue", "Value"), ("actions", "Actions"))
SORTABLE_FIELDS = ("name",)
NON_SORTABLE_FIELDS = ("secretValue", "actions")
DEFAULT_PAGE_SIZE = 10
PAGINATION_RANGE_PATTERN = re.compile(r"^\d+ - \d+ of \d+$")


def _is_known_defect_1203(text: str) -> bool:
    """True for the known, filed, isolated console error (EliteaAI/
    elitea-testing-public#1203) — a React "Maximum update depth exceeded"
    error that may fire on a `/settings/secrets` mount. Matches on the STABLE
    message prefix alone, not a volatile component-stack suffix."""
    return "Maximum update depth exceeded" in text


class TestSecretsPageLayout:
    """ELITEA-2330 — the Secrets page renders its header (title, search, add
    button), a three-column table whose Name column alone is sortable, the
    full per-row anatomy (name, masked reference value, eye toggle, three-dot
    menu) and the pagination footer."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2330_secrets-page-loads-with-correct-layout-and-components.md",
        "onetest-ai Test Case link",
    )
    def test_secrets_page_layout_and_components(self, page):
        secrets_page = SecretsPage(page)
        console_errors = collect_console_errors(page)
        soft_failures: list[str] = []

        with allure.step(
            "Step 1 — Navigate to Settings -> Secrets: the populated table renders"
        ):
            secrets_page.navigate()
            row_count = secrets_page.secret_row.count()
            assert row_count >= 1, (
                "Case precondition — expected at least one secret row so every "
                f"per-row assertion below is non-vacuous, got {row_count}"
            )

        with allure.step('Step 2 — Verify the page header shows "Secrets"'):
            expect(secrets_page.page_title).to_have_text(EXPECTED_TITLE)

        with allure.step("Step 3 — Verify a Search input is present in the top right"):
            expect(secrets_page.search_input).to_be_visible()
            expect(secrets_page.search_input).to_have_attribute(
                "placeholder", EXPECTED_SEARCH_PLACEHOLDER
            )
            assert secrets_page.get_search_value() == "", (
                "Expected the search field to start empty, got "
                f"{secrets_page.get_search_value()!r}"
            )

        with allure.step('Step 4 — Verify a "+" button is present in the top right'):
            expect(secrets_page.add_button).to_be_visible()
            expect(secrets_page.add_button).to_be_enabled()

        with allure.step(
            "Step 5 — Verify the table has exactly three columns — Name (sortable), "
            "Value, Actions — and that Name is the only sortable one"
        ):
            for field, label in EXPECTED_COLUMNS:
                expect(secrets_page.column_header(field)).to_have_text(label)
            # Bi-directional: without the count the claim passes even if a
            # fourth column appeared.
            expect(secrets_page.column_headers()).to_have_count(len(EXPECTED_COLUMNS))

            for field in SORTABLE_FIELDS:
                expect(secrets_page.sort_icon(field)).to_be_visible()
            # The case marks Name specifically as the sortable column; without
            # the negative the claim passes even if all three became sortable.
            for field in NON_SORTABLE_FIELDS:
                expect(secrets_page.sort_icon(field)).to_have_count(0)

        with allure.step(
            "Step 6 — Verify each row shows: secret name, masked value in "
            "{{secret.<name>}} format, eye icon, three-dot menu"
        ):
            names = secrets_page.get_row_names()
            values = secrets_page.get_row_values()

            assert len(names) == row_count, (
                f"Expected one name cell per row ({row_count}), got {len(names)}"
            )
            assert len(values) == row_count, (
                f"Expected one value cell per row ({row_count}), got {len(values)}"
            )
            expect(secrets_page.visibility_toggle_button).to_have_count(row_count)
            expect(secrets_page.row_actions_button).to_have_count(row_count)

            assert all(names), f"Expected every row to render a non-empty name, got {names}"
            mismatches = [
                (name, value)
                for name, value in zip(names, values, strict=True)
                if value != "{{secret." + name + "}}"
            ]
            assert not mismatches, (
                "Expected every row's Value cell to read '{{secret.<that row's name>}}'; "
                f"mismatched (name, value) pairs: {mismatches}"
            )

        with allure.step(
            "Step 7 — Verify the pagination controls: rows-per-page selector, "
            "page range label, prev/next arrows"
        ):
            range_text = secrets_page.get_pagination_text()
            assert PAGINATION_RANGE_PATTERN.match(range_text), (
                f"Expected the pagination range in 'N - M of T' form, got {range_text!r}"
            )
            assert range_text.startswith("1 - "), (
                f"Expected to land on the first page, got {range_text!r}"
            )

            total = secrets_page.get_pagination_total()
            expect(secrets_page.page_size_select).to_have_text(str(DEFAULT_PAGE_SIZE))
            assert row_count == min(DEFAULT_PAGE_SIZE, total), (
                f"Expected the first page to render min(page size {DEFAULT_PAGE_SIZE}, "
                f"total {total}) rows, got {row_count}"
            )

            # Presence alone would pass on two dead buttons — the enabled state
            # is what proves the arrows track the current page position.
            expect(secrets_page.prev_page_button).to_be_visible()
            expect(secrets_page.prev_page_button).to_be_disabled()
            expect(secrets_page.next_page_button).to_be_visible()
            if total > DEFAULT_PAGE_SIZE:
                expect(secrets_page.next_page_button).to_be_enabled()
            else:
                expect(secrets_page.next_page_button).to_be_disabled()

        with allure.step("Step 8 — Verify no unexpected console errors across the flow"):
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
