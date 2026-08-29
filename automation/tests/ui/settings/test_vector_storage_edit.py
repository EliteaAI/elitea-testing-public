"""UI test — Edit an existing Vector Storage configuration.

Test case: ELITEA-2400
AFS: test-specs/settings-ai-providers/l3_edit-vector-storage-configuration_ELITEA-2400.md

Case-identity note (reused from ELITEA-2392, filed as
EliteaAI/elitea-testing-public#1250): "Settings -> AI Configuration -> Vector
Storage section" is Settings -> **AI Providers** (`/settings/ai-providers`) ->
the **Vector Storage** accordion. Not re-filed.

Declared transit (AFS § Preconditions, `.agents/testing.md` § Fidelity policy):
the case assumes "an existing vector storage card", which does not exist by
default — on the shared test projects the section starts empty and therefore
renders nothing at all. This test CREATES the configuration it edits, through
the same UI create form a user would use. That is transit only: it merely
reaches the state the case's step 1 assumes, and the case's own observable —
the renamed card in the Vector Storage section — is still produced entirely by
the product. Nothing is mocked, injected or fabricated.

**Precondition guard.** `CredentialsControls.jsx`'s `isLastInSection` makes the
ONLY vector storage in a project permanently undeletable through the UI, and
Vector Storage has no shared configurations to pad the count. So this test
refuses to run unless the section already holds >=1 OTHER configuration,
failing loudly rather than leaving permanent residue (`_surface.md`; routed to
a human on #1988 § 4).

**This test MUTATES shared, live project configuration** — one configuration is
created and, at the end, deleted in a `finally` under whichever name is
currently live, so a failure between the rename and the verification still
tears down. Creating a Vector Storage configuration additionally ASSIGNS it as
the section's default (live contract, measured during ELITEA-2399's
implementation — unlike the LLMs section), so the pre-existing default is
captured up front and restored before the delete. The edit itself does not
touch the default, but it does re-derive the configuration's `elitea_title`,
which is the key the default is stored under.

Markers:
    - ui, settings, p2 (this suite's l3 -> p2, matching the sibling
      ELITEA-2392 / ELITEA-2396 tests), regression, new
"""

import logging
import re
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

EDIT_URL_PATTERN = re.compile(r"/settings/edit-ai-provider/\d+")


def _slug(display_name: str) -> str:
    """The read-only ID (`elitea_title`) the form derives from *display_name*."""
    return display_name.lower().replace(" ", "_")


class TestEditVectorStorageConfiguration:
    """ELITEA-2400 — edit an existing Vector Storage configuration in place."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2400.md",
        "onetest-ai Test Case link",
    )
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/1988", "Case-text clarification #1988")
    def test_edit_pgvector_display_name(self, page):
        """Open an existing Vector Storage card, verify the edit form is
        pre-populated and inert while pristine, rename it, and verify the
        section reflects the new name IN PLACE (no duplicate, no orphan)."""
        providers_page = AIProvidersPage(page)
        form = AiProviderFormPage(page)
        page.on("dialog", lambda dialog: dialog.accept())

        # `toolkit-field-label-input` carries maxlength="32" and truncates
        # SILENTLY, so the per-run suffix is trimmed to keep the LONGER of the
        # two names ("Autotest PGVector Edited " = 25 + 5 = 30) inside it.
        suffix = str(int(time.time()))[-5:]
        seed_display_name = f"Autotest PGVector {suffix}"
        edited_display_name = f"Autotest PGVector Edited {suffix}"
        live_display_name = seed_display_name
        seeded_card_count = None
        original_default_value = None
        default_changed = False
        body_completed = False

        try:
            with allure.step(f"Step 0 (transit) — Create the configuration {seed_display_name!r} through the UI"):
                providers_page.navigate()
                providers_page.ensure_project_selected(SEEDED_PROJECT_ID)
                response = providers_page.navigate_and_capture_vectorstorage_response()
                assert response.status == 200, f"Vector Storage models request failed: {response.status}"
                body = response.json()
                existing_total = body["total"]
                assert existing_total >= 1, (
                    "The Vector Storage section is EMPTY. The configuration this test creates would then be "
                    "the only one and permanently undeletable through the UI (isLastInSection) — refusing "
                    "to leave permanent residue in a shared project (AFS ELITEA-2400 § Preconditions, "
                    "#1988 § 4)."
                )
                original_default_name = body.get("default_model_name")
                assert original_default_name, (
                    "The project's Default vector storage is UNSET. The selector offers no blank option, so "
                    "this test could not restore that state after creating a configuration (which the product "
                    "makes the default) — refusing to mutate shared project configuration."
                )
                original_default_value = f"{original_default_name}<<>>{body['default_model_project_id']}"

                expect(providers_page.vector_storage_section_header).to_be_visible()
                providers_page.isolate_section(providers_page.vector_storage_section_header)
                initial_card_count = providers_page.get_configuration_card_count()

                # A direct route to the create form (transit): it skips the type
                # picker, whose own React "unique key" console error (#656) is
                # unrelated to this case.
                form.navigate_to_create("pgvector")
                # Settle on the SCHEMA render before typing (`_surface.md`).
                form.wait_for_schema_field("connection_string")
                form.set_display_name(seed_display_name)
                form.fill_secret_field("connection_string", CONNECTION_STRING)
                form.save_and_return_to_list()
                providers_page.isolate_section(providers_page.vector_storage_section_header)
                expect(providers_page.card_for_model(seed_display_name)).to_have_count(1)
                seeded_card_count = providers_page.get_configuration_card_count()
                assert seeded_card_count == initial_card_count + 1, (
                    f"Transit did not add exactly one card: {seeded_card_count} vs {initial_card_count}"
                )
                # Creating it made it the section default (live contract) — the
                # `finally` puts the original back.
                default_changed = True

            with allure.step("Step 1 — The Vector Storage section is rendered and holds the card"):
                expect(providers_page.vector_storage_section_header).to_have_attribute("aria-expanded", "true")
                expect(providers_page.card_for_model(seed_display_name)).to_be_visible()
                console_errors = collect_console_errors(page)

            with allure.step("Step 2 — Click the configuration's card; its edit form opens"):
                providers_page.open_model_card(seed_display_name)
                form.wait_for_form()
                expect(page).to_have_url(EDIT_URL_PATTERN)
                logger.info("Editing configuration id %s", form.configuration_id_from_url())

            with allure.step("Step 3 — The edit form is pre-populated and inert while pristine"):
                expect(form.display_name_input).to_have_value(seed_display_name)
                expect(form.id_input).to_have_value(_slug(seed_display_name))
                expect(form.id_input).to_be_disabled()

                # Axis 2 — the stored secret is NEVER echoed back: what comes
                # back is a masked placeholder, not the URI that was typed
                # (`writeOnly`). Asserted as "not the secret, and still a
                # password field" rather than pinning the placeholder's own
                # value, which the server regenerates.
                connection_string_input = form.secret_native_input("connection_string")
                expect(connection_string_input).to_have_attribute("type", "password")
                masked_value = connection_string_input.input_value()
                assert masked_value, "The stored Connection String came back EMPTY on the edit form"
                assert masked_value != CONNECTION_STRING, (
                    "The stored Connection String was echoed back verbatim — a write-only secret leaked "
                    f"into the DOM: {masked_value!r}"
                )

                # Axis 2 — the dirty-state contract. Step 5 is meaningless if
                # Save was clickable all along.
                expect(form.save_button).to_be_disabled()
                expect(form.discard_button).to_be_disabled()

            with allure.step(f"Step 4 — Change the Display Name to {edited_display_name!r}"):
                form.set_display_name(edited_display_name)
                live_display_name = edited_display_name
                expect(form.display_name_input).to_have_value(edited_display_name)
                expect(form.save_button).to_be_enabled()
                expect(form.discard_button).to_be_enabled()
                # Live behaviour (AFS § Observations): the disabled ID field
                # re-derives from the new label — and it is not cosmetic, the
                # server persists it, which changes this configuration's
                # Default-selector option testid.
                expect(form.id_input).to_have_value(_slug(edited_display_name))

            with allure.step("Step 5 — Click Save; the app returns to the AI Providers list"):
                form.save_and_return_to_list()
                expect(providers_page.vector_storage_section_header).to_be_visible()
                providers_page.isolate_section(providers_page.vector_storage_section_header)

            with allure.step("Step 6 — The Vector Storage section reflects the updated Display Name in place"):
                expect(providers_page.card_for_model(edited_display_name)).to_have_count(1)
                # Axis 2 — an UPDATE, not a create-and-orphan: the old name is
                # gone and the section did not grow.
                expect(providers_page.card_for_model(seed_display_name)).to_have_count(0)
                expect(providers_page.configuration_cards).to_have_count(seeded_card_count)

            with allure.step("Axis 2 — No console errors before teardown"):
                # Asserted BEFORE the delete: the app re-fetches the deleted
                # record afterwards and logs a 404 (AFS § Cleanup).
                # Known defect: #1971 — project-id-less toolkitTypes 404.
                unexpected = exclude_known_defect_urls(console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL)
                assert not unexpected, f"Unexpected console errors: {unexpected}"

            body_completed = True
        finally:
            # Restore the default FIRST: while the transit configuration is the
            # section default it is what the rest of the suite reads, and
            # deletion is additionally blocked while only one remains.
            if default_changed and original_default_value:
                restore_section_default(
                    providers_page,
                    providers_page.vector_storage_section_header,
                    providers_page.vector_storage_default_selector_combobox,
                    original_default_value,
                )
            # Look the name up rather than assume which of the two is live, so
            # a failure between steps 4 and 6 still tears down.
            final_count = delete_configurations_if_present(
                providers_page,
                form,
                providers_page.vector_storage_section_header,
                [live_display_name, seed_display_name, edited_display_name],
            )
            if body_completed and final_count is not None and seeded_card_count is not None:
                assert final_count == seeded_card_count - 1, (
                    f"Cleanup did not restore the card count: {final_count} != {seeded_card_count - 1}"
                )
