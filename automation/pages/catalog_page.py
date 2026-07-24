"""Catalog page object for Elitea platform (Agent Hub / Skill Hub Catalog).

Handles ``/elitea-catalog`` — the published-entity catalog reachable via the
Agents / Skills hub tabs. Scope is exactly what GAP-054 (category "Show
more"/"Show less" pagination) touches: a single category section's
container, card grid, and show-more/show-less toggle.

Testids are dynamic per category (``AgentCategorySection.jsx`` renders one
section per category on the same page), so locators use the class-level
template-constant pattern rather than a static ``LocatorDescriptor``
(``.agents/testing.md`` § Locator policy — Dynamic testid canonical
pattern).

URL: /elitea-catalog?tab={agents|skills}
"""

import logging

from playwright.sync_api import Page
from utils.actions import action

from .base_page import BasePage

logger = logging.getLogger("elitea.pages.catalog")


class CatalogPage(BasePage):
    """Page object for ``/elitea-catalog``.

    Covers the per-category "Show more"/"Show less" pagination control
    (``AgentCategorySection.jsx``) — scope is exactly GAP-054's touched
    elements; the Skills-tab equivalent (``SkillCategorySection.jsx``) is a
    byte-for-byte separate component this page does not yet address (no
    case exercises it with sufficient data — see
    ``test-specs/hubs/_surface.md``).

    URL: /elitea-catalog?tab={agents|skills}
    """

    # ------------------------------------------------------------------
    # Dynamic testid templates — one category section per rendered page.
    # ------------------------------------------------------------------

    CATALOG_CATEGORY_SECTION = '[data-testid="catalog-category-section-{}"]'
    CATALOG_CATEGORY_GRID = '[data-testid="catalog-category-grid-{}"]'
    CATALOG_CATEGORY_SHOW_MORE_BUTTON = '[data-testid="catalog-category-show-more-button-{}"]'

    # Declared improvisation (.agents/role-overrides.md § Declared-improvisation
    # protocol): AgentCard.jsx has no per-card testid, and GAP-054's own
    # Concrete Handles table sanctions ":scope > *" child-count as the
    # correct, minimal-footprint mechanism ("confirmed via live count",
    # not "needs-adding") — adding a per-card testid would be an
    # untouched-element addition beyond this case's scope, since no
    # assertion targets individual card identity, only the grid's
    # cardinality. Kept as an UPPER_CASE class constant (not inlined in a
    # method body) so it stays greppable, matching the letter of the
    # class-level-constant discipline even though it is not itself a
    # `[data-testid=` selector.
    CATALOG_GRID_CHILD = ":scope > *"

    def __init__(self, page: Page):
        super().__init__(page)

    @staticmethod
    def category_slug(category_name: str) -> str:
        """Slugify a category display name the same way the frontend does.

        ``AgentCategorySection.jsx`` derives its dynamic testid suffix as
        ``category.toLowerCase().replace(/\\s+/g, '-')`` — mirror that
        exactly so locators resolve (e.g. ``"Other"`` -> ``"other"``).
        """
        return category_name.lower().replace(" ", "-")

    def navigate_to_tab(self, tab: str) -> None:
        """Navigate to the Catalog page on *tab* ('agents' or 'skills')."""
        self.navigate(f"/elitea-catalog?tab={tab}")
        logger.info("Navigated to Catalog tab=%s", tab)

    def category_section(self, category_name: str):
        """Return the Locator for a category's section container."""
        slug = self.category_slug(category_name)
        return self.page.locator(self.CATALOG_CATEGORY_SECTION.format(slug))

    def category_grid(self, category_name: str):
        """Return the Locator for a category's card grid container."""
        slug = self.category_slug(category_name)
        return self.page.locator(self.CATALOG_CATEGORY_GRID.format(slug))

    def category_show_more_button(self, category_name: str):
        """Return the Locator for a category's Show more/less toggle."""
        slug = self.category_slug(category_name)
        return self.page.locator(self.CATALOG_CATEGORY_SHOW_MORE_BUTTON.format(slug))

    def category_cards(self, category_name: str):
        """Return the Locator for every direct child (card) of *category_name*'s grid.

        See ``CATALOG_GRID_CHILD`` docstring for why this is a structural
        child-count selector rather than a per-card testid.
        """
        return self.category_grid(category_name).locator(self.CATALOG_GRID_CHILD)

    def get_category_card_count(self, category_name: str) -> int:
        """Return the number of cards currently rendered in *category_name*'s grid."""
        return self.category_cards(category_name).count()

    def get_show_more_button_text(self, category_name: str) -> str:
        """Return the toggle's current label ('Show more' / 'Show less')."""
        return (self.category_show_more_button(category_name).text_content() or "").strip()

    @action("Toggle category Show more/less")
    def toggle_show_more(self, category_name: str) -> None:
        """Click *category_name*'s Show more/Show less toggle.

        Purely client-side re-slice for a non-paginated bucket (confirmed
        live, GAP-054) — no network wait needed; callers should assert the
        new card count via Playwright's own auto-retrying checks.
        """
        logger.info("Toggling Show more/less for category=%s", category_name)
        self.category_show_more_button(category_name).click()
