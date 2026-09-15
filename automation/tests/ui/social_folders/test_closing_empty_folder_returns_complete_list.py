"""ELITEA-3208 — Regression: closing an empty folder returns to the complete list (#6483).

AFS: test-specs/social-folders/l1_closing-empty-folder-returns-complete-list_ELITEA-3208.md
Surface digest: test-specs/social-folders/_surface.md
Source defect EliteaAI/elitea_issues#6483 is CLOSED (R-2.0.6) — expected GREEN.

Entity type is DRAWN once per run (lead decision #2301) from the six-type
pool; pin with ``SOCIAL_FOLDER_ENTITY_TYPE=<type>`` in ``.env.test``. This
case needs no entities at all — only the drawn type's list route.

Fidelity: every observable (folder row + count, empty state, header, URL
state, the unfiltered list) is produced by the UI/backend. The only API
call is the teardown DELETE of the disposable folder (transit — cleanup
after every assertion). Clarification #2302: the case text says
``No items in this folder yet.`` (trailing period); the product renders
``No items in this folder yet`` on all five list components — the product
string is asserted.
"""

import logging

import allure
import pytest
from components.folder_section import FolderSection
from fixtures.social_folder_fixtures import EntityTypeBinding, disposable_folder_name
from playwright.sync_api import Page, expect
from utils.console_errors import collect_console_errors

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

        with allure.step(f"Step 0 — Open the {binding.key} list and capture the page-1 baseline"):
            list_page.navigate()  # the type's own list page object; the app adds viewMode itself
            folders.create_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
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
            assert not console_errors, f"Unexpected console errors: {console_errors}"
