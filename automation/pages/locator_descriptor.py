"""Annotation-driven locator descriptors for Page Objects.

Provides a clean way to define locators using Python descriptors and type hints.

POLICY (.claude/rules/page-objects.md, .agents/testing.md § Locator policy):
locators are class-level fields only, declared with ONE explicit kind, picked
by the ladder below — the first rung that uniquely and stably identifies the
element on the target env wins:

    1. testid=            data-testid already present on the target env
    2. role= (+ name=)    ARIA role + accessible name
    3. label=             form control by its <label> / aria-label
    4. css=               stable id / attribute CSS — never positional
    5. xpath=             declared last resort — never positional, never absolute

Every non-testid declaration MUST carry `suggested_testid=` — the testid the
weekly testid migrator adds to EliteaUI and swaps in. That hint is what makes
the migration mechanical (`automation/scripts/locator_inventory.py` reads it).

`locator=` and `fallback=` are LEGACY-ONLY parameters kept so old page objects
keep importing; they are never valid in new or modified declarations.
"""

import re
from collections.abc import Callable

from playwright.sync_api import Locator, Page

# Kinds in ladder order; "testid" is the target state of every locator.
LOCATOR_KINDS = ("testid", "role", "label", "css", "xpath")
LEGACY_KINDS = ("locator", "fallback")

# {section}-{element}-{type}; a trailing "-{}" marks a runtime-parameterized testid.
TESTID_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*(?:-\{\})?$")

# Positional selectors break on any layout change and are never sanctioned.
_XPATH_POSITIONAL_RE = re.compile(r"\[\s*\d+\s*\]|position\(\)|last\(\)")
_XPATH_ABSOLUTE_RE = re.compile(r"^\s*/(?!/)")
_CSS_POSITIONAL_RE = re.compile(
    r":nth-(?:child|of-type|last-child|last-of-type)\(|:(?:first|last|only)-(?:child|of-type)\b|>>\s*nth="
)
_ENGINE_PREFIX_RE = re.compile(r"^\s*[a-z_-]+=")


class LocatorSpec:
    """Shared declaration, validation and resolution for one locator.

    Not used directly — see `LocatorDescriptor` (page-level field) and
    `ScopedLocator` (class-level spec resolved inside a parent locator).
    Invalid declarations raise ValueError at import time, so a policy
    violation fails collection instead of shipping.
    """

    allow_legacy = True

    def __init__(
        self,
        testid: str | None = None,
        locator: str | None = None,
        description: str = "",
        # Legacy support - will be removed in future
        fallback: Callable[[Page], Locator] | None = None,
        *,
        role: str | None = None,
        name: str | None = None,
        exact: bool | None = None,
        label: str | None = None,
        css: str | None = None,
        xpath: str | None = None,
        suggested_testid: str | None = None,
    ):
        """Initialize a locator declaration.

        Args:
            testid: data-testid value (rung 1 — the target state)
            locator: LEGACY ONLY — never in new code (use css= / xpath=)
            description: Human-readable description for docs and the inventory
            fallback: LEGACY ONLY — dead code when testid is set; never in new code
            role: ARIA role (rung 2), optionally narrowed by `name`
            name: accessible name for `role` (only valid with role=)
            exact: exact match for `name` / `label` (Playwright default when None)
            label: label text of a form control (rung 3)
            css: stable, non-positional CSS selector (rung 4)
            xpath: non-positional, relative XPath (rung 5, declared last resort)
            suggested_testid: testid to add for this element — REQUIRED on
                every role/label/css/xpath declaration
        """
        self.testid = testid
        self.locator_selector = locator
        self.fallback_fn = fallback  # Legacy support
        self.description = description
        self.role = role
        self.name = name
        self.exact = exact
        self.label = label
        self.css = css
        self.xpath = xpath
        self.suggested_testid = suggested_testid
        self.attr_name = None
        self.kind = self._validate()

    def _validate(self) -> str:
        """Check the declaration against the locator policy; return its kind."""
        given = [k for k in LOCATOR_KINDS if getattr(self, k)]
        if len(given) > 1:
            raise ValueError(f"Pass exactly one locator kind, got {given}")
        if given and self.locator_selector:
            raise ValueError("locator= is legacy and cannot be combined with a locator kind")
        if (self.locator_selector or self.fallback_fn) and not self.allow_legacy:
            raise ValueError(f"{type(self).__name__} does not accept legacy locator= / fallback=")
        if self.name is not None and not self.role:
            raise ValueError("name= is only valid together with role=")
        if self.exact is not None and not (self.role or self.label):
            raise ValueError("exact= is only valid together with role= or label=")

        if self.xpath and (_XPATH_POSITIONAL_RE.search(self.xpath) or _XPATH_ABSOLUTE_RE.match(self.xpath)):
            raise ValueError(f"Positional or absolute XPath is forbidden: {self.xpath!r}")
        if self.css:
            if _CSS_POSITIONAL_RE.search(self.css):
                raise ValueError(f"Positional CSS is forbidden: {self.css!r}")
            if "data-testid" in self.css:
                raise ValueError(f"Use testid= instead of a data-testid CSS selector: {self.css!r}")
            if _ENGINE_PREFIX_RE.match(self.css):
                raise ValueError(f"Pass plain CSS (use xpath= / role= for other engines): {self.css!r}")

        if given:
            kind = given[0]
        elif self.locator_selector:
            kind = "locator"
        elif self.fallback_fn:
            kind = "fallback"
        else:
            raise ValueError("No locator provided — pass testid=, role=, label=, css= or xpath=")

        if kind == "testid" and self.suggested_testid:
            raise ValueError("suggested_testid= is only for non-testid declarations")
        if kind in LOCATOR_KINDS[1:] and not self.suggested_testid:
            raise ValueError(f"{kind}= declarations must carry suggested_testid= (the migration target)")
        if self.suggested_testid and not TESTID_NAME_RE.match(self.suggested_testid):
            raise ValueError(
                f"suggested_testid must be kebab-case {{section}}-{{element}}-{{type}}: {self.suggested_testid!r}"
            )
        return kind

    @property
    def is_testid(self) -> bool:
        """True when this declaration already resolves by data-testid."""
        return self.kind == "testid"

    def resolve(self, scope: Page | Locator, *args) -> Locator:
        """Build the Playwright locator inside `scope` (a Page or a parent Locator).

        Positional `args` fill `{}` placeholders in the selector strings
        (runtime-parameterized locators); test-generated data only.
        """

        def fmt(value: str | None) -> str | None:
            return value.format(*args) if (value is not None and args) else value

        if self.kind == "testid":
            return scope.get_by_test_id(fmt(self.testid))
        if self.kind == "role":
            kwargs = {}
            if self.name is not None:
                kwargs["name"] = fmt(self.name)
            if self.exact is not None:
                kwargs["exact"] = self.exact
            return scope.get_by_role(self.role, **kwargs)
        if self.kind == "label":
            kwargs = {} if self.exact is None else {"exact": self.exact}
            return scope.get_by_label(fmt(self.label), **kwargs)
        if self.kind == "css":
            return scope.locator(fmt(self.css))
        if self.kind == "xpath":
            return scope.locator(f"xpath={fmt(self.xpath)}")
        if self.kind == "locator":
            return scope.locator(fmt(self.locator_selector))
        # Legacy fallback support
        return self.fallback_fn(scope)


class LocatorDescriptor(LocatorSpec):
    """Descriptor for declaring page-level locators as class fields.

    Usage:
        class MyPage(BasePage):
            login_button = LocatorDescriptor(testid="login-button")
            save_button = LocatorDescriptor(
                role="button", name="Save", suggested_testid="agent-form-save-button"
            )
            name_input = LocatorDescriptor(label="Name", suggested_testid="agent-form-name-input")
    """

    def __set_name__(self, owner, name):
        """Called when descriptor is assigned to class attribute."""
        self.attr_name = name

    def __get__(self, instance, owner) -> Locator:
        """Return the locator for this element.

        Resolves by the declared kind; a legacy testid+fallback pair resolves by testid.
        """
        if instance is None:
            return self

        page: Page = instance.page
        return self.resolve(page)

    def __set__(self, instance, value):
        """Prevent assignment to descriptor."""
        raise AttributeError(f"Cannot set locator {self.attr_name}")


class OptionalLocatorDescriptor(LocatorDescriptor):
    """Locator descriptor that returns None instead of raising error if not found.

    Useful for elements that may or may not be present on the page.
    """

    def __get__(self, instance, owner) -> Locator | None:
        """Return locator or None if not found."""
        if instance is None:
            return self

        try:
            return super().__get__(instance, owner)
        except ValueError:
            return None


class ScopedLocator(LocatorSpec):
    """Class-level locator spec resolved inside a parent locator at call time.

    The non-testid counterpart of the UPPER_CASE `[data-testid="…"]` scoped /
    template string constants — keeps every handle declared at class level
    (and visible to the inventory) while it is resolved per row, per card, or
    with runtime data. Legacy locator= / fallback= are not accepted.

    Usage:
        class AgentsListPage(BasePage):
            CARD_MENU_BUTTON = ScopedLocator(
                role="button", name="More actions", suggested_testid="entity-card-menu-button"
            )
            TAG_OPTION = ScopedLocator(role="option", name="{}", suggested_testid="agent-tag-option-{}")

            def open_card_menu(self, card: Locator) -> None:
                self.CARD_MENU_BUTTON.within(card).click()
    """

    allow_legacy = False

    def __set_name__(self, owner, name):
        """Called when the spec is assigned to a class attribute."""
        self.attr_name = name

    def within(self, scope: Page | Locator, *args) -> Locator:
        """Resolve inside `scope`, filling `{}` placeholders from `args`."""
        return self.resolve(scope, *args)
