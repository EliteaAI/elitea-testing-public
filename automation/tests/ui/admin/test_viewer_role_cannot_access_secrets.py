"""UI test — a user acting under the Viewer role is not offered the Secrets
section in the Settings drawer, while the same user IS offered it in a project
where they hold the secrets permission.

Read-only case (`.agents/testing.md` § Test data strategy): nothing is created,
edited or deleted. Only the active project selection moves, and it is restored
in a `finally` because that selection is app state shared with every other spec.

Test case: ELITEA-2348
AFS: test-specs/settings-secrets/l3_viewer-role-cannot-access-secrets_ELITEA-2348.md

No second identity, and no substitution
---------------------------------------
Elitea roles are PROJECT-scoped, and the shared ${TEST_USER} genuinely holds
different roles in different projects (verified live 2026-08-28 via
`GET /admin/users/prompt_lib/{project_id}`): `viewer` in project 471
(`settings.elitea_team_project_id`), `editor`+`viewer` in project 399
(`settings.elitea_project_id`). `useCheckPermission` reads
`state.user.permissions`, refetched per selected project — project 471 returns
158 permissions with ZERO `configuration.secrets.*`, project 400 returns 360
including 8 of them. So switching the project selector puts the app in a real,
product-computed viewer state. Nothing is injected, stubbed or forced.

Case-text drift — the Monitor half is un-executable, not skipped
----------------------------------------------------------------
The case's steps 4-6 ask to repeat the check as a "Monitor" role. **Elitea has
no Monitor role**: `GET /admin/roles/default/{p}` returns
`['admin','editor','viewer']` for all five selectable projects, and
`grep -rni "monitor" ../EliteaUI/src/` has zero hits. There is no observable to
assert — this is not a masked step, it is a subject the product does not have.
Filed as clarification EliteaAI/elitea-testing-public#1909; the AFS Coverage
Map marks steps 4-6 `un-executable` with that pointer.

Why the deep-linked route is NOT asserted
------------------------------------------
The case's step 3 is an explicit OR — "not visible in the sidebar OR shows an
Access Denied error". The product satisfies the SIDEBAR branch. Deep-linking
`/settings/secrets` on the viewer project still renders the page with an
enabled "+" and no access-denied state, which is the already-filed, OPEN bug
EliteaAI/elitea-testing-public#1773. Asserting that branch would make this spec
a duplicate red for #1773 rather than coverage of ELITEA-2348. It would also
drag in #1203's UNBOUNDED render loop on that route (144 console errors
measured live on project 471).

Markers:
    - ui: requires browser
    - admin: settings/admin surface
    - p2: priority (per AFS metadata: l3 — case frontmatter `priority: medium`)
    - regression
"""

import logging

import allure
import pytest
from config import settings
from pages.settings_drawer_page import SettingsDrawerPage
from playwright.sync_api import expect

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

SECRETS_TAB_ID = "secrets"
CONTROL_TAB_ID = "project-general"
SETTINGS_PATH = "/settings/project-general"
UI_ELEMENT_TIMEOUT = 10_000


def restore_active_project(drawer: SettingsDrawerPage, project_id) -> None:
    """Return the session to *project_id* — UNCONDITIONALLY.

    Cleanup must never be keyed on the element the test asserts. The first
    shape of this guard read ``if not drawer.nav_item(SECRETS_TAB_ID).count()``
    ("am I still on a vantage that hides Secrets?"), which fails OPEN on exactly
    the regression this spec hunts: if the Secrets entry is wrongly PRESENT on
    the viewer project, ``count()`` is non-zero, the restore is skipped, and
    every later spec in the invocation inherits the viewer project as its
    active one — the ``#1082`` shared-state pollution class, triggered by the
    one outcome that matters. Re-selecting the already-active project is a
    harmless no-op, so guarding bought nothing and cost the failure path.

    A failure inside the restore is logged, never raised: an exception here
    would replace the test's real failure with the cleanup's.

    Pinned by ``tests/unit/test_secrets_access_and_error_spec_invariants.py``.
    """
    try:
        drawer.switch_project(project_id)
    except Exception:
        logger.exception("Failed to restore the active project to %s", project_id)


class TestViewerRoleCannotAccessSecrets:
    """ELITEA-2348 — the Settings drawer offers no Secrets entry while the user
    acts under the Viewer role, and offers it again the moment they return to a
    project where they hold the secrets permission."""

    def _assert_drawer_healthy(self, drawer: SettingsDrawerPage) -> list[str]:
        """Prove the drawer actually rendered before reading an ABSENCE from it.

        Without this, a `to_have_count(0)` on the Secrets entry would pass just
        as happily if the whole drawer failed to render — the classic vacuous
        absence assertion.
        """
        expect(drawer.settings_drawer_menu).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        expect(drawer.nav_item(CONTROL_TAB_ID)).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        nav_ids = drawer.nav_item_ids_in_order()
        assert len(nav_ids) > 1, (
            "Drawer-health guard — expected a populated Settings nav so the "
            f"Secrets-absence assertion is meaningful, got {nav_ids}"
        )
        return nav_ids

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/secrets/ELITEA-2348_viewer-and-monitor-roles-cannot-access-secrets-section.md",
        "onetest-ai Test Case link",
    )
    def test_viewer_role_is_not_offered_the_secrets_section(self, page):
        drawer = SettingsDrawerPage(page)
        control_project = settings.elitea_project_id
        viewer_project = settings.elitea_team_project_id

        try:
            with allure.step(
                f"Step 1 — Control: on project {control_project} (user holds "
                "the secrets permission) the Settings drawer DOES offer Secrets"
            ):
                drawer.navigate(SETTINGS_PATH)
                nav_ids = self._assert_drawer_healthy(drawer)
                expect(drawer.nav_item(SECRETS_TAB_ID)).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                assert SECRETS_TAB_ID in nav_ids, (
                    "Control vantage — the Secrets entry must be present where the "
                    f"user holds `configuration.secrets.secret.list`; nav was {nav_ids}"
                )
                logger.info("Control project %s nav: %s", control_project, nav_ids)

            with allure.step(
                f"Step 2 — Switch to project {viewer_project}, where the user's "
                "only role is Viewer: the Secrets entry is NOT offered"
            ):
                drawer.switch_project(viewer_project)
                nav_ids = self._assert_drawer_healthy(drawer)
                # Absence assertion on a real testid (canon #511 extension) —
                # auto-retrying, so a slow per-project permission refetch cannot
                # produce a false green.
                expect(drawer.nav_item(SECRETS_TAB_ID)).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )
                assert SECRETS_TAB_ID not in nav_ids, (
                    "Case step 3 — a Viewer must not be offered the Secrets section; "
                    f"nav was {nav_ids}"
                )
                logger.info("Viewer project %s nav: %s", viewer_project, nav_ids)

            with allure.step(
                "Step 3 — Re-verify on a fresh load: the hiding survives a full "
                "remount, not just an in-session permission refetch"
            ):
                drawer.navigate(SETTINGS_PATH)
                nav_ids = self._assert_drawer_healthy(drawer)
                expect(drawer.nav_item(SECRETS_TAB_ID)).to_have_count(
                    0, timeout=UI_ELEMENT_TIMEOUT
                )
                assert SECRETS_TAB_ID not in nav_ids, (
                    "Case step 3 (fresh load) — a Viewer must not be offered the "
                    f"Secrets section after a full page load; nav was {nav_ids}"
                )

            with allure.step(
                f"Step 4 — Return to project {control_project}: Secrets is offered "
                "again, proving the difference is role-driven and reversible"
            ):
                drawer.switch_project(control_project)
                expect(drawer.nav_item(SECRETS_TAB_ID)).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
        finally:
            # The active project is app state shared with every other spec in
            # the suite (e.g. test_settings_sidebar_item_navigation.py clicks
            # the `secrets` tab on the default project). Never leave the
            # session parked on the viewer project — restore unconditionally,
            # see :func:`restore_active_project` for why no guard is correct.
            restore_active_project(drawer, control_project)
