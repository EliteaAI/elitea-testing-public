"""UI test — Search field filters secrets by name.

Read-only verification against the logged-in user's existing project secrets.
Filtering is client-side and per-keystroke (`SecretsContent.jsx`'s
`name.toLowerCase().includes(search.toLowerCase())` over the already-fetched
list) — no Enter, no submit control, no debounce, and no network request fires
on a keystroke, so every wait is on the rendered rows.

The search term is DERIVED AT RUNTIME from the names the product rendered, never
hardcoded: the spec walks the live names for a prefix that filters to a proper,
non-empty subset small enough to fit one default page, and fails loudly with a
named reason if no such prefix exists.

The expected match set is computed against the WHOLE dataset (collected by
walking the pagination once at the largest page size), not against page 1 — with
121 secrets on 10-row pages a page-1-only comparison would call a broken filter
correct.

No substitution of the system under test: every asserted value is read off the
live rendered table.

Test case: ELITEA-2334
AFS: test-specs/settings-secrets/l3_secrets-search-filters-by-name_ELITEA-2334.md

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
DEFAULT_PAGE_SIZE = 10
EXPECTED_SEARCH_PLACEHOLDER = "Search"
NON_MATCHING_SUFFIX = "zzqqxx"
MAX_PROBE_LENGTH = 12


def _is_known_defect_1203(text: str) -> bool:
    """True for the known, filed, isolated console error EliteaAI/
    elitea-testing-public#1203 ("Maximum update depth exceeded" on mount)."""
    return "Maximum update depth exceeded" in text


def _matches(names: list[str], term: str) -> list[str]:
    """The product's own filter predicate, restated: case-insensitive substring
    match on the name (`SecretsContent.jsx`)."""
    return [name for name in names if term.lower() in name.lower()]


def _pick_probe(all_names: list[str]) -> str:
    """Return a prefix that filters the live set to a PROPER, non-empty subset
    small enough to render on one default page.

    Derived rather than hardcoded so the spec survives anyone adding or renaming
    a secret; raises with a named reason if the live data cannot satisfy the
    case's own precondition (two secrets with different names).
    """
    for name in all_names:
        for length in range(1, min(len(name), MAX_PROBE_LENGTH) + 1):
            probe = name[:length]
            hits = _matches(all_names, probe)
            if 0 < len(hits) < len(all_names) and len(hits) <= DEFAULT_PAGE_SIZE:
                return probe
    raise AssertionError(
        "Could not derive a search probe that filters the live secret set to a "
        f"proper non-empty subset of at most {DEFAULT_PAGE_SIZE} rows — the case's "
        "precondition (at least two secrets with different names) is not satisfiable "
        f"against the {len(all_names)} names present"
    )


class TestSecretsSearchFilter:
    """ELITEA-2334 — typing a partial name filters the table to the matching
    secrets in real time, case-insensitively, and clearing the field restores
    the full set."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2334_search-field-filters-secrets-by-name.md",
        "onetest-ai Test Case link",
    )
    def test_search_field_filters_secrets_by_name(self, page):
        secrets_page = SecretsPage(page)
        console_errors = collect_console_errors(page)
        soft_failures: list[str] = []

        with allure.step(
            "Step 1 — Navigate to Settings -> Secrets with at least two secrets with "
            "different names; read the WHOLE name set so the filter can be judged "
            "against the full dataset rather than page 1"
        ):
            secrets_page.navigate()
            assert secrets_page.secret_row.count() >= MIN_SECRET_ROWS, (
                f"Case precondition — expected at least {MIN_SECRET_ROWS} secret rows, "
                f"got {secrets_page.secret_row.count()}"
            )

            all_names = secrets_page.collect_all_row_names()
            assert len(set(all_names)) >= MIN_SECRET_ROWS, (
                "Case precondition — expected at least two secrets with DIFFERENT names, "
                f"got {sorted(set(all_names))}"
            )

            # Fresh load: back to the first page at the default page size, with an
            # empty search field — the state the case's own steps start from.
            secrets_page.navigate()
            total_all = secrets_page.get_pagination_total()
            assert total_all == len(all_names), (
                f"Expected the collected name set ({len(all_names)}) to match the "
                f"pagination total ({total_all}) — a mismatch means the walk missed rows"
            )

            expect(secrets_page.search_input).to_be_visible()
            expect(secrets_page.search_input).to_have_attribute(
                "placeholder", EXPECTED_SEARCH_PLACEHOLDER
            )
            assert secrets_page.get_search_value() == "", (
                f"Expected the search field to start empty, got {secrets_page.get_search_value()!r}"
            )

            probe = _pick_probe(all_names)
            expected_matches = _matches(all_names, probe)
            logger.info("Search probe %r -> %d expected matches", probe, len(expected_matches))

        with allure.step(
            "Step 2 — Type a partial name in the Search field (character by character, "
            "no Enter pressed and no submit control clicked)"
        ):
            secrets_page.type_search(probe)
            assert secrets_page.get_search_value() == probe, (
                f"Expected the field to display the typed value {probe!r}, got "
                f"{secrets_page.get_search_value()!r}"
            )

        with allure.step(
            "Step 3 — Verify the table filters to show only matching secret names"
        ):
            expect(secrets_page.secret_row).to_have_count(len(expected_matches))
            assert set(secrets_page.get_row_names()) == set(expected_matches), (
                f"Expected exactly the names containing {probe!r} "
                f"({sorted(expected_matches)}), got {sorted(secrets_page.get_row_names())}"
            )
            # "Shows only matching names" passes vacuously if nothing was excluded.
            filtered_total = secrets_page.get_pagination_total()
            assert filtered_total < total_all, (
                f"Expected the filter to exclude something — filtered total {filtered_total} "
                f"is not less than the unfiltered total {total_all}"
            )

        with allure.step("Step 4 — Verify the search is case-insensitive"):
            for variant in (probe.upper(), probe.lower()):
                secrets_page.type_search(variant)
                expect(secrets_page.secret_row).to_have_count(len(expected_matches))
                assert set(secrets_page.get_row_names()) == set(expected_matches), (
                    f"Expected the {variant!r} probe to match the same secrets as "
                    f"{probe!r} ({sorted(expected_matches)}), got "
                    f"{sorted(secrets_page.get_row_names())}"
                )

        with allure.step(
            "Step 5 — Clear the search field — verify all secrets are shown again"
        ):
            secrets_page.clear_search()
            assert secrets_page.get_search_value() == "", (
                f"Expected the search field to be empty, got {secrets_page.get_search_value()!r}"
            )
            expect(secrets_page.secret_row).to_have_count(min(DEFAULT_PAGE_SIZE, total_all))
            assert secrets_page.get_pagination_total() == total_all, (
                f"Expected the full set to be restored (total {total_all}), got "
                f"{secrets_page.get_pagination_total()}"
            )

        with allure.step(
            "Step 6 — Verify a deliberately non-matching term empties the table "
            "(the filter can actually exclude everything)"
        ):
            secrets_page.type_search(probe + NON_MATCHING_SUFFIX)
            expect(secrets_page.secret_row).to_have_count(0)
            # The "No secrets" text is a bare span from the shared
            # GridTableContainer with no testid; the pagination footer unmounting
            # is the testid-based proof of the no-match branch.
            expect(secrets_page.pagination_info).to_have_count(0)

        with allure.step("Step 7 — Verify no unexpected console errors across the flow"):
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
