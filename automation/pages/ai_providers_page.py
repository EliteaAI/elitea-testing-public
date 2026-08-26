"""AI Providers page object (Settings -> AI Providers).

URL: /settings/ai-providers

Covers the page layout (header title) and the seven configuration
accordion sections (``ConfigurationsPanel.jsx`` -> ``ConfigurationSection.jsx``
-> ``AIProviderAccordion.jsx``): LLMs, Embedding Models, Vector Storage,
Image Generation, Speech Recognition (ASR), Text to Speech (TTS), and AI
Credentials. Each populated section renders as an accordion with a count
badge and, once expanded, a "Default" (plus, for LLMs, "High-tier"/
"Low-tier") model selector and >=1 ``ConfigurationCard``. A section with
zero configured items for the active project renders nothing at all
(``ConfigurationSection.jsx``: ``if (!configurations || configurations.length
=== 0) return null;``) -- see :meth:`navigate_and_capture_vectorstorage_response`
for how this page object distinguishes that correct empty-state hide from a
silent load failure.

Locator provenance (ELITEA-2392): the entire ``ai-providers`` component tree
carried zero ``data-testid``/``testId`` usage at analysis time (confirmed via
``grep -rn "testid\\|testId"`` on every file under
``src/[fsd]/features/settings/ui/ai-providers/``). All locators below were
added by this implementation, committed onto ``automation/testids``:

- ``ai-providers-page-title`` wires ``DrawerPageHeader``'s existing
  ``titleTestId`` prop (same mechanism as ``PersonalTokensPage.page_title`` /
  ``SecretsPage.page_title``) -- ``EliteaAI/EliteaUI@5119ba70``.
- ``ai-providers-section-<slug>`` (one per of the 7
  ``ConfigurationSection`` call sites in ``ConfigurationsPanel.jsx``) is a
  new caller-supplied ``sectionTestId`` prop threaded through
  ``ConfigurationSection.jsx`` -> ``AIProviderAccordion.jsx`` onto the
  accordion's ``StyledAccordionSummary`` (the header button element that
  both displays the section title/count and toggles expand/collapse) --
  ``EliteaAI/EliteaUI@5119ba70``.
- ``ai-provider-configuration-card`` wires a new static ``data-testid`` on
  ``ConfigurationCard.jsx``'s outer ``Box`` -- static value repeated per
  card, same pattern as ``PersonalTokensPage.token_row`` --
  ``EliteaAI/EliteaUI@5119ba70``.
- ``ai-providers-section-<slug>-default-selector`` /
  ``...-high-tier-model-selector`` / ``...-low-tier-model-selector`` are new
  ``data-testid`` values templated in JSX from the already-threaded
  ``sectionTestId`` (``ConfigurationSection.jsx``, forwarded to the shared
  ``Select.SingleSelect`` component, which already accepted a
  ``data-testid`` prop) -- ``EliteaAI/EliteaUI@ff547e50``. Only rendered
  once their section is expanded (accordion content unmounts on collapse).
  The shared ``Select.SingleSelect`` component also auto-derives a
  ``{testid}-combobox`` suffix onto the actual clickable/readable node
  (``SelectDisplayProps``) -- pre-existing shared-component convention, not
  added by any Elitea-testing-public work.

Locator provenance (ELITEA-2397): the tier badge testid did not exist before
this implementation --

- ``ai-provider-configuration-badge`` wires a new static ``data-testid`` on
  each of ``ConfigurationCard.jsx``'s three independently-conditional
  ``Typography`` blocks (``isDefault``/``isHighTier``/``isLowTier`` -- three
  separate JSX nodes, not a ternary switching one element between two
  states, so canon ruling #277 does not apply here). Static value repeated
  per badge, same pattern as ``ai-provider-configuration-card`` itself --
  distinguish which badge by its own text content ("Default"/"High-Tier"/
  "Low-Tier"), scoped inside the already-testid-scoped card locator --
  ``EliteaAI/EliteaUI@4213b6c8``.
- ``ai-provider-configuration-card-name`` wires a new static ``data-testid``
  on the card's ``displayName`` ``Typography`` -- needed because the card's
  OUTER testid (``ai-provider-configuration-card``) wraps displayName +
  status text + badge text as sibling elements with no whitespace separator
  in the concatenated text content (e.g. ``"GPT-5.4OK . Shared"``), so an
  exact-match ``^name$`` regex filtered on the outer card testid alone never
  matches (confirmed live, this implementation's first test run) -- exact
  identification requires its own scoped handle, not a text-boundary
  workaround. ``EliteaAI/EliteaUI@e1ea650c``.

Vector Storage and AI Credentials never render any of the above for the
shared ``${TEST_USER}`` project (zero configured items) -- their section
header locators are still defined (referenced via absence assertions,
canon ruling #511 extension) but their selector/card testids never mount.
"""

import logging
import re

from playwright.sync_api import Locator, Response, expect

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.ai_providers")

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

AI_PROVIDERS_PATH = "/settings/ai-providers"

# Per-section models list call -- fires once per section on every page load
# (`useListModelsQuery`), independent of the combined card-listing call.
VECTORSTORAGE_MODELS_URL_SUBSTRING = "/configurations/models/"


def _is_vectorstorage_models_response(response: Response) -> bool:
    """Match the per-section models GET for ``section=vectorstorage``.

    This is the response whose body proves "zero configured items" rather
    than merely "the accordion isn't in the DOM" -- distinguishing a
    correctly-hidden empty section from a silent load failure (AFS step 6).
    """
    return (
        response.request.method == "GET"
        and VECTORSTORAGE_MODELS_URL_SUBSTRING in response.url
        and "section=vectorstorage" in response.url
    )


# ELITEA-2397 -- LLM tier (Default/High-tier/Low-tier) mutation flow.
MODELS_URL_SUBSTRING = "/configurations/models/"


def _is_llm_models_response(response: Response) -> bool:
    """Match the per-section models GET for ``section=llm``.

    This single response body carries everything needed to derive the
    current Default/High-tier/Low-tier values (``default_model_name`` /
    ``high_tier_default_model_name`` / ``low_tier_default_model_name`` +
    their ``*_project_id`` counterparts) AND the candidate option list
    (``items``, each item carrying its own ``high_tier``/``low_tier``
    eligibility booleans) -- confirmed live, 2026-08-06.
    """
    return (
        response.request.method == "GET"
        and MODELS_URL_SUBSTRING in response.url
        and "section=llm" in response.url
    )


def _is_set_default_model_response(response: Response) -> bool:
    """Match the ``POST /configurations/models/{project_id}`` save call.

    Fires on every tier selector change (Default/High-tier/Low-tier alike) --
    no separate Save action. Confirmed live, response ``200`` with body
    ``{"result": "success"}``.
    """
    return response.request.method == "POST" and MODELS_URL_SUBSTRING in response.url


def pick_alternative_llm_model(items: list[dict], current_value: str, tier_field: str | None = None) -> dict:
    """Return the first LLM item eligible for *tier_field* whose value differs
    from *current_value*.

    Args:
        items: the ``items`` list from the ``section=llm`` models response.
        current_value: the tier's current ``"{name}<<>>{project_id}"`` value
            (may be an empty string for an originally-unset tier).
        tier_field: ``None`` for the Default tier (every item is eligible),
            ``"high_tier"``/``"low_tier"`` to filter to that tier's eligible
            subset -- mirrors ``useModelOptions``' ``createOptions()``
            filtering in ``EliteaUI/src/[fsd]/features/settings/lib/hooks/
            useModelConfiguration.hooks.jsx``.

    Raises:
        AssertionError: no eligible alternative exists (should not happen on
            the shared ``${TEST_USER}`` project -- Default offers 10
            alternatives, High-tier 7, Low-tier 2, confirmed live).
    """
    for item in items:
        if tier_field and not item.get(tier_field):
            continue
        value = f"{item['name']}<<>>{item['project_id']}"
        if value != current_value:
            return item
    raise AssertionError(
        f"No alternative LLM option found for tier_field={tier_field!r}, current_value={current_value!r}"
    )


class AIProvidersPage(BasePage):
    """Settings -> AI Providers page (page layout + 7 configuration sections).

    URL: /settings/ai-providers
    """

    # -- Page layout -----------------------------------------------------
    page_title = LocatorDescriptor(
        testid="ai-providers-page-title",
        description='Page header title -- exact text "AI Providers"',
    )

    # -- Section accordion headers (one per configuration section) ------
    llms_section_header = LocatorDescriptor(
        testid="ai-providers-section-llms",
        description='"LLMs" accordion header (auto-expanded by default)',
    )
    embedding_models_section_header = LocatorDescriptor(
        testid="ai-providers-section-embedding-models",
        description='"Embedding Models" accordion header',
    )
    vector_storage_section_header = LocatorDescriptor(
        testid="ai-providers-section-vector-storage",
        description='"Vector Storage" accordion header -- only renders when '
        "the project has >=1 configured item",
    )
    image_generation_section_header = LocatorDescriptor(
        testid="ai-providers-section-image-generation",
        description='"Image Generation" accordion header',
    )
    asr_section_header = LocatorDescriptor(
        testid="ai-providers-section-asr",
        description='"Speech Recognition (ASR)" accordion header',
    )
    tts_section_header = LocatorDescriptor(
        testid="ai-providers-section-tts",
        description='"Text to Speech (TTS)" accordion header',
    )
    ai_credentials_section_header = LocatorDescriptor(
        testid="ai-providers-section-ai-credentials",
        description='"AI Credentials" accordion header -- only renders when '
        "the project has >=1 configured item",
    )

    # -- Default/tier model selectors (mount only once their section is
    #    expanded -- accordion content unmounts on collapse) -------------
    llms_default_selector = LocatorDescriptor(
        testid="ai-providers-section-llms-default-selector",
        description='LLMs section "Default" model selector',
    )
    llms_high_tier_selector = LocatorDescriptor(
        testid="ai-providers-section-llms-high-tier-model-selector",
        description='LLMs section "High-tier" model selector',
    )
    llms_low_tier_selector = LocatorDescriptor(
        testid="ai-providers-section-llms-low-tier-model-selector",
        description='LLMs section "Low-tier" model selector',
    )
    embedding_models_default_selector = LocatorDescriptor(
        testid="ai-providers-section-embedding-models-default-selector",
        description='Embedding Models section "Default" model selector',
    )
    image_generation_default_selector = LocatorDescriptor(
        testid="ai-providers-section-image-generation-default-selector",
        description='Image Generation section "Default" model selector',
    )
    asr_default_selector = LocatorDescriptor(
        testid="ai-providers-section-asr-default-selector",
        description='Speech Recognition (ASR) section "Default" model selector',
    )
    tts_default_selector = LocatorDescriptor(
        testid="ai-providers-section-tts-default-selector",
        description='Text to Speech (TTS) section "Default" model selector',
    )

    # -- LLM tier selector COMBOBOX triggers (ELITEA-2397) ----------------
    # The `-combobox` suffix is the shared `Select.SingleSelect` component's
    # own auto-derived testid (`SelectDisplayProps`) -- this is the actual
    # clickable/readable node (role=combobox), distinct from the outer
    # `llms_*_selector` fields above which locate the FormControl wrapper.
    llms_default_selector_combobox = LocatorDescriptor(
        testid="ai-providers-section-llms-default-selector-combobox",
        description='LLMs section "Default" model selector -- clickable combobox '
        "node; its text_content() is the currently-selected model's display name.",
    )
    llms_high_tier_selector_combobox = LocatorDescriptor(
        testid="ai-providers-section-llms-high-tier-model-selector-combobox",
        description='LLMs section "High-tier" model selector -- clickable combobox node.',
    )
    llms_low_tier_selector_combobox = LocatorDescriptor(
        testid="ai-providers-section-llms-low-tier-model-selector-combobox",
        description='LLMs section "Low-tier" model selector -- clickable combobox node.',
    )

    # -- Per-section loading placeholder (ELITEA-2251) -------------------
    # `ConfigurationSection.jsx`'s `isLoading` branch renders the section
    # title plus a `Typography` reading exactly "Loading..." and nothing
    # else -- no accordion, no cards, no selectors. One placeholder per
    # section (7), regardless of whether that section will turn out to be
    # empty once loaded (the hide-when-empty check happens AFTER the
    # loading branch). The testid is templated from the already-threaded
    # `sectionTestId`, the same derived-id pattern the component already
    # uses for `${sectionTestId}-default-selector` --
    # EliteaAI/EliteaUI@c49f61bc.
    llms_section_loading = LocatorDescriptor(
        testid="ai-providers-section-llms-loading",
        description='LLMs section "Loading..." placeholder -- present only '
        "while the configurations request is in flight",
    )

    # Every section's loading placeholder at once (used for the exact
    # per-section count and for the "loading is over" assertion). Scoped
    # sub-selector class constant per `.agents/testing.md` Locator policy;
    # both halves are `data-testid` matches, no raw handle.
    SECTION_LOADING_SELECTOR = '[data-testid^="ai-providers-section-"][data-testid$="-loading"]'

    # Generic, repeated-per-card testid (same pattern as `secret-row` /
    # `token_row`) -- scoped sub-selector constant per
    # `.agents/testing.md` Locator policy.
    CONFIGURATION_CARD_SELECTOR = '[data-testid="ai-provider-configuration-card"]'

    # Generic, repeated-per-badge testid (ELITEA-2397) -- scoped inside a
    # card locator, distinguished by its own text content ("Default"/
    # "High-Tier"/"Low-Tier").
    TIER_BADGE_SELECTOR = '[data-testid="ai-provider-configuration-badge"]'

    # Generic, repeated-per-card testid for the display-name Typography
    # ALONE (ELITEA-2397) -- required for exact-match model identification;
    # the outer CONFIGURATION_CARD_SELECTOR's text content concatenates
    # displayName + status + badge text with no separator, so an anchored
    # ``^name$`` filter on it alone cannot disambiguate (e.g. "GPT-5.4" vs
    # "GPT-5.4-mini"), confirmed live.
    CARD_NAME_SELECTOR = '[data-testid="ai-provider-configuration-card-name"]'

    # Dynamic (runtime-parameterized) testid -- pre-existing shared
    # `SingleSelectMenuItem` convention (`select-option-{value}`), NOT added
    # by this implementation. Format with a model's own
    # `"{name}<<>>{project_id}"` value read from the LLM models response
    # body (`pick_alternative_llm_model`), per `.agents/testing.md` Locator
    # policy's class-level-template-constant pattern for dynamic testids.
    SELECT_OPTION = '[data-testid="select-option-{}"]'

    def navigate(self) -> None:
        """Navigate to /settings/ai-providers and wait for the page to load."""
        super().navigate(AI_PROVIDERS_PATH)

    def navigate_and_capture_vectorstorage_response(self) -> Response:
        """Navigate while capturing the vectorstorage-scoped models response.

        Returns the raw ``Response`` for the ``section=vectorstorage`` GET so
        the caller can assert both its HTTP status AND its JSON body's item
        count -- the only way to tell "correctly hidden because empty" apart
        from "silently failed to load" (both render identically: no
        accordion in the DOM).
        """
        with self.page.expect_response(
            _is_vectorstorage_models_response, timeout=NAVIGATION_TIMEOUT
        ) as response_info:
            self.navigate()
        return response_info.value

    def navigate_and_capture_llm_response(self) -> Response:
        """Navigate while capturing the LLM-scoped models response (ELITEA-2397).

        Returns the raw ``Response`` for the ``section=llm`` GET, whose JSON
        body carries both the current Default/High-tier/Low-tier values and
        the full candidate ``items`` list (see :func:`pick_alternative_llm_model`).
        """
        with self.page.expect_response(_is_llm_models_response, timeout=NAVIGATION_TIMEOUT) as response_info:
            self.navigate()
        return response_info.value

    def select_tier_model(self, combobox: Locator, option_value: str, timeout: int = UI_ELEMENT_TIMEOUT) -> Response:
        """Open a tier's combobox, select the option matching *option_value*
        (``"{name}<<>>{project_id}"``), and return the raw ``Response`` for the
        ``POST /configurations/models/{project_id}`` save call that fires as a
        result -- no separate Save action (confirmed live, ELITEA-2397).

        Args:
            combobox: one of ``llms_default_selector_combobox`` /
                ``llms_high_tier_selector_combobox`` / ``llms_low_tier_selector_combobox``.
            option_value: the target option's raw value, read from an LLM
                models response item via ``f"{item['name']}<<>>{item['project_id']}"``.
        """
        combobox.click()
        option = self.page.locator(self.SELECT_OPTION.format(option_value))
        option.wait_for(state="visible", timeout=timeout)
        with self.page.expect_response(_is_set_default_model_response, timeout=timeout) as response_info:
            option.click()
        return response_info.value

    def card_for_model(self, model_display_name: str) -> Locator:
        """Return the ``ConfigurationCard`` whose display name EXACTLY matches
        *model_display_name* (exact match required -- some display names are
        string-prefixes of others, e.g. "GPT-5.4" vs "GPT-5.4-mini", confirmed
        live). Filters on the dedicated ``CARD_NAME_SELECTOR`` handle (not the
        outer card testid, whose concatenated text content can't be anchored
        exactly -- see class docstring) via ``.filter(has=...)``, scoping the
        match to the enclosing card.
        """
        pattern = re.compile(rf"^{re.escape(model_display_name)}$")
        name_locator = self.page.locator(self.CARD_NAME_SELECTOR).filter(has_text=pattern)
        return self.page.locator(self.CONFIGURATION_CARD_SELECTOR).filter(has=name_locator)

    def card_tier_badge(self, model_display_name: str, badge_text: str) -> Locator:
        """Return the tier badge locator (``"Default"``/``"High-Tier"``/
        ``"Low-Tier"``) scoped inside the card for *model_display_name*, for
        use with web-first ``expect(...).to_be_visible()`` /
        ``expect(...).to_have_count(0)`` assertions (the badge Typography
        unmounts entirely when its tier flag goes false -- not merely hidden)."""
        return self.card_for_model(model_display_name).locator(self.TIER_BADGE_SELECTOR).filter(has_text=badge_text)

    def section_loading_placeholders(self) -> Locator:
        """Return the locator matching EVERY section's "Loading..." placeholder.

        Resolves to 7 elements (one per ``ConfigurationSection`` call site in
        ``ConfigurationsPanel.jsx``) while the combined configurations request
        is in flight, and to 0 once it resolves -- whether the section then
        renders content or is hidden for being empty.
        """
        return self.page.locator(self.SECTION_LOADING_SELECTOR)

    def populated_section_headers(self) -> list[tuple[str, Locator]]:
        """Return the (label, header locator) pairs for the sections that
        actually render for the shared ``${TEST_USER}`` project.

        Vector Storage and AI Credentials have zero configured items and are
        therefore absent by design (``ConfigurationSection.jsx`` returns
        ``null`` for an empty section) -- see
        :meth:`navigate_and_capture_vectorstorage_response`.
        """
        return [
            ("LLMs", self.llms_section_header),
            ("Embedding Models", self.embedding_models_section_header),
            ("Image Generation", self.image_generation_section_header),
            ("Speech Recognition (ASR)", self.asr_section_header),
            ("Text to Speech (TTS)", self.tts_section_header),
        ]

    def get_configuration_card_count(self) -> int:
        """Return the number of ``ConfigurationCard`` elements currently in the DOM.

        Cards from every *expanded* section are counted together (the
        testid is a generic, repeated-per-card value with no per-section
        scoping element to chain off). Callers isolate a single section's
        contribution by taking a before/after delta around expanding that
        one section -- see :meth:`expand_section`.
        """
        return self.page.locator(self.CONFIGURATION_CARD_SELECTOR).count()

    def expand_section(self, section_header: Locator, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Expand an accordion section by clicking its header, if not already expanded.

        Sections manage independent expand/collapse state (not an
        exclusive/single-open accordion), so expanding one never collapses
        another already-expanded section.
        """
        section_header.wait_for(state="visible", timeout=timeout)
        if section_header.get_attribute("aria-expanded") != "true":
            section_header.click()
            expect(section_header).to_have_attribute("aria-expanded", "true", timeout=timeout)
