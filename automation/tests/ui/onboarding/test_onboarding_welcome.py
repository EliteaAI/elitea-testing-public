"""Tests for the Onboarding Welcome page — ELITEA-2231.

Verifies the first-login Welcome UI contract: when the backend returns
personal_project_id: null for the authenticated user, the app navigates
from root to /onboarding and renders the Welcome screen with the correct
elements and no sidebar navigation.

Coverage boundary: this test verifies the Welcome UI rendering when Redux
state carries personal_project_id: null.  It does NOT verify that the backend
genuinely returns personal_project_id: null for a brand-new user. That is a
separate API-level case.

Mechanism: Playwright page.route() intercepts GET /social/author/, fetches the
genuine backend response, and re-fulfills it with personal_project_id: null
(all other fields byte-identical). This is a declared improvisation — route
interception to establish an auth/onboarding precondition is a new application
of a sanctioned mechanism (generate_entity_modal_page_base.py:100-141).
Ruled by the test-automation lead in batch onboarding-w1 DECISIONS.md § D3.

Usage::

    cd automation
    HEADLESS=true ../.venv/bin/pytest tests/ui/onboarding/test_onboarding_welcome.py -v
"""

import allure
import pytest
from pages.onboarding_page import OnboardingPage

pytestmark = [
    pytest.mark.p2,
    pytest.mark.onboarding,
    pytest.mark.regression,
    pytest.mark.ui,
    pytest.mark.new,
]

# Expected text constants (source: Welcome.jsx — &apos; renders as U+0027,
# — is U+2014 em dash in source, JSX whitespace between lines collapses to space)
_EXPECTED_TITLE = "Welcome to Elitea!"
_EXPECTED_BODY_TEXT = (
    "We're setting up your personal workspace — it'll be ready in about 5 minutes. "
    "While we work our magic, take a quick tour through our onboarding slides!"
)
_EXPECTED_SECONDARY_TEXT = "Ready to explore Elitea's smart tools and tips?"
_EXPECTED_BUTTON_LABEL = "Sure, let's go!"


class TestOnboardingWelcomePage:
    """Onboarding Welcome page — first-login state (ELITEA-2231)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/onboarding/ELITEA-2231_onboarding-welcome-to-elitea-page-is-displayed-on-first-logi.md",
        "onetest-ai Test Case link",
    )
    def test_welcome_page_displayed_on_first_login(self, page):
        """Welcome page is displayed on first login with 'Sure, let's go!' button
        and no project loading yet.

        Verifies ELITEA-2231: all 9 case steps against the Welcome UI when
        personal_project_id is null in Redux state.

        DECLARED IMPROVISATION: route interception (page.route) to establish a
        first-login precondition is a new application of a sanctioned mechanism
        (generate_entity_modal_page_base.py:100-141). Prior uses control timing
        or force error states. This use establishes an auth/onboarding precondition.
        Ruled by the test-automation lead in batch onboarding-w1 DECISIONS.md § D3.

        COVERAGE BOUNDARY: this test does NOT verify that the backend genuinely
        returns personal_project_id: null for a brand-new user. That is a separate
        API-level case. The assertion scope is the Welcome UI rendering when Redux
        state carries personal_project_id: null.
        """
        onboarding_page = OnboardingPage(page)
        captured: dict = {}
        console_errors: list = []

        page.on(
            "console",
            lambda msg: console_errors.append(f"{msg.type}: {msg.text}")
            if msg.type == "error"
            else None,
        )

        with allure.step("Precondition — install fresh-user route mock before first navigation"):
            # Must be called before navigate() so the very first authorDetails
            # call from ProtectedRoutes.jsx is already intercepted.
            captured = onboarding_page.mock_fresh_user_state()

        try:
            with allure.step(
                "Step 1 — Navigate from app root; product routes to /onboarding"
            ):
                # Navigate to the app ROOT, not directly to /onboarding.
                # The product's own redirect (IndexRoute.jsx:15) is case step 1 —
                # navigating straight to /onboarding bypasses the gate under test.
                onboarding_page.navigate("/")
                page.wait_for_url("**/onboarding", timeout=15000)
                assert "/onboarding" in page.url, (
                    f"Expected URL to contain '/onboarding' after root navigation "
                    f"with fresh-user mock active; got: {page.url}"
                )
                # sessionStorage must be clean: no prior button click in this context
                onboarding_state = page.evaluate("() => sessionStorage.getItem('onboarding_state')")
                assert onboarding_state is None, (
                    f"sessionStorage.onboarding_state must be null at the start of "
                    f"the Welcome state; got: {onboarding_state!r}"
                )

            with allure.step(
                "Step 2 — Full-screen welcome page with ELITEA logo at top centre"
            ):
                onboarding_page.page_container.wait_for(state="visible", timeout=10000)
                assert onboarding_page.page_container.is_visible(), (
                    "Full-screen page container (onboarding-page-container) should be visible"
                )
                onboarding_page.page_logo.wait_for(state="visible", timeout=10000)
                assert onboarding_page.page_logo.is_visible(), (
                    "ELITEA brand wordmark SVG container (onboarding-page-logo) "
                    "should be visible at top centre"
                )
                onboarding_page.welcome_card.wait_for(state="visible", timeout=10000)
                assert onboarding_page.welcome_card.is_visible(), (
                    "Welcome card (onboarding-welcome-card) should be visible"
                )
                # Welcome illustration is part of the full-page layout (Axis 2)
                onboarding_page.welcome_illustration.wait_for(state="visible", timeout=10000)
                assert onboarding_page.welcome_illustration.is_visible(), (
                    "Welcome illustration image (onboarding-welcome-illustration, "
                    "chat-welcome.png) should be visible inside the card"
                )

            with allure.step("Step 3 — Title 'Welcome to Elitea!' is displayed"):
                onboarding_page.welcome_title.wait_for(state="visible", timeout=10000)
                assert onboarding_page.welcome_title.is_visible(), (
                    "Welcome title (onboarding-welcome-title) should be visible"
                )
                actual_title = onboarding_page.welcome_title.inner_text()
                assert actual_title == _EXPECTED_TITLE, (
                    f"Title text mismatch.\nExpected: {_EXPECTED_TITLE!r}\nGot: {actual_title!r}"
                )

            with allure.step(
                "Step 4 — Card greeting 'Hello, [Username]!' with real user name from intercepted response"
            ):
                assert "user" in captured and captured["user"], (
                    "User dict must be populated from the intercepted /social/author/ "
                    "response before asserting the greeting. Mock may not have fired — "
                    "check that AUTHOR_DETAILS_ROUTE matches the actual endpoint."
                )
                user_name = captured["user"].get("name") or captured["user"].get("email", "")
                assert user_name, (
                    "User name or email must be non-empty in the intercepted response"
                )
                expected_greeting = f"Hello, {user_name}!"
                onboarding_page.welcome_greeting.wait_for(state="visible", timeout=10000)
                actual_greeting = onboarding_page.welcome_greeting.inner_text()
                assert actual_greeting == expected_greeting, (
                    f"Greeting mismatch.\nExpected: {expected_greeting!r}\nGot: {actual_greeting!r}"
                )

            with allure.step("Step 5 — Card body text: workspace setup copy"):
                onboarding_page.welcome_body_text.wait_for(state="visible", timeout=10000)
                actual_body = onboarding_page.welcome_body_text.inner_text()
                assert actual_body == _EXPECTED_BODY_TEXT, (
                    f"Body text mismatch.\nExpected: {_EXPECTED_BODY_TEXT!r}\nGot: {actual_body!r}"
                )

            with allure.step(
                "Step 6 — Secondary text: 'Ready to explore Elitea's smart tools and tips?'"
            ):
                onboarding_page.welcome_secondary_text.wait_for(state="visible", timeout=10000)
                actual_secondary = onboarding_page.welcome_secondary_text.inner_text()
                assert actual_secondary == _EXPECTED_SECONDARY_TEXT, (
                    f"Secondary text mismatch.\n"
                    f"Expected: {_EXPECTED_SECONDARY_TEXT!r}\nGot: {actual_secondary!r}"
                )

            with allure.step(
                "Step 7 — 'Sure, let's go!' button is visible (NOT clicked — belongs to ELITEA-2232)"
            ):
                onboarding_page.welcome_get_started_button.wait_for(state="visible", timeout=10000)
                assert onboarding_page.welcome_get_started_button.is_visible(), (
                    "'Sure, let's go!' button (onboarding-welcome-get-started-button) "
                    "should be visible on the Welcome screen"
                )
                actual_label = onboarding_page.welcome_get_started_button.inner_text()
                assert actual_label == _EXPECTED_BUTTON_LABEL, (
                    f"Button label mismatch.\n"
                    f"Expected: {_EXPECTED_BUTTON_LABEL!r}\nGot: {actual_label!r}"
                )

            with allure.step(
                "Step 8 — No sidebar navigation and no project dropdown at this stage"
            ):
                # sidebar-toggle and project-selector-trigger are on-main ✓
                # (SidebarBody.jsx:221, SidebarProjectSelect.jsx:94).
                # MainSidebar.jsx:42 returns null when
                # isOnboardingPage && !user.personal_project_id.
                assert onboarding_page.sidebar_toggle.count() == 0, (
                    "sidebar-toggle must be absent on the Welcome screen; "
                    "MainSidebar.jsx returns null when "
                    "isOnboardingPage && !user.personal_project_id"
                )
                assert onboarding_page.project_selector_trigger.count() == 0, (
                    "project-selector-trigger must be absent on the Welcome screen "
                    "(sidebar is not rendered, so the project dropdown is also absent)"
                )

            with allure.step(
                "Step 9 — Personal/private project NOT yet loading; provisioning has not begun"
            ):
                # sessionStorage must still be clean (no button click has occurred)
                onboarding_state = page.evaluate("() => sessionStorage.getItem('onboarding_state')")
                assert onboarding_state is None, (
                    f"sessionStorage.onboarding_state must be null at the Welcome state "
                    f"(no 'Sure, let's go!' click has occurred); got: {onboarding_state!r}"
                )
                # Progress footer must be absent: Onboarding.jsx:182 renders it only
                # when showTour && !thePrivateProjectIsReady (i.e. after button click).
                # This also confirms 'Configuring Personal project...' text is absent,
                # since that text lives inside this footer element.
                assert onboarding_page.progress_footer.count() == 0, (
                    "onboarding-progress-footer must be absent at the Welcome state "
                    "(Onboarding.jsx:182 — footer is rendered only when "
                    "showTour && !thePrivateProjectIsReady, i.e. after button click). "
                    "This also confirms 'Configuring Personal project...' text is absent."
                )


            with allure.step("Axis 2 — No console errors on Welcome page"):
                assert not console_errors, (
                    f"No console errors expected on the Welcome page; got: {console_errors}"
                )

        finally:
            # Teardown — explicit unroute (context also auto-cleans at close)
            onboarding_page.clear_author_details_mock()
