"""Shared not-found (404) page object.

URL: any route whose entity lookup answers 404 — e.g.
``/credentials/all/{non-existent-id}``, ``/skills/{bad-id}``.

The app renders ONE shared component for every such route
(``EliteaUI/src/pages/Page404.jsx``), reached from a page's
``shouldShowNotFoundPage = isError && isNotFoundError(error)`` guard
(``EditCredential.jsx:160``; ``isNotFoundError`` is true for **404 and 400**,
``common/utils.jsx:144``). Its container testid ``page-not-found`` was added
via ``add-data-testid`` for ELITEA-1980 (EliteaAI/EliteaUI@54ce148e) — a
GENERIC testid on a shared component, never feature-scoped
(``.agents/testing.md`` § Locator policy), so every 404 route gains the handle.

**Timing note (ELITEA-1980, recorded in ``_surface.md``):** the not-found state
appears only AFTER the entity request resolves. Until then the route renders
its normal (empty, editable) page shell — on ``/credentials/all/{bad-id}`` that
is a blank credential form with Save/Discard. Callers must settle on the entity
response (``page.expect_response``), never on a timer, or they read the
loading state and mistake it for a missing 404 page.
"""

import logging

from config import settings

from .base_page import BasePage
from .locator_descriptor import LocatorDescriptor

logger = logging.getLogger("elitea.pages.not_found")

UI_ELEMENT_TIMEOUT = 10_000


class NotFoundPage(BasePage):
    """The app's shared 404 state (``Page404.jsx``)."""

    not_found_container = LocatorDescriptor(
        testid="page-not-found",
        description=(
            "Shared Page404 container — carries the 'Page not found. Try Home "
            "page' text and the Home-page link. Rendered by any route whose "
            "entity lookup returns 404/400."
        ),
    )

    def open_route(self, path: str) -> None:
        """Navigate to *path* and stop at ``domcontentloaded``.

        Deliberately NOT :meth:`BasePage.navigate`: that method waits up to 30 s
        for ``networkidle``, which the credentials routes never reach
        (``.agents/testing.md``; ELITEA-1964/1967) — it would burn the whole
        wait on every call. The caller settles on the entity request's own
        response instead, which is also what turns the route's transient page
        shell into the not-found state.
        """
        url = f"{settings.app_base_url}{path}" if not path.startswith("http") else path
        logger.info("Navigating to %s (domcontentloaded only)", url)
        self.page.goto(url, wait_until="domcontentloaded")

    def wait_for_not_found(self, timeout: int = UI_ELEMENT_TIMEOUT) -> None:
        """Wait for the shared not-found state to render."""
        self.not_found_container.wait_for(state="visible", timeout=timeout)
        logger.info("Not-found (Page404) state rendered at %s", self.page.url)

    def get_not_found_text(self) -> str:
        """Return the not-found container's rendered text."""
        return self.not_found_container.inner_text().strip()
