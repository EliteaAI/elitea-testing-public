"""Skill Unpublish and Republish Lifecycle (ELITEA-2599).

Verifies the complete unpublish/republish lifecycle for a skill:

  Part A — Unpublish behavior: publishing v1.0 makes the skill appear in the
    Catalog; attaching it to an agent works and the agent applies it;
    unpublishing removes it from the Catalog IMMEDIATELY (no reload needed);
    the agent's skill attachment (``EntitySkillMapping``, scoped to the
    project-level skill id) is unaffected by the Catalog/publish status, so
    the agent keeps working with the skill after unpublish.

  Part B — Republish and version coexistence: an unpublished skill is still
    fully accessible/editable; republishing after an unpublish allocates a
    NEW ``public_skill_id`` (unpublish is a genuine deletion of the old
    catalog entry); publishing a SIBLING version of a skill whose public
    entry is still live REUSES that ``public_skill_id`` (adds a new
    ``public_version_id`` under the same entry) instead of creating a new
    entry — this is the coexistence mechanism, and the Catalog always shows
    exactly one card per active public entry.

Test case: ELITEA-2599
AFS: test-specs/skills/l3_skill-unpublish-republish-lifecycle_ELITEA-2599.md
"""

import logging
import time
from pathlib import Path

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from pages.agent_hub_page import AgentHubPage
from pages.skill_detail_page import SkillDetailPage

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.p3, pytest.mark.regression]

logger = logging.getLogger("elitea.tests.skills")

CATEGORY = "Quality Assurance"
# Same fixture image + repo-root-relative resolution as
# test_skill_publish_token_invalidation_and_ttl.py / test_skill_fork_end_to_end.py
# (parents[4]: skills -> ui -> tests -> automation -> repo root).
ICON_PATH = str(
    Path(__file__).resolve().parents[4] / "test-data" / "images" / "skill-fork-test-icon.png"
)
# >= 50 chars, contains an action verb — live-confirmed AI content-quality
# gate threshold (issue #1463, same gap already hit by ELITEA-2595/97).
DESCRIPTION = (
    "Converts all response text into upper case formatting whenever "
    "explicitly invoked by name, used to verify skill attachment for the "
    "ELITEA-2599 unpublish/republish lifecycle fixture."
)
# >= 100 chars — same threshold; bounded, permissive phrasing. Live-confirmed
# this run: the ORIGINAL coercive form ("CRITICAL: You MUST... Do NOT...")
# — the same style test_skill_agent_interaction.py uses for a skill that is
# never itself PUT THROUGH the publish content-quality gate — trips the AI
# prompt-injection heuristic HERE (422 FAIL: "Contains a prompt-injection
# style directive that attempts to override normal assistant behavior by
# forcing all-uppercase output and prohibiting explanation"). Rewritten as a
# plain stylistic preference with no imperative/coercive language, same
# deterministic upper-case marker for the chat-response assertion.
INSTRUCTIONS = (
    "This is a lightweight formatting skill for automated regression "
    "testing. When a user explicitly invokes this skill, respond in upper "
    "case letters as a simple stylistic choice, since upper case text is "
    "easy to verify programmatically in an automated test suite. Keep the "
    "reply brief and friendly."
)
NEUTRAL_TEXT_FOR_SKILL = "The quick brown fox jumps over the lazy dog"
# Underscore form — hyphens are silently rejected by the Tags field's
# NormalSingleTagNameInputRegExp (issue #1445/ELITEA-2433, re-confirmed live
# for this case in the AFS).
TAG = "lifecycle_test"

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
AI_RESPONSE_TIMEOUT = 60_000
PUBLISH_VALIDATE_ATTEMPTS = 3


def _make_skill_ready_for_publish(page, skill_api, name_prefix: str):
    """Create a skill via API, then add a tag + custom icon via UI (edit
    mode) and Save — the WARN/PASS prerequisite (issue #1463: a skill with
    only description/instructions still returns FAIL,
    ``validation_token: null``, at ``publish_skill_validate``).

    Mirrors ``test_skill_publish_token_invalidation_and_ttl.py``'s own
    helper of the same name/shape (ELITEA-2597) — icon FIRST (its own
    POST+PUT pair, independent of Save/Formik dirty state), tag SECOND
    (persists only via the ensuing ``save_edits()``); reversing the order
    risks the icon's own refetch discarding the not-yet-saved tag.

    Returns ``(detail_page, skill_id)`` — the page is already positioned on
    the skill's detail page, Save disabled (clean) after the commit.
    """
    ts = int(time.time() * 1000)
    skill_name = f"{name_prefix}-{ts}"[:32]

    created = skill_api.create_skill(
        name=skill_name, description=DESCRIPTION, instructions=INSTRUCTIONS,
    )
    skill_id = created["id"]
    logger.info("Created skill id=%s name=%s", skill_id, skill_name)

    detail_page = SkillDetailPage(page)
    detail_page.navigate(skill_id)
    detail_page.upload_skill_icon_edit_mode(ICON_PATH)
    detail_page.add_tag(TAG)
    assert detail_page.get_tags() == [TAG], (
        f"Expected the tag to commit before Save, got: {detail_page.get_tags()!r}"
    )
    assert detail_page.is_save_enabled(), (
        "Save should be ENABLED (dirty) immediately after committing the tag"
    )
    detail_page.save_edits(timeout=FORM_SAVE_TIMEOUT)
    assert not detail_page.is_save_enabled(), (
        "Save should be DISABLED again once the tag+icon edits are persisted"
    )
    logger.info("Skill id=%s ready for publish (icon+tag added, Save clean)", skill_id)
    return detail_page, skill_id, skill_name


def _publish_validate_with_retry(
    detail_page, version_name: str, category: str,
    attempts: int = PUBLISH_VALIDATE_ATTEMPTS, timeout: int = 15000,
):
    """Open the Publish wizard, fill Preparation, and click Continue —
    retrying up to *attempts* times ONLY on a transient 5xx from
    ``publish_skill_validate`` (AFS ELITEA-2599 § Known Defects: confirmed
    live environment flakiness — the SAME window also hit unrelated
    socket.io polling and a CORS failure — not a coexistence-specific
    rejection). A genuine 200 (WARN/PASS) or 422 (FAIL) is returned
    immediately on the first attempt, never retried; only a real, REPEATED
    5xx surfaces as a failure (via the last captured response).
    """
    last_response = None
    last_exc = None
    for attempt in range(1, attempts + 1):
        detail_page.open_publish_wizard()
        detail_page.fill_publish_preparation_step(version_name, category)
        try:
            response = detail_page.click_publish_continue(timeout=timeout)
        except Exception as exc:  # noqa: BLE001 - bounded retry, re-raised below if exhausted
            last_exc = exc
            logger.warning(
                "publish_skill_validate attempt %d/%d for version %r raised "
                "%s — retrying (AFS-documented transient env flakiness)",
                attempt, attempts, version_name, exc,
            )
            try:
                detail_page.close_publish_wizard()
            except Exception:
                pass
            continue
        if response.status < 500:
            return response
        last_response = response
        logger.warning(
            "publish_skill_validate returned %d on attempt %d/%d for version "
            "%r — retrying (AFS-documented transient env flakiness)",
            response.status, attempt, attempts, version_name,
        )
        detail_page.close_publish_wizard()
    if last_response is not None:
        return last_response
    raise last_exc


def _publish_and_capture(detail_page, version_name: str, category: str):
    """Full Publish flow (validate + confirm) returning the ``publish_skill``
    JSON body. Asserts the validate step never reports FAIL (the icon+tag
    prerequisite makes that unexpected) and the publish itself returns 200.
    """
    validate_response = _publish_validate_with_retry(detail_page, version_name, category)
    assert validate_response.status == 200, (
        f"Expected 200 from publish_skill_validate for version {version_name!r}, "
        f"got {validate_response.status}: {validate_response.text()}"
    )
    validate_body = validate_response.json()
    assert validate_body.get("status") != "FAIL", (
        f"Expected a non-FAIL validation status for version {version_name!r} "
        f"(icon+tag prerequisites are satisfied), got: {validate_body}"
    )
    assert detail_page.is_publish_confirm_enabled(), (
        "Publish button should be enabled after a non-FAIL validation"
    )

    publish_response = detail_page.confirm_publish_and_capture_response()
    assert publish_response.status == 200, (
        f"Expected 200 from publish_skill for version {version_name!r}, "
        f"got {publish_response.status}: {publish_response.text()}"
    )
    body = publish_response.json()
    assert body.get("msg") == "Successfully published", (
        f"Expected 'Successfully published' msg, got: {body}"
    )
    assert body.get("public_skill_id") is not None, f"Expected a public_skill_id, got: {body}"
    assert body.get("public_version_id") is not None, f"Expected a public_version_id, got: {body}"
    logger.info(
        "Published version %r: public_skill_id=%s public_version_id=%s",
        version_name, body["public_skill_id"], body["public_version_id"],
    )
    return body


class TestSkillUnpublishRepublishLifecycle:
    """ELITEA-2599 — Skill Unpublish and Republish Lifecycle."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "skills/ELITEA-2599_skill-unpublish-and-republish-lifecycle.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p3
    def test_unpublish_republish_lifecycle(self, page, skill_api, agent_api):
        skill_id = None
        agent_id = None
        try:
            with allure.step(
                "Step 1 — Create a skill with valid content, add a tag and "
                "a custom icon, save; verify skill created and Save disabled "
                "after the tag+icon commit"
            ):
                detail_page, skill_id, skill_name = _make_skill_ready_for_publish(
                    page, skill_api, "el-2599-lc"
                )
                assert "/skills/all/" in page.url, (
                    f"Expected to be on the skill detail page, got: {page.url}"
                )
                # Capture the DRAFT version's own id (distinct integer from
                # skill_id — confirmed live, e.g. skill=1495 vs
                # version_details.id=1554, same split test_skill_fork_end_to_end.py
                # relies on) so Step 3 can assert the published clone got a
                # NEW version id relative to the actual thing it was cloned
                # from, not the unrelated skill_id.
                draft_version_id_v1 = skill_api.get_skill(skill_id)["version_details"]["id"]

            with allure.step(
                "Step 2 — Open the Publish wizard, fill Version name v1.0 + "
                "Category, agree to terms, Continue; verify a non-FAIL "
                "validation status (WARN or PASS, never gated on which)"
            ):
                v1_validate = _publish_validate_with_retry(detail_page, "v1.0", CATEGORY)
                assert v1_validate.status == 200, (
                    f"Expected 200 from publish_skill_validate, got "
                    f"{v1_validate.status}: {v1_validate.text()}"
                )
                v1_validate_body = v1_validate.json()
                assert v1_validate_body.get("status") != "FAIL", (
                    f"Expected a non-FAIL validation status, got: {v1_validate_body}"
                )

            with allure.step(
                "Step 3 — Click Publish; verify 200 + payload (public_skill_id/"
                "public_version_id/source_version_id), then verify the skill "
                "appears in the Catalog (baseline, checked before unpublish)"
            ):
                v1_publish = detail_page.confirm_publish_and_capture_response()
                assert v1_publish.status == 200, (
                    f"Expected 200 from publish_skill, got {v1_publish.status}: "
                    f"{v1_publish.text()}"
                )
                v1_body = v1_publish.json()
                assert v1_body.get("msg") == "Successfully published", (
                    f"Expected 'Successfully published' msg, got: {v1_body}"
                )
                public_skill_id_v1 = v1_body["public_skill_id"]
                public_version_id_v1 = v1_body["public_version_id"]
                source_version_id_v1 = v1_body["source_version_id"]
                assert source_version_id_v1 != draft_version_id_v1, (
                    "The published clone's version id should be a NEW id, "
                    "distinct from the original draft VERSION's own id "
                    f"(draft_version_id_v1={draft_version_id_v1}) — a republish-"
                    "in-place regression that reused the draft's own version "
                    "id would trivially satisfy a comparison against the "
                    "unrelated skill_id instead"
                )
                logger.info(
                    "v1.0 published: public_skill_id=%s public_version_id=%s "
                    "source_version_id=%s",
                    public_skill_id_v1, public_version_id_v1, source_version_id_v1,
                )

                catalog_page = AgentHubPage(page)
                catalog_page.navigate()
                catalog_page.click_skills_tab(timeout=UI_ELEMENT_TIMEOUT)
                assert catalog_page.is_skill_card_visible(
                    public_skill_id_v1, timeout=NAVIGATION_TIMEOUT
                ), (
                    f"Expected the v1.0 Catalog card (public_skill_id="
                    f"{public_skill_id_v1}) to be visible after publishing"
                )

            with allure.step(
                "Step 4 — Create an agent and attach the published skill to it"
            ):
                created_agent = agent_api.create_agent(
                    name=f"skill-consumer-{skill_id}",
                    description="Disposable agent for ELITEA-2599 lifecycle test",
                    instructions="You are a helpful assistant.",
                )
                agent_id = created_agent["id"]
                agent_page = AgentDetailPage(page)
                agent_page.navigate(agent_id)
                agent_page.attach_skill(skill_name, timeout=UI_ELEMENT_TIMEOUT)
                assert "1/" in agent_page.get_skills_counter_text(), (
                    "Skills counter should show 1 skill attached after attaching"
                )
                assert agent_page.is_skill_attached(skill_name), (
                    f"Skill card for {skill_name!r} should render in the "
                    "agent's Skills section after attaching"
                )

            with allure.step(
                "Step 5 — Test the agent (explicit ~mention) to verify the "
                "skill is applied"
            ):
                initial_count = agent_page.get_chat_message_count()
                agent_page.send_chat_message_with_mention(
                    skill_name, NEUTRAL_TEXT_FOR_SKILL, timeout=UI_ELEMENT_TIMEOUT,
                )
                agent_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                response_before_unpublish = agent_page.get_last_chat_response_text()
                logger.info("Response before unpublish: %r", response_before_unpublish)
                alpha_chars = [c for c in response_before_unpublish if c.isalpha()]
                assert alpha_chars, (
                    f"~{skill_name} response has no alphabetic chars: "
                    f"{response_before_unpublish!r}"
                )
                assert all(c.isupper() for c in alpha_chars), (
                    f"~{skill_name} should return UPPER CASE text before "
                    f"unpublish, got: {response_before_unpublish!r}"
                )

            with allure.step(
                "Step 6 — Navigate to the skill's Published (v1.0) version; "
                "open the overflow menu's Unpublish confirm dialog; verify "
                "the dialog title/body text"
            ):
                detail_page.navigate(skill_id)
                detail_page.switch_version("v1.0", timeout=UI_ELEMENT_TIMEOUT)
                detail_page.open_unpublish_dialog(timeout=UI_ELEMENT_TIMEOUT)
                dialog_text = detail_page.get_unpublish_dialog_text(timeout=UI_ELEMENT_TIMEOUT)
                assert "Unpublish Skill" in dialog_text, (
                    f"Expected the 'Unpublish Skill' dialog title, got: {dialog_text!r}"
                )
                assert "removed from ELITEA Catalog" in dialog_text, (
                    f"Expected the Catalog-removal warning text, got: {dialog_text!r}"
                )

            with allure.step(
                "Step 7 — Click Unpublish to confirm; verify 200 + "
                "{status: 'deleted'}"
            ):
                unpublish_body = detail_page.confirm_unpublish_and_capture_response(
                    timeout=NAVIGATION_TIMEOUT
                )
                assert unpublish_body["http_status"] == 200, (
                    f"Expected 200 from unpublish_skill, got {unpublish_body['http_status']}"
                )
                assert unpublish_body.get("msg") == "Successfully unpublished", (
                    f"Expected msg 'Successfully unpublished', got: {unpublish_body!r}"
                )
                assert unpublish_body.get("status") == "deleted", (
                    f"Expected status 'deleted', got: {unpublish_body!r}"
                )

            with allure.step(
                "Step 8 — Navigate to the Catalog; verify the skill is "
                "IMMEDIATELY absent (no reload beyond a fresh navigation)"
            ):
                catalog_page.navigate()
                catalog_page.click_skills_tab(timeout=UI_ELEMENT_TIMEOUT)
                catalog_page.wait_for_skill_card_absent(
                    public_skill_id_v1, timeout=NAVIGATION_TIMEOUT
                )

            with allure.step(
                "Step 9 — Navigate back to the agent from Step 4; verify the "
                "skill attachment reference is still present (EntitySkillMapping "
                "is scoped to the project-level skill id, independent of "
                "Catalog/publish status)"
            ):
                agent_page.navigate(agent_id)
                # The Skills counter can render transiently ("0/5") right
                # after a full-page navigate before the RTK Query cache
                # refetches (AgentDetailPage.wait_for_skills_counter()'s own
                # documented race) — poll for the settled value rather than
                # a single post-navigate read.
                settled_counter = agent_page.wait_for_skills_counter(
                    "1/", timeout=NAVIGATION_TIMEOUT
                )
                assert settled_counter.startswith("1/"), (
                    "Skills counter should still show 1 skill attached after "
                    f"the skill's Catalog entry was unpublished, got: {settled_counter!r}"
                )
                assert agent_page.is_skill_attached(skill_name), (
                    f"Skill card for {skill_name!r} should still render in "
                    "the agent's Skills section after unpublish"
                )

            with allure.step(
                "Step 10 — Test the agent again; verify it still works with "
                "the (now-unpublished) skill"
            ):
                # No clear_embedded_chat() here — Step 9's navigate(agent_id)
                # already lands on a fresh embedded chat (0 messages), and
                # ClearChatButton.jsx stays DISABLED with nothing to clear
                # (confirmed live: a clear attempt right after navigate times
                # out waiting for the disabled button to become enabled).
                initial_count = agent_page.get_chat_message_count()
                agent_page.send_chat_message_with_mention(
                    skill_name, NEUTRAL_TEXT_FOR_SKILL, timeout=UI_ELEMENT_TIMEOUT,
                )
                agent_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=AI_RESPONSE_TIMEOUT,
                )
                response_after_unpublish = agent_page.get_last_chat_response_text()
                logger.info("Response after unpublish: %r", response_after_unpublish)
                alpha_chars = [c for c in response_after_unpublish if c.isalpha()]
                assert alpha_chars, (
                    f"~{skill_name} response has no alphabetic chars after "
                    f"unpublish: {response_after_unpublish!r}"
                )
                assert all(c.isupper() for c in alpha_chars), (
                    f"~{skill_name} should still return UPPER CASE text "
                    f"after unpublish, got: {response_after_unpublish!r}"
                )

            with allure.step(
                "Step 11 — Navigate to the now-unpublished skill version; "
                "verify it's still accessible/editable and the overflow menu "
                "now offers Publish again (not Unpublish)"
            ):
                detail_page.navigate(skill_id)
                detail_page.switch_version("v1.0", timeout=UI_ELEMENT_TIMEOUT)
                detail_page.open_actions_menu()
                assert detail_page.publish_menuitem.is_visible(), (
                    "'Publish' should be offered again for the now-Draft "
                    "(unpublished) version"
                )
                assert not detail_page.unpublish_menuitem.is_visible(), (
                    "'Unpublish' should no longer be offered — the version "
                    "is Draft again"
                )
                detail_page.close_actions_menu()

            with allure.step(
                "Step 12 — Publish it again as v2.0; verify 200, and that "
                "the resulting public_skill_id is a NEW id, distinct from "
                "v1.0's (unpublish is a genuine deletion — republish always "
                "starts a fresh public entry)"
            ):
                v2_body = _publish_and_capture(detail_page, "v2.0", CATEGORY)
                public_skill_id_v2 = v2_body["public_skill_id"]
                assert public_skill_id_v2 != public_skill_id_v1, (
                    "Republishing after an unpublish should allocate a NEW "
                    f"public_skill_id, distinct from v1.0's "
                    f"({public_skill_id_v1!r}), got the same id again: "
                    f"{public_skill_id_v2!r}"
                )

            with allure.step(
                "Step 13 — Navigate to the Catalog; verify v2.0 is visible "
                "as a single card"
            ):
                catalog_page.navigate()
                catalog_page.click_skills_tab(timeout=UI_ELEMENT_TIMEOUT)
                assert catalog_page.is_skill_card_visible(
                    public_skill_id_v2, timeout=NAVIGATION_TIMEOUT
                ), (
                    f"Expected the v2.0 Catalog card (public_skill_id="
                    f"{public_skill_id_v2}) to be visible after republishing"
                )
                assert catalog_page.get_skill_card_count_by_name(skill_name) == 1, (
                    "Expected exactly ONE Catalog card for the skill after "
                    "republishing as v2.0"
                )

            with allure.step(
                "Step 14 — WITHOUT unpublishing v2.0, publish the base draft "
                "as v3.0; verify 200 with the SAME public_skill_id as v2.0 "
                "(the coexistence mechanism: a sibling version publish while "
                "the public entry stays live ADDS a version under it instead "
                "of creating a new entry)"
            ):
                detail_page.navigate(skill_id)
                detail_page.switch_version("base", timeout=UI_ELEMENT_TIMEOUT)
                v3_body = _publish_and_capture(detail_page, "v3.0", CATEGORY)
                public_skill_id_v3 = v3_body["public_skill_id"]
                public_version_id_v3 = v3_body["public_version_id"]
                assert public_skill_id_v3 == public_skill_id_v2, (
                    "Publishing a sibling version (v3.0) while v2.0's public "
                    f"entry is still live should REUSE public_skill_id "
                    f"{public_skill_id_v2!r}, got a different id: "
                    f"{public_skill_id_v3!r}"
                )
                assert public_version_id_v3 != v2_body["public_version_id"], (
                    "v3.0 should allocate its OWN public_version_id, "
                    "distinct from v2.0's, under the same public_skill_id"
                )

            with allure.step(
                "Step 15 — Navigate to the Catalog; verify STILL only ONE "
                "card for the skill (structural coexistence: one growing "
                "public entry, never duplicate cards)"
            ):
                catalog_page.navigate()
                catalog_page.click_skills_tab(timeout=UI_ELEMENT_TIMEOUT)
                assert catalog_page.is_skill_card_visible(
                    public_skill_id_v2, timeout=NAVIGATION_TIMEOUT
                ), (
                    f"Expected the (still-active) public_skill_id="
                    f"{public_skill_id_v2} Catalog card to be visible"
                )
                assert catalog_page.get_skill_card_count_by_name(skill_name) == 1, (
                    "Expected exactly ONE Catalog card for the skill even "
                    "after a second sibling-version publish (v3.0)"
                )

            with allure.step(
                "Step 16 — (Exploratory, soft) Publish a 4th version (v4.0) "
                "of the same skill without unpublishing v2.0/v3.0; the case "
                "does not prescribe a concrete expected behavior for a "
                "3rd-coexisting-version publish, so a 200 with no visible "
                "rejection is logged as an observation, not asserted as a "
                "hard requirement"
            ):
                detail_page.navigate(skill_id)
                detail_page.switch_version("base", timeout=UI_ELEMENT_TIMEOUT)
                v4_body = _publish_and_capture(detail_page, "v4.0", CATEGORY)
                logger.info(
                    "Step 16 (exploratory): v4.0 publish accepted — "
                    "public_skill_id=%s public_version_id=%s (soft "
                    "observation only, case text is non-prescriptive here)",
                    v4_body["public_skill_id"], v4_body["public_version_id"],
                )
        finally:
            with allure.step("Cleanup — delete the created agent and skill"):
                if agent_id is not None:
                    try:
                        agent_api.delete_agent(agent_id)
                        logger.info("Cleanup: deleted agent id=%d", agent_id)
                    except Exception as exc:
                        logger.warning("Cleanup: failed to delete agent id=%s: %s", agent_id, exc)
                if skill_id is not None:
                    try:
                        skill_api.delete_skill(skill_id)
                        logger.info("Cleanup: deleted skill id=%s", skill_id)
                    except Exception as exc:
                        logger.warning("Cleanup: failed to delete skill id=%s: %s", skill_id, exc)
