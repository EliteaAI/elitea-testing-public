"""Fixtures for the Onboarding surface (cov60 campaign foundation pass).

Provides ``fresh_user_route``, a route-interception fixture that simulates a
"never-onboarded" user on localhost. See the Declared Improvisation in
test-specs/onboarding/l2_sure-lets-go-triggers-provisioning-and-onboarding-tips_ELITEA-2232.md
for why this technique exists: on localhost every API call carries a fixed
dev token for one persistent backend user whose ``personal_project_id`` is
already set, and there is no in-app signup route — so a genuinely fresh-user
precondition is structurally unreachable via the normal ``auth_state``
fast-path.

Mechanism: intercept ONLY ``GET **/api/v2/social/author/`` — the single
endpoint that seeds Redux ``state.user`` (``authorDetails.matchFulfilled`` in
``EliteaUI/src/slices/user.js``) — via ``route.fetch()``, which replays the
real request (including whatever auth header the app attaches) through
Playwright's network stack, then re-fulfills with the SAME body except
``personal_project_id`` forced to ``None``. Every other field (id, email,
name, ...) stays exactly as the real authenticated user's real values. This
reproduces the exact Redux state a genuinely new user would have, through
the SAME code path the real app uses — no ``page.evaluate()`` state
injection.
"""

import logging

import pytest
from playwright.sync_api import Page, Route

logger = logging.getLogger("elitea.automation.fixtures.onboarding")

AUTHOR_DETAILS_ROUTE = "**/api/v2/social/author/"


class FreshUserRoute:
    """Controls the ``social/author/`` route mock installed by ``fresh_user_route``.

    While ``simulate_fresh`` is True (the default after installation), every
    matching response is returned with ``personal_project_id`` forced to
    ``None`` — reproducing a brand-new, never-onboarded user. Call
    ``mark_provisioning_complete()`` to switch the mock back to the real,
    captured ``personal_project_id``, simulating provisioning finishing.
    """

    def __init__(self, page: Page):
        self.page = page
        self._real_body: dict | None = None
        self.simulate_fresh = True

    def _handle(self, route: Route) -> None:
        response = route.fetch()
        body = response.json()
        if self._real_body is None:
            # Cache the real authenticated user's body exactly once — every
            # other field stays real; only personal_project_id is ever
            # substituted.
            self._real_body = dict(body)
            logger.info(
                "fresh_user_route: captured real author body (user id=%s)",
                self._real_body.get("id"),
            )
        mocked = dict(self._real_body)
        if self.simulate_fresh:
            mocked["personal_project_id"] = None
        route.fulfill(response=response, json=mocked)

    def install(self) -> None:
        """Start intercepting ``GET **/api/v2/social/author/``."""
        self.page.route(AUTHOR_DETAILS_ROUTE, self._handle)

    def mark_provisioning_complete(self) -> None:
        """Switch the mock back to the real (non-null) ``personal_project_id``.

        Simulates provisioning finishing — the onboarding tour's 5s poll
        (``Onboarding.jsx``'s ``handleShowTour`` interval) picks this up on
        its next cycle.
        """
        self.simulate_fresh = False
        logger.info("fresh_user_route: switched to real personal_project_id")


@pytest.fixture
def fresh_user_route(page: Page):
    """Simulate a never-onboarded user via ``social/author/`` route interception.

    Installs the mock before the test navigates anywhere, so the very first
    ``GET /api/v2/social/author/`` (fired on protected-route mount) already
    returns ``personal_project_id: null``. Call ``.mark_provisioning_complete()``
    once the test needs to observe the "ready" (post-provisioning) state.

    Yields:
        FreshUserRoute: call ``.mark_provisioning_complete()`` when needed.
    """
    route = FreshUserRoute(page)
    route.install()
    yield route
