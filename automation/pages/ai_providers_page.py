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

from playwright.sync_api import Error as PlaywrightError
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


def _section_models_response_matcher(section: str):
    """Return a predicate matching the per-section models GET for *section*.

    Generic sibling of :func:`_is_vectorstorage_models_response` /
    :func:`_is_llm_models_response` (both left byte-identical for their merged
    callers) -- added for ELITEA-2398/2399/2400/2401, which need the same
    capture for ``section=embedding`` and ``section=vectorstorage``.
    """

    def _matcher(response: Response) -> bool:
        return (
            response.request.method == "GET"
            and MODELS_URL_SUBSTRING in response.url
            and f"section={section}" in response.url
        )

    return _matcher


def project_id_from_models_response(response: Response) -> int:
    """Return the ACTIVE project id from a models response's own URL.

    The URL shape is ``.../configurations/models/{project_id}?...``. Reading the
    id from the product's own request is the honest alternative to hardcoding a
    project number, which every AFS in this cluster explicitly forbids -- the
    Default-selector option testids are keyed ``{key}<<>>{project_id}``, so the
    id is needed to build them.
    """
    match = re.search(r"/configurations/models/(\d+)", response.url)
    assert match, f"Not a per-section models response URL: {response.url}"
    return int(match.group(1))


class AIProvidersPage(BasePage):
    """Settings -> AI Providers page (page layout + 7 configuration sections).

    URL: /settings/ai-providers
    """

    # -- Page layout -----------------------------------------------------
    page_title = LocatorDescriptor(
        testid="ai-providers-page-title",
        description='Page header title -- exact text "AI Providers"',
    )
    # ELITEA-2346: the page's "+" control. Generic, pre-existing sidebar
    # testid (already used by the agents/pipelines/toolkits list pages); its
    # LABEL is route-contextual and reads "AI Provider" here.
    create_button = LocatorDescriptor(
        testid="sidebar-create-button",
        description='"+" create control -- routes to the Create AI Provider type picker',
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

    # -- Default-selector COMBOBOX triggers for the non-LLM sections
    #    (ELITEA-2398 / ELITEA-2399 / ELITEA-2401). Same shared
    #    `Select.SingleSelect` `-combobox` auto-derived suffix as the LLM tier
    #    triggers above: the outer `*_default_selector` fields locate the
    #    FormControl wrapper, these locate the actual clickable/readable
    #    role=combobox node. Pre-existing testids (derived in JSX from the
    #    already-threaded `sectionTestId`) -- nothing added here.
    embedding_models_default_selector_combobox = LocatorDescriptor(
        testid="ai-providers-section-embedding-models-default-selector-combobox",
        description='Embedding Models section "Default" model selector -- clickable '
        "combobox node; its text_content() is the currently-default model's DISPLAY NAME.",
    )
    vector_storage_default_selector_combobox = LocatorDescriptor(
        testid="ai-providers-section-vector-storage-default-selector-combobox",
        description='Vector Storage section "Default" selector -- clickable combobox '
        "node. Unlike every other section its text_content() is the configuration's "
        "`elitea_title`, NOT a display name: a pgvector configuration carries no "
        "`data.name`, so the option key and label both fall back to `elitea_title` "
        "(`_surface.md` -- the same mismatch that causes #1987).",
    )
    # ELITEA-2402/2404/2406 + ELITEA-2403/2405/2407. Same shared
    # `Select.SingleSelect` `-combobox` auto-derived suffix; the three outer
    # `*_default_selector` FormControl wrappers above already existed, these
    # are the actual clickable/readable role=combobox nodes. Pre-existing
    # testids (derived in JSX from the already-threaded `sectionTestId`) --
    # nothing added to EliteaUI here; this was a page-object gap only.
    image_generation_default_selector_combobox = LocatorDescriptor(
        testid="ai-providers-section-image-generation-default-selector-combobox",
        description='Image Generation section "Default" model selector -- clickable '
        "combobox node; its text_content() is the currently-default model's DISPLAY NAME.",
    )
    asr_default_selector_combobox = LocatorDescriptor(
        testid="ai-providers-section-asr-default-selector-combobox",
        description='Speech Recognition (ASR) section "Default" model selector -- '
        "clickable combobox node; its text_content() is the currently-default model's "
        "DISPLAY NAME.",
    )
    tts_default_selector_combobox = LocatorDescriptor(
        testid="ai-providers-section-tts-default-selector-combobox",
        description='Text to Speech (TTS) section "Default" model selector -- clickable '
        "combobox node; its text_content() is the currently-default model's DISPLAY NAME.",
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

    # Generic, repeated-per-card testid for the card's STATUS line
    # ("OK • Shared" / "OK • Local") -- ELITEA-2402/2404/2406 step 3 asserts
    # "model name AND status badge", and only the name half had a handle.
    # Added by this implementation as an attribute on the EXISTING status
    # `Typography` -- EliteaAI/EliteaUI@db8f4b28.
    #
    # WARNING: that Typography also CONTAINS the tier/Default badges
    # (`{statusText}{isHighTier && ...}{isDefault && ...}`), so on the default
    # card its inner text reads "OK • Shared\nDefault" while a non-default card
    # reads exactly "OK • Shared". Assert with `to_contain_text(...)` -- an
    # exact `to_have_text("OK • Shared")` passes on every card EXCEPT the one
    # that matters.
    CARD_STATUS_SELECTOR = '[data-testid="ai-provider-configuration-card-status"]'

    # Provider-group container + its label, inside a section that groups its
    # models by provider (LLMs). Generic, repeated-per-group testids -- same
    # pattern (and same reason) as CONFIGURATION_CARD_SELECTOR /
    # CARD_NAME_SELECTOR: the group Box's concatenated text content includes
    # every card's text, so `has_text` on the group alone cannot identify it.
    # Added by the ELITEA-2395 implementation -- EliteaAI/EliteaUI@a64d3308.
    CONFIGURATION_GROUP_SELECTOR = '[data-testid="ai-providers-configuration-group"]'
    CONFIGURATION_GROUP_NAME_SELECTOR = '[data-testid="ai-providers-configuration-group-name"]'

    # Dynamic (runtime-parameterized) testid -- pre-existing shared
    # `SingleSelectMenuItem` convention (`select-option-{value}`), NOT added
    # by this implementation. Format with a model's own
    # `"{name}<<>>{project_id}"` value read from the LLM models response
    # body (`pick_alternative_llm_model`), per `.agents/testing.md` Locator
    # policy's class-level-template-constant pattern for dynamic testids.
    SELECT_OPTION = '[data-testid="select-option-{}"]'
    # Prefix form of the same pre-existing shared-`Select` convention -- every
    # option of whichever single dropdown is currently open (MUI renders a
    # listbox in a portal and only one can be open at a time). Used to assert
    # the option SET, not just one member (ELITEA-2401 Axis 2).
    #
    # The `:not(...)` half is load-bearing, not defensive: the checkmark the
    # shared `SingleSelect` renders inside the SELECTED option carries
    # `data-testid="select-option-selected-icon"`, which the bare prefix also
    # matches -- so a 2-option dropdown with one selected resolved to THREE
    # elements (live-measured, ELITEA-2401). Both halves are `data-testid`
    # matches, so this stays testid-only per `.agents/testing.md`.
    SELECT_OPTION_PREFIX_SELECTOR = (
        '[data-testid^="select-option-"]:not([data-testid="select-option-selected-icon"])'
    )

    # --- Create-AI-Provider entry point (ELITEA-2346) ------------------
    # Dynamic (runtime-parameterized) testid -- the SAME
    # `toolkit-type-card-{type}` family the credentials type picker uses
    # (`CredentialCreatePage.TYPE_CARD_SELECTOR`); the AI-provider picker
    # renders the shared type-card component, so the values differ
    # (`open_ai`, `azure_openai`, `ollama`, ...) but the testid shape does
    # not. Class-level template constant per `.agents/testing.md` Locator
    # policy's dynamic-testid pattern. Pre-existing testid, not added here.
    TYPE_CARD_SELECTOR = '[data-testid="toolkit-type-card-{}"]'
    # Prefix form -- the "the type picker rendered at all" gate, so
    # :meth:`click_create` settles on a real product signal instead of a
    # URL string or a delay.
    TYPE_CARD_PREFIX_SELECTOR = '[data-testid^="toolkit-type-card-"]'

    def navigate(self) -> None:
        """Navigate to /settings/ai-providers and wait for the page to load."""
        super().navigate(AI_PROVIDERS_PATH)

    def type_card(self, provider_type: str) -> Locator:
        """Return the Create-AI-Provider type-picker card for *provider_type*
        (e.g. ``"open_ai"``) -- ELITEA-2346."""
        return self.page.locator(self.TYPE_CARD_SELECTOR.format(provider_type))

    @property
    def type_cards(self) -> Locator:
        """Every type card currently rendered on the AI-provider type picker."""
        return self.page.locator(self.TYPE_CARD_PREFIX_SELECTOR)

    def click_create(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click the page's "+" control and settle on the rendered type picker
        (ELITEA-2346).

        The "+" routes to ``/settings/create-ai-provider`` -- a type picker,
        NOT a form. Settling on the first rendered type card is the honest
        "the picker is up" signal; ``networkidle`` is unusable on these
        routes (`.agents/testing.md`, ``#1847``).
        """
        self.create_button.click()
        self.type_cards.first.wait_for(state="visible", timeout=timeout)

    def click_type_card(self, provider_type: str, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click the type card for *provider_type* and wait for the
        type-specific AI-provider configuration form to render (ELITEA-2346).

        The form is schema-driven (``GET /configurations/available/?section=…``)
        and renders the SAME shared ``ToolBaseProperty`` / ``SecretField``
        components the credential forms use. Those field testids therefore
        live in exactly ONE page object already
        (``CredentialFormFieldsMixin`` -- ``toolkit-field-label-input`` et
        al.) and are deliberately NOT re-declared here: this method settles
        on the type picker unmounting, and the caller asserts the rendered
        form through that shared page object (AFS step 4's own verification).
        """
        self.type_card(provider_type).click()
        self.type_cards.first.wait_for(state="detached", timeout=timeout)

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

    def reload_and_capture_llm_response(self) -> Response:
        """Reload the CURRENT document while capturing the ``section=llm``
        models GET (ELITEA-2412/2413/2414).

        Mirror of :meth:`navigate_and_capture_llm_response`, but a real
        ``page.reload()`` rather than a fresh ``goto`` -- the reload-persistence
        cases ask for a cold re-boot of the app, and only a reload re-runs the
        boot path that re-derives every section from the server.

        Deliberately NOT :meth:`~pages.base_page.BasePage.reload_and_wait`:
        that reloads with ``wait_until="networkidle"`` and then waits on
        ``networkidle`` a second time, against an app that holds a persistent
        ``/socket.io/`` polling transport open -- the structural race tracked as
        #1847 (`.agents/testing.md`). Waiting on the product's own ``section=llm``
        response is #1847's own prescribed fix, and that response is already this
        surface's oracle.
        """
        with self.page.expect_response(_is_llm_models_response, timeout=NAVIGATION_TIMEOUT) as response_info:
            self.page.reload()
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

    def select_default_configuration(self, combobox: Locator, option_value: str, timeout: int = UI_ELEMENT_TIMEOUT):
        """Section-agnostic name for :meth:`select_tier_model`.

        The mechanism is identical for every section's **Default** selector --
        open the combobox, click ``select-option-{option_value}``, and return
        the ``POST /configurations/models/{project_id}`` response that fires as
        a result (there is no separate Save). :meth:`select_tier_model` was
        written for the LLM tier selectors (ELITEA-2397) and its name says so;
        this delegating alias exists so the Vector Storage / Embedding call
        sites read honestly (ELITEA-2401). Purely additive -- the original is
        untouched and keeps its merged callers.
        """
        return self.select_tier_model(combobox, option_value, timeout=timeout)

    def navigate_and_capture_section_models_response(self, section: str) -> Response:
        """Navigate to the list page while capturing the models GET for *section*
        (``"embedding"`` / ``"vectorstorage"`` / ``"llm"`` / ...).

        The response body is the product's own oracle for that section: its
        ``items`` (each carrying the ``name`` half of the Default-selector
        option key), ``total``, ``default_model_name`` and
        ``default_model_project_id``. Generic sibling of
        :meth:`navigate_and_capture_llm_response` /
        :meth:`navigate_and_capture_vectorstorage_response`, which stay as they
        were for their merged callers.
        """
        with self.page.expect_response(
            _section_models_response_matcher(section), timeout=NAVIGATION_TIMEOUT
        ) as response_info:
            self.navigate()
        return response_info.value

    def navigate_and_capture_section_models_json(self, section: str, attempts: int = 3) -> tuple[Response, dict]:
        """Same capture as :meth:`navigate_and_capture_section_models_response`,
        but returns the response TOGETHER with its parsed JSON body -- retrying
        the whole navigate-and-capture when the browser cannot hand the body
        over.

        Why this exists (measured on ELITEA-2406, 2026-08-30, reproduced 2/2):
        the page fires one models GET **per section**, and a spec typically
        lands on the page once (to switch project) before navigating again to
        capture. ``expect_response`` starts listening BEFORE that second
        navigation, so a response belonging to the OUTGOING document can still
        be the first match -- and once the navigation commits, Chromium prunes
        that document's network entries, so reading the body raises
        ``Protocol error (Network.getResponseBody): No resource with given
        identifier found``. It hits the LAST sections in render order hardest
        (``tts``): the earlier sections' responses have already arrived, so the
        listener never sees them, while the tail ones are still in flight.

        The retry is bounded and changes nothing about what is asserted -- the
        body it returns is still the product's own response to the product's own
        request. On the retry the preceding navigation has fully settled, so
        there is no in-flight leftover to mis-match.
        """
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            response = self.navigate_and_capture_section_models_response(section)
            try:
                return response, response.json()
            except PlaywrightError as error:  # body pruned with the superseded document
                last_error = error
                logger.warning(
                    "Attempt %s/%s: the %s models response body was pruned (%s) - re-capturing",
                    attempt,
                    attempts,
                    section,
                    error,
                )
        raise AssertionError(
            f"Could not read the {section} models response body in {attempts} attempts: {last_error}"
        )

    def select_option(self, option_value: str) -> Locator:
        """Return the dropdown option whose value is *option_value*
        (``"{key}<<>>{project_id}"``) -- for asserting an option's presence,
        label and ``aria-selected`` state without selecting it.

        ``{key}`` is the model identifier (``data.name``) in every section
        EXCEPT Vector Storage, where it is the ``elitea_title``
        (``_surface.md``).
        """
        return self.page.locator(self.SELECT_OPTION.format(option_value))

    @property
    def open_select_options(self) -> Locator:
        """Every option of the currently-open dropdown (see
        :data:`SELECT_OPTION_PREFIX_SELECTOR`)."""
        return self.page.locator(self.SELECT_OPTION_PREFIX_SELECTOR)

    def close_open_dropdown(self) -> None:
        """Dismiss an open MUI dropdown without selecting anything (Escape) --
        so a spec that merely INSPECTS the option list leaves the project's
        default untouched."""
        self.page.keyboard.press("Escape")
        self.open_select_options.first.wait_for(state="detached", timeout=UI_ELEMENT_TIMEOUT)

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

    def card_status(self, model_display_name: str) -> Locator:
        """Return the status line ("OK • Shared" / "OK • Local") scoped inside
        the card for *model_display_name* (ELITEA-2402/2404/2406 step 3).

        See :data:`CARD_STATUS_SELECTOR`: this element also contains the tier /
        Default badges, so assert on it with ``to_contain_text(...)``, never an
        exact match.
        """
        return self.card_for_model(model_display_name).locator(self.CARD_STATUS_SELECTOR)

    def card_badges(self, model_display_name: str) -> Locator:
        """Return EVERY tier/Default badge inside the card for
        *model_display_name* -- for the "this card carries no badge at all"
        assertion (``to_have_count(0)``) that ELITEA-2403/2405/2407 step 6 needs.

        :meth:`card_tier_badge` filters by badge text and therefore cannot
        express "no badge of any kind"; this is its unfiltered sibling.
        """
        return self.card_for_model(model_display_name).locator(self.TIER_BADGE_SELECTOR)

    @property
    def all_default_badges(self) -> Locator:
        """Every ``Default`` badge currently rendered across the expanded
        section(s) -- for the exclusivity invariant "exactly ONE card is the
        default" (ELITEA-2403/2405/2407 Axis 2).

        Combine with :meth:`isolate_section` so the count is scoped to the
        section under test.
        """
        return self.page.locator(self.TIER_BADGE_SELECTOR).filter(has_text=re.compile(r"^Default$"))

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

    @property
    def configuration_cards(self) -> Locator:
        """Every ``ConfigurationCard`` currently rendered (all expanded
        sections together) -- the locator form of
        :meth:`get_configuration_card_count`, for web-first
        ``expect(...).to_have_count(n)`` assertions."""
        return self.page.locator(self.CONFIGURATION_CARD_SELECTOR)

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

    def all_section_headers(self) -> list[tuple[str, Locator]]:
        """Return the (label, header locator) pairs for ALL seven configuration
        sections, whether or not they currently render.

        Superset of :meth:`populated_section_headers` (which lists only the
        five that are populated for the shared ``${TEST_USER}`` project and is
        left untouched for its merged callers). Used by
        :meth:`isolate_section`, which must not leave a section expanded just
        because it happens to be empty on one project and populated on another.
        """
        return [
            ("LLMs", self.llms_section_header),
            ("Embedding Models", self.embedding_models_section_header),
            ("Vector Storage", self.vector_storage_section_header),
            ("Image Generation", self.image_generation_section_header),
            ("Speech Recognition (ASR)", self.asr_section_header),
            ("Text to Speech (TTS)", self.tts_section_header),
            ("AI Credentials", self.ai_credentials_section_header),
        ]

    def collapse_section(self, section_header: Locator, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Collapse an accordion section, if it renders at all and is expanded.

        Tolerant of an absent section by design: a section with zero configured
        items renders NOTHING (``ConfigurationSection.jsx`` returns ``null``),
        and which sections those are differs per project.
        """
        if section_header.count() == 0:
            return
        if section_header.get_attribute("aria-expanded") == "true":
            section_header.click()
            expect(section_header).to_have_attribute("aria-expanded", "false", timeout=timeout)

    def isolate_section(self, section_header: Locator, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Collapse every section, then expand *section_header* -- so that
        :attr:`configuration_cards` counts THIS section's cards and no others.

        The card testid (``ai-provider-configuration-card``) is generic and
        repeated per card, and cards are NOT descendants of their section's
        header element, so there is no locator that scopes a count to one
        section. Isolating the accordion state is the honest way to get a
        section-scoped count -- and it is not merely tidier than a
        whole-page count, it is *correct*: the LLMs section auto-expands only
        on a fresh page load, so a whole-page baseline taken before a Save and
        a whole-page count taken after the app's own navigation back are NOT
        comparable (measured: 15 before, 4 after, ELITEA-2398 first run).
        """
        section_header.wait_for(state="visible", timeout=timeout)
        for _label, header in self.all_section_headers():
            self.collapse_section(header, timeout=timeout)
        self.expand_section(section_header, timeout=timeout)

    def configuration_group(self, group_label: str) -> Locator:
        """Return the provider-group container whose label EXACTLY matches
        *group_label* (``"OpenAI"`` / ``"Anthropic"`` / ``"Other Providers"``
        ... -- ``GROUP_ORDER`` in ``ConfigurationSection.jsx``).

        Filters the group container on its dedicated
        :data:`CONFIGURATION_GROUP_NAME_SELECTOR` child rather than on its own
        text content, which concatenates the label with every card inside it
        (ELITEA-2395) -- the same shape as :meth:`card_for_model`.
        """
        pattern = re.compile(rf"^{re.escape(group_label)}$")
        name_locator = self.page.locator(self.CONFIGURATION_GROUP_NAME_SELECTOR).filter(has_text=pattern)
        return self.page.locator(self.CONFIGURATION_GROUP_SELECTOR).filter(has=name_locator)

    def card_in_group(self, group_label: str, model_display_name: str) -> Locator:
        """Return the ``ConfigurationCard`` for *model_display_name* scoped
        INSIDE the *group_label* provider group (ELITEA-2395 step 11).

        Scoping is the point: :meth:`card_for_model` proves the card exists,
        this proves it exists *in the right group*.
        """
        pattern = re.compile(rf"^{re.escape(model_display_name)}$")
        name_locator = self.page.locator(self.CARD_NAME_SELECTOR).filter(has_text=pattern)
        return (
            self.configuration_group(group_label)
            .locator(self.CONFIGURATION_CARD_SELECTOR)
            .filter(has=name_locator)
        )

    def open_model_card(self, model_display_name: str, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Click the configuration card for *model_display_name*, opening its
        edit form (ELITEA-2396).

        Settling on the form itself is the caller's step -- the edit form is
        schema-driven and mounts seconds after the route change, so
        :meth:`~pages.ai_provider_form_page.AiProviderFormPage.wait_for_form`
        (a rendered field, not the URL and not ``networkidle`` -- see
        `.agents/testing.md` #1847) is the honest "the form is up" signal.
        """
        card = self.card_for_model(model_display_name)
        card.wait_for(state="visible", timeout=timeout)
        card.click()
