"""Annotation-driven locator descriptors for Page Objects.

Provides a clean way to define locators using Python descriptors and type hints.
Priority: testid > locator. Use add-data-testid skill if element lacks both.
"""

from typing import Optional, Callable
from playwright.sync_api import Locator, Page


class LocatorDescriptor:
    """Descriptor for declaring page locators with testid-first strategy.

    Usage:
        class MyPage(BasePage):
            # Preferred: data-testid (most stable)
            login_button = LocatorDescriptor(testid="login-button")

            # Alternative: CSS/ID selector (when testid not available)
            refresh_btn = LocatorDescriptor(locator="#RefreshButton")
            delete_btn = LocatorDescriptor(locator='[aria-label="Delete"]')

    Priority: testid > locator. If element has neither, use add-data-testid skill.
    """

    def __init__(
        self,
        testid: Optional[str] = None,
        locator: Optional[str] = None,
        description: str = "",
        # Legacy support - will be removed in future
        fallback: Optional[Callable[[Page], Locator]] = None,
    ):
        """Initialize locator descriptor.

        Args:
            testid: data-testid attribute value (preferred, takes priority)
            locator: CSS selector string (e.g. "#id", '[aria-label="..."]')
            description: Human-readable description for docs
            fallback: DEPRECATED - use locator parameter instead
        """
        self.testid = testid
        self.locator_selector = locator
        self.fallback_fn = fallback  # Legacy support
        self.description = description
        self.attr_name = None

    def __set_name__(self, owner, name):
        """Called when descriptor is assigned to class attribute."""
        self.attr_name = name

    def __get__(self, instance, owner) -> Locator:
        """Return the locator for this element.

        Priority: testid > locator > fallback (legacy).
        """
        if instance is None:
            return self

        page: Page = instance.page

        if self.testid:
            return page.get_by_test_id(self.testid)

        if self.locator_selector:
            return page.locator(self.locator_selector)

        # Legacy fallback support
        if self.fallback_fn:
            return self.fallback_fn(page)

        raise ValueError(
            f"Cannot locate {self.attr_name}: no testid or locator provided"
        )

    def __set__(self, instance, value):
        """Prevent assignment to descriptor."""
        raise AttributeError(f"Cannot set locator {self.attr_name}")


class OptionalLocatorDescriptor(LocatorDescriptor):
    """Locator descriptor that returns None instead of raising error if not found.

    Useful for elements that may or may not be present on the page.
    """

    def __get__(self, instance, owner) -> Optional[Locator]:
        """Return locator or None if not found."""
        if instance is None:
            return self

        try:
            return super().__get__(instance, owner)
        except ValueError:
            return None
