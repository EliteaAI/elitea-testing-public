"""Regression coverage for the ELITEA-3370 hardening-gate finding (2026-10-19,
batch ``builder-modules-chat-2459``): a NEW full-screen platform release-notes
modal (``data-testid="platform-banner-center"``, "Announcing ELITEA 2.0.7!",
dismiss control ``data-testid="platform-banner-close"`` — a "Got it" button
with no ``aria-label``) started appearing on a cold ``/chat`` load this
session. The pre-existing ``BasePage.dismiss_banner_if_present()`` /
``_click_banner_close_button()`` only query
``button[aria-label="close"]`` inside a high-z-index ancestor, so this
modal's dismiss control was never found: the dialog stayed mounted and
intercepted the very next click underneath it — in practice
``ChatPage.open_internal_tools_menu()``'s ``plus_menu_button.click()`` —
producing a deterministic
``Locator.click: Timeout 10000ms exceeded ... <div
data-testid="platform-banner-center"> subtree intercepts pointer events``
on every one of 3 independent gate runs.

The fix is at the shared level (``BasePage``, per the diagnosis): a new
``dismiss_platform_release_banner_if_present()`` helper on the new
``PLATFORM_RELEASE_BANNER_CLOSE_BUTTON`` testid rung, called from
``BasePage.dismiss_popups()`` (ahead of the existing banner/NPS dismissals)
AND from ``ChatPage.open_internal_tools_menu()`` itself (belt-and-suspenders
for callers that reach the menu without going through ``navigate()``'s
``dismiss_popups()`` call — e.g. already on ``/chat``, or a raw
``page.goto()``). These tests pin BOTH call sites and the ORDER of calls —
dismissal must happen strictly before the click/evaluate it protects, which
is the entire point of the fix; a fix that exists but runs too late (or not
at all on one of the two call sites) would reproduce the exact same gate
failure.

**Fidelity note** (``.agents/testing.md`` § Fidelity policy): these are
framework unit tests pinning the *contract* of a shared page-object helper
(call order, tolerate-absence behaviour) — the same seam
``test_banner_dismiss_navigation_race_tolerance.py`` already pins for the
sibling ``dismiss_banner_if_present()`` helper. No product observable is
substituted; the fake ``Page``/locator stand-ins exist only to make the
control flow deterministic and fast, exactly as that file's ``_StubPage``
does for its own helper.
"""

from pages.base_page import BasePage
from pages.chat_page import ChatPage
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


class _RecordingLocator:
    """Minimal Locator stand-in that appends every call it receives, tagged
    by *name*, to a shared *order* list — the thing these tests actually
    assert on. ``wait_for`` raises ``wait_for_exception`` (if set) instead of
    recording+returning, so a test can simulate "the element isn't there".
    """

    def __init__(self, name: str, order: list[str]):
        self.name = name
        self.order = order
        self.wait_for_exception: BaseException | None = None
        self._visible = True

    def is_visible(self) -> bool:
        return self._visible

    def wait_for(self, state: str | None = None, timeout: int | None = None) -> None:
        self.order.append(f"wait_for:{self.name}")
        if self.wait_for_exception is not None:
            raise self.wait_for_exception

    def click(self, *args, **kwargs) -> None:
        self.order.append(f"click:{self.name}")

    def hover(self) -> None:
        self.order.append(f"hover:{self.name}")

    @property
    def first(self) -> "_RecordingLocator":
        return self


class _FakePage:
    """Stand-in for Playwright's ``Page`` — hands out one ``_RecordingLocator``
    per distinct ``get_by_test_id`` / ``locator`` argument (memoized), so
    locators for different elements never collide, and every call any of
    them receives lands in the single shared *order* list this test reads.
    """

    def __init__(self):
        self.order: list[str] = []
        self._locators: dict[str, _RecordingLocator] = {}
        self.evaluate_calls = 0
        self.evaluate_return = False

    def _locator_for(self, key: str) -> _RecordingLocator:
        if key not in self._locators:
            self._locators[key] = _RecordingLocator(key, self.order)
        return self._locators[key]

    def get_by_test_id(self, testid: str) -> _RecordingLocator:
        return self._locator_for(f"testid:{testid}")

    def locator(self, selector: str) -> _RecordingLocator:
        return self._locator_for(f"css:{selector}")

    def wait_for_timeout(self, milliseconds: int) -> None:
        pass

    def evaluate(self, script: str, *args, **kwargs):
        self.evaluate_calls += 1
        self.order.append("evaluate:banner_script")
        return self.evaluate_return


# ---------------------------------------------------------------------------
# dismiss_platform_release_banner_if_present() in isolation
# ---------------------------------------------------------------------------


def test_dismiss_platform_release_banner_when_present():
    """The modal IS showing: the 'Got it' button is clicked and the
    post-dismiss settle wait runs — mirrors dismiss_banner_if_present's own
    happy-path contract."""
    page = _FakePage()
    base = BasePage(page)

    base.dismiss_platform_release_banner_if_present()

    button = page.get_by_test_id("platform-banner-close")
    assert page.order == [
        f"wait_for:{button.name}",
        f"click:{button.name}",
    ]


def test_dismiss_platform_release_banner_when_absent():
    """No modal this session: wait_for times out, nothing is clicked, and —
    critically — the timeout is swallowed quietly. This is best-effort
    transit machinery (same spirit as dismiss_banner_if_present): it must
    NEVER raise just because the thing it's looking for isn't there."""
    page = _FakePage()
    button = page.get_by_test_id("platform-banner-close")
    button.wait_for_exception = PlaywrightTimeoutError("Timeout 2000ms exceeded")
    base = BasePage(page)

    base.dismiss_platform_release_banner_if_present()  # must not raise

    assert not any(entry.startswith("click:") for entry in page.order), (
        "nothing should be clicked when the modal never appears"
    )


# ---------------------------------------------------------------------------
# The actual regression: ordering at both call sites
# ---------------------------------------------------------------------------


def test_open_internal_tools_menu_dismisses_release_banner_before_plus_menu_click():
    """Pins the exact gate failure (2026-10-19): on a cold chat load, the
    release-notes modal must be dismissed BEFORE ``plus_menu_button`` is
    clicked — not after, not never. Before this fix there was no dismissal
    call here at all, so the plus-menu click raced (and lost to) the modal's
    intercepting subtree on every gate run."""
    page = _FakePage()
    chat = ChatPage(page)

    chat.open_internal_tools_menu()

    order = page.order
    dismiss_click = "click:testid:platform-banner-close"
    menu_click = "click:testid:plus-menu-button"
    assert dismiss_click in order, "the release-notes banner must be dismissed"
    assert menu_click in order, "the plus menu must still be clicked"
    assert order.index(dismiss_click) < order.index(menu_click), (
        "banner dismissal must happen strictly BEFORE the plus-menu click it "
        "protects — this is the ELITEA-3370 gate failure's exact ordering"
    )


def test_open_internal_tools_menu_proceeds_normally_when_no_banner_shown():
    """Second (or later) navigation this session, or a UI version that never
    shows the modal: the dismissal attempt must not block or break the rest
    of the flow — the plus-menu click still happens."""
    page = _FakePage()
    page.get_by_test_id("platform-banner-close").wait_for_exception = (
        PlaywrightTimeoutError("Timeout 2000ms exceeded")
    )
    chat = ChatPage(page)

    chat.open_internal_tools_menu()  # must not raise

    assert "click:testid:platform-banner-close" not in page.order
    assert "click:testid:plus-menu-button" in page.order


def test_dismiss_popups_dismisses_release_banner_before_the_other_two():
    """Pins the ``BasePage.dismiss_popups()`` ordering: the release-notes
    modal is a full-screen overlay that sits on top of (and, once closed,
    can itself reveal) the banner/NPS-survey overlays the other two helpers
    target, so it must run FIRST — otherwise those two still race it,
    identically to the original gate failure."""
    page = _FakePage()
    page.get_by_test_id("platform-banner-close").wait_for_exception = (
        PlaywrightTimeoutError("Timeout 2000ms exceeded")
    )
    page.locator('button:has-text("Not now")').wait_for_exception = (
        PlaywrightTimeoutError("Timeout 1000ms exceeded")
    )
    base = BasePage(page)

    base.dismiss_popups()

    order = page.order
    platform_attempt = "wait_for:testid:platform-banner-close"
    legacy_banner_attempt = "evaluate:banner_script"
    nps_attempt = 'wait_for:css:button:has-text("Not now")'
    assert order.index(platform_attempt) < order.index(legacy_banner_attempt)
    assert order.index(legacy_banner_attempt) < order.index(nps_attempt)
