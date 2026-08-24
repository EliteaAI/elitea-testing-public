"""UI test — the ELITEA logo shows a green dot for an active server connection.

TMS: ELITEA-2233
AFS: test-specs/onboarding/l2_sidebar_logo_socket_status_green_dot_ELITEA-2233.md

The "green dot" is a single 8x8 Box rendered inside the sidebar logo IconButton
(``SidebarBody.jsx:229-235``), wrapped in a Tooltip. Its colour IS the whole state
machine: ``icon.fill.success`` (#2BD48D) when the socket is connected,
``icon.fill.error`` (#D71616) when it is not. There is exactly ONE such element in
the DOM, which is what makes the case's "no red dot is shown" step machine-checkable:
with a count of 1, "this one is green" *is* "no red one exists".

ZERO substitution — no route mock, no injected state, no Redux poke. Every asserted
value (colour, state attribute, accessible name, geometry) is produced by the product
from its real socket connection.

Known handling (nothing masked):
  - #1753 (MINOR, open): the interactive-tour first-visit prompt logs
    "MUI: The modal content node does not accept focus." That ONE message is excluded
    from the console assertion; every other console error still fails the test.
  - Case-text drift (clarification #1765, filed): step 1 says "log in for the first
    time" — the indicator is socket state on every session, not a first-login
    artifact; step 3 says "above the logo" — live it is the logo button's top-RIGHT
    corner, overlapping it; step 4's "(red would indicate server is updating)" is
    really "socket disconnected". The live contract is asserted, per the
    reverse-masking guard.

The disconnected/red state is deliberately NOT exercised: producing it honestly needs
the backend socket to drop, and faking it would be a terminal substitution of the very
thing the case observes (.agents/testing.md § Fidelity policy). It is covered here by
the exhaustive absence assertions in step 4.

Usage::

    cd automation
    HEADLESS=true ../.venv/bin/pytest tests/ui/onboarding/test_sidebar_socket_status_indicator.py -v
"""

import re

import allure
import pytest
from pages.sidebar_header_page import SidebarHeaderPage
from playwright.sync_api import expect

pytestmark = [
    pytest.mark.p2,
    pytest.mark.onboarding,
    pytest.mark.regression,
    pytest.mark.ui,
    pytest.mark.new,
]

UI_ELEMENT_TIMEOUT = 10_000

# palette.icon.fill.success = #2BD48D — the connected colour.
_CONNECTED_COLOR = "rgb(43, 212, 141)"
# palette.icon.fill.error = #D71616 — the disconnected ("red dot") colour the case
# asserts must NOT be shown.
_DISCONNECTED_COLOR = "rgb(215, 22, 22)"
# MUI's Tooltip clones `title={`${systemSenderName} is ${socketStatus}`}` onto the
# child as aria-label, so the product's own semantic statement is readable without
# hovering.
_CONNECTED_ACCESSIBLE_NAME = "Elitea is connected"
# Geometry tolerance in CSS pixels — the dot is absolutely positioned at top:0
# right:0 of the logo button, so the edges coincide exactly; 1px absorbs
# sub-pixel layout rounding without admitting a real move.
_EDGE_TOLERANCE_PX = 1.0
# Known defect: #1753 — the first-visit tour prompt's MUI focus-trap warning.
_KNOWN_CONSOLE_ERROR_1753 = "does not accept focus"


class TestSidebarSocketStatusIndicator:
    """Sidebar logo — green socket-status dot (ELITEA-2233)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/onboarding/"
        "ELITEA-2233_onboarding-elitea-logo-displays-green-dot-indicating-active.md",
        "onetest-ai Test Case link",
    )
    def test_logo_shows_green_connected_dot(self, page):
        """The logo carries a green socket dot and no red one anywhere on the page."""
        sidebar = SidebarHeaderPage(page)
        console_errors: list = []
        page.on(
            "console",
            lambda msg: console_errors.append(f"{msg.type}: {msg.text}")
            if msg.type == "error"
            else None,
        )

        with allure.step(
            "Step 1 — Log in to the application and land on the expected landing page"
        ):
            # `auth_state` carries the authenticated session (on localhost the dev
            # server authenticates via VITE_DEV_TOKEN, so no login screen appears).
            sidebar.navigate("/chat")
            expect(page).to_have_url(re.compile(r"/chat"))

        with allure.step("Step 2 — Locate the ELITEA logo icon in the top left of the sidebar"):
            expect(sidebar.logo_button).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)

        with allure.step("Step 3 — A green dot is displayed on the ELITEA logo"):
            dot = sidebar.socket_indicator_in_logo()
            expect(dot).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
            # Three independent readings of the same fact: the product's own
            # semantic state, the rendered colour, and the accessible name.
            expect(dot).to_have_attribute("data-socket-status", "connected")
            expect(dot).to_have_css("background-color", _CONNECTED_COLOR)
            expect(dot).to_have_attribute("aria-label", _CONNECTED_ACCESSIBLE_NAME)

            # "Displayed above the logo" is a relationship, not a coordinate: the dot
            # is a descendant of the logo button (asserted by the scoped locator
            # above) AND is laid out inside its box, flush with its top edge.
            dot_box = dot.bounding_box()
            logo_box = sidebar.logo_button.bounding_box()
            assert dot_box is not None and logo_box is not None, (
                "Both the socket dot and the logo button must have a layout box"
            )
            assert dot_box["x"] >= logo_box["x"] - _EDGE_TOLERANCE_PX, (
                f"Socket dot starts left of the logo button: dot={dot_box} logo={logo_box}"
            )
            assert (
                dot_box["x"] + dot_box["width"]
                <= logo_box["x"] + logo_box["width"] + _EDGE_TOLERANCE_PX
            ), f"Socket dot extends past the logo button's right edge: dot={dot_box} logo={logo_box}"
            assert abs(dot_box["y"] - logo_box["y"]) <= _EDGE_TOLERANCE_PX, (
                f"Socket dot is not top-aligned with the logo button: "
                f"dot={dot_box} logo={logo_box}"
            )

        with allure.step(
            "Step 4 — No red dot is shown (a red dot would mean the socket is disconnected)"
        ):
            # Exhaustive, not merely "this one isn't red": exactly one indicator
            # element exists in the whole document, so a green one is the only one.
            expect(sidebar.socket_status_indicator).to_have_count(1)
            expect(dot).not_to_have_css("background-color", _DISCONNECTED_COLOR)
            # The same negative stated in the product's own vocabulary.
            expect(sidebar.socket_indicator_disconnected()).to_have_count(0)
            expect(sidebar.socket_indicator_connected()).to_have_count(1)

        with allure.step(
            "Axis 2 — No console errors other than the known first-visit-prompt "
            "focus-trap warning"
        ):
            # Known defect: #1753 — deterministic, filed, open, product-side a11y
            # defect. Excluding this ONE message is not masking: every other console
            # error still fails the test, and the red returns automatically once
            # #1753 is fixed and the filter stops matching.
            unexpected = [e for e in console_errors if _KNOWN_CONSOLE_ERROR_1753 not in e]
            assert not unexpected, (
                f"No console errors expected while reading the sidebar socket status "
                f"other than known defect #1753; got: {unexpected}"
            )
