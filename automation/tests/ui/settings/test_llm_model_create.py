"""UI test — Create a new LLM model configuration (Settings -> AI Providers).

Test cases: ELITEA-2395, ELITEA-2412 (extension — the create survives a reload)
AFS: test-specs/settings-ai-providers/l3_create-llm-model-configuration_ELITEA-2395.md
AFS: test-specs/settings-ai-providers/lextend_new-llm-model-persists-after-reload_ELITEA-2412.md

ELITEA-2412 (`extend-existing`) adds Step 12b: its steps 1-2 (create the model,
verify the card appears in the LLM Models section) are this spec's Steps 2-12
verbatim in substance, and its own subject — the card surviving a full
`page.reload()` — was untested here (this spec never reloaded). The extension is
one reload plus a re-assert of the card, placed before the Default work so the
reload observes a pure create. Its case-text literal Display Name "Persist Test
Model" is deliberately NOT used: this spec's per-run generated name is kept, so
a leftover from a failed run cannot collide (declared deviation, AFS § Test Data).

Case-identity note (reused from ELITEA-2392, filed as
EliteaAI/elitea-testing-public#1250): "Settings -> AI Configuration" does not
exist. The real page is "AI Providers" (`/settings/ai-providers`), whose "LLMs"
accordion (case: "LLM Models" / "Integrations section") is what this case
exercises.

Case-text drift SPECIFIC to this case (filed as a CLARIFICATION,
EliteaAI/elitea-testing-public#1985):

* step 11 — "under the 'Other LLM providers' section". Live, the LLMs accordion
  groups its cards under `OpenAI` / `Anthropic` / `Other Providers`
  (`ConfigurationSection.jsx` `GROUP_ORDER`); a newly created custom model
  lands in the **"Other Providers" group inside the LLMs section**, not in a
  section of its own.
* step 13 — "set as default in top menu". There is no top menu; the control is
  the LLMs accordion's own **Default** selector.

Per the reverse-masking guard (`.agents/testing.md`) this test asserts the LIVE
contract and the drift is filed rather than silently absorbed.

No substitution of the system under test: the model is created through the real
"+" -> LLM Model -> Save flow, and every observable (the card, its group, its
status badge, the Default selector's option list and the resulting badge) is
produced by the product. The only API involvement is READING the product's own
`section=llm` models response as an oracle for the current Default value and
for the new model's option value — never fabricating either.

**This test MUTATES shared, live project configuration**: it creates a real LLM
model configuration and temporarily reassigns the project's Default LLM, which
other UI tests in this suite read. Both are restored in a `finally`; the
original Default is captured from the product's own response before anything is
changed. The MUI Default selector offers no "clear"/blank option (confirmed
live), so a project whose Default starts UNSET cannot be restored — this test
fails loudly in that case instead of leaving the project altered.

Markers:
    - ui, settings, p2 (this suite's l3 -> p2, matching the sibling
      ELITEA-2392 / ELITEA-2397 tests), regression, new
"""

import logging
import re
import time

import allure
import pytest
from pages.ai_provider_form_page import AiProviderFormPage
from pages.ai_providers_page import AIProvidersPage
from playwright.sync_api import expect
from utils.console_errors import (
    TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL,
    collect_console_errors,
    exclude_known_defect_urls,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000

MODEL_NAME = "gpt-4o"
#: `elitea_title` of the shared AI credential present in every non-public
#: project (displayed label "ELPS") — picked by title, never by list position.
CREDENTIAL_TITLE = "elps"
CREDENTIAL_LABEL = "ELPS"
#: Form defaults the case happens to specify — asserted, not typed.
DEFAULT_CONTEXT_WINDOW = "128000"
DEFAULT_MAX_OUTPUT_TOKENS = "16000"
#: The LLMs group a custom (non-OpenAI/Anthropic) model lands in.
OTHER_PROVIDERS_GROUP = "Other Providers"

CREATE_PICKER_URL_PATTERN = re.compile(r"/settings/create-ai-provider(\?|$)")
CREATE_LLM_FORM_URL_PATTERN = re.compile(r"/settings/create-ai-provider/llm_model")


def _option_value(item: dict) -> str:
    """The Default-selector option value the product builds for *item*."""
    return f"{item['name']}<<>>{item['project_id']}"


class TestCreateLlmModelConfiguration:
    """ELITEA-2395 — create an LLM model configuration and set it as Default."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2395.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ai-configuration/ELITEA-2412_saving-a-new-llm-model-configuration-persists-after-page-rel.md",
        "onetest-ai Test Case link (ELITEA-2412)",
    )
    @allure.issue("https://github.com/EliteaAI/elitea-testing-public/issues/1985", "Case-text clarification #1985")
    def test_create_llm_model_and_set_as_default(self, page):
        """Create an LLM model through the UI, verify its card lands in the
        LLMs "Other Providers" group with an OK status badge, verify the card
        survives a full page reload (ELITEA-2412), and verify it can be
        assigned as the project's Default LLM."""
        providers_page = AIProvidersPage(page)
        form = AiProviderFormPage(page)
        page.on("dialog", lambda dialog: dialog.accept())

        display_name = f"Autotest LLM Model {int(time.time())}"
        initial_card_count = None
        original_default_value = None
        default_changed = False
        body_completed = False

        try:
            with allure.step("Step 1 — Open Settings -> AI Providers and capture the LLMs baseline"):
                llm_response = providers_page.navigate_and_capture_llm_response()
                assert llm_response.status == 200, f"LLM models request failed: {llm_response.status}"
                llm_body = llm_response.json()

                expect(providers_page.page_title).to_have_text("AI Providers")
                expect(providers_page.llms_section_header).to_be_visible()
                initial_card_count = providers_page.get_configuration_card_count()

                # The project's own current Default, read from the product's
                # response — the value this test must put back.
                original_default_name = llm_body.get("default_model_name")
                assert original_default_name, (
                    "The project's Default LLM is UNSET. The selector offers no blank option, so this "
                    "test cannot restore that state after assigning one — refusing to mutate shared "
                    "project configuration (AFS ELITEA-2395 § Cleanup)."
                )
                original_default_value = f"{original_default_name}<<>>{llm_body['default_model_project_id']}"
                original_default_label = next(
                    (i["display_name"] for i in llm_body["items"] if _option_value(i) == original_default_value),
                    None,
                )
                assert original_default_label, (
                    f"Current Default {original_default_value!r} is not among the selector's own options"
                )
                logger.info(
                    "Baseline: %s LLM cards, Default=%r (%s)",
                    initial_card_count,
                    original_default_label,
                    original_default_value,
                )

            with allure.step("Step 2 — Click '+' in the AI Providers header"):
                providers_page.click_create()
                expect(page).to_have_url(CREATE_PICKER_URL_PATTERN)

            with allure.step("Step 3 — Select the 'LLM Model' provider type"):
                providers_page.click_type_card("llm_model")
                form.wait_for_form()
                expect(page).to_have_url(CREATE_LLM_FORM_URL_PATTERN)
                # Console axis scoped to the create form and everything after
                # it; the type-picker page's own React "unique key" error
                # (#656) belongs to that page, not to this case's subject.
                console_errors = collect_console_errors(page)
                expect(form.save_button).to_be_disabled()

            with allure.step(f"Steps 4-5 — Fill Display Name {display_name!r}"):
                form.set_display_name(display_name)
                expect(form.display_name_input).to_have_value(display_name)
                # The ID mirrors the Display Name (ELITEA-2409's subject).
                expect(form.id_input).to_have_value(display_name.lower().replace(" ", "_"))

            with allure.step(f"Step 6 — Fill Name (model identifier) {MODEL_NAME!r}"):
                form.type_into_field("name", MODEL_NAME)
                expect(form.field("name")).to_have_value(MODEL_NAME)

            with allure.step(f"Step 7 — Context Window already carries the case's value {DEFAULT_CONTEXT_WINDOW}"):
                expect(form.field("context_window")).to_have_value(DEFAULT_CONTEXT_WINDOW)

            with allure.step(f"Step 8 — Max Output Tokens already carries {DEFAULT_MAX_OUTPUT_TOKENS}"):
                expect(form.field("max_output_tokens")).to_have_value(DEFAULT_MAX_OUTPUT_TOKENS)

            with allure.step(f"Step 9 — Select the saved AI credential {CREDENTIAL_LABEL!r}"):
                # Axis 2 — the credential is the last required field: Save is
                # inert until it is chosen, and enabled afterwards. Without the
                # before-state, "Save is enabled" proves nothing about the form
                # knowing the record is complete.
                expect(form.save_button).to_be_disabled()
                form.select_saved_credential(CREDENTIAL_TITLE)
                expect(form.credential_select_combobox).to_have_text(CREDENTIAL_LABEL)
                # Axis 2 — the form now considers the record complete.
                expect(form.save_button).to_be_enabled()

            with allure.step("Step 10 — Save; the app returns to the AI Providers list"):
                form.save_and_return_to_list()
                expect(providers_page.llms_section_header).to_be_visible()

            with allure.step(f"Step 11 — The new card is in the LLMs '{OTHER_PROVIDERS_GROUP}' group"):
                # Axis 2 — a create, not a silent overwrite of an existing card.
                expect(providers_page.configuration_cards).to_have_count(initial_card_count + 1)
                expect(providers_page.card_in_group(OTHER_PROVIDERS_GROUP, display_name)).to_have_count(1)

            with allure.step("Step 12 — The card shows the Display Name and an OK status badge"):
                card = providers_page.card_for_model(display_name)
                expect(card).to_be_visible()
                expect(card).to_contain_text("OK •")

            with allure.step("Step 12b (ELITEA-2412) — The new card survives a full page reload"):
                # ELITEA-2412's own subject: persistence, not re-render. Every
                # assertion above ran inside the SPA session that created the
                # record, so they prove the client re-rendered its own mutation
                # response — not that the server persisted anything. Placed
                # BEFORE the Default work so the reload observes a pure create.
                reload_response = providers_page.reload_and_capture_llm_response()
                assert reload_response.status == 200, (
                    f"LLM models request after reload failed: {reload_response.status}"
                )
                # Accordion content UNMOUNTS on collapse, so a collapsed LLMs
                # section reads as "the card is missing" (AFS ELITEA-2412 § Automation Hints).
                expect(providers_page.llms_section_header).to_have_attribute(
                    "aria-expanded", "true", timeout=UI_ELEMENT_TIMEOUT
                )
                # Axis 2 — the card came back, in the right group, healthy, and
                # exactly once: presence alone would pass for a record that lost
                # its server-derived grouping, its credential link, or got duplicated.
                expect(providers_page.card_in_group(OTHER_PROVIDERS_GROUP, display_name)).to_have_count(1)
                expect(providers_page.card_for_model(display_name)).to_contain_text("OK •")
                expect(providers_page.configuration_cards).to_have_count(initial_card_count + 1)

            with allure.step("Step 13 — The new model can be assigned as the LLMs Default"):
                refreshed = providers_page.navigate_and_capture_llm_response()
                assert refreshed.status == 200, f"LLM models request failed: {refreshed.status}"
                new_item = next(
                    (i for i in refreshed.json()["items"] if i["display_name"] == display_name),
                    None,
                )
                assert new_item, f"The created model {display_name!r} is not offered by the Default selector"

                response = providers_page.select_tier_model(
                    providers_page.llms_default_selector_combobox, _option_value(new_item)
                )
                default_changed = True
                assert response.status == 200, f"Set-default request failed: {response.status}"

                expect(providers_page.llms_default_selector_combobox).to_have_text(display_name)
                expect(providers_page.card_tier_badge(display_name, "Default")).to_be_visible()

            with allure.step(f"Step 13 (cleanup half) — Restore the original Default {original_default_label!r}"):
                providers_page.select_tier_model(
                    providers_page.llms_default_selector_combobox, original_default_value
                )
                default_changed = False
                expect(providers_page.llms_default_selector_combobox).to_have_text(original_default_label)
                expect(providers_page.card_tier_badge(display_name, "Default")).to_have_count(0)

            with allure.step("Axis 2 — No console errors before teardown"):
                # Asserted BEFORE the delete: the app re-fetches the deleted
                # record afterwards and logs a 404 (AFS § Known Defects).
                # Known defect: #1971 — project-id-less toolkitTypes 404.
                unexpected = exclude_known_defect_urls(console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL)
                assert not unexpected, f"Unexpected console errors: {unexpected}"

            body_completed = True
        finally:
            if default_changed and original_default_value:
                try:
                    providers_page.navigate()
                    providers_page.select_tier_model(
                        providers_page.llms_default_selector_combobox, original_default_value
                    )
                    logger.info("Teardown: restored the Default LLM to %r", original_default_value)
                except Exception:
                    logger.exception("Teardown FAILED to restore the Default LLM to %r", original_default_value)

            final_count = _delete_model_if_present(providers_page, form, display_name)
            if body_completed and final_count is not None and initial_card_count is not None:
                assert final_count == initial_card_count, (
                    f"Cleanup did not restore the LLMs card count: {final_count} != {initial_card_count}"
                )


def _delete_model_if_present(providers_page: AIProvidersPage, form: AiProviderFormPage, display_name: str):
    """Delete the configuration named *display_name* if present; return the
    resulting card count, or ``None`` when teardown could not run."""
    try:
        providers_page.navigate()
        providers_page.llms_section_header.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        if providers_page.card_for_model(display_name).count() == 0:
            logger.info("Teardown: no configuration named %r to delete", display_name)
            return providers_page.get_configuration_card_count()
        providers_page.open_model_card(display_name)
        form.wait_for_form()
        form.delete_current_configuration(display_name)
        providers_page.navigate()
        providers_page.llms_section_header.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
        expect(providers_page.card_for_model(display_name)).to_have_count(0)
        return providers_page.get_configuration_card_count()
    except Exception:  # noqa: BLE001 - teardown must never mask the test's own failure
        logger.exception("Teardown failed to delete the configuration %r", display_name)
        return None
