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

Version-literal flakiness fix (2026-08-14, reviewer finding — see
``.agents/memory/qa-engineer/version_number_literals_are_flaky_assertions.md``):
the 6 component names (``elitea_core``, ``admin``, ...) are stable and stay
hardcoded, but their version NUMBERS are live backend deploy metadata
(``systemInfo.plugins``) that legitimately changes on the next service bump —
pinning exact literals ("0.673", "0.77", ...) would false-red on a routine
release unrelated to this feature. Instead the test asserts FORMAT (each
component shows a semver-like ``name: X.Y[.Z...]`` value) and reads the
ACTUAL versions the tooltip renders at run time, then checks the copied
clipboard text is a faithful reproduction of that same tooltip content — the
case's real intent per the AFS ("the copied text matches what the tooltip
showed"), without freezing any version literal captured during analysis into
the test file.

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

# The exact 6 components the case text enumerates — component NAMES are stable
# (app config), unlike their version numbers, which are live backend deploy
# metadata and are intentionally NOT hardcoded here (see module docstring).
EXPECTED_COMPONENTS = [
    "elitea_core",
    "admin",
    "notifications",
    "configurations",
    "sdk_plugin",
    "indexer_worker",
]

# Semver-like version format the backend renders (`ResourceVersionInfo.jsx`:
# `${plugin.name}: ${plugin.version}`) — e.g. "0.673", "0.9.13". Presence +
# format only; the actual digits are read live per component (Step 5).
VERSION_FORMAT = r"\d+(?:\.\d+)+"

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
            "Step 4 — Verify the tooltip shows all 6 expected components: " + ", ".join(EXPECTED_COMPONENTS)
        ):
            tooltip_text = help_center.version_info_tooltip.text_content() or ""
            for component in EXPECTED_COMPONENTS:
                assert component in tooltip_text, (
                    f"Expected component '{component}' to appear in the tooltip, "
                    f"got: {tooltip_text!r}"
                )

        with allure.step("Step 5 — Verify each component shows a version number in the live-served format"):
            # The name/value are two adjacent inline Typography spans with no text
            # node between them, so DOM text_content() concatenates them with no
            # space ("elitea_core:0.673") even though a flex `gap` renders one
            # visually — allow zero-or-more whitespace between the colon and the
            # version rather than asserting the CSS-rendered gap as literal text.
            #
            # Assert FORMAT, not a pinned literal (2026-08-14 reviewer finding):
            # these are live backend deploy versions that legitimately change on
            # the next service release. Capture the ACTUAL version each component
            # reports right now so Step 9 can verify the clipboard faithfully
            # reproduces THIS run's tooltip content, not a value frozen at
            # analysis time.
            observed_versions: dict[str, str] = {}
            for component in EXPECTED_COMPONENTS:
                pattern = re.compile(rf"{re.escape(component)}:\s*({VERSION_FORMAT})")
                match = pattern.search(tooltip_text)
                assert match, (
                    f"Expected '{component}: <version>' in semver-like format "
                    f"(e.g. '0.673') in the tooltip text, got: {tooltip_text!r}"
                )
                observed_versions[component] = match.group(1)

        with allure.step("Step 6 — Verify the copy button is present at the bottom of the tooltip"):
            expect(help_center.version_info_copy_button).to_be_visible()

        with allure.step("Step 7/8 — Click the copy button and verify the success toast appears"):
            clipboard_text = help_center.copy_version_info()
            expect(help_center.toast_message).to_have_text(EXPECTED_TOAST_TEXT)

        with allure.step(
            "Step 9 — Verify the clipboard contains the version line and faithfully reproduces "
            "the same component versions the tooltip displayed (the honest automated equivalent "
            "of 'paste into a text editor')"
        ):
            assert clipboard_text.startswith("Version:"), (
                f"Expected clipboard text to start with 'Version:', got: {clipboard_text!r}"
            )
            # Fidelity check against THIS run's observed tooltip values (Step 5), not a
            # pinned literal — a stale/wrong clipboard write is still caught (the copy
            # would silently diverge from what was just displayed), while a routine
            # backend version bump between analysis and run time is not a false red.
            for component, version in observed_versions.items():
                expected_line = f"{component}: {version}"
                assert expected_line in clipboard_text, (
                    f"Expected '{expected_line}' (as shown in the tooltip) in the clipboard "
                    f"content, got: {clipboard_text!r}"
                )
