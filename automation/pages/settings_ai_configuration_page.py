"""Settings -> General -> "AI Configurations" accordion page object.

URL: ``/settings/project-general`` (the sidebar Settings button hardcodes this
route -- see :mod:`pages.settings_drawer_page`).

**There is no page or nav item called "AI Configuration" in the live product.**
TMS cases that say "Settings -> AI Configuration" and describe Basic /
OpenAI Template tabs or the ``OpenAI-BaseURL`` / ``Server URL`` /
``OpenAI-Project`` / ``Project ID`` fields mean *this* accordion on Settings ->
General. Cases describing LLM / Embedding / AI-Credentials *sections* mean the
separate Settings -> AI Providers page. See
``test-specs/settings-ai-configurations/_surface.md`` § Page identity.

Component tree (EliteaUI ``src/[fsd]/features/settings/ui/project-general/``):
``ProjectGeneralContent.jsx`` (the ``BasicAccordion``) ->
``project-ai-configurations/ProjectAIConfigurations.jsx`` (holds ``selectedTab``
in a component-local ``useState``, default ``Basic``) ->
``AIConfigurationToggle.jsx`` (the two-button ``Tab.TabGroupButton``) -> either
``AIConfiguration.jsx`` (Basic) or ``open-ai-template/`` (the code template).

Two behaviours this page object exists to encode:

* **A tab switch fires no network request.** Both panels are fed by the same
  already-cached RTK-Query results, so the switch is a pure client-side
  re-render -- wait on the target panel's testid, never on the network
  (``networkidle`` is unusable on this app anyway, ``.agents/testing.md`` #1847).
* **The tab is component-local state with no URL reflection**, so a page reload
  resets it to Basic. Never reload mid-round-trip.

Locator provenance (`test-specs/settings-ai-configurations/_surface.md`
§ Testids, verified `git fetch origin` 2026-08-29):
``ai-configurations`` -- pre-existing, on ``main`` and ``automation/testids``.
Every other testid below was added by this implementation
(EliteaAI/EliteaUI@2deb9655 and EliteaAI/EliteaUI@7418c06f): before it, the
accordion's only ``[data-testid]`` node was an MUI icon. All eight ride
mechanisms the components already expose -- ``BasicAccordion``'s
``items[].testId``, ``TabButtonItem``'s ``{...item.buttonProps}``, and
``FieldWithCopy``'s ``testId`` prop -- so no component plumbing was added.

Tab selection state is read from the toggles' native ``aria-pressed``, never
from a state-named testid (``.agents/testing.md`` § Locator policy, PR #581).
"""

import logging
from urllib.parse import urlsplit

from playwright.sync_api import Locator, Page, Response, expect
from utils.actions import action

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.settings_ai_configuration")

#: Settings -> General, where the AI Configurations accordion lives.
SETTINGS_GENERAL_PATH = "/settings/project-general"

#: A non-settings route to start from, so clicking the sidebar Settings button
#: is a real navigation rather than a no-op (ELITEA-2394 steps 1-2).
NON_SETTINGS_START_PATH = "/agents/all"


class SettingsAIConfigurationPage(BasePage):
    """The "AI Configurations" accordion on Settings -> General."""

    ai_configurations_panel = LocatorDescriptor(
        testid="ai-configurations",
        description="AI Configurations accordion root (summary + both tab panels)",
    )

    accordion_summary = LocatorDescriptor(
        testid="ai-configuration-accordion-summary",
        description="AI Configurations accordion summary; expand state on its "
        "`aria-expanded` attribute (expanded by default)",
    )

    tab_basic_button = LocatorDescriptor(
        testid="ai-configuration-tab-basic-button",
        description='"Basic" tab toggle; selection state on `aria-pressed`',
    )

    tab_openai_template_button = LocatorDescriptor(
        testid="ai-configuration-tab-openai-template-button",
        description='"OpenAI Template" tab toggle; selection state on `aria-pressed`',
    )

    openai_base_url_value = LocatorDescriptor(
        testid="ai-configuration-openai-base-url-value",
        description="Basic tab -- `OpenAI-BaseURL:` value",
    )

    server_url_value = LocatorDescriptor(
        testid="ai-configuration-server-url-value",
        description="Basic tab -- `Server URL:` value",
    )

    openai_project_value = LocatorDescriptor(
        testid="ai-configuration-openai-project-value",
        description="Basic tab -- `OpenAI-Project:` value (the DEFAULT LLM "
        "MODEL's project id, not the selected project's -- the whole row is "
        "conditionally rendered and absent when no default model exists)",
    )

    project_id_value = LocatorDescriptor(
        testid="ai-configuration-project-id-value",
        description="Basic tab -- `Project ID:` value (the selected project)",
    )

    code_preview_editor = LocatorDescriptor(
        testid="ai-configuration-code-preview-editor",
        description="OpenAI Template tab -- read-only CodeMirror container. "
        "Read the code with `inner_text()` on this container; never address "
        "CodeMirror's internal `.cm-line` nodes.",
    )

    code_preview_empty = LocatorDescriptor(
        testid="ai-configuration-code-preview-empty",
        description="OpenAI Template tab -- the 'Select a LLM Model to see "
        "Code examples' empty state, rendered INSTEAD of the editor when the "
        "project has no default LLM model. Referenced only by an absence "
        "assertion on the executed path (canon ruling #511 extension).",
    )

    #: The four Basic-tab fields, keyed by field name -> the label
    #: ``AIConfiguration.jsx`` renders beside the value. Asserting the labels
    #: alongside the values proves the four testids still point at the fields
    #: the case names, not at four arbitrary populated nodes.
    BASIC_FIELD_LABELS = {
        "openai_base_url": "OpenAI-BaseURL:",
        "server_url": "Server URL:",
        "openai_project": "OpenAI-Project:",
        "project_id": "Project ID:",
    }

    #: Markers identifying the page's own default-LLM-model request, whose
    #: ``{project_id}`` path segment is the honest oracle for the ``Project ID``
    #: field (the product's own value, not a constant the test chose).
    #: Shape: ``GET .../configurations/models/{project_id}?...&section=llm``.
    LLM_MODELS_REQUEST_MARKERS = ("/configurations/models/", "section=llm")

    # Scoped compound selector -- any MUI progress indicator rendered INSIDE the
    # accordion. Class-level UPPER_CASE constant per
    # `.claude/rules/page-objects.md` "Scoped selectors"; see
    # `panel_progress_indicators()` for why the child half is a role and not a
    # testid.
    PANEL_PROGRESS_INDICATORS = '[data-testid="ai-configurations"] [role="progressbar"]'

    def __init__(self, page: Page):
        super().__init__(page)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    @action("Open Settings via the sidebar")
    def open_via_sidebar(self, timeout: int = 30000) -> Response:
        """Start on a non-settings route, click sidebar 'Settings', wait for the panel.

        Returns the page's own ``section=llm`` models response, captured across
        the click -- :meth:`project_id_from_models_url` turns it into the
        selected project id, which is what the ``Project ID`` field must equal.
        Reading it from the product's own request keeps the assertion honest and
        environment-independent (the selected project is browser-persisted and
        differs between sessions -- never hardcode 399/400).

        Args:
            timeout: Maximum wait time in milliseconds

        Returns:
            The ``section=llm`` models ``Response`` the settings page fired
        """
        self.navigate(NON_SETTINGS_START_PATH)
        with self.page.expect_response(self._is_llm_models_response, timeout=timeout) as response_info:
            self.sidebar_settings_button.click()
        self.ai_configurations_panel.wait_for(state="visible", timeout=timeout)
        return response_info.value

    @action("Open Settings -> General directly")
    def navigate_to_general(self, timeout: int = 30000) -> None:
        """Load ``/settings/project-general`` and wait for the accordion.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        self.navigate(SETTINGS_GENERAL_PATH)
        self.ai_configurations_panel.wait_for(state="visible", timeout=timeout)

    @classmethod
    def _is_llm_models_response(cls, response: Response) -> bool:
        """True for the page's default-LLM-model listing request."""
        return all(marker in response.url for marker in cls.LLM_MODELS_REQUEST_MARKERS)

    @staticmethod
    def project_id_from_models_url(url: str) -> str:
        """Project id carried by a ``configurations/models/{project_id}`` URL.

        The id is the last path segment; the query string (``include_shared``,
        ``section``) is discarded.

        Args:
            url: Full request URL

        Returns:
            The ``{project_id}`` path segment
        """
        return urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1]

    # ------------------------------------------------------------------
    # Tabs
    # ------------------------------------------------------------------

    @action("Select the Basic tab")
    def select_basic_tab(self, timeout: int = 15000) -> None:
        """Click "Basic" and wait for the toggle to report itself pressed.

        No request fires on a tab switch, so `aria-pressed` -- the product's own
        selection signal -- is what we wait on.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        self.tab_basic_button.click()
        expect(self.tab_basic_button).to_have_attribute("aria-pressed", "true", timeout=timeout)
        logger.info("Selected the Basic tab")

    @action("Select the OpenAI Template tab")
    def select_openai_template_tab(self, timeout: int = 15000) -> None:
        """Click "OpenAI Template" and wait for the toggle to report itself pressed.

        Args:
            timeout: Maximum wait time in milliseconds
        """
        self.tab_openai_template_button.click()
        expect(self.tab_openai_template_button).to_have_attribute(
            "aria-pressed", "true", timeout=timeout
        )
        logger.info("Selected the OpenAI Template tab")

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def basic_field_value(self, field: str) -> Locator:
        """Value node of one Basic-tab *field* (a :attr:`BASIC_FIELD_LABELS` key)."""
        return {
            "openai_base_url": self.openai_base_url_value,
            "server_url": self.server_url_value,
            "openai_project": self.openai_project_value,
            "project_id": self.project_id_value,
        }[field]

    def basic_field_texts(self) -> dict[str, str]:
        """Rendered text of all four Basic-tab values, stripped.

        Returns:
            ``{field_key: text}`` for every :attr:`BASIC_FIELD_LABELS` key
        """
        texts = {field: self.basic_field_value(field).inner_text().strip() for field in self.BASIC_FIELD_LABELS}
        logger.info("Basic tab field values: %s", texts)
        return texts

    def code_template_text(self) -> str:
        """Text of the read-only code template, stripped.

        Read off the container testid rather than CodeMirror's internal
        per-line nodes, which are library-internal DOM.
        """
        return self.code_preview_editor.inner_text().strip()

    def panel_progress_indicators(self) -> Locator:
        """Handle for asserting that **no** loading spinner is left inside the panel.

        DECLARED IMPROVISATION -- canon gap, escalated to the lead
        (``.agents/role-overrides.md`` § Declared-improvisation protocol), NOT
        the #579 exception. #579 sanctions a scoped raw handle only for a
        third-party widget subtree or a third-party editor library's internal
        nodes; this accordion is first-party EliteaUI JSX we own, where a
        missing testid is normally "work to do".

        Why "add the testid" is not an available action here: ELITEA-2394 step 9
        requires that no *permanent loading spinner* is shown, and
        ``AIConfiguration.jsx`` renders **no spinner at all** -- there is no JSX
        node to attach a testid to. The absence-assertion rulings in
        ``.agents/testing.md`` (#511 extension, #277) both presuppose a testid
        on an alternate branch that exists; they do not cover "the branch was
        never authored". Same shape and same open canon question as
        :meth:`pages.settings_drawer_page.SettingsDrawerPage.drawer_logout_controls`.

        Chosen shape, and why it is the most spirit-compliant option available:
        an ARIA-role child handle scoped inside the real app testid parent
        (``ai-configurations``), never free-floating at page level -- the same
        bounded-blast-radius discipline #579 requires. ``role="progressbar"`` is
        MUI ``CircularProgress``'s own contract, so it catches any spinner the
        component tree might grow later, which a hand-placed testid could not.
        Do not extend this shape to any handle that COULD carry a testid.
        """
        return self.page.locator(self.PANEL_PROGRESS_INDICATORS)
