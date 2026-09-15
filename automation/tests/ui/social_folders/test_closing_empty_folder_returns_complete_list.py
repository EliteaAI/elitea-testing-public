"""ELITEA-3208 — Regression: closing an empty folder returns to the complete list (#6483).

AFS: test-specs/social-folders/l1_closing-empty-folder-returns-complete-list_ELITEA-3208.md
Surface digest: test-specs/social-folders/_surface.md
Source defect EliteaAI/elitea_issues#6483 is CLOSED (R-2.0.6) — expected GREEN.

Entity type is DRAWN once per run (lead decision #2301) from the six-type
pool; pin with ``SOCIAL_FOLDER_ENTITY_TYPE=<type>`` in ``.env.test``. The
folder itself stays EMPTY; ONE disposable entity of the drawn type is
seeded via the API so the list page renders at all — a zero-entity list
redirects to the type's create page and never mounts the FOLDERS panel
(verified live: project 399 holds 0 credentials and 0 toolkits, so the
credentials draw redirected 3/3 without it). It is never filed.

Fidelity: every observable (folder row + count, empty state, header, URL
state, the unfiltered list) is produced by the UI/backend. The seeded
entity is a declared TRANSIT substitution (test data reached before the
steps under test; it is part of the read-only page-1 baseline, nothing is
asserted about it). Teardown deletes it and the folder via the API (after
every assertion). Clarification #2302: the case text says
``No items in this folder yet.`` (trailing period); the product renders
``No items in this folder yet`` on all five list components — the product
string is asserted.

Transit guard for product bug #2305 (first-render empty-list redirect): a
landing on the create route is treated as a retryable navigation outcome
(``binding.open_list``); the case's own observables are unchanged.

Console axis scope (declared improvisation — canon gap, lead ruling on
#2301 fix round 3): Axis 2 (no unexpected console errors) is an ADDED
assertion scoped to the case's own steps; the transit precondition (#2305
redirect → create picker, where #656 logs a React key warning and #1971
its 404) is outside the case and must not decide its verdict. The collector
is armed at test start (as on the trunk) and passed into
``binding.open_list``; console messages logged by the create picker during
a #2305 REDIRECTED attempt are cleared inside the guard's re-navigation
branch — exactly the redirected attempt, nothing else. The list's own mount
and every case step remain under Axis 2; when #2305 does not fire, nothing
is cleared. The one standing exclusion is the exact project-id-less
toolkitTypes URL (#1971), never a status code.
"""

import logging

import allure
import pytest
from components.folder_section import FolderSection
from fixtures.social_folder_fixtures import EntityTypeBinding, create_disposable_entities, disposable_folder_name
from playwright.sync_api import Page, expect
from utils.console_errors import (
    TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL,
    collect_console_errors,
    exclude_known_defect_urls,
)

logger = logging.getLogger("elitea.tests.social_folders")

pytestmark = [pytest.mark.ui, pytest.mark.social_folders, pytest.mark.regression, pytest.mark.p0, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
EMPTY_STATE_TEXT = "No items in this folder yet"  # product string — clarification #2302


class TestClosingEmptyFolderReturnsCompleteList:
    """ELITEA-3208 (l1, critical)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "social-folders/ELITEA-3208_regression-closing-an-empty-folder-returns-to-the-complete-list.md",
        "onetest-ai Test Case link",
    )
    def test_closing_empty_folder_returns_complete_list(
        self,
        page: Page,
        social_folder_entity_type: str,
        social_folder_binding: EntityTypeBinding,
        social_folder_cleanup,
    ):
        """Create an empty folder via the UI, open it (exact empty text,
        ``(0)`` in the row and the header), close it — the complete
        unfiltered list (page-1 card names captured in step 0) is back."""
        binding = social_folder_binding
        list_page = binding.list_page_cls(page)
        folders = FolderSection(page, binding.folder_entity_type)
        console_errors = collect_console_errors(page)
        folder_name = disposable_folder_name("3208", binding)

        # Transit: one unfiled disposable entity so the list mounts (a zero-entity list
        # redirects to the create page); it is part of the baseline, never filed.
        create_disposable_entities(binding, social_folder_cleanup, "3208", 1)

        with allure.step(f"Step 0 — Open the {binding.key} list and capture the page-1 baseline"):
            # The type's own navigate() + #2305 transit guard; the live console list is passed so the
            # guard drops ONLY a redirected attempt's create-picker messages — see the docstring.
            binding.open_list(list_page, folders, console_errors=console_errors)
            cards = binding.cards(list_page)
            cards.first.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
            baseline_cards = cards.count()
            baseline_names = binding.card_names(list_page).all_text_contents()
            assert baseline_cards == len(baseline_names) > 0, (
                f"baseline: {baseline_cards} cards vs {len(baseline_names)} names"
            )
            assert folders.url_folder_param() is None, f"no folder should be open yet: {page.url}"
            logger.info("baseline: %s cards on %s", baseline_cards, binding.key)

        with allure.step("Step 1 — Create a disposable empty folder; the row shows (0)"):
            folder_id, _ = folders.create_folder(folder_name)
            social_folder_cleanup.register_folder(folder_id)  # guard set the moment the 201 exists
            expect(folders.folder_item(folder_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(folders.folder_item_count(folder_id)).to_have_text("(0)", timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 2 — Open the empty folder: exact empty text and (0) in header + row"):
            # an empty folder queries the list with the ids=0 sentinel (useFolderEntities.hooks.js)
            folders.open_folder(folder_id, binding.list_path_fragment, expected_ids={"0"})
            folders.expect_folder_param(folder_id)
            expect(folders.header_name).to_have_text(folder_name, timeout=UI_ELEMENT_TIMEOUT)
            expect(folders.header_count).to_have_text("(0)", timeout=UI_ELEMENT_TIMEOUT)
            expect(folders.empty_state).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(folders.empty_state).to_have_text(EMPTY_STATE_TEXT)
            expect(binding.cards(list_page)).to_have_count(0)
            expect(folders.folder_item_count(folder_id)).to_have_text("(0)")

        with allure.step("Step 3 — Close the folder: the complete unfiltered list is shown immediately"):
            unfiltered = folders.close_folder(binding.list_path_fragment)
            assert "ids=" not in unfiltered.url, unfiltered.url
            folders.expect_folder_param(None)
            expect(folders.close_button).to_have_count(0)
            expect(folders.empty_state).to_have_count(0)
            expect(binding.cards(list_page)).to_have_count(baseline_cards, timeout=UI_ELEMENT_TIMEOUT)
            expect(binding.card_names(list_page)).to_have_text(baseline_names)
            expect(folders.folder_item(folder_id)).to_be_visible()
            expect(folders.folder_item_count(folder_id)).to_have_text("(0)")

        with allure.step("Axis 2 — No unexpected console errors"):
            # Known defect: #1971 — the project-id-less toolkitTypes 404 fires on
            # project-scope transitions; excluded by its exact URL only (never by status code).
            unexpected = exclude_known_defect_urls(console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL)
            assert not unexpected, f"Unexpected console errors: {unexpected}"
