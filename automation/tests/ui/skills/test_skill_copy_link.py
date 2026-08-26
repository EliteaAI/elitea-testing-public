"""Copy Link copies a valid URL pointing to the correct Skill and version.

Creates a dedicated, disposable skill via ``SkillAPI.create_skill()``, saves
a named version on it through the UI (``save_as_version()``), then exercises
the VERSION-group "Share" action on the skill controls overflow menu
(``share-version-menuitem``) and verifies:

- the copied URL contains the version id as a distinct trailing path
  segment, contrasted against the SKILL-group "Share" action
  (``share-skill-menuitem``), which deliberately omits it (AFS Axis 2 —
  negative control; both items are visually identical "Share" entries, so
  this guards against the test accidentally wiring to the wrong one), and
- navigating to the copied URL (in a fresh browser tab) opens the correct
  Skill at the correct named version, with no "not found" error.

Mirrors ``test_agent_copy_version_link.py`` (ELITEA-1898) — same
``useCopyLinkMenu()`` mechanism, shared between ``SkillControls.jsx`` and
``ApplicationControls.jsx``.

Case-text drift (case text: a standalone "Copy Link" button) vs. live
product (two separate "Share" menu items; confirmation is a toast, not a
tooltip/icon change) is filed as CLARIFICATION
EliteaAI/elitea-testing-public#1451 — sibling of #1288 (ELITEA-1898) and
#1337 (ELITEA-2049) — not a product defect; the test asserts the
live-contract behavior, not the stale case text (reverse-masking guard).

Spec: test-specs/skills/l2_copy-link-copies-valid-url-to-correct-skill-version_ELITEA-2439.md
"""

import time
from urllib.parse import urlparse

import allure
import pytest
from pages.skill_detail_page import SkillDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p2, pytest.mark.regression, pytest.mark.new_verified]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

VERSION_NAME = "v1-copy-link-test"


def _copy_link_via_menuitem(page, detail_page: SkillDetailPage, menuitem, timeout: int) -> str:
    """Click a "Share" menuitem and return the URL it copies to the clipboard.

    Clears the clipboard first (via a real OS clipboard write — permission
    granted on the browser context by the caller) so waiting for a
    non-empty value afterward is a real condition, not a sleep. The
    menuitem's own click closes the actions menu (``DotMenu.jsx``'s
    ``withClose``), so no separate close step is needed. Also waits for the
    toast confirmation to appear (AFS Test Step 3 — the visual confirmation
    the case describes; live product uses a toast rather than a
    tooltip/icon change — CLARIFICATION #1451).

    ``navigator.clipboard.readText()`` is read via ``page.wait_for_function``
    (an async predicate — Playwright awaits the returned Promise) rather
    than Playwright's own clipboard helper, per AFS Automation Hints: a
    direct ``readText()`` call can hang on a permission prompt if
    ``grant_permissions`` was skipped; polling this way still relies on the
    granted permission but never blocks on an interactive prompt.
    """
    page.evaluate("() => navigator.clipboard.writeText('')")
    menuitem.click()
    detail_page.version_toast_message.wait_for(state="visible", timeout=timeout)
    page.wait_for_function(
        "async () => { const t = await navigator.clipboard.readText(); return t.length > 0; }",
        timeout=timeout,
    )
    return page.evaluate("async () => await navigator.clipboard.readText()")


def _version_id_segment(url: str, skill_id) -> str | None:
    """Return the path segment immediately after ``/skills/all/{skill_id}/``.

    ``None`` if the URL has no such trailing segment — i.e. it's a generic
    skill link (the SKILL-group Share action's shape), not a version-specific
    one (the VERSION-group Share action's shape). Matches on the URL PATH
    only (not a raw substring-of-the-whole-URL check — AFS Automation Hints:
    a substring check alone could spuriously match a numeric-looking
    fragment elsewhere in the URL).
    """
    path = urlparse(url).path
    marker = f"/skills/all/{skill_id}/"
    idx = path.find(marker)
    if idx == -1:
        return None
    remainder = path[idx + len(marker):]
    segment = remainder.split("/")[0] if remainder else ""
    return segment or None


class TestSkillCopyLink:
    """Copy Link copies a valid URL pointing to the correct Skill and version (ELITEA-2439, l2/p2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2439_copy-link-copies-a-valid-url-pointing-to-the-correct-skill-and-version.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1451",
        "Case-text drift CLARIFICATION #1451",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_copy_link_copies_valid_url_to_correct_skill_and_version(self, page, skill_api):
        """The VERSION-group "Share" action copies a URL containing the
        version id as a distinct path segment (contrasted against the
        SKILL-group "Share" action, which omits it); navigating to that URL
        — even via a fresh tab — opens the correct Skill at the correct
        named version, with no "not found" error."""
        ts = int(time.time())
        skill_name = f"autotest-2439-cvl-{ts}"[:32]
        skill_id = None

        try:
            with allure.step(
                "Precondition — create a dedicated disposable skill and save a "
                "named version on it"
            ):
                skill = skill_api.create_skill(
                    name=skill_name,
                    description="Disposable skill for ELITEA-2439 copy-link test.",
                    instructions="You are a test skill used for the copy-link automation. Reply 'ok'.",
                )
                skill_id = skill["id"]
                assert skill_id, "Expected a numeric id for the created skill"

                detail_page = SkillDetailPage(page)
                detail_page.navigate(skill_id)
                assert detail_page.get_version_selector_value() == "base", (
                    "New disposable skill should be showing its 'base' version"
                )
                detail_page.save_as_version(VERSION_NAME, timeout=NAVIGATION_TIMEOUT)
                version_id = detail_page.get_version_id()
                # save_as_version() auto-navigates to the newly-created version
                # (documented in test-specs/skills/_surface.md) — this is
                # precondition setup only; Test Step 1 below explicitly
                # switches back to it so the step genuinely exercises
                # "select a specific named version" rather than finding it
                # already active as a side effect of creation.
                detail_page.switch_version("base", timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.get_version_selector_value() == "base", (
                    "Precondition setup should leave the page on 'base' before "
                    "Step 1 explicitly selects the named version"
                )

                # Clipboard permissions granted once, before any Share click —
                # AFS Automation Hints' preferred pattern over a manual
                # writeText() monkey-patch workaround.
                page.context.grant_permissions(["clipboard-read", "clipboard-write"])

            # Collects "error"-type console messages across the full
            # switch-version -> open-menu -> copy -> navigate-to-copied-URL
            # round trip (AFS Axis 2 — zero console errors) — scoped to
            # "error" only (not "warning"), matching the sibling ELITEA-1898
            # test's precedent. The listener is attached to the ORIGINAL tab
            # here; Step 5 attaches the same collector to the fresh tab it
            # opens, since the copied-URL navigation happens there.
            console_issues = []
            page.on(
                "console",
                lambda msg: console_issues.append(msg) if msg.type == "error" else None,
            )

            with allure.step(
                f"Step 1 — Select the named version {VERSION_NAME!r} from the "
                "VERSION dropdown; verify it becomes active"
            ):
                detail_page.switch_version(VERSION_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.get_version_selector_value() == VERSION_NAME, (
                    f"VERSION selector should show {VERSION_NAME!r} once selected"
                )

            with allure.step(
                "Step 2 — Open the skill controls overflow menu; locate the "
                "VERSION-group 'Share' item (case text: 'Copy Link' button — "
                "live product has no standalone Copy Link button, two "
                "separate 'Share' items instead — CLARIFICATION #1451)"
            ):
                detail_page.open_actions_menu()
                assert detail_page.share_version_menuitem.is_visible(), (
                    "VERSION group should offer a 'Share' item for the "
                    "active named version"
                )
                assert detail_page.share_skill_menuitem.is_visible(), (
                    "SKILL group should also offer its own separate "
                    "'Share' item (negative-control target for Step 4)"
                )

            with allure.step(
                'Step 3 — Click the VERSION-group "Share" item; verify a '
                "visual confirmation appears (case text: tooltip/icon "
                "change — live product shows a toast — CLARIFICATION #1451)"
            ):
                version_share_url = _copy_link_via_menuitem(
                    page, detail_page, detail_page.share_version_menuitem, UI_ELEMENT_TIMEOUT
                )
                assert detail_page.version_toast_message.is_visible(), (
                    "Toast confirmation should be visible after copying the link"
                )
                assert "copied to the clipboard" in (
                    detail_page.version_toast_message.text_content() or ""
                ).lower(), (
                    "Toast should confirm the link was copied to the clipboard"
                )

            with allure.step(
                "Step 4 — Paste the copied URL and inspect it — verify it "
                "contains the version ID (not just the skill URL), "
                "contrasted against the SKILL-group 'Share' action, which "
                "omits it (AFS Axis 2 negative control)"
            ):
                assert version_share_url, "Clipboard should contain the copied URL"
                assert f"/skills/all/{skill_id}" in version_share_url, (
                    f"Copied URL should reference skill {skill_id}: {version_share_url!r}"
                )

                version_segment = _version_id_segment(version_share_url, skill_id)
                assert version_segment == str(version_id), (
                    f"VERSION-group Share URL should carry the version id "
                    f"{version_id!r} as a distinct trailing path segment, "
                    f"got segment {version_segment!r} from {version_share_url!r}"
                )

                detail_page.open_actions_menu()
                skill_share_url = _copy_link_via_menuitem(
                    page, detail_page, detail_page.share_skill_menuitem, UI_ELEMENT_TIMEOUT
                )
                skill_segment = _version_id_segment(skill_share_url, skill_id)
                assert skill_segment is None, (
                    "SKILL-group Share URL should NOT carry a trailing "
                    f"version-id segment, got {skill_segment!r} from "
                    f"{skill_share_url!r}"
                )

            with allure.step(
                "Step 5 — Navigate to the copied version-specific URL in a "
                "fresh browser tab; verify it opens the correct Skill at "
                "the correct version, with no 'not found' error"
            ):
                new_page = page.context.new_page()
                new_page.on(
                    "console",
                    lambda msg: console_issues.append(msg) if msg.type == "error" else None,
                )
                try:
                    new_detail_page = SkillDetailPage(new_page)
                    new_page.goto(version_share_url, wait_until="domcontentloaded")
                    new_detail_page.wait_for_version_selector_and_url_id(
                        VERSION_NAME, str(version_id), timeout=NAVIGATION_TIMEOUT
                    )
                    assert new_detail_page.get_name() == skill_name, (
                        "Copied URL should open the SAME skill it was copied from"
                    )
                    assert new_detail_page.get_version_id() == str(version_id), (
                        "Copied URL should open the SAME version it was "
                        "copied from, not just the same skill"
                    )
                    assert "not found" not in (new_page.content() or "").lower(), (
                        "Copied URL should not surface a 'not found' error"
                    )
                finally:
                    new_page.close()

            with allure.step(
                "Step 6 — Verify zero console errors across the full "
                "switch-version -> open-menu -> copy -> navigate-to-copied-URL "
                "round trip (AFS Axis 2)"
            ):
                assert not console_issues, (
                    "Expected no console errors across the switch-version -> "
                    "open-menu -> copy -> navigate-to-copied-URL round trip, "
                    f"got: {[(m.type, m.text) for m in console_issues]}"
                )
        finally:
            with allure.step("Cleanup — delete the dedicated skill"):
                if skill_id:
                    try:
                        skill_api.delete_skill(skill_id)
                    except Exception as cleanup_exc:
                        print(f"Warning: Failed to cleanup skill {skill_id}: {cleanup_exc}")
