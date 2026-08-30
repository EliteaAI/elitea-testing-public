"""UI test — every authenticated role can reach the PERSONAL settings sections
the case names (Preferences, Personal Tokens, Notifications), each loading
without a permission error.

Read-only case (`.agents/testing.md` § Test data strategy): nothing is created,
edited or deleted — pure navigation across three role vantages. Only the active
project selection moves, and it is restored in a `finally` because that
selection is app state shared with every other spec (the `#1082` pollution
class).

Test case: ELITEA-2247
AFS: test-specs/settings-navigation/l2_all-roles-access-personal-settings-sections_ELITEA-2247.md

The role vantages are real — nothing is substituted
----------------------------------------------------
Elitea roles are PROJECT-scoped, so the shared ${TEST_USER} genuinely holds a
different role in each project, and switching the sidebar project selector
re-fetches `state.user.permissions` for the newly selected project. Verified
live 2026-08-30 via `GET /admin/users/prompt_lib/{id}` +
`GET /auth/permissions/prompt_lib/{id}`:

    admin   -> project 400 "UI Testing"           (360 permissions, 8 `*secret*`)
    editor  -> project 399 "Private"              (299 permissions, 6 `*secret*`)
    viewer  -> project 471 "Elitea Testing Team"  (158 permissions, 0 `*secret*`)

Each parameter therefore exercises a genuinely different, product-computed role
state. No injected state, no fabricated permission payload, no stubbed client
(`.agents/testing.md` § Fidelity policy).

Case-text drift — this test asserts the LIVE contract
------------------------------------------------------
  * The case asks for "all four roles" including **Monitor**. Elitea has
    exactly THREE roles: `GET /admin/roles/default/{id}` returns
    `['admin','editor','viewer']` for every project checked, and
    `grep -rni "monitor" ../EliteaUI/src/` has zero hits. The Monitor step is
    **un-executable, not skipped** — there is no such role to act as, so there
    is no observable to assert. Same disposition ELITEA-2348's merged spec
    already took. Clarification EliteaAI/elitea-testing-public#1909.
  * The case calls the first section "Personalization"; the live product calls
    it **Preferences** (`settings-nav-item-preferences`). Clarification
    EliteaAI/elitea-testing-public#1772.

Both are already-OPEN clarifications; new occurrences were commented there
rather than re-filed.

Why the vantage guard is load-bearing
--------------------------------------
Personal settings are user-scoped, so all three parameters assert the same
sections for the same human — which is exactly the case's claim ("no project
role gates the personal sections"), but it also means a project switch that
silently failed would let all three parameters pass identically while proving
nothing about roles. Step 1 therefore asserts a role-DISCRIMINATING observable
before the personal walk: the Secrets nav entry is offered on 400/399 and has
count 0 on 471, mirroring the permission counts above. This is the same product
signal ELITEA-2348's merged spec asserts, reused here purely as a guard.

Why "no permission error" is asserted at the transport layer too
-----------------------------------------------------------------
On this product a permission failure can surface as a 403 with **no**
access-denied UI at all — that is the shape of the open bug #1773 on the
Secrets route — so a text-only denial regex can pass over a real denial.
`utils.api_failures.collect_api_failures` records the `/api/v2/` responses the
page actually received, and each section is asserted against its own slice.

Markers:
    - ui: requires browser
    - settings: settings pages tests
    - p2: priority (per AFS metadata: l2 — case frontmatter `priority: high`)
    - regression
"""

import logging
import re

import allure
import pytest
from config import settings
from pages.settings_drawer_page import SettingsDrawerPage
from playwright.sync_api import expect
from utils.api_failures import collect_api_failures
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.settings, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

SETTINGS_PATH = "/settings/project-general"
UI_ELEMENT_TIMEOUT = 10_000
CONTENT_TIMEOUT = 30_000

SECRETS_TAB_ID = "secrets"

#: The three PERSONAL sections the case names, keyed by live tab id, with the
#: heading each one renders in the content pane (live-observed 2026-08-30).
#: `preferences` is the case's "Personalization" (clarification #1772).
PERSONAL_SECTIONS = [
    ("preferences", "Preferences"),
    ("tokens", "Personal Tokens"),
    ("notifications", "Notifications Center"),
]

NON_BLANK_PATTERN = re.compile(r"\S")

ACCESS_DENIED_PATTERN = re.compile(
    r"access denied|forbidden|403|not authorized|no permission", re.IGNORECASE
)


def restore_active_project(drawer: SettingsDrawerPage, project_id) -> None:
    """Return the session to *project_id* — UNCONDITIONALLY.

    Cleanup is never keyed on anything this test asserts: a guard would fail
    OPEN on exactly the regression that matters, leaving every later spec in
    the invocation running against a vantage project (the `#1082` shared-state
    pollution class). Re-selecting an already-active project is a harmless
    no-op, so guarding would buy nothing and cost the failure path.

    A failure inside the restore is logged, never raised — an exception here
    would replace the test's real failure with the cleanup's. Same shape as
    `tests/ui/admin/test_viewer_role_cannot_access_secrets.py`.
    """
    try:
        drawer.ensure_project_selected(project_id)
    except Exception:
        logger.exception("Failed to restore the active project to %s", project_id)


class TestAllRolesAccessPersonalSections:
    """ELITEA-2247 — all authenticated roles can access the PERSONAL settings
    sections."""

    def _assert_drawer_healthy(self, drawer: SettingsDrawerPage) -> list[str]:
        """Prove the drawer actually rendered before reading anything off it.

        Without this guard the Secrets-absence half of the vantage guard is
        vacuous — a drawer that failed to render satisfies it just as happily
        as a correctly permission-gated one.
        """
        expect(drawer.settings_drawer_menu).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        nav_ids = drawer.nav_item_ids_in_order()
        assert len(nav_ids) > 1, (
            "Drawer-health guard — expected a populated Settings nav before "
            f"reading the PERSONAL inventory, got {nav_ids}"
        )
        return nav_ids

    @pytest.mark.parametrize(
        "role,project_id_attr,expects_secrets",
        [
            ("admin", "elitea_admin_project_id", True),
            ("editor", "elitea_project_id", True),
            ("viewer", "elitea_team_project_id", False),
        ],
        ids=["admin", "editor", "viewer"],
    )
    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2247_all-authenticated-roles-can-access-personal-settings-section.md",
        "onetest-ai Test Case link",
    )
    def test_all_roles_can_access_personal_settings_sections(
        self, page, role, project_id_attr, expects_secrets
    ):
        """In each real role vantage, Preferences / Personal Tokens /
        Notifications are all offered in the PERSONAL group, each loads its own
        route with its own heading, none shows an access-denied state or
        produces a failing API response, and no console error is logged."""
        drawer = SettingsDrawerPage(page)
        console_errors = collect_console_errors(page)
        api_failures = collect_api_failures(page)

        project_id = getattr(settings, project_id_attr)
        default_project = settings.elitea_project_id

        try:
            with allure.step(
                f"Step 1 — Switch to project {project_id}, where the acting "
                f"user's role is {role}, and open Settings"
            ):
                drawer.navigate(SETTINGS_PATH)
                self._assert_drawer_healthy(drawer)
                drawer.ensure_project_selected(project_id)
                nav_ids = self._assert_drawer_healthy(drawer)

                # Vantage guard — a role-DISCRIMINATING observable, so a
                # project switch that silently failed cannot let all three
                # parameters pass identically. Absence is asserted with an
                # auto-retrying `to_have_count(0)` (canon #511 extension) so a
                # slow per-project permission refetch cannot fake a green.
                if expects_secrets:
                    expect(drawer.nav_item(SECRETS_TAB_ID)).to_be_visible(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                    assert SECRETS_TAB_ID in nav_ids, (
                        f"Vantage guard — the {role} vantage (project "
                        f"{project_id}) holds the secrets permission, so the "
                        f"Secrets entry must be offered; drawer was {nav_ids}"
                    )
                else:
                    expect(drawer.nav_item(SECRETS_TAB_ID)).to_have_count(
                        0, timeout=UI_ELEMENT_TIMEOUT
                    )
                    assert SECRETS_TAB_ID not in nav_ids, (
                        f"Vantage guard — the {role} vantage (project "
                        f"{project_id}) holds NO secrets permission, so the "
                        f"Secrets entry must be absent; drawer was {nav_ids}"
                    )
                logger.info("Vantage %s (project %s) nav: %s", role, project_id, nav_ids)

            with allure.step(
                "Step 2 — Verify the three PERSONAL sections the case names are "
                "offered, under the PERSONAL group header"
            ):
                expect(drawer.section_header("personal")).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                for tab_id, _heading in PERSONAL_SECTIONS:
                    expect(drawer.nav_item(tab_id)).to_be_visible(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                    assert tab_id in nav_ids, (
                        f"Case step {role} — the PERSONAL section '{tab_id}' must "
                        f"be offered in the {role} vantage; drawer was {nav_ids}"
                    )

            for tab_id, heading in PERSONAL_SECTIONS:
                with allure.step(
                    f"Step 3 — Open PERSONAL section '{tab_id}' in the {role} "
                    "vantage; it routes, selects, renders its own heading and "
                    "shows no permission error in the UI or on the wire"
                ):
                    console_mark = len(console_errors)
                    api_mark = len(api_failures)

                    drawer.click_nav_item(tab_id)

                    expect(page).to_have_url(
                        re.compile(rf"/settings/{re.escape(tab_id)}(\?.*)?$"),
                        timeout=UI_ELEMENT_TIMEOUT,
                    )
                    expect(drawer.nav_item(tab_id)).to_have_attribute(
                        "data-active", "true", timeout=UI_ELEMENT_TIMEOUT
                    )
                    expect(drawer.settings_content).to_be_visible(
                        timeout=CONTENT_TIMEOUT
                    )
                    expect(drawer.settings_content).to_contain_text(
                        NON_BLANK_PATTERN, timeout=CONTENT_TIMEOUT
                    )
                    # The section's own heading — proves the RIGHT personal page
                    # rendered, not merely that the pane is non-blank.
                    expect(drawer.settings_content).to_contain_text(
                        heading, timeout=CONTENT_TIMEOUT
                    )

                    content_text = drawer.settings_content.inner_text()
                    denial = ACCESS_DENIED_PATTERN.search(content_text)
                    assert denial is None, (
                        f"Case step 5 — PERSONAL section '{tab_id}' rendered an "
                        f"access-denied state in the {role} vantage: matched "
                        f"{denial.group(0)!r} in the content pane"
                    )

                    section_api_failures = api_failures[api_mark:]
                    assert not section_api_failures, (
                        f"Case step 5 — PERSONAL section '{tab_id}' produced "
                        f"failing API responses in the {role} vantage: "
                        f"{section_api_failures}"
                    )

                    section_console_errors = console_errors[console_mark:]
                    assert not section_console_errors, (
                        f"PERSONAL section '{tab_id}' logged console errors in "
                        f"the {role} vantage: {section_console_errors}"
                    )

                    logger.info(
                        "PERSONAL section %s loaded clean in the %s vantage",
                        tab_id,
                        role,
                    )
        finally:
            # The active project is app state shared with every other spec in
            # the suite — never leave the session parked on a vantage project.
            restore_active_project(drawer, default_project)
