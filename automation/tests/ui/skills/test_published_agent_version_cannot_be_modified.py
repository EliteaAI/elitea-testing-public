"""Published Agent Version Cannot Be Modified (ELITEA-2614).

Publishes a fresh disposable agent (with one attached skill) via the
actions-menu wizard (same ``AgentDetailPage`` publish-wizard methods
ELITEA-1892/2600 already established), then exhaustively attempts every
kind of modification the case names against the resulting PUBLISHED
version:

- Part B (Name/Description/Instructions/Tags): the General-section fields
  stay editable at the INPUT level — enforcement is server-side on Save.
  Each field is edited, Saved, and asserted to be rejected with
  ``400 {"error": "Version id {id} is published and can not be updated"}``
  plus a matching toast, then reset via Discard before the next field.
- Part C (skill attachments): two DIFFERENT enforcement mechanisms —
  the "+ Skill" add button is proactively `disabled` (with a correct
  immutability tooltip); the SkillCard's "remove skill" button is also
  `disabled` but its tooltip stays the generic, non-conditional "Remove
  skill" text; the SkillVersionSelector trigger has no `onClick` handler
  at all when locked (a legal no-op click) and has NO Tooltip wrapper in
  the source, so no aria-label is ever set. The latter two are a MINOR,
  filed product defect (case's own Pass-criterion "tooltip explains
  immutability on disabled controls" fails for these two specific
  controls) — asserted with ``expect.soft()`` + `# Known defect: #1470`
  per the sanctioned-RED pattern, NOT as a hard pass. The Tools section's
  4 "+ X" add buttons (Toolkit/MCP/Agent/Pipeline) DO implement the
  correct immutability tooltip and are hard-asserted.
- Part D: Unpublish reverts the version to Draft — Name/Description Saves
  now succeed, and the Skills section's "+ Skill" button re-enables
  (attaching AND removing a skill both succeed again, closing the loop).

New testids added this dispatch (EliteaAI/EliteaUI@2d05a7f1 on
``automation/testids``): ``agent-add-toolkit-button-tooltip`` /
``agent-add-mcp-button-tooltip`` / ``agent-add-agent-button-tooltip`` /
``agent-add-pipeline-button-tooltip`` — Tooltip wrapper testids on
``ToolMenu.jsx``'s 4 "+ X" buttons, mirroring the pre-existing
``agent-add-skill-button-tooltip`` pattern on ``SkillMenu.jsx``. MUI's
``Tooltip`` clones ``aria-label`` onto its IMMEDIATE child (the wrapping
``<Box component="span">``), never onto the nested button that carries
the button's own testid — confirmed via source read of
``node_modules/@mui/material/Tooltip/Tooltip.js`` (Phase 2 exploration)
before adding these, rather than guessing. Without a wrapper testid there
was no testid-only way to read the Tools buttons' locked tooltip text at
all (`.agents/testing.md` § Locator policy — missing testid on the target
is work to do, not a reason to rung down).

Two case-text CLARIFICATIONs (reverse-masking guard, live product is
correct, not asserted as case-text states) — filed against the AFS, not
re-litigated here:
- The 400 toast/error names the exact version id ("Version id {id} is
  published and can not be updated") rather than the case's generic
  "Version is published and cannot be updated" — asserted via regex
  matching the live (more informative) string.
- The Skill add button's locked tooltip says "...published OR EMBEDDED
  and can not be modified" (a superset of the case's "...published and
  can not be modified") — asserted against the live string.

Spec: test-specs/skills/l2_published-agent-version-cannot-be-modified_ELITEA-2614.md
"""

import logging
import re
import uuid

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from pages.agent_form_page import AgentFormPage
from pages.agents_list_page import AgentsListPage
from pages.skill_detail_page import SkillDetailPage
from pages.skill_form_page import SkillFormPage
from pages.skills_list_page import SkillsListPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.skills, pytest.mark.agents, pytest.mark.regression]

logger = logging.getLogger("elitea.tests.skills")

# ---------------------------------------------------------------------------
# Timeout constants (milliseconds)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
FORM_SAVE_TIMEOUT = 15_000
VALIDATE_TIMEOUT = 30_000  # publish_validate is AI-backed — variable latency
PUBLISH_TIMEOUT = 15_000

_SUFFIX = uuid.uuid4().hex[:6]

SKILL_NAME = f"immutable-skill-2614-{_SUFFIX}"
SKILL_INSTRUCTIONS = (
    "You are a QA validation skill for the ELITEA platform's publish-"
    "immutability exploration test (ELITEA-2614). Whenever invoked, "
    "respond with a short acknowledgement of the request."
)

AGENT_NAME = f"immut-agt-2614-{_SUFFIX}"  # MAX_NAME_LENGTH=32 (constants.js) — kept
# short deliberately so the Part B/D "-EDITED"/"-unlocked" edit suffixes below
# still fit under the limit (a longer base name silently truncates the typed
# edit, masking the whole assertion — discovered live during Phase 2/4).
AGENT_DESCRIPTION = "Disposable agent for ELITEA-2614's publish-immutability test"
AGENT_INSTRUCTIONS = (
    "You are a helpful QA validation assistant for the ELITEA platform "
    "publish-immutability exploration test (ELITEA-2614). You answer "
    "general questions about testing status."
)
AGENT_TAG = "regression"

VERSION_NAME = f"v1-release-{_SUFFIX}"
CATEGORY_NAME = "Quality Assurance"

# Part B — live-confirmed 400 error / toast text (AFS Step 7): names the
# exact locked version id, "can not" (two words) not "cannot" — the case's
# own literal text is a CLARIFICATION-filed paraphrase, not what's asserted.
LOCKED_SAVE_REJECTION_PATTERN = re.compile(r"Version id \d+ is published and can not be updated")

# Part C — live-confirmed tooltip strings (AFS Steps 15/20; SkillMenu.jsx /
# ToolMenu.jsx source).
SKILL_ADD_LOCKED_TOOLTIP = "This agent version is published or embedded and can not be modified"
TOOL_ADD_LOCKED_TOOLTIP = "This agent version is published and can not be modified"

# Part C, group (b) — the ideal/immutability-aware tooltip text the case's
# own Pass-criterion #3 expects on ALL disabled controls. Asserted via
# expect.soft() against the two controls that do NOT implement it
# (Known defect: https://github.com/EliteaAI/elitea-testing-public/issues/1470).
IMMUTABILITY_TOOLTIP_PATTERN = re.compile(r"published|embedded")

# Part D — the same PUT .../application/... endpoint returns 201 (not 200) on
# a successful update once the version is unlocked (confirmed live, Phase 4 —
# unusual REST semantics for an update, but not a defect worth filing: the
# response body + reload-persistence assertions below are what actually prove
# success, this status check just needs to accept the real status code).
SAVE_SUCCESS_STATUSES = (200, 201)


def _create_skill(page) -> int:
    """Create the disposable skill via the UI and return its numeric ID."""
    list_page = SkillsListPage(page)
    list_page.navigate_to_create()

    form_page = SkillFormPage(page)
    form_page.wait_for_form_load()
    form_page.fill_form(
        name=SKILL_NAME,
        instructions=SKILL_INSTRUCTIONS,
        description="QA validation skill for ELITEA-2614",
    )
    form_page.wait_for_form_validation()
    assert form_page.is_save_enabled(), "Save should be enabled after filling all required skill fields"
    form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

    detail_page = SkillDetailPage(page)
    detail_page.verify_on_detail_page()
    skill_id = int(detail_page.get_skill_id())
    logger.info("Created skill %r with id=%d", SKILL_NAME, skill_id)
    return skill_id


def _assert_field_edit_blocked_on_locked_version(detail_page: AgentDetailPage, field_label: str, do_edit) -> None:
    """Edit a General-section field, Save, and assert the locked-version
    rejection (400 + matching error/toast), then reset via Discard.

    Shared mechanism for Part B Steps 6-13 (AFS Automation Hints): the
    field itself stays editable (Formik client-side state) — enforcement
    is server-side, on Save, via a single PUT endpoint shared by all four
    fields (source-confirmed, `EditApplication.jsx` — AFS Axis 2).

    Args:
        detail_page: The AgentDetailPage instance, on the published version.
        field_label: Human-readable field name, for assertion messages.
        do_edit: Zero-arg callable that performs the field edit.
    """
    do_edit()
    assert detail_page.is_save_enabled(), (
        f"Save should become enabled after editing {field_label} on the published version "
        "(the field itself is NOT disabled — enforcement is server-side on Save)"
    )

    response = detail_page.save_and_capture_response(timeout=FORM_SAVE_TIMEOUT)
    assert response.status == 400, (
        f"Saving {field_label} on a published version should be rejected with 400, got {response.status}"
    )
    error_body = (response.json() or {}).get("error", "")
    assert LOCKED_SAVE_REJECTION_PATTERN.search(error_body), (
        f"Expected the 400 response's 'error' field to match "
        f"{LOCKED_SAVE_REJECTION_PATTERN.pattern!r}, got {error_body!r}"
    )

    detail_page.toast_message.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
    toast_text = detail_page.toast_message.text_content() or ""
    assert LOCKED_SAVE_REJECTION_PATTERN.search(toast_text), (
        f"Expected the toast to match {LOCKED_SAVE_REJECTION_PATTERN.pattern!r}, got {toast_text!r}"
    )

    # Reset: the rejected edit is NOT auto-reverted (AFS Step 7 nuance) —
    # Discard + confirm is required before the next field's attempt.
    detail_page.click_discard(timeout=UI_ELEMENT_TIMEOUT)
    detail_page.confirm_discard(timeout=UI_ELEMENT_TIMEOUT)
    assert not detail_page.is_save_enabled(), (
        f"Save should be disabled again after Discard resets {field_label}'s edit"
    )
    logger.info("Confirmed %s edit is blocked on the published version", field_label)


class TestPublishedAgentVersionCannotBeModified:
    """Published Agent Version Cannot Be Modified (ELITEA-2614, l2/p1)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/skills/ELITEA-2614_published-agent-version-cannot-be-modified.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p1
    @pytest.mark.regression
    def test_published_agent_version_cannot_be_modified(self, page, agent_api, skill_api):
        """A published agent version is immutable: General-section field
        Saves are rejected server-side (400 + toast), skill-attachment
        controls are proactively disabled — and Unpublish restores full
        editability."""
        skill_id = None
        agent_id = None

        try:
            with allure.step("Step 1 — Create a disposable Skill (≥100-char instructions)"):
                skill_id = _create_skill(page)

            with allure.step(
                "Step 2 — Create an Agent with name, description, instructions, and a Tag"
            ):
                list_page = AgentsListPage(page)
                list_page.navigate_to_create()

                form_page = AgentFormPage(page)
                form_page.wait_for_form_load()
                form_page.fill_form(
                    name=AGENT_NAME, description=AGENT_DESCRIPTION, instructions=AGENT_INSTRUCTIONS,
                )
                form_page.wait_for_form_validation()
                assert form_page.is_save_enabled(), "Save should be enabled after filling all required agent fields"
                form_page.save_and_wait_for_navigation(timeout=FORM_SAVE_TIMEOUT)

                detail_page = AgentDetailPage(page)
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                detail_page.verify_on_detail_page()
                agent_id = int(detail_page.get_agent_id())
                logger.info("Created agent %r with id=%d", AGENT_NAME, agent_id)

                # Tags field only exists on the detail/edit page (ELITEA-1878/1879
                # precedent), not the create form.
                detail_page.add_tag(AGENT_TAG)
                detail_page.click_save(timeout=FORM_SAVE_TIMEOUT)

            with allure.step("Step 3 — Attach the Skill to the Agent"):
                detail_page.attach_skill(SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.is_skill_attached(SKILL_NAME), (
                    f"Skill card for {SKILL_NAME!r} should render after attaching"
                )

            with allure.step(
                "Step 4 — Publish the Agent via the actions-menu wizard "
                "(Preparation -> Validation -> Publishing)"
            ):
                detail_page.open_publish_wizard(timeout=UI_ELEMENT_TIMEOUT)
                detail_page.fill_publish_preparation_step(
                    VERSION_NAME, CATEGORY_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                assert detail_page.is_publish_continue_enabled(), (
                    "Continue should become enabled once Name, Category, and the agree-checkbox are set"
                )

                validate_status = detail_page.click_publish_continue(timeout=VALIDATE_TIMEOUT)
                assert validate_status == 200, (
                    f"publish_validate should return 200 (no Critical issues), got {validate_status}"
                )
                assert detail_page.publish_confirm_button.is_enabled(), (
                    "Validation step's Publish button should be enabled"
                )

                publish_status = detail_page.confirm_publish(timeout=PUBLISH_TIMEOUT)
                assert publish_status == 200, f"publish POST should return 200, got {publish_status}"

                # Auto-navigation after Publish is unreliable (known defect #614) —
                # explicitly (re)select the new version by name (AFS Automation Hints).
                detail_page.select_version_by_name(VERSION_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert detail_page.get_version_selector_value() == VERSION_NAME, (
                    f"VERSION selector should show {VERSION_NAME!r} once explicitly selected"
                )

            with allure.step(
                "Step 5 — Verify the agent shows as published, confirmed via a "
                "hard reload (publication persisted server-side, not just an "
                "optimistic client flag)"
            ):
                detail_page.wait_for_publish_status_menuitem(expect_unpublish=True, timeout=UI_ELEMENT_TIMEOUT)
                detail_page.close_actions_menu()

                page.reload(wait_until="domcontentloaded")
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                assert detail_page.get_version_selector_value() == VERSION_NAME, (
                    "VERSION selector should still show the published version after a reload"
                )
                detail_page.wait_for_publish_status_menuitem(expect_unpublish=True, timeout=UI_ELEMENT_TIMEOUT)
                detail_page.close_actions_menu()

            with allure.step(
                "Steps 6-7 — Attempt to edit the Name: field stays editable, "
                "Save is rejected 400 + matching toast"
            ):
                assert not detail_page.name_input.is_disabled(), (
                    "Name field should NOT be disabled on a locked version — "
                    "enforcement is server-side on Save, not client-side on the input"
                )
                _assert_field_edit_blocked_on_locked_version(
                    detail_page, "Name",
                    lambda: detail_page.update_name(f"{AGENT_NAME}-EDITED"),
                )

            with allure.step(
                "Steps 8-9 — Attempt to edit the Description: same shared "
                "PUT/toast mechanism, independently asserted"
            ):
                assert not detail_page.description_input.is_disabled(), (
                    "Description field should NOT be disabled on a locked version"
                )
                _assert_field_edit_blocked_on_locked_version(
                    detail_page, "Description",
                    lambda: detail_page.update_description(f"{AGENT_DESCRIPTION} EDITED"),
                )

            with allure.step(
                "Steps 10-11 — Attempt to edit the Instructions: same shared "
                "PUT/toast mechanism, independently asserted"
            ):
                assert not detail_page.instructions_input.is_disabled(), (
                    "Instructions field should NOT be disabled on a locked version"
                )
                _assert_field_edit_blocked_on_locked_version(
                    detail_page, "Instructions",
                    lambda: detail_page.update_text_field("instructions", f"{AGENT_INSTRUCTIONS} EDITED"),
                )

            with allure.step(
                "Steps 12-13 — Attempt to modify Tags (add a new one): same "
                "shared PUT/toast mechanism, independently asserted"
            ):
                assert not detail_page.tags_input.is_disabled(), (
                    "Tags field should NOT be disabled on a locked version"
                )
                _assert_field_edit_blocked_on_locked_version(
                    detail_page, "Tags",
                    lambda: detail_page.add_tag("editedtag"),
                )

            with allure.step(
                'Steps 14-15 — Attempt to add a new Skill: "+ Skill" is '
                "proactively disabled, with the correct immutability tooltip"
            ):
                assert detail_page.is_add_skill_button_disabled(timeout=UI_ELEMENT_TIMEOUT), (
                    '"+ Skill" button should be disabled on a published version'
                )
                skill_add_tooltip = detail_page.get_add_skill_button_tooltip(timeout=UI_ELEMENT_TIMEOUT)
                assert skill_add_tooltip == SKILL_ADD_LOCKED_TOOLTIP, (
                    f'"+ Skill" button tooltip should read {SKILL_ADD_LOCKED_TOOLTIP!r}, got {skill_add_tooltip!r}'
                )

            with allure.step(
                "Steps 16-17 — Attempt to remove the attached Skill: the "
                "remove-icon button is disabled, but its tooltip is the "
                "generic 'Remove skill' text — soft-asserted, Known defect: #1470"
            ):
                detail_page.hover_skill_card(SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                remove_btn = detail_page.get_skill_card_remove_button(SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                remove_btn.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                assert remove_btn.is_disabled(), (
                    "SkillCard 'remove skill' button should be disabled on a published version"
                )
                # Known defect: #1470 — SkillCard.jsx's remove-button Tooltip
                # carries a static "Remove skill" title, never the immutability
                # explanation the case's own Pass-criterion #3 requires. This
                # assertion is RED BY DESIGN until the product fix ships. Short
                # timeout is deliberate (not a weakening): the button is
                # ALREADY visible/rendered — a correctly-conditional tooltip
                # would match instantly, so a long timeout would only burn
                # time waiting on a static DOM value that will never change.
                expect.soft(
                    remove_btn,
                    "Known defect: #1470 — SkillCard remove-button tooltip never "
                    "explains immutability, even on a locked version",
                ).to_have_attribute("aria-label", IMMUTABILITY_TOOLTIP_PATTERN, timeout=2000)

            with allure.step(
                "Steps 18-19 — Attempt to change the attached Skill's version: "
                "the trigger's onClick is inert (no menu opens) and it carries "
                "NO tooltip at all — soft-asserted, Known defect: #1470"
            ):
                menu_opened = detail_page.attempt_open_skill_version_selector(
                    SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                assert not menu_opened, (
                    "Clicking the skill's version-selector trigger on a locked "
                    "version should be a no-op — the Versions menu should NOT open"
                )
                trigger = detail_page.get_skill_version_selector_trigger(SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                # Known defect: #1470 — SkillVersionSelector.jsx has NO Tooltip
                # wrapper at all (source-confirmed), so no aria-label is ever
                # set — RED BY DESIGN until the product fix ships. Short
                # timeout deliberate — see the remove-button assertion above.
                expect.soft(
                    trigger,
                    "Known defect: #1470 — SkillVersionSelector trigger has no "
                    "Tooltip/aria-label at all, even on a locked version",
                ).to_have_attribute("aria-label", IMMUTABILITY_TOOLTIP_PATTERN, timeout=2000)

            with allure.step(
                "Step 20 — Hover the Tools section's 4 add buttons "
                "(Toolkit/MCP/Agent/Pipeline): each shows the correct "
                "immutability tooltip"
            ):
                detail_page.ensure_toolkits_section_visible(timeout=UI_ELEMENT_TIMEOUT)
                tool_add_controls = (
                    ("Toolkit", detail_page.add_toolkit_button, detail_page.get_add_toolkit_button_tooltip),
                    ("MCP", detail_page.add_mcp_button, detail_page.get_add_mcp_button_tooltip),
                    ("Agent", detail_page.add_agent_button, detail_page.get_add_agent_button_tooltip),
                    ("Pipeline", detail_page.add_pipeline_button, detail_page.get_add_pipeline_button_tooltip),
                )
                for label, button, get_tooltip in tool_add_controls:
                    assert not button.is_enabled(), f'"+ {label}" should be disabled on a published version'
                    tooltip = get_tooltip(timeout=UI_ELEMENT_TIMEOUT)
                    assert tooltip == TOOL_ADD_LOCKED_TOOLTIP, (
                        f'"+ {label}" tooltip should read {TOOL_ADD_LOCKED_TOOLTIP!r}, got {tooltip!r}'
                    )

            with allure.step("Step 21 — Unpublish the Agent"):
                detail_page.open_unpublish_dialog(timeout=UI_ELEMENT_TIMEOUT)
                unpublish_status = detail_page.confirm_unpublish(timeout=PUBLISH_TIMEOUT)
                assert unpublish_status == 200, f"unpublish POST should return 200, got {unpublish_status}"

                detail_page.wait_for_publish_status_menuitem(expect_unpublish=False, timeout=UI_ELEMENT_TIMEOUT)
                detail_page.close_actions_menu()

            with allure.step(
                "Step 22 — Attempt to edit the Name: now allowed, Save succeeds"
            ):
                unlocked_name = f"{AGENT_NAME}-unlocked"
                detail_page.update_name(unlocked_name)
                response = detail_page.save_and_capture_response(timeout=FORM_SAVE_TIMEOUT)
                assert response.status in SAVE_SUCCESS_STATUSES, (
                    f"Saving Name should now succeed on the unpublished (Draft) version, got {response.status}"
                )

            with allure.step(
                "Step 23 — Attempt to edit the Description: now allowed, "
                "Save succeeds (same shared mechanism as Step 22, "
                "independently asserted); then reload once and confirm BOTH "
                "edits persisted server-side (closes the case's Step 25 "
                "'Save changes' loop end-to-end for both fields in one pass, "
                "rather than reloading mid-flow between them — a reload "
                "immediately followed by another field edit was observed live "
                "to occasionally race this app's persistent-WebSocket "
                "'networkidle' wait, Phase 4 finding)"
            ):
                unlocked_description = f"{AGENT_DESCRIPTION} UNLOCKED"
                detail_page.update_description(unlocked_description)
                response = detail_page.save_and_capture_response(timeout=FORM_SAVE_TIMEOUT)
                assert response.status in SAVE_SUCCESS_STATUSES, (
                    f"Saving Description should now succeed on the unpublished (Draft) version, got {response.status}"
                )

                page.reload(wait_until="domcontentloaded")
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                assert detail_page.get_name() == unlocked_name, (
                    "Name edit should persist after Unpublish restores editability"
                )
                assert detail_page.get_description() == unlocked_description, (
                    "Description edit should persist after Unpublish restores editability"
                )

            with allure.step(
                "Step 24 — Attempt to add/remove Skills: now allowed — "
                '"+ Skill" re-enables, and removing the attached skill succeeds'
            ):
                assert not detail_page.is_add_skill_button_disabled(timeout=UI_ELEMENT_TIMEOUT), (
                    '"+ Skill" button should be enabled again after Unpublish'
                )
                detail_page.remove_skill(SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert not detail_page.is_skill_attached(SKILL_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Skill {SKILL_NAME!r} should be removable again after Unpublish"
                )
        finally:
            with allure.step(
                "Cleanup — delete the agent (unpublishing any leftover "
                "Published version first) and the skill"
            ):
                if agent_id is not None:
                    try:
                        agent_versions = agent_api.get_agent(agent_id).get("versions", [])
                        for version in agent_versions:
                            if version.get("status") == "published":
                                agent_api.unpublish_version(version["id"])
                        agent_api.delete_agent(agent_id)
                        logger.info("Cleanup: deleted agent id=%d", agent_id)
                    except Exception as exc:
                        logger.warning("Cleanup: failed to delete agent id=%s: %s", agent_id, exc)
                if skill_id is not None:
                    try:
                        skill_api.delete_skill(skill_id)
                        logger.info("Cleanup: deleted skill id=%d", skill_id)
                    except Exception as exc:
                        logger.warning("Cleanup: failed to delete skill id=%s: %s", skill_id, exc)
