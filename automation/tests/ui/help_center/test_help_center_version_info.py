"""UI test for Help Center — version info tooltip displays component versions
and can be copied (ELITEA-2225).

Verifies the header's version label + info-icon tooltip (elitea_core, admin,
notifications, configurations, sdk_plugin, indexer_worker with their live
version numbers), the copy-to-clipboard action, its success toast, and that
the OS clipboard genuinely contains the full version block afterward.

AFS: test-specs/help-center/l2_version-info-tooltip-copy_ELITEA-2225.md

Case-text drift (not a product defect — see AFS Axis 2 / Automation Hints):
the case says "Click the 'i' (info) icon"; the live ``ResourceVersionInfo.jsx``
tooltip (a bare MUI ``Tooltip``, no click-only wiring) opens on HOVER. The
test drives it via ``hover()`` as the code-confirmed intended trigger.

Markers:
    - ui: requires browser
    - help_center: Help Center tests
    - p2: priority (case priority: high)
    - regression
"""

import logging
import re

import allure
import pytest
from pages.help_center_page import HelpCenterPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.help_center, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

# Live-confirmed component list + versions (source: DEV backend's systemInfo.plugins,
# 2026-08-14 exploration) — the exact 6 components the case text enumerates.
EXPECTED_COMPONENT_VERSIONS = {
    "elitea_core": "0.673",
    "admin": "0.77",
    "notifications": "0.21",
    "configurations": "0.160",
    "sdk_plugin": "0.9.13",
    "indexer_worker": "0.854",
}

EXPECTED_TOAST_TEXT = "The version information has been copied to the clipboard."


class TestHelpCenterVersionInfo:
    """ELITEA-2225: version info tooltip displays component versions and can be copied."""

    def test_version_info_tooltip_displays_and_copies(self, page):
        with allure.step("Step 1 — Navigate to Help Center"):
            help_center = HelpCenterPage(page)
            help_center.navigate()
            expect(help_center.page_header).to_be_visible()
            expect(help_center.page_header).to_have_text("Help Center")

        with allure.step("Step 2 — Locate the version label in the header"):
            expect(help_center.version_label).to_be_visible()
            expect(help_center.version_label).to_have_text(re.compile(r"^Version: \S+ \(.+\)$"))

        with allure.step(
            "Step 3 — Hover the 'i' info icon next to the version label (live product: "
            "hover-triggered MUI Tooltip, not click — see AFS Axis 2)"
        ):
            help_center.open_version_info_tooltip()
            expect(help_center.version_info_tooltip).to_be_visible()

        with allure.step(
            "Step 4 — Verify the tooltip shows all 6 expected components: "
            + ", ".join(EXPECTED_COMPONENT_VERSIONS)
        ):
            tooltip_text = help_center.version_info_tooltip.text_content() or ""
            for component in EXPECTED_COMPONENT_VERSIONS:
                assert component in tooltip_text, (
                    f"Expected component '{component}' to appear in the tooltip, "
                    f"got: {tooltip_text!r}"
                )

        with allure.step("Step 5 — Verify each component shows its version number"):
            # The name/value are two adjacent inline Typography spans with no text
            # node between them, so DOM text_content() concatenates them with no
            # space ("elitea_core:0.673") even though a flex `gap` renders one
            # visually — allow zero-or-more whitespace between the colon and the
            # version rather than asserting the CSS-rendered gap as literal text.
            for component, version in EXPECTED_COMPONENT_VERSIONS.items():
                pattern = re.compile(rf"{re.escape(component)}:\s*{re.escape(version)}")
                assert pattern.search(tooltip_text), (
                    f"Expected '{component}: {version}' in the tooltip text, got: {tooltip_text!r}"
                )

        with allure.step("Step 6 — Verify the copy button is present at the bottom of the tooltip"):
            expect(help_center.version_info_copy_button).to_be_visible()

        with allure.step("Step 7/8 — Click the copy button and verify the success toast appears"):
            clipboard_text = help_center.copy_version_info()
            expect(help_center.toast_message).to_have_text(EXPECTED_TOAST_TEXT)

        with allure.step(
            "Step 9 — Verify the clipboard contains the version line and all 6 component "
            "version details (the honest automated equivalent of 'paste into a text editor')"
        ):
            assert clipboard_text.startswith("Version:"), (
                f"Expected clipboard text to start with 'Version:', got: {clipboard_text!r}"
            )
            for component, version in EXPECTED_COMPONENT_VERSIONS.items():
                expected_line = f"{component}: {version}"
                assert expected_line in clipboard_text, (
                    f"Expected '{expected_line}' in the clipboard content, got: {clipboard_text!r}"
                )
