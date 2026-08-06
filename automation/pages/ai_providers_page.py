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

Vector Storage and AI Credentials never render any of the above for the
shared ``${TEST_USER}`` project (zero configured items) -- their section
header locators are still defined (referenced via absence assertions,
canon ruling #511 extension) but their selector/card testids never mount.
"""

import logging

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

    # Generic, repeated-per-card testid (same pattern as `secret-row` /
    # `token_row`) -- scoped sub-selector constant per
    # `.agents/testing.md` Locator policy.
    CONFIGURATION_CARD_SELECTOR = '[data-testid="ai-provider-configuration-card"]'

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
