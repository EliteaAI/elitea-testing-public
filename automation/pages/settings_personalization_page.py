"""Settings personalization-family page object.

The TMS cases in this family (ELITEA-2371/2372/2373/2380/2387) all describe a
single ``Settings -> Personalization`` page. **There is no such page** --
``/settings/personalization`` renders the app's global "Page not found" view.
The sections those cases name are distributed across three real routes, and
this page object models exactly that distribution:

===============================  ============================================
Route                            Sections modelled here
===============================  ============================================
``/settings/preferences``        ``GENERAL``, ``VOICE PERSONALIZATION``,
                                 ``SOUND NOTIFICATIONS``
``/settings/memory``             ``CONTEXT MANAGEMENT``
``/settings/ai-personality``     ``PERSONA MANAGEMENT`` (Default persona,
                                 User instructions)
===============================  ============================================

Clarification for the drift: EliteaAI/elitea-testing-public#1960 (siblings
#1238, #1772).

Scope split against the neighbouring page objects
-------------------------------------------------
``UserProfileSettingsPage`` owns the *controls inside* Context Management and
Voice Personalization (toggles, numeric fields, voice/speed/volume). This class
owns the **accordion chrome** of those same sections -- wrapper / clickable
header / content -- plus the AI Personality persona controls, which nothing
modelled before. Nothing is duplicated: the two page objects address different
elements of the same routes, and this one never re-declares a control the other
already exposes (``context-management-toggle`` is the single exception, and it
is used here purely as Context Management's *content* visibility probe).

Drawer + content-pane fields are declared here rather than cross-imported from
``SettingsProfilePage``, matching the convention the existing
settings/analytics/admin page objects already follow.

Locator provenance
------------------
Pre-existing on ``automation/testids``: ``settings-drawer``,
``settings-content``, ``settings-nav-item-{tabId}`` (EliteaAI/EliteaUI@e1e031a1),
``voice-personalization-section``, ``voice-preview-button``,
``context-management-section``, ``context-management-toggle``,
``select-option-{value}``.
Added for this case set (EliteaAI/EliteaUI@fa505e37, ``automation/testids``;
not yet on ``main``): ``preferences-general-section(-header)``,
``preferences-general-content``, ``sound-notifications-section(-header)``,
``sound-notifications-content``, ``voice-personalization-section-header``,
``context-management-section-header``, ``ai-personality-persona-section``,
``ai-personality-persona-select`` (+ the ``-combobox`` element ``SingleSelect``
derives from it) and ``ai-personality-user-instructions-textarea``.
Added for the ELITEA-2385/2386 controls (EliteaAI/EliteaUI@2d5f38d8 and
EliteaAI/EliteaUI@e087c0df, ``automation/testids``; not yet on ``main``):
``voice-personalization-voice-select`` (+ its derived ``-combobox``),
``voice-personalization-{speed,volume}-slider(-input|-thumb)``,
``sound-notifications-toggle(-input)``,
``sound-notifications-volume-slider(-input|-thumb)`` and
``sound-notifications-preview-button``.

.. note::
   ``BasicAccordion`` hardcodes ``aria-controls="panel-content-${index}"`` per
   *item*, and every section above is a one-item accordion -- so all of them
   share ``aria-controls="panel-content-0"``. Never key a locator on it; the
   per-item ``testId`` on the summary is the handle, and ``aria-expanded`` on
   that same element is the state.
"""

import logging
from typing import NamedTuple

from playwright.sync_api import Locator, Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.settings_personalization")

APP_ROOT_PATH = "/"

PREFERENCES_PATH = "/settings/preferences"
MEMORY_PATH = "/settings/memory"
AI_PERSONALITY_PATH = "/settings/ai-personality"
NOTIFICATIONS_PATH = "/settings/notifications"

#: Autosave endpoint every personalization control writes through. Used by
#: specs as the wait signal (``page.expect_response``) instead of a sleep.
AUTHOR_SETTINGS_ENDPOINT = "/api/v2/social/author/"


class AccordionSection(NamedTuple):
    """One collapsible settings section, addressed by its three testids.

    ``header`` is the clickable summary that carries ``aria-expanded``;
    ``content`` is an element inside the collapsible body, used as the
    "is the content hidden?" observable.
    """

    name: str
    wrapper: Locator
    header: Locator
    content: Locator


class SettingsPersonalizationPage(BasePage):
    """Accordion chrome + persona controls of the personalization family."""

    # ------------------------------------------------------------------
    # Settings shell
    # ------------------------------------------------------------------

    settings_drawer = LocatorDescriptor(
        testid="settings-drawer",
        description="Settings left drawer root (header + PROJECT/PERSONAL menu)",
    )

    settings_content = LocatorDescriptor(
        testid="settings-content",
        description="Settings content pane. A bare `main` selector matches TWO "
        "elements on a settings route -- the app shell's and this one -- so the "
        "testid is required, not a convenience.",
    )

    # Dynamic testid -- one per `SETTINGS_TABS_CONFIG` tab. Class-level per
    # `.agents/testing.md` § Locator policy (inline `get_by_test_id(f"...")` is
    # not the compliant shape).
    SETTINGS_NAV_ITEM = '[data-testid="settings-nav-item-{}"]'

    # ------------------------------------------------------------------
    # /settings/preferences -- GENERAL
    # ------------------------------------------------------------------

    preferences_general_section = LocatorDescriptor(
        testid="preferences-general-section",
        description="GENERAL accordion wrapper on /settings/preferences",
    )

    preferences_general_header = LocatorDescriptor(
        testid="preferences-general-section-header",
        description="Clickable GENERAL accordion summary -- the whole header row "
        "is the click target (the chevron sits inside it) and it carries "
        "`aria-expanded`",
    )

    preferences_general_content = LocatorDescriptor(
        testid="preferences-general-content",
        description="GENERAL accordion body (Theme). Collapse HIDES it "
        "(`visibility: hidden`) rather than unmounting it -- assert "
        "`not_to_be_visible()`, never `to_have_count(0)`.",
    )

    # ------------------------------------------------------------------
    # /settings/preferences -- VOICE PERSONALIZATION
    # ------------------------------------------------------------------

    voice_personalization_section = LocatorDescriptor(
        testid="voice-personalization-section",
        description="VOICE PERSONALIZATION accordion wrapper on /settings/preferences",
    )

    voice_personalization_header = LocatorDescriptor(
        testid="voice-personalization-section-header",
        description="Clickable VOICE PERSONALIZATION accordion summary (carries "
        "`aria-expanded`)",
    )

    voice_preview_button = LocatorDescriptor(
        testid="voice-preview-button",
        description="'Preview Voice' button inside the VOICE PERSONALIZATION body "
        "-- used here as that section's content-visibility observable",
    )

    # ------------------------------------------------------------------
    # /settings/preferences -- SOUND NOTIFICATIONS
    # ------------------------------------------------------------------

    sound_notifications_section = LocatorDescriptor(
        testid="sound-notifications-section",
        description="SOUND NOTIFICATIONS accordion wrapper on /settings/preferences",
    )

    sound_notifications_header = LocatorDescriptor(
        testid="sound-notifications-section-header",
        description="Clickable SOUND NOTIFICATIONS accordion summary (carries "
        "`aria-expanded`)",
    )

    sound_notifications_content = LocatorDescriptor(
        testid="sound-notifications-content",
        description="SOUND NOTIFICATIONS accordion body (toggle + volume slider)",
    )

    # ------------------------------------------------------------------
    # /settings/preferences -- VOICE PERSONALIZATION controls
    # ------------------------------------------------------------------

    voice_select_combobox = LocatorDescriptor(
        testid="voice-personalization-voice-select-combobox",
        description="Display element of the 'Voice' select -- reads the current "
        "voice and opens the option list on click. `SingleSelect` derives this "
        "testid from the wrapper's own (`${dataTestId}-combobox`). The wrapper "
        "itself (`voice-personalization-voice-select`) is never addressed "
        "directly: everything a test does happens on the display element or the "
        "option rows.",
    )

    voice_speed_slider = LocatorDescriptor(
        testid="voice-personalization-speed-slider",
        description="'Speed' Slider root. Its own rendered text IS the mark-label "
        "row (`0.5x 1x 1.5x 2x`), and its bounding box is what a drag target x is "
        "computed against.",
    )

    voice_speed_slider_input = LocatorDescriptor(
        testid="voice-personalization-speed-slider-input",
        description="Hidden `<input type=range>` of the 'Speed' slider -- carries "
        "`min`/`max`/`step`, `value` and `aria-valuenow`.",
    )

    voice_speed_slider_thumb = LocatorDescriptor(
        testid="voice-personalization-speed-slider-thumb",
        description="Draggable thumb of the 'Speed' slider (grab point of a drag)",
    )

    voice_volume_slider = LocatorDescriptor(
        testid="voice-personalization-volume-slider",
        description="'Volume' Slider root of VOICE PERSONALIZATION (marks "
        "`0% 50% 100%`)",
    )

    voice_volume_slider_input = LocatorDescriptor(
        testid="voice-personalization-volume-slider-input",
        description="Hidden `<input type=range>` of the voice 'Volume' slider",
    )

    voice_volume_slider_thumb = LocatorDescriptor(
        testid="voice-personalization-volume-slider-thumb",
        description="Draggable thumb of the voice 'Volume' slider",
    )

    # ------------------------------------------------------------------
    # /settings/preferences -- SOUND NOTIFICATIONS controls
    # ------------------------------------------------------------------

    sound_notifications_toggle = LocatorDescriptor(
        testid="sound-notifications-toggle",
        description="'Play sound when tasks complete' switch -- the MUI "
        "`SwitchBase` **span**. This is the CLICK target (what a user hits); the "
        "checked state lives on the nested input, hence the separate "
        "`sound-notifications-toggle-input` handle.",
    )

    sound_notifications_toggle_input = LocatorDescriptor(
        testid="sound-notifications-toggle-input",
        description="Hidden `<input type=checkbox role=switch>` of the sound "
        "toggle -- the only element `to_be_checked()` accepts. Wired through "
        "`slotProps.input`: MUI v7's `Switch` ignores `inputProps` (its own "
        "slotProps merge overrides it).",
    )

    sound_volume_slider = LocatorDescriptor(
        testid="sound-notifications-volume-slider",
        description="'Volume' Slider root of SOUND NOTIFICATIONS. Conditionally "
        "UNMOUNTED while the toggle is off (`{config.enabled && ...}`) -- assert "
        "`to_have_count(0)`, never `not_to_be_visible()`.",
    )

    sound_volume_slider_input = LocatorDescriptor(
        testid="sound-notifications-volume-slider-input",
        description="Hidden `<input type=range>` of the sound 'Volume' slider",
    )

    sound_volume_slider_thumb = LocatorDescriptor(
        testid="sound-notifications-volume-slider-thumb",
        description="Draggable thumb of the sound 'Volume' slider",
    )

    sound_preview_button = LocatorDescriptor(
        testid="sound-notifications-preview-button",
        description="'Preview Sound' button. Unmounted by the same "
        "`config.enabled &&` guard as the volume slider.",
    )

    # ------------------------------------------------------------------
    # /settings/memory -- CONTEXT MANAGEMENT
    # ------------------------------------------------------------------

    context_management_section = LocatorDescriptor(
        testid="context-management-section",
        description="CONTEXT MANAGEMENT accordion wrapper on /settings/memory",
    )

    context_management_header = LocatorDescriptor(
        testid="context-management-section-header",
        description="Clickable CONTEXT MANAGEMENT accordion summary (carries "
        "`aria-expanded`)",
    )

    context_management_toggle = LocatorDescriptor(
        testid="context-management-toggle",
        description="'Enable context management for new conversations' toggle. "
        "Used here only as CONTEXT MANAGEMENT's content-visibility observable: "
        "it is the one child of that body which is ALWAYS mounted -- the numeric "
        "fields below it are conditionally unmounted when the toggle is off "
        "(`UserProfileSettingsPage` documents that mechanism), so they cannot "
        "serve as a stable collapse probe.",
    )

    # ------------------------------------------------------------------
    # /settings/ai-personality -- PERSONA MANAGEMENT
    # ------------------------------------------------------------------

    persona_section = LocatorDescriptor(
        testid="ai-personality-persona-section",
        description="PERSONA MANAGEMENT accordion wrapper on /settings/ai-personality",
    )

    persona_select = LocatorDescriptor(
        testid="ai-personality-persona-select",
        description="'Default persona' SingleSelect wrapper",
    )

    persona_select_combobox = LocatorDescriptor(
        testid="ai-personality-persona-select-combobox",
        description="Display element of the 'Default persona' select -- reads the "
        "current value and opens the option list on click. `SingleSelect` derives "
        "this testid from the wrapper's own (`${dataTestId}-combobox`).",
    )

    user_instructions_textarea = LocatorDescriptor(
        testid="ai-personality-user-instructions-textarea",
        description="'User instructions' textarea. Its placeholder is per-persona, "
        "so it doubles as a cheap signal that a persona change reached Formik state.",
    )

    #: Option rows of any `SingleSelect` -- shared generic testid emitted by
    #: `SingleSelect.jsx` as `select-option-{value}`. Dynamic pattern, declared
    #: at class level per `.agents/testing.md` § Locator policy.
    SELECT_OPTION = '[data-testid="select-option-{}"]'

    #: Collection handle for **all** option rows of an open `SingleSelect`.
    #: Needed because the count/order assertions address a set, not one row.
    #: Two details are load-bearing:
    #:   * the prefix form is still a testid-keyed selector (`SELECT_OPTION`
    #:     above is its single-row sibling) -- never `li[role="option"]`;
    #:   * `[data-selected]` is NOT decoration. `SingleSelectMenuItem` renders a
    #:     nested `select-option-selected-icon` inside the *selected* row, which
    #:     a bare `select-option-` prefix would count as an eighth option. Only
    #:     the MenuItem rows carry `data-selected`, so the attribute is what
    #:     makes the collection exactly "the option rows".
    SELECT_OPTION_ANY = '[data-testid^="select-option-"][data-selected]'

    #: MUI's "grayed out" marker class. A class MUI adds at render time cannot
    #: carry a testid -- see :meth:`persona_section_disabled_elements` for the
    #: #579 exception discipline this is used under.
    MUI_DISABLED_MARKER = ".Mui-disabled"

    #: Absence handle for the "no Save button" assertion: a control that does
    #: not exist cannot be addressed by a testid. Scoped raw handle under the
    #: `settings-content` testid parent, #579 discipline -- see
    #: :meth:`save_buttons`.
    SAVE_BUTTON_ROLE_NAME = "save"

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def open_settings_tab(self, tab_id: str, timeout: int = 30000) -> None:
        """Reach ``/settings/<tab_id>`` the way a user does.

        App root -> sidebar 'Settings' -> the drawer item. Going through the
        drawer keeps "this section is reachable from the Settings navigation"
        an observed fact rather than an assumption, and it is what the cases'
        "Navigate to ..." steps describe.
        """
        self.navigate(APP_ROOT_PATH)
        self.sidebar_settings_button.click()
        self.settings_drawer.wait_for(state="visible", timeout=timeout)
        self.nav_item(tab_id).click()
        self.settings_content.wait_for(state="visible", timeout=timeout)
        logger.info("Opened Settings -> %s via the sidebar", tab_id)

    def go_to_settings_tab(self, tab_id: str, timeout: int = 30000) -> None:
        """Switch to another settings tab from a settings route already open."""
        self.nav_item(tab_id).click()
        self.settings_content.wait_for(state="visible", timeout=timeout)
        logger.info("Switched to Settings -> %s", tab_id)

    def nav_item(self, tab_id: str) -> Locator:
        """Drawer nav item for *tab_id* (e.g. ``preferences``, ``memory``).

        Selection state is on the element's ``data-active`` attribute, never in
        the testid value (`.agents/testing.md` § Locator policy, PR #581).
        """
        return self.page.locator(self.SETTINGS_NAV_ITEM.format(tab_id))

    # ------------------------------------------------------------------
    # Accordion sections
    # ------------------------------------------------------------------

    def preferences_sections(self) -> list[AccordionSection]:
        """The three collapsible sections of ``/settings/preferences``, in DOM order."""
        return [
            AccordionSection(
                "GENERAL",
                self.preferences_general_section,
                self.preferences_general_header,
                self.preferences_general_content,
            ),
            AccordionSection(
                "VOICE PERSONALIZATION",
                self.voice_personalization_section,
                self.voice_personalization_header,
                self.voice_preview_button,
            ),
            AccordionSection(
                "SOUND NOTIFICATIONS",
                self.sound_notifications_section,
                self.sound_notifications_header,
                self.sound_notifications_content,
            ),
        ]

    def context_management_accordion(self) -> AccordionSection:
        """The ``CONTEXT MANAGEMENT`` section of ``/settings/memory``."""
        return AccordionSection(
            "CONTEXT MANAGEMENT",
            self.context_management_section,
            self.context_management_header,
            self.context_management_toggle,
        )

    @staticmethod
    def toggle_section(section: AccordionSection) -> None:
        """Click a section's header -- the collapse/expand control.

        The whole summary row is the click target; the chevron the case names
        is rendered inside it (`BasicAccordion`'s `expandIcon` slot), so this
        IS the case's "click the chevron".
        """
        section.header.click()
        logger.info("Toggled accordion section %s", section.name)

    # ------------------------------------------------------------------
    # Persona (AI Personality)
    # ------------------------------------------------------------------

    def wait_for_persona_select(self, timeout: int = 30000) -> None:
        """Wait until the 'Default persona' select has rendered.

        Right after navigating to ``/settings/ai-personality`` the select is
        briefly absent from the DOM while the settings query resolves -- an
        element wait, never a sleep.
        """
        self.persona_select_combobox.wait_for(state="visible", timeout=timeout)

    def get_persona(self) -> str:
        """Currently displayed 'Default persona' label (e.g. ``Generic``, ``QA``)."""
        return (self.persona_select_combobox.inner_text() or "").strip()

    def open_persona_options(self, timeout: int = 10000) -> None:
        """Open the 'Default persona' option list."""
        self.persona_select_combobox.click()
        self.persona_option("qa").wait_for(state="visible", timeout=timeout)

    def persona_option(self, value: str) -> Locator:
        """Option row for persona *value* (``generic``, ``qa``, ``nerdy``, ...)."""
        return self.page.locator(self.SELECT_OPTION.format(value))

    def select_persona(self, value: str, timeout: int = 10000) -> None:
        """Pick persona *value* from the 'Default persona' select.

        Does NOT wait for the autosave round-trip: the caller owns a
        ``page.expect_response`` context manager around this call so the PUT's
        status is asserted rather than merely awaited (see
        :data:`AUTHOR_SETTINGS_ENDPOINT`).
        """
        self.open_persona_options(timeout=timeout)
        self.persona_option(value).click()
        logger.info("Selected persona %r", value)

    def close_persona_options(self, timeout: int = 10000) -> None:
        """Dismiss the 'Default persona' option list without changing the value."""
        self.page.keyboard.press("Escape")
        self.persona_option("qa").wait_for(state="hidden", timeout=timeout)

    def persona_options(self) -> Locator:
        """All option rows of the open 'Default persona' list, in DOM order.

        See :data:`SELECT_OPTION_ANY` for why the selector carries
        ``[data-selected]``.
        """
        return self.page.locator(self.SELECT_OPTION_ANY)

    def get_persona_option_labels(self) -> list[str]:
        """Labels of the open option list, in DOM order.

        Each row renders ``customRenderOption`` -- the label on the first line
        and the persona's description below it -- so only the first line is the
        label.
        """
        return [
            (text.strip().splitlines() or [""])[0].strip()
            for text in self.persona_options().all_inner_texts()
        ]

    def persona_option_selected_state(self, value: str) -> str | None:
        """``data-selected`` of one option row (``"true"`` / ``"false"``).

        Selection state is a ``data-*`` attribute on a stable testid, which is
        the shape `.agents/testing.md` § Locator policy requires (never a
        state-switched testid value).
        """
        return self.persona_option(value).get_attribute("data-selected")

    # ------------------------------------------------------------------
    # User instructions (AI Personality)
    # ------------------------------------------------------------------

    def get_user_instructions(self) -> str:
        """Current text of the 'User instructions' textarea.

        The field is stored **per persona** -- it renders the slot of the
        currently selected persona and is absent from the DOM entirely while
        the persona is ``None`` (``values.persona !== 'none'`` guard in
        ``AIPersonalityPersonalization.jsx``). Pin the persona before reading.
        """
        return self.user_instructions_textarea.input_value()

    def fill_user_instructions(self, text: str) -> None:
        """Type *text* into the 'User instructions' textarea (no blur).

        Autosave here is blur-driven (``AIPersonalityFormContent`` wraps the
        form in ``useFormikAutoSaveOnBlur``; ``handleInstructionsChange`` does
        NOT request a save itself), so the caller blurs -- typically via
        :meth:`click_neutral_content_area` -- inside its own
        ``page.expect_response`` block, and asserts the PUT.
        """
        self.user_instructions_textarea.fill(text)
        logger.info("Filled user instructions (%d chars)", len(text))

    def click_neutral_content_area(self) -> None:
        """Click empty space in the settings content pane -- "click outside".

        Deliberately NOT the accordion header: clicking that collapses the
        section (confirmed live). The bottom-left corner of ``settings-content``
        is below the (short) form on every personalization route, so the click
        lands on the ``<main>`` element itself -- enough to move focus off a
        field, which is what fires ``focusout`` and therefore the autosave.
        """
        box = self.settings_content.bounding_box()
        assert box, "settings-content has no bounding box -- is the settings route open?"
        self.settings_content.click(
            position={"x": 8.0, "y": max(box["height"] - 8.0, 8.0)}
        )
        logger.info("Clicked a neutral area of the settings content pane")

    def persona_section_disabled_elements(self) -> Locator:
        """Elements inside PERSONA MANAGEMENT carrying MUI's disabled marker.

        Scoped raw handle, sanctioned exception (`.agents/testing.md`
        § Locator policy, #579 discipline): ``.Mui-disabled`` is a class MUI
        adds at render time to express "grayed out" -- there is no element the
        app could put a testid on to express *that state*, and the project's own
        rule says state is read off attributes/classes rather than a
        state-switched testid. The discipline is honoured: the parent is the
        real app testid ``ai-personality-persona-section`` and the class
        selector is chained off it, never free-floating at page level. Do not
        extend this shape to any handle that COULD carry a testid.

        Expected to have count 0 -- ELITEA-2383 asserts the personality
        controls are not grayed out while context management is off.
        """
        return self.persona_section.locator(self.MUI_DISABLED_MARKER)

    # ------------------------------------------------------------------
    # Preferences controls (voice + sound)
    # ------------------------------------------------------------------

    def select_option(self, value: str) -> Locator:
        """Option row *value* of any open ``SingleSelect`` on this page.

        Same dynamic class constant :data:`SELECT_OPTION` the persona helpers
        use -- the option testids are emitted generically by ``SingleSelect``,
        so one accessor serves every select on the personalization routes.
        """
        return self.page.locator(self.SELECT_OPTION.format(value))

    def select_options(self) -> Locator:
        """All option rows of the currently open ``SingleSelect``.

        See :data:`SELECT_OPTION_ANY` for why the selector carries
        ``[data-selected]``.
        """
        return self.page.locator(self.SELECT_OPTION_ANY)

    def open_voice_options(self, probe_value: str, timeout: int = 10000) -> None:
        """Open the 'Voice' option list, waiting on *probe_value*'s row.

        The list is backend-supplied (model TTS voices), so the caller names a
        row it expects rather than the helper hardcoding one.
        """
        self.voice_select_combobox.click()
        self.select_option(probe_value).wait_for(state="visible", timeout=timeout)

    def choose_open_option(self, value: str, timeout: int = 10000) -> None:
        """Click row *value* of an ALREADY-OPEN select and wait for the list to close.

        Split from :meth:`open_voice_options` deliberately: a case that asserts
        the open list first (ELITEA-2385 step 3) must not re-click the combobox
        to make its choice -- that second click closes the popover instead of
        selecting.
        """
        option = self.select_option(value)
        option.click()
        option.wait_for(state="hidden", timeout=timeout)
        logger.info("Chose select option %r", value)

    def drag_slider_to(self, slider_root: Locator, slider_thumb: Locator, fraction: float) -> None:
        """Drag *slider_thumb* to *fraction* (0..1) of *slider_root*'s width.

        Two facts make this the required shape rather than a convenience:

        * **Drag, not arrow keys.** MUI's keyboard handler adds ``step`` without
          re-rounding, so five ``ArrowRight`` presses land on
          ``1.5000000000000004`` (defect #1966); its pointer handler routes
          through ``roundValueToStep`` and lands exactly on the grid.
        * **Never drop onto a mark label.** The first and last mark labels are
          ``translateX(0)`` / ``translateX(-100%)``-shifted, so their centre is
          NOT the track position they annotate -- dropping on the ``100%`` label
          lands on ``0.95``. The target x is computed from the slider root's own
          bounding box; the y comes from the thumb, because the root's box also
          spans the mark-label row below the track.
        """
        root_box = slider_root.bounding_box()
        assert root_box, "slider root has no bounding box -- is the section expanded?"
        slider_thumb.hover()
        thumb_box = slider_thumb.bounding_box()
        assert thumb_box, "slider thumb has no bounding box"

        target_x = root_box["x"] + root_box["width"] * fraction
        target_y = thumb_box["y"] + thumb_box["height"] / 2

        self.page.mouse.down()
        self.page.mouse.move(target_x, target_y, steps=10)
        self.page.mouse.up()
        logger.info("Dragged slider thumb to fraction %.2f (x=%.1f)", fraction, target_x)

    def is_sound_notifications_enabled(self) -> bool:
        """Whether the 'Play sound when tasks complete' toggle is currently ON.

        Read off the hidden input, which is the element that carries the state
        (``to_be_checked()``/``is_checked()`` reject the SwitchBase span).
        """
        return self.sound_notifications_toggle_input.is_checked()

    # ------------------------------------------------------------------
    # Absence handles
    # ------------------------------------------------------------------

    def save_buttons(self) -> Locator:
        """Handle for asserting that **no** Save button exists in the content pane.

        Scoped raw handle, sanctioned exception (`.agents/testing.md`
        § Locator policy, #579 discipline): an absence assertion cannot be keyed
        on a testid for a control that does not exist. The discipline is
        honoured -- the parent is the real app testid ``settings-content`` and
        the role handle is chained off it, never free-floating at page level.
        Do not extend this shape to any handle that COULD carry a testid.

        Expected to have count 0: personalization settings autosave, so a Save
        button appearing here would mean the case's premise stopped holding.
        """
        return self.settings_content.get_by_role("button", name=self.SAVE_BUTTON_ROLE_NAME)

    def page_save_buttons(self) -> Locator:
        """Page-wide variant of :meth:`save_buttons` (case step 2 says "on the page").

        Same #579 discipline rationale; page-level is unavoidable here because
        the assertion is precisely that no such control exists anywhere.
        """
        return self.page.get_by_role("button", name=self.SAVE_BUTTON_ROLE_NAME)
