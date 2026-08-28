"""UI test -- every collapsible settings section of the personalization family
collapses and expands from its own header, hiding and revealing its content.

Read-only: the accordions are local UI state (MUI `Accordion`), nothing is
seeded, written or cleaned up, and no autosave request fires on a header click.

Test case: ELITEA-2372
AFS: test-specs/settings-user-profile/l3_settings_sections_collapse_expand_ELITEA-2372.md

Case-text drift -- this test asserts the LIVE contract
--------------------------------------------------------
The case says "Navigate to Personalization" and then repeats the collapse /
expand cycle over five sections *on that one page*. There is no such page:
`/settings/personalization` renders the app's global "Page not found" view. The
sections live on two real routes -- `GENERAL`, `VOICE PERSONALIZATION` and
`SOUND NOTIFICATIONS` on `/settings/preferences`, `CONTEXT MANAGEMENT` (the
case's "DEFAULT CONTEXT MANAGEMENT") on `/settings/memory`. The fifth,
`LONG-TERM MEMORY`, renders nowhere at all: `MemoryLongTermMemory.jsx` exists
but its only import is commented out, so nothing in `src/` mounts it. That
repetition is therefore unsatisfiable and is the entire subject of its own case,
ELITEA-2380 (`blocked`); it is dispositioned in the AFS Coverage Map rather than
silently dropped.

Per the reverse-masking guard this spec asserts the live contract -- the four
sections that exist, on the routes they exist on. Clarification:
EliteaAI/elitea-testing-public#1960 (siblings #1238, #1772).

Collapsed does NOT mean unmounted
---------------------------------
MUI's `Collapse` keeps its children in the DOM and hides them via
`visibility: hidden`, so `not_to_be_visible()` is the correct assertion and
`to_have_count(0)` would be wrong here -- it belongs to the *other* hide
mechanism on this surface (Context Management's toggle conditionally unmounts
its numeric fields, which is why this spec probes that section's visibility
through the always-mounted `context-management-toggle`).

No substitutions: every asserted value is produced by the running app.

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - p3: low priority (per AFS metadata: l3 -- case priority `medium`)
    - regression
"""

import logging

import allure
import pytest
from config import settings
from pages.settings_personalization_page import (
    MEMORY_PATH,
    PREFERENCES_PATH,
    AccordionSection,
    SettingsPersonalizationPage,
)
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p3, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000

#: Known defect EliteaAI/elitea-testing-public#1771 -- `/settings/memory` logs a
#: React `disableUnderline` warning on every load, from `MemorySummarization`'s
#: `StyledInputEnhancer`. It is unrelated to accordion behaviour and pre-dates
#: this case. Filtered by its exact message fragment (never by status code or
#: route), so any OTHER console error on that route still fails this test.
KNOWN_DEFECT_1771_FRAGMENT = "disableUnderline"


def _unexpected(console_errors: list[str]) -> list[str]:
    """Console errors other than the known #1771 `disableUnderline` warning."""
    return [e for e in console_errors if KNOWN_DEFECT_1771_FRAGMENT not in e]


class TestSettingsSectionsCollapseExpand:
    """ELITEA-2372 -- all collapsible settings sections collapse and expand."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2372_all-collapsible-sections-can-be-collapsed-and-expanded.md",
        "onetest-ai Test Case link",
    )
    def test_settings_sections_collapse_expand(self, page):
        """Each of the four live collapsible settings sections starts expanded,
        collapses on a header click (`aria-expanded` flips to `false` and its
        content stops being visible), and expands again on a second click --
        across `/settings/preferences` and `/settings/memory`. Collapse state is
        local UI state and does not survive a reload. No console errors other
        than the known #1771 warning are logged."""
        personalization = SettingsPersonalizationPage(page)
        console_errors = collect_console_errors(page)

        with allure.step("Step 1 - Open Settings -> Preferences and verify all three sections start expanded"):
            personalization.open_settings_tab("preferences")
            expect(page).to_have_url(f"{settings.app_base_url}{PREFERENCES_PATH}")
            expect(personalization.nav_item("preferences")).to_have_attribute("data-active", "true")

            preferences_sections = personalization.preferences_sections()
            for section in preferences_sections:
                expect(section.wrapper).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                # Pins `BasicAccordion`'s `defaultExpanded = true` default, which
                # SOUND NOTIFICATIONS relies on without passing the prop -- the
                # collapse assertions below are meaningless without it.
                expect(section.header).to_have_attribute("aria-expanded", "true")
                expect(section.content).to_be_visible()

        for section in preferences_sections:
            self._assert_collapse_expand_cycle(personalization, section)

        with allure.step(
            "Step 6 - Repeat the cycle for CONTEXT MANAGEMENT on Settings -> Memory"
        ):
            personalization.go_to_settings_tab("memory")
            expect(page).to_have_url(f"{settings.app_base_url}{MEMORY_PATH}")
            context_management = personalization.context_management_accordion()
            expect(context_management.wrapper).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            expect(context_management.header).to_have_attribute("aria-expanded", "true")
            expect(context_management.content).to_be_visible()

        self._assert_collapse_expand_cycle(personalization, context_management)

        with allure.step(
            "Step 7 (beyond the case) - Verify collapse state is local UI state: "
            "a reload restores the section to expanded"
        ):
            personalization.toggle_section(context_management)
            expect(context_management.header).to_have_attribute("aria-expanded", "false")
            page.reload()
            expect(context_management.header).to_have_attribute(
                "aria-expanded", "true", timeout=UI_ELEMENT_TIMEOUT
            )
            expect(context_management.content).to_be_visible()

        with allure.step("Step 8 - Verify no unexpected console errors were logged"):
            # `/settings/memory` always logs the #1771 `disableUnderline`
            # warning; nothing else is tolerated. Known defect: #1771.
            assert not _unexpected(console_errors), (
                f"unexpected console errors: {_unexpected(console_errors)}"
            )

    @staticmethod
    def _assert_collapse_expand_cycle(
        personalization: SettingsPersonalizationPage, section: AccordionSection
    ) -> None:
        """Case steps 2-4 for one section: collapse, verify hidden, expand, verify visible."""
        with allure.step(f"Steps 2-4 - Collapse and re-expand the {section.name} section"):
            personalization.toggle_section(section)
            expect(section.header).to_have_attribute("aria-expanded", "false")
            # MUI `Collapse` keeps children MOUNTED and hides them via
            # `visibility: hidden` -- `not_to_be_visible()`, never
            # `to_have_count(0)` (see module docstring).
            expect(section.content).not_to_be_visible()

            personalization.toggle_section(section)
            expect(section.header).to_have_attribute("aria-expanded", "true")
            expect(section.content).to_be_visible()
