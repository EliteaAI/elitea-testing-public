"""Support Assistant — the widget sends the CURRENT page/entity as its context.

TMS case ELITEA-2425 · AFS
``test-specs/support-assistant/l2_assistant-receives-current-page-context_ELITEA-2425.md``

Asks the Support Assistant "what page am I on" from the Agents list and again
from the Pipelines list, then "what entity am I viewing" from an agent detail
page. Asserts the outbound ``support_assistant_context`` frame carries the live
route (and, on the detail page, the entity type/id/name), that the context
MOVES between the two list pages, and that each reply carries the value the
frame supplied.

Fidelity: no substitutions. ``page.on("websocket")`` is passive observation of
the frame the PRODUCT sends — nothing is routed, fulfilled, delayed or
rewritten (.agents/testing.md § Fidelity policy). Replies come from the live
LLM over the real backend; the captured frame (and the live URL / the name the
detail form shows) is the ORACLE the reply is asserted against, never a
hand-written string (.agents/testing.md § How to test a NONDETERMINISTIC
producer).

Two live-product facts this spec is shaped by (both recorded in the AFS):

1. ``current_entity_name`` is resolved from the RTK-Query cache
   (``findApplicationDetailsInCache``), so the detail query must have RESOLVED
   before the message is sent or the key is absent entirely — the test gates on
   the agent name field holding a value, not on a timer.
2. A full page load unmounts the widget, so each round re-opens it from the
   sidebar launcher; the conversation is restored, which is why every count is
   a delta and never an absolute.

Markers:
    - p2 / support_assistant / ui / regression (not smoke — three live LLM
      round trips, ~40-80 s each)

Usage::

    cd automation
    ../.venv/bin/pytest tests/ui/support_assistant/test_support_assistant_page_context.py -v
"""

from urllib.parse import urlparse

import allure
import pytest
from pages.agent_form_page import AgentFormPage
from pages.agents_list_page import AgentsListPage
from pages.pipelines_list_page import PipelinesListPage
from pages.support_assistant_page import SupportAssistantPage
from playwright.sync_api import expect

pytestmark = [
    pytest.mark.p2,
    pytest.mark.ui,
    pytest.mark.support_assistant,
    pytest.mark.regression,
]

WIDGET_TIMEOUT = 15_000
EXPECT_TIMEOUT = 10_000

# Observed reply latency on this surface: 31-135 s, sampled at 40.7 / 41.2 /
# 76.5 s for these questions (surface digest § Assistant context payload).
REPLY_TIMEOUT = 240_000

PAGE_QUESTION = "What page am I currently on in the application?"
ENTITY_QUESTION = "What entity am I currently viewing?"

AGENTS_PATH = "/agents/all"
PIPELINES_PATH = "/pipelines/all"


@allure.issue(
    "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/support-assistant/ELITEA-2425_assistant-receives-current-page-context.md",
    "onetest-ai Test Case link",
)
class TestSupportAssistantPageContext:
    """ELITEA-2425 — assistant receives the current page context."""

    def _ask(self, support_page, question: str) -> None:
        """Open the widget on a fresh chat, send *question*, await the reply."""
        support_page.open_widget_via_sidebar(timeout=WIDGET_TIMEOUT)
        expect(support_page.widget).to_be_visible(timeout=EXPECT_TIMEOUT)
        support_page.start_new_chat_via_testid(timeout=WIDGET_TIMEOUT)
        copy_baseline = support_page.get_copy_button_count()
        support_page.send_message_via_testid(question, timeout=EXPECT_TIMEOUT)
        expect(support_page.bubble_in(support_page.last_user_item())).to_have_text(
            question, timeout=EXPECT_TIMEOUT
        )
        # The copy button renders only on a COMPLETED assistant message — the
        # message item mounts instantly with a "Starting up..." placeholder, so
        # an item-count wait would return before the answer exists.
        expect(support_page.message_copy_buttons).to_have_count(
            copy_baseline + 1, timeout=REPLY_TIMEOUT
        )

    def test_assistant_receives_current_page_context(self, page):
        """The context frame follows the route, and the reply reflects it."""
        console_errors: list[str] = []
        page.on(
            "console",
            lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
        )
        support_page = SupportAssistantPage(page)
        agents_page = AgentsListPage(page)
        pipelines_page = PipelinesListPage(page)
        agent_form = AgentFormPage(page)

        # Armed before the first navigation: page.on("websocket") only fires
        # for sockets opened after the listener is attached.
        frames = support_page.capture_sent_socket_frames()

        with allure.step("Step 1 — Navigate to the Agents page"):
            agents_page.navigate()
            expect(agents_page.entity_card_name.first).to_be_visible(
                timeout=EXPECT_TIMEOUT
            )
            assert urlparse(page.url).path == AGENTS_PATH, (
                f"Expected to be on {AGENTS_PATH}, got {page.url}"
            )

        with allure.step("Step 2-3 — Open the widget and ask which page this is"):
            self._ask(support_page, PAGE_QUESTION)

        with allure.step("Step 4 — The context frame and the reply name the Agents page"):
            context_agents = support_page.last_assistant_context(frames)
            assert context_agents, "No support_predict frame was captured on /agents/all"
            assert context_agents.get("current_page") == urlparse(page.url).path, (
                f"Widget sent current_page={context_agents.get('current_page')!r}, "
                f"live route is {urlparse(page.url).path!r}"
            )
            assert context_agents.get("current_page") == AGENTS_PATH
            reply_agents = support_page.get_last_assistant_text()
            assert context_agents["current_page"] in reply_agents, (
                f"Reply does not name {context_agents['current_page']!r}: {reply_agents!r}"
            )

        with allure.step("Step 5 — Navigate to the Pipelines page and reopen the widget"):
            pipelines_page.navigate()
            assert urlparse(page.url).path == PIPELINES_PATH, (
                f"Expected to be on {PIPELINES_PATH}, got {page.url}"
            )

        with allure.step("Step 6 — The same question now reports the Pipelines page"):
            self._ask(support_page, PAGE_QUESTION)
            context_pipelines = support_page.last_assistant_context(frames)
            assert context_pipelines, (
                "No support_predict frame was captured on /pipelines/all"
            )
            assert context_pipelines.get("current_page") == urlparse(page.url).path
            assert context_pipelines.get("current_page") == PIPELINES_PATH, (
                f"Widget sent current_page={context_pipelines.get('current_page')!r}, "
                f"expected {PIPELINES_PATH!r}"
            )
            # The regression this case exists to catch is a frozen context.
            assert context_pipelines["current_page"] != context_agents["current_page"], (
                "Context did not move between the two pages"
            )
            reply_pipelines = support_page.get_last_assistant_text()
            assert context_pipelines["current_page"] in reply_pipelines, (
                f"Reply does not name {context_pipelines['current_page']!r}: "
                f"{reply_pipelines!r}"
            )

        with allure.step("Step 7a — Open an agent detail page"):
            agents_page.navigate()
            agent_id = agents_page.open_first_agent(timeout=WIDGET_TIMEOUT)
            # A populated name field is the observable proxy for "the
            # applicationDetails query resolved" — that cache entry is what
            # feeds current_entity_name into the context payload.
            expect(agent_form.name_input).not_to_have_value("", timeout=EXPECT_TIMEOUT)
            agent_name = agent_form.get_name()
            assert agent_name, "Agent detail page shows no name"

        with allure.step("Step 7b — Ask which entity is being viewed"):
            self._ask(support_page, ENTITY_QUESTION)
            context_entity = support_page.last_assistant_context(frames)
            assert context_entity, (
                "No support_predict frame was captured on the agent detail page"
            )
            assert context_entity.get("current_entity_type") == "agent", (
                f"Widget sent current_entity_type="
                f"{context_entity.get('current_entity_type')!r}"
            )
            assert context_entity.get("current_entity_id") == agent_id, (
                f"Widget sent current_entity_id="
                f"{context_entity.get('current_entity_id')!r}, URL says {agent_id}"
            )
            assert context_entity.get("current_entity_name") == agent_name, (
                f"Widget sent current_entity_name="
                f"{context_entity.get('current_entity_name')!r}, the detail form "
                f"shows {agent_name!r}"
            )
            assert context_entity.get("current_page") == f"{AGENTS_PATH}/{agent_id}", (
                f"Widget sent current_page={context_entity.get('current_page')!r}"
            )
            reply_entity = support_page.get_last_assistant_text()
            assert context_entity["current_entity_name"] in reply_entity, (
                f"Reply does not name the agent "
                f"{context_entity['current_entity_name']!r}: {reply_entity!r}"
            )

        with allure.step("Step 8 — No console errors were raised during the flow"):
            assert not console_errors, f"Console errors: {console_errors}"
