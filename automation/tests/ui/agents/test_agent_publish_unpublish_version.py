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

Three MINOR, isolated product defects were found live during this run
(neither blocks the functional flow):

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
   navigation"). The SAME defect stales THREE distinct pieces of
   version-scoped client state, each hardened with the SAME poll+API-
   tie-breaker principle (single deterministic failure signature — PR #615
   review round 2):
   a. The VERSION selector/URL/Information-panel id triad itself
      (``select_version_by_name()``, Step 6b) — a bounded 2-cycle
      select+reload retry first; if that never converges,
      ``_confirm_new_version_via_api()`` asks the API whether a distinct
      ``published`` version with the expected name already exists
      server-side. Step 6c (which depends on this same VERSION-selector
      state) is skipped when this happens — re-checking it would just
      re-fail on the identical staleness instead of consolidating into
      one signature.
   b. The actions-menu's Publish/Unpublish menuitem (Steps 7/8) — even
      after (a) agrees. ``wait_for_publish_status_menuitem()`` polls via
      bounded open/close attempts, then a full-page-reload escalation; if
      that never converges, ``_confirm_version_status_via_api()`` asks the
      API whether the version's real status already matches.
   Only a backend-confirmed match is recorded into the SAME
   ``soft_failures``/``pytest.fail()`` mechanism as #611; a backend that
   disagrees too is a genuinely different, real bug and is left to fail
   hard, never silently downgraded (reverse-masking guard).
3. https://github.com/EliteaAI/elitea-testing-public/issues/554 — an
   already-filed, unrelated, intermittent RTK-Query timing race
   (``EliteaUI/src/api/toolkits.js``'s ``toolkitTypes`` endpoint firing
   before ``useSelectedProjectId()`` resolves, 404ing on
   ``.../toolkits/prompt_lib/`` with an empty projectId segment) —
   confirmed to also fire on THIS page (Step 1's initial ``navigate()``
   is a full page load, the same trigger condition already documented on
   #554 as reproducible on any page render, not just Credentials). Since
   the console listener is registered before Step 1 (deliberately, to
   observe the Publish wizard's own Stepper renders later), Step 1's own
   page-load noise was landing inside Step 6a's "wizard console
   cleanliness" window under the original filter, producing an
   ``OTHER_UNEXPECTED`` failure distinct from #611/#614 (observed 1/14
   runs in the PR #615 round-2 verification batch). Filtered using the
   SAME technique already established in
   ``test_credential_search_by_name.py`` — matched on
   ``msg.location.url`` containing the toolkits endpoint path, never a
   blanket "any 404" filter, so an unrelated 404 from a genuinely
   different resource still surfaces as a real failure.

Spec: test-specs/agents/l2_publish-draft-version-status-changes-unpublish-available_ELITEA-1892.md
"""

import uuid

import allure
import pytest

from config import settings
from pages.agent_detail_page import AgentDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.new_verified]

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


# Known defect #554 (already filed, unrelated) — confirmed live during PR
# #615 review round 2 (1/14 runs of the verification batch): an RTK-Query
# timing race in EliteaUI/src/api/toolkits.js's `toolkitTypes` endpoint
# fires before `useSelectedProjectId()` resolves, building the URL with an
# empty projectId segment (".../toolkits/prompt_lib/") which 404s.
# Intermittent (client-side race, not deterministic) and unrelated to the
# Publish/Unpublish flow under test here — Step 1's initial navigate() (a
# full page load, the same trigger condition #554 documents as
# reproducible on "any page render", not just Credentials, where it was
# first filed) is the observed source, well before the Publish wizard
# itself ever opens. SAME filter technique already established in
# test_credential_search_by_name.py — matched on msg.location.url
# containing the toolkits endpoint path, NOT a blanket "any 404" filter,
# so an unrelated 404 from a genuinely different resource still surfaces
# as a real, unexpected failure.
def _is_known_554_toolkits_404(msg) -> bool:
    location_url = (msg.location or {}).get("url", "")
    return "404" in msg.text and "elitea_core/toolkits/prompt_lib/" in location_url


def _confirm_version_status_via_api(
    agent_api, agent_id: int, version_id, expect_published: bool
) -> bool:
    """API-backed tie-breaker for a ``wait_for_publish_status_menuitem``
    DOM-poll timeout (Known defect #614).

    The underlying publish/unpublish data is confirmed always correct via
    the API even when the actions-menu DOM lags (implementer + reviewer
    findings, PR #615). This is the ground truth used to decide whether a
    menu-poll timeout is PROVABLY #614's cosmetic staleness (backend
    already agrees with the expected status — safe to soft-assert) or a
    genuinely different, new bug (backend disagrees too — must stay
    hard). Per the reverse-masking guard, a menu-poll timeout is never
    blanket-downgraded to "soft" without this independent confirmation
    first — only a confirmed-correct backend state earns the known-defect
    label; a backend that's ALSO wrong is a real, unrelated failure.

    Args:
        agent_api: The ``AgentAPI`` client (test-level only — page objects
            never reach into the API layer per the project's layering).
        agent_id: The agent's numeric id.
        version_id: The specific version id whose status is in question —
            accepts either the API's numeric id or the DOM's stringified
            id (``AgentDetailPage.get_version_id()`` returns ``str``); the
            comparison below normalizes both sides to ``str`` (PR #615
            review round 2 fix — an int/str mismatch here made this
            tie-breaker return ``False`` for EVERY call, silently turning
            every confirmed #614 occurrence into a false hard-fail).
        expect_published: ``True`` to confirm status ``"published"``,
            ``False`` to confirm ``"draft"``.

    Returns:
        ``True`` only if the API confirms the expected status for
        ``version_id``; ``False`` if it disagrees or the version can't be
        found on the agent.
    """
    agent = agent_api.get_agent(agent_id)
    expected_status = "published" if expect_published else "draft"
    for version in agent.get("versions", []):
        if str(version.get("id")) == str(version_id):
            return version.get("status") == expected_status
    return False


def _confirm_new_version_via_api(
    agent_api, agent_id: int, version_name: str, exclude_version_id
):
    """API-backed tie-breaker for a ``select_version_by_name`` DOM-poll
    timeout (Known defect #614).

    Mirrors ``_confirm_version_status_via_api()``'s role for
    ``wait_for_publish_status_menuitem`` — the underlying publish data is
    confirmed always correct via the API even when the VERSION-selector
    DOM lags (implementer + reviewer findings, PR #615 review round 2).
    Used to decide whether a ``select_version_by_name`` timeout is
    PROVABLY #614's cosmetic staleness (a distinct, ``published`` version
    with the expected name already exists server-side — the publish clone
    succeeded, only the client-side DOM never reflected it) or a
    genuinely different, new bug (no such version exists — must stay
    hard).

    Args:
        agent_api: The ``AgentAPI`` client (test-level only — page objects
            never reach into the API layer per the project's layering).
        agent_id: The agent's numeric id.
        version_name: The version name Publish was supposed to create,
            e.g. ``"v1-release"``.
        exclude_version_id: The pre-publish (Draft/"base") version id —
            excluded so a stale match against the ORIGINAL version can't
            be mistaken for confirmation that a NEW one was created.
            Accepts either the API's numeric id or the DOM's stringified
            id; compared as ``str`` (same normalization as
            ``_confirm_version_status_via_api()``).

    Returns:
        The new version's numeric id if the API confirms a distinct,
        published version named ``version_name`` exists; ``None`` if no
        such version is found.
    """
    agent = agent_api.get_agent(agent_id)
    for version in agent.get("versions", []):
        if (
            version.get("name") == version_name
            and str(version.get("id")) != str(exclude_version_id)
            and version.get("status") == "published"
        ):
            return version.get("id")
    return None


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
                "this assertion stays scoped away from Step 6b's OWN "
                "reload-time noise. The window still spans Step 1's initial "
                "navigate() (also a full page load) — confirmed live (PR "
                "#615 review round 2) that the SAME already-filed, "
                "unrelated toolkits 404 (#554) can fire there too, so it is "
                "explicitly filtered by resource URL (not blanket-excluded "
                "as 'any 404') alongside #611"
            ):
                unexpected_errors = [
                    m.text for m in console_errors
                    if not _is_known_defect_611(m.text)
                    and not _is_known_554_toolkits_404(m)
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
                'dropdown after the post-publish navigation"). '
                "select_version_by_name() itself now retries a bounded "
                "2 full select+reload cycles; if its DOM poll STILL never "
                "converges, an API-backed tie-breaker "
                "(_confirm_new_version_via_api) decides whether that's "
                "confirmed #614 cosmetic staleness (the clone succeeded "
                "server-side, only the DOM never reflected it) or a "
                "genuinely different bug — same principle as Step 7/8's "
                "menuitem tie-breaker (PR #615 review round 2)"
            ):
                try:
                    new_version_id = detail_page.select_version_by_name(
                        VERSION_NAME, timeout=UI_ELEMENT_TIMEOUT
                    )
                    version_dom_converged = True
                except AssertionError as select_exc:
                    version_dom_converged = False
                    new_version_id = _confirm_new_version_via_api(
                        agent_api, agent_id, VERSION_NAME,
                        exclude_version_id=base_version_id,
                    )
                    if new_version_id is None:
                        # API disagrees too — NOT confirmed #614 cosmetic
                        # staleness. A genuinely different, real bug: stay
                        # hard, don't mask it as the known defect.
                        raise AssertionError(
                            f"{select_exc} (API tie-breaker ALSO disagrees — "
                            f"no distinct 'published' version named "
                            f"{VERSION_NAME!r} exists server-side either; "
                            "this is NOT confirmed as known defect #614's "
                            "cosmetic staleness)"
                        ) from select_exc
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/614: "
                        "select_version_by_name's DOM poll never converged on "
                        f"{VERSION_NAME!r} even though the API confirms a "
                        f"distinct published version (id={new_version_id}) "
                        f"already exists (client-side status staleness, not "
                        f"a data bug): {select_exc}"
                    )

                if version_dom_converged:
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
                f"{VERSION_NAME!r} (selected/active). Skipped when Step "
                "6b's DOM poll never converged (known defect #614, "
                "API-confirmed) — the VERSION dropdown's own client state "
                "is the exact thing that failed to converge there, so "
                "re-checking it here would just re-fail on the SAME "
                "staleness under a different assertion instead of "
                "consolidating into Step 6b's already-recorded soft failure"
            ):
                if version_dom_converged:
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
                "selector/URL agree — poll via open/close attempts, then "
                "an API-backed tie-breaker if the poll never converges, "
                "rather than a single point-in-time check)"
            ):
                try:
                    detail_page.wait_for_publish_status_menuitem(
                        expect_unpublish=True, timeout=UI_ELEMENT_TIMEOUT
                    )
                    menu_converged = True
                except AssertionError as menu_exc:
                    menu_converged = False
                    if not _confirm_version_status_via_api(
                        agent_api, agent_id, new_version_id, expect_published=True
                    ):
                        # API disagrees too — NOT confirmed #614 cosmetic
                        # staleness. A genuinely different, real bug: stay
                        # hard, don't mask it as the known defect.
                        raise AssertionError(
                            f"{menu_exc} (API tie-breaker ALSO disagrees — "
                            f"version {new_version_id} is not 'published' "
                            "server-side either; this is NOT confirmed as "
                            "known defect #614's cosmetic staleness)"
                        ) from menu_exc
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/614: "
                        "actions-menu never showed 'Unpublish' within the poll "
                        f"budget even though the API confirms version "
                        f"{new_version_id} is already 'published' (client-side "
                        f"status staleness, not a data bug): {menu_exc}"
                    )

                if menu_converged:
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

                try:
                    detail_page.wait_for_publish_status_menuitem(
                        expect_unpublish=False, timeout=UI_ELEMENT_TIMEOUT
                    )
                    menu_converged = True
                except AssertionError as menu_exc:
                    menu_converged = False
                    if not _confirm_version_status_via_api(
                        agent_api, agent_id, new_version_id, expect_published=False
                    ):
                        raise AssertionError(
                            f"{menu_exc} (API tie-breaker ALSO disagrees — "
                            f"version {new_version_id} is not 'draft' "
                            "server-side either; this is NOT confirmed as "
                            "known defect #614's cosmetic staleness)"
                        ) from menu_exc
                    soft_failures.append(
                        "Known defect https://github.com/EliteaAI/elitea-testing-public/issues/614: "
                        "actions-menu never showed 'Publish' within the poll "
                        f"budget even though the API confirms version "
                        f"{new_version_id} is already 'draft' again "
                        f"(client-side status staleness, not a data bug): {menu_exc}"
                    )

                if menu_converged:
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
