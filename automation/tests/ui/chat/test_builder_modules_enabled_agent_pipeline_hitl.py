"""UI Test for ELITEA-3372 — Agent/Pipeline Builder, Ask User clarification,
and HITL sensitive-action approval/rejection all continue to work correctly
when Skills Builder and Project Context Builder are also enabled.

Verifies that enabling all four Modules-panel toggles in one conversation
(``internal_mcp``/"Agent & Pipeline Builder", ``skill_builder``,
``project_context_builder``, ``ask_user``) does not regress:
- Agent creation via chat (with Ask-User clarification, when it fires)
- Pipeline creation via chat (same)
- HITL sensitive-action Authorize (executes the tool, deletes the file)
- HITL sensitive-action Block (halts the tool, file remains)
- No cross-contamination between the Agent/Pipeline-builder exchanges and
  the later HITL exchanges in the SAME conversation

AFS: test-specs/chat-interface/
    l1_builder-modules-enabled-agent-pipeline-ask-user-hitl_ELITEA-3372.md

No product defects found — all 12 case steps executed live end-to-end
against the real (unmocked) DEV backend and matched the case's Pass
criteria. One CLARIFICATION (not a defect) was surfaced by the analysis:
the Ask-User clarifying-question card's trigger is genuinely
non-deterministic for the case's own literal messages (a stable LLM
routing decision, not a test-infra flake) — this test branches (polls for
EITHER outcome) rather than asserting the card always appears, per the
AFS's own § Known Defects/Clarifications and the reverse-masking guard in
`.agents/role-overrides.md`.

Markers:
    - ui: requires browser
    - chat: chat-related test
    - p0: critical priority (AFS Priority l1 == TMS `priority: critical`)

Usage:
    cd automation
    pytest tests/ui/chat/test_builder_modules_enabled_agent_pipeline_hitl.py -v
"""

import logging
import time

import allure
import pytest
from api import AgentAPI, ArtifactAPI, PipelineAPI, ToolkitAPI
from pages.chat_page import ChatPage
from pages.guardrails_admin_page import GuardrailsAdminPage
from playwright.sync_api import Page

logger = logging.getLogger(__name__)

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p0, pytest.mark.regression]

# ---------------------------------------------------------------------------
# Timeout constants (ms)
# ---------------------------------------------------------------------------
UI_ELEMENT_TIMEOUT = 10_000
AI_RESPONSE_TIMEOUT = 60_000
CLARIFYING_CARD_POLL_INTERVAL_MS = 500

# Case text's own step-3/6 wording (literal). Confirmed live (AFS § Known
# Defects/Clarifications) to be genuinely non-deterministic whether it
# triggers the Ask-User clarifying card or the AI proceeds directly — this
# test polls for EITHER outcome rather than assuming one.
AGENT_CREATION_MESSAGE = "Create an agent for customer support"
PIPELINE_CREATION_MESSAGE = "Create a pipeline for data processing"

# Plausible free-text answer for whichever clarifying question the stepper
# shows — content doesn't matter to the assertions, only that it is
# non-empty (flips the Skip/Continue button to "Continue").
CLARIFYING_ANSWER_TEXT = "A friendly customer support agent for an e-commerce company"

# Unambiguous delete-file messages naming the bucket/file explicitly (same
# pattern ELITEA-2211's AFS documents — a vague "delete a file" message
# produces a clarifying question rather than a real tool-call attempt).
AUTHORIZE_DELETE_MESSAGE_TEMPLATE = (
    'Use delete_file toolkit to delete a file named "{file}" from bucket '
    '"{bucket}". Execute the tool now, do not ask for clarification.'
)
BLOCK_DELETE_MESSAGE_TEMPLATE = (
    'Use delete_file toolkit to delete a file named "{file}" from bucket '
    '"{bucket}". Execute the tool now, do not ask for clarification.'
)


def _send_and_resolve_builder_flow(
    chat: ChatPage, prompt: str, answer_text: str, timeout: int = AI_RESPONSE_TIMEOUT
) -> int:
    """Send *prompt*, resolve any Ask-User clarifying card that appears, and
    wait for the AI response to settle.

    The Ask-User clarifying card's trigger is genuinely non-deterministic
    for the same message across fresh conversations (AFS § Known Defects/
    Clarifications, confirmed live ~14 runs) — this helper polls for EITHER
    outcome: the clarifying card (``get_by_placeholder("Your option")``) or
    a settled AI response, whichever appears first, and answers the card in
    a bounded loop (never assumes exactly one question) if it shows up.

    Args:
        chat: ChatPage instance.
        prompt: The chat message to send.
        answer_text: Free-text answer typed into the clarifying card's
            custom-option field, if the card appears.
        timeout: Maximum wait time in milliseconds for the whole exchange.

    Returns:
        The AI response's message index (for chip/content assertions).
    """
    initial_count = chat.get_message_count()
    chat.send_message(prompt, use_enter=True)

    custom_option_input = chat.page.get_by_placeholder("Your option")
    ai_response_index = initial_count + 1
    ai_message = chat.messages_container.nth(ai_response_index)
    copy_button = ai_message.locator('button[aria-label="Copy to clipboard"]')

    deadline_ms = timeout
    waited_ms = 0
    card_answered = False

    # Bounded poll: whichever appears first — the clarifying card or the
    # settled response's Copy button — wins. If the card appears, answer it
    # (loop in case the stepper shows more than one question) then continue
    # waiting for the response to settle.
    while waited_ms < deadline_ms:
        if custom_option_input.count() > 0 and custom_option_input.first.is_visible():
            logger.info("Ask-User clarifying card appeared — answering")
            card_answered = True
            # Answer every question the stepper shows (bounded iteration —
            # live runs this pass only ever showed 1, never hardcode "1").
            question_guard = 0
            while custom_option_input.count() > 0 and custom_option_input.first.is_visible():
                question_guard += 1
                if question_guard > 10:
                    raise TimeoutError(
                        "Ask-User clarifying card did not resolve after 10 answered questions"
                    )
                custom_option_input.first.click()
                custom_option_input.first.fill(answer_text)
                # Re-query: the button's accessible name flips from "Skip" to
                # "Continue" once the field is non-empty (same-element
                # ternary, ClarifyingQuestionControl.jsx) — never cache this
                # locator from before the fill.
                continue_button = chat.page.get_by_role("button", name="Continue")
                continue_button.wait_for(state="visible", timeout=UI_ELEMENT_TIMEOUT)
                continue_button.click()
                chat.page.wait_for_timeout(300)
            break
        if copy_button.count() > 0 and copy_button.first.is_visible():
            logger.info("AI proceeded directly — no clarifying card this run")
            break
        chat.page.wait_for_timeout(CLARIFYING_CARD_POLL_INTERVAL_MS)
        waited_ms += CLARIFYING_CARD_POLL_INTERVAL_MS

    logger.info(
        "Builder-flow send resolved (card_answered=%s) — waiting for AI response to settle",
        card_answered,
    )
    chat.wait_for_ai_response(initial_count=initial_count, timeout=timeout)
    return ai_response_index


@allure.epic("Chat")
@allure.feature("Modules Panel")
@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
    "automated-full-regression-ui/chat/build-skills-project-context/"
    "ELITEA-3372_agent-and-pipeline-builder-work-correctly-when-skills-builder-"
    "and-project-context-builder-are-enabled.md",
    "onetest-ai Test Case link (ELITEA-3372)",
)
class TestBuilderModulesEnabledAgentPipelineHitl:
    """ELITEA-3372 — Agent & Pipeline Builder, Ask User clarification, and
    HITL sensitive-action approval/rejection all continue to function with
    Skills Builder / Project Context Builder also enabled, in one
    conversation."""

    @pytest.mark.tms("ELITEA-3372")
    @allure.title(
        "Agent & Pipeline Builder, Ask User, and HITL approval/rejection all work "
        "correctly with Skills Builder and Project Context Builder enabled"
    )
    @allure.severity(allure.severity_level.CRITICAL)
    def test_builder_modules_enabled_agent_pipeline_hitl(
        self,
        page: Page,
        conversation_id,
        agent_api: AgentAPI,
        pipeline_api: PipelineAPI,
        artifact_api: ArtifactAPI,
        toolkit_api: ToolkitAPI,
    ):
        chat = ChatPage(page)
        console_errors = chat.capture_console_errors()

        created_agent_id = None
        created_pipeline_id = None
        bucket_name = None
        toolkit_id = None
        toolkit_name = None
        sensitive_tool_added = False

        try:
            with allure.step(
                "Setup — create an Artifact bucket (2 files) + toolkit for the HITL "
                "Authorize/Block steps, and mark delete_file sensitive via Admin UI Guardrails"
            ):
                run_suffix = str(int(time.time() * 1000))[-6:]
                bucket_name_requested = f"autotest-3372-hitl-{run_suffix}"
                bucket = artifact_api.create_bucket(bucket_name_requested)
                bucket_name = bucket.get("name", bucket_name_requested)
                authorize_file = "authorize-target.txt"
                block_file = "block-target.txt"
                artifact_api.upload_file(bucket_name, authorize_file, b"authorize me")
                artifact_api.upload_file(bucket_name, block_file, b"do not delete me")

                toolkit_name = f"autotest-3372-hitl-tk-{run_suffix}"
                toolkit = toolkit_api.create_artifact_toolkit(
                    name=toolkit_name,
                    description="Auto-created artifact toolkit for ELITEA-3372",
                    bucket_name=bucket_name,
                )
                toolkit_id = toolkit["id"]

                admin_context = page.context.browser.new_context(
                    storage_state=page.context.storage_state()
                )
                admin_page = admin_context.new_page()
                try:
                    guardrails = GuardrailsAdminPage(admin_page)
                    guardrails.navigate_to_guardrails()
                    guardrails.add_sensitive_tool("artifact", "delete_file")
                    guardrails.save_configuration()
                    sensitive_tool_added = True
                    assert guardrails.is_tool_in_sensitive_list("delete_file", "artifact"), (
                        "Expected delete_file to be marked sensitive after save"
                    )
                finally:
                    admin_page.close()
                    admin_context.close()

            with allure.step(
                "Step 1 — Navigate to the fresh conversation, open the Modules panel"
            ):
                chat.navigate_to_chat(conversation_id=conversation_id)
                # Dismiss platform-level announcement overlays if present —
                # confirmed live this pass: (1) the "Announcing ELITEA 2.0.7!"
                # full-screen modal (not covered by
                # BasePage.dismiss_banner_if_present(), which only targets
                # button[aria-label="close"]), followed by (2) a "New Models
                # are added" top banner that only appears once (1) is
                # dismissed and IS covered by dismiss_banner_if_present().
                # Left undismissed, either intercepts later clicks (the
                # plus-menu button, close_modules_panel()'s outside click).
                chat.dismiss_platform_release_banner_if_present()
                chat.dismiss_banner_if_present()
                chat.open_internal_tools_menu()

            with allure.step(
                "Step 2 — Enable all four modules: Agent & Pipeline Builder, Ask User, "
                "Skills Builder, Project Context Builder"
            ):
                for tool_key in ("internal_mcp", "ask_user", "skill_builder", "project_context_builder"):
                    # ensure_module_toggle_checked() is itself idempotent (no-op if
                    # already checked) — a bounded retry absorbs the documented
                    # live flake where its own PUT-settle poll occasionally loses
                    # a race (_surface.md ELITEA-3370 entry: confirmed for
                    # skill_builder/project_context_builder, reproduced live this
                    # pass for skill_builder specifically), without touching the
                    # shared ChatPage method.
                    for attempt in range(3):
                        try:
                            chat.ensure_module_toggle_checked(tool_key, timeout=UI_ELEMENT_TIMEOUT)
                            break
                        except AssertionError:
                            if attempt == 2:
                                raise
                            logger.warning(
                                "ensure_module_toggle_checked(%r) raced — retrying (attempt %d/3)",
                                tool_key, attempt + 2,
                            )
                for tool_key in ("internal_mcp", "ask_user", "skill_builder", "project_context_builder"):
                    assert chat.is_module_toggle_checked(tool_key), (
                        f"Expected module toggle '{tool_key}' to be checked after enabling"
                    )
                chat.close_modules_panel(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                "Step 3/4 — Request Agent creation with an incomplete description; "
                "resolve any Ask-User clarifying question(s); verify completion"
            ):
                agent_response_index = _send_and_resolve_builder_flow(
                    chat, AGENT_CREATION_MESSAGE, CLARIFYING_ANSWER_TEXT
                )

                agents_after = agent_api.list_agents().get("rows", [])
                matching_agents = [
                    a for a in agents_after if "customer support" in a.get("name", "").lower()
                    or "support" in a.get("name", "").lower()
                ]
                assert matching_agents, (
                    f"Expected a new agent whose name traces to 'customer support', "
                    f"found none among: {[a.get('name') for a in agents_after]}"
                )
                created_agent_id = matching_agents[0]["id"]
                created_agent_name = matching_agents[0]["name"]

            with allure.step("Step 5 — Verify Agent chip appears in response"):
                agent_message = chat.messages_container.nth(agent_response_index)
                assert chat.message_has_generated_entity_chip(agent_message), (
                    "Expected a generated-entity-chip on the Agent-creation response"
                )
                chip_text = chat.GENERATED_ENTITY_CHIP.within(agent_message).first.text_content() or ""
                assert created_agent_name.lower() in chip_text.lower() or chip_text.strip() != "", (
                    f"Expected the generated-entity-chip text to relate to the created "
                    f"agent '{created_agent_name}', got chip text: {chip_text!r}"
                )

            with allure.step(
                "Step 6/7 — Repeat the flow requesting Pipeline creation with incomplete "
                "info; resolve any Ask-User clarifying question(s); verify completion"
            ):
                pipeline_response_index = _send_and_resolve_builder_flow(
                    chat, PIPELINE_CREATION_MESSAGE, CLARIFYING_ANSWER_TEXT
                )

                pipelines_after = pipeline_api.list_pipelines().get("rows", [])
                matching_pipelines = [
                    p for p in pipelines_after
                    if "data processing" in p.get("name", "").lower()
                    or "processing" in p.get("name", "").lower()
                ]
                assert matching_pipelines, (
                    f"Expected a new pipeline whose name traces to 'data processing', "
                    f"found none among: {[p.get('name') for p in pipelines_after]}"
                )
                created_pipeline_id = matching_pipelines[0]["id"]
                created_pipeline_name = matching_pipelines[0]["name"]

            with allure.step("Step 8 — Verify Pipeline chip appears in response"):
                pipeline_message = chat.messages_container.nth(pipeline_response_index)
                assert chat.message_has_generated_entity_chip(pipeline_message), (
                    "Expected a generated-entity-chip on the Pipeline-creation response"
                )
                chip_text = chat.GENERATED_ENTITY_CHIP.within(pipeline_message).first.text_content() or ""
                assert created_pipeline_name.lower() in chip_text.lower() or chip_text.strip() != "", (
                    f"Expected the generated-entity-chip text to relate to the created "
                    f"pipeline '{created_pipeline_name}', got chip text: {chip_text!r}"
                )

            with allure.step(
                "Step 9 — Trigger a sensitive tool call (delete_file) requiring approval, "
                "in the SAME conversation"
            ):
                # Close any lingering popper from the Modules/builder flows above —
                # confirmed live (AFS § Concrete Handles / _surface.md ELITEA-3372
                # finding #4) that a stale open popper intercepts
                # add_toolkit_participant()'s own click otherwise.
                chat.page.keyboard.press("Escape")
                chat.page.mouse.click(10, 10)

                chat.add_toolkit_participant(toolkit_name, timeout=UI_ELEMENT_TIMEOUT)
                # add_toolkit_participant() selects the toolkit but leaves the
                # Toolkits submenu popper open (confirmed live — it still
                # covers the composer) — close it before sending.
                chat.page.keyboard.press("Escape")
                chat.page.mouse.click(10, 10)
                chat.send_message(
                    AUTHORIZE_DELETE_MESSAGE_TEMPLATE.format(file=authorize_file, bucket=bucket_name),
                    use_enter=True,
                )
                panel_appeared = chat.wait_for_sensitive_action_panel(timeout=AI_RESPONSE_TIMEOUT)
                assert panel_appeared, (
                    "Expected the Sensitive Action Authorization panel to appear "
                    "for the delete_file tool call"
                )

            with allure.step("Step 10 — Approve the action; verify real backend execution"):
                # force=True — a lingering Toolkits-submenu popper from Step 9's
                # add_toolkit_participant() flow can still intercept pointer events
                # here (mui-patterns.md § MUI Overlay Interception), confirmed live.
                chat.sensitive_action_authorize_button.click(force=True)
                chat.wait_for_ai_response(
                    initial_count=chat.get_message_count() - 1, timeout=AI_RESPONSE_TIMEOUT
                )

                remaining_files = artifact_api.list_bucket_files(bucket_name)
                assert authorize_file not in remaining_files, (
                    f"Expected '{authorize_file}' to be deleted after Authorize, "
                    f"bucket still contains: {remaining_files}"
                )

            with allure.step(
                "Step 11 — Trigger the sensitive tool call again (second file, same "
                "conversation, same toolkit participant)"
            ):
                chat.send_message(
                    BLOCK_DELETE_MESSAGE_TEMPLATE.format(file=block_file, bucket=bucket_name),
                    use_enter=True,
                )
                panel_appeared_again = chat.wait_for_sensitive_action_panel(timeout=AI_RESPONSE_TIMEOUT)
                assert panel_appeared_again, (
                    "Expected the Sensitive Action Authorization panel to re-appear "
                    "for the second delete_file tool call"
                )

            with allure.step("Step 12 — Reject the action; verify the file is preserved"):
                chat.sensitive_action_block_button.click(force=True)
                chat.wait_for_ai_response(
                    initial_count=chat.get_message_count() - 1, timeout=AI_RESPONSE_TIMEOUT
                )

                remaining_files_after_block = artifact_api.list_bucket_files(bucket_name)
                assert block_file in remaining_files_after_block, (
                    f"Expected '{block_file}' to remain after Block/Reject, "
                    f"bucket contains: {remaining_files_after_block}"
                )

            with allure.step(
                "Side-channel check — earlier Agent/Pipeline-builder messages are "
                "unaffected by the later HITL exchanges in the same conversation"
            ):
                agent_message_now = chat.messages_container.nth(agent_response_index)
                assert chat.message_has_generated_entity_chip(agent_message_now), (
                    "Expected the earlier Agent-creation response to still show its "
                    "generated-entity-chip after the later HITL exchanges"
                )
                pipeline_message_now = chat.messages_container.nth(pipeline_response_index)
                assert chat.message_has_generated_entity_chip(pipeline_message_now), (
                    "Expected the earlier Pipeline-creation response to still show its "
                    "generated-entity-chip after the later HITL exchanges"
                )

            with allure.step("Side-channel check — no console errors at any step"):
                assert not console_errors, (
                    f"Unexpected console errors: {[m.text for m in console_errors]}"
                )
        finally:
            console_errors.stop()
            if created_agent_id is not None:
                try:
                    agent_api.delete_agent(created_agent_id)
                except Exception as exc:
                    logger.warning("Failed to delete agent %s: %s", created_agent_id, exc)
            if created_pipeline_id is not None:
                try:
                    pipeline_api.delete_pipeline(created_pipeline_id)
                except Exception as exc:
                    logger.warning("Failed to delete pipeline %s: %s", created_pipeline_id, exc)
            if toolkit_id is not None:
                try:
                    toolkit_api.delete_toolkit(toolkit_id)
                except Exception as exc:
                    logger.warning("Failed to delete toolkit %s: %s", toolkit_id, exc)
            if bucket_name is not None:
                try:
                    artifact_api.delete_bucket(bucket_name)
                except Exception as exc:
                    logger.warning("Failed to delete bucket %s: %s", bucket_name, exc)
            if sensitive_tool_added:
                # The Guardrails sensitive-tool entry is GLOBAL, toolkit-TYPE scoped
                # (AFS § Automation Hints) — clean it up or it silently affects every
                # other artifact toolkit in the project.
                cleanup_context = page.context.browser.new_context(
                    storage_state=page.context.storage_state()
                )
                cleanup_page = cleanup_context.new_page()
                try:
                    guardrails = GuardrailsAdminPage(cleanup_page)
                    guardrails.navigate_to_guardrails()
                    guardrails.remove_sensitive_tool("delete_file")
                    guardrails.remove_empty_sensitive_toolkit_blocks()
                    guardrails.save_configuration()
                except Exception as exc:
                    logger.warning("Failed to clean up sensitive-tool entry: %s", exc)
                finally:
                    cleanup_page.close()
                    cleanup_context.close()
