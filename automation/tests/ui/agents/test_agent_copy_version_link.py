"""Copy version link produces a version-specific URL (ELITEA-1898).

Creates a dedicated, disposable agent via ``AgentAPI.create_agent_full()``
(mirrors the pattern in ELITEA-1888/1892's tests), saves a named version on
it through the UI ("Save As Version"), then exercises the VERSION-group
"Share" action on the actions overflow menu (``share-version-menuitem``) and
verifies:

- the copied URL contains the version id as a distinct trailing path
  segment, contrasted against the AGENT-group "Share" action
  (``share-agent-menuitem``), which deliberately omits it (AFS Axis 2 —
  negative control; both items are visually identical "Share" entries, so
  this guards against the test accidentally wiring to the wrong one), and
- navigating to the copied URL (in a fresh browser tab) opens the correct
  agent at the correct named version, surviving the ``ProjectSwitcher``
  redirect hop the leading ``/{projectId}`` URL segment triggers (AFS Test
  Step 6 note — a hard ``window.location.replace()`` reload before the
  agent page mounts).

Two case-text drifts (case text: a standalone "Copy Link" button with a
tooltip/icon-change confirmation) vs. live product (two separate "Share"
menu items; confirmation is a toast, not a tooltip) are filed as
CLARIFICATION EliteaAI/elitea-testing-public#1288 — not product defects, and
the test asserts the live-contract behavior, not the stale case text
(reverse-masking guard).

Spec: test-specs/agents/l2_copy-version-link-produces-version-specific-url_ELITEA-1898.md
"""

import uuid
from urllib.parse import urlparse

import allure
import pytest
from config import settings
from pages.agent_detail_page import AgentDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.agents]

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
CLIPBOARD_TIMEOUT = 10_000

VERSION_NAME = "v1-copy-link-test"


def _build_dedicated_agent_payload(name: str) -> dict:
    """Build a create-agent payload for a dedicated, disposable test agent.

    Uses ``reasoning_effort: "none"`` and omits ``temperature`` entirely so
    agent creation does not hit the open, unrelated
    EliteaAI/elitea-testing-public#524 defect (`temperature` is not allowed
    together with a `reasoning_effort` other than 'none' on the project's
    reasoning-capable default model) — same workaround as
    ELITEA-1888/1892's payloads. The Share/copy-link flow has no
    AI-validation gate (unlike Publish), so no special Instructions/Tag
    content is required (AFS Test Data).
    """
    return {
        "name": name,
        "description": "Disposable agent for ELITEA-1898 copy-version-link test",
        "type": "interface",
        "versions": [
            {
                "name": "base",
                "tags": [],
                "instructions": "You are a helpful assistant.",
                "variables": [],
                "tools": [],
                "llm_settings": {
                    "max_tokens": -1,
                    "reasoning_effort": "none",
                    "model_name": settings.default_model_name,
                    "model_project_id": settings.default_model_project_id,
                },
                "conversation_starters": [],
                "agent_type": "openai",
                "welcome_message": "",
                "meta": {"step_limit": 25},
            }
        ],
    }


def _copy_link_via_menuitem(page, detail_page: AgentDetailPage, menuitem, timeout: int) -> str:
    """Click a "Share" menuitem and return the URL it copies to the clipboard.

    Clears the clipboard first (via a real OS clipboard write — permission
    granted on the browser context by the caller) so waiting for a
    non-empty value afterward is a real condition, not a sleep. The
    menuitem's own click closes the actions menu (``DotMenu.jsx``'s
    ``withClose``), so no separate close step is needed. Also waits for the
    toast confirmation to appear (AFS Test Step 3 — the visual confirmation
    the case describes, live product uses a toast rather than a
    tooltip/icon change — CLARIFICATION #1288).

    ``navigator.clipboard.readText()`` is read via ``page.wait_for_function``
    (an async predicate — Playwright awaits the returned Promise) rather
    than Playwright's own clipboard helper, per AFS Automation Hints: a
    direct ``readText()`` call can hang on a permission prompt if
    ``grant_permissions`` was skipped; polling this way still relies on the
    granted permission but never blocks on an interactive prompt.
    """
    page.evaluate("() => navigator.clipboard.writeText('')")
    menuitem.click()
    detail_page.toast_message.wait_for(state="visible", timeout=timeout)
    page.wait_for_function(
        "async () => { const t = await navigator.clipboard.readText(); return t.length > 0; }",
        timeout=timeout,
    )
    return page.evaluate("async () => await navigator.clipboard.readText()")


def _version_id_segment(url: str, agent_id) -> str | None:
    """Return the path segment immediately after ``/agents/all/{agent_id}/``.

    ``None`` if the URL has no such trailing segment — i.e. it's a generic
    agent link (the AGENT-group Share action's shape), not a version-specific
    one (the VERSION-group Share action's shape). Matches on the URL PATH
    only (not a raw substring-of-the-whole-URL check — AFS Automation Hints:
    a substring check alone could spuriously match a numeric-looking
    fragment elsewhere in the URL).
    """
    path = urlparse(url).path
    marker = f"/agents/all/{agent_id}/"
    idx = path.find(marker)
    if idx == -1:
        return None
    remainder = path[idx + len(marker):]
    segment = remainder.split("/")[0] if remainder else ""
    return segment or None


class TestAgentCopyVersionLink:
    """Copy version link produces a version-specific URL (ELITEA-1898, l2/p2)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1898_copy-version-link-produces-version-specific-url.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/1288",
        "Case-text drift CLARIFICATION #1288",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_copy_version_link_produces_version_specific_url(self, page, agent_api):
        """The VERSION-group "Share" action copies a URL containing the
        version id as a distinct path segment (contrasted against the
        AGENT-group "Share" action, which omits it); navigating to that URL
        — even via a fresh tab, through the project-switch redirect hop —
        opens the correct agent at the correct named version."""
        with allure.step(
            "Precondition — create a dedicated disposable agent and save a "
            "named version on it"
        ):
            agent_name = f"elitea-1898-cvl-{uuid.uuid4().hex[:8]}"
            agent = agent_api.create_agent_full(_build_dedicated_agent_payload(agent_name))
            agent_id = agent["id"]

            detail_page = AgentDetailPage(page)
            detail_page.navigate(agent_id)
            assert detail_page.get_version_selector_value() == "base", (
                "New disposable agent should be showing its 'base' version"
            )
            detail_page.save_as_version(VERSION_NAME, timeout=NAVIGATION_TIMEOUT)
            # Precondition setup only — return to 'base' so Test Step 1 below
            # genuinely exercises "select a specific named version" rather
            # than finding it already active as a side effect of creation.
            detail_page.select_version_by_name("base", timeout=UI_ELEMENT_TIMEOUT)
            assert detail_page.get_version_selector_value() == "base", (
                "Precondition setup should leave the page on 'base' before "
                "Step 1 explicitly selects the named version"
            )

            # Clipboard permissions granted once, before any Share click —
            # AFS Automation Hints' preferred pattern over the exploration
            # run's writeText() monkey-patch workaround.
            page.context.grant_permissions(["clipboard-read", "clipboard-write"])

        # Collects "error"-type console messages across the full
        # select-version -> open-menu -> copy -> navigate-to-copied-URL
        # round trip (AFS Axis 2: "Zero console errors ... confirmed clean
        # via browser_console_messages(level='error')") — scoped to
        # "error" only (not "warning"), matching what the AFS actually
        # verified live, per the sibling-test precedent in
        # test_agent_llm_selector_openai_models.py. The listener is
        # attached to the ORIGINAL tab here; Step 6 attaches the same
        # collector to the fresh tab it opens, since the copied-URL
        # navigation the AFS's round trip covers happens there.
        console_issues = []
        page.on(
            "console",
            lambda msg: console_issues.append(msg) if msg.type == "error" else None,
        )

        try:
            with allure.step(
                f"Step 1 — Select the named version {VERSION_NAME!r} from the "
                "VERSION dropdown; verify it becomes active"
            ):
                version_id = detail_page.select_version_by_name(
                    VERSION_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                assert detail_page.get_version_selector_value() == VERSION_NAME, (
                    f"VERSION selector should show {VERSION_NAME!r} once selected"
                )

            with allure.step(
                "Step 2 — Open the actions overflow menu; locate the "
                "VERSION-group 'Share' item (case text: 'Copy Link' button — "
                "live product has no standalone Copy Link button, two "
                "separate 'Share' items instead — CLARIFICATION #1288)"
            ):
                detail_page.open_actions_menu()
                assert detail_page.share_version_menuitem.is_visible(), (
                    "VERSION group should offer a 'Share' item for the "
                    "active named version"
                )
                assert detail_page.share_agent_menuitem.is_visible(), (
                    "AGENT group should also offer its own separate "
                    "'Share' item (negative-control target for Step 5)"
                )

            with allure.step(
                'Step 3 — Click the VERSION-group "Share" item; verify a '
                "visual confirmation appears (case text: tooltip/icon "
                "change — live product shows a toast — CLARIFICATION #1288)"
            ):
                version_share_url = _copy_link_via_menuitem(
                    page, detail_page, detail_page.share_version_menuitem, UI_ELEMENT_TIMEOUT
                )
                assert detail_page.toast_message.is_visible(), (
                    "Toast confirmation should be visible after copying the link"
                )
                assert "copied to the clipboard" in (
                    detail_page.toast_message.text_content() or ""
                ).lower(), (
                    "Toast should confirm the link was copied to the clipboard"
                )

            with allure.step("Step 4 — Paste the copied URL and inspect it"):
                assert version_share_url, "Clipboard should contain the copied URL"
                assert f"/agents/all/{agent_id}" in version_share_url, (
                    f"Copied URL should reference agent {agent_id}: {version_share_url!r}"
                )

            with allure.step(
                "Step 5 — Verify the URL contains the version ID (not just "
                "the agent URL) — contrasted against the AGENT-group "
                "'Share' action, which omits it (AFS Axis 2 negative control)"
            ):
                version_segment = _version_id_segment(version_share_url, agent_id)
                assert version_segment == str(version_id), (
                    f"VERSION-group Share URL should carry the version id "
                    f"{version_id!r} as a distinct trailing path segment, "
                    f"got segment {version_segment!r} from {version_share_url!r}"
                )

                detail_page.open_actions_menu()
                agent_share_url = _copy_link_via_menuitem(
                    page, detail_page, detail_page.share_agent_menuitem, UI_ELEMENT_TIMEOUT
                )
                agent_segment = _version_id_segment(agent_share_url, agent_id)
                assert agent_segment is None, (
                    "AGENT-group Share URL should NOT carry a trailing "
                    f"version-id segment, got {agent_segment!r} from "
                    f"{agent_share_url!r}"
                )

            with allure.step(
                "Step 6 — Navigate to the copied version-specific URL in a "
                "fresh browser tab; verify it opens the correct agent at "
                "the correct version (waits for the ProjectSwitcher's hard "
                "reload hop to settle — AFS Test Step 6 note — never an "
                "immediate assert right after goto())"
            ):
                new_page = page.context.new_page()
                new_page.on(
                    "console",
                    lambda msg: console_issues.append(msg) if msg.type == "error" else None,
                )
                try:
                    new_detail_page = AgentDetailPage(new_page)
                    new_page.goto(version_share_url, wait_until="domcontentloaded")
                    # The VERSION trigger's displayed name and the Information
                    # panel's version-id can settle on separate render ticks
                    # (the SAME class of client-state race already documented
                    # on this page object — see AgentDetailPage
                    # .select_version_by_name()'s three-way convergence check
                    # and .confirm_new_version()'s "URL updates before the
                    # trigger re-renders" note) — wait for BOTH to agree
                    # rather than asserting right after the trigger text alone
                    # settles. Delegated to the page object (rather than
                    # inlining the raw testid-string wait_for_function here)
                    # so the two testids stay defined in exactly one file.
                    new_detail_page.wait_for_version_trigger_and_id(
                        VERSION_NAME, str(version_id), timeout=NAVIGATION_TIMEOUT
                    )
                    assert new_detail_page.get_name() == agent_name, (
                        "Copied URL should open the SAME agent it was copied from"
                    )
                    assert new_detail_page.get_version_id() == str(version_id), (
                        "Copied URL should open the SAME version it was "
                        "copied from, not just the same agent"
                    )
                finally:
                    new_page.close()

            with allure.step(
                "Step 7 — Verify zero console errors across the full "
                "select-version -> open-menu -> copy -> navigate-to-copied-URL "
                "round trip (AFS Axis 2)"
            ):
                assert not console_issues, (
                    "Expected no console errors across the select-version -> "
                    "open-menu -> copy -> navigate-to-copied-URL round trip, "
                    f"got: {[(m.type, m.text) for m in console_issues]}"
                )
        finally:
            with allure.step("Cleanup — delete the dedicated agent"):
                try:
                    agent_api.delete_agent(agent_id)
                except Exception as cleanup_exc:
                    print(f"Warning: Failed to cleanup agent {agent_id}: {cleanup_exc}")
