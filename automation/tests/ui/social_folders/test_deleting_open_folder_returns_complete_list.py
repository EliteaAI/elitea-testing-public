"""ELITEA-3209 — Regression: deleting the currently open folder returns to the complete list (#6484).

AFS: test-specs/social-folders/l1_deleting-open-folder-returns-complete-list_ELITEA-3209.md
Surface digest: test-specs/social-folders/_surface.md
Source defect EliteaAI/elitea_issues#6484 is CLOSED (R-2.0.6) — expected GREEN.

Entity type is DRAWN once per run (lead decision #2301); pin with
``SOCIAL_FOLDER_ENTITY_TYPE=<type>`` in ``.env.test``.

Fidelity: the two disposable entities are seeded via the API BEFORE the
list is opened — a declared TRANSIT substitution (test data; AFS
§ Fidelity Declaration). The folder is created, filled, opened and deleted
through the UI, and every observable (counts, the filtered ``ids=`` list
GET, the URL ``folder`` param, the unfiltered list, the entities' unfiled
state) is produced by the product. Teardown deletes the entities via the
API (the folder is already gone — 404 tolerated). No dialog/toast copy is
asserted (EliteaAI/elitea_issues#6480 is open).

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
from urllib.parse import urlparse

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


def _rows_by_id(list_response) -> dict[int, dict]:
    """Index an entity-list response body's rows by id (``rows`` / ``items``)."""
    body = list_response.json()
    rows = body.get("rows") if isinstance(body, dict) else None
    if rows is None and isinstance(body, dict):
        rows = body.get("items", [])
    return {int(row["id"]): row for row in (rows or []) if "id" in row}


class TestDeletingOpenFolderReturnsCompleteList:
    """ELITEA-3209 (l1, critical)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "social-folders/ELITEA-3209_regression-deleting-the-currently-open-folder-returns-to-the-complete-list.md",
        "onetest-ai Test Case link",
    )
    def test_deleting_open_folder_returns_complete_list(
        self,
        page: Page,
        social_folder_entity_type: str,
        social_folder_binding: EntityTypeBinding,
        social_folder_cleanup,
    ):
        """Folder with two entities → open (only those two) → delete while
        open → the complete unfiltered list is back immediately and both
        entities remain available and unfiled."""
        binding = social_folder_binding
        list_page = binding.list_page_cls(page)
        folders = FolderSection(page, binding.folder_entity_type)
        console_errors = collect_console_errors(page)
        folder_name = disposable_folder_name("3209", binding)

        # Transit: two disposable entities via the API, seeded BEFORE the list mounts
        # (an already-mounted list does not show API-created rows until it refetches).
        e1, e2 = create_disposable_entities(binding, social_folder_cleanup, "3209", 2)

        with allure.step(f"Step 0 — Open the {binding.key} list; both entities present; capture the baseline"):
            # The type's own navigate() + #2305 transit guard; the live console list is passed so the
            # guard drops ONLY a redirected attempt's create-picker messages — see the docstring.
            binding.open_list(list_page, folders, console_errors=console_errors)
            for entity in (e1, e2):
                folders.move_to_folder_button(entity["id"]).wait_for(state="attached", timeout=UI_ELEMENT_TIMEOUT)
            cards = binding.cards(list_page)
            baseline_cards = cards.count()
            baseline_names = binding.card_names(list_page).all_text_contents()
            assert baseline_cards == len(baseline_names) >= 2, (
                f"baseline: {baseline_cards} cards vs {len(baseline_names)} names"
            )
            assert folders.url_folder_param() is None, f"no folder should be open yet: {page.url}"

        with allure.step("Step 1 — Create the folder and assign both entities; the count reads (2)"):
            folder_id, _ = folders.create_folder(folder_name)
            social_folder_cleanup.register_folder(folder_id)
            expect(folders.folder_item_count(folder_id)).to_have_text("(0)", timeout=UI_ELEMENT_TIMEOUT)
            folders.move_entity_to_folder(e1["id"], folder_id)
            expect(folders.folder_item_count(folder_id)).to_have_text("(1)", timeout=UI_ELEMENT_TIMEOUT)
            folders.move_entity_to_folder(e2["id"], folder_id)
            expect(folders.folder_item_count(folder_id)).to_have_text("(2)", timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 2 — Open the folder: only its two entities are shown"):
            # "only its two entities" at the request level: the list GET's ids == {e1, e2}
            folders.open_folder(folder_id, binding.list_path_fragment, expected_ids={str(e1["id"]), str(e2["id"])})
            folders.expect_folder_param(folder_id)
            expect(folders.header_name).to_have_text(folder_name, timeout=UI_ELEMENT_TIMEOUT)
            expect(folders.header_count).to_have_text("(2)", timeout=UI_ELEMENT_TIMEOUT)
            expect(binding.cards(list_page)).to_have_count(2, timeout=UI_ELEMENT_TIMEOUT)
            for entity in (e1, e2):
                expect(folders.move_to_folder_button(entity["id"])).to_have_count(1)
            expect(folders.empty_state).to_have_count(0)

        with allure.step("Step 3 — Delete the open folder and confirm: the complete unfiltered list returns"):
            with page.expect_response(
                lambda r: FolderSection.is_entity_list_get(r, binding.list_path_fragment, filtered=False),
                timeout=15_000,
            ) as unfiltered_info:
                folders.delete_folder(folder_id)  # DELETE 204; no dialog/toast copy asserted (#6480)
                folders.expect_folder_param(None)  # the product's own closeFolder() on delete
            unfiltered = unfiltered_info.value
            assert "ids=" not in urlparse(unfiltered.url).query, unfiltered.url
            expect(folders.close_button).to_have_count(0)
            expect(binding.cards(list_page)).to_have_count(baseline_cards, timeout=UI_ELEMENT_TIMEOUT)
            expect(binding.card_names(list_page)).to_have_text(baseline_names)
            expect(folders.folder_item(folder_id)).to_have_count(0)

        with allure.step("Step 4 — Both former entities remain available and unfiled"):
            for entity in (e1, e2):
                expect(folders.move_to_folder_button(entity["id"])).to_have_count(1)
                folders.open_move_menu(entity["id"])
                # 'Remove from folder' renders only for a FILED entity (FolderMenuContent.jsx)
                expect(folders.move_menu_remove_item).to_have_count(0)
                folders.close_move_menu()
            rows = _rows_by_id(unfiltered)
            for entity in (e1, e2):
                row = rows.get(entity["id"])
                assert row is not None, f"entity {entity['id']} missing from the unfiltered list response"
                assert row.get("folder_id") is None and row.get("folder_name") is None, (
                    f"entity {entity['id']} still filed: folder_id={row.get('folder_id')!r} "
                    f"folder_name={row.get('folder_name')!r}"
                )

        with allure.step("Axis 2 — No unexpected console errors"):
            # Known defect: #1971 — the project-id-less toolkitTypes 404 fires on
            # project-scope transitions; excluded by its exact URL only (never by status code).
            unexpected = exclude_known_defect_urls(console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL)
            assert not unexpected, f"Unexpected console errors: {unexpected}"
