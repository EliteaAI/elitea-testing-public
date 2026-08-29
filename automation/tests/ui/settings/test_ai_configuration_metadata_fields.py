"""UI test -- Settings landing: the AI Configurations panel is open by default
and shows the four environment metadata fields with real, non-placeholder values.

Read-only inventory check against whichever project the browser session has
selected (`.agents/testing.md` § Test data strategy). Nothing is created,
modified, or deleted, and no request is intercepted or faked -- every asserted
value is produced by the product (`.agents/testing.md` § Fidelity policy).

Test case: ELITEA-2394
AFS: test-specs/settings-ai-configurations/l2_ai-configuration-environment-metadata-fields_ELITEA-2394.md

Case-text drift -- this test asserts the LIVE contract
--------------------------------------------------------
The TMS case says clicking Settings shows an "AI Configuration" page/tab
"selected and active by default". Live there is **no such nav item**: the
sidebar Settings button hardcodes `/settings/project-general` ("General"), and
the four fields the case enumerates live in the "AI Configurations" accordion
on that page -- expanded by default, with its "Basic" tab pre-selected. The
case's intent (land on Settings, the AI-configuration panel is showing, its
metadata fields are populated) is satisfied exactly; only the names are stale.
Per the reverse-masking guard this spec asserts the live equivalent. Same root
cause as clarification EliteaAI/elitea-testing-public#1772 (row 3); a new
occurrence was commented there rather than filed as a duplicate.

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - p2: priority (per AFS metadata: l2 -- case priority `high`)
    - regression
"""

import logging

import allure
import pytest
from config import settings
from pages.settings_ai_configuration_page import SettingsAIConfigurationPage
from pages.settings_drawer_page import SettingsDrawerPage
from playwright.sync_api import expect
from utils.console_errors import (
    TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL,
    collect_console_errors,
    exclude_known_defect_urls,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p2, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 15_000

GENERAL_TAB_ID = "project-general"

#: Rendered-blank values the case forbids ("undefined", blank). `Not configured`
#: is `AIConfiguration.jsx`'s own fallback for a missing `user.api_url` /
#: `projectId` -- the blank state rendered as words, so it must fail too.
FORBIDDEN_VALUES = {"", "undefined", "null", "nan", "not configured", "-", "n/a"}


class TestAIConfigurationMetadataFields:
    """ELITEA-2394 -- Settings landing shows correct environment metadata fields."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ai-configuration/ELITEA-2394_settings-landing-ai-configuration-page-shows-correct-environ.md",
        "onetest-ai Test Case link",
    )
    def test_ai_configuration_metadata_fields(self, page):
        """Clicking Settings lands on General with the AI Configurations
        accordion already expanded and its Basic tab pressed; all four
        environment metadata fields render beside their own labels with real
        values -- none blank, `undefined` or `Not configured`, no spinner left
        behind; `Project ID` equals the project id in the page's own
        `section=llm` request; `OpenAI-BaseURL` derives from `Server URL`; and
        no console errors are logged."""
        ai_config = SettingsAIConfigurationPage(page)
        drawer = SettingsDrawerPage(page)
        console_errors = collect_console_errors(page)

        with allure.step(
            "Step 1 — Navigate away from Settings, then open it from the sidebar (case steps 1-2)"
        ):
            models_response = ai_config.open_via_sidebar(timeout=UI_ELEMENT_TIMEOUT)
            expect(page).to_have_url(f"{settings.app_base_url}/settings/project-general")
            expect(drawer.nav_item(GENERAL_TAB_ID)).to_have_attribute("data-active", "true")
            # The product's own project id, read off the request the settings
            # page itself fired — the oracle for `Project ID` in step 4.
            expected_project_id = ai_config.project_id_from_models_url(models_response.url)
            assert models_response.status == 200, (
                f"Expected 200 from the page's own models request, got {models_response.status}"
            )
            logger.info("Settings page loaded for project %s", expected_project_id)

        with allure.step(
            "Step 2 — Verify the AI-configuration panel is showing and active by default (case step 3)"
        ):
            expect(ai_config.ai_configurations_panel).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            # Expanded without any user action — the live equivalent of the
            # case's "selected and active by default" (clarification #1772).
            expect(ai_config.accordion_summary).to_have_attribute("aria-expanded", "true")
            expect(ai_config.tab_basic_button).to_have_attribute("aria-pressed", "true")
            expect(ai_config.tab_openai_template_button).to_have_attribute("aria-pressed", "false")

        with allure.step(
            "Step 3 — Verify the four environment metadata fields render with their labels "
            "and non-empty values (case steps 4-8)"
        ):
            for field, label in SettingsAIConfigurationPage.BASIC_FIELD_LABELS.items():
                value = ai_config.basic_field_value(field)
                expect(value, f"{label} value node").to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                assert value.inner_text().strip(), f"Expected a non-empty value for {label}"
                # The label proves this testid is still the field the case
                # names, not just some populated node.
                expect(ai_config.ai_configurations_panel, f"{label} label").to_contain_text(label)

        with allure.step(
            'Step 4 — Verify no value is "undefined", blank or a permanent spinner, '
            "and that the values are the product's own (case step 9)"
        ):
            field_texts = ai_config.basic_field_texts()
            for field, label in SettingsAIConfigurationPage.BASIC_FIELD_LABELS.items():
                assert field_texts[field].lower() not in FORBIDDEN_VALUES, (
                    f"{label} rendered a blank/placeholder value: {field_texts[field]!r}"
                )
            # No permanent loading state left inside the panel — see
            # `panel_progress_indicators()` for the declared improvisation.
            expect(ai_config.panel_progress_indicators()).to_have_count(0)

            assert field_texts["project_id"] == expected_project_id, (
                "Project ID should equal the project the page's own section=llm request used — "
                f"panel showed {field_texts['project_id']!r}, request used {expected_project_id!r}"
            )
            # `AIConfiguration.jsx` computes OpenAI-BaseURL from Server URL;
            # asserting the relationship pins a real regression without
            # hardcoding an environment-specific host.
            expected_base_url = f"{field_texts['server_url'].replace('/api/v2', '')}/llm/v1"
            assert field_texts["openai_base_url"] == expected_base_url, (
                f"OpenAI-BaseURL should be {expected_base_url!r} (derived from Server URL "
                f"{field_texts['server_url']!r}), got {field_texts['openai_base_url']!r}"
            )

            # Known defect: #1971 — the project-id-less `toolkits/prompt_lib/`
            # 404 fires on project-scoped navigation like this one. URL-keyed
            # and opt-in; never a status-code filter.
            unexpected = exclude_known_defect_urls(console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL)
            assert not unexpected, f"Unexpected console errors: {unexpected}"
