"""UI test — Create a new Vector Storage (PGVector) configuration.

Test case: ELITEA-2399
AFS: test-specs/settings-ai-providers/l3_create-vector-storage-pgvector-configuration_ELITEA-2399.md

Case-identity note (reused from ELITEA-2392, filed as
EliteaAI/elitea-testing-public#1250): "Settings -> AI Configuration" is the
"AI Providers" page (`/settings/ai-providers`). Not re-filed.

Case-text drift SPECIFIC to this case (filed as a CLARIFICATION,
EliteaAI/elitea-testing-public#1988):

* steps 2-3 — "Click '+' -> select 'Vector Storage'" then "Select provider:
  PGVector" are ONE click, not two. The "+" opens a flat 12-card type picker
  with no "Vector Storage" entry; the card is "PgVector"
  (`toolkit-type-card-pgvector`) and lands straight on the pgvector form.
  "Vector Storage" is the name of the accordion SECTION on the list page
  (#1988 § 2).
* step 9 — the Default vector storage dropdown labels its options with the
  configuration's `elitea_title`, not its Display Name, because a pgvector
  configuration carries no `data.name` (#1988 § 3).

Per the reverse-masking guard (`.agents/testing.md`) this test asserts the LIVE
contract and the drift is filed rather than silently absorbed.

No substitution of the system under test: the configuration is created through
the real "+" -> PgVector -> Save flow, and every observable (the card, its
status text, the Default selector's option) is produced by the product. The
only API involvement is READING the product's own `section=vectorstorage`
models response — as the precondition oracle (below) and for the ACTIVE PROJECT
ID that keys the option testid. Nothing is fabricated.

**Precondition guard, and it is load-bearing rather than decorative.**
`CredentialsControls.jsx`'s `isLastInSection` makes the ONLY vector storage in
a project permanently undeletable through the UI, and Vector Storage — unlike
Embedding — has no shared configurations to pad the count. So a project going
0 -> 1 can never go back. This test therefore refuses to run unless the section
already holds >=1 configuration, failing loudly instead of leaving permanent
residue (`_surface.md`; routed to a human on #1988 § 4).

**This test MUTATES shared, live project configuration** — the created
configuration is deleted in a `finally`. The project's Default vector storage
is deliberately NOT changed: step 9 asserts option INCLUSION only, as the case
asks, and the dropdown is dismissed with Escape (selecting is ELITEA-2401).

Markers:
    - ui, settings, p2 (this suite's l3 -> p2, matching the sibling
      ELITEA-2392 / ELITEA-2395 / ELITEA-2397 tests), regression, new
"""

import logging
import re
import time

import allure
import pytest
from pages.ai_provider_form_page import AiProviderFormPage
from pages.ai_providers_page import AIProvidersPage, project_id_from_models_response
from playwright.sync_api import expect
from utils.ai_provider_teardown import delete_configurations_if_present
from utils.console_errors import (
    TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL,
    collect_console_errors,
    exclude_known_defect_urls,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

#: The case's "a valid PostgreSQL connection string". Nothing ever dials it —
#: pgvector's schema declares `has_test_connection: false`, so the Test
#: connection button stays disabled and no connection is attempted.
CONNECTION_STRING = "postgresql://autotest:autotest@localhost:5432/autotest"

CREATE_PICKER_URL_PATTERN = re.compile(r"/settings/create-ai-provider(\?|$)")
CREATE_PGVECTOR_FORM_URL_PATTERN = re.compile(r"/settings/create-ai-provider/pgvector")


def _slug(display_name: str) -> str:
    """The read-only ID (`elitea_title`) the form derives from *display_name*."""
    return display_name.lower().replace(" ", "_")


class TestCreateVectorStorageConfiguration:
    """ELITEA-2399 — create a PGVector Vector Storage configuration."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2399.md",
        "onetest-ai Test Case link",
    )
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/1988", "Case-text clarification #1988")
    def test_create_pgvector_configuration(self, page):
        """Create a PGVector configuration through the UI, verify its card
        appears in the Vector Storage section with an OK status, and verify the
        section's Default selector offers it."""
        providers_page = AIProvidersPage(page)
        form = AiProviderFormPage(page)
        page.on("dialog", lambda dialog: dialog.accept())

        # maxlength="32", silent truncation — "Autotest PGVector " is 18.
        suffix = str(int(time.time()))[-5:]
        display_name = f"Autotest PGVector {suffix}"
        initial_card_count = None
        body_completed = False

        try:
            with allure.step("Step 1 — Open Settings -> AI Providers and guard the Vector Storage precondition"):
                response = providers_page.navigate_and_capture_vectorstorage_response()
                assert response.status == 200, f"Vector Storage models request failed: {response.status}"
                project_id = project_id_from_models_response(response)
                existing_total = response.json()["total"]
                assert existing_total >= 1, (
                    "The Vector Storage section is EMPTY. Creating the first configuration in a project "
                    "makes it permanently undeletable through the UI (isLastInSection, and Vector Storage "
                    "has no shared configurations) — refusing to leave permanent residue in a shared "
                    "project (AFS ELITEA-2399 § Known constraints, #1988 § 4)."
                )
                logger.info("Active project id %s, %s existing vector storage(s)", project_id, existing_total)

                expect(providers_page.page_title).to_have_text("AI Providers")
                expect(providers_page.vector_storage_section_header).to_be_visible()
                providers_page.expand_section(providers_page.vector_storage_section_header)
                initial_card_count = providers_page.get_configuration_card_count()
                # The section's current Default, as the product renders it —
                # captured so step 9 can prove creation did not reassign it.
                initial_default_label = providers_page.vector_storage_default_selector_combobox.text_content()
                logger.info("Baseline: %s cards, Default=%r", initial_card_count, initial_default_label)

            with allure.step("Step 2 — Click '+' in the AI Providers header"):
                providers_page.click_create()
                expect(page).to_have_url(CREATE_PICKER_URL_PATTERN)

            with allure.step("Step 3 — Select the 'PgVector' provider type (the case's steps 2-3 are one click)"):
                providers_page.click_type_card("pgvector")
                form.wait_for_form()
                expect(page).to_have_url(CREATE_PGVECTOR_FORM_URL_PATTERN)
                # Console axis scoped to the create form and everything after
                # it; the type-picker page's own React "unique key" error
                # (#656) belongs to that page, not to this case's subject.
                console_errors = collect_console_errors(page)
                expect(form.save_button).to_be_disabled()

            with allure.step(f"Steps 4-5 — Fill Display Name {display_name!r}"):
                form.set_display_name(display_name)
                expect(form.display_name_input).to_have_value(display_name)
                expect(form.id_input).to_have_value(_slug(display_name))
                expect(form.id_input).to_be_disabled()
                # Axis 2 — on the pgvector form the Display Name ALONE completes
                # the record: `connection_string` is schema-optional (no
                # `data.required` array at all), so it does not gate Save. The
                # before/after pair is what makes that a claim rather than a
                # coincidence.
                expect(form.save_button).to_be_enabled()

            with allure.step("Step 6 — Fill the Connection String"):
                form.replace_secret_value("connection_string", CONNECTION_STRING)
                connection_string_input = form.secret_native_input("connection_string")
                expect(connection_string_input).to_have_value(CONNECTION_STRING)
                # Axis 2 — the field is a secret: a regression rendering it as
                # plain text would leak a DB URI into every screenshot and DOM
                # dump. (The stored value never comes back after Save —
                # `writeOnly` — so this is asserted only before Save.)
                expect(connection_string_input).to_have_attribute("type", "password")

            with allure.step("Step 7 — Save; the app returns to the AI Providers list"):
                form.save_and_return_to_list()
                expect(providers_page.vector_storage_section_header).to_be_visible()
                providers_page.expand_section(providers_page.vector_storage_section_header)

            with allure.step("Step 8 — The new card is in the Vector Storage section"):
                # Axis 2 — a CREATE, not an in-place update of an existing
                # configuration (ELITEA-2400 exercises the update path; the two
                # must stay distinguishable).
                expect(providers_page.configuration_cards).to_have_count(initial_card_count + 1)
                card = providers_page.card_for_model(display_name)
                expect(card).to_be_visible()
                expect(card).to_contain_text("OK •")

            with allure.step("Step 9 — The Default vector storage dropdown offers the new configuration"):
                # Axis 2 — creation must not silently reassign the project's
                # Default vector storage.
                expect(providers_page.vector_storage_default_selector_combobox).to_have_text(initial_default_label)

                providers_page.vector_storage_default_selector_combobox.click()
                # Keyed by `elitea_title`, NOT by a model name — this section's
                # own convention, and the reason #1987 exists (#1988 § 3).
                option = providers_page.select_option(f"{_slug(display_name)}<<>>{project_id}")
                expect(option).to_be_visible()
                # Labelled with the ID as well, unlike every other section.
                expect(option).to_have_text(_slug(display_name))
                expect(option).to_have_attribute("aria-selected", "false")
                providers_page.close_open_dropdown()

            with allure.step("Axis 2 — No console errors before teardown"):
                # Asserted BEFORE the delete: the app re-fetches the deleted
                # record afterwards and logs a 404 (AFS § Cleanup).
                # Known defect: #1971 — project-id-less toolkitTypes 404.
                unexpected = exclude_known_defect_urls(console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL)
                assert not unexpected, f"Unexpected console errors: {unexpected}"

            body_completed = True
        finally:
            final_count = delete_configurations_if_present(
                providers_page, form, providers_page.vector_storage_section_header, [display_name]
            )
            if body_completed and final_count is not None and initial_card_count is not None:
                assert final_count == initial_card_count, (
                    f"Cleanup did not restore the card count: {final_count} != {initial_card_count}. "
                    "If the delete menu item was disabled, the precondition guard was bypassed."
                )
