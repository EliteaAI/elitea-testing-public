"""Shared recovery helper for the known ``/credentials/all`` refetch race.

Known defect (github.com/EliteaAI/elitea-testing-public#518):
``CredentialsList.jsx``'s mount effect calls ``onRefetch()`` twice
unconditionally on this exact pathname, and ``useLoadCredentials.js``'s
underlying RTK Query ``refetch()`` throws "Cannot refetch a query that has
not been started yet" when the query hasn't started — an unhandled error
that trips the route's error boundary. Live-verified at a ~60% reproduction
rate during ELITEA-1971 exploration, and again live during ELITEA-1975
(create-credential flow, same ``/credentials/all`` entry point).

This is a recovery-only helper (not a test locator/assertion) — text match
against the app's generic React-Router error boundary output, the same
"workaround, not policy exception" pattern as
``BasePage.dismiss_banner_if_present()``. Extracted to a shared module
(rather than duplicated per page object, per ``.claude/rules/page-objects.md``
"NO Method Duplication") since both :class:`CredentialDetailPage` and
:class:`CredentialCreatePage` land on ``/credentials/all`` as a precondition
and can hit the same out-of-scope race.
"""

import logging

from playwright.sync_api import Page

logger = logging.getLogger("elitea.pages.credentials_list_recovery")


def recover_from_credentials_list_crash(page: Page) -> bool:
    """Reload once if ``/credentials/all`` crashed with the known refetch race.

    Args:
        page: The Playwright ``Page`` currently on (or navigating through)
            ``/credentials/all``.

    Returns:
        True if the crash was detected and recovered from.
    """
    crashed = page.get_by_text("Unexpected Application Error!").count() > 0
    if crashed:
        logger.warning(
            "Recovering from known CredentialsList crash (elitea-testing-public#518) — reloading"
        )
        page.reload(wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle", timeout=15000)
    return crashed
