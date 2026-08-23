"""Configuration OAuth dialog page object (shared ``McpAuthModal``).

Rendered by ``EliteaUI/src/[fsd]/features/mcp/ui/modal/McpAuthModal.jsx`` and
mounted by every OAuth-capable flow — the MCP toolkit flows, the OpenAPI and
SharePoint delegated-login buttons, and the credential form
(``CredentialForm.jsx:363``). It gets its own page object rather than fields
bolted onto :class:`CredentialDetailPage` precisely because it is shared: the
next case that opens it (from a toolkit or an MCP server) reuses this class.

Testids for the whole dialog tree were added for ELITEA-1982
(EliteaAI/EliteaUI@7d7b21d4) — the tree carried none. They are deliberately
GENERIC (``oauth-auth-dialog-*``), not credential-scoped, per
``.agents/testing.md`` § Locator policy's shared-component rule; the Scope
input's testid is passed INTO the shared ``OAuthFormFields`` via a
caller-supplied ``scopeTestId`` prop wired at ``McpAuthModal``'s call site.

⚠️ **presence != open.** ``McpAuthModal`` renders ``<Dialog open={open}
keepMounted>``, so the dialog subtree is ALWAYS in the DOM, and a *closed*
instance holds pre-open state (an empty ``Server:`` href, a Scope value
without the backend's ``offline_access`` prefix) — i.e. it mimics exactly the
failures ELITEA-1982's steps 5-6 look for. Every open/closed check therefore
goes through visibility (:meth:`wait_for_open` / :meth:`wait_for_closed`),
never through a count.
"""

import logging

from playwright.sync_api import Locator, Page

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.oauth_auth_modal")

UI_ELEMENT_TIMEOUT = 10_000


class OAuthAuthModalPage(BasePage):
    """The "Configuration OAuth" dialog (``McpAuthModal``)."""

    dialog = LocatorDescriptor(
        testid="oauth-auth-dialog",
        description=(
            "Dialog root (MUI Dialog, keepMounted — always present in the DOM; "
            "assert VISIBILITY, never count)"
        ),
    )
    dialog_title = LocatorDescriptor(
        testid="oauth-auth-dialog-title",
        description='Dialog title — "Configuration OAuth" for the credential flow',
    )
    dialog_description = LocatorDescriptor(
        testid="oauth-auth-dialog-description",
        description=(
            "Dialog message paragraph. Carries an optional trailing flow hint "
            "(requiresClientSecret / oidc / dcr / pkce) which is empty for a "
            "SharePoint credential's server."
        ),
    )
    server_link = LocatorDescriptor(
        testid="oauth-auth-dialog-server-link",
        description=(
            'The "Server:" value, rendered as an external link. Shows the '
            "credential's oauth_discovery_endpoint (passed as the display URL "
            "by useCreateConfiguration.jsx:183) — NOT auth_metadata.server_url."
        ),
    )
    scope_input = LocatorDescriptor(
        testid="oauth-auth-dialog-scope-input",
        description=(
            'The "Scope (optional)" field — the native <input>; the testid is '
            "supplied to the shared OAuthFormFields by McpAuthModal"
        ),
    )
    cancel_button = LocatorDescriptor(
        testid="oauth-auth-dialog-cancel-button",
        description="Cancel button — closes the dialog without authorizing",
    )
    authorize_button = LocatorDescriptor(
        testid="oauth-auth-dialog-authorize-button",
        description="Authorize button — starts the OAuth handshake in a popup",
    )

    # Scoped sub-selector (class-level constant containing the dialog's own
    # testid, per .agents/testing.md § Locator policy). Counts the inputs the
    # dialog actually renders: the Client Id / Client Secret fields are
    # conditional (needClientId / needsClientSecret) and carry no testids of
    # their own — canon #511 forbids adding testids to elements no test's
    # executed path touches, so their ABSENCE is asserted as "the dialog
    # renders exactly one input" instead.
    DIALOG_INPUTS = '[data-testid="oauth-auth-dialog"] input'

    def __init__(self, page: Page):
        super().__init__(page)

    @property
    def inputs(self) -> Locator:
        """Every ``<input>`` currently rendered inside the dialog."""
        return self.page.locator(self.DIALOG_INPUTS)

    def wait_for_open(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Wait for the dialog to become VISIBLE (not merely mounted)."""
        self.dialog.wait_for(state="visible", timeout=timeout)
        logger.info("Configuration OAuth dialog is open")

    def wait_for_closed(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Wait for the dialog to become hidden (it stays mounted — keepMounted)."""
        self.dialog.wait_for(state="hidden", timeout=timeout)
        logger.info("Configuration OAuth dialog is closed")

    def get_scope_value(self) -> str:
        """Return the Scope field's current value."""
        return self.scope_input.input_value()

    def clear_scope(self) -> None:
        """Clear the Scope field via select-all + Backspace, triggering onChange."""
        self.scope_input.click()
        self.scope_input.select_text()
        self.scope_input.press("Backspace")

    def click_cancel(self) -> None:
        """Click Cancel and wait for the dialog to be hidden."""
        self.cancel_button.click()
        self.wait_for_closed()
