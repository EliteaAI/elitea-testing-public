"""UI test — a user acting under the Admin role is offered every PROJECT
settings section, each loads without an access-denied or 403 error, and the
sections that own editable controls expose them as interactive.

Read-only case (`.agents/testing.md` § Test data strategy): nothing is
created, edited or deleted. `to_be_enabled()` / `to_be_editable()` are
product-state reads, not mutations — this spec never types into, toggles or
submits anything. Only the active project selection moves, and it is restored
in a `finally` because that selection is app state shared with every other
spec (the `#1082` pollution class).

Test case: ELITEA-2245
AFS: test-specs/settings-navigation/l3_admin-role-access-to-all-project-settings-sections_ELITEA-2245.md

The Admin vantage is real — no second identity, no substitution
----------------------------------------------------------------
Elitea roles are PROJECT-scoped, and the shared ${TEST_USER} genuinely holds
different roles in different projects. Verified live 2026-08-30 via
`GET /admin/users/prompt_lib/{id}` + `GET /auth/permissions/prompt_lib/{id}`:
in project 400 (`settings.elitea_admin_project_id`, "UI Testing") the acting
user's role is `admin` — 360 permissions, 8 of them `*secret*` — against
`editor`+`viewer` / 299 in project 399 and `viewer` / 158 in project 471.
Selecting project 400 therefore puts the app in a real, product-computed admin
state: `useCheckPermission` reads `state.user.permissions`, refetched per
selected project. Nothing is injected, stubbed or forced — no `page.route`, no
`evaluate`-injected state, no fabricated permission payload appears anywhere
in this spec (`.agents/testing.md` § Fidelity policy).

Case-text drift — this test asserts the LIVE contract
------------------------------------------------------
The case's step 3 names PROJECT sections that do not all exist. Per the
reverse-masking guard this spec asserts the live contract, not the case text:

  * case "AI Configuration" — no such section. The AI Configurations accordion
    lives *inside* General; the model/provider settings are their own
    **AI Providers** section.
  * case "Project Params" — no such section. Nearest equivalents are
    **General** + **Project Context**.
  * live PROJECT inventory on an admin project: General, AI Providers, Project
    Context, Secrets, Users, Analytics, Usage (7 items).

`Users` renders only when `projectId != user.personal_project_id`, which is why
the admin walk covers one section more than ELITEA-2242/2243's walks on the
personal project 399. Already tracked as clarification
EliteaAI/elitea-testing-public#1772; a new occurrence was commented there
rather than re-filed.

Why "no 403" is asserted at the transport layer too
----------------------------------------------------
The case's step 4 asks that each section load "without an Access Denied or 403
error". On this product a permission failure can surface as a 403 with **no**
access-denied UI at all — that is the shape of the open bug #1773 on the
Secrets route — so a text-only denial regex can pass over a real denial.
`utils.api_failures.collect_api_failures` records the `/api/v2/` responses the
page actually received, and each section is asserted against its own slice.

Why the editable-field checks name individual controls
-------------------------------------------------------
The case's step 5 ("editable fields are interactive, not read-only") is
asserted with one named, permission-gated control per section that owns one —
never with a blanket "no disabled control" count, which would be false-red on
correct product behaviour: on project 400 the Secrets page legitimately
disables `secrets-pagination-prev-button` on the first page, and Users
legitimately disables its header Edit/Delete until a row is selected.
Analytics and Usage are read-only dashboards and make no editable-field claim.

Markers:
    - ui: requires browser
    - admin: settings/admin surface
    - p3: priority (per AFS metadata: l3 — case frontmatter `priority: medium`)
    - regression
"""

import logging
import re

import allure
import pytest
from config import settings
from pages.admin_users_page import AdminUsersPage
from pages.ai_providers_page import AIProvidersPage
from pages.project_context_page import ProjectContextPage
from pages.secrets_page import SecretsPage
from pages.settings_drawer_page import SettingsDrawerPage
from pages.settings_project_general_page import SettingsProjectGeneralPage
from playwright.sync_api import expect
from utils.api_failures import collect_api_failures
from utils.console_errors import collect_console_errors

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.admin, pytest.mark.p3, pytest.mark.regression, pytest.mark.new]

SETTINGS_PATH = "/settings/project-general"
UI_ELEMENT_TIMEOUT = 10_000
#: Analytics/Usage render dashboards behind their own queries — give the
#: content pane longer than a plain drawer element before reading it.
CONTENT_TIMEOUT = 30_000

#: Live PROJECT inventory on an ADMIN project, in DOM order. One item more
#: than the personal-project walks (`users` — see the module docstring).
EXPECTED_PROJECT_TAB_IDS = [
    "project-general",
    "ai-providers",
    "project-context",
    "secrets",
    "users",
    "analytics",
    "usage",
]

#: The two permission-gated PROJECT entries. Their presence is the
#: role-driven observable — on the viewer project 471 `secrets` is absent
#: (proven by ELITEA-2348's merged spec).
PERMISSION_GATED_TAB_IDS = ["secrets", "users"]

#: Any non-whitespace character — an auto-retrying "the pane rendered
#: something" assertion, which a plain `inner_text()` read is not.
NON_BLANK_PATTERN = re.compile(r"\S")

#: Case step 4's denial vocabulary, as rendered in the content pane.
ACCESS_DENIED_PATTERN = re.compile(
    r"access denied|forbidden|403|not authorized|no permission", re.IGNORECASE
)


def restore_active_project(drawer: SettingsDrawerPage, project_id) -> None:
    """Return the session to *project_id* — UNCONDITIONALLY.

    Cleanup is never keyed on anything this test asserts: a guard would fail
    OPEN on exactly the regression that matters, leaving every later spec in
    the invocation running against the admin project (the `#1082` shared-state
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


class TestAdminRoleProjectSectionsAccess:
    """ELITEA-2245 — Admin role has access to all PROJECT settings sections."""

    def _assert_drawer_healthy(self, drawer: SettingsDrawerPage) -> list[str]:
        """Prove the drawer actually rendered before reading anything off it.

        Without this guard every later presence/inventory read is vacuous — a
        drawer that failed to render satisfies an absence assertion just as
        happily as a correctly permission-gated one.
        """
        expect(drawer.settings_drawer).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        expect(drawer.settings_drawer_menu).to_be_visible(timeout=UI_ELEMENT_TIMEOUT)
        nav_ids = drawer.nav_item_ids_in_order()
        assert len(nav_ids) > 1, (
            "Drawer-health guard — expected a populated Settings nav before "
            f"reading the admin inventory, got {nav_ids}"
        )
        return nav_ids

    def _assert_section_loaded_cleanly(
        self,
        drawer: SettingsDrawerPage,
        page,
        tab_id: str,
        console_errors: list[str],
        api_failures: list[str],
    ) -> None:
        """Click *tab_id* and assert it routed, selected, rendered, and did so
        without a denial at either the UI or the transport layer.

        Console errors and API failures are sliced from the mark taken just
        before the click, so a failure names the section that caused it rather
        than the whole walk.
        """
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
        expect(drawer.settings_content).to_be_visible(timeout=CONTENT_TIMEOUT)
        expect(drawer.settings_content).to_contain_text(
            NON_BLANK_PATTERN, timeout=CONTENT_TIMEOUT
        )

        content_text = drawer.settings_content.inner_text()
        denial = ACCESS_DENIED_PATTERN.search(content_text)
        assert denial is None, (
            f"Case step 4 — section '{tab_id}' rendered an access-denied state "
            f"for an Admin: matched {denial.group(0)!r} in the content pane"
        )

        section_api_failures = api_failures[api_mark:]
        assert not section_api_failures, (
            f"Case step 4 — section '{tab_id}' produced failing API responses "
            f"for an Admin: {section_api_failures}"
        )

        section_console_errors = console_errors[console_mark:]
        assert not section_console_errors, (
            f"Section '{tab_id}' logged console errors: {section_console_errors}"
        )

        logger.info("Section %s loaded clean for the Admin vantage", tab_id)

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "settings/ELITEA-2245_admin-role-has-access-to-all-project-settings-sections.md",
        "onetest-ai Test Case link",
    )
    def test_admin_role_has_access_to_all_project_settings_sections(self, page):
        """On a project where the acting user's role is Admin, the Settings
        drawer offers all seven PROJECT sections including the two
        permission-gated ones; each loads its own route with non-blank content,
        no access-denied state, no failing API response and no console error;
        and each section that owns editable controls exposes them enabled."""
        drawer = SettingsDrawerPage(page)
        general = SettingsProjectGeneralPage(page)
        ai_providers = AIProvidersPage(page)
        project_context = ProjectContextPage(page)
        secrets = SecretsPage(page)
        users = AdminUsersPage(page)

        console_errors = collect_console_errors(page)
        api_failures = collect_api_failures(page)

        admin_project = settings.elitea_admin_project_id
        default_project = settings.elitea_project_id

        try:
            with allure.step(
                f"Step 1 — Enter Settings on project {admin_project}, where the "
                "acting user's role is Admin"
            ):
                drawer.navigate(SETTINGS_PATH)
                self._assert_drawer_healthy(drawer)
                drawer.ensure_project_selected(admin_project)
                nav_ids = self._assert_drawer_healthy(drawer)
                expect(drawer.section_header("project")).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(drawer.section_header("personal")).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                logger.info("Admin project %s nav: %s", admin_project, nav_ids)

            with allure.step(
                "Step 2 — Verify the Admin PROJECT inventory, in drawer order, "
                "including the two permission-gated entries"
            ):
                for tab_id in EXPECTED_PROJECT_TAB_IDS:
                    expect(drawer.nav_item(tab_id)).to_be_visible(
                        timeout=UI_ELEMENT_TIMEOUT
                    )
                nav_ids = drawer.nav_item_ids_in_order()
                assert nav_ids[: len(EXPECTED_PROJECT_TAB_IDS)] == EXPECTED_PROJECT_TAB_IDS, (
                    "Case step 3 — the PROJECT group must list the live admin "
                    f"inventory in order {EXPECTED_PROJECT_TAB_IDS}; drawer was {nav_ids}"
                )
                for tab_id in PERMISSION_GATED_TAB_IDS:
                    assert tab_id in nav_ids, (
                        f"The permission-gated '{tab_id}' entry must be offered to "
                        f"an Admin; drawer was {nav_ids}"
                    )

            with allure.step(
                "Steps 3-4 — Click each PROJECT section in drawer order; each "
                "routes, selects, renders content, and shows no denial in the "
                "UI or on the wire"
            ):
                for tab_id in EXPECTED_PROJECT_TAB_IDS:
                    self._assert_section_loaded_cleanly(
                        drawer, page, tab_id, console_errors, api_failures
                    )

            with allure.step(
                "Step 5 — Verify each section that owns editable controls "
                "exposes them as interactive, not read-only"
            ):
                drawer.click_nav_item("project-general")
                # The project-icon edit control is rendered only when
                # `checkPermission(PERMISSIONS.projectContext.edit)` holds, so
                # its presence AND enabled state is a role-driven observable.
                expect(general.project_general_edit_icon_button).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(general.project_general_edit_icon_button).to_be_enabled(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(general.default_modules_section).to_be_visible(
                    timeout=UI_ELEMENT_TIMEOUT
                )

                drawer.click_nav_item("ai-providers")
                # MUI renders a select trigger as a role=combobox node and marks
                # it `aria-disabled` when disabled, which is what `to_be_enabled`
                # reads — so this is a real interactivity check, unlike an
                # `enabled` assertion on the section's own container <div>.
                expect(ai_providers.llms_default_selector_combobox).to_be_visible(
                    timeout=CONTENT_TIMEOUT
                )
                expect(ai_providers.llms_default_selector_combobox).to_be_enabled(
                    timeout=UI_ELEMENT_TIMEOUT
                )

                drawer.click_nav_item("project-context")
                expect(project_context.page_title).to_be_visible(
                    timeout=CONTENT_TIMEOUT
                )
                expect(project_context.create_button).to_be_enabled(
                    timeout=CONTENT_TIMEOUT
                )

                drawer.click_nav_item("secrets")
                expect(secrets.add_button).to_be_enabled(timeout=CONTENT_TIMEOUT)
                expect(secrets.search_input).to_be_editable(timeout=UI_ELEMENT_TIMEOUT)

                drawer.click_nav_item("users")
                expect(users.invite_button).to_be_enabled(timeout=CONTENT_TIMEOUT)
                expect(users.search_input).to_be_editable(timeout=UI_ELEMENT_TIMEOUT)
                # The per-row Edit/Delete icons render for `admin` only — on a
                # project where the user is `viewer` the Users table renders no
                # row action icons at all, so this is the strongest
                # admin-specific observable on this surface.
                expect(users.user_row.first).to_be_visible(timeout=CONTENT_TIMEOUT)
                expect(users.get_first_row_edit_button()).to_be_enabled(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                expect(users.get_first_row_delete_button()).to_be_enabled(
                    timeout=UI_ELEMENT_TIMEOUT
                )
                # `analytics` and `usage` are read-only dashboards — they own no
                # editable control, so steps 3-4's content assertions are the
                # whole of their coverage. Asserting an "editable field" there
                # would be inventing a claim the product does not make.
        finally:
            # The active project is app state shared with every other spec in
            # the suite — never leave the session parked on the admin project.
            restore_active_project(drawer, default_project)
