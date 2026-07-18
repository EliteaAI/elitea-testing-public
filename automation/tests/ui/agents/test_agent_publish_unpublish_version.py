"""Publish a Draft version — status changes and Unpublish becomes available
(ELITEA-1892).

Creates a dedicated, disposable agent (seeded via ``AgentAPI
.create_agent_full()`` with substantive Instructions + a Tag so the AI
``publish_validate`` content-quality gate passes deterministically on the
first attempt — AFS § Automation Hints), publishes its ``base`` Draft
version through the actions-menu "Publish" wizard (a 3-step
Preparation/Validation/Publishing flow — the TMS case text describes only a
single version-name dialog; the live product is the 3-step wizard, filed as
case-text drift CLARIFICATION #612, not a defect), then unpublishes the
resulting Published version and verifies its status reverts to Draft.

Publish CLONES the Draft version into a brand-new version carrying the
Published status — it does not flip the original "base" version's status in
place (AFS Axis 2). Assertions after Publish therefore track the NEW version
id returned by ``AgentDetailPage.select_version_by_name()``, never the
original "base" version id.

Two MINOR, isolated product defects were found live during this run (neither
blocks the functional flow):

1. https://github.com/EliteaAI/elitea-testing-public/issues/611 — React
   console warnings from the Publish wizard Stepper's custom step-icon
   leaking MUI-internal boolean props onto the DOM ``<svg>`` element. The
   console-cleanliness check around the Publish wizard uses the
   pytest-native soft-assertion equivalent (a ``soft_failures`` list + a
   final ``pytest.fail()``, mirroring
   ``test_fork_agent_to_different_project.py``'s known-defect #570 handling
   — Playwright's ``expect.soft()`` only supports Page/Locator/APIResponse,
   not a raw console-message list) with a `# Known defect: #611` comment, so
   it doesn't mask any *other* console error and never demotes the failure
   to a log-only signal.
2. https://github.com/EliteaAI/elitea-testing-public/issues/614 — the AFS's
   own documented behavior ("the app navigates to the new Published version
   and the VERSION selector shows it") does NOT hold reliably live: a
   network trace shows the app briefly navigating to the new version then
   silently reverting to the previously-active one. This is a live-contract
   drift from the AFS (reverse-masking guard) — the test does not assert
   the AFS's stale auto-navigation claim; it explicitly re-selects the new
   version by name from the VERSION dropdown (``select_version_by_name()``
   — a normal, reliable user action, confirmed live not to revert) before
   asserting against it, exactly as the AFS's own Axis 2 note anticipated
   ("...or re-read the VERSION dropdown after the post-publish
   navigation").

Spec: test-specs/agents/l2_publish-draft-version-status-changes-unpublish-available_ELITEA-1892.md
"""

import uuid

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
VALIDATE_TIMEOUT = 30_000  # publish_validate is AI-backed — variable latency
PUBLISH_TIMEOUT = 15_000

VERSION_NAME = "v1-release"
CATEGORY_NAME = "Quality Assurance"

# Known defect #611 — confirmed live (this run): the Publish wizard
# Stepper's custom step-icon (SvgCheckedIcon, checked-icon.svg?react)
# forwards MUI-internal props (`completed`, `active`, `error` — booleans;
# `ownerState` — an object) onto the underlying DOM <svg>, and React emits
# TWO different dev-warning shapes depending on the prop's type: "Received
# `%s` for a non-boolean attribute `%s`." for the booleans, and "React does
# not recognize the `%s` prop on a DOM element" for `ownerState` — 4
# distinct console.error calls in total, matching the AFS's own count. Both
# shapes share the same component stack ("at svg" / "at SvgCheckedIcon" /
# ".../PublishWizardModal.jsx"), so matching is anchored on the component
# name (not the message phrase alone) — an unrelated future warning from a
# different component still surfaces as an unexpected failure instead of
# being silently absorbed by an overly broad filter.
def _is_known_defect_611(text: str) -> bool:
    if "SvgCheckedIcon" not in text:
        return False
    return "non-boolean attribute" in text or "does not recognize the" in text


def _build_dedicated_agent_payload(name: str) -> dict:
    """Build a create-agent payload for a dedicated, disposable test agent.

    Uses ``reasoning_effort: "none"`` and omits ``temperature`` entirely so
    agent creation does not hit the open #524 defect (`temperature` is not
    allowed together with a `reasoning_effort` other than 'none' on the
    project's reasoning-capable default model) — same workaround as
    ELITEA-1888/1899/1872's payloads.

    Seeds substantive Instructions text and a non-empty Tag directly in the
    creation payload (AFS: "any raw-payload creation matching UI defaults is
    preferred") — the two fields the AI ``publish_validate`` gate reports as
    Critical issues when missing (AFS Test Steps, step 5). Seeding them here
    means the wizard's Validation step passes on the FIRST ``Continue``
    click, avoiding the AFS's own live-run 422/422/200 round-trip and the
    flakiness risk that would add to an automated run (AFS § Automation
    Hints). The Tag uses only alphanumeric characters — the live Tags field
    rejects hyphens with a stricter regex than the Version-name field (AFS
    Axis 2), not relevant here since the tag is set via payload, not typed,
    but kept hyphen-free for parity with the AFS's documented test data.
    """
    return {
        "name": name,
        "description": "Disposable agent for ELITEA-1892 publish/unpublish cycle test",
        "type": "interface",
        "versions": [
            {
                "name": "base",
                "tags": [{"name": "regression"}],
                "instructions": (
                    "You are a helpful QA validation assistant for the "
                    "ELITEA platform publish/unpublish test (ELITEA-1892). "
                    "You answer general questions about testing status."
                ),
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


class TestAgentPublishUnpublishVersion:
    """Publish a Draft version — status changes and Unpublish becomes
    available (ELITEA-1892, l2/p1)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/agents/ELITEA-1892_publish-draft-version-status-changes-unpublish-available.md",
        "onetest-ai Test Case link",
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/611", "Known defect #611"
    )
    @allure.issue(
        "https://github.com/EliteaAI/elitea-testing-public/issues/614", "Known defect #614"
    )
    @pytest.mark.p1
    @pytest.mark.regression
    def test_publish_draft_version_then_unpublish_reverts_to_draft(
        self, page, agent_api
    ):
        """Publishing a Draft version clones it into a Published version and
        makes Unpublish available; clicking Unpublish reverts that version's
        status back to Draft."""
        with allure.step("Precondition — create a dedicated disposable agent"):
            agent_name = f"elitea-1892-pub-{uuid.uuid4().hex[:8]}"[:32]
            agent = agent_api.create_agent_full(_build_dedicated_agent_payload(agent_name))
            agent_id = agent["id"]

        detail_page = AgentDetailPage(page)
        # Console messages are captured starting BEFORE the Publish wizard is
        # opened (not after) so the listener actually observes the Stepper's
        # own renders across all three wizard steps — the known defect
        # (#611) fires on the Stepper's icon render, and a listener attached
        # afterward would silently never see it (Playwright console
        # listeners are forward-looking only, no backfill).
        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg) if msg.type == "error" else None,
        )
        soft_failures = []

        try:
            with allure.step(
                "Step 1 — Navigate to agent detail page; confirm the Draft "
                "version is loaded and the overflow menu offers Publish"
            ):
                detail_page.navigate(agent_id)
                assert detail_page.get_version_selector_value() == "base", (
                    "New disposable agent should be showing its 'base' version"
                )
                base_version_id = detail_page.get_version_id()

                detail_page.open_actions_menu()
                assert detail_page.publish_version_menuitem.is_visible(), (
                    "VERSION group should offer 'Publish' for a Draft "
                    "version with applications.publish permission held"
                )
                assert not detail_page.unpublish_version_menuitem.is_visible(), (
                    "'Unpublish' should NOT be offered before any version "
                    "has been published"
                )
                detail_page.close_actions_menu()

            with allure.step(
                'Step 2/3 — Click "Publish"; verify the Publish wizard opens '
                "with a Version-name input on its Preparation step (case "
                "text describes a single dialog — live product is a 3-step "
                "wizard, CLARIFICATION #612)"
            ):
                detail_page.open_publish_wizard(timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.publish_version_name_input.is_visible(), (
                    "Publish wizard Preparation step should show a "
                    "Version-name input"
                )
                assert not detail_page.is_publish_continue_enabled(), (
                    "Continue should stay disabled before Name/Category/"
                    "Terms-agreement are all filled"
                )

            with allure.step(
                "Step 4 — Enter version name, select Category, accept "
                'Publishing Terms, click "Continue"'
            ):
                detail_page.fill_publish_preparation_step(
                    VERSION_NAME, CATEGORY_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                assert detail_page.is_publish_continue_enabled(), (
                    "Continue should become enabled once Name, Category, "
                    "and the agree-checkbox are all set"
                )

                validate_status = detail_page.click_publish_continue(
                    timeout=VALIDATE_TIMEOUT
                )
                assert validate_status == 200, (
                    "publish_validate should return 200 (no Critical issues) "
                    "on the first attempt — the disposable agent was seeded "
                    f"with Instructions + a Tag precisely to satisfy the AI "
                    f"content-quality gate deterministically, got status "
                    f"{validate_status}"
                )

            with allure.step(
                "Step 5 — Verify the AI validation gate advanced the wizard "
                "to its Validation step with 'Publish' enabled (case text: "
                '"verify the version status changes" — there is no literal '
                '"In Review" CollectionStatus in this codebase; the '
                "moderation the case alludes to is this AI-validation gate)"
            ):
                assert detail_page.publish_confirm_button.is_visible(), (
                    "Validation step's Publish button should be visible "
                    "after Continue"
                )
                assert detail_page.publish_confirm_button.is_enabled(), (
                    "Validation step's Publish button should be enabled — "
                    "publish_validate reported no Critical issues (status 200)"
                )

            with allure.step(
                'Step 6 — Click "Publish"; verify the publish POST succeeds '
                "(clones 'base' into a BRAND-NEW version — AFS Axis 2)"
            ):
                publish_status = detail_page.confirm_publish(timeout=PUBLISH_TIMEOUT)
                assert publish_status == 200, (
                    f"publish POST should return 200, got {publish_status}"
                )

            with allure.step(
                "Step 6a — Console-cleanliness check around the Publish "
                "wizard (a known, isolated, non-blocking defect fires React "
                "'non-boolean attribute'/'does not recognize the X prop' "
                "warnings here — soft-asserted via the pytest-native "
                "soft_failures/pytest.fail() mechanism, not a demoted "
                "log-only check). Checked HERE, before Step 6b's own "
                "reload (an implementation technique, not a case step) so "
                "this assertion stays scoped to the wizard's own console "
                "output and doesn't pick up unrelated reload-time noise "
                "(e.g. a pre-existing, out-of-scope toolkits 404 that fires "
                "on every full page load, confirmed unrelated to #611 live)"
            ):
                unexpected_errors = [
                    m.text for m in console_errors
                    if not _is_known_defect_611(m.text)
                ]
                assert not unexpected_errors, (
                    "Expected no UNEXPECTED console errors around the "
                    f"Publish wizard, got: {unexpected_errors!r}"
                )
                # Known defect: #611 — the Publish wizard Stepper's custom
                # step-icon leaks MUI-internal boolean props onto the DOM
                # <svg>, producing React "does not recognize the X prop"
                # warnings on every Stepper render. No visible UI breakage;
                # does not block the publish flow (verified above — the
                # version published successfully). Recorded in
                # soft_failures (real soft-assertion equivalent — see the
                # pytest.fail() call below) rather than only logged, so a
                # regression here (e.g. a NEW prop added to the leak) would
                # still need the pattern widened deliberately, not silently
                # pass unnoticed.
                known_defect_errors = [
                    m.text for m in console_errors
                    if _is_known_defect_611(m.text)
                ]
                if known_defect_errors:
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/611: "
                        f"React 'non-boolean attribute' (SvgCheckedIcon) console "
                        f"error(s) on the Publish wizard: {len(known_defect_errors)} occurrence(s)"
                    )

            with allure.step(
                "Step 6b — Explicitly select the new version by name from "
                "the VERSION dropdown (Known defect #614: the app's own "
                "auto-navigation after Publish is unreliable — it can "
                "briefly land on the new version then silently revert to "
                "the previous one; re-selecting by name is the reliable, "
                "real-user path and is what the AFS's Axis 2 note "
                'anticipated as the fallback — "...or re-read the VERSION '
                'dropdown after the post-publish navigation")'
            ):
                new_version_id = detail_page.select_version_by_name(
                    VERSION_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                assert new_version_id != base_version_id, (
                    "Publish should create a NEW version id, distinct from "
                    f"the original Draft ('base') version id {base_version_id!r} "
                    "— publishing clones the version rather than flipping "
                    "its status in place"
                )
                assert detail_page.get_version_selector_value() == VERSION_NAME, (
                    f"VERSION selector should show {VERSION_NAME!r} once "
                    "explicitly selected"
                )

            with allure.step(
                "Step 6c — Open the VERSION dropdown and verify it lists "
                "both 'base' (unchanged, still Draft) and the new "
                f"{VERSION_NAME!r} (selected/active)"
            ):
                detail_page.open_version_selector()
                assert detail_page.is_version_option_visible(
                    "base", timeout=UI_ELEMENT_TIMEOUT
                ), "VERSION dropdown should still list the original 'base' version"
                assert detail_page.is_version_option_visible(
                    VERSION_NAME, timeout=UI_ELEMENT_TIMEOUT
                ), f"VERSION dropdown should list the new {VERSION_NAME!r} version"
                assert detail_page.is_version_option_active(VERSION_NAME), (
                    f"{VERSION_NAME!r} should be the active/selected option"
                )
                assert not detail_page.is_version_option_active("base"), (
                    "'base' should NOT be the active option anymore — it "
                    "was never touched by Publish"
                )
                detail_page.close_versions_menu()

            with allure.step(
                'Step 7 — Verify "Unpublish" (not "Publish") is now offered '
                "on this version's overflow menu (Known defect #614: the "
                "menu's status can lag by a beat even after the VERSION "
                "selector/URL agree — poll via open/close attempts rather "
                "than a single point-in-time check)"
            ):
                detail_page.wait_for_publish_status_menuitem(
                    expect_unpublish=True, timeout=UI_ELEMENT_TIMEOUT
                )
                assert not detail_page.publish_version_menuitem.is_visible(), (
                    "'Publish' should no longer be offered for an "
                    "already-Published version"
                )
                detail_page.close_actions_menu()

            with allure.step(
                'Step 8 — Click "Unpublish", confirm in the dialog; verify '
                "the unpublish POST succeeds and the version status reverts "
                "to Draft (the overflow menu offers 'Publish' again)"
            ):
                detail_page.open_unpublish_dialog(timeout=UI_ELEMENT_TIMEOUT)
                unpublish_status = detail_page.confirm_unpublish(
                    timeout=NAVIGATION_TIMEOUT
                )
                assert unpublish_status == 200, (
                    "unpublish POST should return 200, got "
                    f"{unpublish_status}"
                )

                detail_page.wait_for_publish_status_menuitem(
                    expect_unpublish=False, timeout=UI_ELEMENT_TIMEOUT
                )
                assert not detail_page.unpublish_version_menuitem.is_visible(), (
                    "'Unpublish' should no longer be offered — the version "
                    "is Draft again"
                )
                detail_page.close_actions_menu()

            if soft_failures:
                pytest.fail(
                    "Soft assertion(s) failed (known isolated product defect, "
                    "not test/infrastructure — the full publish/unpublish "
                    "cycle above passed cleanly):\n" + "\n".join(soft_failures)
                )
        finally:
            with allure.step(
                "Cleanup — delete the dedicated agent (including every "
                "version Publish/Unpublish accumulated on it)"
            ):
                try:
                    agent_api.delete_agent(agent_id)
                except Exception:
                    # Case Step 8 already unpublishes the version it created
                    # in the happy path, so this fallback only matters when
                    # the test failed BEFORE Step 8 ran (leaving a Published
                    # version behind) — delete_agent() 400s with "Cannot
                    # delete application with published or embedded
                    # versions" until every Published version is reverted
                    # first (AFS Cleanup section — no per-version delete
                    # API). Sweep and unpublish any still-Published version,
                    # then retry, so a mid-flow failure never leaks an
                    # undeletable agent.
                    try:
                        agent = agent_api.get_agent(agent_id)
                        for version in agent.get("versions", []):
                            if version.get("status") == "published":
                                agent_api.unpublish_version(version["id"])
                        agent_api.delete_agent(agent_id)
                    except Exception as cleanup_exc:
                        print(f"Warning: Failed to cleanup agent {agent_id}: {cleanup_exc}")
