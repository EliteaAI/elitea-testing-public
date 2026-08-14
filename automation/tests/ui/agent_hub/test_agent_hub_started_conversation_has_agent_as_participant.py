"""Agent Hub — started conversation has the selected agent added as a
Participant, with avatar, name, and version visible (ELITEA-2361).

Opens the "User Story Creator" (id=172) Catalog agent's detail modal, starts
a chat via "Start Chat", expands the Participants panel, and verifies the
agent's own row shows the avatar, the agent name, and the agent version.

Spec: test-specs/agent-hub/l2_agent-hub-started-conversation-has-agent-added-as-participant_ELITEA-2361.md

Reuses ``AgentHubPage`` (Catalog listing + preview modal, ELITEA-2075/2360)
and ``ChatPage``'s Participants-panel helpers
(``expand_participants_panel_via_toggle`` / ``get_participant_row_by_name``,
ELITEA-2075/2168) as-is. One new testid + wrapper method was needed: the
participant row's avatar ``<img>`` (EntityIcon -> EliteAImage.jsx) had no
testid — added ``imgTestId="chat-participant-avatar"`` to
``ParticipantItem.jsx``'s normal (non-error) card branch on
``automation/testids`` (EliteaAI/EliteaUI@87afda90), and
``ChatPage.get_participant_avatar()`` scopes it inside a participant row
(``PARTICIPANT_AVATAR`` class constant, same idiom as
``PARTICIPANT_EDIT_VIEW_BUTTON``).

Case-text drift (CLARIFICATION, already tracked, not re-filed — AFS §
Known Issues / EliteaAI/elitea-testing-public#1042, which explicitly names
this case as an affected sibling): case text "Start conversation" -> live
product reads "Start Chat"; case text's example version "ver-0.1" -> live
agent's actual version is "skills-v3.0". Asserted against the live copy.

Sequenced after ELITEA-2360's own root-cause fix (known defect #1043):
``AgentHubPage.click_start_chat()`` now owns the internal 1s wait before
clicking, so this test calls it exactly as-is with no extra synchronization
at the call site.

Orchestrator's independent 3x gate hit 1/3 fresh red — an intermittent
console-error 404 at Step 2. Reproduced live (1/6 fresh re-runs) with
temporary debug instrumentation; root-caused as an unrelated, pre-existing,
app-wide known-noisy resource — see ``_is_known_1434_montserrat_font_404``
below.
"""

import re

import allure
import pytest
from api import ConversationAPI
from pages.agent_hub_page import AgentHubPage
from pages.chat_page import ChatPage
from playwright.sync_api import Page

pytestmark = [pytest.mark.ui, pytest.mark.chat, pytest.mark.p2, pytest.mark.regression, pytest.mark.new]

UI_ELEMENT_TIMEOUT = 10_000
NAVIGATION_TIMEOUT = 15_000

CATALOG_AGENT_NAME = "User Story Creator"
EXPECTED_AGENT_VERSION = "skills-v3.0"


# Known defect elitea-testing-public#1434 (already filed) — an intermittent
# 404 fetching a Montserrat ``.woff2`` file from Google's Fonts CDN
# (fonts.gstatic.com). NOT tied to this test's own flow: EliteaUI's
# ``index.html`` loads Montserrat via a Google Fonts CSS ``<link>`` tag
# (line 23), so the woff2 fetch happens on EVERY page render, app-wide —
# unrelated to the Agent Hub modal, the Participants panel, or the new
# ``chat-participant-avatar`` testid this test exercises.
# ``fonts.gstatic.com`` URLs are content-hashed and essentially never 404
# once published, so this reads as a transient CDN/network blip rather than
# a broken reference — no fix available on the Elitea side beyond the
# optional mitigation noted on the issue (self-host the font /
# ``rel="preconnect"``). Live-confirmed via temporary debug instrumentation
# (a parallel ``page.on("console", ...)`` printing ``msg.text``/
# ``msg.location`` for every raw error) during this fix-only pass: 1/6 fresh
# re-runs surfaced the exact signature below; removed the debug code once
# confirmed. Same filter-by-resource-URL technique already established by
# ``test_agent_publish_unpublish_version.py``'s ``_is_known_554_toolkits_404``
# — match on BOTH ``msg.text`` and ``(msg.location or {}).get("url", "")``,
# never a blanket "any 404" filter.
def _is_known_1434_montserrat_font_404(msg) -> bool:
    location_url = (msg.location or {}).get("url", "")
    return "404" in msg.text and "fonts.gstatic.com" in location_url and "montserrat" in location_url


# Same known defect (#1434), applied to the raw network ``response`` side-channel
# instead of the console-message side-channel: the SAME woff2 fetch that logs the
# console error above also surfaces here as a bare 4xx status in ``failed_responses``.
# Filtering only the console-error assertions and leaving this one unfiltered would
# just relocate the same intermittent red from one assertion to the other, not fix
# it — so both side-channels for this one known-noisy resource are filtered
# symmetrically. Takes ``(status, url)`` rather than a Playwright message object,
# since ``page.on("response", ...)`` gives no ``.text``/``.location`` shape.
def _is_known_1434_montserrat_font_404_response(status: int, url: str) -> bool:
    return status == 404 and "fonts.gstatic.com" in url and "montserrat" in url


class TestAgentHubStartedConversationHasAgentAsParticipant:
    """ELITEA-2361: Agent Hub — started conversation has agent added as participant (l2, medium)."""

    @allure.issue(
        "https://github.com/EliteaAI/onetest-ai-tm-Elitea/blob/main/tests/automated-full-regression-ui/"
        "agent-hub/ELITEA-2361.md",
        "onetest-ai Test Case link",
    )
    def test_started_conversation_has_agent_as_participant(self, page: Page, _browser_cookies):
        """Starting a conversation from a Catalog agent's detail modal adds that
        agent as a chat participant, and the Participants panel's Agents section
        shows its avatar, name, and version."""
        agent_hub = AgentHubPage(page)
        chat = ChatPage(page)
        conversation_api = ConversationAPI(browser_cookies=_browser_cookies)
        conv_id: int | None = None

        console_errors = agent_hub.capture_console_errors()
        failed_responses: list[tuple[int, str]] = []
        page.on(
            "response",
            lambda resp: failed_responses.append((resp.status, resp.url)) if resp.status >= 400 else None,
        )

        try:
            with allure.step("Step 1 — Navigate to Agent Hub"):
                agent_hub.navigate()
                assert agent_hub.page_heading.is_visible(), "Catalog page heading should be visible"

            with allure.step(f"Step 2 — Click on the {CATALOG_AGENT_NAME!r} agent card to open the detail modal"):
                assert agent_hub.get_agent_card(CATALOG_AGENT_NAME).first.is_visible(), (
                    f"Agent card {CATALOG_AGENT_NAME!r} should be visible on the Catalog page"
                )
                # open_agent_by_name() waits on the agent-details GET response —
                # deterministic ready-signal for the modal, but click_start_chat()
                # owns the extra known-defect-#1043 wait internally (below).
                agent_hub.open_agent_by_name(CATALOG_AGENT_NAME, timeout=NAVIGATION_TIMEOUT)
                # Known defect: elitea-testing-public#1434 — the app-wide Montserrat
                # webfont CDN 404 (see _is_known_1434_montserrat_font_404 docstring)
                # can fire on this step's page render; filtered by resource URL, not
                # a blanket 404 exclusion.
                unexpected_errors = [m.text for m in console_errors if not _is_known_1434_montserrat_font_404(m)]
                assert not unexpected_errors, (
                    f"Unexpected console errors while opening the modal: {unexpected_errors}"
                )

            with allure.step(
                'Step 3 — Click "Start Chat" (case text: "Start conversation" — drift, '
                "tracked EliteaAI/elitea-testing-public#1042)"
            ):
                agent_hub.click_start_chat(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step("Step 4 — Verify the new chat is created and the user lands on the Chat page"):
                page.wait_for_url(re.compile(r"/chat"), timeout=NAVIGATION_TIMEOUT)
                chat.wait_for_page_load()
                # Known defect: elitea-testing-public#1434 — see
                # _is_known_1434_montserrat_font_404_response docstring above.
                unexpected_responses = [
                    (status, url)
                    for status, url in failed_responses
                    if not _is_known_1434_montserrat_font_404_response(status, url)
                ]
                assert not unexpected_responses, f"Unexpected 4xx/5xx responses: {unexpected_responses}"

            with allure.step("Step 5 — Expand the Participants panel"):
                chat.expand_participants_panel_via_toggle(timeout=UI_ELEMENT_TIMEOUT)

            with allure.step(
                f"Step 6 — Verify {CATALOG_AGENT_NAME!r} appears under the Agents section "
                "of the Participants panel"
            ):
                participant_row = chat.get_participant_row_by_name(CATALOG_AGENT_NAME, timeout=UI_ELEMENT_TIMEOUT)
                assert participant_row.is_visible(), (
                    f"Participant row for {CATALOG_AGENT_NAME!r} should be visible in the Participants panel"
                )
                row_text = participant_row.text_content() or ""

            with allure.step("Step 7 — Verify the agent name and version are displayed in the participant row"):
                assert CATALOG_AGENT_NAME in row_text, (
                    f"Participant row should display the agent name {CATALOG_AGENT_NAME!r}, got: {row_text!r}"
                )
                assert EXPECTED_AGENT_VERSION in row_text, (
                    f"Participant row should display the agent version {EXPECTED_AGENT_VERSION!r}, "
                    f"got: {row_text!r}"
                )

            with allure.step("Step 8 — Verify the agent's avatar is visible in the participant row"):
                avatar_img = chat.get_participant_avatar(participant_row, timeout=UI_ELEMENT_TIMEOUT)
                assert avatar_img.count() > 0, (
                    f"Participant row for {CATALOG_AGENT_NAME!r} should display an agent avatar image"
                )
                assert avatar_img.get_attribute("alt") == "elitea", (
                    "Agent avatar image should carry the product's own alt text ('elitea')"
                )

            with allure.step("Side-channel check — zero console errors, zero 4xx/5xx across the whole flow"):
                # Known defect: elitea-testing-public#1434 — see
                # _is_known_1434_montserrat_font_404 docstring above.
                unexpected_errors = [m.text for m in console_errors if not _is_known_1434_montserrat_font_404(m)]
                assert not unexpected_errors, f"Unexpected console errors: {unexpected_errors}"
                unexpected_responses = [
                    (status, url)
                    for status, url in failed_responses
                    if not _is_known_1434_montserrat_font_404_response(status, url)
                ]
                assert not unexpected_responses, f"Unexpected 4xx/5xx responses: {unexpected_responses}"
        finally:
            console_errors.stop()
            # A conversation may not have been created yet if the flow failed before
            # navigation; only attempt cleanup once a conversation id is on the URL.
            match = re.search(r"/chat/(\d+)", page.url)
            if match:
                conv_id = int(match.group(1))
            if conv_id:
                try:
                    conversation_api.delete_conversation(conv_id)
                except Exception:
                    pass
