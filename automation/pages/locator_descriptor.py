"""Annotation-driven locator descriptors for Page Objects.

Provides a clean way to define locators using Python descriptors and type hints.
Supports both data-testid (robust) and fallback locators (role/css selectors).
"""

from typing import Optional, Callable
from playwright.sync_api import Locator, Page


class LocatorDescriptor:
    """Descriptor for declaring page locators with testid + fallback strategy.

    Usage:
        class MyPage(BasePage):
            login_button = LocatorDescriptor(
                testid="login-button",
                fallback=lambda page: page.get_by_role("button", name="Login")
            )

            email_input = LocatorDescriptor(
                testid="email-input",
                fallback=lambda page: page.locator('input[type="email"]')
            )

    When accessed, tries testid first, falls back if element not found.
    """

    def __init__(
        self,
        testid: Optional[str] = None,
        fallback: Optional[Callable[[Page], Locator]] = None,
        description: str = ""
    ):
        """Initialize locator descriptor.

        Args:
            testid: data-testid attribute value (preferred)
            fallback: Function that returns fallback locator
            description: Human-readable description for docs
        """
        self.testid = testid
        self.fallback_fn = fallback
        self.description = description
        self.attr_name = None

    def __set_name__(self, owner, name):
        """Called when descriptor is assigned to class attribute."""
        self.attr_name = name

    def __get__(self, instance, owner) -> Locator:
        """Return the locator for this element.

        Strategy:
        1. Try data-testid (if provided)
        2. Fall back to fallback locator
        3. Raise error if neither works
        """
        if instance is None:
            return self

        page: Page = instance.page

        # Try testid first (most robust)
        if self.testid:
            try:
                locator = page.get_by_test_id(self.testid)
                # Quick check if element exists (timeout 100ms)
                if locator.count() > 0:
                    return locator
            except Exception:
                pass

        # Fall back to provided fallback locator
        if self.fallback_fn:
            return self.fallback_fn(page)

        # No locator strategy available
        raise ValueError(
            f"Cannot locate {self.attr_name}: "
            f"testid='{self.testid}' not found and no fallback provided"
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
