"""UI test — Settings → AI Providers shows a per-section loading state while
configurations load, then replaces it with real content.

Read-only verification against the logged-in user's existing project
configuration data (`.agents/testing.md` § Test data strategy). Nothing is
created, modified, or deleted; the case observes a transient render state.

Test case: ELITEA-2251
AFS: test-specs/settings-ai-providers/l1_settings-sections-loading-state_ELITEA-2251.md

Timing control, NOT substitution (`.agents/testing.md` § Fidelity policy —
"Delaying a real response via `page.route()` so a transient state becomes
observable leaves the product as the producer of every asserted value"): this
test registers a `page.route()` handler on the combined configurations request
(`**/api/v2/configurations/configurations/**`) that HOLDS the real request open
until the loading state has been observed, then `route.continue_()`s it. The
request is the product's own, the response is the DEV backend's own, and every
asserted value — the `Loading...` placeholders, the section accordions, the
model selector — is rendered by the app from that real response. Nothing is
fabricated and nothing is `fulfill()`ed. The TMS case itself asks for this
("on a slow or throttled connection"), so the delay is the case's own
precondition rather than a workaround.

Why hold-and-release rather than a fixed `time.sleep()` inside the handler
(the AFS's original shape, amended in this PR): Playwright's sync API runs
route handlers on the same OS thread as the test body, so a sleeping handler
freezes the test body too — it would resume at the same instant the response
lands, racing the very re-render it is trying to observe. Holding the route and
releasing it explicitly, after the loading assertions have run, makes the
window deterministic instead of timing-dependent, and keeps the delay bounded
by the test's own progress rather than by a guessed constant.

Case-identity note (same drift as ELITEA-2392, already filed as clarification
EliteaAI/elitea-testing-public#1250): the TMS case says "Settings → AI
Configuration"; no such page exists. The sections it describes live on
"AI Providers" (`/settings/ai-providers`), which this test targets.

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - p1: high priority (per AFS metadata: l1 — case priority `high`)
    - regression
"""

import logging
import time

import allure
import pytest
from config import settings
from pages.ai_providers_page import AI_PROVIDERS_PATH, AIProvidersPage
from playwright.sync_api import Route, expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p1, pytest.mark.regression]

UI_ELEMENT_TIMEOUT = 10_000

# The combined card-listing call (`useMultiSectionConfigurations`) — the one
# request whose in-flight state drives every section's `isLoading` branch.
CONFIGURATIONS_ROUTE_GLOB = "**/api/v2/configurations/configurations/**"

# One `ConfigurationSection` per call site in `ConfigurationsPanel.jsx`. All 7
# render their loading placeholder, including the two (Vector Storage, AI
# Credentials) that turn out empty and hide themselves afterwards — the
# hide-when-empty check happens after the loading branch.
EXPECTED_LOADING_PLACEHOLDERS = 7

# Bounded budget for "the page does not remain in a permanent loading state":
# once the real response is released, content must appear within this window
# (live measurement: ~1 s). Asserting the timeout IS this step's content.
TERMINATION_BUDGET_MS = 15_000


class TestAIProvidersSectionsLoadingState:
    """ELITEA-2251 — Settings sections show a loading state while data is fetched."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2251_settings-sections-loading-state.md",
        "onetest-ai Test Case link",
    )
    def test_ai_providers_sections_loading_state(self, page):
        """With the real configurations response held open, every section renders
        a `Loading...` placeholder (7 of them) beneath an already-rendered page
        header and with zero configuration cards; once the real response is
        released, the placeholders vanish, the populated sections and the LLMs
        default-model selector render within a bounded budget, and no console
        errors are logged."""
        ai_providers_page = AIProvidersPage(page)
        console_errors = collect_console_errors(page)
        held_routes: list[Route] = []

        def _hold_configurations_request(route: Route) -> None:
            """Hold the product's own configurations request open (see module
            docstring): the request is neither answered nor altered here, only
            deferred until the test releases it with `route.continue_()`."""
            held_routes.append(route)

        try:
            with allure.step(
                "Step 1 — Arm the timing control: hold the real configurations "
                "request open before the navigation that triggers it"
            ):
                page.route(CONFIGURATIONS_ROUTE_GLOB, _hold_configurations_request)

            with allure.step(
                "Step 2 — Navigate to Settings -> AI Providers; the page shell "
                "renders before the configurations arrive"
            ):
                # NOT `AIProvidersPage.navigate()`: `BasePage.navigate()`
                # waits for `networkidle`, which can never be reached while the
                # configurations request is deliberately held open.
                page.goto(f"{settings.app_base_url}{AI_PROVIDERS_PATH}", wait_until="domcontentloaded")
                expect(ai_providers_page.page_title).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 3 — Verify the loading indicator is shown while configurations "
                "are loading: one placeholder per section, no configuration cards, "
                "no section accordions yet"
            ):
                expect(ai_providers_page.llms_section_loading).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                expect(ai_providers_page.section_loading_placeholders()).to_have_count(
                    EXPECTED_LOADING_PLACEHOLDERS, timeout=UI_ELEMENT_TIMEOUT
                )
                # The loading branch replaces the whole section: no accordion,
                # no cards. A regression that renders an empty accordion (or
                # blanks the page entirely) fails here rather than passing on
                # "the placeholder was visible".
                expect(ai_providers_page.llms_section_header).to_have_count(0)
                card_count_while_loading = ai_providers_page.get_configuration_card_count()
                assert card_count_while_loading == 0, (
                    f"Expected zero configuration cards while configurations are still "
                    f"loading, got {card_count_while_loading}"
                )
                # Axis 2 — the page shell stays rendered during loading.
                expect(ai_providers_page.page_title).to_be_visible()

            with allure.step(
                "Step 4 — Release the real response; verify the loading indicator "
                "disappears and is replaced by real content (not merely removed)"
            ):
                assert held_routes, (
                    "Expected the configurations request to have been intercepted; "
                    "none was — the route handler never fired"
                )
                released_at = time.monotonic()
                for route in held_routes:
                    route.continue_()
                held_routes.clear()

                expect(ai_providers_page.section_loading_placeholders()).to_have_count(
                    0, timeout=TERMINATION_BUDGET_MS
                )
                expect(ai_providers_page.llms_section_header).to_be_visible(timeout=TERMINATION_BUDGET_MS)
                expect(ai_providers_page.llms_default_selector_combobox).to_be_visible(
                    timeout=TERMINATION_BUDGET_MS
                )

            with allure.step(
                "Step 5 — Verify the page does not remain in a permanent loading "
                "state: every populated section renders within the bounded budget"
            ):
                for label, header in ai_providers_page.populated_section_headers():
                    expect(header, f"{label!r} section header").to_be_visible(timeout=TERMINATION_BUDGET_MS)
                expect(ai_providers_page.section_loading_placeholders()).to_have_count(0)
                card_count_after_load = ai_providers_page.get_configuration_card_count()
                assert card_count_after_load > 0, (
                    f"Expected at least one configuration card once loading finished, "
                    f"got {card_count_after_load}"
                )
                elapsed_s = time.monotonic() - released_at
                logger.info("Content rendered %.2fs after the real response was released", elapsed_s)

            with allure.step("Step 6 — Verify no unexpected console errors across the whole flow"):
                assert not console_errors, f"Unexpected console errors: {console_errors}"
        finally:
            # Never leave the product's request hanging, and never let the
            # timing control leak into another test.
            for route in held_routes:
                route.continue_()
            page.unroute(CONFIGURATIONS_ROUTE_GLOB, _hold_configurations_request)
