"""UI test — Image Generation / ASR / TTS sections display model cards and a
populated Default selector (Settings -> AI Providers).

Test cases: ELITEA-2402 (Image Generation), ELITEA-2404 (Speech Recognition /
ASR), ELITEA-2406 (Text to Speech / TTS)
AFS: test-specs/settings-ai-providers/l3_section-model-cards-and-default-selector_ELITEA-2402.md

One parameterized test, one row per TMS case: the three cases differ ONLY in
which section they look at (identical actions, identical order, identical
assertions), which is the AFS's own family shape.

Case-identity note (pre-existing, reused from ELITEA-2392, filed as
EliteaAI/elitea-testing-public#1250): all three cases say "Settings -> AI
Configuration". There is no such page — the sections live on "AI Providers"
(`/settings/ai-providers`). Asserted as the live contract per the
reverse-masking guard; NOT re-filed.

Case-text drift, folded into the same #1250 clarification: each case's step 2
is "Locate the <X> section", but only the LLMs accordion auto-expands
(`defaultExpanded={!expandSection || expandSection === 'llm'}`). Image
Generation, ASR and TTS all start COLLAPSED, and while collapsed the accordion
summary renders the default as untestable plain text (no testid, no combobox)
while the real `role="combobox"` selector is not mounted at all. So "locate"
must mean "expand", or steps 3-5 have nothing to act on. The expand is step 2
below.

**This test is READ-ONLY.** It opens the Default dropdown and closes it again
with Escape without selecting anything, so no project state is mutated and no
teardown is owed. Do not let a future edit make it select an option without
inheriting ELITEA-2403's teardown obligations.

Fidelity (`.agents/testing.md` § Fidelity policy): nothing is mocked, stubbed,
routed or injected. The section's own
`GET /configurations/models/{project_id}?...&section={param}` response is READ
as the oracle for the expected card set, the expected option set and the
expected default — every asserted value is produced by the product. The model
set is project-shared and mutable, so no model name is hardcoded anywhere.

Markers:
    - ui, settings, p2 (this suite's l3 -> p2, matching the merged
      ELITEA-2392 / ELITEA-2397 / ELITEA-2401 siblings), regression, new
"""

import logging

import allure
import pytest
from config import settings
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

#: The project these AI-Providers cases run against — the same seeded project
#: the merged ELITEA-2399/2400/2401 specs use, so the whole cluster reads one
#: consistent project's configuration set.
SEEDED_PROJECT_ID = settings.ai_providers_seeded_project_id

TMS_CASE_URL = (
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/settings/ai-configuration/{}"
)

#: (tms_id, section label, `section=` API param, header field, combobox field).
#: The API param is the product's own section key; the page-object field names
#: carry the testid slug (`ai-providers-section-{slug}`), which is not always
#: the same string — hence both.
SECTION_ROWS = [
    pytest.param(
        "ELITEA-2402",
        "Image Generation",
        "image_generation",
        "image_generation_section_header",
        "image_generation_default_selector_combobox",
        "ELITEA-2402_image-generation-section-displays-model-cards-and-default-se.md",
        id="ELITEA-2402-image-generation",
    ),
    pytest.param(
        "ELITEA-2404",
        "Speech Recognition (ASR)",
        "asr",
        "asr_section_header",
        "asr_default_selector_combobox",
        "ELITEA-2404_asr-section-displays-model-cards-and-default-selector.md",
        id="ELITEA-2404-asr",
    ),
    pytest.param(
        "ELITEA-2406",
        "Text to Speech (TTS)",
        "tts",
        "tts_section_header",
        "tts_default_selector_combobox",
        "ELITEA-2406_tts-section-displays-model-cards-and-default-selector.md",
        id="ELITEA-2406-tts",
    ),
]


def _option_value(item: dict) -> str:
    """The Default-selector option value the product builds for *item*.

    ``"{name}<<>>{project_id}"`` — the project id is the model's OWN, not the
    active project's: every model in these three sections is shared from
    project 1 while a locally-created one keys on the active project.
    """
    return f"{item['name']}<<>>{item['project_id']}"


class TestAiProviderSectionCardsAndDefaultSelector:
    """ELITEA-2402 / 2404 / 2406 — a section lists its model cards and exposes a
    populated Default selector whose dropdown enumerates those same models."""

    @pytest.mark.parametrize(
        "tms_id, section_label, section_param, header_field, combobox_field, case_file", SECTION_ROWS
    )
    def test_section_shows_model_cards_and_default_selector(
        self, page, tms_id, section_label, section_param, header_field, combobox_field, case_file
    ):
        """Expand the section, verify its cards carry a name and a status, and
        verify the Default selector shows the section's actual default and drops
        down the section's actual model set."""
        allure.dynamic.issue(TMS_CASE_URL.format(case_file), f"onetest-ai Test Case {tms_id}")
        allure.dynamic.issue(
            "https://github.com/EliteaAI/elitea-testing-public/issues/1250",
            "Case-text clarification #1250",
        )
        providers_page = AIProvidersPage(page)
        section_header = getattr(providers_page, header_field)
        combobox = getattr(providers_page, combobox_field)

        with allure.step(f"Step 1 — Open Settings -> AI Providers and load the {section_label} section"):
            providers_page.navigate()
            providers_page.ensure_project_selected(SEEDED_PROJECT_ID)
            console_errors = collect_console_errors(page)

            response, body = providers_page.navigate_and_capture_section_models_json(section_param)
            assert response.status == 200, f"{section_label} models request failed: {response.status}"
            items = body["items"]
            total = body["total"]
            # The precondition, read from the product's own response. A section
            # with zero configurations renders NOTHING at all
            # (`ConfigurationSection.jsx`: `if (!configurations ||
            # configurations.length === 0) return null;`), so without this the
            # "section not visible" failure below would be indistinguishable
            # from a correct empty-state hide.
            assert total >= 1, (
                f"The {section_label} section holds NO configurations, so it is hidden by design and this "
                f"case has nothing to observe (AFS ELITEA-2402 § Preconditions)."
            )
            assert len(items) == total, f"Response is self-inconsistent: {len(items)} items vs total {total}"
            default_name = body.get("default_model_name")
            assert default_name, (
                f"The project's Default {section_label} model is UNSET; the case's steps 4-5 have no "
                f"non-empty value to observe (AFS ELITEA-2402 § Preconditions)."
            )
            default_value = f"{default_name}<<>>{body['default_model_project_id']}"
            default_label = next((i["display_name"] for i in items if _option_value(i) == default_value), None)
            assert default_label, f"The reported default {default_value!r} is not among the section's own items"

            expect(providers_page.page_title).to_have_text("AI Providers")
            expect(section_header).to_be_visible()
            logger.info("%s: %s configuration(s), default=%r (%s)", section_label, total, default_label, default_value)

        with allure.step(f"Step 2 — Locate and expand the {section_label} accordion"):
            # Only the LLMs accordion auto-expands; this one starts collapsed
            # and its content (including the real combobox) is not mounted.
            expect(section_header).to_have_attribute("aria-expanded", "false")
            # Isolate rather than merely expand: `ai-providers-section-{slug}`
            # sits on the accordion SUMMARY BUTTON, so cards are NOT its DOM
            # descendants and a whole-page card query would silently mix in
            # every other expanded section's cards.
            providers_page.isolate_section(section_header)
            expect(section_header).to_have_attribute("aria-expanded", "true")

        with allure.step("Step 3 — Every configuration card shows a model name and a status"):
            # Parity with the API's own item set: a dropped card is a real
            # regression that "at least one card" would never catch.
            expect(providers_page.configuration_cards).to_have_count(total)
            for item in items:
                display_name = item["display_name"]
                card = providers_page.card_for_model(display_name)
                expect(card).to_have_count(1)
                # `to_contain_text`, never an exact match: the status element
                # also contains the tier/Default badges, so the default card
                # reads "OK • Shared\nDefault" (page object `CARD_STATUS_SELECTOR`).
                expect(providers_page.card_status(display_name)).to_contain_text("OK")

        with allure.step(f"Step 4 — The Default {section_label} model selector shows a non-empty value"):
            expect(combobox).to_be_visible()
            expect(combobox).to_have_attribute("role", "combobox")
            # Not merely "non-empty": equal to the default the product's own
            # response reports. A stale or wrong label is also non-empty.
            expect(combobox).to_have_text(default_label)

        with allure.step("Step 5 — Clicking the selector drops down the section's available models"):
            combobox.click()
            expect(providers_page.open_select_options).to_have_count(total)
            for item in items:
                expect(providers_page.select_option(_option_value(item))).to_be_visible()
            expect(providers_page.select_option(default_value)).to_have_attribute("aria-selected", "true")
            # Read-only: dismiss without selecting, so the project's default is
            # untouched and the next parameterized row starts from a clean
            # portal (MUI allows only one open listbox at a time).
            providers_page.close_open_dropdown()

        with allure.step("Axis 2 — No console errors across the flow"):
            # Known defect: #1971 — the project-id-less `toolkitTypes` 404 the
            # project switch above triggers. URL-keyed and opt-in; nothing else
            # is filtered.
            unexpected = exclude_known_defect_urls(console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL)
            assert not unexpected, f"Unexpected console errors: {unexpected}"
