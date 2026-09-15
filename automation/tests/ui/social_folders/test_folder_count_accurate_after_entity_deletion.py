"""ELITEA-3210 — Regression: folder count stays accurate after entity deletion and subsequent changes (#6482).

AFS: test-specs/social-folders/l1_folder-count-accurate-after-entity-deletion-and-changes_ELITEA-3210.md
Surface digest: test-specs/social-folders/_surface.md
Source defect EliteaAI/elitea_issues#6482 is CLOSED (R-2.0.6) — expected GREEN.

Entity type is DRAWN once per run (lead decision #2301); pin with
``SOCIAL_FOLDER_ENTITY_TYPE=<type>`` in ``.env.test``.

Fidelity: the four disposable entities are seeded via the API BEFORE the
list is opened — a declared TRANSIT substitution (test data; AFS
§ Fidelity Declaration). The step-2 entity delete is the CASE's own action
and goes through the drawn type's normal delete UI (detail page ⋮ →
Delete → type-to-confirm), never the API; the test issues NO reload/goto
after the confirm — the count is read on the panel row of the list the
product itself lands on. Every count/header/membership observable is
UI/backend-produced; the "no drift" cross-check reads ``entities_count``
from the product's own ``include_counts=true`` refetch.

Type-specific landing after the step-2 delete: skills / agents / MCPs /
credentials land on the bare list route (folder view closed); pipelines
and toolkits redirect with ``navigate(-1)`` back to the ``?folder=`` URL
the detail page was reached from, so the folder view is still open. Step 3
therefore normalises to "closed" before its own open → close → reopen
sequence (declared here and in the AFS).

Known defect (console only): the post-delete stale
``GET /elitea_core/skill/prompt_lib/{pid}/{id}`` → 404 (#2303, skills) /
``GET /configurations/configuration/{pid}/{id}`` → 404 (#1666, credentials)
is excluded by exact URL via ``exclude_known_defect_urls`` — never by
status code.

Transit guard for product bug #2305 (first-render empty-list redirect): a
landing on the create route is treated as a retryable navigation outcome
(``binding.open_list``); the case's own observables are unchanged.
"""

import logging

import allure
import pytest
from components.folder_section import FolderSection
from fixtures.social_folder_fixtures import EntityTypeBinding, create_disposable_entities, disposable_folder_name
from playwright.sync_api import Page, expect
from utils.console_errors import collect_console_errors, exclude_known_defect_urls

logger = logging.getLogger("elitea.tests.social_folders")

pytestmark = [pytest.mark.ui, pytest.mark.social_folders, pytest.mark.regression, pytest.mark.p0, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000


class TestFolderCountAccurateAfterEntityDeletion:
    """ELITEA-3210 (l1, critical)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "social-folders/ELITEA-3210_regression-folder-count-remains-accurate-after-entity-deletion-and-subsequent-changes.md",
        "onetest-ai Test Case link",
    )
    def test_folder_count_accurate_after_entity_deletion(
        self,
        page: Page,
        social_folder_entity_type: str,
        social_folder_binding: EntityTypeBinding,
        social_folder_cleanup,
    ):
        """(3) → delete one entity from inside the folder via its normal
        delete UI → (2) with no refresh → close/reopen still (2) → add one
        → (3) → remove one → (2), panel == backend, membership {e1, e2}."""
        binding = social_folder_binding
        list_page = binding.list_page_cls(page)
        folders = FolderSection(page, binding.folder_entity_type)
        console_errors = collect_console_errors(page)
        folder_name = disposable_folder_name("3210", binding)

        # Transit: four disposable entities via the API (e1–e3 filed in step 1, e4 spare for step 4).
        e1, e2, e3, e4 = create_disposable_entities(binding, social_folder_cleanup, "3210", 4)

        with allure.step(f"Step 0 — Open the {binding.key} list; all four entities present"):
            binding.open_list(list_page, folders)  # the type's own navigate() + #2305 transit guard
            for entity in (e1, e2, e3, e4):
                folders.move_to_folder_button(entity["id"]).wait_for(state="attached", timeout=UI_ELEMENT_TIMEOUT)
            assert folders.url_folder_param() is None, f"no folder should be open yet: {page.url}"

        with allure.step("Step 1 — Assign three entities to a disposable folder: count shows (3)"):
            folder_id, _ = folders.create_folder(folder_name)
            social_folder_cleanup.register_folder(folder_id)
            expect(folders.folder_item_count(folder_id)).to_have_text("(0)", timeout=UI_ELEMENT_TIMEOUT)
            for n, entity in enumerate((e1, e2, e3), start=1):
                folders.move_entity_to_folder(entity["id"], folder_id)
                expect(folders.folder_item_count(folder_id)).to_have_text(f"({n})", timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 2 — From inside the folder, delete e3 via the normal entity delete action: 3 → 2"):
            folders.open_folder(
                folder_id, binding.list_path_fragment, expected_ids={str(e["id"]) for e in (e1, e2, e3)}
            )
            folders.expect_folder_param(folder_id)
            expect(folders.header_count).to_have_text("(3)", timeout=UI_ELEMENT_TIMEOUT)
            expect(binding.cards(list_page)).to_have_count(3, timeout=UI_ELEMENT_TIMEOUT)
            binding.delete_via_ui(page, e3)  # the product's own delete UI; ends on the list route — NO reload issued
            logger.info("landed on %s after deleting %s", page.url, e3["name"])
            expect(folders.folder_item(folder_id)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(folders.folder_item_count(folder_id)).to_have_text("(2)", timeout=UI_ELEMENT_TIMEOUT)
            expect(folders.move_to_folder_button(e3["id"])).to_have_count(0)

        with allure.step("Step 3 — Close and reopen the folder: count still (2)"):
            if folders.url_folder_param() is not None:
                # navigate(-1) types (pipelines, toolkits) come back with the folder still open
                folders.close_folder(binding.list_path_fragment, wait_for_list=False)
            # Re-opens/re-closes within one mount may be served from the RTK cache (no request),
            # so the open/closed state is taken from the URL param + header, and every count/card
            # read below auto-retries.
            folders.open_folder(folder_id, binding.list_path_fragment)
            expect(folders.header_count).to_have_text("(2)", timeout=UI_ELEMENT_TIMEOUT)
            expect(binding.cards(list_page)).to_have_count(2, timeout=UI_ELEMENT_TIMEOUT)
            for entity in (e1, e2):
                expect(folders.move_to_folder_button(entity["id"])).to_have_count(1)
            folders.close_folder(binding.list_path_fragment, wait_for_list=False)
            expect(folders.folder_item_count(folder_id)).to_have_text("(2)")
            folders.open_folder(folder_id, binding.list_path_fragment)
            expect(folders.folder_item_count(folder_id)).to_have_text("(2)")
            expect(folders.header_count).to_have_text("(2)", timeout=UI_ELEMENT_TIMEOUT)
            expect(binding.cards(list_page)).to_have_count(2, timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 4 — Add one more entity (e4) from the complete list: 2 → 3"):
            folders.close_folder(binding.list_path_fragment, wait_for_list=False)  # e4 is only on the complete list
            folders.move_to_folder_button(e4["id"]).wait_for(state="attached", timeout=UI_ELEMENT_TIMEOUT)
            folders.move_entity_to_folder(e4["id"], folder_id)
            expect(folders.folder_item_count(folder_id)).to_have_text("(3)", timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 5 — Remove e4 from the folder: 3 → 2 with no drift"):
            _, refetch = folders.remove_entity_from_folder(e4["id"])
            expect(folders.folder_item_count(folder_id)).to_have_text("(2)", timeout=UI_ELEMENT_TIMEOUT)
            backend_count = FolderSection.entities_count_from_refetch(refetch, folder_id)
            assert backend_count == 2, f"backend entities_count={backend_count!r} while the panel reads (2) — drift"
            # membership changed since the last open (e4 in, then out) — the list GET fires with fresh ids
            folders.open_folder(folder_id, binding.list_path_fragment, expected_ids={str(e1["id"]), str(e2["id"])})
            expect(folders.header_count).to_have_text("(2)", timeout=UI_ELEMENT_TIMEOUT)
            expect(binding.cards(list_page)).to_have_count(2, timeout=UI_ELEMENT_TIMEOUT)
            for entity in (e1, e2):
                expect(folders.move_to_folder_button(entity["id"])).to_have_count(1)
            expect(folders.move_to_folder_button(e4["id"])).to_have_count(0)

        with allure.step("Axis 2 — No unexpected console errors"):
            unexpected = list(console_errors)
            if binding.known_defect_url_fragment is not None:
                # Known defect: #2303 (skills) / #1666 (credentials) — the stale post-delete GET → 404,
                # excluded by its exact URL only (never by status code).
                unexpected = exclude_known_defect_urls(unexpected, binding.known_defect_url_fragment(e3))
            assert not unexpected, (
                f"Unexpected console errors ({binding.known_defect_ref or 'no known defect'}): {unexpected}"
            )
