"""Skills List Page - Dashboard view for browsing skills.

Handles: /app/skills/all
- Skills list display
- Navigate to create skill
"""

import re
import time
import logging
from playwright.sync_api import Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor
from utils.actions import action


logger = logging.getLogger("elitea.pages.skills_list")


class SkillsListPage(BasePage):
    """Page object for the skills list/dashboard page.

    URL: /app/skills/all
    """

    page_header = LocatorDescriptor(
        testid="skills-page-header",
        description="Skills page header"
    )

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @action("Navigate to skills list")
    def navigate(self):
        """Navigate to the skills dashboard and wait until ready."""
        super().navigate("/app/skills/all")
        self.wait_for_page_load()
        logger.info("Navigated to skills dashboard and page loaded")

    @action("Navigate to create skill")
    def navigate_to_create(self):
        """Navigate directly to the create skill page.

        Uses direct URL navigation for reliability.
        """
        super().navigate("/app/skills/create")
        self.wait_for_network(timeout=10000)
        logger.info("Navigated to create skill page")

    # ------------------------------------------------------------------
    # Wait helpers
    # ------------------------------------------------------------------

    def wait_for_page_load(self, timeout: int = 15000):
        """Wait for the skills list page to fully load.

        Uses a regex with $ anchor to ensure we are on /skills/all and not
        on /skills/all/{id} (the detail page URL).  Glob patterns like
        **/skills/all also match /skills/all/4, so regex is required here.
        """
        self.page.wait_for_url(
            re.compile(r".*/skills/all/?$"),
            timeout=timeout,
        )
        self.wait_for_network(timeout=5000)
        self.dismiss_banner_if_present()
        logger.info("Skills list page loaded")

    # ------------------------------------------------------------------
    # List queries
    # ------------------------------------------------------------------

    def skill_exists_in_list(self, name: str) -> bool:
        """Return True if a skill with the given name is currently visible.

        Point-in-time check — no waiting.  Uses case-insensitive match
        because the UI title-cases skill names.

        Args:
            name: Skill name to look for (case-insensitive substring).

        Returns:
            True if the skill is visible right now, False otherwise.
        """
        cards = self.page.get_by_test_id("entity-card-name").all()
        return any(name.lower() in (c.text_content() or "").lower() for c in cards)

    def wait_for_skill_absent(self, name: str, timeout: int = 10000):
        """Wait until a skill is no longer visible in the list.

        Use after deletion — waits for the list to re-fetch and remove the
        skill card.  Succeeds immediately if the skill is already absent.

        Args:
            name: Skill name (case-insensitive).
            timeout: How long to wait in ms.
        """
        deadline = time.time() + timeout / 1000
        while time.time() < deadline:
            if not self.skill_exists_in_list(name):
                return
            self.page.wait_for_timeout(500)
        raise TimeoutError(
            f"Skill '{name}' still visible in list after {timeout}ms"
        )
