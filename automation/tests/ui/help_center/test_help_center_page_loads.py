"""UI test for Help Center — page loads successfully via the sidebar icon
(ELITEA-2219).

Covers the *entry path* and *whole-page composition* no other help-center spec
asserts: the three merged siblings
(``test_help_center_resource_links.py``, ``test_help_center_sidebar_tour.py``,
``test_help_center_version_info.py``) all reach the page by URL via
``HelpCenterPage.navigate()``. This one clicks the sidebar's Help Center ('?')
control the way a user does, then verifies the header, the intro block, all five
resource cards (icon / title / description / links), and the version label + info
icon in the top-right.

AFS: test-specs/help-center/l3_help-center-page-loads-via-sidebar-icon_ELITEA-2219.md

Fidelity: nothing is substituted. Every asserted value is read off the real
rendered page after a real click, with the DEV backend producing the card and
version data — no ``page.route``, no ``route.fulfill``, no ``page.evaluate``
state injection, no API seeding. The case is entirely read-only (no entity is
created, edited or deleted), so there is no teardown and no shared state to
leak.

Transit: Step 1 navigates to ``/agents/all`` for one reason only — to be on a
page OTHER than ``/help-center``, because ``ResourcesButton`` early-returns
(``if (isOnResources) return;``) when it is already there, which would make the
case's own click a silent no-op and leave every later step asserting a page it
never actually opened. It is transit in the strict sense: it reaches the step
under test and produces NONE of the case's observables, every one of which is
read off the real Help Center page after the real click. A read-only list page
is chosen over ``/chat`` deliberately — the agents list mutates nothing and
holds no WebSocket, whereas ``/chat`` restores the shared test user's most
recent conversation, and that restore path is the documented origin of
unrelated background 4xx console errors (``.agents/testing.md``, ELITEA-2234)
that this spec's console axis would red on for no coverage benefit. Measured
locally 2026-09-30: ``/agents/all`` 2153 requests / 3.3s to settle vs ``/chat``
2521 / 4.7s.

Assertion choices that are deliberate, not shortcuts:

* **Version string by REGEX, not literal.** The live value is
  ``Version: 2.0.3 (28-May-2026)``, which is backend deploy metadata
  (``resources_information_version`` / ``_upgrade_date``) and legitimately
  changes on the next release. Pinning it would false-red on a routine deploy —
  the same reasoning already applied on this surface by
  ``test_help_center_version_info.py``.
* **Card count asserted as exactly 5.** TMS case ELITEA-2219 step 6 says "four
  resource cards" and then names five; the live contract is FIVE
  (``RESOURCE_CARD_CONFIGS`` has 5 entries). Pre-tracked as case-text drift
  ``question`` #998 — NOT re-filed. The count assertion guards the ambiguity in
  BOTH directions: a dropped card or a sixth one appearing would each pass a
  per-card-visible-only check.
* **Card link data asserted STRUCTURALLY, not as 19 frozen literals.** All 19
  links are backend-CMS-served and their titles/URLs legitimately change per
  release (the digest already records the Release Notes list shifting and
  ``tutorials-more`` re-pointing). So each card is asserted to have >= 1 link,
  every link to carry a non-empty ``href`` and ``target="_blank"``, plus the two
  tour links the case names *literally* because the case names them. Step 7
  never CLICKS a link, so open defect #1492 (the Release Notes "latest" target
  404s) cannot turn this spec red — that target's reachability is
  ELITEA-2221's scope.
* **The Interactive Tours link COUNT is deliberately NOT frozen.** TMS step 7
  reads "Verify all the cards (e.g.INTERACTIVE TOURS) are visible with their
  links: (e.g. 'Sidebar Interactive Tour' and 'Chat Interactive Tour')" — both
  ``e.g.``s are exemplary, so the case's contract is "every card is visible with
  its links", worked through one example. It never enumerates that card's link
  set as exactly two, so an exact-count assertion would be an invariant this
  spec invented rather than the case's. Nothing is lost by dropping it: a link
  being REMOVED is still caught by the two literal named-link assertions, and a
  named link rendering twice is caught by Playwright strict mode on those same
  locators — the exact count's only unique catch is a link being ADDED, which on
  a CMS-served list is a content change, not a defect. Freezing it would also
  contradict this spec's own refusal to freeze the other 19 links, which arrive
  in the very same ``useGetResourcesConfigQuery`` response.
* **Card titles compared in SOURCE casing** ('Documentation', not
  'DOCUMENTATION'). Playwright's ``to_have_text`` compares ``textContent``,
  while the card title carries CSS ``text-transform: uppercase``; the case
  text's uppercase spelling is that rendered form. Verified live 2026-09-30:
  ``textContent`` 'Documentation' vs ``innerText`` 'DOCUMENTATION'.
* **Version/icon position asserted RELATIONALLY.** The case says "top right
  corner" and "i in circle icon near it"; bare presence would pass even if the
  layout collapsed the label to the left, so the label's ``x`` must exceed the
  top-left header's and the icon's must exceed the label's.
* **Tooltip contents are NOT touched.** Opening the version tooltip and the
  copy-to-clipboard flow are ELITEA-2225's scope, already merged. This case
  asserts the icon's presence only.

Markers:
    - ui: requires browser
    - help_center: Help Center tests
    - p3: priority (case priority: medium)
    - regression
    - new: not yet validated on deployed envs
"""

import logging
import re

import allure
import pytest
from pages.help_center_page import HelpCenterPage
from pages.sidebar_header_page import SidebarHeaderPage
from playwright.sync_api import expect
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.ui,
    pytest.mark.help_center,
    pytest.mark.p3,
    pytest.mark.regression,
    pytest.mark.new,
]

# Transit target for Step 1 — rationale in the module docstring's Transit note.
# Every requirement this target has to meet, and how each was established:
#   * read-only, mutates nothing        — a list page only reads
#   * no persistent WebSocket           — `base_page.py` names Chat and Skills as
#                                         the WebSocket pages, so /skills/all is out
#   * not /help-center                  — so `useMatch({path: HelpCenter})` leaves
#                                         `isOnResources` null and the click really
#                                         navigates rather than early-returning
#   * the '?' control renders there     — route-INDEPENDENT: `SidebarBody` mounts
#                                         `ResourcesButton` inside the app-shell
#                                         `Drawer`, gated only on `!sideBarCollapsed`
#                                         (expanded is the default and never persists)
# Confirmed live on this exact target 2026-09-30: control visible, count 1, the
# click lands on /help-center, zero console errors.
TRANSIT_PATH = "/agents/all"

EXPECTED_PAGE_HEADER = "Help Center"
EXPECTED_INTRO_TITLE = "Explore Help Center"
EXPECTED_INTRO_DESCRIPTION = "Guides, documentation, and release notes to support your work."

# (category, title, description) — `category` is the card's own `testidCategory`
# value in `ResourcesPage.jsx`; title/description are its `defaultTitle` /
# `defaultDescription`, which the backend config currently does not override.
# Titles are SOURCE casing — see the module docstring on text-transform.
RESOURCE_CARDS = [
    ("documentation", "Documentation", "API reference, guides, and platform concepts"),
    ("release-notes", "Release Notes", "Product updates, improvements, and fixes"),
    ("video-library", "Video Library", "Product walkthroughs and recorded sessions"),
    ("tutorials", "Tutorials", "Step-by-step guides and use cases"),
    ("interactive-tours", "Interactive Tours", "Guided tours to explore key features and workflows"),
]

EXPECTED_CARD_COUNT = 5

# The only link literals this spec freezes: TMS step 7 names these two by title
# as its worked example ("e.g. INTERACTIVE TOURS ... 'Sidebar Interactive Tour'
# and 'Chat Interactive Tour'"), so they are case contract rather than CMS data.
INTERACTIVE_TOURS_CATEGORY = "interactive-tours"
INTERACTIVE_TOURS_LINKS = [
    ("sidebar-interactive-tour", "Sidebar Interactive Tour"),
    ("chat-interactive-tour", "Chat Interactive Tour"),
]

# `Version: X.Y.Z (DD-Mon-YYYY)` — the case's literal format, asserted as shape
# because the values are live deploy metadata (see module docstring). The day is
# `\d{1,2}`, NOT `\d{2}`: `resources_information_upgrade_date` is a free-text CMS
# string and only ONE sample has ever been observed (`28-May-2026`), so a release
# on day 1-9 emitted unpadded as `5-Jun-2026` must not red the spec. Shape,
# field order and separators are still asserted in full.
VERSION_LABEL_PATTERN = re.compile(r"^Version: \d+\.\d+\.\d+ \(\d{1,2}-[A-Za-z]{3}-\d{4}\)$")

# Any non-empty href. The case verifies links are DISPLAYED, not that their
# targets resolve — so this checks the link is a real anchor with a destination,
# never that the destination loads.
NON_EMPTY_HREF = re.compile(r"\S")


class TestHelpCenterPageLoads:
    """ELITEA-2219: the Help Center page loads successfully via the sidebar icon."""

    def test_help_center_page_loads_via_sidebar_icon(self, page):
        # Bound before the first navigation so nothing is missed. URL-bearing
        # capture per .agents/testing.md — the URL-less `page.on("console", ...)`
        # shape leaves the recurring background-resource noise class anonymous.
        console_errors = collect_console_errors(page)

        with allure.step(
            f"Step 1 — From {TRANSIT_PATH} (a non-Help-Center page), locate the '?' Help Center "
            "control at the bottom of the left sidebar"
        ):
            # SidebarHeaderPage is the existing app-shell sidebar object and does
            # not override `navigate`, so it is the light transit vehicle here;
            # the control itself is inherited from BasePage, which owns the
            # navigation sidebar's chrome (sidebar_settings_button /
            # sidebar_agent_hub_button are its footer siblings).
            sidebar = SidebarHeaderPage(page)
            sidebar.navigate(TRANSIT_PATH)
            expect(sidebar.sidebar_help_center_button).to_be_visible()
            # Exactly one control bears this testid at runtime, even though
            # `ResourcesButton` declares it on both of its mutually-exclusive
            # returns (build-time `VITE_ELITEA_ASSISTANT` picks one; declared
            # canon gap #2385). A count of 2 would mean that invariant broke.
            expect(sidebar.sidebar_help_center_button).to_have_count(1)

        with allure.step("Step 2 — Click the '?' icon"):
            help_center = HelpCenterPage(page)
            help_center.open_via_sidebar()

        with allure.step("Step 3 — Verify the Help Center page opens"):
            # Path, not full URL: APP_PREFIX is "" on localhost and "/app" on
            # deployed envs, so a full-URL assertion would false-red in CI.
            expect(page).to_have_url(re.compile(r"/help-center$"))
            expect(help_center.page_header).to_be_visible()

        with allure.step(f"Step 4 — Verify the page title '{EXPECTED_PAGE_HEADER}' in the top-left header"):
            expect(help_center.page_header).to_have_text(EXPECTED_PAGE_HEADER)

        with allure.step(
            f"Step 5 — Verify the intro subtitle '{EXPECTED_INTRO_TITLE}' and its description"
        ):
            expect(help_center.intro_title).to_be_visible()
            expect(help_center.intro_title).to_have_text(EXPECTED_INTRO_TITLE)
            expect(help_center.intro_description).to_be_visible()
            expect(help_center.intro_description).to_have_text(EXPECTED_INTRO_DESCRIPTION)

        with allure.step(
            f"Step 6 — Verify all {EXPECTED_CARD_COUNT} resource cards are visible with their titles "
            "(case text says 'four' then names five; the live contract is five — pre-tracked "
            "case-text drift #998)"
        ):
            for category, title, _ in RESOURCE_CARDS:
                expect(help_center.card(category)).to_be_visible()
                expect(help_center.card_title(category)).to_have_text(title)
            # Guards #998 in both directions — a dropped card or a sixth one.
            expect(help_center.card_titles()).to_have_count(EXPECTED_CARD_COUNT)

        with allure.step(
            "Step 7 — Verify each card displays its links: >= 1 link per card, each with a "
            "non-empty href and target='_blank', plus the two tour links the case names"
        ):
            # Link data is backend-served and renders only in ResourceCard's
            # `!isConfigLoading && hasLinks` branch. The card TITLE is not a valid
            # gate for it — the title falls back to a hardcoded default and paints
            # while 16 skeletons are still on screen (measured live), so reading a
            # link count before this wait is a one-shot zero.
            help_center.wait_for_resource_links_loaded()

            for category, title, _ in RESOURCE_CARDS:
                links = help_center.card_links(category)
                link_count = links.count()
                assert link_count >= 1, (
                    f"Expected the '{title}' card to display at least one link, got {link_count}"
                )
                for index in range(link_count):
                    link = links.nth(index)
                    expect(link).to_be_visible()
                    # A link configured without a URL degrades silently to a plain
                    # "<title> (undefined)" <Typography> instead of an <a>
                    # (ResourcesPage.jsx), which a text-only check would not catch.
                    expect(link).to_have_attribute("href", NON_EMPTY_HREF)
                    expect(link).to_have_attribute("target", "_blank")

            # Both named links are asserted LITERALLY because the case names
            # them; the card's link COUNT is deliberately not frozen — TMS step 7
            # names them with "e.g.", as an example rather than an enumeration.
            # See the module docstring for what that does and does not give up.
            for slug, link_title in INTERACTIVE_TOURS_LINKS:
                # Scoped to the Interactive Tours card, so this is containment
                # rather than page-wide presence.
                named_link = help_center.card_link(INTERACTIVE_TOURS_CATEGORY, slug)
                expect(named_link).to_be_visible()
                expect(named_link).to_have_text(link_title)

        with allure.step("Step 8 — Verify each card shows its icon, title, and subtitle description"):
            for category, title, description in RESOURCE_CARDS:
                expect(help_center.card_icon(category)).to_be_visible()
                expect(help_center.card_title(category)).to_have_text(title)
                expect(help_center.card_description(category)).to_have_text(description)

        with allure.step(
            "Step 9 — Verify the application version 'Version: X.X.X (DD-Mon-YYYY)' in the top-right "
            "corner with the 'i' info icon near it (presence + position only — tooltip contents and "
            "copy-to-clipboard are ELITEA-2225's scope)"
        ):
            expect(help_center.version_label).to_be_visible()
            expect(help_center.version_label).to_have_text(VERSION_LABEL_PATTERN)
            expect(help_center.version_info_icon).to_be_visible()

            # "top right" / "near it" are relationships, not coordinates: assert
            # the ordering against the top-left header rather than pinning pixels,
            # so the check survives any viewport but still fails if the layout
            # collapses the label leftward.
            header_box = help_center.page_header.bounding_box()
            label_box = help_center.version_label.bounding_box()
            icon_box = help_center.version_info_icon.bounding_box()
            assert header_box and label_box and icon_box, (
                "Expected the header, version label and info icon all to have a bounding box "
                f"(got header={header_box}, label={label_box}, icon={icon_box})"
            )
            assert label_box["x"] > header_box["x"], (
                "Expected the version label to sit to the RIGHT of the top-left page title "
                f"(label x={label_box['x']}, header x={header_box['x']})"
            )
            assert icon_box["x"] > label_box["x"], (
                "Expected the 'i' info icon to sit immediately to the RIGHT of the version label "
                f"(icon x={icon_box['x']}, label x={label_box['x']})"
            )

        with allure.step(
            "Axis — No console errors across the whole flow (analyst addition: a clean baseline was "
            "observed over four independent live runs, so there is a real invariant to guard)"
        ):
            assert not console_errors, f"Unexpected console errors: {console_errors}"
