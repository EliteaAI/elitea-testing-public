"""UI test — Set a Vector Storage as default (Settings -> AI Providers).

Test case: ELITEA-2401
AFS: test-specs/settings-ai-providers/l3_set-vector-storage-as-default_ELITEA-2401.md

Case-identity note (reused from ELITEA-2392, filed as
EliteaAI/elitea-testing-public#1250): "Settings -> AI Configuration" is the
"AI Providers" page (`/settings/ai-providers`); the "Default vector storage"
dropdown lives inside the **Vector Storage** accordion, which must be expanded
first (accordion content unmounts on collapse). Not re-filed.

**This spec is SANCTIONED-RED on EliteaAI/elitea-testing-public#1987.**
Steps 1-4 pass: the dropdown lists every configuration, a different one can be
selected, the assignment persists (POST 200, and the follow-up GET reports
`"default": true`) and the combobox label updates. Step 5 — "the selected card
gains a 'Default' badge" — fails on a real product defect: no Vector Storage
card ever renders one. `ConfigurationSection.jsx:212` builds the card's key as
`` `${configuration.data?.name || configuration.label}<<>>${project_id}` ``,
but a pgvector configuration has no `data.name`, so the key falls back to the
LABEL while `defaultSettingValue` is the `elitea_title` — they can never be
equal. Every other section supplies `data.name` and renders the badge.

Per `.agents/testing.md` § Merge gate (*Analysis-time entry*), step 5 is
asserted as the CORRECT expected behaviour with `expect.soft()` +
`# Known defect: #1987`: steps 1-4 keep reporting and the spec flips green the
day the product is fixed. Nothing is weakened, skipped or masked. A soft-assert
failure IS a pytest FAILURE (`.agents/testing.md`, verified in-venv
2026-08-22), so this test is expected to FAIL until #1987 ships.

Case-text drift (filed as a CLARIFICATION, #1988 § 3): the dropdown labels its
options with the configuration's `elitea_title`, not its Display Name — the
same missing `data.name` that causes #1987. Asserted as the live contract per
the reverse-masking guard.

Declared transit (`.agents/testing.md` § Fidelity policy): the case's step 3
says "select a DIFFERENT vector storage configuration", which is unsatisfiable
with one. This test creates the second one through the same UI create form a
user would use — transit only; the case's own observables (the combobox label,
the persisted default, the badge) are all produced by the product. Nothing is
mocked, injected or fabricated. The API is READ as an oracle for the current
default and the option set, never fabricated.

The transit has a second half, and it is not optional. Creating a Vector
Storage configuration ASSIGNS it as the section default (live contract,
measured during ELITEA-2399's implementation — unlike the LLMs section), so
straight after creating it the transit configuration IS the default and the
case's "select a different one" would be a no-op. Setup therefore puts the
PRE-EXISTING default back first, so the selection the case asks for is a
genuine change the product has to perform.

**Precondition guard.** `CredentialsControls.jsx`'s `isLastInSection` makes the
ONLY vector storage in a project permanently undeletable, and Vector Storage
has no shared configurations to pad the count — so this test refuses to run
unless the section already holds >=1 configuration. It also refuses when the
section has NO default at start: the selector offers no blank/unset option
(`_surface.md`), so that state could not be restored.

**This test MUTATES shared, live project configuration** — the project's
Default vector storage is reassigned and restored, and the transit
configuration is deleted, both in a `finally`. The default is restored BEFORE
the delete, so the pre-existing configuration is the survivor.

Markers:
    - ui, settings, p2 (this suite's l3 -> p2, matching the sibling
      ELITEA-2392 / ELITEA-2397 tests), regression, new
"""

import logging
import time

import allure
import pytest
from config import settings
from pages.ai_provider_form_page import AiProviderFormPage
from pages.ai_providers_page import AIProvidersPage
from playwright.sync_api import expect
from utils.ai_provider_teardown import delete_configurations_if_present, restore_section_default
from utils.console_errors import (
    TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL,
    collect_console_errors,
    exclude_known_defect_urls,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

CONNECTION_STRING = "postgresql://autotest:autotest@localhost:5432/autotest"

#: The project the Vector Storage cases run against. NOT a convenience: the
#: acting user's default project ("Private", 399) has ZERO vector storages, and
#: `isLastInSection` makes the FIRST one in a project permanently undeletable
#: through the UI — so a spec landing there would either be unable to run or
#: would leave permanent residue in shared state. This project carries the
#: deliberate permanent seed the analyst established for these cases
#: (`_surface.md`). Switching to it is a real user action through the sidebar
#: project selector, the same one several merged chat/artifacts specs use.
SEEDED_PROJECT_ID = settings.ai_providers_seeded_project_id


def _slug(display_name: str) -> str:
    """The read-only ID (`elitea_title`) the form derives from *display_name*."""
    return display_name.lower().replace(" ", "_")


def _option_value(name: str, project_id: int) -> str:
    """The Default-selector option value the product builds.

    For Vector Storage ``name`` is the configuration's ``elitea_title`` — the
    ``items[].name`` the models API returns for this section (`_surface.md`).
    """
    return f"{name}<<>>{project_id}"


class TestSetVectorStorageAsDefault:
    """ELITEA-2401 — assign a Vector Storage configuration as the project default."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2401.md",
        "onetest-ai Test Case link",
    )
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/1987", "Known defect #1987")
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/1988", "Case-text clarification #1988")
    def test_set_vector_storage_as_default(self, page):
        """Open the Vector Storage Default selector, select a different
        configuration, and verify the assignment persists, the label updates and
        the selected card gains a Default badge (the last one is #1987)."""
        providers_page = AIProvidersPage(page)
        form = AiProviderFormPage(page)
        page.on("dialog", lambda dialog: dialog.accept())

        # maxlength="32", silent truncation — "Autotest PGVector Alt " is 22.
        suffix = str(int(time.time()))[-5:]
        transit_display_name = f"Autotest PGVector Alt {suffix}"
        transit_title = _slug(transit_display_name)
        original_default_value = None
        default_changed = False
        body_completed = False

        try:
            with allure.step(f"Step 0 (transit) — Ensure a second configuration {transit_display_name!r} exists"):
                providers_page.navigate()
                providers_page.ensure_project_selected(SEEDED_PROJECT_ID)
                response = providers_page.navigate_and_capture_vectorstorage_response()
                assert response.status == 200, f"Vector Storage models request failed: {response.status}"
                seed_body = response.json()
                assert seed_body["total"] >= 1, (
                    "The Vector Storage section is EMPTY. The configuration this test creates would then be "
                    "the only one and permanently undeletable through the UI (isLastInSection) — refusing "
                    "to leave permanent residue in a shared project (AFS ELITEA-2401 § Preconditions, "
                    "#1988 § 4)."
                )
                pre_transit_default_name = seed_body.get("default_model_name")
                assert pre_transit_default_name, (
                    "The project's Default vector storage is UNSET. The selector offers no blank option, so "
                    "this test cannot restore that state after assigning one — refusing to mutate shared "
                    "project configuration (AFS ELITEA-2401 § Cleanup)."
                )
                original_default_value = (
                    f"{pre_transit_default_name}<<>>{seed_body['default_model_project_id']}"
                )
                expect(providers_page.vector_storage_section_header).to_be_visible()

                # A direct route to the create form (transit): it skips the type
                # picker, whose own React "unique key" console error (#656) is
                # unrelated to this case.
                form.navigate_to_create("pgvector")
                form.set_display_name(transit_display_name)
                form.replace_secret_value("connection_string", CONNECTION_STRING)
                form.save_and_return_to_list()
                default_changed = True

                # Creating it made it the default (live contract), which would
                # turn the case's step 3 into a no-op — put the pre-existing
                # default back so the selection is a genuine change.
                providers_page.isolate_section(providers_page.vector_storage_section_header)
                providers_page.select_default_configuration(
                    providers_page.vector_storage_default_selector_combobox, original_default_value
                )
                expect(providers_page.vector_storage_default_selector_combobox).to_have_text(
                    pre_transit_default_name
                )

            with allure.step("Step 1 — Expand Vector Storage and capture the current default"):
                response = providers_page.navigate_and_capture_vectorstorage_response()
                assert response.status == 200, f"Vector Storage models request failed: {response.status}"
                body = response.json()
                items = body["items"]
                total = body["total"]
                assert total >= 2, (
                    f"The case needs a DIFFERENT configuration to select; the section holds {total}"
                )

                original_default_name = body["default_model_name"]
                assert original_default_name == pre_transit_default_name, (
                    f"Setup did not restore the pre-existing default: {original_default_name!r} != "
                    f"{pre_transit_default_name!r}"
                )
                target_item = next((i for i in items if i["name"] == transit_title), None)
                assert target_item, (
                    f"The transit configuration {transit_title!r} is not offered by the Default selector"
                )
                target_value = _option_value(target_item["name"], target_item["project_id"])
                assert target_value != original_default_value, (
                    f"The transit configuration is ALREADY the default ({target_value!r}) — the case needs "
                    "to select a different one"
                )

                providers_page.isolate_section(providers_page.vector_storage_section_header)
                console_errors = collect_console_errors(page)
                # The label is the elitea_title in this section, not a display
                # name (#1988 § 3) — asserted as the live contract.
                expect(providers_page.vector_storage_default_selector_combobox).to_have_text(original_default_name)
                logger.info("Default before: %r; selecting %r", original_default_value, target_value)

            with allure.step("Step 2 — Open the Default vector storage dropdown"):
                providers_page.vector_storage_default_selector_combobox.click()
                # Axis 2 — the option set matches the section's configuration
                # set one-for-one: no extras, none missing.
                expect(providers_page.open_select_options).to_have_count(total)
                for item in items:
                    option_value = _option_value(item["name"], item["project_id"])
                    expect(providers_page.select_option(option_value)).to_be_visible()
                expect(providers_page.select_option(original_default_value)).to_have_attribute(
                    "aria-selected", "true"
                )
                providers_page.close_open_dropdown()

            with allure.step(f"Step 3 — Select the different configuration {transit_title!r}"):
                set_default_response = providers_page.select_default_configuration(
                    providers_page.vector_storage_default_selector_combobox, target_value
                )
                default_changed = True
                assert set_default_response.status == 200, (
                    f"Set-default request failed: {set_default_response.status}"
                )

            with allure.step("Step 4 — The dropdown updates to show the selected configuration"):
                expect(providers_page.vector_storage_default_selector_combobox).to_have_text(transit_title)

            with allure.step("Step 4b — The assignment persisted, and the default is exclusive"):
                # Axis 2 — separates "the UI label changed" from "the setting
                # persisted", which is what lets #1987 be classified as
                # display-only rather than reported as data loss.
                refreshed = providers_page.navigate_and_capture_vectorstorage_response()
                assert refreshed.status == 200, f"Vector Storage models request failed: {refreshed.status}"
                refreshed_body = refreshed.json()
                assert refreshed_body["default_model_name"] == transit_title, (
                    f"Default not persisted: {refreshed_body['default_model_name']!r} != {transit_title!r}"
                )
                refreshed_items = {i["name"]: i for i in refreshed_body["items"]}
                assert refreshed_items[transit_title]["default"] is True, (
                    f"The selected configuration is not marked default: {refreshed_items[transit_title]}"
                )
                # A default is exclusive — asserting only the new one would pass
                # against a bug that marks two.
                assert refreshed_items[original_default_name]["default"] is False, (
                    f"The previous default is still marked default: {refreshed_items[original_default_name]}"
                )

            with allure.step("Step 5 — The selected configuration's card gains a 'Default' badge"):
                providers_page.isolate_section(providers_page.vector_storage_section_header)
                # Known defect: #1987 — no Vector Storage card ever renders the
                # badge (configKey falls back to the label while the selector
                # keys by elitea_title). Asserted as the CORRECT expected
                # behaviour, softly, so steps 1-4 keep reporting. Do not weaken.
                expect.soft(providers_page.card_tier_badge(transit_display_name, "Default")).to_be_visible()

            with allure.step(f"Step 5 (cleanup half) — Restore the original default {original_default_name!r}"):
                providers_page.select_default_configuration(
                    providers_page.vector_storage_default_selector_combobox, original_default_value
                )
                default_changed = False
                expect(providers_page.vector_storage_default_selector_combobox).to_have_text(original_default_name)

            with allure.step("Axis 2 — No console errors before teardown"):
                # Asserted BEFORE the delete: the app re-fetches the deleted
                # record afterwards and logs a 404 (AFS § Cleanup).
                # Known defect: #1971 — project-id-less toolkitTypes 404.
                unexpected = exclude_known_defect_urls(console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL)
                assert not unexpected, f"Unexpected console errors: {unexpected}"

            body_completed = True
        finally:
            # Restore the default FIRST: deletion is blocked while only one
            # configuration remains, and the pre-existing one must be the
            # survivor AND the default.
            if default_changed and original_default_value:
                restore_section_default(
                    providers_page,
                    providers_page.vector_storage_section_header,
                    providers_page.vector_storage_default_selector_combobox,
                    original_default_value,
                )

            final_count = delete_configurations_if_present(
                providers_page, form, providers_page.vector_storage_section_header, [transit_display_name]
            )
            if body_completed:
                assert final_count is not None, "Teardown could not delete the transit configuration"
