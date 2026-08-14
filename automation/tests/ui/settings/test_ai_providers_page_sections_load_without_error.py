"""UI test — AI Providers page loads all integration sections without error.

Read-only verification against the logged-in user's existing project
configuration data (`.agents/testing.md` § Test data strategy — prefer
read-only assertions on existing data when the observable doesn't require
fresh state). This case never creates, modifies, or deletes a configuration.

Test case: ELITEA-2392
AFS: test-specs/settings-ai-providers/l3_ai-providers-page-sections-load-without-error_ELITEA-2392.md

Case-identity note (full write-up in the AFS): the TMS case is titled "AI
Configuration page loads all integration sections without error" and directs
the tester to "Settings -> AI Configuration" — no such page/nav-item exists
in the live product. The described sections (LLM Models, Embedding Models,
Vector Storage, Image Generation, ASR, TTS, AI credentials) live on the
sidebar item labelled "AI Providers" (`/settings/ai-providers`), which this
test targets instead. Filed as a case-text clarification:
EliteaAI/elitea-testing-public#1250. Case step 12 / "Expected Final State"
("AI Configuration"/"OpenAI Template" tabs present at top) is NOT automated —
those tabs belong to a different page entirely (Settings -> General ->
"AI Configurations" accordion, labelled "Basic"/"OpenAI Template" there, not
"AI Configuration"/"OpenAI Template") — see AFS Coverage Map row 12.

Vector Storage and AI Credentials currently have zero configured items in
the shared `${TEST_USER}` project — both correctly render nothing at all
(`ConfigurationSection.jsx` returns `null` for an empty section) rather than
an empty-state placeholder. This is verified as correct empty-state
behaviour (API 200 + zero items), not treated as a defect or a load failure,
per the AFS's Reverse-masking guard.

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - p2: medium priority (per AFS metadata: l3 — this suite's l3 maps to p2,
      matching the sibling settings-personal-tokens/settings-secrets tests)
    - regression
"""

import logging

import allure
import pytest
from pages.ai_providers_page import AIProvidersPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
CONFIGURATIONS_URL_SUBSTRING = "/configurations/"


class TestAIProvidersPageSections:
    """ELITEA-2392 — AI Providers page loads all integration sections without error."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings-ai-providers/ELITEA-2392_ai-providers-page-sections-load-without-error.md",
        "onetest-ai Test Case link",
    )
    def test_ai_providers_page_sections_load_without_error(self, page):
        """Every populated section (LLMs/Embedding/Image Gen/ASR/TTS) renders with
        its default selector(s) and >=1 configuration card, in the expected
        order; the two zero-config sections (Vector Storage/AI Credentials)
        are correctly absent, not silently broken; zero console errors, zero
        non-2xx across every configurations endpoint."""
        ai_providers_page = AIProvidersPage(page)
        console_errors = ai_providers_page.capture_console_errors()
        configurations_requests = ai_providers_page.capture_requests_matching(CONFIGURATIONS_URL_SUBSTRING)

        try:
            with allure.step(
                "Step 1 — Navigate to Settings -> AI Providers, capturing the "
                "vectorstorage-scoped models response body for the zero-items proof"
            ):
                vectorstorage_response = ai_providers_page.navigate_and_capture_vectorstorage_response()
                assert vectorstorage_response.status == 200, (
                    f"Expected the vectorstorage-scoped models request to return 200, "
                    f"got {vectorstorage_response.status}"
                )
                vectorstorage_body = vectorstorage_response.json()
                vectorstorage_item_count = len(vectorstorage_body.get("items", []))

            with allure.step('Step 2 — Verify the page header reads "AI Providers"'):
                assert ai_providers_page.page_title.text_content() == "AI Providers", (
                    f"Expected page header text 'AI Providers', got "
                    f"{ai_providers_page.page_title.text_content()!r}"
                )

            with allure.step(
                "Step 3 — Verify the LLMs, Embedding Models, Image Generation, ASR, "
                "and TTS section headers are present, in that relative top-to-bottom order "
                "(Vector Storage and AI Credentials are not rendered for this project — step 6/10)"
            ):
                rendered_headers = [
                    ("LLMs", ai_providers_page.llms_section_header),
                    ("Embedding Models", ai_providers_page.embedding_models_section_header),
                    ("Image Generation", ai_providers_page.image_generation_section_header),
                    ("Speech Recognition (ASR)", ai_providers_page.asr_section_header),
                    ("Text to Speech (TTS)", ai_providers_page.tts_section_header),
                ]
                positions = []
                for name, header in rendered_headers:
                    expect(header).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                    box = header.bounding_box()
                    assert box is not None, f"Expected a bounding box for the {name!r} section header"
                    positions.append((name, box["y"]))
                sorted_by_y = sorted(positions, key=lambda item: item[1])
                assert positions == sorted_by_y, (
                    f"Expected section header top-to-bottom order "
                    f"{[p[0] for p in positions]}, but vertical position sorts them as "
                    f"{[p[0] for p in sorted_by_y]}"
                )

            with allure.step(
                "Step 4 — Verify the LLMs section (auto-expanded by default) shows "
                "Default/High-tier/Low-tier model selectors and at least one "
                "configuration card"
            ):
                expect(ai_providers_page.llms_section_header).to_have_attribute(
                    "aria-expanded", "true", timeout=UI_ELEMENT_TIMEOUT
                )
                expect(ai_providers_page.llms_default_selector).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(ai_providers_page.llms_high_tier_selector).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(ai_providers_page.llms_low_tier_selector).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                llms_card_count = ai_providers_page.get_configuration_card_count()
                assert llms_card_count > 0, (
                    f"Expected at least 1 configuration card under LLMs "
                    f"(already expanded), got {llms_card_count}"
                )

            with allure.step(
                "Step 5 — Expand Embedding Models; verify it shows a Default "
                "selector and at least one configuration card"
            ):
                count_before = ai_providers_page.get_configuration_card_count()
                ai_providers_page.expand_section(ai_providers_page.embedding_models_section_header)
                expect(ai_providers_page.embedding_models_default_selector).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                count_after = ai_providers_page.get_configuration_card_count()
                assert count_after > count_before, (
                    f"Expected the visible configuration card count to increase "
                    f"after expanding Embedding Models, got {count_before} -> {count_after}"
                )

            with allure.step(
                'Step 6 — Verify no "Vector Storage" accordion header is rendered, '
                "AND the underlying section=vectorstorage request returned 200 with "
                "zero items (the absence is a correct empty-state hide, not a "
                "silent load failure)"
            ):
                expect(ai_providers_page.vector_storage_section_header).to_have_count(0)
                assert vectorstorage_item_count == 0, (
                    f"Expected the vectorstorage-scoped models response to report "
                    f"zero items for this project, got {vectorstorage_item_count}"
                )

            with allure.step(
                "Step 7 — Expand Image Generation; verify it shows a Default "
                "selector and at least one configuration card"
            ):
                count_before = ai_providers_page.get_configuration_card_count()
                ai_providers_page.expand_section(ai_providers_page.image_generation_section_header)
                expect(ai_providers_page.image_generation_default_selector).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                count_after = ai_providers_page.get_configuration_card_count()
                assert count_after > count_before, (
                    f"Expected the visible configuration card count to increase "
                    f"after expanding Image Generation, got {count_before} -> {count_after}"
                )

            with allure.step(
                'Step 8 — Expand Speech Recognition (ASR); verify it shows a '
                "Default selector and at least one configuration card"
            ):
                count_before = ai_providers_page.get_configuration_card_count()
                ai_providers_page.expand_section(ai_providers_page.asr_section_header)
                expect(ai_providers_page.asr_default_selector).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                count_after = ai_providers_page.get_configuration_card_count()
                assert count_after > count_before, (
                    f"Expected the visible configuration card count to increase "
                    f"after expanding Speech Recognition (ASR), got {count_before} -> {count_after}"
                )

            with allure.step(
                'Step 9 — Expand Text to Speech (TTS); verify it shows a Default '
                "selector and at least one configuration card"
            ):
                count_before = ai_providers_page.get_configuration_card_count()
                ai_providers_page.expand_section(ai_providers_page.tts_section_header)
                expect(ai_providers_page.tts_default_selector).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                count_after = ai_providers_page.get_configuration_card_count()
                assert count_after > count_before, (
                    f"Expected the visible configuration card count to increase "
                    f"after expanding Text to Speech (TTS), got {count_before} -> {count_after}"
                )

            with allure.step(
                'Step 10 — Verify no "AI Credentials" accordion header is rendered '
                "(the combined configurations request's 200 status is asserted "
                "below, across every configurations endpoint fired during this test)"
            ):
                expect(ai_providers_page.ai_credentials_section_header).to_have_count(0)

            # Step 11 is decomposed across steps 4/5/7/8/9 above (each
            # populated section's own >=1-card check) — no separate block.

            with allure.step(
                "Final check — zero console errors and zero non-2xx responses "
                "across every /configurations/ endpoint captured during this test"
            ):
                resolved_requests = [r for r in configurations_requests if r["status"] is not None]
                assert resolved_requests, (
                    "Expected at least one /configurations/ response to have been captured"
                )
                non_2xx = [r for r in resolved_requests if not (200 <= r["status"] < 300)]
                assert not non_2xx, f"Unexpected non-2xx configurations responses: {non_2xx}"
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()
            configurations_requests.stop()
