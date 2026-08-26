"""UI tests for Help Center — resource card links redirect to the correct
external page (ELITEA-2220, ELITEA-2221, ELITEA-2222, ELITEA-2223, ELITEA-2224).

Family AFS (ELITEA-2220/2221/2222/2224 — differ only in data):
    test-specs/help-center/l3_resource-card-link-redirects-external-page_ELITEA-2220.md
Separate AFS (ELITEA-2223 — extra steps + an EPAM SSO wall on the destination):
    test-specs/help-center/l2_video-library-more-redirects-external-portal_ELITEA-2223.md

Known live defect (ELITEA-2221 row): the Release Notes card's "Release 2.0.2
(latest)" link 404s on docs.elitea.ai — filed as
EliteaAI/elitea-testing-public#1492. That one row is asserted with
``expect.soft()`` against the CORRECT expected title so the rest of the
family stays green while this row stays honestly red until the link is
fixed (sanctioned RED per ``.agents/testing.md`` § Merge gate).

Known environment limit (ELITEA-2223): Video Library's "More..." link
correctly redirects to ``videoportal.epam.com``, which requires an EPAM
corporate SSO session this suite has no credentials for. Steps verifying the
channel page's own content (title, tabs, video listing) are NOT automated —
see the AFS § Blocked Steps. Only the redirect mechanism itself (href +
final-host) is asserted.

Markers:
    - ui: requires browser
    - help_center: Help Center tests
    - p2 / p1: priority (see each test)
    - regression
"""

import logging
import re

import allure
import pytest
from pages.help_center_page import HelpCenterPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

# (case_id, card_title, card_link_slugs, click_slug, expected_href, expect_ok,
#  expected_title_substring, known_defect)
RESOURCE_LINK_CASES = [
    pytest.param(
        "ELITEA-2220",
        "Documentation",
        ["getting-started", "how-to-guides", "integrations", "migration-update"],
        "getting-started",
        "https://docs.elitea.ai/getting-started/chat-quick-start",
        True,
        "Quick Start",
        None,
        id="ELITEA-2220-documentation-getting-started",
    ),
    pytest.param(
        "ELITEA-2221",
        "Release Notes",
        ["release-2-0-2-latest", "release-2-0-1", "release-2-0-0", "release-2-0-0b2"],
        "release-2-0-2-latest",
        "https://docs.elitea.ai/release-notes/rn-2-0-2",
        False,
        "Release Notes - 2.0.2",
        "EliteaAI/elitea-testing-public#1492",
        id="ELITEA-2221-release-notes-latest",
    ),
    pytest.param(
        "ELITEA-2222",
        "Tutorials",
        ["course-ai-based-elitea-platform", "how-to-create-an-agent", "how-to-create-a-pipeline", "tutorials-more"],
        "how-to-create-an-agent",
        "https://docs.elitea.ai/archive/create-agent",
        True,
        "Create Your First Agent",
        None,
        id="ELITEA-2222-tutorials-how-to-create-an-agent",
    ),
    pytest.param(
        "ELITEA-2224",
        "Tutorials",
        ["course-ai-based-elitea-platform", "how-to-create-an-agent", "how-to-create-a-pipeline", "tutorials-more"],
        "tutorials-more",
        "https://docs.elitea.ai/",
        True,
        "Welcome to ELITEA Documentation",
        None,
        id="ELITEA-2224-tutorials-more",
    ),
]

# ELITEA-2224's non-"More..." link count on the Tutorials card preview — the
# concrete baseline for "displays more tutorials than shown in the card preview".
TUTORIALS_PREVIEW_LINK_COUNT = 3


class TestHelpCenterResourceLinks:
    """ELITEA-2220/2221/2222/2223/2224: resource card links redirect correctly."""

    @pytest.mark.p2
    @pytest.mark.ui
    @pytest.mark.help_center
    @pytest.mark.regression
    @pytest.mark.new
    @pytest.mark.parametrize(
        "case_id,card_title,card_link_slugs,click_slug,expected_href,expect_ok,"
        "expected_title_substring,known_defect",
        RESOURCE_LINK_CASES,
    )
    def test_resource_card_link_redirects_to_external_page(
        self,
        page,
        case_id,
        card_title,
        card_link_slugs,
        click_slug,
        expected_href,
        expect_ok,
        expected_title_substring,
        known_defect,
    ):
        with allure.step(f"Step 1 — [{case_id}] Navigate to Help Center"):
            help_center = HelpCenterPage(page)
            help_center.navigate()
            expect(help_center.page_header).to_be_visible()
            expect(help_center.page_header).to_have_text("Help Center")

        with allure.step(
            f'Step 2/3 — [{case_id}] Locate the "{card_title}" card and verify its links are displayed'
        ):
            for slug in card_link_slugs:
                link = help_center.resource_link(slug)
                expect(link).to_be_visible()

        with allure.step(f'Step 4 — [{case_id}] Verify "{click_slug}" href, then click it'):
            click_link = help_center.resource_link(click_slug)
            expect(click_link).to_have_attribute("href", expected_href)
            new_page = help_center.open_resource_link_in_new_tab(click_slug)

        with allure.step(f"Step 5 — [{case_id}] Verify the user is redirected to {expected_href} in a new tab"):
            expect(new_page).to_have_url(expected_href)

        with allure.step(f"Step 6 — [{case_id}] Verify the target page loads without errors"):
            title_pattern = re.compile(re.escape(expected_title_substring))
            if expect_ok:
                expect(new_page).to_have_title(title_pattern)
            else:
                expect.soft(
                    new_page,
                    f"Known defect: {known_defect} — {expected_href} should show a page titled "
                    f'"{expected_title_substring}...", but currently 404s ("Page Not Found")',
                ).to_have_title(title_pattern)

        if case_id == "ELITEA-2224":
            with allure.step(
                f"Step 7 — [{case_id}] CLARIFICATION: verify the docs homepage's navigation exposes "
                f"more linked topics than the {TUTORIALS_PREVIEW_LINK_COUNT}-link Tutorials card preview "
                "(live product routes 'More...' to the general docs homepage, not a dedicated "
                "tutorials-list page — see AFS Automation Hints)"
            ):
                # Third-party destination (docs.elitea.ai) — NOT subject to the
                # testid-only locator policy, which governs only our own
                # EliteaUI/elitea_assistant source. Ordinary role-based locators apply.
                nav_links = new_page.get_by_role("navigation", name="Pages").get_by_role("link")
                nav_link_count = nav_links.count()
                assert nav_link_count > TUTORIALS_PREVIEW_LINK_COUNT, (
                    f"Expected the docs homepage nav to expose more than "
                    f"{TUTORIALS_PREVIEW_LINK_COUNT} links (the Tutorials card preview count), "
                    f"got {nav_link_count}"
                )

    @pytest.mark.p1
    @pytest.mark.ui
    @pytest.mark.help_center
    @pytest.mark.regression
    @pytest.mark.new
    def test_video_library_more_redirects_to_external_portal(self, page):
        """ELITEA-2223: Video Library "More..." redirects to the external video portal.

        Steps 1-5 of the case (navigate, locate card, click, redirect mechanism)
        are fully asserted. Steps 6-8 (channel-page identity, Videos/Playlists
        tabs, video listing content) are NOT automatable — the destination
        requires an authenticated EPAM corporate SSO session
        (access.epam.com) this suite has no credentials for. See the AFS
        § Blocked Steps for the full reasoning.
        """
        video_library_slugs = [
            "self-service-agent-publishing",
            "clearer-shared-credential-setup",
            "indexing-completion-summary-report",
            "notification-center-inbox-style-management",
            "video-library-more",
        ]
        expected_href = "https://videoportal.epam.com/channel/DdYPoMVa2X/videos"

        with allure.step("Step 1 — Navigate to Help Center"):
            help_center = HelpCenterPage(page)
            help_center.navigate()
            expect(help_center.page_header).to_be_visible()
            expect(help_center.page_header).to_have_text("Help Center")

        with allure.step('Step 2/3 — Locate the "Video Library" card and verify its links are displayed'):
            for slug in video_library_slugs:
                link = help_center.resource_link(slug)
                expect(link).to_be_visible()

        with allure.step('Step 4 — Verify "More..." href, then click it'):
            more_link = help_center.resource_link("video-library-more")
            expect(more_link).to_have_attribute("href", expected_href)
            new_page = help_center.open_resource_link_in_new_tab("video-library-more")

        with allure.step(
            "Step 5 — Verify the user is redirected to the external Video Digital Platform portal "
            "(environment-agnostic form: the final resolved URL's host is on epam.com — the "
            "unauthenticated browser is bounced from videoportal.epam.com to an EPAM SSO login "
            "gate before the channel page itself renders, see AFS § Network Behavior)"
        ):
            new_page.wait_for_load_state("domcontentloaded")
            expect(new_page).to_have_url(re.compile(r"://[^/]*\.epam\.com/"))

        with allure.step(
            "Steps 6-8 — NOT AUTOMATED (documented block, not a masked failure): channel-page "
            'identity ("Elitea - AI Collaborative Platform"), Videos/Playlists tabs, and video '
            "listing (thumbnails/titles/authors/durations) all require an authenticated EPAM "
            "SSO session (access.epam.com) this suite has no credentials for. See AFS "
            "§ Blocked Steps for the full reasoning — this is a corporate SSO wall, not an "
            "Elitea product gap."
        ):
            logger.info(
                "ELITEA-2223 steps 6-8 intentionally not automated — EPAM SSO wall, "
                "see test-specs/help-center/l2_video-library-more-redirects-external-portal_ELITEA-2223.md"
            )
