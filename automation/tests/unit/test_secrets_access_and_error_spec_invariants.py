"""Unit tests pinning the two review findings on the settings-w05 secrets pair.

Both are static/structural defects that no browser run could surface — the
first only bites on the spec's own failure path, the second is a convention
violation — so they are pinned here rather than left to the next reviewer.

1. **ELITEA-2348 — the cleanup guard must not fail open.**
   ``test_viewer_role_cannot_access_secrets.py`` restored the active project in
   a ``finally`` keyed on ``drawer.nav_item("secrets").count()``. That reads
   "am I still on a vantage that hides Secrets?", which is non-zero exactly
   when the spec fails for the reason it exists (the Secrets entry wrongly
   PRESENT under the Viewer role) — so the restore was skipped on the one
   outcome that pollutes every later spec in the invocation with the viewer
   project. The restore is now unconditional; these tests fail if a guard
   comes back.

2. **ELITEA-2349 — no locators built in the spec file.**
   ``.agents/conventions.md`` § Hard don'ts: "Never build locators inside
   methods or spec files — class fields only". The spec re-implemented
   ``SecretsPage.get_row_names()`` inline and built the severity-scoped toast
   locator by hand instead of calling ``toast_alert_with_severity()``.
"""

import inspect

import pytest

from tests.ui.admin import (
    test_secrets_error_state_on_network_failure as error_state_spec,
)
from tests.ui.admin import (
    test_viewer_role_cannot_access_secrets as viewer_spec,
)

CONTROL_PROJECT = "399"

#: Every Playwright handle-construction call the locator policy bans from a
#: spec file (`.agents/role-overrides.md` § Reviewer slot — the same set the
#: reviewer's mechanical grep uses).
LOCATOR_CONSTRUCTORS = (
    ".locator(",
    "get_by_role(",
    "get_by_label(",
    "get_by_text(",
    "get_by_placeholder(",
    "get_by_title(",
    "get_by_alt_text(",
    "get_by_test_id(",
    "query_selector(",
)


class _StubNavItem:
    """Stand-in for a Playwright ``Locator`` that only needs ``count()``."""

    def __init__(self, count: int):
        self._count = count

    def count(self) -> int:
        return self._count


class _StubDrawer:
    """Minimal ``SettingsDrawerPage`` stand-in recording project switches."""

    def __init__(self, secrets_nav_count: int = 0, switch_raises: bool = False):
        self._secrets_nav_count = secrets_nav_count
        self._switch_raises = switch_raises
        self.switched_to: list[str] = []

    def nav_item(self, tab_id: str) -> _StubNavItem:
        count = self._secrets_nav_count if tab_id == viewer_spec.SECRETS_TAB_ID else 1
        return _StubNavItem(count)

    def switch_project(self, project_id) -> None:
        self.switched_to.append(project_id)
        if self._switch_raises:
            raise RuntimeError("project selector never opened")


class TestViewerSpecCleanupCannotFailOpen:
    """ELITEA-2348 — the restore runs on the failure path, not only the happy one."""

    @pytest.mark.parametrize(
        "secrets_nav_count, why",
        [
            (0, "happy path — Secrets correctly hidden on the viewer project"),
            (
                1,
                "FAILURE path — Secrets wrongly PRESENT (the regression the spec "
                "hunts); the old guard skipped the restore here",
            ),
        ],
    )
    def test_restore_is_unconditional(self, secrets_nav_count, why):
        drawer = _StubDrawer(secrets_nav_count=secrets_nav_count)

        viewer_spec.restore_active_project(drawer, CONTROL_PROJECT)

        assert drawer.switched_to == [CONTROL_PROJECT], (
            f"The active project must be restored regardless of state ({why}); "
            f"switch_project calls were {drawer.switched_to}"
        )

    def test_restore_failure_does_not_mask_the_real_failure(self):
        """A raising restore must not replace the test's own exception."""
        drawer = _StubDrawer(secrets_nav_count=1, switch_raises=True)

        viewer_spec.restore_active_project(drawer, CONTROL_PROJECT)  # must not raise

        assert drawer.switched_to == [CONTROL_PROJECT]

    def test_finally_block_delegates_to_the_helper(self):
        """No re-inlined, re-guarded restore in the spec body."""
        source = inspect.getsource(
            viewer_spec.TestViewerRoleCannotAccessSecrets.test_viewer_role_is_not_offered_the_secrets_section
        )
        finally_body = "\n".join(
            line
            for line in source.split("finally:", 1)[1].splitlines()
            if line.strip() and not line.strip().startswith("#")
        )

        assert "restore_active_project(" in finally_body, (
            "The finally block must delegate to restore_active_project()"
        )
        assert "if " not in finally_body, (
            "The restore must be unconditional — a conditional in the finally "
            f"block is the fail-open shape this pins against:\n{finally_body}"
        )


class TestSpecsBuildNoLocators:
    """Both specs — handles come from the page object, never built in the spec."""

    @pytest.mark.parametrize(
        "spec_module",
        [error_state_spec, viewer_spec],
        ids=["ELITEA-2349", "ELITEA-2348"],
    )
    def test_no_locator_constructed_in_the_spec_file(self, spec_module):
        source = inspect.getsource(spec_module)
        code_lines = [
            line
            for line in source.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        offenders = [
            line.strip()
            for line in code_lines
            if any(token in line for token in LOCATOR_CONSTRUCTORS)
        ]

        assert not offenders, (
            "`.agents/conventions.md` § Hard don'ts — locators live only as "
            "page-object class fields; found in "
            f"{spec_module.__name__}:\n" + "\n".join(offenders)
        )

    def test_page_object_owns_the_accessors_the_spec_needs(self):
        """The two accessors the ELITEA-2349 spec was re-implementing exist."""
        from pages.secrets_page import SecretsPage

        assert callable(SecretsPage.get_row_names)
        assert callable(SecretsPage.toast_alert_with_severity)
