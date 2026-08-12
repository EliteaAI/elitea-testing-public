"""UI test — Nested Agent with MCP tool output (ELITEA-1951).

Verifies that a parent agent can invoke a nested sub-agent which has an MCP
configured, and that the parent agent's response includes the real output
of the MCP tool the sub-agent used — not a hallucinated summary.

- The **sub-agent** is precondition data only (no case step asserts its own
  creation) — reused from the AFS's own persistent fixture,
  ``autotest_nested_mcp_subagent`` (id 7827, left in place by the analyst's
  live run, `autotest_*`-prefixed per this project's established persistent-
  fixture convention), which already has the project's ``autotest_mcp_run_tool``
  Remote MCP attached and the exact instructions this test's chat message
  depends on. Rule 10 (read-only-by-default): the sub-agent's own creation
  isn't asserted by any case step, so reusing this stable existing fixture
  is preferred over seeding a fresh one — matching the AFS's own explicit
  precondition guidance ("the implementer may reuse them directly").
- The **parent agent** IS under test at Steps 1/2/3/5 (case asserts the
  create-via-UI-form flow and the "+ Agent" attach flow itself), so it is
  still built fresh, live, through the Agents "Create" form, exactly like
  ``test_agent_management.py::test_create_agent_via_ui``.

**Attach mechanism (Steps 2/3): ``AgentDetailPage.attach_agent_by_testid()``,
not the pre-existing ``attach_agent()``.** Implementation-time exploration
found ``attach_agent()`` (via ``Popper.select_menuitem``'s raw
``li[role="menuitem"]:has-text(...)`` CSS selection + a plain Playwright
``.click()``) intermittently fails specifically for a long/truncated agent
name: the item visibly highlights (hover state) and its overflow tooltip
renders, but the click never reaches the underlying ``<li>`` — no attach
request fires (or the backend rejects a stale reference) and the popper
never closes. A role-based click, a raw JS ``element.click()``, and a
testid-scoped Playwright ``.click()`` all landed reliably against the SAME
picker/agent in live testing — pointing at a MUI Tooltip-portal overlay
intercepting the mouse-simulated click's computed coordinates when the
truncation tooltip is showing, not an issue with the target agent itself
(reproduced identically against both a freshly-created and this run's
persistent sub-agent). New additive method ``attach_agent_by_testid()``
mirrors the already-established ``Popper.select_menuitem_by_testid()``
pattern (ELITEA-1735) instead — ``attach_agent()`` itself is untouched (other
merged callers depend on its current behavior).

Per the reverse-masking guard, this test asserts the live product's contract
rather than the case's stale text for steps 2 and 5: the case describes an
"Agent tab" that becomes "active" and an explicit ParentAgent Save step; the
live product instead opens a popper directly on the "+ Agent" button click
(same 4-independent-buttons, no-tabs pattern already filed and confirmed for
Toolkit/MCP in
https://github.com/EliteaAI/elitea-testing-public/issues/530 — confirmed by
this case's AFS to extend unchanged to the Agent tool type) and auto-saves
the attachment instantly (the agent-level Save button stays disabled
throughout — asserted directly rather than clicked).

Two testids were added this run (zero existed before on either component):
- ``agent-tool-version-selector-trigger/menu/option-{tool_id}[-{version_id}]``
  on ``AgentPipelineVersionSelector.jsx`` (Step 4's version selector).
- ``chat-answer-nested-agent-accordion-summary/details-{agent_name}`` on
  ``SubAgentAccordion.jsx`` (Steps 6/7's nested-invocation accordion — the
  AFS's own suggested text-match fallback would fail this project's
  testid-only mechanical review gate, so a dedicated testid was added
  instead of the text-match shape the AFS flagged as merely optional).

**Step 7's anti-hallucination proof is anchored on ``REAL_CONTENT_MARKER``
("DeepWiki-Open Overview", a real section name from the live wiki-structure
result), not a literal ``"MCP_TOOL_OUTPUT:"`` prefix match — case-text drift
(CLARIFICATION, not a defect).** The AFS documents the sub-agent's own
instructed prefix surviving the parent's "verbatim, unmodified" relay as the
proof signal. Confirmed live across multiple implementation runs: the real,
non-hallucinated DeepWiki-Open content reaches the parent's response every
time, but the literal ``"MCP_TOOL_OUTPUT:"`` marker does not always survive —
the LLM sometimes prepends a framing sentence or otherwise reformats despite
the "unmodified" instruction (ordinary LLM relay-formatting non-determinism,
not a platform defect — the same class of finding as the message-wording
determinism note in AFS § Test Data). Asserting the literal prefix's presence
would make the test flaky for a reason unrelated to what Step 7 actually
needs to prove (that real tool output, not a hallucination, reached the
response) — REAL_CONTENT_MARKER (plus the requested repo name) is asserted
instead, and the prefix's presence is logged as an informational note only
when absent, never a hard failure.

**Nested-accordion re-collapse race (Step 6/7).** The nested
``SubAgentAccordion``'s expand state is local React ``useState`` that
resets if the component remounts — observed live to happen while the
response is still progressively streaming/re-rendering AFTER
``wait_for_chat_response()`` (Step 6) already returned. Expanding the
accordion before the chain has FULLY settled can have it silently
re-collapse before Step 7 reads its contents. Fixed by waiting for
``REAL_CONTENT_MARKER`` in the final answer text (the true completion
signal — it can only appear once the entire nested chain has resolved)
BEFORE expanding the accordion, not just for ``wait_for_chat_response()``'s
weaker "the parent's own top-level turn is done" signal.

**Two ``chat-answer-tool-chip`` elements share the same nested-accordion
details container** — the parent's own "called this agent as a tool" chip
(bare agent name, DOM-first) and the sub-agent's OWN nested MCP tool-call
chip ("{toolkit}: {tool} ({agent})", DOM-second); not documented by the AFS.
``AgentDetailPage.get_nested_agent_tool_chip_locator()`` /
``get_nested_agent_tool_chip_texts()`` take an optional ``toolkit_name``
filter to target the second one specifically — omitting it (or using
``.first``) risks silently reading the wrong chip.

No product defect found.

Spec: test-specs/agents/l3_nested-agent-with-mcp-tool-output_ELITEA-1951.md
"""

import logging

import allure
import pytest
from pages.agent_detail_page import AgentDetailPage
from pages.agent_form_page import AgentFormPage
from pages.agents_list_page import AgentsListPage
from playwright.sync_api import expect

pytestmark = [pytest.mark.ui, pytest.mark.agents, pytest.mark.mcp]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000
# Nested tool-call chain observed up to ~40s ("Thought for 40 secs") in live
# exploration — a longer budget than a flat single-tool-call flow needs.
CHAT_RESPONSE_TIMEOUT = 90_000

logger = logging.getLogger("elitea.tests.agents")

# Persistent fixture (AFS Preconditions) — reused, never created/deleted by
# this test. Verified present via AgentAPI.list_agents() during
# implementation (id 7827, default_version_id 8057).
SUB_AGENT_ID = 7827
SUB_AGENT_NAME = "autotest_nested_mcp_subagent"
MCP_TOOLKIT_NAME = "autotest_mcp_run_tool"
PARENT_AGENT_NAME = "autotest_1951_nested_parent"
MCP_TOOL_NAME = "read_wiki_structure"
REPO_NAME = "AsyncFuncAI/deepwiki-open"
# Real, repo-specific structural marker only a genuine tool call could produce
# (confirmed live, non-hallucinated) — the primary anti-hallucination proof.
# See module docstring re: why this is used instead of a literal
# "MCP_TOOL_OUTPUT:" prefix match.
REAL_CONTENT_MARKER = "DeepWiki-Open Overview"

PARENT_AGENT_INSTRUCTIONS = (
    f"When the user asks you anything, always invoke the {SUB_AGENT_NAME} "
    "tool and return its full response verbatim, unmodified."
)
# Determinism-critical (AFS § Test Data): a vaguer message produced NO tool
# invocation at all in live exploration — this exact wording (names the
# sub-agent, its tool, AND the tool's required parameter) reliably produces
# the full invoke -> nested-tool-call -> relay chain in one pass.
CHAT_MESSAGE = (
    f"Ask {SUB_AGENT_NAME} to use its {MCP_TOOL_NAME} tool for "
    f'repoName="{REPO_NAME}" and return its full response to me verbatim.'
)


# Known defect #554 (already filed, unrelated) — an RTK-Query timing race in
# EliteaUI/src/api/toolkits.js's `toolkitTypes` endpoint fires before
# `useSelectedProjectId()` resolves, building the URL with an empty
# projectId segment (".../toolkits/prompt_lib/") which 404s. Intermittent
# (client-side race, not deterministic) and unrelated to the nested-agent/
# MCP-tool-output flow this filter is applied to — surfaced non-
# deterministically on the batch's own hardening-gate runs
# (elitea-testing-public#1277). SAME filter technique already established
# in test_credential_search_by_name.py / test_agent_publish_unpublish_version.py
# — matched on msg.location.url containing the toolkits endpoint path, NOT
# a blanket "any 404" filter, so an unrelated 404 from a genuinely
# different resource still surfaces as a real, unexpected failure.
def _is_known_554_toolkits_404(msg) -> bool:
    location_url = (msg.location or {}).get("url", "")
    return "404" in msg.text and "elitea_core/toolkits/prompt_lib/" in location_url


class TestNestedAgentWithMcpToolOutput:
    """Nested Agent with MCP tool output (ELITEA-1951, l3)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/"
        "automated-full-regression-ui/agents/"
        "ELITEA-1951_mcp-integration-in-agent-nested-agent-with-mcp.md",
        "onetest-ai Test Case link",
    )
    @pytest.mark.p2
    @pytest.mark.regression
    def test_nested_agent_with_mcp_tool_output(self, page, agent_api):
        """Parent agent invokes a nested sub-agent, relays its MCP tool output.

        Steps (AFS test-specs/agents/l3_nested-agent-with-mcp-tool-output_ELITEA-1951.md):
        1. Create the parent agent via the Agents "Create" form.
        2. Click "+ Agent" in the Tools section (opens a popper — live-accurate
           equivalent of the case's "Agent tab").
        3. Attach the sub-agent (which has the MCP configured) via the popper.
        4. Verify the sub-agent card shows a version selector with "base".
        5. Verify the attach auto-saved (agent-level Save stays disabled).
        6. Send the deterministic message via the embedded chat; verify the
           parent invokes the sub-agent (nested accordion appears/expands).
        7. Verify the parent's response includes the real MCP tool output
           relayed from the nested sub-agent.

        Args:
            page: Playwright page fixture.
            agent_api: Session-scoped AgentAPI client (parent-agent cleanup only —
                the sub-agent is a persistent fixture, never deleted here).
        """
        parent_agent_id = None

        console_errors = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg)
            if msg.type == "error" and not _is_known_554_toolkits_404(msg)
            else None,
        )

        try:
            with allure.step(
                "Precondition — verify the persistent sub-agent fixture is present "
                "with the MCP toolkit attached"
            ):
                sub_detail_page = AgentDetailPage(page)
                sub_detail_page.navigate(SUB_AGENT_ID)
                sub_detail_page.verify_on_detail_page(expected_agent_id=SUB_AGENT_ID)
                assert sub_detail_page.get_name() == SUB_AGENT_NAME, (
                    f"Sub-agent fixture {SUB_AGENT_ID} should be named {SUB_AGENT_NAME!r}"
                )
                assert sub_detail_page.is_toolkit_attached(
                    MCP_TOOLKIT_NAME, timeout=UI_ELEMENT_TIMEOUT
                ), (
                    f"MCP '{MCP_TOOLKIT_NAME}' should already be attached to the "
                    f"persistent sub-agent fixture {SUB_AGENT_NAME!r}"
                )

            with allure.step("Step 1 — Create the parent agent via the Agents 'Create' form"):
                list_page = AgentsListPage(page)
                list_page.navigate_to_create()

                form_page = AgentFormPage(page)
                form_page.wait_for_form_load()
                create_requests = form_page.capture_requests_matching(
                    "applications/prompt_lib", method="POST"
                )
                form_page.fill_form(
                    name=PARENT_AGENT_NAME,
                    description="Auto-created parent agent for ELITEA-1951",
                    instructions=PARENT_AGENT_INSTRUCTIONS,
                )
                form_page.wait_for_form_validation()
                assert form_page.is_save_enabled(), (
                    "Save button should be enabled after filling required fields"
                )
                form_page.save_and_wait_for_navigation(timeout=NAVIGATION_TIMEOUT)

                detail_page = AgentDetailPage(page)
                detail_page.wait_for_page_load(timeout=NAVIGATION_TIMEOUT)
                detail_page.verify_on_detail_page()
                parent_agent_id = int(detail_page.get_agent_id())

                create_calls = [r for r in create_requests if r["status"] == 201]
                assert create_calls, (
                    "POST .../elitea_core/applications/prompt_lib/... should return 201 on "
                    f"parent-agent creation, captured: {create_requests!r}"
                )

            with allure.step(
                "Step 2/3 — Attach the sub-agent via the '+ Agent' picker (live-accurate "
                "equivalent of the case's 'Agent tab' — see module docstring)"
            ):
                assert not detail_page.is_toolkit_attached(SUB_AGENT_NAME, timeout=1000), (
                    f"Sub-agent '{SUB_AGENT_NAME}' should not be attached before the attach action"
                )
                # page.expect_response() (not capture_requests_matching()) — ties the
                # response wait to this exact action window, avoiding an event-listener
                # race observed during implementation where capture_requests_matching()
                # recorded the PATCH *request* but its matching *response* handler never
                # fired (status stayed None) despite the UI's own success toast/card
                # confirming the attach genuinely succeeded server-side. Same
                # `with page.expect_response(...)` idiom test_agent_self_attachment_blocked.py
                # already uses successfully.
                with page.expect_response(
                    lambda resp: "application_relation/prompt_lib" in resp.url
                    and resp.request.method == "PATCH",
                    timeout=UI_ELEMENT_TIMEOUT,
                ) as response_info:
                    detail_page.attach_agent_by_testid(SUB_AGENT_NAME)
                attach_response = response_info.value
                assert attach_response.status == 201, (
                    "PATCH .../application_relation/prompt_lib/... should return 201 on "
                    f"sub-agent attach, got {attach_response.status} ({attach_response.url})"
                )

            with allure.step(
                "Step 4 — Sub-agent appears in the Tools list with a version selector showing 'base'"
            ):
                assert detail_page.is_toolkit_attached(SUB_AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT), (
                    f"Sub-agent card for '{SUB_AGENT_NAME}' should render after attaching"
                )
                detail_page.open_tool_version_selector(timeout=UI_ELEMENT_TIMEOUT)
                trigger_text = detail_page.get_tool_version_selector_trigger_text()
                assert trigger_text == "base", (
                    f"Version selector trigger should read 'base', got {trigger_text!r}"
                )
                option_texts = detail_page.get_tool_version_option_texts(timeout=UI_ELEMENT_TIMEOUT)
                assert option_texts == ["base"], (
                    f"Version menu should list exactly one 'base' option, got {option_texts!r}"
                )
                page.keyboard.press("Escape")

            with allure.step(
                "Step 5 — Agent-level Save stays disabled (attach already auto-saved at Step 3, "
                "live-accurate equivalent of the case's explicit Save step — see module docstring)"
            ):
                assert not detail_page.save_button.is_enabled(), (
                    "Agent-level Save button should remain disabled — the sub-agent attach auto-persists"
                )

            with allure.step(
                "Step 6 — Send the deterministic message via the embedded chat; parent invokes the sub-agent"
            ):
                initial_count = detail_page.get_chat_message_count()
                detail_page.send_chat_message(CHAT_MESSAGE)
                detail_page.wait_for_chat_response(
                    initial_count=initial_count, timeout=CHAT_RESPONSE_TIMEOUT
                )

                accordion = detail_page.get_outer_thought_accordion(timeout=UI_ELEMENT_TIMEOUT)
                expect(accordion).to_be_visible()

                # wait_for_chat_response() above only guarantees the PARENT's own top-level
                # response is complete, not that the SUB-agent's nested MCP call has resolved —
                # the response keeps streaming/re-rendering afterward (confirmed live: content
                # arrives progressively for several more seconds). Critically, each of those
                # re-renders can RESET the nested SubAgentAccordion's local `expanded` React
                # state if the component remounts — expanding it too early got observed
                # silently re-collapsing before Step 7 could read its contents. So: wait for the
                # TRUE completion signal first — the final answer text containing the real,
                # repo-specific content only the resolved tool call could produce (see module
                # docstring re: REAL_CONTENT_MARKER vs. the less reliable literal
                # "MCP_TOOL_OUTPUT:" prefix) — THEN expand the now-stable accordion.
                expect(detail_page.skill_test_last_response).to_contain_text(
                    REAL_CONTENT_MARKER, timeout=CHAT_RESPONSE_TIMEOUT
                )

                summary = detail_page.expand_nested_agent_accordion(
                    SUB_AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                expect(summary).to_have_attribute("aria-expanded", "true")

            with allure.step(
                "Step 7 — Parent's response includes the nested MCP tool output"
            ):
                # Two DISTINCT `chat-answer-tool-chip` elements live inside the same nested
                # accordion details container (confirmed live, not documented by the AFS): the
                # PARENT's own "called this agent as a tool" chip (text = bare agent name,
                # DOM-first) and the sub-agent's OWN nested MCP tool-call chip (text =
                # "{toolkit}: {tool} ({agent})", DOM-second) — filter by toolkit_name to target
                # the second one specifically; see get_nested_agent_tool_chip_locator()'s
                # docstring.
                expected_tool_chip_text = f"{MCP_TOOLKIT_NAME}: {MCP_TOOL_NAME} ({SUB_AGENT_NAME})"
                tool_chip_locator = detail_page.get_nested_agent_tool_chip_locator(
                    SUB_AGENT_NAME, toolkit_name=MCP_TOOLKIT_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                expect(tool_chip_locator.first).to_contain_text(
                    expected_tool_chip_text, timeout=UI_ELEMENT_TIMEOUT
                )
                tool_chip_texts = detail_page.get_nested_agent_tool_chip_texts(
                    SUB_AGENT_NAME, toolkit_name=MCP_TOOLKIT_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                assert any(expected_tool_chip_text in t for t in tool_chip_texts), (
                    f"Nested accordion should show the sub-agent's own MCP tool-call chip "
                    f"{expected_tool_chip_text!r}, got: {tool_chip_texts!r}"
                )

                model_chip_texts = detail_page.get_nested_agent_model_chip_texts(
                    SUB_AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT
                )
                assert model_chip_texts, (
                    "Nested accordion should show at least one model chip for the "
                    "sub-agent's own completion"
                )

                # Already guaranteed by Step 6's wait — re-asserted here as this step's own
                # explicit checkpoint (resolves immediately; no new wait budget spent).
                expect(detail_page.skill_test_last_response).to_contain_text(
                    REAL_CONTENT_MARKER, timeout=UI_ELEMENT_TIMEOUT
                )
                final_answer_text = detail_page.get_last_chat_response_text()
                assert REAL_CONTENT_MARKER in final_answer_text, (
                    "Parent's final answer should contain the real, non-hallucinated "
                    f"DeepWiki-Open structure ({REAL_CONTENT_MARKER!r}), got: {final_answer_text!r}"
                )
                assert REPO_NAME in final_answer_text, (
                    "Parent's final answer should reference the requested repo "
                    f"{REPO_NAME!r}, got: {final_answer_text!r}"
                )
                # "MCP_TOOL_OUTPUT:" (the sub-agent's own instructed prefix) is a SOFT signal
                # only — case-text drift (CLARIFICATION, not a defect): confirmed live across
                # multiple runs that the parent's "verbatim, unmodified" relay doesn't always
                # preserve this exact literal marker (LLM relay-formatting non-determinism,
                # e.g. adding a framing sentence or dropping the marker), while the REAL
                # DeepWiki-Open content — the actual thing being proven — is present every
                # time. See module docstring.
                if "MCP_TOOL_OUTPUT:" not in final_answer_text:
                    logger.info(
                        "Sub-agent's 'MCP_TOOL_OUTPUT:' prefix did not survive the parent's "
                        "relay this run (known LLM relay-formatting non-determinism) — real "
                        "content is present and asserted above regardless."
                    )

            assert not console_errors, (
                f"Expected no console errors, got: {[m.text for m in console_errors]}"
            )

        finally:
            # Only the fresh parent is cleaned up — the sub-agent (SUB_AGENT_ID) is a
            # persistent project fixture, intentionally never deleted here (AFS § Cleanup).
            if parent_agent_id is not None:
                try:
                    agent_api.delete_agent(parent_agent_id)
                    logger.info("Cleanup: deleted parent agent %s", parent_agent_id)
                except Exception as exc:
                    logger.warning(
                        "Cleanup: failed to delete parent agent %s: %s", parent_agent_id, exc
                    )
