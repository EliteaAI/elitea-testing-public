"""Annotation-driven locator descriptors for Page Objects.

Provides a clean way to define locators using Python descriptors and type hints.
New page objects should use testid-only declarations; legacy fallbacks are
accepted but never executed when a testid is present.
"""

from typing import Optional, Callable
from playwright.sync_api import Locator, Page


class LocatorDescriptor:
    """Descriptor for declaring page locators with testid-first strategy.

    Usage (preferred — testid only):
        class MyPage(BasePage):
            login_button = LocatorDescriptor(testid="login-button")
            email_input = LocatorDescriptor(testid="email-input")

    When a testid is provided it is returned directly; the fallback is never
    called.  Playwright's built-in auto-wait handles element timing.
    """

    def __init__(
        self,
        testid: Optional[str] = None,
        fallback: Optional[Callable[[Page], Locator]] = None,
        description: str = ""
    ):
        """Initialize locator descriptor.

        Args:
            testid: data-testid attribute value (preferred, takes priority)
            fallback: Fallback locator function (only used when testid is absent)
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

        Testid takes priority; fallback is only used when no testid is set.
        """
        if instance is None:
            return self

        page: Page = instance.page

        if self.testid:
            return page.get_by_test_id(self.testid)

        if self.fallback_fn:
            return self.fallback_fn(page)

        raise ValueError(
            f"Cannot locate {self.attr_name}: no testid or fallback provided"
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
