"""Annotation-driven locator descriptors for Page Objects.

Provides a clean way to define locators using Python descriptors and type hints.

POLICY (testid-only — .claude/rules/page-objects.md, .agents/testing.md):
new code passes `testid=` and NOTHING else. If the element lacks a data-testid,
add one to EliteaUI via the add-data-testid skill — never reach for `locator=`
or `fallback=`. Both are LEGACY-ONLY parameters kept so old page objects keep
importing; they are never valid in new or modified declarations. For
runtime-parameterized testids use the class-level template-constant pattern
(.agents/testing.md § Locator policy), not this class.
"""

from typing import Optional, Callable
from playwright.sync_api import Locator, Page


class LocatorDescriptor:
    """Descriptor for declaring page locators. Testid-only in new code.

    Usage (the ONLY sanctioned form):
        class MyPage(BasePage):
            login_button = LocatorDescriptor(testid="login-button")

    Element has no data-testid? Add one via the add-data-testid skill —
    do NOT use `locator=` or `fallback=`: both are legacy-only (old code
    keeps importing; new/modified declarations must not pass them, and the
    reviewer's mechanical gate blocks them).
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
            testid: data-testid attribute value — the only parameter new code passes
            locator: LEGACY ONLY — never in new code (add a testid instead)
            description: Human-readable description for docs
            fallback: LEGACY ONLY — dead code when testid is set; never in new code
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
