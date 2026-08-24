"""UI test — the onboarding provisioning state after "Sure, let's go!".

TMS: ELITEA-2232
AFS: test-specs/onboarding/lmedium_onboarding_provisioning_after_get_started_ELITEA-2232.md

Clicking "Sure, let's go!" on the first-login Welcome card replaces it with the
onboarding tips card at slide 1 / 48, renders the "Configuring Personal
project..." progress footer, and starts a 5-second poll of
GET /api/v2/social/author/ that was not running before the click. No sidebar and
no project dropdown exist while that state is on screen. When the poll finally
sees a non-null personal_project_id, the footer unmounts and the sidebar appears
on /onboarding itself, with the entity menu and the Private project in the
project selector.

This is the only spec in the suite that asserts onboarding-progress-footer
PRESENT — the other three onboarding specs assert it absent.

SUBSTITUTIONS (both TRANSIT, declared per .agents/testing.md § Fidelity policy
and AFS § Fidelity Declaration):

  1. OnboardingPage.mock_fresh_user_state() forces personal_project_id to null
     on GET /social/author/ (every other field is the genuine backend response,
     fetched live via route.fetch()). It establishes the case's own stated
     first-login precondition, which no account in this environment is in.
     Sanctioned by the test-automation lead, batch onboarding-w1 DECISIONS § D3.
     Every observable asserted in steps 1-10 is rendered by the PRODUCT from that
     state — the card, the counter, the tip copy, the footer copy, the progress
     animation, the poll cadence, the absent sidebar.
  2. The mask is RELEASED mid-test (clear_author_details_mock) so the next poll
     receives the unmodified backend response. This is the "delay a real response
     so a transient state is observable" shape applied in reverse: the real
     ready-state is withheld for a few seconds, then delivered unaltered. Every
     value asserted in step 11 — the project name, the sidebar, the entity menu —
     comes from the genuine backend payload. DECLARED IMPROVISATION: D3 sanctioned
     INSTALLING this mock; releasing it mid-test to observe the completion
     transition is a new application of the same mechanism (AFS § Fidelity
     Declaration, flagged for the lead).

COVERAGE BOUNDARY: this spec verifies the UI contract of the provisioning state
and of the transition out of it. It does NOT verify that the backend actually
provisions a personal project for a brand-new account — that is an API/e2e
concern with a ~5-minute real wait and no available fresh account. The mock
authors exactly one field (personal_project_id: null) and no assertion reads it.

Usage::

    cd automation
    HEADLESS=true ../.venv/bin/pytest tests/ui/onboarding/test_onboarding_provisioning.py -v
"""

import re
import time

import allure
import pytest
from pages.onboarding_page import OnboardingPage
from playwright.sync_api import expect

pytestmark = [
    pytest.mark.p2,
    pytest.mark.onboarding,
    pytest.mark.regression,
    pytest.mark.ui,
    pytest.mark.new,
]

UI_ELEMENT_TIMEOUT = 10_000
READY_TRANSITION_TIMEOUT = 20_000

# Observation windows (see the comments at their use sites — these are NOT
# waits-for-a-condition; there is nothing to wait for, the assertion is that
# nothing happened / that a number moved).
QUIET_WINDOW_MS = 7_000
POLL_WINDOW_S = 12.0
PROGRESS_WINDOW_MS = 6_000

# Source of truth for the copy: EliteaUI
# src/[fsd]/features/onboarding/lib/constants/onboardingTips.constants.js
# (first entry; 48 entries total). The rendered text drops the markdown **
# around "Quick Action:".
_EXPECTED_TIP1_TITLE = "Tip 1: Welcome to ELITEA"
_EXPECTED_TIP1_DESCRIPTION = (
    "ELITEA is your AI-powered workspace where you create intelligent agents, "
    "automate workflows with pipelines, and chat with powerful AI models. "
    "Everything you need is organized in the left sidebar for easy access."
)
_EXPECTED_TIP1_QUICK_ACTION = (
    "Quick Action: Click the ELITEA logo (top-left) to explore all available menus."
)
_EXPECTED_SLIDE_COUNTER = "1 / 48"
_EXPECTED_STATUS_LABEL = "Configuring Personal project..."
_EXPECTED_ESTIMATED_TIME = "about 5 min"
_EXPECTED_PROJECT_LABEL = "Private"
_SIDEBAR_ANCHOR_ITEM = "chat"

# Onboarding.jsx:71-73 — progress starts at 5 and grows by 95/150 per second.
# The initial read happens inside the first one-second interval tick, so the
# value is at its baseline; the upper bound keeps the assertion meaningful
# without making it a stopwatch race.
_PROGRESS_START = 5
_PROGRESS_START_UPPER_BOUND = 12


class TestOnboardingProvisioning:
    """Onboarding provisioning state — tour + progress footer (ELITEA-2232)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/onboarding/"
        "ELITEA-2232_onboarding-clicking-sure-lets-go-triggers-project-provisioni.md",
        "onetest-ai Test Case link",
    )
    def test_get_started_starts_provisioning_poll_and_shows_tips_with_progress_footer(
        self, page
    ):
        """"Sure, let's go!" shows tips 1/48 + the configuring footer, starts the
        account-status poll, hides the sidebar, and hands over to the ready state."""
        onboarding_page = OnboardingPage(page)
        console_errors: list = []
        author_polls: list = []

        page.on(
            "console",
            lambda msg: console_errors.append(f"{msg.type}: {msg.text}")
            if msg.type == "error"
            else None,
        )
        # Count the account-status requests on the page's own request event — no
        # interception, so this observes the product's real network behaviour.
        page.on(
            "request",
            lambda request: author_polls.append(time.monotonic())
            if "/social/author/" in request.url
            else None,
        )

        with allure.step(
            "Precondition — install the fresh-user route mock before first navigation"
        ):
            # Must be installed before the first goto() so the very first
            # authorDetails call from ProtectedRoutes.jsx is already intercepted.
            onboarding_page.mock_fresh_user_state()

        try:
            with allure.step(
                "Precondition — /onboarding shows the Welcome card (first-login state)"
            ):
                # Direct navigation, one hop — same entry as the merged ELITEA-2231
                # spec. Root '/' also redirects here while the mock is installed.
                onboarding_page.navigate("/onboarding")
                expect(page).to_have_url(re.compile(r"/onboarding"))
                expect(onboarding_page.welcome_card).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert (
                    page.evaluate("() => sessionStorage.getItem('onboarding_state')")
                    is None
                ), "sessionStorage.onboarding_state must be unset before the click"

            with allure.step(
                "Step 9a — Baseline: no account-status polling before the click "
                "(quiet window)"
            ):
                # /social/author/ is fetched twice during normal page load, so the
                # quiet window must start AFTER the Welcome card is visible.
                # Deliberate observation window, not a wait-for-a-condition: the
                # assertion is that NOTHING happens, so there is nothing to wait on.
                polls_before_quiet_window = len(author_polls)
                page.wait_for_timeout(QUIET_WINDOW_MS)
                polls_during_quiet_window = len(author_polls) - polls_before_quiet_window
                assert polls_during_quiet_window == 0, (
                    f"No GET /social/author/ request may be issued while the Welcome "
                    f"card is on screen — provisioning polling must not be running "
                    f"before the click; got {polls_during_quiet_window} request(s) in "
                    f"{QUIET_WINDOW_MS / 1000:.0f}s"
                )

            with allure.step("Step 1 — Click 'Sure, let's go!' on the Welcome page"):
                polls_before_click = len(author_polls)
                onboarding_page.click_get_started()
                click_ts = time.monotonic()
                expect(onboarding_page.tour_container).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

            with allure.step(
                "Step 8 — Progress footer with 'Configuring Personal project...' "
                "and 'about 5 min' at the bottom of the page"
            ):
                # Asserted first among the state checks so the progress bar's
                # starting value is read at the top of the provisioning state.
                expect(onboarding_page.progress_footer).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(onboarding_page.progress_status_label).to_have_text(
                    _EXPECTED_STATUS_LABEL
                )
                expect(onboarding_page.progress_estimated_time).to_have_text(
                    _EXPECTED_ESTIMATED_TIME
                )
                expect(onboarding_page.progress_bar).to_be_visible()
                expect(onboarding_page.progress_bar).to_have_attribute(
                    "role", "progressbar"
                )
                initial_progress = int(
                    onboarding_page.progress_bar.get_attribute("aria-valuenow")
                )
                assert (
                    _PROGRESS_START <= initial_progress <= _PROGRESS_START_UPPER_BOUND
                ), (
                    f"The determinate progress bar must start at its baseline "
                    f"{_PROGRESS_START} (Onboarding.jsx:71-73); got "
                    f"aria-valuenow={initial_progress}"
                )

            with allure.step(
                "Step 2 — The welcome card is replaced by the onboarding tips slide view"
            ):
                # 'Replaced' is a pair: the card is gone AND the tour is shown.
                expect(onboarding_page.welcome_card).to_have_count(0)
                expect(onboarding_page.tour_container).to_be_visible()

            with allure.step("Step 3 — ELITEA logo is shown at the top centre of the page"):
                expect(onboarding_page.page_logo).to_be_visible()

            with allure.step('Step 4 — First slide title is "Tip 1: Welcome to ELITEA"'):
                # Steps 4-6 share ONE node: TourContent.jsx renders the whole tip as a
                # single <Markdown> inside onboarding-tour-tip-content, whose children
                # are produced by the markdown renderer and carry no testids of their
                # own. Three contains-text checks on that node — a decomposition, not
                # a dropped step.
                expect(onboarding_page.tour_tip_content).to_be_visible()
                expect(onboarding_page.tour_tip_content).to_contain_text(
                    _EXPECTED_TIP1_TITLE
                )

            with allure.step("Step 5 — Slide description matches Tip 1's copy verbatim"):
                expect(onboarding_page.tour_tip_content).to_contain_text(
                    _EXPECTED_TIP1_DESCRIPTION
                )

            with allure.step("Step 6 — Quick Action text matches Tip 1's copy"):
                expect(onboarding_page.tour_tip_content).to_contain_text(
                    _EXPECTED_TIP1_QUICK_ACTION
                )

            with allure.step('Step 7 — Slide counter shows "1 / 48"'):
                expect(onboarding_page.tour_page_indicator).to_have_text(
                    _EXPECTED_SLIDE_COUNTER
                )
                # Axis 2 — independent proof the card really is at the FIRST slide:
                # the counter text alone could read "1 / 48" while the position is
                # wrong (TourContent.jsx: disabled={currentStep === 1}). Same
                # rationale as ELITEA-2235's Axis 2.
                expect(onboarding_page.tour_prev_button).to_be_disabled()

            with allure.step(
                "Step 10 — No sidebar navigation and no project dropdown while the "
                "project is still loading"
            ):
                # MainSidebar.jsx returns null when
                # isOnboardingPage && !user.personal_project_id.
                expect(onboarding_page.progress_footer).to_be_visible()
                expect(onboarding_page.sidebar_toggle).to_have_count(0)
                expect(onboarding_page.project_selector_trigger).to_have_count(0)
                # Axis 2 — the provisioning state and the ready state are mutually
                # exclusive (Onboarding.jsx:182/213); the banner's absence is what
                # proves the page is genuinely provisioning, not merely showing a
                # footer.
                expect(onboarding_page.workspace_ready_title).to_have_count(0)

            with allure.step(
                "Axis 2 — The click's persisted side effect: "
                "sessionStorage.onboarding_state == 'true'"
            ):
                # Onboarding.jsx:68 — this is what makes a refresh resume the tour
                # instead of re-showing the Welcome card.
                assert (
                    page.evaluate("() => sessionStorage.getItem('onboarding_state')")
                    == "true"
                ), "The click must persist sessionStorage.onboarding_state = 'true'"

            with allure.step(
                "Axis 2 — The determinate progress bar advances (it is not frozen)"
            ):
                # Deliberate observation window: the assertion is that a number MOVED,
                # so there is no condition to wait for. Onboarding.jsx increments
                # progress by 95/150 every second.
                page.wait_for_timeout(PROGRESS_WINDOW_MS)
                later_progress = int(
                    onboarding_page.progress_bar.get_attribute("aria-valuenow")
                )
                assert later_progress > initial_progress, (
                    f"The progress bar must advance while the project is being "
                    f"configured; aria-valuenow stayed at {initial_progress} after "
                    f"{PROGRESS_WINDOW_MS / 1000:.0f}s"
                )

            with allure.step(
                "Step 9b — Provisioning polling begins only now: the click starts the "
                "5s GET /social/author/ poll"
            ):
                # Case-text drift (clarification #1756): the click issues no
                # provisioning call — handleShowTour() starts a 5s poll of the
                # account-status endpoint. The poll START is the observable
                # "it begins only now".
                elapsed = time.monotonic() - click_ts
                if elapsed < POLL_WINDOW_S:
                    # Close the 12s observation window opened by the click.
                    page.wait_for_timeout(int((POLL_WINDOW_S - elapsed) * 1000) + 200)
                polls_in_window = [
                    ts
                    for ts in author_polls[polls_before_click:]
                    if ts - click_ts <= POLL_WINDOW_S
                ]
                assert len(polls_in_window) >= 2, (
                    f"The click must start the 5s account-status poll (measured live "
                    f"at +5s/+10s/+15s); expected >= 2 GET /social/author/ requests "
                    f"within {POLL_WINDOW_S:.0f}s of the click, got "
                    f"{len(polls_in_window)}"
                )

            with allure.step(
                "Step 11 — Once loading completes, the private project appears in the "
                "left-menu dropdown with the sidebar entities displayed"
            ):
                # Release the mask (substitution #2): the next poll receives the
                # unmodified backend response, so everything asserted below is the
                # product's own rendering of genuine backend data.
                onboarding_page.clear_author_details_mock()
                expect(onboarding_page.workspace_ready_title).to_be_visible(
                    timeout=READY_TRANSITION_TIMEOUT
                )
                expect(onboarding_page.progress_footer).to_have_count(0)
                expect(onboarding_page.sidebar_toggle).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(onboarding_page.project_selector_trigger).to_be_visible()
                expect(onboarding_page.project_selector_trigger).to_contain_text(
                    _EXPECTED_PROJECT_LABEL
                )
                # The entity menu fills in progressively — anchor on ONE item with an
                # auto-waiting expect, never assert the list length.
                expect(
                    onboarding_page.sidebar_menu_item(_SIDEBAR_ANCHOR_ITEM)
                ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
                onboarding_page.open_project_selector()
                expect(
                    onboarding_page.project_selector_option(_EXPECTED_PROJECT_LABEL)
                ).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Axis 2 — No error-level console messages across the flow"):
                assert not console_errors, (
                    f"No console errors expected across the provisioning flow; "
                    f"got: {console_errors}"
                )

        finally:
            # Explicit teardown — the mock is normally released inside step 11; this
            # also covers an early failure (the context auto-cleans at close too).
            onboarding_page.clear_author_details_mock()
