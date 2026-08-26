"""UI test for ELITEA-1807 — Artifacts landing page, collapse/expand panels.

Verifies that the Artifacts page's two collapsible panels — the BUCKETS left
panel (``<<`` / ``>>``) and the global navigation sidebar (``<`` / ``>``) —
each collapse and expand correctly, and that neither one's state affects the
other's.

**How panel state is asserted.** Both controls are ONE element whose icon flips
with the state, and the icons are untagged SVGs. Per
``.agents/testing.md`` § Locator policy (PR #581 ruling: testid = stable
identity, state = a ``data-*`` attribute), each toggle carries
``data-collapsed="true|false"``, rendered from the very same value that selects
which icon to draw — so asserting the attribute IS asserting the icon swap the
case describes. The testids were added for this case on
EliteaAI/EliteaUI@9062dff0.

**Collapse is two different things, deliberately asserted as such.** When the
BUCKETS panel collapses, the heading / storage selector / footer are
*unmounted* (``BucketsPanel.jsx`` gates them on ``!collapsed``) — count 0 —
while the bucket ROWS stay in the DOM and merely go invisible
(``display: collapsed ? 'none' : 'flex'``). When the sidebar collapses, its
entries stay visible as icons and only their label ``<Typography>`` is
unmounted (``showLabel={!sideBarCollapsed}``), so each entry's text becomes
empty. Asserting the wrong one of these would pass for the wrong reason.

CLARIFICATION (case-text drift, not a defect — reverse-masking guard):
- EliteaAI/elitea-testing-public#1619 — the case enumerates the sidebar labels
  as "… Toolkits … Agent HUB". Live they read **"Toolkits & Indexes"**
  (``SidebarBody.jsx``) and **"Catalog"** (``AgentHubButton.jsx``); the other
  nine match. Nothing is broken, so the live labels are asserted and the case
  text is filed for correction. Sibling of #1208 (same rename, Catalog page
  header).

Fidelity: **no substitution of any kind** — no seeding, no ``page.route``, no
injected state. Every observable is rendered by the product from its own React
state in response to real clicks. The case's precondition ("at least one bucket
present") is satisfied by buckets that already exist in the project, so this
test is fully read-only (workflow skill Hard Rule 10) and adds nothing to the
known ``#636`` bucket leak.

AFS:
    test-specs/artifacts/l3_artifacts-landing-page-collapse-expand-panels_ELITEA-1807.md

Markers:
    - ui: requires browser
    - regression: regression test
    - new: added on automation/base, not yet validated on deployed envs

Usage:
    cd automation
    pytest tests/ui/artifacts/test_artifacts_landing_page_collapse_expand_panels.py -v
"""

import logging

import allure
import pytest
from pages.artifacts_page import ArtifactsPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.regression, pytest.mark.new]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

VIEWPORT_WIDTH = 1600
VIEWPORT_HEIGHT = 900

# Sidebar nav entries: the section's own `value` (which keys its testid) → the
# label the product renders when the sidebar is expanded. Keyed by `value`
# because the label is the thing under test — see CLARIFICATION #1619 for the
# two entries whose live label differs from the case text.
SIDEBAR_NAV_ENTRIES = {
    "chat": "Chats",
    "agents": "Agents",
    "pipelines": "Pipelines",
    "skills": "Skills",
    "toolkits": "Toolkits & Indexes",  # case text says "Toolkits" — #1619
    "mcps": "MCPs",
    "credentials": "Credentials",
    "applications": "Applications",
    "artifacts": "Artifacts",
}

SETTINGS_LABEL = "Settings"
AGENT_HUB_LABEL = "Catalog"  # case text says "Agent HUB" — #1619

# Collapsed sidebar: the entries remain, their labels do not.
COLLAPSED_LABEL = ""


@allure.epic("Artifacts")
@allure.feature("Landing Page UI")
class TestArtifactsLandingPageCollapseExpandPanels:
    """ELITEA-1807 — BUCKETS panel and navigation sidebar collapse/expand."""

    # ------------------------------------------------------------------
    # Suite-local assertion helpers (state shapes asserted 8+ times each)
    # ------------------------------------------------------------------

    @staticmethod
    def _assert_sidebar_expanded(artifacts_page: ArtifactsPage) -> None:
        """Sidebar in full mode: every entry visible WITH its label."""
        expect(artifacts_page.sidebar_collapse_toggle_button).to_have_attribute(
            "data-collapsed", "false", timeout=UI_ELEMENT_TIMEOUT
        )
        for value, label in SIDEBAR_NAV_ENTRIES.items():
            item = artifacts_page.sidebar_menu_item(value)
            expect(item).to_be_visible()
            expect(item).to_have_text(label)
        expect(artifacts_page.sidebar_settings_button).to_be_visible()
        expect(artifacts_page.sidebar_settings_button).to_have_text(SETTINGS_LABEL)
        expect(artifacts_page.sidebar_agent_hub_button).to_be_visible()
        expect(artifacts_page.sidebar_agent_hub_button).to_have_text(AGENT_HUB_LABEL)

    @staticmethod
    def _assert_sidebar_collapsed(artifacts_page: ArtifactsPage) -> None:
        """Sidebar in icon-only mode: entries still there, labels gone."""
        expect(artifacts_page.sidebar_collapse_toggle_button).to_have_attribute(
            "data-collapsed", "true", timeout=UI_ELEMENT_TIMEOUT
        )
        for value in SIDEBAR_NAV_ENTRIES:
            item = artifacts_page.sidebar_menu_item(value)
            expect(item).to_be_visible()
            expect(item).to_have_text(COLLAPSED_LABEL)
        expect(artifacts_page.sidebar_settings_button).to_be_visible()
        expect(artifacts_page.sidebar_settings_button).to_have_text(COLLAPSED_LABEL)
        expect(artifacts_page.sidebar_agent_hub_button).to_be_visible()
        expect(artifacts_page.sidebar_agent_hub_button).to_have_text(COLLAPSED_LABEL)

    @staticmethod
    def _assert_buckets_panel_expanded(artifacts_page: ArtifactsPage) -> None:
        """BUCKETS panel in full mode: header, storage, footer and list back."""
        expect(artifacts_page.buckets_panel_toggle_button).to_have_attribute(
            "data-collapsed", "false", timeout=UI_ELEMENT_TIMEOUT
        )
        expect(artifacts_page.buckets_heading).to_be_visible()
        expect(artifacts_page.storage_selector).to_be_visible()
        expect(artifacts_page.buckets_footer_count).to_be_visible()
        expect(artifacts_page.any_bucket_row()).to_be_visible()

    @staticmethod
    def _assert_buckets_panel_collapsed(artifacts_page: ArtifactsPage) -> None:
        """BUCKETS panel collapsed: chrome unmounted, list invisible."""
        expect(artifacts_page.buckets_panel_toggle_button).to_have_attribute(
            "data-collapsed", "true", timeout=UI_ELEMENT_TIMEOUT
        )
        # The toggle itself survives — it is what renders the '>>' icon.
        expect(artifacts_page.buckets_panel_toggle_button).to_be_visible()
        # Unmounted (gated on `!collapsed`), not merely hidden.
        expect(artifacts_page.buckets_heading).to_have_count(0)
        expect(artifacts_page.storage_selector).to_have_count(0)
        expect(artifacts_page.buckets_footer_count).to_have_count(0)
        # Still in the DOM (display:none) — so visibility, not count, is the
        # honest assertion for the bucket list.
        expect(artifacts_page.any_bucket_row()).not_to_be_visible()

    # ------------------------------------------------------------------
    # The case
    # ------------------------------------------------------------------

    @pytest.mark.p2
    @allure.title("ELITEA-1807 — BUCKETS panel and sidebar collapse/expand independently")
    @allure.description(
        "Collapses and expands the Artifacts BUCKETS left panel and the main "
        "navigation sidebar, verifying each restores fully (bucket list back; "
        "icons AND labels back), and that neither panel's state is disturbed "
        "by toggling the other — checked in both directions and from both "
        "starting states."
    )
    def test_collapse_and_expand_panels_independently(self, page):
        page.set_viewport_size({"width": VIEWPORT_WIDTH, "height": VIEWPORT_HEIGHT})
        artifacts_page = ArtifactsPage(page)

        with allure.step("Step 1 — Navigate to Artifacts; both panels are visible"):
            artifacts_page.navigate_to_artifacts()
            expect(artifacts_page.buckets_heading).to_be_visible(timeout=NAVIGATION_TIMEOUT)
            # Precondition: at least one bucket exists, so both panels render.
            self._assert_buckets_panel_expanded(artifacts_page)
            self._assert_sidebar_expanded(artifacts_page)

        with allure.step("Step 2 — Click '<<': the BUCKETS panel collapses fully and shows '>>'"):
            assert artifacts_page.toggle_buckets_panel(timeout=UI_ELEMENT_TIMEOUT) is True
            self._assert_buckets_panel_collapsed(artifacts_page)

        with allure.step("Step 3 — Click '>>': the BUCKETS panel is restored with its bucket list"):
            assert artifacts_page.toggle_buckets_panel(timeout=UI_ELEMENT_TIMEOUT) is False
            self._assert_buckets_panel_expanded(artifacts_page)

        with allure.step("Step 4 — Click '<': the sidebar collapses to icon-only and shows '>'"):
            assert artifacts_page.toggle_sidebar(timeout=UI_ELEMENT_TIMEOUT) is True
            self._assert_sidebar_collapsed(artifacts_page)

        with allure.step("Step 5 — Click '>': the sidebar expands with every icon AND label"):
            assert artifacts_page.toggle_sidebar(timeout=UI_ELEMENT_TIMEOUT) is False
            # Labels asserted per entry through its own testid (a page-level
            # text match would also hit the breadcrumb / page heading).
            # "Toolkits & Indexes" and "Catalog" are the LIVE labels — the
            # case text's "Toolkits"/"Agent HUB" are stale (#1619).
            self._assert_sidebar_expanded(artifacts_page)

        with allure.step(
            "Step 6 — Toggling the BUCKETS panel leaves the sidebar untouched"
        ):
            artifacts_page.toggle_buckets_panel(timeout=UI_ELEMENT_TIMEOUT)
            self._assert_buckets_panel_collapsed(artifacts_page)
            self._assert_sidebar_expanded(artifacts_page)

            artifacts_page.toggle_buckets_panel(timeout=UI_ELEMENT_TIMEOUT)
            self._assert_buckets_panel_expanded(artifacts_page)
            self._assert_sidebar_expanded(artifacts_page)

        with allure.step(
            "Step 7a — Toggling the sidebar leaves an EXPANDED BUCKETS panel untouched"
        ):
            artifacts_page.toggle_sidebar(timeout=UI_ELEMENT_TIMEOUT)
            self._assert_sidebar_collapsed(artifacts_page)
            self._assert_buckets_panel_expanded(artifacts_page)

            artifacts_page.toggle_sidebar(timeout=UI_ELEMENT_TIMEOUT)
            self._assert_sidebar_expanded(artifacts_page)
            self._assert_buckets_panel_expanded(artifacts_page)

        with allure.step(
            "Step 7b — Toggling the sidebar leaves a COLLAPSED BUCKETS panel collapsed"
        ):
            # The direction a regression actually hits: a re-render RESETTING
            # the collapsed panel back to expanded.
            artifacts_page.toggle_buckets_panel(timeout=UI_ELEMENT_TIMEOUT)
            self._assert_buckets_panel_collapsed(artifacts_page)

            artifacts_page.toggle_sidebar(timeout=UI_ELEMENT_TIMEOUT)
            self._assert_sidebar_collapsed(artifacts_page)
            self._assert_buckets_panel_collapsed(artifacts_page)

            artifacts_page.toggle_sidebar(timeout=UI_ELEMENT_TIMEOUT)
            self._assert_sidebar_expanded(artifacts_page)
            self._assert_buckets_panel_collapsed(artifacts_page)

        with allure.step("Expected final state — both panels expanded again"):
            artifacts_page.toggle_buckets_panel(timeout=UI_ELEMENT_TIMEOUT)
            self._assert_buckets_panel_expanded(artifacts_page)
            self._assert_sidebar_expanded(artifacts_page)
