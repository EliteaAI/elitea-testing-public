"""UI test -- the "OpenAI Template" tab of the AI Configurations panel loads a
populated code template, and switching back restores the Basic metadata fields.

Read-only round-trip against whichever project the browser session has selected
(`.agents/testing.md` § Test data strategy). Nothing is created, modified or
deleted; no request is intercepted or faked -- the code template asserted here
is the one the product generated from its own configuration
(`.agents/testing.md` § Fidelity policy). The template's `api_key` is the
literal placeholder `Your_Personal_Token`, so no secret is ever rendered.

Test case: ELITEA-2393
AFS: test-specs/settings-ai-configurations/l3_openai-template-tab-loads-code-template_ELITEA-2393.md

Case-text drift -- this test asserts the LIVE contract
--------------------------------------------------------
The TMS case says "Navigate to Settings → AI Configuration" and, in step 5,
"click back to the AI Configuration tab". Live there is **no page or tab of
that name**: the panel is the "AI Configurations" accordion on Settings →
General, and the tab the case means is labelled **"Basic"** -- its content is
the four environment metadata fields ("the integrations content"). Per the
reverse-masking guard this spec asserts the live names and the live round-trip.
Filed as clarification EliteaAI/elitea-testing-public#1981.

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - p3: priority (per AFS metadata: l3 -- case priority `medium`)
    - regression
"""

import logging

import allure
import pytest
from pages.settings_ai_configuration_page import SettingsAIConfigurationPage
from playwright.sync_api import expect
from utils.console_errors import (
    TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL,
    collect_console_errors,
    exclude_known_defect_urls,
)

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p3, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 15_000

#: Floor on the rendered template length. 485 characters / 23 lines were
#: observed live, so this is generous — it exists to fail on an empty or
#: single-line editor, not to pin the template's exact size.
MIN_TEMPLATE_LENGTH = 100

#: Fragments that make this the OpenAI code template specifically, rather than
#: arbitrary non-empty text. The language selector defaults to Python and the
#: case never changes it.
EXPECTED_TEMPLATE_FRAGMENTS = ("from openai import OpenAI", "client = OpenAI(")


class TestAIConfigurationOpenAITemplateTab:
    """ELITEA-2393 -- OpenAI Template tab loads code template content."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ai-configuration/ELITEA-2393_openai-template-tab-loads-code-template-content.md",
        "onetest-ai Test Case link",
    )
    def test_openai_template_tab_loads_code_template(self, page):
        """From the default Basic tab, clicking "OpenAI Template" activates it
        exclusively, unmounts the metadata fields and renders a populated,
        OpenAI-specific Python template built from this project's own
        `OpenAI-BaseURL`; clicking back to "Basic" unmounts the editor and
        restores the four metadata fields with identical values, with no
        console errors across the round-trip."""
        ai_config = SettingsAIConfigurationPage(page)
        console_errors = collect_console_errors(page)

        with allure.step(
            "Step 1 — Open Settings → General and locate the AI Configurations panel (case step 1)"
        ):
            ai_config.navigate_to_general(timeout=UI_ELEMENT_TIMEOUT)
            expect(ai_config.ai_configurations_panel).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(ai_config.accordion_summary).to_have_attribute("aria-expanded", "true")
            # Starting state — makes step 5's "the content returns" a real
            # round-trip rather than a no-op.
            expect(ai_config.tab_basic_button).to_have_attribute("aria-pressed", "true")
            expect(ai_config.openai_base_url_value).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            fields_before = ai_config.basic_field_texts()

        with allure.step('Step 2 — Click the "OpenAI Template" tab (case step 2)'):
            # A tab switch fires no request — `select_openai_template_tab`
            # waits on the toggle's own `aria-pressed`, never on the network.
            ai_config.select_openai_template_tab(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 3 — Verify the tab becomes active, exclusively (case step 3)"):
            expect(ai_config.tab_openai_template_button).to_have_attribute("aria-pressed", "true")
            expect(ai_config.tab_basic_button).to_have_attribute("aria-pressed", "false")
            # The two panels are mutually exclusive renders; asserting only the
            # newly-shown one would pass if both rendered at once.
            expect(ai_config.openai_base_url_value).to_have_count(0)

        with allure.step(
            "Step 4 — Verify the content area shows a non-empty code template (case step 4)"
        ):
            expect(ai_config.code_preview_editor).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            template = ai_config.code_template_text()
            assert len(template) >= MIN_TEMPLATE_LENGTH, (
                f"Expected a populated code template (>= {MIN_TEMPLATE_LENGTH} chars), "
                f"got {len(template)}: {template!r}"
            )
            for fragment in EXPECTED_TEMPLATE_FRAGMENTS:
                assert fragment in template, (
                    f"Expected the OpenAI code template to contain {fragment!r}; got: {template!r}"
                )
            # Generated from THIS project's configuration, not a static blob —
            # the base URL the Basic tab showed must appear in the template.
            expected_base_url = f'base_url="{fields_before["openai_base_url"]}'
            assert expected_base_url in template, (
                f"Expected the template to embed the project's own base URL "
                f"({expected_base_url!r}); got: {template!r}"
            )
            # The "no default LLM model" branch also renders non-empty text
            # inside the panel — absence proves the editor is what rendered.
            expect(ai_config.code_preview_empty).to_have_count(0)

        with allure.step(
            'Step 5 — Click back to the "Basic" tab and verify the metadata content returns '
            "(case step 5 / Expected Final State)"
        ):
            ai_config.select_basic_tab(timeout=UI_ELEMENT_TIMEOUT)
            expect(ai_config.tab_basic_button).to_have_attribute("aria-pressed", "true")
            expect(ai_config.tab_openai_template_button).to_have_attribute("aria-pressed", "false")
            expect(ai_config.code_preview_editor).to_have_count(0)

            for field, label in SettingsAIConfigurationPage.BASIC_FIELD_LABELS.items():
                expect(ai_config.basic_field_value(field), f"{label} value node").to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
            fields_after = ai_config.basic_field_texts()
            assert fields_after == fields_before, (
                '"The integrations content returns" means the SAME content — '
                f"before: {fields_before}, after: {fields_after}"
            )

            # Known defect: #1971 — the project-id-less `toolkits/prompt_lib/`
            # 404 fires on project-scoped navigation. URL-keyed and opt-in;
            # never a status-code filter.
            unexpected = exclude_known_defect_urls(console_errors, TOOLKIT_TYPES_MISSING_PROJECT_ID_404_URL)
            assert not unexpected, f"Unexpected console errors: {unexpected}"
