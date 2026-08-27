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

3. **ELITEA-2349 — no shadowed page-object members.**
   The branch re-declared ``toast_alert`` / ``toast_message`` /
   ``TOAST_ALERT_SEVERITY`` on ``SecretsPage``, which a sibling settings-w05
   unit had already merged into the batch trunk ~120 lines above. Python keeps
   the LAST definition, so the richer originals became dead code silently —
   ruff, the locator grep and a green run are all blind to it.
"""

import ast
import inspect
from pathlib import Path

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


class TestPageObjectHasNoShadowedMembers:
    """`SecretsPage` must not define the same class member twice.

    Third review finding on this unit (PR #1911, re-review): the branch
    appended ``toast_alert`` / ``toast_message`` / ``TOAST_ALERT_SEVERITY``
    to ``SecretsPage`` although a sibling settings-w05 unit had already
    merged them into the batch trunk ~120 lines above. Python keeps the LAST
    definition, so the earlier, far richer ones (severity auto-hide durations,
    the secrets-flow message catalogue) became dead code — silently.

    Nothing else on this stack catches it: ruff's default `E,F,I,W,UP` set has
    no rule for a redefined class attribute (`F811` covers imports and
    functions, not ``ast.Assign`` targets), both definitions pass the
    reviewer's locator grep, and the run stays green because the two shapes are
    functionally identical. An AST walk is the only cheap detector, so it is
    pinned here.

    Scoped to ``SecretsPage`` — the class this unit edits. Other page objects
    carry the same pre-existing debt (`ChatPage`, `SkillDetailPage`,
    `PipelineDetailPage`); widening this test would fail on work nobody on this
    branch touched. Reported to the lead instead.
    """

    def _duplicate_members(self, class_name: str, module_path: Path) -> dict:
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                seen: dict[str, list[int]] = {}
                for statement in node.body:
                    names = []
                    if isinstance(statement, ast.Assign):
                        names = [
                            target.id
                            for target in statement.targets
                            if isinstance(target, ast.Name)
                        ]
                    elif isinstance(statement, ast.AnnAssign) and isinstance(
                        statement.target, ast.Name
                    ):
                        names = [statement.target.id]
                    elif isinstance(
                        statement, (ast.FunctionDef, ast.AsyncFunctionDef)
                    ):
                        names = [statement.name]
                    for name in names:
                        seen.setdefault(name, []).append(statement.lineno)
                return {n: ls for n, ls in seen.items() if len(ls) > 1}
        raise AssertionError(f"class {class_name} not found in {module_path}")

    def test_secrets_page_defines_every_member_once(self):
        from pages import secrets_page

        duplicates = self._duplicate_members(
            "SecretsPage", Path(secrets_page.__file__)
        )

        assert not duplicates, (
            "SecretsPage defines these members more than once — Python keeps "
            "the LAST definition, so the earlier one is dead code and any edit "
            "to it does nothing:\n"
            + "\n".join(
                f"  {name}: lines {lines}" for name, lines in sorted(duplicates.items())
            )
        )

    def test_the_toast_handles_the_specs_use_are_the_documented_ones(self):
        """The surviving definitions are the richer, first-block ones.

        Deleting the duplicates is only correct if what remains is the block
        that documents the severity durations and the secrets message
        catalogue — otherwise the fix would have kept the thin copy.
        """
        from pages.secrets_page import SecretsPage

        assert "data-severity" in SecretsPage.__dict__["toast_alert"].description
        message_description = SecretsPage.__dict__["toast_message"].description
        assert "have been copied" in message_description
        assert "already exists" in message_description
